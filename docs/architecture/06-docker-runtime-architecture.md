# Docker Runtime Architecture

This document describes the containerized deployment architecture and runtime configuration.

## Docker Compose Overview

The system runs as a multi-container application using Docker Compose for local development and testing.

```yaml
# CONCEPTUAL DOCKER COMPOSE STRUCTURE (Non-Production)
# This is for architectural reference only
version: '3.8'

services:
  django:
    # Web application layer
    image: project_django:latest
    ports:
      - "8000:8000"
    volumes:
      - shared_storage:/data/shared/
    environment:
      - FASTAPI_URL=http://fastapi:8001
      - DATABASE_URL=postgresql://...
    depends_on:
      - postgres
    networks:
      - ml_network

  fastapi:
    # AI service layer
    image: project_fastapi:latest
    ports:
      - "8001:8001"
    volumes:
      - shared_storage:/app/shared_data/
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - CLEARML_WORKSPACE=PROJECT_WORKSPACE_PLACEHOLDER
    depends_on:
      - postgres
    networks:
      - ml_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  postgres:
    # Database layer
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=PASSWORD_PLACEHOLDER
      - POSTGRES_DB=mldb
    networks:
      - ml_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  shared_storage:
    driver: local
  db_data:
    driver: local

networks:
  ml_network:
    driver: bridge
```

## Container Specifications

### Django Container

**Purpose**: Web application layer for request submission and result visualization

**Image**: Python 3.11 slim with Django

**Dependencies**:
```
Django==4.x
djangorestframework==3.x
psycopg2-binary==2.9.x
requests==2.x
python-dotenv==1.0.x
gunicorn==20.x
```

**Port Mapping**:
- `8000:8000` - Django development server (or gunicorn in production)

**Volume Mounts**:
```
/data/shared/  ← Shared storage for reading results
```

**Environment Variables** (example placeholders):
```env
DEBUG=False  # Always False in non-development
ALLOWED_HOSTS=localhost,127.0.0.1,[DJANGO_SERVICE_NAME]
FASTAPI_URL=http://[FASTAPI_SERVICE_NAME]:[FASTAPI_PORT]
DATABASE_URL=[DATABASE_CONNECTION_STRING_PLACEHOLDER]
SECRET_KEY=[DJANGO_SECRET_KEY_PLACEHOLDER]
```

**Network**: `ml_network` (bridge)

**Startup Command**:
```bash
python manage.py migrate
gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Health Check**:
```bash
curl -f http://localhost:8000/health/ || exit 1
```

---

### FastAPI Container

**Purpose**: AI service orchestration layer

**Image**: NVIDIA CUDA 12.1 runtime + Python 3.11

**Dependencies**:
```
fastapi==0.x
pydantic==2.x
uvicorn==0.x
torch==2.x  # with CUDA 12.1
ultralytics==8.x  # YOLOv8/v11
sahi==0.x  # High-resolution inference
clearml==1.x  # Experiment tracking
opencv-python==4.x
numpy==1.x
Pillow==10.x
```

**Port Mapping**:
- `8001:8001` - FastAPI server

**Volume Mounts**:
```
/app/shared_data/  ← Shared storage for reading/writing artifacts
```

**GPU Support**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Environment Variables**:
```env
CUDA_VISIBLE_DEVICES=0
CLEARML_API_HOST=https://api.clearml.com/
CLEARML_API_ACCESS_KEY=ACCESS_KEY_PLACEHOLDER
CLEARML_API_SECRET_KEY=SECRET_KEY_PLACEHOLDER
SHARED_STORAGE_PATH=/app/shared_data/
LOG_LEVEL=INFO
```

**Startup Command**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Health Check**:
```bash
curl -f http://localhost:8001/health/ || exit 1
```

**GPU Runtime Notes**:
- Base image must be NVIDIA CUDA runtime (not plain Python)
- Container requires `nvidia-docker` or Docker with GPU plugin
- CUDA libraries and cuDNN included in base image
- PyTorch installed with CUDA support during image build

---

### PostgreSQL Container

**Purpose**: Database for user data, request history, and metadata

**Image**: `postgres:15-alpine` (minimal, efficient)

**Port Mapping**:
- `5432:5432` - PostgreSQL server

**Volume Mounts**:
```
db_data:/var/lib/postgresql/data  ← Persistent database storage
```

**Environment Variables**:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=PASSWORD_PLACEHOLDER
POSTGRES_DB=mldb
PGDATA=/var/lib/postgresql/data
```

**Network**: `ml_network` (bridge)

