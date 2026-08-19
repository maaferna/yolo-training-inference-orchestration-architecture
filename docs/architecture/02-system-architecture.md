# System Architecture

## Public-Safe Architecture Notice

This document describes a generalized and anonymized architecture for an internal AI vision platform. It does not include private source code, real datasets, trained weights, production credentials, client names, institutional identifiers, real metrics, real coordinates, or deployment-specific infrastructure details.

The architecture is documented for professional portfolio and architectural review purposes. It should be read as a public-safe system design reference, not as a production release or implementation guide for a private codebase.

---

## Architecture Positioning

This system is best described as an **internal production-oriented AI vision platform architecture**.

It is designed for a controlled organizational environment with a limited number of technical, operational, or research users. It is not designed as a public SaaS product, a large-scale multi-tenant platform, or a globally distributed cloud service.

The architecture prioritizes:

- clear separation between web orchestration and GPU-intensive processing;
- reproducible training and inference workflows;
- controlled internal operation;
- GPU runtime stability;
- artifact traceability;
- dataset and model governance;
- pragmatic deployment cost control;
- optional scale-out only when operational evidence justifies it.

---

## Current Deployment Model

The current architecture is based on a controlled internal deployment model:

- Django provides the web application, configuration layer, request submission, metadata persistence, and result visualization.
- FastAPI provides the AI service boundary for GPU-backed training, validation, inference, and experiment coordination.
- PyTorch/CUDA provides the GPU runtime for YOLO training and inference.
- Training currently executes on a single GPU. Multi-GPU runtime strategies (DataParallel, DDP) are documented and evaluated, but they are not the current execution model.
- Shared storage is used for artifact exchange between the web layer and AI service layer.
- ClearML is used for experiment tracking, metric logging, run comparison, and model artifact references.
- Docker Compose or a managed single-server deployment is sufficient for the documented internal operating context.

This architecture does **not** require Kubernetes, multi-region deployment, distributed worker pools, or public cloud GPU orchestration by default.

---

## Current Architecture Characteristics

| Aspect | Current Status | Notes |
|---|---|---|
| Deployment context | Internal platform | Designed for controlled organizational use, not public SaaS or multi-tenant deployment. |
| User profile | Limited internal users | Operational, technical, research, or production staff. |
| Web layer | Django | Handles configuration, metadata, user interaction, history, and result visualization. |
| AI service layer | FastAPI | Handles GPU-backed training, validation, inference, and experiment coordination. |
| Request handling | Synchronous / controlled | Acceptable when workload volume is predictable and users understand long-running jobs. |
| Job queue | Not required by default | Optional if timeouts, concurrency, retry, or cancellation become operationally important. |
| GPU training runtime | Single-GPU | Multi-GPU strategies (DP, DDP) are documented and evaluated; DDP is explicitly deferred. See `13-gpu-resource-management.md`. |
| Distributed job orchestration | Not implemented | No formal GPU worker pool, scheduler, or distributed job registry in the current architecture. |
| Storage | Shared artifact storage | Practical for controlled internal workflows; requires path validation and artifact governance. |
| Experiment tracking | ClearML | Supports metadata, metrics, artifacts, and run comparison, but does not replace a transactional model registry. |
| Cloud deployment | Optional / selective | Useful for intranet integration, metadata, result visualization, selected inference, or archival workflows. |
| Kubernetes | Not required | Optional only if operational scale, uptime, or multi-server management justifies it. |

---

## Important Distinction: Multi-GPU Runtime vs Distributed Platform

A key distinction in this architecture is the difference between **multi-GPU training runtime** and **distributed platform orchestration**.

### Multi-GPU Training Runtime

This refers to how a single training workload uses available GPU resources.

Examples:

- single-GPU YOLO training;
- PyTorch DataParallel execution;
- PyTorch Distributed Data Parallel execution;
- CUDA memory management across one or more GPUs;
- training-time GPU synchronization and cleanup.

This capability belongs to the **training runtime layer**.

### Distributed Job Orchestration

