# ADR-004: Use ClearML for Experiment Tracking with Local Artifacts as Source of Truth

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Problem
We need to track ML experiments for reproducibility and comparison:
- Which models were trained when?
- What hyperparameters were used?
- What were the metrics (mAP, precision, recall)?
- How do different training runs compare?
- Can we recover which data trained a particular model?

### Options Considered
1. **Manual logging** (write metrics to CSV)
2. **MLflow** (open-source ML tracking)
3. **ClearML** (formerly Allegro Trains)
4. **Weights & Biases** (W&B, cloud-based)
5. **Neptune** (cloud-based tracking)
6. **No tracking** (keep metrics only in local logs)

### Key Constraints
- Want experiment tracking, not full MLOps platform
- Need reproducibility within research team
- Cannot rely on external cloud services (data sensitivity)
- Local artifacts (models) must remain authoritative
- Integration with ClearML server (can be self-hosted)

### Current Project Status (June 2026)
- **Current Setup**: ClearML Cloud (SaaS platform account)
- **Stage**: MVP with production-ready MLOps
- **Team Maturity**: Structured experiment tracking in place
- **Next Phase**: Migrate from Cloud to self-hosted for cost optimization and data sovereignty

---

## Decision

**Use ClearML for experiment tracking with local filesystem as source of truth for artifacts**

```
Training Process
    ↓
ClearML Task initialized
    ↓
Training runs, logs metrics → ClearML
    ├── Hyperparameters logged
    ├── Metrics (mAP, precision, recall) logged
    └── Model artifact path stored
    ↓
Best model saved to filesystem
    └── /shared_storage/models/best.pt
    ↓
ClearML logs reference to model path
    └── Task artifact: /shared_storage/models/best.pt
```

**Key design**: ClearML is metadata tracker, not artifact repository
- ClearML logs: "model saved at path X with metrics Y"
- Actual model file: lives in shared filesystem
- Django/researchers: read models from filesystem
- ClearML: provides experiment comparison/visualization

---

## Architecture

### What ClearML Provides
- ✅ Experiment metadata (task name, project, hyperparameters)
- ✅ Metrics logging (mAP50, precision, recall, loss curves)
- ✅ Model artifact registration (path reference + metadata)
- ✅ Task comparison UI (which training run was best?)
- ✅ Execution logs and debug information

### What ClearML Does NOT Provide
- ❌ Data lineage (which datasets trained this model? - not implemented)
- ❌ Hyperparameter inheritance tracking (advanced feature; not used)
- ❌ Model registry (artifacts live on filesystem, not in ClearML)
- ❌ Deployment pipeline (not part of this architecture)

### Why Local Filesystem is Authoritative

1. **Performance**: Model loading doesn't require ClearML server
2. **Reliability**: Models persist even if ClearML is down
3. **Compatibility**: Tools expect filesystem paths (Docker, YOLO CLI)
4. **Cost**: Artifact storage isn't double-counted
5. **Simplicity**: "Source of truth" is one place, not split

---

## Consequences

### Benefits

✅ **Experiment Visibility**
- UI shows all training runs and their metrics
- Easy to compare different hyperparameter choices
- Metrics persist for post-hoc analysis

✅ **Reproducibility**
- Exactly which code version ran? Logged in ClearML
- What seed values were used? Logged
- What was the random state? Logged
- Can recreate experiment conditions

✅ **Debugging**
- Training logs captured in ClearML
- Stack traces accessible for failed runs
- Metrics timeline shows where training degraded

✅ **Team Alignment**
- Researchers see all experiments (not just their own runs)
- Can learn from others' attempts
- Prevents duplicate work

✅ **Lightweight**
- ClearML is just metadata store
- Can be self-hosted (no vendor lock-in)
- Doesn't require restructuring artifact storage

### Drawbacks

❌ **Split Authority**
- Model files in filesystem, metadata in ClearML
- Coordination required (if file deleted, ClearML points to nothing)
- Cleanup complexity (delete from both places)

❌ **Not Full Lineage**
- Can't answer "which dataset trained this model?" automatically
- Data provenance requires manual documentation
- Phase 2 could add data versioning, but not implemented

❌ **ClearML Dependency**
- ClearML server must be running for logging
- If ClearML is down, training continues but doesn't log
- Must maintain ClearML infrastructure

❌ **Artifact Duplication Risk**
- If ClearML accidentally becomes artifact store, creates confusion
- Requires clear documentation (done in this ADR)
- Team discipline needed to maintain the pattern

---

## Alternatives Considered

### Alternative 1: MLflow

