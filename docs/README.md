# Documentation Directory

Well-organized architecture and operational documentation.

## Structure

```
docs/
├── architecture/          # Core system architecture documentation (21 documents)
│   ├── 01-context-and-problem.md
│   ├── 02-system-architecture.md
│   ├── ... (19 more)
│   └── adr/               # ADR-001..008 (initial iteration), ADR-009..013 (revision)
│
├── evolution/            # A later revision of the same architecture (8 documents)
│   ├── 00-what-came-next.md
│   └── ... (7 more)
│
├── portfolio/            # Portfolio and resume materials
│   ├── PORTFOLIO_IMPLEMENTATION_GUIDE.md
│   └── PORTFOLIO_RESUME_CONTENT.md
│
└── operations/          # Retired operational calendar; README explains where its content went
```

## Quick Start

**For System Architecture Overview:**
- Start with `architecture/01-context-and-problem.md`
- Then read `architecture/02-system-architecture.md`

**For Portfolio Materials:**
- See `portfolio/PORTFOLIO_RESUME_CONTENT.md`
- Implementation guide: `portfolio/PORTFOLIO_IMPLEMENTATION_GUIDE.md`

**For the Evolution Path:**
- Start with `architecture/16-production-evolution-roadmap.md`
- Then `evolution/` for the later revision of the architecture

## Navigation

Architecture files are numbered `01` to `21`; the numbering is the reading order.

- **01-05**: Problem statement, architecture overview, components, flows, API contracts
- **06-08**: Docker runtime, shared storage, dataset configuration
- **09-13**: Training engine, continuous improvement, SAHI inference, experiment tracking, GPU management
- **14-18**: Error handling, limitations, evolution roadmap, sanitization policy, responsibilities
- **19-21**: Result synchronization, deployment cost strategy, synthetic dataset generation

`evolution/` is read after `architecture/`: `00` explains what stayed and what changed, `01-06`
describe the revision by topic, `07` is the ledger of the roadmap. ADRs marked `revision`
supersede or amend the ones marked `initial`; the ADR index says which.

The full index with one-line purposes is in the root `README.md`.