**Health Check**:
```bash
pg_isready -U postgres || exit 1
```

**Initialization**:
- Database `mldb` created automatically
- Django migrations run on startup
- Initial schema created from Django models

**Backup Strategy**:
```bash
# Backup database
docker exec postgres pg_dump -U postgres mldb > backup.sql

# Restore database
docker exec -i postgres psql -U postgres mldb < backup.sql
```

---

## Networking

### Docker Network Configuration

**Type**: Bridge network named `ml_network`

**Service Discovery** (example placeholders):
- Services communicate by container name (DNS resolution)
- Example: Django connects to FastAPI at `http://[FASTAPI_SERVICE_NAME]:[FASTAPI_PORT]`
- PostgreSQL accessible at `postgresql://[DATABASE_HOST]:[DATABASE_PORT]/[DATABASE_NAME]`

**Communication Flows**:
```
Django Container                FastAPI Container
    ↓                                   ↓
   [ml_network]  ←─────────────────→  [ml_network]
    ↓                                   ↓
[8000:8000]                        [8001:8001]
   ↑                                    ↑
   │ User browser                       │ GPU Device
   └──────────────────────────────────→ (0)
```

**Port Exposure**:
- Django: 8000 (exposed to host)
- FastAPI: 8001 (exposed to host)
- PostgreSQL: 5432 (exposed to host for admin access)
- Internal communication: via Docker network (no exposure needed)

---

## Shared Storage Volume

### Volume Configuration

```yaml
volumes:
  shared_storage:
    driver: local
    driver_opts:
      type: tmpfs  # For development/testing
      # OR
      o: bind
      device: /path/to/shared  # For persistent storage
```

### Mount Points

| Service | Container Path | Purpose |
|---------|---|---|
| Django | `/data/shared/` | Read results and artifacts |
| FastAPI | `/app/shared_data/` | Read/write artifacts and models |

### Critical Requirement: Path Consistency

```
BOTH CONTAINERS MUST MOUNT THE SAME UNDERLYING VOLUME!

Django path:      /data/shared/
FastAPI path:     /app/shared_data/
Underlying volume: shared_storage

File written by FastAPI at:
  /app/shared_data/models/best.pt

Must be readable by Django at:
  /data/shared/models/best.pt
```

---

## Inference Result Path Translation: 4-Layer Coordinate System

### The Path Coordination Challenge

When FastAPI generates inference results and Django needs to serve them to browsers, files must pass through 4 different coordinate systems:

```
Layer 1: FastAPI Container Coordinate System
         /app/compute_service/outputs/run_001/
         └─ Where FastAPI writes results (source)

Layer 2: Host Filesystem (via bind mount)
         /home/user/outputs/run_001/
         └─ Persistent storage on host

Layer 3: Django Container Coordinate System  
         /app/web_service/outputs/run_001/
         └─ Where Django reads files

Layer 4: Public HTTP URL (served by web server)
         /media/deep_learning_outputs/outputs/run_001/
         └─ Where browsers access images
```

### Docker Compose Configuration for Path Coordination

```yaml
services:
  fastapi:
    volumes:
      # FastAPI sees host filesystem at /app/compute_service/outputs
      - /home/user/outputs:/app/compute_service/outputs  # Bind mount
  
  django:
    volumes:
      # Django sees SAME host filesystem at different container path
      - /home/user/outputs:/app/web_service/outputs  # Same source, different target!
      
  nginx:
    volumes:
      # Static file serving: Django volume → public URL
      - /home/user/outputs:/usr/share/nginx/html/deep_learning_outputs
    # /media/deep_learning_outputs → /usr/share/nginx/html/deep_learning_outputs
```

### Path Translation Logic Diagram

```
FastAPI generates: /app/compute_service/outputs/run_001/image.jpg
                   ↓
                   (bind mount mapping: /app/compute_service → /home/user)
                   ↓
Host filesystem:   /home/user/outputs/run_001/image.jpg
                   ↓
                   (Django reads via its mount: /home/user → /app/web_service)
                   ↓
Django accesses:   /app/web_service/outputs/run_001/image.jpg
                   ↓
                   (Django template renders)
                   ↓
Browser request:   /media/deep_learning_outputs/outputs/run_001/image.jpg
                   ↓
                   (nginx static file serving)
                   ↓
Server response:   Image bytes from /home/user/outputs/run_001/image.jpg
```

### Why 4 Layers Instead of Direct Access?

