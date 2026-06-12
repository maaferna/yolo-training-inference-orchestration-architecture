# Contributing to This Architecture Repository

This is an architecture documentation repository for a YOLO training and inference orchestration system. We welcome contributions that improve documentation clarity, add examples, or expand architectural understanding.

## Before Contributing

**This repository follows strict sanitization standards** to remain suitable for public GitHub release.

### The Golden Rule

❌ **NEVER COMMIT**:
- Real company or customer names
- Real IP addresses, hostnames, or domain names
- Any credentials (API keys, passwords, tokens, SSH keys)
- Real production metrics or data
- Real dataset names or model checkpoint names
- Real AWS/Cloud account information

✓ **ALWAYS USE PLACEHOLDERS**:
- Companies: `CUSTOMER_NAME_PLACEHOLDER`
- Models: `MODEL_NAME_PLACEHOLDER`
- IPs/Hosts: `IP_ADDRESS_PLACEHOLDER`, `HOSTNAME_PLACEHOLDER`
- APIs/Keys: `API_KEY_PLACEHOLDER`, `TOKEN_PLACEHOLDER`
- Metrics: `ILLUSTRATIVE_METRIC_VALUE`
- Data: `DATASET_NAME_PLACEHOLDER`, `TRAINING_DATA_PATH_PLACEHOLDER`

## Contribution Workflow

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/yolo-training-inference-orchestration-architecture.git
cd yolo-training-inference-orchestration-architecture
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes (With Sanitization)

When editing documentation:

```markdown
❌ DO NOT WRITE:
  "Our system processes real customer data from ACME Corporation..."
  "Models are stored on gpu-prod-01.company.internal..."
  "Datasets are in s3://company-ai-models-prod/..."

✓ DO WRITE:
  "The system processes data from [CUSTOMER_NAME_PLACEHOLDER]..."
  "Models are stored on [HOSTNAME_PLACEHOLDER]..."
  "Datasets are in S3 at [S3_BUCKET_PLACEHOLDER]/..."
```

### 4. Run Sanitization Checks

**Before committing, run the validation script**:

```bash
bash validate-sanitization.sh
```

**Before pushing, run the complete check**:

```bash
bash complete-sanitization-check.sh
```

If either script fails, **do not push**. Fix the issues and re-run.

### 5. Commit and Push

```bash
git add .
git commit -m "docs: improve architecture documentation"
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Describe what you improved
- Link any related issues
- Confirm you ran sanitization checks

## Sanitization Guidelines

### Category A: Corporate & Product Identity

**Forbidden**:
- Real company names (Apple, Google, Meta, Amazon, Microsoft)
- Customer names (ACME, TechCorp, Deloitte)
- Proprietary model names (OmniDetect, CompanyYOLO)
- Internal project codenames

**Use Instead**:
```markdown
- CUSTOMER_NAME_PLACEHOLDER
- PROJECT_NAME_PLACEHOLDER
- MODEL_NAME_PLACEHOLDER
- ORGANIZATION_PLACEHOLDER
```

### Category B: Credentials & Secrets

**Forbidden** (EVER):
- API keys (OpenAI, HuggingFace, ClearML)
- AWS/Azure/GCP credentials
- Database passwords
- Private SSH keys
- Any authentication tokens

**Pattern**: If it could authenticate you, it's forbidden.

### Category C: Network & Infrastructure

**Forbidden**:
- IP addresses (192.168.x.x, 10.x.x.x, public IPs)
- Hostnames (gpu-01, training-server, db-prod)
- Internal domain names (.internal, .corp, .company, .local)
- AWS/Azure subscription IDs

**Use Instead**:
```markdown
- IP_ADDRESS_PLACEHOLDER
- HOSTNAME_PLACEHOLDER
- DOMAIN_PLACEHOLDER
- COMPUTE_NODE_PLACEHOLDER
```

### Category D: Storage & Resources

**Forbidden**:
- Real S3 bucket names (company-ai-models-prod)
- Real dataset paths or names
- Real model checkpoint identifiers
- Production metrics if from internal systems

**Use Instead**:
```markdown
- S3_BUCKET_PLACEHOLDER
- DATASET_NAME_PLACEHOLDER
- DATASET_PATH_PLACEHOLDER
- ILLUSTRATIVE_METRIC_VALUE
- CHECKPOINT_PATH_PLACEHOLDER
```

### Category E: Suspicious Patterns

The validation script automatically flags:
- Long hex strings (40+ characters) - potential tokens
- Email addresses from internal domains
- Phone numbers
- AWS key patterns

**If flagged, explain in comments why it's safe** or remove it.

## Example: Good vs. Bad Contribution

### ❌ BAD (Contains Real Data)

```markdown
# YOLO Training Architecture

