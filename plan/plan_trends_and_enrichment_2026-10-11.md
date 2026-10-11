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
