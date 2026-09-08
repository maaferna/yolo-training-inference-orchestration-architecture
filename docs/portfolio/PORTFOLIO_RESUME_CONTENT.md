# Professional Resume & Portfolio Content

> **This document is portfolio-safe**: all content uses anonymized, publicly shareable language.
> No real institutions, clients, projects, dates or measured results are referenced. Safe to
> include in applications, LinkedIn, interviews and portfolios.

**Portfolio-safe resume bullets, LinkedIn description, GitHub description and project card**
**Generated from**: YOLO Training & Inference Orchestration Architecture

## How this content is built

The strongest story this repository tells is not a technology list. It is a set of
**limitation → resolution** pairs: the initial iteration wrote down its limitations and the
triggers that would justify change (`docs/architecture/15`, `16`); a later revision recorded
what happened when those triggers fired (`docs/evolution/`, ADR-009 to ADR-013). Every bullet
below is built on one of those pairs, so each claim can be traced to a document.

One statement of scope, so that nothing below overclaims: **in the later revision, training
runs outside the platform** and enters through an import step that fingerprints the weights,
and **the revision's GPU path was not validated** (its test suite runs on CPU with a mock
runtime). The initial iteration is the one that orchestrated training on the GPU: DataParallel
across two GPUs as the runtime, single-GPU as the fallback, DDP deferred. See
`docs/evolution/00-what-came-next.md`.

Verbs are design verbs throughout — *designed, documented, specified, proposed, evaluated* —
because this repository documents an architecture; the implementation remains private.

---

## 1. MACHINE LEARNING ENGINEER - Resume Bullets (5)

### Bullet #1: Multi-Seed Validation and Model Selection
**Limitation**: A single training run is biased by its random initialization, and the initial
iteration selected the best model inside the training loop as a side effect.
**Resolution**: Multi-seed training with validation-based aggregation; in the later revision,
selection became a registry act after validation, never a training side effect (ADR-010).

```
• Designed a multi-seed YOLO training strategy with validation-based
  model selection and explicit CUDA cleanup between seeds, so runs
  are comparable rather than contaminated by the previous seed's
  state; later specified that selection is a registry decision after
  validation, displayed to a person, not an automatic side effect of
  the training loop
```

**Why this matters**: shows reproducibility and statistical reasoning, and the maturity to
move a decision out of the loop that produced it.

---

### Bullet #2: GPU Memory Management and OOM Recovery
**Limitation**: An out-of-memory error ended the run.
**Resolution**: Progressive resource scaling and fallback validation, documented in
`docs/architecture/13` and `14`.

```
• Designed a CUDA memory management pattern for sequential multi-seed
  training: explicit cache release and memory-stat reset between
  seeds, progressive resource scaling on OOM (batch size, then image
  size) and fallback validation when the training call returns no
  result, so an OOM degrades the run instead of terminating it
```

**Why this matters**: hands-on GPU runtime reasoning, kept distinct from distributed
orchestration.

---

### Bullet #3: Experiment Tracking Without Data Egress
**Limitation**: The initial tracking tool defaulted to a hosted endpoint and uploaded sample
imagery as part of its default logging — a leak path where images are the confidential asset.
**Resolution**: Local artifacts and run manifests as the source of truth; the tool withdrawn on
data-egress grounds; a self-hosted, tracking-only server decided and not deployed (ADR-012).

```
• Designed experiment tracking with local artifacts and a per-run
  manifest as the source of truth and a tracker as metadata only;
  later evaluated the initial tool's default data egress as a security
  property, documented its withdrawal, and specified a self-hosted
  tracking-only replacement whose deployment waits for an in-platform
  producer (ADR-012)
```

**Why this matters**: MLOps judgment that treats a vendor default as a security decision, not
a convenience.

---

### Bullet #4: High-Resolution Small-Object Detection
**Limitation**: Small objects fall below the detector's effective resolution at full-frame
scale.
**Resolution**: SAHI tiled inference with configurable overlap and detection reconstruction
(`docs/architecture/11`, ADR-005).

```
• Specified a SAHI tiling strategy for high-resolution inference:
  per-tile YOLO detection with configurable overlap, reconstruction of
  tile detections into image coordinates, and a documented
  compute-versus-accuracy trade-off between tile size, overlap and
  the number of tiles per image
```

**Why this matters**: computer-vision reasoning beyond a benchmark score.

---

### Bullet #5: From Conditional Model Updates to a Registry
**Limitation**: The continuous-improvement loop updated a file-based "best model" reference
automatically, and two concurrent runs could overwrite each other (`docs/architecture/10`).
**Resolution**: A transactional model registry with fingerprints, human promotion and rollback
(ADR-010).

