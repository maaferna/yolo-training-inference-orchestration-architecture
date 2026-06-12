# YOLO Training & Inference Orchestration Architecture

## ⚠️ Public-Safe Documentation Repository

**This repository contains generalized, anonymized architecture documentation only. It is NOT a production release of private code.**

### What This Repository Is

This repository documents **architectural decisions for a web-connected AI vision platform** that separates user-facing web services from GPU-intensive ML workloads. It demonstrates:

- **Microservice separation**: stateless web tier (Django) and compute tier (FastAPI) with independent scaling
- **GPU compute dispatch**: YOLO training with multi-seed experimentation and validation-based model selection
- **MLOps integration**: ClearML for experiment tracking, metric logging, and model artifact registration
- **High-resolution inference patterns**: SAHI tiling for per-tile inference on large images
- **Pragmatic growth philosophy**: start synchronous on single GPU, evolve to async/queue-based when queue wait exceeds 30 minutes
- **Failure mode documentation**: explicit identification of known failure modes and error messaging
- **Production evolution planning**: hypothetical roadmap with trigger metrics for scaling from MVP to enterprise scale

**This is an MVP-level architecture** (single GPU service, shared filesystem storage). Not yet deployed in production. The production evolution roadmap documents hypothetical scaling patterns with explicit trigger metrics.

### What This Repository Is NOT

🚫 **This repository does not contain:**
- Production source code from the private implementation
- Actual datasets or training data
- Real trained model weights
- Real metrics or performance results
- Real coordinates, detections, or inference outputs
- Client, institution, farm, field, or researcher names
- Credentials, secrets, or API keys
- Absolute local paths or environment-specific configurations
- ClearML workspace names or sensitive infrastructure details
- Real screenshots, generated images, or model outputs
- Runnable Django, FastAPI, YOLO, SAHI, ClearML, or training code
- Production Dockerfiles or deployable containers
- Private IP information or deployment infrastructure

This repository does not contain the private implementation, datasets, trained weights, real metrics, credentials, or production deployment files.

---

## Maturity Tier: MVP Architecture

This repository represents **Phase 1 of a documented production evolution roadmap**:

| Aspect | Status | Notes |
|--------|--------|-------|
| Request handling | Synchronous | Single GPU service instance; HTTP-based request/response |
| Job queuing | Not implemented | Triggers Phase 2 when queue wait time exceeds 30 minutes |
| Multi-GPU scaling | Conceptual | Roadmap: Add worker pool when > 3 concurrent jobs observed |
| Distributed training | Deferred to Phase 3 | DDP pattern documented in roadmap; single GPU sufficient for MVP |
| Kubernetes orchestration | Future phase | Local Docker Compose sufficient for current phase |
| Model registry | ClearML artifact registration | Experiment tracking + metric logging implemented; not full registry |
| Inference serving | Per-request | No inference caching or batch optimization yet |
| Observability | Partial | Error handling and logging; no distributed tracing or alerting |
| High-availability | Single node | No failover or redundancy at MVP scale |

**Philosophy**: Build for current requirements, add complexity only when real bottlenecks appear. Each phase is triggered by specific metrics, not speculation.

---

For a comprehensive visual and textual overview of the system architecture, see [**docs/02-system-architecture.md**](./docs/02-system-architecture.md).

The system separates web orchestration (Django) from GPU-intensive compute services (FastAPI), enabling independent scaling and clear component responsibilities.

---

## Clear Responsibility Boundaries

Explicit responsibility separation prevents architectural complexity and makes failure modes obvious:

- **Django**: Web UI, authentication, request history, result visualization → NOT model training
- **FastAPI**: Training orchestration, inference dispatch, experiment coordination → NOT user authentication
- **YOLO Training**: Model training with validation-based selection → NOT hyperparameter tuning
- **SAHI Inference**: High-resolution detection via tiling → NOT post-processing or filtering
- **ClearML**: Experiment tracking, metrics collection, model lineage → NOT model storage or serving
- **PostgreSQL**: User data, configuration, request metadata → NOT ML artifact storage
- **Shared Storage**: Models, checkpoints, training outputs → NOT user data or credentials

