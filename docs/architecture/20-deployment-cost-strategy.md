# Deployment Cost Strategy and Hybrid GPU Architecture

## Purpose

This document analyzes deployment cost considerations for an internal AI vision platform that combines web orchestration, GPU-backed model training, high-resolution inference, dataset engineering, and artifact management.

The goal is to compare local GPU infrastructure, AWS GPU execution, and hybrid deployment options in order to support an informed architectural and financial decision.

This document is intentionally public-safe and generalized. It does not include real costs, private infrastructure details, production credentials, internal datasets, real model weights, real metrics, or confidential business information.

---

## Decision Context

The platform is intended for controlled internal use by a limited group of operational, technical, or research users. It is not designed as a public SaaS product or large-scale multi-tenant platform.

The organization already operates part of its application or intranet in AWS. However, GPU-heavy workloads such as YOLO training, high-resolution inference, SAHI processing, model validation, and synthetic dataset generation can create significant cost and data movement considerations if executed entirely in the cloud.

The key architectural question is:

```text
Should GPU workloads run locally, in AWS, or through a hybrid deployment model?
```

This decision should not be based only on whether AWS can technically run GPU workloads. It should consider workload duration, dataset size, transfer cost, operational simplicity, GPU availability, traceability, and long-term maintainability.

---

## Workload Characteristics

The platform includes different workload profiles. Training, inference, dataset generation, and visualization do not have the same cost behavior.

| Workload                     |              Frequency |     Duration | Data Volume |    GPU Need | Cost Sensitivity |
| ---------------------------- | ---------------------: | -----------: | ----------: | ----------: | ---------------: |
| YOLO training                | Occasional / scheduled | Long-running |        High |        High |             High |
| Model validation             |             Occasional |       Medium | Medium-High |      Medium |           Medium |
| SAHI batch inference         |             Occasional |  Medium-Long |        High | Medium-High |      Medium-High |
| Single-image inference       |               Sporadic |        Short |  Low-Medium |      Medium |       Low-Medium |
| Synthetic dataset generation |        Research-driven | Long-running |        High | Medium-High |             High |
| Web visualization            |               Frequent |        Short |         Low |        None |              Low |
| Metadata management          |               Frequent |        Short |         Low |        None |              Low |

This distinction is important because training and inference should not automatically share the same deployment strategy.

---

## Main Deployment Options

The following deployment options are considered:

1. Fully local GPU deployment.
2. Fully AWS GPU deployment.
3. Hybrid deployment.

Each option has different cost, operational, and scalability implications.

---

## Option A: Fully Local GPU Deployment

In this model, GPU-heavy workloads run on a local workstation or server controlled by the organization.

### Suitable For

* long-running YOLO training;
* repeated experimentation;
* high-volume image processing;
* synthetic dataset generation;
* SAHI batch-heavy workflows;
* workflows where raw images are generated or stored locally;
* controlled internal operation with a limited number of users.

### Advantages

* predictable fixed hardware cost;
* no continuous cloud GPU billing during long jobs;
* reduced need to upload large raw datasets;
* better control over local image repositories;
* suitable for iterative experimentation;
* easier repeated training when datasets remain local;
* useful when jobs can run for hours or days.

### Limitations

* upfront hardware acquisition cost;
* local maintenance responsibility;
* hardware may be idle between jobs;
* limited elasticity;
* local backup and monitoring are required;
* failure of the local machine can interrupt training workflows;
* remote integration with cloud-hosted intranet requires synchronization.

### Architectural Notes

A fully local GPU deployment is technically reasonable when the primary bottleneck is training cost or local data volume. However, it may be less convenient if the user-facing application, authentication, dashboards, and reporting already live in AWS.

---

## Option B: Fully AWS GPU Deployment

In this model, training, validation, inference, and artifact processing all run in AWS using GPU-enabled compute resources.

### Suitable For

* cloud-native operations;
* workloads where raw data already lives in AWS;
* temporary burst capacity;
* short-lived inference tasks;
* cases where hardware ownership is not desired;
* organizations that prefer managed infrastructure over local maintenance.

### Advantages

* no local hardware purchase;
* scalable on demand;
* integrates naturally with AWS-hosted web applications;
* remote access is simpler;
* useful for ephemeral inference tasks if compute is stopped after use;
* enables cloud-native storage and deployment patterns.