**Approach**: Use MLflow for both metrics and artifact storage

**Why not chosen**:
- MLflow also tracks artifacts (would break our "filesystem authoritative" goal)
- Similar complexity to ClearML
- ClearML has better UI for experiment comparison (personal team preference)
- MLflow more common, but ClearML sufficient for MVP

### Alternative 2: Weights & Biases (W&B)

**Approach**: Use cloud-hosted W&B for everything

**Why not chosen**:
- External cloud dependency (data sensitivity concerns)
- Subscription cost for teams
- Data leaves organization
- Not self-hostable
- ClearML works without internet connectivity

### Alternative 3: No Experiment Tracking

**Approach**: Skip structured tracking, use file logs only

**Why not chosen**:
- No UI for experiment comparison
- Metrics scattered in logs (hard to parse)
- No reproducibility mechanism
- Doesn't scale beyond handful of runs
- Loses value of structured experiment management

### Alternative 4: TensorBoard Only

**Approach**: Use TensorBoard for metrics visualization

**Why not chosen**:
- TensorBoard only handles metrics, not hyperparameters
- No experiment comparison features
- No reproducibility metadata
- More manual logging required

---

## Implementation Pattern

```python
from clearml import Task

# Initialize task
task = Task.init(
    project_name="ai_vision_platform",
    task_name=f"training_experiment_{job_id}"
)

# Log hyperparameters
task.connect_configuration(
    config_dict={
        'model': 'yolo_v8',
        'epochs': 100,
        'batch_size': 32,
        'learning_rate': 0.001
    }
)

# Log metrics (during training)
task.get_logger().report_scalar(
    title="mAP",
    series="validation",
    value=0.742,
    iteration=epoch
)

# Log model artifact
task.upload_artifact(
    name="best_model",
    artifact_object="/shared_storage/models/best.pt"
)

# Task completes
task.close()
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ClearML server down | Low | Medium | Training continues; log to local file as fallback |
| Split authority causes confusion | Medium | Low | Clear documentation (this ADR); team training |
| Artifact proliferation | Medium | Low | Implement cleanup policy; disk monitoring |
| ClearML API changes | Low | Low | Version lock ClearML; test regularly |
| Data duplication issues | Low | High | Document sync pattern; automate if needed |

---

## Future Evolution

### Phase 2: Add Data Versioning
- Track dataset versions in ClearML
- Answer "which dataset trained this model?"
- Could integrate with Data Catalyst or similar

### Phase 3: Model Registry
- Promote ClearML to include model registry
- Track model lineage (data → model → deployment)
- Could move artifacts to MinIO/S3

### Phase 4: Full MLOps Integration
- ClearML could orchestrate training (not just track)
- Pipelines defined in ClearML
- Auto-deployment of models (CD/ML)

---

## ClearML Cloud → Self-Hosted Migration Strategy

### Current State Analysis

**What's Working Now** ✅
- ClearML Cloud for experiment tracking
- Metrics logging from FastAPI training jobs
- Web UI for experiment visualization
- Hyperparameter comparison between runs
- Team access to experiment history

**Why Migrate?** 💰
- ClearML Cloud has paywall at scale (team + storage)
- Data sovereignty: models and experiments leave infrastructure
- Cost optimization: self-hosted = fixed cost, not variable
- Full control: no dependency on external platform availability

### Migration Decision

**Recommended Approach: ClearML Self-Hosted**

```
Current Setup (Cloud):
    ClearML Cloud Platform
         ↓
    All experiments logged here
         ↓
    Metrics, hyperparameters, artifacts

Target Setup (Self-Hosted):
    ClearML Server (local)
    ├── MongoDB (metadata)
    ├── Elasticsearch (logs)
    ├── MinIO/Filesystem (artifacts)
    └── Web UI (localhost:8008)
         ↓
    Same UI, same features, zero code changes
