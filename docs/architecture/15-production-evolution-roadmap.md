# Internal Platform Evolution Roadmap

This document describes a pragmatic evolution path for a controlled internal AI vision platform.

The architecture is intended for internal agricultural, operational, and research-oriented workflows. It is **not** designed as a public SaaS product, a large-scale multi-tenant platform, or a globally distributed ML service.

The goal is not to evolve automatically toward Kubernetes, multi-region deployment, or large-scale distributed infrastructure. The goal is to improve reliability, traceability, operational usability, GPU workload control, and artifact governance for a limited group of users running scheduled training, inference, validation, and research-oriented workflows.

---

## Evolution Philosophy

**Scale by operational evidence, not by default.**

For an internal platform with predictable workloads and a limited user base, the first improvements should focus on:

- preflight validation;
- job status tracking;
- clear error states;
- GPU and storage health checks;
- artifact manifests;
- backup and retention policies;
- controlled concurrency;
- reproducible configuration and dataset lineage.

Queues, worker pools, object storage, Kubernetes, and distributed observability are optional tools. They should be introduced only when the operational context proves they are needed.

---

## Current Operating Context

The expected deployment context includes:

- a limited number of internal users;
- scheduled or occasional training and inference jobs;
- controlled access to datasets and generated artifacts;
- GPU-backed execution on a dedicated workstation, server, or small internal deployment;
- Django-based project, dataset, and configuration management;
- FastAPI-based AI processing;
- shared storage for model and inference artifacts;
- experiment tracking for reproducibility and debugging.

In this context, Docker Compose, a dedicated AI service, shared storage, and controlled synchronous execution can be acceptable when concurrency is low and operators understand that some jobs are long-running.

---

## Current Architecture

Current characteristics:

- Django web layer for configuration, request submission, metadata, and visualization;
- FastAPI AI service for GPU-backed training, validation, inference, and experiment coordination;
- synchronous HTTP communication between Django and FastAPI;
- shared filesystem artifact exchange;
- GPU-backed training and inference with single-GPU or multi-GPU runtime strategies depending on environment and configuration;
- experiment tracking and metric logging;
- basic error handling and operational diagnostics;
- public-safe architecture documentation without private implementation code.

### Important distinction: multi-GPU runtime vs distributed job orchestration

Multi-GPU training runtime and distributed platform orchestration are different concerns.

| Concern | Meaning | Current interpretation |
|--------|---------|------------------------|
| Single-GPU runtime | One training or inference job uses one GPU | Valid runtime mode. |
| Multi-GPU runtime | One training job uses multiple GPUs through runtime strategies such as DataParallel or evaluated DDP patterns | Training-runtime concern, not equivalent to platform-level distributed execution. |
| Distributed job orchestration | Many jobs are scheduled across workers, queues, GPUs, or nodes with state tracking and retry behavior | Optional future concern; not required for the current internal deployment if concurrency remains low. |

This distinction avoids incorrectly treating the absence of a worker pool or Kubernetes as a failure of the training runtime.

---

## Priority 1: Operational Reliability

These improvements should come before queues, Kubernetes, or distributed infrastructure.

### Recommended improvements

- Validate dataset paths before execution.
- Validate generated dataset configuration files before training.
- Validate model checkpoint references before inference or retraining.
- Validate output directories and write permissions.
- Validate storage mounts from both web and AI service perspectives.
- Check GPU availability and available memory before launching heavy jobs.
- Add explicit job status records.
- Add structured logs with correlation IDs.
- Add clear user-facing error states.
- Persist artifact manifests for each execution.
- Define backup and retention policies for datasets, models, and outputs.
- Verify that generated artifacts are accessible from the web visualization layer.

### Why this comes first

Most operational failures in this type of internal platform are more likely to come from:

- missing files;
- invalid paths;
- storage mount issues;
- GPU memory contention;
- partially generated outputs;
- unclear errors;
- stale model references;
- configuration drift.

Solving these issues usually produces more value than adding distributed infrastructure prematurely.

---

## Priority 2: Controlled Background Execution

A lightweight background execution layer should be added only if synchronous execution becomes operationally painful.

### Possible triggers

Add background execution if one or more of the following becomes common:

- repeated HTTP timeouts;
- users frequently submit more than one long-running job at the same time;
- training and inference compete for GPU memory;
- operators need cancellation, retry, progress tracking, or resumability;
- failed jobs require manual cleanup too often;
- the web interface becomes blocked or confusing during long executions.

### Possible additions

- Lightweight job queue.
- Single GPU worker or controlled worker process.
- Job status polling.
- Progress reporting.
- Controlled retry policy.
- Job cancellation.
- GPU resource locking.
- Job timeout policy.

### What this does not require by default

Controlled background execution does not automatically require:

- a large distributed worker pool;
- Kubernetes;
- multi-region deployment;
- enterprise observability stacks;
- complex event streaming;
- public SaaS-style autoscaling.

For a controlled internal platform, a small queue plus one GPU worker may be enough.

---

## Priority 3: Artifact and Model Governance

Before scaling infrastructure, improve traceability.

### Recommended improvements

- Database-backed model reference registry.
- Artifact manifest per run.
- Dataset version registry.
- Immutable run identifiers.
- Retention policy for large outputs.
- Clear separation between raw data, generated outputs, model checkpoints, and publishable artifacts.
- Validation that model references and metrics belong to the same run.
- Explicit promotion flow for the current best model reference.
- Clear rollback strategy for model reference updates.

### Why this matters

File-based model references can be acceptable at low scale, but they become fragile when:

- multiple jobs run concurrently;
- more than one user can trigger retraining;
- model references are updated automatically;
- artifacts are moved, deleted, or regenerated;
- long-term traceability is required.

