# ADR-001: Path Translation Layer for Multi-Container Artifact Synchronization

**Status**: Accepted (Implemented Phase 1)  
**Date**: June 2026  
**Deciders**: Architecture team  
**Affects**: Inference result synchronization, artifact management, Django-FastAPI integration

---

## Context

### Problem Statement

When FastAPI (running in Docker container) generates inference results and Django (in a different container) needs to access them, a coordinate system mismatch emerges:

- **FastAPI container sees**: `/app/compute_service/outputs/run_001/`
- **Host filesystem has**: `/host/outputs/run_001/`
- **Django container sees**: `/app/web_service/outputs/run_001/`
- **Users access via**: `/media/deep_learning_outputs/outputs/run_001/`

All four paths reference the **same physical files**, but Docker's container isolation creates a coordinate system translation challenge.

### Technical Context

Docker mounts in docker-compose.yml:

```yaml
services:
  fastapi:
    volumes:
      - /host/outputs:/app/compute_service/outputs  # Bind mount
  
  django:
    volumes:
      - /host/outputs:/app/web_service/outputs  # Different mount point!
      
  nginx:
    # Serves /app/web_service as /media/ via HTTP
```

**Key Issue**: FastAPI and Django mount the same host path at **different container paths**. This is intentional (service isolation) but creates path translation complexity.

---

## Decision

### Chosen Solution: Path Translation Layer Abstraction

**Design Pattern**: Centralized PathTranslator class that handles all 4-layer coordinate system mappings.

**Implementation**:

```python
class PathTranslator:
    """
    Centralized path mapping between 4 coordinate systems.
    Prevents scattered, hardcoded path translations throughout codebase.
    """
    
    def __init__(self, config):
        # 4 coordinate systems
        self.fastapi_container_path = "/app/compute_service/outputs"
        self.host_path = config['INFERENCE_HOST_PATH']  # /host/outputs
        self.volume_path = config['INFERENCE_VOLUME_PATH']  # /app/web_service/outputs
        self.media_url_prefix = config['MEDIA_URL_PREFIX']  # /media/deep_learning_outputs
    
    def container_to_host(self, container_path):
        """FastAPI container path → Host filesystem"""
        relative = container_path.replace(
            self.fastapi_container_path, ""
        ).lstrip('/')
        return os.path.join(self.host_path, relative)
    
    def host_to_volume(self, host_path):
        """Host filesystem → Django volume"""
        relative = os.path.relpath(host_path, self.host_path)
        return os.path.join(self.volume_path, relative)
    
    def volume_to_url(self, volume_path):
        """Django volume → Public HTTP URL"""
        relative = os.path.relpath(volume_path, self.volume_path)
        return f"{self.media_url_prefix}/outputs/{relative}"
    
    def fastapi_response_to_urls(self, fastapi_response):
        """End-to-end: FastAPI response → Final accessible URLs"""
        fastapi_path = fastapi_response['output_storage_path']
        host_path = self.container_to_host(fastapi_path)
        volume_path = self.host_to_volume(host_path)
        
        return {
            'host_path': host_path,
            'volume_path': volume_path,
            'image_url': self.volume_to_url(volume_path) + '/image.jpg',
            'metrics_url': self.volume_to_url(volume_path) + '/metrics.json',
            'csv_url': self.volume_to_url(volume_path) + '/detections.csv'
        }
```

### Rationale

**Why centralized abstraction instead of inline conversions?**

1. **Maintainability**: Single source of truth for path logic
2. **Testability**: Easy to unit test path conversions
3. **Configuration**: Paths defined in one place, not hardcoded everywhere
4. **Evolution**: Easy to add Layer 5 (e.g., S3 bucket paths in Phase 3)

**Why this specific layer ordering?**

- Layer 1 (FastAPI container): Source of truth where files are written
- Layer 2 (Host filesystem): Persistent storage, accessible via bind mount
- Layer 3 (Django volume): Accessible to Django container for serving
- Layer 4 (Public URL): Final destination for browser access

This sequence follows the natural data flow: generation → persistence → accessibility → rendering.

---

## Alternatives Considered

### Alternative 1: Embed Path Logic in Views

**Approach**: Handle path translation inline in Django inference view

**Pros**:
- Minimal initial code
- No abstraction layer

**Cons**:
- Path logic scattered across multiple files
- Difficult to test independently
- Hard to modify coordinate system mappings
- Error-prone when adding new layers (e.g., S3 in Phase 3)

**Decision**: Rejected. Violates DRY principle.

---

### Alternative 2: Use Django Settings Only

**Approach**: Store all paths in django.conf.settings

```python
# settings.py
INFERENCE_HOST_PATH = "/host/outputs"
INFERENCE_VOLUME_PATH = "/app/web_service/outputs"
MEDIA_URL_PREFIX = "/media/deep_learning_outputs"
```

Then use inline:

```python
# views.py
host_path = os.path.join(settings.INFERENCE_HOST_PATH, run_slug)
volume_path = os.path.join(settings.INFERENCE_VOLUME_PATH, run_slug)
```

**Pros**:
- Centralized configuration

**Cons**:
- Path logic still scattered in views
- No validation of coordinate system integrity
- Difficult to extend (e.g., path_translator.add_layer() for S3)
- Testing requires Django test client

**Decision**: Rejected. Settings alone don't provide abstraction needed.

---

### Alternative 3: Use Environment Variables Only

**Approach**: FastAPI returns full URLs, not paths