### Limitations

* GPU instance cost can be high for multi-day training;
* idle GPU resources can create unnecessary cost;
* large image datasets may be expensive or slow to upload;
* repeated training can generate significant compute cost;
* storage, snapshots, logs, monitoring, and networking may create hidden costs;
* incorrect network design can increase data transfer cost;
* cost predictability can be weaker than owning hardware.

### Architectural Notes

A fully cloud-based GPU deployment may be attractive for convenience, but it should be justified with realistic workload estimates. For long-running training over large drone imagery datasets, cloud GPU cost can grow quickly.

---

## Option C: Hybrid Deployment

In this model, long-running training and data-heavy processing remain local, while AWS hosts the web application, selected inference services, metadata, and user-facing results.

```text
Local GPU Workstation / Server
    ├── YOLO training
    ├── model validation
    ├── synthetic dataset generation
    ├── heavy batch inference
    └── selected model checkpoint

        ↓ selected artifact synchronization

AWS-hosted Application
    ├── intranet / web application
    ├── model metadata
    ├── selected trained checkpoints
    ├── optional cloud inference endpoint
    ├── result storage
    └── visualization layer
```

### Suitable For

* internal platforms with limited users;
* heavy training workloads;
* AWS-hosted intranet integration;
* occasional cloud inference;
* large local datasets;
* organizations seeking a balance between cost control and cloud integration.

### Advantages

* keeps expensive long-running training off cloud GPU instances;
* reduces transfer of raw datasets;
* allows AWS to serve the user-facing application;
* enables cloud inference only when operationally justified;
* balances cost, usability, and integration;
* allows local experimentation while preserving cloud-based visibility;
* reduces the need for always-on cloud GPU capacity.

### Limitations

* requires artifact synchronization;
* model lineage must be carefully tracked;
* local and cloud environments must remain compatible;
* operational process must define what is uploaded and when;
* debugging can span both local and cloud environments;
* security policy must define how model artifacts move between environments.

### Architectural Notes

For this project type, hybrid deployment is likely the most balanced option. It avoids paying cloud GPU costs for multi-day training while preserving integration with an AWS-hosted intranet or management system.

---

## Cost Drivers

The cost decision should consider more than GPU hourly pricing.

Important cost drivers include:

* GPU instance runtime;
* local GPU hardware acquisition;
* local maintenance and electricity;
* storage for datasets, checkpoints, outputs, and logs;
* upload and download of large image datasets;
* outbound data transfer;
* block storage volumes;
* object storage requests;
* snapshots and backups;
* logs and monitoring retention;
* idle compute resources;
* failed or repeated jobs;
* manual operation time;
* data synchronization between local and cloud environments.

For long-running training jobs, cloud cost can increase quickly if GPU instances remain active for days.

---

## Data Transfer Considerations

High-resolution agricultural imagery can be large. This affects both cost and workflow design.

The most important question is:

```text
Where do the raw images live initially?
```

If raw drone imagery is generated and stored locally, uploading full datasets to AWS for training may introduce cost, latency, and operational friction.

If raw imagery already lives in AWS, cloud-side inference or training may be more reasonable.

### Recommended Principle

```text
Process data close to where it naturally lives.
```

### Practical Guidance

* If raw images are local, train and preprocess locally when possible.
* If the web application is in AWS, upload only selected artifacts needed for visualization or inference.
* Avoid repeatedly transferring raw datasets between local and cloud.
* Prefer syncing compact artifacts such as model checkpoints, metadata, summaries, and selected reports.
* Define retention policies for large outputs.

---

## Training vs Inference Cost Profile

Training and inference should be evaluated separately.

### Training

Training is usually:

* long-running;
* GPU-intensive;
* data-heavy;
* experiment-driven;
* sensitive to repeated runs;
* expensive if executed on cloud GPUs for multiple days.

For this reason, local GPU infrastructure can be more cost-effective when training is repeated or when datasets are stored locally.

### Inference

Inference can be:

* short-lived;
* event-driven;
* easier to run on demand;
* suitable for cloud execution if integrated with an existing web application.

Cloud inference may be cost-effective when GPU tasks are started only when needed and stopped immediately after completion.

### SAHI Batch Inference

SAHI inference can be more expensive than regular single-pass inference because images are sliced into tiles and inference is run repeatedly across those tiles.

