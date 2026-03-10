# Feature: [NAME]

---
type: feature
status: planning
tags: []
depends_on: []
required_by: []
---

> **Budget**: 600 tokens
> **Use if**: <500 LOC AND <3 components AND <2 external dependencies
> **Otherwise**: Use template_FEATURE.md

## User Intent

**Goal**: [What user wants to accomplish and why]

**Success Criteria**:
- User can [capability]
- System [behavior]
- [Measurable outcome]

**User Flow**:
1. User [action] → 2. System [response] → 3. Result: [goal achieved]

## Status: [Planning | In Progress | Testing | Complete]
**Last Updated**: [DATE]

## Implementation

[2-3 sentences: how this works technically]

**Key Files**:
- `src/[path]` - [purpose]
- `src/[path]` - [purpose]

**Data Model** (if applicable):
```typescript
interface [Name] {
  // Essential fields only
}
```

## Dependencies

**Requires**:
- [feature_[name].md] - [what it provides]
- [External service] - [purpose]

**Configuration**:
- `ENV_VAR`: [purpose]

## Testing
- [ ] Works as intended
- [ ] Edge cases handled
- [ ] Error states graceful

## Implementation Notes
> Add discoveries during development

- [DATE]: [Note]

## Outstanding
- [ ] [Task if any]
