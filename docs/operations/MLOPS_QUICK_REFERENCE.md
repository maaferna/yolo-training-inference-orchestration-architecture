# MLOps Quick Reference Guide

**Last Updated**: June 12, 2026  
**For**: Researchers, ML Engineers, DevOps Team  

---

## 🚀 Quick Start: Submit a Training Job

### Via Django Web UI

```
1. Go to http://your-django-ui/train
2. Select model: YOLO-v8, v8, v5
3. Select dataset: COCO, Custom Dataset
4. Set hyperparameters:
   - Learning rate: 0.001
   - Batch size: 32
   - Epochs: 100
5. Click "Submit"
6. Get experiment ID
7. Track in ClearML: https://clearml.app (or localhost:8008 after migration)
```

### Via FastAPI (Programmatic)

```bash
curl -X POST http://fastapi:8080/train \
  -H "Content-Type: application/json" \
  -d '{
    "model": "yolo_v8",
    "dataset": "coco",
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100
  }'

# Response:
{
  "job_id": "abc123",
  "clearml_task_id": "xyz789",
  "clearml_ui_url": "https://clearml.app/tasks/xyz789"
}
```

---

## 📊 Viewing Experiment Results

### In ClearML UI

```
1. Go to https://clearml.app (Cloud)
   or http://localhost:8008 (Self-Hosted)
2. Project: "yolo-training"
3. See all experiments with:
   - Metrics (mAP, precision, recall)
   - Hyperparameters
   - Training time
   - Status (running, completed, failed)
```

### Compare Experiments

```
1. Select 2+ experiments
2. Click "Compare"
3. See side-by-side:
   - Metrics comparison
   - Hyperparameter differences
   - Which is better
```

---

## 🎯 Common Tasks

### Find Best Model from Last Week

```python
from clearml import Task
from datetime import datetime, timedelta

# Query last week
last_week = datetime.now() - timedelta(days=7)
tasks = Task.get_tasks(
    project_name="yolo-training",
    status="completed"
)

# Find best by mAP
best_task = max(
    tasks,
    key=lambda t: t.get_metrics_scalar_latest_values()
        .get('validation', {})
        .get('mAP50', 0)
)

print(f"Best: {best_task.name}")
print(f"mAP50: {best_task.get_metrics_scalar_latest_values()['validation']['mAP50']}")
print(f"Model: {best_task.artifacts['model']['url']}")
```

### Run Model Inference

```bash
curl -X POST http://fastapi:8080/infer \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/data/image.jpg",
    "model_id": "best",
    "confidence_threshold": 0.5
  }'

# Returns:
{
  "detections": [...],
  "inference_time_ms": 45,
  "model_used": "yolo_v8_epoch_100"
}
```

### Reproduce Past Experiment

```python
from clearml import Task

# Find original task
original_task = Task.get_task(task_id="xyz789")

# Clone it
cloned_task = Task.clone_task(
    source_task_id=original_task.id,
    project_name="yolo-training",
    task_name=f"reproduce_{original_task.name}"
)

# Submit for re-execution
cloned_task.execute()
```

---

## 📁 File Locations

```
Project Root: <REPOSITORY_ROOT>/

Key Directories:
├── docs/MLOPS_STATUS_REPORT.md  ← Current status
├── docs/MIGRATION_*             ← Migration guides
├── examples/api-payloads/       ← API request examples
├── examples/docker/             ← Docker configs
└── shared_storage/              ← Shared models & datasets
    ├── models/
    │   ├── best.pt
    │   ├── yolo_v8_*.pt
    │   └── (versioned models)
    └── datasets/
        ├── coco/
        └── custom/
```

---

## 🔧 Configuration

### Environment Variables

```bash
# ClearML Configuration (FastAPI container)
export CLEARML__API__HOST=https://clearml.app  # Cloud
# OR
export CLEARML__API__HOST=http://localhost:8008  # Self-Hosted

export CLEARML__API__ACCESS_KEY=your_key
export CLEARML__API__SECRET_KEY=your_secret

# Training Configuration
export BATCH_SIZE=32
export LEARNING_RATE=0.001
export MAX_EPOCHS=100
export DEVICE=cuda:0
```

### ClearML API Keys

```bash
# Get from: https://clearml.app/settings/workspace
# or: http://localhost:8008/settings/workspace (self-hosted)

# Save to ~/.clearml/clearml.conf
```

---

## 🚨 Troubleshooting

### "Cannot connect to ClearML"

```bash
# Test connection
python -c "from clearml import Task; t = Task.init('test', 'test')"

# If fails:
# 1. Check API host
echo $CLEARML__API__HOST

# 2. Check credentials
cat ~/.clearml/clearml.conf

# 3. Check network
curl $CLEARML__API__HOST/version

# 4. Check server running (if self-hosted)
curl http://localhost:8008/version
```

### Training Job Hanging

```bash
# Check job logs
docker logs training_worker_abc123

# Check ClearML task status
python -c "
from clearml import Task
t = Task.get_task('xyz789')
print(f'Status: {t.status}')
print(f'Last update: {t.last_update}')
"

# If stuck, cancel and retry
python -c "
from clearml import Task
t = Task.get_task('xyz789')
t.close(status='closed')
"
```

### Out of Memory

```bash
# Reduce batch size
export BATCH_SIZE=16

# Or check what's running
nvidia-smi

# Kill zombie processes
pkill -f training_worker
```

---

## 📚 Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Migration Guide | Cloud → Self-Hosted | docs/MIGRATION_* |
| MLOps Status | Current project status | docs/MLOPS_STATUS_REPORT |
| This Guide | Quick reference | (this file) |

---

## 🔗 Useful Links

### ClearML Cloud
- Dashboard: https://clearml.app
- Docs: https://clear.ml/docs/
- Settings: https://clearml.app/settings/workspace

### Self-Hosted (After Migration)
- Dashboard: http://localhost:8008
- API: http://localhost:8008/v2.23/tasks
- Status: http://localhost:8008/version

### Project Resources
- Django UI: http://your-domain/
- FastAPI Docs: http://fastapi-service:8080/docs
- Shared Storage: /shared_storage/

---

## ✅ Pre-Experiment Checklist

Before submitting a training job:

- [ ] Dataset prepared and validated
- [ ] Hyperparameters reasonable (not extreme)
- [ ] ClearML connection working: `curl $CLEARML__API__HOST/version`
- [ ] Storage space available: `df -h /shared_storage`
- [ ] GPU available: `nvidia-smi`
- [ ] Task name descriptive and unique
- [ ] Know where to find logs: ClearML UI

---

## 📞 Support

**Question**: Check `docs/architecture/` for design documentation  
**Bug**: Report in GitHub issues  
**Access**: Contact MLOps team for ClearML credentials  
**Performance**: Check MLOPS_STATUS_REPORT.md metrics  

---

## Version Info

- **Last Updated**: June 12, 2026
- **ClearML Cloud Version**: Latest
- **ClearML Self-Hosted Target**: 1.6+
- **FastAPI**: 0.68+
- **Django**: 3.2+