This clarity prevents "dependency spaghetti" and makes failure scenarios explicit. For full responsibility matrix and failure handling table, see [**docs/03-component-responsibilities.md**](./docs/03-component-responsibilities.md).

---

## Main Components

For detailed component responsibilities, interactions, and failure modes, see [**docs/03-component-responsibilities.md**](./docs/03-component-responsibilities.md).

Key components include:

### 1. **Django Web Application**
   Request submission, result visualization, and user management layer.

### 2. **FastAPI AI Service**
   Orchestration engine coordinating training, inference, and experiment tracking.

### 3. **YOLO Training Engine**
   Multi-seed training with automatic model selection based on validation metrics.

### 4. **Continuous Improvement Training**
   - Incremental training on new data
   - Historical baseline comparison
   - Conditional best model update
   - Experiment isolation and tracking

### 5. **SAHI Inference Engine**
   - High-resolution image tiling
   - Small-object detection
   - Detection result merging
   - Output artifact generation

### 6. **ClearML Experiment Tracking**
   - Experiment metadata logging
   - Metrics collection and comparison
   - Model lineage tracking
   - Failure isolation and debugging

### 7. **Shared Storage Layer**
   - Model checkpoints
   - Best model references
   - Training artifacts
   - Inference outputs

### 8. **GPU Resource Management**
   - CUDA memory management
   - DataParallel execution
   - DDP (Distributed Data Parallel) evaluation
   - Multi-GPU orchestration

---

## Technology Stack & Integration Patterns

| Layer | Technology | Integration Pattern |
|-------|-----------|----------------------|
| **Web** | Django + DRF | Request/response validation, ORM-backed data persistence |
| **Compute** | FastAPI | Async task delegation via HTTP; long-running training/inference |
| **Training** | PyTorch + Ultralytics YOLO | Multi-seed experimentation with validation-based model selection |
| **Inference** | YOLO + SAHI | High-resolution image tiling strategy for small-object detection |
| **Experiment Tracking** | ClearML | Metadata logging, metrics collection, model lineage management |
| **Database** | PostgreSQL | User data, request history, configuration metadata |
| **GPU Execution** | CUDA + DDP | Resource management, distributed data parallel evaluation |
| **Containerization** | Docker Compose | Local development; evolution path to Kubernetes |
| **Storage** | Shared volumes | Local filesystem; evolution path to S3/blob storage |

**Integration Philosophy**: Keep concerns separated (web, compute, storage, database). Communicate via clear interfaces (HTTP between services, filesystem for artifacts, relational DB for metadata).

### Django Configuration Layer

This architecture includes a Django-based YOLO dataset configuration management layer that centralizes training parameters through ORM models (ProjectConfiguration, ClassSet, DetectionClass, DatasetConfig) with automatic Ultralytics-compatible YAML generation. See [**docs/08-yolo-dataset-configuration-management.md**](./docs/08-yolo-dataset-configuration-management.md) for comprehensive documentation.

### Auxiliary: Synthetic Dataset Generation

The broader ecosystem includes an auxiliary synthetic dataset generation pipeline based on SAM (Segment Anything Model) for dataset engineering and research experimentation. This component automates object extraction from annotated images and synthetic scene composition, supporting dataset enrichment workflows. See [**docs/20-synthetic-dataset-generation-pipeline.md**](./docs/20-synthetic-dataset-generation-pipeline.md) for details.

---

## What This Repository Demonstrates

### A. System Design Thinking
- **Responsibility separation**: Django (stateless web) vs FastAPI (compute tier) prevents cross-cutting concerns
- **Failure mode analysis**: Each component has explicit handling strategy (see docs/13-error-handling-and-fallbacks.md)
- **Synchronous-first pragmatism**: MVP justifies simple HTTP-based communication; documents when async is needed
- **Scaling philosophy**: Growth is metrics-driven (queue wait time, job concurrency) not speculative

