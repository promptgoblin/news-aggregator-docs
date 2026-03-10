#!/bin/bash
# Quick validation for pre-commit hook
# Usage: ./validate_quick.sh <file1.md> [file2.md ...]

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/venv/bin/python"

# Check if Python venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python venv not found at ${SCRIPT_DIR}/venv"
    echo "   Run: python3 -m venv ${SCRIPT_DIR}/venv"
    echo "   Then: ${SCRIPT_DIR}/venv/bin/pip install tiktoken"
    exit 1
fi

# If no arguments, show usage
if [ $# -eq 0 ]; then
    echo "Usage: validate_quick.sh <file1.md> [file2.md ...]"
    exit 1
fi

echo "🔍 Running quick validation on $# files..."
echo ""

# Track overall status
HAS_ERRORS=0

# Run each check
echo "1️⃣  Checking filename conventions..."
if ! $PYTHON "${SCRIPT_DIR}/check_filename.py" "$@"; then
    HAS_ERRORS=1
fi
echo ""

echo "2️⃣  Checking token budgets..."
if ! $PYTHON "${SCRIPT_DIR}/check_token_budget.py" "$@"; then
    HAS_ERRORS=1
fi
echo ""

echo "3️⃣  Checking required sections..."
if ! $PYTHON "${SCRIPT_DIR}/check_structure.py" "$@"; then
    HAS_ERRORS=1
fi
echo ""

echo "4️⃣  Checking internal links..."
if ! $PYTHON "${SCRIPT_DIR}/check_links.py" "$@"; then
    HAS_ERRORS=1
fi
echo ""

# If all checks passed, add compliance badges
if [ $HAS_ERRORS -eq 0 ]; then
    echo "5️⃣  Adding compliance badges..."
    $PYTHON "${SCRIPT_DIR}/add_compliance_badge.py" "$@"
    echo ""
    echo "✅ All validation checks passed!"
    exit 0
else
    echo ""
    echo "❌ Validation failed. Please fix errors above."
    exit 1
fi
