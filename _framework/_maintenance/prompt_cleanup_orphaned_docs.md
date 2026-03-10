# Maintenance: Cleanup Orphaned Docs

## Objective
Remove or archive documentation that's outdated, unreferenced, or duplicate to keep the docs clean and focused.

## What You'll Do

### 1. Find Orphaned Documents
Scan all docs and identify:
- **Unreferenced docs**: Not linked from any other doc
- **No incoming references**: Not in any index, not referenced by features/plan
- **Exception**: PLAN.md, _status.md, _context.md, README.md (entry points don't need incoming refs)

### 2. Find Stale Status Markers
Look for docs with:
- Status: "Complete" but Last Updated >6 months ago
- Status: "In Progress" but Last Updated >3 months ago
- Features marked "Planning" but have implementation details
- Dates in the future or obviously wrong

### 3. Identify Duplicates
Check for:
- Multiple docs covering same topic
- Content copy-pasted between docs (violates "link, don't duplicate")
- Same information in plan section AND feature doc (should be in one, referenced from other)

### 4. Find Empty or Placeholder Docs
- Docs with only template structure, no real content
- Docs with [PLACEHOLDER] text still present
- Files created but never filled out

### 5. Find Backup and Old Files
Scan for files that clutter the docs:
- `.backup`, `.bak`, `.old` extensions
- Tilde suffixes: `~`, `.swp`, `.tmp`
- Version suffixes: `_v1`, `_v2`, `_old`, `_backup`, `_copy`
- Date suffixes without proper naming: `feature_2024_01_15` (not a session log)
- Examples: `PLAN.md.backup`, `feature_auth_old.md`, `notes_v2.md`

### 6. Scan for Outdated Content
- References to deprecated tech/libraries
- Old architecture that's changed
- Features that were removed or replaced
- Session logs >6 months old (consider archiving)

## Analysis Report

### Orphaned Documents
```
Files with no incoming references:
- [filename] - Created: [date] - Last Updated: [date]
- Action: [Archive | Delete | Add to index | Link from X]
```

### Stale Status
```
Files with outdated status:
- [filename] - Status: [status] - Last Updated: [date]
- Action: [Update status | Archive | Mark deprecated]
```

### Duplicates Found
```
Duplicate content detected:
- [file1] and [file2] cover [topic]
- Action Taken: [Merged into file1, archived file2]
- Content consolidated: [what was merged]
- Differences preserved: [any unique info from file2]
```

### Empty/Placeholder Docs
```
Incomplete documents:
- [filename] - [X% placeholders remaining]
- Action: [Complete | Delete | Archive]
```

### Backup/Old Files Found
```
Backup and versioned files cluttering docs:
- [filename.backup] - Created: [date]
- [filename_old.md] - Created: [date]
- [filename_v2.md] - Created: [date]
- Action: [Archive to /docs/archive/ | Compare with current and delete if identical]
```

### Outdated Content
```
Potentially outdated:
- [filename] - [Reason: old tech, changed architecture, etc.]
- Action: [Update | Archive | Mark deprecated]
```

## Cleanup Actions

### Merge & Consolidate
When multiple docs cover the same topic:
- Choose best template/structure to keep
- Merge unique content from all sources
- Preserve valuable details from each
- Archive originals with "Merged into [target]" note
- Update all references to point to merged doc

### Extract & Organize
When valuable info is scattered:
- Extract gotchas → knowledge/gotcha_*.md
- Extract solutions → knowledge/solution_*.md
- Extract decisions → plan sections
- Leave reference in original location if needed

### Archive
Move to `/docs/archive/[YYYY_MM]/`:
- Old session logs (>6 months)
- Deprecated features (after extracting lessons learned)
- Outdated plan sections (after noting what changed)
- Superseded iterations (keep latest, archive old)
- Add note in archived file: "Archived [date] - [reason]"

### Delete
Remove completely (only if truly useless):
- Empty template copies never filled out
- Duplicates fully merged elsewhere
- Test docs that served their purpose
- Random notes fully incorporated elsewhere
- Backup files identical to current version (`.backup`, `.bak`, `_old.md`)
- Editor temp files (`.swp`, `~`, `.tmp`)

### Update
Fix in place:
- Add missing cross-references
- Update stale status fields
- Complete placeholder docs
- Refresh outdated content
- Add deprecation notices where appropriate

### Link/Index
Add to appropriate index:
- Orphaned docs that should be discoverable
- Add to _index.md or parent doc references

## Execute Cleanup

### Phase 1: Safe Actions
- Archive old session logs
- Delete or archive backup/old files (compare first)
- Delete editor temp files (.swp, ~, .tmp)
- Delete empty placeholder docs
- Update stale status fields
- Add orphaned docs to indexes

### Phase 2: Review Required
Present list of:
- Potential duplicates (need merge decision)
- Potentially outdated content (need validation)
- Orphaned docs that might be unused (need keep/archive decision)

## Cleanup Checklist

- [ ] All docs scanned for orphans
- [ ] Stale status markers identified
- [ ] Duplicates found and analyzed
- [ ] Empty docs identified
- [ ] Outdated content flagged
- [ ] Archive folder created: /docs/archive/[YYYY_MM]/
- [ ] Safe cleanup actions executed
- [ ] Review items documented
- [ ] Indexes updated to reflect cleanup
- [ ] PLAN.md updated if features removed

## Report Format

### Cleanup Summary
```
Total Docs Before: [X]
Archived: [Y]
Deleted: [Z]
Updated: [W]
Total Docs After: [X-Y-Z]

Disk Space Saved: [if significant]
```

### Actions Taken

**Merged & Consolidated:**
```
- [target_file]: Merged content from:
  - [source_file_1]: [unique content preserved]
  - [source_file_2]: [unique content preserved]
  Sources archived to /docs/archive/[YYYY_MM]/
```

**Extracted & Organized:**
```
- Created knowledge/gotcha_[name].md from scattered notes in:
  - [source_file_1]: [what was extracted]
- Created knowledge/solution_[name].md from:
  - [source_file]: [what was extracted]
```

**Archived to /docs/archive/[YYYY_MM]/:**
```
- [file]: [reason]
- [file]: Superseded by [new_file]
- [file]: Deprecated, lessons extracted to [knowledge_file]
```

**Deleted:**
```
- [file]: [reason - empty/duplicate/test]
- [file.backup]: Identical to current version
- [file_old.md]: Content merged into [current_file.md]
- [*.swp, *~]: Editor temp files
```

**Updated:**
```
- [filename]: [what was updated]
- [filename]: Added deprecation notice, points to [new_approach]
```

**Added to indexes:**
```
- [filename]: [which index]
```

### Needs Manual Review
```
Duplicates requiring merge decision:
- [file1] vs [file2]: [overlapping topic]

Potentially outdated (verify before action):
- [filename]: [why might be outdated]

Orphaned docs (keep or archive?):
- [filename]: [context]
```

## Success Criteria

- [x] All orphaned docs identified
- [x] Stale status markers fixed
- [x] Duplicates found and handled
- [x] Empty docs cleaned up
- [x] Archive folder organized
- [x] Indexes reflect current state
- [x] Report generated
- [x] Manual review items documented

## Notes

- Don't delete knowledge entries - archive them (might be useful later)
- Session logs >6 months old → archive automatically
- When in doubt, archive rather than delete
- Keep at least last 10 session logs even if old
- Update PLAN.md if you remove features
- **Backup files (.backup, .old, _v2)**: Compare with current first, then delete if identical or archive if different
- **Editor temp files**: Always safe to delete (.swp, ~, .tmp)
- **Versioned files**: If multiple versions exist, keep latest, archive others with note of what changed
