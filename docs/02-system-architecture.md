# System Architecture

## Architecture Overview

This document describes the complete system architecture including all layers, components, and their relationships.

```
┌──────────────────────────────────────────────────────────────────┐
│                     DJANGO WEB APPLICATION                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • Request Submission UI                                    │  │
│  │ • Result Visualization & Dashboard                         │  │
│  │ • User Authentication & Authorization                      │  │
│  │ • Result History & Artifact Browsing                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  PostgreSQL Database: User data, request history, result refs    │
└──────┬───────────────────────────────────────────────────────────┘
       │
       │ HTTP/REST API
       │ (JSON payloads)
       │
┌──────▼───────────────────────────────────────────────────────────┐
│              FASTAPI AI ORCHESTRATION SERVICE                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ API Endpoints & Request Validation                        │  │
│  │ • /training (POST) - Submit training job                  │  │
│  │ • /ci-training (POST) - Continuous improvement            │  │
│  │ • /inference (POST) - Run SAHI inference                  │  │
│  │ • /status/{job_id} (GET) - Check job status              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ YOLO TRAINING ENGINE                                       │  │
│  │ • Multi-seed training with random initialization           │  │
│  │ • Validation & metrics collection                          │  │
│  │ • Best model selection based on mAP50                      │  │
│  │ • Checkpoint management                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CONTINUOUS IMPROVEMENT TRAINING PIPELINE                   │  │
│  │ • Load previous best model                                 │  │
│  │ • Incremental training on new data                         │  │
│  │ • Baseline comparison (historical performance)             │  │
│  │ • Conditional best model update (only if improved)         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ SAHI INFERENCE ENGINE                                      │  │
│  │ • High-resolution image tiling (slicing)                   │  │
│  │ • Per-tile YOLO inference                                  │  │
│  │ • Detection merging & deduplication                        │  │
│  │ • Output artifact generation                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CLEARML EXPERIMENT TRACKING LAYER                          │  │
│  │ • Experiment initialization & metadata                     │  │
│  │ • Metrics logging (precision, recall, mAP, etc.)           │  │
│  │ • Model artifact registration                              │  │
│  │ • Run comparison & lineage tracking                        │  │
│  │ • Failure isolation and debugging logs                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ERROR HANDLING & FALLBACKS                                 │  │
│  │ • Ultralytics train() validation                           │  │
│  │ • Manual validation fallback                               │  │
│  │ • CUDA OOM detection and recovery                          │  │
│  │ • DDP error handling                                       │  │
│  │ • Graceful error responses to Django                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────────┘
       │
       │ Read/Write via mount path
       │ (Artifact files)
       │
┌──────▼───────────────────────────────────────────────────────────┐
│              SHARED STORAGE LAYER (Docker Volume)                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ARTIFACT CATEGORIES:                                       │  │
│  │ • Training checkpoints (epoch-based)                       │  │
│  │ • Best model weights & metadata                            │  │
│  │ • Training summaries & metrics                             │  │
│  │ • Inference outputs & detections                           │  │
│  │ • Preview images & visualizations                          │  │
│  │ • Error logs & traces                                      │  │
│  │ • Path mapping:                                            │  │
│  │   - FastAPI: /app/shared_data/...                          │  │
│  │   - Django: /data/shared/...                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────────┘
       │
       │ CUDA Device Access
       │ (GPU compute)
       │
┌──────▼───────────────────────────────────────────────────────────┐
│                GPU COMPUTE LAYER (NVIDIA CUDA)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • PyTorch/CUDA runtime                                     │  │
│  │ • DataParallel (single GPU)                                │  │
│  │ • DDP (Distributed Data Parallel - evaluated)              │  │
│  │ • Memory management & cleanup                              │  │
│  │ • CUDA context synchronization                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────────┘
       │
       │
┌──────▼───────────────────────────────────────────────────────────┐
│           DOCKER RUNTIME LAYER (Container Orchestration)         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • Django Container (port 8000)                             │  │
│  │   - Image: custom Django app with DRF                      │  │
│  │   - Mounts: /data/shared/ (read/write)                     │  │
│  │                                                             │  │
│  │ • FastAPI Container (port 8001)                            │  │
│  │   - Image: custom FastAPI + PyTorch + CUDA                 │  │
│  │   - GPU support: --gpus all                                │  │
│  │   - Mounts: /app/shared_data/ (read/write)                 │  │
│  │                                                             │  │
│  │ • PostgreSQL Container (port 5432)                         │  │
│  │   - Image: postgres:15-alpine                              │  │
│  │   - Mounts: db_data volume                                 │  │
│  │                                                             │  │
│  │ • Docker Network: ml_network (bridge)                      │  │
│  │ • Shared Volume: shared_storage                            │  │
│  │ • Environment Variables:                                   │  │
│  │   - FASTAPI_URL for Django                                 │  │
│  │   - Database connection strings                            │  │
│  │   - ClearML configuration                                  │  │
│  │   - GPU device selection                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Django Web Application Layer

**Purpose**: Provides user interface and request management

**Responsibilities**:
- Accept training, CI training, and inference requests from users
- Validate input data and parameters
- Submit requests to FastAPI service
- Display results and artifacts to users
- Maintain request history and audit trail
- Provide authentication and authorization
- Cache results for performance

**Key Components**:
- Django REST Framework API endpoints
- View functions for request submission
- Result visualization templates
- User authentication middleware
- PostgreSQL database models
- Task status polling mechanism

**Inputs**:
- User training parameters (dataset, model size, epochs, etc.)
- User inference requests (image upload, inference parameters)
- User query requests (history, results, artifacts)

**Outputs**:
- HTTP responses with job IDs, status, or results
- Links to artifacts in shared storage
- Error messages and validation feedback

### 2. FastAPI AI Orchestration Service Layer

**Purpose**: Orchestrates all AI/ML workflows and coordinates with storage

**Responsibilities**:
- Receive and validate API requests from Django
- Orchestrate training, CI training, and inference pipelines
- Manage GPU resources and CUDA context
- Initialize and manage ClearML experiments
- Coordinate with shared storage
- Handle errors and fallbacks
- Log results and metadata

**Key Components**:
- FastAPI application instance
- Pydantic models for request validation
- Training orchestration logic
- Inference pipeline logic
- ClearML integration layer
- Error handling and recovery
- Result aggregation and storage

**Inputs**:
- REST API requests from Django
- Configuration files (model paths, hyperparameters)
- Training data references
- ClearML credentials and configuration

**Outputs**:
- Training artifacts (checkpoints, best model)
- Inference results and detections
- Experiment metadata to ClearML
- Metrics and performance logs
- Error traces and debugging information

### 3. YOLO Training Engine

**Purpose**: Executes YOLOv8/v11 training with multi-seed experimentation

**Responsibilities**:
- Load base YOLO model (v8s, v8m, v8l, etc.)
- Execute multiple training runs with random seeds
- Collect training and validation metrics
- Select best model based on mAP50
- Store checkpoints and best model
- Handle training failures and recovery

**Key Features**:
- Multi-seed training (e.g., 3-5 seeds for statistical significance)
- Epoch-based training with early stopping
- Validation after each epoch
- mAP50-based model selection
- Checkpoint persistence
- CUDA memory management between runs

**Constraints**:
- Single GPU per training job
- High memory requirements (varies with model size)
- Long training time (varies with dataset and hardware)
- Ultralytics API stability assumption

### 4. Continuous Improvement Training Pipeline

**Purpose**: Enables incremental model improvement with baseline comparison

**Responsibilities**:
- Load previous best model from shared storage
- Prepare new training data
- Execute incremental training
- Compare new metrics against historical baseline
- Decide whether to update best model
- Log comparison results to ClearML
- Update best model reference only if improved

**Key Features**:
- Baseline loading and metric comparison
- Performance improvement threshold checking
- Selective best model updates (prevents degradation)
- ClearML experiment isolation
- Historical metric tracking
- Rollback capability (keep previous best model)

**Constraints**:
- File-based model registry (race condition risk)
- Requires baseline metrics in database or file
- Atomic update mechanism missing
- Potential concurrent CI training conflicts

### 5. SAHI Inference Engine

**Purpose**: Performs high-resolution object detection on large images

**Responsibilities**:
- Receive input image and inference parameters
- Slice/tile image into manageable chunks
- Run YOLO inference on each tile
- Merge and deduplicate detections across tiles
- Apply NMS (Non-Maximum Suppression)
- Generate output manifest with detections
- Store inference results to shared storage

**Key Features**:
- Automatic image tiling based on model input size
- Per-tile confidence threshold
- NMS parameters (IOU threshold, score threshold)
- Detection merging and deduplication
- Output manifest generation
- Performance trade-off: latency vs. accuracy

**Constraints**:
- Inference time proportional to image size
- Memory requirements increase with image resolution
- Tile overlap creates redundant computation
- NMS parameters require tuning

### 6. ClearML Experiment Tracking Layer

**Purpose**: Provides reproducibility, debugging, and model lineage

**Responsibilities**:
- Initialize task/experiment for each training run
- Log hyperparameters and configuration
- Record metrics during training
- Track model artifacts and checkpoints
- Maintain model lineage and versioning
- Enable experiment comparison and analysis
- Isolate failed runs for debugging

**Key Features**:
- Automatic metric logging
- Model artifact registration
- Experiment comparison UI
- Run isolation and failure analysis
- Hyperparameter tracking
- Resource usage monitoring
- Selective logging (avoid logging massive artifacts)

**Integration Points**:
- Initialize task at training start
- Log metrics after each validation step
- Register best model as artifact
- Close task on completion or failure

### 7. Shared Storage Layer

**Purpose**: Persists artifacts and enables data exchange between services

**Responsibilities**:
- Store training checkpoints
- Maintain best model reference (JSON file)
- Store inference outputs and manifests
- Persist training summaries and metrics
- Provide consistent path access to both services
- Manage artifact lifecycle

**Artifact Categories**:
```
/shared_storage/
├── models/
│   ├── best_model.pt           # Latest best model
│   ├── best_model_ref.json     # Metadata reference
│   └── checkpoints/            # Training checkpoints
├── training/
│   ├── run_001/
│   │   ├── summary.json        # Training summary
│   │   ├── metrics.csv         # Epoch metrics
│   │   └── logs.txt            # Training logs
│   └── run_002/
├── inference/
│   ├── job_001/
│   │   ├── output_manifest.json # Detection results
│   │   └── preview.png         # Visualization
│   └── job_002/
└── ci_training/
    ├── run_001/
    │   ├── comparison.json     # Baseline comparison
    │   └── decision.log        # Update decision
