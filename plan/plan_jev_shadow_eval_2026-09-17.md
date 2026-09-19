# Plan: Jev (TypeSafe) shadow eval for dedup review — 2026-09-17

**Status:** shadow LIVE in prod since 2026-09-18 (see "Status 2026-09-19" below).
**Goal:** find out whether Jev can replace (or front-run) Haiku on the pairwise "same event?" dedup
review, and whether its price makes a wider similarity band / longer lookback worthwhile.
Haiku stays authoritative throughout; Jev is record-only.

## Measured baseline (prod, 14 days to 2026-09-17)

| Stage | Calls | Cost | Jev fit |
|---|---|---|---|
| `dedup_review` (0.70–0.85 band, pairwise yes/no) | 15,670 | $12.55 ($0.0008/call) | Yes — a Noul |
| `clustering_validate` (group split) | 151 | $0.49 | Possible as pairwise Nouls; no money in it |
| `clustering_normalize` (HyDE summaries) | 119 | $9.14 | No — generative |

- Jev: $0.042/M input tokens, output free, 1,200 req/min. A pair is ~450 tokens → ~$0.00002/pair (~40x cheaper), and it is off the dedicated Claude subscription quota.
- **Re-review waste:** "keep" verdicts are not persisted, so every kept pair is re-reviewed each run while either event is inside the 48h window: mean 6.45 reviews per pair (median 7, max 10). ~85% of `dedup_review` spend is repeat work. A verdict cache fixes this independent of Jev — **Mike's call, not yet changed.**
- Widened band 0.60–0.70: 27,117 candidate pairs in 12 days (~2,260/day). Haiku: ~$1.80/day even with a cache. Jev: ~$0.05/day.

## Jev constraints that shape the design (docs.typesafe.ai/model-jaggedness/jev-1.13)

- Dates are read as text, not ordered → compute chronology in code, pass `older_event` / `newer_event` + a plain-language `timing` sentence.
- Instructions are read literally; no multi-hop → positive phrasing, concrete examples in criteria. "Launch vs reaction to launch" is the case to probe.
- `jev-latest` floats → store the concrete response `model` per row (pin the spec, not the model).
- Ask a Noul (`same_event`) and a 3-level Score (`relation`: different / same story, separate occurrence / same occurrence) in ONE request; the middle Score level names our main failure mode.

## Phase 1 — offline benchmark (ready)

Files in `ai-news-aggregator/resources/jev_eval/` (no git):
- `export.sql` — read-only prod export; `build_dataset.py` — joins `pipeline.log` "haiku-kept" lines to pairs by title prefix.
- `dataset.json` — 2,224 Haiku-labeled pairs (1,959 no / 265 yes) + 27,117 unreviewed widened-band pairs. Caveat: tier1 text is as of export, not review time.
- `bench_jev.py` — `TYPESAFE_API_KEY=… python3 bench_jev.py` → 265 yes + 335 no + 200 widened; reports agreement (Noul and Score), calibration buckets, cascade sizing (share of pairs Jev is confident on + agreement inside it), latency, cost, and widened-band hits. `--dry-run` prints a request without a key. Expected cost: ~2 cents.
- Then: strong-model judge (Sonnet/Opus, thinking on, blind to which model said what) on ALL disagreements + a random sample of agreements (both-wrong check). Report → `outbox/`.

## Phase 1b — normalize-step augmentation (Mike's idea, 2026-09-17)

Have the normalize step (which sees the source lede) emit structured occurrence context so the
pairwise judgment becomes a literal comparison instead of a multi-hop inference.

- **Hard rule: new fields are NOT embedded.** The fingerprint prompt deliberately strips reactions and
  framing so sources converge ("Identify the UNDERLYING EVENT, not the document type"); `summary`
  stays byte-for-byte the same contract. New fields ride alongside in the JSON.
- Fields describe the OCCURRENCE, not the article genre (an analysis piece about a launch is still the launch):
  - `occurrence_type` enum: launch_release | deal_funding | partnership | policy_legal | incident | research | results_metrics | personnel | reaction_response | other
  - `stage` enum: rumored_or_in_talks | announced | shipped_or_closed | aftermath — targets the recurring "in talks" vs signed-deal confusion (XDOF stealth raise vs Series-B talks).
  - `anchor`: ≤8 words naming the prior occurrence this one responds to, else "" (e.g. "Anthropic Fable 5.1 launch").
- Roll-up: stored in `articles.metadata`; an event's context = majority over its founding articles.
- Consumers: Jev state (`older_event.kind/stage/anchor`), cluster validation, and a free code rule
  (same anchor + different stage ⇒ related-not-same, no model call).
