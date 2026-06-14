# ClearML Experiment Tracking

This document describes ClearML integration for experiment tracking, metric logging, model artifact registration, and failure isolation.

## ClearML Role in Architecture

ClearML serves as the **experiment metadata repository** - not the source of truth for artifacts, but the record of what happened.

**What ClearML provides** (implemented):
- ✅ Experiment metadata (task info, hyperparameters)
- ✅ Metrics logging (mAP, precision, recall)
- ✅ Model artifact registration (model path references)
- ✅ Task comparison and history

**What ClearML does NOT provide** (not implemented):
- ❌ Data lineage (which datasets fed this model?)
- ❌ Hyperparameter inheritance tracking
- ❌ Dependency resolution
- ❌ Model registry (source of truth is shared filesystem)

```
┌──────────────────────┐
│  Training/CI/Inference Event
└────────┬─────────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │ FastAPI Service                         │
    │ - Runs training/inference               │
    │ - Generates artifacts                   │
    │ - Writes to shared storage              │
    └────┬──────────────────────┬─────────────┘
         │                      │
    ┌────▼─────────────────┐   ┌▼──────────────────────┐
    │ Shared Storage       │   │ ClearML Task         │
    │ (Artifacts)          │   │ (Metadata/Tracking)  │
    │ - best.pt            │   │ - Hyperparameters    │
    │ - summary.json       │   │ - Metrics            │
    │ - inference results  │   │ - Task info          │
    │ SOURCE OF TRUTH      │   │ - Logs/Debug info    │
    └──────────────────────┘   └──────────────────────┘
         ↑                             ↑
         │                             │
         └─────────────────┬───────────┘
                           │
                    ┌──────▼──────────┐
                    │ Django Layer   │
                    │ - Read results │
                    │ - Display UI   │
                    └────────────────┘
```

---

## Experiment Initialization

### Creating a Task

```python
from clearml import Task

def initialize_training_task(training_id, hyperparams):
    """Initialize ClearML task for training run"""
    
    task = Task.init(
        project_name="AI_Orchestration_Project",
        task_name=f"training_run_{training_id}",
        task_type=Task.TaskTypes.training
    )
    
    # Connect hyperparameters
    task.connect_configuration(
        configuration_dict={
            'model_size': hyperparams['model_size'],
            'epochs': hyperparams['epochs'],
            'batch_size': hyperparams['batch_size'],
            'learning_rate': hyperparams['learning_rate'],
            'num_seeds': hyperparams['num_seeds'],
            'dataset': 'PROJECT_DATASET_PLACEHOLDER'
        },
        name="training_hyperparameters"
    )
    
    # Set task properties
    task.set_parameter('dataset_tag', 'ANONYMIZED_DATASET')
    task.add_tags(['training', 'multi-seed'])
    
    return task
```

### CI Training Task

```python
def initialize_ci_training_task(ci_run_id, baseline_model):
    """Initialize ClearML task for CI training"""
    
    task = Task.init(
        project_name="AI_Orchestration_Project",
        task_name=f"ci_training_{ci_run_id}",
        task_type=Task.TaskTypes.training
    )
    
    # Connect baseline info
    task.connect_configuration(
        configuration_dict={
            'baseline_model_mAP50': baseline_model['mAP50'],
            'baseline_model_seed': baseline_model['seed'],
            'new_dataset': 'PROJECT_NEW_DATA_PLACEHOLDER'
        },
        name="ci_baseline"
    )
    
    task.add_tags(['ci-training', 'continuous-improvement'])
    
    return task
```

---

## Metrics Logging

### Per-Epoch Metrics

```python
def log_training_metrics_per_epoch(task, results):
    """Log metrics from each training epoch"""
    
    logger = task.get_logger()
    
    # Ultralytics provides per-epoch metrics
    if hasattr(results.box, 'maps'):  # List of mAP50 per epoch
        for epoch, map50 in enumerate(results.box.maps):
            logger.report_scalar(
                title="Training Metrics",
                series="mAP50",
                value=map50,
                iteration=epoch
            )
    
    # Loss metrics
    if hasattr(results, 'losses'):
        for epoch, train_loss in enumerate(results.losses.get('train', [])):
            logger.report_scalar(
                title="Training Metrics",
                series="train_loss",
                value=train_loss,
                iteration=epoch
            )
```

### Final Metrics

