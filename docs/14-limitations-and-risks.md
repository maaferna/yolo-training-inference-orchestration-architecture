# Limitations and Risks

This document explicitly states the current limitations of this architecture, known risks, and reasons for these constraints.

## No Formal Job Queue

### Current Limitation

The system uses **synchronous request/response** through FastAPI:

```
Django HTTP Request
    ↓
FastAPI receives
    ↓
[Long-running training/inference starts]
    ↓
[Django waits for response]
    ↓
[Training completes: 1-3 hours]
    ↓
Response returned to Django
    ↓
Django displays results
```

**Problem**: Django connection must remain open for hours

### Why This Limitation Exists

- **Pragmatic MVP**: Simpler to implement than message queue
- **Early validation**: Proves concept before investing in infrastructure
- **Resource efficiency**: No overhead of separate queue system
- **Debugging**: Direct request/response easier to trace

### Consequences

- ⚠️ Single FastAPI instance becomes bottleneck
- ⚠️ Django client must maintain HTTP connection
- ⚠️ Browser timeout risk (HTTP timeout ~30 minutes typical)
- ⚠️ No distributed task execution
- ⚠️ No job persistence or recovery

### When This Becomes a Problem

- > 5 concurrent training requests
- > 10 concurrent inference requests
- Network instability (HTTP connection drops)
- Need for job recovery after service restart

---

## No Celery, Redis, Kafka, or RabbitMQ

### Absent Components

These popular message queue systems are **not implemented**:

- **Celery**: Distributed task queue for Python
- **Redis**: In-memory data store (job queue, caching)
- **Kafka**: Event streaming platform
- **RabbitMQ**: Message broker

### Why Not Implemented

**Reasons for pragmatic delay**:

1. **Added Complexity**:
   - Extra services to deploy and maintain
   - Debugging across services difficult
   - Configuration management overhead

2. **Current Scale**: 
   - Single GPU doesn't justify distributed queue
   - Synchronous is sufficient for 1-2 concurrent jobs

3. **Cost**:
   - Additional infrastructure
   - DevOps investment for monitoring

4. **Maturity**:
   - Validate basic architecture first
   - Then scale when bottlenecks appear

### When Job Queue Becomes Essential

- **Trigger 1**: > 3 concurrent long-running jobs
- **Trigger 2**: Need for job persistence (failures)
- **Trigger 3**: Multiple GPU workers needed
- **Trigger 4**: Multi-user contention

### Implementation Timeline

**Phase 1** (Current): Synchronous, single GPU
**Phase 2** (Future): Add Redis + basic queue
**Phase 3** (Future): Full Celery infrastructure
**Phase 4** (Future): Kafka for event streaming

---

## Long-Running Tasks Are Synchronous

### Synchronous Blocking

```python
# Current approach
@app.post("/training")
async def start_training(request):
    # This blocks for 1-3 hours!
    results = train_model(request.dataset)
    return results
```

### Problems

- ⚠️ HTTP connection must remain open (timeout risk)
- ⚠️ Uvicorn worker thread blocked
- ⚠️ Can't serve other requests well
- ⚠️ Limited to ~4-8 concurrent tasks (thread pool size)

### Recommended: Async Pattern

```python
# Future approach
@app.post("/training")
async def start_training(request):
    # Submit job to queue
    job_id = queue.submit(train_model, request)
    # Return immediately
    return {'job_id': job_id, 'status': 'QUEUED'}

# Later: poll for results
@app.get("/training/{job_id}")
async def get_training_status(job_id):
    status = queue.get_status(job_id)
    return {'status': status}
```

---

## Shared Filesystem Coupling

### Tight Coupling Issue

```
Architecture Dependency:

FastAPI ←→ [SHARED VOLUME] ←→ Django
             (docker volume)

Both services tightly coupled via filesystem
```

### Problems

