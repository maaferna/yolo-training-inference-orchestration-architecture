# Quick Sanitization Implementation Guide

Execute these steps to prepare the repository for public release.

## Phase 1: Path Leakage Cleanup (5 minutes)

### Step 1a: Replace `/app/compute_service/outputs`

Open VS Code Find & Replace (`Ctrl+H`):
- **Find**: `/app/compute_service/outputs`
- **Replace**: `/app/compute_service/outputs`
- **Scope**: All files (or use Replace All)
- **Expected replacements**: 8-12

### Step 1b: Replace `/app/web_service/outputs`

- **Find**: `/app/web_service/outputs`
- **Replace**: `/app/web_service/outputs`
- **Scope**: All files
- **Expected replacements**: 5-8

### Step 1c: Replace `/home/user/ml_projects/outputs`

- **Find**: `/home/user/ml_projects/outputs`
- **Replace**: `/host/shared_artifacts`
- **Scope**: All files
- **Expected replacements**: 1-2
- **Note**: May need manual review for context

### Step 1d: Replace `/home/user/outputs`

- **Find**: `/home/user/outputs`
- **Replace**: `/host/shared_artifacts`
- **Scope**: All files
- **Expected replacements**: 3-5
- **Note**: Manual review recommended

---

## Phase 2: Model Name Consistency (10 minutes)

### Step 2a: Replace `ProjectConfiguration`

- **Find**: `ProjectConfiguration`
- **Replace**: `ProjectConfiguration`
- **Scope**: `08-yolo-dataset-configuration-management.md`, `17-technical-responsibilities.md`
- **Expected replacements**: 4-6

### Step 2b: Replace `DatasetConfig`

- **Find**: `DatasetConfig`
- **Replace**: `DatasetConfig`
- **Scope**: `08-yolo-dataset-configuration-management.md`, `17-technical-responsibilities.md`
- **Expected replacements**: 2-3

---

## Phase 3: Portfolio Polish (5 minutes)

### Step 3a: Update PORTFOLIO_RESUME_CONTENT.md

**Find**: `(/app/compute_service/outputs)`
**Replace**: `(inference output coordination)`
**Expected**: 1 replacement

**Find**: `(ProjectConfiguration, ClassSet, DetectionClass models)`
**Replace**: `(project configuration models)`
**Expected**: 1 replacement

---

## Phase 4: ADR Update (5 minutes)

### Step 4a: Update ADR-001

In `docs/architecture/adr/ADR-001-path-translation-layer.md`:

**Find**: `/app/compute_service/outputs/run_001/`
**Replace**: `/app/compute_service/outputs/run_001/`
**Expected**: 3-4 replacements

**Find**: `/home/user/outputs/run_001/`
**Replace**: `/host/shared_artifacts/run_001/`
**Expected**: 2 replacements

**Find**: `/app/web_service/outputs/run_001/`
**Replace**: `/app/web_service/outputs/run_001/`
**Expected**: 2 replacements

---

## Phase 5: Verification (10 minutes)

### Verification Checks

Run these terminal commands to verify no leakage remains:

```bash
# Check 1: No "compute_service" prefix remaining
grep -r "compute_service_" docs/ examples/ || echo "✅ CLEAN: No compute_service_ found"

# Check 2: No /home/user paths
grep -r "/home/user" docs/ examples/ || echo "✅ CLEAN: No /home/user found"

# Check 3: No /app/web_service
grep -r "/app/web_service" docs/ examples/ || echo "✅ CLEAN: No /app/web_service found"

# Check 4: No ProjectConfiguration references (if fully replaced)
grep -r "ProjectConfiguration" docs/ examples/ || echo "✅ CLEAN: No ProjectConfiguration found"
```

All should show "✅ CLEAN".

### Manual Review

After automated verification, manually review these files:

1. `docs/architecture/06-docker-runtime-architecture.md` — Read lines 320-360 (path examples)
2. `docs/architecture/18-inference-result-synchronization.md` — Read problem statement and code examples
3. `docs/architecture/17-technical-responsibilities.md` — Scan for any remaining specific names
4. `docs/portfolio/PORTFOLIO_RESUME_CONTENT.md` — Read the technical bullets

---

## Final Checklist Before Publishing

- [ ] Phase 1 complete (all path replacements done)
- [ ] Phase 2 complete (model names standardized)
- [ ] Phase 3 complete (portfolio content updated)
- [ ] Phase 4 complete (ADR updated)
- [ ] Phase 5 verification all passed
- [ ] Manual review completed
- [ ] No grep errors found (all returned "✅ CLEAN")
- [ ] Readme.md disclaimer still in place
- [ ] All cross-references still valid
- [ ] Documentation reads naturally with new terminology

---

## Git Commit

After all changes are complete:

```bash
# Stage all changes
git add -A

# Commit with semantic message
git commit -m "docs(sanitization): generalize internal paths and model names for public release

- Replace /app/compute_service/outputs with /app/compute_service/outputs
- Replace /home/user/outputs with /host/shared_artifacts
- Replace /app/web_service/outputs with /app/web_service/outputs
- Replace ProjectConfiguration with ProjectConfiguration
- Replace DatasetConfig with DatasetConfig
- Update portfolio content for public readability
- Update ADR-001 with generalized path examples

This prepares the repository for public publication while maintaining
all architectural documentation quality and clarity."

# Push to GitHub
git push origin master
```

---

## GitHub Configuration (After Push)

1. Go to repository Settings
2. Update Description:
   ```
   Generalized and anonymized architecture documentation for an AI vision 
   platform integrating web orchestration, GPU-backed ML services, dataset 
   configuration management, and model training orchestration.
   ```
3. Add Topics: `ai`, `architecture`, `system-design`, `mlops`, `portfolio`
4. Optionally enable GitHub Pages for docs

---

## Estimated Timeline

- Phase 1: 5 minutes
- Phase 2: 10 minutes
- Phase 3: 5 minutes
- Phase 4: 5 minutes
- Phase 5 verification: 10 minutes
- Manual review: 10 minutes
- Git operations: 5 minutes

**Total: ~50 minutes**

---

**Ready to proceed?** Follow this guide in order, and your repository will be publication-ready!

