#!/usr/bin/env bash
#
# Public-safe validation gate for this documentation repository.
#
#   ./scripts/validate-sanitization.sh            check the whole repository
#   ./scripts/validate-sanitization.sh --staged   check only staged files (pre-commit hook)
#   ./scripts/validate-sanitization.sh --quiet     print only failures and the verdict
#
# Exit status: 0 when every blocking check passes, 1 otherwise.
#
# Blocking checks cover the leaks defined in
# docs/architecture/16-public-release-sanitization.md. Consistency problems
# (broken links, stale indexes) are reported as warnings and never block.
#
# Some documents legitimately quote forbidden patterns as policy examples.
# Those are listed in scripts/sanitization-allowlist.txt.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STAGED=0
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --staged) STAGED=1 ;;
    --quiet)  QUIET=1 ;;
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

ALLOWLIST="scripts/sanitization-allowlist.txt"
FAILURES=0
WARNINGS=0

if [ -t 1 ] && [ "${NO_COLOR:-}" = "" ]; then
  R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; B=$'\033[1m'; N=$'\033[0m'
else
  R=""; G=""; Y=""; B=""; N=""
fi

say() { [ "$QUIET" -eq 1 ] || echo "$@"; }

# Files in scope: tracked text files, or the staged subset.
file_list() {
  if [ "$STAGED" -eq 1 ]; then
    git diff --cached --name-only --diff-filter=ACM
  else
    git ls-files
  fi | grep -E '\.(md|json|env|mmd|ya?ml|txt|svg|sh|py)$' || true
}

# Drop lines whose "path:line" prefix is allowlisted.
filter_allowed() {
  if [ -f "$ALLOWLIST" ]; then
    grep -vFf <(grep -vE '^\s*(#|$)' "$ALLOWLIST") || true
  else
    cat
  fi
}

run_check() {
  local label="$1" blocking="$2" hits="$3"
  if [ -z "$hits" ]; then
    say "  ${G}pass${N}  $label"
  elif [ "$blocking" = "block" ]; then
    echo "  ${R}FAIL${N}  $label"
    echo "$hits" | sed 's/^/          /'
    FAILURES=$((FAILURES + 1))
  else
    say "  ${Y}warn${N}  $label"
    [ "$QUIET" -eq 1 ] || echo "$hits" | sed 's/^/          /'
    WARNINGS=$((WARNINGS + 1))
  fi
}

FILES="$(file_list)"
if [ -z "$FILES" ]; then
  say "Nothing in scope."
  exit 0
fi

say "${B}Public-safe validation${N}  ($(echo "$FILES" | wc -l) files in scope)"
say ""
say "${B}Blocking checks${N}"

# 1 · Real absolute paths belonging to a person or machine.
run_check "no real absolute paths" block "$(
  echo "$FILES" | xargs -r grep -nE '/home/[a-z][a-z0-9_-]+|/Users/[A-Za-z]|C:\\Users' 2>/dev/null \
    | grep -vE '/home/user|/home/<' | filter_allowed)"

# 2 · Credentials carrying an apparent value.
run_check "no credentials with a value" block "$(
  echo "$FILES" | xargs -r grep -nEi \
    '(api[_-]?key|secret[_-]?key|access[_-]?key|password|token)[[:space:]]*[:=][[:space:]]*"?[A-Za-z0-9_/+.-]{8,}' 2>/dev/null \
    | grep -viE 'placeholder|never_commit|xxxx|your_|<[A-Z_]+>|\[[A-Z_]+\]|example|\$\{|_HERE' | filter_allowed)"

# 3 · Routable IP addresses.
run_check "no routable IP addresses" block "$(
  echo "$FILES" | xargs -r grep -nE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' 2>/dev/null \
    | grep -vE '0\.0\.0\.0|127\.0\.0\.1|255\.255|\b0\.[0-9]+\.[0-9]+\.[0-9]+\b' | filter_allowed)"

# 4 · Contactable addresses.
run_check "no email addresses" block "$(
  echo "$FILES" | xargs -r grep -nE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' 2>/dev/null \
    | grep -viE 'example\.com|noreply|@master|@[0-9a-f]{7}|placeholder|^[^:]*:[0-9]+:.*git@' | filter_allowed)"

# 5 · Binaries that could carry real data. Generated diagrams are the only allowed images.
run_check "no unexpected binary assets" block "$(
  git ls-files | grep -iE '\.(png|jpe?g|gif|webp|bmp|tiff?|pt|pth|onnx|pkl|h5|npy|zip|tar|gz|csv|xlsx|parquet)$' \
    | grep -vE '^assets/(diagrams|poster)/[a-z0-9-]+\.png$' || true)"

# 6 · Model and dataset directories that should never be committed.
run_check "no dataset or weight directories" block "$(
  git ls-files | grep -iE '^(datasets?|weights?|runs|models|media|shared_storage)/' || true)"

say ""
say "${B}Advisory checks${N}"

# 7 · Internal links that do not resolve.
run_check "internal links resolve" warn "$(
  echo "$FILES" | grep '\.md$' | xargs -r grep -noE '\]\(\.?[./][^)]*\)' 2>/dev/null \
    | sed 's/](/\t/' | tr -d ')' | while IFS=$'\t' read -r src link; do
        f="${src%%:*}"; rest="${src#*:}"; ln="${rest%%:*}"; t="${link%%#*}"
        [ -z "$t" ] && continue
        case "$t" in http*|mailto*) continue;; esac
        case "$t" in /*) p=".$t";; *) p="$(dirname "$f")/$t";; esac
        [ -e "$p" ] || echo "$f:$ln -> $link"
      done | grep -v '^\.github/archive/' | sort -u | filter_allowed)"

# 8 · Empty tracked files.
run_check "no empty tracked files" warn "$(
  echo "$FILES" | while read -r f; do
    [ -f "$f" ] && [ ! -s "$f" ] && echo "$f"
  done | grep -v '^\.github/archive/' || true)"

# 9 · Duplicate document numbering.
run_check "no duplicate document prefixes" warn "$(
  ls docs/architecture/*.md 2>/dev/null | sed 's#.*/##' | cut -c1-2 | sort | uniq -d \
    | while read -r n; do ls docs/architecture/$n-* | tr '\n' ' '; echo; done)"

say ""
if [ "$FAILURES" -gt 0 ]; then
  echo "${R}${B}BLOCKED${N}  $FAILURES blocking check(s) failed. Do not push."
  echo "         Fix the findings above, or add a justified entry to $ALLOWLIST."
  exit 1
fi

say "${G}${B}OK${N}  no leaks detected${WARNINGS:+, $WARNINGS advisory warning(s)}."
exit 0
