# YOLO Training Engine

This document details the YOLO training implementation, multi-seed strategy, metric collection, and error handling.

## YOLOv8/YOLOv11 Training Overview

### Base Model Selection

The training engine supports YOLOv8 and YOLOv11 models from Ultralytics in various sizes:

| Size | Parameters | GFLOPs | Typical Use |
|------|---|---|---|
| `nano` (n) | 3.2M | 8.6 | Edge devices, limited resources |
| `small` (s) | 11.2M | 28.6 | Default choice, balanced |
| `medium` (m) | 25.9M | 78.9 | Higher accuracy needed |
| `large` (l) | 43.7M | 165.4 | Demanding accuracy requirements |
| `xlarge` (x) | 68.2M | 257.8 | Maximum accuracy, high compute |

### Baseline Model Source

Models are loaded from Ultralytics pretrained weights:

```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8s.pt')  # Ultralytics auto-downloads

# Model properties
model.model.names  # Class names from dataset
model.model.nc     # Number of classes
```

### Training Initialization

```python
# Key parameters for training
results = model.train(
    data='path/to/data.yaml',        # YOLO dataset format
    epochs=100,                      # Training epochs
    imgsz=640,                       # Input image size
    batch=32,                        # Batch size
    device=0,                        # GPU device
    workers=8,                       # DataLoader workers
    patience=50,                     # Early stopping patience
    save=True,                       # Save checkpoints
    save_period=10,                  # Save every N epochs
    seed=42,                         # Random seed
    mosaic=1.0,                      # Mosaic augmentation
    translate=0.1,                   # Translation augmentation
    scale=0.5,                       # Scale augmentation
    flipud=0.5,                      # Vertical flip probability
    fliplr=0.5,                      # Horizontal flip probability
    optimizer='SGD',                 # Optimizer: SGD, Adam, AdamW
    lr0=0.001,                       # Initial learning rate
    lrf=0.1,                         # Final LR as fraction of initial
    momentum=0.937,                  # SGD momentum
    weight_decay=0.0005,             # L2 regularization
    warmup_epochs=3.0,               # Warmup epochs
    cos_lr=True                      # Cosine learning rate schedule
)
```

---

## Multi-Seed Training Strategy

### Motivation

Running multiple training runs with different random seeds provides:

1. **Statistical Significance**: Reduces variance from random initialization
2. **Confidence**: Model quality is robust, not luck-dependent
3. **Robustness**: Average metrics represent true capability
4. **Reproducibility**: Can rerun any seed for verification

### Seed Selection

```python
SEEDS = [42, 123, 456]  # 3 seeds typical
# Alternative: [42, 123, 456, 789, 999]  # 5 seeds for more confidence

for seed in SEEDS:
    train_single_seed(
        model_size='s',
        seed=seed,
        epochs=100,
        other_params=...
    )
```

### Per-Seed Training Loop

```python
def train_single_seed(seed, model_size, epochs, dataset_yaml):
    """Train with a single random seed"""
    
    # Set seed
    import random
    import numpy as np
    import torch
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    
    # Load model
    model = YOLO(f'yolov8{model_size}.pt')
    
    # Train
    results = model.train(
        data=dataset_yaml,
        epochs=epochs,
        seed=seed,  # Ultralytics also uses seed
        device=0,
        ...
    )
    
    # Return results
    return results  # Contains metrics
```

### Metrics Collection Across Seeds

```python
def collect_metrics_across_seeds(seeds, model_size, epochs, dataset_yaml):
    """Run training with multiple seeds and collect results"""
    
    all_results = {}
    
    for seed in seeds:
        results = train_single_seed(
            seed=seed,
            model_size=model_size,
            epochs=epochs,
            dataset_yaml=dataset_yaml
        )
        
        # Extract key metrics
        metrics = {
            'seed': seed,
            'mAP50': results.box.map50,
            'mAP75': results.box.map75,
            'mAP': results.box.map,
            'precision': results.box.mp,
            'recall': results.box.mr,
            'final_epoch': epochs,
            'training_time': results.speed
        }
        
        all_results[f'seed_{seed}'] = metrics
        
        # Cleanup CUDA memory after each seed
        torch.cuda.empty_cache()
    
    return all_results
```

### Aggregating Results

