# Production Evolution Roadmap

This document outlines the recommended evolution path from current pragmatic architecture to production-scale enterprise system.

## Evolution Philosophy

**Principle**: Build minimum viable orchestration, add enterprise features as real bottlenecks appear.

```
Phase 1 (Current): MVP Orchestration
    ↓ (Growth: > 3 concurrent jobs)
Phase 2: Distributed Job Queue
    ↓ (Growth: > 10 concurrent jobs)
Phase 3: Multi-GPU Worker Pool
    ↓ (Growth: > 50 concurrent jobs)
Phase 4: Kubernetes + Object Storage
    ↓ (Growth: Multi-region needed)
Phase 5: Enterprise Observability & SLA
```

---

## Phase 1: Current MVP (Synchronous Single Service)

### Timeline: Now

### Architecture

```
Django Web ←HTTP→ FastAPI Single Instance ←→ Shared Volume
    (port 8000)        (port 8001, 1 GPU)       (local)
         ↓                    ↓                      ↓
   PostgreSQL          PyTorch Training      Local Models/Data
```

### Characteristics

- ✓ Synchronous request/response
- ✓ Single GPU service instance
- ✓ Shared filesystem storage
- ✓ ClearML experiment tracking
- ✓ Basic error handling

### When to Move to Phase 2

**Trigger metrics**:
- Average queue wait time > 30 minutes
- > 3 concurrent long-running jobs observed
- Training requests being dropped
- System overload during peak hours

### Django Configuration Layer Evolution (Integrated into Phase 1+)

Django YOLO configuration models (ProjectConfiguration, ClassSet, DatasetConfig) require continuous improvement in parallel with GPU infrastructure scaling.

For comprehensive documentation, see [**docs/08-yolo-dataset-configuration-management.md**](./08-yolo-dataset-configuration-management.md).

**Phase 1 Enhancements (Immediate)**:

1. **Add Async YAML Generation**
   - Make `DatasetConfig.generate_yaml()` async (Celery or APScheduler)
   - Prevents UI blocking on large ClassSets
   - Returns job status to user

2. **Implement Configuration Validation**
   - Checksum YAML content after generation
   - Compare with database state on load
   - Warn user of drift

3. **Create ConfigurationRegistry Table**
   - Track all YAML file generations
   - Link YAML to ProjectConfiguration and user
   - Enable audit trail and history

4. **Use Environment Variables for Paths**
   - Replace hardcoded `/data/shared/` paths
   - Read `CONFIG_BASE_PATH` from settings
   - Support multi-environment deployments

5. **Add Preflight Validation**
   - Validate dataset directories exist
   - Check write permissions for YAML generation
   - Fail early with clear error messages

**Phase 2 Enhancements (With Job Queue)**:

1. **Async Configuration Generation**
   - Queue configuration generation as Celery task
   - Support bulk YAML generation for multiple projects
   - Parallel generation across workers

2. **Configuration Versioning**
   - Store previous YAML versions in database
   - Enable rollback if configuration breaks training
   - Compare versions in UI

3. **Linked Job Tracking**
   - Each YAML file linked to training jobs
   - Prevent deletion of active YAML files
   - Track model lineage to configuration

**Phase 3+ Enhancements**:

1. **Configuration as Code**
   - YAML definitions stored in version control
   - GitOps-style configuration management
   - Reproducible configurations

2. **Configuration Marketplace**
   - Share ClassSets across teams
   - Version control for class hierarchies
   - Templated configurations for common tasks

3. **Advanced Validation**
   - Test YAML with Ultralytics before submission
   - Detect class imbalance from dataset statistics
   - Recommend optimal training parameters

---

## Synthetic Dataset Generation Pipeline Evolution

For comprehensive documentation, see [**docs/20-synthetic-dataset-generation-pipeline.md**](./docs/20-synthetic-dataset-generation-pipeline.md).

### Phase 1 Enhancement (Current): Notebook-Based Experimentation

**Current State**:
- Sequential SAM processing
- Single GPU execution
- Local filesystem storage
- Batch compositing possible but not optimized

**Phase 1 Improvements**:
- ✓ Implement object filtering and quality checks
- ✓ Support COCO/YOLO dual-format export
- ✓ Version artifacts with manifest metadata
- ✓ Implement error recovery (skip failed images)

---

### Phase 2 Enhancement (With Job Queue): Distributed Pipeline

**When Phase 1 triggers**:
- Dataset generation needed for 1000+ images
- Sequential processing takes 2+ hours
- Interactive notebook workflow becomes tedious