For large images or batch processing, SAHI may behave more like a heavy processing workload than a lightweight inference call. Its deployment location should depend on image size, batch size, and where the raw images are stored.

---

## Recommended Strategy

For a controlled internal platform, the recommended baseline is a hybrid architecture:

1. Use local GPU infrastructure for long-running training, validation, synthetic dataset generation, and heavy batch processing.
2. Keep the web application, metadata, dashboards, and user-facing workflows integrated with AWS if the organization already uses AWS.
3. Upload only selected model checkpoints, configuration metadata, summary metrics, and compact artifacts to AWS.
4. Use AWS GPU inference only for workloads that benefit from cloud integration and are short-lived or scheduled.
5. Avoid uploading all raw datasets to AWS unless cloud-side processing is required.
6. Keep cloud GPU resources ephemeral to avoid idle cost.
7. Track model lineage across local and cloud environments.
8. Define clear rules for what artifacts are synchronized.
9. Add cloud budget monitoring before enabling recurring GPU workloads.

---

## Artifact Synchronization Requirements

If training is performed locally and inference or visualization happens in AWS, the following artifacts should be synchronized:

* selected model checkpoint;
* model version metadata;
* class mapping;
* dataset configuration reference;
* training configuration summary;
* validation summary;
* inference parameters;
* known limitations;
* summary metrics;
* generated reports;
* compact previews;
* artifact manifest.

Uploading only the model checkpoint is not sufficient because it loses traceability.

A model artifact should be accompanied by enough metadata to answer:

```text
Which data produced this model?
Which configuration was used?
Which classes does it predict?
Which runtime environment was used?
Which validation results supported this model?
Which inference parameters are recommended?
```

---

## Decision Matrix

| Criterion                     | Local GPU |                   AWS GPU |             Hybrid |
| ----------------------------- | --------: | ------------------------: | -----------------: |
| Long-running training cost    |    Strong |                      Weak |             Strong |
| Occasional inference          |    Medium |                    Strong |             Strong |
| Integration with AWS intranet |    Medium |                    Strong |             Strong |
| Large local dataset handling  |    Strong |               Weak-Medium |             Strong |
| Elastic scaling               |      Weak |                    Strong |             Medium |
| Operational simplicity        |    Medium |                    Medium |             Medium |
| Fixed cost predictability     |    Strong |                      Weak |             Medium |
| Avoiding idle GPU cost        |    Medium |       Strong if ephemeral |             Strong |
| Traceability                  |    Medium |                    Medium | Strong if governed |
| Maintenance burden            |    Medium |                Low-Medium |             Medium |
| Remote accessibility          |    Medium |                    Strong |             Strong |
| Data transfer minimization    |    Strong | Weak if raw data is local |             Strong |

---

## Suggested Operating Model

A practical operating model could be:

```text
1. Raw imagery is stored locally or in the organization-controlled data environment.
2. Training is executed on a local GPU workstation or server.
3. Model checkpoints and training summaries are reviewed.
4. Only selected model artifacts are promoted.
5. Selected artifacts are synchronized to AWS.
6. AWS-hosted intranet exposes metadata, reports, and optional inference workflows.
7. Cloud GPU inference is started only when needed.
8. Cloud GPU resources are stopped after completion.
```

This keeps high-volume data processing close to local GPU resources while preserving cloud integration for the user-facing system.

---

## Risks and Mitigations

| Risk                                                              | Mitigation                                                              |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Cloud GPU cost grows unexpectedly                                 | Use ephemeral GPU tasks, budget alerts, and job-level cost tracking     |
| Large datasets are repeatedly uploaded                            | Keep raw datasets local and upload selected artifacts only              |
| Model lineage is lost between local and cloud                     | Persist model metadata, configuration summaries, and artifact manifests |
| Local GPU server becomes a single point of failure                | Add backup policy and optional cloud burst capacity                     |
| AWS inference environment differs from local training environment | Standardize container images and runtime versions                       |
| Outputs become expensive to store                                 | Define retention and cleanup policies                                   |
| Cloud networking costs are underestimated                         | Estimate data movement before deployment                                |
| Cloud GPU tasks remain idle                                       | Automate shutdown after job completion                                  |
| Local hardware is underused                                       | Schedule training, validation, and dataset generation workflows         |
| Local maintenance becomes difficult                               | Document operating procedures and define technical ownership            |

