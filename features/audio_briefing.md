# Feature: Audio Briefing (Goblin News Daily / Weekly)

---
type: feature
status: planning
complexity: C3
tags: [audio, tts, podcast, distribution, elevenlabs, growth]
depends_on: [production_deployment]
required_by: []
last_updated: 2026-07-07
author: mike + Claude (co-founder session)
---

> **BUILD AGENT (Opus):** This is a planning spec, not a finished design — implement to match **User Intent**, not just the letter of each step. It is intentionally detailed. Read the whole doc before writing code; the Gotchas and Cost sections change decisions made in earlier sections. Several external-API and platform details were written against a **Jan 2026 knowledge cutoff** — every place tagged **[VERIFY]** must be re-checked against live docs at build time (ElevenLabs models/pricing, Apple/Spotify submission rules, podcast namespace tags).
>
> **Non-negotiable design principle:** we are *re-rendering an existing asset* (the distilled, scored event), not creating new content. Every stage should reuse the pipeline's existing outputs. If you find yourself re-distilling or re-scoring, stop — you're rebuilding the moat instead of using it.

---

## 1. User Intent

### Goal
Turn the existing distilled/scored event corpus into a **short, natural, high-signal audio news briefing** people actually want to listen to — an efficient "catch me up on AI" for a commute/gym/coffee, distributed on podcast platforms so people can subscribe. The signal score is the differentiator: *ranked, high-signal-only, in five minutes.* Nobody else can promise that because nobody else scores.

### Success Criteria
- A **Daily** episode auto-publishes every morning covering the prior editorial day's 7+ events, ordered high-to-low signal, **under 5 minutes**, in one consistent natural-sounding voice.
- A **Weekly** recap episode auto-publishes (Sunday) covering the week's top storylines.
- Episodes appear automatically in Apple Podcasts and Spotify (and ideally YouTube) with **zero per-episode manual work** after one-time setup.
- The audio reads as *written-for-the-ear prose*, not TTS of bullet lists; AI jargon/model names are pronounced correctly.
- Publishing is **reliable** (same time daily) and **fails safe** (a broken run does not publish a garbled episode; it alerts instead).
- Marginal cost stays low (**~$30–100/mo all-in**) and it does **not** compete with the news pipeline's weekly Sonnet quota.

### Explicit Non-Goals for v1 (decided, with reasons — do not build these first)
- **No "breaking"/standalone real-time episodes.** AI news is almost never minutes-sensitive (even model releases: you want to know it dropped, but substance comes days later). Podcast UX isn't built for breaking news, and a standalone 9 duplicates the daily. *Speed, if we want it, ships as a push notification / on-site "Major" tag — a different surface. Revisit "Specials" as v2.*
- **No per-user personalized audio on podcast platforms.** A podcast is one feed = one show; personalized feeds can't go to Spotify. Personalized audio (user's own filters) is a **later, on-site/in-app** feature over the existing per-user RSS, not a launch item.
- **No user control over the public shows' contents.** Rigidity is what makes auto-distribution possible; keep the public shows editorially fixed (threshold + ordering rules only).

