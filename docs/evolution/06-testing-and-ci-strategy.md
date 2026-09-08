# Testing and CI Strategy Without a GPU

> Public-safe documentation. Design-level description of the test and integration discipline
> of a later revision. Test counts are given as an order of magnitude only; no runner host,
> access path or hardware is described.

## Purpose

`15-limitations-and-risks.md` lists, under reproducibility and testing, that the initial
iteration had no automated tests and no continuous integration: every change was checked by
running a job on the GPU and looking. The revision made the platform testable without a GPU.
This document records how, and what that discipline deliberately does not cover.

## Context

Two facts made testing hard in the initial iteration: the only way to exercise the AI service
was to load real weights on a real device, and the web layer's calls to the service were tested
only by running both. The revision addressed the first with a runtime seam and the second with
contract tests, and then let a CI job run the whole thing on a machine with no GPU at all.

## Design

### The runtime seam

```text
  feature code (inference, sliced inference, validation, training, metrology)
        │
        ▼
  Runtime protocol: load(model_ref) · predict(image, params) · train(config) · device()
        │
   ┌────┴─────────────────┐
   ▼                      ▼
  mock runtime          real runtime
  deterministic          the deep-learning library
  synthetic boxes        device injected from configuration
  no weights, no device  CPU fallback when no device is configured
```

- Every feature depends on the protocol, never on the library.
- The mock returns deterministic detections derived from the image dimensions and the
  parameters, so a test can assert on layout, naming, manifests, GeoJSON and metrology
  arithmetic without any model.
- Which runtime is active is a configuration value; the health endpoint reports it, and every
  run manifest records it (`03`), so a mock result can never be mistaken for a real one.
- The device is **injected**, not probed: the real runtime is told whether a device is
  available. This is what makes "GPU not validated" a precise statement rather than an
  accident (`00`).

### What the suites cover

| Suite | What it asserts | Where |
|---|---|---|
| Unit | Coordinate reconstruction, naming, manifest writing, registry transactions, metrology stages | Both services |
| Contract, wire level | The web layer's client and the AI service's routes agree on every payload and error envelope, exercised through the real HTTP layer with the mock runtime | Both |
| Purity and fences | The web layer's service client imports no framework; the AI service imports no database driver; feature packages do not import each other | Both |
| Document guards | The Compose file chain is consistent; claims the README makes about commands and targets are true; every error code raised is in the catalogue | Repository |
| Console | Every view renders; every string is translated (`05`); permissions hold per group | Web layer |
| Mutation-checked subsets | For coordinate and registry code, a mutation run confirms the tests actually fail when the logic is broken | Both |

The whole set runs on CPU, in the order of two thousand tests, in minutes.

### Continuous integration

```text
  push ─► lint ─► compose-chain guard ─► build both images from the checkout
                                        ─► start a throwaway Compose project
                                            (own name, own volumes, mock runtime)
                                        ─► run both suites inside the containers
                                        ─► tear down, delete volumes
```

- The CI job uses the **same** Compose definitions as a deployment, so what is tested is the
  image that would ship, not a developer's environment.
- The project is throwaway: named per run, volumes removed afterwards, nothing shared with a
  local stack.
- The job is advisory: it reports, it does not yet block merges. Branch protection was a
  process decision deferred until more than one person commits.
- The runner is self-managed. Its host setup is operational detail and is not published.

### What is deliberately not tested

| Not covered | Why | Consequence |
|---|---|---|
| The real runtime on a device | No GPU in CI; the device is injected | Device behaviour, memory and throughput remain claims of the initial iteration (`13`) |
| Model accuracy on real images | No real images or weights in the repository | Accuracy is a property of a trained model, validated outside the platform |
| Sliced inference border behaviour with real detections | Mock boxes do not straddle tiles the way real ones do | Reconstruction is unit-tested on synthetic cases only |
| The browser | No end-to-end browser tests | Views render, interactions are not scripted |
| Metrology against ground truth | See `04` | Arithmetic is tested; the method is not validated |

## Constraints

- The mock has to stay honest: it must produce results with the same shape and edge cases as
  the real runtime, including empty results and failures. A mock that is friendlier than
  reality tests nothing.
- Contract tests double the cost of every payload change, by design.
- CI needs a container runtime on the runner; it does not need anything else.

## Risks

**False confidence.** A green suite says the plumbing is right. The document guard that keeps
the README honest exists precisely because a green badge tempts overstatement.

**Advisory CI is ignorable.** Until it blocks, a red run is a notification. The mitigation is
social, not technical, and is stated as such.

**Mock drift.** The real runtime's output shape changes with library versions; the mock does
not. A contract test against the real runtime on CPU, with tiny weights, is the improvement
that closes this.

## Recommended Improvements

1. A CPU smoke test with a tiny real model in CI, so the real runtime path is exercised at
   least once without a device.
2. Branch protection once a second contributor exists.
3. A scripted browser test for the three core flows: upload, submit, view results.
4. When a device is available to CI, a single device job that runs the same suite with the
   real runtime injected as available.

## Summary

A runtime seam with a deterministic mock, wire-level contract tests between the two services,
purity fences, document guards and a throwaway Compose stack in CI made the revision reviewable
on any machine. The boundary of that confidence is stated: nothing here validates the GPU, the
model or the browser, and the repository does not claim otherwise.
