# Shared Storage and Artifacts

This document details the shared storage architecture, artifact categories, path mapping, and risks.

## Shared Storage Purpose

The shared storage layer serves as the **single source of truth** for all artifacts generated during training and inference. It enables:

1. **Data Persistence** - Artifacts survive container restarts
2. **Service Decoupling** - Django and FastAPI can access artifacts independently
3. **Asynchronous Updates** - FastAPI writes, Django reads at its own pace
4. **Artifact Versioning** - Historical artifacts retained for debugging
5. **Model Registry** - Central location for model management (file-based)

---

## Artifact Categories

### 1. Model Weights

**Location**: `/shared_storage/models/`

**Files**:
```
best.pt                    # Current best model weights (only one file)
best_model_ref.json        # Metadata reference file
```

**Size**: Typically 50-200 MB per model (varies by model size)

**Lifecycle**: 
- Created: During training after best model selection
- Updated: Only when CI training improves performance
- Backed up: Implicitly (keep version history in future)
- Cleaned: Manually or by retention policy

**Format**:
- `.pt` files are PyTorch model checkpoints
- Loadable with: `model = YOLO('/shared_storage/models/best.pt')`
- Contains model weights, architecture, and metadata

---

### 2. Training Checkpoints

**Location**: `/shared_storage/models/checkpoints/`

**Files**:
```
seed_42_epoch_50.pt
seed_42_epoch_100.pt
seed_123_epoch_50.pt
seed_123_epoch_100.pt
seed_456_epoch_50.pt
seed_456_epoch_100.pt
```

**Size**: 50-200 MB each (accumulated over training)

**Lifecycle**:
- Created: During multi-seed training (every N epochs)
- Used: For training resumption or debugging
- Cleaned: Keep latest 2 epochs per seed, delete older
- Archived: Before training new model

**Rationale**: 
- Enable training resumption if interrupted
- Debug intermediate model states
- Compare performance across epochs

---

### 3. Training Summaries

**Location**: `/shared_storage/training/run_{RUN_ID}/`

**Files**:
```
summary.json               # Overall training summary
metrics.csv                # Per-epoch metrics table
training_config.json       # Hyperparameters and settings
logs.txt                   # Training output logs
```

**Summary Content**:
```json
{
  "run_id": "run_001",
  "timestamp": "2026-06-09T10:30:00Z",
  "model_size": "s",
  "total_epochs": 100,
  "num_seeds": 3,
  "best_seed": 42,
  "best_mAP50": 0.85,
  "training_time_seconds": 3600,
  "final_epoch_mAP50": 0.83,
  "final_epoch_precision": 0.88,
  "final_epoch_recall": 0.82,
  "clearml_task_id": "task_123456"
}
```

**Metrics CSV**:
```csv
epoch,train_loss,val_loss,mAP50,mAP75,precision,recall
1,0.5234,0.4821,0.34,0.22,0.65,0.58
2,0.4891,0.4456,0.51,0.35,0.72,0.65
...
100,0.2156,0.2145,0.85,0.78,0.88,0.82
```

**Size**: CSV typically 10-50 KB, JSON summaries 1-5 KB

**Lifecycle**:
- Created: During training after each epoch
- Accessed: For result visualization and analysis
- Retained: Indefinitely (small size)
- Compared: Across runs to assess improvement

---

### 4. Best Model Reference

**Location**: `/shared_storage/models/best_model_ref.json`

**Critical Metadata**:
```json
{
  "model_path": "/shared_storage/models/best.pt",
  "mAP50": 0.85,
  "mAP75": 0.78,
  "precision": 0.88,
  "recall": 0.82,
  "seed": 42,
  "epochs_trained": 100,
  "model_size": "s",
  "training_timestamp": "2026-06-09T10:30:00Z",
  "last_updated": "2026-06-09T12:00:00Z",
  "training_type": "initial",
  "clearml_task_id": "task_123456",
  "dataset_yaml": "datasets/PROJECT_PLACEHOLDER/data.yaml"
}
```

**Purpose**: 
- Single source of truth for which model is "best"
- Used by inference pipeline to load correct model
- Used by CI training for baseline comparison
- Enables quick model switching without searching

**Access Pattern**:
```python
# Load reference
import json
with open('/shared_storage/models/best_model_ref.json') as f:
    ref = json.load(f)

# Use to load model
from ultralytics import YOLO
model = YOLO(ref['model_path'])
baseline_mAP50 = ref['mAP50']
```

