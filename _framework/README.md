# Documentation Framework - For Human Readers

> **AI Agents**: Read `START_HERE.md` instead - this file is for humans.

## What Is This?

A structured documentation framework optimized for AI-assisted development with autonomous agent workflows. Supports orchestrator/sub-agent patterns, parallel work streams, complexity-based model selection, and phase-gated human review.

## Quick Start

### For AI Agents
Point your agent to: `docs/CLAUDE.md` (auto-loaded by Claude Code) or `docs/_framework/START_HERE.md`

### For Humans

**New project?**
1. Copy this framework to your project's `/docs` folder
2. Create `docs/plan/PLAN.md` using `template_PLAN.md`
3. Define your vision, make quick decisions, create plan sections
4. Create feature docs with Definition of Done
5. Set up `docs/_queue.md` with phases, tasks, and parallel groups
6. Initialize `docs/_planning_status.md`
7. Point your AI agent to `CLAUDE.md` and let it orchestrate

**Existing project?**
1. Copy framework to `/docs`
2. Point agent to `_maintenance/prompt_migrate_existing_docs.md`
3. Agent will convert existing docs to framework structure

## Core Concepts

### 1. Orchestration & Sub-Agents
The framework supports modern agent workflows:
- **Orchestrator** (top-tier model) reads the queue, dispatches sub-agents
- **Sub-agents** (matched by complexity) implement individual tasks
- **Parallel groups** define what can be built simultaneously
- **Gates** define where agents stop for human review

See `guide_orchestration.md`.

### 2. Complexity Levels (C1/C2/C3)
Every task is assigned a complexity that determines which model tier to use:
- **C1 (Routine)**: Cheapest/fastest model - scaffolding, config, patterns
- **C2 (Moderate)**: Mid-tier model - typical feature work
- **C3 (Complex)**: Most capable model - architecture, cross-cutting concerns

See `guide_complexity_levels.md`.

### 3. Definition of Done
Every feature doc includes concrete, verifiable acceptance criteria:
- Automated checks (commands agents can run)
- Acceptance criteria (observable behaviors)
- Docs requirements (built into every task)

Agents self-validate before marking tasks complete.

### 4. Phase Gates
Agents work autonomously through entire phases. Human review happens at phase boundaries:
- Agent completes all phase tasks
- Agent reports what was built + any blockers
- Human tests the holistic experience
- Human feedback becomes tasks in the next phase

No per-feature human approval needed. Just "tell me when done, I'll check the whole thing."

### 5. Progressive Disclosure
Agents load minimal context:
- `CLAUDE.md` (~500 tokens, auto-loaded) - Agent instructions
- `_status.md` (~300 tokens) - Current state
- `_queue.md` (~1,200+ tokens) - Work dispatch
- Feature doc (~800-2,000 tokens) - Task details

**Target**: <3,000 tokens to start orchestrating

### 6. User Intent Drives Implementation
Every feature doc starts with what the user wants and why it matters.
Agents implement to match intent, not just technical specs.

### 7. Token Budget Awareness
Relaxed for modern 200k+ context windows but still enforced to prevent bloat.
See `TOKEN_BUDGETS.md` for limits (v3).

### 8. Knowledge Capture
Systematic capture of gotchas, solutions, patterns, and performance wins.
Prevents repeated debugging of known issues.

## Document Structure

```
docs/
├── CLAUDE.md                    # Agent instructions (auto-loaded by Claude Code)
├── .cursorrules                 # Agent instructions (auto-loaded by Cursor)
├── _status.md                   # Current work state (agents read first)
├── _context.md                  # Project history and context
├── _queue.md                    # Implementation queue (phases, tasks, gates)
├── _planning_status.md          # Planning progress dashboard
├── _framework/                  # Framework docs
│   ├── START_HERE.md           # Agent entry point
│   ├── TOKEN_BUDGETS.md        # Budget guidelines
│   ├── guide_orchestration.md  # Orchestrator guide
│   ├── guide_complexity_levels.md # C1/C2/C3 criteria
│   ├── guide_docs_compliance.md # Keeping docs current
│   ├── guide_*.md              # Other task-specific guides
│   ├── template_*.md           # Doc templates
│   └── _maintenance/           # Maintenance prompts
├── plan/
│   ├── PLAN.md                 # Master plan
│   └── plan_section_*.md       # Detailed sections
├── features/                    # Feature docs (with DoD)
│   ├── feature_*.md            # Main features
│   └── feature_*_*.md          # Sub-features
├── knowledge/                   # Lessons learned
│   ├── _index.md               # Searchable index
│   ├── gotcha_*.md             # Pitfalls
│   ├── solution_*.md           # Solutions
│   ├── pattern_*.md            # Patterns
│   └── perf_*.md               # Optimizations
├── reference/                   # External docs
│   ├── _index.md               # Searchable index
│   ├── api_*.md                # API docs
│   └── lib_*.md                # Library docs
├── checklists/                  # Task lists
├── audits/                      # Assessments
└── sessions/                    # Work logs
```

