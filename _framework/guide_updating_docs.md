# Guide: Updating Documentation

**Use when**: Maintaining docs during implementation work

## Update _status.md (Critical)

**AGENT**: If you just committed code, read this section. Otherwise jump to your scenario below.

### When to Update
- **After any git commit** (primary trigger)
- Starting new feature/task
- Reaching meaningful milestone
- Completing a feature
- Getting blocked
- Switching focus areas
- About to end session (planned or context running low)

### What to Update
```markdown
## Current Session
Working On: [current feature or task]
Status: [Planning | In Progress | Testing | Blocked]
Blocked By: [issue or "Nothing"]

## Next Steps
1. [Next priority]
2. [Second priority]
3. [Third priority]

## Active Documents
- Feature: [current feature doc]
- Plan Section: [if relevant]
- Reference: [if using external API]

## Feature Status
- [Add or update feature with emoji]
  ✅ Complete | 🔄 In Progress | 📋 Planned | 💡 Proposed

## Recent Changes
- **[DATE]**: [What was done] - See [doc_name.md]

**Last Updated**: [DATE]
```

### Also Update _context.md When:
- Completing a feature (update Feature Status)
- Significant milestone (add to Recent Changes)
- End of work session (add to Recent Changes)

**Just needed _status.md update? You're done. Otherwise continue below.**

---

## Update Feature Docs

### During Implementation

**Add to "Implementation Notes"**:
- Discoveries during development
- Changes from original plan (and why)
- Technical debt added (with reason)
- Integration gotchas encountered

```markdown
## Implementation Notes
- 2024-10-05: Changed from REST to GraphQL for real-time - better performance
- 2024-10-05: Added TODO: refactor validation (copy-paste for speed)
```

### After Completing Work

**Update**:
- Status: `Planning` → `In Progress` → `Testing` → `Complete`
- Mark Testing checklist items
- Fill Outstanding section with any remaining tasks
- Add "Completed" date

**Updated feature docs? Jump to:** [Common Update Scenarios](#common-update-scenarios)

---

## Update Knowledge Base

### During Debugging

If issue takes >30 min:
1. Create `knowledge/gotcha_[desc].md`
2. Document symptoms, cause, solution
3. Add to `knowledge/_index.md`
4. Reference in feature's Implementation Notes

### When Finding Patterns

If approach used 2+ times:
1. Create `knowledge/pattern_[desc].md`
2. Include when to use AND when NOT to use
3. Add to `knowledge/_index.md`
4. Reference from features using it

**Updated knowledge? Jump to:** [Common Update Scenarios](#common-update-scenarios)

---

## Update Plan Sections

### When Decisions Change

**Add to Decision History**:
```markdown
## Decision History
**2024-03**: Chose PostgreSQL (performance needs)
**2024-05**: → Changed to MongoDB (schema flexibility won)
See: session_2024_05_12_db_migration.md
```

**Update affected**:
- Feature docs that depend on this decision
- PLAN.md if impacts multiple features
- Implementation approaches in plan section

## Common Update Scenarios

### Completed a Feature
1. Update feature doc Status → `Complete`
2. Update `_context.md` Feature Status → ✅
3. Update `_context.md` Recent Changes
4. Update `_status.md` Working On → next feature
5. Commit changes

### Hit a Blocker
1. Update `_status.md` Status → `Blocked`
2. Update `_status.md` Blocked By → specific issue
3. Document in feature's Outstanding section
4. Update Next Steps with unblocking tasks

### Found a Gotcha
1. Create `knowledge/gotcha_[desc].md`
2. Add to `knowledge/_index.md`
3. Note in current feature's Implementation Notes
4. Update `_context.md` Recent Changes

### Architecture Decision Changed
1. Update relevant `plan_section_*.md`
2. Add to Decision History with rationale
3. Update affected feature docs
4. Create session log if significant
5. Update `_context.md` Recent Changes

### Switching Tasks
1. Update current feature doc (save state in Implementation Notes)
2. Update `_status.md` Working On
3. Update `_status.md` Active Documents
4. Update `_status.md` Next Steps
5. Commit

## Session End Updates

### Before Ending Session

**If significant work done** (3-5+ commits):
1. Create `session_[YYYY_MM_DD]_[topic].md`
2. Document decisions, problems, solutions
3. Extract knowledge entries if needed
4. List next session priorities

**Always**:
1. Update `_status.md` with current state
2. Update `_context.md` Recent Changes
3. Commit all doc changes
4. Ensure nothing in intermediate state

## Anti-Patterns

❌ Don't update docs only at end of session
✅ Update `_status.md` after each commit

❌ Don't duplicate info across docs
✅ Update in one place, reference from others

❌ Don't leave outdated status markers
✅ Keep status current in all docs

❌ Don't skip Implementation Notes
✅ Document as you discover

## Quick Checklist

After each commit:
- [ ] `_status.md` Working On current?
- [ ] Feature doc Implementation Notes updated?
- [ ] Relevant knowledge entries created?
- [ ] Status markers accurate?

After milestones:
- [ ] `_context.md` Recent Changes updated?
- [ ] `_context.md` Feature Status current?