---

## AWS-Specific Considerations

If AWS GPU execution is considered, the following should be evaluated before implementation:

* instance family and GPU type;
* hourly GPU cost;
* expected job duration;
* storage volume size;
* storage throughput requirements;
* S3 or EFS usage;
* data transfer direction and volume;
* CloudWatch log retention;
* NAT Gateway usage;
* idle compute risk;
* autoscaling policy;
* shutdown automation;
* security boundaries;
* budget alerts.

The organization should estimate a typical workload, not an ideal workload.

A cost estimate should include at least:

```text
monthly GPU hours
+ storage volume
+ object storage
+ logs
+ data transfer
+ snapshots
+ operational margin
```

---

## Questions for the Organization

Before deciding, the organization should clarify:

1. How often will YOLO training be executed?
2. How long does a typical training job run?
3. How large are the raw image datasets?
4. Where are drone images initially stored?
5. How often will inference be executed?
6. Are inference jobs single-image, batch, or SAHI-heavy?
7. Do users need real-time inference or batch reports?
8. What is the acceptable waiting time for results?
9. Is the local GPU server acceptable from an IT/security perspective?
10. Does AWS integration require cloud-side processing, or only result visualization?
11. What monthly cloud budget is acceptable?
12. What level of downtime is tolerable?
13. Who will maintain the local GPU machine?
14. Which artifacts must be preserved long-term?
15. How long should generated outputs be retained?
16. Is cloud burst capacity required for exceptional workloads?
17. Does the organization prefer fixed capital cost or variable cloud cost?

---

## Recommended Baseline Architecture

The recommended baseline is:

```text
Local GPU infrastructure
    for long-running training, validation, synthetic data generation, and heavy batch processing

AWS-hosted application layer
    for intranet integration, metadata, visualization, reports, selected artifact storage, and optional on-demand inference
```

This approach balances:

* cost control;
* data locality;
* operational simplicity;
* cloud integration;
* traceability;
* internal usability.

---

## When to Prefer Local GPU

Prefer local GPU infrastructure when:

* training jobs run for many hours or days;
* raw images are generated or stored locally;
* experiments are repeated frequently;
* cloud GPU idle time would be difficult to control;
* datasets are large;
* the organization wants predictable fixed cost;
* users can tolerate scheduled processing;
* there is technical ownership for the local machine.

---

## When to Prefer AWS GPU

Prefer AWS GPU execution when:

* GPU tasks are short-lived;
* inference is sporadic;
* images or inputs already live in AWS;
* the workload must integrate tightly with an AWS-hosted intranet;
* the organization does not want local hardware;
* burst capacity is occasionally needed;
* tasks can be started and stopped automatically;
* budget controls and monitoring are configured.

---

## When to Prefer Hybrid

Prefer hybrid deployment when:

* training is heavy but inference is occasional;
* the web application already lives in AWS;
* raw data is large and mostly local;
* only selected model artifacts need to be shared;
* the organization wants cloud accessibility without moving all GPU processing to AWS;
* cost predictability matters;
* the platform is used by a limited internal group.

For the described internal AI vision platform, hybrid deployment is likely the most balanced option.

---

## Recommendation Summary

For the expected internal use case, a hybrid deployment strategy is likely the most cost-effective and operationally reasonable option.

Long-running training and data-heavy workflows should remain close to the raw data and local GPU workstation or server. AWS should be used for the existing intranet, metadata management, result visualization, selected artifact storage, and optional on-demand inference.

This strategy avoids paying cloud GPU costs for multi-day training while preserving integration with the organization’s AWS-hosted systems.

The final decision should be made after estimating:

* expected monthly GPU hours;
* dataset size and transfer volume;
* inference frequency;
* acceptable wait time;
* local hardware cost;
* cloud GPU cost;
* operational ownership;
* backup and retention requirements.

The recommended decision principle is:

```text
Train where the data and GPU cost make sense.
Serve where the users and application already are.
```


## Raw Imagery Storage and Data Movement Strategy

### Purpose

This section analyzes where high-resolution drone imagery should be stored and processed in order to control infrastructure cost, bandwidth usage, operational complexity, and cloud dependency.

