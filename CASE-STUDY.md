# Engineering Case Study: AI Vision Platform Architecture
## From Notebooks to Production-Ready System

> **Published**: June 12, 2026  
> **Audience**: Software architects, ML engineers, system designers  
> **Reading Time**: 35-45 minutes  
> **Format**: Technical case study (no proprietary code or data)  

---

## Executive Summary

This case study documents architectural decisions for an **AI vision platform** that bridges a critical gap: researchers need flexibility for experimentation, but production workloads need reliability and stability. The naive approach—putting GPU work directly in a Django web layer—leads to blocked requests, resource contention, and architectural chaos.

This architecture separates concerns: Django handles web request processing (user requests, authentication, visualization), while FastAPI handles compute dispatch and coordination (GPU-intensive training and inference). The separation enables independent scaling and forces explicit responsibility boundaries.

**What you'll learn**:
- Why microservice separation is worth the operational overhead
- How to dispatch and coordinate GPU resources without over-engineering
- What makes MVP-level architectures pragmatic and scalable to production
- How to design for observability and reproducibility
- When to add complexity vs. when to keep it simple

This is not a deployed production system (hence "MVP-level"). Rather, it's a documented architecture showing how to think about scaling from research notebooks to production systems.

---

## 1. Problem Context & Motivation

### The Initial Situation

Imagine a team managing computer vision research: they have users submitting training requests, researchers iterating on models, and a growing collection of trained artifacts. Initially, everything lived in a Django application:

```
User submits training request
  → Django receives request
    → Django starts YOLO training
      → GUI blocks for 30+ minutes
        → User waits
          → Training completes
            → User sees results
```

This works for 1-2 sequential requests. But as demand grows:

- **Request 2 arrives while Request 1 is training** → Django worker is blocked → Request 2 queues → Users see "500 Server Error" (timeout)
- **Researcher wants to use Jupyter notebook** → They access GPU directly → Training request in Django fails (GPU memory is gone)
- **We want to track experiments** → Where do we store metadata? In Django ORM? That mixes research concerns with web concerns.
- **We need to scale** → Do we buy 10 GPUs for the Django layer? That's expensive and silly (web doesn't need GPU).

### Conflicting Requirements

The problem isn't technical; it's **architectural misalignment**:

