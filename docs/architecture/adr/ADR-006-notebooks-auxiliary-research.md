# ADR-006: Use Notebooks as Auxiliary Research Workflow, Not Production Path

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Temptation
Jupyter notebooks are fantastic for research:
- Interactive experimentation
- Rapid iteration
- Visual inspection of outputs
- Easy to share results

### The Reality Check
Notebooks break at scale:
- **Not concurrent**: One person, one kernel, one request at a time
- **Not reproducible**: "I ran it 3 times and got different results"
- **Not auditable**: No history of who ran what when
- **Not accessible**: Can't submit requests through a notebook UI
- **Not reliable**: Kernel crashes lose all state
- **Not version-controlled**: .ipynb is JSON nightmare for git

### The Hybrid Question
Can notebooks be both research AND production tool?

**Answer**: No. They're excellent at one, terrible at the other. Pick one.

---

## Decision

**Notebooks are AUXILIARY research workflow, NOT production execution path**

Clear role separation:

```
PRODUCTION PATH (what users see):
Django Web → FastAPI → GPU → Results

RESEARCH PATH (for experimentation):
Notebook → Manual exploration → Insights → Code into production path

┌─────────────────────────────────────┐
│  Notebook (Researcher playing)      │
│  - Test new ideas                   │
│  - Explore datasets                 │
│  - Prototype algorithms             │
│  - Generate figures for paper       │
│  - NOT running user training jobs   │
└─────────────────────────────────────┘
          ↓ (insights)
┌─────────────────────────────────────┐
│  Production System                  │
│  (Django + FastAPI + GPU)           │
│  - Handles user requests            │
│  - Runs reproducible training       │
│  - Tracks experiments               │
│  - Provides UI/API                  │
└─────────────────────────────────────┘
```

---

## What Notebooks Can Do

✅ **Research**
- Explore new model architectures
- Test dataset preprocessing
- Visualize model predictions
- Generate analysis plots

✅ **Prototyping**
- Try new YOLO versions
- Test hyperparameters
- Profile performance
- Debug training failures

✅ **Knowledge Sharing**
- Document findings
- Create tutorials
- Share with team
- Archive historical explorations

---

## What Notebooks CANNOT Do

❌ **Production Training Jobs**
- Not submitted through Django/FastAPI
- Not tracked in experiment registry
- Not auditable or reproducible
- Not concurrent with other jobs

❌ **User-Facing Inference**
- Can't serve 100s of concurrent users
- Can't guarantee response time
- Can't scale horizontally

❌ **Real-Time Monitoring**
- Can't alert when things fail
- Can't recover from errors
- Can't be 24/7 available

---

## Consequences

### Benefits

✅ **Clear Boundaries**
- Researchers know what's safe (notebooks for exploration)
- Production code protected (can't accidentally run notebook in production)
- Prevents "runs in notebook" → "fails in production" surprises

✅ **Production Reliability**
- Production system not contaminated with research code
- No stray notebooks crashing production
- Clear responsibility (notebooks are developer tools, not infrastructure)

✅ **Reproducibility**
- Production training uses repeatable path (Django → FastAPI → GPU)
- Experiments tracked in ClearML
- Notebooks are documentation, not mechanism

✅ **Scalability Clarity**
- Notebooks scale to 1-2 researchers
- Production scales to many users
- This distinction prevents over-engineering

### Drawbacks

❌ **Friction for Researchers**
- Can't just run training in notebook
- Have to go through Django/FastAPI
- More steps to validate new idea

❌ **Duplicate Code**
- Preprocessing logic in both notebook and FastAPI
- Risk of divergence
- Requires discipline to keep in sync

❌ **Learning Curve**
- New researchers must learn Django + FastAPI
- Not as approachable as single notebook
- More onboarding effort

---

## Alternatives Considered

### Alternative 1: Notebooks as Primary Path

**Approach**: Researchers submit training jobs through Jupyter notebooks

**Why not chosen**:
- Doesn't scale to multiple users
- Kernel crashes lose state
- No experiment tracking (manual logging)
- Can't serve UI to non-technical users
- Defeats purpose of having Django/FastAPI

### Alternative 2: Papermill for Notebook Automation

**Approach**: Use Papermill to parameterize and execute notebooks

**Why not chosen**:
- Adds complexity (Papermill execution)
- Still doesn't solve scalability
- Notebooks not designed for production parametrization
- Better to have purpose-built FastAPI service

### Alternative 3: Share Code Between Notebook and FastAPI

**Approach**: Import common modules (preprocessing, model loading) in both

**Why not chosen**:
- Better than duplication
- But still doesn't change fundamental limitation: notebooks can't be production
- Can do this AND follow this ADR (shared utils module)

---

## Recommended Pattern

**For shared code between research and production**:

```
project/
├── production/
│   ├── django/           ← Production web layer
│   └── fastapi/          ← Production GPU layer
│
├── research/
│   └── notebooks/        ← Researcher explorations
│       └── experiment_001.ipynb
│
└── shared/               ← Code used by both
    ├── preprocessing.py
    ├── model_loading.py
    └── utils.py
```

Both production code and research notebooks import from `shared/`.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Researcher runs training in notebook anyway | High | Medium | Clear documentation + team training |
| Code divergence between notebook and FastAPI | Medium | Low | Shared module strategy; code reviews |
| Productivity hit for researchers | Medium | Low | Good documentation; pre-built templates |

---

## Governance

**What Goes in Notebooks?**
- ✅ Exploratory data analysis
- ✅ Model prototyping
- ✅ Visualization and analysis
- ✅ Algorithm research
- ❌ Production training paths
- ❌ User-facing services

**Enforcement**:
- Production code review checks for notebooks in production paths
- Documentation makes policy clear
- Team culture emphasizes "notebooks for research"

---

## Future Evolution

### Phase 2: Notebook Service
- Could add JupyterHub for team notebook server
- Still for research, not production
- Researchers don't run training from notebooks; they submit via Django

### Phase 3: Experiment Hub
- Web UI for browsing all experiments (from ClearML)
- Researchers submit explorations through UI
- Results flow back through notebook for visualization

---

## Public-Safe Note

This ADR describes organizational policy around Jupyter notebooks vs. production systems. The pattern of separating research tools from production infrastructure is standard in ML teams. This ADR contains no proprietary details.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-001**: Separation of web and compute that makes production path clear
- **ADR-003**: FastAPI as the production inference path
