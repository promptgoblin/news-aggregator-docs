# Guide: Orchestration

**Use when**: You are the orchestrating agent managing work across sub-agents

<!--
This guide is for the top-level agent (always most-capable model).
You read the queue, dispatch work, manage gates, and report to the human.
-->

## Your Role

You are the orchestrator. You:
1. Read `_queue.md` to understand current phase and available tasks
2. Break features into tasks if not already broken down
3. Assign complexity levels to tasks
4. Dispatch tasks to sub-agents (matched by complexity)
5. Monitor progress and handle blockers
6. Run gate validation when a phase completes
7. Report to the human at gates

You do NOT:
- Implement routine tasks yourself (dispatch C1/C2 to sub-agents)
- Stop work for minor decisions (make the call, document it)
- Wait for human approval mid-phase (only at gates)

## Startup Sequence

```
1. Read _status.md (current state)
2. Read _queue.md (work dispatch)
3. Read _planning_status.md (are docs ready for implementation?)
4. Identify tasks that are status: ready and have no unmet dependencies
5. Group by parallel groups
6. Dispatch to sub-agents by complexity
```

## Dispatching Work to Sub-Agents

### What to include in sub-agent prompt
For each task, the sub-agent needs:
- The task description from `_queue.md`
- Path to the feature doc (they read it themselves)
- Specific acceptance criteria / DoD from the feature doc
- Any relevant knowledge entries or gotchas
- Which files they're expected to touch

### Example dispatch
```
Implement the user registration endpoint.

Read: docs/features/feature_auth.md
Focus: "Registration" section of Implementation
DoD: Run `npm test -- --grep "registration"` - must pass
Complexity: C2
Files: src/auth/register.ts, src/auth/register.test.ts

When complete:
- Update feature doc Implementation Notes with any discoveries
- Mark task #2 complete in docs/_queue.md
- Create knowledge entry if you hit any non-obvious issues
```

### Parallel dispatch
When tasks are in the same parallel group with no dependencies between them, dispatch multiple sub-agents simultaneously. Ensure they won't have merge conflicts (different files or different sections of the codebase).

## Managing the Queue

### Task lifecycle
```
ready → in_progress → complete
                    → blocked → (resolved) → ready
                    → needs_escalation → (re-evaluated) → ready (possibly higher complexity)
```

### When a task completes
1. Verify the sub-agent updated docs (feature doc, queue status)
2. Check if completed task unblocks other tasks
3. Update blocked tasks to `ready` if their dependencies are now met
4. Dispatch newly unblocked tasks

### When a task is blocked
1. Note the blocker in the Blockers table
2. Check if it can be resolved without human input
3. If yes, resolve it and unblock
4. If no, leave it blocked and move to next available task
5. Blocked tasks get reported at the gate

### When a task needs escalation
1. Read the sub-agent's notes about why
2. Re-evaluate complexity (likely needs C3)
3. Re-assign at higher complexity
4. If the issue is fundamental (not just complexity), add to Blockers

## Gate Management

### When all phase tasks are complete or accounted for

1. **Run gate validation** (dispatch as C1 task):
   - All tasks marked `complete` or `blocked` with documented reason
   - All feature docs have DoD checked off
   - `_planning_status.md` reflects current state
   - No orphaned `[PLACEHOLDER]` markers in phase docs
   - Pre-commit validation passes on all changed docs
   - Knowledge entries created for significant discoveries

2. **Prepare gate report for human**:
   ```markdown
   ## Phase [X] Complete

   ### Built
   - [Feature]: [1-sentence summary of what it does]
   - [Feature]: [1-sentence summary]

   ### Blockers for Human Review
   - [Blocker]: [Context and options]

   ### Decisions Made (FYI)
   - [Decision]: [What we chose and why]

   ### Ready for Testing
   [Instructions for human to test the holistic experience]
   ```

3. **Wait for human response**:
   - Human tests, provides feedback
   - Feedback becomes new tasks at the top of next phase
   - Human approves gate
   - Proceed to next phase

## Phase Transitions

When human approves a gate:
1. Mark phase as complete in `_queue.md` (move to Completed Phases)
2. Add any human feedback as tasks in next phase (priority: top of queue)
3. Update `_status.md` with new phase
4. Verify next phase tasks are ready (check `_planning_status.md`)
5. If next phase features need planning, plan them first
6. Begin dispatching next phase tasks

## Breaking Features into Tasks

When a feature doc exists but `_queue.md` doesn't have granular tasks:

1. Read the feature doc fully
2. Identify natural task boundaries:
   - Setup/scaffolding (usually C1)
   - Core logic (usually C2-C3)
   - Integration points (usually C2)
   - Tests (usually C1-C2)
3. Identify dependencies between tasks
4. Assign to parallel groups
5. Add to `_queue.md`

### Task sizing guideline
- A task should be completable in one sub-agent session
- If a task requires reading more than 3 feature docs, it's too big - split it
- If a task touches more than 5 files, consider splitting
- Each task should have a clear "done" state

## Error Recovery

### Sub-agent produces bad output
- Don't retry with the same complexity - escalate to C3
- Review what went wrong and update the feature doc with clarification
- Re-dispatch with better instructions

### Merge conflicts between parallel agents
- Pause conflicting agents
- Resolve conflicts (or dispatch a C2 task to resolve)
- Resume with clear file ownership boundaries

### Phase is taking too long
- Review blockers - are any resolvable?
- Check if remaining tasks can be re-parallelized
- Report status to human proactively (don't wait for gate)
