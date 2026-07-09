# Current Phase — "Foundation + Analytics + Storylines Engine"

**Started:** 2026-07-09 · **Owner:** Mike · **Status:** Planning → ready to build

> This is the single "what we're building now" doc — follow along here. Detailed
> designs live in the linked feature specs; this doc is the **ordered checklist**
> that ties them together with dependencies and acceptance criteria.
>
> **Phase goal:** make the pipeline reliable and measurable, then build the
> **storylines engine** — the keystone that both deepens the product on-site
> (SEO + narrative depth) and becomes the **context source** every later surface
> (podcast, email, catch-up, "what happened with X", social) draws on. With zero
> users yet, this phase is about acquisition surface (storyline SEO) + the engine,
> on a reliable base — not retention features.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## Dependency map for this phase

```
0. FOUNDATION ───────────────────────────────► unblocks all
     ├─ deploy pending branch (incl. analytics CSP fix + daily-top fix + audit)
     ├─ ingestion health + ops alerts (reliability)
     └─ User.email capture (unblocks Email Digest, next phase)

1. ANALYTICS (Umami) ── needs: branch deployed (CSP fix)

2. STORYLINES ENGINE ── the keystone
     ├─ new + UPDATED event awareness
     └─ emits a CONTEXT OBJECT ──► consumed later by podcast / email / catch-up / ask

3. (parallel, cheap) AUDIO M0 listen-test ── go/no-go for the full podcast (next phase)
```

---

## 0. Foundation (do first — small, unblocks everything)

### 0.1 Ship the pending branch  `[ ]`
Merge + deploy `audit-remediation-2026-07-04` (carries the security/bug fixes, the **daily-top timezone fix**, AND the **CSP fix that unblocks Umami analytics**), then reload nginx.
- **Ref:** `sessions/2026-07-04-audit-remediation.md`; deploy skill (`./deploy/deploy.sh` + `docker exec nginx-proxy nginx -s reload`).
- **Done when:** site 200, `/api/health` ok, right commit live, daily-top ordering correct in-browser, no CSP console errors from the Umami script.

### 0.2 Ingestion health audit + build ops alerts  `[ ]`
We've had silent source decay before; reliability must precede any subscriber-facing launch.
- **Audit (can do anytime):** verify all ~26 sources still produce; flag dead/404 feeds, quiet sources, junk. (Claude can run this live on request.)
- **Build:** the `ops_notifications` alerts (per-source drop, "0 events in 24h") — spec'd, still unbuilt.
- **Ref:** `features/ops_notifications.md`, `features/pipeline_v2_source_quality.md`, ROADMAP "Ingestion Health Audit".
- **Done when:** a stale/broken source pages instead of decaying silently; audit shows all sources healthy (or issues logged + fixed).

### 0.3 `User.email` capture  `[ ]`
Small prerequisite for the (next-phase) email digest — do it now while it's cheap.
- Add `User.email` (Alembic, nullable, indexed), read `params.get("email", [None])[0]` in the SSO callback (`api/auth.py` ~L296–306), validate/store, upsert on login. Email is **already in the DiscourseConnect payload** — just captured. Optional one-time Discourse API backfill for existing users.
- **Ref:** `features/email_digest.md` §8.15.
- **Done when:** new/returning SSO logins populate `User.email`; no behavior change otherwise.

---

## 1. Analytics rollout (Umami)  `[ ]`
**Status of what exists:** the tracker is already wired in the frontend (`frontend/src/app/layout.tsx`, gated by `NEXT_PUBLIC_UMAMI_WEBSITE_ID` + `NEXT_PUBLIC_UMAMI_SRC`); Umami is self-hosted at `analytics.promptgoblins.ai` (memory `reference_umami_analytics.md`). **There is NO dedicated analytics plan doc** — this section is it. The audit found the tracker **CSP-blocked → ~zero data**; the fix is on the branch (0.1).

- `[ ]` **Deploy the CSP fix** (0.1) so `analytics.promptgoblins.ai` is allowed in `script-src` + `connect-src`.
- `[ ]` **Confirm env vars are set in the prod build** — `NEXT_PUBLIC_UMAMI_WEBSITE_ID` + `NEXT_PUBLIC_UMAMI_SRC` are `NEXT_PUBLIC_*` (baked at build), so verify they're present when `ai-signal-web` is built, and the website is registered in the Umami dashboard.
- `[ ]` **Verify data flows** — load prod, confirm no CSP violations in console, confirm hits appear in the Umami dashboard.
- `[ ]` **Add custom events** (Umami `data-*` / `umami.track`) for the actions that matter: event opens, "Discuss" clicks, votes, bookmarks, RSS/subscribe clicks, filter/score usage. (Later: audio plays, email opens, storyline views.) These are the metrics that tell us what's working once features ship.
- **Done when:** real pageviews + a first custom event show up in Umami for prod traffic.