- **Measure before shipping:** run the augmented prompt offline over the articles behind the benchmark
  pairs, re-run `bench_jev.py` with and without the fields. Ship to prod only if judged accuracy lifts,
  and A/B that `summary` output is unchanged (fingerprint drift would move every cluster threshold).
  Cost: ~15 output tokens/article on a $0.65/day stage — negligible.

## Related stories (finding)

- The site's "related" block = `/api/events/{slug}/related` = top-2 nearest `hyde_embedding`, no threshold,
  no time window, no notion of relation type. Nearest neighbours are often near-duplicates of the same story.
- The agent's `link_related_events` table is NOT read by the frontend, and `relationship_type` is unenforced:
  dozens of invented labels incl. full sentences (enum was related/follow_up/predecessor). Dead data today.
- Jev's middle Score level IS a related-stories classifier. Make the Score 4-level —
  different / same topic or company only / same ongoing story, separate occurrence / same occurrence —
  and every shadowed pair at level 2 is a typed related-story candidate; follow_up vs predecessor
  direction comes from dates in code. Shadow week evaluates this against cosine top-2 for free.
  Also a natural feed for the storylines engine spec (July 2026).

## Phase 2 — shadow week (after Phase 1 looks sane)

- Migration b24: `dedup_shadow_verdicts` (event ids, similarity, band, haiku_verdict, jev_noul, jev_score, jev_probs, resolved model, tokens, latency_ms, created_at).
- `pipeline/jev_client.py` (httpx, 10s timeout, fail-silent) called beside `_haiku_should_merge`; failures only increment a counter. No effect on merges.
- Jev-only, record-only: 0.60–0.70 band, and a longer recency window, to size what widening would catch.
- Usage logged to `llm_usage_log` (pipeline `news`, stage `dedup_shadow_jev`). Standard ruff + canary deploy.

## Phase 3 — end-of-week eval

Judged disagreement matrix, calibration, widened-band yield (judged), cost/latency. Likely candidate
outcome: cascade — Jev decides confident pairs, Haiku only sees the uncertain middle.

## Status 2026-09-19

- Deploy 1 live since 2026-09-18 00:11 UTC (app c354722): verdict cache + record-only Jev shadow, pinned jev-1.13.0. Canary PASS. First pass: 712 rows, all with Jev, 0 errors.
- Deploy 2 (Haiku prompt alignment) NOT shipped — dev A/B negative + would move the baseline mid-week. Patch in outbox.
- Bench-top report: `outbox/jev-vs-haiku-dedup-benchmark-2026-09-17.md`. Runbook: `app/deploy/runbooks/jev-release-benchmark.md`.
- Mike's framing: the pipeline's rules (cosine cutoffs at steps 4 and 6) exist because Haiku was too expensive to put at the article level. Jev removes that constraint. Dedup is the calibration step; clustering is the target.

## Timeline

| When | What |
|---|---|
| Fri 09-19 | Day-2 checkpoint: judge disagreements at 0.1/0.2/0.5 + 100 random <0.05 pairs; confirm cache skips. If low band clean → propose "Jev keeps <0.05, Haiku above". |
| Thu 09-25 | End-of-week eval (out-of-sample). Decide merge-side cutoff; cascade in dedup. |
| Week of 09-28 | Measure where duplicates come from (verdict table): step-6 cross-run near-misses vs step-4 same-batch splits. Build the bigger gray band as a SHADOW (record what Jev would join). |
| Week of 10-05 | Judge the clustering shadow → switch live. |
| Mid-Oct | Second gray band, same shadow → judge → switch pattern. |

## Further Jev candidates (validate each bench-top before building; ~200 real examples + blind judge)

Jev fails on multi-step reasoning and reads literally. The pattern that works: decompose into many literal
questions asked in one parallel request (or gate them), combine in code. Ranked by fit × value:

1. **Bullet-vs-source verification** (quality) — per bullet: "is this claim supported by the source text?" Closest to TypeSafe's citation-check cookbook. Try first.
2. **Category check** — Choice over the category enum from the summary; pre-fill or verify the agent's pick (a chronic tool rejection).
3. **Typed related stories** — per candidate pair: follow-up / predecessor / same topic / unrelated. Replaces cosine top-2; feeds the storylines engine.
4. **Skip pointless updates (step 7a)** — the only one with money behind it (Sonnet sessions). Whole question ("anything new?") is out of Jev's reach; decomposed = code splits the article into claims, per claim "is this stated in the event summary?", new = count. Validate the decomposition before building.
5. **Newsletter link triage** — per link: story / sponsor / navigation.
6. **Freshness gate at ingestion** — works only if code supplies dates and Jev judges framing ("reports a new occurrence vs re-covers old news").
7. **Score second opinion** — weakest fit (needs world knowledge/taste). Try last; expect it not to work.

Mike 2026-09-19: "may or may not be worth the effort, but certainly worth trying."
