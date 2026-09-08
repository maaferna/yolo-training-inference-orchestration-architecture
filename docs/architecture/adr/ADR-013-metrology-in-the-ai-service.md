# ADR-013: Compute Detection Metrology as a Job Type of the AI Service

**Status**: Accepted
**Iteration**: revision
**Public-Safe**: Yes
**Relates to**: [ADR-001](./ADR-001-separate-web-and-ai-services.md) (service separation),
[ADR-009](./ADR-009-submit-poll-in-process-execution.md) (job model).

---

## Context

The revision added a metrology stage that turns detections into physical sizes, clusters,
coverage and density (`docs/evolution/04-detection-metrology.md`). It runs on CPU, needs no
model, and consumes the outputs of an inference batch plus image metadata. Three places could
host it:

- the web layer, computed at render time when an operator opens a results page;
- the AI service, as a job type with its own record and manifest;
- a third service.

Forces:

- Results must be reproducible artifacts an operator can download and a GIS can open, not
  numbers recomputed on each page view.
- The computation can take minutes for a large batch; it must not block a web request
  (ADR-009 applies).
- The web layer must stay free of numerical and geospatial dependencies (ADR-001's separation
  is about dependency weight as much as about GPU work).
- The metrology outputs need the same provenance as detections: which detections, which
  parameters, which gates fired.

## Decision

Metrology is a **job type of the AI service**. It is submitted like inference, runs on its own
CPU pool, writes a job record, produces per-image and per-batch tables plus GeoJSON, and writes a
run manifest recording the detection run it consumed, the parameters and the gate outcomes. It
never touches the device. The web layer reads its outputs through the manifest contract and
renders them; it computes nothing.

## Alternatives Considered

### Compute in the web layer at render time
Rejected. Not reproducible (results depend on code at view time), not downloadable as
artifacts, blocks the request, and drags numerical and geospatial libraries into the web image.

### A third service
Rejected. It would be a second process with no database and the same storage contract as the
AI service — that is, the AI service again, plus a deployment unit. `16`'s rule applies: no
new service without a trigger.

### Inside the inference job, as a post-processing step
Rejected. Operators run metrology selectively, with different parameters, sometimes long after
inference; coupling it to the inference run would force re-inference to re-measure.

## Consequences

### Positive
- Metrology inherits the job record, manifest, error envelope and polling of ADR-009 for free.
- Outputs are artifacts with provenance, downloadable and reproducible.
- The web image stays lean; the AI image already carries the geospatial layer.

### Negative
- The AI service's CPU pool for metrology shares the process with device-bound pools; a heavy
  metrology batch competes for CPU with the inference pipeline's pre- and post-processing.
- Two job types must be run in sequence by the operator (inference, then metrology). The
  console offers the second from the first's results page.

### Neutral
- The AI service now has a job type that does not use the GPU. The name "AI service" is kept;
  "compute service" would be more accurate and is noted here.

## Revisit When

- Metrology batches routinely starve inference of CPU → a dedicated process for CPU job types,
  reading the same storage contract.
- Ground-truth validation of the method exists (`04`, risks) → parameters and gates become
  versioned configuration with their validation record.

## Public-Safe Note

The method is described in `docs/evolution/04-detection-metrology.md` without thresholds,
species, sites or results. This ADR concerns placement only.