This refers to how multiple independent jobs are scheduled, queued, retried, monitored, cancelled, and assigned to workers.

Examples:

- job queue;
- background workers;
- GPU-aware scheduler;
- job registry;
- retry with backoff;
- worker pool;
- distributed execution across nodes;
- Kubernetes or another orchestration layer.

This capability belongs to the **platform orchestration layer**.

The current architecture can support multi-GPU training runtime patterns without being a fully distributed job orchestration platform.

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         INTERNAL USERS                               │
│  Operations staff • Production staff • Researchers • Technical users  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         DJANGO WEB LAYER                             │
│                                                                      │
│  Responsibilities:                                                   │
│  • project and dataset configuration                                 │
│  • training/inference request submission                             │
│  • user authentication and permissions                               │
│  • metadata persistence                                               │
│  • result visualization                                               │
│  • artifact references and history                                    │
│                                                                      │
│  Metadata Store: relational database                                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ HTTP / REST API
                                │ structured request payloads
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       FASTAPI AI SERVICE LAYER                       │
│                                                                      │
│  Responsibilities:                                                   │
│  • request validation                                                 │
│  • training orchestration                                             │
│  • continuous improvement training                                    │
│  • YOLO inference                                                     │
│  • SAHI tiled inference                                                │
│  • ClearML experiment coordination                                    │
│  • artifact generation                                                │
│  • error handling and fallback coordination                           │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────┐       ┌───────────────────────────────┐
│      GPU COMPUTE LAYER      │       │     EXPERIMENT TRACKING       │
│                             │       │                               │
│ • PyTorch/CUDA runtime      │       │ • ClearML metadata logging    │
│ • YOLO training/inference   │       │ • metrics and comparisons     │
│ • Single-GPU execution      │       │ • model artifact references   │
│ • CUDA memory cleanup       │       │ • failure analysis context    │
└───────────────┬─────────────┘       └───────────────┬───────────────┘
                │                                     │
                ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        SHARED ARTIFACT STORAGE                       │
│                                                                      │
│ • model checkpoints                                                   │
│ • selected best model reference                                       │
│ • training summaries                                                  │
│ • inference outputs                                                   │
│ • compressed previews                                                 │
│ • reports and manifests                                               │
│ • GIS-compatible output artifacts, when applicable                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

## 1. Django Web Application Layer

### Purpose

The Django layer provides the user-facing and administrative side of the platform.

### Responsibilities

- Manage projects, datasets, class definitions, and configuration metadata.
- Generate or reference dataset configuration artifacts.
- Submit training, validation, and inference requests to the AI service.
- Persist request metadata, execution history, and result references.
- Display results, reports, previews, and artifact links.
- Provide authentication, authorization, and administrative workflows.

### Not Responsible For

- Direct GPU execution.
- YOLO model training.
- SAHI inference execution.
- CUDA resource management.
- Long-running compute execution inside the web process.

---

## 2. FastAPI AI Service Layer

### Purpose

The FastAPI layer acts as the service boundary for AI processing. It separates compute-heavy workloads from the web application.

### Responsibilities

- Receive structured requests from Django.
- Validate payloads and required artifact references.
- Orchestrate YOLO training, CI training, inference, and SAHI workflows.
- Coordinate GPU-backed execution through PyTorch/CUDA.
- Register experiment metadata and metrics in ClearML.
- Write generated artifacts to shared storage.
- Return structured execution metadata to the web layer.

### Current Execution Model

The current architecture may execute long-running jobs synchronously through the AI service. This can be acceptable in a controlled internal environment where jobs are scheduled, users are limited, and long-running execution is expected.

A background job queue should be introduced only if synchronous execution causes operational pain, such as repeated timeouts, competing jobs, or the need for cancellation/retry/progress tracking.

---

## 3. YOLO Training Engine

### Purpose

The YOLO training engine executes model training and validation workflows for object detection.

### Responsibilities

