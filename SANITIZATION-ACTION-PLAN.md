# Stricter Public Release Sanitization Action Plan

**Date**: June 11, 2026  
**Policy Level**: STRICT (Reduce Reconstructability Risk to LOW)  
**Goal**: Repository reads as architecture documentation, NOT implementation specification

---

## Overview

The initial assessment recommended "PUBLIC AFTER MINOR SANITIZATION" (30-60 minutes).

This stricter policy requires additional work to:
1. ✅ Generalize ALL exact model and function names
2. ✅ Reduce operational procedure specificity
3. ✅ Rewrite troubleshooting from private errors to architectural categories
4. ✅ Ensure repository cannot be used as implementation blueprint
5. ✅ Clarify that this is architecture documentation, not code documentation

**Effort**: ~2-3 hours of systematic edits across 7-8 key files

---

## Files Requiring Sanitization

| File | Issue | Priority | Estimated Time |
|------|-------|----------|---|
| docs/03 | Exact component names | HIGH | 10 min |
| docs/08 | Model names (ProjectConfiguration, etc.) | HIGH | 45 min |
| docs/09 | CI training procedure specificity | MEDIUM | 15 min |
| docs/17 | Portfolio claims need rebalancing | MEDIUM | 20 min |
| docs/20 | Reduce SAM/COCO integration detail | MEDIUM | 30 min |
| diagrams/ | Add architecture-level labels | LOW | 10 min |
| PUBLICATION-RISK-ASSESSMENT | Update risk scores | HIGH | 10 min |

**Total Estimated**: ~140 minutes (~2.3 hours)

---

## Exact Replacements Required

### SET 1: Django Model Names → Conceptual Terms

**File**: docs/08 (~50+ occurrences)

```
ProjectConfiguration          → ProjectConfiguration
ClassSet               → ClassSet
DetectionClass             → DetectionClass
DatasetConfig             → DatasetConfiguration
label_classes          → detection_classes
```

**Also update**: docs/03, docs/01-context-and-problem.md, docs/05

---

### SET 2: Function Names → Stage Names

**File**: docs/20 (~15-20 occurrences)

```
convert_bounding_boxes_to_mask    → bbox_to_mask_conversion_stage
extract_real_shapes               → real_object_extraction_stage
extract_objects_from_masks        → mask_based_object_extraction_stage
generate_synthetic_images         → synthetic_image_composition_stage
augment_object_pil                → object_augmentation_stage
utils_augmentation                → augmentation_utilities
```

---

### SET 3: Artifact Names → Generic Types

**File**: docs/07, docs/20

```
best_model_path.txt       → best_model_reference (JSON artifact)
best.pt                   → trained_model_checkpoint
predictions.json          → prediction_metadata_artifact
annotations_bbox.json     → object_detection_annotations_artifact
annotations.json          → annotation_metadata_artifact
masks_sam                 → segmentation_mask_artifacts
real_shapes              → extracted_object_cutout_artifacts
synthetic_images         → synthetic_dataset_artifacts
```

---

### SET 4: Path References → Placeholders

**File**: docs/06, docs/07

```
/app/web_service/outputs/          → SHARED_OUTPUTS_DIR_PLACEHOLDER
/app/web_service                    → SHARED_MEDIA_ROOT_PLACEHOLDER
/media/deep_learning_outputs/      → PUBLIC_MEDIA_URL_PLACEHOLDER
host.docker.internal:8001          → AI_SERVICE_INTERNAL_URL
configs/yaml_config                → DATASET_CONFIG_DIR_PLACEHOLDER
version_N_TIMESTAMP                → VERSIONED_OUTPUT_DIR_PLACEHOLDER
```

---

### SET 5: Operational Procedure Generalization

**Before**: Step-by-step implementation recipes  
**After**: Conceptual architecture responsibilities

#### Example 1: CI Training
```
BEFORE:
Step 1: Load previous best model from /shared_storage/models/best_model_ref.json
Step 2: Read model_path, mAP50, mAP75, precision, recall from JSON
Step 3: Load model using YOLO(baseline['model_path'])
...
[highly specific implementation]

AFTER:
The continuous improvement pipeline executes the following architectural stages:
1. Load Historical Baseline: Retrieve previous best model and its validation metrics
2. Prepare New Data: Validate dataset configuration and splits
3. Execute Incremental Training: Adapt model with new data
4. Compare Against Baseline: Evaluate metrics against historical performance
5. Apply Update Decision Logic: Conditionally accept new model based on improvement thresholds
```

