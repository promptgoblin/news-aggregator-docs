# Guide: Initial Planning

**Use when**: Starting a new project from scratch

## Workflow

### 1. Initialize _status.md
```markdown
Working On: Initial planning
Status: Planning
Next Steps:
1. Define project vision
2. Make quick decisions
3. Identify plan sections needed
```

### 2. Create PLAN.md
1. Copy `template_PLAN.md` to `plan/PLAN.md`
2. Fill **Vision**: What you're building, why, problem it solves (2-3 sentences)
3. List **Quick Decisions**: Framework, database, auth, deployment
   - Keep brief - just the choice and 1-sentence rationale

### 3. Identify Planning Areas
Determine what needs deep research/design:

**Common plan sections**:
- `plan_section_architecture.md` - System design, tech stack, infrastructure
- `plan_section_data_model.md` - Database schema, relationships, data flow
- `plan_section_auth.md` - Authentication/authorization approach
- `plan_section_api_design.md` - API structure, endpoints, patterns
- `plan_section_deployment.md` - Hosting, CI/CD, environments
- `plan_section_testing.md` - Testing strategy, frameworks, coverage

Create only what you need. Simple projects may only need 1-2 sections.

### 4. Create Plan Sections
For each area:
1. Copy `template_PLAN_SECTION.md` to `plan/plan_section_[area].md`
2. Fill **Overview**, **Key Decisions**, **Design**
3. Document **Rationale** (why this choice over alternatives)
4. List in PLAN.md "Plan Sections" area

**Parallel planning**: Multiple plan sections can be planned simultaneously by different sub-agents (each is typically C2-C3). Track assignments in `_planning_status.md`.

### 5. Define Features in PLAN.md
Once architecture is clear:
1. List features with brief descriptions
2. Mark status: Planning | Not Started
3. Reference relevant plan sections
4. Assign initial complexity (C1/C2/C3) - see `guide_complexity_levels.md`
5. Map feature dependencies (what depends on what)

### 6. Create Feature Docs When Ready
When ready to implement:
1. Copy `template_FEATURE.md` (or `template_FEATURE_SIMPLE.md` for simple features)
2. Fill **User Intent section FIRST** (what user wants, why, success criteria)
3. Add technical details
4. Fill **Definition of Done** with concrete, runnable checks
5. Set complexity in frontmatter
6. Link from PLAN.md

**Parallel feature planning**: Feature docs can be planned simultaneously by sub-agents. Track in `_planning_status.md`.

### 7. Set Up Implementation Queue
Once features are defined:
1. Copy `template_QUEUE.md` to `_queue.md`
2. Organize features into phases
3. Break features into tasks with complexity levels
4. Identify parallel groups (what can be built simultaneously)
5. Define gates between phases

### 8. Initialize Planning Status
1. Copy `template_PLANNING_STATUS.md` to `_planning_status.md`
2. List all plan sections and feature docs
3. Mark depth (stub/outline/full) for each
4. Note pending decisions that block planning

### 9. Update Status Files
After completing each major step:
- Update `_status.md`: Working On, Next Steps, Active Phase
- Update `_context.md`: Feature Status, Recent Changes

## Tips

- **Start simple**: Don't over-plan. Create plan sections as you discover need for them
- **User Intent first**: Even in planning, think about what users will do
- **Link dependencies**: Note in plan sections which features depend on which decisions
- **Plan in parallel**: Use sub-agents to plan independent features simultaneously
- **Fill DoD early**: Writing Definition of Done during planning forces concrete thinking
- **Token budget**: Keep PLAN.md under 1,200 tokens - move details to plan sections

## Execution Sequence

```
1. Initialize _status.md and _context.md
2. Create PLAN.md with vision
3. Make quick decisions (framework, database, auth, hosting)
4. Create plan_section_architecture.md (system design)
5. Create plan_section_data_model.md (schema design)
6. [Create additional plan sections as needed - can parallelize]
7. Define features in PLAN.md with dependencies and complexity
8. Create feature docs (starting with feature_*.md - can parallelize)
9. Set up _queue.md with phases, tasks, parallel groups, gates
10. Initialize _planning_status.md
11. Update _status.md and _context.md
-> Planning complete, ready to implement
```

## Planning Complete When...

Use this checklist to determine if planning is complete:

### MVP (Minimum Viable Planning)
Sufficient to start coding:
- [ ] PLAN.md created with clear vision (what/why/problem)
- [ ] Quick Decisions documented (tech stack basics)
- [ ] 3-5 core features defined (enough for MVP)
- [ ] Feature dependencies mapped (know implementation order)
- [ ] Each feature has complexity assigned (C1/C2/C3)
- [ ] `_queue.md` created with Phase 1 tasks and parallel groups
- [ ] `_planning_status.md` initialized
- [ ] Phase 1 feature docs have DoD filled with concrete checks
- [ ] _status.md shows clear "Next Steps: Begin Phase 1"

### Full Planning
Recommended for complex projects:
- [ ] All of MVP checklist above
- [ ] Key plan sections complete (architecture, data model)
- [ ] Auth/security approach documented (if applicable)
- [ ] All MVP features have feature docs at "full" depth
- [ ] Edge cases and technical risks identified
- [ ] Testing strategy outlined
- [ ] All phases defined in `_queue.md` with gates
- [ ] `_planning_status.md` shows no stubs for Phase 1 features

**Guideline**: For most projects, start with MVP planning. Plan Phase 1 fully, outline later phases. Create additional plan sections and feature docs as you discover need during implementation.

## Next Steps

After planning complete:
- Orchestrator reads `guide_orchestration.md` to begin dispatching work
- Sub-agents read their assigned feature docs and implement
- Use `guide_docs_compliance.md` to keep docs current during coding
- Human reviews holistically at phase gates
