# ADR-002: Use Shared Artifact Storage as Initial Integration Mechanism

**Status**: Accepted  
**Date**: June 2026  
**Public-Safe**: Yes  

---

## Context

### The Challenge
With Django and FastAPI now separate services, they need a way to exchange artifacts (models, checkpoints, inference outputs). Options include:

1. **HTTP file transfer** (stream from service A to service B)
2. **Shared filesystem** (both services mount same volume)
3. **Object storage** (S3, MinIO, etc.)
4. **Database** (store as BLOB in PostgreSQL)

### MVP Constraints
- Single machine deployment (not distributed)
- Local Docker containers (all on same host)
- Limited team bandwidth for operational complexity
- Need for fast development iteration

### Key Requirements
- FastAPI writes training artifacts (checkpoints, best models)
- Django reads results for display
- ClearML also needs to track artifacts
- Files can be large (models 100MB+)
- Need version history and artifact organization

---

## Decision

**Use Docker volume mounting for shared filesystem**

Both Django and FastAPI mount the same storage volume, enabling direct file access:

```
Docker Host Filesystem
    ↓
Shared Volume: shared_storage/
    ↓
├── Django (mounted at /data/shared/)
├── FastAPI (mounted at /app/shared_data/)
└── (same underlying files)
```

**Artifact Organization**:
```
shared_storage/
├── models/
│   ├── best.pt           ← Current best model
│   └── backup_v1.pt      ← Historical models
├── checkpoints/
│   ├── epoch_10.pt       ← Training checkpoints
│   └── epoch_20.pt
├── training_outputs/
│   └── summary.json      ← Metrics and metadata
├── inference/
│   ├── results_job123/
│   └── detections.json
└── configs/
    └── training_config.yaml
```

---

## Consequences

### Benefits

✅ **Simplicity**
- No additional infrastructure (no S3, Redis, etc.)
- Both services access files directly
- Fast development iteration (change files, restart services)

✅ **Performance**
- No network overhead (local filesystem access)
- Large model files transfer fast
- Real-time file updates visible to both services

✅ **Familiarity**
- Developers understand filesystem semantics
- Debugging: can inspect files directly
- No new concepts (Redis, S3 API, etc.)

✅ **Cost**
- Zero infrastructure cost
- Single storage backend
- Works with Docker Compose out of box

### Drawbacks

❌ **Single Point of Failure**
- Shared filesystem goes down → entire system fails
- No redundancy or failover
- Corrupt filesystem affects both services

❌ **Not Distributed**
- Doesn't scale to multiple machines
- Cannot support multi-region deployment
- Blocks transition to cloud/Kubernetes

❌ **Not Concurrent**
- Multiple writers to same file cause race conditions
- No distributed locking mechanism
- FastAPI overwriting checkpoints while Django reading → corruption risk

❌ **No Versioning/Archival**
- Old artifacts must be manually managed
- No built-in retention policy
- Storage growth unlimited

❌ **No Access Control**
- No way to restrict which services access which files
- No audit trail of who read/wrote what
- Security concerns at scale

---

## Alternatives Considered

### Alternative 1: S3/Object Storage from Day 1

**Approach**: Use AWS S3 or MinIO for all artifacts

**Why not chosen**:
- Operational overhead: requires S3/MinIO service
- Cost: either cloud costs or hardware for MinIO
- Development complexity: S3 API is more complex than filesystem
- MVP overkill: single machine doesn't justify object storage
- Phase 2 candidate: when we need multi-region or better resilience

### Alternative 2: HTTP File Transfer Between Services

**Approach**: FastAPI uploads files to Django via POST /upload; Django downloads via GET

**Why not chosen**:
- Network overhead: unnecessary serialization/deserialization
- Complexity: requires chunking for large files
- Failure risk: mid-transfer failure leaves partial files
- Bidirectional complication: Django needs to write configs, FastAPI needs to read
- Performance: slower than direct filesystem access

### Alternative 3: Database as Artifact Store (PostgreSQL BLOB)

**Approach**: Store all artifacts as BLOB in PostgreSQL

**Why not chosen**:
- Database not designed for large binary objects (slow, expensive)
- Models are 100MB+ (PostgreSQL BLOB performance degrades)
- Backup/recovery becomes database responsibility (models should be separate)
- Query performance suffers with large BLOB storage
- Filesystem already optimized for file I/O

### Alternative 4: Direct Inter-Service Memory Sharing (Shared Memory)

**Approach**: Use shared memory segments for artifact exchange

**Why not chosen**:
- Only works for single machine (already our constraint, but fragile)
- Memory-limited (models often larger than available RAM)
- Complex debugging (memory addresses, serialization)
- Fragility: process crash loses all in-memory data

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Filesystem corruption | Low | High | Regular backups; Phase 2 adds versioning |
| Race conditions (concurrent writes) | Medium | High | Clear protocol: FastAPI writes, Django reads; ClearML logs metadata |
| Storage fills up | Medium | High | Implement cleanup policy; monitor disk usage |
| Performance degrades with large files | Low | Medium | Profile; Phase 2 considers object storage if needed |
| Distributed system impossible | High | High | Acknowledged trade-off; Phase 4 migration path documented |

**Mitigation Strategy**:
- Phase 1 (Current): Document clear write-read pattern; manual cleanup
- Phase 2: Add Redis for job status; artifact storage remains shared FS
- Phase 4: Migration to S3/MinIO when multi-region needed

---

## Future Evolution

### Phase 2 Evolution
Keep shared filesystem, but add queue for async coordination:
- Redis manages job state (queued, running, done)
- Shared filesystem still holds artifacts
- Better decoupling of request/response cycle

### Phase 4 Evolution
Migrate to object storage:
- Replace shared filesystem with S3/MinIO
- No code changes (abstract storage layer)
- Enables multi-region deployment
- Better resilience and scaling

---

## Public-Safe Note

This ADR describes a general pattern of using shared storage for MVP systems. The specific paths (/data/shared/, /app/shared_data/) are generic container paths, not revealing actual infrastructure.

**Safe for public portfolio distribution**: ✅ Yes

---

## Related ADRs

- **ADR-001**: Separation of services that need artifact exchange
- **ADR-003**: FastAPI as compute service writing artifacts
- **ADR-004**: ClearML metadata coordination with artifact storage

---

## References

This decision aligns with:
- MVP/prototype patterns (simplicity first)
- Pragmatic architecture (choose simple until proof of need for complex)
- Docker best practices (volume mounting for state)
