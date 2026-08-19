# Repository Audit — August 2026

Complete audit of the repository against its own public-safe policy
(`docs/architecture/17-public-release-sanitization.md`, `.github/public-safety-checklist.md`)
and against internal consistency, technical accuracy and portfolio effectiveness.

- **Audited at**: commit `034d5c6`
- **Scope**: all 165 tracked files, ~43,500 lines of Markdown. Includes `.github/archive/` —
  that directory is committed and therefore public, whatever its name suggests.
- **Method**: automated sweeps for leaks, link resolution against disk, structural comparison of
  declared indexes versus the real tree, cross-document contradiction checks on load-bearing
  architectural claims, provenance tracing of every quantitative claim, and reproducibility
  checks on the generated assets.

## Verdict

> **Correction, added during step 5.** The statement below was wrong. It was reached by sweeping
> for leak *patterns* — credentials, IPs, paths — and `.github/archive/` contains no credential
> and no client name in the ordinary sense. What it contains is **C1 below**: the sanitization
> mapping table itself, which converts every placeholder in the public documentation back to its
> private original. A pattern sweep cannot see that, and this audit should have read the archive
> rather than only grepping it.

~~**No critical leak blocks publication.**~~ **One critical finding: C1.** Otherwise no
credential with a real value, No credential with a real value, no client, institution
or person other than the author, no real dataset, model weight, screenshot or inference output
exists anywhere in the tree. Placeholder discipline in `examples/` and in the architecture
documents is genuinely good.

The problems are of a different kind, and there are two clusters of them.

~~**The safety process the repository documents no longer runs.**~~ **Resolved** — see H1.
`CONTRIBUTING.md` told contributors to execute five sanitization scripts deleted in `ca58f44`,
including one installed as a git pre-commit hook. The enforcement mechanism for the repository's
central policy was a set of commands that errored out. It is now a single working gate.

~~**Numbers presented as results have no source.**~~ **Resolved** — see H2 and H3. "80% OOM
reduction" and "15-25% mAP improvement" appeared only in the two portfolio documents and nowhere
in the architecture documentation. "~60% cost savings" derived from a cost model whose every
input was a placeholder. All three fed into resume bullets, and the portfolio guide's own DO list
instructed the reader to use them — on the same page where its DON'T list forbids overclaiming.

The `Level 2/5 → 4/5` maturity claim was **checked and kept**: unlike the others it is a genuine
self-assessment against the rubric defined at `MLOPS_STATUS_REPORT.md:57`. It is now labelled
"self-assessed" wherever it appears. Also checked and kept: the `1%` promotion threshold and the
`50%` batch-size fallback step, which are configuration values, not results.

---

## Critical

| # | Finding | Location |
|---|---|---|
| C1 | **The archive published the key to the sanitization.** `.github/archive/` was committed and public. It contained the complete before-and-after mapping produced during the public-release cleanup, presented as a table pairing each private identifier — container paths and Django model names — with the generic name that replaced it. Every generic name a reader meets in the live documentation could therefore be reversed to its private original, including an institution acronym the owner is not cleared to publish. The live documents were largely clean; the archive undid them. **Resolved**: the 79-file archive is deleted, and the sanitization is completed in the live documents, which had themselves retained 33 private identifiers the original cleanup missed. This report deliberately does not restate the mapping. | `.github/archive/` (deleted) · 8 live files |
| C2 | ~~**Git history retained the pre-sanitization documents.**~~ **Resolved.** The commit that generalized the private identifiers left the earlier content reachable through `git log -S` and `git show`, so deleting the archive at `HEAD` was not sufficient. History was rewritten with `git-filter-repo` across all 64 commits, covering file contents, commit messages — three of which spelled the mapping out in prose, including one written during this audit — and every case variant of each identifier. Verified against a fresh clone of the remote: zero occurrences in content, messages and paths. All 64 commits, their authorship and dates are preserved; every SHA changed. | all commits, rewritten `6474480` → `8ac66da` |

**Residual exposure after C2 — measured, not assumed.** Force-pushing repoints the branch but
does not remove the old objects from GitHub. Checked directly against the API and the raw host:

