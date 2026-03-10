# Guide: Creating Plan Sections, Checklists, Audits, and Sessions

**Use when**: Creating non-feature documentation

## Plan Sections

### When to Create

- Architecture needs decisions (system design, tech stack)
- Complex topic requires research and rationale
- Multiple features depend on this decision
- >3 alternatives considered

### Creating Plan Section

1. Copy `template_PLAN_SECTION.md` to `plan/plan_section_[topic].md`
2. Fill Overview, Key Decisions, Design
3. Document rationale and alternatives considered
4. Link from `PLAN.md` in "Plan Sections"
5. Reference from relevant feature docs

**Naming**: `plan_section_[topic].md`

---

## Checklists

### Purpose
Step-by-step task lists for deployment, testing, launch, etc.

### Creating Checklist

1. Copy `template_CHECKLIST.md` to `checklists/checklist_[phase].md`
2. Fill with actionable steps
3. Include verification steps
4. Add rollback procedures
5. Link from `PLAN.md`

**Naming**: `checklist_[phase].md`

**Examples**:
- `checklist_deployment.md`
- `checklist_testing.md`
- `checklist_launch.md`

---

## Audits

### Purpose
Assessments and findings (security, performance, quality)

### Creating Audit

1. Copy `template_AUDIT.md` to `audits/audit_[type]_[date].md`
2. Document methodology and findings
3. Prioritize issues (Critical/High/Medium/Low)
4. Create action items
5. Link from `PLAN.md`

**Naming**: `audit_[type]_[date].md`

**Examples**:
- `audit_security_2025_10.md`
- `audit_performance_2025_q1.md`
- `audit_accessibility_2025_10_05.md`

---

## Session Logs

### When to Create

- After multiple commits (3-5+ commits of work)
- Completing significant milestone
- Context running low (about to end session)

**Note**: Update `_status.md` after EACH commit. Session logs summarize multiple commits.

### Creating Session Log

1. Copy `template_SESSION_LOG.md` to `sessions/session_[YYYY_MM_DD]_[topic].md`
2. Document decisions, problems, solutions
3. List next session priorities
4. Create knowledge entries for discoveries
5. Update `_context.md` Recent Changes

**Naming**: `session_[YYYY_MM_DD]_[topic].md`

**Examples**:
- `session_2025_10_07_auth_implementation.md`
- `session_2025_10_08_performance_fixes.md`

---

## After Creating Any Doc

1. Update parent/index file:
   - Plan sections → Update `PLAN.md`
   - Current work → Update `_status.md`
   - Milestone → Update `_context.md`
2. Add cross-references from related docs
3. Verify naming follows conventions
4. Check token budget (see `TOKEN_BUDGETS.md`)

## General Naming Rules

**Always lowercase** (except PLAN.md, README.md)
**Use underscores** between words

See `NAMING_CONVENTIONS.md` for complete rules.

## Cross-Referencing

**Quick rules**:
- Use relative links: `[plan_section_auth.md]`
- Link when dependency/context needed
- Bi-directional links
- Never duplicate content - link instead

See [guide_cross_referencing.md] for complete patterns.