### B. AI/ML Architecture Knowledge
- **Multi-seed experimentation**: Why train multiple seeds for statistical robustness over single-run results
- **Model selection logic**: Validation metrics drive selection (mAP50), not heuristics or manual selection
- **High-resolution inference**: SAHI tiling strategy trades compute for detection accuracy on small objects
- **GPU resource management**: CUDA context handling, DataParallel patterns, DDP evaluation strategies
- **Experiment tracking**: ClearML integration enables reproducibility, comparison, and failure debugging

### C. Backend Integration & Full-Stack Patterns
- **Web-to-compute communication**: Synchronous HTTP at MVP, designed for queue migration
- **Shared storage orchestration**: Docker volumes in development; evolution path to object storage
- **Database schema design**: User data (PostgreSQL) vs ML artifacts (filesystem) separation
- **Configuration management**: YOLO dataset YAML generation from ORM models; validation pipeline
- **Error propagation**: Specific failures mapped to HTTP status codes and user-facing messages

### D. Production Evolution Thinking
- **Pragmatic MVP**: No Kubernetes, no message queues, no object storage—sufficient for current scale
- **Growth-triggered phases**: Each evolution phase is triggered by specific bottleneck metrics
- **Technical decision rationale**: Documents when synchronous fails, when async becomes necessary
- **Cost awareness**: Complexity is added only when real constraints appear, not pre-emptively

### E. Responsible Public Documentation
- **Anonymized architecture**: No customer, institution, or project names; no real credentials
- **Sanitized code examples**: All database URLs, API keys use placeholders; function names are generic
- **Educational value preserved**: Patterns are reusable; actual implementation remains private
- **Security discipline**: Pre-commit hooks for credential detection, contributing guidelines, audit reports

### NOT Demonstrated
- ❌ Production deployment to real cloud infrastructure (conceptual only)
- ❌ Inference at scale or model serving optimization (future roadmap item)
- ❌ Advanced MLOps features (no CI/CD, no automated retraining triggers at MVP)
- ❌ Kubernetes orchestration (documented as Phase 4)
- ❌ Multi-region or high-availability patterns (Phase 5)

---

## 📖 Engineering Case Study: Deep Dive

For a comprehensive narrative-driven exploration of the architectural decisions behind this system, see the **[Engineering Case Study](./CASE-STUDY.md)**.

**What the case study covers**:
- **Problem Context**: Why separate web and compute layers? What conflicting requirements exist?
- **Constraints & Trade-offs**: What are the hard limits? When do we evolve?
- **Architecture Decision**: The core Django/FastAPI separation and why it matters
- **Component Design**: What each layer does (and does NOT do)
- **Data & Artifact Flows**: How requests move through the system
- **Operational Challenges**: What happens when things break?
- **Dataset Configuration**: How to manage training data at scale
- **Trade-offs Explained**: Why certain choices are intentionally "incomplete"
- **Evolution Roadmap**: Phases 1-5 with trigger metrics and rationale
- **Lessons Learned**: Principles that generalize beyond this project
- **Portfolio Relevance**: What this demonstrates in interviews

**Reading time**: 35-45 minutes  
**Best for**: Architects wanting to understand the reasoning, not just the components

This is the document to share when someone asks: **"Why did you design it this way?"**

---

## System Flow Summary

### Training Flow
1. Django user submits training request
2. FastAPI receives and validates request
3. ClearML experiment is initialized
4. YOLO training engine executes multi-seed training
5. Best model is selected based on mAP50
6. Artifacts are stored to shared volume
7. Results are exposed to Django for visualization

### Continuous Improvement Training Flow
1. New data is submitted to CI training pipeline
2. Previous best model is loaded
3. Incremental training is performed
4. New metrics are compared against historical baseline
5. Best model is updated only if performance improves
6. ClearML tracks all comparison metrics

