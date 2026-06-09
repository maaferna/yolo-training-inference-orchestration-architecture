# Component Responsibilities

## Component Ownership Matrix

This document clearly defines what each component is responsible for and what it is NOT responsible for.

## Django Web Application

### IS RESPONSIBLE FOR
- ✅ User interface and request submission
- ✅ User authentication and authorization
- ✅ Input validation at API boundary
- ✅ Request history storage in database
- ✅ Result caching and retrieval from shared storage
- ✅ Visualization of results and artifacts
- ✅ Poll FastAPI for job status
- ✅ Error handling and user-facing error messages
- ✅ Database persistence of user data
- ✅ Session management and CSRF protection
- ✅ Rate limiting and throttling (if implemented)
- ✅ Link generation to artifacts in shared storage

### IS NOT RESPONSIBLE FOR
- ❌ Model training execution
- ❌ GPU computation
- ❌ Inference processing
- ❌ ClearML integration (that's FastAPI's job)
- ❌ Artifact storage in shared volume (just reads from it)
- ❌ CUDA context management
- ❌ Model checkpointing
- ❌ Long-running task execution
- ❌ Experiment tracking or comparison
- ❌ FastAPI service deployment or health
- ❌ Database schema for ML artifacts (only user/request data)

### Key Dependencies
- FastAPI service (HTTP client to /training, /inference, /ci-training endpoints)
- PostgreSQL database (user data, request history)
- Shared storage volume (read access to results)

### Failure Modes and Handling
| Failure | Handling | Responsibility |
|---------|----------|-----------------|
| FastAPI service down | Return 503 error to user | Django |
| Shared storage unavailable | Cached results or error | Django |
| Database connection lost | Return 500 error | Django |
| Invalid request parameters | Return 400 validation error | Django |
| FastAPI timeout | Return 504 error | Django |

---

## FastAPI AI Service

### IS RESPONSIBLE FOR
- ✅ Receive and validate API requests
- ✅ Coordinate YOLO training pipeline
- ✅ Manage CUDA context and GPU resources
- ✅ Initialize ClearML experiments
- ✅ Log metrics to ClearML
- ✅ Handle training errors and fallbacks
- ✅ Load and manage model artifacts
- ✅ Coordinate inference pipeline
- ✅ Write artifacts to shared storage
- ✅ Manage long-running task execution
- ✅ Cleanup resources after job completion
- ✅ Return job status and results to Django

### IS NOT RESPONSIBLE FOR
- ❌ User interface or web rendering
- ❌ User authentication (Django handles this)
- ❌ Request history or audit trail
- ❌ User data persistence
- ❌ ClearML workspace access control (assumes configured)
- ❌ Shared storage volume management (just writes to mount point)
- ❌ Job queue or scheduler (synchronous only)
- ❌ Multi-GPU distributed training coordination
- ❌ Model versioning or registry (file-based only)
- ❌ Performance monitoring or alerting
- ❌ Retry logic with exponential backoff (not implemented)

### Key Dependencies
- YOLO/Ultralytics library (training and inference)
- PyTorch + CUDA (GPU computation)
- ClearML client (experiment tracking)
- SAHI library (high-resolution inference)
- Shared storage volume (artifact read/write)
- PostgreSQL (optional - could log run metadata)

### Failure Modes and Handling
| Failure | Handling | Responsibility |
|---------|----------|-----------------|
| CUDA OOM | Return error, Django client can retry | FastAPI |
| Ultralytics train() returns None | Use manual validation fallback | FastAPI |
| Shared storage path mismatch | Raise error, return to Django | FastAPI |
| DDP initialization failure | Fall back to DataParallel | FastAPI |
| ClearML connection lost | Continue training, log warning | FastAPI |
| Corrupted settings.json | Clear cache, retry | FastAPI |

---

## YOLO Training Engine

### IS RESPONSIBLE FOR
- ✅ Load YOLOv8/v11 model from Ultralytics
- ✅ Execute training with specified parameters
- ✅ Run multi-seed training loops
- ✅ Collect training metrics (loss, mAP, etc.)
- ✅ Perform validation after each epoch
- ✅ Save checkpoints
- ✅ Select best model based on mAP50
- ✅ Log metrics to ClearML
- ✅ Handle training failures gracefully

### IS NOT RESPONSIBLE FOR
- ❌ Data loading or augmentation (Ultralytics handles this)
- ❌ Dataset normalization (Ultralytics handles this)
- ❌ Hyperparameter optimization (HPO)
- ❌ Long-term model registry (FastAPI handles this)
- ❌ Multi-GPU distributed training (evaluated but not implemented)
- ❌ Model interpretation or explainability
- ❌ Performance benchmarking across hardware
- ❌ Automatic learning rate scheduling (Ultralytics default)

