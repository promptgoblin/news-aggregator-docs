#!/usr/bin/env python3
"""
Check if markdown files are within token budgets.
Usage: python3 check_token_budget.py <file1.md> [file2.md ...]
"""

import sys
import re
from pathlib import Path

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed")
    print("Install with: pip install tiktoken")
    sys.exit(1)

# Initialize tokenizer
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))

# Token budgets by file type (v3 - updated for modern context windows)
BUDGETS = {
    '_status.md': 300,
    '_context.md': 400,
    '_index.md': 600,
    'PLAN.md': 1200,
    'plan_section_': 2500,
    'feature_': 2000,
    'template_FEATURE_SIMPLE.md': 1200,
    'template_FEATURE.md': 2000,
    'gotcha_': 800,
    'solution_': 800,
    'pattern_': 800,
    'perf_': 800,
    'session_': 800,
    'audit_': 1200,
    'checklist_': 1000,
    'api_': 1200,
    'lib_': 1200,
}

# Tolerance: files can exceed by this percentage without triggering error
TOLERANCE = 0.20  # 20% over budget is acceptable if justified

def get_budget(filepath: str) -> int:
    """Get token budget for a file."""
    filename = Path(filepath).name

    # Check exact match first
    if filename in BUDGETS:
        return BUDGETS[filename]

    # Check prefix match
    for prefix, budget in BUDGETS.items():
        if filename.startswith(prefix):
            return budget

    # No budget defined (framework files, etc.)
    return None

def has_budget_override_comment(content: str) -> bool:
    """Check if file has a comment justifying budget override."""
    # Look for: <!-- TOKEN BUDGET EXCEEDED: reason -->
    return '<!-- TOKEN BUDGET EXCEEDED:' in content or \
           '<!-- EXCEEDED:' in content

def check_token_budget(filepath: str) -> tuple[bool, str]:
    """
    Check if file is within token budget.
    Returns: (is_valid, message)
    """
    path = Path(filepath)

    # Skip non-markdown files
    if not filepath.endswith('.md'):
        return True, ""

    budget = get_budget(filepath)
    if budget is None:
        # No budget defined, skip
        return True, ""

    try:
        content = path.read_text(encoding='utf-8')
        token_count = count_tokens(content)

        if token_count <= budget:
            return True, f"✅ {path.name}: {token_count}/{budget} tokens"

        # Over budget - check tolerance
        overage = (token_count - budget) / budget

        if overage <= TOLERANCE:
            # Within tolerance
            return True, f"⚠️  {path.name}: {token_count}/{budget} tokens ({overage:.0%} over, within tolerance)"

        # Over tolerance - check for override comment
        if has_budget_override_comment(content):
            return True, f"⚠️  {path.name}: {token_count}/{budget} tokens (override comment found)"

        # Over budget and no justification
        return False, f"❌ {path.name}: {token_count}/{budget} tokens ({overage:.0%} over)\n   Add comment: <!-- TOKEN BUDGET EXCEEDED: reason -->"

    except Exception as e:
        return False, f"Error reading {filepath}: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: check_token_budget.py <file1.md> [file2.md ...]")
        sys.exit(1)

    errors = []
    warnings = []

    for filepath in sys.argv[1:]:
        is_valid, message = check_token_budget(filepath)
        if message:
            if is_valid:
                if message.startswith('⚠️'):
                    warnings.append(message)
                else:
                    print(message)
            else:
                errors.append(message)

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  {warning}")

    if errors:
        print("\n❌ Token budget errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ All files within token budgets")
        sys.exit(0)

if __name__ == "__main__":
    main()
