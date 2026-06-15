# Sanitization Implementation Guide
## Step-by-Step Instructions for Public Release

**Estimated Time**: 45-60 minutes  
**Difficulty**: Very Easy (automated find-replace)  
**Risk**: Low (changes are straightforward renames)  

---

## Quick Start (TL;DR)

If you just want to do it quickly:

```bash
# VS Code: Open Find & Replace (Ctrl+H)
# Execute these 4 find-replace operations in order:

1. Find: /app/compute_service  →  Replace: /app/compute_service
2. Find: /app/web_service          →  Replace: /app/web_service
3. Find: /home/user               →  Replace: /host
4. Find: ProjectConfiguration           →  Replace: ProjectConfiguration
5. Find: DatasetConfig               →  Replace: DatasetConfig

# After replacements, run verification:
grep -r "compute_service_\|/home/user\|ProjectConfiguration\|DatasetConfig" docs/ && echo "FOUND!" || echo "✅ CLEAN"

# Commit and push
git add -A
git commit -m "docs(sanitization): generalize paths and model names for public release"
git push origin master
```

---

## Detailed Step-by-Step Guide

### Step 1: Open Find & Replace

**VS Code**:
- Keyboard: `Ctrl+H` (Windows/Linux) or `Cmd+Shift+H` (Mac)
- Menu: Edit → Replace in Files

**GitHub Web Editor**:
- Open file → Edit mode → Use browser find (Ctrl+F)

### Step 2: Path Replacements (Priority 1)

#### 2.1 Replace: `/app/compute_service` → `/app/compute_service`

**In VS Code Find & Replace**:
- Find: `/app/compute_service`
- Replace: `/app/compute_service`
- Click "Replace All"

**Files Affected**:
- docs/architecture/18-inference-result-synchronization.md (20+ refs)
- docs/architecture/06-docker-runtime-architecture.md (5+ refs)
- docs/architecture/adr/ADR-001-path-translation-layer.md (5+ refs)
- docs/architecture/04-system-flow.md (1-2 refs)
- docs/architecture/13-error-handling-and-fallbacks.md (1-2 refs)

**Expected Result**: Should replace ~34-35 occurrences

**Verification**:
```bash
grep -r "compute_service" docs/
# Should return 0 results
```

---

#### 2.2 Replace: `/app/web_service` → `/app/web_service`

**In VS Code Find & Replace**:
- Find: `/app/web_service`
- Replace: `/app/web_service`
- Click "Replace All"

**Files Affected**:
- docs/architecture/18-inference-result-synchronization.md (10+ refs)
- docs/architecture/06-docker-runtime-architecture.md (3+ refs)
- docs/architecture/adr/ADR-001-path-translation-layer.md (3+ refs)

**Expected Result**: Should replace ~16-17 occurrences

**Verification**:
```bash
grep -r "web_service" docs/
# Should return 0 results
```

---

#### 2.3 Replace: `/home/user` → `/host`

**In VS Code Find & Replace**:
- Find: `/home/user`
- Replace: `/host`
- Click "Replace All"

**Files Affected**:
- docs/architecture/18-inference-result-synchronization.md (8+ refs)
- docs/architecture/06-docker-runtime-architecture.md (3+ refs)
- docs/architecture/adr/ADR-001-path-translation-layer.md (5+ refs)
- docs/architecture/04-system-flow.md (1+ ref)
- docs/architecture/13-error-handling-and-fallbacks.md (2+ refs)

**Expected Result**: Should replace ~20 occurrences

**Important**: After this replacement, check for any references to `/home/user/ml_projects` or `/home/user/shared_configs` that might need separate handling.

**Verification**:
```bash
grep -r "/home/user" docs/
# Should return 0 results
```

---

### Step 3: Model Name Replacements (Priority 2)

#### 3.1 Replace: `ProjectConfiguration` → `ProjectConfiguration`

**In VS Code Find & Replace**:
- Find: `ProjectConfiguration`
- Replace: `ProjectConfiguration`
- Click "Replace All"

**Files Affected**:
- docs/architecture/08-yolo-dataset-configuration-management.md (2-3 refs)
- docs/architecture/17-technical-responsibilities.md (1-2 refs)
- docs/architecture/04-system-flow.md (1-2 refs)

**Expected Result**: Should replace ~5 occurrences

**Verification**:
```bash
grep -r "ProjectConfiguration" docs/
# Should return 0 results
```

---

#### 3.2 Replace: `DatasetConfig` → `DatasetConfig`

**In VS Code Find & Replace**:
- Find: `DatasetConfig`
- Replace: `DatasetConfig`
- Click "Replace All"

**Files Affected**:
- docs/architecture/08-yolo-dataset-configuration-management.md (2-3 refs)
- docs/architecture/17-technical-responsibilities.md (1 ref)

**Expected Result**: Should replace ~4 occurrences

**Verification**:
```bash
grep -r "DatasetConfig" docs/
# Should return 0 results
```

