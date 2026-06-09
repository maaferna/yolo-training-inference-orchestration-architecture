# Continuous Improvement Training

This document describes the continuous improvement training pipeline, incremental training on new data, and baseline comparison logic.

## Continuous Improvement Motivation

**Goal**: Enable models to improve over time as new training data becomes available, while preventing performance degradation.

**Key Principle**: A model should only be updated if it demonstrably improves upon the current best model.

---

## CI Training Pipeline Flow

### Step 1: Load Previous Best Model

```python
import json
from pathlib import Path
from ultralytics import YOLO

def load_previous_best():
    """Load previous best model and its baseline metrics"""
    
    # Load reference file
    ref_path = Path('/shared_storage/models/best_model_ref.json')
    
    with open(ref_path) as f:
        ref = json.load(f)
    
    # Extract baseline
    baseline = {
        'model_path': ref['model_path'],
        'mAP50': ref['mAP50'],
        'mAP75': ref['mAP75'],
        'precision': ref['precision'],
        'recall': ref['recall'],
        'timestamp': ref['training_timestamp']
    }
    
    # Load model
    model = YOLO(baseline['model_path'])
    
    return model, baseline
```

### Step 2: Prepare New Training Data

```python
def prepare_new_dataset(new_dataset_yaml):
    """Validate new training data"""
    
    import yaml
    from pathlib import Path
    
    with open(new_dataset_yaml) as f:
        dataset_config = yaml.safe_load(f)
    
    # Validate paths exist
    for split in ['train', 'val']:
        split_path = dataset_config.get(split)
        if not Path(split_path).exists():
            raise FileNotFoundError(f"Dataset split not found: {split_path}")
    
    print(f"Dataset validated: {new_dataset_yaml}")
    
    return dataset_config
```

### Step 3: Execute Incremental Training

```python
def incremental_training(
    model,
    new_dataset_yaml,
    epochs=50,
    batch_size=32,
    ci_run_id='ci_001'
):
    """Run training on new data"""
    
    results = model.train(
        data=new_dataset_yaml,
        epochs=epochs,
        batch=batch_size,
        device=0,
        patience=20,           # Early stopping
        seed=42,               # Reproducible
        save=True,
        project='runs/ci_training',
        name=f'run_{ci_run_id}'
    )
    
    # Extract new metrics
    new_metrics = {
        'mAP50': results.box.map50,
        'mAP75': results.box.map75,
        'precision': results.box.mp,
        'recall': results.box.mr,
        'timestamp': datetime.now().isoformat()
    }
    
    return results, new_metrics
```

---

## Baseline Comparison

### Step 4: Compare Against Historical Baseline

```python
def compare_metrics(baseline, new_metrics, improvement_threshold=0.01):
    """Compare new metrics against baseline"""
    
    comparison = {
        'baseline': baseline,
        'new_metrics': new_metrics,
        'improvements': {}
    }
    
    # Calculate improvements for each metric
    for metric_name in ['mAP50', 'mAP75', 'precision', 'recall']:
        baseline_val = baseline[metric_name]
        new_val = new_metrics[metric_name]
        
        absolute_change = new_val - baseline_val
        percentage_change = (absolute_change / baseline_val) * 100 if baseline_val > 0 else 0
        
        comparison['improvements'][metric_name] = {
            'baseline': baseline_val,
            'new': new_val,
            'absolute_change': absolute_change,
            'percentage_change': percentage_change
        }
    
    return comparison
```

### Step 5: Decision Logic

```python
def make_update_decision(
    comparison,
    improvement_threshold=0.01,
    primary_metric='mAP50'
):
    """Decide whether to update best model"""
    
    primary_improvement = comparison['improvements'][primary_metric]
    absolute_change = primary_improvement['absolute_change']
    
    # Threshold-based decision
    if absolute_change >= improvement_threshold:
        decision = {
            'approve': True,
            'reason': (
                f"Improvement of {absolute_change:.4f} in {primary_metric} "
                f"exceeds threshold of {improvement_threshold}"
            )
        }
    else:
        decision = {
            'approve': False,
            'reason': (
                f"No sufficient improvement. "
                f"Change: {absolute_change:.4f}, "
                f"threshold: {improvement_threshold}"
            )
        }
    
    return decision
```