**Risk**: File-based registry susceptible to race conditions (see risks section)

---

### 5. Inference Outputs

**Location**: `/shared_storage/inference/job_{JOB_ID}/`

**Files**:
```
output_manifest.json       # Detection results and metadata
detections.csv             # Tabular format of detections
preview.png                # Visualization of detections (optional)
```

**Manifest Content**:
```json
{
  "job_id": "inf_12345",
  "timestamp": "2026-06-09T11:30:00Z",
  "image_shape": [3072, 4096, 3],
  "image_hash": "sha256_hash_placeholder",
  "model_used": "/shared_storage/models/best.pt",
  "inference_config": {
    "tile_size": 640,
    "tile_overlap": 0.5,
    "confidence_threshold": 0.25,
    "nms_threshold": 0.5
  },
  "num_detections": 245,
  "inference_time_seconds": 12.5,
  "detections": [
    {
      "id": 0,
      "bbox": [100, 150, 200, 300],
      "confidence": 0.92,
      "class_id": 0,
      "class_name": "object_placeholder",
      "source_tile": "tile_3_4"
    },
    {
      "id": 1,
      "bbox": [400, 500, 550, 700],
      "confidence": 0.88,
      "class_id": 1,
      "class_name": "object_placeholder",
      "source_tile": "tile_5_6"
    }
  ]
}
```

**CSV Format**:
```csv
detection_id,class_id,class_name,bbox_x1,bbox_y1,bbox_x2,bbox_y2,confidence,source_tile
0,0,object_placeholder,100,150,200,300,0.92,tile_3_4
1,1,object_placeholder,400,500,550,700,0.88,tile_5_6
...
```

**Size**: JSON typically 100 KB - 5 MB (depends on detection count)

**Lifecycle**:
- Created: During inference processing
- Accessed: For result visualization and download
- Retained: Medium-term (can be cleaned after viewing)
- Archived: For audit trail if needed

---

### 6. CI Training Artifacts

**Location**: `/shared_storage/ci_training/run_{RUN_ID}/`

**Files**:
```
comparison.json            # Baseline vs. new metrics comparison
decision.log               # Update decision and reasoning
new_model_experimental.pt  # Experimental new model (not best)
```

**Comparison Content**:
```json
{
  "run_id": "ci_train_001",
  "timestamp": "2026-06-09T11:00:00Z",
  "baseline": {
    "mAP50": 0.85,
    "precision": 0.88,
    "recall": 0.82,
    "timestamp": "2026-06-09T10:30:00Z"
  },
  "new_metrics": {
    "mAP50": 0.87,
    "precision": 0.89,
    "recall": 0.84,
    "timestamp": "2026-06-09T11:00:00Z"
  },
  "improvement": {
    "mAP50_absolute": 0.02,
    "mAP50_percentage": 2.35,
    "improvement_threshold": 0.01
  },
  "decision": "APPROVED",
  "decision_reason": "Model improved by 2.35%, exceeds 1.0% threshold"
}
```

**Decision Log**:
```
2026-06-09 11:00:00 - CI Training Started
2026-06-09 11:15:00 - Loading baseline: best_model_ref.json
2026-06-09 11:15:02 - Baseline mAP50: 0.85
2026-06-09 11:15:05 - Loading new data from datasets/NEW_DATA_PLACEHOLDER/
2026-06-09 11:30:00 - Training completed
2026-06-09 11:30:05 - New metrics: mAP50=0.87
2026-06-09 11:30:10 - Improvement: 0.02 (+2.35%)
2026-06-09 11:30:15 - Decision: APPROVED - Updating best_model_ref.json
2026-06-09 11:30:20 - CI Training Completed Successfully
```

**Size**: JSON 1-5 KB, decision log 1-10 KB

**Lifecycle**:
- Created: During CI training execution
- Accessed: For audit trail and debugging
- Retained: Indefinitely (small size)
- Compared: To track model improvement over time

---

### 7. Error Logs

**Location**: `/shared_storage/errors/`

**Files**:
```
error_20260609_103000.log  # Training failure logs
error_20260609_110500.log  # Inference failure logs
```

