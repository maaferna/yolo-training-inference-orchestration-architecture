# Migration Guide: ClearML Cloud → Self-Hosted

> **Note**: This is a template for infrastructure operations teams. It documents the deployment and operations patterns that would be used if this architecture were moved to self-hosted infrastructure. These are NOT part of the core architecture documentation; they are examples of DevOps execution planning.

**Status**: Planning Phase  
**Target Date**: Q3 2026  
**Risk Level**: Low (can run in parallel)  

---

## Quick Summary

Migrate from ClearML Cloud (SaaS) to self-hosted ClearML Server to:
- ✅ Potentially reduce cost — quantify with the worksheet below before committing
- ✅ Keep data internal (data sovereignty)
- ✅ Full control and customization
- ✅ Zero code changes (same API)

**Timeline**: 4 weeks, minimal disruption

---

## Phase 1: Assessment (Week 1)

### Current Usage Inventory

```bash
# Questions to answer:
- How many experiments currently in Cloud? _____
- Total storage used? _____ GB
- Number of active researchers? _____
- How many concurrent jobs? _____
```

### Infrastructure Check

**Do we have**:
- [ ] Spare server (4+ cores, 16+ GB RAM, 500+ GB storage)?
- [ ] Kubernetes cluster available?
- [ ] Docker + Docker Compose installed?
- [ ] Network access (firewall rules OK)?
- [ ] Backup storage?

### Cost Analysis

This is a worksheet, not a result. It predicts nothing until real figures are
substituted, and no saving should be quoted anywhere until they have been.

**Current** (ClearML Cloud):
```
Monthly subscription:  CLOUD_SUBSCRIPTION
Storage:               CLOUD_STORAGE
Monthly total:         CLOUD_MONTHLY = CLOUD_SUBSCRIPTION + CLOUD_STORAGE
```

**After Migration** (Self-Hosted):
```
Server or VM:          HOST_MONTHLY
Storage:               STORAGE_MONTHLY
Operations time:       4 hours/month x HOURLY_RATE = OPS_MONTHLY
Monthly total:         SELF_MONTHLY = HOST_MONTHLY + STORAGE_MONTHLY + OPS_MONTHLY

One-off migration:     4 weeks of engineering time = MIGRATION_COST
```

**Break-even**:
```
monthly_saving = CLOUD_MONTHLY - SELF_MONTHLY
break_even     = MIGRATION_COST / monthly_saving        (months)
```

Two things this makes explicit that a raw price comparison hides:

- If `monthly_saving` is zero or negative once operations time is counted, there
  is no break-even and self-hosting costs more, whatever the subscription line says.
- Operations time is the term most often left out, and the one most likely to
  decide the answer for a small internal team.

---

## Phase 2: Deployment (Week 2)

### Option A: Docker Compose (Development/Small Teams)

**Best for**: <10 researchers, single server

```bash
# 1. Create directory
mkdir -p /opt/clearml-server
cd /opt/clearml-server

# 2. Create docker-compose.yml (see ADR-004 for full content)
# Copy full docker-compose from ADR-004 here

# 3. Deploy
docker-compose up -d

# 4. Verify
curl http://localhost:8008/version
```

**Access**:
- UI: http://localhost:8008
- Default credentials: admin / password
- Change password immediately!

### Option B: Kubernetes (Production/Large Teams)

**Best for**: 20+ researchers, need high availability

```bash
# Using Helm (simplest)
helm repo add allegroai https://allegroai.github.io/helm-charts
helm repo update

helm install clearml allegroai/clearml \
  --namespace clearml \
  --create-namespace \
  --values values.yaml
```

See `docs/deployment/clearml-k8s-values.yaml` for production config.

### Post-Deployment Setup

```bash
# 1. Access web UI
# Go to http://your-server:8008

# 2. Change admin password
# Settings → Users → admin → Change Password

# 3. Create first project
# Create project "yolo-training"

# 4. Create API credentials
# Settings → Workspace → Generate new credentials
# Store safely (credentials.txt)
```

---

## Phase 3: FastAPI Integration (Week 3)

### Update Configuration

**Option A: Environment Variables** (Recommended)

```bash
# In your FastAPI container/pod
export CLEARML__API__HOST=http://clearml-server:8008
export CLEARML__API__WEB_HOST=http://clearml-server:8008
export CLEARML__API__ACCESS_KEY=your_access_key
export CLEARML__API__SECRET_KEY=your_secret_key
```

**Option B: Code Update** (If env vars not available)

