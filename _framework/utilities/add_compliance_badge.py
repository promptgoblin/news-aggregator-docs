#!/usr/bin/env python3
"""
Add or update compliance badge in markdown files.
Usage: python3 add_compliance_badge.py <file1.md> [file2.md ...]
"""

import sys
from pathlib import Path
from datetime import datetime

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

# Token budgets (simplified mapping)
BUDGETS = {
    '_status.md': 250,
    '_context.md': 300,
    'PLAN.md': 800,
    'plan_section_': 1200,
    'feature_': 1000,
    'gotcha_': 600,
    'solution_': 600,
    'pattern_': 600,
    'perf_': 600,
    'session_': 600,
    'audit_': 800,
    'checklist_': 700,
}

def get_budget(filepath: str) -> int:
    """Get token budget for a file."""
    filename = Path(filepath).name

    if filename in BUDGETS:
        return BUDGETS[filename]

    for prefix, budget in BUDGETS.items():
        if filename.startswith(prefix):
            return budget

    return None

def create_badge(filepath: str, content: str) -> str:
    """Create compliance badge for file."""
    budget = get_budget(filepath)
    if budget is None:
        return None  # No badge for files without budgets

    token_count = count_tokens(content)
    date = datetime.now().strftime("%Y-%m-%d")

    # Determine status
    if token_count <= budget:
        status = "✅"
    elif token_count <= budget * 1.2:  # Within 20% tolerance
        status = "⚠️"
    else:
        status = "❌"

    # Create compact badge
    budget_display = f"{budget//1000}k" if budget >= 1000 else str(budget)
    return f"<!-- VALIDATED: {date} | {token_count}/{budget_display} {status} -->"

def add_or_update_badge(filepath: str) -> bool:
    """Add or update compliance badge in file. Returns True if modified."""
    path = Path(filepath)

    if not filepath.endswith('.md'):
        return False

    try:
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Find title line (should be first line starting with #)
        title_idx = None
        for i, line in enumerate(lines):
            if line.startswith('#'):
                title_idx = i
                break

        if title_idx is None:
            # No title, can't add badge
            return False

        # Check if badge already exists after title
        badge_idx = None
        if title_idx + 1 < len(lines):
            if lines[title_idx + 1].strip().startswith('<!-- VALIDATED:'):
                badge_idx = title_idx + 1
            elif title_idx + 2 < len(lines) and lines[title_idx + 1].strip() == '':
                if lines[title_idx + 2].strip().startswith('<!-- VALIDATED:'):
                    badge_idx = title_idx + 2

        # Create new badge
        new_badge = create_badge(filepath, content)
        if new_badge is None:
            return False

        # Update or insert badge
        if badge_idx is not None:
            # Update existing badge
            old_badge = lines[badge_idx].strip()
            if old_badge != new_badge:
                lines[badge_idx] = new_badge
                path.write_text('\n'.join(lines), encoding='utf-8')
                return True
        else:
            # Insert new badge after title (with blank line)
            insert_idx = title_idx + 1
            if insert_idx < len(lines) and lines[insert_idx].strip() == '':
                # Already has blank line
                lines.insert(insert_idx + 1, new_badge)
            else:
                # Add blank line and badge
                lines.insert(insert_idx, '')
                lines.insert(insert_idx + 1, new_badge)

            path.write_text('\n'.join(lines), encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: add_compliance_badge.py <file1.md> [file2.md ...]")
        sys.exit(1)

    modified = []

    for filepath in sys.argv[1:]:
        if add_or_update_badge(filepath):
            modified.append(filepath)

    if modified:
        print(f"✅ Updated badges in {len(modified)} files:")
        for path in modified:
            print(f"  - {path}")
    else:
        print("ℹ️  No badges needed updating")

    sys.exit(0)

if __name__ == "__main__":
    main()