**Content**:
```
2026-06-09 10:30:00 - ERROR - CUDA out of memory error
2026-06-09 10:30:01 - Traceback (most recent call last):
  File "training.py", line 45, in run_training
    model.train(...)
RuntimeError: CUDA out of memory. Tried to allocate 1.23 GiB

2026-06-09 10:30:02 - Recovery: Reducing batch size from 32 to 16
2026-06-09 10:30:03 - Retrying training with reduced parameters
2026-06-09 10:31:00 - Training completed successfully after retry
```

**Size**: 1-100 KB each (depends on error detail)

**Lifecycle**:
- Created: When exceptions occur
- Accessed: For debugging failures
- Retained: Medium-term (can implement rotation)
- Cleaned: Periodically (keep last 30 days)

---

## Path Mapping Between Services

### Critical Requirement: Volume Consistency

```
Docker Compose Configuration:

volumes:
  shared_storage:
    driver: local

services:
  django:
    volumes:
      - shared_storage:/data/shared/

  fastapi:
    volumes:
      - shared_storage:/app/shared_data/
```

### Path Translation Table

| Logical Path | FastAPI Container | Django Container | Shared Volume |
|---|---|---|---|
| `best_model` | `/app/shared_data/models/best.pt` | `/data/shared/models/best.pt` | `shared_storage/models/best.pt` |
| `training_summary` | `/app/shared_data/training/run_001/summary.json` | `/data/shared/training/run_001/summary.json` | `shared_storage/training/run_001/summary.json` |
| `inference_output` | `/app/shared_data/inference/job_001/manifest.json` | `/data/shared/inference/job_001/manifest.json` | `shared_storage/inference/job_001/manifest.json` |

### Implementation Pattern

**FastAPI Side**:
```python
import os
from pathlib import Path

SHARED_STORAGE_PATH = os.getenv('SHARED_STORAGE_PATH', '/app/shared_data/')

# Save model
model_path = Path(SHARED_STORAGE_PATH) / 'models' / 'best.pt'
model.save(model_path)

# Load reference
ref_path = Path(SHARED_STORAGE_PATH) / 'models' / 'best_model_ref.json'
with open(ref_path) as f:
    ref = json.load(f)
```

**Django Side**:
```python
import os
from pathlib import Path

SHARED_STORAGE_PATH = '/data/shared/'

# Read results
manifest_path = Path(SHARED_STORAGE_PATH) / 'inference' / job_id / 'output_manifest.json'
with open(manifest_path) as f:
    results = json.load(f)
```

---

## Risks of File-Based Architecture

### Risk 1: Path Mismatch

**Problem**: Containers mount different volumes due to configuration error

**Symptom**: FastAPI can't find files written by earlier runs; Django can't read files written by FastAPI

**Example**:
```
FastAPI: /app/shared_data/ → volume A
Django: /data/shared/ → volume B (WRONG!)

Result: Files are in volume A, but Django looks in volume B
```

**Prevention**:
- ✓ Double-check docker-compose YAML before running
- ✓ Implement startup verification script
- ✓ Log mount paths and validate they're consistent
- ✓ Use Docker named volumes (not bind mounts in production)

**Verification Test**:
```bash
# Inside FastAPI container
docker exec fastapi bash -c "echo test > /app/shared_data/test.txt"

# Inside Django container
docker exec django cat /data/shared/test.txt
# Should output: test
```

---

### Risk 2: Race Condition in Best Model Registry

**Problem**: Concurrent CI training runs can corrupt best_model_ref.json

**Scenario**:
```
CI Training A:                    CI Training B:
Read best_model_ref.json
  mAP50 = 0.85
                                  Read best_model_ref.json
                                    mAP50 = 0.85
                                  Complete training
                                    new_mAP50 = 0.84 (worse)
Complete training                 
  new_mAP50 = 0.86 (better)
Write best_model_ref.json ─┐
  with 0.86                 ├─→ Last write wins!
                           │
                       Write best_model_ref.json
                         with 0.84 (OVERWRITES!)

Result: Best model is degraded to 0.84
```

**Prevention**:
- ✓ Serialize CI training jobs (one at a time)
- ✓ Use atomic file operations (write to tmp, then move)
- ✓ Implement file locking mechanism
- ✓ Move to database-based registry (future improvement)

**Atomic Write Pattern**:
```python
import json
import tempfile
import shutil
from pathlib import Path

def write_best_model_ref_atomic(ref_data, path):
    # Write to temporary file
    path = Path(path)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=path.parent,
        delete=False,
        suffix='.json'
    ) as tmp:
        json.dump(ref_data, tmp)
        tmp_name = tmp.name
    
    # Atomic rename (no race condition)
    shutil.move(tmp_name, path)
```

