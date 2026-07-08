# Goblin News — Feature Roadmap

**Last Updated**: 2026-07-08

## Priority Order

### Tier 1 — Ship the Product (Complete)

| # | Feature | Complexity | Doc | Status |
|---|---------|-----------|-----|--------|
| 1 | **Production Deployment** | C3 | [production_deployment.md](production_deployment.md) | Shipped |
| 2 | **Grok Sentiment (two-pass)** | C2 | [sentiment_reactions.md](sentiment_reactions.md) | Shipped |
| 3 | **UI Overhaul (modal, WTM, view toggle)** | C2 | — | Shipped |
| 4 | **Ops Notifications (forum bot)** | C1 | [ops_notifications.md](ops_notifications.md) | Planning |

### Tier 2 — Community Integration (Complete)

| # | Feature | Complexity | Doc | Status |
|---|---------|-----------|-----|--------|
| 5 | **Forum Auth (Discourse SSO)** | C2 | [forum_auth.md](forum_auth.md) | Shipped |
| 6 | **Discuss Button** | C2 | [discourse_integration.md](discourse_integration.md) | Shipped |
| 7 | **RSS Feeds** | C1 | [rss_feeds.md](rss_feeds.md) | Shipped |
| — | **Community Voting** | C2 | [community_voting.md](community_voting.md) | Shipped |

### Tier 3 — Growth Features

| # | Feature | Complexity | Doc | Status |
|---|---------|-----------|-----|--------|
| 8 | ~~AI Event Calendar~~ | C3 | [event_calendar.md](event_calendar.md) | **Killed 2026-04-07** — built then archived. See archive doc for revival recipe. |
| 9 | ~~Curated Blogs & Research~~ | C2 | [curated_content.md](curated_content.md) | **Deferred** — see decision record |
| 10 | **Audio Briefing** (daily/weekly podcast) | C3 | [audio_briefing.md](audio_briefing.md) | Planning (spec'd 2026-07) |
| 11 | **Storylines** (living-thread pages + synthesis engine) | C3 | [storylines.md](storylines.md) | Planning (spec'd 2026-07) — unlocks catch-me-up, "what happened with X", topic emails, social drafts |
| 12 | **Email Digest** (daily/weekly, per-user filters) | C2 | [email_digest.md](email_digest.md) | Planning (spec'd 2026-07) |

**Sequencing note (2026-07-08):** Audio and Storylines are the two high-leverage plays; the Email Digest shares infra with both (scheduled job + `llm_client.py` + tz). Storylines is the engine that also powers catch-me-up / semantic-ask / topic-emails / social — highest leverage per build. User-facing generation (storylines, email intros, catch-up) runs on **DeepSeek via `llm_client.py`**, NOT the Claude subscription (the sub can't serve per-user features). Discord/Slack push bot = **parked** until requested (push model = per-subscriber webhook registry + retries = ongoing surface area, unlike pull-based RSS/podcast).

---

## Sequencing Logic

**Why this order:**

1. **Production deployment first** — nothing else matters until it's live
2. **Grok sentiment before deploy** — easier to test locally, adds value from day one. Can also be done in parallel with deploy prep since it's pipeline-side only
3. **UI overhaul** — already in progress (plan exists), makes the reading experience good before going public
4. **Ops notifications** — small effort, huge operational value once live
5. **Forum auth** — prerequisite for Discuss button and user preferences
6. **Discuss button** — depends on auth, creates the forum ↔ news flywheel
7. **RSS feeds** — small effort, big value for power users
8. **Event calendar** — new data model + UI + discovery pipeline = essentially a second product. High value but ship news first.
9. ~~Curated content~~ — **Deferred**. News pipeline already picks up noteworthy research/blogs. Dedicated pipelines are costly, hard to tune for signal quality, and the forum is a better venue for community-curated content. See [curated_content.md](curated_content.md) for full decision record.

---

## Cross-Cutting Concerns

### Claude Code Subscription Management
- OAuth token stored in Docker volume
- Refresh utility: `scripts/refresh-claude-auth.sh`
- Ops bot reminds Mike at 60/30/15/7/daily before expiry
- Budget: start with $20/mo, upgrade to $100 if needed
- Rate limit handling: exponential backoff + ops notification

### Claude Code Updates
- Track `claude --version` on each pipeline run

### Ingestion Health Audit (noted 2026-07-08 — TODO)
**We need to periodically verify ingestion is still healthy and sources haven't silently broken.** We've had source issues before (silent ingest decay incident; see `_status.md` and the rate-limit-cascade / monitoring knowledge). This is partly covered by existing pieces but not fully wired:
- **What exists:** the `/admin/health` dashboard (content + pipeline diagnostics, incl. stale-source detection) and the `ops_notifications.md` spec (per-source ingest-drop alerts, 0-events-in-24h alert) — the latter is **still Planning, not built**.
- **The gap / TODO:** (1) **build** the ops_notifications alerts (a stale/broken source should page, not decay silently); (2) run a **periodic manual source audit** — are all ~26 sources still returning content, any feed URLs 404/changed, any source producing junk or nothing, do we need to add/drop sources; (3) consider a scheduled automated source-health check (last-article-age per source → alert if a source goes quiet beyond its normal cadence).
- **Related docs:** `ops_notifications.md`, `pipeline_v2_source_quality.md`, `_status.md` (union-find + rate-limit incidents).
- **Priority:** not urgent-now, but do before/alongside launching audio + email (a broken pipeline makes a *missing podcast episode / empty digest* very visible to subscribers — reliability becomes a growth feature).
- Notify Mike via forum bot when version changes
- Test pipeline output quality after model updates
- Eventually migrate to API when revenue supports it

### Pipeline Schedule
- 2x daily (6am + 6pm UTC) for news
- Sentiment Pass 2: daily cron for events 3-7 days old
- Event calendar: TBD (less frequent, events don't change rapidly)

### Security Model
- Agent container isolated (no inbound network)
- All LLM output sanitized before DB insert
- Discourse bot has minimal API permissions
- User auth via Discourse (no passwords stored locally)
- Content from pipeline treated as untrusted

---

## Pipeline Bugs — Status

Observed during 2026-03-09 pipeline run:

1. **PDF null bytes**: Newsletter ingestion crashed on a PDF link (MIT Tech Review report). `raw_content` contained binary PDF data with null bytes → PostgreSQL rejected it. Fix: detect non-text content types and skip or store as metadata only. **Status: Open**

2. ~~**Mega-cluster**: 153 articles landed in 1 cluster.~~ **FIXED** — Root cause was union-find transitive closure, not cold-start. Replaced with HyDE clustering (Haiku normalization → embed → similarity graph). See `docs/plan/plan_section_event_intelligence.md` for full postmortem.

3. **Newsletter extraction failure**: The Neuron newsletter returned markdown-wrapped JSON instead of raw JSON. **FIXED** — Parser now strips markdown code fences before JSON parse.

4. **Distillation quality on low-signal events**: Tier3 details were 1-2 words + context for lower-importance stories. **FIXED** — Caused by mega-cluster (agent fatigue), not model capability. With correct clustering + Sonnet for all distillation, this should be resolved. Needs validation on next run.