- All 12 pre-rewrite commits that carried the identifier still resolve at
  `/repos/{owner}/{repo}/commits/{sha}` (HTTP 200).
- The deleted archive file is still downloadable at `raw.githubusercontent.com/.../2fab4da/...`,
  identifiers intact.
- The commit message of `2fab4da` still contains all eight identifiers, because it described the
  mapping in prose before that message was rewritten.

`raw.githubusercontent.com` does **not** serve every old path — `eaba2f2` returns 404 — so the
exposure is partial rather than complete, but it is live.

Closing it requires GitHub Support to purge the cached views; the request is drafted with these
SHAs as evidence. Switching the repository to private closes public access immediately and is
the faster mitigation the owner controls, at the cost of breaking the diagram URLs while private.
No credential was involved, so nothing needs rotating. There were no forks at the time of the
rewrite, which bounds the exposure.

## High

| # | Finding | Location |
|---|---|---|
| H1 | ~~**The documented safety gate is broken.**~~ **Resolved.** Six commands referenced sanitization scripts deleted in `ca58f44`, including one installed as a pre-commit hook that failed silently. Fixed by implementing a single working gate, `scripts/validate-sanitization.sh`, and rewriting the three affected sections of `CONTRIBUTING.md` around it. The gate reproduces M1 and M9 independently. | `CONTRIBUTING.md` · `scripts/validate-sanitization.sh` |
| H2 | ~~**Unsourced performance claims used in CV material.**~~ **Resolved.** "reducing OOM incidents by 80%" (8 occurrences) and "15-25% mAP improvement" (5) existed only in `docs/portfolio/` with no derivation anywhere. All 16 rewritten as outcome statements: OOM is recovered rather than fatal; small objects below full-frame detection scale become detectable. The DO-list instruction that told readers to reuse the numbers now says the opposite. | `PORTFOLIO_RESUME_CONTENT.md:36,196,517,538,651` · `PORTFOLIO_IMPLEMENTATION_GUIDE.md:28,110,150,244,245,415,435` |
| H3 | ~~**A cost saving asserted from a model made entirely of placeholders.**~~ **Resolved.** The worksheet is now labelled as a worksheet, the placeholders are named after what they hold, `ROI breakeven` is replaced with a real break-even (`MIGRATION_COST / monthly_saving`, in months), and operations time is called out as the term most likely to decide the answer. The eight downstream "~60%" claims are gone. Original finding: ** The cost analysis reads `Monthly subscription: $X` / `Storage: $Y` / `Server/VM: $Z` / `Ops time: 4 hours × $rate`. Nothing can be computed from it, yet line 14 states "~60% savings after 6 months" as fact, and the delivery report derives it from an equally unsourced "~40% of cloud cost". The claim then propagates to 8 locations including resume bullets. Separately, `ROI breakeven: $ANNUAL_CLOUD / $ANNUAL_SELFHOSTED` is a ratio, not a breakeven — a breakeven is a point in time. | `MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md:14,44-62` · `MLOPS_DELIVERY_REPORT.md:141-142` · `MLOPS_DOCUMENTATION_SUMMARY.md:232,274` · `MLOPS_IMPLEMENTATION_ROADMAP.md:521` · both portfolio docs |
| H4 | ~~**The documentation index names files that do not exist.**~~ **Resolved.** Index regenerated from disk, now 21 entries matching the tree exactly. Original finding: ** 11 of 20 entries are wrong (`09-yolo-training-engine.md` … `19-jupyter-research-workflow.md`); the last never existed in any form. Two real documents — `19-inference-result-synchronization.md` and `20-deployment-cost-strategy.md` — are missing from the index entirely. | `README.md:480-501` |
| H5 | ~~**The repository tree block repeats the same wrong numbering**~~ **Resolved.** Tree regenerated from disk; `public-safety-checklist.md` shown under `.github/`; `scripts/` and the generated assets added. Original finding: ** and places `public-safety-checklist.md` at the root; it lives in `.github/`. | `README.md:441-471,508` |
| H6 | ~~**Multi-GPU is described two incompatible ways.**~~ **Resolved.** Reconciled toward `13-gpu-resource-management.md`, the document that actually specifies the runtime: single-GPU is current, DataParallel is evaluated and unused, DDP is deferred. 12 sites corrected across the README and `02-system-architecture.md`. Original finding: ** README and `02-system-architecture.md` state "Training GPU execution — Implemented / evaluated", "DataParallel support and evaluated DDP patterns". `13-gpu-resource-management.md` states "DataParallel (Current **Single-GPU** Approach)", "Why Single GPU Currently", "Distributed Data Parallel (DDP) — **Deferred to Phase 3**" and "Current: Sequential Training on Same GPU". The front page oversells relative to the document that actually specifies the runtime. | `README.md:70,134,259,297` vs `13-gpu-resource-management.md:120,144,154,376` |
| H7 | ~~**A diagram advertises a job queue the architecture declares absent.**~~ **Resolved.** The two queue lines are replaced by an explicit note that the request is synchronous and stays open for the run, matching every architecture document and the generated `02-training-flow.png`. Original finding: ** `FastAPI->>FastAPI: Queue training job` and `Accept (status=QUEUED)` are shown as current behaviour. Every architecture document states execution is synchronous and no queue exists. (By contrast `15-limitations-and-risks.md:130` shows `QUEUED` under an explicit "Recommended: Async Pattern / # Future approach" heading — that one is correct and is **not** a finding.) | `diagrams/training-flow.mmd:11-12` |

