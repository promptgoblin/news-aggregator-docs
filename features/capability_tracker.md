# Feature: Releases (capability tracker) and Guides

---
type: feature
status: live
complexity: C3
tags: [capabilities, changelog, docs-diff, jev, grok, rss, frontend]
depends_on: [rss_feeds, sentiment_reactions, forum_auth]
required_by: []
---

## User Intent

### Goal
Keep daily users of AI coding tools (Claude Code, Codex, Cursor, Windsurf) and frontier models current on
*what the tools can do now*: every material new feature, change, removal and model release, distilled into
a quick look (what it is, why it matters, when and when not to use it, how to use it, examples) plus what
practitioners found in the first week. A backfilled corpus makes the tab a reference; the feed and RSS are
the diff. Same mechanics as the news feed so it is one product with two tabs.

### Success Criteria
- A feature that ships only in docs (like `/security-review` did) appears as a change within a day.
- Jev + Haiku gating keeps the feed to ~10 notable changes a week for Claude Code with no bug fixes or UI
  polish in the notable tier.
- Every sentence in an entry is traceable to a vendor source line or an attributed practitioner post. No
  invented flags, settings or behaviour; "Not documented by the vendor" where the source is silent.
- Notable changes and model releases carry an "In practice" section by day 7 when discussion exists.
- Skim / summaries / deep dive, swipe, bookmarks, read marks, filters, search and RSS all work on the tab
  exactly as on News, light and dark, mobile.
- Steady-state cost ≈ $3/wk Grok, < 1% of the weekly Sonnet quota.

### User Flow
1. User opens the Releases tab, filters to the tools they use (filters persist as saved defaults).
2. Rows show product, version, kind, title; summaries mode shows the skim bullets.
3. Tapping opens the deep dive; swipe moves through changes; bookmark saves for later.
4. Day 3 and day 7: the entry gains an "In practice" section and an Updated badge, re-surfacing it.
5. User subscribes to the product RSS feed in their reader to get only that tool's diff.

## Status: Live for the six tools; model families dark
**Started**: 2026-10-11
**Last Updated**: 2026-11-11

Deployed 2026-11-11 (app 5f616d5, migration b35). The site is now News | Releases | Guides.
The design that shipped is the "FINAL DESIGN (2026-11-11)" section of the plan; it supersedes the
October text and the success criteria above where they differ (Jev is a noise filter, an editor pass
scores, no Haiku gray band).

## References
- Plan + API contract: [plan/plan_capability_tracker_2026-10-11.md](../plan/plan_capability_tracker_2026-10-11.md)
- Vetting report and backtest: workspace `outbox/capability-tracker-vetting/`
- 20 sample entries + 30-day change table from the dev run: workspace `outbox/releases-sample-entries-2026-11-11.md`
- Related: [sentiment_reactions.md](sentiment_reactions.md), [rss_feeds.md](rss_feeds.md)

## Implementation

