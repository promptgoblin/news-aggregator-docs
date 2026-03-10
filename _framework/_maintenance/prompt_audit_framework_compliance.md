# Maintenance: Audit Framework Compliance

## Objective
Verify all documentation follows framework conventions and fix violations automatically.

## What You'll Do

### 1. Scan All Documentation
```
- List all .md files in /docs (exclude _framework)
- Categorize by folder: plan/, features/, knowledge/, reference/, etc.
- Count total docs by type
```

### 2. Check Naming Conventions
For each document, verify:
- ✅ Uses lowercase (except PLAN.md, README.md)
- ✅ Uses underscores, not hyphens or spaces
- ✅ Follows type prefix pattern: feature_*, gotcha_*, api_*, etc.
- ✅ Dates use YYYY_MM_DD format
- ✅ No special characters

**Reference:** `/docs/_framework/NAMING_CONVENTIONS.md`

### 3. Verify Template Structure
For each doc type, check required sections exist:
- Features: User Intent, Status, Implementation, Dependencies
- Knowledge: Summary, Problem/Pattern, Solution, When to Use
- Plan Sections: Overview, Key Decisions, Design, Dependencies
- Session Logs: Objectives, Completed, Discoveries, Next Session

**Reference:** Check against templates in `/docs/_framework/template_*.md`

### 4. Validate Cross-References
- Find all references to other docs: `[filename.md]` or `docs/path/file.md`
- Verify each referenced file exists
- Check for broken links
- Identify references to non-existent files

### 5. Check Status Fields
- Features must have: Planning | In Progress | Testing | Complete
- PLAN.md must have: Planning | Building | Reviewing | Launching
- Session logs must have dates
- Check for placeholder text still present: [PLACEHOLDER], [NAME], [DATE]

## Auto-Fix When Possible

### Rename Files
- Fix capitalization issues
- Replace hyphens with underscores
- Add missing type prefixes if obvious from content

### Update Structure
- Add missing required sections to docs
- Move content to proper sections
- Add placeholders for missing content

### Fix References
- Update references to renamed files
- Fix path issues

## Report Format

### Summary
```
Total Docs Scanned: [X]
Violations Found: [Y]
Auto-Fixed: [Z]
Needs Manual Review: [W]
```

### Violations by Category
```
Naming Convention Violations: [count]
- [filename] → [issue] → [auto-fixed: yes/no]

Template Structure Violations: [count]
- [filename] → [missing section] → [auto-fixed: yes/no]

Broken References: [count]
- [filename] → [broken reference] → [suggested fix]

Stale Status/Placeholders: [count]
- [filename] → [issue]
```

### Manual Review Required
```
Files needing human decision:
- [filename]: [reason why can't auto-fix]
```

## Success Criteria

- [x] All docs scanned
- [x] Naming violations identified and fixed
- [x] Template structure checked
- [x] Cross-references validated
- [x] Report generated
- [x] Auto-fixes applied where safe
- [x] Manual review items documented

## Content Cleanup Powers

You MAY modify content when:
- **Removing duplicates**: Same info in multiple docs → consolidate to one, reference from others
- **Merging related docs**: Multiple docs on same topic → combine into proper template
- **Updating outdated info**: Old tech/approaches clearly superseded → update or add deprecation note
- **Extracting to knowledge**: Scattered gotchas/solutions → extract to knowledge base
- **Consolidating notes**: Random scattered notes → organize into proper sections

You MUST flag for review when:
- Conflicting information (not sure which is correct)
- Major content decisions (delete entire doc?)
- Unclear if information is current or outdated

## Notes

- Make backups before major changes (or rely on git)
- Be conservative - if unsure, flag for manual review
- Prioritize preserving information over perfect organization
- Update _index.md files if you rename/merge/delete docs
- Document all content changes in report