### Example Scenarios

**Scenario A: Improvement Approved**
```python
baseline = {'mAP50': 0.85, 'precision': 0.88, 'recall': 0.82}
new_metrics = {'mAP50': 0.87, 'precision': 0.89, 'recall': 0.84}
improvement_threshold = 0.01

comparison = compare_metrics(baseline, new_metrics)
decision = make_update_decision(comparison, improvement_threshold)

# Result: approve=True, reason="Improvement of 0.02 exceeds threshold of 0.01"
```

**Scenario B: Improvement Rejected**
```python
baseline = {'mAP50': 0.85, 'precision': 0.88, 'recall': 0.82}
new_metrics = {'mAP50': 0.853, 'precision': 0.881, 'recall': 0.821}
improvement_threshold = 0.01

comparison = compare_metrics(baseline, new_metrics)
decision = make_update_decision(comparison, improvement_threshold)

# Result: approve=False, reason="Change: 0.003, threshold: 0.01"
```

**Scenario C: Degradation Detected**
```python
baseline = {'mAP50': 0.85, 'precision': 0.88, 'recall': 0.82}
new_metrics = {'mAP50': 0.83, 'precision': 0.86, 'recall': 0.80}
improvement_threshold = 0.01

comparison = compare_metrics(baseline, new_metrics)
decision = make_update_decision(comparison, improvement_threshold)

# Result: approve=False, reason="Change: -0.02, threshold: 0.01"
# Important: Model degradation is rejected, keeps current best
```

---

## Conditional Best Model Update

### Approved: Update Best Model

```python
def update_best_model(new_model_path, new_metrics, comparison, ci_run_id):
    """Update best_model_ref.json with new model"""
    
    import shutil
    from pathlib import Path
    
    # Copy new model to registry location
    shared_path = Path('/shared_storage/models/best.pt')
    shutil.copy(new_model_path, shared_path)
    
    # Create updated reference
    best_model_ref = {
        'model_path': str(shared_path),
        'mAP50': new_metrics['mAP50'],
        'mAP75': new_metrics['mAP75'],
        'precision': new_metrics['precision'],
        'recall': new_metrics['recall'],
        'timestamp': new_metrics['timestamp'],
        'training_type': 'ci',  # Mark as CI training
        'ci_run_id': ci_run_id,
        'previous_mAP50': comparison['baseline']['mAP50'],
        'improvement': {
            'absolute': comparison['improvements']['mAP50']['absolute_change'],
            'percentage': comparison['improvements']['mAP50']['percentage_change']
        }
    }
    
    # Write atomically (write to tmp, then rename)
    import tempfile
    import json
    
    ref_path = Path('/shared_storage/models/best_model_ref.json')
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=ref_path.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(best_model_ref, tmp, indent=2)
        tmp_path = tmp.name
    
    # Atomic rename
    import os
    os.replace(tmp_path, ref_path)
    
    # Optional: backup old model
    backup_path = Path('/shared_storage/models/best_v_backup.pt')
    # shutil.copy(...)  # backup previous model
    
    print(f"Best model updated: {ref_path}")
    
    return best_model_ref
```

### Rejected: Preserve Existing Model

```python
def preserve_existing_model(comparison, ci_run_id):
    """Keep existing model, archive new training artifacts"""
    
    from pathlib import Path
    import json
    
    # Create CI training record (for audit trail)
    ci_record = {
        'ci_run_id': ci_run_id,
        'baseline': comparison['baseline'],
        'new_metrics': comparison['new_metrics'],
        'improvements': comparison['improvements'],
        'decision': 'REJECTED',
        'reason': 'Model degradation detected',
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to archive
    archive_path = Path(
        f'/shared_storage/ci_training/run_{ci_run_id}/decision.json'
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(archive_path, 'w') as f:
        json.dump(ci_record, f, indent=2)
    
    print(f"CI training rejected. Keeping current best model.")
    print(f"Archive: {archive_path}")
    
    return ci_record
```

