#!/bin/bash
# validate-sanitization.sh
# Stricter sanitization validation for public release

set -e

echo "🔍 STRICTER SANITIZATION VALIDATION"
echo "===================================="
echo ""

REPORT_FILE="sanitization-validation-$(date +%Y%m%d-%H%M%S).txt"
FAILED=0

{
  echo "=== SANITIZATION VALIDATION REPORT ==="
  echo "Generated: $(date)"
  echo ""
  
  echo "=== SECTION 1: Category A (Corporate Identity) ==="
  echo ""
  
  echo "Checking for real company names (Apple, Google)..."
  if grep -r "Apple\|Google" docs/ examples/ 2>/dev/null | head -5; then
    echo "❌ FAILED: Found real company names"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for customer/organization names (ACME, TechCorp, etc.)..."
  if grep -r "ACME\|TechCorp\|Accenture\|Deloitte\|Consulting" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | head -5; then
    echo "❌ FAILED: Found customer names"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "=== SECTION 2: Category B (Credentials) ==="
  echo ""
  
  echo "Checking for AWS keys (AKIA*)..."
  if grep -rE "AKIA[0-9A-Z]{16}" docs/ examples/ 2>/dev/null; then
    echo "❌ FAILED: Found AWS keys"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for password patterns..."
  if grep -rE "password\s*[:=]|passwd\s*[:=]" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | head -5; then
    echo "❌ FAILED: Found password patterns"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for API key patterns..."
  if grep -rE "api_key\s*[:=]|apikey\s*[:=]|API_KEY\s*[:=]" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | head -5; then
    echo "❌ FAILED: Found API key patterns"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for long hex strings (potential tokens)..."
  LONG_HEX_COUNT=$(grep -rE "[a-fA-F0-9]{40,}" docs/ examples/ 2>/dev/null | wc -l)
  if [ $LONG_HEX_COUNT -gt 0 ]; then
    echo "⚠️  WARNING: Found $LONG_HEX_COUNT long hex strings (verify they're safe)"
    grep -rE "[a-fA-F0-9]{40,}" docs/ examples/ 2>/dev/null | head -3
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "=== SECTION 3: Category C (Network/Infrastructure) ==="
  echo ""
  
  echo "Checking for IP addresses..."
  if grep -rE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" docs/ examples/ 2>/dev/null | grep -v "^[0-9.]*$" | head -5; then
    echo "❌ FAILED: Found IP addresses"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for .internal domains..."
  if grep -r "\.internal" docs/ examples/ 2>/dev/null; then
    echo "❌ FAILED: Found .internal domains"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for .corp domains..."
  if grep -r "\.corp" docs/ examples/ 2>/dev/null; then
    echo "❌ FAILED: Found .corp domains"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for .company domains..."
  if grep -r "\.company" docs/ examples/ 2>/dev/null; then
    echo "❌ FAILED: Found .company domains"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for AWS account IDs (12 digit numbers)..."
  if grep -rE "[0-9]{12}" docs/ examples/ 2>/dev/null | grep -v "^\d*\..*\d*$" | head -3; then
    echo "⚠️  WARNING: Found potential AWS account IDs (verify context)"
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "=== SECTION 4: Category D (Storage & Resources) ==="
  echo ""
  
  echo "Checking for database connection strings..."
  if grep -rE "postgresql://|mysql://|mongodb://|redis://" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | head -5; then
    echo "❌ FAILED: Found connection strings"
    FAILED=1
  else
    echo "✓ None found"
  fi
  
  echo ""
  echo "Checking for S3 bucket references..."
  if grep -rE "s3://[a-z0-9\-]{3,63}/" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" | head -5; then
    echo "⚠️  WARNING: Found S3 bucket references (verify they're safe)"
  else
    echo "✓ None found or properly namespaced"
  fi
  
  echo ""
  echo "=== VALIDATION COMPLETE ==="
  
} | tee "$REPORT_FILE"

echo ""
if [ $FAILED -eq 0 ]; then
  echo "✅ SANITIZATION VALIDATION PASSED"
  echo "📊 Report saved to: $REPORT_FILE"
  exit 0
else
  echo "❌ SANITIZATION VALIDATION FAILED"
  echo "📊 Report saved to: $REPORT_FILE"
  exit 1
fi
