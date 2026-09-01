# Gotcha: Months-Old Story Republished as Breaking News (2026-09-01)

## What Happened

The 14:03 UTC Grok sweep (prompt: "top AI stories from the last 8 hours")
returned the original WSJ "Meta buys AI startup Manus for more than $2B"
story — months old, with a truncated URL ending in a dangling hyphen and no
date. It went through every stage and landed at the top of the feed as a
score-9 top story, "7h ago". Mike (and any reader) read it as a new deal. The
real story had been blocked by China in April and unwound by August.

## Root Cause — six date-blind layers in a row

1. **Grok sweep** never captured a publish date, so `published_at` was NULL and
   nothing could age-check the story.
2. **WSJ returned 401** → curator-summary fallback kept the story alive (by
   design since 2026-07-27: "never drop curated stories").
3. **Event matching** only considers events with `last_updated_at` in the last
   14 days. The live Manus saga event had absorbed articles through mid-August
   via dedup auto-merges, but merges reassign articles without touching
   `last_updated_at` (still April 28) → invisible → new event.
4. **Event Intelligence** had no clock. Neither the orchestrator dispatch nor
   the SCORER prompt stated today's date; the research digest (WSJ/Reuters/
   AP/TechCrunch coverage of the *original* announcement) read as fresh.
5. **Dedup Haiku review** was told "related but distinct events (launch vs
   reaction) are NOT the same" and dutifully kept "Meta acquires Manus" apart
   from "China blocks Meta's Manus acquisition" (sim 0.759).
6. **Feed** shows `first_seen_at` → "7h ago".

The same story nearly recurred on 2026-08-10 (Grok returned an X-post recap);
that copy happened to score above the auto-merge threshold and vanished into
the saga event, so nobody noticed.

## Fix (app commits 2026-09-01)

- `grok_sweep.py`: prompt asks for `PUBLISHED_DATE` (YYYY-MM-DD) per story;
  parsed into `published_at`; stories older than `MAX_STORY_AGE_DAYS` (3) are
  dropped at parse time. Undated stories are kept (losing a curated story is
  worse); future dates are treated as hallucinated (date discarded, story kept).
- `grok_research.py`: reply carries `EVENT_DATE`; tool result now includes
  `event_date`, `days_old`, `stale` (> `STALE_EVENT_DAYS` = 14).
- `clustering.py`: "recently active" = `last_updated_at` in window OR an
  article ingested in window (`EXISTS` on articles), so merge-fed sagas stay
  matchable.
- `dedup.py`: pairs are presented chronologically (OLDER/NEWER with dates); a
  third verdict `stale` merges the newer copy INTO the older event without
  adopting its score (`_merge_event(adopt_score=False)`, method
  `haiku-stale`, counter `stale_merged`).
- Runbooks: SCORER gets `TODAY (UTC) is <date>` (`TODAY_SENTINEL` substituted
  in `build_subagents`) and a hard rule — stale re-coverage scores 3;
  EVENT_INTELLIGENCE gets a STALE RE-COVERAGE section with the skip-log shape
  (`decision="skip — stale re-coverage (...)"`, which the record_pipeline_log
  flip contract already handles). `get_cluster_summary` returns `today` and
  per-primary-article `published_at`; the dispatch message states the date.

## Lessons

- **LLM stages need a clock.** An agent that cannot see today's date cannot
  tell old from new, no matter how good the prompt. Inject the date wherever a
  recency judgement is made.
- **Every ingestion path must carry a date or be gated.** RSS has one; the
  Grok/TechMeme/newsletter fallback paths did not. If a source cannot supply a
  date, ask the model for one and gate on it.
- **"Recently active" must include merges.** Any bookkeeping that attaches
  children without bumping the activity timestamp silently ages an event out
  of the match window.
- **A dedup prompt that only knows "same vs distinct" cannot express "old
  news".** Give it the chronology and a third answer.

## When NOT to apply

Do not widen the 14-day match window globally or bump `last_updated_at` on
merges: the feed shows `last_updated_at` as "Updated Nh ago" for events with
updates, so a merge-driven bump would surface stale sagas as freshly updated.