- ⚠️ No abstraction layer
- ⚠️ Hard to replace storage backend
- ⚠️ Path management fragile
- ⚠️ No storage versioning
- ⚠️ Scaling to multiple nodes impossible (local filesystem)

### Current Workarounds

- Use bind mounts (development)
- Docker named volumes (local development)
- NFS mount (could work, adds latency)

### Future: Storage Abstraction

```python
# Future approach with abstraction

class ArtifactStorage:
    """Abstract storage interface"""
    
    def save_model(self, model_path, key):
        pass
    
    def load_model(self, key):
        pass

class LocalStorage(ArtifactStorage):
    """Local filesystem implementation"""
    pass

class S3Storage(ArtifactStorage):
    """AWS S3 implementation"""
    pass

# Use abstraction in code
storage = LocalStorage()  # Swap implementations
storage.save_model(model, 'best_model_v1')
```

---

## Single FastAPI GPU Service Bottleneck

### Single Instance Constraint

```
GPU Workload:

Job 1: Training (GPU 0) ━━━━━━━━━━━━━━━━ [3 hours]
                                          ↑
Job 2: Inference ❌ (queued, blocked)    Queue

Result: Sequential execution, no parallelism
```

### When Bottleneck Appears

- > 2 concurrent long jobs
- Peak usage times with high request load
- Multi-user scenarios

### Solution: Multiple GPU Workers

```
Future: Multi-instance with load balancing

Load Balancer (nginx)
    ├→ FastAPI Worker 0 (GPU 0) ━━━━━ [Training]
    ├→ FastAPI Worker 1 (GPU 1) ━━━ [Inference]
    ├→ FastAPI Worker 2 (GPU 2) ━ [CI Training]
    └→ FastAPI Worker 3 (GPU 3)   [Ready]
```

---

## No Distributed Job Scheduling

### Manual Coordination

Currently, users must:
- Submit jobs manually
- Wait for completion
- No job priorities
- No fairness guarantees

### Problems

