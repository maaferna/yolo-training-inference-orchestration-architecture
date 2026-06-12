# ADR-003: Use FastAPI as GPU-Backed AI Service Boundary

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Question
Having separated web and compute, we need to choose a framework for the GPU-backed compute service. Options:

1. **Flask**: Simple, minimal, synchronous
2. **FastAPI**: Modern, async-native, automatic API docs
3. **Celery**: Task queue framework
4. **Ray**: Distributed computation framework
5. **Keep code outside framework**: Raw PyTorch training loops

### MVP Requirements
- GPU access (CUDA)
- HTTP endpoint for receiving training requests
- Async job handling (long-running GPU tasks)
- Integration with PyTorch/YOLO ecosystem
- Minimal operational overhead

### Observations
- PyTorch training libraries (Ultralytics) are not async-aware
- Most heavy lifting happens in C/CUDA (not Python-bound)
- FastAPI async helps with I/O (reading configs, writing results) but not GPU compute
- We need a thin wrapper around blocking GPU code, not a heavy framework

---

## Decision

**Use FastAPI as the HTTP boundary for GPU compute service**

```
HTTP Request → FastAPI endpoint → Start GPU job → Wait for completion → Return result
```

**Why FastAPI?**

1. **Modern async foundation** 
   - Even though GPU code blocks, FastAPI manages I/O smoothly
   - Config loading, file I/O, API response generation all async-friendly

2. **Built-in API documentation**
   - FastAPI auto-generates Swagger/OpenAPI docs
   - Request/response schemas are self-documenting
   - Helps with Django integration (clear contract)

3. **Type hints and validation**
   - Pydantic models for request validation
   - Reduces boilerplate error checking
   - Helps prevent bad requests reaching GPU code

4. **Lightweight**
   - No magic or hidden complexity
   - Straightforward to debug
   - Minimal performance overhead

5. **Aligns with ML tools**
   - Popular in ML/AI community
   - Good integration examples with PyTorch
   - Hyperscaler-friendly (easily migrates to cloud)

---

## Architecture Pattern

```
FastAPI Service Layer
├── Endpoint: /training (POST)
│   ├── Validate request (Pydantic)
│   ├── Prepare GPU environment
│   ├── Call blocking GPU code (Ultralytics, YOLO)
│   ├── Poll for completion
│   └── Return results (JSON)
│
├── Endpoint: /inference (POST)
│   ├── Load model
│   ├── Call inference (SAHI tiling)
│   └── Return detections (JSON)
│
└── Endpoint: /status/{job_id} (GET)
    └── Return job status (queued, running, done, failed)
```

**Important**: FastAPI endpoint is *synchronous* from client perspective
- Client makes request
- Server runs blocking GPU code
- Server returns response (minutes later)
- This is acceptable at MVP scale (Phase 2 adds job queue)

---

## Consequences

### Benefits

✅ **Simplicity**
- Thin HTTP wrapper around GPU code
- No queue framework overhead
- Developers focus on GPU code, not plumbing

✅ **Debuggability**
- Synchronous request/response easy to trace
- Stack traces point directly to GPU code
- No async/await complexity hiding bugs

✅ **Performance**
- No serialization overhead (unlike Celery)
- Direct GPU memory access
- Minimal software layers between request and GPU

✅ **Django Integration**
- Clear HTTP contract between services
- Easy to test (curl, Postman, browser)
- Standard REST semantics

✅ **Documentation**
- Auto-generated Swagger UI
- Type hints visible to Django developers
- Self-documenting API

### Drawbacks

❌ **Synchronous Blocking**
- Client connection must stay open for entire job (30+ minutes)
- HTTP timeout risk (typical timeout ~30 minutes)
- No job persistence if service restarts

❌ **Single Request = Single GPU Thread**
- Can't queue multiple requests
- Second request waits for first to complete
- No concurrency at all (Phase 2 fixes with workers)

❌ **No Error Recovery**
- Failed mid-training GPU code has no retry logic
- Partial state on disk if process crashes
- Manual intervention needed for many failure modes

