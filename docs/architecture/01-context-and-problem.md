# Context and Problem Statement

## Business Context

This system was designed to integrate a web administration layer with a GPU-intensive AI processing service for training and inference of YOLO object detection models on high-resolution images.

### Core Technical ProblemModel references become inconsistent	Add database-backed model registry or transactional reference tracking.

The fundamental challenge: implement a unified orchestration system capable of:
- Training YOLOv8/v11 models with multi-seed statistical rigor
- Automatic model selection based on validation metrics  
- Continuous improvement training with baseline comparison
- High-resolution inference without losing small-object detection
- Full experiment tracking and model versioning
- Seamless data exchange between web application and GPU compute layers

## Primary Technical Challenges

1. **Training at Scale**
   - Coordinating multi-seed training runs for statistical significance
   - Selecting best-performing models from multiple experiments
   - Managing GPU memory and computation time

2. **Continuous Improvement**
   - Loading and incrementally training on new data
   - Comparing against historical baselines
   - Preventing model degradation with conditional updates

3. **High-Resolution Inference**
   - Standard inference fails on large images (e.g., > 1024 pixels)
   - Small-object detection requires specialized approaches
   - Result tiling and merging introduces complexity

4. **Experiment Management**
   - Tracking which model came from which run
   - Isolating failed experiments
   - Comparing metrics across runs
   - Maintaining model lineage for debugging

5. **Resource Orchestration**
   - GPU memory constraints
   - Multiple services competing for CUDA resources
   - Synchronization between training and inference pipelines

6. **Multi-Service Integration**
   - Web layer (Django) needs to submit and view results
   - AI layer (FastAPI) performs compute-intensive tasks
   - Shared storage synchronization
   - Asynchronous long-running operations

7. **Django-Based YOLO Configuration Management**
   - Centralizing YOLO dataset configuration (train/val/test paths, class definitions)
   - Managing dataset metadata through Django ORM models (ProjectConfiguration, ClassSet, DetectionClass)
   - Automatically generating YAML configuration files for Ultralytics
   - Coordinating configuration between web UI and FastAPI training service
   - Handling Docker path mapping between host and container environments
   - Synchronizing custom class definitions across multiple training scenarios

## Why This Architecture?

### Microservice Separation

The separation of Django (web) and FastAPI (AI service) provides:

- **Technology independence**: Choose the right tool for each domain
- **Resource isolation**: Web requests don't compete with GPU compute
- **Scalability path**: Each service can scale independently
- **Clear contracts**: Well-defined API boundaries

### Container Runtime (Docker)

Containerization enables:

- **Reproducibility**: Same environment across development and deployment
- **GPU access**: nvidia-docker provides CUDA access to containers
- **Service orchestration**: Docker Compose simplifies local development
- **Future Kubernetes path**: Easy migration to container orchestration

### ClearML Integration

Experiment tracking solves:

- **Reproducibility**: Every run is recorded and comparable
- **Debugging**: Failed runs can be analyzed in isolation
- **Model lineage**: Understanding model provenance and changes
- **Metric comparison**: Side-by-side evaluation of experiments

### Shared Storage

A common filesystem layer enables:

- **Artifact persistence**: Models, checkpoints, results
- **Lazy loading**: Django reads results without duplicating data
- **Path-based references**: Simple artifact discovery (though with risks)
- **Checkpoint management**: Training resumption and validation
- **Generated Configuration**: YAML files created by Django-based configuration layer

### Django Configuration Layer

Centralizing YOLO training configuration through Django ORM models provides:

- **Single source of truth**: Dataset paths, class definitions, project metadata in database
- **Automated YAML generation**: DatasetConfig model generates Ultralytics-compatible configuration
- **Reusability**: ClassSet enables class definition reuse across multiple projects
- **Web UI integration**: Bootstrap-based UI for managing projects, class sets, and configurations
- **Docker coordination**: Environment-aware path mapping between host and container filesystems

