# Planning Status

<!--
AGENT: This tracks the planning process itself.
Use this to know: what's fully planned, what's a stub, what needs decisions.
Sub-agents can use this to plan features in parallel.
Update this as planning progresses.
-->

> **Budget**: 800 tokens for structure; grows with features

**Last Updated**: [DATE]

## Planning Overview

| Document | Depth | Placeholders | Ready to Implement | Blocker |
|----------|-------|-------------|-------------------|---------|
| [plan_section_architecture.md] | full | 0 | yes | - |
| [plan_section_data_model.md] | outline | 3 | no | needs schema review |
| [feature_auth.md] | full | 0 | yes | - |
| [feature_payments.md] | stub | 8 | no | payment provider decision |
| [feature_notifications.md] | stub | 12 | no | needs planning |

<!--
DEPTH LEVELS:
- stub: Created from template, mostly placeholders. Not actionable.
- outline: Key sections filled, some placeholders. Approach is clear but details missing.
- full: All sections complete, no placeholders. Ready for implementation.
-->

## Pending Decisions

<!--
Decisions that block planning progress. Orchestrator resolves or escalates to human.
Once resolved, update the decision here and unblock affected docs.
-->

| Decision | Blocks | Options | Status | Resolved |
|----------|--------|---------|--------|----------|
| [Payment provider] | feature_payments, plan_section_integrations | Stripe vs Square | needs_human_input | - |
| [Notification channels] | feature_notifications | Email-only vs multi-channel | ready_to_decide | - |

<!-- STATUS: needs_research | needs_human_input | ready_to_decide | resolved -->

## Planning Assignments

<!--
For parallel planning: which sub-agent is planning which docs.
Orchestrator assigns these. C2 or C3 depending on feature complexity.
-->

| Document | Assigned To | Complexity | Status |
|----------|------------|-----------|--------|
| [feature_auth.md] | - | C3 | complete |
| [feature_payments.md] | - | C3 | blocked (pending decision) |
| [plan_section_api.md] | - | C2 | ready to plan |

## Recently Completed Planning

- [DATE]: [feature_auth.md] → full (was outline)
- [DATE]: [plan_section_architecture.md] → full (was stub)

## Planning Checklist (Per Document)

<!--
Use this to verify a doc is truly "full" depth before marking it ready to implement.
-->

### Feature Docs
- [ ] User Intent filled (Goal, Success Criteria, User Flow)
- [ ] Implementation approach described (not placeholder)
- [ ] Key Files identified (actual paths, not template examples)
- [ ] Dependencies listed with specific feature/plan refs
- [ ] Definition of Done has concrete, runnable checks
- [ ] Complexity assigned (C1/C2/C3)
- [ ] No `[PLACEHOLDER]` or `[NAME]` markers remain

### Plan Section Docs
- [ ] Key Decisions filled with rationale
- [ ] Design section has specifics, not generics
- [ ] Impact on Features lists actual feature docs
- [ ] Risks identified with mitigation
- [ ] No `[PLACEHOLDER]` or `[NAME]` markers remain