```python
# fastapi/main.py
from clearml import Task
from clearml.config import config_file

# Configure for self-hosted
config_file.set("api/host", "http://clearml-server:8008")
config_file.set("api/web_host", "http://clearml-server:8008")

@app.post("/train")
async def submit_training(config: TrainingConfig):
    task = Task.init(
        project_name="yolo-training",
        task_name=f"training_{config.model}_{datetime.now().isoformat()}"
    )
    # Rest of code unchanged
```

### Testing Integration

```python
# test_clearml_integration.py
from clearml import Task
import time

def test_clearml_connection():
    """Verify FastAPI can connect to self-hosted ClearML"""
    try:
        task = Task.init(
            project_name="yolo-training",
            task_name="test_integration",
            task_type="testing"
        )
        
        # Log a test metric
        task.get_logger().report_scalar(
            title="test",
            series="metric",
            value=42.0,
            iteration=0
        )
        
        task.close()
        print("✅ ClearML integration successful")
        return True
    except Exception as e:
        print(f"❌ ClearML integration failed: {e}")
        return False

if __name__ == "__main__":
    test_clearml_connection()
```

**Run test**:
```bash
python test_clearml_integration.py
# Should output: ✅ ClearML integration successful
```

### Docker Network Setup

**If running in Docker**:

```yaml
# docker-compose.yml for FastAPI service
services:
  fastapi:
    image: your-fastapi:latest
    environment:
      CLEARML__API__HOST: http://clearml-server:8008
      CLEARML__API__WEB_HOST: http://clearml-server:8008
    networks:
      - clearml-network
    depends_on:
      - clearml-server

networks:
  clearml-network:
    external: true
    name: clearml-network  # Must match ClearML deployment
```

---

## Phase 4: Migration (Week 4)

### Data Export from Cloud (Optional)

```python
# export_experiments.py
from clearml import Task
import json
from datetime import datetime

def export_all_experiments(project_name):
    """Export all experiments from ClearML Cloud"""
    
    # Configure for Cloud (current)
    from clearml.config import config_file
    config_file.set("api/host", "https://clearml.app")
    
    tasks = Task.get_tasks(
        project_name=project_name,
        include_subprojects=True
    )
    
    export_data = []
    for task in tasks:
        export_data.append({
            "name": task.name,
            "id": task.id,
            "project": task.get_project_name(),
            "created": task.created.isoformat(),
            "status": task.status,
            "hyperparameters": task.get_hyperparams(),
            "metrics": task.get_metrics(),
        })
    
    # Save to file
    filename = f"clearml_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported {len(export_data)} experiments to {filename}")
    return filename

if __name__ == "__main__":
    export_all_experiments("yolo-training")
```

**Run export**:
```bash
python export_experiments.py
# Creates: clearml_export_20260612_140000.json
```

### Redirect New Jobs

```bash
# BEFORE: All jobs go to Cloud
# FastAPI endpoint: clearml.app (no changes needed)

# AFTER: All jobs go to self-hosted
export CLEARML__API__HOST=http://clearml-server:8008

# Restart FastAPI
docker-compose restart fastapi
# or
kubectl rollout restart deployment/fastapi
```

### Run in Parallel (2 Weeks)

**Week 3-4: Parallel Execution**
```
Old Path (Cloud):     New Path (Self-Hosted):
ClearML Cloud    →    ← ClearML Server
  ↑                        ↑
  └─ FastAPI ─────────────┘

Both running, jobs log to self-hosted only
Verify everything works before decommissioning Cloud
```

**Monitoring**:
```bash
# Check self-hosted is logging experiments
curl http://localhost:8008/tasks?project=yolo-training

# Should return tasks with recent timestamps
```

### Decommission Cloud

Once confident (after 2 weeks of parallel):
```bash
# 1. Archive any critical experiments
python export_experiments.py

# 2. Verify all necessary data in self-hosted
# UI: Check http://localhost:8008

# 3. Cancel ClearML Cloud subscription
# Web: Go to ClearML.app → Billing → Cancel

# 4. Remove Cloud credentials (if any stored in code)
grep -r "clearml.app" .  # Should be empty
```

---

## Phase 5: Operations (Ongoing)

### Daily Monitoring

