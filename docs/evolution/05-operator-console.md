# Operator Console: Batches, Maps and Localisation

> Public-safe documentation. Design-level description of the web layer in a later revision. No
> screenshots, no place names, no example coordinates from real imagery. The geospatial
> computation itself is documented in the companion evaluation-pipeline repository; this
> document covers how the web layer consumes and presents it.

## Purpose

The initial iteration's web layer submitted jobs and showed previews
(`03-component-responsibilities.md`, `19-inference-result-synchronization.md`). The revision
turned it into an operator console: batches with progress, results on an interactive map,
downloadable artifacts, and an interface in the operators' language. This document records the
design decisions behind that console.

## Context

Once execution became submit/poll (`01`), the web layer had to do three new things: show a
batch's progress while it runs, present results that are spatial rather than only visual, and be
usable by staff who are not developers. Each led to a decision.

## Design

### Batch lifecycle

```text
  upload images ─► batch created ─► submit (one run per image or per group)
       │                                     │
       │                                     ▼
       │                         job-history rows: submitted
       │                                     │
       ▼                                     ▼
  progress page  ◄── poll (batched) ──  running / done / failed per run
       │
       ▼
  results page: table, previews, map, downloads, metrology (if run)
       │
       ▼
  delete batch ─► cascades: runs, outputs, job records, metrology outputs
```

- A **batch** is the operator's unit; a **run** is the service's. The console maps one to the
  other and never shows a run identifier as the primary key.
- Progress is a page that polls the batched status endpoint and updates counts in place.
- Artifacts (previews, tables, GeoJSON) are read **straight from the shared volume** by the web
  layer, using the relative paths in the run manifest (`03`). The AI service does not serve
  files.
- Deletion cascades from the batch so that storage does not accumulate orphaned runs.

### Interactive map from GeoJSON

The AI service writes, per batch, a GeoJSON document with the image footprints, the detections
(as points or polygons in geographic coordinates) and, when metrology ran, the foci and coverage
cells (`04`). The geographic transform, from pixel to projected to geographic coordinates, is the
one documented in the companion evaluation-pipeline repository; the console does not repeat it.

The console renders that document on an interactive map:

- **Vendored map library, no build step.** The JavaScript and CSS of the map library and of the
  UI framework are committed as static files. There is no bundler, no package manager step and
  no network dependency at render time. The decision is recorded as a design rule: a console
  that must run on an isolated internal host cannot depend on a CDN, and a documentation-driven
  team should not have to maintain a front-end build.
- Layers per kind: footprints, detections per `DetectionClass`, foci, coverage. Each can be
  toggled; the popup on a detection shows its class, confidence and, when available, physical
  size with its gate status.
- The base layer is whatever the deployment configures; the console ships with none, so a
  deployment without external connectivity still renders the overlays on a blank canvas.
- The same GeoJSON is downloadable, so a desktop GIS can open it; the console is a viewer, not
  the system of record.

### Localisation

The console is presented in the operators' language, not the developers'.

- Every user-facing string goes through the framework's translation catalogue; source strings
  are English, the catalogue supplies the interface language.
- A **guard test** renders every console view and fails if an untranslated source string
  appears. This is what keeps the catalogue complete: a developer who adds a label without a
  translation breaks the build, not the operator's morning.
- Dates, numbers and units follow the interface locale; identifiers and codes (`03`) do not,
  because they are contracts.

### Roles

Two groups: *operate* (upload, submit, view, download, delete own batches) and *administer*
(users, tokens, model promotion, all batches). Promotion (`02`) is deliberately behind the
second.

## Constraints

- The console reads the volume, so the web container must mount it at the same path as the AI
  service (`03`, ADR-011).
- A map with tens of thousands of detection points becomes slow in the browser. The console
  clusters points at low zoom and shows coverage cells instead of individual detections past a
  configurable count.
- One interface language at a time per deployment. Multi-language switching per user was not
  needed and was not built.

## Risks

**Rendering from the volume couples the console to the storage layout.** The run manifest's
relative paths are the contract; a change in output layout that is not reflected in manifests
breaks pages silently. The manifest schema test (`03`) is the mitigation.

**Vendored libraries age.** Without a package manager, updating the map or UI library is a
manual copy. The trade-off is accepted for an internal tool; the version is recorded in a
checked-in note.

**A map implies precision.** A point on a map reads as exact; the underlying position has the
uncertainty of the image geotag. The popup shows the gate status for metrology; it does not yet
show positional uncertainty.

## Recommended Improvements

1. Positional uncertainty in the detection popup, derived from the image geotag accuracy.
2. A "download batch as archive" action, so operators do not fetch artifacts one by one.
3. Server-side tiling of overlays if batch sizes grow past what the browser clusters
   comfortably.

## Summary

The console makes the submit/poll model visible (progress per batch), makes results spatial (a
GeoJSON layer per batch on an interactive map with vendored libraries and no build step), and
makes the tool usable by its actual operators (a translation catalogue enforced by a guard
test). It reads artifacts from the volume through the manifest contract and leaves the
geospatial mathematics to the pipeline that produces the GeoJSON.
