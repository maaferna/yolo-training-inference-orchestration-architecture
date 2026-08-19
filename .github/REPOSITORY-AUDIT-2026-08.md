# Repository Audit — August 2026

Complete audit of the repository against its own public-safe policy
(`docs/architecture/16-public-release-sanitization.md`, `.github/public-safety-checklist.md`)
and against internal consistency, technical accuracy and portfolio effectiveness.

- **Audited at**: commit `034d5c6`
- **Scope**: all 165 tracked files, ~43,500 lines of Markdown. Includes `.github/archive/` —
  that directory is committed and therefore public, whatever its name suggests.
- **Method**: automated sweeps for leaks, link resolution against disk, structural comparison of
  declared indexes versus the real tree, cross-document contradiction checks on load-bearing
  architectural claims, provenance tracing of every quantitative claim, and reproducibility
  checks on the generated assets.

## Verdict

**No critical leak blocks publication.** No credential with a real value, no client, institution
or person other than the author, no real dataset, model weight, screenshot or inference output
exists anywhere in the tree. Placeholder discipline in `examples/` and in the architecture
documents is genuinely good.

The problems are of a different kind, and there are two clusters of them.

**The safety process the repository documents no longer runs.** `CONTRIBUTING.md` still tells
contributors to execute five sanitization scripts that were deleted in `ca58f44`, including one
it instructs them to install as a git pre-commit hook. The enforcement mechanism for the
repository's central policy is now a set of commands that error out.

**Numbers presented as results have no source.** "80% OOM reduction" and "15-25% mAP improvement"
appear only in the two portfolio documents and nowhere in the architecture documentation.
"~60% cost savings" is derived from a cost model whose every input is a placeholder. All three
are fed into resume bullets, and the portfolio guide's own DO list instructs the reader to use
them — on the same page where its DON'T list forbids overclaiming.

---

## High

| # | Finding | Location |
|---|---|---|
| H1 | **The documented safety gate is broken.** Six commands reference the sanitization scripts deleted in `ca58f44`: "Before committing, run `bash validate-sanitization.sh`", "Before pushing, run `bash complete-sanitization-check.sh`", "If either script fails, do not push", and `cp validate-sanitization.sh .git/hooks/pre-commit`. The scripts do not exist, so the hook install fails silently and every check errors with "No such file". A contributor following the documented process gets no sanitization coverage at all. | `CONTRIBUTING.md:63,69,203,204,222,225` |
| H2 | **Unsourced performance claims used in CV material.** "reducing OOM incidents by 80%" appears 8 times and "15-25% mAP improvement on small objects" 5 times, exclusively inside `docs/portfolio/`. Neither number appears in `13-error-handling-and-fallbacks.md`, `12-gpu-resource-management.md`, `10-sahi-inference-engine.md` or anywhere else. They have no derivation in the repository. | `PORTFOLIO_RESUME_CONTENT.md:36,196,517,538,651` · `PORTFOLIO_IMPLEMENTATION_GUIDE.md:28,110,150,244,245,415,435` |
| H3 | **A cost saving asserted from a model made entirely of placeholders.** The cost analysis reads `Monthly subscription: $X` / `Storage: $Y` / `Server/VM: $Z` / `Ops time: 4 hours × $rate`. Nothing can be computed from it, yet line 14 states "~60% savings after 6 months" as fact, and the delivery report derives it from an equally unsourced "~40% of cloud cost". The claim then propagates to 8 locations including resume bullets. Separately, `ROI breakeven: $ANNUAL_CLOUD / $ANNUAL_SELFHOSTED` is a ratio, not a breakeven — a breakeven is a point in time. | `MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md:14,44-62` · `MLOPS_DELIVERY_REPORT.md:141-142` · `MLOPS_DOCUMENTATION_SUMMARY.md:232,274` · `MLOPS_IMPLEMENTATION_ROADMAP.md:521` · both portfolio docs |
| H4 | **The documentation index names files that do not exist.** 11 of 20 entries are wrong (`09-yolo-training-engine.md` … `19-jupyter-research-workflow.md`); the last never existed in any form. Two real documents — `18-inference-result-synchronization.md` and `19-deployment-cost-strategy.md` — are missing from the index entirely. | `README.md:480-501` |
| H5 | **The repository tree block repeats the same wrong numbering** and places `public-safety-checklist.md` at the root; it lives in `.github/`. | `README.md:441-471,508` |
| H6 | **Multi-GPU is described two incompatible ways.** README and `02-system-architecture.md` state "Training GPU execution — Implemented / evaluated", "DataParallel support and evaluated DDP patterns". `12-gpu-resource-management.md` states "DataParallel (Current **Single-GPU** Approach)", "Why Single GPU Currently", "Distributed Data Parallel (DDP) — **Deferred to Phase 3**" and "Current: Sequential Training on Same GPU". The front page oversells relative to the document that actually specifies the runtime. | `README.md:70,134,259,297` vs `12-gpu-resource-management.md:120,144,154,376` |
| H7 | **A diagram advertises a job queue the architecture declares absent.** `FastAPI->>FastAPI: Queue training job` and `Accept (status=QUEUED)` are shown as current behaviour. Every architecture document states execution is synchronous and no queue exists. (By contrast `14-limitations-and-risks.md:130` shows `QUEUED` under an explicit "Recommended: Async Pattern / # Future approach" heading — that one is correct and is **not** a finding.) | `diagrams/training-flow.mmd:11-12` |

