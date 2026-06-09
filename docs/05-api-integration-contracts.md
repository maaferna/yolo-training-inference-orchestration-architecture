# API Integration Contracts

This document describes the API contracts between Django and FastAPI services. These are conceptual specifications - no actual endpoint code is included in this documentation repository.

## Design Principles

- **Stateless**: Each request is independent; services do not maintain session state
- **Async-Ready**: Response structure supports future async/polling patterns
- **Error Transparency**: Errors include actionable debugging information
- **Validation**: Request validation happens at API boundary
- **Schema Documentation**: Pydantic models define all payload structures

## Training Request Endpoint

### Endpoint Specification
```
Method: POST
URL: http://fastapi:8001/training
Content-Type: application/json
Response Codes:
  - 202 Accepted (job queued successfully)
  - 400 Bad Request (invalid parameters)
  - 422 Unprocessable Entity (validation error)
  - 500 Internal Server Error (server error)
  - 503 Service Unavailable (GPU unavailable)
```

### Request Payload

```json
{
  "dataset_yaml_path": "datasets/DATASET_PLACEHOLDER/data.yaml",
  "model_size": "s",
  "epochs": 100,
  "batch_size": 32,
  "learning_rate": 0.001,
  "device": 0,
  "num_seeds": 3,
  "imgsz": 640,
  "confidence_threshold": 0.25,
  "request_id": "req_unique_12345",
  "user_id": 42
}
```

### Request Payload Schema

| Field | Type | Required | Range/Notes |
|-------|------|----------|------------|
| `dataset_yaml_path` | string | Yes | Path to YOLO dataset.yaml in shared storage |
| `model_size` | enum | Yes | One of: `s`, `m`, `l`, `x` |
| `epochs` | integer | Yes | Range: 1-300 epochs typical |
| `batch_size` | integer | Yes | Range: 8-128 (depends on GPU memory) |
| `learning_rate` | float | Yes | Range: 0.0001-0.01 |
| `device` | integer | Yes | GPU device index (0, 1, 2...) |
| `num_seeds` | integer | Yes | Range: 1-5 (more seeds = more compute) |
| `imgsz` | integer | Yes | One of: 320, 416, 512, 640, 1024, 1536 |
| `confidence_threshold` | float | No | Default: 0.25, Range: 0.0-1.0 |
| `request_id` | string | Yes | Unique identifier for request tracing |
| `user_id` | integer | Yes | Django user ID for audit trail |

### Response Payload (Success)

```json
{
  "job_id": "train_req_12345",
  "status": "SUBMITTED",
  "message": "Training job submitted successfully",
  "estimated_duration_seconds": 3600,
  "polling_url": "/training/status/train_req_12345",
  "result_url": "/training/results/train_req_12345",
  "timestamp": "2026-06-09T10:30:00Z"
}
```

### Response Payload Schema

| Field | Type | Notes |
|-------|------|-------|
| `job_id` | string | Unique job identifier for tracking |
| `status` | enum | One of: `SUBMITTED`, `RUNNING`, `COMPLETED`, `FAILED` |
| `message` | string | Human-readable status message |
| `estimated_duration_seconds` | integer | Rough estimate for user expectations |
| `polling_url` | string | Endpoint to check job status |
| `result_url` | string | Endpoint to retrieve results (when complete) |
| `timestamp` | string | ISO 8601 timestamp of response |

### Error Response Payloads

#### Validation Error (400)
```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": {
    "batch_size": "Must be between 8 and 128",
    "epochs": "Must be at least 1"
  },
  "timestamp": "2026-06-09T10:30:00Z"
}
```

#### GPU Unavailable (503)
```json
{
  "error": true,
  "error_code": "RESOURCE_UNAVAILABLE",
  "message": "GPU device not available",
  "details": "Device 0 is busy or offline",
  "suggestion": "Try device 1 or retry in a few moments",
  "timestamp": "2026-06-09T10:30:00Z"
}
```

#### Server Error (500)
```json
{
  "error": true,
  "error_code": "INTERNAL_ERROR",
  "message": "Training failed unexpectedly",
  "details": "CUDA out of memory error",
  "request_id": "req_12345",
  "job_id": "train_req_12345",
  "timestamp": "2026-06-09T10:30:00Z"
}
```

---

## Continuous Improvement Training Endpoint

### Endpoint Specification
```
Method: POST
URL: http://fastapi:8001/ci-training
Content-Type: application/json
Response Codes: Same as training endpoint
```

### Request Payload

```json
{
  "new_dataset_yaml_path": "datasets/NEW_DATA_PLACEHOLDER/data.yaml",
  "baseline_metric_name": "mAP50",
  "baseline_metric_value": 0.85,
  "improvement_threshold": 0.01,
  "epochs": 50,
  "batch_size": 32,
  "request_id": "req_ci_12345",
  "user_id": 42
}
```

