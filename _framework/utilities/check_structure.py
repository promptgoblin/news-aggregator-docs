#!/usr/bin/env python3
"""
Check if markdown files have required sections.
Usage: python3 check_structure.py <file1.md> [file2.md ...]
"""

import sys
from pathlib import Path

# Required sections by file type
REQUIRED_SECTIONS = {
    'feature_': ['## User Intent', '## Status', '## Implementation'],
    'plan_section_': ['## Overview', '## Key Decisions'],
    'gotcha_': ['## Problem', '## Solution'],
    'solution_': ['## Problem', '## Solution'],
    'pattern_': ['## Pattern', '## When to Use'],
}

def check_structure(filepath: str) -> tuple[bool, str]:
    """
    Check if file has required sections.
    Returns: (is_valid, error_message)
    """
    path = Path(filepath)
    filename = path.name

    # Skip non-markdown files
    if not filename.endswith('.md'):
        return True, ""

    # Find matching requirements
    required = None
    for prefix, sections in REQUIRED_SECTIONS.items():
        if filename.startswith(prefix):
            required = sections
            break

    if required is None:
        # No requirements for this file type
        return True, ""

    try:
        content = path.read_text(encoding='utf-8')

        missing = []
        for section in required:
            if section not in content:
                missing.append(section)

        if missing:
            return False, f"Missing required sections in {filename}: {', '.join(missing)}"

        return True, f"✅ {filename}: all required sections present"

    except Exception as e:
        return False, f"Error reading {filepath}: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: check_structure.py <file1.md> [file2.md ...]")
        sys.exit(1)

    errors = []

    for filepath in sys.argv[1:]:
        is_valid, message = check_structure(filepath)
        if message:
            if is_valid:
                print(message)
            else:
                errors.append(message)

    if errors:
        print("\n❌ Structure errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ All files have required sections")
        sys.exit(0)

if __name__ == "__main__":
    main()
