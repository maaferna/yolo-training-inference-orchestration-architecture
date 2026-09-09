# YOLO Training & Inference Orchestration Architecture

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-Web%20Application-092E20?style=for-the-badge&logo=django&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-AI%20Service-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Metadata%20Store-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![REST API](https://img.shields.io/badge/REST%20API-Service%20Integration-005571?style=for-the-badge)

> **Documentation only.** Generalized and anonymized architecture for an internal AI vision
> platform. No source code, datasets, model weights, credentials, real infrastructure details or
> measured results. Every number, path and identifier shown is an illustrative placeholder.
> The full rule is in [`17-public-release-sanitization.md`](./docs/architecture/17-public-release-sanitization.md);
> contributors follow [`CONTRIBUTING.md`](./CONTRIBUTING.md) and a validation gate.

An internal platform where a limited group of operators and researchers submit YOLO training and
high-resolution inference jobs. The design problem is not scale — it is keeping GPU-bound work
from taking down a web application, and keeping the artifacts it produces traceable.

[![System architecture](./assets/diagrams/01-system-architecture.png)](./assets/diagrams/01-system-architecture.png)

## What this repository argues

Most architecture write-ups list what was built. This one is mostly about what was **not** built,
and why:

- **No job queue, no worker pool, no Kubernetes** — each is named as a non-goal with the specific
  operational evidence that would justify it. See [the evolution roadmap](./docs/architecture/16-production-evolution-roadmap.md).
- **The risks are stated, not hidden** — synchronous execution blocking the request, filesystem
  coupling between services, a race condition on the file-based model reference, GPU contention.
  See [limitations and risks](./docs/architecture/15-limitations-and-risks.md).
- **Cost is an architectural decision** — where training runs and where the application lives are
  reasoned about separately, from data volume and GPU hours.
  See [deployment and cost strategy](./docs/architecture/20-deployment-cost-strategy.md).
- **What came next is on the record** — when the triggers fired, a later revision answered with
  job records, a registry, contracts and tests, not a queue. It also moved training out of the
  platform and left its GPU path unvalidated, and says so.
  See [what came next](./docs/evolution/00-what-came-next.md).

## Start here

| If you have | Read |
|---|---|
| 30 seconds | The diagram above, and [the poster](./assets/poster/poster-architecture.png) |
| 5 minutes | [The questions this architecture answers](#the-questions-this-architecture-answers) |
| A hiring decision | [Limitations](./docs/architecture/15-limitations-and-risks.md), then [what a later revision did about them](./docs/evolution/00-what-came-next.md), then the [ADRs](./docs/architecture/adr/) |
| An hour | [`01-context-and-problem.md`](./docs/architecture/01-context-and-problem.md) onward, in order |

Reading paths by audience, each ending in the evolution section:

| Audience | Path |
|---|---|
| Portfolio reviewer | `01-context-and-problem` → `18-technical-responsibilities` → `evolution/00` → `evolution/07` |
| Backend / platform | `02-system-architecture` → `05-api-integration-contracts` → `06-docker-runtime-architecture` → `evolution/01` → `evolution/03` |
| ML / computer vision | `09-yolo-training-engine` → `11-sahi-inference-engine` → `13-gpu-resource-management` → `evolution/02` → `evolution/04` |
| Architecture reviewer | `02-system-architecture` → `15-limitations-and-risks` → `16-production-evolution-roadmap` → `evolution/07` → ADRs |

---

## Scope and maturity

This documents an architecture for a **controlled internal deployment**, not a public SaaS
product, a multi-tenant platform or a globally distributed service. The expected users are a
limited group of operational, technical and research staff submitting scheduled or occasional
jobs. At that scale a single node with Docker Compose, a dedicated AI service, GPU-backed
execution and shared artifact storage is sufficient.

| Aspect | Status | Notes |
|--------|--------|-------|
| Deployment context | Internal platform | Controlled organizational use, not public multi-tenant SaaS |
| Request handling | Synchronous in the initial iteration | Replaced by submit/poll in a later revision — [ADR-009](./docs/architecture/adr/ADR-009-submit-poll-in-process-execution.md) |
| Job queuing | Non-goal until triggered | The trigger fired and the answer was still not a queue — [`evolution/07`](./docs/evolution/07-roadmap-realized.md) |
| Training GPU execution | DataParallel on two GPUs | Single-GPU is the fallback; DDP evaluated and deferred — [`13`](./docs/architecture/13-gpu-resource-management.md) |
| Distributed job orchestration | Not implemented | No worker pool, scheduler or distributed job registry |
| Kubernetes | Not required | Docker Compose fits the operational scale |
| Model registry | File-based, then transactional | The file reference and its race were replaced — [ADR-010](./docs/architecture/adr/ADR-010-transactional-model-registry.md) |
| Observability | Basic | Structured logs, job status and health checks over distributed tracing |
| High availability | Optional | Redundancy is a business decision, not an architectural default |

**Not demonstrated here:** public SaaS architecture, high-throughput multi-tenant serving, a
current Kubernetes requirement, multi-region or high-availability design for external customers,
source-level implementation of the private system, or a fully automated enterprise MLOps platform.

**Philosophy:** build for the real operational context. Reliability, traceability and artifact
governance return more, at this scale, than any distributed component added ahead of the evidence
for it.

---

## Architecture and components

```text
User / Operator
      ↓
Django Web Layer
      ↓ HTTP
FastAPI AI Service Layer
      ↓
YOLO / SAHI / Training Runtime
      ↓
GPU Runtime + Shared Artifact Storage
      ↓
Django Result Visualization
```

Explicit responsibility separation is what keeps failure modes reasonable:

| Component | Owns | Must not own | Detail |
|---|---|---|---|
| Django web layer | Web UI, authentication, request metadata, dataset configuration, result visualization | GPU-heavy execution | [`03`](./docs/architecture/03-component-responsibilities.md) |
| FastAPI AI service | Training orchestration, inference dispatch, validation, experiment coordination | User authentication, web presentation | [`03`](./docs/architecture/03-component-responsibilities.md), [ADR-003](./docs/architecture/adr/ADR-003-fastapi-gpu-service.md) |
| YOLO training engine | Multi-seed training, validation, metric extraction, checkpoints | Request handling | [`09`](./docs/architecture/09-yolo-training-engine.md) |
| Continuous improvement | Incremental retraining against a baseline, model reference update | Unconditional promotion | [`10`](./docs/architecture/10-continuous-improvement-training.md) |
| SAHI inference layer | Tiling, small-object inference, detection reconstruction | Model selection | [`11`](./docs/architecture/11-sahi-inference-engine.md) |
| Experiment tracking | Run metadata, metrics, artifact references, lineage | Being the source of truth for artifacts | [`12`](./docs/architecture/12-clearml-experiment-tracking.md), [ADR-012](./docs/architecture/adr/ADR-012-experiment-tracking-revised.md) |
| Dataset configuration | Project definitions, detection classes, class sets, dataset files | Training execution | [`08`](./docs/architecture/08-yolo-dataset-configuration-management.md) |
| Synthetic dataset workflow | SAM-assisted extraction, composition, annotation export | Being a production path | [`21`](./docs/architecture/21-synthetic-dataset-generation-pipeline.md), [ADR-006](./docs/architecture/adr/ADR-006-notebooks-auxiliary-research.md) |
| Relational database | User data, configuration, request records | ML outputs and generated files | [`07`](./docs/architecture/07-shared-storage-and-artifacts.md) |
| Shared artifact storage | Checkpoints, outputs, previews, reports | Structured metadata | [`07`](./docs/architecture/07-shared-storage-and-artifacts.md), [ADR-002](./docs/architecture/adr/ADR-002-shared-artifact-storage.md) |

> Public-safe names are used throughout: `ProjectConfiguration`, `DetectionClass`, `ClassSet`
> and `DatasetConfiguration`.

Full boundary reasoning is in [`02-system-architecture.md`](./docs/architecture/02-system-architecture.md).

---

## Diagrams and posters

All are generated from [`scripts/build_visuals.py`](./scripts/build_visuals.py); the PNGs and the
SVGs in `assets/src/` are build products, not hand-edited files. Regenerate with
`./scripts/render-visuals.sh` (needs `python3` and `rsvg-convert`).

| Diagram | What it answers |
|---|---|
| [01 · System architecture](./assets/diagrams/01-system-architecture.png) | How the layers separate and what talks to what |
| [02 · Training request flow](./assets/diagrams/02-training-flow.png) | What happens between a submitted request and a selected model |
| [03 · Continuous improvement](./assets/diagrams/03-ci-training-flow.png) | How the system decides whether a new model replaces the old one |
| [04 · SAHI tiled inference](./assets/diagrams/04-sahi-inference.png) | Why tiling recovers small objects, and what it costs |
| [05 · Deployment and cost strategy](./assets/diagrams/05-deployment-strategy.png) | Local, cloud or hybrid — and the reasoning behind the choice |
| [06 · Synthetic dataset generation](./assets/diagrams/06-synthetic-dataset.png) | How scarce annotated data is expanded into a usable dataset |
| [07 · Production evolution roadmap](./assets/diagrams/07-evolution-roadmap.png) | What gets added first, which trigger justifies it, and what a later revision realized |
| [08 · Submit/poll execution lifecycle](./assets/diagrams/08-submit-poll-lifecycle.png) | How the later revision answered timeouts without a queue |
| [09 · Model registry and promotion](./assets/diagrams/09-model-registry-promotion.png) | How the file-based model reference became version records with human promotion |
| [10 · Detection metrology](./assets/diagrams/10-detection-metrology.png) | How detections become physical sizes, foci, coverage and density, and why each carries a status |
| [11 · Testing and CI without a GPU](./assets/diagrams/11-testing-and-ci.png) | How a mock/real runtime seam made the platform reviewable, and what is deliberately not tested |

Two one-page sheets, sized for print and for portfolio use:
[**Architecture**](./assets/poster/poster-architecture.png) covers the system, the execution flows
and the defining decisions;
[**What came next**](./assets/poster/poster-what-came-next.png) covers the later revision — what
stayed, each confessed limitation and its resolution, and what the revision deliberately did not do.

---

## Technology stack

| Layer | Technology | Integration pattern |
|-------|------------|---------------------|
| Web | Django + Django REST Framework | Request validation, user workflows, database-backed metadata |
| AI service | FastAPI | Internal service boundary for GPU-backed training and inference |
| Training | PyTorch + Ultralytics YOLO | Multi-seed experimentation, validation-based selection, checkpoints |
| Inference | YOLO + SAHI | High-resolution tiling for small-object detection |
| Experiment tracking | Run manifests; a tracker as metadata only | ClearML in the initial iteration, withdrawn later (ADR-012); local artifacts remain the source of truth |
| Database | PostgreSQL or equivalent | User data, project metadata, configuration, request history |
| GPU execution | CUDA + PyTorch | DataParallel across two GPUs; single-GPU fallback; DDP deferred |
| Containerization | Docker Compose | Controlled internal deployment; Kubernetes optional and evidence-gated |
| Storage | Shared volumes | Practical artifact exchange; object storage only if governance becomes hard |
| Annotation and datasets | CVAT, Roboflow | Dataset preparation feeding the configuration layer |
| Research workflow | Jupyter Notebook | Auxiliary experimentation, not the production execution path |
| Synthetic data | SAM + OpenCV + Pillow + NumPy | Object extraction, synthetic composition, annotation export |

**Integration philosophy:** keep concerns separated. HTTP between services, a relational database
for metadata, artifact storage for generated files. Add queues, workers, object storage or
orchestration only when operational evidence justifies the complexity.

---

## The Questions This Architecture Answers

If you want the argument rather than the specification, these are the questions worth reading for:

| Question | Where |
|---|---|
| Why are Django and FastAPI separated at all? | [`ADR-001`](./docs/architecture/adr/ADR-001-separate-web-and-ai-services.md) |
| Why should GPU work never run inside the web layer? | [`03-component-responsibilities.md`](./docs/architecture/03-component-responsibilities.md) |
| When is synchronous execution acceptable, and when does it stop being so? | [`15-limitations-and-risks.md`](./docs/architecture/15-limitations-and-risks.md) |
| What exactly justifies adding a job queue? | [`16-production-evolution-roadmap.md`](./docs/architecture/16-production-evolution-roadmap.md) |
| Why is shared storage both practical and a liability? | [`07-shared-storage-and-artifacts.md`](./docs/architecture/07-shared-storage-and-artifacts.md) |
| Why are notebooks useful for research but not as a production execution model? | [`ADR-006`](./docs/architecture/adr/ADR-006-notebooks-auxiliary-research.md) |
| Why is Kubernetes optional rather than inevitable? | [`16-production-evolution-roadmap.md`](./docs/architecture/16-production-evolution-roadmap.md) |
| Where should training run, and where should the application live? | [`20-deployment-cost-strategy.md`](./docs/architecture/20-deployment-cost-strategy.md) |
| What happened when the triggers actually fired? | [`docs/evolution/07-roadmap-realized.md`](./docs/evolution/07-roadmap-realized.md) |
| How do you replace a synchronous request without adding a queue? | [`docs/evolution/01-submit-poll-execution.md`](./docs/evolution/01-submit-poll-execution.md), [`ADR-009`](./docs/architecture/adr/ADR-009-submit-poll-in-process-execution.md) |
| How was the model-reference race condition closed? | [`docs/evolution/02-model-registry-and-promotion.md`](./docs/evolution/02-model-registry-and-promotion.md), [`ADR-010`](./docs/architecture/adr/ADR-010-transactional-model-registry.md) |
| How is a platform like this tested without a GPU? | [`docs/evolution/06-testing-and-ci-strategy.md`](./docs/evolution/06-testing-and-ci-strategy.md) |

**Flows in one line each**, detailed in [`04-system-flow.md`](./docs/architecture/04-system-flow.md):
a **training** request is validated by the web layer, delegated to the AI service, executed on the
GPU runtime, and returns metrics and a checkpoint; **continuous improvement** resolves the previous
model reference, retrains, and updates it only if the improvement rule holds; **inference** runs
direct or tiled, reconstructs tile detections into image-level outputs and persists artifacts;
**artifact exposure** has the AI service write to shared storage and the web layer resolve and
render what the manifest lists.

---

## Production Evolution Roadmap

Recommended next steps, ordered by return at this scale rather than by ambition. Items marked
realized were addressed in a later revision; the trigger-by-trigger ledger is in
[`07-roadmap-realized.md`](./docs/evolution/07-roadmap-realized.md). Numbers and statuses here
are illustrative, as everywhere in this repository.

**Priority 1 · Reliability**

- [ ] Preflight validation for datasets, storage, models, outputs and GPU availability.
- [x] Explicit job status records. *Realized.*
- [ ] Structured logs with correlation identifiers.
- [x] Artifact manifests for generated outputs. *Realized.*
- [ ] Storage and GPU health checks.
- [ ] Backup and retention policies.

**Priority 2 · Controlled background execution**

- [x] ~~A lightweight queue~~ Timeouts arrived; the response was submit/poll on in-process pools, **not a queue**. *Realized differently.*
- [ ] A single GPU worker or admission lane — **the open trigger**: jobs can still compete for the device.
- [ ] Job cancellation and retry policy.
- [x] Progress and status polling. *Realized.*

**Priority 3 · Governance**

- [x] A database-backed model reference registry. *Realized; ADR-010.*
- [ ] Dataset version tracking, linked to training runs.
- [x] Validate generated artifacts before visualization. *Realized through the manifest contract.*

**Optional scale-out**, none of which was triggered: distributed workers, object storage,
Kubernetes. Each waits for concurrent long-running load, storage that is hard to govern locally,
or an uptime commitment. Full reasoning in
[`16-production-evolution-roadmap.md`](./docs/architecture/16-production-evolution-roadmap.md).

---

## Documentation index

The canonical map, with a one-line purpose per document, is
[`docs/README.md`](./docs/README.md). The shape of it:

```text
docs/
├── architecture/     01..21, the initial iteration; adr/ holds ADR-001..008 (initial) and 009..013 (revision)
├── evolution/        00..07, what a later revision did when the triggers fired
├── operations/       retired operational calendar; README explains where its content went
└── portfolio/        resume, profile and interview material
assets/               generated diagrams and posters · diagrams/ Mermaid sources · examples/ payloads and manifests
scripts/              validate-sanitization.sh (public-safe gate), build_visuals.py, render-visuals.sh
```

**Architecture, `01` to `21`** — the reading order; gaps and duplicates are treated as defects.
Problem and context (`01`), system architecture (`02`), component responsibilities (`03`), flows
(`04`), API contracts (`05`), Docker runtime (`06`), shared storage and artifacts (`07`), dataset
configuration (`08`), training engine (`09`), continuous improvement (`10`), SAHI inference (`11`),
experiment tracking (`12`), GPU resource management (`13`), error handling (`14`), limitations and
risks (`15`), evolution roadmap (`16`), sanitization policy (`17`), technical responsibilities
(`18`), result synchronization (`19`), deployment and cost (`20`), synthetic datasets (`21`).

**Evolution** — the initial iteration confessed its limitations and named the triggers that would
justify change. This section records what a later revision did when they fired.

| Document | Purpose |
|----------|---------|
| [`00-what-came-next.md`](./docs/evolution/00-what-came-next.md) | What stayed, what changed, what left the platform, what was not validated |
| [`01-submit-poll-execution.md`](./docs/evolution/01-submit-poll-execution.md) | Run identifier on submit, in-process pools, durable job records, no broker |
| [`02-model-registry-and-promotion.md`](./docs/evolution/02-model-registry-and-promotion.md) | Versions with fingerprints, human promotion in one transaction, rollback |
| [`03-service-contracts.md`](./docs/evolution/03-service-contracts.md) | One error envelope, one run manifest, authentication, same-path invariant |
| [`04-detection-metrology.md`](./docs/evolution/04-detection-metrology.md) | From pixel boxes to physical size, foci, coverage and density, with gates |
| [`05-operator-console.md`](./docs/evolution/05-operator-console.md) | Batches with progress, GeoJSON on an interactive map, localization guard test |
| [`06-testing-and-ci-strategy.md`](./docs/evolution/06-testing-and-ci-strategy.md) | Mock/real runtime seam, contract tests, CI on a throwaway Compose stack |
| [`07-roadmap-realized.md`](./docs/evolution/07-roadmap-realized.md) | The roadmap of `16`, trigger by trigger: realized, not triggered, discarded |

Decision records of the revision: [ADR-009](./docs/architecture/adr/ADR-009-submit-poll-in-process-execution.md) execution ·
[ADR-010](./docs/architecture/adr/ADR-010-transactional-model-registry.md) registry ·
[ADR-011](./docs/architecture/adr/ADR-011-single-mount-path-invariant.md) storage path ·
[ADR-012](./docs/architecture/adr/ADR-012-experiment-tracking-revised.md) tracking ·
[ADR-013](./docs/architecture/adr/ADR-013-metrology-in-the-ai-service.md) metrology placement.
The [ADR index](./docs/architecture/adr/README.md) says which supersede which.

**Companion repository** — the script-level pipelines this platform orchestrates (YOLO and SAHI
inference with geospatial export, COCO evaluation, video tracking, dataset validation and
benchmarking, and the training runtime itself) are documented in
[`agridrone-vision-evaluation-pipeline`](https://github.com/maaferna/agridrone-vision-evaluation-pipeline).
That repository answers *how a run is computed and evaluated*; this one answers *how runs are
requested, tracked, stored and governed*. Neither repeats the other.

---

## Contributing and licence

Contributions preserve the public-safe standard, avoid implementation leakage, keep the initial
iteration and the later revision clearly separated, and align roadmap items with operational
evidence rather than speculation. The workflow and the validation gate are in
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

| What | Licence | File |
|---|---|---|
| Documentation, diagrams and generated images | CC BY 4.0 | [`LICENSE-DOCS`](./LICENSE-DOCS) |
| Executable content — `scripts/` | MIT | [`LICENSE`](./LICENSE) |

Reuse of the diagrams is welcome under attribution: credit this repository and link back to it.
This is a documentation repository, not a support channel for any private system; open an issue
with a specific architecture question.
