# System Flows

This document describes the complete request/response flows, error handling flows, and data movement through the system.

## Training Request Flow

### Happy Path: User Submits Training Job

```
┌─ DJANGO LAYER ─────────────────────────────────────────┐
│                                                          │
│  1. User fills training form (UI)                       │
│     - Dataset YAML path                                 │
│     - Model size (s, m, l, x)                          │
│     - Epochs, batch size, device info                  │
│                                                          │
│  2. Django validates input (format, ranges)             │
│     ├─ Validation fails? → Return 400                  │
│     └─ Validation passes ↓                             │
│                                                          │
│  3. Create Request object in PostgreSQL                 │
│     - Request ID: unique UUID                          │
│     - Status: PENDING                                  │
│     - Created timestamp                                │
│                                                          │
│  4. Return 202 Accepted to user                         │
│     - Job ID for polling                               │
└────────────────────┬──────────────────────────────────┘
                     │ HTTP POST /training
                     │ (JSON payload)
                     ↓
┌─ FASTAPI LAYER ────────────────────────────────────────┐
│                                                          │
│  5. Receive and validate request                        │
│     ├─ Parse JSON with Pydantic                        │
│     ├─ Validate ranges and paths                       │
│     ├─ Check CUDA availability                         │
│     └─ Return 422 if invalid                           │
│                                                          │
│  6. Initialize ClearML task                            │
│     - project_name: PROJECT_NAME_PLACEHOLDER           │
│     - task_name: training_TIMESTAMP                    │
│     - Connect hyperparameters                          │
│                                                          │
│  7. Load base YOLO model                               │
│     - yolov8s/m/l/x from Ultralytics                  │
│     - Move to GPU (device='0')                         │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ TRAINING ENGINE ──────────────────────────────────────┐
│                                                          │
│  8. Execute multi-seed training loop                   │
│     for seed in [42, 123, 456]:                        │
│       8a. Set random seed                              │
│       8b. YOLO.train(                                  │
│             data=dataset_yaml,                         │
│             epochs=epochs,                             │
│             batch=batch_size,                          │
│             device='0'                                 │
│           )                                            │
│       8c. results = trainer.results                    │
│       8d. Log metrics to ClearML                       │
│       8e. Store checkpoint: runs/seed_42/              │
│       8f. Cleanup CUDA memory                          │
│     end for                                            │
│                                                          │
│  9. Validation fallback (if train() returns None)      │
│     - Run manual val()                                 │
│     - Extract metrics                                 │
│                                                          │
│  10. Select best model                                 │
│      - Compare mAP50 across seeds                      │
│      - Copy best model to shared storage               │
│      - Generate best_model_ref.json:                   │
│        {                                               │
│          "model_path": "/shared/models/best.pt",       │
│          "mAP50": 0.85,                                │
│          "seed": 42,                                   │
│          "timestamp": "2026-06-09T10:30:00Z"           │
│        }                                               │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ SHARED STORAGE ───────────────────────────────────────┐
│                                                          │
│  11. Artifacts persisted:                              │
│      /shared_storage/models/best.pt                    │
│      /shared_storage/models/best_model_ref.json        │
│      /shared_storage/training/RUN_001/summary.json     │
│      /shared_storage/training/RUN_001/metrics.csv      │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓ ClearML task completion
                     │
┌─ FASTAPI RESPONSE ─────────────────────────────────────┐
│                                                          │
│  12. Log task completion to ClearML                    │
│  13. Prepare response:                                 │
│      {                                                 │
│        "job_id": "req_12345",                          │
│        "status": "COMPLETED",                          │
│        "best_model_path": "/shared/models/best.pt",    │
│        "best_mAP50": 0.85,                             │
│        "artifacts_url": "/shared/training/RUN_001/"    │
│      }                                                 │
│  14. Return 200 OK                                     │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓ HTTP Response (JSON)
                     │
┌─ DJANGO LAYER ─────────────────────────────────────────┐
│                                                          │
│  15. Update Request object                             │
│      - Status: COMPLETED                               │
│      - Best model path                                 │
│      - Artifacts reference                            │
│      - Completed timestamp                            │
│                                                          │
│  16. Display results to user                           │
│      - Best model metrics                             │
│      - Link to artifacts                              │
│      - Training time                                  │
│                                                          │
└────────────────────────────────────────────────────────┘
```