```python
def log_final_training_metrics(task, results, best_seed_results):
    """Log final training metrics"""
    
    logger = task.get_logger()
    
    # Final metrics
    logger.report_scalar(
        title="Final Training Metrics",
        series="best_mAP50",
        value=best_seed_results['best_mAP50']
    )
    
    logger.report_scalar(
        title="Final Training Metrics",
        series="mean_mAP50_across_seeds",
        value=best_seed_results['mean_mAP50']
    )
    
    logger.report_scalar(
        title="Final Training Metrics",
        series="best_seed",
        value=best_seed_results['best_seed']
    )
    
    # Training statistics
    logger.report_text(
        title="Training Summary",
        series="Statistics",
        text=(
            f"Best mAP50: {best_seed_results['best_mAP50']:.4f}\n"
            f"Mean mAP50: {best_seed_results['mean_mAP50']:.4f}\n"
            f"Std Dev: {best_seed_results['std_mAP50']:.4f}\n"
            f"Best Seed: {best_seed_results['best_seed']}"
        )
    )
```

### CI Training Comparison Logging

```python
def log_ci_comparison_metrics(task, comparison, decision):
    """Log CI training comparison metrics"""
    
    logger = task.get_logger()
    
    # Baseline vs. New
    logger.report_scalar(
        title="CI Training Comparison",
        series="Baseline_mAP50",
        value=comparison['baseline']['mAP50']
    )
    
    logger.report_scalar(
        title="CI Training Comparison",
        series="New_mAP50",
        value=comparison['new_metrics']['mAP50']
    )
    
    # Improvement
    improvement = comparison['improvements']['mAP50']
    logger.report_scalar(
        title="CI Training Comparison",
        series="Absolute_Improvement",
        value=improvement['absolute_change']
    )
    
    logger.report_text(
        title="CI Decision",
        series="Approval",
        text=decision['reason']
    )
```

---

## Model Registration

### Register Best Model

```python
def register_best_model_to_clearml(task, model_path, metrics):
    """Register best model as artifact"""
    
    task.upload_artifact(
        name="best_model",
        artifact_object=model_path
    )
    
    # Also upload metadata
    task.upload_artifact(
        name="best_model_metadata",
        artifact_object={
            'model_path': model_path,
            'mAP50': metrics['best_mAP50'],
            'mAP75': metrics['best_mAP75'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'timestamp': metrics['timestamp']
        }
    )
```

### Link Model to Task

```python
def connect_model_to_task(task, model_path):
    """Connect model so ClearML tracks it"""
    
    task.connect_model(
        name="best_model",
        model=model_path
    )
```

---

## Task Status and Completion

### Close Task on Success

```python
def complete_training_task(task, status="completed", comment=None):
    """Mark training task as complete"""
    
    if comment:
        task.upload_artifact(
            name="completion_note",
            artifact_object=comment
        )
    
    task.close(
        status=Task.TaskStatus.completed if status == "completed" else Task.TaskStatus.failed
    )
```

### Handle Failures

```python
def log_training_failure(task, error_message, traceback_str):
    """Log failure information to ClearML"""
    
    logger = task.get_logger()
    
    # Log error details
    logger.error(error_message)
    logger.error(traceback_str)
    
    # Upload error log as artifact
    task.upload_artifact(
        name="error_log",
        artifact_object=traceback_str
    )
    
    # Close task with failed status
    task.close(status=Task.TaskStatus.failed)
```

---

## Selective Logging Strategy

### What to Log to ClearML

**DO log**:
- ✅ Epoch metrics (mAP, loss, etc.)
- ✅ Hyperparameters and configuration
- ✅ Training duration and timing
- ✅ Comparison results (CI training)
- ✅ Decision rationale
- ✅ Error messages and tracebacks
- ✅ Model metadata (size, seed, training type)

**DON'T log**:
- ❌ Complete training dataset
- ❌ All training checkpoints (too large)
- ❌ Raw image data
- ❌ Intermediate training outputs
- ❌ Large video files

### Rationale

ClearML storage is designed for **metadata and small artifacts**, not massive data. The shared storage is the source of truth for large artifacts.

```python
# GOOD: Log summary
task.upload_artifact(
    name="training_summary",
    artifact_object={
        'total_epochs': 100,
        'best_mAP50': 0.85,
        'training_time_hours': 2.5
    }
)

# BAD: Don't log full training data
# task.upload_artifact(
#     name="training_dataset",
#     artifact_object=full_dataset  # Could be GBs!
# )
```

