# Feature: Storylines (living-thread pages + the synthesis engine)

---
type: feature
status: planning
complexity: C3
tags: [storylines, synthesis, discovery, seo, moat, engine]
depends_on: [production_deployment]
required_by: [email_digest, catch_me_up, semantic_ask]
last_updated: 2026-07-08
author: mike + Claude (co-founder session)
---

> **BUILD AGENT (Opus):** implement to **User Intent**, not the letter of each step. Read the whole doc first — the Gotchas section changes earlier decisions. `[VERIFY]` = re-check at build (my knowledge cutoff is Jan 2026).
>
> **The big idea in one line:** a *storyline* is a **persistent, blog-format "living page"** that tracks one ongoing narrative over time (e.g. "the OpenAI–NYT copyright suit", "the GPT-5 arc", "the AI-datacenter buildout"), updating as new events join it. Underneath, it's a **synthesis-over-time engine** that reuses the curated/scored event corpus — and that engine is the shared substrate for `email_digest` (topic-follow emails), catch-me-up, "what happened with X" search, and social-post drafts. **Build the engine once; expose it on many surfaces.** This is the biggest moat-deepener in the roadmap: it upgrades "event intelligence" into "narrative intelligence," which is genuinely hard to replicate because it requires the curated+scored corpus you already have.

---

## 1. User Intent

### Goal
Let a reader **follow a thread, not a firehose.** Instead of scrolling isolated events, they land on a living page for a topic that says *here's the whole story so far, updated,* with a timeline of the events that make it up — each linking back to the full event. It's the difference between "56 headlines about OpenAI" and "the OpenAI story, told, and kept current."

### Success Criteria
- Related events over time are **automatically grouped** into a storyline (no manual curation required to keep it running).
- Each storyline has a **public blog-format page**: a current synthesized narrative at top + a reverse-chronological timeline of its member events, each linking to the event.
- The narrative **updates automatically** when a new event joins, and **freezes** when the thread goes quiet (no wasted re-synthesis).
- Events show a **"part of: [storyline]"** link; storylines are **browsable** (index by activity/category).
- The same engine can answer **"what happened with X"** and generate **catch-up** / **social** / **topic-email** outputs (later phases).
- Runs on **DeepSeek via `llm_client.py`** (user-facing → must not use the Claude subscription), synthesizing only-on-change → **cheap**.

### Non-Goals (v1)
- No user-authored/edited storylines (fully automatic; admin merge/split only).
- No real-time updates (batch, after the pipeline).
- The "ask/what-happened-with-X" query UI and social drafts are **later phases** (§9) — v1 is auto-detection + pages.

### User Flow
1. A reader clicks "part of: The OpenAI–NYT suit" on an event (or finds it in the storylines index / via search).
2. They read the synthesized "story so far" and skim the timeline of events, tapping any for the full detail.
3. (Later) They **follow** it → get an email/notification when it updates.

---

## 2. Where this content is served (positioning — answers Mike's question)

The storyline **is the on-site blog-format page** — that's home base. The *same synthesized narrative* is then cheaply repurposed:
- **On-site storyline pages + index** — primary surface. Evergreen, self-updating → **SEO gold** (indexable pages that keep getting fresher) and the core utility ("curated AI news you can *follow*, not raw web").
- **"What happened with X" search / ask** (§9, later) — a query returns the relevant storyline(s), synthesized.
- **Topic emails** — "follow" a storyline → digest when it updates. This is the topic-scoped flavor of `email_digest.md`.
- **Social posts** (later) — auto-draft "here's what happened with [storyline] this week" threads for X/LinkedIn → marketing/distribution.
- **Catch-me-up** — "what you missed" = updates to storylines you follow + new storylines since your last visit.

One engine, five surfaces. Don't build those as separate features — build the storyline engine, then the outputs are thin adapters over it.

---

## 3. Architecture Overview