---

## 2. Storylines engine (the keystone)  `[ ]`
Full design: **`features/storylines.md`** (M1 scope). Build the engine + read-only pages. This is the biggest item in the phase.

- `[ ]` **Data model** — `storylines`, `storyline_events` (+ `storyline_follows` stub for later). Alembic migration. Advisory lock **id 46**.
- `[ ]` **Detection/assignment job** (`agent/storylines.py`, own lock, runs after the pipeline) — embedding candidate match + DeepSeek judge (`llm_client.py`), conservative; promotion threshold (`MIN_EVENTS`/`MIN_SPAN`) to prevent sprawl.
- `[ ]` **New + UPDATED event awareness** *(2026-07-09 addition)* — the job triggers on events that are new **or updated** (new `EventUpdate` / bumped `update_count`), re-synthesizes the affected storyline, and the narrative **attributes the shift** ("[outlet] now also reporting, adds [angle]") rather than silently rewriting. See `storylines.md` §6.1.
- `[ ]` **Synthesis → context object** *(2026-07-09 addition)* — emit a reusable per-storyline object `{title, narrative_md, one_liner, whats_new, member_event_ids, status}`, only-on-change, on DeepSeek. This is what the podcast/email/catch-up/ask consume later. See `storylines.md` §6.2.
- `[ ]` **One-time backfill** over existing ~3k events (respect the promotion threshold; budget the DeepSeek cost).
- `[ ]` **Frontend** — `/storyline/[slug]` (narrative + timeline showing event updates), `/storylines` index, "part of: [storyline]" links on events. JSON-LD + canonical for SEO.
- `[ ]` **Tune thresholds** on real data (expect iteration, like the HyDE thresholds).
- **Done when:** related events auto-group into sensible, non-sprawly storylines; pages render narrative + timeline (with updates); the context object is queryable for downstream; job fails safe + alerts; DeepSeek spend tracked and low.

---

## 3. (Parallel, cheap) Audio M0 — the listen test  `[ ]`
Not the full podcast build (that's next phase) — just the **go/no-go spike**. Full design: `features/audio_briefing.md` (M0 + cowboy-mode regeneration harness).
- `[ ]` Generate a sample episode from a real recent day: select → script (A/B DeepSeek vs Anthropic-API vs Grok via `llm_client.py`) → ElevenLabs (audition a Voice Design custom voice) → stitch with a Suno intro/outro. No DB, no cron, no feed.
- `[ ]` **Listen test:** does Mike want to subscribe? Tune prompt/voice/word-ranges by regenerating.
- **Done when:** Mike has heard it and decided whether to green-light the full audio build (and locked a rough voice + script style).
- **Note:** once storylines M1 exists, regenerate an M0 episode **with storyline context** injected to hear the difference (situational takes vs robotic) — this validates the storyline→podcast connection before the full build.

---

## Explicitly NEXT phase (NOT now)
- **Audio full pipeline** (daily → weekly recap; weekly reuses storyline synthesis; consumes storyline context + update-awareness).
- **Email digest** (v1 templated → DeepSeek intro → storyline-follow emails). Needs 0.3 done.
- **Storyline-powered surfaces:** catch-me-up, "what happened with X" / semantic ask, social clips/posts.
- **Parked:** Discord/Slack push bot (until requested).

## Key constraints carried into this phase
- **User-facing generation → DeepSeek via `llm_client.py`, never the Claude sub** (storylines synthesis, later email intros/catch-up). The sub is Mike's personal shared quota; can't serve per-user features.
- **Reliability is a feature** — 0.2 lands before subscriber-facing launches.
- **Advisory-lock registry:** news=42, event-calendar=43 (dead), audio=44, email=45, storylines=46.

## References
- Specs: `features/storylines.md`, `features/audio_briefing.md`, `features/email_digest.md`, `features/ops_notifications.md`.
- Session: `sessions/2026-07-04-audit-remediation.md` (the pending branch). Roadmap: `features/ROADMAP.md`.