| Layer | Reason |
|-------|--------|
| Layer 1 (FastAPI container) | Source generation; isolated compute environment |
| Layer 2 (Host filesystem) | Persistent storage; survives container restart |
| Layer 3 (Django container) | Accessible to web app; supports static file serving |
| Layer 4 (Public URL) | Standard HTTP access; separates internal paths from URLs |

This separation enables:
- ✅ Service isolation (FastAPI and Django don't share filesystem)
- ✅ Independent scaling (replace containers without losing data)
- ✅ Security (internal paths not exposed to browsers)
- ✅ Flexibility (change storage backend in Phase 3 without affecting consumers)

### PathTranslator Implementation

For comprehensive documentation on path translation abstraction, see:
- [ADR-001: Path Translation Layer](./adr/ADR-001-path-translation-layer.md)
- [Inference Result Synchronization Layer](./18-inference-result-synchronization.md)

**Centralized path mapping**:

```python
# All coordinate system mappings in one place
translator = PathTranslator(settings)

# Convert FastAPI response to accessible URLs
fastapi_response = {
    "output_storage_path": "/app/compute_service/outputs/run_001/"
}

urls = translator.fastapi_response_to_urls(fastapi_response)
# Returns:
# {
#   'host_path': '/home/user/outputs/run_001/',
#   'volume_path': '/app/web_service/outputs/run_001/',
#   'image_url': '/media/deep_learning_outputs/outputs/run_001/image.jpg'
# }
```

---

### Artifact Structure

```
shared_storage/
├── models/
│   ├── best.pt                      # Current best model weights
│   ├── best_model_ref.json          # Metadata reference
│   ├── checkpoints/
│   │   ├── seed_42_epoch_50.pt
│   │   ├── seed_123_epoch_50.pt
│   │   └── seed_456_epoch_50.pt
│   └── backups/
│
├── training/
│   ├── run_001/
│   │   ├── summary.json             # Training summary
│   │   ├── metrics.csv              # Per-epoch metrics
│   │   └── logs.txt                 # Training logs
│   └── run_002/
│
├── ci_training/
│   ├── run_001/
│   │   ├── comparison.json
│   │   ├── decision.log
│   │   └── new_model_experimental.pt
│   └── run_002/
│
├── inference/
│   ├── job_001/
│   │   ├── output_manifest.json
│   │   ├── detections.csv
│   │   └── preview.png
│   └── job_002/
│
└── errors/
    ├── error_20260609_103000.log
    └── error_20260609_110500.log
```

---

## Django Configuration and Path Mapping

When Django YOLO configuration models (ProjectConfiguration, ClassSet, DatasetConfig) generate dataset YAML files, they must be accessible to both Django and FastAPI containers.

For comprehensive documentation, see [**docs/08-yolo-dataset-configuration-management.md**](./08-yolo-dataset-configuration-management.md).

### Generated YAML Files

```
shared_storage/
└── configs/
    ├── yaml_1717857600.yaml         # Generated by Django DatasetConfig model
    ├── yaml_1717857700.yaml         # Each timestamp corresponds to a configuration
    └── yaml_1717857800.yaml         # Used by training requests
```

### Container Path Mapping Example

```
Host System:
  /home/user/shared_configs/yaml_1717857600.yaml  (actual file)

Django Container:
  Volume mount: shared_storage:/data/shared
  Accessible at: /data/shared/configs/yaml_1717857600.yaml
  Django code: config_path = "/data/shared/configs/yaml_1717857600.yaml"

FastAPI Container:
  Volume mount: shared_storage:/app/shared_data
  Accessible at: /app/shared_data/configs/yaml_1717857600.yaml
  FastAPI code: config_path = "/app/shared_data/configs/yaml_1717857600.yaml"

Environment-Variable-Based Resolution:
  Django sets: CONFIG_BASE_PATH=/data/shared/configs/
  FastAPI sets: CONFIG_BASE_PATH=/app/shared_data/configs/
  Both read: config_filename = "yaml_1717857600.yaml"
  Both access same file via different mount paths
```

### Critical Integration Point

Django DatasetConfig must output file paths that FastAPI can read:

```
Django generates:
  dataset_yaml_path = "/data/shared/configs/yaml_1717857600.yaml"
  
Django returns to frontend:
  "dataset_yaml_path": "/shared_storage/configs/yaml_1717857600.yaml"
  (or environment-relative path)
  
FastAPI receives and adapts:
  # FastAPI container mapping
  fastapi_path = os.getenv('CONFIG_BASE_PATH') + "yaml_1717857600.yaml"
  fastapi_path = "/app/shared_data/configs/yaml_1717857600.yaml"
```

---

## Environment Variable Strategy

### Configuration Layers

1. **Docker Compose `.env` file** (development)
   - Override service defaults
   - Credentials and secrets
   - Never committed to Git

2. **Container environment variables**
   - Define in `docker-compose.yml`
   - Override from `.env` file
   - Available to application code

3. **Application configuration**
   - Read environment variables in code
   - Use sensible defaults for optional vars
   - Validate required variables on startup

### Example: FastAPI Environment

```python
# In FastAPI app initialization
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Required
    cuda_visible_devices: str  # "0" or "0,1,2"
    
    # Optional with defaults
    clearml_workspace: str = "projects/ai-orchestration"
    shared_storage_path: str = "/app/shared_data/"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

settings = Settings()
```

---

## Mount Risks and Mitigations

### Risk 1: Path Mismatch

**Problem**: Django reads from `/data/shared/` but FastAPI writes to `/app/shared_data/` pointing to different volumes

**Symptom**: FileNotFoundError when Django tries to read artifacts

**Prevention**:
- ✓ Double-check docker-compose volume mounts
- ✓ Test volume connectivity before running training
- ✓ Log actual mount paths on startup
- ✓ Include mount paths in health check

**Test**:
```bash
# Inside FastAPI container
docker exec fastapi ls -la /app/shared_data/

# Inside Django container
docker exec django ls -la /data/shared/

# Should show same files!
```

---

### Risk 2: Permission Denied

**Problem**: FastAPI cannot write to shared volume due to file permissions

**Symptom**: PermissionError when saving artifacts

**Prevention**:
- ✓ Ensure container user has write permissions (typically uid 1000)
- ✓ Volume should be owned by container user
- ✓ Use proper file permissions (0755 directories, 0644 files)
- ✓ Avoid root-owned volumes

**Test**:
```bash
# Check permissions in FastAPI container
docker exec fastapi stat /app/shared_data/
```

---

### Risk 3: Stale Data Caching

**Problem**: Django reads old version of file because OS/container caches the data

**Symptom**: Django sees old metrics even though FastAPI updated them

**Prevention**:
- ✓ Avoid aggressive caching of shared storage reads
- ✓ Implement cache invalidation based on timestamps
- ✓ Use `fsync()` after critical writes (Python: `file.flush()`)
- ✓ Consider adding cache headers in responses

---

### Risk 4: Concurrent Write Conflicts

**Problem**: Multiple FastAPI instances (future) writing to same artifact

**Symptom**: Corrupted JSON files or race conditions

**Prevention**:
- ✓ Write to temporary file first
- ✓ Atomic rename operation (mv tmp final)
- ✓ Implement file locking (future: use database instead)
- ✓ For now: ensure single FastAPI instance

---

## Health Check Recommendations

### Django Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**What to check**:
- ✓ HTTP endpoint responding
- ✓ Database connectivity
- ✓ Shared storage accessibility

---

### FastAPI Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**What to check**:
- ✓ HTTP endpoint responding
- ✓ CUDA device accessible
- ✓ PyTorch working
- ✓ ClearML configured (or optional)
- ✓ Shared storage mount accessible

---

### PostgreSQL Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

---

## Scaling Considerations (Future)

### Current Limitations
- Single Django container
- Single FastAPI container (with single GPU)
- Single PostgreSQL container

### Path to Multi-Container Deployment
1. Add load balancer (nginx)
2. Scale Django containers horizontally
3. Add job queue (Celery)
4. Scale FastAPI GPU workers
5. Move to Kubernetes orchestration

### Container Registry
- Build images: `docker build -t project_django:latest .`
- Tag for registry: `docker tag project_django:latest registry.example.com/project_django:latest`
- Push: `docker push registry.example.com/project_django:latest`

---

## Non-Production Emphasis

**This Docker Compose configuration is for architectural documentation and conceptual understanding only.**

**Production Considerations NOT included**:
- ❌ Multi-stage builds for optimization
- ❌ Security hardening (read-only filesystems, non-root users)
- ❌ Resource limits and requests
- ❌ Secrets management (Vault, AWS Secrets Manager)
- ❌ Logging aggregation (ELK, Splunk)
- ❌ Monitoring and alerting
- ❌ Container registry and image signing
- ❌ Network policies and segmentation
- ❌ Multi-region deployment
- ❌ Disaster recovery

**For production deployment**, refer to Kubernetes manifests, Terraform configurations, and organizational deployment standards.

---

**This Docker architecture enables local development and testing of the multi-service AI orchestration system while maintaining clear separation of concerns and enabling a future path to distributed deployment.**
