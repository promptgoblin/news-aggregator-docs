#!/bin/bash
# Install git hooks for documentation validation
# Usage: ./install_hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find git root by searching upward for .git directory
# Handles both cases:
#   - docs is a subdirectory of project (project/docs/_framework/utilities/)
#   - docs is the git root itself (docs/_framework/utilities/)
PROJECT_ROOT="${SCRIPT_DIR}"
while [ ! -d "${PROJECT_ROOT}/.git" ]; do
    PARENT="$(dirname "${PROJECT_ROOT}")"
    if [ "${PARENT}" = "${PROJECT_ROOT}" ]; then
        echo "❌ Not in a git repository. Initialize git first:"
        echo "   cd to your project/docs directory and run: git init"
        exit 1
    fi
    PROJECT_ROOT="${PARENT}"
done

HOOKS_DIR="${PROJECT_ROOT}/.git/hooks"

# Detect if docs is a subdirectory or if we're in a standalone docs repo
if [ -d "${PROJECT_ROOT}/docs/_framework" ]; then
    # docs is a subdirectory (e.g., project/docs/)
    REPO_TYPE="project"
    DOCS_PREFIX="docs/"
elif [ -d "${PROJECT_ROOT}/_framework" ]; then
    # We're in the docs directory itself (standalone docs repo)
    REPO_TYPE="standalone"
    DOCS_PREFIX=""
else
    echo "❌ Cannot determine repository structure"
    echo "   Expected either PROJECT_ROOT/docs/_framework/ or PROJECT_ROOT/_framework/"
    exit 1
fi

echo "📦 Installing git hooks..."
echo "   Git root: ${PROJECT_ROOT}"
echo "   Repo type: ${REPO_TYPE} (docs ${DOCS_PREFIX:+in subdirectory}${DOCS_PREFIX:-is git root})"
echo ""

# Create hooks directory if it doesn't exist
mkdir -p "${HOOKS_DIR}"

# Create pre-commit hook
HOOK_FILE="${HOOKS_DIR}/pre-commit"

# Generate hook with appropriate paths based on repo structure
if [ "$REPO_TYPE" = "project" ]; then
    # Project repo: files are at docs/features/..., validation at docs/_framework/utilities/
    cat > "${HOOK_FILE}" << 'EOF'
#!/bin/bash
# Pre-commit hook for documentation validation
# Auto-installed by docs/_framework/utilities/install_hooks.sh

# Get the project root (parent of .git)
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
VALIDATE_SCRIPT="${PROJECT_ROOT}/docs/_framework/utilities/validate_quick.sh"

# Get list of staged markdown files in docs/
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM | grep "^docs/.*\.md$" || true)

# If no docs are staged, exit successfully
if [ -z "$STAGED_DOCS" ]; then
    exit 0
fi

echo "📝 Validating documentation changes..."
echo ""

# Convert to absolute paths
STAGED_PATHS=""
for file in $STAGED_DOCS; do
    STAGED_PATHS="${STAGED_PATHS} ${PROJECT_ROOT}/${file}"
done

# Run validation
if ! bash "${VALIDATE_SCRIPT}" $STAGED_PATHS; then
    echo ""
    echo "❌ Documentation validation failed!"
    echo "   Fix errors above or commit with --no-verify to bypass"
    exit 1
fi

# If badges were updated, stage them
for file in $STAGED_DOCS; do
    git add "${PROJECT_ROOT}/${file}"
done

echo ""
echo "✅ Documentation validation passed"
exit 0
EOF
else
    # Standalone docs repo: files are at features/..., validation at _framework/utilities/
    cat > "${HOOK_FILE}" << 'EOF'
#!/bin/bash
# Pre-commit hook for documentation validation
# Auto-installed by _framework/utilities/install_hooks.sh

# Get the project root (parent of .git)
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
VALIDATE_SCRIPT="${PROJECT_ROOT}/_framework/utilities/validate_quick.sh"

# Get list of staged markdown files (entire repo is docs)
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM | grep "\.md$" || true)

# If no docs are staged, exit successfully
if [ -z "$STAGED_DOCS" ]; then
    exit 0
fi

echo "📝 Validating documentation changes..."
echo ""

# Convert to absolute paths
STAGED_PATHS=""
for file in $STAGED_DOCS; do
    STAGED_PATHS="${STAGED_PATHS} ${PROJECT_ROOT}/${file}"
done

# Run validation
if ! bash "${VALIDATE_SCRIPT}" $STAGED_PATHS; then
    echo ""
    echo "❌ Documentation validation failed!"
    echo "   Fix errors above or commit with --no-verify to bypass"
    exit 1
fi

# If badges were updated, stage them
for file in $STAGED_DOCS; do
    git add "${PROJECT_ROOT}/${file}"
done

echo ""
echo "✅ Documentation validation passed"
exit 0
EOF
fi

# Make hook executable
chmod +x "${HOOK_FILE}"

echo "✅ Pre-commit hook installed at: ${HOOK_FILE}"
echo ""
echo "📋 What happens now:"
echo "   - Git will validate docs on every commit"
echo "   - Only changed files are validated (fast)"
echo "   - Compliance badges added automatically"
echo "   - Commit blocked if validation fails"
echo ""
echo "To bypass validation (not recommended):"
echo "   git commit --no-verify"
echo ""
echo "To uninstall:"
echo "   rm ${HOOK_FILE}"

exit 0
