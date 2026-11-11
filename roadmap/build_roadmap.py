#!/usr/bin/env python3
"""Validate roadmap.json and generate the self-contained roadmap.html.

Usage:
    python3 roadmap/build_roadmap.py [--copy-to DIR] [--check] [--json PATH] [--out PATH]

Standard library only. Exits non-zero with one line per problem if the JSON is invalid;
nothing is written in that case. See README.md in this folder for the schema and rules.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ("shipped", "building", "next", "idea", "dropped")
STORY_REQUIRED_STAGES = ("building", "next")
ITEM_KEYS = {"id", "title", "track", "stage", "one_liner", "depends_on", "story", "docs", "status_note"}
ITEM_REQUIRED = ("id", "title", "track", "stage", "one_liner")
STORY_KEYS = {"intent", "key_features", "reasoning", "open_questions"}
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ONE_LINER_SOFT_MAX = 120
PLACEHOLDER = "__ROADMAP_JSON__"


def _is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def find_cycle(deps: dict[str, list[str]]) -> list[str] | None:
    """Return one dependency cycle as a list of ids (first id repeated at the end), or None."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {k: WHITE for k in deps}
    for root in deps:
        if colour[root] != WHITE:
            continue
        path = [root]
        iters = [iter(deps[root])]
        colour[root] = GREY
        while iters:
            nxt = next(iters[-1], None)
            if nxt is None:
                colour[path.pop()] = BLACK
                iters.pop()
            elif nxt not in colour:
                continue  # unknown id, reported separately
            elif colour[nxt] == GREY:
                return path[path.index(nxt):] + [nxt]
            elif colour[nxt] == WHITE:
                colour[nxt] = GREY
                path.append(nxt)
                iters.append(iter(deps[nxt]))
    return None


def validate(data) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object with 'updated', 'tracks' and 'items'"], warnings

    extra = set(data) - {"updated", "tracks", "items"}
    if extra:
        errors.append(f"unknown top-level key(s): {', '.join(sorted(extra))}")
    updated = data.get("updated")
    if not (isinstance(updated, str) and DATE_RE.match(updated)):
        errors.append("'updated' must be a date string YYYY-MM-DD")

    tracks = data.get("tracks")
    track_ids: set[str] = set()
    if not isinstance(tracks, list) or not tracks:
        errors.append("'tracks' must be a non-empty list of {id, name}")
        tracks = []
    for i, t in enumerate(tracks):
        if not (isinstance(t, dict) and isinstance(t.get("id"), str) and isinstance(t.get("name"), str)
                and t["id"] and t["name"]):
            errors.append(f"tracks[{i}]: needs string 'id' and 'name'")
            continue
        if t["id"] in track_ids:
            errors.append(f"tracks: duplicate track id '{t['id']}'")
        track_ids.add(t["id"])

    items = data.get("items")
    if not isinstance(items, list) or not items:
        errors.append("'items' must be a non-empty list")
        return errors, warnings

    seen: dict[str, int] = {}
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errors.append(f"items[{i}]: must be an object")
            continue
        iid = it.get("id")
        if isinstance(iid, str) and iid:
            if iid in seen:
                errors.append(f"duplicate item id '{iid}' (items[{seen[iid]}] and items[{i}])")
            else:
                seen[iid] = i

    stage_of = {it["id"]: it.get("stage") for it in items
                if isinstance(it, dict) and isinstance(it.get("id"), str)}
    deps: dict[str, list[str]] = {}

    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        iid = it.get("id")
        where = f"item '{iid}'" if isinstance(iid, str) and iid else f"items[{i}]"

        for key in ITEM_REQUIRED:
            if not (isinstance(it.get(key), str) and it[key].strip()):
                errors.append(f"{where}: '{key}' is required and must be a non-empty string")
        unknown = set(it) - ITEM_KEYS
        if unknown:
            hint = ""
            if "unlocks" in unknown:
                hint = " ('unlocks' is derived from depends_on; never store it)"
            elif unknown & {"date", "due", "eta", "target", "deadline", "quarter", "when"}:
                hint = " (no dates on items: the roadmap is sequence and dependencies only)"
            errors.append(f"{where}: unknown key(s) {', '.join(sorted(unknown))}{hint}")
        if isinstance(iid, str) and iid and not ID_RE.match(iid):
            errors.append(f"{where}: id must be kebab-case (lowercase letters, digits, hyphens)")

        stage = it.get("stage")
        if isinstance(stage, str) and stage not in STAGES:
            errors.append(f"{where}: unknown stage '{stage}' (use one of: {', '.join(STAGES)})")
        track = it.get("track")
        if isinstance(track, str) and track_ids and track not in track_ids:
            errors.append(f"{where}: unknown track '{track}' (known: {', '.join(sorted(track_ids))})")

        one = it.get("one_liner")
        if isinstance(one, str) and len(one) > ONE_LINER_SOFT_MAX:
            warnings.append(f"{where}: one_liner is {len(one)} chars; keep it under ~{ONE_LINER_SOFT_MAX}")

        dl = it.get("depends_on", [])
        if not (isinstance(dl, list) and all(isinstance(d, str) for d in dl)):
            errors.append(f"{where}: 'depends_on' must be a list of item ids")
            dl = []
        if len(set(dl)) != len(dl):
            errors.append(f"{where}: 'depends_on' lists the same id twice")
        for d in dl:
            if d == iid:
                errors.append(f"{where}: depends on itself")
            elif d not in seen:
                errors.append(f"{where}: depends_on '{d}' does not exist")
            elif stage_of.get(d) == "dropped" and stage != "dropped":
                errors.append(f"{where}: depends on '{d}', which is dropped; remove the dependency or drop this item")
            elif stage == "shipped" and stage_of.get(d) in ("building", "next", "idea"):
                errors.append(f"{where}: is shipped but depends on '{d}', which is {stage_of[d]}; "
                              f"a shipped item cannot wait on unshipped work")
        if isinstance(iid, str) and iid:
            deps[iid] = [d for d in dl if d in seen and d != iid]

        story = it.get("story")
        if story is None:
            if stage in STORY_REQUIRED_STAGES:
                errors.append(f"{where}: stage '{stage}' needs a 'story' with intent, key_features and reasoning")
        elif not isinstance(story, dict):
            errors.append(f"{where}: 'story' must be an object")
        else:
            bad = set(story) - STORY_KEYS
            if bad:
                errors.append(f"{where}: unknown story key(s) {', '.join(sorted(bad))}")
            for key in ("intent", "reasoning"):
                if key in story and not isinstance(story[key], str):
                    errors.append(f"{where}: story.{key} must be a string")
            for key in ("key_features", "open_questions"):
                if key in story and story[key] != [] and not _is_str_list(story[key]):
                    errors.append(f"{where}: story.{key} must be a list of non-empty strings")
            if stage in STORY_REQUIRED_STAGES:
                for key in ("intent", "reasoning"):
                    if not (isinstance(story.get(key), str) and story[key].strip()):
                        errors.append(f"{where}: stage '{stage}' needs a non-empty story.{key}")
                if not (_is_str_list(story.get("key_features")) and story["key_features"]):
                    errors.append(f"{where}: stage '{stage}' needs at least one story.key_features entry")

        docs = it.get("docs", [])
        if docs != [] and not _is_str_list(docs):
            errors.append(f"{where}: 'docs' must be a list of repo paths")
        else:
            for d in docs:
                if re.match(r"^[a-z]+://", d):
                    errors.append(f"{where}: docs entry '{d}' is a URL; use a path inside the docs repo")
                elif not (HERE.parent / d).exists():
                    warnings.append(f"{where}: docs path '{d}' not found in the docs repo")
        if "status_note" in it and not isinstance(it["status_note"], str):
            errors.append(f"{where}: 'status_note' must be a string")

    cycle = find_cycle(deps)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle) + "  (each item depends on the next)")
    return errors, warnings