```bash
#!/bin/bash
# check_clearml_health.sh

echo "=== ClearML Server Health Check ==="

# 1. Web UI
curl -s http://localhost:8008/version > /dev/null && \
  echo "✅ Web UI: OK" || echo "❌ Web UI: DOWN"

# 2. MongoDB
docker exec clearml-mongo mongosh -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" --eval "db.adminCommand('ping')" 2>/dev/null | grep "ok" > /dev/null && \
  echo "✅ MongoDB: OK" || echo "❌ MongoDB: DOWN"

# 3. Elasticsearch
curl -s http://localhost:9200/_cluster/health | grep "green\|yellow" > /dev/null && \
  echo "✅ Elasticsearch: OK" || echo "❌ Elasticsearch: DOWN"

# 4. RabbitMQ
curl -s -u guest:guest http://localhost:15672/api/aliveness-test/clearml-network | grep "ok" > /dev/null && \
  echo "✅ RabbitMQ: OK" || echo "❌ RabbitMQ: DOWN"

echo "=== Health Check Complete ==="
```

**Run daily**:
```bash
chmod +x check_clearml_health.sh
# Add to crontab: 0 9 * * * /path/to/check_clearml_health.sh
```

### Weekly Backup

```bash
#!/bin/bash
# backup_clearml.sh

BACKUP_DIR="/backups/clearml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Starting ClearML backup..."

# 1. MongoDB backup
docker exec clearml-mongo mongodump --archive > $BACKUP_DIR/mongo_$TIMESTAMP.archive

# 2. Artifacts backup
rsync -av /opt/clearml/data/artifacts $BACKUP_DIR/artifacts_$TIMESTAMP

# 3. Compress and upload
tar -czf $BACKUP_DIR/clearml_$TIMESTAMP.tar.gz $BACKUP_DIR/mongo_$TIMESTAMP.archive $BACKUP_DIR/artifacts_$TIMESTAMP

# 4. Keep only last 4 weeks
find $BACKUP_DIR -mtime +30 -delete

echo "✅ Backup complete: $BACKUP_DIR/clearml_$TIMESTAMP.tar.gz"
```

**Run weekly**:
```bash
chmod +x backup_clearml.sh
# Add to crontab: 0 2 * * 0 /path/to/backup_clearml.sh
```

### Storage Management

**Monitor disk usage**:
```bash
#!/bin/bash
# Monitor artifact storage growth

du -sh /opt/clearml/data/artifacts

# If approaching capacity:
# - Archive old experiments
# - Delete old checkpoints
# - Consider MinIO backend (external storage)
```

---

## Troubleshooting

### Issue: "Cannot connect to ClearML Server"

```bash
# Check 1: Server running?
docker-compose ps
# Should show clearml-server as "Up"

# Check 2: Port accessible?
curl http://localhost:8008/version
# Should return version info

# Check 3: FastAPI env vars correct?
echo $CLEARML__API__HOST
# Should be http://clearml-server:8008 (or actual IP)

# Check 4: Network connectivity?
docker exec clearml-server ping mongo
# Should show responses
```

### Issue: "No experiments appearing in UI"

```bash
# Check MongoDB has data:
docker exec clearml-mongo mongosh -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD"
> use clearml
> db.tasks.count()
# Should be > 0 after submitting jobs

# Check FastAPI actually submitting:
# Add logging to training script
from clearml import Task
task = Task.init(...)  # This will print debug info
print(f"Task ID: {task.id}")
```

### Issue: "Out of disk space"

```bash
# Check usage:
df -h /opt/clearml/data

# Clean old artifacts:
docker exec clearml-server /opt/clearml/bin/cleanup.sh --days 30

# Or manually remove old experiments:
docker exec clearml-mongo mongosh -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD"
> use clearml
> db.tasks.deleteMany({created: {$lt: new Date(Date.now() - 90*24*60*60*1000)}})
# Deletes experiments older than 90 days
```

---

## Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Web UI accessible | Visit http://localhost:8008 |
| New experiments logged | Submit test job, see in UI |
| Metrics persisted | Check metrics in experiment details |
| Models visible | Check artifacts in experiment |
| Performance acceptable | Page load < 2 seconds |
| Backups running | Check backup directory updated weekly |
| All team can access | Researchers can login |

---

## Rollback Plan

If issues arise:

1. **Keep ClearML Cloud active** during transition
2. **Run parallel for 2 weeks** before decommissioning
3. **If disaster**: Point FastAPI back to Cloud
   ```bash
   unset CLEARML__API__HOST
   unset CLEARML__API__WEB_HOST
   # Restart FastAPI
   ```

---

## Related Documentation

- **ADR-004**: ClearML experiment tracking architecture decision
- **ADR-007**: Alternative MLOps tools comparison
- `docs/deployment/clearml-k8s-values.yaml`: Kubernetes config
- ClearML official docs: https://clear.ml/docs/latest/

---

## Questions?

Contact: MLOps team  
Updated: June 12, 2026