### Triggers
- Receives call from FastAPI with training parameters
- Initiated by Django user request for training

### Outputs
- Best model weights (.pt file)
- Training summary (metrics, timing)
- Checkpoints for resumption
- Metrics logged to ClearML

---

## Continuous Improvement Training Pipeline

### IS RESPONSIBLE FOR
- ✅ Load previous best model from shared storage
- ✅ Prepare new training data
- ✅ Execute incremental training on new data
- ✅ Collect new metrics
- ✅ Retrieve historical baseline metrics
- ✅ Compare new vs. baseline performance
- ✅ Decide whether to update best model
- ✅ Update best model reference IF improved
- ✅ Log comparison decision to ClearML
- ✅ Prevent model degradation

### IS NOT RESPONSIBLE FOR
- ❌ Initial baseline model creation (standard training)
- ❌ Data version control
- ❌ Automatic retraining triggers
- ❌ Rollback to previous models (manual process)
- ❌ Multi-model ensemble management
- ❌ A/B testing between model versions
- ❌ Feature engineering or data preprocessing

### Key Decision Logic
```
Load best model: best_model_ref.json
Load historical baseline: metadata or database

Run incremental training on new data
  ↓
Collect new metrics (new_mAP50, etc.)
  ↓
IF new_mAP50 > baseline_mAP50 THEN
  Update best_model_ref.json with new model path
  Log: "Model improved, updating best model"
ELSE
  Keep existing best model
  Log: "Model degraded, keeping current best"
END IF
```

### Failure Modes
| Scenario | Handling |
|----------|----------|
| Previous best model missing | Error: cannot load baseline |
| Baseline metrics unavailable | Error: cannot compare |
| Concurrent CI training runs | RACE CONDITION - file-based registry issue |
| New training fails | Revert to previous best model |
| Metrics comparison ambiguous | Log warning, default to conservative (keep old) |

---

## SAHI Inference Engine

### IS RESPONSIBLE FOR
- ✅ Receive inference request with image
- ✅ Load best model from shared storage
- ✅ Tile/slice large image into chunks
- ✅ Run YOLO inference on each tile
- ✅ Merge detections across tiles
- ✅ Apply NMS (Non-Maximum Suppression)
- ✅ Generate output manifest
- ✅ Store results to shared storage
- ✅ Handle inference failures gracefully

### IS NOT RESPONSIBLE FOR
- ❌ Image preprocessing or normalization (YOLO handles)
- ❌ Image format conversion (assumed valid input)
- ❌ Result filtering or post-processing beyond NMS
- ❌ Generating visualizations (optional feature)
- ❌ Real-time streaming inference
- ❌ Batch inference processing

### Performance Parameters
- Tile size: typically 640 (standard YOLO input)
- Overlap: 50-75% between tiles (for edge detection)
- NMS threshold: 0.5 (typical object detection value)
- Confidence threshold: 0.25 (tunable per request)

### Trade-offs
- **Lower tile size** → More tiles → Slower but catches small objects
- **Higher overlap** → More computation → Better edge detection
- **Lower confidence** → More detections → Potential false positives
- **Higher NMS threshold** → Fewer merged detections → Potential missed objects

---

## ClearML Experiment Tracking Layer

### IS RESPONSIBLE FOR
- ✅ Initialize experiment task at training start
- ✅ Log hyperparameters and configuration
- ✅ Record metrics during training (after each epoch)
- ✅ Register model artifacts
- ✅ Tag experiments with metadata
- ✅ Enable experiment comparison
- ✅ Maintain run history
- ✅ Facilitate debugging of failed runs
- ✅ Provide model lineage tracking

### IS NOT RESPONSIBLE FOR
- ❌ Model storage (local artifacts are source of truth)
- ❌ Experiment scheduling or triggering
- ❌ Automatic hyperparameter optimization (HPO)
- ❌ Data versioning
- ❌ Real-time monitoring infrastructure
- ❌ Multi-tenant workload isolation
- ❌ Cost tracking or resource billing

### Integration Points
```
FastAPI starts training
  ↓
Initialize ClearML task: clearml.Task.init(...)
  ↓
Log hyperparameters: task.connect_configuration(...)
  ↓
[Training loop]
  for epoch in epochs:
    run validation
    log metrics: task.upload_artifact(...) or logger.report_scalar(...)
  end
  ↓
On success:
  Register best model: task.upload_artifact(best_model.pt)
  Close task: task.close()
  
On failure:
  Log error: logger.error(...)
  Close task: task.close()
```

### Selective Logging Strategy
**DO log to ClearML**:
- ✅ Epoch metrics (mAP, precision, recall, loss)
- ✅ Hyperparameters
- ✅ Training configuration
- ✅ Best model metadata
- ✅ Timing information
- ✅ Error messages

