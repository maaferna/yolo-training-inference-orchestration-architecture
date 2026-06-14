# Docker Runtime Architecture

This document describes the containerized deployment architecture and runtime configuration for the agricultural computer vision platform.

---

## 1. Problem Context

A containerized computer vision platform was being developed and stabilized for processing agricultural images through object detection models. The platform was built on Django and FastAPI, deployed in Docker containers with GPU support.

### Key Challenges Addressed

* Integration between web backend and inference services
* GPU deployment within Docker containers
* Management of agricultural image projects and orthomosaics
* Execution of inference on large-scale images using SAHI
* System observability and monitoring through logging
* Troubleshooting deployment and operational issues in containers

### Technical Focus Areas

* Multi-container orchestration
* GPU/CUDA runtime configuration
* Shared storage and artifact management
* Django logging in Docker environments
* Real-time observability for containerized services

---

## 2. Component Overview

The system consists of multiple specialized modules:

### Image Inference Module
- Executes object detection on agricultural images using YOLO and SAHI
- Handles high-resolution inference through tiling and result consolidation

### Orthomosaic Processing Module
- Enables inference on large-resolution images through tile segmentation
- Consolidates results from individual tiles

### Project Management Module
- Administers image processing projects
- Manages image storage, inference configurations, and result persistence

### Django Backend
- Data management and web interface
- REST APIs for system integration
- Result persistence and project administration

### Inference Service
- Decoupled execution of computer vision models
- Handles inference orchestration independent of backend

### Docker Infrastructure
- Orchestrates Backend, Database, Frontend, Inference Services, and auxiliary CV tools

---

## 3. Technologies Employed

| Layer | Technologies |
|-------|---|
| **Backend** | Python, Django, Django REST Framework |
| **Inference** | FastAPI, PyTorch, YOLO, SAHI |
| **Frontend** | React, JavaScript |
| **Database** | PostgreSQL |
| **Infrastructure** | Docker, Docker Compose |
| **GPU Computing** | CUDA, NVIDIA Container Runtime |
| **CV Libraries** | OpenCV, Ultralytics, SAHI |
| **Complementary Tools** | CVAT, FiftyOne, Nuclio, WebODM |

---

## 4. Docker Compose Overview

The system runs as a multi-container application using Docker Compose for local development and testing.

### System Architecture Diagram

```
                 +------------------+
                 |     Frontend     |
                 |      React       |
                 +--------+---------+
                          |
                          |
                          v
                 +------------------+
                 |     Django       |
                 |     Backend      |
                 +----+--------+----+
                      |        |
                      |        |
                      v        v
             +------------+   +----------------+
             | PostgreSQL |   | File Storage   |
             +------------+   +----------------+
                                   |
                                   |
                                   v
                         +-------------------+
                         | Inference Service |
                         | FastAPI + YOLO    |
                         | SAHI + PyTorch    |
                         +---------+---------+
                                   |
                                   |
                                   v
                               GPU Layer
                          CUDA / NVIDIA
```

### Main Data Flow

**Inference Pipeline**:
1. User accesses frontend and loads agricultural images or selects existing project
2. Frontend sends inference configuration to Django backend (model, confidence threshold, image size, slice size, overlap ratio)
3. Django registers the execution and persists configuration to PostgreSQL
4. FastAPI Inference Service receives image and parameters
5. SAHI partitions large images into tiles
6. YOLO executes detection on each tile
7. SAHI merges detection results
8. Results are stored in database and filesystem
9. Backend exposes results through API to frontend

### Component Responsibilities

| Component | Responsibility |
|-----------|---|
| **Frontend (React)** | User interface, image upload, configuration, result visualization |
| **Django Backend** | API management, data persistence, project administration, inference orchestration |
| **PostgreSQL** | Project metadata, execution history, detection results, configuration storage |
| **File Storage** | Original images, generated tiles, inference results |
| **FastAPI Service** | Model inference execution, SAHI tile processing, GPU management |


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

---

## 5. Django Real-Time Logging Configuration

### Problem Addressed

When Django was deployed within Docker Compose, logs were not visible in real-time despite the backend responding correctly to HTTP requests.

### Root Causes

* **Output Buffering**: Python processes executed via Conda/Mamba buffered stdout/stderr
* **Process Wrapping**: Using `mamba run` or bash wrappers without `exec` prevented log capture
* **Lost Observability**: Inability to diagnose issues when server responded but logs were invisible
* **Infrastructure Uncertainty**: Difficulty confirming ports, active processes, and correct server execution

### Solution Implemented

#### Entrypoint Configuration

The startup script was modified to:
- Disable Python output buffering with `PYTHONUNBUFFERED=1`
- Set proper encoding with `PYTHONIOENCODING=utf-8`
- Execute Django using `exec` to connect stdout/stderr directly to Docker

#### Environment Variables

```env
PYTHONUNBUFFERED=1          # Disable output buffering
PYTHONIOENCODING=utf-8      # Proper character encoding
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
```