- ⚠️ First-come-first-served (not priority-based)
- ⚠️ No workload balancing
- ⚠️ No SLA guarantees
- ⚠️ No preemption (can't prioritize urgent jobs)

### Future: Kubernetes Scheduler

```yaml
# Future: Kubernetes CronJob for CI training

apiVersion: batch/v1
kind: CronJob
metadata:
  name: ci-training-daily
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ci-training
            image: project_fastapi:latest
            resources:
              requests:
                nvidia.com/gpu: 1
          restartPolicy: OnFailure
```

---

## No Job Registry

### Current: Implicit Job State

Jobs exist only while running:
- No persistent record of queued jobs
- No failed job history
- No job metadata storage
- Can't query "all jobs from last week"

### Future: Job Registry Table

```sql
CREATE TABLE job_registry (
    job_id UUID PRIMARY KEY,
    job_type ENUM('training', 'ci-training', 'inference'),
    status ENUM('queued', 'running', 'completed', 'failed'),
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    user_id INTEGER,
    parameters JSONB,
    result_summary JSONB,
    error_message TEXT
);
```

---

## No Transactional Model Registry

### Current: File-Based Registry (Race Conditions Possible)

```python
# Simplified: no atomicity

def update_best_model():
    # Read
    ref = json.load(best_model_ref.json)
    
    # Process
    ref['mAP50'] = 0.87
    
    # Write
    json.dump(ref)  # NOT atomic - can have race condition!
```

### Problems

- ⚠️ Concurrent CI training can corrupt state
- ⚠️ Model can be temporarily degraded
- ⚠️ No rollback capability
- ⚠️ No audit trail of changes

### Mitigation (Current)

- Serialize CI training (one at a time)
- Atomic file operations (write to tmp, rename)

### Future: Transactional Registry

```sql
CREATE TABLE model_registry (
    model_id UUID PRIMARY KEY,
    model_name VARCHAR,
    model_path VARCHAR,
    mAP50 FLOAT,
    is_best BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE(model_name, is_best)
);

-- Atomic update
BEGIN TRANSACTION;
UPDATE model_registry SET is_best = FALSE WHERE model_name = 'default' AND is_best = TRUE;
INSERT INTO model_registry (...) VALUES (...);
COMMIT;  -- All or nothing
```

---

## Limited Observability

### Current State

**Available**:
- ✓ Application logs (console output)
- ✓ ClearML experiment tracking (metadata)
- ✓ Local error files (in shared storage)

**Missing**:
- ❌ Distributed tracing (Jaeger, DataDog)
- ❌ Metrics collection (Prometheus)
- ❌ Structured logging (ELK, Splunk)
- ❌ Correlation IDs (cross-service tracing)
- ❌ Performance monitoring
- ❌ Alerting and anomaly detection

### When Observability Becomes Critical

- Debugging production issues (hard without traces)
- Performance optimization (need metrics)
- SLA monitoring (need monitoring data)
- Multi-service troubleshooting (need correlation)

### Recommended: Structured Logging Foundation

```python
# Future: Structured logging with correlation IDs

import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id', default=str(uuid.uuid4()))

def log_structured(level, message, **fields):
    """Structured log with correlation ID"""
    
    fields['correlation_id'] = correlation_id.get()
    fields['timestamp'] = datetime.now().isoformat()
    fields['level'] = level
    fields['message'] = message
    
    print(json.dumps(fields))  # or send to logging service
```

---

## Django Configuration Layer Risks

Django YOLO configuration models (ProjectConfiguration, ClassSet, DatasetConfig) introduce specific architectural risks. For comprehensive documentation, see [**docs/08-yolo-dataset-configuration-management.md**](./08-yolo-dataset-configuration-management.md).

### Risk 1: YAML/Database Configuration Drift

**Scenario**:
- Django database has DetectionClass A, B, C
- YAML file was previously generated with classes A, B
- FastAPI training uses stale YAML file with only A, B
- New class C is ignored
- Model trained on incomplete class set

**Impact**:
- ⚠️ Inconsistent training datasets
- ⚠️ Hard to debug (appears random)
- ⚠️ Model degradation on new classes

**Mitigation**:
- Regenerate YAML immediately after class changes
- Add integration test: compare YAML names with DB classes
- Include class checksum in YAML for validation

---

### Risk 2: Hardcoded Path Coupling

**Scenario**:
- Django hardcodes `/data/shared/configs/` 
- Docker mount setup changes to `/app/configs/`
- DatasetConfig still writes to old hardcoded path
- FastAPI can't find YAML files
- Training requests fail

**Impact**:
- ⚠️ Tight coupling between code and infrastructure
- ⚠️ Difficult environment transitions (dev→staging→prod)
- ⚠️ Container orchestration inflexible

**Mitigation**:
- Use environment variables: `CONFIG_BASE_PATH`
- Read from settings, not hardcoded strings
- Validate paths at startup

---

### Risk 3: Synchronous YAML Generation Blocking

**Scenario**:
- Large ClassSet with 1000+ classes
- YAML generation takes 5+ seconds
- Django UI blocks during `DatasetConfig.generate_yaml()`
- User sees spinner for 5+ seconds
- Appears frozen/unresponsive

**Impact**:
- ⚠️ Poor user experience
- ⚠️ Appears to be bug
- ⚠️ No parallelism

**Mitigation**:
- Make generation async (Django task, Celery)
- Cache generated YAML files
- Pre-generate YAMLs on schedule

---

### Risk 4: No Formal Retry Logic

**Scenario**:
- DatasetConfig.save_yaml() fails (disk full, permission denied)
- Django UI shows error, but no automatic retry
- User must manually regenerate, might forget
- Training never runs

**Impact**:
- ⚠️ Depends on user manual intervention
- ⚠️ No recovery mechanism
- ⚠️ Failed attempts not tracked

**Mitigation**:
- Implement exponential backoff retry
- Log retry attempts for debugging
- Email user if permanent failure

---

### Risk 5: No Job Status Registry

**Scenario**:
- User creates ProjectConfiguration 1 with ClassSet A
- User creates ProjectConfiguration 2 with ClassSet B
- Both generate YAML files at similar timestamps
- User can't remember which YAML is for which project
- Wrong YAML used for training

**Impact**:
- ⚠️ Confusion between configurations
- ⚠️ Manual tracking burden
- ⚠️ Audit trail missing

**Mitigation**:
- Create YAMLJobRegistry table
- Link each YAML file to project and user
- Display generation history in UI

---

### Risk 6: Stale dataset_yaml_path References

**Scenario**:
- User generates YAML, trains model, saves result
- User later regenerates YAML (classes changed)
- Old best_model_ref.json points to old YAML
- Using old model for inference loads incompatible classes
- Inference fails or produces incorrect results

**Impact**:
- ⚠️ Model-configuration mismatch
- ⚠️ Silent failures (model loads but classes wrong)
- ⚠️ Model lineage broken

**Mitigation**:
- Validate YAML availability before inference
- Store YAML content/hash in model metadata
- Prevent deletion of YAML files in use

---

## Not Production-Ready for High-Throughput

### Scale Limitations

| Metric | Current | Enterprise |
|--------|---------|-----------|
| Concurrent jobs | 1-2 | 100+ |
| Job throughput | ~2-5/hour | 1000+/hour |
| Uptime SLA | None | 99.9% |
| Data retention | Limited | Indefinite |
| Geographic distribution | Single region | Multi-region |
| Cost efficiency | High | Optimized |

### Bottlenecks for Scale

1. **Single GPU Service**: Can handle ~1-2 concurrent long jobs
2. **Synchronous Tasks**: Can't parallelize across jobs
3. **Shared Filesystem**: Not distributed
4. **No Queue**: No job buffering
5. **No Monitoring**: Can't detect degradation

### Path to Scale

**<10 concurrent jobs**: Current architecture sufficient
**10-50 concurrent**: Add job queue + 2-4 GPU workers
**50-500 concurrent**: Multi-node Kubernetes + object storage
**500+**: Autoscaling Kubernetes + serverless inference

---

## Summary of Limitations

| Category | Current | Gap | Impact |
|----------|---------|-----|--------|
| Job Queue | ❌ None | Needed for scale | Synchronous bottleneck |
| Task Distribution | ❌ Single instance | Need multiple workers | Single point of failure |
| Model Registry | ⚠️ File-based | Need transactional DB | Race conditions possible |
| Storage | ⚠️ Shared filesystem | Need object storage | Not multi-node scalable |
| Observability | ⚠️ Basic logging | Need structured tracing | Debugging difficult |
| Reliability | ⚠️ Basic error handling | Need retry + circuit breaker | System fragility |
| Scalability | ❌ Single service | Need autoscaling | Not ready for load |

---

## Reasons These Exist

These are not bugs or oversights. They reflect **pragmatic engineering decisions**:

1. **Start Simple**: Validate concept before infrastructure investment
2. **Cost**: Enterprise infrastructure is expensive to build/maintain
3. **Complexity**: Each added component increases operational overhead
4. **Maturity**: Evolve architecture as requirements change
5. **ROI**: Build complex features when bottlenecks become real

---

## Evolution Strategy

**Recommended sequence**:

1. **Phase 1 (Now)**: Validate basic orchestration
2. **Phase 2 (1-3 months)**: Add job queue when > 3 concurrent jobs needed
3. **Phase 3 (3-6 months)**: Distributed GPU workers
4. **Phase 4 (6+ months)**: Object storage and Kubernetes
5. **Phase 5**: Enterprise-scale multi-region deployment

---

**This architecture is pragmatically scoped for early-stage development and validation. Production scale evolution is addressed in the roadmap.**