```python
def aggregate_seed_results(all_results):
    """Compute statistics across seeds"""
    
    import numpy as np
    
    metrics_list = list(all_results.values())
    mAP50_values = [m['mAP50'] for m in metrics_list]
    
    aggregated = {
        'mean_mAP50': np.mean(mAP50_values),
        'std_mAP50': np.std(mAP50_values),
        'max_mAP50': np.max(mAP50_values),
        'min_mAP50': np.min(mAP50_values),
        'best_seed': metrics_list[np.argmax(mAP50_values)]['seed'],
        'all_seeds_results': all_results
    }
    
    return aggregated
```

---

## Metric Collection

### Available Metrics

YOLOv8 provides comprehensive detection metrics:

```
Metric              | Range  | Interpretation
────────────────────|--------|──────────────────────────
mAP50               | 0-100  | Average precision at 50% IoU
mAP75               | 0-100  | Average precision at 75% IoU
mAP                 | 0-100  | Average precision (0.5-0.95)
Precision (P)       | 0-100  | TP / (TP + FP)
Recall (R)          | 0-100  | TP / (TP + FN)
F1 Score            | 0-1    | 2 * (P*R) / (P+R)
Loss (train)        | 0-∞    | Training loss (lower better)
Loss (val)          | 0-∞    | Validation loss (lower better)
```

### Per-Epoch Logging

```python
def train_with_metric_logging(dataset_yaml, clearml_task=None):
    """Train and log metrics to ClearML"""
    
    results = model.train(data=dataset_yaml, ...)
    
    # results object structure:
    # results.box.map50 → single float value (final epoch)
    # results.box.maps  → list of mAP50 per epoch
    
    if clearml_task:
        # Log metrics to ClearML for tracking
        for epoch, map50 in enumerate(results.box.maps):
            clearml_task.upload_artifact(
                name=f"metrics_epoch_{epoch}",
                artifact_object={'mAP50': map50}
            )
```

### Results Structure

```python
# results = model.train(...)
# Access trained model
model_best = results.model  # YOLOv8 instance with best weights

# Get box metrics (most common)
print(results.box)
# Output: dict_keys(['curve', 'fitness', 'map', 'map50', 'maps', 'mp', 'mr', 'speeds'])

# Access specific metrics
mAP50 = results.box.map50  # single float for best epoch
mAP50_per_epoch = results.box.maps  # list of values per epoch
```

---

## Validation Fallback

### Problem: Ultralytics train() Returns None

Occasionally, Ultralytics' `train()` method returns `None` instead of results object.

**Cause**: Internal error, CUDA issue, or corrupted state

**Solution**: Implement manual validation fallback

### Validation Fallback Pattern

```python
def train_with_fallback(model, dataset_yaml, **train_kwargs):
    """Train with fallback validation if train() returns None"""
    
    results = model.train(data=dataset_yaml, **train_kwargs)
    
    if results is None:
        print("WARNING: train() returned None, using manual validation fallback")
        
        # Fallback: manual validation
        val_results = model.val(data=dataset_yaml)
        
        # Extract metrics manually
        metrics = {
            'mAP50': val_results.box.map50,
            'mAP75': val_results.box.map75,
            'precision': val_results.box.mp,
            'recall': val_results.box.mr,
            'fallback': True  # Mark as fallback
        }
        
        return metrics
    else:
        # Normal path: use results
        metrics = {
            'mAP50': results.box.map50,
            'mAP75': results.box.map75,
            'precision': results.box.mp,
            'recall': results.box.mr,
            'fallback': False
        }
        
        return metrics
```

### Clearing Ultralytics Cache (if corrupted)

```python
import shutil
import os

def clear_ultralytics_cache():
    """Clear Ultralytics settings cache that may be corrupted"""
    
    cache_dir = os.path.expanduser('~/.config/Ultralytics')
    settings_file = os.path.join(cache_dir, 'settings.json')
    
    if os.path.exists(settings_file):
        try:
            os.remove(settings_file)
            print(f"Cleared corrupted settings: {settings_file}")
        except Exception as e:
            print(f"Error clearing settings: {e}")
```

---

## Model Selection Based on mAP50

### Selection Criteria

After multi-seed training, select the best model based on mAP50 metric:

```python
def select_best_model(all_results, copy_to_shared_storage=True):
    """Select best model from multi-seed training"""
    
    best_seed = None
    best_mAP50 = -1
    
    for seed_name, metrics in all_results.items():
        if metrics['mAP50'] > best_mAP50:
            best_mAP50 = metrics['mAP50']
            best_seed = metrics['seed']
    
    # Copy best model to shared storage
    if copy_to_shared_storage:
        source = f'runs/detect/train_{best_seed}/weights/best.pt'
        destination = '/shared_storage/models/best.pt'
        
        import shutil
        shutil.copy(source, destination)
    
    return {
        'best_seed': best_seed,
        'best_mAP50': best_mAP50,
        'model_path': destination if copy_to_shared_storage else source
    }
```

