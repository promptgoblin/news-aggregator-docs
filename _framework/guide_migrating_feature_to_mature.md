# Guide: Migrating Feature to Mature Template

**Use this when**: Feature is complete, stable, and in production for 2+ months

## Why Migrate?

**Token savings**: 1,000 → 400 tokens (~60% reduction)

**Benefits**:
- Faster agent context loading for stable features
- Removes planning artifacts no longer needed
- Keeps essential implementation reference
- Maintains links and dependencies

**When to migrate**:
- ✅ Feature complete & in production >3 months
- ✅ No changes in 2+ months (stable)
- ✅ No planned sub-features or major changes
- ❌ Don't migrate if still evolving

## Migration Steps

### 1. Read Current Feature Doc

Read the existing `features/feature_[name].md` to extract:
- Summary of what feature does
- User value
- Key implementation details
- Dependencies and references
- Configuration (env vars, feature flags)
- Known limitations

### 2. Create Mature Version

Copy `docs/_framework/template_FEATURE_MATURE.md` over the existing feature doc:

```bash
cp docs/_framework/template_FEATURE_MATURE.md docs/features/feature_[name].md
```

Or better: Read template, fill it out with extracted info from step 1.

### 3. Fill Template Sections

**Summary** (compress User Intent):
- One-sentence "What" description
- User value (from User Intent > Goal)
- Status: "✅ Complete and stable since [date]"
- Key capabilities (from Success Criteria)

**Implementation** (compress from old Implementation section):
- High-level architecture approach
- Key files (3-5 most important)
- Entry points (API/UI/Background)
- Data model (core entities only)
- External integrations (if any)

**Configuration** (if applicable):
- Environment variables
- Feature flags
- Deployment notes

**Known Limitations** (if applicable):
- List limitations with workarounds
- Context on why limitation exists

**Maintenance**:
- What to monitor
- Reference common gotchas
- Update frequency

**References**:
- Migrate all links from old References section
- Ensure depends_on and required_by are correct

### 4. Add Migration Note

In the "Migration Notes" section at bottom:
```markdown
**Migrated from**: template_FEATURE.md on 2025-10-07
**Token savings**: 1,050 tokens → 385 tokens (63% reduction)
```

### 5. Validate

Check that mature doc has:
- [ ] All critical implementation details preserved
- [ ] Dependencies and references intact
- [ ] Configuration documented
- [ ] Known limitations noted
- [ ] Links to related knowledge entries
- [ ] Token count <400 (or <500 if complex)

### 6. Update PLAN.md

If feature is listed in `PLAN.md`, optionally update status:
```markdown
- ✅ **[Feature name]** - Complete and stable ([feature_name.md])
```

### 7. Git Commit

The old version is preserved in git history if ever needed.

```bash
git add docs/features/feature_[name].md
git commit -m "Migrate feature_[name] to mature template

Feature is stable and in production. Reduced from 1,050 → 385 tokens (63%).
Planning artifacts (User Intent, Testing) preserved in git history.
"
```

## What Gets Removed

**User Intent section**:
- Goal → Condensed to Summary
- Success Criteria → Condensed to Key Capabilities
- User Flows → Removed (in code/tests)
- Non-Goals → Removed (historical context)

**Status section**:
- Current Status → Simplified to "Complete"
- Progress → Removed (feature is done)
- Blockers → Removed (none, it's complete)
- Last Updated → Moved to frontmatter

**Implementation section**:
- Approach → Condensed to Architecture one-liner
- Key Files → Top 3-5 files only
- Implementation Notes → Removed (in code comments)
- Decisions → Key ones kept, others in git history

**Testing section**:
- Removed entirely (tests exist in codebase)

**Dependencies section**:
- Merged into References

## What Gets Kept

✅ Summary of what feature does (from User Intent)
✅ User value (why it exists)
✅ Key implementation details (how it works)
✅ Entry points (where to start reading code)
✅ Configuration (env vars, flags)
✅ Known limitations (important for agents)
✅ Maintenance info (monitoring, common issues)
✅ All cross-references and dependencies

## Example Migration

### Before (template_FEATURE.md - 1,050 tokens)

```markdown
# Feature: User Authentication

## User Intent

**Goal**: Users can securely log in, log out, and maintain session state

**Success Criteria**:
- Users can register with email/password
- Users can log in and receive JWT
- Sessions expire after 24 hours
- Failed login attempts are rate-limited

[... 15 more lines of User Intent ...]

## Status

**Current Status**: ✅ Complete
**Progress**: Shipped in v2.1 on 2024-06-15
**Blockers**: None
**Last Updated**: 2024-10-05

## Implementation

**Approach**: JWT-based authentication with refresh tokens

**Key Files**:
- `src/auth/login.ts` - Login handler
- `src/auth/register.ts` - Registration handler
- `src/auth/middleware.ts` - Auth middleware
- `src/auth/tokens.ts` - JWT utilities
[... continues for 30+ lines ...]

## Testing
[... 20 lines of testing details ...]
```

### After (template_FEATURE_MATURE.md - 385 tokens)

```markdown
# Feature: User Authentication

---
type: feature
status: complete
last_updated: 2025-10-07
---

## Summary

**What**: Secure user authentication with email/password and JWT sessions

**User value**: Users can securely access their accounts with session management

**Status**: ✅ Complete and stable since v2.1 (2024-06-15)

**Key capabilities**:
- Email/password registration and login
- JWT-based sessions (24h expiry)
- Refresh token rotation
- Rate-limited login attempts

## Implementation

**Architecture**: JWT auth + bcrypt passwords + PostgreSQL user store

**Key files**:
- `src/auth/login.ts` - Login handler
- `src/auth/middleware.ts` - Auth middleware
- `src/auth/tokens.ts` - JWT utilities

**Entry points**:
- API: `POST /api/auth/login`, `POST /api/auth/register`
- Middleware: `requireAuth()` middleware

**Data model**: `users` table (id, email, password_hash, created_at)

**External integrations**: None

## Configuration

**Environment variables**:
- `JWT_SECRET`: Token signing key - Required
- `JWT_EXPIRY`: Session duration - Optional (default: 24h)

## Maintenance

**Monitoring**: Track failed login rate, token refresh failures

**Common issues**: → See [knowledge/gotcha_jwt_race_condition.md]

**Update frequency**: Rare (1-2x/year for security patches)

## References

**Dependencies**: None

**Required by**:
- [features/feature_dashboard.md]
- [features/feature_api.md]

**Code**: `src/auth/`
```

**Token reduction**: 1,050 → 385 tokens (63% reduction)

## Success Criteria

- [x] Feature doc migrated to mature template
- [x] Token count <400 (or <500 if complex)
- [x] All critical info preserved
- [x] Dependencies intact
- [x] Committed to git (old version in history)
- [x] PLAN.md updated if needed

## Notes

- Don't rush migration - wait until feature truly stable
- Keep mature template focused - resist adding back removed sections
- If feature needs changes later, it's fine - edit mature template in place
- Git history preserves full planning details if ever needed
- Migrating 10 features: 10,000 → 4,000 tokens saved
