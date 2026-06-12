# ADR-001: Separate Django Web Orchestration from FastAPI AI Processing

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Problem
Initially, all workloads (web requests and GPU-intensive ML tasks) were managed in a single Django application. This created several critical issues:

1. **Resource Contention**: Web requests compete with long-running training jobs for the same resources
2. **Scaling Misalignment**: Web tier and GPU tier need different scaling characteristics (web: horizontal; GPU: vertical)
3. **Operational Complexity**: A single framework handling both stateless web concerns and stateful GPU orchestration creates conceptual and operational overhead
4. **Responsibility Confusion**: What is Django responsible for? Authentication? Training? Inference? Both leads to architectural confusion

### Key Constraints
- Single GPU resource (expensive, not to be wasted)
- Small team (limited operational capacity)
- Need for clear separation of concerns (web vs. compute)
- Requirement for independent deployment and scaling paths

### Observations
- Web requests: stateless, fast (< 1 sec typical), high frequency
- GPU jobs: stateful, slow (30+ minutes typical), low frequency
- These are fundamentally different problems requiring different solutions

---

## Decision

**Separate the system into two independent services:**

1. **Django Web Application** (port 8000)
   - Handles: Request submission, authentication, result visualization
   - Does NOT handle: GPU training or inference execution
   - Responsibility: User interface, request persistence, result display

2. **FastAPI AI Service** (port 8001)
   - Handles: GPU-intensive training and inference execution
   - Does NOT handle: User authentication or web UI
   - Responsibility: Model training, inference dispatch, experiment tracking
   - GPU-backed: Direct access to CUDA resources

**Integration Mechanism**: HTTP/REST API between services

```
[User] → [Django Web] ←→ [FastAPI AI Service] → [GPU]
           (8000)          (8001)
```

---

## Consequences

### Benefits

✅ **Clear Responsibility Boundaries**
- Django owns web concerns (authentication, UI, request history)
- FastAPI owns compute concerns (training, inference, experiment tracking)
- Each team can reason about their own layer independently

✅ **Independent Scaling**
- Web can scale horizontally (more Django instances)
- GPU service scales vertically (more GPU, more worker processes)
- Different resources for different problems

✅ **Technology Alignment**
- Django excels at web frameworks (ORM, auth, templating)
- FastAPI excels at async services (built for I/O-heavy operations)
- Each chosen for what it does best

✅ **Operational Clarity**
- Failure modes are explicit (if training fails, web stays up)
- Monitoring is simpler (separate concerns = separate metrics)
- Debugging is easier (stack traces point to specific service)

✅ **Future Flexibility**
- Can evolve each service independently
- Can replace Django UI with different frontend (React, Vue, etc.)
- Can add multiple FastAPI workers when needed

### Drawbacks

❌ **Network Overhead**
- HTTP requests between services add latency
- Each request crosses serialization boundary (JSON)
- Network failure could break integration

❌ **Distributed System Complexity**
- Debugging issues across services is harder
- State consistency requires careful coordination
- Correlation IDs needed to track requests across boundary

❌ **Operational Burden**
- Two services to deploy, monitor, and maintain (instead of one)
- Docker Compose complexity increases
- More moving parts to configure correctly

❌ **Development Complexity**
- Local development requires running both services
- Requires understanding both Django and FastAPI
- Integration testing more involved than single-service testing

---

## Alternatives Considered

### Alternative 1: Single Django Service with Background Tasks (Celery)

**Approach**: Keep everything in Django, use Celery for async task execution

**Why not chosen**:
- Adds Celery complexity (message broker, worker processes) upfront
- Still requires understanding of queue semantics
- Doesn't solve technology mismatch (Django not ideal for async GPU orchestration)
- Delays learning true distributed system patterns
- At MVP scale, premature optimization (added complexity for unproven benefit)

### Alternative 2: Kubernetes from Day 1

**Approach**: Use Kubernetes pods for both services, service mesh for communication

**Why not chosen**:
- Massive operational overhead for single GPU
- Kubernetes designed for multi-node, auto-scaling scenarios
- Learning curve too steep for MVP (focus should be on model, not infrastructure)
- Docker Compose sufficient for current scale
- Can migrate to Kubernetes later when genuinely needed (Phase 4)

### Alternative 3: Single FastAPI Service Only

**Approach**: Replace Django entirely with FastAPI for both web and GPU

**Why not chosen**:
- FastAPI not optimized for traditional web concerns (templates, ORM, etc.)
- Django ORM is stronger for relational data (user management, request history)
- Loses battle-tested web framework stability
- FastAPI excels at async I/O, but web request handling doesn't need that

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| HTTP timeout during long training | Medium | High | Implement async job pattern in Phase 2 (add Redis queue) |
| Network failure breaks system | Low | High | Implement circuit breaker + fallback responses |
| Latency overhead unacceptable | Low | Medium | Profile in production; optimize if needed |
| Debugging complexity increases | High | Low | Implement correlation IDs for request tracking |
| Data consistency issues | Medium | High | Clear contract for request/response format (API docs) |

**Mitigation Strategy**:
- Phase 1 (Current): Accept HTTP request/response model; document limitations
- Phase 2 (Future): Add job queue (Redis) to decouple request/response
- Phase 3+: Can evolve integration pattern as needs grow

---

## Public-Safe Note

This ADR contains no proprietary implementation details, actual server names, credentials, or confidential system information. It describes the general pattern of separating web and compute services, a widely recognized architecture pattern.

All specific details (port numbers, service names, etc.) are generic and non-revealing.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-002**: Use Shared Artifact Storage as Integration Mechanism
- **ADR-003**: Use FastAPI as GPU-Backed AI Service Boundary
- **ADR-009**: Future Migration Toward Job Queues (when Phase 2 needed)

---

## References

This decision draws from:
- Microservices architecture patterns (Newman, "Building Microservices")
- Separation of concerns principle
- Single Responsibility Principle (SRP)
- Technology selection rationale