```

**Path Mapping Between Services**:
- FastAPI: `/app/shared_data/` (inside container)
- Django: `/data/shared/` (inside container)
- Both mount the same Docker volume: `shared_storage`

**Risks**:
- Path mismatch if volume mounted incorrectly
- Concurrent writes to same artifact (race condition)
- File permissions issues
- Stale data if caching not managed
- Hardcoded paths reduce portability

### 8. GPU Compute Layer

**Purpose**: Provides CUDA acceleration for training and inference

**Responsibilities**:
- Provide CUDA context for PyTorch
- Manage GPU memory allocation
- Coordinate between training runs
- Handle OOM (Out of Memory) errors
- Synchronize CUDA operations
- Clean up GPU memory between jobs

**Key Technologies**:
- NVIDIA CUDA runtime
- PyTorch with CUDA backend
- nvidia-docker for container GPU access
- DataParallel for single GPU (current)
- DDP evaluated for future distributed training

**Memory Management**:
- Pre-allocate GPU memory if possible
- Clear CUDA cache between runs
- Monitor memory usage during execution
- Handle OOM gracefully (reduce batch size or fallback)
- Synchronize before memory cleanup

**Constraints**:
- Single GPU device per training run
- Limited CUDA memory (e.g., 24GB typical)
- Context switching overhead
- No resource sharing between concurrent jobs (currently)

### 9. Docker Runtime Layer

**Purpose**: Provides containerized, reproducible execution environment

**Responsibilities**:
- Define service containers (Django, FastAPI, PostgreSQL)
- Manage container lifecycle
- Configure networking between services
- Mount volumes for shared storage
- Configure GPU access
- Set environment variables
- Provide health checks

**Container Specifications**:

**Django Container**:
- Base image: `python:3.11-slim`
- Dependencies: Django, DRF, psycopg2
- Port mapping: `8000:8000`
- Volume mounts: `/data/shared/` (shared storage)
- Network: `ml_network`
- No GPU required

**FastAPI Container**:
- Base image: `nvidia/cuda:12.1-runtime-ubuntu22.04`
- Dependencies: FastAPI, PyTorch, Ultralytics, SAHI, ClearML
- Port mapping: `8001:8001`
- Volume mounts: `/app/shared_data/` (shared storage)
- GPU support: `--gpus all`
- Network: `ml_network`
- Environment: CUDA_VISIBLE_DEVICES, etc.

**PostgreSQL Container**:
- Base image: `postgres:15-alpine`
- Port mapping: `5432:5432`
- Volume mounts: `db_data` volume
- Network: `ml_network`
- Environment: POSTGRES_PASSWORD, POSTGRES_DB

**Networking**:
- Docker bridge network: `ml_network`
- Service discovery via container names (DNS)
- Django → FastAPI: `http://fastapi:8001`
- Both → PostgreSQL: `postgresql://postgres:5432/mldb`