Our system trains YOLO models for ACME Corporation's street view project.

Infrastructure:
- Training nodes: gpu-prod-01.company.internal, gpu-prod-02.company.internal
- Dataset: s3://company-ai-models-prod/street-view-data-2024
- Model storage: /mnt/company-nfs/models/
- Metrics: mAP50=0.89 on ACME's private test set

Credentials:
- ClearML token: clearml-xxxxxxxxxxxxx
- AWS access key: AKIAIOSFODNN7EXAMPLE
```

### ✓ GOOD (Uses Placeholders)

```markdown
# YOLO Training Architecture

The system trains YOLO models for [CUSTOMER_NAME_PLACEHOLDER]'s object detection project.

Infrastructure:
- Training nodes: [HOSTNAME_PLACEHOLDER]-01, [HOSTNAME_PLACEHOLDER]-02
- Dataset: [S3_BUCKET_PLACEHOLDER]/[DATASET_NAME_PLACEHOLDER]
- Model storage: [TRAINING_DATA_PATH_PLACEHOLDER]/models/
- Metrics: mAP50 = [ILLUSTRATIVE_METRIC_VALUE] on [CUSTOMER_NAME_PLACEHOLDER]'s test set

Note: Actual credentials are managed through environment variables.
- ClearML token: [API_KEY_PLACEHOLDER] (stored in .env)
- AWS access key: [CLOUD_CREDENTIALS_PLACEHOLDER] (stored in AWS credentials)
```

## Pre-commit Hook (Optional but Recommended)

Install the pre-commit hook to prevent accidental commits:

```bash
chmod +x validate-sanitization.sh
cp validate-sanitization.sh .git/hooks/pre-commit
```

Now the validation runs automatically before each commit.

## Testing Your Changes

### Test Documentation Clarity

Ask yourself:
- Is the architecture clear without real company data?
- Would a new developer understand the system?
- Are placeholders obvious and consistent?

### Test Sanitization

```bash
# Quick check
bash validate-sanitization.sh

# Complete check
bash complete-sanitization-check.sh
```

## Common Questions

### Q: Can I use our real project name?

**A**: Only if it's already public. Use a placeholder like `[PROJECT_NAME_PLACEHOLDER]` otherwise.

### Q: Can I include real metrics from public benchmarks?

**A**: Yes, if they're from published papers or public datasets. For internal metrics, use `[ILLUSTRATIVE_METRIC_VALUE]`.

### Q: What if someone commits sensitive data?

**A**: GitHub has tools to remove it:
```bash
git filter-branch -f --tree-filter 'rm -f secrets.env' HEAD
```

Report it in an issue immediately.

### Q: Can I link to internal documentation?

**A**: Use `[INTERNAL_DOCUMENTATION_LINK_PLACEHOLDER]` with a note that it's internal-only.

## Code of Conduct

- Respect the sanitization standards
- Review contributions for sensitive data
- Help others understand why something needs a placeholder
- No exceptions for "just this once"

## Questions?

See [docs/architecture/architecture/16-public-release-sanitization.md](./docs/architecture/16-public-release-sanitization.md) for comprehensive sanitization guidelines.

---

**Thank you for contributing safely!** 🎉
