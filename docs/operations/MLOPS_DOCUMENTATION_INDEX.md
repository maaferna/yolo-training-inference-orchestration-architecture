# MLOps Documentation Index

**Last Updated**: June 12, 2026  
**Status**: Complete  

---

## 📖 Documentation Overview

This is the central index for all MLOps documentation. Start here to find what you need.

---

## For Different Audiences

### 👨‍💻 Researchers & ML Engineers

**Start Here**: [MLOps Quick Reference Guide](MLOPS_QUICK_REFERENCE.md)

**Essential Reading**:
1. How to submit training jobs
2. How to view experiment results
3. How to reproduce past experiments
4. Troubleshooting guide

**Next**: [ADR-004: ClearML Architecture](adr/ADR-004-clearml-experiment-tracking.md)

---

### 🔧 DevOps & Infrastructure

**Start Here**: [Migration Guide: ClearML Cloud → Self-Hosted](MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md)

**Essential Reading**:
1. Phase 1: Assessment (Week 1)
2. Phase 2: Deployment (Week 2)
3. Phase 5: Operations (Ongoing)
4. Troubleshooting section

**Next**: [ADR-004: Self-Hosted Deployment Details](adr/ADR-004-clearml-experiment-tracking.md)

---

### 📊 Managers & Technical Leads

**Start Here**: [MLOps Status Report](MLOPS_STATUS_REPORT.md)

**Essential Reading**:
1. Executive Summary
2. Current Architecture
3. MLOps Maturity Assessment
4. Roadmap (Q3 2026 → 2027)

