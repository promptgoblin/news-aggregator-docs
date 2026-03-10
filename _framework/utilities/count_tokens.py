#!/usr/bin/env python3
# Run from project root: python3 utilities/count_tokens.py
# Or use venv: utilities/venv/bin/python utilities/count_tokens.py
"""
Count tokens in all markdown documentation files.
Uses tiktoken with cl100k_base encoding (GPT-4/Claude comparable).
"""

import os
from pathlib import Path
from datetime import datetime

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed")
    print("Install with: pip install tiktoken")
    exit(1)

# Initialize tokenizer (cl100k_base is used by GPT-4, close enough for Claude)
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))

def main():
    # Find all markdown files in docs/
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("Error: docs/ directory not found")
        exit(1)

    md_files = sorted(docs_dir.rglob("*.md"))

    if not md_files:
        print("No markdown files found in docs/")
        exit(1)

    # Count tokens for each file
    results = []
    total_tokens = 0

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            tokens = count_tokens(content)
            total_tokens += tokens

            # Calculate relative path from docs directory
            rel_path = str(md_file)
            results.append((rel_path, tokens))
        except Exception as e:
            print(f"Warning: Could not process {md_file}: {e}")

    # Generate markdown output
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_lines = [
        "# Documentation Token Counts",
        "",
        f"Last updated: {timestamp}",
        f"Total tokens: {total_tokens:,}",
        f"Total files: {len(results)}",
        "",
        "| Path | Tokens |",
        "|------|--------|",
    ]

    # Sort by token count (descending) for easy identification of large files
    results.sort(key=lambda x: x[1], reverse=True)

    for path, tokens in results:
        output_lines.append(f"| {path} | {tokens:,} |")

    # Write to file
    output_path = Path("docs/_framework/token_counts.md")
    output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    # Also print to console
    print("\n".join(output_lines))
    print(f"\n✓ Saved to {output_path}")

if __name__ == "__main__":
    main()