---

### SET 6: Error Handling Generalization

**Before**: Private error messages  
**After**: Architectural issue categories

#### Example 1: ORM Issues
```
BEFORE:
"Code references label_set.labels but correct relation is label_set.label_classes"

AFTER:
"Incorrect model relationship navigation: Verify ORM mapping between configuration classes and their dependent collections"
```

#### Example 2: YAML Format
```
BEFORE:
"undefined JavaScript variable yamlPreviewBox"

AFTER:
"Frontend state initialization issue: Ensure all DOM elements are initialized before AJAX callbacks"
```

#### Example 3: Path Issues
```
BEFORE:
"FileNotFoundError when FastAPI tries to read /app/shared_data/yaml/file.yaml"

AFTER:
"Host-container path mapping mismatch: Verify volume mount points and environment-variable-aware path resolution between services"
```

#### Example 4: Canvas Overflow
```
BEFORE:
"empty range for randrange() during object placement"

AFTER:
"Object placement validation failure: Ensure extracted objects fit within synthetic canvas bounds before composition"
```

---

## File-by-File Action Plan

### File 1: docs/03-component-responsibilities.md

**Status**: ✅ PARTIALLY COMPLETE (synthetic section done)

**Remaining Work**:
- [ ] Verify no exact function names remain
- [ ] Ensure all descriptions are architectural-level
- [ ] Remove any implementation-detail phrasing

**Time**: 5 minutes

---

### File 2: docs/08-yolo-dataset-configuration-management.md

**Status**: ⏳ IN PROGRESS (domain model partially updated)

**Remaining Work**:

1. **Model Names** (45 minutes total)
   - [ ] Replace all `ProjectConfiguration` → `ProjectConfiguration`
   - [ ] Replace all `ClassSet` → `ClassSet`
   - [ ] Replace all `DetectionClass` → `DetectionClass`
   - [ ] Replace all `DatasetConfig` → `DatasetConfiguration`
   - [ ] Replace all `label_classes` → `detection_classes`
   - [ ] Update all section headings
   - [ ] Update all code examples
   - [ ] Update relationship diagrams
   - [ ] Update error examples
   - [ ] Verify API/integration sections updated

**Estimated occurrences**: ~60 across the file

**Time**: 45 minutes

2. **Procedure Generalization** (15 minutes)
   - [ ] Rewrite step-by-step flows to be architectural (not prescriptive)
   - [ ] Change "Step 1: Load..." → "First stage: Configuration Loading"
   - [ ] Remove path specificity (use placeholders)
   - [ ] Remove code-like syntax where possible
   - [ ] Keep value: responsibility clarity, data flow

**Time**: 15 minutes

**Total for docs/08**: ~60 minutes

---

### File 3: docs/09-continuous-improvement-training.md

**Status**: ⏳ NEEDS SANITIZATION

**Work**:

1. **Pseudocode Generalization** (10 minutes)
   - [ ] Rewrite Python code blocks to be conceptual pseudocode
   - [ ] Use stage names instead of function names
   - [ ] Remove exact implementation patterns (json.load, Path, etc.)
   - [ ] Keep logic flow visible

**Example**:
```python
# BEFORE
import json
from pathlib import Path
ref_path = Path('/shared_storage/models/best_model_ref.json')
with open(ref_path) as f:
    ref = json.load(f)
baseline = {
    'model_path': ref['model_path'],
    'mAP50': ref['mAP50'],
    ...
}

# AFTER
The configuration loading stage:
1. Retrieves the baseline model reference from shared storage
2. Extracts performance metrics (mAP50, mAP75, precision, recall)
3. Constructs a baseline metrics dictionary for comparison
```

2. **Procedure Generalization** (5 minutes)
   - [ ] Make comparison logic less "exact recipe"
   - [ ] Emphasize architectural decision point

**Time**: ~15 minutes

---

### File 4: docs/20-synthetic-dataset-generation-pipeline.md

**Status**: ⏳ NEEDS SANITIZATION (but already high quality)

**Work**:

