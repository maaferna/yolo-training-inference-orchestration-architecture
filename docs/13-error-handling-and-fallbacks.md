# Error Handling and Fallbacks

This document describes error scenarios, recovery mechanisms, and mitigation strategies.

## Common Error Scenarios

### 1. Ultralytics train() Returns None

**Problem**: `model.train()` returns `None` instead of results object

**Cause**: 
- Internal Ultralytics error
- Corrupted settings.json cache
- CUDA initialization issue
- Version compatibility

**Detection**:
```python
results = model.train(...)
if results is None:
    print("ERROR: train() returned None")
```

**Recovery**:
```python
def train_with_none_fallback():
    """Handle train() returning None"""
    
    try:
        results = model.train(...)
        
        if results is None:
            print("Fallback: Using manual validation")
            results = model.val()
            
            # Extract metrics manually
            metrics = {
                'mAP50': results.box.map50,
                'completed_with_fallback': True
            }
    except Exception as e:
        print(f"Error: {e}")
        raise
```

### 2. CUDA Out of Memory (OOM)

**Problem**: GPU runs out of memory during training

**Error**:
```
RuntimeError: CUDA out of memory. 
Tried to allocate X.XXGiB. 
GPU has X.XXGiB free
```

**Cause**:
- Batch size too large for image size
- Model size too large
- Accumulated GPU cache not cleaned
- Dataset too large in memory

**Detection**:
```python
except RuntimeError as e:
    if "CUDA out of memory" in str(e):
        print("OOM detected")
        handle_oom()
    else:
        raise
```

**Recovery Strategy**:
```python
def handle_oom_recovery(batch_size, imgsz):
    """Recover from OOM by reducing resource usage"""
    
    # Option 1: Reduce batch size
    if batch_size > 8:
        print(f"Reducing batch size: {batch_size} → {batch_size // 2}")
        return train_with_reduced_batch(batch_size // 2)
    
    # Option 2: Reduce image size
    elif imgsz > 416:
        print(f"Reducing image size: {imgsz} → 512")
        return train_with_reduced_imgsz(512)
    
    # Option 3: Enable gradient accumulation
    elif not gradient_accumulation:
        print("Enabling gradient accumulation")
        return train_with_gradient_accumulation()
    
    # Option 4: Fail gracefully
    else:
        raise RuntimeError("Cannot fit training in GPU memory")
```

### 3. DDP (Distributed Data Parallel) Errors

**Problem**: Multi-GPU training fails with DDP

**Error**:
```
RuntimeError: NCCL operation failed with specific error
or
RuntimeError: Expected to have finished reduction in the prior iteration
```

**Cause**:
- GPU communication timeout
- Uneven batch distribution
- NCCL initialization failure
- Network issues (multi-node)

**Detection**:
```python
except RuntimeError as e:
    if "NCCL" in str(e) or "reduction" in str(e):
        print("DDP error detected")
        handle_ddp_error()
```

**Recovery**:
```python
def handle_ddp_error_fallback():
    """Fall back from DDP to single GPU"""
    
    print("DDP failed, falling back to single GPU DataParallel")
    
    # Use first GPU only
    results = model.train(
        device=0,  # Single GPU fallback
        batch=16   # Reduced batch size
    )
    
    return results
```

### 4. Corrupted Ultralytics settings.json

**Problem**: Ultralytics cache directory has corrupted settings

**Symptoms**:
- Persistent "settings corrupted" errors
- Some training runs fail repeatedly
- Errors inconsistent across runs

**Location**: `~/.config/Ultralytics/settings.json`

**Recovery**:
```python
import os
import shutil

def clear_ultralytics_cache():
    """Clear and recreate Ultralytics cache"""
    
    cache_dir = os.path.expanduser('~/.config/Ultralytics')
    settings_file = os.path.join(cache_dir, 'settings.json')
    
    if os.path.exists(settings_file):
        try:
            # Remove corrupted settings
            os.remove(settings_file)
            print(f"Removed corrupted settings: {settings_file}")
            
            # Recreate with defaults
            from ultralytics import YOLO
            _ = YOLO('yolov8s.pt')  # Force recreation
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            raise
```

### 5. Shared Storage Path Mismatch

**Problem**: FastAPI can't find files at expected path

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: 
'/app/shared_data/models/best.pt'
```

**Cause**:
- Docker volume not mounted correctly
- Path mismatch between services
- Volume not created

**Detection**:
```python
import os
from pathlib import Path

def verify_shared_storage():
    """Verify shared storage accessibility"""
    
    test_path = Path('/app/shared_data')
    
    if not test_path.exists():
        raise RuntimeError(
            f"Shared storage not accessible at {test_path}\n"
            f"Check docker-compose volume mounts"
        )
    
    # Try write
    try:
        test_file = test_path / 'test.txt'
        test_file.write_text('test')
        test_file.unlink()
    except Exception as e:
        raise RuntimeError(f"Cannot write to shared storage: {e}")
```

**Recovery**:
```python
def handle_mount_error():
    """Provide troubleshooting info for mount issues"""
    
    # Check mount from inside container
    import subprocess
    result = subprocess.run(['mount'], capture_output=True, text=True)
    
    # Check volume list
    docker_volumes = subprocess.run(
        ['docker', 'volume', 'ls'],
        capture_output=True, text=True
    )
    
    error_info = {
        'mounted_volumes': result.stdout,
        'docker_volumes': docker_volumes.stdout,
        'troubleshooting': [
            'Verify docker-compose.yml volume configuration',
            'Check volume created: docker volume ls',
            'Inspect volume: docker volume inspect shared_storage',
            'Recreate volume: docker volume rm shared_storage'
        ]
    }
    
    return error_info
