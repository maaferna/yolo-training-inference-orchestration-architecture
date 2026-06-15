# Sanitization Reference Card

**Print this out or bookmark for quick reference during implementation.**

---

## The 4 Critical Path Replacements

### Replacement 1
```
Find:    /app/compute_service/outputs
Replace: /app/compute_service/outputs
```

### Replacement 2
```
Find:    /app/web_service/outputs
Replace: /app/web_service/outputs
```

### Replacement 3
```
Find:    /home/user/ml_projects/outputs
Replace: /host/shared_artifacts
```

### Replacement 4
```
Find:    /home/user/outputs
Replace: /host/shared_artifacts
```

---

## The 2 Critical Model Name Replacements

### Replacement 5
```
Find:    ProjectConfiguration
Replace: ProjectConfiguration
```

### Replacement 6
```
Find:    DatasetConfig
Replace: DatasetConfig
```

---

## Verification Commands

Run after all replacements:

```bash
# Should all return nothing (clean)
grep -r "compute_service_" docs/ examples/ || echo "✅ CLEAN"
grep -r "/home/user" docs/ examples/ || echo "✅ CLEAN"
grep -r "/app/web_service" docs/ examples/ || echo "✅ CLEAN"
grep -r "ProjectConfiguration" docs/ examples/ || echo "✅ CLEAN"
```

---

## Priority Files

| File | Replacements | Effort |
|------|--------------|--------|
| 06-docker-runtime-architecture.md | 8-12 | 5 min |
| 18-inference-result-synchronization.md | 25-30 | 10 min |
| 17-technical-responsibilities.md | 12-15 | 5 min |
| ADR-001-path-translation-layer.md | 8-10 | 5 min |
| PORTFOLIO_RESUME_CONTENT.md | 2-3 | 2 min |

**Total**: 60-80 replacements | ~30 minutes

---

## Git Commit Template

```bash
git add -A

git commit -m "docs(sanitization): generalize paths and model names for public release

- Replace /app/compute_service/outputs with /app/compute_service/outputs
- Replace /home/user/outputs with /host/shared_artifacts
- Replace /app/web_service/outputs with /app/web_service/outputs
- Replace ProjectConfiguration with ProjectConfiguration
- Replace DatasetConfig with DatasetConfig

This prepares the repository for public publication."

git push origin master
```

---

## Final Checklist

- [ ] All 4 path replacements done
- [ ] All 2 model name replacements done
- [ ] All 4 verification commands pass (0 results)
- [ ] Manual review of main files completed
- [ ] Git commit executed
- [ ] Changes pushed to GitHub

---

## How to Use in VS Code

1. Press `Ctrl+H` (Windows/Linux) or `Cmd+H` (Mac)
2. Enter find term from this card
3. Enter replace term from this card
4. Click "Replace All" (or manually verify each)
5. Move to next replacement
6. After all 6 replacements, run verification commands

---

**Done in ~50 minutes. Result: Public-ready repository!**