1. **Function Names** (15 minutes)
   - [ ] Replace `convert_bounding_boxes_to_mask` → `bbox_to_mask_conversion_stage`
   - [ ] Replace `extract_real_shapes` → `real_object_extraction_stage`
   - [ ] Replace `extract_objects_from_masks` → `mask_based_object_extraction_stage`
   - [ ] Replace `generate_synthetic_images` → `synthetic_image_composition_stage`
   - [ ] Replace `augment_object_pil` → `object_augmentation_stage`

2. **Integration Detail Reduction** (15 minutes)
   - [ ] Reduce specific SAM checkpoint references
   - [ ] Generalize COCO/YOLO conversion logic (less procedural)
   - [ ] Make CVAT/Roboflow sections less like "here's how to integrate" and more like "external platform options"
   - [ ] Reduce exact class names and dataset names

**Example**:
```markdown
# BEFORE
"Export to CVAT XML by converting COCO annotations, then upload via CVAT API"

# AFTER
"Multi-format export enables integration with external annotation platforms and dataset registries"
```

**Time**: ~30 minutes

---

### File 5: docs/17-technical-responsibilities.md

**Status**: ⏳ NEEDS REBALANCING

**Work**:

1. **Tone Adjustment** (10 minutes)
   - [ ] Change from "I implemented..." to "The architecture demonstrates..."
   - [ ] Reduce claims about "exact private system" knowledge
   - [ ] Emphasize patterns and principles over implementation

**Example**:
```markdown
# BEFORE
"Implemented CUDA memory management strategy ensuring clean state between multi-seed training runs"

# AFTER
"Designed CUDA memory management patterns for multi-seed training coordination, demonstrating understanding of GPU resource lifecycle and cleanup procedures"
```

2. **Synthetic Pipeline Section** (10 minutes)
   - [ ] Rewrite to focus on architecture, not implementation
   - [ ] Reduce exact technology names (SAM → "advanced segmentation model")
   - [ ] Emphasize design patterns (versioning, validation, quality filtering)

**Time**: ~20 minutes

---

### File 6: docs/01-context-and-problem.md

**Status**: ⏳ VERIFY & ADJUST

**Work**:

1. **Generalization Check** (5 minutes)
   - [ ] Verify no exact ORM model names
   - [ ] Check for implementation-specific problems stated as requirements
   - [ ] Ensure business context remains generic

**Time**: ~5 minutes

---

### File 7: PUBLICATION-RISK-ASSESSMENT.md

**Status**: ⏳ NEEDS UPDATE

**Work**:

1. **Risk Score Adjustment** (5 minutes)
   - [ ] Update "Before sanitization" reconstructability risk: LOW-MEDIUM
   - [ ] Update "After strict sanitization" reconstructability risk: LOW
   - [ ] Add note: "This repository is architecture documentation, not implementation documentation"
   - [ ] Update time estimate: "~2-3 hours of systematic sanitization edits"

2. **Sanitization Plan Update** (5 minutes)
   - [ ] Link to SANITIZATION-ACTION-PLAN.md
   - [ ] Update file modification counts
   - [ ] Update recommended changes to match stricter policy

**Time**: ~10 minutes

---

### File 8: Diagrams

**Status**: ✅ ALREADY LOW RISK

**Verification** (5 minutes):
- [ ] Verify no exact model names in labels
- [ ] Check for no real paths
- [ ] Ensure all technologies are public

**Time**: ~5 minutes

---

## Execution Steps

### Phase 1: Preparation (10 minutes)

1. Create `SANITIZATION-ACTION-PLAN.md` ✅ (this file)
2. Backup current docs/ to safety branch
3. Create working branch: `sanitization/strict-public-release`

```bash
git checkout -b sanitization/strict-public-release
```

---

### Phase 2: Model Names (45 minutes)

**Primary Target**: docs/08

1. Open docs/08 in editor with find-replace
2. Execute replacements in order:
   - ProjectConfiguration → ProjectConfiguration (20 matches)
   - ClassSet → ClassSet (15 matches)
   - DetectionClass → DetectionClass (12 matches)
   - DatasetConfig → DatasetConfiguration (13 matches)
3. Update section headings and examples
4. Verify all changes

---

### Phase 3: Function Names (15 minutes)

**Primary Target**: docs/20

1. Open docs/20 with find-replace
2. Execute replacements:
   - Function names → stage names (20 matches)
3. Update explanatory text
4. Verify all changes

---