```json
{
  "output_storage_path": "s3://bucket/outputs/run_001/",
  "image_url": "https://domain.com/media/outputs/run_001/image.jpg"
}
```

**Pros**:
- No path translation needed
- Works across providers (local, S3, GCS)

**Cons**:
- Doesn't work for MVP (we need host filesystem access during development)
- Adds complexity to FastAPI response generation
- Doesn't solve Docker mount mismatch problem
- Requires external URL generation in FastAPI (violates SoC)

**Decision**: Rejected for MVP. Suitable for Phase 3 (distributed storage).

---

## Consequences

### Positive

✅ **Clarity**: Path coordinate systems explicitly documented in one place

✅ **Maintainability**: Changes to path logic affect single class, not multiple files

✅ **Testability**: PathTranslator can be unit tested independently of Django

✅ **Extensibility**: Easy to add new layers (e.g., S3, GCS, MinIO)

✅ **Reusability**: Can be used in multiple views/services

### Negative

⚠️ **Initial Complexity**: Requires additional abstraction layer (slight learning curve)

⚠️ **Configuration Dependency**: Requires correct settings configuration (risk of misconfiguration)

⚠️ **Performance**: Minimal (path translations are O(1) string operations)

### Mitigation for Negatives

**Configuration Risk**:
- Add validation in PathTranslator.__init__() to verify paths exist
- Document expected directory structure in README
- Use schema validation for config values

---

## Implementation Details

### File Synchronization Pattern (Paired with Path Translation)

PathTranslator works in conjunction with `wait_for_path()` function:

```python
def wait_for_path(path, timeout=300):
    """
    Wait for directory to stabilize (FastAPI finished writing).
    
    Returns True when:
    - Directory exists
    - Required files present (metrics.json, image_*.jpg)
    - File count unchanged for 3 consecutive polls
    
    Raises TimeoutError if not stable after timeout seconds.
    """
    # Implementation in docs/19-inference-result-synchronization.md
```

**Usage in Django view**:

```python
# Get paths from FastAPI response
translator = PathTranslator(settings)
paths = translator.fastapi_response_to_urls(fastapi_response)

# Wait for files to be complete
wait_for_path(paths['host_path'], timeout=300)

# Now safe to copy
shutil.copytree(
    paths['host_path'],
    paths['volume_path'],
    dirs_exist_ok=True
)

# Generate database record with final (volume) paths
run = DetectionRunRecord.objects.create(
    output_volume_path=paths['volume_path'],  # Use final layer only!
    image_url=paths['image_url'],
    metrics_url=paths['metrics_url'],
    csv_url=paths['csv_url']
)
```

### Configuration Example

```python
# settings.py
INFERENCE_CONFIG = {
    'INFERENCE_HOST_PATH': '/host/outputs',
    'INFERENCE_VOLUME_PATH': '/app/web_service/outputs',
    'MEDIA_URL_PREFIX': '/media/deep_learning_outputs',
}

# usage
translator = PathTranslator(settings.INFERENCE_CONFIG)
```

---

## Testing Strategy

### Unit Tests

```python
def test_container_to_host_conversion():
    config = {...}
    translator = PathTranslator(config)
    
    container_path = "/app/compute_service/outputs/run_001/"
    host_path = translator.container_to_host(container_path)
    
    assert host_path == "/host/outputs/run_001/"

def test_full_pipeline():
    config = {...}
    translator = PathTranslator(config)
    
    fastapi_response = {
        'output_storage_path': '/app/compute_service/outputs/run_001/'
    }
    
    urls = translator.fastapi_response_to_urls(fastapi_response)
    
    assert urls['host_path'].startswith('/host/')
    assert urls['volume_path'].startswith('/app/web_service/')
    assert urls['image_url'].startswith('/media/deep_learning_outputs/')
```

### Integration Tests

- Test with real Docker Compose setup
- Verify files accessible at each layer
- Test concurrent inference jobs (race condition safety)

### Manual Testing

1. Create inference job
2. Verify files appear in each path layer
3. Verify browser can access rendered images via public URL
4. Verify database records reference correct (final) paths

---

## Phase Evolution

### Phase 1 (Current)
- ✅ Single GPU, local filesystem only
- ✅ PathTranslator with 4 layers
- ✅ Handles host + container + volume + URL mappings

### Phase 2
- Consider: Object storage abstraction (Layer 5: S3, MinIO)
- Extend: `PathTranslator.add_object_storage_layer()`

### Phase 3
- Consider: Multi-node distributed storage
- Modify: PathTranslator for distributed filesystem paths

### Phase 4+
- Consider: CDN layer (Layer 6: CloudFront, Cloudflare)
- Extend: URL generation for different geographic regions

---

## Related ADRs

- **ADR-002** (Future): Async Job Queue Architecture
- **ADR-003** (Future): Distributed Model Registry

---

## References

**Documentation**:
- [Inference Result Synchronization Layer](../19-inference-result-synchronization.md)
- [Docker Runtime Architecture](../06-docker-runtime-architecture.md)

**Design Patterns**:
- Adapter Pattern: Convert between coordinate systems
- Facade Pattern: Hide path complexity behind simple interface

---

## Decision Record

| Aspect | Details |
|--------|---------|
| Date | June 2026 |
| Status | Accepted & Implemented |
| Risk Level | Low (well-understood problem, proven solution) |
| Complexity | Medium (requires careful configuration) |
| Testing | Unit + integration tests implemented |
| Documentation | Comprehensive (ADR + design docs + code comments) |