### Inference Flow
1. Django user submits inference request with image
2. FastAPI receives request
3. High-resolution image is processed with SAHI tiling
4. YOLO inference is applied to each tile
5. Detection results are merged and deduplicated
6. Output manifest is generated
7. Results are returned to Django

### Artifact Exposure Flow
1. FastAPI writes artifacts to shared volume
2. Django reads artifacts via mounted volume
3. Results are cached and visualized
4. Error states are logged to ClearML

---

## Architectural Evolution Path

This repository demonstrates **pragmatic growth thinking**. Instead of building for "infinite scale" from day one, the roadmap shows when and why to evolve each component:

### Phase 1: MVP (Current Design)
- Single GPU service instance
- Synchronous HTTP request/response
- Shared filesystem storage
- **Scaling limit**: ~3 concurrent long-running jobs
- **Trigger for Phase 2**: Average queue wait time > 30 minutes

### Phase 2: Async Job Queue
- **When**: 3+ concurrent jobs consistently observed
- **Add**: Celery/RQ job queue for asynchronous training
- **Benefit**: Non-blocking user requests; better resource utilization

### Phase 3: Multi-GPU Worker Pool
- **When**: > 10 concurrent jobs consistently observed
- **Add**: Multiple GPU service instances with load balancing
- **Benefit**: Higher throughput; independent job scheduling

### Phase 4: Kubernetes + Object Storage
- **When**: Multi-region deployment needed or > 50 concurrent jobs
- **Add**: Kubernetes orchestration; S3/blob storage for artifacts
- **Benefit**: Managed scaling; geographic redundancy

### Phase 5: Enterprise Observability
- **When**: SLA requirements > 99.5% uptime
- **Add**: Distributed tracing, metrics, alerting, incident management
- **Benefit**: Production reliability; operational visibility

**Philosophy**: Add complexity only when real bottlenecks appear, not speculation. For detailed reasoning and trigger metrics, see [**docs/15-production-evolution-roadmap.md**](./docs/15-production-evolution-roadmap.md).

---

## Repository Structure

```
yolo-training-inference-orchestration-architecture/
├── README.md                                  # This file
├── LICENSE                                    # MIT or Apache 2.0
├── .gitignore                                 # Git ignore rules
│
├── docs/                                      # Comprehensive documentation
│   ├── 01-context-and-problem.md            # Problem statement & motivation
│   ├── 02-system-architecture.md            # Detailed architecture breakdown
│   ├── 03-component-responsibilities.md     # Each component's role
│   ├── 04-system-flow.md                    # Request/response flows
│   ├── 05-api-integration-contracts.md      # API payload contracts (no code)
│   ├── 06-docker-runtime-architecture.md    # Container architecture
│   ├── 07-shared-storage-and-artifacts.md   # Storage design & path mapping
│   ├── 08-yolo-training-engine.md           # YOLO training details
│   ├── 09-continuous-improvement-training.md # CI training pipeline
│   ├── 10-sahi-inference-engine.md          # SAHI inference design
│   ├── 11-clearml-experiment-tracking.md    # ClearML integration
│   ├── 12-gpu-resource-management.md        # GPU orchestration
│   ├── 13-error-handling-and-fallbacks.md   # Error scenarios & mitigations
│   ├── 14-limitations-and-risks.md          # Current limitations
│   ├── 15-production-evolution-roadmap.md   # Future improvements
│   ├── 16-public-release-sanitization.md    # Safety & sanitization guide
│   └── 17-technical-responsibilities.md     # Portfolio positioning
│
├── diagrams/                                  # Mermaid architecture diagrams
│   ├── architecture-overview.mmd            # System architecture diagram
│   ├── training-flow.mmd                    # Training request flow
│   ├── ci-training-flow.mmd                 # CI training flow
│   ├── inference-flow.mmd                   # Inference request flow
│   ├── storage-flow.mmd                     # Artifact storage flow
│   └── future-production-architecture.mmd   # Proposed production architecture
│
├── examples/                                  # Example payloads & configs
│   ├── api-payloads/
│   │   ├── training-request.example.json           # Training request payload
│   │   ├── ci-training-request.example.json        # CI training request
│   │   └── sahi-inference-request.example.json     # Inference request
│   │
│   ├── artifact-manifests/
│   │   ├── training-summary.example.json           # Training output manifest
│   │   ├── best-model-reference.example.json       # Best model reference
│   │   └── inference-output-manifest.example.json  # Inference result manifest
│   │
│   └── docker/
│       ├── docker-compose.conceptual.yml   # Conceptual Docker Compose (non-production)
│       └── environment.example.env         # Environment variable template
│
├── assets/                                    # Supporting materials
│   └── README.md                            # Asset guidelines
│
└── public-safety-checklist.md               # Pre-publication safety review
```

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| **01-context-and-problem.md** | Problem statement, motivation, and business context |
| **02-system-architecture.md** | Complete system architecture with all layers |
| **03-component-responsibilities.md** | Detailed responsibilities of each component |
| **04-system-flow.md** | Request flows, response flows, error handling flows |
| **05-api-integration-contracts.md** | API payload structures and contracts |
| **06-docker-runtime-architecture.md** | Container architecture and runtime design |
| **07-shared-storage-and-artifacts.md** | Storage layer, artifact categories, path mapping |
| **08-yolo-training-engine.md** | YOLO training implementation details |
| **09-continuous-improvement-training.md** | CI training pipeline and baseline comparison |
| **10-sahi-inference-engine.md** | SAHI-based high-resolution inference |
| **11-clearml-experiment-tracking.md** | ClearML integration and experiment management |
| **12-gpu-resource-management.md** | GPU orchestration, CUDA management, memory handling |
| **13-error-handling-and-fallbacks.md** | Error scenarios and mitigation strategies |
| **14-limitations-and-risks.md** | Current limitations and known risks |
| **15-production-evolution-roadmap.md** | Future improvements for production readiness |
| **16-public-release-sanitization.md** | Guidelines for maintaining public safety |
| **17-technical-responsibilities.md** | Portfolio positioning and technical claims |

