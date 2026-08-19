# Repository Content Audit — August 2026

Full audit of the repository against its own public-safe policy
(`docs/architecture/16-public-release-sanitization.md`) and against internal consistency.

- **Scope**: every tracked file except `.git/`, including `.github/archive/` — that directory is
  committed and therefore public, whatever its name suggests.
- **Volume reviewed** (at commit `ed8b778`): 21 architecture documents, 9 ADRs, 7 operations documents, 2 portfolio
  documents, 4 Mermaid sources, 8 example files, 5 scripts, 79 archive files (~21,000 lines).
- **Method**: pattern sweeps for leaks, link resolution against disk, structural comparison of
  the declared index versus the real file tree, and reading for contradictions between documents.

## Verdict

**No critical leak blocks publication.** No credential with a real value, no client or
institution name, no real dataset, no model weight and no real image exists anywhere in the tree.
The placeholder discipline is applied consistently in `examples/` and in the architecture
documents.

Two problems do reach the level that a technical reviewer would notice, and both damage
credibility rather than security: **unsourced quantitative claims presented as results**, and a
**documentation index that does not match the files on disk**.

---

## Findings

| # | Severity | Category | Location | Finding |
|---|---|---|---|---|
| 1 | High | Unsourced metrics | `docs/portfolio/PORTFOLIO_RESUME_CONTENT.md:36,56,302` · `PORTFOLIO_IMPLEMENTATION_GUIDE.md:28,110,150,406` | Resume bullets claim "reducing OOM incidents by 80%", "~60% cost reduction", "by 50%". The README states the repository contains no real metrics. A reviewer who compares the two finds a contradiction, and it puts every other claim in doubt. |
| 2 | High | Unsourced metrics | `docs/architecture/10-sahi-inference-engine.md:256-266,312,325,338` | Latency figures (`600ms`, `1200ms`, `2500ms`) and recall figures (75%, 90%, 95%) are presented as results with no note that they are illustrative. |
| 3 | High | Internal contradiction | `diagrams/training-flow.mmd:11-12` | The diagram shows `Queue training job` and `status=QUEUED`. Every architecture document states there is no job queue and that execution is synchronous. The diagram advertises a capability the architecture explicitly declares absent. |
| 4 | High | Index desync | `README.md:480-501` | The documentation index lists `09-yolo-training-engine.md` through `19-jupyter-research-workflow.md`. On disk the numbering is shifted by one from `08` onward, and `19-jupyter-research-workflow.md` does not exist. Eleven of twenty entries point at filenames that are not in the repository. |
| 5 | High | Index desync | `README.md:441-471` | The repository tree block reproduces the same wrong numbering and places `public-safety-checklist.md` at the root; it actually lives in `.github/`. |
| 6 | Medium | Duplicate numbering | `docs/architecture/08-yolo-training-engine.md` · `08-yolo-dataset-configuration-management.md` | Two distinct documents share the prefix `08`. This is the root cause of findings 4 and 5. |
| 7 | Medium | Duplicate content | `docs/architecture/adr/ADR-004-clearml-experiment-tracking.md` · `ADR-007-clearml-experiment-tracking.md` | Two accepted ADRs decide the same thing — ClearML for experiment tracking — without either superseding the other. Also `ADR-001` exists twice: `ADR-001-separate-web-and-ai-services.md` and `ADR-001-path-translation-layer.md`. |
| 8 | ~~Medium~~ **Resolved** | Ghost directory | `docs/adr/` | A parallel ADR directory of 8 empty files duplicating the real `docs/architecture/adr/`. Removed in `ff31efd`/`f390374`; inbound references repointed in `63b3d0a`. |
| 9 | ~~Medium~~ **Resolved** | Empty scripts | `scripts/*.sh` | Five 0-byte sanitization scripts advertised a safety gate that did not exist. Removed in `ca58f44`. The sweeps they implied now live in the `public-safe-audit` skill. |
| 10 | Medium | Empty files | `.github/archive/` (27 of 79 files) | Roughly a third of the archive consists of 0-byte files. |
| 11 | Medium | Broken links | 8 occurrences | `README.md:297` → `./CASE-STUDY.md` (never existed). Five documents link to `./docs/20-synthetic-dataset-generation-pipeline.md` with a duplicated `docs/` segment: `03:519`, `04:613`, `14:533`, `16:434`, `17:533`. `adr/ADR-001-path-translation-layer.md:365-366` links to sibling paths that resolve outside the `adr/` directory. |
| 12 | Medium | Leaked local path | `docs/operations/MLOPS_QUICK_REFERENCE.md:147` | `Project Root: /home/user/myprojects/...` — a real absolute path in a live document. The policy at `16-public-release-sanitization.md:22` forbids exactly this. Still present after the `ca58f44..f390374` cleanup touched this file. Also in `.github/archive/IMPLEMENTATION-COMPLETE.md:320` and `PUBLICATION-READY.md:187`. |
| 13 | Low | Stale count | `docs/README.md:8,40` | States "20 documents" and a `13-20` grouping that no longer matches the 21 files or their current subjects. |
| 14 | Low | Illustrative values unmarked | `diagrams/ci-training-flow.mmd:24`, `docs/architecture/07:276,654`, `11:421` | `mAP50` values appear without an illustrative marker. Low risk — clearly synthetic — but inconsistent with the strict policy stated in the README. |
| 15 | Low | Dangling reference | `README.md:295-309` | An "Engineering Case Study" section describes a document that is not in the repository, hedged as "if included in your repository". |
| 16 | Low | Template residue | `README.md:473` | "Adjust the structure to match your actual repository" — instructions to the author left in reader-facing text. Same pattern in `docs/README.md` ("operations/ (future)") although `operations/` now holds seven documents. |

