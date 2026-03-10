# Feature: [NAME]

---
type: feature
status: planning
complexity: C2
tags: []
depends_on: []
required_by: []
---

> **Budget**: 2k tokens. Split if >2.5k & can be implemented in separate commits without merge conflicts
> **Use if**: >500 LOC OR >3 components OR >2 external dependencies
> **Otherwise**: Use template_FEATURE_SIMPLE.md
> **AGENT**: User Intent is CRITICAL - implement to match intent, not just requirements
> **Complexity**: C1 (routine) | C2 (moderate) | C3 (complex) - see guide_complexity_levels.md

## User Intent

### Goal
[What user wants to accomplish and why it matters]

### Success Criteria
- User can [capability]
- System [behavior]
- Experience feels [quality - fast, intuitive, secure]
- [Measurable criterion]

### User Flow
1. User [action]
2. System [response]
3. User [sees/experiences]
4. Result: [Goal achieved]

## Status: [Planning | In Progress | Testing | Complete]
**Started**: [DATE]
**Last Updated**: [DATE]

## References
> **AGENT**: Read these for context

- Plan: [plan/PLAN.md#features]
- Design: [plan/plan_section_[NAME].md]
- Related: [feature_[NAME].md]
- API: [reference/api_[NAME].md]

## Implementation

### Approach
[2-3 sentences on how this works technically]

### Key Components
- **[Component]**: [Purpose]
- **[Component]**: [Purpose]

### Key Files
- `src/features/[name]/index.ts` - Main logic
- `src/api/[name].ts` - API endpoints
- `src/components/[Name].tsx` - UI components
- `tests/[name].test.ts` - Tests

### Data Model
```typescript
// Key interfaces/schema
interface [Name] {
  // Essential fields
}
```

## Dependencies

### Setup Required
- [setup/setup_[NAME].md]: [What it provides]

### Features Required
- [feature_[NAME].md]: [Functionality needed]

### Requires This Feature
- [feature_[NAME].md]: [How they use it]

### External Services
- [Service]: [Purpose] - See [reference/api_[NAME].md]

## Configuration
- `ENV_VAR_NAME`: [Purpose] - See [setup/setup_[NAME].md]

## Edge Cases & Considerations

### Handled
- [Scenario]: [How we handle it]

### Limitations
- [Limitation]: [Why and potential solution]

### Performance
- [Consideration]: [Impact and mitigation]

### Security
- [Aspect]: [How handled]
- [Auth/Authz]: [Approach]

## Definition of Done

<!--
AGENT: You cannot mark this feature complete until ALL checks pass.
Automated checks must be runnable commands. Acceptance criteria must be verifiable.
-->

### Automated Checks
<!-- Commands that an agent can run to verify completion -->
- [ ] `[test command]` passes
- [ ] `[lint/type-check command]` passes
- [ ] `[specific verification command]` returns expected result

### Acceptance Criteria
<!-- Verifiable conditions - not aspirational, not vague -->
- [ ] [Specific user-facing behavior exists]
- [ ] [Specific system behavior is observable]
- [ ] [Error case is handled: describe how]
- [ ] [Performance target: specific metric]

### Docs (Standard - applies to all tasks)
- [ ] Implementation Notes updated with discoveries/deviations
- [ ] `_queue.md` task status updated
- [ ] Knowledge entry created if debugging took >30 min
- [ ] No `[PLACEHOLDER]` markers remain in this doc

## Implementation Notes
> Discoveries and decisions during development. Update as you work, not after.

- [DATE]: [Discovery/decision and reasoning]
- [DATE]: [Change from plan and why]

## Outstanding
- [ ] [Task]
- [ ] [Task]
- [ ] [Bug]: [Description]
