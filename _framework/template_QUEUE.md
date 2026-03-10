# Implementation Queue

<!--
AGENT: This is your primary work dispatch document.
Read this to know: what to work on, in what order, with what resources.
Update this as you complete tasks.
-->

> **Budget**: 1.5k tokens for structure; grows with tasks (that's fine - this is a working doc)

## Active Phase: [Phase Name] [Status]

### Phase Goal
[1-2 sentences: what's true when this phase is complete]

### Tasks

<!-- STATUS: ready | in_progress | complete | blocked | needs_escalation -->
<!-- COMPLEXITY: C1 (routine) | C2 (moderate) | C3 (complex) - see guide_complexity_levels.md -->

| # | Task | Feature | Complexity | Status | Owner | Depends On | Notes |
|---|------|---------|-----------|--------|-------|------------|-------|
| 1 | [Task description] | [feature_name.md] | C2 | ready | - | - | |
| 2 | [Task description] | [feature_name.md] | C1 | ready | - | - | |
| 3 | [Task description] | [feature_name.md] | C3 | blocked | - | #1, #2 | |
| 4 | [Task description] | [feature_name.md] | C1 | ready | - | - | |

### Parallel Groups

<!--
Tasks in the same group can be worked simultaneously by different sub-agents.
Tasks in different groups must be completed sequentially (earlier groups first).
-->

- **Group A** (can start immediately): #1, #2, #4
- **Group B** (requires Group A): #3

### Blockers

<!-- Track anything preventing progress. Orchestrator resolves or escalates. -->

| Task | Blocker | Type | Resolution |
|------|---------|------|------------|
| - | - | - | - |

---

## Gate: [Phase Name] → [Next Phase Name]

**Type**: phase_boundary

**When all Phase tasks are complete or accounted for:**

1. Orchestrator spawns C1 sub-agent to run gate validation:
   - [ ] All tasks marked `complete` or `blocked` with documented reason
   - [ ] All feature docs have DoD checked off
   - [ ] `_planning_status.md` reflects current state
   - [ ] No orphaned `[PLACEHOLDER]` markers in phase docs
   - [ ] Run: `docs/_framework/utilities/validate_quick.sh` on all changed docs
   - [ ] Knowledge entries created for significant discoveries
   - [ ] Blockers documented with context

2. Orchestrator reports to human:
   - Summary of what was built
   - List of unresolved blockers needing human input
   - Any decisions made that human should be aware of

3. Human tests holistic experience, provides feedback

4. Feedback becomes tasks at the top of next phase queue

- **APPROVED**: [yes/no] [date]
- **Feedback tasks added**: [list or "none"]

---

## Next Phase: [Phase Name] [NOT STARTED]

### Phase Goal
[1-2 sentences]

### Tasks

| # | Task | Feature | Complexity | Status | Owner | Depends On | Notes |
|---|------|---------|-----------|--------|-------|------------|-------|
| | | | | | | | |

### Parallel Groups
- **Group A**: [tasks]

---

## Completed Phases

### Phase: [Name] - Completed [DATE]
- Tasks completed: [X]
- Blockers resolved: [X]
- Human feedback items: [X]
- Gate approved: [DATE]

---

## Standard Definition of Done (All Tasks)

<!--
AGENT: Every task is incomplete until ALL of these are true.
Do not mark a task complete without verifying each item.
-->

### Code
- [ ] Implementation matches feature doc specifications
- [ ] No TODO/FIXME/HACK left in committed code (or documented in feature doc if intentional)
- [ ] Tests pass (run the test command specified in feature DoD)

### Docs
- [ ] Feature doc Implementation Notes updated with discoveries/deviations
- [ ] This queue updated (task status → complete)
- [ ] Knowledge entry created if debugging took >30 min
- [ ] No `[PLACEHOLDER]` markers left in docs you touched

### Verification
- [ ] Feature-specific DoD checks pass (see feature doc)

---

## Escalation Policy

<!--
AGENT: Read this carefully. This determines when you stop vs. keep moving.
-->

### Keep Working (do NOT stop)
- Minor ambiguity in requirements → make the reasonable choice, document it in Implementation Notes
- UX/taste decisions → implement your best judgment, human reviews holistically at gate
- A single task is blocked → mark it blocked, move to next available task
- Unsure about naming/style → follow existing project patterns
- Feature works but could be better → ship it, note improvement ideas in Outstanding

### Mark Blocked (move to next task)
- External dependency unavailable (API down, credentials missing, service not provisioned)
- Conflicting requirements between features that can't be resolved from docs
- Task depends on a blocked task (cascade block)

### Escalate to Human (add to Blockers table, keep working on other tasks)
- Fundamental architectural decision not covered in plan docs
- Security-sensitive decision with no documented policy
- Cost/billing implications that need human approval
- Legal/compliance questions
- Anything that would be very expensive to undo if wrong

**Golden Rule**: When in doubt, make your best call, document it clearly, and keep moving. The human reviews holistically at the gate. It's cheaper to adjust a reasonable decision than to block waiting for approval.
