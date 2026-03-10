# Guide: Creating Documentation

**Use when**: Creating any type of documentation

## Quick Router

**What are you creating?**

### Feature Documentation
→ Read [guide_creating_feature.md](guide_creating_feature.md)

- Standard features (>500 LOC OR >3 components OR >2 dependencies)
- Simple features (<500 LOC AND <3 components AND <2 dependencies)
- Sub-features and splitting logic
- Granularity guidelines

### Knowledge Entries
→ Read [guide_creating_knowledge.md](guide_creating_knowledge.md)

- Gotchas (problems encountered)
- Solutions (reusable fixes)
- Patterns (design patterns)
- Performance optimizations

### Reference Documentation
→ Read [guide_creating_reference.md](guide_creating_reference.md)

- External API documentation
- Library documentation
- When to create vs inline link

### Other Documentation
→ Read [guide_creating_other.md](guide_creating_other.md)

- Plan sections (architecture, decisions)
- Checklists (deployment, testing)
- Audits (security, performance)
- Session logs (work summaries)

## Decision Tree

```
What are you documenting?

User-facing feature?
  → guide_creating_feature.md

Bug, gotcha, or solution?
  → guide_creating_knowledge.md

External API or library?
  → guide_creating_reference.md

Architecture decision?
  → guide_creating_other.md (Plan Sections)

Task list or audit?
  → guide_creating_other.md (Checklists/Audits)

Work summary?
  → guide_creating_other.md (Session Logs)
```

## General Guidelines

**All document types**:

1. **Choose right template** - See specific guides above
2. **Fill User Intent first** (for features) or Summary (for knowledge)
3. **Follow naming conventions** - Always lowercase, use underscores
4. **Update parent/index files**:
   - Features → `PLAN.md`
   - Current work → `_status.md`
   - Knowledge/Reference → Category `_index.md`
5. **Add cross-references** - Bidirectional links
6. **Check token budget** - See `TOKEN_BUDGETS.md`

## Common Naming Patterns

- Features: `feature_[name].md`
- Sub-features: `feature_[parent]_[sub].md`
- Knowledge: `[type]_[description].md` (gotcha, solution, pattern, perf)
- References: `api_[service]_[topic].md` or `lib_[library]_[topic].md`
- Plan sections: `plan_section_[topic].md`
- Sessions: `session_[YYYY_MM_DD]_[topic].md`
- Checklists: `checklist_[phase].md`
- Audits: `audit_[type]_[date].md`

See `NAMING_CONVENTIONS.md` for complete rules.

## Cross-Referencing

**Quick rules**:
- Use relative links: `[feature_auth.md]`
- Link when dependency/context needed
- Bidirectional: if A needs B, both link to each other
- Never duplicate content - link instead

See [guide_cross_referencing.md] for complete patterns.

---

**Next**: Read the specific guide for your document type above.
