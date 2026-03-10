# Plan: [PROJECT_NAME]

> **Budget**: 1.2k tokens. Move details to plan_section_*.md if exceeding
> **Workflow**: 1) Vision & Quick Decisions → 2) Create plan sections → 3) List features with complexity → 4) Set up _queue.md → 5) Update as single source of truth

## Vision
[2-3 sentences: what we're building, why, what problem it solves]

**Status**: [Planning | Building | Reviewing | Launching]
**Current Focus**: [What's being worked on]
**Last Updated**: [DATE]

## Quick Decisions
> Key decisions affecting multiple features

- **Framework**: [Choice] - [Rationale]
- **Database**: [Choice] - [Rationale]
- **Authentication**: [Choice] - [Rationale]
- **Deployment**: [Choice] - [Rationale]

## Plan Sections
> **AGENT**: Read these for detailed design/architecture

- [plan_section_architecture.md]: System design, stack, infrastructure
- [plan_section_data_model.md]: Schema, relationships, data flow
- [plan_section_[NAME].md]: [Coverage]

## Features
> **AGENT**: Check _queue.md for implementation status and task assignments

### Core
- [feature_[NAME].md]: [Description] - **C[1/2/3]** - **[Status]**
- [feature_[NAME].md]: [Description] - **C[1/2/3]** - **[Status]**

### Secondary
- [Not Started] [Name]: [Description] - **C[1/2/3]**

### Future
- [Idea]: [Why we might want this]

### Dependencies & Parallel Groups
> Text-based dependency flow. Detailed task assignments in _queue.md

```
Parallel Group A (can build simultaneously):
  feature_auth, feature_database_setup, feature_api_scaffold

Parallel Group B (requires Group A):
  feature_user_profile → feature_settings
  feature_payments

feature_auth → feature_user_profile → feature_settings
             ↘ feature_payments ↗
```

## Audits & Reviews
- [audit_[TYPE]_[DATE].md]: [Findings/status]
- [Planned] [Type] Audit: [Target date]

## Checklists
- [checklist_deployment.md]: Deployment procedure
- [checklist_[NAME].md]: [Purpose]

## Phases
> Detailed task breakdown, assignments, and gates are in _queue.md

### Phase 1: Foundation [Status]
- [ ] [Milestone]
- [ ] [Milestone]
- **Gate**: Human reviews holistic experience before Phase 2

### Phase 2: Core Features [Status]
- [ ] [Milestone]
- [ ] [Milestone]
- **Gate**: Human reviews before Phase 3

### Phase 3: Polish & Launch [Status]
- [ ] [Milestone]
- [ ] [Milestone]

## Success Metrics
- [Metric]: [Target]
- [Metric]: [Target]

## External Resources
- [Design Mockups]: [Link]
- [API Docs]: [reference/api_[NAME].md]
- [Requirements]: [Link]