The next maturity step should therefore focus on governance and consistency, not necessarily cluster scaling.

---

## Priority 4: Dataset and Configuration Governance

The dataset configuration layer should evolve with the platform.

### Recommended improvements

- Validate generated dataset configuration files before training.
- Track configuration versions.
- Detect drift between database configuration and generated files.
- Persist configuration lineage.
- Prevent deletion of configurations used by active or historical jobs.
- Associate training runs with dataset configuration versions.
- Record class mapping versions.
- Record dataset root references using placeholders or environment-driven paths in public documentation.
- Validate that generated configuration files can be read by the training runtime.

### Why this matters

Training failures are often caused by configuration issues rather than model code. A strong internal platform should make dataset and configuration state explicit, reproducible, and inspectable.

---

## Priority 5: Research and Synthetic Dataset Workflow Hardening

Notebook-driven and synthetic data generation workflows are valuable for research, but they should not become hidden production paths.

### Recommended improvements

- Keep notebooks as research clients or validation workflows.
- Avoid duplicating business logic inside notebooks.
- Ensure notebooks consume documented configuration files and artifacts.
- Add artifact manifests for generated synthetic datasets.
- Add validation for generated annotations.
- Track source dataset version, object extraction settings, and generation parameters.
- Define when synthetic dataset generation should remain manual and when it should become a queued job.

### When to promote synthetic generation to a background job

Consider background execution if:

- synthetic generation becomes routine rather than exploratory;
- SAM or segmentation processing takes hours;
- multiple dataset versions must be generated regularly;
- generated artifacts become too large to manage manually;
- failures require repeated manual cleanup.

---

## Optional Scale-Out Path

Distributed workers, object storage, Kubernetes, and enterprise observability are optional future paths.

They are justified only if:

- job concurrency grows beyond the capacity of the current server;
- storage volume exceeds local operational capacity;
- uptime requirements become business-critical;
- the platform must run across multiple servers or locations;
- multiple teams require independent workload isolation;
- manual operation becomes unreliable or too costly;
- compliance or audit requirements exceed what lightweight logging and manifests can provide.

### Possible future additions

- GPU worker pool.
- Object storage such as S3, GCS, MinIO, or equivalent.
- Kubernetes or another orchestrator.
- Centralized monitoring and alerting.
- Distributed tracing.
- Advanced model registry.
- Automated dataset validation suite.

### Explicit non-goal for the current scope

The current architecture does not need to become a public multi-tenant SaaS platform to be valuable. It can be a valid internal production-oriented system if it is reliable, traceable, understandable, and fit for the actual workload.

---

## When Not to Add Distributed Infrastructure

Do not add Kubernetes, distributed queues, object storage, or multi-worker scheduling if:

- the user base remains small;
- jobs are scheduled or occasional;
- one GPU server is enough;
- downtime can be handled operationally;
- local storage is manageable;
- manual supervision is acceptable;
- a simpler process provides better maintainability;
- the cost of additional infrastructure exceeds the business value;
- the team does not have enough operational capacity to maintain the added infrastructure.

A simpler architecture can be more reliable when the operational scope is narrow.

---

## Decision Matrix

| Operational signal | Recommended response |
|--------------------|----------------------|
| Occasional long jobs, few users | Keep synchronous execution; improve error messages and status visibility. |
| Repeated request timeouts | Add lightweight background execution and job polling. |
| Training and inference compete for GPU memory | Add GPU locking, scheduling policy, or separate execution windows. |
| Model references become inconsistent | Add database-backed model registry or transactional reference tracking. |
| Generated artifacts become hard to trace | Add artifact manifests and retention policies. |
| Dataset configurations drift from generated files | Add configuration versioning and validation. |
| Multiple users submit long jobs frequently | Add a queue and a controlled GPU worker. |
| One server is no longer enough | Consider worker pool or additional GPU node. |
| Storage exceeds local management capacity | Consider object storage and lifecycle policies. |
| Uptime becomes business-critical | Consider HA patterns, monitoring, alerting, and incident response. |
| Deployment must span multiple servers | Consider orchestration tools such as Kubernetes. |

---

## Recommended Next Steps

Recommended near-term improvements:

1. Add preflight validation.
2. Add job status tracking.
3. Add artifact manifests.
4. Add structured logs with correlation IDs.
5. Add GPU and storage health checks.
6. Add database-backed model reference tracking if concurrent training becomes possible.
7. Add dataset configuration versioning.
8. Add backup and retention policy.
9. Add a lightweight queue only if synchronous execution becomes unreliable.
10. Keep Kubernetes and distributed worker pools as optional future paths.

---

## Roadmap Summary

| Priority | Focus | Why it matters |
|----------|-------|----------------|
| 1 | Operational reliability | Prevent avoidable failures before adding infrastructure. |
| 2 | Controlled background execution | Avoid blocking the web layer when long-running jobs become frequent. |
| 3 | Artifact and model governance | Improve traceability and prevent inconsistent model references. |
| 4 | Dataset and configuration governance | Make training inputs reproducible and auditable. |
| 5 | Research workflow hardening | Keep notebooks useful without turning them into hidden production paths. |
| Optional | Scale-out infrastructure | Add workers, object storage, or Kubernetes only if the operating context requires it. |

---

## Summary

This roadmap prioritizes internal operational reliability over premature scale. The architecture should evolve toward distributed infrastructure only when the actual workload and business context require it.

For the current internal deployment model, the most valuable improvements are likely to be:

- better validation;
- better status visibility;
- better artifact traceability;
- better model reference governance;
- better GPU and storage diagnostics.

The absence of Kubernetes, a distributed queue, or a large worker pool is not necessarily a weakness. In this context, it can be an intentional architectural trade-off.