## Agent Workflow

### Orchestrator Flow
1. Read `CLAUDE.md` → `_status.md` → `_queue.md` → `_planning_status.md`
2. Identify ready tasks in current phase
3. Dispatch sub-agents by complexity (C1/C2/C3)
4. Monitor progress, resolve blockers
5. When phase complete: run gate validation, report to human
6. Incorporate human feedback, proceed to next phase

### Sub-Agent Flow
1. Read assigned feature doc
2. Implement task
3. Verify Definition of Done
4. Update docs (Implementation Notes + queue status)
5. Report completion

### Creating Docs
- Use templates from `_framework/template_*.md`
- Follow naming: `[type]_[name].md` (lowercase, underscores)
- Respect token budgets
- Link instead of duplicate
- Fill Definition of Done with concrete checks

## Templates

All in `docs/_framework/`:
- `template_QUEUE.md` - Implementation queue with phases and gates
- `template_PLANNING_STATUS.md` - Planning progress dashboard
- `template_FEATURE.md` - Features with DoD (~2,000 token budget)
- `template_FEATURE_SIMPLE.md` - Simple features (~1,200 tokens)
- `template_PLAN.md` - Master plan (~1,200 tokens)
- `template_PLAN_SECTION.md` - Plan details (~2,500 tokens)
- `template_KNOWLEDGE.md` - Gotchas/solutions (~800 tokens)
- `template_SESSION_LOG.md` - Work summary (~800 tokens)
- `template_AUDIT.md` - Assessments (~1,200 tokens)
- `template_CHECKLIST.md` - Task lists (~1,000 tokens)

## Guides for Agents

Task-specific guides in `_framework/`:
- `guide_orchestration.md` - Managing sub-agents and work dispatch
- `guide_complexity_levels.md` - C1/C2/C3 assignment criteria
- `guide_docs_compliance.md` - Keeping docs current during work
- `guide_initial_planning.md` - Starting new project
- `guide_creating_docs.md` - Creating any doc type
- `guide_updating_docs.md` - Maintaining during work
- `guide_navigation.md` - Finding documents
- `guide_cross_referencing.md` - Linking patterns

## Maintenance

### Token Analysis
```bash
docs/_framework/utilities/venv/bin/python docs/_framework/utilities/count_tokens.py
```

View results in `docs/_framework/token_counts.md`

### Framework Cleanup
Point agent to maintenance prompts in `_framework/_maintenance/`:
- `prompt_cleanup_orphaned_docs.md` - Remove stale docs
- `prompt_rebuild_indexes.md` - Refresh indexes
- `prompt_fix_broken_references.md` - Fix links
- `prompt_audit_framework_compliance.md` - Check conventions
- `prompt_migrate_existing_docs.md` - Convert existing docs

## Core Principles

1. **User Intent is Sacred** - Implement what user wants, not just specs
2. **Docs are Part of the Task** - Not a separate step, not policed after the fact
3. **Link, Never Duplicate** - Cross-reference instead of copy
4. **Complexity Drives Model Selection** - C1/C2/C3 for efficient resource use
5. **Gates, Not Micromanagement** - Agents work autonomously, humans review at phase boundaries
6. **Token Budget Awareness** - Focused docs, not bloated ones
7. **Follow Naming Conventions** - Consistency enables findability
8. **Progressive Disclosure** - Load only what's needed

## FAQ

**Q: What changed in v3?**
A: Added orchestration layer (`_queue.md`), complexity levels (C1/C2/C3), Definition of Done in feature docs, planning status tracking, phase gates, and relaxed token budgets for modern context windows.

**Q: Is v3 backward compatible with v2 projects?**
A: Yes. All new files are additive. Existing feature docs work fine - they just won't have DoD sections until you add them. You can adopt v3 features incrementally.

**Q: Why complexity levels?**
A: Not every task needs the most expensive model. Scaffolding (C1) can use a fast cheap model. Architecture decisions (C3) need the best. This saves cost and time.

**Q: Why no per-feature human review?**
A: Modern agents get things right most of the time. Stopping for human approval on each feature creates bottlenecks. Instead, agents work through entire phases autonomously, and humans review the holistic experience at gates.

**Q: Why is Definition of Done important?**
A: It lets agents self-validate. Instead of hoping the implementation is correct, the agent runs concrete checks before marking done. Catches issues immediately, not at review time.

**Q: Can I use this without sub-agents?**
A: Yes. The "Solo Agent" workflow in START_HERE.md works for single-agent setups. The queue and gates still help structure the work.

## Philosophy

Documentation should:
- Drive implementation through clear user intent
- Enable autonomous agent workflows with minimal human interruption
- Preserve decisions and knowledge
- Optimize for AI context windows
- Support parallel work streams
- Be consistent and findable

---

**Version**: 3.0
**Last Updated**: 2026-02-05
**For**: AI-assisted development teams using Claude Code, Cursor, or similar tools