### Why mAP50?

- **Industry Standard**: mAP50 is standard for object detection benchmarks
- **Conservative**: 50% IoU threshold is realistic for most applications
- **Efficient**: Faster to compute than mAP (0.5-0.95)
- **Interpretable**: Single number, easy to compare

**Alternative metrics**:
- `mAP75`: Higher IoU threshold, stricter accuracy requirement
- `mAP`: Average across all IoU thresholds, most comprehensive
- `F1`: Combines precision and recall, simpler but less nuanced

---

## Multi-GPU Considerations

### Current: DataParallel (Single GPU)

```python
# Current implementation uses single GPU
model = YOLO('yolov8s.pt')
results = model.train(device=0, ...)  # Single GPU
```

### Evaluated: Distributed Data Parallel (DDP)

For future multi-GPU training:

```python
# Future: Multi-GPU with DDP
model = YOLO('yolov8s.pt')
results = model.train(
    device=[0, 1, 2, 3],  # Multiple GPUs
    workers=16,           # More workers for multi-GPU
    ...
)
```

**Considerations**:
- ✓ Linear speedup with GPU count (ideal case)
- ✗ Communication overhead between GPUs
- ✗ Synchronization at batch boundaries
- ✗ More complex debugging

---

## CUDA Memory Management

### Memory Cleanup Between Seeds

```python
import torch

def cleanup_cuda_memory():
    """Clean up CUDA memory after training"""
    
    # Clear cache
    torch.cuda.empty_cache()
    
    # Reset peak memory tracking
    torch.cuda.reset_peak_memory_stats()
    
    # Optional: Get memory info
    allocated = torch.cuda.memory_allocated() / 1e9  # GB
    reserved = torch.cuda.memory_reserved() / 1e9    # GB
    print(f"After cleanup - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
```

### Pre-Training Memory Check

```python
def check_gpu_memory(required_gb=2.0):
    """Verify GPU has enough memory before training"""
    
    import torch
    
    available = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU Memory: {available:.2f}GB available")
    
    if available < required_gb:
        raise RuntimeError(
            f"Insufficient GPU memory. "
            f"Need {required_gb}GB, have {available:.2f}GB"
        )
```

### Out-of-Memory Error Recovery

```python
def train_with_oom_recovery(model, dataset_yaml, initial_batch_size=32):
    """Train with automatic recovery from OOM errors"""
    
    batch_size = initial_batch_size
    
    while batch_size > 4:  # Minimum batch size
        try:
            results = model.train(
                data=dataset_yaml,
                batch=batch_size,
                ...
            )
            return results
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"OOM with batch {batch_size}, reducing to {batch_size // 2}")
                batch_size //= 2
                torch.cuda.empty_cache()
            else:
                raise
    
    raise RuntimeError("Cannot train even with minimum batch size")
```

---

## Checkpointing and Resume

### Saving Checkpoints

```python
# Ultralytics saves automatically during training
# Checkpoints stored in: runs/detect/train/weights/

# epoch50.pt     → Checkpoint at epoch 50
# last.pt        → Last epoch checkpoint
# best.pt        → Best epoch (by default metric)
```

### Resuming Training

```python
def resume_training(last_checkpoint_path):
    """Resume training from checkpoint"""
    
    model = YOLO(last_checkpoint_path)  # Load checkpoint
    
    results = model.train(
        resume=True,  # Resume mode
        epochs=150,   # Total epochs after resume
        ...
    )
    
    return results
```

---

## Training Configuration Logging

### Log Configuration to ClearML

```python
def log_training_config_to_clearml(task, config):
    """Log training configuration for reproducibility"""
    
    # Log as text
    task.upload_artifact(
        name="training_config",
        artifact_object=config
    )
    
    # Or connect to task
    task.connect_configuration(
        configuration_dict=config,
        name="training_parameters"
    )
```

---

## Summary

The YOLO training engine provides:

✅ Multi-seed training for statistical significance
✅ Comprehensive metric collection
✅ Fallback validation when train() fails
✅ Automatic model selection based on mAP50
✅ CUDA memory management
✅ Error recovery and logging
✅ Checkpoint persistence

This enables reliable, reproducible training runs with confidence in model quality.