---

### Risk 3: Stale Data / Caching Issues

**Problem**: Django reads old version of file due to filesystem caching

**Symptom**: Django displays outdated metrics even though FastAPI updated them

**Prevention**:
- ✓ Use cache-busting headers in responses
- ✓ Always include timestamp in JSON
- ✓ Implement ETags or version numbers
- ✓ Add fsync() after critical writes

**Critical Write Pattern**:
```python
import json

def write_with_sync(data, path):
    with open(path, 'w') as f:
        json.dump(data, f)
        f.flush()           # Flush to buffer
        os.fsync(f.fileno())  # Force write to disk
```

---

### Risk 4: Permission Denied Errors

**Problem**: Container user lacks write permissions to shared volume

**Symptom**: `PermissionError: [Errno 13] Permission denied`

**Prevention**:
- ✓ Ensure volume is owned by container user (uid 1000 typical)
- ✓ Use chmod 755 for directories, 644 for files
- ✓ Avoid root-owned volumes
- ✓ Test permissions before committing

**Check**:
```bash
docker exec fastapi ls -ld /app/shared_data/
# Output should show: drwxr-xr-x or similar (not 000)
```

---

### Risk 5: Disk Space Exhaustion

**Problem**: Artifacts accumulate and fill shared volume

**Symptom**: `No space left on device` error

**Prevention**:
- ✓ Implement cleanup policies (rotate old logs)
- ✓ Archive old training runs
- ✓ Delete inference outputs after viewing
- ✓ Monitor disk usage

**Cleanup Strategy**:
```python
import os
from datetime import datetime, timedelta

def cleanup_old_artifacts(base_path, max_age_days=30):
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    
    for artifact_dir in Path(base_path).glob('*/*'):
        mtime = datetime.fromtimestamp(
            os.path.getmtime(artifact_dir)
        )
        if mtime < cutoff_time:
            shutil.rmtree(artifact_dir)
```

---

### Risk 6: Hardcoded Paths Reduce Portability

**Problem**: Code contains hardcoded paths like `/app/shared_data/`

**Symptom**: Can't run in different environments with different mount paths

**Prevention**:
- ✓ Use environment variables for all paths
- ✓ Centralize path configuration
- ✓ Support path prefixes for flexibility

**Good Pattern**:
```python
# config.py
SHARED_STORAGE_PATH = os.getenv(
    'SHARED_STORAGE_PATH',
    '/app/shared_data/'  # default, can override
)

# training.py
from config import SHARED_STORAGE_PATH
model_path = Path(SHARED_STORAGE_PATH) / 'models' / 'best.pt'
```

---

## Future Storage Evolution

### Current: File-Based Registry
- ✓ Simple to implement
- ❌ Race conditions possible
- ❌ Limited querying capability
- ❌ Hard to track lineage

### Recommended Phase 1: Atomic Writes
- ✓ Fix race conditions
- ✓ Low complexity
- ❌ Still file-based
- Estimated effort: 1-2 days

### Recommended Phase 2: Database Registry
- ✓ ACID transactions
- ✓ Rich querying
- ✓ Model lineage tracking
- ✓ Audit trail
- Estimated effort: 3-5 days
- Storage: PostgreSQL table

### Recommended Phase 3: Object Storage
- ✓ Scalable (S3, GCS, MinIO)
- ✓ Built-in versioning
- ✓ Lifecycle policies
- Estimated effort: 1-2 weeks
- Considerations: Network latency, API calls

### Schema for Future Database Registry

```sql
CREATE TABLE model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_path VARCHAR(255) NOT NULL,
    metrics JSONB NOT NULL,  -- {mAP50: 0.85, ...}
    model_size VARCHAR(10),
    training_type VARCHAR(20),  -- 'initial' or 'ci'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_best BOOLEAN DEFAULT FALSE,
    clearml_task_id VARCHAR(255),
    UNIQUE(model_name, is_best)  -- Only one "best" per model name
);

CREATE TABLE inference_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    model_id INTEGER REFERENCES model_registry(id),
    image_hash VARCHAR(255),
    num_detections INTEGER,
    inference_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

**Shared storage is the bridge between stateless services. Well-designed artifact management is critical for system reliability and future scalability.**