### Request Payload Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `new_dataset_yaml_path` | string | Yes | Path to new training data |
| `baseline_metric_name` | string | Yes | Typically `mAP50` or `mAP75` |
| `baseline_metric_value` | float | Yes | Previous best performance value |
| `improvement_threshold` | float | No | Default: 0.01 (1% improvement required) |
| `epochs` | integer | Yes | Incremental training epochs (usually fewer than initial) |
| `batch_size` | integer | Yes | Same as initial training typically |
| `request_id` | string | Yes | Unique identifier for tracing |
| `user_id` | integer | Yes | User who initiated request |

### Response Payload (Success)

```json
{
  "job_id": "ci_train_12345",
  "status": "COMPLETED",
  "message": "Continuous improvement training completed",
  "baseline_metric": {
    "name": "mAP50",
    "value": 0.85
  },
  "new_metric": {
    "name": "mAP50",
    "value": 0.87
  },
  "improvement": {
    "absolute": 0.02,
    "percentage": 2.35
  },
  "model_updated": true,
  "decision_reason": "Model improved - updating best model",
  "model_path": "/shared/models/best.pt",
  "result_url": "/ci-training/results/ci_train_12345",
  "timestamp": "2026-06-09T11:00:00Z"
}
```

### Response Payload Schema (CI Training)

| Field | Type | Notes |
|-------|------|-------|
| `model_updated` | boolean | Whether best model was replaced |
| `decision_reason` | string | Explanation of update decision |
| `improvement` | object | Absolute and percentage change metrics |
| Other fields | same | As training endpoint |

---

## SAHI Inference Endpoint

### Endpoint Specification
```
Method: POST
URL: http://fastapi:8001/inference
Content-Type: multipart/form-data or application/json (base64)
Response Codes: Same as training endpoint
```

### Request Payload (Option A: Base64 Encoding)

```json
{
  "image_base64": "iVBORw0KGgo...SUEVORK5CYII=",
  "confidence_threshold": 0.25,
  "nms_threshold": 0.5,
  "tile_size": 640,
  "tile_overlap": 0.5,
  "request_id": "req_inf_12345",
  "user_id": 42
}
```

### Request Payload Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `image_base64` | string | Yes | Base64-encoded image data (PNG or JPG) |
| `confidence_threshold` | float | No | Default: 0.25, Range: 0.0-1.0 |
| `nms_threshold` | float | No | Default: 0.5, Range: 0.3-0.9 |
| `tile_size` | integer | No | Default: 640 (YOLO standard input size) |
| `tile_overlap` | float | No | Default: 0.5 (50% overlap between tiles) |
| `request_id` | string | Yes | Request tracing identifier |
| `user_id` | integer | Yes | User who initiated inference |

### Response Payload (Success)

```json
{
  "job_id": "inf_12345",
  "status": "COMPLETED",
  "message": "Inference completed successfully",
  "image_shape": [3072, 4096, 3],
  "num_detections": 245,
  "inference_time_seconds": 12.5,
  "detections": [
    {
      "id": 0,
      "bbox": [100, 150, 200, 300],
      "confidence": 0.92,
      "class_id": 0,
      "class_name": "object_placeholder"
    },
    {
      "id": 1,
      "bbox": [400, 500, 550, 700],
      "confidence": 0.88,
      "class_id": 1,
      "class_name": "object_placeholder"
    }
  ],
  "manifest_path": "/shared/inference/job_12345/output_manifest.json",
  "preview_image_url": "/shared/inference/job_12345/preview.png",
  "result_url": "/inference/results/inf_12345",
  "timestamp": "2026-06-09T11:30:00Z"
}
```

### Detection Object Schema

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Detection index (0-based) |
| `bbox` | array | [x1, y1, x2, y2] in pixel coordinates |
| `confidence` | float | Detection confidence (0.0-1.0) |
| `class_id` | integer | YOLO class ID |
| `class_name` | string | Human-readable class name |

---

## Status Polling Endpoint

### Endpoint Specification
```
Method: GET
URL: http://fastapi:8001/status/{job_id}
Response Codes:
  - 200 OK (status retrieved)
  - 404 Not Found (job not found)
  - 500 Internal Server Error
```

### Response Payload (Job Still Running)

```json
{
  "job_id": "train_req_12345",
  "status": "RUNNING",
  "progress_percent": 45,
  "current_epoch": 45,
  "total_epochs": 100,
  "elapsed_seconds": 1800,
  "estimated_remaining_seconds": 2200,
  "current_step": "training",
  "message": "Training epoch 45/100",
  "timestamp": "2026-06-09T11:00:00Z"
}
```

