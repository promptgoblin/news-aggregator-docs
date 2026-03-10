# Guide: Cross-Referencing

**Use when**: Creating links between documents or unsure about linking patterns

## Linking Syntax

**Always use relative links**:
```markdown
✅ [feature_auth.md]
✅ [plan_section_architecture.md](../plan/plan_section_architecture.md)
❌ /docs/features/feature_auth.md
❌ https://github.com/.../feature_auth.md
```

## Link Patterns by Document Type

| From → To | Pattern | Example |
|-----------|---------|---------|
| Feature → Feature | `[feature_name.md]` | `[feature_auth.md]` |
| Feature → Plan | `[plan_section_name.md](../plan/...)` | `[plan_section_auth.md](../plan/plan_section_auth.md)` |
| Plan → Feature | `[feature_name.md](../features/...)` | `[feature_auth.md](../features/feature_auth.md)` |
| Any → Knowledge | `[type_desc.md](../knowledge/...)` | `[gotcha_jwt_expiry.md](../knowledge/gotcha_jwt_expiry.md)` |
| Any → Reference | `[api_service.md](../reference/...)` | `[api_stripe_webhooks.md](../reference/api_stripe_webhooks.md)` |

## When to Link vs. Mention

**Link when**:
- Direct dependency (required reading)
- Provides context/rationale (explains "why")
- Reader should jump there
- <3 hops away

**Don't link when**:
- Tangential mention
- External URL is better
- Too far away (>3 hops)

**Examples**:
```markdown
✅ "Requires [feature_auth.md] for user context"
❌ "Uses authentication like other features"
✅ "See [plan_section_auth.md] for JWT rationale"
❌ "Considered in planning"
```

## Bi-Directional Linking

When A depends on B, link in both directions:

**feature_payment.md**:
```markdown
**Requires**: [feature_auth.md] - Authenticated user context
```

**feature_auth.md**:
```markdown
**Required By**: [feature_payment.md], [feature_profile.md]
```

## Link Text Best Practices

Add context explaining why to follow link:

```markdown
✅ "See [plan_section_auth.md] for JWT implementation rationale"
✅ "Auth flow in [feature_auth.md]"
❌ "See [plan_section_auth.md]" (no context)
❌ "Click here" (never)
```

## Never Duplicate

**Always link** instead of copying:

```markdown
❌ Bad:
## Authentication
We use JWT tokens with bcrypt hashing...
[300 words copied from feature_auth.md]

✅ Good:
## Authentication
JWT-based. See [feature_auth.md] for details.
```

If copying >2 sentences, create a link instead.

## Quick Reference

See examples in:
- [_examples/example_feature_full.md] - Shows proper dependency linking
- [_examples/example_plan_section.md] - Shows bi-directional references
