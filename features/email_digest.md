# Feature: Email Digest (Goblin News Daily / Weekly Inbox)

---
type: feature
status: planning
complexity: C3
tags: [email, digest, retention, growth, esp]
depends_on: [production_deployment]
required_by: []
last_updated: 2026-07-08
author: mike + Claude (co-founder session)
---

> **BUILD AGENT (Opus):** This is a planning spec, not a finished design — implement to match **User Intent**, not just the letter of each step. Read the whole doc before writing code; the **Gotchas (§8)** and **Cost (§9)** sections override naïve choices made earlier. Several ESP- and email-standard-specific details were written against a **Jan 2026 knowledge cutoff** — every place tagged **[VERIFY]** must be re-checked against live provider docs at build time (ESP pricing/free-tier limits, `List-Unsubscribe-Post` one-click behavior, DMARC/BIMI norms, deliverability rules).
>
> **Non-negotiable design principle:** this feature *re-renders an existing asset* (the distilled, scored event) into an email. It is the **text sibling of the audio briefing** (`features/audio_briefing.md`) and shares its infrastructure — scheduled job, advisory-lock pattern, `llm_client.py`, timezone handling, `_build_event_query`. If you find yourself re-distilling, re-scoring, or building a second event query, stop — reuse the pipeline's existing outputs and the existing per-user filter machinery.

---

## 1. User Intent

### Goal
Deliver a **daily or weekly email** to each logged-in user containing the high-signal events that match **their own saved filters** — the highest-ROI retention channel we have. The site is pull; email is push. It brings people back on a habit, and every send cross-promotes the audio show. Unlike the public podcast (one fixed feed for everyone), the digest is **per-user personalized** off the filters they already saved on the site.