---

#### 3.3 Optional: Replace `ClassSet` → `ClassSet`

**In VS Code Find & Replace**:
- Find: `ClassSet`
- Replace: `ClassSet`
- Click "Replace All"

**Note**: This is optional but recommended for consistency. Check context before replacing as some occurrences might be legitimate references.

**Files Affected**:
- docs/architecture/08-yolo-dataset-configuration-management.md
- docs/architecture/04-system-flow.md

**Expected Result**: Should replace ~10-15 occurrences

---

### Step 4: Verification

#### 4.1 Run Comprehensive Scan

**On macOS/Linux**:
```bash
cd <REPOSITORY_ROOT>

echo "=== SANITIZATION VERIFICATION REPORT ===" && \
echo "" && \

echo "[1] Checking for /app/compute_service references..." && \
if grep -r "/app/compute_service" docs/ > /dev/null 2>&1; then
  echo "❌ FOUND /app/compute_service references:"
  grep -r "/app/compute_service" docs/ | head -5
  echo "Total count: $(grep -r "/app/compute_service" docs/ | wc -l)"
else
  echo "✅ CLEAN - No /app/compute_service references"
fi && \
echo "" && \

echo "[2] Checking for /home/user references..." && \
if grep -r "/home/user" docs/ > /dev/null 2>&1; then
  echo "❌ FOUND /home/user references:"
  grep -r "/home/user" docs/ | head -5
else
  echo "✅ CLEAN - No /home/user references"
fi && \
echo "" && \

echo "[3] Checking for /app/web_service references..." && \
if grep -r "/app/web_service" docs/ > /dev/null 2>&1; then
  echo "❌ FOUND /app/web_service references:"
  grep -r "/app/web_service" docs/ | head -5
else
  echo "✅ CLEAN - No /app/web_service references"
fi && \
echo "" && \

echo "[4] Checking for ProjectConfiguration references..." && \
if grep -r "ProjectConfiguration" docs/ > /dev/null 2>&1; then
  echo "❌ FOUND ProjectConfiguration references:"
  grep -r "ProjectConfiguration" docs/
else
  echo "✅ CLEAN - No ProjectConfiguration references"
fi && \
echo "" && \

echo "[5] Checking for DatasetConfig references..." && \
if grep -r "DatasetConfig" docs/ > /dev/null 2>&1; then
  echo "❌ FOUND DatasetConfig references:"
  grep -r "DatasetConfig" docs/
else
  echo "✅ CLEAN - No DatasetConfig references"
fi && \
echo "" && \

echo "=== VERIFICATION COMPLETE ===" && \
echo "If all show ✅, you're ready to publish!"
```

#### 4.2 Spot-Check Key Files

After automated replacement, manually verify these files make sense:

**File**: `docs/architecture/18-inference-result-synchronization.md`
- Search for `/app/compute_service` (should have many occurrences)
- Search for `/app/web_service` (should have several occurrences)
- Search for `/host` (should have several occurrences)
- Verify the examples still illustrate the path translation concept

**File**: `docs/architecture/06-docker-runtime-architecture.md`
- Check around line 321-323 for updated paths
- Verify Docker compose example still makes sense
- Confirm mount points are clear

**File**: `docs/architecture/adr/ADR-001-path-translation-layer.md`
- Verify decision context is still clear
- Check all code examples have updated paths
- Confirm configuration examples are consistent

#### 4.3 Manual Content Review

Read through these sections to ensure changes make sense:

- [ ] README.md — Disclaimer section
- [ ] docs/architecture/02-system-architecture.md — Architecture diagram
- [ ] docs/architecture/18-inference-result-synchronization.md — Path translation section
- [ ] docs/architecture/06-docker-runtime-architecture.md — Docker compose conceptual section

---

### Step 5: Git Commit

#### 5.1 Stage Changes

```bash
# Add all modified files
git add -A

# Verify what will be committed
git status

# You should see modified files:
# - docs/architecture/04-system-flow.md
# - docs/architecture/06-docker-runtime-architecture.md
# - docs/architecture/08-yolo-dataset-configuration-management.md
# - docs/architecture/13-error-handling-and-fallbacks.md
# - docs/architecture/17-technical-responsibilities.md
# - docs/architecture/18-inference-result-synchronization.md
# - docs/architecture/adr/ADR-001-path-translation-layer.md
# - docs/architecture/04-system-flow.md (if affected)
```

#### 5.2 Create Commit

