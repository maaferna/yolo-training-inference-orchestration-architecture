# Public Release Sanitization Guide

This document outlines the sanitization process for preparing this repository for public release while protecting confidential information.

## Before Any Public Release

### Critical Rule

**This repository contains NO production code.** All content is architecture documentation with placeholder examples. However, some references in code comments or filenames could leak confidential information if not carefully reviewed.

---

## Forbidden Terms Checklist

### Never Commit These Terms

❌ **Real Company Names**
- Customer names (e.g., "ACME Corporation", "TechCorp", real company names)
- Use: `CUSTOMER_NAME_PLACEHOLDER`, `PROJECT_STAKEHOLDER_PLACEHOLDER`

❌ **Real IP Addresses**
- Actual IP addresses (e.g., "192.168.1.100", "10.20.30.40")
- Use: `IP_ADDRESS_PLACEHOLDER`, `COMPUTE_NODE_IP_PLACEHOLDER`

❌ **Real Hostnames**
- Actual server names (e.g., "gpu-prod-01.company.com", "training-server")
- Use: `HOSTNAME_PLACEHOLDER`, `COMPUTE_NODE_HOSTNAME`

❌ **Real Domain Names**
- Actual domains (e.g., "company.internal", "ai-ml.example.com")
- Use: `DOMAIN_PLACEHOLDER`, `INTERNAL_REGISTRY_PLACEHOLDER`

❌ **Real Model Names**
- Proprietary model names (e.g., "OmniDetect-v3", "CompanyAI")
- Use: `MODEL_NAME_PLACEHOLDER`, `CUSTOM_DETECTION_MODEL`

❌ **Real Dataset Names**
- Proprietary datasets (e.g., "StreetView-2024", "InternalInventory")
- Use: `DATASET_NAME_PLACEHOLDER`, `PROPRIETARY_TRAINING_DATA`

❌ **Credentials**
- API keys (e.g., "sk-1234567890abcdef")
- Use: `API_KEY_PLACEHOLDER`

❌ **Real URLs to Internal Services**
- Internal GitLab/GitHub instances (e.g., "https://gitlab.company.internal/ai/training")
- Use: `INTERNAL_REPOSITORY_URL_PLACEHOLDER`

❌ **Real Cloud Credentials**
- AWS Access Keys, Azure storage keys
- Use: `AWS_ACCESS_KEY_PLACEHOLDER`, `CLOUD_CREDENTIALS_PLACEHOLDER`

❌ **Real S3 Bucket Names**
- Corporate bucket names (e.g., "company-ml-models-prod", "internal-datasets")
- Use: `S3_BUCKET_PLACEHOLDER`, `OBJECT_STORAGE_PLACEHOLDER`

❌ **Real Database Names**
- Proprietary database names (e.g., "training_prod", "inference_cache")
- Use: `DATABASE_NAME_PLACEHOLDER`, `METADATA_STORE_PLACEHOLDER`

❌ **Internal Process Names**
- Proprietary processes or algorithms (e.g., "EnhancedAugmentation-3", "ProprietaryNMS")
- Use: `PROPRIETARY_ALGORITHM_PLACEHOLDER`

---

## Allowed Placeholder Examples

### Good Placeholder Patterns

✓ **Metric Values**: `ILLUSTRATIVE_METRIC_VALUE`, `EXAMPLE_mAP50`
✓ **Dataset References**: `DATASET_PLACEHOLDER`, `TRAINING_DATA_SAMPLE`
✓ **Model References**: `MODEL_PATH_PLACEHOLDER`, `MODEL_NAME_PLACEHOLDER`
✓ **Paths**: `/path/to/shared/data`, `/app/shared_data/`
✓ **Framework Names**: `FastAPI`, `Django`, `PyTorch`, `YOLO` (these are public)
✓ **Standard Algorithms**: `YOLO`, `SAHI`, `NMS` (these are public)
✓ **Standard Services**: `PostgreSQL`, `Redis`, `Kubernetes` (these are public)
✓ **Generic Names**: `PROJECT_NAME_PLACEHOLDER`, `USER_ID_PLACEHOLDER`

### JSON Examples with Safe Placeholders

**Good**:
```json
{
  "dataset_id": "DATASET_PLACEHOLDER_001",
  "model_name": "yolo_v11",
  "training_date": "2024-01-15",
  "metrics": {
    "mAP50": 0.85
  }
}
```