```

### Why ClearML Self-Hosted vs MLflow?

| Criterion | ClearML Self-Hosted | MLflow Self-Hosted |
|-----------|-------------------|-----------------|
| **UI Quality** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Functional |
| **Hyperparameter Sweeps** | ✅ Built-in | ❌ Need Optuna separately |
| **Model Registry** | ✅ Complete | ⚠️ Basic |
| **Team Features** | ✅ Multi-user projects | ⚠️ Limited |
| **Operational Complexity** | Medium (3 services) | Low (single process) |
| **Team Already Knows** | ✅ Yes | ❌ New learning |
| **Investment Preservation** | ✅ High | ❌ Needs migration |
| **Feature Parity with Cloud** | ✅ 100% | ⚠️ 70% |

**Recommendation**: Keep ClearML, migrate to self-hosted

### Implementation Roadmap

#### Phase 1: Preparation (Week 1)
- [ ] Inventory current ClearML Cloud usage
  - Number of experiments
  - Storage size
  - Models to preserve
- [ ] Evaluate infrastructure options
  - Dedicated server vs. K8s deployment
  - Storage backend (local disk, NFS, MinIO)
  - Network access requirements

#### Phase 2: Self-Hosted Deployment (Week 2)
- [ ] Deploy ClearML Server
  - Use Docker Compose for development
  - Use Kubernetes for production
- [ ] Configure data storage
  - Database: MongoDB
  - Cache: Redis (optional)
  - Artifacts: Filesystem or MinIO
- [ ] Set up backups and monitoring

#### Phase 3: FastAPI Integration (Week 3)
- [ ] Update endpoint in FastAPI config
  - Change from `clearml.app/` to `localhost:8008`
  - Test with sample training job
  - Verify metrics logging works
- [ ] Run parallel testing
  - Keep Cloud running as backup
  - New jobs go to self-hosted
  - Verify functionality matches

#### Phase 4: Migration (Week 4)
- [ ] Export experiments from Cloud (optional)
- [ ] Redirect all new jobs to self-hosted
- [ ] Run for 1-2 weeks in parallel
- [ ] Cancel ClearML Cloud subscription

### Docker Compose Setup (Self-Hosted)

```yaml
# docker-compose.yml for ClearML Server
version: '3.8'

services:
  # MongoDB: stores metadata, configs, users
  mongo:
    image: mongo:4.4
    container_name: clearml-mongo
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: clearml
      MONGO_INITDB_ROOT_PASSWORD: clearml_password
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

  # Elasticsearch: stores logs and search indices
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    container_name: clearml-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  # ClearML Server: main application
  clearml-server:
    image: allegroai/clearml-server:latest
    container_name: clearml-server
    ports:
      - "8008:8008"  # Web UI + API
      - "8080:8080"  # File server
    environment:
      MONGO_URL: mongodb://clearml:clearml_password@mongo:27017
      ELASTICSEARCH_URL: http://elasticsearch:9200
      CLEARML_RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672//
    depends_on:
      - mongo
      - elasticsearch
      - rabbitmq
    volumes:
      - clearml_data:/opt/clearml/data
      - clearml_logs:/opt/clearml/logs
    restart: unless-stopped

  # RabbitMQ: message queue for task distribution
  rabbitmq:
    image: rabbitmq:3.9-management
    container_name: clearml-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: unless-stopped

volumes:
  mongo_data:
    driver: local
  elasticsearch_data:
    driver: local
  clearml_data:
    driver: local
  clearml_logs:
    driver: local
  rabbitmq_data:
    driver: local

networks:
  default:
    name: clearml-network
```

**Deployment**:
```bash
docker-compose up -d
# Access UI at http://localhost:8008
# Default credentials: admin / password
```

### Code Changes Needed (Minimal)

**Current FastAPI** (Cloud):
```python
from clearml import Task
from clearml.config import config_file

# Default: uses clearml.app (cloud)
task = Task.init(
    project_name="yolo-training",
    task_name=f"training_{job_id}"
)
```

**Updated FastAPI** (Self-Hosted):
```python
from clearml import Task
from clearml.config import config_file

# One-time configuration
config_file.set("api/host", "http://localhost:8008")
config_file.set("api/web_host", "http://localhost:8008")

# Rest is identical
task = Task.init(
    project_name="yolo-training",
    task_name=f"training_{job_id}"
)
```

**Or via environment variables** (cleaner):
```bash
export CLEARML__API__HOST=http://localhost:8008
export CLEARML__API__WEB_HOST=http://localhost:8008
```

### Data Migration from Cloud

**Option A: Export from Cloud**
```python
# Export all experiments and models from ClearML Cloud
from clearml import Task

# Authenticate with Cloud credentials
exported_tasks = Task.get_tasks(project_name="yolo-training")

for task in exported_tasks:
    print(f"Task: {task.name}")
    print(f"  Metrics: {task.get_metrics_scalar_latest_values()}")
    print(f"  Artifacts: {task.artifacts}")
    # Could serialize to JSON for backup