---

## Experiment Comparison

### Query Tasks in ClearML

```python
from clearml import Task

def find_training_tasks():
    """Query all training tasks"""
    
    tasks = Task.get_tasks(
        project_name="AI_Orchestration_Project",
        task_type="training",
        status="completed"
    )
    
    for task in tasks:
        print(f"Task: {task.name}")
        print(f"  Params: {task.get_configuration()}")
        print(f"  Status: {task.get_status()}")
        print(f"  Metrics: {task.get_last_scalar_metric_events()}")
```

### ClearML UI for Comparison

- View side-by-side metrics charts
- Compare hyperparameters across runs
- Track model lineage and evolution
- Debug failed runs with full logs

---

## Model Lineage and Versioning

### Track Model Provenance

```python
def log_model_lineage(task, model_info):
    """Log model lineage information"""
    
    task.connect_configuration(
        configuration_dict={
            'base_model': 'yolov8s_pretrained',
            'training_type': model_info.get('training_type'),  # 'initial' or 'ci'
            'previous_model_info': model_info.get('previous_model'),
            'dataset_version': 'DATASET_V1_PLACEHOLDER'
        },
        name="model_lineage"
    )
```

### Version Tracking

```python
# Each model stored with metadata including:
# - Training task ID (ClearML)
# - Hyperparameters
# - Performance metrics
# - Training timestamp
# - Seed (if multi-seed training)
# - Previous model it was trained from (if CI training)

# Enables reconstruction of model history:
# Model 1 (seed 42) → Model 2 (seed 123) → Model 3 (seed 456)
#         ↓                  ↓
#      mAP50: 0.82      mAP50: 0.85 (best)
```

---

## Failure Isolation and Debugging

### Log Debug Information

```python
def log_debug_context(task, context_dict):
    """Log context for debugging failures"""
    
    task.upload_artifact(
        name="debug_context",
        artifact_object={
            'gpu_device': context_dict.get('gpu_device'),
            'cuda_version': context_dict.get('cuda_version'),
            'pytorch_version': context_dict.get('pytorch_version'),
            'system_info': context_dict.get('system_info'),
            'seed': context_dict.get('seed'),
            'dataset_path': 'ANONYMIZED_PATH_PLACEHOLDER'
        }
    )
```

### Isolate Failed Runs

```python
def query_failed_task(task_id):
    """Retrieve failed task details"""
    
    task = Task.get_task(task_id=task_id)
    
    # Get logs
    logs = task.get_task_log()
    
    # Get configuration
    config = task.get_configuration_dict()
    
    # Debug information
    events = task.get_all_events()
    
    return {
        'logs': logs,
        'config': config,
        'events': events,
        'status': task.get_status()
    }
```

---

## ClearML Configuration

### Connection Setup

```python
# Requires ClearML configuration in ~/.clearml/clearml.conf

# Example environment variables:
import os

os.environ['CLEARML_API_HOST'] = 'https://api.clearml.com/'
os.environ['CLEARML_API_ACCESS_KEY'] = 'ACCESS_KEY_PLACEHOLDER'
os.environ['CLEARML_API_SECRET_KEY'] = 'SECRET_KEY_PLACEHOLDER'
os.environ['CLEARML_WEB_HOST'] = 'https://app.clearml.com'
os.environ['CLEARML_FILES_HOST'] = 'https://files.clearml.com'
```

### Project Organization

```
ClearML Projects:
├── AI_Orchestration_Project
│   ├── Training Runs
│   │   ├── training_run_001 (seed 42)
│   │   ├── training_run_002 (seed 123)
│   │   └── training_run_003 (seed 456)
│   ├── CI Training Runs
│   │   ├── ci_training_001 (approved - updated model)
│   │   ├── ci_training_002 (rejected - degradation)
│   │   └── ci_training_003 (approved)
│   └── Inference Runs
│       ├── inference_job_001
│       └── inference_job_002
```

---

## Summary

ClearML integration provides:

✅ Experiment metadata tracking
✅ Per-epoch and final metrics logging
✅ Model metadata registration
✅ Run comparison and analysis
✅ Failure isolation and debugging
✅ Model lineage and provenance
✅ Task status management

**Key Design**: ClearML tracks what happened, shared storage holds what was produced. Separation of concerns enables both reliability and scalability.

---

**Important**: This documentation describes ClearML integration patterns. The private codebase contains actual credentials and workspace configurations that are not included in this repository.
