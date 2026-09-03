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
- `dedup.py`: pairs are presented chronologically (OLDER/NEWER with dates).
  **A third verdict, `stale`, was tried and REMOVED two days later** — see
  "What went wrong with the dedup layer" below.
- Runbooks: SCORER gets `TODAY (UTC) is <date>` (`TODAY_SENTINEL` substituted
  in `build_subagents`) and a hard rule — stale re-coverage scores 3;
  EVENT_INTELLIGENCE gets a STALE RE-COVERAGE section with the skip-log shape
  (`decision="skip — stale re-coverage (...)"`, which the record_pipeline_log
  flip contract already handles). `get_cluster_summary` returns `today` and
  per-primary-article `published_at`; the dispatch message states the date.

## What went wrong with the dedup layer (2026-09-03)

The `stale` verdict ("the newer event is re-coverage of the older one's
story → merge it into the older event") looked right for the Manus case and
was wrong almost everywhere else. In two days Haiku applied it to 47 pairs:
the Fable 5.1 launch (5 sources, score 9) vanished into an 82-day-old
"leaked system prompt" story, the Gemini 3.8 Flash release into a
two-month-old LM Arena sighting, the OpenAI Astra delay into an unrelated
Anthropic story (taking the editor's score adjustment with it), an Uber
robotaxi launch into a cab-driver reaction, an acquisition into an
earnings report. A one-turn, no-thinking yes/no reviewer cannot judge
"is the newer one a NEW development" — it pattern-matches on shared
entities. **Over-merging hides fresh news, which is as damaging as showing
stale news.** Reverted with `scripts/revert_stale_merges.py` (articles
back by cluster including auto-merge subtrees, editor adjustments back by
resulting score + window, `event_merges` rows kept as `reverted:`
provenance, invariant ignores them). Dedup is yes/no again; stale news is
stopped upstream (sweep date gate, EI staleness skip, research event_date).

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
- **Do not ask the dedup reviewer to judge staleness.** It cannot tell
  "re-coverage" from "new chapter"; give it the chronology for context, but
  keep the verdict yes/no and stop stale stories before they become events.

## When NOT to apply

Do not widen the 14-day match window globally or bump `last_updated_at` on
merges: the feed shows `last_updated_at` as "Updated Nh ago" for events with
updates, so a merge-driven bump would surface stale sagas as freshly updated.