**DON'T log to ClearML**:
- ❌ Complete training dataset
- ❌ All checkpoints (too large)
- ❌ Intermediate outputs
- ❌ Raw image data
- ❌ Large video files
- ❌ Credential files or secrets

*Rationale*: ClearML storage is for metadata and model artifacts, not raw data.

---

## Shared Storage Layer

### IS RESPONSIBLE FOR
- ✅ Persist model weights (.pt files)
- ✅ Store best model reference (JSON metadata)
- ✅ Maintain training artifacts (logs, summaries)
- ✅ Store inference results and manifests
- ✅ Provide consistent path access to both services
- ✅ Enable artifact discovery and retrieval

### IS NOT RESPONSIBLE FOR
- ❌ Dataset storage (should be external or preprocessed)
- ❌ Raw training data (should be in database or external)
- ❌ Backup and disaster recovery (infrastructure concern)
- ❌ Data versioning or git-like capabilities
- ❌ Access control (reliant on Docker volume permissions)
- ❌ Replication across sites
- ❌ Long-term archive storage

### Artifact Lifecycle
```
Training Artifacts:
  Created by: FastAPI during training
  Used by: Django for visualization, ClearML for artifact registration
  Lifecycle: Persist until explicitly deleted or superseded

Model Artifacts:
  Created by: YOLO training engine
  Owned by: Model registry (best_model_ref.json)
  Lifecycle: Long-term, backed up, versioned in future

Inference Artifacts:
  Created by: SAHI inference engine
  Used by: Django for result display
  Lifecycle: Medium-term, can be cleaned after viewing
  
CI Training Artifacts:
  Created by: CI pipeline during incremental training
  Used by: Comparison and decision logic
  Lifecycle: Archived for audit trail
```

### Path Consistency Requirements
| Service | Container Path | Volume Mount | Host Path (dev) |
|---------|---|---|---|
| FastAPI | `/app/shared_data/` | `shared_storage:/app/shared_data` | `./shared_storage/` |
| Django | `/data/shared/` | `shared_storage:/data/shared` | `./shared_storage/` |

**Critical**: Both paths must refer to the same volume content!

---

## GPU Compute Layer

### IS RESPONSIBLE FOR
- ✅ Provide CUDA runtime to containers
- ✅ Manage GPU memory allocation
- ✅ Handle CUDA context creation and cleanup
- ✅ Synchronize GPU operations
- ✅ Report GPU memory usage
- ✅ Handle OOM (Out of Memory) errors

### IS NOT RESPONSIBLE FOR
- ❌ CPU scheduling
- ❌ Kernel module management
- ❌ Driver installation (assumed in base image)
- ❌ Multi-GPU resource allocation
- ❌ GPU workload balancing
- ❌ Thermal management

### Memory Management
```
Before training:
  torch.cuda.empty_cache()  # Clear GPU cache
  
During training:
  PyTorch manages allocation
  Monitor: torch.cuda.memory_allocated()
  
After training:
  torch.cuda.empty_cache()  # Critical cleanup
  
If OOM occurs:
  Reduce batch size
  Reduce image size
  Enable gradient accumulation
  Fall back to CPU (not recommended)
```

---

## Docker Runtime Layer

### IS RESPONSIBLE FOR
- ✅ Define container images and configurations
- ✅ Manage container lifecycle (start, stop, health)
- ✅ Configure networking between services
- ✅ Mount volumes for persistence
- ✅ Configure GPU device access
- ✅ Set environment variables
- ✅ Provide health check mechanisms

### IS NOT RESPONSIBLE FOR
- ❌ Service orchestration (no Kubernetes here)
- ❌ Auto-scaling
- ❌ Load balancing
- ❌ Storage volume provisioning (assumed external)
- ❌ Network security (assumed in infrastructure)

### Container Responsibilities
```
Django Container:
  - Expose port 8000
  - Mount /data/shared/ (read/write)
  - No GPU required
  - Start: 2-3 seconds typical
  
FastAPI Container:
  - Expose port 8001
  - Mount /app/shared_data/ (read/write)
  - GPU support enabled
  - Start: 5-10 seconds typical (CUDA init)
  
PostgreSQL Container:
  - Expose port 5432
  - Mount db_data volume
  - No GPU needed
  - Start: 1-2 seconds typical
```

---

## Summary: Responsibility Checklist

**Before modifying a component, verify**:

1. ✓ Does it match the documented responsibility?
2. ✓ Is this responsibility NOT assigned to another component?
3. ✓ Does the change require coordination with other components?
4. ✓ Will the change introduce new dependencies?
5. ✓ Does it increase coupling between services?
6. ✓ Is error handling clear and documented?
7. ✓ Is failure mode handling well-defined?

---

**This responsibility matrix enables clear ownership, easier debugging, and a foundation for future refactoring.**