## Medium

| # | Finding | Location |
|---|---|---|
| M1 | **A real absolute path is still published.** `Project Root: /home/user/myprojects/...`. The policy at `16-public-release-sanitization.md:22` forbids exactly this. It survived the `ca58f44..f390374` cleanup, which edited this very file. Also in three archive files. | `MLOPS_QUICK_REFERENCE.md:147` · `.github/archive/{PUBLICATION-READY.md:187, IMPLEMENTATION-COMPLETE.md:320, SANITIZATION_IMPLEMENTATION_GUIDE.md:188}` |
| M2 | **Duplicate numbering.** Two documents share prefix `08-`, and two ADRs share `ADR-001`. This is the root cause of H4 and H5: everything after `08` is offset by one. | `docs/architecture/08-*` · `adr/ADR-001-*` |
| M3 | **Two accepted ADRs decide the same thing.** `ADR-004` and `ADR-007` both adopt ClearML for experiment tracking; both are `Status: Accepted`; neither supersedes the other. A reader cannot tell which governs. | `adr/ADR-004`, `adr/ADR-007` |
| M4 | **The YOLO version is inconsistent.** `YOLOv8` appears 15 times, `YOLOv11` 6 times, and `environment.example.env` sets `YOLO_VERSION=11`, while the README speaks generically of "YOLO". `MLOPS_QUICK_REFERENCE.md:12` offers "YOLO-v8, v8, v5". | across `docs/`, `diagrams/`, `examples/` |
| M5 | **A dangling reference created by the recent cleanup.** "See docs/adr for detailed decision rationale" — that directory was removed in `f390374`. The path is now `docs/architecture/adr/`. | `PORTFOLIO_RESUME_CONTENT.md:653` |
| M6 | **Seven broken internal links in live documents.** Five use `./docs/20-synthetic-dataset-generation-pipeline.md` with a duplicated `docs/` segment; two in `ADR-001-path-translation-layer.md` resolve outside the `adr/` directory; `README.md:334` points to `./CASE-STUDY.md`, which has never existed. | `03:519`, `04:613`, `14:533`, `16:434`, `17:533`, `adr/ADR-001-path-translation-layer.md:365-366`, `README.md:334` |
| M7 | **27 of 79 archive files are 0 bytes.** | `.github/archive/` |
| M8 | **`MLOPS_QUICK_REFERENCE.md` is the least sanitized file in the repository.** Beyond M1 it points at `docs/MLOPS_STATUS_REPORT.md` and `docs/MIGRATION_*` (both moved to `docs/operations/`), documents a `shared_storage/` tree that does not match `07-shared-storage-and-artifacts.md`, and uses `http://fastapi:8080` where every other document uses `:8001`. | `MLOPS_QUICK_REFERENCE.md:12,147,150-154,260-261,281` |
| M9 | **A weak credential in a copyable compose example.** `MONGO_INITDB_ROOT_PASSWORD: clearml_password`. It is clearly a sample, but it is the one place in the repository where a literal password appears instead of a placeholder, and it is in a block a reader may paste. | `adr/ADR-004-clearml-experiment-tracking.md:375` |
| M10 | **`docs/README.md` is stale.** Claims "20 documents" (there are 21), describes `operations/` as "(future)" and "(emerging)" when it holds seven documents, and its "13-20" grouping no longer matches the subjects at those numbers. | `docs/README.md:9,18,32,39` |

## Low

