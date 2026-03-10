#!/usr/bin/env python3
"""
Check if markdown files follow naming conventions.
Usage: python3 check_filename.py <file1.md> [file2.md ...]
"""

import sys
import re
from pathlib import Path

# Naming patterns by directory
PATTERNS = {
    'features': r'^feature_[a-z0-9_]+\.md$',
    'plan': r'^(PLAN\.md|plan_section_[a-z0-9_]+\.md)$',
    'knowledge': r'^(gotcha|solution|pattern|perf)_[a-z0-9_]+\.md$',
    'reference': r'^(api|lib|spec|guide)_[a-z0-9_]+\.md$',
    'sessions': r'^session_\d{4}_\d{2}_\d{2}_[a-z0-9_]+\.md$',
    'checklists': r'^checklist_[a-z0-9_]+\.md$',
    'audits': r'^audit_[a-z0-9_]+_\d{4}(_\d{2}|_q[1-4])\.md$',
}

# Special files allowed anywhere
SPECIAL_FILES = {
    'README.md', 'PLAN.md', '_index.md', '_status.md', '_context.md',
    'CLAUDE.md', 'CHANGELOG.md',
}

def check_filename(filepath: str) -> tuple[bool, str]:
    """
    Check if filename follows conventions.
    Returns: (is_valid, error_message)
    """
    path = Path(filepath)
    filename = path.name

    # Skip non-markdown files
    if not filename.endswith('.md'):
        return True, ""

    # Check special files
    if filename in SPECIAL_FILES:
        return True, ""

    # Check framework files (templates, guides, etc.)
    if '_framework' in path.parts:
        # Framework files have their own conventions
        if filename.startswith('template_') or filename.startswith('guide_') or \
           filename.startswith('example_') or filename.startswith('prompt_'):
            # Check lowercase and underscores
            if filename.replace('_', '').replace('.md', '').islower():
                return True, ""
            else:
                return False, f"Framework file must be lowercase with underscores: {filename}"
        # Allow other framework docs
        return True, ""

    # Check by directory
    for dir_name, pattern in PATTERNS.items():
        if dir_name in path.parts:
            if re.match(pattern, filename):
                return True, ""
            else:
                return False, f"Invalid {dir_name} filename: {filename}\n  Expected pattern: {pattern}"

    # If in docs/ but not in a specific category, allow it
    if 'docs' in path.parts:
        return True, ""

    return True, ""

def main():
    if len(sys.argv) < 2:
        print("Usage: check_filename.py <file1.md> [file2.md ...]")
        sys.exit(1)

    errors = []

    for filepath in sys.argv[1:]:
        is_valid, error_msg = check_filename(filepath)
        if not is_valid:
            errors.append(error_msg)

    if errors:
        print("❌ Filename convention errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All filenames follow conventions")
        sys.exit(0)

if __name__ == "__main__":
    main()