- Load base YOLO model configuration or checkpoint references.
- Execute training runs with controlled parameters.
- Support multi-seed experimentation when needed.
- Collect training and validation metrics.
- Select model candidates based on validation criteria.
- Persist checkpoints, summaries, and selected model references.
- Release GPU memory between runs when needed.

### GPU Execution

Training runs on a single GPU today. The documented path beyond that is:

- single-GPU execution — **current**;
- multi-GPU DataParallel execution — evaluated, not in use;
- Distributed Data Parallel execution — deferred, dependent on runtime environment and configuration.

Whichever of these is in use, it is a training runtime capability. It does not imply that the platform has distributed job orchestration, worker pools, or Kubernetes.

### Constraints

- Training can be long-running.
- GPU memory pressure must be managed explicitly.
- Dataset size and image resolution directly affect runtime and memory usage.
- DDP/DP stability depends on OS, CUDA, PyTorch, driver versions, and runtime configuration.
- Concurrent training jobs require explicit scheduling or resource locking if introduced.

---

## 4. Continuous Improvement Training Pipeline

### Purpose

The continuous improvement training pipeline supports incremental model improvement using previous model references and new data.

### Responsibilities

- Load the previous selected model reference.
- Execute additional training on new or expanded datasets.
- Compare new validation metrics against a historical baseline.
- Update the selected model reference only when improvement criteria are satisfied.
- Log experiment metadata and comparison context.
- Preserve traceability between dataset configuration, model artifact, and result summary.

### Current Risks

- File-based or lightweight model references can create race conditions if multiple updates occur simultaneously.
- A transactional model registry is recommended if multiple users or parallel training workflows become common.
- Model lineage must include dataset configuration, class mapping, model version, training parameters, and validation summary.

---

## 5. SAHI Inference Engine

### Purpose

The SAHI inference engine supports object detection on high-resolution imagery by slicing large images into smaller tiles before inference.

### Responsibilities

- Accept image or batch inference requests.
- Slice high-resolution images into tiles.
- Run YOLO inference per tile.
- Merge and deduplicate detections.
- Generate detection metadata, previews, and output artifacts.
- Persist compact results for web visualization.

### Cost and Data Consideration

For full drone campaigns with hundreds of large images, local batch inference may be more cost-effective than uploading all raw imagery to cloud storage. Cloud inference is more appropriate for selected, short-lived, or intranet-integrated workloads.

---

## 6. ClearML Experiment Tracking Layer

### Purpose

ClearML provides experiment tracking, metrics, and artifact references for training and validation workflows.

### Responsibilities

- Log training configuration metadata.
- Track validation metrics and experiment summaries.
- Register selected model artifacts or references.
- Support run comparison and debugging.
- Preserve model lineage context.

### Boundary

ClearML is used for tracking and experiment visibility. It should not be treated as a complete transactional model registry unless the architecture explicitly defines governance, promotion, rollback, and consistency rules.

---

## 7. Shared Artifact Storage Layer

### Purpose

Shared storage enables controlled exchange of generated artifacts between the web application and AI service.

### Artifact Categories

```text
SHARED_ARTIFACT_STORAGE/
├── models/
│   ├── selected_model_checkpoint
│   ├── model_reference_metadata
│   └── checkpoints/
├── training_runs/
│   ├── run_identifier/
│   │   ├── training_summary
│   │   ├── metric_summary
│   │   └── execution_log
├── inference_runs/
│   ├── job_identifier/
│   │   ├── output_manifest
│   │   ├── compressed_preview
│   │   └── detection_summary
└── reports/
    ├── generated_reports
    └── GIS_or_vector_outputs
```

### Responsibilities

- Store selected model checkpoints and references.
- Store training and inference summaries.
- Store compact previews and reports for web visualization.
- Maintain artifact structure for reproducibility.
- Provide a consistent path contract between services.

### Risks

- Path mismatch between containers or host environments.
- File permission errors.
- Concurrent writes to the same artifact reference.
- Stale model references.
- Unbounded growth of outputs and checkpoints.
- Tight coupling between service logic and filesystem layout.

### Recommended Improvements