| Requirement | Web Users | ML Researchers |
|-------------|-----------|-----------------|
| **Speed** | Fast response (< 1 sec) | Flexibility (iterate quickly) |
| **Reliability** | High uptime (minimal errors) | Best effort (experiments fail) |
| **Resources** | CPU + memory | GPU + memory |
| **Iteration** | Stable code (don't break UI) | Experimental code (try new things) |

Trying to satisfy both in one layer causes both to suffer.

### Why Notebooks Aren't Enough

Jupyter notebooks are fantastic for research:
- Interactive experimentation
- Visual inspection of outputs
- Quick iteration on ideas

But they break at scale:
- **Not concurrent**: One person per notebook, one request at a time
- **Not reproducible**: "I ran this cell 5 times and got different results"
- **Not auditable**: No record of who ran what when
- **Not accessible**: Users can't submit requests through a notebook UI
- **Not reliable**: Kernel crashes lose state

The gap between "notebook works great" and "production needs this model" is huge. This architecture bridges that gap.

### GPU Resources Are Precious

GPUs are expensive ($10-20k per card). Unlike CPU resources (which are cheap and plentiful), GPU resources need to be:
- **Managed carefully** (no wasting compute time)
- **Shared fairly** (if 5 people submit training jobs, all should make progress)
- **Visible** (who is using the GPU? which job? why?)
- **Accountable** (which experiment consumed how much compute?)

This architecture adds visibility and accountability through experiment tracking (ClearML).

---

## 2. Constraints & Trade-offs

### Hard Constraints

**Resource Constraints**:
- Single GPU (not unlimited compute)
- 32-64GB GPU memory (not unlimited)
- 16-32 cores of CPU (shared with Django)
- Storage is local filesystem (not distributed)

**Operational Constraints**:
- Small team running this (not enterprise SRE organization)
- Manual deployment (not full CI/CD pipeline)
- On-premises GPU (not cloud auto-scaling)

**Time Constraints**:
- Need working MVP quickly
- Can't spend 6 months perfecting architecture

### Deliberate Trade-offs

**Synchronous vs. Async**
- **MVP Choice**: Synchronous HTTP requests (simple)
- **Trade-off**: Users wait for training to complete
- **When to change**: When average queue wait time > 30 minutes
- **Rationale**: At MVP scale (~3 concurrent jobs), synchronous is acceptable. Building Celery/RQ adds 40% complexity for 5% of systems at this scale.

**Shared Filesystem vs. Object Storage**
- **MVP Choice**: Shared filesystem (convenient, single node)
- **Trade-off**: Single point of failure; not geo-distributed
- **When to change**: When system spans multiple regions or >50 concurrent jobs
- **Rationale**: S3/object storage adds operational burden; shared filesystem works locally.

**Manual Configuration vs. Automated**
- **MVP Choice**: Manual YAML configs (flexible, researchers control everything)
- **Trade-off**: Configuration can drift; hard to reproduce
- **When to change**: When config errors cause 20%+ of failed jobs
- **Rationale**: ORM-based config generation (discussed in Section 7) provides middle ground: flexible but version-controlled.

**Kubernetes vs. Docker Compose**
- **MVP Choice**: Docker Compose (one machine, simple orchestration)
- **Trade-off**: No auto-scaling, no multi-region failover
- **When to change**: When need multi-region deployment or 99.5% SLA
- **Rationale**: Kubernetes adds massive complexity; local Docker is sufficient for MVP.

---

## 3. Architecture Decision: Why Separate Django & FastAPI?

### The Core Problem

Long-running GPU tasks (training takes 30+ minutes) have fundamentally different characteristics than web requests (users expect < 1 second):

| Characteristic | Web Requests | GPU Training |
|----------------|--------------|---------------|
| Duration | 100ms - 2 seconds | 30 minutes - 2 hours |
| Frequency | Constant (many per second) | Sparse (1-2 per day) |
| Resource | CPU + memory | GPU + memory |
| Failure impact | Refresh page | Lose 2 hours of computation |
| Scaling | Horizontal (add servers) | Vertical (better GPU or more cores) |

**Can a single framework handle both?** Technically yes. But it forces compromises:

- **If we optimize for web**: Django is perfect, but GPU training blocks all other requests
- **If we optimize for GPU**: We add queuing, async handling, which web doesn't need
- **If we try to do both**: We end up with a bloated system that does neither well

### The Decision: Separate Services

Separate web orchestration from compute orchestration:

```
┌─────────────────────────────────────────────────────────┐
│ Users submit requests via web                           │
└────────┬─────────────────────────────────────────────────┘
         │ HTTP
         ▼
    ┌─────────────┐
    │ Django      │ ← Web tier: User auth, request history, UI
    │ (web layer) │ ← Fast, stateless, horizontally scalable
    └──────┬──────┘
           │ HTTP (calls FastAPI when training is needed)
           ▼
    ┌─────────────────────┐
    │ FastAPI             │ ← Compute tier: Orchestration engine
    │ (compute layer)     │ ← Handles long-running tasks
    │                     │ ← Can be scaled independently
    └──────┬──────────────┘
           │ PyTorch (actual GPU work)
           ▼
    ┌─────────────────────┐
    │ GPU + PyTorch       │
    │ (execution layer)   │
    └─────────────────────┘
```

### Why This Works

**1. Independent Scaling**
- If web traffic spikes, add more Django instances (cheap, CPU-only)
- If GPU is saturated, add more GPU capacity (expensive, vertical scaling)
- They don't block each other

**2. Different Operational Requirements**
- Django: restart quickly, stateless, can be load-balanced
- FastAPI: maintains state (which GPU jobs are running), careful about restarts
- Separating them means different restart strategies

**3. Clear Failure Boundaries**
- If Django crashes: Users can't submit requests, but running GPU jobs keep going
- If FastAPI crashes: Running jobs are lost (bad), but users know immediately (good observability)
- If GPU crashes: Both see the failure, but it's obvious which component failed

**4. Research Flexibility**
- Researchers can run Jupyter notebooks against the GPU
- Django users can still submit web-based training requests
- Both are visible via ClearML experiment tracking

**5. Force Responsibility Boundaries**
- Django CANNOT directly train models (it calls FastAPI)
- FastAPI CANNOT manage users (it delegates to Django)
- This clarity prevents architectural chaos

### The Trade-off: Added Complexity

We now manage 2 services instead of 1:

**Operational overhead**:
- Configuration management (each service has its own config)
- Deployment coordination (deploy Django and FastAPI independently? or together?)
- Debugging across service boundaries (is the problem in Django or FastAPI?)
- Shared state complexity (both services read/write to database and storage)

**When you might not want this separation**:
- If you truly only do web serving (no long-running compute) → use Django only
- If you truly only do compute (no user-facing web) → use FastAPI only
- At MVP scale (< 3 concurrent requests) → overhead might not be worth it

**Why it's worth it here**:
- We have both web users AND long-running compute
- Scale will grow (future phases need this separation anyway)
- Separation pays for itself through clarity

---

## 4. Component Design: Each Layer's Responsibility

### 4.1 Web Orchestration Layer (Django)

**What it does**:
- User authentication and session management
- Training/inference request submission and validation
- Request history and result visualization
- REST API for programmatic access

**Why Django**:
- Mature web framework with excellent ORM
- Strong authentication/authorization libraries
- Best-in-class admin panel for data management
- Fast to develop and debug
- Large community and production experience

**What it explicitly does NOT do**:
- Never touches GPU directly
- Never runs training code
- Never manages model artifacts directly (reads results from shared storage)
- Never handles experiment tracking (delegates to ClearML via FastAPI)

**Failure mode**:
- If Django crashes: Users can't submit new requests, but in-progress GPU jobs keep running
- If database crashes: User data is inaccessible (need backup recovery)
- Mitigation: Regular database backups, stateless design (can restart Django without data loss)

**Data it owns**:
- User authentication (usernames, hashed passwords)
- Request history (who submitted what request when)
- Configuration metadata (user-facing settings)
- Result references (pointers to artifacts in shared storage)

**How it communicates**:
- FastAPI: HTTP requests to submit training/inference jobs
- PostgreSQL: SQL queries for user data and configuration
- Shared storage: Reads result artifacts (models, metrics, visualizations)

---

### 4.2 Compute Orchestration Layer (FastAPI)

**What it does**:
- Receives training/inference requests from Django
- Validates request parameters
- Initializes ClearML experiments for tracking
- Orchestrates PyTorch execution
- Manages GPU resource allocation
- Collects training metrics and outputs
- Persists artifacts to shared storage

**Why FastAPI**:
- Built for async tasks (long-running training/inference)
- Simple HTTP interface (Django can call it easily)
- Python-native (same language as PyTorch)
- Automatic API documentation (helps with debugging)
- Non-blocking I/O (can handle multiple requests without blocking)

**What it explicitly does NOT do**:
- Never manages user authentication (relies on Django)
- Never stores user session data
- Never manages user-facing visualization
- Never persists data that requires ACID transactions (use database for that)

**Failure mode**:
- If FastAPI crashes: In-progress jobs are lost (bad), but failure is obvious
- Recovery: ClearML experiment record shows incomplete metrics; job is marked as failed
- Mitigation: For Phase 2, use job queue that persists request (so job can resume)

**Data it owns**:
- Experiment state (which jobs are running, what metrics they've produced)
- Artifact metadata (where are outputs stored, what are their names)
- GPU resource state (which GPU is occupied, by which job)

**How it communicates**:
- Django: HTTP responses (results, status)
- PyTorch: Direct GPU access (executes training)
- ClearML: Experiment logging (sends metrics and metadata)
- Shared storage: Reads configs, writes models and metrics

---

### 4.3 GPU Execution Layer (PyTorch + YOLO)

**What it does**:
- Actual model training with PyTorch
- Multi-seed experimentation (trains multiple models, selects best)
- Validation metrics collection (tracks mAP50, precision, recall, etc.)
- Model checkpointing (saves intermediate states)
- Best model selection based on validation performance

**Why multi-seed training**:
- Single training runs are noisy (depends on random initialization)
- Multiple seeds (e.g., 3-5 runs) reduce statistical variance
- Allows selection based on validation metrics, not luck
- Reproducible: "Given this seed, reproduce this exact training run"

**What it explicitly does NOT do**:
- No hyperparameter tuning (out of scope at MVP)
- No model ensemble (single best model is selected)
- No architecture search (using fixed YOLO versions)

**Failure mode**:
- If training fails (OOM, NaN loss, etc): PyTorch raises exception
- FastAPI catches exception, logs to ClearML
- User sees error message in Django UI
- Mitigation: Clear error messages map to actionable fixes (e.g., "reduce batch size")

**Data it produces**:
- Model checkpoints (saved at intervals during training)
- Validation metrics (mAP50, precision, recall at each epoch)
- Best model reference (pointer to best checkpoint)
- Training logs (loss curves, learning rates, etc.)

**How it communicates**:
- ClearML: Logs metrics continuously (FastAPI/ClearML bridge)
- Shared storage: Reads training data, writes checkpoints
- FastAPI: Returns results (best model path, final metrics)

---

### 4.4 High-Resolution Inference Engine (SAHI)

**What it does**:
- Breaks large images into overlapping tiles
- Runs YOLO inference on each tile independently
- Merges detection results from multiple tiles
- Deduplicates detections (same object detected in multiple tiles)
- Generates output manifest (list of detections with confidence)

**Why SAHI is necessary**:
- YOLO has a receptive field limit (objects smaller than a certain size disappear)
- Tiling strategy allows detection of small objects without retraining
- Trade-off: Uses more compute (runs inference many times) for better recall

**What it explicitly does NOT do**:
- No post-processing (filtering by confidence, NMS, etc.)
- No model ensemble (single YOLO model)
- No confidence score recalibration

**Failure mode**:
- If tiling fails (invalid image format, incompatible resolution): error is caught
- FastAPI logs error; user sees message in Django UI
- Mitigation: Input validation (check image format before tiling)

**Data it produces**:
- Detection list (bounding boxes, class labels, confidence scores)
- Tile metadata (which tile each detection came from)
- Inference timing (how long each tile took to process)

**How it communicates**:
- PyTorch: Uses YOLO model for inference
- Shared storage: Reads image and model, writes detection manifest
- FastAPI: Returns detection results

---

### 4.5 Experiment Tracking (ClearML)

**What it does**:
- Logs experiment metadata (hyperparameters, data paths, software versions)
- Collects training metrics in real-time (loss, accuracy, etc.)
- Tracks artifact lineage (which model came from which training run)
- Enables experiment comparison (side-by-side metrics from different runs)
- Stores complete training history (can reproduce or rollback)

**Why ClearML**:
- Non-invasive integration (minimal code changes to PyTorch)
- Auto-logs metrics and hyperparameters
- Built-in experiment comparison UI
- Reproducibility: can re-run exact experiment from stored config
- No external service needed (can run locally)

**What it explicitly does NOT do**:
- No model serving or inference deployment
- No automated retraining triggers
- No data versioning (that's your responsibility)

**Failure mode**:
- If ClearML is down: Training still happens, but metrics aren't logged
- Recovery: ClearML stores "offline" mode data; syncs when back online
- Impact: Acceptable at MVP (loss of 1 experiment's logging is not critical)

**Data it owns**:
- Complete training history (all metrics from every training run)
- Experiment configurations (hyperparameters, model versions)
- Model artifacts (where each model is stored)
- Comparison data (metrics across different runs)

**How it communicates**:
- PyTorch: Receives metrics callbacks (loss, accuracy at each epoch)
- Shared storage: Stores experiment records
- Web UI: Provides experiment visualization and comparison

---

### 4.6 Data Persistence (PostgreSQL + Shared Storage)

**PostgreSQL: User Data & Configuration**
- Stores user accounts, authentication tokens
- Stores request history (who submitted what, when)
- Stores YOLO dataset configurations (ORM models that generate YAML)
- **Characteristics**: ACID transactional, reliable, not suitable for large artifacts
- **Failure mode**: Database failure means data loss (mitigate with backups and replication)

**Shared Storage: ML Artifacts**
- Stores training data (images for training)
- Stores model checkpoints (intermediate and final models)
- Stores inference outputs (detection results, visualizations)
- **Characteristics**: Simple, fast for local access, not distributed
- **Failure mode**: Storage failure means recent artifacts are lost (mitigate with backups and snapshots)

**Why separate**:
- PostgreSQL handles user data (needs ACID properties)
- Shared storage handles ML artifacts (needs high throughput, not transactions)
- Each is optimized for its use case

---

## 5. Data & Artifact Flow

### 5.1 Training Request Flow

**Step 1: User submits request via Django**
```
User clicks "Start Training" in Django UI
  → Django validates input (dataset name, YOLO version, etc.)
    → Django stores request in PostgreSQL
      → Django returns "training started" to user
```

**Step 2: Django calls FastAPI**
```
Django makes HTTP POST to FastAPI
  → Payload: training config (dataset, model version, hyperparameters)
    → FastAPI receives and validates
      → Returns "job accepted" to Django
```

**Step 3: FastAPI initializes experiment**
```
FastAPI initializes ClearML experiment
  → ClearML creates experiment record
    → Logs hyperparameters and config
      → Assigns experiment ID
```

**Step 4: Data preparation**
```
FastAPI downloads training data to shared storage
  → Checks if dataset exists locally
    → If not: download from source
      → Verify integrity (checksums)
```

**Step 5: Training execution**
```
FastAPI invokes PyTorch/YOLO training
  → YOLO reads config from shared storage
    → Trains model with multiple seeds (e.g., 3 runs)
      → Each seed produces different model (due to random initialization)
        → Validation metrics are collected (mAP50, precision, recall)
          → Best model is selected (highest mAP50)
```

**Step 6: ClearML logging**
```
At each epoch:
  → PyTorch computes metrics (loss, accuracy)
    → ClearML receives metric update
      → Stores in ClearML database
        → Plots visualizations in real-time
```

**Step 7: Artifact persistence**
```
After training:
  → Best model is saved to shared storage
    → Model name: "best_model_seed123.pt"
      → Metrics are saved as JSON
        → Training log is saved as text
          → FastAPI writes summary to PostgreSQL (via Django call)
```

**Step 8: User receives results**
```
Django polls FastAPI for job status
  → FastAPI responds with "training complete"
    → Django reads artifacts from shared storage
      → Renders metrics and model info in UI
        → User sees training results
```

**Why this flow matters**: Shows explicit handoff points; explains why synchronous works at MVP; identifies where async would help (Step 8: polling is inefficient at scale).

---

### 5.2 Inference Request Flow

**Step 1: User submits inference request via Django**
```
User uploads image and selects trained model
  → Django validates image (format, size)
    → Django stores request metadata in PostgreSQL
      → Django calls FastAPI with image reference
```

**Step 2: FastAPI processes request**
```
FastAPI receives inference request
  → Loads model from shared storage (caches in memory)
    → Loads inference engine (SAHI)
      → Returns "inference started" to Django
```

**Step 3: SAHI breaks image into tiles**
```
SAHI analyzes image resolution
  → Calculates tile size (e.g., 640x640, 25% overlap)
    → Breaks image into N tiles
      → Each tile is queued for inference
```

**Step 4: Inference on each tile**
```
For each tile:
  → YOLO runs inference (model outputs detections)
    → Detections include: bbox, class, confidence
      → Results are accumulated in memory
```

**Step 5: Merge and deduplicate**
```
After all tiles:
  → SAHI merges results from overlapping regions
    → Deduplicates detections (same object in multiple tiles)
      → Filters by confidence threshold
        → Produces final detection list
```

**Step 6: Artifact creation**
```
FastAPI creates inference output
  → Saves detection list as JSON (bbox, class, confidence)
    → Saves image with bounding boxes drawn (visualization)
      → Saves inference log (which tiles, execution time)
        → Writes results to shared storage
```

**Step 7: Django receives results**
```
Django polls FastAPI for status
  → Receives "inference complete"
    → Reads detection results from shared storage
      → Reads visualization (image with boxes drawn)
        → Renders in UI
```

**Step 8: User sees results**
```
User sees:
  → Image with bounding boxes
    → List of detected objects (class, confidence)
      → Inference timing (how long it took)
```

**Why this flow matters**: Shows complexity of high-resolution inference; explains why SAHI is necessary; identifies where caching would help (Step 2: loading model takes time; could be cached in Phase 2).

---

### 5.3 Artifact Lineage

Complete lineage from input to output:

```
Training Request (user input)
  ↓
ClearML Experiment ID
  ↓ (linked to)
Training Config (hyperparameters, data)
  ↓
Model Checkpoints (intermediate states)
  ↓
Best Model Reference
  ↓ (linked to)
Inference Request (user provides image + model ref)
  ↓
Detection Results
  ↓
Visualization (bounding boxes on image)
```

**Why this matters**: Every artifact can be traced back to its source. Given an inference result, you can:
1. Find which model was used (model ref)
2. Find which training run produced it (ClearML experiment)
3. Reproduce the training run (ClearML stores config)
4. Understand why this inference result exists

This is **reproducibility**.

---

## 6. Operational Challenges & Failure Modes

### 6.1 GPU Resource Contention

**The Problem**:
Multiple concurrent training jobs compete for GPU memory. YOLO training can use 8-16GB GPU memory per job. With a single 40GB GPU, you can run 2-3 concurrent jobs comfortably before hitting limits.

**Current Approach (MVP)**:
- Accept that we can handle ~3 concurrent training jobs
- Additional requests are held in HTTP request queue (simple but blocks users)
- Average response time grows as queue depth increases
- At 10+ concurrent requests, users see timeouts (30+ minute waits)

**Signal that we need to evolve**:
- Average queue wait time > 30 minutes
- Users complaining about timeouts
- Failed requests due to HTTP timeout

**Phase 2 Solution**:
- Add Celery job queue (Redis or RabbitMQ)
- Jobs are queued asynchronously
- User receives "job ID" immediately (< 1 second response)
- User polls or webhooks for completion
- Jobs are processed as GPU becomes available
- Can now handle 10-20+ concurrent queued jobs

**Trade-off**: Celery adds complexity (new service, queue management, error recovery). But it enables order-of-magnitude improvement in throughput.

**Lesson**: Start synchronous when scale is low. Add async when real bottleneck appears.

---

### 6.2 Synchronous Request Blocking

**The Problem**:
User submits training request → Django calls FastAPI → FastAPI waits for training → User waits (30+ minutes) for HTTP response.

If anything goes wrong (network glitch, FastAPI crashes), user loses all information about the training run.

**Current Approach (MVP)**:
- HTTP timeout is set high (30-60 minutes)
- Frontend shows "training in progress" spinner
- Trade-off: User can't do anything else while waiting

**Signal that we need to evolve**:
- Users complaining they can't submit another job while one is running
- Users accidentally closing browser (losing training state)
- Network instability causing request loss

**Phase 2 Solution**:
- Asynchronous job submission: user gets job ID immediately
- User can submit another job while first one is running
- User can close browser; job continues running
- User polls for status or receives webhook notification when complete

**Trade-off**: User experience improves (no blocking). Implementation gets more complex (need polling, notifications, job tracking).

**Lesson**: Synchronous is acceptable for MVP. Plan for async evolution before it's critical.

---

### 6.3 Shared Filesystem Reliability

**The Problem**:
Shared filesystem is convenient (simple mount, file operations look like local) but has risks:

- **Single point of failure**: If storage fails, recent artifacts are lost
- **Not geo-distributed**: Can't survive datacenter outage
- **No versioning**: Accidentally overwrite important model (no rollback)
- **Limited concurrency**: Many simultaneous writes can cause issues

**Current Approach (MVP)**:
- Accept that storage can fail
- Rely on regular backups and snapshots
- Document the risk (this is acceptable at MVP)

**Mitigation**:
- Regular backup schedule (daily snapshots)
- Automated backup verification
- Clear documentation: "If storage fails, restore from latest backup"

**Signal that we need to evolve**:
- Storage failure occurs and causes service outage
- Need to recover from backup (manual process is too slow)
- Geographic redundancy needed (multi-region deployment)

**Phase 4 Solution**:
- Migrate to S3 or cloud blob storage
- Built-in versioning and replication
- Geographic distribution (backup in multiple regions)
- Automated recovery (object storage is more resilient)

**Trade-off**: S3 adds cost and operational complexity. But enables geographic distribution and eliminates single point of failure.

**Lesson**: Shared filesystem is practical for MVP. Plan migration to object storage when scale or reliability requirements increase.

---

### 6.4 Model Artifact Management

**The Problem**:
Need to track which model was used for which inference. If "best model" reference is stale or incorrect, wrong model is used for inference.

**Current Approach (MVP)**:
- ClearML tracks model lineage (which training run produced this model)
- "Best model" reference points to specific artifact
- Model version is stored in PostgreSQL (for audit trail)

**Risks**:
- If best model reference is accidentally overwritten
- If model file is corrupted
- If multiple training runs produce same model name (collision)

**Mitigation**:
- ClearML keeps version history (can rollback)
- Atomic writes to model references (rename, not overwrite)
- Unique model naming (include timestamp or run ID)

**Signal that we need to evolve**:
- Model confusion (wrong version used for inference)
- Need for formal model registry
- Model approval workflows (can't deploy model without review)

**Phase 5 Solution**:
- Formal model registry (MLflow, Seldon, or custom)
- Model versioning with semantic versioning
- Model approval workflow (review before deployment)
- Model rollback capabilities

**Trade-off**: Model registry adds overhead. But enables governance and prevents model-related errors.

**Lesson**: ClearML is sufficient for MVP model tracking. Add formal registry when governance becomes critical.

---

### 6.5 Configuration Drift

**The Problem**:
YOLO configurations can change over time. If configuration history isn't maintained, can't reproduce old training runs.

**Example**:
- Training Run 1 (Jan): dataset=images_v1, model=yolov8n, classes=5
- Training Run 2 (Feb): dataset=images_v2, model=yolov8s, classes=10
- Training Run 3 (Mar): dataset=images_v3, model=yolov8m, classes=15

If you want to reproduce Training Run 1 (Jan), need to know the exact config from January. If config is stored as "current YAML file", you can't reproduce history.

**Current Approach (MVP)**:
- Store YOLO configs in PostgreSQL ORM models
- Django can generate YAML on demand (immutable snapshot)
- ClearML stores config as part of experiment record
- Combined: historical configs are recoverable

**Risks**:
- If PostgreSQL record is deleted
- If YAML generation logic changes
- If ClearML experiment record is lost

**Mitigation**:
- ClearML is source of truth for config (not PostgreSQL)
- Regular exports of ClearML experiments (archived backups)
- Config audit trail (log all config changes)

**Signal that we need to evolve**:
- Reproducibility failure (can't recreate old training run)
- Configuration errors cause training failures
- Need formal config versioning

**Phase 4 Solution**:
- Configuration as code (store YAML in version control)
- Git history provides full audit trail
- Each training run references config commit hash
- Enables full reproducibility (check out commit, run training)

**Trade-off**: Adds version control discipline. But enables reproducibility as first-class concern.

**Lesson**: ClearML + PostgreSQL is sufficient for MVP config tracking. Plan migration to version-controlled configs when reproducibility becomes critical.

---

## 7. Dataset Configuration & Synthetic Data Generation

### Why Dataset Configuration Matters

**The Naive Approach**: Create YOLO dataset manually:
```yaml
# manual_dataset.yaml (easy to get wrong)
path: /data/images
train: train/images
val: val/images
test: test/images
nc: 5  # 5 classes
names: ['class1', 'class2', ...]
```

Problems:
- Manual YAML is error-prone
- Changes aren't tracked
- Hard to reproduce: "which config was used for training run X?"
- Not auditable: who changed what, when?

**The Structured Approach**: Use Django ORM:
```python
# Django models
ProjectConfiguration
  ├── name: "fruit_detection"
  ├── description: "Detect fruits in orchard images"
  └── label_sets: [ClassSet]
  
ClassSet (dataset configuration)
  ├── name: "v2_with_augmentation"
  ├── training_images: [path to images]
  ├── validation_split: 0.2
  └── label_classes: [DetectionClass]
  
DetectionClass
  ├── name: "apple"
  ├── id: 0
  └── color: "#FF0000"

DatasetConfig (generated automatically)
  ├── path: /data/project_1/classset_v2/
  ├── train: train/images
  ├── val: val/images
  ├── nc: 5
  └── names: [apple, banana, ...]
```

Benefits:
- Configuration is queryable (can ask: "how many classes in dataset X?")
- Changes are tracked in database (audit trail)
- YAML is auto-generated (reduces error)
- Versioning is automatic (database tracks history)

### Why Synthetic Data Generation Matters

**The Problem**: Real-world datasets are expensive to create:
- Collecting images (photography, sensors, cameras)
- Annotating images (manual bounding box labeling)
- Quality control (verify annotations are correct)
- Cost per dataset: weeks of work, $10k-50k

**The Opportunity**: Use existing annotated data to generate synthetic data:

```
Existing annotated dataset
  ↓
1. Extract objects (use SAM to segment each annotated object)
  ├── Apple #1 (bounding box → mask → segmented image)
  ├── Apple #2 (segmented)
  ├── Banana #1 (segmented)
  └── ...
  
2. Extract backgrounds (images without objects)
  ├── Orchard #1 (background only)
  ├── Orchard #2 (background only)
  └── ...
  
3. Compose new scenes (paste objects into backgrounds)
  ├── New Image #1: [Orchard #1 bg + Apple #1 + Apple #2 + Banana #1]
  ├── New Image #2: [Orchard #2 bg + Apple #1 + Banana #2]
  └── ... (generate 100+ new images)
  
4. Generate annotations (bounding boxes for pasted objects)
  ├── New Image #1: {apple: [bbox1, bbox2], banana: [bbox3]}
  └── New Image #2: {apple: [bbox1], banana: [bbox2]}
  
Result: New synthetic dataset with 100+ images, fully annotated
```

**Benefits**:
- Augment dataset without collecting more real images
- Explore edge cases (rare object combinations that don't exist in real data)
- Improve model robustness (trained on diverse compositions)
- Cost-effective (reuse existing annotated data)

**Risks**:
- Synthetic data doesn't guarantee real-world performance
- Pasted objects might look unrealistic (jarring compositions)
- Annotations might be incorrect (bounding boxes of pasted objects)

**Mitigation**:
- Validate synthetic models on real test set
- Combine synthetic + real data for training
- Use visual inspection to check quality of synthetic images

### Integration into Training Pipeline

**Option 1: Pure Real Data**
```
Load dataset config
  → Real images only
    → Train YOLO
      → Test on real test set
```

**Option 2: Pure Synthetic Data**
```
Load dataset config
  → Real images only
    → Generate synthetic scenes
      → Train YOLO on synthetic
        → Test on real test set (will perform worse)
```

**Option 3: Hybrid (Recommended)**
```
Load dataset config
  → Real images
    → Generate synthetic scenes (N=100 new images)
      → Mix real + synthetic for training
        → Train YOLO on hybrid dataset
          → Test on real test set (improved robustness)
```

---

## 8. Trade-offs: Why Certain Choices Are Intentional

### The MVP Philosophy

This architecture is deliberately designed for **current constraints**, not future speculation. Every design choice answers: "What's the simplest thing that solves the problem TODAY?"

### Key Trade-offs

#### Trade-off 1: Synchronous vs. Async Job Handling

| Aspect | Synchronous (MVP) | Asynchronous (Phase 2) |
|--------|-------------------|----------------------|
| **User Experience** | Wait for job to complete | Get job ID, poll for status |
| **Implementation** | 20 lines of code | 200 lines of code (Celery, queue, polling) |
| **Concurrency limit** | ~3 concurrent jobs | ~20 concurrent jobs (depends on queue size) |
| **Failure recovery** | User retries HTTP request | Job persists in queue, can resume |
| **Operational burden** | None | Manage message broker, monitor queue depth |
| **When to switch** | Queue wait time > 30 minutes | Real bottleneck observed |

**Decision Rationale**: Synchronous is simpler and sufficient for MVP. If we never hit the queue wait > 30 min threshold, we've avoided unnecessary complexity.

---

#### Trade-off 2: Shared Filesystem vs. Object Storage

| Aspect | Shared Filesystem (MVP) | Object Storage (Phase 4) |
|--------|------------------------|-----------------------|
| **Setup time** | 5 minutes (mount volume) | 30 minutes (S3 bucket, IAM, config) |
| **Performance** | Fast local access | Network latency (but scalable) |
| **Reliability** | Depends on storage device | Built-in redundancy, geo-distribution |
| **Cost** | Cheap (local storage) | Moderate (S3 pricing) |
| **When to switch** | Multi-region or 50+ concurrent jobs | Geographic redundancy needed |

**Decision Rationale**: Shared filesystem is convenient for single-node MVP. Object storage is necessary when scaling multi-region or when reliability becomes critical.

---

#### Trade-off 3: Single GPU vs. Multi-GPU Worker Pool

| Aspect | Single GPU (MVP) | Multi-GPU (Phase 3) |
|--------|-----------------|-------------------|
| **Throughput** | 1 training job at a time | Multiple jobs in parallel |
| **GPU utilization** | ~80% (good) | ~90% (better, but overhead) |
| **Cost per job** | Cheap (1 GPU) | Higher (multiple GPUs) |
| **Operational complexity** | Single machine | Load balancing, failover |
| **When to switch** | Queue consistently full | Throughput bottleneck |

**Decision Rationale**: Single GPU is sufficient for MVP. Multi-GPU is necessary when demand exceeds single GPU capacity.

---

#### Trade-off 4: Manual Configuration vs. Automated Config

| Aspect | Manual YAML (Naive) | ORM-based Generation (MVP) | Full Config as Code (Phase 4) |
|--------|-------------------|---------------------------|------------------------------|
| **Flexibility** | Very high (edit YAML directly) | Medium (query ORM, generate) | Low (must commit to git) |
| **Auditability** | None (manual changes lose history) | High (database tracks changes) | Very high (git commits) |
| **Reproducibility** | Low (can't know config from old run) | High (ClearML stores config) | Very high (git commit hash) |
| **When to switch** | MVP | Config errors > 20% of failures | Reproducibility critical |

**Decision Rationale**: ORM-based generation strikes balance between flexibility and auditability for MVP. Full config-as-code is better but adds discipline overhead.

---

#### Trade-off 5: Kubernetes vs. Docker Compose

| Aspect | Docker Compose (MVP) | Kubernetes (Phase 4) |
|--------|---------------------|------------------|
| **Setup time** | 30 minutes | 2-3 days |
| **Multi-node support** | No | Yes |
| **Auto-scaling** | Manual | Automatic |
| **Operational burden** | Minimal | High (etcd, kubelet, networking) |
| **Learning curve** | Easy (5 concepts) | Steep (50+ concepts) |
| **When to switch** | Multi-region deployment | Geographic redundancy needed |

**Decision Rationale**: Docker Compose is sufficient for single-node MVP. Kubernetes is necessary when scaling to multi-region or when auto-scaling becomes critical.

---

#### Trade-off 6: Per-Request Inference vs. Batch + Caching

| Aspect | Per-Request (MVP) | Batch + Caching (Phase 5) |
|--------|------------------|-------------------------|
| **Latency per request** | 30-60 seconds | 2-5 seconds (cached) |
| **Implementation** | Simple (load model, run once) | Complex (batch queue, cache manager) |
| **GPU utilization** | 60% (idle waiting for input) | 95% (processing batches) |
| **When to switch** | Latency critical to users | Need real-time inference |

**Decision Rationale**: Per-request is sufficient for MVP. Batch + caching is necessary when inference latency becomes user-visible problem.

---

## 9. Current Maturity: MVP vs. Production

### What This Architecture IS

✅ **Sound Architectural Foundations**
- Clear separation of concerns
- Explicit responsibility boundaries
- Designed for growth (roadmap with trigger metrics)

✅ **Suitable for Research & Internal ML Workflows**
- Supports both web users and notebook researchers
- Full experiment tracking via ClearML
- Reproducibility through artifact lineage

✅ **Production-Grade Experiment Tracking**
- ClearML integration captures all metadata
- Can reproduce any training run
- Enables model comparison and debugging

✅ **Handling Real Constraints**
- Manages single GPU resource effectively
- Prevents concurrent job conflicts
- Tracks resource utilization

### What This Architecture IS NOT

❌ **Not Recommended for Customer-Facing Real-Time Inference**
- Synchronous blocking (users wait 30+ minutes)
- Single point of failure (shared storage, single GPU)
- No SLA guarantees

❌ **Not Suitable for Mission-Critical Workloads**
- No high-availability (single node failure = service down)
- No geographic redundancy
- No automated failover

❌ **Not Fully Automated MLOps Pipeline**
- No continuous training (manual model deployments)
- No automated model monitoring (no "drift detection")
- No CD pipeline for models

❌ **Not Enterprise-Scale System**
- Handles ~3 concurrent jobs (not 100s)
- Single GPU (not multi-region GPU infrastructure)
- Manual operations (not fully automated)

### Maturity Classification

**Phase 1: MVP** (Current)
- ✓ Architectural patterns are sound
- ✓ Components are clearly defined
- ✗ Limited concurrency and reliability
- ✗ Single point of failure

**Phase 2-5**: See roadmap section below

---

## 10. Production Evolution Roadmap

### Design Philosophy

Rather than over-engineer for speculative future scale, this architecture evolves through **measured, metric-driven phases**.

Each phase:
1. Solves a specific bottleneck (not speculative)
2. Is triggered by observable metric threshold
3. Adds minimum necessary complexity
4. Maintains backward compatibility where possible

### Phase 1: MVP (Current)

**Characteristics**:
- Single FastAPI instance (one GPU service)
- Synchronous HTTP request/response
- Shared filesystem storage (local mount)
- Basic experiment tracking (ClearML)
- Manual deployment (no CI/CD)

**Throughput**: ~3 concurrent training jobs (before queue waits exceed 5 minutes)

**Trigger for Phase 2**: Average queue wait time > 30 minutes OR user complaints about blocking

**Operational Characteristics**:
- Simple deployment (docker-compose up)
- Clear visibility (each job is in-flight or queued)
- Low operational overhead
- No external services (no message broker, no separate queue)

---

### Phase 2: Asynchronous Job Queue

**Trigger**: Queue wait time > 30 minutes (consistent observation)

**Changes**:
1. Add Celery or RQ for async job queuing
2. Add Redis or RabbitMQ as message broker
3. FastAPI becomes async job dispatcher (not waits for completion)
4. Django polls FastAPI for job status (or receives webhook callback)
5. Users receive job ID immediately (< 1 second)

**Benefits**:
- Non-blocking user interface (users can submit another job immediately)
- Better resource utilization (jobs processed as GPU becomes available)
- Job persistence (can resume after service restart)

**New Throughput**: ~15-20 concurrent queued jobs (depends on queue size)

**New Complexity**:
- Manage message broker reliability
- Handle job timeout and retry logic
- Implement polling/webhook notification system

**Trigger for Phase 3**: Consistent queue backlog (more than 1 job waiting)

---

### Phase 3: Multi-GPU Worker Pool

**Trigger**: Consistent observation that queue has 3+ jobs waiting

**Changes**:
1. Add 2-3 FastAPI instances (one per GPU)
2. Add load balancer (nginx or cloud LB) to distribute jobs
3. Each worker has independent GPU
4. Job distribution is automatic (based on load)

**Benefits**:
- Order of magnitude throughput improvement
- Better GPU utilization (parallel processing)
- Job isolation (one GPU's failure doesn't affect others)

**New Throughput**: ~50 concurrent queued jobs (depends on number of workers)

**New Complexity**:
- Load balancing and worker discovery
- State consistency across workers (careful about shared storage access)
- Worker failure detection and replacement

**Trigger for Phase 4**: Need for geographic redundancy OR consistent queue > 50 jobs

---

### Phase 4: Kubernetes + Object Storage

**Trigger**: Need for multi-region deployment OR SLA requirements > 99%

**Changes**:
1. Migrate from Docker Compose to Kubernetes
2. Migrate from shared filesystem to S3/blob storage
3. Add horizontal pod autoscaling (auto-add workers when queue grows)
4. Add cross-region replica (for geographic redundancy)

**Benefits**:
- Automatic scaling (no manual worker addition)
- Geographic redundancy (survive region outage)
- Better reliability (99.5% SLA feasible)
- Cloud-native operations

**New Throughput**: 100s-1000s concurrent jobs (depends on cloud infrastructure)

**New Complexity**:
- Kubernetes operations (etcd, kubelets, networking)
- Object storage integration (S3 API, credentials, costs)
- Multi-region synchronization (data replication)

**Trigger for Phase 5**: Need for 99.9% SLA AND critical observability of failures

---

### Phase 5: Enterprise Observability

**Trigger**: SLA requirements > 99.5% AND need to debug complex failures

**Changes**:
1. Add distributed tracing (Jaeger, Zipkin)
2. Add metrics aggregation (Prometheus, Datadog)
3. Add alerting system (PagerDuty, OpsGenie)
4. Add incident response workflows
5. Add formal model governance (model registry, approvals)

**Benefits**:
- Complete visibility into request flow (where does latency come from?)
- Automatic alerting (on-call team notified immediately)
- Incident tracking and post-mortems
- Model governance (can't deploy model without approval)

**New SLA Target**: 99.9% uptime with < 5 min MTTR

**New Complexity**:
- Observability infrastructure (Prometheus, Grafana, alerts)
- Incident response processes
- Model governance workflows

---

### Key Principle: Measured Evolution

Notice that each phase:
1. **Solves a real problem** (not speculation)
2. **Is triggered by observable metric** (not guesswork)
3. **Adds minimum necessary complexity** (not over-engineering)

**This prevents**:
- Over-engineering for scale that never materializes
- Technical debt from pre-mature optimization
- Operational burden from unnecessary services

**This enables**:
- Focus on current constraints (solve today's problem)
- Clear upgrade path (when to move to next phase)
- Rational investment in infrastructure

---

## 11. Lessons Learned & Architectural Principles

### Principle 1: Separate Concerns Early

**Lesson**: Components with fundamentally different scaling characteristics should not share resources.

**Application**: Web serving (CPU-bound, stateless) is different from GPU training (GPU-bound, stateful). Putting them in the same service causes both to suffer.

**Generalization**: Any time you have two workloads with different resource profiles, scaling needs, or failure modes, consider separating them.

**Anti-Pattern**: Monolithic service trying to do "everything" (web + GPU + batch + monitoring).

---

### Principle 2: Start Synchronous, Evolve to Async

**Lesson**: Synchronous request/response is simpler and acceptable when scale is low. Don't pre-emptively add async complexity.

**Application**: MVP uses HTTP request/response for training (users wait 30+ minutes). Phase 2 adds Celery when queue waits exceed 30 minutes.

**Generalization**: Measure first, optimize later. Build for current constraints; evolve as constraints change.

**Anti-Pattern**: Starting with Celery/Kafka/message queues when 3 requests per day don't need them.

---

### Principle 3: Make Responsibility Boundaries Explicit

**Lesson**: Document what each component IS and IS NOT responsible for. Clarity prevents architectural chaos.

**Application**: Django handles user auth (not model training). FastAPI handles orchestration (not user management). YOLO handles inference (not post-processing).

**Generalization**: Create a responsibility matrix early. Review it with team. Update as boundaries shift.

**Anti-Pattern**: Ambiguous ownership leading to features implemented in the wrong layer.

---

### Principle 4: Design for Observability & Debugging

**Lesson**: Every component failure should have clear, obvious signals. Errors should map to specific components and actionable fixes.

**Application**: Training failure is logged in ClearML with specific error message ("OOM: increase batch size"). User sees error in Django UI. Support team can debug quickly.

**Generalization**: Invest in logging, error messages, and tracing early. Don't debug by adding random print statements.

**Anti-Pattern**: Generic "500 Server Error" messages that don't help debug.

---

### Principle 5: Track Lineage from Input to Output

**Lesson**: Every artifact should be traceable back to its source. Enable reproducibility as first-class concern.

**Application**: ClearML tracks training config → model checkpoint → best model → inference results. Given an inference result, can reproduce exact training run.

**Generalization**: ML systems must be reproducible. Build this in early; retrofitting is hard.

**Anti-Pattern**: Models without version history; can't reproduce or rollback.

---

### Principle 6: Use Metrics to Trigger Evolution

**Lesson**: Define success metrics before problems appear. Use metrics to decide when to evolve.

**Application**: "When queue wait time > 30 minutes, add Celery." "When queue has 3+ jobs waiting, add worker pool."

**Generalization**: Be data-driven. Avoid "someday we might need to scale" → instead, watch metrics and upgrade when they signal bottleneck.

**Anti-Pattern**: Over-engineering based on imagined future scale.

---

### Principle 7: Accept Trade-offs Explicitly

**Lesson**: Every architecture choice has trade-offs. Make them explicit; don't pretend perfection.

**Application**: "We chose shared filesystem for MVP (convenient) over S3 (complex). Trade-off: single point of failure. Acceptable at MVP; will migrate to Phase 4."

**Generalization**: Document trade-offs. Communicate them to stakeholders. Plan migrations when constraints change.

**Anti-Pattern**: Ignoring trade-offs; discovering them painfully after deployment.

---

### Principle 8: Version Everything that Matters

**Lesson**: Model versions, config versions, dataset versions should all be trackable. Enable reproducibility.

**Application**: ClearML tracks model version (which checkpoint). PostgreSQL tracks config version (which YAML config). Both enable reproduction.

**Generalization**: Add versioning infrastructure early. The cost is small; the benefit (reproducibility) is huge.

**Anti-Pattern**: "Latest model" with no history; can't rollback or debug.

---

## 12. Portfolio Relevance: What This Demonstrates

### For Software Architects

**This case study demonstrates**:
- Microservice separation based on scaling characteristics
- Component responsibility boundaries
- Pragmatic MVP design
- Measured evolution (metrics-driven, not speculative)
- Trade-off analysis and explicit trade-off acceptance

**You should notice**:
- Why Django and FastAPI are separated (not just "they're different frameworks")
- How responsibilities map to components (not just listing technologies)
- When to add complexity (when bottlenecks appear, not pre-emptively)

---

### For ML Engineers

**This case study demonstrates**:
- GPU resource management and orchestration
- Experiment tracking and reproducibility
- Multi-seed training for statistical confidence
- High-resolution inference strategies (SAHI)
- Dataset configuration and synthetic data generation

**You should notice**:
- Why multi-seed training matters (not single runs)
- How ClearML enables reproducibility
- Trade-offs in inference strategies (speed vs. accuracy)
- Dataset engineering as part of pipeline

---

### For System Designers

**This case study demonstrates**:
- Failure mode analysis and mitigation
- Resource orchestration (GPU as scarce resource)
- Operational evolution roadmap
- Trade-off prioritization

**You should notice**:
- How each component can fail and what that means
- Why shared storage has limitations (and when to migrate)
- How to phase infrastructure improvements

---

### For Hiring Managers

**This case study demonstrates**:
- Engineering maturity (knows when NOT to add complexity)
- Communication clarity (documents reasoning, not just code)
- System thinking (sees components and interactions, not just features)
- Pragmatic decision-making (MVP mindset, evolution planning)

**You should notice**:
- Author understands trade-offs and makes explicit choices
- Author can articulate "why" (not just "what")
- Author thinks about operations and failure modes
- Author balances pragmatism with long-term thinking

---

### Interview Talking Points

If asked: **"Walk me through your most complex architectural decision"**

Response template:
```
The core decision was separating Django and FastAPI.

Initial problem: GPU training tasks were blocking web requests. 
Django is optimized for fast request/response; YOLO is optimized for 
long-running compute. Trying to do both in one service meant neither 
worked well.

Solution: Separate into two services. Django handles web tier (user auth, 
request history, visualization). FastAPI handles compute tier (GPU 
orchestration, training, inference). They communicate via HTTP.

Trade-off: Added operational complexity (now managing 2 services). 
But enables independent scaling and clear responsibility boundaries.

Result: Web requests are fast again. GPU work has its own scaling path. 
Each component's failures are obvious.

This scales: Phase 2 adds Celery when queue waits exceed 30 minutes. 
Phase 3 adds worker pool when single GPU saturates. Each phase is 
triggered by real metric, not speculation.

What I'd do differently: We started with shared filesystem for storage. 
That's fine for MVP but risky. If I did it again, I'd plan the S3 migration 
earlier (Phase 4, not Phase 4).
```

---

## Conclusion

This architecture demonstrates **pragmatic engineering**: building for current constraints, evolving as constraints change, making trade-offs explicit, and designing for observability.

It's not the most sophisticated system, nor is it the simplest. It's appropriately engineered for an MVP AI platform that bridges research and production workloads.

The real value isn't in any single component (Django, FastAPI, YOLO, ClearML exist elsewhere). The value is in how they're **integrated**: clear boundaries, explicit responsibilities, measured evolution, and honest assessment of limitations.

That's what makes this architecture worth studying.

---

## Navigation & Further Reading

**To understand the architecture deeply**:
- Start here (this case study)
- Read [Component Responsibilities](./docs/architecture/03-component-responsibilities.md)
- Review [Production Evolution Roadmap](./docs/architecture/15-production-evolution-roadmap.md)

**To implement similar patterns**:
- Study [System Architecture](./docs/architecture/0system-architecture.md)
- Follow [Docker Runtime Architecture](./docs/architecture/06-docker-runtime-architecture.md)
- Adapt [GPU Resource Management](./docs/architecture/12-gpu-resource-management.md)

**To understand failure scenarios**:
- Review [Error Handling and Fallbacks](./docs/architecture/13-error-handling-and-fallbacks.md)
- Study [Limitations and Risks](./docs/architecture/14-limitations-and-risks.md)

**For interview preparation**:
- See [Project Positioning](./PROJECT-POSITIONING.md)

---

**Questions?** See [README.md](./README.md) for high-level overview, or check specific docs linked above.
