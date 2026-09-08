# Roadmap Realised: Trigger by Trigger

> Public-safe documentation. This is the ledger of `16-production-evolution-roadmap.md` and of
> the README's evolution checklist, read against a later revision. No dates; outcomes only.

## Purpose

`16` argues that infrastructure should be added when a named trigger fires, and lists what
each trigger would justify. A roadmap of that kind is only credible if someone later records
what happened. This document does that, item by item, with one of four outcomes:

- **Realised** — the trigger fired and the item was built as described.
- **Realised differently** — the trigger fired and the response differed from the wording.
- **Not triggered** — the evidence did not appear; the item was correctly not built.
- **Discarded** — the item was considered and rejected for a recorded reason.

## Priority 1: Operational reliability

| Item | Outcome | Notes |
|---|---|---|
| Preflight validation of datasets, storage, models, outputs, GPU | **Realised differently** | Input validation happens synchronously at submit (`01`); model resolution is validated by fingerprint (`02`); GPU availability is injected, not probed (`06`). Dataset validation is a job type. |
| Explicit job status records | **Realised** | Job record per run plus a job-history table (`01`, ADR-009). |
| Structured logs with correlation identifiers | **Realised differently** | Logs are structured; the correlation identifier is the run identifier, present in every record and manifest. A request identifier across the two services is listed as an improvement (`03`). |
| Artifact manifests for generated outputs | **Realised** | One manifest per run, append-only schema, relative paths (`03`). |
| Storage and GPU health checks | **Realised differently** | A health endpoint reports storage root, runtime kind and device state; the device is reported as configured or not, never probed. |
| Backup and retention policies | **Realised** | Database backup with verification; retention is a batch-level cascade rather than a sweep (`01`, `05`). Runbooks exist and are not published. |

## Priority 2: Controlled background execution

| Item | Outcome | Notes |
|---|---|---|
| Lightweight queue, only on timeouts or contention | **Realised differently** | Timeouts fired. The response was submit/poll on in-process pools with durable records, **not a queue** (`01`, ADR-009). |
| Single GPU worker or controlled worker process | **Not triggered → now the open trigger** | The revision admits several jobs at once; contention on the device is the named next trigger (`01`, risks). |
| Job cancellation and retry policy | **Not triggered** | Re-submission by a person after reading the failure reason was sufficient. |
| Progress and status polling | **Realised** | Batched status query; console progress page (`01`, `05`). |
| GPU resource locking | **Not triggered** | Same as the controlled worker: the design recommendation is a single admission lane. |

## Priority 3: Artifact and model governance

| Item | Outcome | Notes |
|---|---|---|
| Database-backed model reference registry | **Realised** | Version and promotion records, one transaction, human promotion, exported list as the AI service's only source (`02`, ADR-010). |
| Dataset version tracking | **Realised differently** | Dataset configurations, label sets and camera calibrations are registered in the web database; the configuration seam to training of `08` exists but has no production caller because training left the platform (`00`). |
| Link training runs to dataset configuration versions | **Realised differently** | The link is on the model version at import, as a reference string; a foreign key waits for dataset versions to be first-class (`02`). |
| Validate generated artifacts before visualisation | **Realised** | Manifest presence and schema are the gate; the console renders only what a manifest lists (`03`, `05`). |

## Optional scale-out

| Item | Outcome | Notes |
|---|---|---|
| Distributed workers | **Not triggered** | One host, one device. |
| Object storage | **Not triggered** | Local volume with a same-path invariant (ADR-011). |
| Kubernetes | **Not triggered** | Compose with overlays for development, CI and deployment variants. |
| Centralised monitoring | **Not triggered** | Health endpoint and structured logs; no tracing. |

## Decisions of the initial iteration that were reversed

| Initial decision | Outcome | Record |
|---|---|---|
| ClearML for experiment tracking (ADR-004, ADR-007) | **Discarded** — withdrawn on data-egress grounds; a self-hosted alternative decided and not deployed | ADR-012 supersedes both |
| Synchronous request from the client's perspective (ADR-003) | **Amended** — boundary kept, execution mode changed | ADR-009 |
| Path translation across containers (ADR-008) | **Discarded** — replaced by a same-path invariant | ADR-011 |
| Automatic model reference update on improvement (`10`) | **Discarded** — replaced by human promotion with an event | ADR-010 |
| In-loop model selection during training (`09`) | **Discarded** — selection is a registry act after validation, not a training side effect | ADR-010 |
| Training as a platform job (`09`, `10`, `03`) | **Moved out** — training in notebooks, weights imported with a fingerprint | `00`, ADR-012 addendum |

## What the revision did not do

Stated plainly, because a ledger that lists only wins is a brochure:

- It did not run training inside the platform.
- It did not validate the GPU path; every test runs on CPU with a mock runtime.
- It did not add a broker, a worker pool, object storage or Kubernetes — and that is the
  point.
- It did not control admission on the device, which is the next trigger.
- It did not validate metrology against ground truth (`04`).
- It did not make CI blocking.

## Summary

Of the roadmap's items, the reliability and governance priorities were realised, mostly as
written; the background-execution priority was realised as submit/poll rather than as a queue;
the scale-out options were not triggered. Four decisions of the initial iteration were reversed
and each has a superseding record. The thesis of `16` — add infrastructure when the evidence
arrives, and expect the evidence to ask for less than a queue — is what the ledger shows.