## Medium

| # | Finding | Location |
|---|---|---|
| M1 | **A real absolute path is still published.** `Project Root: /home/user/myprojects/...`. The policy at `17-public-release-sanitization.md:22` forbids exactly this. It survived the `ca58f44..f390374` cleanup, which edited this very file. Also in three archive files. | `MLOPS_QUICK_REFERENCE.md:147` · `.github/archive/{PUBLICATION-READY.md:187, IMPLEMENTATION-COMPLETE.md:320, SANITIZATION_IMPLEMENTATION_GUIDE.md:188}` |
| M2 | ~~**Duplicate numbering.**~~ **Resolved.** 13 documents renumbered so `docs/architecture/` runs `01` to `21` with no collision. The target numbering is the one the README already claimed for 09-18, so this restored the intended order rather than inventing a new one. Original finding: ** Two documents share prefix `08-`, and two ADRs share `ADR-001`. This is the root cause of H4 and H5: everything after `08` is offset by one. | `docs/architecture/08-*` · `adr/ADR-001-*` |
| M3 | ~~**Two accepted ADRs decide the same thing.**~~ **Resolved.** They are complementary, not duplicated: ADR-004 carries the decision, architecture and migration; ADR-007 carries the tool evaluation. The titles hid that. ADR-007 is retitled to name its scope, both carry an explicit `Relationship` line, and the index says which to read first. Original finding: ** `ADR-004` and `ADR-007` both adopt ClearML for experiment tracking; both are `Status: Accepted`; neither supersedes the other. A reader cannot tell which governs. | `adr/ADR-004`, `adr/ADR-007` |
| M4 | ~~**The YOLO version is inconsistent.**~~ **Resolved.** `09-yolo-training-engine.md:9` is the authoritative statement — the engine supports YOLOv8 and YOLOv11 — so generic prose that arbitrarily picked one version now says "YOLO", and the supported-set form `YOLOv8/v11` is used where the versions matter. 12 sites corrected. Original finding: ** `YOLOv8` appears 15 times, `YOLOv11` 6 times, and `environment.example.env` sets `YOLO_VERSION=11`, while the README speaks generically of "YOLO". `MLOPS_QUICK_REFERENCE.md:12` offers "YOLO-v8, v8, v5". | across `docs/`, `diagrams/`, `examples/` |
| M5 | **A dangling reference created by the recent cleanup.** "See docs/adr for detailed decision rationale" — that directory was removed in `f390374`. The path is now `docs/architecture/adr/`. | `PORTFOLIO_RESUME_CONTENT.md:653` |
| M6 | ~~**Seven broken internal links in live documents.**~~ **Resolved.** Eight in total: the five duplicated `docs/` segments and the two ADR sibling paths were repaired during the renumber; `README.md:334` no longer promises a `CASE-STUDY.md` that never existed. The advisory link check now passes. Original finding: ** Five use `./docs/21-synthetic-dataset-generation-pipeline.md` with a duplicated `docs/` segment; two in `ADR-001-path-translation-layer.md` resolve outside the `adr/` directory; `README.md:334` points to `./CASE-STUDY.md`, which has never existed. | `03:519`, `04:613`, `14:533`, `16:434`, `17:533`, `adr/ADR-001-path-translation-layer.md:365-366`, `README.md:334` |
| M7 | ~~27 of 79 archive files are 0 bytes.~~ **Resolved** with C1: the archive is deleted. | `.github/archive/` |
| M8 | ~~**`MLOPS_QUICK_REFERENCE.md` is the least sanitized file in the repository.**~~ **Resolved**, and the same defects were found and fixed in three sibling operations documents: stale `docs/` paths, a storage tree that contradicted `07-shared-storage-and-artifacts.md`, and `:8080` where the rest of the repository uses `:8001` (now 12 consistent references). Original finding: ** Beyond M1 it points at `docs/MLOPS_STATUS_REPORT.md` and `docs/MIGRATION_*` (both moved to `docs/operations/`), documents a `shared_storage/` tree that does not match `07-shared-storage-and-artifacts.md`, and uses `http://fastapi:8080` where every other document uses `:8001`. | `MLOPS_QUICK_REFERENCE.md:12,147,150-154,260-261,281` |
| M9 | ~~**A weak credential in a copyable compose example.**~~ **Resolved**, and it was wider than reported: six sites across two documents, plus RabbitMQ's default `guest:guest`. All now read from the environment, with a note that credentials belong in a git-ignored `.env` or a secret store. Original finding: ** `MONGO_INITDB_ROOT_PASSWORD: clearml_password`. It is clearly a sample, but it is the one place in the repository where a literal password appears instead of a placeholder, and it is in a block a reader may paste. | `adr/ADR-004-clearml-experiment-tracking.md:375` |
| M10 | ~~**`docs/README.md` is stale.**~~ **Resolved.** Counts, groupings and the `operations/` description corrected against disk. Original finding: ** Claims "20 documents" (there are 21), describes `operations/` as "(future)" and "(emerging)" when it holds seven documents, and its "13-20" grouping no longer matches the subjects at those numbers. | `docs/README.md:9,18,32,39` |

