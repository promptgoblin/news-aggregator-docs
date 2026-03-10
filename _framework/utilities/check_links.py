#!/usr/bin/env python3
"""
Check for broken internal links in markdown files.
Usage: python3 check_links.py <file1.md> [file2.md ...]
"""

import sys
import re
from pathlib import Path

def extract_internal_links(content: str) -> list[str]:
    """Extract internal markdown links from content."""
    # Match [text](path) and [path] style links
    # Exclude external URLs (http://, https://)
    links = []

    # [text](path) style
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        link = match.group(2)
        if not link.startswith('http://') and not link.startswith('https://') and not link.startswith('#'):
            # Remove anchor if present
            link = link.split('#')[0]
            if link:
                links.append(link)

    # [path.md] style (reference without explicit URL)
    for match in re.finditer(r'\[([^\]]+\.md)\](?!\()', content):
        link = match.group(1)
        links.append(link)

    return links

def resolve_link(source_file: Path, link: str) -> Path:
    """Resolve a relative link from source file."""
    # Handle ../ and ./ paths
    if link.startswith('../'):
        # Relative to parent directory
        return (source_file.parent / link).resolve()
    elif link.startswith('./'):
        # Relative to same directory
        return (source_file.parent / link[2:]).resolve()
    else:
        # Assume same directory
        return (source_file.parent / link).resolve()

def check_links(filepath: str) -> tuple[bool, list[str]]:
    """
    Check for broken internal links in file.
    Returns: (is_valid, broken_links)
    """
    path = Path(filepath)

    # Skip non-markdown files
    if not filepath.endswith('.md'):
        return True, []

    try:
        content = path.read_text(encoding='utf-8')
        links = extract_internal_links(content)

        broken = []
        for link in links:
            target = resolve_link(path, link)
            if not target.exists():
                broken.append(f"{link} → {target}")

        return len(broken) == 0, broken

    except Exception as e:
        return False, [f"Error reading file: {e}"]

def main():
    if len(sys.argv) < 2:
        print("Usage: check_links.py <file1.md> [file2.md ...]")
        sys.exit(1)

    all_broken = {}

    for filepath in sys.argv[1:]:
        is_valid, broken = check_links(filepath)
        if not is_valid:
            all_broken[filepath] = broken
        elif broken:
            all_broken[filepath] = broken

    if all_broken:
        print("❌ Broken internal links found:")
        for filepath, broken in all_broken.items():
            print(f"\n  {filepath}:")
            for link in broken:
                print(f"    - {link}")
        sys.exit(1)
    else:
        print("✅ No broken internal links")
        sys.exit(0)

if __name__ == "__main__":
    main()
