# GPU Resource Management

This document details GPU orchestration, CUDA memory management, multi-GPU strategies, and constraints.

## CUDA Memory Architecture

### GPU Memory Structure

```
GPU Memory (e.g., 24GB A100):

┌─────────────────────────┐
│ CUDA Runtime Context    │ ~100 MB
├─────────────────────────┤
│ Model Weights (YOLO s)  │ ~50 MB
├─────────────────────────┤
│ Optimizer State         │ ~100 MB
├─────────────────────────┤
│ Activations (batch 32)  │ ~2-4 GB
├─────────────────────────┤
│ Gradients              │ ~50 MB
├─────────────────────────┤
│ Intermediate Buffers    │ ~500 MB
├─────────────────────────┤
│ Free Memory             │ Remaining
└─────────────────────────┘
```

### Memory Allocation Flow

```python
import torch

# Check available memory
available = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB
print(f"Total GPU Memory: {available:.2f} GB")

# Check used memory
allocated = torch.cuda.memory_allocated(0) / 1e9
reserved = torch.cuda.memory_reserved(0) / 1e9
print(f"Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")

# Clear cache (returns memory to OS)
torch.cuda.empty_cache()
```

---

## Memory Release Strategy

### After Each Training Seed

```python
def cleanup_between_seeds():
    """Release GPU memory between multi-seed training"""
    
    import torch
    
    # Explicit cleanup steps:
    
    # 1. Remove references
    model = None
    results = None
    trainer = None
    
    # 2. Force garbage collection
    import gc
    gc.collect()
    
    # 3. CUDA cache clear
    torch.cuda.empty_cache()
    
    # 4. Reset peak memory
    torch.cuda.reset_peak_memory_stats()
    
    # 5. Verify cleanup
    allocated_after = torch.cuda.memory_allocated(0) / 1e9
    print(f"Memory after cleanup: {allocated_after:.2f} GB")
    
    if allocated_after > 1.0:
        print("WARNING: Memory not fully released")
```

### Critical Cleanup Points

```python
def train_multiple_seeds():
    """Training loop with careful memory management"""
    
    import torch
    from ultralytics import YOLO
    
    for seed in [42, 123, 456]:
        print(f"\n--- Training Seed {seed} ---")
        
        # Check before training
        torch.cuda.reset_peak_memory_stats()
        
        # Load model fresh each iteration
        model = YOLO('yolov8s.pt')
        
        try:
            # Train
            results = model.train(
                data='dataset.yaml',
                epochs=100,
                device=0,
                seed=seed
            )
            
        finally:
            # ALWAYS cleanup, even if error
            del model
            del results
            torch.cuda.empty_cache()
```

---

## DataParallel (Current Single-GPU Approach)

### Current Implementation

```python
import torch
from ultralytics import YOLO

def train_with_dataparallel(model_size='s'):
    """Train using single GPU (no DataParallel needed)"""
    
    # Ultralytics handles device internally
    model = YOLO(f'yolov8{model_size}.pt')
    
    results = model.train(
        data='dataset.yaml',
        device=0,  # Single GPU
        batch=32,
        epochs=100
    )
    
    return results
```

### Why Single GPU Currently

- **Simplicity**: No synchronization overhead
- **Debugging**: Easier to trace issues
- **Development**: Faster iteration
- **Cost**: Efficient resource utilization
- **Scalability**: Foundation for DDP upgrade

---

## Distributed Data Parallel (DDP) - Deferred to Phase 3

### Multi-GPU Architecture

```python
# FUTURE: Multi-GPU with DDP
def train_with_ddp(model_size='s', gpu_ids=[0, 1, 2, 3]):
    """Train using multiple GPUs with DDP"""
    
    model = YOLO(f'yolov8{model_size}.pt')
    
    results = model.train(
        data='dataset.yaml',
        device=gpu_ids,        # List of GPU IDs
        batch=128,             # Larger batch (32 per GPU × 4 GPUs)
        epochs=100,
        workers=16             # More DataLoader workers
    )
    
    return results
```

### DDP Trade-offs

**Advantages**:
- ✓ Linear speedup with GPU count (ideal case)
- ✓ Large batch sizes improve convergence
- ✓ Leverages all available GPUs

