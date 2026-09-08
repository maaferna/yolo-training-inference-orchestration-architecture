# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting the key architectural decisions for the YOLO Training & Inference Orchestration Architecture.

## What are ADRs?

ADRs are records of architecturally significant decisions: the issues that motivated them, their context, and the rationale for choosing a particular solution. They provide a way to capture **why** we chose certain approaches, not just **what** we chose.

Each ADR follows a standard format:
- **Status**: Accepted, Proposed, Deprecated, Superseded
- **Context**: The issue and factors driving the decision
- **Decision**: What we decided to do
- **Consequences**: What follows from this decision
- **Alternatives Considered**: Other options we evaluated
- **Risks**: Known risks and mitigations
- **Public-Safe Note**: Confirmation that ADR contains no proprietary details

## ADRs in This Repository

| # | Title | Status | Iteration | Focus |
|---|-------|--------|------|-------|
| 001 | Separate Django Web Orchestration from FastAPI AI Processing | ✅ Accepted | initial | Architecture |
| 002 | Use Shared Artifact Storage as Initial Integration Mechanism | ✅ Accepted | initial | Storage |
| 003 | Use FastAPI as GPU-Backed AI Service Boundary | ✅ Accepted (amended by 009) | initial | Compute |
| 004 | Use ClearML for Experiment Tracking | ⤴ Superseded by 012 | initial | **MLOps** |
| 005 | Use SAHI for High-Resolution Small-Object Inference | ✅ Accepted | initial | Inference |
| 006 | Use Notebooks as Auxiliary Research Workflow | ✅ Accepted | initial | **MLOps** |
| 007 | Tracking Tool Evaluation: ClearML over MLflow and W&B | ⤴ Superseded by 012 | initial | **MLOps** |
| 008 | Path Translation Layer for Multi-Container Artifact Synchronization | ⤴ Superseded by 011 | initial | Storage |
| 009 | Execute Jobs as Submit/Poll on In-Process Pools, Without a Broker | ✅ Accepted (amends 003) | revision | Compute |
| 010 | Keep the Model Reference in a Transactional Registry with Human Promotion | ✅ Accepted | revision | **MLOps** |
| 011 | Mount Shared Storage at the Same Path in Every Container | ✅ Accepted (supersedes 008) | revision | Storage |
| 012 | Withdraw the SaaS-Default Tracking Tool; Self-Hosted Tracking-Only, Not Deployed | ✅ Accepted — not implemented (supersedes 004, 007) | revision | **MLOps** |
| 013 | Compute Detection Metrology as a Job Type of the AI Service | ✅ Accepted | revision | Compute |

### Reading Guide by Topic

#### 🏗️ Core Architecture
- **ADR-001**: Why we separate web (Django) from compute (FastAPI)
- **ADR-002**: Where models and artifacts live (shared storage)
- **ADR-003**: Why FastAPI is our compute boundary
- **ADR-008**: How container paths became web-visible URLs in the initial iteration (superseded)
- **ADR-011**: Why the later revision mounts one path everywhere and translates nothing
- **ADR-009**: Why the later revision answered timeouts with submit/poll on in-process pools, not a queue
- **ADR-013**: Why detection metrology is a job type of the AI service

#### 📊 MLOps & Experiment Management
- **ADR-012**: The tracking decision as it stands — the initial tool withdrawn, a self-hosted tracking-only server decided and not deployed — **start here**
- **ADR-004**: The initial tracking decision and its architecture (superseded)
- **ADR-007**: The evaluation behind it — why ClearML over MLflow and Weights & Biases (superseded)
- **ADR-010**: The model registry: versions, fingerprints, human promotion, one transaction
- **ADR-006**: Why notebooks are research tools, not production

#### 🔬 Inference & Models
- **ADR-005**: Why SAHI for small-object detection

> The race condition on the file-based model reference documented in
> `../10-continuous-improvement-training.md` is closed by ADR-010. The reading order across
> iterations is `initial` ADRs first, then `docs/evolution/00-what-came-next.md`, then the
> `revision` ADRs.

## ADR Template

Each ADR follows this structure:

```markdown
# ADR-XXX: [Title]

**Status**: Accepted | Proposed | Deprecated | Superseded  
**Iteration**: initial | revision  
**Public-Safe**: Yes | Annotated

## Context

[Background and issue motivating the decision]

## Decision

[What we decided]

## Consequences

### Benefits
- [Positive outcomes]

### Drawbacks
- [Negative outcomes]

## Alternatives Considered

### Alternative 1: [Name]
[Why we didn't choose this]

### Alternative 2: [Name]
[Why we didn't choose this]

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Risk] | High/Med/Low | High/Med/Low | [How we handle it] |

## Public-Safe Note

This ADR contains no proprietary implementation details, credentials, real names, or confidential information. It is safe for public distribution as portfolio documentation.
```

## How to Use These ADRs

### As a Technical Reference
Use ADRs to understand the rationale behind architectural choices. Each ADR explains:
- Why we chose this approach
- What constraints we considered
- What we knew about limitations (and didn't overclaim)
- How this fits into the broader evolution roadmap

### As a Portfolio Resource
These ADRs demonstrate:
- Thoughtful architectural decision-making
- Honest assessment of tradeoffs and limitations
- Evolution-first mindset (designing for growth, not building for infinite scale)
- Professional documentation practices

### As Interview Discussion Points
You can reference specific ADRs when discussing:
- System design thinking
- Pragmatic architectural choices
- How you balance MVP pragmatism with future scaling
- How you document and communicate architectural decisions

## Relationship to Other Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **ADR (this directory)** | Document architectural decisions | When you want to understand the "why" |
| **../../../README.md** | Argument, start-here table and full index | When you want the complete story |
| **../02-system-architecture.md** | Technical architecture diagram | When you want the baseline |
| **../16-production-evolution-roadmap.md** | Evidence-triggered evolution path | When you want to understand growth |

## Contributing New ADRs

When proposing new architectural decisions:
1. Create new ADR file: `docs/architecture/adr/ADR-NNN-title.md`
2. Follow the template above
3. Be specific about context and tradeoffs
4. Always include a Public-Safe note
5. Update this README with a link

---

*ADRs are intentionally written to be public-safe for portfolio and hiring contexts.*  
*All contain no proprietary details, credentials, or implementation secrets.*