def render(data, template: str) -> str:
    if template.count(PLACEHOLDER) != 1:
        raise SystemExit(f"template.html must contain {PLACEHOLDER} exactly once")
    # '</' cannot appear inside a <script> element; '<\/' is the same string to a JSON parser.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return template.replace(PLACEHOLDER, payload)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate roadmap.json and build roadmap.html")
    ap.add_argument("--json", type=Path, default=HERE / "roadmap.json", help="source JSON (default: roadmap/roadmap.json)")
    ap.add_argument("--out", type=Path, default=HERE / "roadmap.html", help="output HTML (default: roadmap/roadmap.html)")
    ap.add_argument("--copy-to", type=Path, metavar="DIR", help="also copy the generated HTML into DIR")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = ap.parse_args(argv)

    try:
        data = json.loads(args.json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"roadmap: {args.json} not found", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"roadmap: {args.json} is not valid JSON: {e}", file=sys.stderr)
        return 2

    errors, warnings = validate(data)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        print(f"roadmap: {len(errors)} validation error(s) in {args.json}; nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    counts = {s: sum(1 for it in data["items"] if it["stage"] == s) for s in STAGES}
    summary = ", ".join(f"{s} {n}" for s, n in counts.items())
    if args.check:
        print(f"roadmap: valid ({len(data['items'])} items: {summary})")
        return 0

    # template.html is a page FRAGMENT (title, style, markup, script; no html/head/body), which is the
    # form a hosted page publisher expects. The local file wraps it in a minimal document.
    fragment = render(data, (HERE / "template.html").read_text(encoding="utf-8"))
    args.out.with_suffix(".fragment.html").write_text(fragment, encoding="utf-8")
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '</head>\n<body>\n' + fragment + '\n</body>\n</html>\n')
    args.out.write_text(html, encoding="utf-8")
    print(f"roadmap: wrote {args.out} ({len(data['items'])} items: {summary})")
    if args.copy_to:
        if not args.copy_to.is_dir():
            print(f"roadmap: --copy-to {args.copy_to} is not a directory", file=sys.stderr)
            return 2
        dest = args.copy_to / args.out.name
        shutil.copyfile(args.out, dest)
        print(f"roadmap: copied to {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