## Low

| # | Finding |
|---|---|
| L1 | ~~Roughly 45 broken internal links inside `.github/archive/`.~~ **Resolved** with C1: the archive is deleted. |
| L2 | ~~Concrete ports and hostnames mutually inconsistent.~~ **Resolved** with M8: the AI service is `:8001` in all 12 references. The remaining ports (`8008` for ClearML, `8000` for Django, `9200` for Elasticsearch) are that software's documented defaults. |
| L3 | ~~`deep_learning/deep_learning/` duplicated route.~~ **Closed, no action.** After the C2 purge removed the institution prefix, `deep_learning` is an ordinary Django app name with nothing distinguishing about it. The duplicated route is documented as a known bug, which is honest documentation worth keeping; genericizing it to `<app>/<app>` would cost clarity and buy nothing. |
| L4 | ~~Dangling "Engineering Case Study" section.~~ **Resolved** with M6: replaced by a question-to-document table pointing at the eight documents that carry the reasoning. |
| L5 | ~~Author-facing template residue.~~ **Resolved** during the renumber in step 3, replaced by a statement that the numbering is the reading order and that gaps and duplicates are treated as defects. |
| L6 | ~~**The licence does not fit the artefact.**~~ **Resolved.** Split in two: CC BY 4.0 (`LICENSE-DOCS`) for the prose, diagrams and generated images; MIT (`LICENSE`) for the scripts, which are now real executable content. The README states which covers what and invites reuse of the diagrams under attribution. Original finding: ** `LICENSE` is MIT — a software licence — for a repository that is 128 Markdown files, 8 generated images and no application code. For prose and diagrams the conventional choice is CC BY 4.0. This matters now that the images are being embedded in a separate portfolio project: MIT's terms are written around "the Software" and its attribution requirement sits oddly on an image tag. |
| L7 | ~~`README.md` opens with 50 lines of badges and buries its argument.~~ **Resolved by reordering rather than cutting.** The file still runs long, but a reviewer now meets, in order: a one-line scope disclaimer, the problem in two sentences, the system diagram, the three things the repository actually argues, and a "start here" table routed by how much time the reader has. The badge wall moved down beside the technology table, where it belongs. |

