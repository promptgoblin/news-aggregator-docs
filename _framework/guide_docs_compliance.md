# Guide: Docs Compliance

**Use when**: Understanding how docs stay current during implementation

## Principle

Docs updates are part of the task, not a follow-up activity.
The agent that does the work updates the docs. Same context, same task, same moment.

If docs require a separate agent to police, the workflow is wrong.

## Three Layers of Enforcement

### Layer 1: Definition of Done (Every Task)

Every task in `_queue.md` is incomplete until docs are updated. This is built into the Standard DoD:

**After completing code for any task**:
- [ ] Feature doc Implementation Notes updated with discoveries/deviations
- [ ] `_queue.md` status updated (this task → complete)
- [ ] Knowledge entry created if debugging took >30 min
- [ ] No `[PLACEHOLDER]` markers left in docs you touched

This is not a separate "docs step." It's the last part of the task itself. The agent that wrote the code has the context fresh - that's the best moment to document.

### Layer 2: Gate Validation (At Phase Boundaries)

When a phase completes, the orchestrator spawns a C1 sub-agent to verify docs compliance across the entire phase:

**Gate validation checklist**:
- [ ] All phase tasks marked `complete` or `blocked` with reason
- [ ] All feature docs have DoD fully checked off
- [ ] `_planning_status.md` reflects current state (depths, placeholders)
- [ ] No orphaned `[PLACEHOLDER]` markers in any phase docs
- [ ] Pre-commit validation passes: `docs/_framework/utilities/validate_quick.sh`
- [ ] Knowledge entries exist for significant discoveries
- [ ] Blockers documented with enough context for human to act

If validation fails, the orchestrator fixes issues before reporting the gate to the human.

### Layer 3: Pre-Commit Hooks (Every Commit)

Already exist and validate:
- File naming conventions
- Token budgets
- Required sections present
- Internal links valid
- Compliance badges

These catch structural issues automatically. No agent action needed.

## What Gets Updated When

| Event | Update |
|-------|--------|
| Task started | `_queue.md` task status → in_progress |
| Discovery during implementation | Feature doc Implementation Notes |
| Task completed | `_queue.md` task status → complete |
| Debugging >30 min | Create `knowledge/gotcha_*.md`, add to `_index.md` |
| Reusable pattern found | Create `knowledge/pattern_*.md`, add to `_index.md` |
| Task blocked | `_queue.md` status → blocked, add to Blockers table |
| Phase completed | Gate validation, orchestrator report |
| Architecture decision changed | `plan_section_*.md` Decision History, affected feature docs |
| Human feedback received | New tasks in `_queue.md`, update affected feature docs |

## Anti-Patterns

**"I'll update docs later"**
No. Update now while context is fresh. Later means never or low-quality.

**Separate "docs update" task in the queue**
No. Docs updates are part of every task's DoD, not a standalone task.

**One agent implements, another documents**
No. The implementing agent has the context. A different agent produces worse docs.

**Updating docs only at session end**
No. Update per-task. If the agent crashes mid-phase, docs reflect the last completed task.

## For Orchestrators

Your docs responsibilities:
1. Verify sub-agents are updating docs as part of task completion
2. Run gate validation before reporting to human
3. Keep `_queue.md` accurate (this is YOUR doc to maintain)
4. Keep `_planning_status.md` current as planning progresses
5. Update `_status.md` at phase transitions

You don't need to police every doc update. The DoD structure and gate validation catch drift.

## For Sub-Agents

Your docs responsibilities:
1. Read the feature doc before starting work
2. Update Implementation Notes as you discover things
3. Check off DoD items as you complete them
4. Update your task status in `_queue.md` when done
5. Create knowledge entries for non-obvious issues

That's it. Follow the DoD and docs stay current naturally.