```

### 6. Django to FastAPI 404 Errors

**Problem**: Django receives 404 from FastAPI endpoints

**Error**:
```
ConnectionError: 404 Not Found
URL: http://fastapi:8001/training
```

**Cause**:
- FastAPI service not running
- Service name mismatch in Docker network
- Port mismatch
- Endpoint not defined

**Detection**:
```python
import requests

def check_fastapi_connectivity():
    """Check if FastAPI service is reachable"""
    
    try:
        response = requests.get('http://fastapi:8001/health/', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Cannot reach FastAPI: {e}")
        return False
```

**Recovery**:
```python
def handle_fastapi_connection_error(retry_count=3):
    """Handle and recover from FastAPI connection errors"""
    
    import time
    
    for attempt in range(retry_count):
        try:
            response = requests.post('http://fastapi:8001/training', ...)
            return response
        except ConnectionError:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
            time.sleep(wait_time)
    
    raise RuntimeError(
        "FastAPI service unreachable after retries. "
        "Check: docker ps, docker logs fastapi"
    )
```

---

## Partial Error Handling

### Seed N Fails, Continue Training

```python
def train_multiple_seeds_with_partial_failure():
    """Continue training if one seed fails"""
    
    results = {}
    failed_seeds = []
    
    for seed in [42, 123, 456]:
        try:
            result = train_single_seed(seed)
            results[seed] = result
        except Exception as e:
            print(f"Seed {seed} failed: {e}")
            failed_seeds.append(seed)
            # Continue with next seed
    
    if len(results) == 0:
        raise RuntimeError("All seeds failed")
    
    # Select best from successful seeds
    best_seed = max(results.keys(), 
                    key=lambda s: results[s]['mAP50'])
    
    return {
        'best': results[best_seed],
        'failed_seeds': failed_seeds,
        'completed_seeds': len(results)
    }
```

---

## Error Response to Django

### Standard Error Response

```python
def create_error_response(error_type, error_message, job_id=None):
    """Create standardized error response"""
    
    from datetime import datetime
    
    return {
        'error': True,
        'error_code': error_type,
        'http_status': error_code_to_status(error_type),
        'message': error_message,
        'job_id': job_id,
        'timestamp': datetime.now().isoformat(),
        'details': {
            'attempted_recovery': True,
            'recovery_result': 'check_logs'
        }
    }
```

### Error Codes

| Error Code | HTTP Status | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `RESOURCE_UNAVAILABLE` | 503 | GPU/storage unavailable |
| `CUDA_OOM` | 507 | Out of memory |
| `FILE_NOT_FOUND` | 500 | Artifact missing |
| `MOUNT_ERROR` | 500 | Storage mount issue |
| `DDP_ERROR` | 500 | Multi-GPU error |
| `TIMEOUT` | 504 | Timeout |
| `INTERNAL_ERROR` | 500 | Unexpected |

---

## Logging and Debugging

### Comprehensive Error Logging

```python
import traceback
from datetime import datetime

def log_error_comprehensively(error, context):
    """Log error with full context"""
    
    error_log = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': {
            'job_id': context.get('job_id'),
            'user_id': context.get('user_id'),
            'operation': context.get('operation'),
            'seed': context.get('seed'),
            'gpu_device': context.get('gpu_device'),
            'model_size': context.get('model_size')
        }
    }
    
    # Save to local file
    import json
    error_file = f'/shared_storage/errors/error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    with open(error_file, 'w') as f:
        json.dump(error_log, f, indent=2)
    
    # Also log to ClearML if task available
    if 'task' in context:
        task = context['task']
        task.upload_artifact(
            name="error_log",
            artifact_object=error_log
        )
    
    return error_file
```

---

## Limited Retry Logic

### Current: No Automatic Retry

```python
# Current implementation
try:
    results = model.train(...)
except Exception as e:
    # Return error to Django
    return error_response(e)

# Django must implement user-initiated retry
```

### Recommended: Automatic Retry with Backoff

```python
import time
import random

def retry_with_exponential_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                # All retries exhausted
                raise
```

---

## No Formal Health Checks

### Current: No Built-in Health Checks

```
# Services are assumed healthy
# No periodic verification
# Issues detected only when requests fail
```

### Recommended: Health Check Endpoints

```python
@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    
    import torch
    
    checks = {
        'service': 'ok',
        'cuda_available': torch.cuda.is_available(),
        'shared_storage': check_storage_accessible(),
        'database': check_database_connection(),
        'clearml': check_clearml_connection()
    }
    
    all_healthy = all(v == 'ok' or v == True for v in checks.values())
    
    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks
    }
```

---

## Summary

Error handling in current system:

✓ **Handling Present**:
- OOM detection and recovery (batch size reduction)
- Partial seed failure (continue with others)
- Train() None fallback (manual validation)
- Error logging to local storage
- ClearML integration for error tracking

⚠️ **Limited**:
- No automatic retry with backoff
- No formal health checks
- No circuit breaker pattern
- No rate limiting

❌ **Not Implemented**:
- Formal retry logic
- Distributed tracing
- Monitoring and alerting
- Advanced observability

**Evolution Path**: Phase 1 focus on reliability (atomic writes, health checks), Phase 2 add comprehensive observability.
