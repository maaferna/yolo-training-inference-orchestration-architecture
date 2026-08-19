# ADR-007: Tracking Tool Evaluation — ClearML over MLflow and Weights & Biases

**Status**: Accepted — supporting evaluation for ADR-004
**Date**: June 2026
**Public-Safe**: Yes
**Relationship**: This ADR records *why* ClearML was chosen: the tool comparison, the
reproducibility workflow it enables and the governance it does not provide. The decision itself,
its integration architecture and the migration strategy are in
[ADR-004](./ADR-004-clearml-experiment-tracking.md). Read ADR-004 first; read this one when the
question is "why not MLflow or Weights & Biases?".

---

## Context

### The Problem: "What Trained the Model?"

After 3 months of training experiments:
- Which hyperparameters gave the best accuracy?
- Did we use augmentation v1 or v2?
- What GPU did experiment_42 run on?
- Can we reproduce the results from last month?

Without tracking:
- ❌ Notebooks with scattered outputs
- ❌ Model files named `model_final_v2_actually_final.pth`
- ❌ Lost training logs
- ❌ No reproducibility

### The ML Ops Reality

Modern ML requires:
1. **Experiment Tracking**: Log parameters, metrics, artifacts
2. **Reproducibility**: Rebuild exact conditions
3. **Comparison**: Which experiment was better?
4. **Governance**: What trained production model?
5. **Automation**: Submit experiments from code, not manually

### Why Not DIY?

**Option**: Build custom tracking (database + API)

**Problems**:
- Reinventing wheel (others solved this)
- Maintenance burden
- Missing features (hyperparameter sweep, nested runs, etc.)
- No UI/visualization out of box

**Better**: Use proven tool, focus on orchestration

---

## Decision

**Use ClearML for experiment tracking, hyperparameter sweep, and model registry**

```
┌─────────────────────────────────────────────────────────┐
│              FastAPI GPU Service                        │
│  (runs training job in worker)                          │
└──────────────────┬──────────────────────────────────────┘
                   │ logs metrics/params/artifacts
                   ↓
         ┌─────────────────────┐
         │     ClearML         │
         │  - Experiment DB    │
         │  - Model Registry   │
         │  - Hyperparameter   │
         │    Sweeps           │
         │  - Web UI           │
         └─────────────────────┘
                   ↑
                   │ researcher queries
                   │
         ┌─────────────────────┐
         │   Jupyter Notebook  │
         │  (analysis)         │
         └─────────────────────┘
```

---

## Why ClearML?

### Features

✅ **Task Tracking**
- Auto-capture: Git commit, environment, installed packages
- Manual log: Hyperparameters, metrics, artifacts
- Web UI shows all runs with filtering/search

✅ **Hyperparameter Optimization**
- Built-in sweeps (grid, random, Bayesian)
- Automatic parallel execution
- Results aggregation

✅ **Model Registry**
- Version models with metadata
- Link to experiment that created it
- Track which model is in production

✅ **Reproducibility**
- Restore experiment: environment, code, hyperparameters
- Rerun with exact conditions
- Compare reproducibility reports

✅ **Team Features**
- Multi-user projects
- Shared results dashboard
- Integration with git

### Why Not Alternatives?

| Tool | Pros | Cons | Why ClearML Wins |
|------|------|------|-----------------|
| **MLflow** | Popular, simple | No hyperparameter optimization, limited model registry | ClearML's sweep + registry better for our needs |
| **Weights & Biases** | Great dashboard, mature | Proprietary, SaaS-only, cost | ClearML has on-prem option, lower overhead |
| **Neptune** | Good UI, integrations | Limited free tier | ClearML free tier sufficient |
| **Custom DB** | Full control | Maintenance, reinventing wheel | Not worth the cost |

---

## Architecture: ClearML Integration

### Where ClearML Fits

```
User submits training request via Django
        ↓
FastAPI receives request
        ↓
Create ClearML Task (experiment created)
        ↓
Initialize training script with ClearML logger
        ↓
Training loop:
  - Log metrics (loss, accuracy) → ClearML
  - Log artifacts (checkpoints) → ClearML
  - Log images (sample predictions) → ClearML
        ↓
Training complete
        ↓
Register final model in ClearML Model Registry
        ↓
FastAPI returns model metadata + ClearML task ID
        ↓
User can view full experiment in ClearML Web UI
```

### Code Pattern

