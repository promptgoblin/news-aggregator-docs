# Framework Quick Start

**Read this first, then only the guide you need.**

## What are you doing?

**Orchestrating work across sub-agents?**
-> Read `guide_orchestration.md` then `_queue.md`

**Starting a new project?**
-> Read `guide_initial_planning.md`

**Implementing a feature (as a sub-agent)?**
-> Read your assigned feature doc, follow its Definition of Done

**Implementing a feature (solo, no orchestrator)?**
-> Read `guide_navigation.md` then `guide_creating_feature.md`

**Planning features for implementation?**
-> Read `_planning_status.md` then feature docs that need planning

**Mid-work updates?**
-> Read `guide_docs_compliance.md`

**Finding something?**
-> Read `guide_navigation.md`

**Assigning complexity to tasks?**
-> Read `guide_complexity_levels.md`

**Need linking patterns?**
-> Read `guide_cross_referencing.md`

**Framework broken/messy?**
-> Read `_maintenance/README.md`

## Core Rules (Never Violate)

1. **Read `_status.md` first** - Shows current state
2. **Read `_queue.md` for work dispatch** - Shows what to build and in what order
3. **User Intent drives implementation** - Not just technical specs
4. **Docs update = part of the task** - Not a separate step (see `guide_docs_compliance.md`)
5. **Link, never duplicate** - Cross-reference instead of copying
6. **Follow naming**: `[type]_[name].md` (lowercase, underscores)
7. **Respect token budgets** - See `TOKEN_BUDGETS.md` for limits
8. **Respect complexity levels** - C1/C2/C3 determines sub-agent model (see `guide_complexity_levels.md`)

## Document Types Quick Ref

| You need to... | Create this |
|----------------|-------------|
| Set up work queue | `_queue.md` (from `template_QUEUE.md`) |
| Track planning status | `_planning_status.md` (from `template_PLANNING_STATUS.md`) |
| Plan architecture | `plan/plan_section_[topic].md` |
| Add user feature | `features/feature_[name].md` |
| Document gotcha | `knowledge/gotcha_[desc].md` |
| Save reusable pattern | `knowledge/pattern_[desc].md` |
| Record solution | `knowledge/solution_[desc].md` |
| Document external API | `reference/api_[service]_[topic].md` |
| Create task list | `checklists/checklist_[phase].md` |
| Log work session | `sessions/session_[YYYY_MM_DD]_[topic].md` |

## Workflow

### Orchestrator (top-level agent)
```
1. Read _status.md (current state)
2. Read _queue.md (work dispatch)
3. Read _planning_status.md (are docs ready?)
4. Break features into tasks if needed
5. Assign complexity (C1/C2/C3) to each task
6. Dispatch sub-agents by complexity
7. Monitor progress, handle blockers
8. Run gate validation when phase completes
9. Report to human at gates
```

### Sub-Agent (dispatched for a task)
```
1. Read assigned feature doc
2. Read referenced plan sections if needed
3. Implement the task
4. Verify Definition of Done
5. Update docs (Implementation Notes, _queue.md status)
6. Report completion to orchestrator
```

### Solo Agent (no sub-agents)
```
1. Read _status.md (current state)
2. Read _queue.md (pick next ready task)
3. Read feature doc for that task
4. Implement, verify DoD, update docs
5. Move to next task
6. Stop at gates for human review
```

## Token Budget Awareness

**Target**: <3,000 tokens to start orchestrating, <5,000 per sub-agent task

See `TOKEN_BUDGETS.md` for full budget table and rationale.

---

**Next**: Choose the guide for your current role/task above, then get to work.
