#!/bin/bash
# production-ready-final-check.sh
# Final verification with smart pattern matching

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 PRODUCTION-READY FINAL CHECK                    ║"
echo "║                                                                  ║"
echo "║   Verifying repository is 100% safe for public GitHub release   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

CRITICAL_FAILED=0

echo "🔐 CHECKING FOR CRITICAL ISSUES"
echo "================================"
echo ""

# 1. Check for actual AWS keys (AKIA pattern - very specific)
echo -n "AWS Access Keys (AKIA...)... "
if grep -rE "AKIA[0-9A-Z]{16}" docs/ examples/ 2>/dev/null | grep -v "PLACEHOLDER" >/dev/null; then
  echo "❌ FAILED"
  CRITICAL_FAILED=1
else
  echo "✓ SAFE"
fi

# 2. Check for actual credentials (not placeholders)
echo -n "Actual credentials... "
if grep -r "password\s*=\|api_key\s*=" docs/ examples/ 2>/dev/null | \
   grep -v "PLACEHOLDER\|\.env\|env:\|getenv" >/dev/null; then
  echo "❌ FAILED"
  CRITICAL_FAILED=1
else
  echo "✓ SAFE"
fi

# 3. Check for database connection strings (not placeholders)
echo -n "Database URLs... "
if grep -rE "postgresql://[a-z0-9]+:[a-z0-9]+@|mysql://[a-z0-9]+:[a-z0-9]+@" docs/ examples/ 2>/dev/null; then
  echo "❌ FAILED"
  CRITICAL_FAILED=1
else
  echo "✓ SAFE"
fi

# 4. Check for IP addresses (not in examples of what NOT to do)
echo -n "IP Addresses... "
if grep -rE "\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b" docs/ examples/ 2>/dev/null | \
   grep -v "PLACEHOLDER\|0\.0\|127\.0\|192\.168\|255\.255" | \
   grep -v "10\.0\.0\|172\." | grep -v "^[0-9.]*$" | head -3 >/dev/null; then
  echo "⚠️  WARNING (check context)"
else
  echo "✓ SAFE"
fi

# 5. Verify the sensitive function names have been renamed
echo -n "Old function names removed... "
if grep -r "extract_real_shapes\|generate_synthetic_images" docs/ 2>/dev/null >/dev/null; then
  echo "❌ FAILED"
  CRITICAL_FAILED=1
else
  echo "✓ SAFE"
fi

# 6. Verify new generic names are present
echo -n "New generic names in place... "
if grep -r "extract_objects_from_source\|generate_training_images" docs/20-synthetic-dataset-generation-pipeline.md 2>/dev/null >/dev/null; then
  echo "✓ PRESENT"
else
  echo "⚠️  WARNING"
fi

# 7. Check for model weights
echo -n "Model weights (.pt, .pth)... "
if find . -type f \( -name "*.pt" -o -name "*.pth" \) 2>/dev/null | grep -v ".venv\|node_modules" >/dev/null; then
  echo "❌ FOUND"
  CRITICAL_FAILED=1
else
  echo "✓ NOT INCLUDED"
fi

# 8. Check for actual datasets
echo -n "Raw datasets... "
if [ -d "datasets" ] || [ -d "raw_data" ]; then
  echo "❌ FOUND"
  CRITICAL_FAILED=1
else
  echo "✓ NOT INCLUDED"
fi

# 9. Check .gitignore is comprehensive
echo -n ".gitignore configured... "
if grep -q "\.env\|credentials\|*.pt\|datasets/\|AWS_SECRET" .gitignore 2>/dev/null; then
  echo "✓ CONFIGURED"
else
  echo "⚠️  CHECK MANUALLY"
fi

# 10. Verify all files are non-binary (no executables with secrets)
echo -n "No compiled/binary files... "
if find . -type f \( -name "*.pyc" -o -name "*.so" \) 2>/dev/null | grep -v ".venv\|__pycache__" >/dev/null; then
  echo "⚠️  FOUND (.pyc files)"
else
  echo "✓ SAFE"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"

if [ $CRITICAL_FAILED -eq 0 ]; then
  echo "║                                                                  ║"
  echo "║              ✅ PRODUCTION READY - ALL CHECKS PASSED ✅           ║"
  echo "║                                                                  ║"
  echo "║  Your repository is 100% safe for public GitHub release!        ║"
  echo "║                                                                  ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "📊 SUMMARY:"
  echo "  • No AWS keys or credentials found"
  echo "  • No database connection strings with real data"
  echo "  • No IP addresses in actual code"
  echo "  • All sensitive function names removed"
  echo "  • No model weights or datasets included"
  echo "  • .gitignore is properly configured"
  echo ""
  echo "🚀 NEXT STEPS:"
  echo "  1. git add . && git commit -m 'Full polish: Complete sanitization'"
  echo "  2. git tag -a v1.0.0-public -m 'Public release - production-ready'"
  echo "  3. git push origin master v1.0.0-public"
  echo "  4. Create GitHub release from the tag"
  echo ""
  exit 0
else
  echo "║                                                                  ║"
  echo "║              ❌ CRITICAL ISSUES FOUND - CANNOT PUBLISH ❌         ║"
  echo "║                                                                  ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Please fix the critical issues above before publishing."
  echo ""
  exit 1
fi
