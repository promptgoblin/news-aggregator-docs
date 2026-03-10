# Token Budgets

**Last Updated**: 2026-02-05
**Based on**: Actual tiktoken analysis (cl100k_base encoding)
**Version**: 3.0 - Updated for modern context windows (200k+) and sub-agent workflows

## Purpose
Keep documentation focused and context-efficient. These are **strong guidelines**, not hard limits. The goal is preventing bloat, not artificial constraint.

## Budget by Document Type

| Document Type | Token Budget | Split Guideline |
|---------------|--------------|-----------------|
| `_status.md` | 300 | Never split - current work + active phase |
| `_context.md` | 400 | Never split - recent history only |
| `_queue.md` | 1,500+ | Working doc - grows with tasks, that's fine |
| `_planning_status.md` | 800 | Working doc - grows with features |
| `PLAN.md` | 1,200 | Move details to plan_section_*.md |
| `plan_section_*.md` | 2,500 | If >3,000, topic too broad - split |
| `feature_*.md` | 2,000 | If >2,500, create sub-features if logical |
| `feature_*.md` (mature) | 600 | Migrate when complete & stable |
| `feature_*_sub.md` | 1,200 | Sub-features should be focused |
| `knowledge/*.md` | 800 | Focused = valuable |
| `knowledge/_index.md` | 600 | Search index - agents grep, not read |
| `session_*.md` | 800 | Summarize, link to commits for detail |
| `q[N]_[YYYY]_summary.md` | 1,000 | Quarterly summary, archive old sessions |
| `audit_*.md` | 1,200 | Link to full reports if >1,200 |
| `checklist_*.md` | 1,000 | Link to detailed runbooks if >1,000 |
| `reference/*.md` | 1,200 | If >1,200, split by topic/endpoint |

### v3 Changes from v2
- Feature docs: 1,000 → 2,000 (accommodates DoD section, reduces forced splits)
- Plan sections: 1,200 → 2,500 (more room for decision rationale)
- Knowledge: 600 → 800 (more room for code examples)
- All other types: ~50% increase to reduce artificial constraints
- New types: `_queue.md`, `_planning_status.md` (working docs, budget is soft)

### Why Relax Budgets?
- Context windows are 200k+ (up from 100k when v2 was written)
- Sub-agents each get their own context window
- Models handle larger docs without quality degradation
- Forced splitting often creates more work (reading 3 files vs 1 richer file)
- The discipline is still "keep docs focused" - just with more room

## When to Exceed Budget

**Use discretion**. Exceed budget when:
- Feature is cohesive and splitting would hurt clarity
- Content cannot be extracted to sub-docs without duplication
- Information is critical and frequently accessed together

**When exceeding, add comment:**
```markdown
<!-- TOKEN BUDGET EXCEEDED: [reason] -->
```

## Splitting Guidelines

### When to Split Features
- **DO split** if >2,500 tokens AND:
  - Multiple distinct user workflows
  - Can be implemented independently
  - Has clear logical boundaries

- **DON'T split** if:
  - Tightly coupled logic that can't be separated
  - Single cohesive user workflow
  - Would require content duplication

### When to Split Plan Sections
- If >3,000 tokens, topic is too broad
- Example: `plan_section_api.md` (3,500 tokens)
  - Split to: `plan_section_api_rest.md` + `plan_section_api_graphql.md`

### When to Create Sub-Features
Pattern: `feature_[parent]_[sub].md`

Example:
- `feature_payment.md` (3,000 tokens) → Split to:
  - `feature_payment.md` (1,200 tokens - overview + orchestration)
  - `feature_payment_subscriptions.md` (1,000 tokens)
  - `feature_payment_invoicing.md` (1,000 tokens)
  - `feature_payment_refunds.md` (800 tokens)

## Template Sizes (Current)

Based on tiktoken analysis (needs re-run after v3 updates):

| Template | Current Tokens | Status |
|----------|----------------|--------|
| `template_FEATURE.md` | ~800 | ✅ Within budget (2,000) |
| `template_FEATURE_SIMPLE.md` | ~282 | ✅ Within budget (1,200) |
| `template_QUEUE.md` | ~1,200 | ✅ Working doc |
| `template_PLANNING_STATUS.md` | ~600 | ✅ Within budget (800) |
| `template_SESSION_LOG.md` | ~387 | ✅ Within budget (800) |
| `template_PLAN.md` | ~592 | ✅ Within budget (1,200) |
| `template_PLAN_SECTION.md` | ~492 | ✅ Within budget (2,500) |
| `template_KNOWLEDGE.md` | ~489 | ✅ Within budget (800) |
| `template_AUDIT.md` | ~624 | ✅ Within budget (1,200) |
| `template_CHECKLIST.md` | ~589 | ✅ Within budget (1,000) |

## Current Framework Stats

**Orchestrator startup cost** (minimum load):
- `CLAUDE.md`: ~500 tokens (auto-loaded)
- `_status.md`: ~300 tokens
- `_queue.md`: ~1,200 tokens (varies with project size)
- **Total**: ~2,000 tokens to start orchestrating

**Sub-agent startup cost** (per task):
- Feature doc: ~800-2,000 tokens
- Referenced plan section (if needed): ~500-2,500 tokens
- **Total**: ~800-4,500 tokens depending on task complexity

**Full context load** (complex feature):
- Orchestrator startup + feature doc + plan section + knowledge refs
- **Total**: ~4,000-8,000 tokens (well within 200k context)

## Monitoring

Run token count script periodically:
```bash
docs/_framework/utilities/venv/bin/python docs/_framework/utilities/count_tokens.py
```

Review `docs/_framework/token_counts.md` for changes.

## Archival Strategy (Session Logs)

**Problem**: Session logs accumulate unbounded over time
**Solution**: Quarterly archival with compressed summaries

**Process**:
- End of each quarter: Create `q[N]_[YYYY]_summary.md` (1,000 tokens)
- Archive individual sessions to `sessions/archive/[YYYY]/q[N]/`
- Keep current quarter + all quarterly summaries in root

**Token savings**:
- 50 sessions x 800 tokens = 40,000 tokens
- 1 quarterly summary = 1,000 tokens
- **Reduction**: 97% (40,000 → 1,000 tokens)

See: `docs/_framework/_maintenance/prompt_archive_session_logs.md`

## Success Criteria

- Agent loads <3,000 tokens to start orchestrating
- Sub-agent loads <5,000 tokens for typical task
- Sub-agent loads <8,000 tokens for complex multi-dependency task
- No single doc >3,000 tokens (except working docs like `_queue.md`)
- `_status.md` stays <300 tokens
- `_planning_status.md` usable as planning dashboard
- `knowledge/_index.md` used for search only
- Session logs archived quarterly to prevent unbounded growth