**Phase 2 Improvements**:
1. **Async SAM Segmentation**
   - Queue SAM tasks via Celery
   - Batch process 8-16 images per task
   - Utilize multiple GPUs for parallelism

2. **Distributed Object Extraction**
   - Split dataset across workers
   - Extract objects in parallel
   - Aggregate results in shared storage

3. **Synthetic Composition Workers**
   - Distribute image composition tasks
   - Balance workload across workers
   - Monitor quality metrics in real-time

4. **Dataset Registry**
   - Publish dataset versions to central registry
   - Track lineage (source images → extracted objects → compositions)
   - Link to training jobs that consumed dataset

5. **Quality Monitoring**
   - Real-time quality metrics dashboard
   - Alert on composition failures
   - Track object coverage and distribution

**Expected Performance**:
- 1000-image segmentation: 10 hours → 30 minutes (4 GPU workers)
- Composition time: 4 hours → 15 minutes (multi-worker parallel)
- Total pipeline: 14 hours → 45 minutes

---

### Phase 3+ Enhancement: Enterprise Scale

**Phase 3 Improvements**:
1. **GPU Affinity**
   - Route SAM tasks to high-memory GPUs (A100/H100)
   - Route composition to general GPUs

2. **Distributed Object Storage**
   - Objects stored in S3 buckets with versioning
   - CDN-accessible for external platform uploads
   - Lifecycle policies for old versions

3. **Artifact Manifest Registry**
   - Metadata database for all generated artifacts
   - Query: "Find all datasets with CLASS_NAME_PLACEHOLDER"
   - Trace: "Which models trained on dataset version_5?"

4. **Advanced Validation Pipeline**
   - Automated quality gates before export
   - Validation against platform requirements
   - Automated platform uploads (CVAT, Roboflow)

5. **A/B Testing Support**
   - Generate multiple composition strategies
   - Compare model performance on each variant
   - Track which synthetic data helps most

---

## Phase 2: Distributed Job Queue (3-6 months)

### Timeline: When Phase 1 bottleneck appears

### Architecture

```
Django Web ←HTTP→ FastAPI API Layer
    (port 8000)    (lightweight, 8001)
                          ↓
                    Redis Queue
                          ↓
              ┌──────────┬──────────┐
              ↓          ↓          ↓
           Worker 0  Worker 1  Worker 2
          (GPU 0)    (GPU 1)    (GPU 2)
```

### New Components

#### Redis (Job Queue)

```yaml
# docker-compose Phase 2
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
```

**Role**: Persistent job queue
- Queue training/inference tasks
- Job persistence (survive service restart)
- Task priority queuing
- Job metadata storage

#### Celery (Task Distribution)

```python
# celery_app.py - Phase 2

from celery import Celery

app = Celery(
    'PROJECT_NAME_PLACEHOLDER',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)

@app.task(bind=True)
def train_model_task(self, dataset_id, hyperparams):
    """Distributed training task"""
    
    # Task runs on available worker
    self.update_state(state='PROGRESS', meta={'progress': 10})
    
    results = train_model(dataset_id, hyperparams)
    
    return results

# Queue job from Django
from celery_app import train_model_task

task = train_model_task.delay(dataset_id, hyperparams)
task_id = task.id  # Return immediately
```

#### FastAPI Refactored as Coordinator

```python
# Phase 2: FastAPI as coordinator, not executor

@app.post("/training")
async def submit_training(request: TrainingRequest):
    """Queue training job, return immediately"""
    
    task = train_model_task.delay(
        dataset_id=request.dataset_id,
        hyperparams=request.hyperparams
    )
    
    return {
        'job_id': task.id,
        'status': 'QUEUED',
        'queue_position': get_queue_position(task.id)
    }

@app.get("/training/{job_id}/status")
async def get_training_status(job_id: str):
    """Poll job status"""
    
    task = train_model_task.AsyncResult(job_id)
    
    return {
        'job_id': job_id,
        'status': task.state,
        'progress': task.info.get('progress') if task.info else None,
        'result': task.result if task.state == 'SUCCESS' else None
    }
```

### New Capabilities

✓ Async job submission
✓ Job persistence across restarts
✓ Priority queuing
✓ Multiple workers (horizontal scaling)
✓ Job status polling
✓ Retry logic

### Expected Scale Impact