**Bad** (contains internal data):
```json
{
  "dataset_id": "acme-corp-street-view-2024",
  "model_name": "OmniDetect-v3-proprietary",
  "training_date": "2024-01-15",
  "metrics": {
    "mAP50": 0.85
  }
}
```

---

## Files Never to Publish

### Absolutely Forbidden Files

❌ **Never include**:
- `credentials.env` (API keys, passwords)
- `secrets.yaml` (cloud credentials)
- `.env` files with real values
- Database backups or exports
- Training datasets (raw images)
- Trained model weights (.pt, .pth files > 100MB)
- Real customer data samples
- Internal logs with sensitive information
- Database connection strings with real hosts

### Git Configuration

```bash
# .gitignore - These should already be here

# Credentials
*.env
secrets/
credentials.yaml
.aws/
.gcloud/

# Data files
datasets/
*.csv (with real data)
*.xlsx (with real data)

# Model weights
*.pt
*.pth
*.weights (large model files)

# Logs with sensitive data
logs/
*.log

# IDE/local
.vscode/settings.json
.idea/
```

---

## Code Comment Audit

### What to Check

Before publishing, search for these patterns in code comments:

```bash
# Commands to find potentially sensitive comments

grep -r "CUSTOMER\|COMPANY\|INTERNAL\|SECRET\|CREDENTIALS\|TOKEN\|API_KEY" \
  --include="*.py" \
  --include="*.md" \
  --include="*.yaml" \
  --include="*.json" \
  docs/

grep -r "192\.|10\.|172\." --include="*.md" docs/  # IP addresses
grep -r "http://.*\.internal\|https://.*\.internal" docs/  # Internal URLs
grep -r "[a-zA-Z0-9]{20,}" docs/  # Potential API keys (long hex strings)
```

---

## Manual Review Checklist

Before pushing to public GitHub:

### 1. Documentation Review

- [ ] README.md: No real company names
- [ ] All docs/ files: No real metrics/data (use PLACEHOLDER format)
- [ ] All docs/ files: No internal URLs or IP addresses
- [ ] All examples: Use placeholder values
- [ ] API examples: No real authentication tokens

### 2. Code Artifacts

- [ ] No .py files (Python source code absent)
- [ ] No actual Docker/docker-compose files (only conceptual YAML)
- [ ] No shell scripts with real commands
- [ ] No configuration files with real credentials

### 3. Path/Filesystem References

- [ ] All file paths generic (/app/shared_data, /data/shared/, not company-specific)
- [ ] No references to real mount points
- [ ] No hardcoded domain names

### 4. Example Data

- [ ] API payload examples use placeholder values
- [ ] JSON examples use PLACEHOLDER_VALUE format
- [ ] No real model names or dataset names
- [ ] No real training metrics from production

### 5. Diagrams

- [ ] Mermaid diagrams use generic service names (FastAPI, Django, etc.)
- [ ] No real component names
- [ ] No real IP addresses or hostnames

### 6. Final Pass

```bash
# Search for numbers that might be real data
grep -Er "[0-9]{5,}" docs/ | grep -v "^[0-9.]*$"

# Search for suspicious patterns
grep -Er "\.internal|\.corp|\.company" docs/

# Search for potential credentials (long hex strings)
grep -Er "[a-fA-F0-9]{32,}" docs/
```

---

## Sanitization Workflow

### Step 1: Audit

```bash
# Create audit report
AUDIT_REPORT="pre-release-audit-$(date +%Y%m%d).txt"

echo "=== DOCUMENTATION AUDIT ===" > $AUDIT_REPORT

echo "" >> $AUDIT_REPORT
echo "=== Potential IP Addresses ===" >> $AUDIT_REPORT
grep -rn "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" docs/ >> $AUDIT_REPORT || echo "None found" >> $AUDIT_REPORT

echo "" >> $AUDIT_REPORT
echo "=== Potential Real Domains ===" >> $AUDIT_REPORT
grep -rn "\.internal\|\.corp\|\.company" docs/ >> $AUDIT_REPORT || echo "None found" >> $AUDIT_REPORT

echo "" >> $AUDIT_REPORT
echo "=== Long Hex Strings (potential tokens) ===" >> $AUDIT_REPORT
grep -rn "[a-fA-F0-9]\{40,\}" docs/ >> $AUDIT_REPORT || echo "None found" >> $AUDIT_REPORT

# Review report
cat $AUDIT_REPORT
```

### Step 2: Verify .gitignore

```bash
# Check that sensitive files would be ignored
git check-ignore -v credentials.env
git check-ignore -v *.pt
git check-ignore -v datasets/
git check-ignore -v logs/*.log
```