**Disadvantages**:
- ✗ Communication overhead (all-reduce at each epoch)
- ✗ Synchronization points block fast GPUs
- ✗ Batch size must divide evenly across GPUs
- ✗ Harder debugging (requires DDP-aware tools)
- ✗ Network bandwidth bottleneck for distributed nodes

### DDP Communication Pattern

```
Epoch N complete:
┌──────────────────────────────────────┐
│ Gradient averaging across GPUs       │
│  GPU0: [g1, g2, g3]                 │
│  GPU1: [g1', g2', g3']              │
│  GPU2: [g1'', g2'', g3'']           │
│  GPU3: [g1''', g2''', g3''']        │
├──────────────────────────────────────┤
│ All-Reduce on gradients (communication)
├──────────────────────────────────────┤
│ All GPUs update: avg([g1, g1', ...])│
│ Synchronized update                  │
├──────────────────────────────────────┤
│ Next epoch starts (all synchronized)
```

---

## Image Size Trade-offs

### Supported Image Sizes

```
YOLO training input sizes (common values):

Size    | Use Case | Memory | Speed | Quality
────────────────────────────────────────────────
320     | Mobile   | 1-2GB | Fast  | Lower
416     | Edge     | 2-3GB | Fast  | Medium
512     | Default  | 3-4GB | Norm  | Good
640     | Standard | 4-5GB | Norm  | Good
1024    | Large    | 8-10GB| Slow  | Better
1536    | XLarge   | 15GB+ | Very Slow | Best
2048    | MaxRes   | 20GB+ | Extreme | Excellent
```

### Memory Scaling

```
Memory ∝ Image Size²

640 × 640   → 4 GB typical
1024 × 1024 → 10 GB (6.4× increase!)
1536 × 1536 → 22 GB (5.6× of 1024)

Each 50% increase in size requires ~2.25× more memory
```

### Choosing Image Size

```python
# Check GPU memory
total_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9

if total_memory_gb > 20:
    imgsz = 1536  # High-end GPU
elif total_memory_gb > 10:
    imgsz = 1024  # Mid-range GPU
elif total_memory_gb > 8:
    imgsz = 800   # Constrained GPU
else:
    imgsz = 640   # Limited resources
```

---

## GPU Contention and Scheduling

### Current: No Scheduling

```
Timeline:
T1: Training job 1 starts on GPU 0 ✓
T2: Training job 2 requests GPU 0 ✗ (ERROR: already in use)

Problem: Only one job can use GPU at a time
Solution: Queue jobs or allocate multiple GPUs
```

### Future: GPU Job Scheduling

```python
# Future implementation with job queue

class GPUJobScheduler:
    """Simple GPU job scheduler"""
    
    def __init__(self, num_gpus=4):
        self.num_gpus = num_gpus
        self.gpu_availability = {i: True for i in range(num_gpus)}
    
    def allocate_gpu(self, job_id, required_count=1):
        """Allocate GPU(s) to job"""
        available_gpus = [
            gpu_id for gpu_id, available in self.gpu_availability.items()
            if available
        ]
        
        if len(available_gpus) < required_count:
            return None  # No GPUs available
        
        allocated = available_gpus[:required_count]
        for gpu_id in allocated:
            self.gpu_availability[gpu_id] = False
        
        return allocated
    
    def release_gpu(self, gpu_ids):
        """Release GPUs after job completion"""
        for gpu_id in gpu_ids:
            self.gpu_availability[gpu_id] = True
```

---

## CUDA OOM (Out of Memory) Handling

### Detection and Recovery

```python
def train_with_oom_recovery():
    """Train with automatic recovery from OOM"""
    
    batch_size = 32
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            model.train(
                data='dataset.yaml',
                batch=batch_size,
                device=0,
                epochs=100
            )
            break  # Success
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"OOM at batch {batch_size}, attempt {attempt + 1}")
                
                # Reduce batch size
                batch_size = batch_size // 2
                
                # Cleanup
                import torch
                torch.cuda.empty_cache()
                
                # Retry
                if attempt < max_retries - 1:
                    continue
                else:
                    raise RuntimeError("Cannot train within memory limits")
            else:
                raise
```

### Prevention Strategy