---

## ClearML Selective Logging

### Log Comparison Metrics

```python
def log_ci_to_clearml(task, comparison, decision):
    """Log CI training metrics to ClearML"""
    
    # Log baseline metrics
    for metric, value in comparison['baseline'].items():
        if metric != 'timestamp':
            task.upload_artifact(
                name=f"baseline_{metric}",
                artifact_object=value
            )
    
    # Log improvements
    for metric_name, improvement in comparison['improvements'].items():
        task.upload_artifact(
            name=f"improvement_{metric_name}",
            artifact_object=improvement
        )
    
    # Log decision
    task.upload_artifact(
        name="ci_decision",
        artifact_object={
            'approved': decision['approve'],
            'reason': decision['reason']
        }
    )
    
    # Log to task text
    task.report_text(
        title="CI Training Decision",
        series="CI",
        value=decision['reason']
    )
```

---

## Race Condition Risk: File-Based Best Model Reference

### The Problem

```
Timeline of potential race condition:

Time  CI Training A          CI Training B
────  ─────────────────────  ─────────────────────
T1    Read best_model_ref    (waiting)
      baseline mAP50 = 0.85
T2                          Read best_model_ref
                            baseline mAP50 = 0.85
T3    Training complete      (still training)
      new mAP50 = 0.86
      (improvement!)
T4                          Training complete
                            new mAP50 = 0.84
                            (degradation!)
T5    Write best_model_ref   (waiting)
      Update to 0.86
T6                          Write best_model_ref
                            Update to 0.84 ← OVERWRITES!

RESULT: Best model degraded to 0.84, should be 0.86
```

### Consequences

- ✗ Model quality unexpectedly decreases
- ✗ Inference pipeline uses degraded model
- ✗ Hard to detect until metrics monitoring
- ✗ No audit trail of what happened

### Mitigations (Current)

1. **Serialize CI Training**: Run one CI training job at a time
   - Enforce in job queue (when implemented)
   - Document in operations manual

2. **Atomic File Operations**: Write to tmp file, then rename
   - Atomic rename has minimal race window
   - Still not perfect, but much safer

### Recommended Solution (Future)

Implement database-backed transactional model registry:

```sql
CREATE TABLE model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255),
    model_path VARCHAR(255),
    mAP50 FLOAT,
    is_best BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE (model_name, is_best)
);

-- Update best model atomically
BEGIN TRANSACTION;
UPDATE model_registry SET is_best = FALSE 
WHERE model_name = 'default' AND is_best = TRUE;

INSERT INTO model_registry 
  (model_name, model_path, mAP50, is_best, created_at)
VALUES 
  ('default', '/path/to/new/model.pt', 0.86, TRUE, NOW());
COMMIT;
```

---

## Configuration Parameters

### Tunable Thresholds

```python
CI_CONFIG = {
    'improvement_threshold': 0.01,    # 1% improvement required
    'primary_metric': 'mAP50',        # Which metric to prioritize
    'max_epochs': 50,                 # CI training epochs
    'batch_size': 32,                 # CI training batch size
    'early_stopping_patience': 20,    # Stop if no improvement
}
```

### Recommended Values

| Parameter | Recommended | Range | Notes |
|-----------|---|---|---|
| `improvement_threshold` | 0.01 | 0.001-0.05 | More conservative: lower threshold |
| `primary_metric` | mAP50 | mAP50, mAP75, F1 | mAP50 most common |
| `max_epochs` | 50 | 20-100 | Fewer than initial training |
| `batch_size` | 32 | 16-64 | Same as initial training typical |
| `patience` | 20 | 10-30 | Stop if no improvement for N epochs |

---

## Summary

Continuous Improvement Training provides:

✅ Incremental model improvement from new data
✅ Baseline comparison for confidence
✅ Conservative update strategy (prevents degradation)
✅ ClearML integration for experiment tracking
✅ Audit trail of update decisions
⚠️ File-based registry race condition (needs mitigation)

**Key Design**: Models only update when improvement is demonstrated, with clear decision logic and audit trails.
