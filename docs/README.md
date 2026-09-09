# Documentation Index

The canonical index of this repository, with a one-line purpose per document. The root
[`README.md`](../README.md) carries the argument and the reading paths; this file carries the map.

```text
docs/
├── architecture/     01..21, the initial iteration
│   └── adr/          ADR-001..008 (initial iteration), ADR-009..013 (later revision)
├── evolution/        00..07, what a later revision did when the triggers fired
├── portfolio/        resume, profile and interview material
└── operations/       retired operational calendar; its README says where the content went
```

## Architecture — the initial iteration

Numbered `01` to `21`; the numbering is the reading order, and gaps or duplicates are treated as
defects. Several of these documents carry a banner marking them as the initial iteration and
pointing at the later revision that changed them.

| Document | Purpose |
|----------|---------|
| [`01-context-and-problem.md`](./architecture/01-context-and-problem.md) | Problem statement, context, and design motivation |
| [`02-system-architecture.md`](./architecture/02-system-architecture.md) | High-level architecture, layer boundaries, GPU and OS runtime decisions |
| [`03-component-responsibilities.md`](./architecture/03-component-responsibilities.md) | What each component owns, and what it must not own |
| [`04-system-flow.md`](./architecture/04-system-flow.md) | Training, inference, configuration and artifact flows |
| [`05-api-integration-contracts.md`](./architecture/05-api-integration-contracts.md) | Conceptual API payloads and integration contracts |
| [`06-docker-runtime-architecture.md`](./architecture/06-docker-runtime-architecture.md) | Container and runtime architecture |
| [`07-shared-storage-and-artifacts.md`](./architecture/07-shared-storage-and-artifacts.md) | Artifact categories, path mapping, and the risks they carry |
| [`08-yolo-dataset-configuration-management.md`](./architecture/08-yolo-dataset-configuration-management.md) | Database-backed dataset configuration and YAML generation |
| [`09-yolo-training-engine.md`](./architecture/09-yolo-training-engine.md) | Training runtime, multi-seed strategy, validation-based selection |
| [`10-continuous-improvement-training.md`](./architecture/10-continuous-improvement-training.md) | Incremental training and the model reference update rule |
| [`11-sahi-inference-engine.md`](./architecture/11-sahi-inference-engine.md) | High-resolution tiled inference and detection reconstruction |
| [`12-clearml-experiment-tracking.md`](./architecture/12-clearml-experiment-tracking.md) | Experiment tracking and lineage, with local artifacts authoritative |
| [`13-gpu-resource-management.md`](./architecture/13-gpu-resource-management.md) | CUDA memory, DataParallel across two GPUs, single-GPU fallback, DDP deferred |
| [`14-error-handling-and-fallbacks.md`](./architecture/14-error-handling-and-fallbacks.md) | Error categories, recovery and mitigation patterns |
| [`15-limitations-and-risks.md`](./architecture/15-limitations-and-risks.md) | Every limitation stated openly, with the trigger that would change it |
| [`16-production-evolution-roadmap.md`](./architecture/16-production-evolution-roadmap.md) | The evidence-gated evolution path and its non-goals |
| [`17-public-release-sanitization.md`](./architecture/17-public-release-sanitization.md) | The public-safe rule this repository is held to |
| [`18-technical-responsibilities.md`](./architecture/18-technical-responsibilities.md) | Portfolio-safe framing of responsibilities and interview material |
| [`19-inference-result-synchronization.md`](./architecture/19-inference-result-synchronization.md) | Getting inference results back to the web layer |
| [`20-deployment-cost-strategy.md`](./architecture/20-deployment-cost-strategy.md) | Local, cloud and hybrid deployment, reasoned from cost |
| [`21-synthetic-dataset-generation-pipeline.md`](./architecture/21-synthetic-dataset-generation-pipeline.md) | SAM-assisted synthetic dataset generation as an auxiliary workflow |

## Evolution — a later revision of the same architecture

Read after `architecture/`. `00` explains what stayed and what changed, `01` to `06` describe the
revision by topic, `07` is the ledger of the roadmap.

| Document | Purpose |
|----------|---------|
| [`00-what-came-next.md`](./evolution/00-what-came-next.md) | What stayed, what changed, what left the platform, what was not validated |
| [`01-submit-poll-execution.md`](./evolution/01-submit-poll-execution.md) | Run identifier on submit, in-process pools, durable job records, no broker |
| [`02-model-registry-and-promotion.md`](./evolution/02-model-registry-and-promotion.md) | Versions with fingerprints, human promotion in one transaction, rollback |
| [`03-service-contracts.md`](./evolution/03-service-contracts.md) | One error envelope, one run manifest, authentication, same-path invariant |
| [`04-detection-metrology.md`](./evolution/04-detection-metrology.md) | From pixel boxes to physical size, foci, coverage and density, with gates |
| [`05-operator-console.md`](./evolution/05-operator-console.md) | Batches with progress, GeoJSON on an interactive map, localization guard test |
| [`06-testing-and-ci-strategy.md`](./evolution/06-testing-and-ci-strategy.md) | Mock/real runtime seam, contract tests, CI on a throwaway Compose stack |
| [`07-roadmap-realized.md`](./evolution/07-roadmap-realized.md) | The roadmap of `16`, trigger by trigger: realized, not triggered, discarded |

## Decision records

[`architecture/adr/`](./architecture/adr/README.md) holds them with a status table saying which
supersede or amend which. ADR-001 to ADR-008 belong to the initial iteration; ADR-009 to ADR-013
to the later revision.

## Portfolio

[`portfolio/`](./portfolio/) holds resume bullets, profile text, a project card and an interview
script, all built on limitation-to-resolution pairs and traceable to the documents above.