```
NEW JOB  agent/storylines.py   [advisory lock id 46; registry: news=42, old-events=43, audio=44, email=45, storylines=46]
   runs AFTER the news pipeline (reads the events it produced), as its own job (independent failure domain; off the Claude-sub path)
     │
     ├─ 1. CANDIDATES   for each new/updated event: find candidate storylines (event hyde_embedding
     │                  cosine vs storyline centroid + member events) and recent un-storylined events.
     ├─ 2. ASSIGN       LLM judge (DeepSeek via llm_client.py): belongs to storyline X? extends/starts a
     │                  new one with these events? or standalone? (mirror the dedup/cluster-validate judge.)
     ├─ 3. PROMOTE      a group becomes a PUBLIC storyline only once it has >= MIN_EVENTS over >= MIN_SPAN
     │                  (anti-sprawl). Until then it's provisional/internal.
     ├─ 4. SYNTHESIZE   for each CHANGED storyline only: regenerate the narrative from member events in
     │                  chronological order (DeepSeek). Freeze dormant storylines (no regen).
     └─ 5. RECORD       upsert storylines + storyline_events; recompute centroid; set status/activity.
FRONTEND: /storyline/[slug] (blog page), /storylines (index), "part of" badge on events.
```

**Reuse, don't rebuild:** embeddings already exist (`Event.hyde_embedding`); storyline matching is cosine over those (same pgvector ops as related-events/dedup). The LLM judge mirrors `pipeline/dedup.py` / clustering validation (but on **DeepSeek**, user-facing). RSS/XML, scheduling, and the **fixed** advisory-lock pattern come from the existing code. Synthesis uses `llm_client.py`.

**Level distinction (important):** the pipeline already clusters **articles → events** (HyDE, threshold 0.80). Storylines are the **next level up: events → storylines**, over **much longer time spans** (weeks/months, not a 14-day match window). Do not reuse the event-match thresholds; storylines need their own, looser, time-tolerant matching + an LLM judge, because "same ongoing story" is broader than "same event."

---

## 4. Data Model

```sql
CREATE TABLE storylines (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug         TEXT UNIQUE NOT NULL,          -- stable for SEO; do NOT churn on every update
  title        TEXT NOT NULL,                 -- stable; only rename on a material narrative shift
  narrative_md TEXT,                          -- current synthesized "story so far"
  summary      TEXT,                          -- one-liner for cards/index/social
  category     TEXT,                          -- inherited (majority of member events); may span
  centroid     VECTOR(1536),                  -- mean of member hyde_embeddings; for matching
  status       TEXT NOT NULL DEFAULT 'provisional', -- provisional|active|dormant|closed|merged
  event_count  INT NOT NULL DEFAULT 0,
  first_event_at TIMESTAMPTZ,
  last_event_at  TIMESTAMPTZ,                 -- drives dormancy
  merged_into  UUID REFERENCES storylines(id),-- if merged
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE storyline_events (
  storyline_id UUID NOT NULL REFERENCES storylines(id) ON DELETE CASCADE,
  event_id     UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  added_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (storyline_id, event_id)
);
CREATE INDEX ix_storylines_status_activity ON storylines (status, last_event_at DESC);
-- pgvector index on centroid for matching (ivfflat/hnsw, cosine), like the events embedding index.

-- (Phase 2) user follows:
CREATE TABLE storyline_follows (
  user_id UUID NOT NULL, storyline_id UUID NOT NULL, created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, storyline_id)
);
```

- `status='provisional'` = detected but not yet public (below the promotion threshold). Only `active`/`dormant`/`closed` are user-visible.
- Store `narrative_md` so the page renders instantly without re-calling the LLM; regenerate only on membership change.
- `centroid` recomputed on membership change; matching = cosine(new event embedding, centroid) + candidate member similarity.

---

## 5. Event → Storyline Assignment (the technical crux)