```bash
git commit -m "docs(sanitization): generalize paths and model names for public release

- Replace /app/compute_service with /app/compute_service (FastAPI)
- Replace /app/web_service with /app/web_service (Django)
- Replace /home/user with /host (host filesystem)
- Standardize ProjectConfiguration → ProjectConfiguration
- Standardize DatasetConfig → DatasetConfig
- Standardize ClassSet → ClassSet

Files updated:
- docs/architecture/18-inference-result-synchronization.md (25+ refs)
- docs/architecture/06-docker-runtime-architecture.md (8+ refs)
- docs/architecture/adr/ADR-001-path-translation-layer.md (8+ refs)
- docs/architecture/17-technical-responsibilities.md (3-5 refs)
- docs/architecture/04-system-flow.md (1-2 refs)
- docs/architecture/13-error-handling-and-fallbacks.md (2-3 refs)
- docs/architecture/08-yolo-dataset-configuration-management.md (2-3 refs)

Risk assessment:
- Before: MEDIUM (path and model name references)
- After: LOW (generalized, anonymized)

Status: Ready for public portfolio publication"
```

#### 5.3 Push to Remote

```bash
# Push to current branch
git push origin master

# Or if using main instead of master:
git push origin main

# Verify push was successful
git log --oneline -5
# You should see your sanitization commit at the top
```

---

### Step 6: GitHub Publication

#### 6.1 Verify Repository is Public

1. Go to GitHub.com
2. Navigate to your repository
3. Click "Settings" tab
4. Scroll down to "Danger Zone"
5. Verify repository visibility is "Public" ✅

#### 6.2 Add Repository Description

1. Go to repository home page
2. Click the settings icon (⚙️) next to repository name
3. Add description (max 2000 chars):

```
Generalized & anonymized architecture documentation for an AI vision platform 
integrating Django web orchestration, FastAPI GPU services, YOLO training/inference, 
SAHI high-resolution inference, ClearML experiment tracking, and synthetic dataset 
generation. Demonstrates professional MLOps patterns and production evolution planning.
```

#### 6.3 Add Topics/Tags

1. In repository settings, add topics:
   - `machine-learning`
   - `mlops`
   - `architecture`
   - `django`
   - `fastapi`
   - `docker`
   - `yolo`
   - `pytorch`

#### 6.4 Create Release/Tag (Optional)

```bash
# Create a version tag
git tag -a v1.0.0 -m "Initial public release - generalized architecture documentation"

# Push tag to remote
git push origin v1.0.0

# Or do this through GitHub UI:
# - Go to Releases
# - Click "Create a new release"
# - Select tag v1.0.0
# - Title: "Initial Public Release"
# - Description: "Generalized architecture documentation ready for portfolio publication"
```

---

## Troubleshooting

### Issue: Find & Replace Shows "0 matches"

**Problem**: You're looking for a string that doesn't exist

**Solution**:
- Verify the exact spelling
- Check if it's already been replaced
- Use grep to manually search:
  ```bash
  grep -r "search_term" docs/
  ```

### Issue: Replaced Too Much (Accidentally Replaced Good Content)

**Solution**: Undo the changes
```bash
# Undo last commit (keeping changes)
git reset --soft HEAD~1

# Or undo changes to a specific file
git checkout HEAD -- docs/architecture/filename.md

# Or undo with find-replace again (replace back)
# E.g., if you replaced too much, use Find & Replace to put things back
```

### Issue: Some Files Didn't Update

**Solution**: 
- Check file encoding (ensure UTF-8)
- Try manual replacement in those files
- Verify file is in docs/ folder (not elsewhere)

### Issue: Tests or Links are Broken

**Solution**:
- Fix links manually if they reference old names
- Verify relative links still work
- Check that referenced sections exist

---

## Post-Sanitization Checklist

- [ ] Ran verification script successfully (all checks pass)
- [ ] Spot-checked 3-4 key files manually
- [ ] No unintended changes to content
- [ ] All replacements make sense in context
- [ ] Git commit created with descriptive message
- [ ] Changes pushed to remote
- [ ] Repository is public on GitHub
- [ ] Repository has description and topics
- [ ] README is visible and clear
- [ ] No secrets or sensitive info in git history

---

## Next Steps After Sanitization

1. **Share on LinkedIn** - Announce the public release
2. **Add to Portfolio** - Link from your portfolio website
3. **Share with Community** - Post to r/MachineLearning, Hacker News, etc.
4. **Reference in Resume** - Add GitHub repository link
5. **Monitor Issues** - Respond to questions/feedback

---

## Quick Command Reference

```bash
# One-liner verification (run after each operation)
echo "✅ Path Checks:" && \
grep -r "compute_service_\|/home/user\|web_service" docs/ 2>/dev/null && echo "❌ FOUND!" || echo "CLEAN" && \
echo "✅ Name Checks:" && \
grep -r "ProjectConfiguration\|DatasetConfig" docs/ 2>/dev/null && echo "❌ FOUND!" || echo "CLEAN"

# Count replacements made
echo "Checking /app/compute_service count:" && grep -r "/app/compute_service" docs/ | wc -l
echo "Checking /app/web_service count:" && grep -r "/app/web_service" docs/ | wc -l
echo "Checking /host count:" && grep -r "/host" docs/ | wc -l
```

---

**Ready to sanitize and publish?** → Start with Step 1! 🚀