### Error Scenarios

#### Scenario A: CUDA OOM During Training

```
FastAPI:
  Try: trainer.train(...)
  Catch: RuntimeError("CUDA out of memory")
    ↓
  Log error to ClearML
  ↓
  CUDA recovery:
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
  ↓
  Attempt retry with reduced parameters:
    - Reduce batch size (32 → 16)
    - Reduce image size (640 → 416)
  ↓
  If retry succeeds:
    Continue normally
  ↓
  If retry fails:
    Return error response to Django
    
Django:
  Receive 500 error with message: "GPU memory exhausted"
  User can retry with smaller parameters
```

#### Scenario B: Ultralytics train() Returns None

```
FastAPI:
  results = model.train(...)
  if results is None:
    ↓
    Fallback: Manual validation
      results = model.val()
    ↓
    Extract metrics from results manually
    ↓
    Continue normally
```

#### Scenario C: Shared Storage Path Mismatch

```
FastAPI:
  Try: open('/app/shared_data/best.pt')
  Catch: FileNotFoundError
    ↓
  Log critical error to ClearML
  ↓
  Return error response:
    {
      "error": "Shared storage not mounted correctly",
      "expected_path": "/app/shared_data/",
      "hint": "Check docker-compose volume mounts"
    }
    
Django:
  Receive error response
  Display message to user with troubleshooting steps
```

---

## Continuous Improvement Training Flow

```
┌─ CI TRAINING INITIATION ───────────────────────────────┐
│                                                          │
│  1. User submits CI training request                   │
│     - New training data reference                      │
│     - Baseline comparison metric (e.g., mAP50)         │
│     - Optional: override threshold for acceptance      │
│                                                          │
│  2. Django validates and creates CI_Request            │
│                                                          │
│  3. FastAPI receives /ci-training request              │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ CI TRAINING EXECUTION ────────────────────────────────┐
│                                                          │
│  4. Load previous best model                           │
│     best_model_ref = load_json(                         │
│       '/shared_storage/models/best_model_ref.json'      │
│     )                                                   │
│     model_path = best_model_ref['model_path']           │
│     historical_mAP50 = best_model_ref['mAP50']          │
│                                                          │
│  5. Load model from disk                               │
│     model = YOLO(model_path)                           │
│                                                          │
│  6. Run incremental training                           │
│     results = model.train(                             │
│       data=new_dataset_yaml,                           │
│       epochs=incremental_epochs,                       │
│       device='0'                                       │
│     )                                                  │
│     new_mAP50 = results.box.map50                       │
│                                                          │
│  7. Baseline Comparison                                │
│     improvement_percent = (                            │
│       (new_mAP50 - historical_mAP50)                    │
│       / historical_mAP50 * 100                         │
│     )                                                  │
│                                                          │
│  8. Decision Logic                                     │
│     if new_mAP50 > historical_mAP50:                    │
│       (update best model - see next section)           │
│     else:                                              │
│       (keep existing model - see below)                │
│                                                          │
└────────────────────────────────────────────────────────┘
```

### Decision A: Model Improved → Update Best Model

```
┌─ UPDATE BEST MODEL ────────────────────────────────────┐
│                                                          │
│  9. Copy new model to registry                         │
│     shutil.copy(                                       │
│       'runs/detect/train/weights/best.pt',             │
│       '/shared_storage/models/best.pt'                 │
│     )                                                  │
│                                                          │
│  10. Update reference file                             │
│      best_model_ref.json:                              │
│      {                                                 │
│        "model_path": "/shared_storage/models/best.pt", │
│        "mAP50": 0.87,  # improved from 0.85            │
│        "previous_mAP50": 0.85,                         │
│        "improvement": "0.02",                          │
│        "timestamp": "2026-06-09T11:00:00Z",            │
│        "training_type": "CI",                          │
│        "data_source": "new_dataset_placeholder"        │
│      }                                                 │
│                                                          │
│  11. Archive previous best (optional)                  │
│      /shared_storage/models/best_v1_backup.pt          │
│                                                          │
│  12. Log to ClearML                                    │
│      task.report_text(                                 │
│        "Model improved: 0.85 → 0.87 mAP50"             │
│      )                                                 │
│                                                          │
│  13. Return success to Django                          │
│                                                          │
└────────────────────────────────────────────────────────┘
```

