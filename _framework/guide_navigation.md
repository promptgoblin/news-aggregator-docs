# Guide: Navigation

**Use when**: Finding documents or understanding project structure

## Always Start Here

1. **Read `_status.md`** - Current work state, blockers, next steps (~200 tokens)
2. **Read `_context.md`** if resuming work - Recent changes, feature status (~300 tokens)
3. **Read `plan/PLAN.md`** if needed - Overall context, features, decisions
4. **Load specific docs** only as needed for your task

## Finding Documents

### By Task Type

**Implementing a feature?**
1. Check `plan/PLAN.md` features list
2. Open `features/feature_[name].md`
3. Read "References" section for dependencies
4. Load referenced plan sections if needed

**Found what you need? Jump to:** [Loading Strategy](#loading-strategy)

---

**Debugging/troubleshooting?**
1. Search `knowledge/_index.md` for symptoms
2. Open relevant `gotcha_*.md` or `solution_*.md`
3. Check feature's "Implementation Notes" for known issues

**Found what you need? Jump to:** [Loading Strategy](#loading-strategy)

---

**Integrating external service?**
1. Check `reference/_index.md`
2. Open `api_[service]_*.md` or `lib_[library]_*.md`
3. Create new reference doc if not exists

**Found what you need? Jump to:** [Loading Strategy](#loading-strategy)

---

**Deploying/launching?**
1. Open `checklists/checklist_deployment.md`
2. Check `audit_*.md` for any blockers

**Found what you need? Jump to:** [Loading Strategy](#loading-strategy)

---

### By Information Type

**Architecture decisions**: `plan/plan_section_architecture.md`
**Data model**: `plan/plan_section_data_model.md`
**Auth approach**: `plan/plan_section_auth.md`
**Reusable patterns**: `knowledge/_index.md` → `pattern_*.md`
**Known gotchas**: `knowledge/_index.md` → `gotcha_*.md`
**Session history**: `sessions/session_[date]_*.md` (latest)

## Loading Strategy

### Priority Order
```
1. _status.md (always, ~200 tokens)
2. _context.md (if resuming/switching, ~300 tokens)
3. PLAN.md (if needed for context, ~500 tokens)
4. Current feature doc (~600 tokens)
5. Referenced plan sections (only if needed, ~400 tokens each)
6. Knowledge entries (search, don't read all)
7. External references (only during integration)
```

**Target**: <2,000 tokens to start most tasks

### Smart Loading

**DON'T load**:
- All features (load only current one)
- All knowledge entries (search index, load specific)
- All plan sections (load only referenced)
- Maintenance prompts (unless fixing framework)

**DO load**:
- _status.md (current state)
- _context.md (if resuming work)
- PLAN.md (overview if needed)
- Current feature doc
- Dependencies explicitly referenced

## Cross-References

**Follow links when**:
- Feature references plan section for rationale
- Feature depends on another feature
- Knowledge entry references related solutions

**Stop loading when**:
- Reference is tangential (note for later, don't load)
- You have enough context to proceed

## Search Methods

### By File Name Pattern
```bash
# Find feature
ls features/feature_[topic]*.md

# Find knowledge about auth
ls knowledge/*auth*.md

# Find recent sessions
ls -t sessions/ | head -5
```

### By Content
```bash
# Find docs mentioning "stripe"
grep -r "stripe" docs/

# Find all TODOs
grep -r "TODO" docs/features/

# Find gotchas about specific issue
grep -r "race condition" docs/knowledge/
```

### Using Indexes

- `_status.md`: See active documents for current work
- `_context.md`: See recent changes and feature status
- `knowledge/_index.md`: Search by keyword (don't read sequentially)
- `reference/_index.md`: Find external API docs

## When Lost

1. Read `_status.md` - Shows current focus
2. Read "Active Documents" section
3. Read `_context.md` for recent history
4. Follow links from there
5. If still unclear, read `PLAN.md` for full context

## Token Budget Awareness

**Each doc you load costs tokens**. Load minimally:
- Essential: _status + current feature = ~800 tokens
- With context: + _context + PLAN = ~1,600 tokens
- With plan detail: + 1 plan section = ~2,000 tokens
- Heavy load: + multiple refs = >3,000 tokens

Keep under 2,000 tokens for normal tasks.