**FastAPI service**:
```python
from clearml import Task

@app.post("/train")
async def submit_training(config: TrainingConfig):
    # Create ClearML task (experiment)
    task = Task.init(
        project_name="yolo-training",
        task_name=f"training_{config.model}_{datetime.now().isoformat()}"
    )
    
    # Connect hyperparameters
    task.connect_configuration(vars(config))
    
    # Spawn worker (could be Celery, K8s job, etc.)
    worker_id = spawn_training_worker(config, task_id=task.id)
    
    return {
        "worker_id": worker_id,
        "clearml_task_id": task.id,
        "clearml_ui_url": f"https://clearml-ui/tasks/{task.id}"
    }
```

**Training script** (runs in worker):
```python
from clearml import Task
import yolo

# Connect to ClearML task
task = Task.current_task()

# Log metrics during training
for epoch in range(num_epochs):
    loss = train_epoch()
    task.logger.report_scalar(
        title="training",
        series="loss",
        value=loss,
        iteration=epoch
    )

# Log final model
model.save("final_model.pth")
task.upload_artifact("model", "final_model.pth")

# Register in model registry
model_task = Task.current_task()
model_name = f"yolo_model_{datetime.now().isoformat()}"
Model(name=model_name, task=model_task).upload("final_model.pth")
```

---

## Deployment Options

### Option 1: ClearML Server (Recommended)
- **Setup**: Deploy ClearML Server + Web UI + Database
- **Where**: Same infrastructure as Django/FastAPI
- **Benefit**: On-premises, no external dependencies, full control
- **Cost**: Open-source (free) + hosting costs
- **Recommendation**: For production deployments

### Option 2: ClearML Cloud
- **Setup**: Use managed ClearML cloud
- **Where**: SaaS hosted by ClearML
- **Benefit**: No ops burden, instant setup
- **Cost**: Free tier or paid plans
- **Recommendation**: For prototyping/research phase

### Option 3: Hybrid
- **Setup**: ClearML Cloud for research, ClearML Server for production
- **When**: Researchers use cloud freely, production tracked on-prem
- **Benefit**: Low overhead development, secured production
- **Recommendation**: If tight ops budget initially

**For this architecture: Start Option 2 (Cloud), migrate to Option 1 (Server) at scale**

---

## Integration Points

### 1. Training Submission
```
Django Web UI → Request training
            ↓
FastAPI creates ClearML Task
            ↓
Task ID returned to user
            ↓
User can monitor in ClearML UI
```

### 2. Hyperparameter Sweeps
```
Researcher defines sweep config
            ↓
ClearML creates multiple child tasks
            ↓
Each task runs with different hyperparams
            ↓
ClearML aggregates results
            ↓
Best config recommended
            ↓
Researcher can clone best task to production
```

### 3. Model Registry → Production
```
ClearML registers trained model
            ↓
Model metadata stored (accuracy, F1, etc.)
            ↓
Production system queries model registry
            ↓
"Give me best model from last week"
            ↓
ClearML returns model file + metadata
            ↓
FastAPI inference loads it
```

---

## What Gets Tracked

### Automatically (By ClearML)
- ✅ Git commit hash
- ✅ Python version
- ✅ Package versions (installed packages)
- ✅ Hostname / GPU info
- ✅ System resources (CPU, memory, disk)
- ✅ Script name and path
- ✅ Working directory

### Manually Logged (By Training Script)
- ✅ Hyperparameters (learning rate, batch size, etc.)
- ✅ Metrics (loss, accuracy, F1 per epoch)
- ✅ Artifacts (model checkpoints, weights)
- ✅ Images (sample predictions, confusion matrices)
- ✅ Text (training logs, debug output)
- ✅ Tables (class-wise metrics)

### Why This Matters
If training fails in production, you can:
1. Find task in ClearML UI
2. See exact git commit, packages, hyperparameters
3. Clone the task
4. Reproduce locally
5. Debug and re-run

---

## Reproducibility Workflow

```
Researcher: "Let me reproduce experiment_42"
                    ↓
1. Find experiment_42 in ClearML UI
                    ↓
2. Click "Clone Task"
                    ↓
3. ClearML captures:
   - Exact git commit
   - Exact hyperparameters
   - Exact packages + versions
   - Same seed
                    ↓
4. Researcher submits cloned task
                    ↓
5. Training runs with identical conditions
                    ↓
6. Results should match (or be close)
                    ↓
If divergence: Investigate
- Different GPU type?
- Different CUDA version?
- Non-deterministic op (e.g., augmentation)?
```

---

## Governance

### What Must Be Logged

**Every training task MUST log**:
- [ ] Model architecture (name, version)
- [ ] Training hyperparameters
- [ ] Dataset version/split
- [ ] Validation metrics
- [ ] Final model artifact