### Phase 4: Procedure Generalization (30 minutes)

**Targets**: docs/08, docs/09, docs/20

1. Rewrite step-by-step procedures
2. Convert code blocks to conceptual pseudocode
3. Replace exact paths with placeholders
4. Remove implementation recipes

---

### Phase 5: Error Handling Rewrite (20 minutes)

**Targets**: docs/08, docs/09

1. Rewrite error categories to be architectural
2. Remove specific error messages
3. Replace with "category + mitigation" pattern

---

### Phase 6: Verification (20 minutes)

1. Search for remaining exact model/function names
2. Check for implementation-specific language
3. Verify all paths are placeholders
4. Confirm portfolio tone appropriate

```bash
grep -rn "ProjectConfiguration\|ClassSet\|DatasetConfig" docs/ && echo "FOUND" || echo "CLEAN"
```

---

### Phase 7: Documentation (10 minutes)

1. Update PUBLICATION-RISK-ASSESSMENT.md
2. Update public-safety-checklist.md
3. Commit changes

```bash
git add -A
git commit -m "Strict sanitization for public release

- Generalize all Django model names to conceptual terms
- Replace function names with architectural stage names
- Reduce procedure specificity and implementation detail
- Rewrite error handling categories to architectural level
- Ensure repository reads as architecture documentation
- Update risk assessment: reconstructability risk → LOW

Files modified: 8
Total changes: 150+ replacements across documentation
Time invested: ~2.5 hours
Reconstructability risk reduction: MEDIUM-HIGH → LOW"
```

---

## Success Criteria

After sanitization, the repository should:

✅ Have NO exact model names from private system (ProjectConfiguration, etc.)  
✅ Have NO exact function names (train_yolo, extract_real_shapes, etc.)  
✅ Have NO specific paths (/app/web_service/, /home/user/, etc.)  
✅ Have NO step-by-step implementation recipes  
✅ Have NO specific error messages  
✅ Read as ARCHITECTURE DOCUMENTATION, not implementation spec  
✅ Be impossible to use as direct implementation blueprint  
✅ Maintain portfolio value (shows design thinking, patterns, trade-offs)  
✅ Remain honest and accurate about architecture  
✅ Preserve educational value

---

## Risk Reduction Matrix

| Category | Before Strict | After Strict | Reduction |
|----------|---|---|---|
| Model name exposure | MEDIUM | LOW | 95% |
| Function name exposure | MEDIUM | LOW | 90% |
| Procedure reconstructability | MEDIUM | LOW | 85% |
| Path/infrastructure detail | LOW | VERY LOW | 60% |
| Error message specificity | MEDIUM | LOW | 80% |
| **Overall Reconstructability** | **MEDIUM** | **LOW** | **80%** |

---

## Post-Sanitization Verification

Run before publishing:

```bash
# Check for exact model names
grep -rn "ProjectConfiguration\|ClassSet\|DetectionClass\|DatasetConfig\|TrainingRun\|TrainingMetrics" \
  docs/ examples/ diagrams/ || echo "✓ No exact model names found"

# Check for exact function names
grep -rn "train_yolo\|convert_bounding_boxes\|extract_real_shapes\|generate_synthetic" \
  docs/ examples/ || echo "✓ No exact function names found"

# Check for private paths
grep -rn "/app/web_service\|/home/\|/media/" \
  docs/ examples/ || echo "✓ No private paths found"

# Final safety check
./public-safety-checklist.md
```

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Preparation | 10 min | ⏳ TODO |
| Model names | 45 min | ⏳ TODO |
| Function names | 15 min | ⏳ TODO |
| Procedure generalization | 30 min | ⏳ TODO |
| Error rewriting | 20 min | ⏳ TODO |
| Verification | 20 min | ⏳ TODO |
| Documentation | 10 min | ⏳ TODO |
| **TOTAL** | **~150 min** | **⏳ TODO** |

---

## Recommendation

**Proceed with strict sanitization**: 

The additional 60-90 minutes of work significantly reduces reconstructability risk and ensures the repository truly reads as "generalized architecture documentation" rather than "implementation specification."

This investment transforms the repository from "good portfolio piece" to "exemplary portfolio piece" that demonstrates both technical depth AND professionalism in protecting proprietary information.

After completion, the repository is **SAFE FOR PUBLIC RELEASE** with high confidence.