### Decision B: Model Degraded → Keep Existing

```
┌─ PRESERVE EXISTING MODEL ──────────────────────────────┐
│                                                          │
│  9. DO NOT update best_model_ref.json                  │
│     (Keep historical version)                          │
│                                                          │
│  10. Store CI training artifacts separately            │
│      /shared_storage/ci_training/run_001/              │
│      ├── new_model.pt (experimental, not best)         │
│      ├── metrics.json (0.83 mAP50)                     │
│      └── decision.log                                 │
│           "Degradation detected: 0.85 → 0.83"          │
│           "Keeping previous best model"                │
│                                                          │
│  11. Log to ClearML                                    │
│      task.report_text(                                 │
│        "Model degradation detected. " +                │
│        "Keeping current best: 0.85 mAP50"              │
│      )                                                 │
│                                                          │
│  12. Return conservative response to Django            │
│                                                          │
└────────────────────────────────────────────────────────┘
```

### Risk: Race Condition with File-Based Registry

```
Timeline of RACE CONDITION:

Time  Thread 1 (CI Training A)    Thread 2 (CI Training B)
────  ─────────────────────      ─────────────────────
T1    Read best_model_ref.json     (waiting)
      mAP50 = 0.85
T2                                 Read best_model_ref.json
                                   mAP50 = 0.85
T3    Training completes           (still training)
      new_mAP50_A = 0.86
T4                                 Training completes
                                   new_mAP50_B = 0.84
T5    Write best_model_ref.json    (waiting)
      Update to 0.86
T6                                 Write best_model_ref.json
                                   Update to 0.84  ← OVERWRITES!
      
RESULT: Best model degraded to 0.84, should be 0.86

PREVENTION (future):
  - Implement atomic file writes with tmp file + rename
  - Use database for transactional updates
  - Implement file locking mechanism
  - Use message queue for CI training job serialization
```

---

## SAHI Inference Flow