For this platform, raw drone imagery is not a minor artifact. A single flight campaign can generate hundreds of high-resolution images, and repeated uploads to cloud storage can introduce significant bandwidth, storage, retrieval, and operational costs.

The key architectural question is:

```text
Should raw drone imagery be uploaded to cloud storage by default, or should it remain close to the local GPU processing environment?
```

---

## Context

The platform processes drone imagery for agricultural analysis, model training, validation, and inference.

Typical image acquisition may involve:

* hundreds of images per flight;
* high-resolution images;
* repeated campaigns over time;
* local acquisition from drones or field operations;
* training and inference workflows that may read the same images multiple times;
* generated outputs such as previews, detection metadata, reports, GIS artifacts, and model checkpoints.

Because of this, raw imagery should be treated as a high-volume data asset, not simply as web application media.

---

## Baseline Recommendation

The recommended baseline is:

```text
Keep raw drone imagery local by default.
Process close to where the data is generated.
Synchronize only selected artifacts to the cloud-hosted intranet.
```

This means cloud storage should not automatically become the primary destination for all raw drone images unless cloud-side processing, historical archiving, or disaster recovery requirements justify it.

---

## Recommended Data Placement

| Data / Artifact Type              | Recommended Location                          | Reason                                                                           |
| --------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Raw drone images                  | Local storage / NAS / GPU workstation storage | High volume, locally generated, frequently used for training or batch processing |
| Active training datasets          | Local GPU processing environment              | Avoids repeated upload/download and cloud GPU data access overhead               |
| Intermediate checkpoints          | Local storage                                 | Frequent writes, low public-facing value                                         |
| Selected best model checkpoint    | Local + cloud copy                            | Needed for inference, traceability, and deployment                               |
| Training metadata                 | Cloud database or metadata store              | Lightweight and useful for web visualization                                     |
| Detection JSON / summaries        | Cloud                                         | Compact and useful for intranet views                                            |
| Compressed previews / thumbnails  | Cloud                                         | Suitable for user-facing visualization                                           |
| Full-resolution inference outputs | Local or selective cloud storage              | Potentially large; upload only when needed                                       |
| Historical raw imagery            | Optional cloud archival tier                  | Useful only if long-term retention or disaster recovery is required              |
| GIS/vector outputs                | Cloud if needed by users                      | Smaller than raw imagery and useful for reporting                                |

---

## Cloud Storage Is Useful, But Not Always as Primary Storage

Cloud object storage can be useful for:

* selected model artifacts;
* result visualization;
* report sharing;
* historical archiving;
* disaster recovery;
* selected datasets required for cloud-side inference;
* integration with an existing cloud-hosted intranet.

However, cloud storage should not be used by default for every raw image if the main training and heavy inference workloads run locally.

---

## Training Data Considerations

Training workloads are usually:

* long-running;
* GPU-intensive;
* data-heavy;
* iterative;
* sensitive to repeated dataset reads;
* likely to generate multiple checkpoints and logs.

If training is performed locally, the active training dataset should remain local. Uploading the full raw dataset to cloud storage only to train or validate elsewhere may increase complexity and cost without delivering proportional value.

Recommended policy:

```text
If training runs locally, keep active training datasets local.
Upload only selected model artifacts, configuration summaries, and compact results.
```

---

## Inference Data Considerations

Inference has two possible profiles:

### Batch or campaign-level inference

If inference processes entire drone campaigns with hundreds of large images, local execution may be more cost-effective.

Recommended policy:

```text
For large batch inference over full flight campaigns, process locally and upload compact results.
```

### On-demand cloud inference

If inference is occasional, short-lived, and directly integrated with the existing intranet, cloud GPU execution can be reasonable.

Recommended policy:

```text
Use cloud inference only for selected workloads where cloud integration provides operational value.
```

---

## Hybrid Data Flow

A practical hybrid flow is:

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
   ├── model checkpoint
   ├── model metadata
   ├── dataset version summary
   ├── inference summaries
   ├── compressed previews
   ├── reports
   └── GIS-compatible outputs
          ↓