## What was verified clean

- **Credentials**: every occurrence is a placeholder (`PLACEHOLDER_*`, `[..._PLACEHOLDER]`). The
  `clearml-xxxxxxxxxxxxx` in `CONTRIBUTING.md:176` and `PASSWORD_PLACEHOLDER` in `06-docker-runtime-architecture.md`
  are policy examples, which is their intended use.
- **Network identifiers**: only `0.0.0.0`, `127.0.0.1` and `localhost`.
- **Binary assets**: before this audit the repository contained no images at all. The PNGs now in
  `assets/` are synthetic diagrams generated from `scripts/build_visuals.py`; no screenshot,
  inference preview, mask or drone photograph exists anywhere.
- **Proper nouns**: the only named entities are technologies and the author's own public GitHub
  handle. No client, institution, field, farm or person appears.
- **Example payloads**: `examples/api-payloads/` and `examples/artifact-manifests/` use generic
  identifiers throughout.

## Status

Findings 8 and 9 were fixed on `master` in `ca58f44..f390374`, independently of and
concurrently with this audit. Re-verified after rebase: the empty ADR directory and the
empty sanitization scripts are gone. **Finding 12 survived that cleanup and is still open**
— the same commit range edited `MLOPS_QUICK_REFERENCE.md` without removing the leaked path.
All other findings stand as written.

## Recommended order of work

1. **Mark or remove the unsourced numbers** (findings 1, 2, 14). Highest credibility return for
   the least effort. Either qualify each figure as illustrative or replace it with a directional
   statement.
2. **Fix the Mermaid queue contradiction** (finding 3). One diagram, two lines.
3. **Resolve the `08` collision and regenerate the index** (findings 4, 5, 6, 13). Renumbering
   touches filenames, so do it in one commit and update every inbound link.
4. **Repair the eight broken links** (finding 11).
5. **Remove the leaked absolute path** (finding 12). One line, still open.
6. **Decide on the remaining empty files** (finding 10): 27 of the 79 archive files are 0 bytes.
7. **Reconcile the ClearML ADRs** (finding 7): mark one `Superseded by`, or merge them.
8. **Clean the template residue** (findings 15, 16).

Items 1 through 4 and 6 are what a technical reviewer is most likely to notice in the first ten
minutes of reading. Items 5, 7 and 8 are hygiene.