### Success Criteria
- A user can opt in to a **Daily** or **Weekly** digest, or turn it **off**, from a preferences page, with no new account (reuse the existing DiscourseConnect SSO user).
- Each morning (in the **user's local timezone**) a user who is due receives an email listing **their** matching events (title, signal, one-line, category, link), ranked high-to-low signal, with links back to the full event on the site.
- We **never** send an empty digest — if a user has zero matching events for the period, we **skip** them silently (no "no news today" email).
- The email renders correctly across Gmail, Apple Mail, and Outlook, in light and dark mode, with a plain-text alternative.
- **One-click unsubscribe works instantly** and is honored immediately (`List-Unsubscribe` header + a tokenized link).
- We **never double-send** a period to the same user (idempotent send log).
- Deliverability is healthy: SPF/DKIM/DMARC pass, bounces and spam complaints auto-suppress the address, and we don't get our sending domain blocklisted.
- Marginal cost stays **near zero** in v1 (templated, no LLM) and **pennies** in v2 (optional DeepSeek intro).

### Explicit Non-Goals for v1 (decided, with reasons — do not build these first)
- **No LLM in v1.** The v1 digest is a deterministic template render of already-distilled fields. Zero LLM cost, zero hallucination risk, zero quota contention. The synthesized intro is a *v2* add-on (§2), not a launch requirement.
- **No marketing/newsletter blasts, no drip campaigns, no re-engagement sequences.** This is a transactional-style content digest to opted-in users, not a growth-email engine. (It becomes the retention flywheel *by being reliable and useful*, not by volume — §10.)
- **No per-storyline "follow" emails in v1.** That's v3, and it depends on the storylines feature (`storylines.md`, not yet written) existing first.
- **No HTML editor / custom templates per user.** One responsive template, parameterized by the user's matched events and prefs.
- **No open/click tracking pixels beyond what the ESP gives for free**, and treat even that as optional (privacy — §8). Deliverability signals (bounce/complaint) are mandatory; open tracking is nice-to-have.

### User Flow (recipient)
1. A logged-in user visits **Preferences → Email digest**, flips it on, picks **Daily** or **Weekly**, and optionally tweaks threshold / categories / send hour (defaults inherited from their saved feed filters).
2. They receive a **confirmation** the setting is saved (and, if we do double opt-in — §5 — a one-time confirm email).
3. Each morning in their timezone, if they have matching events for the period, a digest lands in their inbox: ranked list, each item linking to the full event on the site; a footer cross-promoting the audio show and a one-click unsubscribe.
4. They click through to read on the site (marking events read via existing read-state), or one-click unsubscribe — which is honored immediately and confirmed on a landing page.

---

## 2. Scope & Phasing (build in this order)

| Milestone | Deliverable | Gate to next |
|---|---|---|
| **v1 — Templated digest (no LLM)** | ESP wired up (domain auth, webhooks). Scheduled job selects each due user's matching events via `_build_event_query` + their saved prefs, renders one responsive HTML+text email (ranked list: title, signal, one-liner, category, link), sends via ESP, writes a send-log row. Preferences page (frequency/threshold/categories/send-hour/off). One-click unsubscribe. Skip-if-empty. | A week of daily sends to a small seed group (Mike + a few opt-ins) with correct content, correct timezone, no double-sends, clean deliverability (SPF/DKIM/DMARC pass, mail-tester ≥ 9/10). |
| **v2 — Synthesized intro (optional, DeepSeek)** | An optional 1–2 sentence "your week in AI" intro at the top, generated per-user via `llm_client.py` on **DeepSeek**. Off by default or behind a per-user toggle; falls back to no-intro on any LLM error. | Intro reads well, adds < $0.01/send, never blocks or delays a send on LLM failure. |
| **v3 — Storyline "follow" emails** | Per-storyline follow: a user follows a storyline; when it gets a material update, they get a focused email. **Depends on `storylines.md`** (the storyline model + update-detection). Reuses this feature's ESP, send-log, unsubscribe, and rendering. | — |

Ship v1 fully before touching v2. v1 is the product; the intro is polish. **v3 is gated on a feature that does not exist yet** — do not build it until storylines lands.

**Why "no LLM" in v1 is the right call (not just a cost dodge):**
1. **Cost** — a templated render is free; an LLM-per-user-per-day scales linearly with users and would dwarf every other line item.
2. **Safety** — the digest is user-facing published content. A template can't hallucinate; it only echoes fields the distiller already vetted.
3. **Quota** — critically, **user-facing generation CANNOT use the Claude Agent SDK / Mike's Claude Code subscription** (see §3). Keeping v1 LLM-free sidesteps the whole question; v2's intro uses DeepSeek via `llm_client.py`, never the SDK.

---

## 3. Architecture Overview

```
NEW SCHEDULED JOB  (cron; runs frequently — e.g. hourly — because send time is per-user-local)
  agent/email_digest.py   [own advisory lock — use id 45]
      Advisory-lock registry:  news=42 · (old event-calendar)=43 · audio=44 · EMAIL=45
    │
    ├─ 1. DUE USERS   query users whose email digest is enabled AND whose local
    │                 send-hour == current hour in their tz AND who have no send-log
    │                 row for this period yet.  (§ Scheduling)
    │
    │      per due user:
    ├─ 2. SELECT      reuse events.py::_build_event_query with the user's saved
    │                 filters (categories, tags, threshold) over the digest window
    │                 (calendar day / week in the USER's tz). Ranked score DESC. (§ Selection)
    ├─ 3. SKIP-EMPTY  if 0 matching events → write a 'skipped' send-log row, send NOTHING. (§8)
    ├─ 4. (v2) INTRO  optional: llm_client.py on DeepSeek → 1–2 sentence intro. Best-effort. (§2)
    ├─ 5. RENDER      render ONE email (inline-CSS HTML + plain-text alt + preheader)
    │                 from the matched events. Per-user unsubscribe token in footer/headers. (§7)
    ├─ 6. SEND        POST to ESP transactional API with List-Unsubscribe headers. (§4)
    └─ 7. RECORD      insert email_send_log row (user, period, status, message_id). Idempotent. (§6)

WEBHOOKS (ESP → us):  bounce / complaint / delivery → suppress + update send-log. (§4)
FRONTEND:  Preferences → Email digest panel (frequency/threshold/categories/send-hour/off) +
           tokenized one-click unsubscribe landing page. (§5)
```

**Why a separate job, not bolted onto `run_pipeline` or the audio job:** different cadence (this fires ~hourly to hit each user's local morning, vs the news pipeline's 6/14/22 UTC and the audio job's editorial-midnight), and independence — a pipeline or audio failure must not block email and vice-versa. It reuses the same container, DB, config, and the **fixed advisory-lock pattern** from `orchestrator.py::run_pipeline`. Model the job structure on that file.

**Reuse, don't rebuild:**
- **Selection** → `src/ai_signal/api/events.py::_build_event_query` (already parameterized by `category`, `tags`, `score_min`, `tz`, range/after/before, sort). The digest maps a user's saved prefs onto these params. Do **not** write a second event query.
- **User + prefs** → `src/ai_signal/api/auth.py` (`get_current_user`, `get_preferences`/`update_preferences`, `User.preferences` JSONB). Email settings extend the existing preferences blob (or a sibling table — §6). Do **not** build a second auth/user system.
- **Read-state / bookmarks** → existing `UserReadEvent` / `UserBookmark`. Optionally exclude already-read events from a digest, and/or badge bookmarked ones (§ Selection).
- **Timezone** → reuse the tz-aware day-boundary logic added 2026-07-07 (the `day_score` grouping in `_build_event_query` and `_safe_tz`). The digest's "day"/"week" window and the send-hour check both run in the **user's IANA tz**.
- **Scheduling/lock** → `orchestrator.py::run_pipeline` fixed advisory-lock pattern (dedicated connection, released in `finally`). Advisory lock **id 45**.
- **LLM (v2 only)** → `src/ai_signal/llm_client.py` `LLMClient("deepseek", model).complete(...)`, cost-tracked.
- **Alerting** → `features/ops_notifications.md` (`notify_forum` / `post_to_ops_category`). The send job must fail-safe and alert.
- **RSS/description HTML pattern** → `events.py::_build_rss_description` already renders an event's fields to inline-styled HTML; the email item template can borrow from it (but email HTML has stricter rules — §7).

---

## 4. Email Delivery / ESP (the big NEW dependency)

This is the one genuinely new external system. **Fastmail JMAP is used for INGESTION** (reading inbound newsletters into the pipeline) — do **not** try to reuse it for outbound. Sending *to users* needs a proper **transactional ESP** with authenticated domains, deliverability infrastructure, suppression lists, and bounce/complaint webhooks. Rolling our own SMTP from the Hetzner box is a deliverability trap (shared IP reputation, no feedback loops, blocklist risk) — do not.

### Recommendation: **Resend** (primary), **Postmark** (strong alternative) **[VERIFY pricing/limits]**

| ESP | Ease (dev) | Deliverability (small sender) | Free tier **[VERIFY]** | Notes |
|---|---|---|---|---|
| **Resend** ✅ *recommend* | Excellent — clean API, first-class React/HTML email, easy domain auth, webhooks for bounce/complaint/delivery | Good; built on SES infra + curated pools | ~3,000 emails/mo, 100/day free | Best DX for a small sender; batch send API; simple `List-Unsubscribe` support. Newer company — verify enterprise-grade needs later. |
| **Postmark** ✅ *strong alt* | Excellent — famously reliable transactional | **Best-in-class** for transactional; separate transactional/broadcast streams protect reputation | ~100/mo free, then ~$15/mo tiers | Strict about transactional-only content — a *content digest* may need their **broadcast** message stream, not the transactional one. Verify our use-case fits their policy. |
| **AWS SES** | Lower — more setup (IAM, config sets, SNS for webhooks), no template niceties | Good, but **you own reputation entirely** (warmup, complaint handling all on you) | ~$0.10 / 1,000 emails (no real free tier outside EC2) | Cheapest at scale; most ops burden. Overkill for launch; revisit if volume explodes. |
| **SendGrid** | OK, but heavier console; historically noisier shared IPs | Mixed on shared IPs for small senders | Free tier exists but throttled | Workable, not the best fit here. |

**Decision:** start on **Resend** for developer speed and a generous free tier; keep the send call behind a small `email_sender.py` interface (single `send_email(to, subject, html, text, headers, tags)` function) so the provider is swappable to Postmark/SES without touching the job. **[VERIFY Resend free-tier limits and that its `List-Unsubscribe` one-click flow is supported before committing.]**

### Domain & authentication setup (one-time, required)
- **Dedicated sending subdomain** — send from e.g. `news@mail.promptgoblins.ai` (or `updates@`), **not** the root domain. Isolating a subdomain protects the root domain's reputation (and the forum's transactional mail) from any digest deliverability issues. **[VERIFY the exact subdomain convention the chosen ESP wants.]**
- **SPF** — publish the ESP's SPF include on the sending subdomain.
- **DKIM** — add the ESP's DKIM CNAME/TXT records; verify the domain signs.
- **DMARC** — publish a DMARC record on the org domain (start `p=none` with `rua=` reporting to watch alignment, tighten to `p=quarantine`/`reject` once aligned). Ensure DKIM/SPF **alignment** with the From domain.
- **Return-Path / custom MAIL FROM** — set the ESP's custom return-path on the subdomain so bounces flow back and SPF aligns. **[VERIFY]**
- **[VERIFY] BIMI** — optional later; needs DMARC enforcement + a VMC. Not v1.

### Deliverability practices
- **Warmup** — a brand-new sending domain has no reputation. **Start small**: seed sends to Mike + a handful of opt-ins, ramp volume gradually over days/weeks. Do not blast the whole user base on day one even if opt-ins exist. (Managed ESPs on shared pools reduce but don't eliminate this — **[VERIFY current warmup guidance]**.)
- **Bounce handling (webhook)** — on a **hard bounce**, immediately add the address to a **suppression list** and stop sending. Soft bounces: retry a bounded number of times, then suppress.
- **Complaint handling (webhook)** — on a **spam complaint** (FBL), **immediately suppress and disable that user's digest** (treat a complaint as an unsubscribe). Never send to a complainer again. High complaint rates get the domain blocklisted — this is existential, not optional.
- **Delivery / open (webhook)** — optionally record delivery + opens in the send-log for observability. Opens are privacy-sensitive (§8) and unreliable — treat as informational only.
- **Rate limits** — the ESP caps requests/sec and daily volume on free/low tiers. The send job must respect them: batch or throttle, honor `429` with backoff, and never hammer the API. **[VERIFY the chosen ESP's rate limits & batch endpoint.]**

**Tradeoffs:** Resend = fastest to ship, generous free tier, good-enough deliverability, slightly less battle-tested than Postmark. Postmark = best deliverability + reputation isolation but stricter content policy (verify a content digest is allowed on its broadcast stream) and thinner free tier. SES = cheapest and most controllable but you own all the ops (warmup, FBL wiring, no templating). For a small sender optimizing ease + deliverability, **Resend now, Postmark as the escape hatch**.

---

## 5. Compliance & Unsubscribe

Email to users is legally regulated. Non-negotiable:

- **One-click unsubscribe** — every email includes a **tokenized unsubscribe link** in the visible footer **and** the machine headers:
  - `List-Unsubscribe: <https://news.promptgoblins.ai/api/email/unsubscribe?token=…>, <mailto:unsubscribe@mail.promptgoblins.ai?subject=unsubscribe>`
  - `List-Unsubscribe-Post: List-Unsubscribe=One-Click` — enables Gmail/Apple's native one-tap unsubscribe button. **[VERIFY the exact header behavior + that a POST to the URL is honored without auth.]**
  - The unsubscribe endpoint must work **without login** (the token authenticates the action) and be **idempotent**. It flips the user's digest to off, records the event, and shows a confirmation landing page.
- **Honor opt-outs promptly** — an unsubscribe takes effect **immediately** (before the next send). No "allow 10 days." A spam complaint (§4) counts as an unsubscribe.
- **CAN-SPAM** — include a **physical mailing address** in the footer, a clear From identity ("Goblin News"), no deceptive subject lines, and a functioning unsubscribe. **[VERIFY: Mike must provide a real mailing address — a P.O. box is acceptable.]**
- **GDPR / consent** — sending is **opt-in only** (digest defaults to **off**; the user must enable it). Provide a **preferences page** (below) to change or withdraw consent anytime. Store consent provenance (when they opted in, from where). Retain the minimum: email address + prefs + send log.
- **Double opt-in (consider — §8)** — because SSO gives us the address without an explicit "email me" click, **strongly consider** a one-time double-opt-in confirmation email when a user first enables the digest (send only after they click confirm). This protects deliverability (only confirmed, wanted addresses) and strengthens consent. Recommended; make it a config flag so it can be toggled.

### Manage-preferences page (Preferences → Email digest)
Extends the existing preferences UI (which already writes `User.preferences` via `PUT /api/user/preferences`). Fields:
- **Frequency:** `off` (default) | `daily` | `weekly`.
- **Signal threshold:** min score (default inherits the site default of 5; the spec examples elsewhere use 7 — let the user pick; default to their saved feed filter or 5). **[Mike: default 5 or 7? see Open Questions]**
- **Categories / tags:** default to the user's saved feed filters (`default_categories`, `default_tags`), overridable for the digest.
- **Send hour:** local hour of day (default e.g. 08:00) — used with the user's tz.
- **Weekly day** (if weekly): which weekday (default Monday or Sunday).
- **Email address:** the SSO-derived address. **Confirmed:** DiscourseConnect already sends `email` in the signed SSO payload — the callback (`auth.py` ~L277–306) just parses `external_id`/`username`/`avatar_url` and **discards it**, and `User` has no `email` column. Fix is small (see §8.15): add `User.email` (Alembic) + read `params.get("email", [None])[0]` in the callback. NOT an SSO scope change or API lookup. (Consent is the separate gate — see double opt-in.)

---

## 6. Data Model

New Alembic migration. Two concerns: **preferences** (what/when to send) and a **send log** (idempotency + deliverability tracking).

**Preferences:** store on a dedicated table rather than only the `User.preferences` JSONB, because we need to **query users by send-hour/tz/frequency efficiently** (the "who is due now" query runs hourly and must be indexable). A JSONB-only design forces a full scan.

```sql
-- one row per user who has ever configured the digest
CREATE TABLE email_digest_prefs (
  user_id        UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  enabled        BOOLEAN NOT NULL DEFAULT false,     -- opt-in; false = no sends
  frequency      TEXT NOT NULL DEFAULT 'daily',      -- 'daily' | 'weekly'
  weekly_dow     SMALLINT DEFAULT 1,                 -- 0=Sun..6=Sat, if weekly
  send_hour      SMALLINT NOT NULL DEFAULT 8,        -- local hour 0-23
  timezone       TEXT NOT NULL DEFAULT 'UTC',        -- IANA; validated like _safe_tz
  score_min      SMALLINT NOT NULL DEFAULT 5,        -- signal threshold
  categories     TEXT[],                             -- null/empty = all
  tags           TEXT[],                             -- null/empty = all
  email          TEXT,                               -- recipient (see §5 sourcing gap)
  intro_enabled  BOOLEAN NOT NULL DEFAULT false,     -- v2 DeepSeek intro toggle
  confirmed_at   TIMESTAMPTZ,                        -- double opt-in confirm time (null=unconfirmed)
  unsub_token    UUID NOT NULL DEFAULT gen_random_uuid(),  -- stable per-user unsubscribe token
  consent_at     TIMESTAMPTZ,                        -- when they opted in
  suppressed_at  TIMESTAMPTZ,                        -- hard-bounce/complaint kill switch (overrides enabled)
  suppressed_reason TEXT,                            -- 'bounce' | 'complaint' | 'manual'
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_email_prefs_due
  ON email_digest_prefs (enabled, frequency, send_hour)
  WHERE enabled AND suppressed_at IS NULL;

-- one row per (user, period) — the idempotency + deliverability ledger
CREATE TABLE email_send_log (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  frequency     TEXT NOT NULL,                       -- 'daily' | 'weekly'
  period_key    TEXT NOT NULL,                       -- e.g. 'daily:2026-07-08' or 'weekly:2026-W28' (in user's tz)
  status        TEXT NOT NULL,                       -- 'sent' | 'skipped_empty' | 'suppressed' | 'failed'
  event_ids     UUID[],                              -- events included (audit/debug)
  event_count   INT NOT NULL DEFAULT 0,
  esp_message_id TEXT,                               -- provider message id (correlate webhooks)
  opened_at     TIMESTAMPTZ,                         -- optional, from webhook
  bounced_at    TIMESTAMPTZ,
  complained_at TIMESTAMPTZ,
  llm_cost_usd  NUMERIC(10,6) DEFAULT 0,             -- v2 intro cost
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, period_key)                       -- IDEMPOTENCY: never double-send a period
);
CREATE INDEX ix_email_send_log_msgid ON email_send_log (esp_message_id);
```

- `UNIQUE (user_id, period_key)` is the **idempotency guarantee** — the send job inserts the log row (status `sent`/`skipped_empty`) **before or transactionally with** the send; a duplicate run for the same period no-ops on the unique violation. `period_key` is computed in the **user's tz** so DST/tz never causes a double or missed period.
- `suppressed_at` is the **kill switch** and overrides `enabled` everywhere — a hard bounce or complaint sets it; the due-users query filters it out.
- `unsub_token` is stable per user (a UUID; not guessable) and is what the `List-Unsubscribe` URL carries.
- Advisory lock id for the job: **45** (registry: news=42, old event-calendar=43, audio=44). Keep a comment noting the registry.
- **Email sourcing (small, confirmed fix):** the address IS in the SSO payload; add `User.email` + read it in the callback + backfill on next login (§8.15). Old users get an address the next time they log in via SSO; a one-time Discourse API backfill is optional.

---

## 7. HTML Email Rendering Gotchas (READ — email is not the web)

Email clients are a decade behind browsers; the site's Next.js components will **not** render. Build a dedicated, boring, bulletproof template.

- **Inline CSS only.** No `<style>` blocks relied upon (Gmail strips/limits them), no external stylesheets, no `<link>`. Every style is a `style="…"` attribute. (`events.py::_build_rss_description` already does inline styles — good starting reference, but tighten for email.)
- **Table-based layout.** Use nested `<table>`s with explicit widths for structure — flexbox/grid don't work in Outlook (Word rendering engine). Single-column, max ~600px wide, centered.
- **No JS, no forms, no web fonts you depend on.** Provide system-font stacks; treat any web font as progressive enhancement.
- **Dark mode.** Support `prefers-color-scheme` where clients honor it (Apple Mail, some Gmail), but **don't rely on it** — pick colors that read in both. Set explicit `background-color` on containers; avoid pure-white logos on transparent (invert in dark mode). Test Apple Mail dark mode explicitly (it re-colors aggressively).
- **Plain-text alternative part (required).** Always send a `text/plain` alternative alongside `text/html` — improves deliverability and serves text-only clients. It's a simple ranked list with URLs.
- **Preheader text.** Include hidden preheader text (the inbox preview snippet) — e.g. "Your 6 highest-signal AI stories for Tuesday." Hide it visually but keep it first in the DOM.
- **Images.** Minimize; many clients block images by default. The logo can be a hosted image with solid `alt` text, but the digest must be fully legible with images off. **No tracking pixel is required** (§8) — if the ESP injects one, that's its call, not ours.
- **Links.** Absolute `https://news.promptgoblins.ai/event/{slug}` URLs (reuse the slug pattern from `events.py`). Consider UTM params for attribution (`?utm_source=email&utm_medium=digest`) so Umami can attribute click-throughs.
- **Keep it lightweight.** Gmail **clips messages over ~102 KB** — a long digest gets truncated with a "[Message clipped]" link. Cap the number of events (e.g. top ~10–15), keep markup lean, don't inline base64 images.
- **Test across clients.** Gmail (web + app), Apple Mail (macOS + iOS, light + dark), Outlook (web + desktop). Use a render-test service (Litmus/Email on Acid) or at minimum manual sends to real accounts. **[VERIFY current client quirks.]**
- **Accessibility.** Semantic-ish tables with `role="presentation"` on layout tables, real `alt` text, sufficient contrast, logical reading order for screen readers.

### Email content structure (per send)
1. **Preheader** (hidden): count + day.
2. **Header:** small Goblin News logo/wordmark + "Your AI briefing — Tuesday, July 8" (date in user's tz).
3. **(v2) Intro:** 1–2 sentence synthesized summary (DeepSeek), if enabled.
4. **Ranked event list** — for each event: **signal badge** (e.g. "Signal 8"), **title** (linked to `/event/{slug}`), **one-liner** (first line of `tier1_scan` or a dedicated summary field), **category** chip. High-to-low signal.
5. **Cross-promo:** "🎧 Prefer to listen? Get the 5-minute audio briefing →" (link to `/listen`) — §10.
6. **Footer:** manage-preferences link, one-click unsubscribe link, physical address, "you're getting this because you enabled the Goblin News digest."

---

## 8. Gotchas & Things To Consider (overrides naïve choices above)

1. **Never send an empty digest.** If a user has zero matching events for the period, **skip** (write `skipped_empty` to the log) — do not send a "no news today" email. Empty/near-empty sends annoy users, tank engagement, and raise complaint rates. Consider a **minimum-events floor** (e.g. skip if < 1; optionally skip daily if < 2 and roll into weekly — decide with Mike).
2. **Timezone correctness for send time.** The "due now" check and the digest window are both in the **user's IANA tz**, using real zone math (DST-aware), reusing `_safe_tz`. The job runs ~hourly in UTC and, for each user, asks "is it their `send_hour` right now in their tz, and do they lack a log row for this period?" Never use fixed offsets.
3. **Idempotency is structural, not hopeful.** The `UNIQUE (user_id, period_key)` constraint is the real guard (§6). If the job crashes mid-batch and reruns, already-logged users are skipped by the unique violation. Compute `period_key` in the user's tz so a DST shift can't create a duplicate or a gap.
4. **Deliverability / reputation is existential.** Start small, warm up (§4). A spike of bounces or complaints on a young domain gets you blocklisted, which poisons *all* mail from that subdomain. This is why: opt-in only, double-opt-in considered, skip-empty, instant unsubscribe, auto-suppression.
5. **Bounce/complaint auto-suppression.** Webhooks must set `suppressed_at` immediately; the due-users query excludes suppressed users. A complaint = permanent stop for that address. Never resurrect a suppressed address without an explicit new opt-in.
6. **Unsubscribe must be instant and honored.** Tokenized, works without login, idempotent, takes effect before the next send. `List-Unsubscribe` + `List-Unsubscribe-Post` for native one-click. Test it (§ Testing).
7. **Never leak one user's data to another.** Each email is rendered from **one user's** filtered events and carries **that user's** unsubscribe token. A batch-send bug that reuses the wrong recipient/token is a privacy incident. Assert `to`, token, and body are built per-user inside the loop — never share mutable render state across users. Do not put another user's identifiers anywhere in the payload.
8. **Rate limits of the ESP.** Free/low tiers cap req/sec and daily volume. Batch or throttle, honor `429` with backoff, and if the batch exceeds the daily cap, defer the remainder (they'll still have no log row → picked up next run) rather than dropping them. **[VERIFY caps.]**
9. **Fail-safe + alert.** Wrap the job; a per-user send failure marks that user's log `failed` and continues to the next user (one bad address must not abort the batch). A systemic failure (ESP down, auth broken) must **alert Mike** via the `ops_notifications` mechanism (`notify_forum`/`post_to_ops_category`). Silent email outages erode the retention flywheel.
10. **Privacy of email addresses.** Email is PII. Store minimally, never log full addresses in plaintext app logs (log user_id + a hash), scope DB access, and honor deletion (SSO user deletion cascades via FK). Don't expose addresses in any API response.
11. **Double opt-in consideration.** Because SSO hands us an address without an explicit "email me" action, an unconfirmed enable is weak consent and risky for deliverability. Strongly consider requiring a confirm click before the first send (config-flagged). Recommended for launch.
12. **Open tracking is optional and privacy-sensitive.** Don't add tracking pixels for their own sake. If the ESP provides opens, treat as informational; consider disabling to respect privacy and because Apple Mail Privacy Protection makes opens meaningless anyway.
13. **Gmail clipping (§7)** — cap event count and keep markup lean so the digest doesn't get truncated (which also hides the unsubscribe footer — a compliance problem).
14. **Content-policy fit (Postmark).** If we switch to Postmark, a *content digest* likely belongs on its **broadcast** stream, not transactional — verify before assuming.
15. **Email sourcing (small, confirmed).** DiscourseConnect already includes `email` in the signed SSO payload; the callback (`auth.py` ~L277–306) parses `external_id`/`username`/`avatar_url` and drops it, and `User` has no `email` column. **Fix:** add `User.email` (Alembic migration, nullable, indexed for the send query), read `params.get("email", [None])[0]` in the callback, validate/store it, upsert on each login. Existing users populate on their next SSO login (optional one-time Discourse `/users/{username}.json` backfill). This is a ~10-line prerequisite, **not** a scope change. Consent (double opt-in) is the separate gate — a forum signup is not consent to be emailed.
16. **Frequency = weekly means a different window.** Weekly digests select the last 7 days (calendar week in user tz) and should probably raise the effective threshold or cap count (a week of 5+ events is a lot). Decide default behavior with Mike.

---

## 9. Cost Model (estimate — track actuals)

| Item | Basis | ~Monthly |
|---|---|---|
| **ESP (v1)** | Templated sends. Small user base → within free tier. | **$0** on Resend (~3k/mo free) or Postmark (~100/mo free) **[VERIFY]**. At scale: SES ~$0.10/1k, Resend/Postmark paid tiers ~$15–20/mo for tens of thousands. |
| **LLM intro (v2, optional)** | 1 DeepSeek call/user/send, ~1–2k in / ~80 out. DeepSeek ~$0.44/M in, $0.87/M out. | **Pennies.** ~$0.001/send → e.g. 100 users daily ≈ **~$3/mo**; 1k users daily ≈ **~$30/mo**. Scales with users — keep it optional/off by default; this is the only line that grows with the base. |
| **Storage** | Two small tables. | **~$0** |
| **Render/test tooling** | Litmus/Email-on-Acid (optional, or free manual testing) | $0–~$100/mo if you buy a render service |
| **Total (v1)** | | **~$0/mo** until volume crosses ESP free tiers |
| **Total (v2)** | | **ESP free-tier + a few $ of DeepSeek**, scaling with users |

Cheap because v1 renders existing content with no LLM. Report per-run actuals (users sent, skipped, failed, and any LLM cost) after v1 — Mike wants cost visibility, and the digest's cost story is "basically free, and the intro is the only thing that scales with the base."

---

## 10. Promotion & Growth Strategy

Email is the **retention flywheel** — the cheapest way to bring people back on a habit. Exploit the surfaces we own and cross-wire it with the audio show.

- **Reciprocal cross-promo with audio.** Every email footer promotes the podcast ("🎧 Prefer to listen? 5-minute audio briefing →" → `/listen`), and every podcast episode / the `/listen` page promotes the email ("📬 Get it in your inbox each morning →"). Audio and email are siblings; each is the other's top-of-funnel (this is already noted in `audio_briefing.md §16`).
- **On-site capture.** A persistent, low-friction **"Get the daily briefing in your inbox"** call-to-action on the site (feed page + a dedicated `/email` or the preferences panel). For logged-in users it's a one-click enable; for anonymous, it routes through SSO login then enable. Consider a lightweight email-capture even pre-login (but sending still requires a confirmed opt-in — §5).
- **The hook / positioning:** same signal-first message as the show — *"The AI news that matters, ranked. The 7-plus stories, in your inbox, every morning. Nothing else."* Personalized ("matching your filters") is the digest's edge over the fixed podcast.
- **Reliability = compounding retention.** Same time every day, correct content, never a broken or empty send. Consistency is the entire growth mechanism for a digest — which is why the fail-safe/alert (§8.9) is a growth feature, not just ops.
- **Forum tie-in.** Reuse the existing **Discuss** path (event → forum topic); a digest item can link to its discussion if one exists. Do **not** auto-post digests to the forum.

---

## 11. Definition of Done (per phase)

### v1 — Templated digest
**Automated checks**
- [ ] Alembic migration creates `email_digest_prefs` + `email_send_log`; `alembic upgrade head` clean, downgrade works.
- [ ] Unit test: due-users query returns exactly the users whose local `send_hour` == now, enabled, unsuppressed, unconfirmed excluded (if double-opt-in on), and without a log row for the period.
- [ ] Unit test: `period_key` computed in user tz is stable across a rerun (idempotency); a second run for the same period inserts no new send.
- [ ] Unit test: skip-empty writes `skipped_empty` and sends nothing.
- [ ] Render test: HTML passes inline-CSS lint; plain-text alt present; unsubscribe headers present.
- [ ] Job holds advisory lock **45** on a dedicated connection, released in `finally` (mirrors `run_pipeline`).

**Acceptance criteria**
- [ ] A seed user with saved filters receives a correctly-ranked digest at their local send hour.
- [ ] A user with zero matches receives nothing (logged `skipped_empty`).
- [ ] One-click unsubscribe (header + link) disables the digest immediately and shows a confirmation page.
- [ ] Bounce and complaint webhooks set `suppressed_at`; suppressed users are never sent to.
- [ ] SPF/DKIM/DMARC pass; **mail-tester.com ≥ 9/10**.
- [ ] No double-send across a forced job rerun.
- [ ] Preferences page: frequency (off/daily/weekly), threshold, categories, send-hour all persist and take effect.
- [ ] A systemic send failure alerts Mike via `ops_notifications`.

### v2 — Synthesized intro
- [ ] Intro generated via `llm_client.py` DeepSeek, ≤ 2 sentences, cost logged to `email_send_log.llm_cost_usd`.
- [ ] LLM failure/timeout falls back to no-intro and still sends (never blocks/delays).

### v3 — Storyline follow (gated on `storylines.md`)
- [ ] Deferred until storylines exists; reuses ESP, send-log, unsubscribe, rendering.

Each milestone: update this doc's status + a session log; add a `knowledge/gotcha_*.md` for anything that cost >30 min (e.g., DKIM alignment, `List-Unsubscribe-Post` behavior, Outlook table quirks, mail-tester findings).

---

## 12. Testing Strategy

- **Seed-user sends (v1 gate):** enable the digest for Mike + a few opt-ins; run the job for a week; confirm correct content, timezone, ranking, and no double-sends.
- **Deliverability test:** send to **mail-tester.com** and iterate to ≥ 9/10 (SPF/DKIM/DMARC/alignment, spam-score, no blocklist). Re-run after any From/domain change.
- **Render tests:** send to real Gmail (web+app), Apple Mail (macOS+iOS, light+dark), Outlook (web+desktop); verify layout, dark mode, images-off legibility, no Gmail clipping, working links. Optionally Litmus/Email-on-Acid.
- **Idempotency test:** run the job twice for the same period → exactly one send per user; unique-constraint prevents the second.
- **Skip-empty test:** a user with no matching events in the window → `skipped_empty`, zero emails.
- **Unsubscribe test:** click the footer link AND POST the `List-Unsubscribe` URL (one-click) → digest disabled immediately, confirmation shown, next run skips them.
- **Suppression test:** simulate a bounce/complaint webhook → `suppressed_at` set, user excluded from the next run.
- **Failure injection:** ESP returns 5xx/429 for one user → that user logged `failed`, batch continues; ESP fully down → alert fires, nothing double-sends on retry.
- **Privacy test:** assert each rendered email's `to` + unsubscribe token match the intended user (no cross-user leakage) across a multi-user batch.
- **Timezone/DST test:** users in multiple tzs (incl. one crossing a DST boundary) each get exactly one send per period at their local hour.

---

## 13. Open Questions for Mike
- **Email address sourcing:** confirmed small fix — email is already in the SSO payload, just add `User.email` + read it (§8.15). Not a blocker in the scary sense; just do it first. Decision: one-time Discourse API backfill for existing users, or let them populate on next login?
- **Double opt-in:** require a confirm click before the first send? (Recommended — safer consent + deliverability.)
- **Default threshold:** digest `score_min` default 5 (site default) or 7 (higher-signal, matches the audio show's floor)?
- **Empty/thin-day floor:** skip daily if < N events? Roll thin days into weekly?
- **Weekly behavior:** which weekday, and raise threshold / cap count for the 7-day window?
- **ESP choice:** Resend (recommended) vs Postmark — any existing account/preference? Confirm the sending subdomain (`mail.` / `updates.`) and From name/address.
- **Physical mailing address** for the CAN-SPAM footer (P.O. box fine).
- **Open tracking:** on (observability) or off (privacy)? Default off.
- **v2 intro:** ship it, and on-by-default or opt-in per user?
- **Send cadence of the job:** hourly is simplest for per-user-local send hours — acceptable, or prefer coarser (e.g. every 15/30 min) for tighter send-time accuracy?

---

## References
> **AGENT:** Read these for context before implementing.

- **Sibling feature:** `features/audio_briefing.md` — the text/audio pair; shares the scheduled-job pattern, `llm_client.py` usage, tz handling, advisory-lock registry (audio=44, email=45), and the reciprocal cross-promo strategy. Match its depth and the "re-render existing assets" principle.
- **Selection:** `src/ai_signal/api/events.py::_build_event_query` (reuse for per-user filtered selection; `effective_score = coalesce(community_score, importance_score)`; tz-aware `day_score` grouping + `_safe_tz`, added 2026-07-07). Also `_build_rss_description` for an inline-styled HTML-render reference.
- **Users / prefs / read-state / bookmarks:** `src/ai_signal/api/auth.py` — DiscourseConnect SSO (`get_current_user`, `require_user`), `get_preferences`/`update_preferences`, `PreferencesUpdate` (extend for email fields), `UserReadEvent`, `UserBookmark`. **Note the email-sourcing gap** (callback extracts username/avatar/trust, not email).
- **User model:** `src/ai_signal/models/user.py` — `User.preferences` JSONB shape; add `email_digest_prefs` + `email_send_log` (§6).
- **LLM (v2):** `src/ai_signal/llm_client.py` — `LLMClient("deepseek", model).complete(system, prompt, max_tokens)`, cost-tracked. **User-facing generation must use this (DeepSeek), NOT the Agent SDK / Claude Code subscription** (quota is shared with Mike's interactive use — see MEMORY + audio_briefing §6).
- **Scheduling / advisory lock:** `agent/orchestrator.py::run_pipeline` — copy the **fixed** lock pattern (dedicated connection, `pg_try_advisory_lock(45)`, released in `finally`). Model `agent/email_digest.py` on this file's structure.
- **Alerting:** `features/ops_notifications.md` — `notify_forum` / `post_to_ops_category` for fail-safe alerts on send failures.
- **Storylines (v3 dependency, not yet written):** `features/storylines.md` — per-storyline follow emails depend on it; do not build v3 until it lands.
- **Config / deploy:** `src/ai_signal/config.py` `Settings` (add ESP + email env vars); `deploy/cron/pipeline-cron` (add the hourly email job line); `docker-compose.prod.yml`; nginx (unsubscribe + webhook endpoints); `DEPLOYMENT.md`.
- **New config/env:** `RESEND_API_KEY` (or `POSTMARK_API_KEY` / SES creds), `EMAIL_FROM` (e.g. `Goblin News <news@mail.promptgoblins.ai>`), `EMAIL_SUBDOMAIN`, `EMAIL_WEBHOOK_SECRET`, `EMAIL_DOUBLE_OPT_IN` (bool), `EMAIL_PHYSICAL_ADDRESS`, `EMAIL_INTRO_PROVIDER`/`EMAIL_INTRO_MODEL` (v2, deepseek), `DEEPSEEK_API_KEY` (already used by `llm_client.py`).