```python
def check_memory_requirements(model_size, batch_size, imgsz):
    """Estimate memory requirements"""
    
    # Rough estimates (empirical values)
    base_memory = {
        's': 0.5,   # GB
        'm': 1.0,
        'l': 1.5,
        'x': 2.0
    }
    
    # Batch and image size multipliers
    memory_per_sample = (imgsz / 640) ** 2 * 0.1  # GB per sample
    batch_memory = batch_size * memory_per_sample
    
    total_estimated = base_memory[model_size] + batch_memory + 2.0  # + overhead
    
    return total_estimated
```

---

## Multi-GPU Coordination

### Current: Sequential Training on Same GPU

```
Seed 1:  [Training]========
Seed 2:              [Training]========
Seed 3:                       [Training]========
```

### Future: Parallel Training on Multiple GPUs

```
GPU 0: [Seed 1 Training]========
GPU 1:                [Seed 2 Training]========
GPU 2:                       [Seed 3 Training]========
GPU 3:                              [Seed 4 Training]========

Speedup: 4× (for 4 seeds on 4 GPUs)
```

### Implementation Path

```python
# Stage 1: Manual GPU allocation
seeds_per_gpu = [(42, 0), (123, 1), (456, 2), (789, 3)]
processes = []

for seed, gpu_id in seeds_per_gpu:
    p = Process(
        target=train_seed,
        args=(seed, gpu_id)
    )
    p.start()
    processes.append(p)

for p in processes:
    p.join()

# Stage 2: Use job queue (Celery + Redis)
# Stage 3: Kubernetes with GPU node affinity
```

---

## CUDA Context Management

### Single Context (Current)

```python
# Ultralytics manages CUDA context internally
# One context per GPU device

model = YOLO('yolov8s.pt')
results = model.train(device=0)  # Context auto-managed
```

### Multiple Contexts (Future)

```python
import torch

def train_with_explicit_context(seed, gpu_id):
    """Train with explicit CUDA context management"""
    
    # Set device context
    torch.cuda.set_device(gpu_id)
    
    # Verify device
    current_device = torch.cuda.current_device()
    print(f"Training on device: {current_device}")
    
    # Train
    model = YOLO('yolov8s.pt')
    results = model.train(
        data='dataset.yaml',
        device=gpu_id,
        seed=seed
    )
    
    return results
```

---

## Monitoring GPU Usage

### Real-time Monitoring

```python
import torch
import time

def monitor_gpu_training():
    """Monitor GPU during training"""
    
    start_time = time.time()
    
    while training_active:
        # Memory stats
        allocated = torch.cuda.memory_allocated(0) / 1e9  # GB
        cached = torch.cuda.memory_cached(0) / 1e9
        peak = torch.cuda.max_memory_allocated(0) / 1e9
        
        # GPU utilization (requires nvidia-smi)
        import subprocess
        nvidia_output = subprocess.check_output([
            'nvidia-smi', '--query-gpu=utilization.gpu',
            '--format=csv,noheader'
        ])
        utilization = int(nvidia_output.decode().strip().split()[0])
        
        print(f"Allocated: {allocated:.2f}GB, Peak: {peak:.2f}GB, "
              f"Utilization: {utilization}%")
        
        time.sleep(10)
```

---

## Recommendations

### Current Optimization Strategy

1. **Single GPU Training** ✓
   - Use imgsz=640-800 for balance
   - Batch size 16-32 on standard GPUs (24GB)
   - Cleanup between seeds rigorously

2. **Memory Management** ✓
   - Monitor peak memory usage
   - Reduce batch size if OOM occurs
   - Clear cache between jobs

3. **Multi-Seed Efficiency** ✓
   - Sequential on single GPU (current)
   - 3-5 seeds for statistical significance

### Future Improvements

1. **Multi-GPU Training** (Phase 2)
   - DDP for 4+ GPUs
   - Parallel seed training

2. **GPU Scheduling** (Phase 2)
   - Job queue (Celery + Redis)
   - Fair allocation across users

3. **Heterogeneous GPUs** (Phase 3)
   - Support mixed GPU types
   - Adaptive batching

---

**GPU resource management is critical for ML training efficiency. Current single-GPU approach is pragmatic; future multi-GPU support enables significant speedups.**
