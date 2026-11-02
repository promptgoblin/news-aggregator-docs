# Plan: Trend engine + event enrichment (for a later agent)

---
type: plan
status: ready-for-pickup
complexity: C3
tags: [trends, enrichment, tags, storylines, scoring]
depends_on: [closed tag vocabulary (app commit 994950f + backfill), plan_trend_enrichment_research_2026-10-11.md]
last_updated: 2026-10-11
author: Claude (session 43) from Mike's direction
---

**Read first:** [plan_trend_enrichment_research_2026-10-11.md](plan_trend_enrichment_research_2026-10-11.md) — the
enrichment schema, the momentum formula, the backtest gate, costs. This page is the wrapper: intent, what already exists,
build order, and the decisions Mike still owns. Nothing here is built; Mike asked for a plan only.

## Intent (Mike, 2026-10-11)
- "Historical trends will be valuable over time." A momentum / what's-hot index over themes, companies, models, products,
  people — from OUR published events (frequency, sources, scores, sentiment, "what it means"), not raw web volume.
- Uses: a public trending/"pulse" index + storyline pages ("part of X"); historical charts; a BOUNDED input to the
  importance scorer (the rubric's BUZZ rule: a 6 can become a 7, never above the class ceiling, never a 9).
- Worked example: Jev launches → competitors flood in → Jev posts first-week revenue. Each later story matters more
  because of the hype, and the index should show the wave.

## What already exists (as of 2026-10-11)
| piece | state |
|---|---|
| Closed tag vocabulary: 43 themes (code) + entity registry with aliases + roles (theme/subject/mentioned) in `event_tags`; proposals queue with originating events | app commit 994950f; deploy + Haiku backfill of ~6.5k events in progress (session 43) |
| Scorer labels (story_class, gate, class_ceiling, passes_8_test) | computed in `create_event` (apply_score_rules) but NOT persisted — step 0 below |
| Sentiment (reactions, stance, voices) | `events.sentiment_passes`; only on 8+ plus 4 best 7s per run — a function of score, so it can modify the index but must never feed the scorer |
| Related events / dedup verdicts via Jev | `event_related_picks`, `dedup_review_verdicts` — "same event?" is validated; "same storyline?" is not |
| Storylines engine | docs/features/storylines.md (planning); the trend layer is its input |
| Volume facts | published events/month 511 (Mar) → 1,524 (Sep): raw counts are invalid, use share of daily coverage; weekends ≈ 35-40% of weekday volume; 21% of events merged away; 77% single-source; 9.5% have a first-party article |

## Build order (from the research doc; S/M/L)
0. **Persist the scorer's labels** on events (`story_class`, `gate`, `class_ceiling`, `passes_8_test`, `raw_score`) — S.
   Every day without it is history that cannot be recovered. (Recommended to do immediately; Mike to confirm.)
1. **Enrichment fields in the tagger's Haiku call** (+~$0.001/event): `arc_role` (new | follow-up | satellite),
   `action` (shipped | closed | ruled | announced | reported | rumored), `is_prospective`, `claim_basis`
   (first-party | reporting | rumor), `jurisdictions`, numeric facts (amount/count/version) — M. Backfill ~$35-50 in nightly chunks.
2. **Daily aggregation**: per term (theme/entity) per day: event count, share of day's mass, weighted score, source
   diversity, first-party count, reaction count — materialized nightly; retain forever (small) — M.
3. **Momentum**: ln(EWMA share ÷ baseline share over days 15-90) with a prior; "trending" gated by a Poisson burst z-test,
   diversity (≥3 events, ≥2 outlets), single-event dominance, hype (reposter/farm share) — M.
4. **Backtest gate** (ship gate for anything public): 6-month replay must surface the Jev wave, the Sep "agents going
   rogue" wave and the California AI-law signings, with controls; then 3 weeks of Mike reviewing the top-10 risers — M.
5. **Public index + storyline hooks** ("part of X"; storyline membership judged by Jev only after a ~200-pair gold set) — L.
6. **Scorer hook** (optional, last): one TREND line in the SCORER payload, subject entities only, max +1 (6→7), 2 weeks in
   shadow before live. Scores feed the trend, so anything larger is a feedback loop — S.

## Decisions Mike owns
1. Persist scorer labels now (step 0) even though "no trend work yet"? (Recommended: yes — tiny, prevents data loss.)
2. Jev for "same storyline?" needs a ~200-pair hand-labeled gold set before it gates public storyline pages.
3. A Fable-written weekly "why it's hot" narrative conflicts with the rule that reader-facing generation goes through
   DeepSeek — keep it as an internal DM unless approved for public use.
4. Which themes/entities are public on the index page vs internal only.

## Costs
Steady state ≈ $0.20-0.35/day (Haiku enrichment + nightly aggregation + Jev). One-time backfill ≈ $35-50 (or free on a
subscription-backed SDK run, as the tag backfill is doing).

## Definition of done for the pickup agent
- Steps 0-4 built with tests; backtest report in `docs/outbox`-style markdown showing the three known arcs; no public
  surface until Mike signs the 3-week review; scorer hook stays off by default.

## Implementation notes (2026-11-02) — step 1, enrichment layer

Built on app branch `feat/trend-enrichment` (from main 184e57d). Step 0 (scorer labels) already lives in
`events.scoring` since app commit 0d4f8a5 and is NOT duplicated; the enrichment fallbacks read `story_class` from it.

**Code:** `src/ai_signal/enrichment.py` (enums, validation, fallbacks, source_stats / buzz arithmetic, async
upsert helpers), `src/ai_signal/models/enrichment.py` (`EventEnrichment`, `EventNumber`), migration
`alembic/versions/b32_event_enrichment.py` (revises b31), `agent/runbooks.py` `ENRICHMENT_SPEC` (part 4 of the
TAGGER prompt, shared with the backfill), `agent/tools.py` `_apply_enrichment` (create_event / update_event),
`pipeline/dedup.py` `reassign_event_children` (survivor source_stats), `pipeline/sentiment.py` (buzz upsert),
`scripts/backfill_enrichment.py`, `tests/test_enrichment.py`.

**Tables**
| table | columns |
|---|---|
| `event_enrichment` (PK `event_id` FK events CASCADE) | `arc_role` text, `action` text, `is_prospective` bool, `claim_basis` text, `jurisdictions` text[], `source_stats` jsonb, `buzz` jsonb, `enrichment_version` int NOT NULL, `enriched_at` timestamptz, `enrich_model` text |
| `event_numbers` (id serial) | `event_id` FK events CASCADE, `kind` text, `value` numeric, `unit` text, `currency` char(3), `as_of` date, `entity_slug` text, `is_prospective` bool, `claim_basis` text, `key_fact_idx` int; index (entity_slug, kind, as_of) |

`source_stats` = `{distinct_sources, distinct_domains, types: {primary, publication, newsletter, aggregator, blog},
has_primary}` (types count DISTINCT sources; `social` folds into aggregator; aggregator = `sources.source_type =
'aggregator'` or the legacy names TechMeme / Google News * / Hacker News * / Reddit *; domain = registrable domain of
`source_metadata.original_url` > `resolved_url` > `url`, hosted platforms such as substack.com keep the author label).
`buzz` = `{reactions, stance_pos, stance_neg, stance_mixed, stance_other, notable_voices, sentiment_score, passes,
pass2_shift, latest_pass_at}` from the LATEST pass in `events.sentiment_passes`; NULL until a pass exists.

**Enums (code, `ai_signal.enrichment`)** — arc_role: new | development | reaction | satellite | retrospective.
action: launch_model | launch_product | open_weights | raise | acquire | partner | compute_deal | earnings_metric | sue |
rule | sign_law | propose_law | regulator_action | hire_depart | incident | research_result | deploy_adopt | statement.
claim_basis: self_reported | third_party_data | independent_verification | official_record. number kinds: arr | revenue |
valuation | raise | acquisition_price | users | tokens_per_day | compute | parameters | benchmark | price | headcount |
context_window | downloads | market_cap | capex | contract_value | fine | share_percent | count | other. jurisdictions:
`^[A-Z]{2}(-[A-Z0-9]{1,3})?$` (US, US-CA, EU, CN), max 6. Off-list values are dropped and logged to `pipeline_logs`
(stage `enrichment`, decision `reject`); the event is never failed.

**Version:** `agent/config.py` `ENRICHMENT_VERSION = 1`. Bump when enums, the prompt block or the arithmetic change
meaning; never chart across versions without re-running the backfill over the old range.

**Fallbacks** (when Haiku omits a field): arc_role = `satellite` if `events.scoring.story_class == 'satellite'`,
else `development` when the cluster was attached to an existing event (update_event path, or create_event with
`related_event_id` / `match_confidence` in an article's source_metadata), else `new`; is_prospective =
`story_class == 'prospective'`. A row written without any Haiku answer keeps `enriched_at` NULL so the backfill
revisits it. Re-enrichment on updates: the EI runbook tells the orchestrator to re-run the TAGGER and pass
`enrichment` to update_event only on material updates (the ones recorded with a `summary_fact`); update_event always
recomputes source_stats.

**Backfill** (do not run from dev01; the agent container holds the credentials and shares the 5-hour quota with the
cron runs):
```
docker exec -u pipeline ai-signal-agent bash -c 'cd /app && PYTHONPATH=/app:/app/src \
  python -m scripts.backfill_enrichment --arithmetic-only'               # free: source_stats + buzz for all active events
docker exec -u pipeline ai-signal-agent bash -c 'cd /app && PYTHONPATH=/app:/app/src \
  python -m scripts.backfill_enrichment --dry-run --limit 8'             # plan + one sample payload, writes nothing
docker exec -u pipeline ai-signal-agent bash -c 'cd /app && PYTHONPATH=/app:/app/src \
  python -m scripts.backfill_enrichment --limit 500 --batch 4 --sleep 2'  # one nightly chunk, oldest first
```
Flags: `--limit`, `--since YYYY-MM-DD`, `--batch` (events per Haiku call), `--sleep`, `--max-cost`, `--model`,
`--dry-run`, `--arithmetic-only`. Resumable by construction (selects `enriched_at IS NULL`). Prints running SDK cost
and $/event. Not yet run as of 2026-11-02.

## Implementation notes (2026-11-02) — steps 2-4, aggregation + momentum + backtest

Built on app branch `feat/trend-index` (worktree off main 184e57d). Not deployed, no migration run, no cron installed.

**Module layout** (`src/ai_signal/trends/`, pure compute, no DB):
- `constants.py` — every weight/window, `CALC_VERSION = 1`. Bump it when any value or formula changes, then
  `--rebuild-all`.
- `mass.py` — `EventRec`/`ArticleRef`/`EnrichmentRec`/`KeyRef`; w(e,k) = role × imp × nov × hype × buzz / √fanout;
  activity weights; the per-source cap (`source_cap_factors`: one source ≤ max(40%, 1/n) of the key's trailing-7d mass,
  single-source windows uncapped — the domain gate already blocks them).
- `series.py` — EWMA (half-life 4d), baseline (d-90…d-15; pre-series days are not data, pre-key days are zero),
  prior (0.5 events/week at imp 1.0 over the 28d mean daily total), momentum, Poisson burst z, NEW flag.
- `gate.py` — §2c gate; returns trending/hype/failure reasons + window stats (stored in `trend_daily.flags`).
- `compute.py` — `compute_trends(TrendInput, start, end)` → `trend_daily` rows, day totals, activity rows, full
  per-key series. `keys_from_tags` (role theme → theme key; subject|mentioned → entity key), `add_jurisdiction_keys`
  (from enrichment), `storyline_keys_hook` (hook only — storylines not built).
- `loaders.py` — `build_input(events, event_tags, tags, articles, sources, event_updates, event_merges, enrichment)`
  from plain row dicts: the DB job and the CSV backtest share it.
- `ranking.py` — `current_ranking(db, key_type, …)` replaces the planned `mv_trend_current` view; `record_snapshot`.
- Models `src/ai_signal/models/trend.py`; migration `alembic/versions/b33_trend_tables.py` (revises
  `b32_event_enrichment`): `event_activity`, `trend_daily`, `trend_day_totals`, `trend_snapshots`.

**Deliberate choices beyond the research text:** momentum is computed for NEW keys too (the prior makes it finite) and
stored; `flags.new` tells consumers to show "NEW" instead of "×N" — without this the Jev test ("NEW by Sep 16 AND top-5
by momentum in the Sep 14 week") is self-contradictory. `flags.warmup` marks days whose baseline window has < 30
in-series days (the first ~45 days of history); tests ignore them. Merged-away events are excluded throughout; a merge
is activity on the survivor on `merged_at`. Activity mass carries the role weight (mentioned 0.25) but no fanout.
Missing enrichment ⇒ nov = hype = buzz = 1.0, except `scoring.story_class` satellite → 0.4 and prospective → 0.6.

**Run:**
```
python -m scripts.trend_nightly                   # trailing 30 days, idempotent (delete+insert the window)
python -m scripts.trend_nightly --rebuild-all     # after a CALC_VERSION bump
python -m scripts.backtest_trends --export-dir resources/trend_backtest_export_<date>/   # or --db
```
The backtest writes `outbox/trend_backtest_<date>.md` with the §2e table and weekly top-10 movers.

**Proposed cron line** (deploy/cron/pipeline-cron, NOT installed — Mike's call after the migration):
```
30 23 * * * pipeline cd /app && PYTHONPATH=/app:/app/src /usr/local/bin/python -m scripts.trend_nightly >> /var/log/pipeline/trends.log 2>&1
```

**Backtest 2026-11-02 (no enrichment rows → all verdicts provisional):** Jev PASS (NEW Sep 15; TypeSafe #5 in the
Sep 14 week, #2 in the Sep 28 week; 15 co-mention edges). Duplicate injection PASS (Δmomentum 0.06 < ln 1.5).
Rogue-agent FAIL at theme level: `safety-incidents` runs ~10 events/week all August, so the week of Aug 31 is ×1.95
(z 2.0), just under the gate; it trends 6 days in the Sep 28 week; two false days Jul 30-31. The 4-event regex wave is
a sub-theme the closed vocabulary cannot see. California not evaluable (no `US-CA`); proxy `regulation-us` peaks ×2.4
(z 8.2) on Sep 20 and is back under ×1.5 by Oct 13. Agents control FAIL: share 10.9% (Apr) → 14.8% (Oct), +36% (raw
count ×3.5) — the Aug–Sep source expansion changed the topic mix (§7 "the corpus is the instrument"). Flat keys: Microsoft
and enterprise-adoption 0 burst days; Nvidia one 11-day episode around Aug 26 earnings (the literal ≤2 days/month rule
cannot hold with a 7-day-window z). Stability FAIL on momentum (Spearman 0.54, set overlap 79%) but 0.93 on heat and 0.81
for themes — rank the public page by heat (or weekly mean momentum) and use momentum for the gate.
