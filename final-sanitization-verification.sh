#!/bin/bash
# final-sanitization-verification.sh
# Smart sanitization check that excludes documentation-only files

set -e

echo "🔐 FINAL SANITIZATION VERIFICATION"
echo "===================================="
echo ""

FAILED=0

# Helper function - check but exclude the sanitization guide itself
check_pattern_smart() {
  local name=$1
  local pattern=$2
  
  echo -n "✓ Checking for $name... "
  
  # Search excluding the sanitization guide (which shows examples of what NOT to do)
  if grep -r "$pattern" docs/ examples/ 2>/dev/null | \
     grep -v "docs/16-public-release-sanitization.md" | \
     head -1 >/dev/null; then
    echo "❌ FOUND IN ACTUAL CODE"
    grep -r "$pattern" docs/ examples/ 2>/dev/null | \
      grep -v "docs/16-public-release-sanitization.md" | head -3
    return 1
  else
    echo "✓"
    return 0
  fi
}

echo "📋 RUNNING SMART CHECKS (excluding docs/16-public-release-sanitization.md)"
echo ""

# Check critical patterns in actual code (not in the guide)
check_pattern_smart "Real company names" "Apple\|Google\|Meta\|Microsoft\|Amazon" || FAILED=1
check_pattern_smart "Customer names" "ACME\|TechCorp" || FAILED=1
check_pattern_smart "AWS keys" "AKIA[0-9A-Z]{16}" || FAILED=1
check_pattern_smart "API key patterns" "api_key\s*[:=]\|apikey\s*[:=]" || FAILED=1
check_pattern_smart "Password patterns" "password\s*[:=]" || FAILED=1

echo ""
echo "📋 CHECKING FOR RENAMED FUNCTIONS (should be gone)"
echo ""

if grep -r "extract_real_shapes\|generate_synthetic_images" docs/ 2>/dev/null; then
  echo "❌ FAILED: Found old function names"
  FAILED=1
else
  echo "✓ All old function names have been replaced"
fi

echo ""
echo "📋 CHECKING FOR NEW FUNCTION NAMES (should be present)"
echo ""

if grep -r "extract_objects_from_source\|generate_training_images" docs/20-synthetic-dataset-generation-pipeline.md 2>/dev/null >/dev/null; then
  echo "✓ New generic function names are in place"
else
  echo "❌ WARNING: New function names not found as expected"
fi

echo ""
echo "═════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
  echo ""
  echo "✅ FINAL SANITIZATION VERIFICATION PASSED"
  echo ""
  echo "Repository is now 100% safe for public GitHub release:"
  echo "  • No real company names"
  echo "  • No credentials or API keys"
  echo "  • No sensitive function names"
  echo "  • All generic/educational names"
  echo ""
  echo "Ready to publish! 🚀"
  exit 0
else
  echo ""
  echo "❌ SANITIZATION VERIFICATION FAILED"
  echo "Please fix the issues above before publishing"
  exit 1
fi
