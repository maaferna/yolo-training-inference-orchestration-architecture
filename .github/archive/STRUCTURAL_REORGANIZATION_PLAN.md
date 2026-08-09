# Structural Reorganization Plan

**Date**: June 14, 2026  
**Purpose**: Clean up root and docs/ directory structure

---

## Current State Analysis

### 🔴 Issues Identified

1. **Root Directory Bloat** (40+ uppercase .MD files)
   - Temporary working documents mixed with permanent content
   - Status reports, audit notes, and transitory content
   - Creates visual clutter and confusion

2. **Shell Scripts in Root** (5 .sh files)
   - Validation and checking scripts scattered in root
   - Should be organized in `scripts/` subdirectory
   - Harder to discover and maintain

3. **docs/ Directory Mixed Content**
   - Core architecture docs (numbered 01-20)
   - Portfolio docs (PORTFOLIO_*.md)
   - Transitory docs (MLOPS_*.md, MIGRATION_*.md)
   - Should be better organized

### ✅ What's Currently Good

- ✅ `docs/architecture/` — Well-organized (21 files)
- ✅ `docs/portfolio/` — Clean (2 files)
- ✅ `docs/operations/` — Exists but minimal content
- ✅ Numbered docs (01-20) — Good naming convention
- ✅ ADR subfolder — Professional structure

---

## Reorganization Strategy

### Phase 1: Move Shell Scripts

**From Root → `scripts/`**

```
Root Level (BEFORE):
├── complete-sanitization-check.sh
├── final-sanitization-verification.sh
├── production-ready-check.sh
├── production-ready-final-check.sh
└── validate-sanitization.sh

Root Level (AFTER):
└── scripts/
    ├── complete-sanitization-check.sh
    ├── final-sanitization-verification.sh
    ├── production-ready-check.sh
    ├── production-ready-final-check.sh
    └── validate-sanitization.sh
```

**Action**: Create `scripts/` directory and move all `.sh` files there

---

### Phase 2: Categorize Uppercase .MD Files

**Root-level uppercase .MD files analysis:**

| File | Category | Recommendation |
|------|----------|-----------------|
| README.md | ✅ Keep | Essential (root level) |
| CONTRIBUTING.md | ✅ Keep | Standard (root level) |
| LICENSE | ✅ Keep | Standard (root level) |
| INDEX.md | ❓ Decide | Project index (consider move to docs/) |
| public-safety-checklist.md | ⚠️ Transitory | → `docs/operations/` or archive |
| ANALYSIS-NEW-PROJECT-DETAILS.md | ⚠️ Transitory | → GitHub Archive |
| PHASE-1-INTEGRATION-REPORT.md | ⚠️ Transitory | → GitHub Archive |
| AUDIT_DOCUMENTATION_INDEX.md | ✅ Keep | Public release audit (root) |
| SANITIZATION_*.md (4 files) | ✅ Keep | Public release guides (root) |
| PUBLIC_RELEASE_RISK_ASSESSMENT.md | ✅ Keep | Public release docs (root) |
| All MLOPS_*.md (6 files) | ⚠️ Transitory | → GitHub Archive |
| All CASE-STUDY*.md (3 files) | ⚠️ Transitory | → GitHub Archive |
| All STATUS/REPORT files (15+ files) | ⚠️ Transitory | → GitHub Archive |
| PORTFOLIO_*.md files | ❓ Decide | In docs/portfolio/ already? Check |
| Others (ARCHITECTURE-REVIEW, etc.) | ⚠️ Transitory | → GitHub Archive |

**Keep in Root** (essential):
- README.md
- CONTRIBUTING.md
- LICENSE
- AUDIT_DOCUMENTATION_INDEX.md
- PUBLIC_RELEASE_RISK_ASSESSMENT.md
- SANITIZATION_QUICK_GUIDE.md
- SANITIZATION_SUMMARY.md
- SANITIZATION_REFERENCE_CARD.md
- public-safety-checklist.md