### Step 3: Clean Dangerous Files

```bash
# Remove any accidental commits
git rm --cached credentials.env
git rm --cached model_weights.pt

# Force update .gitignore
git add .gitignore
git commit -m "Enforce strict .gitignore for public release"
```

### Step 4: Tag Release

```bash
# Tag this version as public-safe
git tag -a v1.0.0-public \
  -m "Public documentation release - architecture only, no production code" \
  -m "- All examples use placeholder values" \
  -m "- No credentials, API keys, or real company data" \
  -m "- No trained model weights" \
  -m "- No actual source code (Python, Docker containers)" \
  -m "- Safe for public GitHub release"

git push origin v1.0.0-public
```

---

## Documentation Header Template

All documentation files should start with:

```markdown
# [Document Title]

> **PUBLIC SAFE**: This document contains only architecture documentation with placeholder examples.
> No production code, credentials, or proprietary data. Safe for public release.

```

---

## Response to Questions About Proprietary Content

### Q: Why no actual code?

> This is a documentation portfolio project. Sharing production code would expose proprietary algorithms, business logic, and infrastructure details. This repository demonstrates architectural understanding through system design without disclosing implementation details.

### Q: Why placeholder values?

> Real metrics, customer names, and dataset references are replaced with placeholders to maintain confidentiality while explaining the system design clearly. The focus is on "how the system works" not "what data we trained on."

### Q: Can I use this code?

> This is not meant to be runnable code. It's an architecture reference for learning system design patterns. To implement, you would:
> 1. Study the architecture documented here
> 2. Understand the design decisions
> 3. Implement your own code from scratch
> 4. Adapt patterns to your specific needs

### Q: Why Docker Compose only conceptually?

> Actual Docker configurations would need real image names, registry URLs, and credentials. The conceptual YAML provides structure without the security risk of accidental credential exposure.

---

## Continuous Monitoring

After public release, continue monitoring:

```bash
# Weekly audit (add to CI/CD)
#!/bin/bash

SUSPICIOUS_PATTERNS=(
  "API_KEY"
  "PASSWORD"
  "SECRET"
  "CREDENTIALS"
  "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}"
  "\.internal"
  "\.corp"
)

for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
  if grep -rn "$pattern" docs/ examples/ diagrams/; then
    echo "⚠️ WARNING: Found suspicious pattern: $pattern"
  fi
done
```

---

## Release Checklist

Before publishing to public GitHub:

- [ ] All .env files removed or use `.example.env` with placeholders
- [ ] No actual credentials anywhere
- [ ] No real company/customer names
- [ ] All metrics are PLACEHOLDER_VALUE or ILLUSTRATIVE
- [ ] No model weights included
- [ ] No real datasets included
- [ ] README.md explains this is documentation-only
- [ ] LICENSE includes confidentiality notice
- [ ] .gitignore prevents accidental commits
- [ ] CONTRIBUTING.md (if added) reminds contributors
- [ ] All diagrams use generic component names
- [ ] Audit script runs clean (no suspicious patterns)

---

## Example: Safe vs. Unsafe Payload

### ❌ Unsafe (contains real data)

```json
{
  "customer_id": "acme-corp-2024",
  "dataset_name": "StreetView-Manhattan-Q1",
  "model_version": "OmniDetect-v3-proprietary",
  "s3_bucket": "company-ai-models-prod",
  "training_node": "gpu-ml-01.company.internal",
  "results": {
    "mAP50": 0.89,
    "mAP75": 0.76,
    "frames_processed": 1234567
  }
}
```

### ✓ Safe (uses placeholders)

```json
{
  "customer_id": "CUSTOMER_ID_PLACEHOLDER",
  "dataset_name": "DATASET_NAME_PLACEHOLDER",
  "model_version": "MODEL_VERSION_PLACEHOLDER",
  "s3_bucket": "S3_BUCKET_PLACEHOLDER",
  "training_node": "TRAINING_NODE_PLACEHOLDER",
  "results": {
    "mAP50": "ILLUSTRATIVE_METRIC_VALUE",
    "mAP75": "ILLUSTRATIVE_METRIC_VALUE",
    "frames_processed": "ILLUSTRATIVE_COUNT_VALUE"
  }
}
```

---

## Success Criteria

✓ All confidential information removed
✓ No credentials exposed
✓ Architecture clearly explained
✓ Learning value preserved
✓ Legal/compliance cleared
✓ Ready for public GitHub
✓ Audit script passes
✓ Team review approved