---

## Current Maturity Level

**Early Production / Advanced Prototype**

- ✅ Core orchestration engine operational
- ✅ Multi-service integration working
- ✅ GPU training and inference functional
- ✅ ClearML experiment tracking implemented
- ✅ Basic error handling and fallbacks in place
- ⚠️ Synchronous long-running tasks (no job queue)
- ⚠️ File-based model registry (race conditions possible)
- ⚠️ Limited observability and monitoring
- ⚠️ No distributed job scheduling
- ❌ Not production-grade for high-throughput scenarios

---

## Key Limitations

### Current State
- **No formal job queue** (Celery, Redis, Kafka, RabbitMQ)
- **Long-running tasks are synchronous** through FastAPI
- **Single FastAPI GPU service** as potential bottleneck
- **Shared filesystem coupling** creates tight dependencies
- **File-based model registry** susceptible to race conditions
- **No transactional model registry**
- **Limited observability** (logs, traces, metrics)
- **No retry logic** with exponential backoff
- **No health checks or preflight validation**

### Why These Exist
These limitations reflect pragmatic early-stage design decisions optimized for initial development and validation rather than high-volume production deployment.

---

## Production Evolution Roadmap

### Phase 1: Reliability (Recommended Next Steps)
- [ ] Implement formal job queue (Celery + Redis)
- [ ] Add transactional model registry (database-backed)
- [ ] Implement health checks and service discovery
- [ ] Add structured logging with correlation IDs
- [ ] Implement retry logic with exponential backoff

### Phase 2: Scalability
- [ ] Move to object storage (S3, GCS, MinIO)
- [ ] Implement distributed GPU worker pool
- [ ] Add job registry and status polling
- [ ] Implement GPU job scheduling and fairness

### Phase 3: Observability
- [ ] Add distributed tracing (Jaeger, DataDog)
- [ ] Implement comprehensive metrics (Prometheus)
- [ ] Add performance monitoring and SLO tracking
- [ ] Implement alerting and anomaly detection

