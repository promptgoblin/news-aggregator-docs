# Guide: Complexity Levels

**Use when**: Assigning complexity to tasks in `_queue.md` or features in feature docs

## Three Levels

### C1 - Routine

**What it means**: Straightforward work that follows established patterns with minimal judgment.

**Characteristics**:
- Single file or small set of closely related files
- Following an existing pattern in the codebase with little adaptation
- Clear inputs and outputs, no ambiguity
- No architectural decisions

**Examples**:
- Scaffolding a new model/component following existing ones
- CRUD endpoints matching an existing resource pattern
- Config file changes, environment variable additions
- Writing tests that mirror existing test patterns
- Creating docs from templates
- Renaming, reformatting, simple refactors
- Adding a field to an existing form/API/model

**Model guidance**: Use the fastest/cheapest model available (e.g., Haiku-tier)

---

### C2 - Moderate

**What it means**: Work that requires understanding context and adapting patterns, but operates within a single feature boundary.

**Characteristics**:
- Multi-file changes within one feature
- Adapting existing patterns to new requirements
- Integration with one external service using documented APIs
- Moderate business logic with some edge cases
- Requires reading and understanding related docs

**Examples**:
- Implementing a new feature that follows the project's conventions but isn't copy-paste
- Integrating a well-documented third-party API (Stripe, SendGrid, etc.)
- Writing tests that require understanding feature behavior and edge cases
- Bug fixes where the root cause is identified in the docs
- Planning a feature that has clear parallels in the existing codebase
- Data migrations with straightforward transformations

**Model guidance**: Use a mid-tier model (e.g., Sonnet-tier)

---

### C3 - Complex

**What it means**: Work requiring architectural judgment, novel problem-solving, or reasoning about system-wide implications.

**Characteristics**:
- Cross-cutting concerns affecting multiple features
- No existing pattern in the codebase to follow
- Multi-service integration or coordination
- Complex business logic with subtle edge cases
- Security-sensitive implementations
- 3+ feature dependencies

**Examples**:
- Designing and implementing auth/permissions systems
- Building real-time features (WebSockets, SSE, pub/sub)
- Data model changes that affect multiple features
- Performance optimization requiring profiling and tradeoff analysis
- Debugging without a known root cause
- Planning features with novel architecture
- Implementing complex state machines or workflow engines
- Any work involving cryptography, financial calculations, or compliance

**Model guidance**: Use the most capable model available (e.g., Opus-tier)

---

## Assigning Complexity

### Who assigns?
The **orchestrating agent** (always top-tier) assigns complexity when breaking features into tasks for `_queue.md`. Humans can override.

### Feature vs. Task complexity
- **Feature docs** get an overall complexity in frontmatter - this is the default for tasks from that feature
- **Individual tasks** in `_queue.md` can override up or down
- A C3 feature often has C1 sub-tasks (scaffolding, config) and C3 sub-tasks (core logic)

### When unsure
- Default to one level higher (C1 → C2, C2 → C3)
- A slightly overpowered model wastes a little cost
- An underpowered model wastes time and produces lower quality work
- After task completion, note actual complexity for future calibration

## Complexity Escalation

If a sub-agent encounters work harder than its assigned complexity:

1. **Stop** working on the task
2. **Document** what was discovered in the feature's Implementation Notes
3. **Update** `_queue.md`: set task status to `needs_escalation`, add note explaining why
4. **Move on** to next available task at the agent's level
5. Orchestrator re-evaluates and re-assigns at appropriate complexity

Signs a task needs escalation:
- Agent is making assumptions about architecture it shouldn't
- Multiple approaches seem valid and the tradeoffs are unclear
- Unexpected dependencies or side effects discovered
- Task scope significantly larger than originally estimated

## Model Mapping

This framework is vendor-agnostic. Map C1/C2/C3 to your available models:

| Complexity | Anthropic | OpenAI | Generic |
|-----------|-----------|--------|---------|
| C1 | Haiku | GPT-4o-mini | Fastest/cheapest |
| C2 | Sonnet | GPT-4o | Mid-tier |
| C3 | Opus | o1/o3 | Most capable |

Override in your project's `CLAUDE.md` or `.cursorrules` if your model lineup differs.
