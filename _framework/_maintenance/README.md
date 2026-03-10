# Maintenance Prompts

Use these prompts to fix, audit, or migrate documentation when things get messy or you're adopting the framework mid-project.

## Available Prompts

### `prompt_audit_framework_compliance.md`
**Use when:** Agent has been creating docs that don't follow framework conventions
**What it does:**
- Checks all docs against naming conventions
- Verifies template structure compliance
- Validates cross-references
- Auto-fixes violations where safe
- **Can merge duplicates and consolidate content**
- **Can extract knowledge from scattered notes**
- Reports what needs manual review

### `prompt_migrate_existing_docs.md`
**Use when:** Converting an existing project to this framework
**What it does:**
- Analyzes existing documentation structure
- Maps existing docs to framework doc types
- **Merges multiple old docs into single framework docs**
- **Extracts gotchas/solutions to knowledge base**
- **Updates outdated terminology and references**
- Migrates content into proper templates
- Creates missing index files
- Documents uncertainties for verification
- Archives originals safely

### `prompt_cleanup_orphaned_docs.md`
**Use when:** Project has accumulated stale or unreferenced docs
**What it does:**
- Identifies docs not referenced anywhere
- Finds outdated status markers
- **Merges duplicate content intelligently**
- **Extracts valuable info from scattered notes**
- **Consolidates multiple docs on same topic**
- Archives old iterations and deprecated features
- Updates or removes orphaned files
- Updates indexes to reflect cleanup

### `prompt_rebuild_indexes.md`
**Use when:** Search index files are outdated or missing entries
**What it does:**
- Scans knowledge/ and reference/ folders
- Regenerates knowledge/_index.md and reference/_index.md (search indexes only)
- Creates concise, search-optimized descriptions
- Maintains proper formatting
- Verifies _status.md and _context.md (does NOT auto-rebuild them)

### `prompt_fix_broken_references.md`
**Use when:** Cross-references between docs are broken or invalid
**What it does:**
- Finds all cross-references in docs
- Validates each reference exists
- Identifies circular dependencies
- Reports broken links
- Suggests fixes or updates references

### `prompt_archive_session_logs.md`
**Use when:** End of quarter or sessions/ folder has >50 files
**What it does:**
- Groups sessions by quarter (Q1-Q4)
- Creates quarterly summaries (800 tokens from 10-50 sessions)
- Moves old sessions to archive/[YYYY]/q[N]/
- Keeps current quarter accessible
- **97% token reduction for historical session context**

## Usage

Point your agent to the specific prompt:

```
Please read docs/_framework/_maintenance/prompt_[name].md and execute it.
```

Or for multiple maintenance tasks:

```
Please read docs/_framework/_maintenance/README.md, then execute:
1. prompt_audit_framework_compliance.md
2. prompt_cleanup_orphaned_docs.md
3. prompt_rebuild_indexes.md
```

## When to Run Maintenance

### Regular (Scheduled)
- `prompt_rebuild_indexes.md` - Monthly (keep indexes fresh)
- `prompt_archive_session_logs.md` - Quarterly (end of Q1/Q2/Q3/Q4)

### As Needed
- `prompt_audit_framework_compliance.md` - After agent misbehavior
- `prompt_cleanup_orphaned_docs.md` - When docs feel cluttered
- `prompt_fix_broken_references.md` - After reorganization
- `prompt_archive_session_logs.md` - When sessions/ has >50 files

### One-Time
- `prompt_migrate_existing_docs.md` - When adopting framework