```
┌─ INFERENCE REQUEST ────────────────────────────────────┐
│                                                          │
│  1. User uploads image (PNG, JPG, etc.)                │
│     - Image size: e.g., 4096 × 3072 pixels             │
│     - Size: < 100 MB typical                           │
│                                                          │
│  2. Django validates and submits to FastAPI            │
│     POST /inference                                    │
│     {                                                  │
│       "image_base64": "iVBORw0KGgo...",                │
│       "confidence_threshold": 0.25,                    │
│       "nms_threshold": 0.5,                            │
│       "tile_overlap": 0.5                              │
│     }                                                  │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ SAHI INFERENCE ENGINE ────────────────────────────────┐
│                                                          │
│  3. Decode and validate image                          │
│     image = cv2.imdecode(...)  # or PIL               │
│     shape = image.shape  # (H, W, C)                   │
│                                                          │
│  4. Load best model                                    │
│     model = YOLO('/shared_storage/models/best.pt')     │
│                                                          │
│  5. Initialize SAHI Detector                           │
│     detector = Detector(                               │
│       model_type="yolov8",                             │
│       model_path="/shared_storage/models/best.pt",     │
│       confidence=0.25,                                 │
│       device="cuda:0"                                  │
│     )                                                  │
│                                                          │
│  6. Run SAHI inference (automatic tiling)              │
│     results = detector.predict(                        │
│       image,                                           │
│       slice_height=640,                                │
│       slice_width=640,                                 │
│       overlap_height_ratio=0.5,                        │
│       overlap_width_ratio=0.5                          │
│     )                                                  │
│                                                          │
│     [Internally: SAHI handles]                         │
│     - Image tiling calculation                         │
│     - Per-tile YOLO inference                          │
│     - Coordinate transformation                        │
│     - Detection merging across tiles                   │
│     - NMS application                                 │
│                                                          │
│  7. Extract detections                                 │
│     detections = results.object_prediction_list        │
│     for det in detections:                             │
│       x1, y1, x2, y2 = det.bbox.to_xyxy()              │
│       confidence = det.score.value                     │
│       class_id = det.category.id                       │
│       class_name = det.category.name                   │
│                                                          │
│  8. Generate output manifest                           │
│     manifest = {                                       │
│       "timestamp": "2026-06-09T11:30:00Z",             │
│       "image_shape": [3072, 4096, 3],                  │
│       "tile_config": {                                 │
│         "tile_size": 640,                              │
│         "overlap": 0.5                                 │
│       },                                               │
│       "num_detections": 245,                           │
│       "detections": [                                  │
│         {                                              │
│           "bbox": [x1, y1, x2, y2],                    │
│           "confidence": ILLUSTRATIVE_METRIC_VALUE,     │
│           "class_id": 0,                               │
│           "class_name": "object"                       │
│         },                                             │
│         ...                                            │
│       ]                                                │
│     }                                                  │
│                                                          │
│  9. Store results to shared storage                    │
│     /shared_storage/inference/job_12345/               │
│     ├── output_manifest.json                          │
│     ├── preview.png (optional visualization)           │
│     └── detections.csv (tabular format)                │
│                                                          │
│  10. Return response to Django                         │
│       {                                                │
│         "job_id": "inf_12345",                         │
│         "num_detections": 245,                         │
│         "manifest_path": "/shared/inference/job_12345" │
│       }                                                │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ DJANGO RESULTS DISPLAY ───────────────────────────────┐
│                                                          │
│  11. Read manifest from shared storage                 │
│      manifest = load_json(                             │
│        '/data/shared/inference/job_12345/manifest.json'│
│      )                                                 │
│                                                          │
│  12. Display results to user                           │
│      - Number of detections: 245                       │
│      - Detection table (class, confidence, bbox)       │
│      - Link to preview image                           │
│      - Download manifest option                        │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

## Django Configuration to Training Flow

This flow describes how Django configuration models (ProjectConfiguration, ClassSet, DatasetConfig) coordinate to prepare YOLO training.

For comprehensive documentation, see [**docs/08-yolo-dataset-configuration-management.md**](./08-yolo-dataset-configuration-management.md).

```
┌─ DJANGO ADMIN UI ──────────────────────────────────────┐
│                                                          │
│  1. Administrator creates project                      │
│     - Project name: ILLUSTRATIVE_PROJECT_NAME          │
│     - Dataset root: /data/ILLUSTRATIVE_DATASET         │
│     - Label set: Select existing or create new         │
│                                                          │
│  2. Administrator defines label set (if new)           │
│     - Add DetectionClass objects:                          │
│       * DetectionClass 1: person, color=RED               │
│       * DetectionClass 2: vehicle, color=BLUE             │
│       * DetectionClass 3: animal, color=GREEN             │
│     - Save as reusable ClassSet                        │
│                                                          │
│  3. Link ProjectConfiguration to ClassSet                    │
│     - Project → ClassSet M2M relation created         │
│     - Database state now reflects configuration       │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓ User clicks "Generate YAML"
                     │
┌─ DJANGO BACKEND ───────────────────────────────────────┐
│                                                          │
│  4. DatasetConfig.generate_yaml() called with:            │
│     - project: ProjectConfiguration instance                │
│     - dataset_root: /data/ILLUSTRATIVE_DATASET         │
│                                                          │
│  5. Fetch related data from database                   │
│     - project.label_sets.all() → [ClassSet]           │
│     - label_set.label_classes.all() → [DetectionClass]    │
│                                                          │
│  6. Build intermediate YAML dictionary:                │
│     {                                                  │
│       "path": "/data/ILLUSTRATIVE_DATASET",           │
│       "train": "train/images",                        │
│       "val": "val/images",                            │
│       "test": "test/images",                          │
│       "nc": 3,                                        │
│       "names": ["person", "vehicle", "animal"]        │
│     }                                                  │
│                                                          │
│  7. Apply custom PyYAML serializer                     │
│     - Default PyYAML would produce:                    │
│       names:                                          │
│         - person                                      │
│         - vehicle                                     │
│         - animal                                      │
│     - Custom representer forces inline-style:         │
│       names: ["person", "vehicle", "animal"]          │
│                                                          │
│  8. Write YAML file to shared storage:                 │
│     Path: /shared_storage/configs/yaml_TIMESTAMP.yaml  │
│     Content: (inline-style YAML from step 7)          │
│                                                          │
│  9. Return YAML file path to Django UI                 │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ DJANGO FRONTEND (AJAX) ───────────────────────────────┐
│                                                          │
│  10. Display YAML preview to user                      │
│      - Show file path                                 │
│      - Show YAML content in textarea                  │
│      - Allow download or copy                         │
│                                                          │
│  11. User submits training request with YAML path:     │
│      {                                                 │
│        "dataset_yaml_path": "/shared_storage/configs/yaml_TIMESTAMP.yaml", │
│        "model_size": "m",                             │
│        "epochs": 50                                   │
│      }                                                │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓ HTTP POST /training (with YAML path)
                     │
