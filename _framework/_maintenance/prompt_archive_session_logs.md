# Maintenance: Archive Session Logs

## Objective
Prevent unbounded session log growth by archiving old sessions and creating quarterly summaries.

**Run this**:
- End of each quarter (Q1: Apr 1, Q2: Jul 1, Q3: Oct 1, Q4: Jan 1)
- When sessions/ folder exceeds 50 files
- When sessions older than 6 months exist

## What You'll Do

### 1. Analyze Current Session Logs

Scan `docs/sessions/` for:
- Total session count
- Date range of sessions
- Sessions older than current quarter
- Sessions older than 6 months

**Report**:
```
Total sessions: [N]
Date range: [earliest] to [latest]
Current quarter (Q[N] [YEAR]): [count] sessions
Previous quarters: [count] sessions
Archival candidates (>6 months old): [count]
```

### 2. Group Sessions by Quarter

Organize sessions into quarters:
- Q1: January - March
- Q2: April - June
- Q3: July - September
- Q4: October - December

**Example**:
```
2024 Q1: 12 sessions (session_2024_01_15_*.md ... session_2024_03_28_*.md)
2024 Q2: 15 sessions (session_2024_04_02_*.md ... session_2024_06_30_*.md)
2024 Q3: 18 sessions (session_2024_07_05_*.md ... session_2024_09_29_*.md)
2024 Q4: 8 sessions (session_2024_10_03_*.md ... session_2024_12_20_*.md)
2025 Q1: 6 sessions (current quarter - do not archive yet)
```

### 3. Create Quarterly Summaries

For each COMPLETED quarter (not current quarter):

**Step 1**: Read all sessions from that quarter
**Step 2**: Use template: `/docs/_framework/template_SESSION_QUARTERLY_SUMMARY.md`
**Step 3**: Extract and synthesize:
- Major features completed or advanced
- Strategic decisions made
- Problems solved and lessons learned
- Knowledge documented (gotchas, solutions, patterns)
- Technical debt added/resolved
- Key metrics and progress

**Step 4**: Create summary file
**Naming**: `q[N]_[YYYY]_summary.md`
**Location**: `docs/sessions/q[N]_[YYYY]_summary.md`
**Examples**:
- `docs/sessions/q1_2024_summary.md`
- `docs/sessions/q2_2024_summary.md`
- `docs/sessions/q3_2024_summary.md`

**Token budget**: 800 tokens per summary (compress 10-50 sessions → single narrative)

### 4. Create Archive Directory Structure

```
docs/sessions/
├── archive/
│   ├── 2024/
│   │   ├── q1/
│   │   ├── q2/
│   │   ├── q3/
│   │   └── q4/
│   └── 2025/
│       └── q1/
├── q1_2024_summary.md
├── q2_2024_summary.md
├── q3_2024_summary.md
├── q4_2024_summary.md
├── session_2025_01_15_feature_x.md (current quarter - active)
├── session_2025_02_03_refactor_y.md (current quarter - active)
└── session_2025_03_20_launch_z.md (current quarter - active)
```

### 5. Archive Old Sessions

**Archive sessions from completed quarters**:

For each session older than current quarter:
1. Move to `archive/[YYYY]/q[N]/`
2. Add archive note at top of file:
```markdown
> **Archived**: [DATE] - See quarterly summary: [q[N]_[YYYY]_summary.md]
```

**Example**:
```bash
# Move Q1 2024 sessions
mv docs/sessions/session_2024_01_15_*.md docs/sessions/archive/2024/q1/
mv docs/sessions/session_2024_02_*.md docs/sessions/archive/2024/q1/
mv docs/sessions/session_2024_03_*.md docs/sessions/archive/2024/q1/
```

**Keep in root `sessions/`**:
- Current quarter sessions (active work)
- All quarterly summaries (q[N]_[YYYY]_summary.md)

### 6. Update References

**Check for broken links**:
- Quarterly summaries should reference archived sessions correctly
- If any docs reference specific old sessions, update paths:
  - Old: `sessions/session_2024_01_15_auth.md`
  - New: `sessions/archive/2024/q1/session_2024_01_15_auth.md`

**Update _status.md** if it references archived sessions

### 7. Verify Archive

**Checklist**:
- [ ] All completed quarters have summaries
- [ ] All sessions older than current quarter are archived
- [ ] Archive directory structure exists
- [ ] No broken references in active docs
- [ ] Quarterly summaries within 800 token budget
- [ ] Current quarter sessions remain in root sessions/

## Archival Policy

### Always Keep (Never Archive)
- Current quarter sessions (most recent 3 months)
- All quarterly summaries

### Archive After Quarter Completes
- Individual session logs from completed quarters
- Move to `archive/[YYYY]/q[N]/`

### Exceptions: Keep in Root
If a session is frequently referenced by active features/plan:
- Can keep in root with note: `<!-- Kept for frequent reference -->`
- Or update references to point to archived location

### Very Old Sessions (>2 years)
- Quarterly summaries are sufficient
- Individual sessions can be removed from git if:
  - Quarterly summary created
  - No unique information lost
  - Git history preserves original

## Report Format

### Archive Summary
```
Quarter: Q[N] [YEAR]
Sessions archived: [count]
Quarterly summary: q[N]_[YYYY]_summary.md
Token count: [N]/800 tokens
Archived to: docs/sessions/archive/[YYYY]/q[N]/
```

### Sessions Remaining
```
Current quarter (Q[N] [YEAR]): [count] sessions (not archived)
Quarterly summaries: [count] files
Total sessions in root: [count]
Total sessions archived: [count]
```

### Space Saved
```
Before archival: [N] sessions in root
After archival: [M] sessions in root + [K] quarterly summaries
Token reduction: [before] → [after] tokens for session context
```

## Success Criteria

- [x] All completed quarters have summaries
- [x] Sessions archived by year/quarter
- [x] No information lost (summaries capture key points)
- [x] Current quarter sessions easily accessible
- [x] Quarterly summaries within token budget
- [x] Archive structure organized and scalable

## Notes

- Run at end of each quarter (April 1, July 1, October 1, January 1)
- Current quarter = last 3 months, don't archive yet
- Quarterly summaries replace need to read individual sessions
- Archive preserves details if ever needed
- Git history always preserves original sessions
- Token savings: 50 sessions × 600 tokens = 30,000 → 800 tokens (97% reduction)

## Example: Archiving Q4 2024

**Date**: January 1, 2025 (Q4 2024 is now complete)

**Actions**:
1. Read all `session_2024_10_*.md`, `session_2024_11_*.md`, `session_2024_12_*.md`
2. Create `docs/sessions/q4_2024_summary.md` (synthesize 18 sessions → 800 tokens)
3. Create `docs/sessions/archive/2024/q4/`
4. Move all Q4 2024 sessions to archive folder
5. Add archive note to each moved session
6. Verify no broken links

**Result**:
```
docs/sessions/
├── archive/
│   └── 2024/
│       └── q4/  (18 sessions archived)
├── q4_2024_summary.md (NEW)
└── session_2025_01_02_*.md (current quarter - kept)
```

**Token savings**: 18 sessions × 600 tokens = 10,800 tokens → 800 tokens
