# Guide: Creating Knowledge Entries

**Use when**: Documenting gotchas, solutions, patterns, or performance optimizations

## When to Create

**Create `knowledge/*.md` when**:
- Same issue occurred 2+ times OR solution non-obvious (→ `gotcha_*.md`)
- Solution is reusable across features (→ `solution_*.md`)
- Pattern used 2+ times (→ `pattern_*.md`)
- Measurable performance gain (→ `perf_*.md`)

**Just note in feature doc when**:
- Feature-specific quirk
- One-time workaround
- Obvious from code

## Creating Knowledge Doc

1. Copy `template_KNOWLEDGE.md` to `knowledge/[type]_[desc].md`
2. Fill with working code examples
3. Specify when to use AND when NOT to use
4. Add tags in frontmatter: `tags: [topic, library, issue-type]`
5. Reference where used in codebase
6. Add to `knowledge/_index.md`

## Knowledge Types

**Gotcha** (`gotcha_*.md`):
- Problem that's not obvious
- Took >30min to debug
- Likely to recur
- Example: `gotcha_jwt_race_condition.md`

**Solution** (`solution_*.md`):
- Reusable fix for common problem
- Applicable across features
- Example: `solution_optimistic_updates.md`

**Pattern** (`pattern_*.md`):
- Reusable design pattern
- Used 2+ times in codebase
- Example: `pattern_error_boundary.md`

**Performance** (`perf_*.md`):
- Optimization with measurable impact
- Before/after metrics
- Example: `perf_react_memo.md`

## Template Sections

**Required**:
- Summary: One-sentence takeaway
- Problem/Pattern: What happens and why
- Solution/Implementation: How to fix/apply
- When to Use: Guidelines for applicability

**Important**:
- Code examples (working, complete)
- Diagnosis steps (for gotchas)
- Impact metrics (for perf)
- Tags for searchability

## After Creating

1. Add to `knowledge/_index.md` with keywords
2. Note in related feature docs
3. Update `_context.md` if significant discovery
4. Verify naming follows conventions

## Naming Pattern

- `gotcha_[description].md`
- `solution_[description].md`
- `pattern_[description].md`
- `perf_[description].md`

Always lowercase, use underscores.

## Search Optimization

Add comprehensive tags for grep searches:
```yaml
tags: [auth, jwt, security, race-condition]
related_features: [feature_auth, feature_api]
```

This enables: `grep "tags:.*jwt" knowledge/*.md`
