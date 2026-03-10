# Maintenance: Migrate Existing Docs to Framework

## Objective
Convert an existing project's documentation to this framework structure while preserving all valuable content.

## What You'll Do

### 1. Analyze Existing Structure
```
- List all existing .md files in the project
- Identify doc categories (README, architecture, features, API docs, etc.)
- Note current folder structure
- Identify valuable content vs. outdated/redundant
```

### 2. Map to Framework Doc Types
For each existing doc, determine:
- **Planning doc?** → plan/PLAN.md or plan/plan_section_*.md
- **Feature/capability?** → features/feature_*.md
- **API/library reference?** → reference/api_*.md or lib_*.md
- **Lesson/gotcha?** → knowledge/gotcha_*.md or solution_*.md
- **Process/checklist?** → checklists/checklist_*.md
- **Other?** → Determine appropriate location

### 3. Create Framework Structure
```
Create folders if they don't exist:
- docs/plan/
- docs/features/
- docs/knowledge/
- docs/reference/
- docs/checklists/
- docs/audits/
- docs/sessions/
- docs/_framework/ (copy framework templates here)
```

### 4. Migrate Content

For each document:

**Step 1:** Choose appropriate template
**Step 2:** Copy template to proper location with framework naming
**Step 3:** Extract content from old doc
**Step 4:** Map content to template sections
**Step 5:** Fill any gaps with placeholders or notes

#### Common Mappings

**Old README → plan/PLAN.md**
- Project description → Vision
- Tech stack choices → Quick Decisions
- Feature list → Features section

**Old architecture.md → plan/plan_section_architecture.md**
- System design → Design section
- Tech choices → Key Decisions
- Diagrams → Keep in Design section

**Old features/X.md → features/feature_X.md**
- Description → User Intent > Goal
- Requirements → User Intent > Success Criteria
- Implementation → Implementation section
- Add missing sections (Status, Dependencies, Testing)

**Old docs/api.md → Multiple reference/api_*.md**
- Split by service/topic
- Each API gets its own doc

**Old TROUBLESHOOTING.md → Multiple knowledge/gotcha_*.md**
- One gotcha doc per issue
- Extract to knowledge base

### 5. Create PLAN.md
```
1. Extract project vision from existing docs
2. List tech stack decisions
3. Create plan sections for major areas
4. List features (link to feature docs)
5. Define phases and milestones
```

### 6. Create Index and Status Files
```
- docs/_status.md: Current work state (from template_STATUS.md - manual, not auto-generated)
- docs/_context.md: Project context and history (from template_CONTEXT.md - manual)
- docs/knowledge/_index.md: Search index of gotchas/solutions/patterns
- docs/reference/_index.md: Search index of external docs
```

### 7. Establish Cross-References
```
- Link features to plan sections
- Link knowledge entries to features where applied
- Link reference docs from features that use them
- Ensure bidirectional references
```

### 8. Archive Old Docs
```
Create /docs/archive/ folder
Move original docs there with date stamp
Add note in each: "Migrated to [new location]"
```

## Migration Checklist

### Preparation
- [ ] Backup existing docs (git commit)
- [ ] Copy framework templates to docs/_framework/
- [ ] Create folder structure

### Content Migration
- [ ] PLAN.md created with vision and decisions
- [ ] Plan sections created for major areas
- [ ] Features migrated to feature_*.md docs
- [ ] Reference docs split and organized
- [ ] Knowledge base populated from troubleshooting/lessons
- [ ] Checklists extracted if applicable

### Organization
- [ ] All docs follow naming conventions
- [ ] All docs use proper templates
- [ ] Cross-references established
- [ ] Index files created
- [ ] Old docs archived with migration notes

### Validation
- [ ] No content lost
- [ ] All important info has a home
- [ ] Links between docs work
- [ ] Framework structure followed

## Report Format

### Migration Summary
```
Original Docs: [X]
Migrated to Plan: [count]
Migrated to Features: [count]
Migrated to Knowledge: [count]
Migrated to Reference: [count]
Migrated to Checklists: [count]
Archived: [count]
```

### New Structure
```
docs/
├── PLAN.md
├── plan/
│   ├── plan_section_*.md [list them]
├── features/
│   ├── feature_*.md [list them]
├── knowledge/
│   ├── [type]_*.md [list them]
├── reference/
│   ├── [prefix]_*.md [list them]
└── archive/
    ├── [old docs]
```

### Content Transformations
```
Merged & Consolidated:
- feature_auth.md: Merged from [old_auth.md, old_login.md, old_oauth.md]
- plan_section_architecture.md: Consolidated from [arch_v1.md, design_notes.md, tech_stack.md]

Extracted & Separated:
- knowledge/gotcha_*.md: Extracted 5 gotchas from old_troubleshooting.md
- knowledge/solution_*.md: Extracted 3 solutions from old_wiki_dump.md

Updated & Modernized:
- [file]: Updated "React 16" → "React 18", noted migration needed
- [file]: Added deprecation notice for old auth approach

Marked for Verification:
- [file]: Contains potentially outdated deployment info (⚠️ note added)
- [file]: Conflicting info with [other_file] (flagged for resolution)
```

### Content Not Migrated
```
Files not migrated (and why):
- [filename]: [reason - outdated, redundant, etc.]
- [filename]: Fully duplicated by [new_file], no unique content
```

## Success Criteria

- [x] All valuable content preserved
- [x] New framework structure in place
- [x] All docs follow templates
- [x] Cross-references established
- [x] Indexes created
- [x] Old docs archived
- [x] Nothing lost

## Content Transformation Powers

During migration, you MAY:

### Merge & Consolidate
- Combine multiple old docs about same feature into one feature_*.md
- Merge scattered architecture notes into plan_section_architecture.md
- Consolidate API docs into organized reference docs

### Extract & Separate
- Pull gotchas from troubleshooting docs → individual knowledge entries
- Extract decisions from meeting notes → plan sections
- Separate mixed content into proper doc types

### Update & Modernize
- Update outdated terminology to current
- Fix references to old architecture
- Add deprecation notices where appropriate
- Note what's changed since doc was written

### Organize & Structure
- Impose template structure on unstructured content
- Group related scattered content together
- Create proper hierarchies (features, sub-features)

### Document Uncertainty
- Note where info might be outdated: "⚠️ Pre-migration note: verify if still current"
- Mark sections needing validation: "TODO: Verify this approach still used"
- Flag conflicting info: "⚠️ Conflicts with [other_doc], needs resolution"

## Notes

- Archive originals - don't delete anything
- When in doubt, migrate it (can clean up later with cleanup prompt)
- Document all transformations in migration report
- It's okay to have incomplete sections - mark with TODO
- Prioritize preserving information over perfect organization
- Note migration date in each doc: "Migrated from [old_location] on [date]"
