# Maintenance: Fix Broken References

## Objective
Find and fix all broken cross-references between documentation files to maintain navigation integrity.

## What You'll Do

### 1. Extract All References

Scan all .md files in /docs for references in these formats:
- `[filename.md]` - Markdown link reference
- `[text](filename.md)` - Inline markdown link
- `[text](../path/filename.md)` - Relative path link
- `docs/folder/filename.md` - Plain text reference
- `See feature_name.md` - Prose reference

Build a reference map:
```
File: docs/features/feature_auth.md
References:
  - plan/plan_section_auth.md (line 28)
  - reference/api_auth0.md (line 45)
  - knowledge/gotcha_jwt_refresh.md (line 89)
```

### 2. Validate Each Reference

For each reference found:
- Check if target file exists at specified path
- Verify path is correct (relative vs absolute)
- Note if target was likely renamed (similar name exists)

### 3. Identify Broken References

Categorize issues:

**Missing Files:**
- Referenced file doesn't exist at any path
- May have been deleted or renamed

**Wrong Paths:**
- File exists but path is wrong
- Common with relative paths (../../../)

**Renamed Files:**
- Reference uses old name
- New file with similar name exists

**Circular Dependencies:**
- Doc A references Doc B references Doc A
- Not broken, but note for awareness

### 4. Find Suggested Fixes

For each broken reference:

**If file doesn't exist:**
- Search for similar filenames
- Check /docs/archive/ for moved files
- Suggest creating file if makes sense
- Suggest removing reference if outdated

**If wrong path:**
- Find correct path
- Suggest path fix

**If renamed:**
- Identify new filename
- Suggest reference update

### 5. Auto-Fix Safe Issues

Automatically fix:
- Wrong relative paths (can determine correct path)
- References to renamed files (if mapping is clear)
- Path format issues (e.g., missing .md extension)

### 6. Flag for Manual Review

Human review needed for:
- References to non-existent files (delete reference or create file?)
- Multiple possible matches for broken reference
- Circular dependencies (if problematic)
- Ambiguous renames

## Analysis Report

### Broken References by Type

**Missing Files ([count]):**
```
[source_file.md] line [X] → [target_file.md]
  Status: File doesn't exist
  Suggestion: [Create file | Remove reference | Check archive]
  Similar files: [list if any]
```

**Wrong Paths ([count]):**
```
[source_file.md] line [X] → [wrong/path/file.md]
  Status: File exists at [correct/path/file.md]
  Auto-fix: Update path
```

**Renamed Files ([count]):**
```
[source_file.md] line [X] → [old_name.md]
  Status: File renamed to [new_name.md]
  Auto-fix: Update reference
```

**Circular Dependencies ([count]):**
```
[file_a.md] ↔ [file_b.md]
  Status: Circular reference (may be intentional)
  Action: Note only, no fix needed
```

### Reference Statistics
```
Total references found: [X]
Valid references: [Y]
Broken references: [Z]
Auto-fixed: [W]
Manual review needed: [V]
```

## Execute Fixes

### Auto-Fix Phase
For safe fixes:
- Update wrong paths
- Update references to renamed files
- Fix path format issues
- Add .md extensions where missing

### Manual Review Items
```
Files needing human decision:

1. [source] → [missing_target]
   Options:
   a) Create [missing_target] (recommended if referenced multiple times)
   b) Remove reference (if outdated)
   c) Redirect to different file

2. [source] → [ambiguous_target]
   Possible matches:
   a) [option_1.md]
   b) [option_2.md]
   Which should it reference?
```

## Validation

After fixes:
- Re-scan all docs
- Verify broken references reduced
- Check auto-fixes didn't break anything
- Confirm circular deps are intentional

## Fix Checklist

- [ ] All .md files scanned for references
- [ ] Reference map built
- [ ] Each reference validated
- [ ] Broken references categorized
- [ ] Safe auto-fixes applied
- [ ] Manual review items documented
- [ ] Validation scan completed
- [ ] Report generated

## Report Format

### Fix Summary
```
References Before: [X total], [Y broken]
References After: [X total], [Z broken]
Auto-Fixed: [count]
Still Broken: [count requiring manual review]
```

### Auto-Fixes Applied
```
Path corrections: [count]
- [file] line [X]: [old_path] → [new_path]

Renamed file updates: [count]
- [file] line [X]: [old_name] → [new_name]

Format fixes: [count]
- [file] line [X]: [issue fixed]
```

### Still Broken (Manual Review)
```
Missing files: [count]
- [source] → [target]: [recommendation]

Ambiguous: [count]
- [source] → [target]: [possible matches]
```

### Circular Dependencies Found
```
Intentional bidirectional references:
- [file_a] ↔ [file_b]: [context]
```

## Success Criteria

- [x] All files scanned
- [x] All references extracted and validated
- [x] Broken references categorized
- [x] Safe fixes auto-applied
- [x] Manual review items documented with suggestions
- [x] Validation completed
- [x] Report generated

## Notes

- Circular refs between features and plan sections are normal
- Parent/child feature refs are bidirectional by design
- Don't break working relative paths
- Preserve link text, only fix targets
- Update indexes if you rename files
- Test a few fixes before bulk applying