### User Flow (listener)
1. Listener finds "Goblin News Daily" in Apple/Spotify/YouTube (or the site's Listen page) and subscribes.
2. Each morning a new <5-min episode is waiting; ranked, highest-signal first.
3. They catch up on everything that matters in AI for the prior day, then optionally tap a show-note link to read the full event on the site.
4. Weekly, a slightly longer recap ties the week's storylines together.

---

## 2. Scope & Phasing (build in this order)

| Milestone | Deliverable | Gate to next |
|---|---|---|
| **M0 — Prototype (throwaway)** | A script + one MP3 generated from *last week's real events*, produced by hand-running the stages locally. **No DB, no cron, no feed.** | **The listen test:** Mike listens. Does it clear "I'd actually subscribe"? If not, iterate on script prompt + voice before building anything durable. This is the real go/no-go. |
| **M1 — Daily pipeline (internal)** | Scheduled job: select → script → TTS → assemble → store MP3 → write `audio_episodes` row. Episode viewable/playable on an internal `/listen` page. Not yet on platforms. | A week of daily episodes generate reliably and sound good. Monitoring/alert on failure works. |
| **M2 — Podcast feed + platforms** | Podcast RSS feed(s), show artwork, submit to Apple + Spotify (+ YouTube). Public Listen page with subscribe buttons + transcripts. | Feed validates; episodes appear in Apple/Spotify; downloads tracked. |
| **M3 — Weekly recap** | Weekly storyline recap episode (reuses the pipeline with a different selection + prompt). | — |
| **M4 (later) — Personalized on-site audio** | Logged-in users generate audio from *their* filters, on demand, on-site only. Separate design. | — |
| **M5 (later) — Social clips** | Auto-cut 60-sec vertical clips of top stories for TikTok/Reels/Shorts/X (marketing, not a podcast feed). See Promotion §12. | — |

Ship M0→M2 before touching M3+. Resist scope creep; the daily show is the product.

**Development approach — "cowboy mode" (Mike's call, and correct given zero users yet):** don't gate hard on a hand-built M0 prototype. Build the full pipeline early, but with a first-class **regeneration + comparison harness**: a mode that re-runs select→script→TTS→assemble for a *chosen past day* (or several) **without publishing**, and can generate **multiple variants** (different script providers via `llm_client.py`, different word-range params, different voices) side-by-side. Iterate by listening and regenerating until the prompts/voice/word-ranges are dialed in, then **lock** those params and let the daily cron run against them. Because there are no subscribers, breakage is cheap — the risk is quality, not outage, so optimize the loop for fast listen-and-tune. Concretely: implement a `--regenerate DATE [--provider X] [--voice Y] [--variant-label Z]` CLI that writes variants to a scratch dir and never touches `audio_episodes.status='published'` or the public feed. Keep every variant's `script_json` so a winner can be reproduced. This collapses M0 and M1 into "build it, then tune it," which is the right shape here.

---

## 3. Architecture Overview

```
NEW SCHEDULED JOB  (cron, separate from the news pipeline; fires at editorial ~midnight)
  agent/audio_briefing.py   [own advisory lock — use id 44; news=42, old events used 43]
    │
    ├─ 1. SELECT      reuse events query → prior editorial-day events, score>=THRESHOLD,
    │                 ordered by effective_score DESC, capped. (§5)
    ├─ 2. SCRIPT      ONE Sonnet call (Agent SDK, tools=[]) → segmented spoken script JSON,
    │                 word-budgeted by signal, with pronunciation-safe text. (§6)
    ├─ 3. TTS         ElevenLabs per segment (voice consistency via previous/next text). (§7)
    ├─ 4. ASSEMBLE    ffmpeg: intro sting → [segment, chime, segment, …] → outro,
    │                 loudness-normalize to -16 LUFS, encode MP3, write ID3 tags. (§8)
    ├─ 5. STORE       write MP3 to audio volume; served static by nginx w/ range support. (§9)
    ├─ 6. RECORD      insert audio_episodes row (guid, duration, path, transcript, event_ids). (§10)
    └─ 7. PUBLISH     regenerate podcast RSS feed(s) from audio_episodes. (§11)

DISTRIBUTION (one-time): submit feed URL to Apple/Spotify/YouTube → they poll & auto-ingest. (§13)
FRONTEND: /listen page (player + subscribe buttons + transcripts). (§ Frontend)
```

**Why a separate job, not bolted onto `run_pipeline`:** different schedule (editorial midnight vs 6/14/22 UTC), and independence — a news-pipeline failure must not block audio and vice-versa. It reuses the same container, DB, config, advisory-lock pattern, and RSS-XML approach. **Script gen uses `llm_client.py` (direct paid API), NOT the Agent SDK** — so the audio job is fully decoupled from the shared Claude-sub quota (see §6). Model the job structure on `agent/orchestrator.py`.

**Reuse, don't rebuild:** selection reuses `src/ai_signal/api/events.py::_build_event_query` (or a small dedicated query); day boundary reuses the tz-aware logic added 2026-07-07; RSS-XML reuses the `Element/SubElement/tostring` approach already in `events.py::rss_feed`; scheduling/lock reuses the orchestrator pattern; secrets go in `src/ai_signal/config.py` `Settings`.

---

## 4. Key Decisions for Mike (resolve before/at M0)

These change the build; get answers early.

1. **Editorial timezone** for "the previous day." Recommend a **fixed** zone (e.g. `America/Los_Angeles` or `America/New_York`) — a public show is one canonical day, not per-listener. This is different from the per-viewer tz on the site feed. **[DECISION NEEDED]**
2. **Publish time.** "Fires at midnight" → pick the UTC cron time that = shortly after the editorial day ends *and* lands the episode before listeners wake (e.g. 10:00 UTC ≈ 2–3am PT publishes for the US morning). **[DECISION NEEDED]**
3. **Voice.** ~~One ElevenLabs voice…~~ **RESOLVED:** design a custom branded voice via ElevenLabs **Voice Design** (prompt-to-voice), audition in M0, lock one `voice_id`. See §7.
4. **Show branding & structure.** Recommend **one feed** "Goblin News Daily" carrying daily episodes + the weekly recap as a longer Sunday episode (simpler: one subscribe link). Alternative: two separate shows. **[DECISION NEEDED]**
5. **Signal threshold & length.** Recommend **7+**, target **≤5:00**, higher-signal stories get proportionally more words (§6). Consider **weekdays-only** daily to start (fewer weekend stories). **[DECISION NEEDED]**
6. **AI-voice disclosure** wording (put it in the show description; lean into it — it's on-brand). Non-optional for platform safety.

**Resolved 2026-07-08 (Mike):**
- **Voice** → custom ElevenLabs Voice Design (§4.3, §7).
- **Word budget** → per-tier + total **ranges**, not a max (§6).
- **Script model** → run on `llm_client.py` (provider-agnostic); **A/B Claude vs DeepSeek vs Grok in M0**, then pick. Decouples from the Claude sub. (§6)
- **Pronunciation** → prompted-in (phonetic spoken `text` + clean `text_display` for transcript). (§6)
- **Intro/outro** → Mike generates via **Suno**; chime TBD. (§8)
- **Dev approach** → cowboy mode: build full pipeline, tune by regeneration, then lock. (§2)

**Still open:** editorial timezone + publish times (§4.1/4.2); one feed vs two shows (§4.4); threshold 7 vs 8 + length cap + weekdays-only (§4.5); show name + cover art; YouTube in M2 or defer.

---

## 5. Stage 1 — Selection

**Input:** prior editorial day. **Output:** ordered list of events to voice.

- Compute the editorial-day window from `EDITORIAL_TZ`: `[prev local midnight, local midnight)` converted to UTC, filter `Event.first_seen_at` within it. (Note: the site's `range` filter uses *rolling* windows; the audio job must use a true **calendar day** in `EDITORIAL_TZ` — do not reuse `range=yesterday`.)
- Filters: `status='active'`, `published_at IS NOT NULL`, `effective_score >= AUDIO_THRESHOLD` where `effective_score = coalesce(community_score, importance_score)`.
- Order: `effective_score DESC`, tiebreak `first_seen_at DESC`.
- **Cap the count** so length stays bounded even on heavy days: e.g. top ~8–12 stories; the word budget (§6) is the real length governor, but a hard cap prevents pathological days.
- **Dedup/storyline awareness:** if two selected events are near-duplicates (they shouldn't be post-dedup, but check), collapse. If several events are the same storyline, the script prompt should be *told* they're related so it can group them (pass a `related_group` hint if the hyde-embedding related-events data is cheap to include).
- **Empty/thin day:** if 0 qualifying events, **do not publish an empty episode** (a silent/"no news today" episode annoys subscribers and looks broken). Skip and alert. If 1–2 only, still publish (short is fine) but consider a floor.
- Pass to script stage, per event: `title`, `effective_score`, `category`, `tier1_scan`, `what_this_means` (and/or `tier2_understand`), and for 8+ the latest `sentiment_passes` summary (overall_sentiment, fault_lines, a couple of paraphrasable reaction themes — **not** raw quotes), plus the site `slug` for show notes.

---

## 6. Stage 2 — Script Generation (the make-or-break stage)

**One Sonnet call** (via Claude Agent SDK, **`tools=[]`**, see quota note §Cost). Output = **structured JSON** so the assembler can insert chimes between segments and build show notes/transcript.

### Design rules (encode these in the system prompt)
- **Write for the ear, not the eye.** Spoken cadence, short sentences, no bulleted lists read aloud, no "colon then list." Contractions. One idea per sentence.
- **Structure:** cold-open (date + story count + est. length) → per-story segments in signal order → sign-off. Signposting between stories ("Top story…", "Next…", "Also worth knowing…", "Finally…").
- **Word budget by signal = a RANGE, not a max** (Mike's call — ranges give the writer room to serve the content: a meaty 9 runs long, a thin one runs short). TTS ≈ 150 wpm, so ~5 min ≈ ~750 spoken words. Give the writer a **per-tier range** and a **total target range**, and let it flex within them: e.g. 9 → **130–190** words (+ a sentiment beat); 8 → **80–130** (+ optional sentiment); 7 → **40–80**. Total target e.g. **550–780** words. Instruct: use the low end for thin stories, the high end for rich ones; if the sum would exceed the total max, trim the lowest-signal stories first (drop, don't crush everything). All ranges are prompt parameters, not hardcoded prose.
- **Per story:** the *what* (headline in plain speech) → the *key fact(s)* quickly → a brief *"why it matters"* take drawn from `what_this_means` (rephrased for speech, not read verbatim). For 8+, add one sentence of **paraphrased** sentiment ("reaction was split — builders impressed, skeptics flagged the eval methodology"). Never read raw X posts.
- **No hallucinated specifics.** The script may only use facts present in the provided event fields. Instruct explicitly: do not invent numbers, dates, quotes, or outcomes. (This is user-facing published content — treat like the distiller's opinion-vs-fact guardrails already in the pipeline.)
- **Pronunciation is handled in the PROMPT (Mike's call):** the script writer is instructed to spell tricky names/acronyms **phonetically in the spoken `text`** (e.g. "GPT-four-oh", "Qwen" → "chwen", "S-L-M"). This avoids standing up the ElevenLabs pronunciation-dictionary infra. **BUT** to keep the on-site transcript/show-notes readable, the writer **also emits a clean `text_display`** per segment (normal spelling) — the phonetic `text` goes to TTS, the clean `text_display` becomes the transcript. Feed the writer the shared **lexicon** (Appendix D) so it knows the known-problem tokens; keep the lexicon easy to extend (new models/names appear weekly). The ElevenLabs pronunciation dictionary (§7) remains an optional upgrade if prompt-phonetics prove inconsistent.
- **Tone:** confident, concise, lightly personable — a sharp briefer, not a hype man, not a monotone. Match Goblin News brand ("for people who build with AI").

### Output JSON schema (validate it; retry on mismatch)
```json
{
  "title": "AI Briefing — Thu Jul 3: Anthropic's J-Space, Tencent Hy3, +4 more",
  "est_seconds": 270,
  "intro": "Your AI briefing for Thursday, July third. Six stories, about four minutes.",
  "segments": [
    {
      "event_id": "…uuid…",
      "signal": 9,
      "slug": "anthropic-discovers-j-space",
      "text": "Top story. Anthropic says it's found what it's calling Jay-Space…",
      "text_display": "Top story. Anthropic says it's found what it's calling J-Space…",
      "words": 148
    }
  ],
  "outro": "That's your briefing. Full stories and sources at news dot prompt goblins dot A-I. See you tomorrow.",
  "show_notes_md": "1. **Anthropic's J-Space** (signal 9) — https://news.promptgoblins.ai/event/…\n2. …"
}
```
Notes: `text` (phonetic) per segment goes to **TTS**; `text_display` (clean spelling) is concatenated into the **transcript**. `show_notes_md` becomes the RSS `<description>`/`<content:encoded>` and the site show-notes (links drive traffic back — see Promotion). `title` should be **search-friendly** (date + top headline) for platform SEO. Keep the on-air URL spoken form ("news dot prompt goblins dot A-I") in `outro` but real links in show notes.

**Model — use the provider-agnostic `src/ai_signal/llm_client.py`, NOT the Agent SDK (Mike's call).** `LLMClient(provider, model).complete(system, prompt, max_tokens)` already supports `anthropic` / `deepseek` / `grok` on equal footing with per-call cost tracking. This is the right call for three reasons:
  1. **A/B the script writer** — generate the same episode with multiple providers and pick the one Mike likes (do this in M0). Make `provider`+`model` config (`AUDIO_SCRIPT_PROVIDER`, `AUDIO_SCRIPT_MODEL`).
  2. **Decouples from the Claude-sub quota** — the Agent SDK draws on Mike's shared Claude Code subscription; a direct paid-API call (pennies/episode) means the podcast never competes with his interactive coding and stays reliable. This makes the podcast the **first stage to move off the Agent SDK** onto `llm_client.py` (the noted migration direction).
  3. **Same wrapper powers user-facing features** (catch-me-up, etc.) which **cannot** use the Claude sub — DeepSeek via `llm_client.py` is the path there too.
  Quality: DeepSeek is cheap and fine for *rewriting already-curated* content; still A/B it against Claude (Anthropic API) and Grok. Note: testing the Claude candidate through `llm_client.py` needs a paid `ANTHROPIC_API_KEY` (separate from the sub).

---

## 7. Stage 3 — Text-to-Speech (ElevenLabs)  **[VERIFY all specifics]**

- **Provider:** ElevenLabs (quality leader; there is no Anthropic TTS — this is the one external dependency). Alternatives if cost/latency matter later: OpenAI TTS (cheaper, decent), Google/Azure. Keep the TTS call behind a small `tts.py` interface so the provider is swappable.
- **Model:** pick the current best natural-narration model (e.g. `eleven_multilingual_v2` or the latest v3-class model) — **[VERIFY current model names/quality]**. Favor quality over the cheapest "turbo/flash" model for a flagship listen.
- **Voice — design a CUSTOM branded voice via ElevenLabs Voice Design (Mike's call):** generate a voice from a text prompt (describe the ideal Goblin News briefer), audition options in M0, then lock one `voice_id` and never change it (voice = brand). **[VERIFY Voice Design is available on the plan + how to persist the generated voice_id]**. Fallback: pick a stock voice if Voice Design output isn't good enough.
- **Voice settings:** tune `stability` / `similarity_boost` / `style` for consistent, non-robotic narration; lock the values once chosen.
- **Continuity across segments:** synthesize per segment but pass `previous_text`/`next_text` (or the request-stitching feature) so prosody is continuous — **[VERIFY the current param names]**. Alternatively synthesize the whole script in one request and mark segment boundaries with silence you detect, but per-segment gives cleaner chime insertion. Prefer per-segment.
- **Pronunciation dictionary:** upload/attach a **pronunciation dictionary** (alias and/or IPA/CMU phoneme rules) so "Qwen", "GPT-4o", "Hugging Face", "S>Space", model version strings etc. are said correctly **without** mangling the on-site transcript — **[VERIFY dictionary API + which model supports phoneme tags]**. This is the single biggest audio-quality lever for *AI* news. Seed it from Appendix D; make it easy to extend.
- **Output format:** request MP3 at a podcast-appropriate bitrate (e.g. 128 kbps CBR, 44.1 kHz) or a WAV/PCM you re-encode in ffmpeg (cleaner for the loudness pass). Mono is acceptable and smaller for spoken word; stereo is fine too — pick one and be consistent.
- **Robustness:** retry with backoff on 429/5xx; ElevenLabs has per-plan concurrency and character quotas — batch segments sequentially to respect concurrency; on hard failure, **abort the episode and alert** (do not publish partial audio).
- **Cost tracking:** log characters used per episode into the existing `llm_usage_log`-style tracking (or a new `audio_usage` row) so spend is visible (Mike wants cost visibility).

---

## 8. Stage 4 — Audio Assembly (ffmpeg)

- **Elements:** intro sting (1–3s branded) → for each segment: `segment_audio` then a short **chime/earcon** (~0.4–0.8s) as a separator → outro sting. Do **not** put a chime after the last segment before the outro; design the sequence deliberately.
- **Loudness normalization (required):** normalize the final mix to **-16 LUFS integrated, ≤ -1 dBTP true peak** (Apple/industry spoken-word target) using ffmpeg `loudnorm` (two-pass for accuracy). Inconsistent loudness is the #1 reason a podcast feels amateur and gets skipped.
- **Encode:** MP3, 128 kbps (spoken word doesn't need more), 44.1 kHz. Keep episodes small — smaller files = faster downloads = fewer drop-offs and cheaper hosting.
- **ID3 tags:** title, artist ("Goblin News"), album (show name), track/date, cover art embedded, and ideally **chapter markers** (one per story) so players show a chapter list — nice-to-have, high polish. **[VERIFY chapter tag format: ID3 CHAP frames / Podcasting 2.0 `podcast:chapters` JSON]**.
- **Intro/outro: generated with Suno (Mike will make these).** Confirm the Suno plan grants **commercial/distribution rights** for the generated tracks (paid tiers do — **[VERIFY current Suno license terms for podcast distribution]**) and keep the license/receipt on file, since Spotify/YouTube content-ID can flag music. The **chime/earcon between stories is TBD** — options: a short Suno-generated sting, a simple synthesized tone, or a subtle whoosh; keep it short (~0.4–0.8s) and non-intrusive. Store all audio assets (intro/outro/chime) in the asset store with their license noted; never use a copyrighted track.
- **Determinism:** given the same script+assets, assembly should be reproducible. Assembly runs offline (no network) — good for retries.

See Appendix C for concrete ffmpeg commands.

---

## 9. Stage 5 — Hosting the MP3

- **Where:** the Hetzner box has ample disk (906 GB, ~6% used). Episodes are ~3–6 MB; ~30/mo ≈ 150 MB/mo, ~2 GB/yr. Store under a mounted **audio volume** (e.g. `~/apps/ai-signal/audio/` bind-mounted into a container) and **serve as static files directly via nginx** — *not* through the Next.js app.
- **Why static/nginx:** podcast players **require HTTP byte-range requests** (`Accept-Ranges: bytes`) for seeking/streaming; nginx serves static files with range support by default. Serving MP3 through the Next app risks breaking range support and wastes app resources.
- **Headers:** `Content-Type: audio/mpeg`, `Accept-Ranges: bytes`, long `Cache-Control` (episodes are immutable once published), correct `Content-Length`. Serve at a stable path, e.g. `https://news.promptgoblins.ai/audio/daily/2026-07-03.mp3` (or GUID-based).
- **Immutability & GUID:** the enclosure URL for a published episode must **never change** (players cache by URL/GUID). If you must re-encode, publish a new episode, don't swap bytes at an existing URL.
- **Analytics bonus:** because you host the enclosure, **nginx access logs = real download counts** (better than platform stats). Consider a tiny downloads table or log parser later. Beware: prefetching by apps inflates counts — use the IAB "unique download" heuristics if you get serious (dedupe by IP+UA within 24h, ignore range-0 byte probes).
- **Backups/retention:** keep all episodes (they're small). Optionally sync `audio/` to the existing Hetzner Storage Box (borg) so a disk loss doesn't lose the catalog — a missing back-catalog breaks the feed for new subscribers.

---

## 10. Data Model

New Alembic migration. Keep it minimal.

```sql
-- one row per published (or attempted) episode
CREATE TABLE audio_episodes (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),   -- also the RSS <guid>
  show          TEXT NOT NULL,             -- 'daily' | 'weekly'
  editorial_date DATE NOT NULL,            -- the day (in EDITORIAL_TZ) the ep covers
  title         TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'pending', -- pending|generating|published|failed|skipped
  audio_path    TEXT,                      -- relative path / URL of the MP3
  audio_bytes   BIGINT,                    -- enclosure length (required by RSS)
  duration_sec  INT,                       -- itunes:duration
  transcript    TEXT,                      -- full plain-text transcript (accessibility + SEO)
  show_notes_md TEXT,                      -- RSS description + site show notes
  script_json   JSONB,                     -- the generated script (audit/debug/regeneration)
  event_ids     UUID[],                    -- events covered (for show notes + dedup)
  tts_chars     INT,                       -- cost tracking
  published_at  TIMESTAMPTZ,               -- RSS pubDate
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (show, editorial_date)            -- idempotency: one episode per day per show
);
CREATE INDEX ix_audio_episodes_show_pub ON audio_episodes (show, published_at DESC);
```

- The `UNIQUE(show, editorial_date)` makes re-runs idempotent (skip if a published episode exists; allow retry if `failed`).
- Store `script_json` and `transcript` — needed for the site, SEO, debugging, and re-encoding without re-calling the LLM.
- Advisory lock id for the job: **44** (news=42; old event calendar used 43). Keep a comment noting the registry.

---

## 11. Stage 7 — Podcast RSS Feed

Podcasting is **pull-based**: you host one RSS feed per show; directories poll it and auto-ingest new `<item>`s. Generate the feed from `audio_episodes` on each publish (and/or serve it dynamically like `events.py::rss_feed`, but a regenerated static file is cache-friendly).

**Channel-level (required by Apple):** `title`, `description`, `link`, `language` (`en-us`), `itunes:image` (see artwork), `itunes:category` (e.g. `Technology` / `News` — pick the allowed taxonomy value **[VERIFY current Apple categories]**), `itunes:explicit` (`false`), `itunes:author`, `itunes:owner` (name + email), `itunes:type` (`episodic`). Add Podcasting 2.0 `podcast:` tags where cheap (`podcast:guid`, `podcast:transcript` pointing at the transcript, `podcast:locked`).

**Item-level (per episode):** `title`, `enclosure` (url + **length in bytes** + `type="audio/mpeg"`), `guid isPermaLink="false"` (the episode UUID — **stable forever**), `pubDate` (RFC-2822), `itunes:duration`, `itunes:episodeType` (`full`), `description`/`content:encoded` (show notes with links back to the site), optional `itunes:image`, `podcast:transcript` (link to transcript file — great for accessibility + some players show it).

**Artwork:** square **3000×3000** (min 1400), RGB, JPEG/PNG, under platform size limits **[VERIFY]**. Needs to look good as a tiny thumbnail. You have goblin brand assets — produce a dedicated square cover.

**Gotchas (see §14):** GUID stability, correct byte-length, valid RFC-2822 dates, feed must validate (run it through a validator before submitting), don't let a CDN/cache serve a stale feed after publish (short cache on the `.xml`, long cache on the immutable `.mp3`).

See Appendix B for a concrete feed template.

---

## 12. Scheduling & Orchestration

- New entrypoint `agent/audio_briefing.py` with `run_daily()` / `run_weekly()`; `python -m agent.audio_briefing daily`.
- Cron in `deploy/cron/pipeline-cron`: daily at the chosen UTC time (e.g. `0 10 * * *` for daily; `30 10 * * 0` for weekly). **[Mike: confirm times per §4.2]**. Keep weekdays-only option (`* * 1-5`) in mind.
- **Advisory lock id 44**, held on a dedicated connection released in `finally` (mirror the fixed pattern in `orchestrator.py::run_pipeline` — do **not** copy the old leaky version).
- **Fail-safe & alerting:** wrap each stage; on any failure, mark the episode `failed`, publish nothing, and **alert** (Discourse DM / the mechanism from `features/ops_notifications.md`). Podcast subscribers *notice* missing/late/garbled episodes, so reliability matters more than for the silent pipeline. A missed day should page.
- **Idempotency:** if today's episode already `published`, exit. If `failed`/absent, generate.
- **Ordering vs the news pipeline:** the audio job reads events the pipeline already produced; ensure the daily fires *after* the last relevant pipeline run for that editorial day (the 22:00 UTC run). Pick the audio time accordingly.

---

## 13. Distribution / Platform Submission (one-time per platform)

The reason auto-upload "just works": you submit the **feed URL once**; platforms poll it forever.

- **Apple Podcasts** — submit the feed in **Apple Podcasts Connect**; it validates the feed and artwork, then auto-polls. Biggest directory; do this first. **[VERIFY current requirements]**
- **Spotify** — **Spotify for Podcasters**: add the existing RSS feed; Spotify polls it. Caveat: Spotify has tightened around low-effort/AI-spam feeds — present a real branded show and **disclose the AI voice** in the description. **[VERIFY whether RSS ingestion is still open / any AI-content policy]**
- **YouTube** — the exception (not RSS): render audio over a static/branded image as video and upload via the **YouTube Data API** (automatable) or manually at first. Huge search/discovery for "AI news daily." Optional for M2, high-value.
- **Aggregators/directories** for backlinks + reach: Overcast, Pocket Casts, Podcast Index, Podchaser, ListenNotes — most pull from Apple/Podcast Index automatically once you're listed; submit to Podcast Index directly (open, feeds the 2.0 ecosystem).
- Keep a **submission checklist** doc (per platform: URL submitted, status, category chosen, owner email verified).

---

## 14. Gotchas & Things To Consider (READ THIS — it overrides naïve choices above)

1. **Pronunciation of AI jargon is the #1 quality killer.** "GPT-4o", "Qwen", "Hugging Face", "Claude 4.8", version strings, company names. Fix at the **TTS pronunciation-dictionary** layer (keeps transcript clean), seed Appendix D, and make it trivially extensible — expect to add entries weekly as new models/names appear.
2. **Loudness normalization is mandatory** (-16 LUFS). Skipping it is why AI podcasts sound amateur and get skipped.
3. **GUID must be permanent and unique per episode.** Change it and every player shows a duplicate. Use the DB UUID; never regenerate.
4. **Enclosure byte-length must be exact** and the URL immutable. Wrong length or a swapped file corrupts players' download/seek.
5. **Feed caching poisoning:** after publishing, players must see the new item promptly. Short `Cache-Control` on the `.xml`, long/immutable on `.mp3`. If nginx/proxy caches the feed, purge/short-TTL it.
6. **Byte-range support on the MP3** is required for streaming/seek — serve static via nginx, not through the app.
7. **Empty/thin days:** never publish a "no news" episode; skip + alert. Define the minimum-stories floor.
8. **Reliability is the growth flywheel.** Subscribers expect the same time daily. Late/missing episodes churn listeners. This makes the ops-alerting dependency real, not optional.
9. **AI-content & disclosure policies** (esp. Spotify): disclose the synthetic voice; don't spin up multiple near-duplicate feeds (reads as spam). One quality branded show.
10. **Music/audio licensing:** intro/outro/chime must be licensed/royalty-free. Copyright strikes = removal.
11. **Attribution/legal:** you're voicing *your own distilled analysis* of events — fine. Do **not** read others' article text verbatim, and **paraphrase** sentiment/X reactions (never read raw quotes). Keep it your take + facts.
12. **No hallucinated audio.** Once it's spoken and published, errors are loud and un-editable. The script prompt must be strict about only using provided facts; consider a lightweight QC pass (reuse the pipeline's QC pattern) on the script before TTS for 8+ episodes.
13. **Quota safety (the event-calendar lesson):** script gen is **one Sonnet call per episode** (≈30/mo). That will **not** starve the weekly Sonnet quota the way the calendar's daily enrichment did. Keep it that way — do not add per-story LLM calls. If you ever want per-story QC, budget it against the *weekly* quota explicitly.
14. **ElevenLabs quota/concurrency & cost spikes:** a runaway loop could burn the character quota fast. Cap characters per episode; alert on anomalies; track `tts_chars`.
15. **Timezone correctness for "yesterday":** use a true calendar day in `EDITORIAL_TZ` (not the site's rolling `range=yesterday`), and remember DST — use IANA zone math, not fixed offsets.
16. **Transcripts = accessibility + SEO + a moat surface.** Publish the full transcript on each episode's page (indexable) and via `podcast:transcript`. Cheap, high value.
17. **Duplicate coverage confusion** (the reason we cut standalone-9s): keep public shows scheduled; if M5 social clips reuse a story, that's fine (different surface), but don't ship a *podcast* episode that duplicates the daily.
18. **Analytics honesty:** raw download counts are inflated by prefetch; if you report numbers, use IAB-style dedup. Don't over-index on vanity counts early — the listen-through and subscriber trend matter more.
19. **Voice/model drift:** if you upgrade the ElevenLabs model/voice later, the show's sound changes — announce it, and never silently change voices mid-run.
20. **Rebuild-safety:** store `script_json` + `transcript` so you can re-encode audio (new chime, loudness fix) without re-calling the LLM; but if you re-encode a *published* episode, publish a correction or leave it — don't mutate a live enclosure.

---

## 15. Cost Model (estimate — track actuals)

| Item | Basis | ~Monthly |
|---|---|---|
| Script gen (`llm_client.py`, direct API) | 1 call/episode × ~30/mo; ~5–10k in, ~1.5k out | **~$0.30/mo (DeepSeek)** to **~$2–3/mo (Anthropic API)**. Direct paid API — does NOT touch the Claude sub quota. |
| ElevenLabs TTS | ~4k chars/daily + ~8k/weekly ≈ ~130k chars/mo **[VERIFY plan]** | **~$22–99** (Creator ~$22/100k or Pro ~$99/500k) |
| Storage | ~2 GB/yr on existing disk | **~$0** |
| Music/assets | one-time licensed pack | one-time |
| **Total** | | **~$30–100/mo** for a flagship feature |

Cheap because we render existing content. Report actuals after M1 (Mike wants cost visibility — surface per-episode cost like the pipeline does).

---

## 16. Promotion & Growth Strategy

Podcasts grow on **consistency + cross-promotion + searchability**, not virality. Exploit the surfaces you already own.

**Owned-surface cross-promo (do at M2):**
- **The site:** a persistent "🎧 Listen — your AI briefing in 5 min" banner + a `/listen` page with player, subscribe buttons (Apple/Spotify/YouTube/RSS), and transcripts.
- **The forum (promptgoblins.ai):** a **one-time launch announcement** + a pinned "how to subscribe" post, and ask the community to **rate/review on Apple** (ratings drive Apple ranking — the cheapest lever you have). **Do NOT auto-post every episode to the forum** — the news site is a subdomain of the forum, so per-episode posts just spam duplicate content. Forum engagement stays user-initiated via the existing **Discuss** button, unchanged.
- **The text RSS feed & (future) email digest:** add a "listen to today's briefing" link. Audio and the email digest are siblings — build the digest and every email promotes the podcast and vice-versa.

**Searchability / SEO:**
- **Episode titles** = date + top-story headline (podcast search is keyword-driven). Show title/description keyword-tuned: "Daily AI News", "AI news in 5 minutes", "ranked by signal."
- **Transcripts on each episode page** make the whole catalog indexable by Google → organic discovery → site traffic → forum.
- Submit to Podcast Index/Podchaser/ListenNotes for backlinks.

**The hook (marketing message):** lean on the thing only you have — *"The only AI news that's ranked. You hear the 7-plus stories and nothing else. Five minutes, every morning."* Signal-first is the positioning.

**YouTube as a discovery engine:** consistent branded thumbnails + the audio-as-video upload. YouTube search + suggested is a top-of-funnel machine for "AI news daily."

**Social clips (M5 — reframes the "break the 9s" idea):** don't make 9s a separate *podcast*; auto-cut a **60-sec vertical clip** of the top story (audio + captions + waveform/brand) for TikTok/Reels/Shorts/X. That's where "fast + big story" belongs — as *marketing*, driving subscribes — not as a real-time podcast episode. High reuse of the pipeline; big reach potential.

**Reliability = compounding growth:** same time every day, never miss. Podcast retention rewards habit. This is why the alerting/fail-safe (§14.8) is a growth feature, not just ops.

**Partnerships:** offer the player/embed to AI newsletters and communities; a "powered by Goblin News" audio embed spreads the brand.

---

## 17. Definition of Done

- **M0:** an MP3 of last week's real events exists; Mike has done the listen test and approved the voice + script style. Script prompt + pronunciation lexicon seeded.
- **M1:** daily job runs on cron for 7 consecutive days without manual touch; episodes are correct, ≤ target length, loudness-normalized; failures alert and do not publish; `/listen` internal page plays them; per-episode cost logged.
- **M2:** feed validates in a podcast validator; live in Apple + Spotify; public `/listen` page with subscribe buttons + transcripts; download counts observable; YouTube optional.
- **M3:** weekly recap publishing reliably.
- Each milestone: update this doc's status + a session log; add a `knowledge/gotcha_*.md` for anything that cost >30 min (e.g., the pronunciation-dictionary setup, loudnorm settings, feed-validation quirks).

---

## 18. Testing Strategy

- **The listen test (M0, human):** does Mike want to listen? Non-negotiable gate. Re-run whenever the voice/model/prompt changes materially.
- **Script validation:** JSON schema + length/word-budget assertions + a "facts only present in inputs" spot-check (optionally an LLM-judge QC pass for 8+ eps).
- **Audio checks (automated):** measure output LUFS/true-peak (ffmpeg `ebur128`) and assert within target; assert duration ≤ cap; assert file plays and has valid MP3 headers.
- **Feed validation:** run the generated RSS through a validator (Cast Feed Validator / Podbase / Apple's validator) in CI before any submit; assert required tags, valid pubDate, unique/stable GUIDs, correct enclosure length.
- **End-to-end dry run:** a `--dry-run` mode that runs select→script→(optionally TTS)→assemble→writes files but does **not** mark published / regenerate the public feed — for safe iteration.
- **Idempotency test:** re-run the job for a day already published → no-op.
- **Failure injection:** force TTS/LLM failure → episode `failed`, nothing published, alert fired.

---

## 19. Open Questions for Mike
- Editorial timezone + exact publish times (§4.1/4.2).
- Voice choice; clone a custom voice? (§4.3)
- One feed (daily + weekly) vs two shows (§4.4).
- Threshold 7 vs 8; length cap; weekdays-only? (§4.5)
- Show name/branding + cover art direction.
- Do we want YouTube in M2 or defer?
- Personalized on-site audio (M4) — priority vs email digest?

---

## Appendix A — Script Generation Prompt (starting draft; iterate in M0)

```
SYSTEM:
You write a short spoken AUDIO news briefing about AI, to be read aloud by a
text-to-speech voice. It must sound natural and be efficient — a sharp briefer,
not a hype man, not a monotone. You are given today's stories as structured data.

HARD RULES
- Write for the EAR: short spoken sentences, contractions, one idea per sentence.
  No bullet lists, no "colon then list", no headers, no markdown in spoken text.
- Use ONLY facts present in the provided story data. Never invent numbers, dates,
  quotes, names, or outcomes. If unsure, say less.
- Order stories exactly as given (already ranked by signal). Signpost between them
  ("Top story…", "Next…", "Also…", "Finally…").
- Word budget per story is a RANGE (use the low end for thin stories, the high
  end for rich ones — serve the content):
  9 → {r9_min}-{r9_max} words + one sentence paraphrasing audience sentiment (if provided).
  8 → {r8_min}-{r8_max} words + optional one sentence of paraphrased sentiment.
  7 → {r7_min}-{r7_max} words.
  Keep the TOTAL within {total_min}-{total_max} words; if the sum would exceed
  total_max, DROP the lowest-signal stories rather than crushing every story.
- Each story: say what happened in plain speech → the key fact(s) quickly → a brief
  "why it matters" drawn from the provided take (rephrase for speech, don't read it
  verbatim). For 8+, add ONE sentence paraphrasing the sentiment ("reaction was
  split — builders impressed, skeptics flagged the methodology"). Never read raw
  quotes or social posts.
- Cold open: date, number of stories, approx length. Sign-off: point to
  "news dot prompt goblins dot A-I" for full stories, and "see you tomorrow".
- Pronunciation: in each segment's `text` (the spoken version), spell tricky
  AI names/acronyms PHONETICALLY so the TTS says them right (e.g. "GPT-four-oh",
  "Qwen" → "chwen", "S-L-M"). Use the provided lexicon; if a name isn't in it and
  is likely to be mis-said, phoneticize it sensibly. In `text_display` (for the
  transcript), write the SAME sentence with normal spelling ("GPT-4o", "Qwen").
  Only `text` and `text_display` differ, and only on tricky tokens.

Provided lexicon (extendable): {lexicon}

OUTPUT: JSON exactly matching the provided schema (each segment has both `text`
and `text_display`). No prose outside the JSON.

USER (data):
date: {editorial_date}
target_words: {target_words}
stories:  # already ranked, highest signal first
- event_id, signal, category, title, key_facts (tier1_scan), take (what_this_means),
  sentiment (overall + fault_lines + paraphrasable themes, only for 8+), slug
```

## Appendix B — Podcast RSS template (skeleton — **[VERIFY tags]**)

```xml
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:podcast="https://podcastindex.org/namespace/1.0">
  <channel>
    <title>Goblin News Daily</title>
    <link>https://news.promptgoblins.ai/listen</link>
    <language>en-us</language>
    <description>The AI news that matters, ranked by signal. ~5 minutes, every morning. AI-generated voice.</description>
    <itunes:author>Goblin News</itunes:author>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="https://news.promptgoblins.ai/audio/cover.jpg"/>
    <itunes:category text="News"><itunes:category text="Tech News"/></itunes:category>
    <itunes:owner><itunes:name>Mike</itunes:name><itunes:email>mike@promptgoblins.ai</itunes:email></itunes:owner>
    <podcast:guid>STABLE-SHOW-GUID</podcast:guid>
    <!-- per episode -->
    <item>
      <title>AI Briefing — Thu Jul 3: Anthropic's J-Space, Tencent Hy3, +4</title>
      <enclosure url="https://news.promptgoblins.ai/audio/daily/2026-07-03.mp3"
                 length="4187321" type="audio/mpeg"/>
      <guid isPermaLink="false">EPISODE-UUID</guid>
      <pubDate>Thu, 03 Jul 2026 10:00:00 +0000</pubDate>
      <itunes:duration>0:04:31</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <description><![CDATA[ show notes with links back to the site ]]></description>
      <podcast:transcript url="https://news.promptgoblins.ai/audio/daily/2026-07-03.txt" type="text/plain"/>
    </item>
  </channel>
</rss>
```

## Appendix C — ffmpeg assembly (concrete commands)

```bash
# 1. Concatenate: intro, then segment+chime pairs, then outro (build a concat list).
#    (Generate seg_XX.mp3 from TTS; chime.mp3 and intro/outro.mp3 are licensed assets.)
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy joined.mp3   # if all same codec/params
#    If params differ, decode+re-encode instead of -c copy.

# 2. Two-pass loudness normalize to -16 LUFS / -1 dBTP:
ffmpeg -i joined.mp3 -af loudnorm=I=-16:TP=-1:LRA=11:print_format=json -f null -   # pass 1 (read measured values)
ffmpeg -i joined.mp3 -af loudnorm=I=-16:TP=-1:LRA=11:measured_I=..:measured_TP=..:measured_LRA=..:measured_thresh=..:offset=.. \
       -c:a libmp3lame -b:a 128k -ar 44100 final.mp3                                 # pass 2

# 3. Verify loudness:
ffmpeg -i final.mp3 -af ebur128 -f null -
# 4. Tag (id3v2 / ffmpeg -metadata) title/artist/album/date + embed cover.
```

## Appendix D — Pronunciation lexicon (seed; extend continuously)

Store as an ElevenLabs pronunciation dictionary (alias/phoneme) **and** a human-readable source file in the repo. Seed examples (verify actual pronunciations):
- `GPT-4o` → "G P T four oh"
- `GPT-5.5` → "G P T five point five"
- `Qwen` → "chwen"
- `Hugging Face` → keep (usually fine) — verify
- `xAI` → "X A I"
- `LLaMA` / `Llama` → "lah-mah"
- `Claude` → keep
- `SLM`, `RAG`, `MoE`, `RLHF` → spell out letters ("R A G") unless a known word ("Moe"? no → "M o E")
- model version strings, Greek letters, Chinese lab names → add as they appear.

---

## References
- Reuse: **`src/ai_signal/llm_client.py`** (provider-agnostic `LLMClient` — anthropic/deepseek/grok, cost-tracked — the script writer; also the path for all user-facing gen that can't use the Claude sub), `src/ai_signal/api/events.py` (`_build_event_query`, `rss_feed` XML pattern), `agent/orchestrator.py` (scheduling + advisory-lock pattern, **fixed** version), `agent/config.py` (budgets), `src/ai_signal/config.py` (`Settings` for secrets), the tz-aware day boundary (added 2026-07-07).
- Music: **Suno** for intro/outro (Mike; verify commercial license). Voice: **ElevenLabs Voice Design** for a custom branded voice.
- Lessons: `features/event_calendar.md` (quota discipline — one Sonnet call/episode), `docs/knowledge/gotcha_agent_sdk_overhead.md` (`tools=[]`; keep thinking ON for script quality), `features/ops_notifications.md` (alerting the audio job depends on).
- Deploy: `deploy/cron/pipeline-cron`, `docker-compose.prod.yml` (add audio volume), nginx config (static `audio/` location with range support), `DEPLOYMENT.md`.
- New config/env: `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `AUDIO_SCRIPT_PROVIDER` (anthropic|deepseek|grok), `AUDIO_SCRIPT_MODEL`, plus the provider key it needs (`DEEPSEEK_API_KEY` / paid `ANTHROPIC_API_KEY` / `XAI_API_KEY`), `EDITORIAL_TZ`, `AUDIO_THRESHOLD`, word-range params (`AUDIO_WORDS_*`), `AUDIO_BASE_URL`.