- **Throughput**: 5-10 concurrent jobs (vs. 1-2 today)
- **Latency**: Median job waits 0-5 min (vs. immediate in Phase 1)
- **Reliability**: Jobs survive service restart

---

## Phase 3: Multi-GPU Worker Pool (6-12 months)

### Timeline: When Phase 2 shows resource saturation

### Architecture

```
Load Balancer (nginx)
    ↓
FastAPI API Layer (stateless)
    ↓
Redis Queue (central task broker)
    ├──────┬──────┬──────┬──────┐
    ↓      ↓      ↓      ↓      ↓
  GPU 0  GPU 1  GPU 2  GPU 3  GPU 4
  Worker Worker Worker Worker Worker
  (Compute (Compute
   Node 1)  Node 2)
```

### New Components

#### GPU Cluster

```bash
# Phase 3: Multi-GPU infrastructure

# Compute Node 1 (4× GPU)
  - FastAPI Worker × 4 (1 GPU each)
  - Shared storage mount
  - GPU-optimized Ubuntu 22.04 + CUDA 12.1

# Compute Node 2 (4× GPU)
  - FastAPI Worker × 4 (1 GPU each)
  - Shared storage mount
  - GPU-optimized Ubuntu 22.04 + CUDA 12.1

# Redis + PostgreSQL (separate high-availability node)
  - PostgreSQL 15 with replication
  - Redis cluster mode (HA)
```

#### Job Affinity & GPU Selection

```python
# Phase 3: Smart job placement

class GPUWorkload:
    """Describe GPU requirements"""
    
    def __init__(self):
        self.memory_required_gb = 16
        self.gpu_type = 'A100'  # or 'H100'
        self.preferred_workers = ['compute-node-1']

@app.post("/training")
async def submit_training(request: TrainingRequest):
    """Queue with GPU requirements"""
    
    workload = GPUWorkload()
    
    # Celery routes to appropriate worker
    task = train_model_task.apply_async(
        args=(request.dataset_id,),
        kwargs={'hyperparams': request.hyperparams},
        queue='gpu_queue',
        routing_key=f'gpu.{workload.gpu_type}'
    )
    
    return {'job_id': task.id, 'status': 'QUEUED'}
```

#### Distributed Model Registry

```sql
-- Phase 3: Model registry becomes source of truth

CREATE TABLE models (
    model_id UUID PRIMARY KEY,
    model_name VARCHAR(255),
    version INT,
    artifact_path VARCHAR(1024),  -- S3 path: s3://bucket/models/...
    mAP50 FLOAT,
    training_config JSONB,
    training_date TIMESTAMP,
    created_by VARCHAR(255),
    is_best BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE model_versions (
    version_id UUID PRIMARY KEY,
    model_id UUID REFERENCES models(model_id),
    version INT,
    is_active BOOLEAN,
    promoted_at TIMESTAMP
);

-- Atomic promotion logic
BEGIN;
  UPDATE models SET is_best = FALSE WHERE model_name = 'default' AND is_best = TRUE;
  INSERT INTO models (...) VALUES (...);
  UPDATE models SET is_best = TRUE WHERE model_id = NEW_MODEL_ID;
COMMIT;
```

### Expected Scale Impact

- **Throughput**: 20-50 concurrent jobs
- **Fault tolerance**: Single GPU failure doesn't halt all jobs
- **Cost efficiency**: Auto-scale workers by load
- **Flexibility**: Different job types can go to different node types

---

## Phase 4: Kubernetes + Object Storage (12-18 months)

### Timeline: When multi-region or automatic scaling needed

### Architecture

```
Kubernetes Cluster (k8s 1.27+)
┌─────────────────────────────────────┐
│  Ingress (nginx)                    │
│      ↓                              │
│  FastAPI Service (replicas: 3)      │
│      ↓                              │
│  Redis (StatefulSet)                │
│      ↓                              │
│  GPU Worker Pool (DaemonSet)        │
│      ├─ Node A (4× GPU A100)        │
│      └─ Node B (4× GPU A100)        │
│                                     │
│  PostgreSQL (StatefulSet, 3 nodes)  │
└─────────────────────────────────────┘
          ↓
    S3-Compatible Storage
    (AWS S3 or MinIO)
```

#### Kubernetes Manifests

