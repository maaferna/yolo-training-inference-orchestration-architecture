# ADR-005: Use SAHI for High-Resolution Small-Object Inference

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Problem
Standard YOLO inference works well on typical resolution images (640×480). But some use cases require:
- High-resolution imagery (4K, 8K)
- Detection of small objects in large images
- Field-level or panoramic imaging

Direct approaches fail:
1. **Resize down** → Small objects become undetectable
2. **Inference at full resolution** → OOM (GPU memory exceeded) or very slow
3. **Manual tiling** → Complex preprocessing, prone to missed objects at tile boundaries

### SAHI (Sliced Aided Hyperbolic Inference)
SAHI solves this by:
- Automatically tiling large images
- Running YOLO inference on each tile
- Merging detections and removing duplicates
- Returning unified detection list

### Technical Question
Could we do this ourselves vs. using SAHI library?

---

## Decision

**Use SAHI library for high-resolution small-object inference**

SAHI handles:
- Intelligent tiling strategies
- Slice overlap calculation (prevents boundary artifacts)
- Detection merging and de-duplication
- Confidence score filtering
- IoU-based duplicate removal

```
Large Image (4K, 8K)
    ↓
SAHI Slice Generator
    ├── Tile 1 → YOLO inference → [det1, det2]
    ├── Tile 2 → YOLO inference → [det3, det4]
    └── Tile 3 → YOLO inference → [det2_dup, det5]
    ↓
SAHI Merge & Deduplicate
    └── [det1, det2, det3, det4, det5] (unified)
    ↓
Result to user
```

---

## Consequences

### Benefits

✅ **Correctness**
- Detects small objects that standard inference misses
- Handles boundaries correctly (overlapping tiles)
- Proven approach (used in competitions)

✅ **Simplicity**
- SAHI handles tiling complexity
- Single library call: `sahi.predict(image, detector)`
- No custom boundary logic needed

✅ **Performance**
- Reasonable latency for typical images
- GPU batching across tiles possible
- Controllable trade-off: slice size ↔ accuracy ↔ speed

✅ **Flexibility**
- Configurable tile size, overlap, confidence threshold
- Works with any YOLO model (v5, v8, etc.)
- Easy to experiment with parameters

### Drawbacks

❌ **Dependency**
- Adds external library (SAHI)
- Must maintain compatibility with YOLO versions
- SAHI API changes could require refactoring

❌ **Performance Not Optimal**
- Sequential tile processing (no parallelization in SAHI)
- Phase 3 could optimize with parallel tile inference

❌ **Not Streaming**
- Must load entire high-res image in memory
- Streaming inference not possible
- Very large images might still OOM

---

## Alternatives Considered

### Alternative 1: Manual Tiling

**Approach**: Write custom tiling logic ourselves

**Why not chosen**:
- Reinventing existing solution (SAHI)
- Edge cases hard to get right (overlapping tiles, boundary duplicates)
- More code to maintain
- SAHI already proven and tested

### Alternative 2: Pre-process Down-Sample

**Approach**: Always resize to standard size before YOLO

**Why not chosen**:
- Small objects become undetectable
- Defeats purpose of high-res image processing
- Wastes potential of expensive GPU inference

### Alternative 3: Custom CUDA Kernel

**Approach**: Implement tiling in CUDA for performance

**Why not chosen**:
- Engineering overhead not justified for MVP
- SAHI + tuning sufficient for current scale
- Can be revisited in Phase 3 for optimization

---

## Limitations

- **Sequential**: Tiles processed one at a time (not parallel)
- **Memory**: Full image must fit in system memory
- **Latency**: Inference time scales with image size
- **Not streaming**: Cannot process streaming video (yet)

These are acceptable for MVP research use case.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| SAHI dependency breaks | Low | Medium | Version lock; test regularly |
| Performance unacceptable | Low | High | Profile; Phase 3 optimizations |
| Memory exhaustion on huge images | Low | Medium | Document size limits; add validation |

---

## Future Evolution

### Phase 3: Optimization
- Parallel tile processing (batch across tiles)
- Streaming inference (process tile-by-tile output)
- GPU-accelerated tiling in CUDA

### Phase 4: Advanced
- Ensemble methods (multiple model predictions per tile)
- Confidence calibration across tiles
- Real-time video processing

---

## Public-Safe Note

This ADR describes SAHI (open-source library) and the decision to use it for tiled inference. The high-resolution image processing problem is generic; this ADR contains no proprietary details.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-003**: FastAPI integration point for SAHI inference
- **ADR-009**: Phase 3 optimization opportunities