**Move to Archive** (transitory/working documents):
- 30+ status reports, working docs, and audit notes
- MLOPS_*.md series
- CASE-STUDY*.md series
- AUDIT-REVIEW-*.md
- ARCHITECTURE-REVIEW-*.md
- CONTENT-AUDIT-*.md
- All similar transitory files

---

### Phase 3: docs/ Directory Organization

**Current**:
```
docs/
├── 01-context-and-problem.md
├── ... (20 numbered architecture files)
├── MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md
├── MLOPS_DELIVERY_REPORT.md
├── ... (6 MLOPS_*.md files)
├── PORTFOLIO_IMPLEMENTATION_GUIDE.md
├── PORTFOLIO_RESUME_CONTENT.md
├── adr/
├── architecture/
├── operations/
└── portfolio/
```

**Proposed**:
```
docs/
├── 01-context-and-problem.md (move into architecture/)
├── ... (move numbered files into architecture/)
├── adr/
├── architecture/
│   ├── 01-context-and-problem.md
│   ├── ... (20 files)
│   └── 20-synthetic-dataset-generation-pipeline.md
├── portfolio/
│   ├── PORTFOLIO_IMPLEMENTATION_GUIDE.md
│   └── PORTFOLIO_RESUME_CONTENT.md
├── operations/
│   └── (empty or minimal)
└── archive/ (transitory docs)
    ├── MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md
    ├── MLOPS_DELIVERY_REPORT.md
    └── (other working docs if keeping in docs/)
```

**OR Better: Move to `.github/archive/docs/`**

```
.github/
└── archive/
    ├── docs/ (transitory working docs)
    │   ├── MLOPS_DELIVERY_REPORT.md
    │   ├── MIGRATION_CLEARML_CLOUD_TO_SELFHOSTED.md
    │   └── ...
    └── scripts/ (validation scripts)
        ├── complete-sanitization-check.sh
        ├── production-ready-*.sh
        └── ...
```

---

## Specific Action Items

### ✅ Action 1: Create `scripts/` Directory

```bash
mkdir -p scripts
mv complete-sanitization-check.sh scripts/
mv final-sanitization-verification.sh scripts/
mv production-ready-check.sh scripts/
mv production-ready-final-check.sh scripts/
mv validate-sanitization.sh scripts/
```

**Result**: Clean root, organized scripts

---

### ✅ Action 2: Archive Transitory Docs to `.github/archive/`

**Create structure**:
```bash
mkdir -p .github/archive/docs
mkdir -p .github/archive/root-markdown-files
```

**Move transitory root-level .MD files** (~30 files):
```bash
# These are working/status docs from iterations
# Move to .github/archive/root-markdown-files/

mv ANALYSIS-NEW-PROJECT-DETAILS.md .github/archive/root-markdown-files/
mv ARCHITECTURE-REVIEW-COMPLETE.md .github/archive/root-markdown-files/
mv AUDIT-REVIEW-AND-NEXT-STEPS.md .github/archive/root-markdown-files/
mv CASE-STUDY*.md .github/archive/root-markdown-files/
mv CODE-SECURITY-AUDIT.md .github/archive/root-markdown-files/
mv COMPREHENSIVE-REVIEW-STATUS.md .github/archive/root-markdown-files/
# ... (all other transitory files)
```

**Move transitory docs/ directory files**:
```bash
mkdir -p .github/archive/docs
mv docs/MLOPS_*.md .github/archive/docs/
mv docs/MIGRATION_*.md .github/archive/docs/
```

---

### ✅ Action 3: Clean Root Directory

**Keep in root**:
- README.md
- CONTRIBUTING.md
- LICENSE
- AUDIT_DOCUMENTATION_INDEX.md
- PUBLIC_RELEASE_RISK_ASSESSMENT.md
- SANITIZATION_*.md (3 files)
- public-safety-checklist.md

**Result**: Root with only essential files (8 files)

---

### ✅ Action 4: Reorganize `docs/`

**Option A: Keep flat structure**
```
docs/
├── 01-context-and-problem.md
├── ... (numbered files)
├── adr/
├── architecture/ (move numbered files here)
├── portfolio/
├── operations/
└── README.md (new - navigation)
```