For detailed architecture of the Django configuration layer, see [**docs/08-yolo-dataset-configuration-management.md**](./08-yolo-dataset-configuration-management.md).

## Key Design Decisions

### Decision 1: Synchronous Training Pipeline

**Choice**: Long-running training tasks execute synchronously through FastAPI

**Rationale**:
- Initial validation of concept
- Simple request/response semantics
- No message queue complexity
- GPU cost per task is high (time is money)

**Trade-off**:
- Limited concurrency
- Single service becomes bottleneck
- Client must maintain connection

### Decision 2: File-Based Model Registry

**Choice**: Best model reference stored as JSON file in shared volume

**Rationale**:
- Simple to implement
- Direct file system access from both services
- No separate registry service needed
- Easy to inspect and debug

**Trade-off**:
- Race condition risk in CI training
- No transactions or ACID guarantees
- Coupling to shared filesystem
- Path management complexity

### Decision 3: Multi-Seed Training with mAP50 Selection

**Choice**: Train multiple models with random seeds, select based on mAP50 metric

**Rationale**:
- Reduces variance from random initialization
- mAP50 is standard object detection metric
- Provides statistical confidence in model selection
- Justifies GPU compute investment

**Trade-off**:
- Increases training time (3-5x typical)
- Higher GPU memory requirements
- More complex result aggregation

### Decision 4: SAHI for High-Resolution Inference

**Choice**: Use SAHI (Sliced Aided Hyper Inference) for inference on large images

**Rationale**:
- Standard YOLO inference fails on high-resolution images
- Small objects often lost in downsampling
- SAHI provides transparent slicing/merging
- Ultralytics official recommendation

**Trade-off**:
- Additional inference latency (tiling overhead)
- Complex post-processing (NMS across tiles)
- More memory during inference

## System Constraints and Assumptions

### GPU Constraints
- Single GPU per training run
- Limited CUDA memory (e.g., 24GB)
- CUDA context management required
- Memory cleanup between runs essential

### Storage Assumptions
- Shared volume always available
- Consistent path mapping between services
- Local filesystem fast enough for I/O
- No concurrent writes to same artifact

### Training Assumptions
- YOLOv8/v11 stable with multi-seed training
- Ultralytics API provides reliable train() and val() methods
- mAP50 suitable as primary metric
- Model validation always runs after training

### Service Assumptions
- Django and FastAPI services healthy and responsive
- Database always available
- No network partitions between services
- Volume mounts correctly specified in Docker

## Success Criteria

This architecture successfully addresses:

✅ **Multi-experiment tracking** - All runs recorded in ClearML
✅ **Model selection** - Automated selection based on mAP50
✅ **Continuous improvement** - Incremental training pipeline functional
✅ **High-resolution inference** - SAHI-based detection works on large images
✅ **GPU efficiency** - Shared GPU resource pool
✅ **Result persistence** - Artifacts available to web layer
✅ **Error isolation** - Failed runs don't crash entire system
✅ **Architecture documentation** - This repository demonstrates understanding

## Known Limitations

❌ **Not production-ready** for high-throughput or multi-tenant scenarios
❌ **No formal job queue** (blocking bottleneck exists)
❌ **File-based registry** (race conditions possible)
❌ **Limited observability** (logs but no structured tracing)
❌ **Synchronous tasks** (no async job execution)
❌ **Single service bottleneck** (GPU device is constrained)

## Evolution Path

This architecture establishes the foundation for future improvements:

1. **Phase 1: Job Queue** - Add Celery + Redis for async task execution
2. **Phase 2: Distributed Workers** - Multiple GPU-backed FastAPI instances
3. **Phase 3: Model Registry** - Database-backed transactional registry
4. **Phase 4: Object Storage** - S3-based artifact management
5. **Phase 5: Observability** - Distributed tracing and structured logging

---

**This repository documents this architecture for portfolio and reference purposes, without exposing the private production implementation.**
