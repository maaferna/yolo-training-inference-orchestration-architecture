# ADR-009: Execute Jobs as Submit/Poll on In-Process Pools, Without a Broker

**Status**: Accepted
**Iteration**: revision
**Public-Safe**: Yes
**Amends**: [ADR-003](./ADR-003-fastapi-gpu-service.md) — the service boundary stands; the
execution mode it describes ("synchronous from the client's perspective") is replaced.

---

## Context

ADR-003 accepted that the AI service would run blocking GPU code inside the request and return
minutes later, and named the condition under which that would stop being acceptable. The
condition arrived: inference batches over large sets of high-resolution images outlived any
HTTP timeout, operators needed progress, and a service restart left no record of what had been
running.

The forces:

- One host, one device, one AI service process. There is nothing to dispatch to.
- The AI service holds no database (the web layer owns all rows).
- The team operating the platform is small; every additional service is an operational cost
  that `16-production-evolution-roadmap.md` says must be justified by evidence.
- Failures must be explainable after the fact, which the open request never allowed.

## Decision

Submission returns immediately with a run identifier. The job executes on an in-process thread
pool inside the AI service, one small pool per feature. State lives in one durable job record
per run, written atomically to the shared volume, and in a job-history table in the web
database that the console updates on every poll. Status is queried in batches. On startup the
service sweeps every record still marked running to failed. No broker, no retry, no resume, no
cancellation.

Design detail is in [`docs/evolution/01-submit-poll-execution.md`](../../evolution/01-submit-poll-execution.md).

## Alternatives Considered

### Keep the synchronous request and raise timeouts
Rejected. Timeouts were the symptom; the disease was that nothing recorded a job independently
of the connection that started it.

### A task queue with a broker and a worker process
Rejected for this iteration. It solves retry, cancellation and multi-worker dispatch — none of
which had a trigger — at the cost of two more services to run, monitor and secure. `16` names
those as the triggers for a queue, and they had not fired.

### Background tasks of the web framework
Rejected. Running GPU work inside the web process is the coupling ADR-001 exists to prevent.

### A separate worker process polling a directory
Considered. It gives crash isolation from the API process at the cost of a second process and a
second deployment unit. Deferred: the admission problem (below) is the same, and the API process
restarting is already handled by reconciliation.

## Consequences

### Positive
- The web request returns in milliseconds; timeouts disappear as a failure class.
- Every run leaves a durable record even if the request that started it dies.
- Restart behaviour is defined: in-flight jobs fail with a reason instead of vanishing.
- Two processes, as before. No new service.

### Negative
- **Admission is not controlled.** Several pools can admit several device-bound jobs at once;
  they compete for GPU memory. This is the open risk and the next trigger.
- A crash of the AI service process fails every job in flight.
- No cancellation: a long batch runs to completion or to failure.

### Neutral
- The job record on the volume duplicates the job-history row in the database. They serve
  different readers (the service and the operator) and the duplication is intentional.

## Revisit When

- Two device-bound jobs contend for GPU memory in normal operation → add a single admission
  lane for device jobs (the "controlled worker" of `16`).
- Operators need to stop a running batch more than occasionally → cancellation flag on the job
  record.
- A second device or a second host appears → a broker becomes worth its cost.
- A client retries submits after network errors and duplicates appear → idempotent submit keyed
  on a client identifier.

## Public-Safe Note

This ADR describes an execution model at the level of design. It contains no module, endpoint
or table names of any implementation, no measurements, and no identifying information.