❌ **Not Suitable for Scale**
- Once we have 10 concurrent requests, this falls apart
- Phase 2 migration to job queue becomes mandatory
- Current design intentionally MVP-scoped

---

## Alternatives Considered

### Alternative 1: Celery with Redis/RabbitMQ

**Approach**: Use Celery task queue from the start

**Why not chosen**:
- Adds Redis or RabbitMQ to infrastructure (more to deploy/maintain)
- Celery complexity upfront (task definitions, worker management)
- MVP doesn't need it yet; single GPU sufficient
- Delayed to Phase 2 when concurrent jobs observed
- "Build complexity only when you need it" principle

### Alternative 2: Ray for Distributed Computing

**Approach**: Use Ray for GPU task distribution

**Why not chosen**:
- Designed for multi-node distributed computing
- Overkill for single machine with one GPU
- Ray's complexity unnecessary at MVP scale
- Learning curve steep for small team
- Ray excellent for Phase 3+ (multi-GPU workers)

### Alternative 3: Apache Airflow

**Approach**: Use Airflow for job orchestration

**Why not chosen**:
- Designed for data pipeline orchestration (DAGs)
- Overkill for simple "run training → return results"
- Operational burden (web UI, scheduler, executor)
- Not a natural fit for synchronous training requests
- Better for batch processing than real-time requests

### Alternative 4: Raw ASGI Application

**Approach**: Build custom ASGI app without FastAPI framework

**Why not chosen**:
- No built-in validation, documentation, or error handling
- Essentially reinventing FastAPI
- More boilerplate, more bugs
- Minimal performance benefit

---

## MVP Limitations (Intentional)

This design intentionally accepts limitations:

1. **No concurrent training jobs**
   - If second request arrives during training, must wait
   - This is accepted at MVP scale (~1-2 jobs per day)
   - Phase 2: Add Redis queue for concurrency

2. **No job persistence**
   - Service restart = lost job
   - Acceptable for research/MVP context
   - Phase 2: ClearML + job registry for persistence

3. **HTTP timeout risk**
   - 30-minute timeout typical for HTTP servers
   - Training often takes 1-3 hours
   - Phase 2: Implement async polling pattern

**Key point**: These are *documented limitations*, not bugs. We chose MVP simplicity over enterprise patterns, intentionally.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| HTTP timeout during training | Medium | High | Phase 2: Add job queue; document current limitation |
| Concurrent requests fail | High | High | Document as Phase 1 limitation; Phase 2 fixes |
| No job recovery on restart | Medium | Medium | ClearML logs metadata; Phase 2 adds job registry |
| Performance becomes bottleneck | Low | Medium | Profile; Phase 2 adds workers if needed |
| Scaling becomes impossible | High | High | Intentional; Phase 2 redesigns with workers |

**Mitigation Strategy**:
- Phase 1: Document all limitations clearly (DONE - see docs/14-limitations-and-risks.md)
- Phase 2: Implement job queue + worker pattern
- Phase 3+: Multi-GPU workers, Kubernetes orchestration

---

## Future Evolution

### Phase 2: Add Job Queue
- Keep FastAPI, add Redis for job coordination
- FastAPI becomes job submitter (async)
- Worker processes handle GPU execution
- Django polls for results

### Phase 3: Multiple GPU Workers
- Scale from 1 GPU to N GPU workers
- Load balancing across workers
- Still using FastAPI + Redis

### Phase 4: Kubernetes
- Workers become Kubernetes pods
- Auto-scaling based on queue depth
- Object storage replaces shared filesystem
- Still FastAPI at service boundary

---

## Public-Safe Note

This ADR describes framework selection rationale for building GPU service boundaries. The specific choice (FastAPI) is a well-known open-source framework; this document contains no proprietary implementation details.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-001**: Service separation that enables FastAPI specialization
- **ADR-004**: ClearML for metadata coordination with FastAPI
- **ADR-009**: Future job queue pattern (Phase 2)

---

## References

This decision aligns with:
- Framework selection based on use case (not cargo cult)
- MVP pragmatism (simple first, complex when needed)
- Explicit trade-off documentation
