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

| # | Title | Status | Date | Focus |
|---|-------|--------|------|-------|
| 001 | Separate Django Web Orchestration from FastAPI AI Processing | ✅ Accepted | June 2026 | Architecture |
| 002 | Use Shared Artifact Storage as Initial Integration Mechanism | ✅ Accepted | June 2026 | Storage |
| 003 | Use FastAPI as GPU-Backed AI Service Boundary | ✅ Accepted | June 2026 | Compute |
| 004 | Use ClearML for Experiment Tracking | ✅ Accepted | June 2026 | **MLOps** |
| 005 | Use SAHI for High-Resolution Small-Object Inference | ✅ Accepted | June 2026 | Inference |
| 006 | Use Notebooks as Auxiliary Research Workflow | ✅ Accepted | June 2026 | **MLOps** |
| 007 | ClearML Experiment Tracking Alternatives & Rationale | ✅ Accepted | June 2026 | **MLOps** |

### Reading Guide by Topic

#### 🏗️ Core Architecture
- **ADR-001**: Why we separate web (Django) from compute (FastAPI)
- **ADR-002**: Where models and artifacts live (shared storage)
- **ADR-003**: Why FastAPI is our compute boundary

#### 📊 MLOps & Experiment Management
- **ADR-004**: ClearML experiment tracking **[Includes migration strategy to self-hosted]**
- **ADR-006**: Why notebooks are research tools, not production
- **ADR-007**: Alternative tracking solutions and why ClearML won

#### 🔬 Inference & Models
- **ADR-005**: Why SAHI for small-object detection
- **ADR-007** (future): Model registry and production model selection

## ADR Template

Each ADR follows this structure:

```markdown
# ADR-XXX: [Title]

**Status**: Accepted | Proposed | Deprecated | Superseded  
**Date**: YYYY-MM-DD  
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
| **CASE-STUDY.md** | Narrative explanation of full system | When you want the complete story |
| **LEARNING-PATH.md** | Guided reading by audience | When you need structured guidance |
| **docs/02-system-architecture.md** | Technical architecture diagram | When you want the current state |
| **docs/15-production-evolution-roadmap.md** | Future scaling directions | When you want to understand growth |

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
