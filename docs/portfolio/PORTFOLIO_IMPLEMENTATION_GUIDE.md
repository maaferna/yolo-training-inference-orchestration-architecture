# Portfolio & Resume Implementation Guide

> **This document is portfolio-safe**: all guidance uses publicly shareable language. No real
> credentials, institutions, projects, dates or measured results are referenced. Safe to follow
> in hiring, interviews and professional networking.

**How to use the content in `PORTFOLIO_RESUME_CONTENT.md` across platforms**

The material is built on **limitation → resolution** pairs: what the initial iteration wrote
down as a limitation (`docs/architecture/15`, `16`) and what a later revision did about it
(`docs/evolution/`, ADR-009 to ADR-013). Keep that shape wherever the content goes; it is the
strongest and most verifiable story the repository has.

One scope statement to carry into every platform: in the later revision, training runs outside
the platform and enters through a fingerprinted import, and the revision's GPU path was not
validated. The initial iteration is the one that orchestrated training on the GPU, with
DataParallel across two GPUs as the training runtime and single-GPU as the fallback.

---

## Quick Start: Pick Your Scenario

### Scenario 1: Resume / CV submission

**Use**: resume bullets from `PORTFOLIO_RESUME_CONTENT.md`, sections 1–3
**Approach**: two or three bullets from the relevant profile (ML / Backend / CV)
**Format**: keep the limitation → resolution shape; tailor to the job description

**Example for an ML Engineer position:**
```
PROFESSIONAL EXPERIENCE

Machine Learning Engineer | Company | <dates>
• Designed a multi-seed YOLO training strategy with validation-based
  selection and CUDA cleanup between seeds; later specified that
  selection is a registry decision shown to a person, not a training
  side effect (ADR-010)

• Designed OOM recovery for sequential training runs: progressive
  resource scaling (batch size, then image size) and fallback
  validation, so an OOM degrades the run instead of ending it

• Designed experiment tracking with local artifacts and run manifests
  as the source of truth; evaluated the initial tool's default data
  egress, documented its withdrawal and specified a self-hosted
  tracking-only replacement, decided and not deployed (ADR-012)
```

---

### Scenario 2: LinkedIn profile update

**Use**: section 4 (LinkedIn description) and section 6 (project card)
**Approach**: post as a Featured project
**Format**: narrative with the initial iteration, the revision and the scope statement

**Steps**:
1. Profile → Featured → Add → Project
2. Title: "YOLO Training & Inference Orchestration Architecture"
3. Paste section 4
4. Link the GitHub repository and one rendered diagram from `assets/diagrams/`
5. Do not add numbers the repository does not state

---

### Scenario 3: Portfolio website project card

**Use**: section 6
**Approach**: a standalone project page built around the limitation → resolution table
**Format**: HTML or Markdown

**Example structure**:
```
/portfolio/projects/yolo-orchestration/
├── index.html (or index.md)
├── images/
│   ├── 01-system-architecture.png     (from assets/diagrams/)
│   ├── 02-training-flow.png
│   ├── 04-sahi-inference.png
│   └── 07-evolution-roadmap.png
└── README.md
```

---

### Scenario 4: GitHub repository

**Use**: section 5
**Approach**: About section and README top
**Format**: Markdown

**Steps**:
1. Settings → About: paste the short description
2. Topics: `architecture`, `mlops`, `computer-vision`, `yolo`, `sahi`, `fastapi`, `django`,
   `cuda`, `docker-compose`, `adr`
3. Keep the README's "What this repository argues" section as the entry point
4. Badges: "Documentation only" and "Public-safe" — never "production ready"

---

### Scenario 5: Cold outreach / networking email

**Use**: section 4 condensed plus one limitation → resolution pair
**Format**: short paragraph with a link

**Template**:
```
Subject: Architecture of an internal AI vision platform — with its
         limitations and what became of them

Hi [Name],

I designed and documented the architecture of an internal computer-
vision platform that separates web orchestration from GPU-bound YOLO
work. What I think makes it worth a look: the initial iteration states
its limitations and the triggers that would justify change, and a
later revision records what happened when they fired.

One example: request timeouts arrived, and the answer was submit/poll
on in-process pools with durable job records — not a queue. Another:
the race on the file-based model reference was closed by a
transactional registry with human promotion.

Repository:
github.com/maaferna/yolo-training-inference-orchestration-architecture

I would be glad to discuss how these patterns apply to [context].

Best,
[Your Name]
```

---

### Scenario 6: Technical interview preparation

**Use**: all bullets plus `docs/architecture/18-technical-responsibilities.md`
**Approach**: talking points on decisions, triggers and outcomes
**Format**: conversational, each answer ending on a record (an ADR or an evolution document)