```yaml
# Phase 4: Kubernetes FastAPI deployment

apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-api
  template:
    metadata:
      labels:
        app: fastapi-api
    spec:
      containers:
      - name: fastapi
        image: project_fastapi:latest
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        env:
        - name: REDIS_URL
          value: redis://redis-service:6379
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: gpu-worker
spec:
  serviceName: gpu-worker
  replicas: 2  # Per compute node
  selector:
    matchLabels:
      app: gpu-worker
  template:
    metadata:
      labels:
        app: gpu-worker
    spec:
      nodeSelector:
        gpu: "true"  # Node must have GPU
      containers:
      - name: worker
        image: project_fastapi_worker:latest
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
        env:
        - name: CELERY_BROKER_URL
          value: redis://redis-service:6379/0
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8001
  selector:
    app: fastapi-api
```

#### S3-Compatible Storage Integration

```python
# Phase 4: Artifact storage abstraction

import boto3
from botocore.client import Config

class S3ArtifactStorage:
    """Store artifacts in S3 (or MinIO) - example with placeholders"""
    
    def __init__(self, bucket_name='[S3_BUCKET_PLACEHOLDER]'):
        self.s3 = boto3.client(
            's3',
            endpoint_url=os.getenv('S3_ENDPOINT'),  # S3 or MinIO
            aws_access_key_id=os.getenv('[AWS_ACCESS_KEY_PLACEHOLDER]'),
            aws_secret_access_key=os.getenv('[AWS_SECRET_KEY_PLACEHOLDER]'),
            config=Config(signature_version='s3v4')
        )
        self.bucket = bucket_name
    
    def save_model(self, model_path: str, key: str):
        """Upload model to S3"""
        self.s3.upload_file(
            model_path,
            self.bucket,
            f'models/{key}.pt'
        )
    
    def load_model(self, key: str) -> str:
        """Download model from S3 to local cache"""
        local_path = f'/tmp/{key}.pt'
        self.s3.download_file(
            self.bucket,
            f'models/{key}.pt',
            local_path
        )
        return local_path
    
    def get_download_url(self, key: str, expires_in=3600):
        """Generate signed URL for model"""
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': f'models/{key}.pt'},
            ExpiresIn=expires_in
        )

# Usage in training
storage = S3ArtifactStorage()
storage.save_model('/app/models/best.pt', f'training_{run_id}_best')
model_url = storage.get_download_url(f'training_{run_id}_best')
```

#### Horizontal Scaling with HPA

```yaml
# Phase 4: Auto-scale FastAPI based on load

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Expected Scale Impact

- **Throughput**: 100-500 concurrent jobs
- **Availability**: Multi-node redundancy (99.9% uptime)
- **Cost**: Auto-scaling by demand
- **Flexibility**: Easy to add new node types (TPU, etc.)
- **Portability**: Can run on AWS, GCP, on-premises

---

## Phase 5: Enterprise Observability & Reliability (18+ months)

### Timeline: When production requirements demand it

### Purpose

Phase 5 adds infrastructure for:
- Visibility into system behavior (metrics, logs, traces)
- Reliability guarantees (SLO/SLI framework)
- Incident response processes
- On-call operational readiness

### Components

#### Metrics Collection (Prometheus + Grafana)

**Metrics to track**:
- Training job duration (histogram)
- Queue depth (gauge)
- Job success rate (counter)
- GPU utilization (gauge)
- Model inference latency (histogram)
- HTTP error rates (counter)

**Example Implementation**:

```python
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

# Create metrics
training_duration = Histogram('training_seconds', 'Training job duration')
queue_depth = Gauge('queue_depth', 'Current queue size')
job_success = Counter('jobs_completed_total', 'Total completed jobs', ['status'])
gpu_utilization = Gauge('gpu_utilization_percent', 'GPU memory usage')

# Usage
with training_duration.time():
    run_training_job(job_id)
```

**Deployment**:
- Prometheus server scrapes metrics from `/metrics` endpoint
- Grafana queries Prometheus for dashboards
- Alert rules configured in Prometheus

#### Centralized Logging (Loki or ELK Stack)

**Logs to aggregate**:
- Django application logs
- FastAPI access/error logs
- Training job logs
- Worker process logs
- GPU error logs

**Example: Structured Logging**:

```python
# Phase 5: Prometheus metrics

from prometheus_client import Counter, Histogram, Gauge

# Define metrics
training_jobs_total = Counter(
    'training_jobs_total',
    'Total training jobs',
    ['status']  # COMPLETED, FAILED, CANCELLED
)

training_duration_seconds = Histogram(
    'training_duration_seconds',
    'Training duration in seconds',
    buckets=[60, 300, 900, 3600, 7200]  # 1m, 5m, 15m, 1h, 2h
)

