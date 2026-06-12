#!/bin/bash
# complete-sanitization-check.sh
# Complete end-to-end sanitization check before public release

set -e

echo "🔍 COMPLETE SANITIZATION CHECK"
echo "=============================="
echo ""

FAILED=0
WARNINGS=0

# Helper function for checking patterns
check_pattern() {
  local name=$1
  local pattern=$2
  local scope=${3:-"docs/ examples/"}
  local exclude=${4:-""}
  
  echo -n "Checking for $name... "
  
  if [ -z "$exclude" ]; then
    if grep -r "$pattern" $scope 2>/dev/null | head -1 >/dev/null; then
      echo "❌ FAILED"
      grep -r "$pattern" $scope 2>/dev/null | head -3
      return 1
    else
      echo "✓"
      return 0
    fi
  else
    if grep -r "$pattern" $scope 2>/dev/null | grep -v "$exclude" | head -1 >/dev/null; then
      echo "❌ FAILED"
      grep -r "$pattern" $scope 2>/dev/null | grep -v "$exclude" | head -3
      return 1
    else
      echo "✓"
      return 0
    fi
  fi
}

# CATEGORY A: Corporate Identity
echo "📋 CATEGORY A: Corporate Identity"
echo "===================================="

# Exclude the sanitization guide from checks (it documents what NOT to do)
echo -n "Checking for Real company names (Apple, Google)... "
if grep -r "Apple\|Google" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for Microsoft references... "
if grep -r "\\bMicrosoft\\b" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for Amazon references... "
if grep -r "\\bAmazon\\b" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for Customer names (ACME, TechCorp)... "
if grep -r "ACME\|TechCorp\|Accenture\|Deloitte" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for Proprietary model names... "
if grep -r "OmniDetect\|CompanyYOLO\|ProprietaryAI" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo ""
echo "📋 CATEGORY B: Credentials & Secrets"
echo "====================================="

echo -n "Checking for AWS Access Keys (AKIA*)... "
if grep -rE "AKIA[0-9A-Z]{16}" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for password patterns... "
if grep -rE "password\s*[:=]|passwd\s*[:=]" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for API key patterns... "
if grep -rE "api_key\s*[:=]|apikey\s*[:=]|API_KEY\s*[:=]" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for AWS secret patterns... "
if grep -rE "AWS_SECRET\|aws_secret_access_key" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for Database passwords... "
if grep -rE "DB_PASSWORD\|DATABASE_PASSWORD" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

# Check for long hex strings (potential tokens)
echo -n "Checking for long hex strings (40+ chars)... "
LONG_HEX=$(grep -rE "[a-fA-F0-9]{40,}" docs/ examples/ 2>/dev/null | wc -l)
if [ $LONG_HEX -gt 0 ]; then
  echo "⚠️  ($LONG_HEX found - verify context)"
  WARNINGS=$((WARNINGS + 1))
else
  echo "✓"
fi

echo ""
echo "📋 CATEGORY C: Network & Infrastructure"
echo "========================================"

echo -n "Checking for IPv4 addresses... "
if grep -rE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | grep -v "^\d*\..*\d*$" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for .internal domains... "
if grep -r "\.internal" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for .corp domains... "
if grep -r "\.corp" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for .company domains... "
if grep -r "\.company" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for AWS account IDs (12-digit)... "
AWS_IDS=$(grep -rE "[0-9]{12}" docs/ examples/ 2>/dev/null | grep -v "^\d*\..*\d*$" | wc -l)
if [ $AWS_IDS -gt 0 ]; then
  echo "⚠️  ($AWS_IDS found - verify context)"
  WARNINGS=$((WARNINGS + 1))
else
  echo "✓"
fi

echo ""
echo "📋 CATEGORY D: Storage & Resources"
echo "=================================="

echo -n "Checking for Database connection strings... "
if grep -rE "postgresql://|mysql://|mongodb://|redis://" docs/ examples/ 2>/dev/null | grep -v "16-public-release" | grep -v "PLACEHOLDER" | head -1 >/dev/null; then
  echo "❌ FAILED"
  FAILED=1
else
  echo "✓"
fi

echo -n "Checking for S3 bucket names... "
S3_BUCKETS=$(grep -rE "s3://[a-z0-9\-]{3,63}/" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | wc -l)
if [ $S3_BUCKETS -gt 0 ]; then
  echo "⚠️  ($S3_BUCKETS found - verify context)"
  WARNINGS=$((WARNINGS + 1))
else
  echo "✓"
fi

echo ""
echo "📋 SYSTEM STATE"
echo "================"

# Check important files exist
echo -n "Checking for .gitignore... "
if [ -f ".gitignore" ]; then echo "✓"; else echo "❌ MISSING"; FAILED=1; fi

echo -n "Checking for docs/16-public-release-sanitization.md... "
if [ -f "docs/16-public-release-sanitization.md" ]; then echo "✓"; else echo "❌ MISSING"; FAILED=1; fi

echo -n "Checking for CONTRIBUTING.md... "
if [ -f "CONTRIBUTING.md" ]; then echo "✓"; else echo "⚠️  NOT YET CREATED"; fi

echo ""
echo "═════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
  echo "✅ COMPLETE SANITIZATION CHECK PASSED"
  if [ $WARNINGS -gt 0 ]; then
    echo "⚠️  ($WARNINGS warnings - review manually)"
  fi
  echo ""
  echo "Repository is ready for publication:"
  echo "  1. Tag: git tag -a v1.0.0-public -m 'Public release - sanitized architecture'"
  echo "  2. Push: git push origin v1.0.0-public"
  echo "  3. Create GitHub release with tag"
  exit 0
else
  echo "❌ COMPLETE SANITIZATION CHECK FAILED"
  echo ""
  echo "Issues found - please fix before publication:"
  echo "  - Review the output above"
  echo "  - See docs/16-public-release-sanitization.md for guidelines"
  echo "  - See CONTRIBUTING.md for contribution requirements"
  exit 1
fi
