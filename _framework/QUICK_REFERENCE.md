# Quick Reference

**AGENT**: Use conditional lookup only. Don't read entire file.

## I need to...

**Create a feature** → [Create New Feature](#create-new-feature)
**Update docs after commit** → [Update After Commit](#update-after-commit)
**Document a gotcha** → [Found a Gotcha](#found-a-gotcha)
**Name a file** → [File Naming](#file-naming)
**Know token budgets** → [Token Budgets](#token-budgets)
**Decide if I should create something** → [Decision Trees](#decision-trees)
**Find something** → [Common Searches](#common-searches)
**Core rules reminder** → [Core Principles](#core-principles)

---

## Create New Feature
1. Copy `template_FEATURE.md` → `features/feature_[name].md`
2. Fill User Intent FIRST
3. Add to `PLAN.md` features list
4. Update `_status.md`

**Simple feature?** Use `template_FEATURE_SIMPLE.md`
**Mature feature?** Migrate to `template_FEATURE_MATURE.md` after launch (saves ~60% tokens)

---

## Update After Commit
1. Update `_status.md`: Working On, Status, Next Steps
2. Update feature doc Implementation Notes
3. Create knowledge entry if >30min debug
4. Update `_context.md` at milestones
5. Commit doc changes with code

---

## Found a Gotcha
1. Create `knowledge/gotcha_[desc].md`
2. Add to `knowledge/_index.md`
3. Note in feature Implementation Notes
4. Update `_context.md` Recent Changes

---

## File Naming

**Pattern**: `[type]_[name].md` (lowercase, underscores)

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature_[name]` | `feature_user_auth.md` |
| Sub-feature | `feature_[parent]_[sub]` | `feature_payment_subscriptions.md` |
| Plan section | `plan_section_[topic]` | `plan_section_architecture.md` |
| Gotcha | `gotcha_[desc]` | `gotcha_jwt_race_condition.md` |
| Solution | `solution_[desc]` | `solution_optimistic_updates.md` |
| Pattern | `pattern_[desc]` | `pattern_error_boundary.md` |
| Performance | `perf_[desc]` | `perf_react_memo.md` |
| API ref | `api_[service]_[topic]` | `api_stripe_webhooks.md` |
| Library | `lib_[library]_[topic]` | `lib_prisma_relations.md` |
| Session | `session_[YYYY_MM_DD]_[topic]` | `session_2024_10_05_auth.md` |
| Checklist | `checklist_[phase]` | `checklist_deployment.md` |
| Audit | `audit_[type]_[date]` | `audit_security_2024_10.md` |

**See**: `NAMING_CONVENTIONS.md` for complete rules

---

## Token Budgets

| Doc Type | Budget | Split If... |
|----------|--------|-------------|
| `_status.md` | 200 | Never |
| `_context.md` | 300 | Never |
| `PLAN.md` | 800 | Move to plan sections |
| `plan_section_*.md` | 1,200 | >1,500 |
| `feature_*.md` | 1,000 | >1,200 & divisible |
| `feature_*.md` (mature) | 400 | Migrate when complete |
| `knowledge/*.md` | 600 | Focused only |
| `session_*.md` | 600 | Summarize better |

**Exceed with reason**: `<!-- TOKEN BUDGET EXCEEDED: [reason] -->`

---

## Decision Trees

### Should I create a knowledge entry?
```
Same issue 2+ times OR solution non-obvious? → Yes: gotcha_*.md | No: note in feature doc
Solution reusable across features? → Yes: solution_*.md | No: note in feature doc
Pattern used 2+ times? → Yes: pattern_*.md | No: wait for 2nd use
```

### Should I create a reference doc?
```
API in 2+ features? → Yes: api_*.md | No: inline link
>5 endpoints OR complex auth? → Yes: api_*.md | No: inline link
>3 env vars required? → Yes: api_*.md or lib_*.md | No: inline link
```

### Should I migrate feature to mature template?
```
Feature complete & in production >3 months? → Yes: template_FEATURE_MATURE.md
Feature stable (no changes in 2+ months)? → Yes: template_FEATURE_MATURE.md
Feature still evolving? → No: keep template_FEATURE.md
Planning new sub-features? → No: keep template_FEATURE.md

Migration saves: 1,000 tokens → 400 tokens (~60% reduction)
```

### Should I split this feature?
```
>1,200 tokens?
  No → Keep as-is
  Yes → Can implement in separate commits without merge conflicts?
        → Yes: split to sub-features
        → No: Keep together + budget comment
```

---

## Common Searches

```bash
# Find feature
ls features/feature_[topic]*.md

# Find knowledge about topic
grep -r "topic" docs/knowledge/

# Recent sessions
ls -t sessions/ | head -5

# Token counts
cat docs/_framework/token_counts.md
```

---

## Template Locations

All in `docs/_framework/`:
- `template_FEATURE.md` - Complex feature
- `template_FEATURE_SIMPLE.md` - Simple feature
- `template_PLAN.md` - Master plan
- `template_PLAN_SECTION.md` - Plan detail
- `template_KNOWLEDGE.md` - Gotcha/solution/pattern
- `template_SESSION_LOG.md` - Work session
- `template_AUDIT.md` - Assessment
- `template_CHECKLIST.md` - Task list

---

## Core Principles

1. **User Intent is sacred** - Implement what user wants
2. **Link, never duplicate** - Cross-reference instead of copy
3. **Update _status.md after each commit** - Keep current work visible
4. **Update _context.md at milestones** - Preserve project history
5. **Token budget awareness** - Load <2,000 tokens for most tasks
6. **Follow naming conventions** - Consistency enables findability

---

## Status Indicators

**Feature**: ✅ Complete | 🔄 In Progress | 📋 Planned | 💡 Proposed | ⚠️ Blocked
**Session**: Planning | In Progress | Testing | Blocked

---

## Cross-Referencing

✅ DO: Relative links `[feature_auth.md]`, bi-directional, link not duplicate
❌ DON'T: Absolute paths, duplicate content, break links
