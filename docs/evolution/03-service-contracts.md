# Service Contracts: Errors, Manifests and Authentication

> Public-safe documentation. Design-level description of a later revision. Error codes, fields
> and header names are illustrative shapes, not the published contract.

## Purpose

`05-api-integration-contracts.md` gives the conceptual payloads of the initial iteration and
notes that the boundary carried a user identifier but no credential, and that errors were
messages rather than a contract. `14-error-handling-and-fallbacks.md` lists failure scenarios
as prose. `19-inference-result-synchronization.md` and ADR-008 describe a path-translation layer
across four coordinate systems. This document describes the three contracts the revision put in
their place: one error envelope, one run manifest, one authentication scheme, plus the storage
invariant that made path translation unnecessary.

## Context

Contracts became necessary the moment the request stopped waiting
(`01-submit-poll-execution.md`). A console that polls has to interpret a status and an error
without a human reading a log; a run that finishes after the request has ended has to describe
itself; and a service that accepts work asynchronously has to know who submitted it.

## Design

### One error envelope

Every non-success response from the AI service, and every JSON error from the web layer's own
endpoints, has the same shape:

```json
{
  "error": {
    "code": "INPUT_NOT_FOUND",
    "message": "Illustrative human-readable text",
    "details": { "path": "PLACEHOLDER_RELATIVE_PATH" }
  }
}
```

- `code` is stable and documented in a catalogue; renaming a code is a breaking change.
- `message` is for people and may change freely.
- `details` is structured and optional.
- HTTP status carries the class (400 validation, 401/403 authentication and permission, 404,
  409 conflict, 422 semantic, 500 unexpected); the code carries the cause.

The catalogue lives next to the contract and is maintained **in the same change** as any
endpoint that raises a new code. A test asserts that every code raised in the service appears in
the catalogue and vice versa.

### One run manifest

Every job writes a manifest beside its outputs when it finishes, and only then: a run without a
manifest is a run that did not finish.

```text
  <run_id>/manifest.json
  ├── run: identifier, feature, status, started/finished (relative to the run)
  ├── inputs: what was received — counts, resolutions, formats, source batch
  ├── runtime: mock or real, library versions, device as reported, model fingerprint
  ├── parameters: the job's configuration as actually used
  ├── outputs: one entry per file with role, relative path and size
  └── schema_version
```

The manifest is **append-only in schema**: fields may be added, never renamed or removed, so an
old manifest is always readable by a new console. Every path in it is relative to the run
directory. The web layer reads manifests directly from the volume to render results; it never
asks the AI service to serve a file.

### One mount path

The initial iteration mounted the shared volume at different paths in each container and
translated between them (ADR-008). The revision mounts the volume at the **same absolute path**
in both containers and states that as an invariant: the AI service's storage root and the web
layer's storage root are the same string, checked at startup, and a test fails if the two
configuration values ever diverge. With one path there is nothing to translate, and every path
in a manifest is relative anyway. ADR-011 records the decision and supersedes ADR-008.

### Authentication

| Boundary | Scheme |
|---|---|
| Web layer ↔ AI service | A service key sent in a header; compared in constant time; rotated by configuration |
| Operator ↔ web layer (browser) | Framework sessions, CSRF, two permission groups (operate, administer), lockout after repeated failures, forced password change on first login |
| Automation ↔ web layer (API) | Bearer tokens stored **hashed**; the plaintext is shown once at creation; revocable individually |

The initial iteration's `user_id` in the payload is kept as provenance but no longer implies
authorisation; the token or session does.

## Constraints

- The envelope is JSON only. HTML error pages exist for the browser but never for the
  service boundary.
- The manifest is written once. A job that wants to report progress uses the job record
  (`01`), not the manifest.
- Same-path mounting assumes both containers run on the same host or share the same network
  filesystem path. That is true at this scale and is stated as the assumption it is.

## Risks

**Catalogue drift.** Codes multiply. The test that ties catalogue and code together is the
only thing that keeps the list honest; the count in the revision was in the tens.

**Manifest bloat.** Recording every output with size is cheap; recording per-detection data in
the manifest would not be. Detections stay in their own output files; the manifest lists them.

**Header key as a shared secret.** One key for the web layer means one rotation affects one
client. It is adequate for two processes on one host; it is not a multi-tenant design.

## Recommended Improvements

1. A `request_id` echoed in every envelope and manifest, so a failed job can be traced from
   the console to the service log.
2. Signed manifests, once anyone other than the two services reads them.
3. Per-feature service keys if a second AI service host ever appears.

## Summary

Three contracts replaced three kinds of prose: an error envelope with stable codes, a
per-run manifest with provenance and relative paths, and explicit authentication at both
boundaries. The same-path invariant removed the need for path translation altogether. Together
they are what allowed the request to stop waiting (`01`) without losing the ability to explain
what happened.
