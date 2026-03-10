# Project Agent Instructions

<!-- This file is auto-loaded by Claude Code. Keep it current with your project. -->

## Startup Sequence

1. Read `docs/_status.md` - current state and active phase
2. Read `docs/_queue.md` - your work dispatch (what to build, in what order)
3. Read `docs/_planning_status.md` - are feature docs ready for implementation?
4. Read the feature doc for your assigned task
5. Work, following the Definition of Done

## Role: Orchestrator

If you are the top-level agent (reading this directly):
- You manage the queue, dispatch sub-agents, and handle gates
- Read `docs/_framework/guide_orchestration.md` for full instructions
- Always use the most capable model for orchestration
- Dispatch sub-agents matched to task complexity (C1/C2/C3)

## Role: Sub-Agent

If you were spawned by an orchestrator to complete a specific task:
- Read the feature doc specified in your task
- Implement to match User Intent, not just technical specs
- Follow the Definition of Done (feature doc + standard DoD)
- Update docs as part of task completion, not as a separate step

## Sub-Agent Model Selection

When spawning sub-agents, use the task's complexity level from `_queue.md`:
- **C1 (Routine)**: Fastest/cheapest model - scaffolding, config, simple patterns
- **C2 (Moderate)**: Mid-tier model - typical feature work, integrations
- **C3 (Complex)**: Most capable model - architecture, cross-cutting, novel problems

See `docs/_framework/guide_complexity_levels.md` for detailed criteria.

## Docs Discipline

- Updating docs is part of completing a task, not a separate step
- Before marking any task complete, verify the Standard DoD in `_queue.md`
- At gates: run gate validation before reporting to human
- Never leave `[PLACEHOLDER]` markers in docs you've worked on
- Create knowledge entries (`docs/knowledge/gotcha_*.md`) when debugging takes >30 min

## Escalation Policy

**Keep working** (don't stop) for:
- Minor ambiguity → make the reasonable choice, document it
- UX/taste decisions → use best judgment, human reviews at gate
- Single blocked task → mark blocked, move to next task

**Escalate** (document and keep working on other tasks) for:
- Undocumented architectural decisions
- Security-sensitive choices with no policy
- Cost/billing implications
- Anything very expensive to undo

## Key Framework Docs

- `docs/_framework/START_HERE.md` - Framework quick start
- `docs/_framework/guide_orchestration.md` - Orchestrator guide
- `docs/_framework/guide_complexity_levels.md` - C1/C2/C3 criteria
- `docs/_framework/guide_docs_compliance.md` - How docs stay current
- `docs/_framework/template_*.md` - Templates for all doc types