```

**Option B: Keep Cloud as Archive**
- Leave historical experiments on ClearML Cloud
- New experiments go to self-hosted
- Query Cloud for historical reference only
- Easier transition, no data loss risk

### Storage Considerations

**Artifact Storage Location**:
```
Self-Hosted ClearML Server
├── Database: /opt/clearml/data (MongoDB)
├── Logs: /opt/clearml/logs (Elasticsearch)
└── Artifacts: /opt/clearml/data/artifacts (models, checkpoints)
```

**Capacity Planning**:
- Small project (1-5 researchers): 500 GB sufficient
- Medium project (5-20 researchers): 2-5 TB recommended
- Large scale: MinIO or S3 backend for artifacts

### Monitoring and Maintenance

**Health Checks**:
```bash
# Check if ClearML Server is running
curl http://localhost:8008/version

# Check MongoDB
docker exec clearml-mongo mongosh -u clearml -p clearml_password --eval "db.adminCommand('ping')"

# Check Elasticsearch
curl http://localhost:9200/_cluster/health
```

**Backups** (critical):
```bash
# Daily backup strategy
# 1. MongoDB backup
docker exec clearml-mongo mongodump --out /backups/mongo_$(date +%Y%m%d)

# 2. Artifacts backup
rsync -av /opt/clearml/data/artifacts /backups/artifacts_$(date +%Y%m%d)

# 3. Logs backup (optional, large)
rsync -av /opt/clearml/logs /backups/logs_$(date +%Y%m%d)
```

### Rollback Strategy

If self-hosted doesn't work:
1. Keep ClearML Cloud account active during transition
2. Run 2 weeks in parallel (jobs log to both)
3. Only after validation, decommission Cloud
4. Worst case: restore from Cloud backup

### Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Web UI accessible | ✅ Yes | http://localhost:8008 loads |
| New experiments logged | ✅ Yes | Run test training job |
| Metrics persisted | ✅ Yes | Check metrics in UI |
| Models visible | ✅ Yes | Artifacts list populated |
| Performance | <2s | UI response time |
| Data migration | ✅ Optional | Historical experiments preserved |

### Cost-Benefit Analysis

**Before Migration** (ClearML Cloud):
- Monthly subscription: ~$200-500 (depends on usage)
- Data leaves infrastructure
- Limited storage
- Vendor lock-in risk

**After Migration** (Self-Hosted):
- Server hosting: ~$50-200/month (depends on infrastructure)
- Storage: ~$100-500/month (depends on volume)
- Ops overhead: ~4 hours/month (monitoring, backups)
- Data stays internal
- Full control and auditability

**Break-even**: ~6 months if infrastructure already exists

---

## Future Evolution

### Phase 2: Add Data Versioning
- Track dataset versions in ClearML
- Answer "which dataset trained this model?"
- Could integrate with Data Catalyst or similar

### Phase 3: Model Registry
- Promote ClearML to include model registry
- Track model lineage (data → model → deployment)
- Could move artifacts to MinIO/S3

### Phase 4: Full MLOps Integration
- ClearML could orchestrate training (not just track)
- Pipelines defined in ClearML
- Auto-deployment of models (CD/ML)

---

## Data Classification

**What ClearML Stores**:
- Experiment metadata (safe, public)
- Metrics and hyperparameters (safe, public)
- Training logs (usually safe, check for data leaks)
- Model paths (safe)

**What ClearML Does NOT Store**:
- Actual training data (stays local)
- Model weights (stays on filesystem)
- Raw images/detections (stays local)

---

## Public-Safe Note

This ADR describes the decision to use ClearML (open-source tool) for experiment tracking. The pattern of "external metadata store + local artifact storage" is a well-known approach. This ADR contains no proprietary details, credentials, or workspace identifiers.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-002**: Shared artifact storage (models live here)
- **ADR-003**: FastAPI logs experiments to ClearML
- **ADR-006**: Notebooks use ClearML results for visualization and analysis
- **ADR-007**: Alternative tracking architecture (ClearML vs alternatives)
- **ADR-009**: Phase 2 could extend this with data versioning

---

## References

This decision aligns with:
- Separation of concerns (tracking vs. storage)
- Single source of truth principle (artifacts on filesystem, metadata in ClearML)
- MLOps maturity models (structured experiment tracking at Level 2)
- Industry best practices: experiment tracking as infrastructure foundation

## Implementation Status

**Current** ✅
- ClearML Cloud integration working
- FastAPI submits training experiments
- Experiment UI accessible to team
- Metrics and hyperparameters logged

**In Progress** 🚀
- Evaluation of self-hosted deployment
- Infrastructure assessment for ClearML Server
- Cost analysis vs Cloud subscription

**Roadmap** 📋
- Q3 2026: Deploy ClearML Self-Hosted
- Q3 2026: Migrate experiments to self-hosted
- Q4 2026: Data versioning integration (ADR-009)