**Recommendation**: Enforce via code review + FastAPI validation

### What Goes in Model Registry

**Only production-candidate models**:
- Accuracy > threshold
- Tested on validation set
- Linked to experiment
- Metadata complete

### Access Control
- Researchers: Full access (all tasks)
- Team leads: Full access (review/approve)
- Automated systems: Read-only (fetch best model)

---

## Consequences

### Benefits

✅ **Reproducibility**
- Exact conditions captured
- Can re-run experiment months later
- Debug production models

✅ **Collaboration**
- Team sees all experiments
- Share best results
- Learn from others' trials

✅ **Governance**
- Audit trail: who ran what when
- Model provenance: which experiment created this model?
- Compliance-ready

✅ **Efficiency**
- Hyperparameter sweeps automated
- No manual result aggregation
- Dashboard replaces spreadsheets

✅ **Production Safety**
- Know exactly what trained production model
- Quick rollback (use previous model)
- Alerts if training diverges

### Drawbacks

❌ **Another System**
- ClearML server to deploy/maintain
- Researchers must learn new UI
- API integration needed

❌ **Data Storage**
- Artifacts stored somewhere (disk, S3, etc.)
- Can accumulate (checkpoints from every epoch)
- Need cleanup strategy

❌ **Learning Curve**
- New tool for team
- Not as simple as print logging
- Onboarding time

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ClearML server down → Can't log experiments | Low | High | Deploy high-availability; fallback to offline mode |
| Artifact storage fills up | Medium | Medium | Implement retention policy (keep last 3 checkpoints) |
| Researchers skip logging to go faster | High | Medium | Code review enforcement; make logging trivial |
| Integration complexity | Medium | Low | Well-documented patterns in codebase |

---

## Alternatives Considered

### Alternative 1: MLflow
**Approach**: Use MLflow for experiment tracking

**Why not chosen**:
- No built-in hyperparameter sweep (need Optuna separately)
- Limited model registry (basic versioning)
- More manual work to wire up

### Alternative 2: Weights & Biases
**Approach**: Use W&B for everything

**Why not chosen**:
- SaaS-only (can't run on-prem if needed)
- Costs scale with team size
- Overkill for this use case initially
- Harder to migrate off if needed

### Alternative 3: Custom Tracking (Database + API)
**Approach**: Build in-house experiment tracker

**Why not chosen**:
- Months of development
- Maintenance burden
- Missing features (UI, sweeps, model registry)
- Reinventing solution that exists

---

## Future Evolution

### Phase 1: Basic Tracking (Now)
- Manual logging in training scripts
- ClearML Server or Cloud
- Basic model registry

### Phase 2: Automated Sweeps
- Hyperparameter optimization pipelines
- Automatic Bayesian search
- Results ranking

### Phase 3: MLOps Platform
- ClearML integration with deployment pipeline
- Automated A/B testing
- Production monitoring

### Phase 4: Advanced Features
- Auto-scaling workers based on queue
- Custom metrics and KPIs
- Integration with monitoring/alerting

---

## Migration Strategy

### Phase 0: Dev Environment (Week 1)
- Spin up ClearML Cloud account
- Create sample training script with logging
- Test capture/replay

### Phase 1: Research Phase (Week 2-3)
- Train researchers on ClearML UI
- Log all new experiments
- Verify reproducibility

### Phase 2: Production Integration (Week 4+)
- FastAPI creates ClearML tasks
- Model registry integration
- Production queries model registry

---

## Public-Safe Note

This ADR describes using ClearML, a standard open-source MLOps tool used widely in industry. The architectural patterns (experiment tracking, model registry, reproducibility) are standard ML practices. No proprietary details included.

**Safe for public portfolio distribution**: ✅ Yes

---

## Current Implementation Status

**Timeline**: June 2026  
**Current Phase**: ClearML Cloud (SaaS)  
**Next Phase**: ClearML Self-Hosted (Q3 2026)  

See MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md for detailed migration plan.

---

## Related ADRs

- **ADR-003**: FastAPI as orchestration point (ClearML integrates here)
- **ADR-004**: ClearML architecture with local artifacts as source of truth
- **ADR-006**: Notebooks import results from ClearML for analysis
- **ADR-008** (future): Model registry and production model selection
- **ADR-009** (future): Data versioning integration with ClearML

## Migration Documentation

- **ADR-004**: Detailed self-hosted migration strategy included
- **MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md**: Step-by-step 4-week plan
- **MLOPS_STATUS_REPORT.md**: Current project status and roadmap