**Next**: [ADR Overview](#adr-decision-records)

---

### 🎓 New Team Members

**Start Here**: [Getting Started Checklist](#getting-started-checklist)

**Day 1**:
- [ ] Get ClearML credentials
- [ ] Read Quick Reference Guide
- [ ] Run first training job
- [ ] View results in ClearML UI

**Week 1**:
- [ ] Read all ADRs (architecture decisions)
- [ ] Understand current architecture
- [ ] Set up local development environment

---

## 📚 All Documentation

### Quick References

| Document | Purpose | Audience |
|----------|---------|----------|
| [MLOps Quick Reference](MLOPS_QUICK_REFERENCE.md) | Daily tasks, common commands | Everyone |
| [MLOps Status Report](MLOPS_STATUS_REPORT.md) | Current state, metrics, roadmap | Managers, Leads |

### Detailed Guides

| Document | Purpose | Audience |
|----------|---------|----------|
| [Migration Guide](MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md) | 4-week plan to self-hosted ClearML | DevOps, Infra |
| [ClearML Architecture](adr/ADR-004-clearml-experiment-tracking.md) | Detailed architecture & migration strategy | Architects, Leads |

### Architecture Decision Records (ADRs)

See [ADR Overview](#adr-decision-records) below

---

## 🏗️ ADR Decision Records

All architecture decisions documented as Architecture Decision Records (ADRs).

### Core Architecture

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](adr/ADR-001-web-compute-separation.md) | Separate Web & GPU Compute | ✅ Accepted |
| [ADR-002](adr/ADR-002-shared-storage.md) | Shared Artifact Storage | ✅ Accepted |
| [ADR-003](adr/ADR-003-fastapi-gpu-service.md) | FastAPI as GPU Service | ✅ Accepted |
| [ADR-004](adr/ADR-004-clearml-experiment-tracking.md) | ClearML Experiment Tracking | ✅ Accepted |

### Supporting Decisions

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-005](adr/ADR-005-django-web-interface.md) | Django for Web Interface | ✅ Accepted |
| [ADR-006](adr/ADR-006-notebooks-auxiliary-research.md) | Notebooks for Research Only | ✅ Accepted |
| [ADR-007](adr/ADR-007-clearml-experiment-tracking.md) | Alternative Tracking Tools Comparison | ✅ Accepted |

### How to Read ADRs

Each ADR follows this structure:
1. **Context**: Why this decision was needed
2. **Decision**: What we decided
3. **Consequences**: Benefits and drawbacks
4. **Alternatives Considered**: Why we chose this option
5. **Risks**: What could go wrong
6. **Future Evolution**: How this might change

---

## 🚀 Getting Started Checklist

### Day 1: Setup

- [ ] **Get ClearML Credentials**
  ```bash
  Contact MLOps team for credentials
  Save to ~/.clearml/clearml.conf
  ```

- [ ] **Verify ClearML Connection**
  ```bash
  curl https://clearml.app/version
  # Should return: {version: "X.X.X"}
  ```

- [ ] **Read Quick Reference**
  - 15 min read
  - Bookmark it!

### Day 2: First Experiment

- [ ] **Submit Training Job**
  - Via Django UI OR
  - Via FastAPI (see examples)

- [ ] **View in ClearML**
  - Go to https://clearml.app
  - Find your experiment
  - Check metrics

- [ ] **Reproduce Experiment**
  - Clone experiment in ClearML
  - Re-submit
  - Verify reproducibility

### Week 1: Deep Dive

- [ ] **Read Architecture Decisions**
  - Start with ADR-001 (overview)
  - Then ADR-004 (ClearML details)
  - Then others as relevant

- [ ] **Understand File Locations**
  ```bash
  ls -la /shared_storage/models/
  # See versioned models
  ```

- [ ] **Troubleshoot Common Issues**
  - Follow MLOPS_QUICK_REFERENCE.md
  - Ask team if stuck

### Week 2: Production Ready

- [ ] **Complete on-site training** (if available)
- [ ] **Have 5+ successful experiments** in ClearML
- [ ] **Understand your role** in the MLOps pipeline
- [ ] **Know who to contact** for issues

---

## 🔄 Current State Summary

### What's Working Now ✅

```
✅ Django Web UI
  ├── Training request submission
  ├── Model selection for inference
  └── Results visualization

✅ FastAPI Service
  ├── Training job orchestration
  ├── Inference API
  └── ClearML integration

✅ ClearML Cloud
  ├── Experiment tracking
  ├── Metrics logging
  ├── Web UI for comparison
  └── Team collaboration

✅ Model Storage
  ├── Shared filesystem
  ├── Versioned models
  └── ClearML registry links

✅ Containerization
  ├── Docker training workers
  ├── Docker FastAPI service
  └── Reproducible environments
```

### What's Coming Q3 2026 🚀

```
🚀 ClearML Self-Hosted
  ├── Deployment & setup
  ├── Experiment migration
  └── Cost reduction

🚀 Data Versioning
  ├── Track datasets
  ├── Link to experiments
  └── Reproducibility++

🚀 Infrastructure
  ├── Better monitoring
  ├── Auto-scaling workers
  └── Cost optimization
```

---

## 📊 Key Metrics to Track

### Monthly Review Items

```
✅ Training Metrics
   - Total experiments
   - Success rate
   - Avg training time

✅ Infrastructure Metrics
   - GPU utilization
   - Storage used
   - Monthly costs

✅ Team Productivity
   - Experiments per researcher
   - Time to market for models
   - Experiment reproducibility %
```

See [MLOps Status Report](MLOPS_STATUS_REPORT.md) for detailed metrics.

---

## 🆘 Troubleshooting Guide

### Can't Connect to ClearML?

→ [MLOPS_QUICK_REFERENCE.md: Troubleshooting](MLOPS_QUICK_REFERENCE.md#-troubleshooting)

### Training Job Failed?

→ [MLOPS_QUICK_REFERENCE.md: Training Job Hanging](MLOPS_QUICK_REFERENCE.md#training-job-hanging)

### Don't Know How to Do Something?

→ [MLOPS_QUICK_REFERENCE.md: Common Tasks](MLOPS_QUICK_REFERENCE.md#-common-tasks)

### Something Else?

→ Contact MLOps team or open GitHub issue

---

## 📞 Getting Help

| Issue | First Try | Escalate To |
|-------|-----------|------------|
| How do I...? | Quick Reference Guide | MLOps Team |
| Something broken | Troubleshooting section | DevOps |
| Architecture question | Read relevant ADR | Technical Lead |
| Feature request | MLOps Status Report roadmap | ML Ops Lead |

---

## 🔗 External Links

### ClearML Resources
- [Official Docs](https://clear.ml/docs/)
- [Cloud Dashboard](https://clearml.app)
- [GitHub Repository](https://github.com/allegroai/clearml)

### Project Resources
- Django UI: http://your-domain/ (set in deployment)
- FastAPI Docs: http://fastapi-service:8080/docs
- Shared Storage: /shared_storage/

---

## 📋 Document Maintenance

| Document | Update Frequency | Owner |
|----------|------------------|-------|
| Quick Reference | Quarterly | ML Ops Lead |
| Status Report | Monthly | ML Ops Lead |
| Migration Guide | Quarterly | DevOps |
| ADRs | As-needed | Technical Lead |

**Last Updated**: June 12, 2026  
**Review Cycle**: Monthly

---

## 🎯 Next Steps

1. **Pick your role above** (Researcher, DevOps, Manager, New Member)
2. **Follow the recommended reading**
3. **Bookmark the Quick Reference Guide**
4. **Ask questions!** (that's what this team is for)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 12, 2026 | Initial documentation |
| | | - ADR-001 through ADR-007 |
| | | - Migration guide completed |
| | | - Status report created |
| | | - Quick reference published |

---

**Questions?** Open an issue or contact the MLOps team.  
**Found an error?** Please report it!  
**Want to contribute?** See CONTRIBUTING.md