### Response Payload (Job Completed)

```json
{
  "job_id": "train_req_12345",
  "status": "COMPLETED",
  "progress_percent": 100,
  "result": {
    "best_mAP50": 0.85,
    "best_model_path": "/shared/models/best.pt",
    "training_time_seconds": 3600,
    "num_epochs_run": 100
  },
  "result_url": "/training/results/train_req_12345",
  "timestamp": "2026-06-09T12:00:00Z"
}
```

### Response Payload (Job Failed)

```json
{
  "job_id": "train_req_12345",
  "status": "FAILED",
  "error": true,
  "error_code": "CUDA_OOM",
  "message": "Training failed: GPU memory exhausted",
  "failed_at_epoch": 45,
  "error_details": {
    "type": "RuntimeError",
    "message": "CUDA out of memory"
  },
  "timestamp": "2026-06-09T11:45:00Z"
}
```

---

## Error Response Structure

All error responses follow this standard structure:

```json
{
  "error": true,
  "error_code": "ERROR_CODE_PLACEHOLDER",
  "http_status": 500,
  "message": "Human-readable error message",
  "details": "Additional context or debugging information",
  "request_id": "req_12345",
  "job_id": "optional_if_available",
  "timestamp": "2026-06-09T10:30:00Z",
  "suggestion": "Optional: what to try next"
}
```

### Common Error Codes

| Code | HTTP Status | Meaning | User Action |
|------|-------------|---------|------------|
| `VALIDATION_ERROR` | 400 | Invalid input parameters | Fix parameters and retry |
| `RESOURCE_UNAVAILABLE` | 503 | GPU or other resource not available | Try another device or retry |
| `CUDA_OOM` | 507 | GPU memory exhausted | Reduce batch size/image size |
| `FILE_NOT_FOUND` | 500 | Artifact or dataset not found | Check path and retry |
| `MOUNT_ERROR` | 500 | Shared storage not accessible | Check Docker volume configuration |
| `CLEARML_ERROR` | 500 | ClearML service unavailable | Check ClearML credentials |
| `INTERNAL_ERROR` | 500 | Unexpected error | Contact support with job_id |
| `TIMEOUT` | 504 | Request timeout (if implemented) | Increase timeout or retry |

---

## Validation Requirements

### Training Endpoint Validation

**Input Validation**:
- ✓ `dataset_yaml_path` file must exist and be readable
- ✓ `model_size` must be one of: s, m, l, x
- ✓ `epochs` must be: 1 ≤ epochs ≤ 300
- ✓ `batch_size` must be: 8 ≤ batch_size ≤ 128
- ✓ `learning_rate` must be: 0.0001 ≤ lr ≤ 0.01
- ✓ `device` must be valid GPU index or -1 for CPU
- ✓ `num_seeds` must be: 1 ≤ seeds ≤ 5
- ✓ `imgsz` must be power of 2: 320, 416, 512, 640, 1024, 1536, 2048
- ✓ `request_id` must be non-empty string

**Business Logic Validation**:
- ✓ GPU must be available and have sufficient memory
- ✓ CUDA devices must be accessible
- ✓ ClearML workspace must be configured
- ✓ Dataset path must be accessible from FastAPI container

### Inference Endpoint Validation

**Input Validation**:
- ✓ `image_base64` must be valid base64 string
- ✓ Image must be decodable (PNG, JPG, BMP)
- ✓ Image size must be ≤ 8192×8192 pixels
- ✓ `confidence_threshold` must be: 0.0 ≤ threshold ≤ 1.0
- ✓ `nms_threshold` must be: 0.0 ≤ threshold ≤ 1.0
- ✓ `tile_size` must be power of 2: 320, 416, 512, 640, 1024

**Business Logic Validation**:
- ✓ Best model must exist and be loadable
- ✓ SAHI library must be available
- ✓ GPU must have sufficient memory for inference

---

## Contract Evolution

### Backward Compatibility Strategy

When evolving contracts:

1. **Add optional fields only** - don't remove required fields
2. **Version the API** - `/v1/training`, `/v2/training`, etc.
3. **Support old contract briefly** - during transition period
4. **Document deprecation** - clearly mark which fields are deprecated
5. **Provide migration guide** - help clients upgrade

### Example: Adding a Field

```json
{
  // v1 - existing fields
  "dataset_yaml_path": "...",
  "model_size": "s",
  
  // v2 - new optional field
  "enable_validation": true,  // default: true
  
  // v2 - future deprecation (keep supporting)
  "old_field": "value"  // deprecated: use new_field instead
}
```

---

**These API contracts define the interface between Django and FastAPI. Implementation details are in the private codebase.**