gpu_memory_usage_percent = Gauge(
    'gpu_memory_usage_percent',
    'GPU memory usage percentage',
    ['gpu_id', 'worker_node']
)

# Usage in code
with training_duration_seconds.time():
    results = train_model(...)
    training_jobs_total.labels(status='COMPLETED').inc()
```

#### Distributed Tracing (OpenTelemetry + Jaeger)

**Purpose**: Track request/job flow across services.

**Example**: Request enters Django → queued in Redis → picked by worker → updates ClearML → returns result

**Implementation**:
- Instrument Django, FastAPI, worker processes
- Propagate correlation IDs through all services
- Store traces in Jaeger backend
- Query: "Show me all spans for training job #42"

**Example Code**:
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup
jaeger_exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(...)

# Automatic instrumentation
FastAPIInstrumentor().instrument_app(app)

# Manual tracing
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("training_step") as span:
    span.set_attribute("job_id", job_id)
    train_model(...)
```

#### Alerting & On-Call Management (Prometheus Alertmanager)

**Alerts to configure**:
- ❌ **Critical**: GPU down, service unavailable, training failure rate > 50%
- ⚠️ **Warning**: Queue depth > 10 jobs, GPU memory > 95%, training slower than baseline
- ℹ️ **Info**: Daily report of completed jobs, dataset sizes

**Example Alert Rules**:
```yaml
groups:
  - name: training_jobs
    rules:
      - alert: HighJobFailureRate
        expr: rate(training_jobs_total{status="FAILED"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Training failure rate > 10%"
      
      - alert: QueueBacklog
        expr: queue_depth > 10
        for: 15m
        annotations:
          summary: "10+ jobs waiting in queue"
```

**Alerting Channels**:
- Email notifications
- Slack webhooks
- PagerDuty for critical alerts (on-call escalation)

#### SLO/SLI Framework

**SLOs to Define** (example targets):
- **Availability**: System available 99.5% of time (monthly)
- **Training Success Rate**: 99% of jobs complete successfully
- **Inference Latency**: 95th percentile < 500ms
- **Queue Time**: 95% of jobs start within 15 minutes of submission

**SLIs (Service Level Indicators)**:
```python
# Calculate SLI: What percentage of requests were successful?
successful_requests = training_jobs_total{status="COMPLETED"}
total_requests = training_jobs_total
success_sli = successful_requests / total_requests

# Calculate SLI: What percentage completed within SLO?
jobs_within_latency_slo = histogram_quantile(0.95, training_duration_seconds) < 1800
completed_jobs = training_jobs_total{status="COMPLETED"}
latency_sli = jobs_within_latency_slo / completed_jobs
```

**Error Budget**:
- Availability SLO: 99.5% → Error budget = 0.5% = ~3.6 hours downtime/month
- If actual availability is 99.3% → Used 0.2% of budget → 0.3% remaining
- Triggers deployment freeze if budget exhausted

#### Incident Response Process

**When alert fires**:
1. On-call engineer pages
2. Opens runbook (documented troubleshooting steps)
3. Implements immediate mitigation
4. Posts-incident: documents root cause, adds monitoring to prevent repeat

**Example Runbook**:
```markdown
# Runbook: GPU Out of Memory

## Symptoms
- Alert: "gpu_memory_exhausted"
- Error logs: "CUDA out of memory"

## Immediate Actions
1. Check active training jobs: `redis-cli KEYS 'job:*'`
2. Kill long-running job (> 2 hours): `kill -9 <pid>`
3. Restart GPU: `nvidia-smi -pm 1` (reset persistence mode)
4. Verify recovery: `nvidia-smi`

## Root Cause Investigation
- Check training job logs for memory leak
- Profile memory usage with `gpustat`
- Update model configs if needed

## Prevention
- Add memory limit checks before training
- Monitor GPU memory over time
- Alert at 80% usage (earlier warning)
```

### Phase 5 Benefits

| Capability | Before Phase 5 | After Phase 5 |
|-----------|---------|-----------|
| **Visibility** | Error logs only | Full observability (metrics, logs, traces) |
| **Alerting** | Manual checking | Automated, multi-channel alerts |
| **Incident Time** | 1-2 hours (discovery) | 5-10 min (page on-call) |
| **Reliability** | Best effort | SLO-backed guarantees |
| **Scaling** | Guess and check | Data-driven capacity planning |
| **Cost** | Unknown | Quantified per job |

### Timeline & Complexity