### Phase 4: Production Hardening
- [ ] API versioning and backward compatibility
- [ ] Rate limiting and quota management
- [ ] Advanced security (RBAC, audit logging)
- [ ] Multi-region deployment support
- [ ] Disaster recovery and backup strategies

---

## Confidentiality Policy

**This repository is designed to be publicly shareable while protecting all private IP and sensitive data.**

### Never Commit to This Repository
- ❌ Source code from the private project
- ❌ Real datasets or data
- ❌ Trained model weights (.pt, .pth files)
- ❌ Real metrics or performance results
- ❌ Real coordinates, detections, or predictions
- ❌ Client, institution, farm, field, or researcher names
- ❌ Credentials, API keys, secrets
- ❌ Absolute local paths or environment details
- ❌ ClearML workspace names or infrastructure details
- ❌ Real screenshots or model outputs
- ❌ .env files with actual values

### Always Use
- ✅ Placeholder values (PROJECT_NAME_PLACEHOLDER, etc.)
- ✅ Anonymized examples
- ✅ Generic architectures
- ✅ Illustrative diagrams
- ✅ Conceptual code snippets (documentation only)

---

## 📚 Learning Resources

**For Understanding the Architecture**:
- **[Engineering Case Study](./CASE-STUDY.md)** — Narrative-driven deep dive (35-45 min read)
  - Why Django and FastAPI are separated
  - How components interact and fail
  - Evolution roadmap with trigger metrics
  - Lessons and architectural principles
  
- **[Component Responsibilities](./docs/03-component-responsibilities.md)** — What each part does
  - Responsibility matrix
  - IS/IS NOT boundaries
  - Failure handling strategies
  
- **[Production Evolution Roadmap](./docs/15-production-evolution-roadmap.md)** — Scaling path
  - Phases 1-5 with trigger metrics
  - When to add complexity
  - Cost/benefit analysis

**For Interview Preparation**:
- **[Project Positioning](./PROJECT-POSITIONING.md)** — Talking points and Q&A
  - Elevator pitch (60 seconds)
  - Common interview questions
  - Positioning by audience

- **[Portfolio Positioning Analysis](./PORTFOLIO-POSITIONING-ANALYSIS.md)** — Strategic positioning
  - What this demonstrates
  - Red flags to avoid
  - Interviewer perspective

**For Implementation Details**:
- **[System Architecture](./docs/02-system-architecture.md)** — High-level design overview
- **[Docker Runtime Architecture](./docs/06-docker-runtime-architecture.md)** — Deployment setup
- **[GPU Resource Management](./docs/12-gpu-resource-management.md)** — GPU orchestration
- **[Error Handling](./docs/13-error-handling-and-fallbacks.md)** — Failure scenarios

---

## Getting Started

1. **Read first:** `docs/01-context-and-problem.md`
2. **Understand the design:** `docs/02-system-architecture.md`
3. **Review the flows:** `docs/04-system-flow.md`
4. **Study integration contracts:** `docs/05-api-integration-contracts.md`
5. **Explore component details:** `docs/08-12` (specific technologies)
6. **Review limitations:** `docs/14-limitations-and-risks.md`
7. **Check safety:** `public-safety-checklist.md` before any modifications

---

## Contributing

This is a documentation and architecture reference repository. Contributions should:
- Add accurate, anonymized architecture documentation
- Maintain confidentiality and public safety
- Include meaningful diagrams and examples
- Update the public-safety-checklist before changes
- Follow the maturity statement precisely

---

## License

This repository is licensed under the **MIT License**. See LICENSE file for details.

The documentation is provided as-is for portfolio, educational, and architectural reference purposes.

---

## Questions & Feedback

For questions about architecture patterns, design decisions, or system integration approaches documented here, please refer to the relevant documentation files or open an issue with specific architectural questions.

**Important:** This is a documentation repository, not a support channel for the private production system.

---

**Last Updated:** June 2026
**Repository Type:** Architecture Documentation (Non-Production)
**Status:** Public-Safe Release