**Response framework**:
```
"Walk me through how you designed this system"

1. Problem: GPU-bound work inside a web application takes it down
2. Decision: two services — Django for metadata and visualisation,
   FastAPI owning the GPU runtime — HTTP between them, shared
   artifact storage
3. Depth: multi-seed training with CUDA cleanup; SAHI tiling; local
   artifacts as the source of truth
4. Limitations written down: request open for the whole job, a
   file-based model reference with a race, path translation, no tests
5. Outcome: when timeouts arrived the answer was submit/poll with job
   records, not a queue; the race became a transactional registry;
   path translation became a same-path invariant; contracts and a
   test suite followed. No broker, no Kubernetes.

"What would you do differently?"

"Two things the revision already did: withdraw a tracking tool whose
default sent data off-premises, and take model promotion out of the
training loop. One thing still open: admission control on the device,
which is the next trigger."
```

---

## Platform-Specific Implementation

### LinkedIn (detailed)

```
STEP 1: Headline
Add "ML Systems Architect" or "AI Platform Engineer" if relevant

STEP 2: Featured project
Title: YOLO Training & Inference Orchestration Architecture
Content: section 4
Link: github.com/maaferna/yolo-training-inference-orchestration-architecture
Image: assets/diagrams/01-system-architecture.png

STEP 3: Experience
Bullets from sections 1–3, design verbs only

STEP 4: Skills
System architecture; GPU runtime (CUDA); service contracts; MLOps;
Python (PyTorch, FastAPI, Django); testing without a GPU

STEP 5: About
"I design and document architectures for AI vision platforms, and I
write down their limitations before their features. See the featured
project for one whose limitations were later resolved on record."
```

### GitHub repository

```
STEP 1: About
Short description from section 5

STEP 2: Topics
architecture, mlops, computer-vision, yolo, sahi, fastapi, django,
cuda, docker-compose, adr

STEP 3: Badges
Documentation only · Public-safe · Anonymized

STEP 4: README entry points
- What this repository argues
- docs/architecture/15-limitations-and-risks.md
- docs/evolution/00-what-came-next.md
- docs/architecture/adr/

STEP 5: Never add
Production-ready badges, self-assessed maturity levels, dates
```

### Portfolio website

```
STEP 1: Page
yoursite.com/projects/yolo-orchestration

STEP 2: Sections
├── Title and one-paragraph overview
├── Architecture diagram
├── Limitation → resolution table (section 6)
├── Scope statement (training outside the platform; GPU path not
│   validated in the revision)
├── Technical highlights
├── Technologies
└── Links: repository, docs/architecture/adr/, docs/evolution/

STEP 3: Visuals (from assets/diagrams/ and assets/poster/)
01 system architecture · 02 training flow · 04 SAHI · 07 roadmap

STEP 4: Outcomes, not percentages
- OOM recovered rather than fatal
- small objects detectable that full-frame inference misses
- timeouts answered without a broker
- lineage questions answerable from the registry
```

---

## Tailoring by Role

### Machine Learning Engineer

**Resume**: bullets 1–3 of section 1
**Emphasize**: reproducibility; why selection left the training loop; why the tracker was
withdrawn and what replaced it as the source of truth
**Interview**: multi-seed strategy; CUDA cleanup and OOM recovery; tracking without egress
**Avoid**: deployment detail; claiming the revision trained on the GPU

### Backend / Platform Engineer

**Resume**: bullets 1, 3 and 5 of section 2
**Emphasize**: answering a trigger with the smallest change; contracts; tests without a GPU
**Interview**: why two services; submit/poll instead of a queue; error envelope, manifest,
service tokens, same-path invariant; the evolution ledger
**Avoid**: deep CV detail

### Computer Vision Engineer

**Resume**: bullets 1, 4 and 5 of section 3
**Emphasize**: small objects; physical quantities from detections; what is not validated
**Interview**: SAHI trade-offs; metrology stages and gates; GeoJSON in the console
**Avoid**: infrastructure detail

### AI / MLOps Lead

**Resume**: the limitation → resolution table of section 6 as the spine
**Emphasize**: restraint that can be audited; four decisions reversed with superseding records
**Interview**: the whole arc from `16` to `docs/evolution/07`

---

## Common Interview Questions & Responses

### "Walk me through this architecture"

```
"An internal computer-vision platform: a small group of operators
submits YOLO training and high-resolution inference jobs. The design
problem is not scale; it is keeping GPU-bound work from taking down a
web application and keeping its artifacts traceable.

Django owns metadata, configuration and visualisation. FastAPI owns
the GPU runtime. HTTP between them, shared artifact storage as the
integration mechanism, a relational database only on the web side.

The initial iteration stated its limitations: the request stays open
for the whole job, the best model is a file with a race condition,
paths are translated across containers, nothing is tested. It also
named the trigger for each.

When the triggers fired, the revision answered each one with the
smallest change that closed it: job records and polling, not a queue;
a transactional registry, not a lock; one mount path, not a
translation layer; a mock/real runtime seam and a CPU test suite, not
a GPU in CI. A queue, a worker pool and Kubernetes were never
triggered, and that is on record."
```