```
• Designed a continuous-improvement training loop with baseline
  comparison and threshold-gated model updates; documented the race
  condition in the file-based model reference and specified its
  resolution: versions with weight fingerprints, promotion and rollback
  as single transactions with an event naming the previous version,
  performed by a person rather than by the training job
```

**Why this matters**: production thinking — preventing regressions and answering lineage
questions matter as much as improvements.

---

## 2. BACKEND / AI PLATFORM ENGINEER - Resume Bullets (5)

### Bullet #1: Service Separation and the End of the Open Request
**Limitation**: The HTTP request stayed open for the whole GPU job; timeouts arrived and
operators had no progress.
**Resolution**: Submit returns a run identifier; the job runs on an in-process pool with a
durable job record; the console polls. No broker (ADR-009).

```
• Designed a two-service architecture separating web orchestration
  (Django/DRF) from GPU compute (FastAPI) behind an HTTP boundary;
  when request timeouts arrived, specified submit/poll execution on
  in-process pools with a durable job record per run, a job-history
  table and startup reconciliation — deliberately without a queue,
  because one host and one device leave nothing to dispatch to
```

**Why this matters**: the core backend decision, and the discipline to answer a trigger with
the smallest change that closes it.

---

### Bullet #2: GPU Compute Orchestration
**Limitation**: GPU-bound work inside a web process takes the application down with it.
**Resolution**: A dedicated compute service owning the GPU runtime, with the runtime scope
stated honestly.

```
• Designed the AI service boundary that owns YOLO training, validation
  and inference on CUDA; documented DataParallel across two GPUs as
  the training runtime, single-GPU as the fallback and DDP deferred
  pending a runtime audit, keeping multi-GPU runtime distinct from
  distributed job orchestration throughout
```

**Why this matters**: systems thinking with a precise claim about what was exercised.

---

### Bullet #3: Service Contracts
**Limitation**: Error handling was prose that callers parsed; paths were translated across four
coordinate systems; any caller could submit GPU work.
**Resolution**: One error envelope with stable codes, one run manifest, service tokens,
and a same-path invariant in place of path translation (`docs/evolution/03`, ADR-011).

```
• Specified the contracts between web and compute services: a single
  error envelope with a catalogued set of stable codes, an append-only
  run manifest with relative paths, a service key compared in constant
  time between the services and hashed bearer tokens for automation
  clients; replaced a path-translation layer with a same-path mount
  invariant asserted at startup and covered by a test
```

**Why this matters**: production systems are defined by their contracts and their failure
modes.

---

### Bullet #4: Artifact Storage, Configuration and Governance
**Limitation**: Checkpoints and outputs scattered on a shared volume with no versioning; the
best-model file was the de-facto registry.
**Resolution**: Artifact categories and risks documented; a database-backed registry exporting
a fingerprint-verified list the compute service resolves models through (ADR-002, ADR-010).

```
• Designed the shared artifact storage layer and its risk register
  (path fragility, permissions, stale caches, disk growth); specified a
  database-backed model registry that exports a list of loadable
  versions with fingerprints, so the compute service refuses arbitrary
  paths; designed ORM-backed dataset configuration with generated
  YOLO-compatible YAML
```

**Why this matters**: full-stack thinking from database to compute to storage.

---

### Bullet #5: Evolution by Evidence, Then the Ledger
**Limitation**: Roadmaps that promise infrastructure on a calendar are never checked.
**Resolution**: A roadmap gated by named triggers, and a trigger-by-trigger ledger of what was
realized, realized differently, not triggered or discarded (`docs/architecture/16`,
`docs/evolution/07`).

```
• Documented a production evolution roadmap in which a queue, a
  worker pool and Kubernetes are non-goals until a named trigger
  fires; recorded the outcome trigger by trigger — job records,
  polling, registry, contracts and tests were realized, no broker or
  Kubernetes was needed — and specified a mock/real runtime seam with
  a CPU test suite on the order of two thousand tests and CI on a
  throwaway Compose stack
```

**Why this matters**: strategic restraint that can be audited.

---

## 3. COMPUTER VISION ENGINEER - Resume Bullets (5)

### Bullet #1: Small-Object Detection via SAHI Tiling
**Limitation**: Accuracy on small objects degrades in large images.
**Resolution**: Tiling with overlap and reconstruction (`docs/architecture/11`).

```
• Specified a SAHI-based tiled inference pipeline for high-resolution
  images: overlapping tiles, per-tile YOLO detection and
  reconstruction into image coordinates; documented the trade-off
  between tile size, overlap and compute so the strategy can be chosen
  from the expected object size rather than fixed
```

