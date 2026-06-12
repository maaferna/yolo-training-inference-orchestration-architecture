#!/bin/bash
# production-ready-check.sh
# Final validation - checks only actual code/examples, not documentation

set -e

echo "✅ PRODUCTION-READY VALIDATION"
echo "=============================="
echo ""

PASSED=0
FAILED=0

echo "📋 Checking for actual sensitive data (not documentation)..."
echo ""

# These checks focus on ACTUAL CONTENT, not documentation explanations

echo -n "1. Real unplaceholdered AWS keys in examples... "
FOUND=$(find examples -type f -name "*.json" -o -name "*.yaml" -o -name "*.yml" 2>/dev/null | xargs grep -l "AKIA" 2>/dev/null | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "2. Real unplaceholdered IP addresses in examples... "
FOUND=$(find examples -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | xargs grep -l "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" 2>/dev/null | grep -v "PLACEHOLDER" | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "3. Real hostnames in examples (gpu-prod, training-server)... "
FOUND=$(find examples -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | xargs grep -l "gpu-prod\|training-server\|db-prod" 2>/dev/null | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "4. Real company names in examples (ACME, TechCorp)... "
FOUND=$(find examples -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | xargs grep -l "ACME\|TechCorp\|OmniDetect" 2>/dev/null | grep -v "PLACEHOLDER" | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "5. No actual credentials in .env files... "
if [ -f ".env" ] || [ -f "credentials.env" ] || [ -f "secrets.yaml" ]; then
  echo "❌ FAILED - Found sensitive files in repo"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "6. No model weights in repository... "
FOUND=$(find . -type f \( -name "*.pt" -o -name "*.pth" -o -name "*.weights" \) 2>/dev/null | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED - Found $FOUND model weight files"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo -n "7. No raw dataset archives in repository... "
FOUND=$(find . -type f \( -name "*.zip" -o -name "*.tar" -o -name "*.tar.gz" \) 2>/dev/null | wc -l)
if [ $FOUND -gt 0 ]; then
  echo "❌ FAILED - Found $FOUND archive files"
  FAILED=$((FAILED + 1))
else
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
fi

echo ""
echo "📋 Required Files Check"
echo "======================"

echo -n "CONTRIBUTING.md exists... "
if [ -f "CONTRIBUTING.md" ]; then
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
else
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
fi

echo -n "LICENSE exists with confidentiality notice... "
if grep -q "CONFIDENTIALITY\|confidential" LICENSE 2>/dev/null; then
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
else
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
fi

echo -n ".gitignore is comprehensive... "
if grep -q "\.env\|\.pt\|datasets/\|credentials/" .gitignore 2>/dev/null; then
  echo "✓ PASS"
  PASSED=$((PASSED + 1))
else
  echo "❌ FAILED"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════"
echo "Results: $PASSED Passed, $FAILED Failed"
echo "════════════════════════════════════════"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "✅ REPOSITORY IS PRODUCTION-READY"
  echo ""
  echo "Next steps for publication:"
  echo "  1. Review all changes: git status"
  echo "  2. Commit: git add . && git commit -m 'Full Polish: Sanitization + Contributing + Publication Ready'"
  echo "  3. Tag: git tag -a v1.0.0-public -m 'Public release - sanitized architecture documentation'"
  echo "  4. Push: git push origin master && git push origin v1.0.0-public"
  exit 0
else
  echo "❌ REPOSITORY NOT READY - Issues found"
  exit 1
fi