### "How do you approach scalability?"

```
"By trigger, not by calendar. The initial iteration ran synchronously
with DataParallel on two GPUs, which fit a predictable internal workload. The
roadmap named what would justify each addition: job status and
polling once operators need progress; a controlled GPU worker once
jobs compete for the device; a broker only once retry, cancellation
and multi-worker dispatch are real requirements.

What actually happened: timeouts fired and polling with durable job
records was enough. Contention on the device is the open trigger; the
design recommendation is a single admission lane. Nothing further was
triggered."
```

### "Why multi-seed training?"

```
"A single run gives one draw from the initialization distribution,
not the distribution. Several seeds give a spread; selection on
aggregated validation metrics is more robust than selection on one
lucky run.

The runtime cost is CUDA hygiene: seeds run sequentially, so cache
release and memory-stat reset between them keep each seed comparable.

The later decision was to take selection out of the loop: the score
is shown to a person and promotion is a registry transaction with an
event, not a side effect of training (ADR-010)."
```

### "How do you handle GPU memory issues?"

```
"An OOM should degrade the run, not end it. The documented pattern is
progressive resource scaling — reduce batch size first, then image
size — with fallback validation when the training call returns no
result, and explicit cleanup between seeds so a previous run's state
does not cause the next one's OOM.

To be precise about scope: those are runtime facts of the initial
iteration, which orchestrated training on the GPU. The later revision
did not validate its GPU path; its tests run on CPU with a mock
runtime."
```

### "Why SAHI for inference?"

```
"Small objects in a large image fall below the detector's effective
resolution once the image is resized to the model's input. Tiling
keeps them at a scale the model can see: overlapping tiles, per-tile
detection, reconstruction into image coordinates.

The trade-off is compute: more tiles and more overlap cost more
passes. The strategy is chosen from the expected object size, not
fixed. In the revision, the reconstructed detections feed a metrology
stage that turns boxes into physical size, coverage and density —
documented as not yet validated against ground truth."
```

### "Describe a problem you found and how it was resolved"

```
"The continuous-improvement loop updated a file-based best-model
reference whenever a run beat the baseline. Two concurrent runs could
read the same baseline and the worse one could write last. I
documented the timeline and the mitigation options.

The revision closed it properly: model versions as rows with a
weight fingerprint, promotion and rollback as single transactions
writing an event that names the previous version, the user and a
reason, and a person performing the promotion. The AI service
resolves models only through the exported list, verifying the
fingerprint (ADR-010)."
```

### "What would you change in production?"

```
"Only what a trigger asks for. The open one is admission on the
device: several jobs can be accepted at once and there is no lane
control. Beyond that: make CI blocking, validate the metrology method
against ground truth, deploy the tracking server once training
returns to the platform, and add a request identifier that spans both
services. None of those is a queue or Kubernetes; the ledger in
docs/evolution/07 is explicit about why."
```

---

## Credibility Checklist

Before sharing portfolio content, verify:

- No institution, client, site, person or hardware names
- No private dataset references, weights or measured results
- No credentials, infrastructure identifiers or absolute paths
- No calendar dates, quarters or years; iterations only
- No self-assessed maturity levels; no counts the repository does not state
- Design verbs only: designed, documented, specified, proposed, evaluated
- The initial tracking tool is described as withdrawn, never as current
- No queue, worker pool or Kubernetes claimed; they were not triggered
- The scope statement is present: training outside the platform in the revision; GPU path
  not validated there
- Every claim points at a document: `docs/architecture/`, `docs/architecture/adr/`,
  `docs/evolution/`

---

## Tracking Updates

When the portfolio content changes, note it here by iteration, not by date:

| Revision | Changes | Where used |
|---|---|---|
| Initial | Bullets by profile, LinkedIn, GitHub, project card | All platforms |
| Limitation → resolution rewrite | Content rebuilt on the evolution documents and ADR-009 to ADR-013; tracking tool marked withdrawn; maturity levels, dates and unsourced counts removed | All platforms |

---

## Final Thoughts

This content demonstrates a way of working: state the limitation, name the trigger, answer it
with the smallest change that closes it, and write down the outcome — including what was not
built and what was not validated.

Use it to show:
- system architecture with explicit responsibility boundaries
- decisions with triggers, and a ledger of what those triggers produced
- contracts and tests as the answer to prose and manual checks
- honest scope: what the initial iteration exercised, what the revision moved out

The goal is not to claim more than the repository can evidence, but to show how you think
about systems whose limitations you are willing to write down.

---

**Associated content**: `PORTFOLIO_RESUME_CONTENT.md`
**Status**: public-safe portfolio content