**Why this matters**: practical CV on real-world image sizes.

---

### Bullet #2: Multi-Seed Experimental Validation
**Limitation**: Single-run selection biased by initialization.
**Resolution**: Multi-seed training, aggregated validation metrics, CUDA cleanup between seeds.

```
• Designed a multi-seed validation framework selecting on aggregated
  validation metrics across seeds, with explicit CUDA cleanup so each
  seed starts from a clean device state; later specified that the
  selection score is displayed for a person to act on rather than
  promoted automatically (ADR-010)
```

**Why this matters**: rigor in model selection, and restraint in automating it.

---

### Bullet #3: Dataset Configuration Management
**Limitation**: Hand-edited dataset YAML is error-prone and unversioned.
**Resolution**: ORM-backed configuration (`ProjectConfiguration`, `ClassSet`,
`DetectionClass`, `DatasetConfiguration`) with generated YOLO-compatible YAML
(`docs/architecture/08`).

```
• Designed a database-backed YOLO dataset configuration layer with
  project, class-set and detection-class models and automatic
  generation of training-compatible YAML, so label schemas and dataset
  definitions are versioned records rather than files edited by hand
```

**Why this matters**: configuration as data, not as manual files.

---

### Bullet #4: Detection Metrology
**Limitation**: Detections stopped at pixel boxes; operators asked for physical quantities.
**Resolution**: A CPU-bound metrology job type in the AI service turning boxes into physical
size, clusters, coverage and density, with gates (`docs/evolution/04`, ADR-013).

```
• Designed a detection-metrology job type that converts pixel
  detections into planar physical sizes, clusters, coverage and
  density using preserved image metadata, placed in the AI service as
  a CPU job with its own record and manifest so results are
  reproducible artifacts; documented that the method is not yet
  validated against ground truth
```

**Why this matters**: turns a detector into an instrument, and says what remains unproven.

---

### Bullet #5: Operator Console with Geospatial Results
**Limitation**: Results shown as image previews only; operators asked "where".
**Resolution**: GeoJSON per batch rendered on an interactive map; batch progress by polling;
localization with a guard test (`docs/evolution/05`).

```
• Designed an operator console that renders per-batch GeoJSON
  (footprints, detections per class, foci, coverage) on an interactive
  map from a vendored library with no build step, exposes the same
  GeoJSON for desktop GIS, polls batched job status for progress, and
  enforces localization with a guard test that fails on any
  untranslated string
```

**Why this matters**: CV output that an operator can act on.

---

## 4. LINKEDIN PROJECT DESCRIPTION

### Title
**YOLO Training & Inference Orchestration: Architecture for an Internal AI Vision Platform**

### Description

```
Designed and documented the architecture of an internal computer-vision
platform that separates web orchestration from GPU-bound YOLO training
and inference — and, unusually, recorded what happened when its
declared limitations were reached.

THE INITIAL ITERATION
• Django web layer (metadata, configuration, visualisation) separated
  from a FastAPI AI service that owns the GPU runtime
• Multi-seed YOLO training with validation-based selection and CUDA
  cleanup between seeds; DataParallel across two GPUs, single-GPU
  fallback, DDP deferred
• SAHI tiled inference for small objects in high-resolution images
• Tracking with local artifacts as the source of truth
• Limitations stated in writing: the request stays open for the whole
  job, a file-based model reference with a race condition, path
  translation across containers, no tests, no CI

THE LATER REVISION — limitation by limitation
• Timeouts arrived: submit/poll on in-process pools with durable job
  records and startup reconciliation, not a queue (ADR-009)
• Model reference race: transactional registry with weight
  fingerprints, human promotion and rollback (ADR-010)
• Path translation: replaced by a same-path invariant, tested (ADR-011)
• Tracking tool withdrawn on data-egress grounds; a self-hosted
  tracking-only server decided and not deployed (ADR-012)
• Contracts: one error envelope, one run manifest, service tokens
• Detection metrology as a CPU job type: physical size, coverage,
  density (ADR-013)
• Operator console with GeoJSON maps and a localization guard test
• Mock/real runtime seam, a CPU test suite on the order of two
  thousand tests, CI on a throwaway Compose stack
• Still no broker, no worker pool, no Kubernetes — the triggers never
  fired

STATED HONESTLY
Training runs outside the platform in the later revision and enters
through a fingerprinted import; the revision's GPU path was not
validated. The initial iteration is the one that orchestrated training
on the GPU.

TECHNOLOGIES
Django, FastAPI, PyTorch, Ultralytics YOLO, SAHI, PostgreSQL, CUDA,
Docker Compose, Git

REPOSITORY
github.com/maaferna/yolo-training-inference-orchestration-architecture

Architecture is documented in detail; the implementation remains
private. The value is in the decisions, their triggers and their
outcomes.
```