Cloud-hosted Intranet / Metadata / Visualization
```

This approach keeps high-volume raw data close to the processing environment while still allowing the organization to use cloud services for web access, reporting, metadata, and selected inference workflows.

---

## Storage Class Considerations

Cloud archival or infrequent-access storage can be useful for historical raw imagery, but only when access patterns are well understood.

A poor storage-class decision can create unexpected costs if archived data is frequently retrieved for training, inference, or reprocessing.

General guidance:

| Access Pattern                       | Suggested Strategy                       |
| ------------------------------------ | ---------------------------------------- |
| Active training data                 | Local or frequently accessed storage     |
| Recent campaigns under analysis      | Local or active storage                  |
| Historical imagery rarely accessed   | Cloud archival or infrequent-access tier |
| Data requiring frequent reprocessing | Avoid cold/archive tiers                 |
| User-facing previews                 | Cloud standard/object storage            |
| Compact metadata                     | Cloud database or object storage         |

---

## Cost Drivers

The storage and data movement decision should consider:

* upload bandwidth from local site to cloud;
* time required to upload flight campaigns;
* cloud storage cost;
* retrieval cost from infrequent-access tiers;
* cloud GPU runtime cost;
* repeated reads during training;
* generated outputs and checkpoints;
* log retention;
* duplication between local and cloud environments;
* manual effort required to manage synchronization.

The highest cost risk is not only storage itself, but repeated movement and processing of high-volume imagery without a clear reason.

---

## Decision Matrix

| Question                                          | If Yes | Recommended Action                                                       |
| ------------------------------------------------- | ------ | ------------------------------------------------------------------------ |
| Are raw images generated locally?                 | Yes    | Keep raw images local by default                                         |
| Is training performed locally?                    | Yes    | Keep active training datasets local                                      |
| Is inference performed over full campaigns?       | Yes    | Prefer local batch inference and upload results                          |
| Is cloud inference occasional and short-lived?    | Yes    | Cloud inference can be reasonable                                        |
| Does the intranet only need results and previews? | Yes    | Upload summaries, previews, and metadata instead of raw imagery          |
| Is long-term archival required?                   | Yes    | Use cloud archival or infrequent-access storage selectively              |
| Will old imagery be reprocessed frequently?       | Yes    | Avoid cold storage for those datasets                                    |
| Is upload bandwidth limited?                      | Yes    | Avoid routine full-dataset uploads                                       |
| Is disaster recovery required?                    | Yes    | Replicate selected raw data or compressed archives with retention policy |

---

## Recommended Policy

The recommended operating policy is:

1. Store raw drone imagery locally by default.
2. Process training and heavy batch inference close to the raw data.
3. Upload selected model checkpoints, metadata, previews, reports, and compact results to the cloud.
4. Use cloud storage for historical archiving only when retention requirements justify it.
5. Use cloud GPU inference only when workload size, user access, and integration needs justify cloud execution.
6. Avoid repeatedly uploading full flight campaigns unless cloud-side processing is required.
7. Define a retention policy for raw imagery, processed outputs, and publishable artifacts.
8. Maintain traceability between local datasets, trained models, and cloud-published results.

---

## Risks and Mitigations

| Risk                                                     | Mitigation                                                             |
| -------------------------------------------------------- | ---------------------------------------------------------------------- |
| Cloud storage grows unexpectedly                         | Define retention and lifecycle policies                                |
| Upload bandwidth becomes a bottleneck                    | Keep raw data local and upload only compact artifacts                  |
| Training data and model metadata become disconnected     | Use artifact manifests and dataset version references                  |
| Cloud inference requires full-resolution images          | Upload only selected inference batches or run inference locally        |
| Historical data becomes expensive to retrieve            | Choose storage class based on expected access frequency                |
| Duplicate datasets exist in local and cloud environments | Define clear source-of-truth rules                                     |
| Users expect cloud access to all raw images              | Provide previews and reports unless raw imagery is explicitly required |
| Local storage becomes a single point of failure          | Add backup or selective cloud archival strategy                        |

---

## Summary

Raw drone imagery should not be uploaded to cloud storage by default. For this internal AI vision platform, the most cost-effective and operationally reasonable approach is to keep high-volume raw imagery close to the local GPU processing environment and synchronize only selected artifacts to the cloud-hosted application.

Cloud storage remains valuable for metadata, previews, reports, selected checkpoints, historical archiving, and optional cloud inference. The decision should be driven by workload profile, data volume, access frequency, bandwidth, and business requirements rather than a default cloud-first assumption.