For each new/updated event since the last run:
1. **Candidate set:** top-K storylines by `cosine(event.hyde_embedding, storyline.centroid)` above a loose floor, PLUS recent (last ~30–45d) events not yet in a storyline that are embedding-similar to this event (potential new-storyline seeds). Time-tolerant: storylines can be months long, so do **not** apply the event-match 14-day window.
2. **LLM judge (DeepSeek, `llm_client.py`):** given the event (title + tier1) and each candidate storyline (title + current narrative), decide: `extends: <storyline_id>` | `new_storyline_with: [event_ids]` | `standalone`. One cheap call per event (or batch several events per call to save cost). Mirror the yes/no discipline of `dedup.py`; be **conservative** — over-merging into a wrong storyline is worse than leaving standalone.
3. **Promotion (anti-sprawl):** a `new_storyline_with` group becomes a real storyline only when it reaches **`MIN_EVENTS` (e.g. 3) over `MIN_SPAN` (e.g. spanning >1 day)**. Below that it stays `provisional` (internal). A single event never creates a public storyline; a second/third related event **retroactively** forms one.
4. **Membership + recompute:** insert into `storyline_events`, recompute `centroid`, bump `event_count`/`last_event_at`, set `status='active'`.
5. **Dormancy/closing:** a sweep marks storylines with no new event in `DORMANT_DAYS` (e.g. 21) as `dormant` (frozen — no re-synthesis); optionally an LLM/heuristic marks clearly-resolved threads `closed`.

Thresholds (`STORYLINE_SIM_FLOOR`, `MIN_EVENTS`, `MIN_SPAN`, `DORMANT_DAYS`, top-K) are **config**, tuned on real data (expect iteration, like the HyDE thresholds were).

---

## 6. Narrative Synthesis

