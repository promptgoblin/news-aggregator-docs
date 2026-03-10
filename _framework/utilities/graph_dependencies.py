#!/usr/bin/env python3
"""
Dependency Graph Utility

Parses YAML frontmatter from docs to:
- Generate Mermaid dependency diagrams
- Detect circular dependencies
- Validate bidirectional consistency
- Report orphaned features

Usage:
    python graph_dependencies.py [--output mermaid|text] [--check-cycles] [--validate]
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

def extract_frontmatter(file_path: str) -> Dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match YAML frontmatter between --- delimiters
        # Can be at start or after title line
        match = re.search(r'\n?---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}

        frontmatter = {}
        yaml_content = match.group(1)

        # Parse simple YAML fields (enough for our use case)
        # Handle type, status, depends_on, required_by, tags
        for line in yaml_content.split('\n'):
            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle list values in brackets
            if value.startswith('[') and value.endswith(']'):
                # Remove brackets and split by comma
                items = value[1:-1].split(',')
                frontmatter[key] = [item.strip() for item in items if item.strip()]
            else:
                frontmatter[key] = value

        return frontmatter
    except Exception as e:
        print(f"Warning: Error reading {file_path}: {e}", file=sys.stderr)
        return {}

def scan_docs(docs_dir: str) -> Dict[str, Dict]:
    """Scan all markdown files and extract frontmatter."""
    docs = {}
    docs_path = Path(docs_dir)

    # Skip _framework directory
    for md_file in docs_path.rglob('*.md'):
        if '_framework' in md_file.parts:
            continue
        if 'archive' in md_file.parts:
            continue

        frontmatter = extract_frontmatter(str(md_file))
        if frontmatter:
            # Store relative path from docs/ directory
            rel_path = md_file.relative_to(docs_path)
            docs[str(rel_path)] = frontmatter

    return docs

def build_dependency_graph(docs: Dict[str, Dict]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build dependency graph from frontmatter.

    Returns:
        (depends_on_graph, required_by_graph)
    """
    depends_on = defaultdict(list)
    required_by = defaultdict(list)

    for doc_path, frontmatter in docs.items():
        # Extract depends_on
        deps = frontmatter.get('depends_on', [])
        if isinstance(deps, str):
            deps = [deps] if deps else []
        depends_on[doc_path] = deps

        # Extract required_by
        reqs = frontmatter.get('required_by', [])
        if isinstance(reqs, str):
            reqs = [reqs] if reqs else []
        required_by[doc_path] = reqs

    return dict(depends_on), dict(required_by)

def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles

def validate_bidirectional(depends_on: Dict[str, List[str]], required_by: Dict[str, List[str]]) -> List[str]:
    """Validate bidirectional consistency.

    If A depends_on B, then B should have A in required_by.
    """
    errors = []

    # Check depends_on → required_by
    for doc, deps in depends_on.items():
        for dep in deps:
            if dep not in required_by or doc not in required_by[dep]:
                errors.append(f"{doc} depends_on {dep}, but {dep} doesn't list {doc} in required_by")

    # Check required_by → depends_on
    for doc, reqs in required_by.items():
        for req in reqs:
            if req not in depends_on or doc not in depends_on[req]:
                errors.append(f"{doc} required_by {req}, but {req} doesn't list {doc} in depends_on")

    return errors

def generate_mermaid(depends_on: Dict[str, List[str]], docs: Dict[str, Dict]) -> str:
    """Generate Mermaid flowchart from dependency graph."""
    lines = ["```mermaid", "graph TD"]

    # Create nodes with labels
    node_ids = {}
    for i, doc_path in enumerate(depends_on.keys()):
        node_id = f"N{i}"
        node_ids[doc_path] = node_id

        # Get doc type and name for label
        frontmatter = docs.get(doc_path, {})
        doc_type = frontmatter.get('type', 'unknown')
        doc_name = Path(doc_path).stem

        # Create label with type badge
        label = f"{doc_name}<br/>[{doc_type}]"
        lines.append(f"    {node_id}[\"{label}\"]")

    # Add edges
    for doc, deps in depends_on.items():
        if not deps:
            continue
        for dep in deps:
            if dep in node_ids and doc in node_ids:
                lines.append(f"    {node_ids[doc]} --> {node_ids[dep]}")

    lines.append("```")
    return "\n".join(lines)

def generate_text_report(depends_on: Dict[str, List[str]], required_by: Dict[str, List[str]]) -> str:
    """Generate human-readable text report."""
    lines = ["# Dependency Graph Report\n"]

    # Overall stats
    total_docs = len(set(depends_on.keys()) | set(required_by.keys()))
    docs_with_deps = sum(1 for deps in depends_on.values() if deps)
    docs_required = sum(1 for reqs in required_by.values() if reqs)

    lines.append(f"## Summary\n")
    lines.append(f"- Total documents: {total_docs}")
    lines.append(f"- Documents with dependencies: {docs_with_deps}")
    lines.append(f"- Documents required by others: {docs_required}")
    lines.append("")

    # Dependencies
    lines.append("## Dependencies (depends_on)\n")
    for doc in sorted(depends_on.keys()):
        deps = depends_on[doc]
        if deps:
            lines.append(f"**{doc}**")
            for dep in deps:
                lines.append(f"  - depends on: {dep}")
            lines.append("")

    # Required by
    lines.append("## Required By\n")
    for doc in sorted(required_by.keys()):
        reqs = required_by[doc]
        if reqs:
            lines.append(f"**{doc}**")
            for req in reqs:
                lines.append(f"  - required by: {req}")
            lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Analyze documentation dependencies')
    parser.add_argument('--docs-dir', default='docs', help='Documentation directory (default: docs)')
    parser.add_argument('--output', choices=['mermaid', 'text'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--check-cycles', action='store_true',
                        help='Check for circular dependencies')
    parser.add_argument('--validate', action='store_true',
                        help='Validate bidirectional consistency')

    args = parser.parse_args()

    # Scan documents
    docs = scan_docs(args.docs_dir)
    if not docs:
        print("No documents with frontmatter found", file=sys.stderr)
        return 1

    # Build dependency graphs
    depends_on, required_by = build_dependency_graph(docs)

    # Check for cycles if requested
    if args.check_cycles:
        cycles = detect_cycles(depends_on)
        if cycles:
            print("❌ Circular dependencies detected:\n", file=sys.stderr)
            for cycle in cycles:
                print(f"  {' → '.join(cycle)}", file=sys.stderr)
            return 1
        else:
            print("✅ No circular dependencies found")

    # Validate bidirectional consistency if requested
    if args.validate:
        errors = validate_bidirectional(depends_on, required_by)
        if errors:
            print("❌ Bidirectional consistency errors:\n", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1
        else:
            print("✅ Bidirectional consistency validated")

    # Generate output
    if args.output == 'mermaid':
        print(generate_mermaid(depends_on, docs))
    else:
        print(generate_text_report(depends_on, required_by))

    return 0

if __name__ == '__main__':
    sys.exit(main())
