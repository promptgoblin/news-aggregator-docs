# Feature: [NAME]

---
type: feature
status: complete
tags: []
depends_on: []
required_by: []
last_updated: [YYYY-MM-DD]
---

> **Budget**: 400 tokens. Compressed template for complete, stable features
> **Use when**: Feature is complete, tested, stable, and in production
> **Migration**: Convert from template_FEATURE.md after feature launches
> **Purpose**: Reduce token overhead by removing planning artifacts

<!-- VALIDATED: [DATE] | [N]/400 ✅ -->

## Summary

**What**: [One-sentence description of what the feature does]

**User value**: [Primary benefit to users]

**Status**: ✅ Complete and stable since [date or version]

**Key capabilities**:
- [Core capability 1]
- [Core capability 2]
- [Core capability 3]

## Implementation

> Condensed reference - agents read this to understand how it works

**Architecture**: [High-level approach - e.g., "REST API + React UI + PostgreSQL storage"]

**Key files**:
- `src/[path]` - [What it does]
- `src/[path]` - [What it does]
- `src/[path]` - [What it does]

**Entry points**:
- API: `[endpoint or function]`
- UI: `[component or page]`
- Background: `[job or service]`

**Data model**: [Core entities/tables]

**External integrations**: [Third-party services used, if any]

## Configuration

> Only include if feature has config/env vars

**Environment variables**:
- `[VAR_NAME]`: [Purpose] - [Required/Optional]

**Feature flags**: [If any]

**Deployment notes**: [If any special considerations]

## Known Limitations

> Only include if limitations exist

- [Limitation 1]: [Workaround or future plan]
- [Limitation 2]: [Context on why limitation exists]

## Maintenance

**Monitoring**: [What to watch - errors, metrics, dashboards]

**Common issues**: → See [knowledge/gotcha_*.md] entries

**Update frequency**: [How often this feature typically needs changes]

## References

**Dependencies**:
- [feature_*.md] - [Why needed]

**Required by**:
- [feature_*.md] - [How this is used]

**Documentation**:
- [reference/api_*.md] - [External API docs]
- [knowledge/pattern_*.md] - [Relevant patterns]

**Code**: [Link to main implementation file or directory]

## Migration Notes

> Delete this section after migration

**Migrated from**: [template_FEATURE.md] on [DATE]

**Removed sections** (archived in git history if needed):
- User Intent (captured in "Summary" above)
- Status tracking (now just "Complete")
- Testing details (in git history + test files)
- Implementation decisions (key ones in "Implementation")

**Token savings**: [Before: X tokens] → [After: ~400 tokens] (~X% reduction)
