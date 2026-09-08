# ADR-011: Mount Shared Storage at the Same Path in Every Container

**Status**: Accepted
**Iteration**: revision
**Public-Safe**: Yes
**Supersedes**: [ADR-008](./ADR-008-path-translation-layer.md) — the path translation layer.

---

## Context

ADR-008 and `19-inference-result-synchronization.md` describe a translation layer between four
coordinate systems: the AI service's container path, the web layer's container path, the host
path and the URL the browser sees. The initial iteration implemented it as string replacement
with hard-coded prefixes, and `07-shared-storage-and-artifacts.md` lists path mismatch as a
standing risk. The revision had to decide whether to formalize the translator or remove the
need for it.

Forces:

- Both containers run on the same host and mount the same volume.
- Every artifact reference the web layer needs is produced by the AI service.
- The browser never needs a filesystem path; it needs a URL the web layer serves.
- Path bugs were silent: a wrong prefix produced a missing preview, not an error.

## Decision

The shared volume is mounted at the **same absolute path** in the web container and the AI
service container. Both services read their storage root from configuration, and the two
values are required to be identical: each service asserts it at startup against the value the
other reports on its health endpoint, and a test in each repository fails if the configured
roots diverge. Every path written into a job record or run manifest is **relative to the run
directory**. The web layer builds URLs from those relative paths; nothing translates an
absolute path into another absolute path anywhere.

Design context is in [`docs/evolution/03-service-contracts.md`](../../evolution/03-service-contracts.md).

## Alternatives Considered

### Formalise the translator as a module with tests
Rejected. It would have made a workaround reliable instead of removing it. Four coordinate
systems remain four opportunities to be wrong.

### Have the AI service serve artifacts over HTTP
Rejected for this iteration. It removes the shared mount from the web layer at the cost of a
second file-serving path, streaming large outputs through the API process, and a new
authorization surface. The trigger for it is a second host; it has not fired.

### Object storage with signed URLs
Rejected. `16` names it as optional scale-out with its own trigger (storage hard to govern
locally), which had not fired. It also does not remove the need for a stable relative layout.

## Consequences

### Positive
- The translation layer and its class of silent bugs are gone.
- Manifests are portable: relative paths survive a change of mount point on both sides at once.
- The invariant is checked by machines, not remembered by people.

### Negative
- Both containers must be able to mount the same path, which ties them to one host or to a
  shared filesystem exposed at the same path. This is stated as the assumption it is.
- Any deployment variant that cannot honor the invariant fails at startup rather than degrading.

### Neutral
- The web layer still reads the volume directly. The coupling ADR-002 accepted remains; it is
  now a documented invariant instead of a translation.

## Revisit When

- The AI service moves to a second host → artifacts served over HTTP or object storage, with
  the relative layout kept as the contract.
- Multiple AI service instances write to the same volume → per-instance run prefixes to avoid
  collisions.

## Public-Safe Note

This ADR states a configuration invariant. No real mount path, hostname or filesystem detail
is given; the container path placeholders of the repository apply.
