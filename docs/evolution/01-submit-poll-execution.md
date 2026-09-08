# Submit/Poll Execution Without a Broker

> Public-safe documentation. Design-level description of a later revision; no module names, no
> measured throughput, no calendar dates. Concurrency figures are illustrative.

## Purpose

The initial iteration held the HTTP request open for the duration of a training or inference
job (`04-system-flow.md`, ADR-003). `15-limitations-and-risks.md` named the triggers that would
make that unacceptable: timeouts, operators needing progress, failures that could not be
explained afterwards. This document describes the execution model the revision adopted when
those triggers fired, and why it is still not a job queue.

## Context

Three things had become routine:

- an inference batch over hundreds of high-resolution images outlived any sensible HTTP timeout;
- operators asked "is it still running?" and the only answer was to look at the GPU;
- a restart of the AI service left half-written outputs with no record of what had been
  in flight.

The roadmap's answer to these triggers was explicit: job status records and polling first, a
controlled worker only when jobs compete for the GPU, a broker only for retry, cancellation and
multi-worker dispatch. The revision implemented the first step and stopped there.

## Design

### The request no longer waits

```text
  Console (web layer)            AI service                    Shared storage
  ──────────────────             ──────────                    ──────────────
  1. insert job-history row
     status = submitted
  2. POST /<feature>/submit  ─►  validate inputs
                                 create run_id
                                 write jobs/<feature>/<run_id>.json  (atomic)
                                 hand the job to the feature pool
  3. ◄── 202 { run_id }          (returns in milliseconds)

  4. every few seconds:
     POST /<feature>/status  { run_ids: [...] }         ─►  read job records
     ◄── { run_id: status, ... }
     update job-history rows
                                 ... job runs on a pool thread ...
                                 write <run_id>/manifest.json + outputs/   (atomic)
                                 job record status = done | failed
  5. console reads outputs
     straight from the volume
```

**Submit returns a run identifier.** Validation is synchronous and cheap; anything that would
fail fast still fails in the request. Everything else happens after the response.

**One durable job record per run.** The AI service writes a small JSON document per run,
created exclusively (never overwritten by a second submit with the same identifier) and updated
atomically through a temporary file and a rename. It is the AI service's only state, and it is a
file because the AI service holds no database. The design rule of the revision is: the web
layer owns rows, the AI service owns bytes.

**The web layer keeps a job-history table.** Every submit inserts a row before the HTTP call,
so a request that never returns still leaves a trace. Every poll writes the returned status back
into that row. The table is the operator's source of truth; the file is the service's.

**Execution happens on in-process pools.** Each feature (direct inference, sliced inference,
validation, training, metrology) has its own small thread pool inside the single AI service
process. No new process, no sidecar, no broker.

**Status queries are batched.** One request carries many run identifiers, so a console page
showing a large batch does not turn into hundreds of polls.

**Startup reconciliation.** When the AI service starts, every job record still marked running
is swept to failed with a reason. Nothing resumes. This is deliberate: a resumed job whose
inputs may have changed is worse than a clear failure.

### What this is not

| Not provided | Why |
|---|---|
| Retry | A failed job is re-submitted by a person who has read the reason |
| Cancellation | Jobs are short enough at this scale; the trigger has not fired |
| Resume after restart | See reconciliation above |
| A broker or a second worker process | The GPU is one device; dispatch across workers has nothing to dispatch to |
| Priority | All operators share one lane |

## Constraints

- Everything runs inside one AI service process. A crash of that process fails every job in
  flight, and the reconciliation on restart is what makes that survivable.
- The job record is a file on the shared volume. It is readable by the web layer for
  diagnostics but is written only by the AI service.
- Status is polled, not pushed. The polling interval is a console setting.

## Risks

**Admission is not controlled.** This is the open risk of the design and the one the initial
iteration predicted under "GPU contention". With one pool per feature, several jobs can be
admitted at once, and if two of them need the device they compete for its memory. The revision
documents this as a known condition rather than solving it. The design recommendation is a
single GPU lane: one admission token for any job that will touch the device, with the feature
pools kept only for CPU-bound work such as metrology. That is the "controlled worker" of the
roadmap, and its trigger is exactly this contention.

**Lost updates on status.** The console writes status back on every poll. Two console
sessions polling the same batch write the same value; no conflict, but no protection either if
the schema ever gains fields that differ per session.

**Unbounded job records.** Job records accumulate on the volume. Deletion is cascaded from the
batch (deleting a batch removes its runs, outputs and records), which makes retention a
batch-level policy rather than a background sweep.

## Recommended Improvements

1. A single GPU admission lane, as described above, before any second job type that uses the
   device is enabled.
2. A cancellation flag on the job record, honored between processing units, so that a
   long batch can be stopped without restarting the service.
3. Idempotent submit keyed on a client-supplied identifier, so that a console retry after a
   network error does not create a duplicate run.
4. Only then, and only if a second GPU or a second worker host appears: a broker.

## Summary

The revision replaced the open HTTP request with submit, a durable job record, a job-history
table and batched polling, all inside the existing two processes. It added no queue, no worker
pool and no broker, which is what `16-production-evolution-roadmap.md` said the first step
should look like. The price is uncontrolled admission on the GPU, named here as the next
trigger. ADR-009 records the decision and amends ADR-003.