| # | Finding |
|---|---|
| L1 | Roughly 45 broken internal links inside `.github/archive/`, including `./docs/architecture/0system-architecture.md` (truncated filename) in `CASE-STUDY.md:1483` and `LEARNING-PATH.md:106`. |
| L2 | Concrete ports and hostnames scattered and mutually inconsistent: `localhost:8008`, `clearml-server:8008`, `fastapi:8001`, `fastapi-service:8080`, `django:8000`. Not a leak — none is a real host — but it reads as unreviewed. |
| L3 | `deep_learning/deep_learning/` duplicated route appears in two documents. It is documented honestly as a known routing bug, which is a point in the repository's favour; it does expose an internal app naming convention. |
| L4 | `README.md:295-309` describes an "Engineering Case Study" document that is not in the repository, hedged as "if included in your repository". |
| L5 | Author-facing template residue in reader-facing text: "Adjust the structure to match your actual repository" (`README.md:473`). |
| L6 | **The licence does not fit the artefact.** `LICENSE` is MIT — a software licence — for a repository that is 128 Markdown files, 8 generated images and no application code. For prose and diagrams the conventional choice is CC BY 4.0. This matters now that the images are being embedded in a separate portfolio project: MIT's terms are written around "the Software" and its attribution requirement sits oddly on an image tag. |
| L7 | `README.md` is 711 lines / 40 KB. As the front door for a portfolio reviewer this is long; the strongest material (the non-goals, the risk register, the cost reasoning) sits far below the fold. |

## Verified clean

- **Credentials**: every occurrence is a placeholder (`PLACEHOLDER_*`, `[..._PLACEHOLDER]`,
  `NEVER_COMMIT`). The `clearml-xxxxxxxxxxxxx` in `CONTRIBUTING.md:176` and
  `PASSWORD_PLACEHOLDER` in `06-docker-runtime-architecture.md` are policy examples, which is
  their intended use. The single exception is M9.
- **Network identifiers**: only `0.0.0.0`, `127.0.0.1`, `localhost` and container service names.
  The two IPs in `16-public-release-sanitization.md:22` are the policy quoting its own
  forbidden patterns.
- **Proper nouns**: technologies, plus the author's own name in `LICENSE` and public GitHub
  handle. No client, institution, field, farm, researcher or project name.
- **Binary assets**: the only binaries are the eight diagrams generated by
  `scripts/build_visuals.py`. No screenshot, inference preview, mask, drone photograph, model
  weight or dataset.
- **Example payloads**: `examples/api-payloads/` and `examples/artifact-manifests/` use generic
  identifiers throughout.
- **Generated visuals**: `scripts/build_visuals.py` reproduces its SVG output byte-for-byte and
  the PNGs re-render identically. The diagrams carry no fabricated metric, pin no YOLO version,
  and the one mention of a queue is explicitly framed as conditional and future.

## Resolved since the previous pass

Fixed on `master` in `ca58f44..f390374`, verified after rebase:

- the empty `docs/adr/` directory and its eight 0-byte files — removed;
- the five 0-byte sanitization scripts — removed.

Both fixes removed the artefact but left the references behind: the scripts produced **H1**
(six dangling commands in `CONTRIBUTING.md`) and the directory produced **M5**. The habit worth
adopting is to re-grep for the name of anything deleted before committing the deletion.

## Recommended order of work

1. **H1** — repair or remove the safety gate in `CONTRIBUTING.md`. The repository currently
   documents a control that cannot run. Either reimplement the scripts or replace those sections
   with the sweeps now held in `.claude/skills/public-safe-audit/SKILL.md`.
2. **H2, H3** — qualify or delete the unsourced numbers, and remove the DO-list instruction that
   tells the reader to reuse them. Highest credibility return in the repository for the least
   effort.
3. **H4, H5, M2, M10** — resolve the `08-` collision, then regenerate every index and tree from
   disk. One commit, since renumbering moves filenames and inbound links.
4. **H6, H7, M4** — reconcile the multi-GPU wording with `12-gpu-resource-management.md`, remove
   the queue from `training-flow.mmd`, and settle on one YOLO version or on none.
5. **M1** — delete the leaked absolute path. One line, still open after two cleanup passes.
6. **M5, M6** — repair the eight broken links.
7. **M3, M9, M8** — supersede one ClearML ADR, replace the literal Mongo password with a
   placeholder, and give `MLOPS_QUICK_REFERENCE.md` the sanitization pass the rest of the
   repository has had.
8. **L1–L7** — hygiene. Of these, **L6** (licence) is worth an early decision because the
   diagrams are already being reused in a separate project.

Items 1 through 5 are what a technical reviewer is most likely to hit in the first ten minutes.
