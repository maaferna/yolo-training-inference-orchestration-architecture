# Documentation Directory

Well-organized architecture and operational documentation.

## Structure

```
docs/
├── architecture/          # Core system architecture documentation (20 documents)
│   ├── 01-context-and-problem.md
│   ├── 02-system-architecture.md
│   ├── ... (18 more)
│
├── portfolio/            # Portfolio and resume materials
│   ├── PORTFOLIO_IMPLEMENTATION_GUIDE.md
│   └── PORTFOLIO_RESUME_CONTENT.md
│
└── operations/          # MLOps status, roadmap, migration, quick reference (7 documents)
```

## Quick Start

**For System Architecture Overview:**
- Start with `architecture/01-context-and-problem.md`
- Then read `architecture/02-system-architecture.md`

**For Portfolio Materials:**
- See `portfolio/PORTFOLIO_RESUME_CONTENT.md`
- Implementation guide: `portfolio/PORTFOLIO_IMPLEMENTATION_GUIDE.md`

**For Operational Details:**
- Start with `operations/MLOPS_STATUS_REPORT.md`
- Then `operations/MLOPS_IMPLEMENTATION_ROADMAP.md`

## Navigation

Architecture files are numbered `01` to `21`; the numbering is the reading order.

- **01-05**: Problem statement, architecture overview, components, flows, API contracts
- **06-08**: Docker runtime, shared storage, dataset configuration
- **09-13**: Training engine, continuous improvement, SAHI inference, experiment tracking, GPU management
- **14-18**: Error handling, limitations, evolution roadmap, sanitization policy, responsibilities
- **19-21**: Result synchronization, deployment cost strategy, synthetic dataset generation

The full index with one-line purposes is in the root `README.md`.

---

Last updated: August 19, 2026