- **Only for CHANGED storylines** (new member this run). Dormant/unchanged storylines are never re-synthesized → cost control.
- Input: member events in **chronological order** (title, tier1_scan, what_this_means, date, score). Output: `narrative_md` (the "story so far" — a tight, factual, evergreen synthesis with a lede and a "latest" section) + `summary` (one-liner) + a possibly-updated `title` (**only if the story materially shifted**; otherwise keep the stable title for SEO).
- **Facts-only guardrail** (reuse the pipeline's opinion-vs-fact discipline): synthesis may only use facts present in member events; no invented outcomes/dates/quotes. Consider a light QC pass for high-visibility storylines.
- Model: DeepSeek via `llm_client.py` (user-facing; **not** the Claude sub). Provider/model configurable so it can be A/B'd like the audio script writer.
- **Title/slug stability:** the `slug` is permanent once public (SEO + inbound links). Title changes are rare and deliberate; never churn either on routine updates.

---

## 6.1 Event-update awareness (Mike, 2026-07-09)

Events are not static — the pipeline ties new articles to an existing event over time via `create_event_update` (writes an `EventUpdate` with `update_summary` + `article_ids`) and bumps `Event.update_count`. Storylines must treat an **updated event** as a change signal, not just a **new event**:
- **Trigger:** the assignment/synthesis job runs on events that are new **OR updated** since the last run (track a high-water mark on `updated_at`/`update_count`, or diff `EventUpdate` rows). An update to a member event should re-synthesize its storyline (subject to the only-on-change cost rule).
- **Narrative reflects the update, with attribution of the shift:** the synthesis prompt should distinguish "a new development in this thread" from "a new outlet is now also reporting the same development, adding [angle]." Feed the member events' `EventUpdate.update_summary` list so the narrative can say e.g. "…and as of today, [outlet] adds [new context/angle]" rather than silently rewriting.
- **Timeline shows updates:** the storyline page timeline (and any downstream surface) should surface an event's updates ("+2 updates — newest: …"), not just the original event.
- This is a **consumable "what's new" signal** — see the next note; it's exactly what makes downstream takes feel current instead of stale.

## 6.2 The storyline is a CONTEXT OBJECT for downstream surfaces (Mike, 2026-07-09)

A storyline's value isn't only the on-site page — its **narrative + "what's new since X"** is the broader-context object that other features consume so their output feels situated, not robotic:
- **Podcast script writer** (see `audio_briefing.md`): when narrating today's event, pass the storyline it belongs to (the "story so far" + latest update) so the writer can give a **situational take** — "this is the latest turn in the ongoing [X] saga; last week [Y], and now [Z]" — instead of an isolated one-event summary. **This is a primary reason storylines is sequenced before the full podcast build.**
- Also consumed by catch-me-up, "what happened with X," and topic-emails.
- **Design implication:** the synthesis stage should emit a structured, reusable context object per storyline — `{title, narrative_md, one_liner, whats_new (recent updates/events), member_event_ids, status}` — not just HTML for the page. Store it (`narrative_md` + `summary` cover most; add a `whats_new` field or derive it from recent `storyline_events`/`EventUpdate`) so downstream callers get it cheaply without re-synthesizing.

## 7. Frontend

- **`/storyline/[slug]`** — blog-format page: title, current `narrative_md`, a "latest update" marker, then a **reverse-chronological timeline** of member events (each a card linking to the event modal/detail). Add JSON-LD (`NewsArticle`/`Article`) + canonical URL + OpenGraph for SEO/shares (the site already needs per-event OG — same pattern).
- **`/storylines`** — browsable index: active first, filter by category, show activity/recency and event count. Great landing/SEO surface.
- **Event integration** — a **"part of: [storyline]"** badge/link on event rows and in the event modal (an event can be in at most one storyline in v1). Also surface "related storylines."
- **(Phase 2) Follow button** — logged-in users follow a storyline → updates via email/notification.

---

## 8. Gotchas & Things To Consider (overrides naive choices above)

1. **Sprawl is the #1 risk.** Without the promotion threshold you'll get thousands of one-event "storylines." Enforce `MIN_EVENTS`/`MIN_SPAN`; keep provisional ones internal. Better to under-create than to litter the index.
2. **Re-synthesis cost.** Regenerate narratives **only on change**; freeze dormant threads. A naive "regenerate all nightly" would be needless DeepSeek spend and churn SEO content.
3. **Factuality.** Synthesis is user-facing and evergreen — a hallucinated "outcome" sits there for weeks. Strict facts-only prompt + QC on high-visibility storylines.
4. **Merge/split.** Two storylines that are really one → **merge** (set `merged_into`, move events, redirect the slug 301). One storyline that's actually two threads → **split** (harder; provide an **admin tool**, don't automate splits in v1). Detect merge candidates by centroid cosine + LLM judge, like event dedup.
5. **Slug/title stability = SEO.** Changing a public slug breaks inbound links and search ranking; never do it silently (301 on merge only). Titles rarely change.
6. **Matching drift.** Recompute `centroid` on membership change; a stale centroid mis-assigns new events. Consider member-similarity as a tiebreak, not centroid alone.
7. **Category spanning.** A storyline can cross categories (a model release is "products" + "enterprise"). Inherit the majority but don't force a single category to gate visibility.
8. **Cold start / backfill.** On first run, backfill storylines over the existing ~3k events (a one-time batch) — but respect the promotion threshold so backfill doesn't create noise. Budget the backfill's DeepSeek cost explicitly (it's a one-time larger run).
9. **Dormancy vs resolution.** "No new events" ≠ "resolved." Mark `dormant` on silence; only mark `closed` with a real signal. Show dormant storylines as "quiet since [date]," not deleted.
10. **Standalone events are fine.** Most events won't be in a storyline. That's correct — don't force everything into a thread.
11. **Quota discipline (event-calendar lesson).** User-facing → **DeepSeek via `llm_client.py`**, never the Claude sub. Batch the assignment judge (several events/call) and synthesize only-on-change to keep it cheap. Track spend (reuse the usage logging).
12. **Fail-safe + alert.** If the storyline job fails, the pages just don't update — degrade gracefully, alert (reuse `ops_notifications`), never publish a half-synthesized narrative.
13. **Duplicate content / canonical.** Storyline pages summarize events that also have their own pages — use canonical tags and distinct framing (narrative vs event) so Google sees them as complementary, not duplicate.
14. **Privacy/moat exposure.** Storyline pages are your synthesized IP; fine to expose (it's the product), but they make the corpus scrapable — acceptable, just be aware.

---

## 9. Phasing

| Milestone | Deliverable |
|---|---|
| **M1 — Engine + pages** | Assignment job (detect/promote/synthesize), data model, one-time backfill, read-only `/storyline/[slug]` + `/storylines` index, "part of" links. Tune thresholds on real data. |
| **M2 — Follow + updates** | `storyline_follows`, follow button, update notifications/emails (needs `email_digest` infra). |
| **M3 — Ask / "what happened with X"** | Semantic retrieval over storyline centroids + member events → return the synthesized storyline for a query. Powers `semantic_ask` and **catch-me-up** ("updates to what you follow + new storylines since your last visit"). |
| **M4 — Social drafts** | Auto-draft "what happened with [storyline] this week" for X/LinkedIn (marketing; reuse synthesis). Admin merge/split tools hardened throughout. |

Ship M1 and let it run/tune before M2+. M1 alone is a real SEO + UX win.

---

## 10. Cost Model

| Item | Basis | ~Cost |
|---|---|---|
| Assignment judge (DeepSeek) | batched, ~per new event/day | pennies/day |
| Synthesis (DeepSeek) | only changed storylines/day | pennies/day |
| One-time backfill | ~3k events → judge + synthesize | a few $ once (budget it) |
| Embeddings | reuse existing `hyde_embedding` | $0 |

Cheap because it renders existing content on a cheap provider, only-on-change. Track actuals.

## 11. Definition of Done
- **M1:** related events auto-group into sensible storylines (spot-check quality); promotion threshold prevents sprawl; pages render narrative + timeline; backfill done; job fails safe + alerts; DeepSeek spend tracked and low. Thresholds documented.
- Each milestone: update this doc + a session log; add `knowledge/gotcha_*.md` for anything >30 min (e.g. threshold tuning, merge/split).

## 12. Testing Strategy
- **Assignment quality:** hand-label a sample of recent events into expected storylines; measure precision/recall of the auto-assignment; tune thresholds. Watch the failure mode from the union-find clustering post-mortem (over-merging into mega-threads) — the LLM judge + conservative bias guards it.
- **No-sprawl assertion:** count public storylines after backfill; assert reasonable (not thousands).
- **Synthesis:** facts-only spot-check; assert no regeneration for unchanged/dormant storylines (cost guard).
- **Merge:** create two obviously-same storylines → merge tool produces one + 301.
- **Idempotency:** re-run the job with no new events → no changes, no LLM calls.

## 13. Open Questions for Mike
- Fully-automatic storylines, or a light **admin approve/rename** step before a storyline goes public? (Recommend auto + admin override.)
- Thresholds: starting `MIN_EVENTS` (3?), `MIN_SPAN`, `DORMANT_DAYS` (21?), similarity floor — will tune, but pick starting values.
- Should storylines feed the **audio weekly recap** (weekly = "top storylines this week")? Strong fit — the weekly audio and storylines want the same synthesis.
- Priority of M2 (follow/emails) vs M3 (ask) vs the audio feature.

## 14. References
- Reuse: `src/ai_signal/llm_client.py` (DeepSeek synthesis + assignment judge — user-facing, off the Claude sub), `Event.hyde_embedding` + the pgvector related-events/dedup queries (`pipeline/dedup.py`, `api/events.py` related), the clustering/judge patterns (`pipeline/clustering.py`), `agent/orchestrator.py` (job + **fixed** advisory lock), `src/ai_signal/config.py` (`Settings`).
- Siblings/consumers: `audio_briefing.md` (weekly recap can reuse storyline synthesis), `email_digest.md` (topic-follow emails = a storyline-scoped digest), future `catch_me_up` / `semantic_ask` (both are query adapters over this engine).
- History: the union-find clustering post-mortem in `_status.md` (over-merging failure mode to avoid), `event_calendar.md` (quota discipline).
- New config/env: `STORYLINE_PROVIDER`/`STORYLINE_MODEL` (default deepseek), `DEEPSEEK_API_KEY`, `STORYLINE_SIM_FLOOR`, `STORYLINE_MIN_EVENTS`, `STORYLINE_MIN_SPAN_DAYS`, `STORYLINE_DORMANT_DAYS`.