- Use artifact manifests per run.
- Add preflight validation for read/write paths.
- Define retention policies.
- Move model references to a database-backed registry if concurrency increases.
- Avoid treating shared storage as a substitute for full artifact governance.

---

## 8. Raw Imagery Storage and Data Movement Layer

### Purpose

Raw drone imagery is a high-volume data asset and should be treated differently from lightweight web artifacts.

Drone campaigns may produce hundreds of high-resolution images per flight. Uploading all raw imagery to cloud storage by default can increase bandwidth usage, storage cost, operational complexity, and processing latency.

### Recommended Baseline

```text
Raw drone imagery: local by default
Training datasets: close to local GPU processing
Heavy batch inference: local when data volume is high
Selected model artifacts: synchronized to cloud when useful
Metadata, previews, and reports: synchronized to cloud-hosted intranet
Historical archive: optional cloud storage with lifecycle policy
```

### Hybrid Data Flow

```text
Drone Flight
   ↓
Local Image Ingestion
   ↓
Local Validation / Preprocessing
   ↓
Local GPU Training or Heavy Batch Inference
   ↓
Selected Artifact Synchronization
   ├── selected model checkpoint
   ├── model metadata
   ├── dataset version summary
   ├── inference summaries
   ├── compressed previews
   ├── reports
   └── GIS-compatible outputs
          ↓
Cloud-hosted Intranet / Metadata / Visualization
```

### Rationale

This approach avoids uploading large raw datasets unless cloud-side processing is required. It supports a hybrid architecture where AWS or another cloud provider can host the existing intranet, metadata, selected model artifacts, and result visualization without becoming the default storage location for every raw image.

---

## 9. GPU Compute Layer

### Purpose

The GPU compute layer provides CUDA acceleration for training, validation, and inference.

### Responsibilities

- Provide CUDA runtime access for PyTorch.
- Support GPU-backed YOLO training and inference.
- Provide single-GPU execution today, with a documented path to multi-GPU.
- Manage CUDA memory and cleanup.
- Handle GPU memory pressure and OOM conditions.
- Coordinate model loading and release.

### Key Technologies

- NVIDIA GPU runtime.
- CUDA.
- PyTorch CUDA backend.
- DataParallel — evaluated, not currently in use.
- Distributed Data Parallel — deferred; see `13-gpu-resource-management.md`.
- Docker GPU runtime support.

### Operating System Runtime Decision

Ubuntu is the preferred runtime baseline for this architecture because GPU-heavy workloads involving PyTorch, CUDA, NVIDIA drivers, Docker GPU access, YOLO training, and DDP/DP behavior are sensitive to OS and driver compatibility.

Other operating systems or Linux distributions may work, but they can introduce additional runtime friction. Ubuntu provides a more predictable and commonly supported baseline for GPU-backed computer vision workloads.

### Constraints

- GPU memory is finite and must be actively managed.
- DDP/DP behavior depends on driver, CUDA, PyTorch, and OS compatibility.
- Concurrent jobs require resource locking or scheduling.
- Long-running training jobs can monopolize GPU resources.

---

## 10. Docker Runtime Layer

### Purpose

The Docker runtime layer provides reproducible service boundaries for the web application, AI service, database, and shared storage.

### Responsibilities

- Define service containers.
- Isolate web and compute dependencies.
- Provide GPU access to the AI service.
- Mount shared artifact storage.
- Configure service networking.
- Provide environment-based configuration.

### Conceptual Services

| Service | Role | GPU Required |
|---|---|---|
| Django web service | UI, metadata, request submission, visualization | No |
| FastAPI AI service | Training, validation, inference, experiment coordination | Yes |
| Relational database | User metadata, request records, configuration references | No |
| Shared storage | Artifact exchange and generated outputs | No |

### Runtime Notes

- Docker Compose or a managed single-server deployment is sufficient for the current internal operating context.
- Kubernetes is not a required next step.
- GPU access should be validated through preflight checks.
- Environment-specific paths should be represented through configuration, not hardcoded values.