**Shared Volume**:
- Volume name: `shared_storage`
- Type: `local` (or bind mount for development)
- Mounted in Django: `/data/shared/`
- Mounted in FastAPI: `/app/shared_data/`

**Environment Configuration**:
- `.env` file with:
  - `FASTAPI_URL=http://fastapi:8001`
  - `DATABASE_URL=postgresql://...`
  - `CLEARML_WORKSPACE=...`
  - `CUDA_VISIBLE_DEVICES=0`

---

## Data Flow Summary

### Training Request Flow
```
Django UI (user input)
  ↓
Django REST endpoint (validation)
  ↓
POST /training → FastAPI (validation)
  ↓
Initialize ClearML task
  ↓
YOLO multi-seed training
  ↓
Select best model (mAP50)
  ↓
Write artifacts → Shared Storage
  ↓
ClearML task complete
  ↓
Response → Django → UI
```

### Inference Request Flow
```
Django UI (image upload)
  ↓
Django endpoint → POST /inference to FastAPI
  ↓
Load best model from Shared Storage
  ↓
SAHI tiling + YOLO inference
  ↓
Merge/deduplicate detections
  ↓
Generate output manifest
  ↓
Write to Shared Storage
  ↓
Response with result URL
  ↓
Django reads from Shared Storage
  ↓
Display results to user
```

## Assumptions and Constraints

### Assumptions
✓ PostgreSQL always available and healthy
✓ Shared volume always mounted correctly
✓ CUDA available in FastAPI container
✓ Ultralytics API stable and reliable
✓ ClearML credentials valid and available
✓ Network latency between services acceptable
✓ Disk space sufficient for artifacts

### Constraints
✗ Single GPU per training job (no multi-GPU training)
✗ No distributed training across multiple GPUs
✗ Synchronous training (Django client must wait)
✗ No job queue or task distribution
✗ Shared filesystem coupling
✗ File-based model registry (no transactional safety)
✗ Limited observability (logs only)

---

**This architecture provides a functional foundation for AI/ML orchestration while maintaining clear separation of concerns and a pragmatic path to production evolution.**
