# Maintenance: Rebuild Index Files

Regenerate searchable _index.md files to accurately reflect current documentation state.

**Run this when**:
- Index files are outdated
- Documents have been added/removed/renamed
- Search is returning stale results

## Index Files to Rebuild

**Search Indexes** (rebuild these):
- `/docs/knowledge/_index.md` - Knowledge base search index
- `/docs/reference/_index.md` - External docs search index

**Working State Files** (DO NOT rebuild):
- `/docs/_status.md` - Current work (manually updated by agent after each commit)
- `/docs/_context.md` - Project context (manually updated at milestones)

**Deprecated**:
- `/docs/_index.md` - No longer used (replaced by _status.md + _context.md)

## Workflow

### 1. Scan knowledge/ folder

For each knowledge doc:
- Read frontmatter tags and Summary section
- Extract type (gotcha, solution, pattern, perf)
- Write concise description

**Format**:
```markdown
- `gotcha_[name].md` - [Problem]: [Solution approach]
- `solution_[name].md` - [What it solves]: [Key benefit]
- `pattern_[name].md` - [Pattern name]: [When to use]
- `perf_[name].md` - [Optimization]: [Measured improvement]
```

### 2. Scan reference/ folder

For each reference doc:
- Identify type (api, lib, spec, guide)
- Extract service/library name
- Write description focusing on key topics

**Format**:
```markdown
- `api_[name].md` - [Service] [topics]: [when to use]
- `lib_[name].md` - [Library] [feature]: [usage context]
- `spec_[name].md` - [Spec name]: [what it defines]
```

### 3. Build knowledge/_index.md

Use template: `/docs/_framework/template_KNOWLEDGE_INDEX.md`

**Include**:
- Grouped by type (Gotchas, Solutions, Patterns, Performance)
- Search-optimized descriptions
- Keywords for grep searches

**Example**:
```markdown
# Knowledge Base Index

**Last Updated**: [DATE]
**Total Entries**: [N]

## Gotchas
- `gotcha_jwt_race_condition.md` - JWT token validation race: Use atomic checks
- `gotcha_react_strict_mode.md` - Double render in dev: Expected behavior

## Solutions
- `solution_optimistic_updates.md` - Instant UI feedback: Optimistic state + rollback
- `solution_debounce_search.md` - Search performance: 300ms debounce + cancel

## Patterns
- `pattern_error_boundary.md` - Graceful error handling: Catch/display/recover
- `pattern_feature_flags.md` - Progressive rollout: Runtime toggles

## Performance
- `perf_react_memo.md` - Prevent re-renders: 40% reduction in render time
- `perf_image_lazy_load.md` - Faster page load: 60% LCP improvement
```

### 4. Build reference/_index.md

Use template: `/docs/_framework/template_REFERENCE_INDEX.md`

**Include**:
- Grouped by type (APIs, Libraries, Specs)
- Service names for search
- Quick reference for which doc covers what

**Example**:
```markdown
# Reference Documentation Index

**Last Updated**: [DATE]

## External APIs
- `api_stripe_webhooks.md` - Stripe webhook handling: event types, verification, retries
- `api_sendgrid_templates.md` - SendGrid email templates: dynamic content, tracking

## Libraries
- `lib_prisma_relations.md` - Prisma ORM: complex relations, nested queries
- `lib_zod_validation.md` - Zod schema validation: type inference, error handling

## Specifications
- `spec_oauth_flow.md` - OAuth 2.0 implementation: PKCE flow, token refresh
```

### 5. Verify Working State Files

**Check (but don't rebuild)**:
- `_status.md` exists and follows template
- `_context.md` exists and follows template
- If missing: Alert user, don't auto-generate

These are manually curated by the working agent and should NOT be rebuilt during index maintenance.

## Token Budget

- `knowledge/_index.md`: Target <400 tokens (search-only, not for reading)
- `reference/_index.md`: Target <400 tokens (search-only, not for reading)

## Completion Checklist

- [ ] knowledge/_index.md scanned and rebuilt
- [ ] reference/_index.md scanned and rebuilt (if reference docs exist)
- [ ] All links verified (no broken references)
- [ ] Token counts within budget
- [ ] _status.md and _context.md verified but NOT rebuilt

## Testing Index Quality

Good index entries enable quick searches:

```bash
# Find JWT-related knowledge
grep -i "jwt" docs/knowledge/_index.md

# Find Stripe API docs
grep -i "stripe" docs/reference/_index.md

# Find performance optimizations
grep "perf_" docs/knowledge/_index.md
```

Each grep should return relevant entries immediately.

## Common Issues

**Issue**: Index has stale entries
**Fix**: Re-scan folders, remove deleted docs

**Issue**: Index is too verbose (>400 tokens)
**Fix**: Shorten descriptions to one line per entry

**Issue**: Can't find docs via grep
**Fix**: Add more keywords to descriptions

**Issue**: _status.md is missing
**Fix**: Alert user - this needs manual creation, not auto-generation