---

## Data Flow Summary

## Training Request Flow

```text
User submits training request in Django
  ↓
Django validates project and dataset configuration
  ↓
Django sends structured request to FastAPI AI service
  ↓
FastAPI validates request and resolves artifacts
  ↓
ClearML experiment context is initialized
  ↓
YOLO training executes on GPU runtime
  ↓
Training metrics and selected checkpoint are generated
  ↓
Artifacts are written to shared storage
  ↓
Metadata and result references return to Django
  ↓
Django displays status, summaries, and artifacts
```

## Continuous Improvement Flow

```text
New dataset or configuration submitted
  ↓
Previous selected model reference resolved
  ↓
Incremental training executes
  ↓
New metrics compared against baseline
  ↓
Selected model reference updated only if improvement criteria are met
  ↓
Experiment metadata logged
  ↓
Django exposes comparison and result summary
```

## Inference Flow

```text
User submits image or batch inference request
  ↓
Django sends request to FastAPI AI service
  ↓
Selected model reference is resolved
  ↓
YOLO or SAHI inference executes
  ↓
Detections are merged and summarized
  ↓
Compact artifacts are written to shared storage
  ↓
Django visualizes previews, summaries, and reports
```

## Hybrid Deployment Flow

```text
Raw imagery remains local by default
  ↓
Training or heavy batch inference runs near local GPU resources
  ↓
Selected artifacts are synchronized to cloud-hosted intranet
  ↓
Cloud layer provides metadata, previews, reports, and optional inference
```

---

## Assumptions

- Users are limited and internal.
- Workloads are scheduled, occasional, or controlled.
- Long-running jobs are expected and acceptable within the operational context.
- Raw drone imagery is high-volume and may be better processed locally.
- Cloud deployment is useful for intranet integration, metadata, reports, and selected inference, but not necessarily for all raw data and training workloads.
- Ubuntu is the preferred GPU runtime baseline for CUDA/PyTorch compatibility.
- Multi-GPU training runtime is available or evaluated independently from distributed platform orchestration.

---

## Current Constraints

- No formal job queue by default.
- No distributed worker pool by default.
- No Kubernetes requirement in the current architecture.
- No multi-region deployment requirement.
- Synchronous execution may become problematic if long-running jobs are submitted concurrently.
- Shared filesystem coupling requires validation and governance.
- Lightweight model references require stronger consistency if concurrency increases.
- Limited observability compared with enterprise-scale distributed systems.
- Raw imagery storage and cloud synchronization require explicit cost strategy.

---

## Recommended Near-Term Improvements

Before adding distributed infrastructure, prioritize:

1. Preflight validation for datasets, models, output directories, GPU availability, and storage mounts.
2. Explicit job status records for long-running operations.
3. Structured logs with correlation IDs.
4. Artifact manifests per training or inference run.
5. Storage lifecycle and retention policies.
6. Database-backed model reference tracking.
7. Dataset configuration versioning.
8. GPU memory and resource health checks.
9. Raw imagery storage policy.
10. Optional lightweight queue only if synchronous execution creates real operational pain.

---

## Optional Future Scale-Out

Scale-out infrastructure should be treated as conditional, not inevitable.

Optional additions may include:

- lightweight job queue;
- single GPU worker process;
- GPU resource locking;
- distributed worker pool;
- object storage;
- Kubernetes or another orchestrator;
- centralized monitoring and alerting;
- distributed tracing.

These should be introduced only if workload volume, uptime requirements, storage pressure, or operational complexity justify them.

---

## Summary

This architecture provides a fit-for-purpose foundation for an internal AI vision platform. It separates web orchestration from GPU-intensive processing, supports GPU-backed YOLO training and inference, documents multi-GPU runtime considerations, and preserves a pragmatic path toward reliability and optional scale-out.

The architecture should evolve by operational evidence, not by default. For the current context, reliability, traceability, artifact governance, GPU runtime stability, and cost-aware data placement are more important than premature distributed infrastructure.