┌─ FASTAPI LAYER ────────────────────────────────────────┐
│                                                          │
│  12. Receive training request                          │
│      - Parse dataset_yaml_path                        │
│      - Validate YAML file exists in shared storage    │
│      - Load YAML content                              │
│                                                          │
│  13. Ultralytics YOLO training executes               │
│      trainer.train(                                   │
│        data="/shared_storage/configs/yaml_TIMESTAMP.yaml", │
│        model="yolov8m.pt",                           │
│        epochs=50                                     │
│      )                                               │
│                                                          │
│  14. Training proceeds with classes from YAML:         │
│      - Class 0: person                               │
│      - Class 1: vehicle                              │
│      - Class 2: animal                               │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ TRAINING EXECUTION ───────────────────────────────────┐
│                                                          │
│  15. Multi-seed training loop with Django config      │
│      (Same as standard training flow, but config      │
│       originated from Django database models)         │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ ARTIFACTS BACK TO DJANGO ─────────────────────────────┐
│                                                          │
│  16. Best model stored in shared_storage              │
│      Django can associate training result with:        │
│      - Original ProjectConfiguration                        │
│      - ClassSet used                                 │
│      - YAML configuration file                       │
│      - Training metrics                              │
│                                                          │
└────────────────────────────────────────────────────────┘
```

### Docker Path Coordination

Django and FastAPI must both access the same YAML file despite different mount paths:

```
Host system:
  /home/user/shared_configs/yaml_TIMESTAMP.yaml (actual file)

Django container:
  Volume mount: shared_storage:/data/shared
  Access path: /data/shared/yaml_TIMESTAMP.yaml

FastAPI container:
  Volume mount: shared_storage:/app/shared_data
  Access path: /app/shared_data/yaml_TIMESTAMP.yaml

Both containers refer to same file via Docker volume mapping
```

---

## Error Handling Flow

```
┌─ ERROR DETECTION ──────────────────────────────────────┐
│                                                          │
│  Exception occurs in FastAPI:                          │
│  try:                                                  │
│    [training or inference logic]                       │
│  except ValueError as e:                               │
│    # Input validation error                            │
│    → HTTP 422 Unprocessable Entity                    │
│  except RuntimeError as e:                             │
│    if "CUDA out of memory" in str(e):                  │
│      → HTTP 507 Insufficient Storage                  │
│    else:                                               │
│      → HTTP 500 Internal Server Error                 │
│  except FileNotFoundError as e:                        │
│    # Shared storage issue                              │
│    → HTTP 500 Internal Server Error                   │
│  except Exception as e:                                │
│    # Unexpected error                                  │
│    → HTTP 500 Internal Server Error                   │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ ERROR LOGGING ────────────────────────────────────────┐
│                                                          │
│  Log to ClearML:                                       │
│    task.upload_artifact(                               │
│      name="error_log",                                 │
│      artifact_object=traceback.format_exc()            │
│    )                                                   │
│                                                          │
│  Log to local file:                                    │
│    /shared_storage/errors/error_TIMESTAMP.log          │
│                                                          │
│  Log to console:                                       │
│    logger.error(f"Training failed: {error_details}")    │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ RESPONSE TO DJANGO ───────────────────────────────────┐
│                                                          │
│  {                                                      │
│    "error": true,                                      │
│    "error_code": "CUDA_OOM",                           │
│    "message": "GPU memory exhausted",                   │
│    "details": "Reduce batch size or image size",       │
│    "job_id": "req_12345",                              │
│    "timestamp": "2026-06-09T11:45:00Z"                 │
│  }                                                      │
│                                                          │
└────────────────────┬──────────────────────────────────┘
                     │
                     ↓
┌─ DJANGO HANDLING ──────────────────────────────────────┐
│                                                          │
│  Update request status: ERROR                          │
│  Store error details in database                       │
│  Display error message to user                         │
│  Suggest troubleshooting steps                         │
│  Allow user to retry or adjust parameters             │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

**This flow documentation enables clear understanding of happy paths, error scenarios, and system coordination.**