**Duration**: 12-18 months  
**Team**: DevOps engineer + platform engineer  
**Effort**: 600-800 hours  
**Complexity**: Very High

**Why Phase 5 is separate**:
- Requires DevOps expertise (not ML engineering)
- Only needed when system is production-critical
- Can operate for years without Phase 5 at small scale
- Typical large enterprise already has this infrastructure

---

## When NOT to Implement Phases 2-5

**Keep MVP-only if**:
- < 1 job per day
- < 1 year project lifespan
- < 5 concurrent users
- Single GPU sufficient
- Downtime tolerance: 1-2 hours
- Manual troubleshooting acceptable

**Upgrade to Phase 2+ when**:
- > 3 concurrent jobs frequently observed
- > 50 GB/day data generation
- > 5 concurrent users
- Need for job recovery after failure
- Downtime costs real money
    except Exception as e:
        checks['components']['redis'] = f'unhealthy: {e}'
        checks['status'] = 'unhealthy'
    
    # Check GPU availability
    try:
        available_gpus = get_available_gpu_count()
        checks['components']['gpu'] = f'healthy ({available_gpus} available)'
    except Exception as e:
        checks['components']['gpu'] = f'error: {e}'
    
    return checks

# SLA Monitoring
def check_sla():
    """Monitor SLA compliance"""
    
    # Check P99 latency (should be < 5 seconds)
    p99_latency = get_percentile_latency(99)
    assert p99_latency < 5, f"P99 latency SLA breach: {p99_latency}s"
    
    # Check success rate (should be > 99.5%)
    success_rate = get_success_rate()
    assert success_rate > 0.995, f"Success rate SLA breach: {success_rate}"
    
    # Check model training success (should be > 90%)
    training_success_rate = get_training_success_rate()
    assert training_success_rate > 0.9, f"Training SLA breach: {training_success_rate}"
```

### Expected Capabilities

✓ Full request tracing across services
✓ Automatic alert on SLA breach
✓ Performance trend analysis
✓ Anomaly detection
✓ Audit logging
✓ Compliance reporting

---

## Implementation Priority Matrix

```
                  Effort
            Low         High
Impact ┌─────────────┬─────────────┐
High   │ Redis Queue │ Kubernetes  │
       │ (Phase 2)   │ (Phase 4)   │
       ├─────────────┼─────────────┤
Low    │ Health Chks │ Observability
       │ (Phase 5)   │ (Phase 5)
       └─────────────┴─────────────┘

Recommended Order:
1. Phase 2: Redis Queue (high impact, moderate effort)
2. Phase 3: GPU Pool (high impact, high effort)
3. Phase 4: Kubernetes (medium impact, very high effort)
4. Phase 5: Observability (medium impact, moderate effort)
```

---

## Cost Evolution

| Phase | Infrastructure | Annual Cost (Estimate) |
|-------|----------------|------------------------|
| 1 | Single GPU VM | $1,000-5,000 |
| 2 | Add Redis cluster | +$500-1,000 |
| 3 | 4-GPU cluster | $8,000-20,000 |
| 4 | Kubernetes + multi-region | $15,000-50,000 |
| 5 | Full observability stack | +$5,000-10,000 |

---

## Success Metrics by Phase

### Phase 1 Goals
- ✓ Validate YOLO training orchestration works
- ✓ Verify FastAPI can communicate with Django
- ✓ Confirm GPU training completes without errors

### Phase 2 Goals
- ✓ Support 5-10 concurrent jobs
- ✓ Zero job loss on service restart
- ✓ Sub-5-minute average queue wait

### Phase 3 Goals
- ✓ Support 20-50 concurrent jobs
- ✓ Single GPU failure doesn't cascade
- ✓ 99.5% job success rate

### Phase 4 Goals
- ✓ Support 100-500 concurrent jobs
- ✓ 99.9% uptime (multi-node redundancy)
- ✓ Multi-region deployment possible

### Phase 5 Goals
- ✓ Automated alerting on anomalies
- ✓ < 100ms tracing overhead
- ✓ SLA compliance dashboard
- ✓ Sub-second debugging queries

---

## Continuity Strategy

Each phase:
1. ✓ Maintains backward compatibility (APIs unchanged)
2. ✓ Can be deployed incrementally
3. ✓ Allows rollback to previous phase
4. ✓ Provides clear metrics for trigger to next phase

**Principle**: Don't build Phase 4 infrastructure for Phase 1 scale. Evolve as real bottlenecks appear.