### Pipeline (`src/ai_signal/releases/`, runner `python -m ai_signal.releases.run`)
| Stage | Module | What it does |
|---|---|---|
| poll | `poll.py`, `parsers.py`, `trackers.py`, `fetch.py` | 13 vendor sources through load.party: changelogs, GitHub releases, RSS, and docs snapshots (`llms-full.txt` where it fits under load.party's 5 MiB body cap, per-page index with hot pages for Claude Code). Docs edits become `docs_deltas`. |
| gate | `gate.py` | Jev (TypeSafe) per line: `kept = material >= 0.60`, plus audience and surface. Noise filter only. |
| editor | `editor.py` | One Sonnet call per batch of 25 kept lines: groups lines into changes (merging into changes of the last 60 days), scores 1-10 on the news scale, sets kind / audience / surfaces. Docs-only changes are capped at 5 until a changelog line confirms them. |
| writer + QC | `sources.py`, `writer.py`, `qc.py` | For changes scoring >= `WRITE_MIN` (6) released in the last 90 days. Sources are collected in code (the change's lines, linked docs deltas, docs sections found by identifiers or page title, vendor launch posts from linked news events). One Sonnet call writes the entry; validators check quotes and identifiers against the sources; a blind Haiku QC call flags unsupported claims; one rewrite; still failing means not shown. At most 2 attempts per change. |
| reactions | `reactions.py` | Grok x_search at T+3 and T+7 for score >= 8 or model releases; "In practice" is shown only with 3 or more valid posts. Daily cap $2. |
| register | `register.py` | News events tagged as a product launch are matched to changes by Jev (0.70); unmatched model launches seed a change. Completeness check. |
| digest | `digest.py` | Weekly per-product digest page; forum DM behind `RELEASES_DM_ENABLED`. |
| alerts | `alerts.py` | Source failures, writer reject share, cost, stage failures (DM to the admin through the news alert path). |

All LLM calls are single grounded calls through `releases/llm.py::ask_json` (no tools, no agent loop,
isolated from account connectors). Run record: `pipeline_logs` rows with `stage='releases_run'`, not
`pipeline_runs` (news consumers read "latest row" there). Advisory lock 43.

### Data model
Migration `b35_release_tracker`: tracked_products, release_sources, release_entries, docs_pages,
docs_deltas, release_changes, release_change_updates, release_digests, user_release_bookmarks,
user_release_reads, release_register.

### API and frontend
`src/ai_signal/api/releases.py` (list, detail, products, timeline, digests, RSS, sitemap, user
bookmarks/reads, admin score/hide/rewrite). Pages: `/releases`, `/release/[slug]`,
`/releases/[product]`, `/releases/digest/[slug]`. Only products with `tracked_products.is_live` are
shown or written; the rest are polled so their history is ready.

### Guides
Markdown with frontmatter in `frontend/content/guides/<slug>.md`, rendered at build time
(`frontend/src/lib/guides.ts`), PDFs in `frontend/public/guides/<slug>/`. Pages `/guides` and
`/guides/[slug]`. The old `promptgoblins.ai/library/...` pages and PDFs 301 to the new URLs (exact
locations in the forum nginx conf; other files under /library/ are still served statically). To update a
guide: edit the markdown, bump version and changelog, add the versioned PDF, deploy the web container.

## Configuration
Env (agent container, `.env.prod`): `RELEASES_ENABLED` (cron does nothing without it),
`RELEASES_DM_ENABLED` (weekly digest DM), and optional `REL_*` overrides for every constant in
`releases/config.py` (`REL_WRITE_MIN`, `REL_WRITER_BUDGET_USD`, `REL_RUN_COST_ALERT_USD`, ...).
Cron: daily 05:10 UTC, digests Monday 07:10 UTC (`deploy/cron/pipeline-cron`), log `logs/releases.log`.

## Measured (dev run, Claude Code, 2026-11-11)
- 8,933 changelog lines, 1,298 kept by Jev; last 90 days: 441 kept -> 337 changes (80% single-line).
- Dev scores (older model): 9: 6, 8: 5, 7: 71, 6: 105, 5: 92, <=4: 59. Prod first run (2026-11-11, 17 min, $3.06): 442 kept lines -> 315 changes; 9: 5, 8: 4, 7: 10, 6: 79, 5: 96, <=4: 121. `WRITE_MIN` is 6 (98 entries).
- Writer: about $0.20 per entry attempted, about 1 in 5 hidden by QC on the first day. Editor: about
  $0.56 per backfill batch, about $0.20 on a normal day. A no-news daily run makes 0 LLM calls.

## Edge Cases & Considerations
- load.party truncates bodies at 5 MiB without an error; `fetch.py` raises on a body at the cap.
- Vendors edit docs continuously; a docs edit is not a release (docs-only score cap).
- A round-up post grouped into several changes points at the highest-scored one; the others are
  listed in `release_entries.editor_note`.
- If a releases run overlaps a news run, the news cost-anomaly rule counts its LLM spend.

## Open
- Model families: the register seeds a change with the news headline as its title and score 9, and some seeds are rumours or availability stories. Seeds need an editor pass (title, score, drop) before `is_live` is set for the three families (tried and reverted 2026-11-13).
- Admin feedback notes (`GET /api/admin/releases/feedback`) are read in bulk and distilled into prompt rules.
- Grouping granularity: families of small API lines (eight separate "Mod ..." changes) are not folded.
- Follows and alerts per product (v2); long-form derived guides.