---

## 5. GITHUB REPOSITORY DESCRIPTION

### Short Description (GitHub main)

```
Architecture of an internal YOLO training and inference platform:
web orchestration separated from GPU compute, limitations stated,
and a later revision that records what each limitation became —
job records instead of a queue, a registry instead of a file, a
same-path invariant instead of path translation.
```

### Long Description (GitHub About section)

```
YOLO Training & Inference Orchestration Architecture

Public-safe architecture documentation for an internal AI vision
platform separating user-facing web workflows from GPU-intensive
machine learning workloads.

WHAT IT ARGUES

- No job queue, no worker pool, no Kubernetes: each is a non-goal
  with the operational evidence that would justify it.
- The risks are stated: synchronous execution, filesystem coupling, a
  race on the file-based model reference, GPU contention.
- Cost is an architectural decision: where training runs and where
  the application lives are reasoned about separately.

WHAT HAPPENED NEXT (docs/evolution/)

- Timeouts: submit/poll on in-process pools with durable job records
  (ADR-009), not a queue
- Model reference race: transactional registry, fingerprints, human
  promotion, rollback (ADR-010)
- Path translation: same-path invariant (ADR-011)
- Tracking tool withdrawn on data-egress grounds; self-hosted
  tracking-only server decided, not deployed (ADR-012)
- Contracts: error envelope, run manifest, service tokens
- Detection metrology as a CPU job type (ADR-013)
- Operator console: GeoJSON maps, localization guard test
- Mock/real runtime seam, CPU test suite on the order of two thousand
  tests, CI on a throwaway Compose stack
- Training moved outside the platform (fingerprinted import); the
  revision's GPU path was not validated

WHAT'S INCLUDED

- Architecture documents 01 to 21
- Architecture Decision Records ADR-001 to ADR-013
- Evolution documents 00 to 07, including a trigger-by-trigger ledger
- Diagrams and a poster generated from one build script
- A sanitization gate and a public-safety checklist

WHAT'S NOT INCLUDED

- Source code, datasets, weights, measured results
- Credentials, infrastructure identifiers, absolute paths
- Names of organizations, sites, people or hardware

TECHNOLOGIES

Backend: Django, FastAPI, PostgreSQL
ML/CV: PyTorch, Ultralytics YOLO, SAHI, SAM
Runtime: Docker Compose, CUDA, DataParallel (DDP deferred)

DOCUMENTATION STRUCTURE

docs/architecture/          Documents 01 to 21 (the initial iteration)
docs/architecture/adr/      ADR-001 to ADR-013
docs/evolution/             The later revision, 00 to 07
docs/portfolio/             This material

PHILOSOPHY

Add infrastructure when a named trigger fires, and expect the evidence
to ask for less than a queue.
```

---

## 6. PORTFOLIO WEBSITE - PROJECT CARD

````markdown
## YOLO Training & Inference Orchestration Architecture

**Role:** Architect and author | **Technologies:** Django, FastAPI, PyTorch, YOLO, SAHI, CUDA, Docker Compose
**Status:** Documented architecture with a recorded later revision | **Public-safe:** yes

### Overview

An internal computer-vision platform where a small group of operators
submits YOLO training and high-resolution inference jobs. Web
orchestration (Django) is separated from GPU compute (FastAPI) behind
an HTTP boundary with shared artifact storage between them. The
design problem is not scale; it is keeping GPU-bound work from taking
down a web application, and keeping its artifacts traceable.

### Limitation → Resolution

| Limitation stated in the initial iteration | Resolution in the later revision | Record |
|---|---|---|
| The request stays open for the whole job | Submit/poll on in-process pools, durable job records, startup reconciliation — no queue | ADR-009 |
| File-based model reference with a race | Transactional registry, weight fingerprints, human promotion, rollback | ADR-010 |
| Path translation across containers | Same-path mount invariant, asserted and tested | ADR-011 |
| Tracking tool with data egress by default | Withdrawn; manifests as source of truth; self-hosted tracking-only server decided, not deployed | ADR-012 |
| Errors as prose, no service authentication | One error envelope, one run manifest, service tokens | evolution 03 |
| Detections stop at pixel boxes | Metrology job type: physical size, clusters, coverage, density | ADR-013 |
| Results as image previews only | Operator console with GeoJSON maps; localization guard test | evolution 05 |
| No tests, no CI | Mock/real runtime seam; CPU suite on the order of two thousand tests; CI on a throwaway Compose stack | evolution 06 |
| Queue, worker pool, Kubernetes as non-goals | Not triggered; recorded as such | evolution 07 |

