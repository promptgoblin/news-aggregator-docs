# Guide: Creating Features

**Use when**: Creating feature documentation

## Template Decision Tree

**Feature type?**
- Simple (<500 LOC AND <3 components AND <2 dependencies) → `template_FEATURE_SIMPLE.md` ([example](../_examples/example_feature_simple.md))
- Complex (>500 LOC OR >3 components OR >2 dependencies) → `template_FEATURE.md` ([example](../_examples/example_feature_full.md))

## Granularity Guidelines

**One feature per user-facing capability**

✅ Good: `feature_user_authentication.md` (register + login + logout)
❌ Too granular: `feature_login.md` + `feature_register.md` + `feature_logout.md`
❌ Too broad: `feature_user_management.md` (auth + profile + settings + admin)

**When to split**: >1,200 tokens AND (distinct workflows OR independent implementation)
**Pattern**: `feature_[parent]_[sub].md`

## Creating Standard Feature

1. Copy `template_FEATURE.md` to `features/feature_[name].md`
2. **Fill User Intent section FIRST**
   - What user wants to accomplish
   - Why it matters
   - Success criteria from user perspective
3. Fill Implementation details
4. Add to `PLAN.md` features list
5. Update `_status.md`

## Creating Simple Feature

For straightforward features (<500 LOC AND <3 components AND <2 dependencies):

1. Copy `template_FEATURE_SIMPLE.md` to `features/feature_[name].md`
2. Fill User Intent and basic implementation
3. Add to `PLAN.md`
4. Update `_status.md`

## Creating Sub-Features

When parent feature >1,000 tokens OR has distinct workflows:

1. Create `feature_[parent]_[sub].md`
2. Reference parent in "References" section
3. Parent lists sub-features in "Dependencies > Requires This Feature"

**Example**:
- Parent: `feature_payment.md`
- Subs: `feature_payment_subscriptions.md`, `feature_payment_refunds.md`

## When to Split Features

**Split if**:
- >1,200 tokens AND can be implemented in separate commits without merge conflicts
- Multiple distinct user workflows
- Can be implemented independently

**Keep together if**:
- Tightly coupled logic
- Single cohesive user workflow
- Splitting requires content duplication

Add if keeping together: `<!-- TOKEN BUDGET EXCEEDED: [reason] -->`

## After Creating

1. Update `PLAN.md` features list
2. Update `_status.md` current work
3. Add cross-references from related docs
4. Check token budget (see `TOKEN_BUDGETS.md`)

## Naming Pattern

- Features: `feature_[name].md`
- Sub-features: `feature_[parent]_[sub].md`

Always lowercase, use underscores.

## Cross-Referencing

**Quick rules**:
- Use relative links: `[feature_auth.md]`
- Link when dependency/context needed
- Bi-directional: if A needs B, both link to each other
- Never duplicate content - link instead

See [guide_cross_referencing.md] for complete patterns.