## Verified clean

- **Credentials**: every occurrence is a placeholder (`PLACEHOLDER_*`, `[..._PLACEHOLDER]`,
  `NEVER_COMMIT`). The `clearml-xxxxxxxxxxxxx` in `CONTRIBUTING.md:176` and
  `PASSWORD_PLACEHOLDER` in `06-docker-runtime-architecture.md` are policy examples, which is
  their intended use. The single exception is M9.
- **Network identifiers**: only `0.0.0.0`, `127.0.0.1`, `localhost` and container service names.
  The two IPs in `17-public-release-sanitization.md:22` are the policy quoting its own
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

1. ~~**H1**~~ — **done.** `scripts/validate-sanitization.sh` implements the gate; `CONTRIBUTING.md`
   documents it. Running it now reports **2 blocking failures — M1 and M9** — which is the gate
   working, not a regression. Those are steps 5 and 7 below and are one line each.
2. ~~**H2, H3**~~ — **done.** 16 performance claims rewritten as outcomes, 8 cost claims replaced
   by a break-even method, the DO-list instruction inverted, the maturity self-assessment labelled.
3. ~~**H4, H5, M2, M10**~~ — **done.** 13 documents renumbered to `01`-`21`, 41 inbound references
   rewritten, both indexes regenerated from disk. **M6 and L4 fell out with it**: all three advisory
   checks now pass. `.github/archive/` was deliberately left untouched as a historical record.
4. ~~**H6, H7, M4**~~ — **done.** Multi-GPU wording reconciled toward the runtime document, the
   queue removed from `training-flow.mmd`, and model naming normalized against the authoritative
   supported-versions statement.
5. ~~**M1**~~ — **partially done.** The live document is sanitized
   (`MLOPS_QUICK_REFERENCE.md:147` now reads `<REPOSITORY_ROOT>/`). Four archive occurrences remain
   and are subsumed by the C1 decision below.

   **C1 and C2 now outrank everything left on this list.** C1 is fixable at `HEAD`: delete
   `.github/archive/`, or sanitize the mapping tables inside it. The archive is 79 files of
   superseded process notes, 27 of them empty and roughly 45 carrying broken links; it serves no
   reader of this repository. C2 is only fixable by rewriting history and force-pushing, which
   breaks every existing clone. Both are decisions for the repository owner, not defaults.
6. **M5, M6** — repair the eight broken links.
7. ~~**M3, M9, M8**~~ — **done.** The gate now reports no leaks and no advisory warnings.
8. ~~**L1-L7**~~ — **done.** L1 and L2 closed with earlier steps, L5 during the renumber, L3 closed
   as no-action with the reasoning recorded.

---

## Closing state

All 2 critical, 7 high, 10 medium and 7 low findings are closed. `./scripts/validate-sanitization.sh`
passes every blocking and advisory check.

Two things this audit got wrong, both recorded above rather than quietly amended:

- The original verdict said no critical leak blocked publication. It was reached by grepping for
  leak patterns, and the worst finding — C1, a mapping table that made the whole sanitization
  reversible — is not a pattern. Process documents have to be read.
- The report itself then reproduced that mapping in full while describing the finding, and the
  commit message describing C1 did the same. Both were redacted in the C2 rewrite. A document may
  record that a substitution happened; never what it was.

The residual exposure noted under C2 is outside this repository's control and is the one open
item: old objects stay reachable by direct SHA until GitHub garbage-collects them.