### Scope, stated plainly

In the later revision, training runs outside the platform and enters
through a fingerprinted import; the revision's GPU path was not
validated. The initial iteration orchestrated training on the GPU:
DataParallel across two GPUs, single-GPU fallback, DDP evaluated and
deferred.

### Technical highlights

**Multi-seed training with CUDA hygiene**
```
Train seed → validate → record metrics
release cache, reset memory stats, collect
next seed
→ aggregate validation metrics; selection shown to a person
```

**SAHI tiled inference**
```
Large image → overlapping tiles → per-tile YOLO detection
→ reconstruction into image coordinates → metrology (optional)
```

**Evolution by trigger**
```
Baseline:      synchronous HTTP, DataParallel on two GPUs
Trigger fired: timeouts → submit/poll, job records (no broker)
Trigger fired: lineage questions → registry with promotion events
Open trigger:  jobs compete for the device → single admission lane
Not triggered: distributed workers, object storage, Kubernetes
```

### Documentation

- Architecture documents `01`–`21`, ADR-001 to ADR-013, evolution documents `00`–`07`
- Diagrams and a poster generated from a single build script
- A sanitization gate that blocks paths, credentials, dates and identifiers

**Repository**: github.com/maaferna/yolo-training-inference-orchestration-architecture
**Decision records**: docs/architecture/adr/
**Later revision**: docs/evolution/
````

---

## 7. SUMMARY TABLE - Content for Different Platforms

| Platform | Use this | Purpose |
|----------|----------|---------|
| **Resume** | Bullets from sections 1–3 | Specific, traceable bullets |
| **LinkedIn** | Section 4 | Project showcase with the limitation → resolution arc |
| **GitHub** | Section 5 | Discovery and credibility |
| **Portfolio website** | Section 6 | Deep dive with the resolution table |
| **Interview prep** | All sections plus `docs/architecture/18-technical-responsibilities.md` | Talking points about decisions and triggers |
| **Email / outreach** | Section 4 condensed | Quick value proposition |

---

## 8. CUSTOMIZATION GUIDE

### For Machine Learning roles
Lead with: multi-seed validation, OOM recovery, tracking without egress (bullets 1–3).
Emphasize: reproducibility, why selection left the training loop, why the tracker was withdrawn.

### For Backend / Platform roles
Lead with: service separation and submit/poll, contracts, evolution ledger (bullets 1, 3, 5).
Emphasize: answering a trigger with the smallest change; contracts; tests without a GPU.

### For Computer Vision roles
Lead with: SAHI, metrology, operator console (bullets 1, 4, 5).
Emphasize: small objects, physical quantities, what is not yet validated.

### For AI / MLOps lead roles
Lead with: the full limitation → resolution table (section 6) and the ledger
(`docs/evolution/07-roadmap-realized.md`).
Emphasize: restraint that can be audited; decisions reversed with a superseding record.

---

## 9. TIPS FOR USING THIS CONTENT

### DO
- Adapt bullets to the job description; keep the limitation → resolution shape.
- Describe outcomes, not invented numbers. This repository documents architecture, so it
  cannot evidence a percentage. If you have a measured figure from private work, it belongs
  on your CV — never in this public repository, and never sourced back to it.
- Use design verbs: designed, documented, specified, proposed, evaluated.
- Name the record: "see ADR-009" is stronger than "we added polling".
- State the scope once: training outside the platform in the later revision; GPU path not
  validated there.

### DON'T
- Claim the code is production-deployed or that the repository contains it.
- Present the initial tracking tool as current; it was withdrawn (ADR-012).
- Claim a queue, a worker pool or Kubernetes; they were not triggered.
- Date anything by calendar or quarter; the repository orders by iteration only.
- Give self-assessed maturity levels or counts that no document in the repository states.
- Mention client, institution, site, person or hardware names.

### FRAMING
"I designed and documented the architecture of an internal AI vision platform that separates
web orchestration from GPU compute, wrote down its limitations and the triggers that would
justify change, and recorded what a later revision did when those triggers fired — job records
instead of a queue, a registry instead of a file, contracts and tests instead of prose. The
implementation remains private; the public repository holds the decisions and their outcomes."

---

**Source repository**: github.com/maaferna/yolo-training-inference-orchestration-architecture
**Status**: public-safe portfolio content