#### Logging Configuration

Loggers configured for:
* Django server startup and lifecycle events
* HTTP request/response details
* SQL query visibility in debug mode
* Application-level errors and warnings

#### Docker Log Capture

Real-time logs now visible via:
```bash
docker logs <container_id> -f
docker-compose logs -f django
docker-compose logs -f fastapi
```

### Impact

* ✅ HTTP requests visible in real-time
* ✅ SQL queries traceable during development
* ✅ Server initialization events observable
* ✅ Application errors immediately detectable
* ✅ Operational troubleshooting significantly faster

---

## 6. Container Startup Flow

### Step 1: Container Initialization

When Docker Compose starts the backend:

```bash
docker-compose up backend
```

The entrypoint performs:
1. Verification of mounted volumes
2. Configuration of environment variables (unbuffered output, encoding)
3. Execution of Django migrations
4. Initialization of application components
5. Logging system configuration

### Step 2: Backend Initialization

During startup:
* Django loads configuration
* PostgreSQL connection validated
* Installed applications initialized
* Models registered
* Logging system configured

### Step 3: Vision Library Initialization

If configured:
* PyTorch loaded and GPU detected
* FAISS indices initialized (if used)
* CUDA resources detected and allocated

### Step 4: Server Startup

Finally:
* Django application starts on port 8000 (internal)
* Docker exposes configured host port
* Log capture activated for real-time monitoring

### Step 5: Validation

Checks performed:
* Volume mount existence and permissions
* Django project availability
* PostgreSQL reachability
* Migration status
* GPU availability (FastAPI)
* Configuration consistency

### Step 6: Data Persistence

**PostgreSQL**:
- Users, projects, configurations
- Inference execution history
- Detection results and metadata
- Image metadata

**File System**:
- Original images
- Generated tiles
- Inference results
- Static files

---

## 7. Architectural Patterns Detected

### Microservices Architecture
Separation between management backend (Django) and specialized inference service (FastAPI)

### API Integration
Component communication via REST APIs

### Batch Processing
Multiple images and orthomosaics processed in pipeline

### GPU Computing
GPU acceleration for inference execution

### Data Persistence
Multi-layer storage for configurations, projects, and results

### Containerized Deployment
All services deployed and managed via Docker

### Modular Architecture
Clear separation between management, inference, storage, and visualization

### Computer Vision Pipeline
Complete pipeline: ingestion → segmentation → inference → consolidation → persistence

---

## 8. Technical Complexity Assessment

### Classification: **High**

### Justification

The system integrates multiple advanced technologies:

* **Frontend**: React-based user interface
* **Backend**: Django with DRF for API management
* **Inference**: FastAPI with YOLO and SAHI
* **Database**: PostgreSQL for persistence
* **Infrastructure**: Docker Compose with GPU support
* **Logging**: Real-time observability in containerized environment
* **Integrations**: Multiple CV tools (CVAT, FiftyOne, Nuclio, WebODM)

This corresponds to responsibilities of:
- Machine Learning Engineer
- AI Platform Engineer
- Computer Vision Engineer
- Backend Architect
- MLOps Engineer

---

## 9. Architectural Risks and Mitigations

### Risk: Tight Coupling

**Issue**: Django maintains direct knowledge of inference service configuration

**Mitigation**: Use environment variables and service discovery patterns

### Risk: Scalability Limitation

**Issue**: Current setup designed for single instances

**Mitigation**: Add load balancer, task queue, horizontal scaling layer

### Risk: GPU Resource Contention

**Issue**: Multiple concurrent inferences compete for VRAM and CUDA

**Mitigation**: Implement request queuing and rate limiting

### Risk: Single Point of Failure

**Issue**: Backend failure impacts entire system

**Mitigation**: Implement redundancy and failover mechanisms

### Risk: Storage Growth

**Issue**: Ortomosaics and tiles generate large data volumes

**Mitigation**: Implement distributed storage and cleanup policies

### Risk: Long-Running Requests

**Issue**: Inference on large images may timeout

**Mitigation**: Implement async processing and job queues

### Risk: Logging Overhead

**Issue**: Excessive SQL logging impacts performance

**Mitigation**: Disable verbose logging in production

---

## 10. System Maturity Level

### Classification: **Scalable System**

### Characteristics Present

✅ Modular architecture with clear separation of concerns  
✅ Backend decoupled from inference service  
✅ Complete containerization  
✅ GPU support and acceleration  
✅ Dataset management integration  
✅ Full computer vision pipeline  
✅ Integration with specialized CV tools  

### Characteristics Not Yet Present

❌ Task queue or message broker  
❌ Distributed storage systems  
❌ Event-driven architecture  
❌ Horizontal auto-scaling  
❌ Workflow orchestration  
❌ Multi-region deployment  

This represents an advanced scalable system appropriate for medium-scale production use, with clear pathways for evolution toward fully distributed architecture.