**Option B: Move numbered files into architecture/**
```
docs/
├── adr/
├── architecture/
│   ├── 01-context-and-problem.md
│   ├── ... (numbered files)
│   └── 20-synthetic-dataset-generation-pipeline.md
├── portfolio/
├── operations/
└── README.md (navigation guide)
```

**Recommendation**: Option B is cleaner

---

## Summary of Changes

### Before
```
Root: 45+ files (.MD + .sh)
docs/: Mixed content (architecture + portfolio + transitory)
.sh files: Scattered in root
Scripts: Not organized
Archive: None
```

### After
```
Root: 8-10 essential files
docs/architecture/: 20 numbered files (organized)
docs/portfolio/: 2 files
docs/architecture/adr/: ADRs
scripts/: 5 shell scripts
.github/archive/: 30+ transitory files
.github/archive/docs/: Transitory docs
```

---

## Recommended Implementation Order

### Week 1 (Priority: HIGH)
1. ✅ Create `scripts/` directory
2. ✅ Move `.sh` files to `scripts/`
3. ✅ Archive transitory root .MD files to `.github/archive/root-markdown-files/`

### Week 2 (Priority: MEDIUM)
4. ✅ Move numbered docs 01-20 into `docs/architecture/`
5. ✅ Move transitory docs/ files to `.github/archive/docs/`
6. ✅ Create `docs/README.md` navigation guide

### Week 3 (Priority: LOW)
7. ⚠️ Review and consolidate remaining transitory content
8. ⚠️ Update any references/links

---

## Git Considerations

### Before Archiving

```bash
# Verify all files in archive will be preserved
git log --follow .github/archive/

# Create an archive branch for reference
git branch archive/transitory-docs

# Tag the current state
git tag pre-archive-cleanup
```

### Archiving Process

```bash
# Phase 1: Move scripts
git add scripts/
git commit -m "chore(refactor): move shell scripts to scripts/ directory"

# Phase 2: Archive transitory root docs
git add .github/archive/root-markdown-files/
git rm *.MD (selectively)
git commit -m "chore(archive): move transitory root-level docs to .github/archive/"

# Phase 3: Archive transitory docs/ files
git add .github/archive/docs/
git rm docs/MLOPS_*.md docs/MIGRATION_*.md
git commit -m "chore(archive): move transitory documentation to .github/archive/docs/"

# Phase 4: Reorganize docs/
git add docs/architecture/
git commit -m "docs(refactor): move numbered architecture docs into docs/architecture/"
```

---

## File Preservation

### Archive Locations

All files will be preserved (nothing deleted):
- `.github/archive/root-markdown-files/` — Root-level working docs
- `.github/archive/docs/` — Transitory docs from docs/ directory
- `.github/archive/scripts/` — Backup of shell scripts (if desired)

### Recovery

If any archived file is needed:
```bash
# View archive
ls -la .github/archive/root-markdown-files/
ls -la .github/archive/docs/

# Restore if needed
git show archive-branch:docs/MLOPS_DELIVERY_REPORT.md
```

---

## Estimated Timeline

- **Phase 1 (scripts)**: 5 minutes
- **Phase 2 (archive root docs)**: 10 minutes
- **Phase 3 (archive docs/ files)**: 5 minutes
- **Phase 4 (reorganize docs/)**: 10 minutes
- **Verification & cleanup**: 10 minutes

**Total: ~40 minutes**

---

## Questions for User

1. **Archive strategy**: `.github/archive/` or complete removal?
   - Recommended: `.github/archive/` (preserve history, reduce clutter)

2. **Numbered files**: Move into `docs/architecture/` or keep in `docs/`?
   - Recommended: Move to `docs/architecture/` (better organization)

3. **INDEX.md**: Keep in root or move to `docs/`?
   - Recommendation: Move to `docs/` as navigation guide

4. **Operations folder**: Any content to add?
   - Recommendation: Add deployment, monitoring, troubleshooting docs

---

**Status**: Ready for implementation approval

