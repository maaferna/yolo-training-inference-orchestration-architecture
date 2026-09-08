# ADR-010: Keep the Model Reference in a Transactional Registry with Human Promotion

**Status**: Accepted
**Iteration**: revision
**Public-Safe**: Yes
**Closes**: the gap noted in [the ADR index](./README.md) — "a formal model registry has no
ADR yet" — and the race condition documented in
[`10-continuous-improvement-training.md`](../10-continuous-improvement-training.md).

---

## Context

The initial iteration recorded "the current best model" as a reference file in shared storage,
rewritten by any training run whose score beat the baseline. `10` documents the race between
two concurrent runs reading the same baseline and writing conflicting references, and `07`
lists the file as the de-facto registry. `16` names the trigger: lineage questions that storage
alone cannot answer. They arrived — which weights produced a result, who switched models, what
the previous model was.

Two further forces:

- Training moved out of the platform (ADR-012 addendum); weights now arrive from outside and
  must be identified on arrival.
- The AI service holds no database; whatever the registry decides must reach it as a file it
  can trust.

## Decision

Model versions are rows in the web database: name and version unique together, a SHA-256
fingerprint of the weights, a stage (candidate, serving, retired), family, size, input
resolution, a dataset configuration reference and an optional external tracking identifier.
Promotion and rollback are single transactions that demote the previous serving version and
write a promotion event naming the previous version, the user and a reason. Promotion is
performed by a person; the selection score is displayed, never acted on automatically. The
registry exports a JSON list of loadable versions to the shared volume, and the AI service
resolves models exclusively through that list, verifying the fingerprint and refusing arbitrary
paths and directory walks.

Design detail is in [`docs/evolution/02-model-registry-and-promotion.md`](../../evolution/02-model-registry-and-promotion.md).

## Alternatives Considered

### Keep the reference file and add a lock
Rejected. A lock fixes the write race and nothing else: no history, no fingerprint, no reason,
no rollback. It also leaves the AI service trusting a path.

### Use the experiment-tracking tool's model registry
Rejected. ADR-007 had already found the candidate tools' registries weak for this need, and
ADR-012 withdraws the tracking tool altogether. A registry the platform depends on cannot live
in a tool the platform may not deploy.

### Automatic promotion on score
Rejected. It is the initial iteration's "update on improvement" with a database instead of a
file. The race is gone but the judgement is still absent; a person reading the score was judged
cheaper than a wrong model in production.

### A registry inside the AI service
Rejected. The AI service holds no database by design; giving it one for this would split
ownership of rows between the two services.

## Consequences

### Positive
- No race: there is no shared mutable reference to race for.
- Full lineage: version, fingerprint, dataset reference, promotion history with reasons.
- The AI service cannot load unregistered weights, by construction.
- Rollback is one transaction.

### Negative
- One more export to keep in sync; a small window exists between promotion and export.
- Fingerprinting large weights files costs time at registration and export.
- A person must act to promote; the initial iteration's fully automatic loop is gone.

### Neutral
- Training being outside the platform means the registry's import path is the normal path, not
  an exception.

## Revisit When

- Dataset versions become first-class records → replace the dataset reference string with a
  foreign key.
- A second AI service host reads the same registry → move the exported list to a service
  endpoint with the same fingerprint semantics.
- Promotion frequency rises to the point that a person is the bottleneck → gated automatic
  promotion for candidates that pass every validation threshold, with the event still recorded.

## Public-Safe Note

Field names are descriptive placeholders. No schema, module or table name of an implementation
is given; the selection score is described without its weights.
