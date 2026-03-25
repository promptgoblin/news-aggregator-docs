# Project Status

**Last Updated**: 2026-03-25

## Active Phase
**Phase**: Phase 2 — Foundation
**Phase Status**: In Progress — Pipeline running, community voting live, preparing for event calendar feature

## Current Session

**Working On**: Event calendar feature (next)
**Status**: All Phase 2 features shipped. Community voting, admin tools, security hardened. Ready for new features.

## Recent Changes

### 2026-03-23 — 2026-03-25

- **Community voting**: Up/down vote on events with reputation-weighted scoring. Diminishing returns curve (hard to push 9→10), consensus bonus, membership scaling. Scores become fractional (2 decimal) when voted. Vote buttons after summary section.
- **Admin tools**: Score adjust (+1/-1 with required reason for prompt tuning dataset), category change (dropdown), source attribution (shows which feed surfaced each article)
- **Share button**: Copy permalink, share to X, share to LinkedIn. In modal footer and permalink page.
- **Modal persistence**: Event slug in URL (`?event=slug`) survives browser refresh
- **Sentiment Pass 2**: Re-checks high-scoring events with no X discussion after 24h. Fixed Grok prompt hedging "Limited" when reactions were found.
- **Opinion-vs-fact guardrails**: Distiller, editor, QC prompts now require attribution for opinion/analysis articles
- **Bug fixes**: Day headers on week/month (flat list now), mobile search zoom (16px input), duplicate day headers (Map merge), sidebar stale searchParams
- **Security (round 3)**: Admin from Discourse admin flag (dynamic, not hardcoded), HTML sanitization on admin inputs, UUID validation, slug validation, `is_admin` on User model synced from SSO
- **Admin auth**: Dynamic from Discourse — whoever is admin on the forum is admin on AI Signal. No hardcoded IDs.

### 2026-03-12 — 2026-03-23

- **Signal score filter**: Tappable number buttons (5–9) to filter minimum signal score, wired to RSS feed
- **RSS feed**: Full-content RSS endpoint with details table, mobile-friendly HTML
- **Bookmarks/save**: Save events for later, bookmark filter inline under Read Status in sidebar
- **Day group headers + infinite scroll**: Feed grouped by day with styled headers, loads more on scroll
- **Default sort**: Daily top (group by day desc, score desc within day)
- **Security hardening (two rounds)**:
  - Open redirect fix, rate limiting, CORS, security headers, secrets cleanup
  - Disable FastAPI docs in prod, escape ILIKE wildcards, admin authz (`require_admin`), env filtering in agent entrypoint
  - Pin `claude-agent-sdk` version, alembic env var override for DB creds
  - `.env.prod` chmod 600 on server
  - Accepted risk: non-root Docker USER (not applied)
- **Pipeline fixes**: Advisory lock for concurrent runs, zero-norm embedding guard, datetime timezone handling, cluster ID collision fix, post-clustering embedding verification, consent/cookie page detection
- **Google News URL decoding** for proper article fetching
- **Mobile improvements**: Read/unread toggle on mobile, mobile-friendly detail tables (stacked cards)
- **Sidebar bug fix**: Use `window.location.search` to avoid stale `useSearchParams` during transitions; include `score_min` and `bookmarks` in URL filter detection

### 2026-03-11

- **User auth via DiscourseConnect SSO**: Full sign-in/sign-out flow. JWT session cookies, AuthProvider context.
- **Discuss on Forum workflow**: "Discuss" button creates Discourse topics in AI News category (cat 8). Race condition protection via `SELECT ... FOR UPDATE`.
- **Related events via cosine similarity**: `hyde_embedding` cosine distance query, top 2 similar events.
- **Read/unread tracking**: Server-side read state, eye icon toggle, filter by All/Unread/Read.
- **Save filter preferences**: Persist current filters to backend, auto-load on fresh visits.
- **Search/filter interaction**: Search ignores all filters, sorts newest. Switching filters clears search.

### 2026-03-10

- **Secondary categories**, **newsletter URL resolution**, **Grok sentiment analysis**, **sortable columns**, **data cleanup** (see git log for details)

## Where We Are
- **Phase 1 PASSED** — all prompts validated on real data
- **Phase 2 backend — Agent SDK pipeline LIVE**:
  - Python project scaffolding (pyproject.toml, Dockerfile, docker-compose.yml)
  - SQLAlchemy models for all entities (Event, Article, Source, Channel, Tag, PipelineLog + supporting tables)
  - Alembic migrations generated and applied
  - FastAPI API with endpoints: events feed, event detail, updates, related, tags, admin stats
  - **Agent SDK pipeline** (replaced Celery):
    - Custom MCP tools (`agent/tools.py`) — 13 tools for all DB operations + vector search
    - Agent runbooks (`agent/runbooks.py`) — system prompts for classifier, event intelligence, and 5 subagents
    - Agent configs (`agent/agents.py`) — subagent definitions with model selection
    - Pipeline orchestrator (`agent/orchestrator.py`) — cron-triggered, sequential pipeline
    - Pipeline config (`agent/config.py`) — model selection, budgets, thresholds
  - Newsletter ingestion: parses email (Fastmail JMAP) → extracts story links → fetches full articles → stores
  - RSS ingestion: polls feeds → fetches full articles when content is short → stores
  - Article content extraction uses `trafilatura` (fast, no LLM needed)
  - 27 sources live: 7 company blogs, 4 publications, 2 dev blogs, 11 newsletters, 2 HN feeds
  - ~212 articles ingested, ~113 active events from first pipeline run
- **Clustering — HyDE (v3)**: Haiku normalizes articles → embed normalized summaries → similarity graph (0.80 threshold) → connected components. Working well.
- **Secondary categories**: Optional `secondary_category` on events for cross-category discoverability.
- **Newsletter URL resolution**: Tracking URLs resolved at ingestion. Dedup checks both original and resolved URLs.
- **Grok sentiment analysis (Step 5)**: xAI Responses API + `x_search` tool. Runs on events scored >= 8. Two-pass system: Pass 1 at event creation, Pass 2 re-checks after 24h if no discussion found.
- **Community voting — LIVE**:
  - Reputation-weighted up/down votes (trust level + likes from Discourse)
  - Diminishing returns curve, consensus bonus, membership scaling
  - Scores become fractional (2 decimal) when voted, integer otherwise
  - Community adjustment capped at ±2.0 points
- **Admin tools — LIVE**:
  - Score adjust (+1/-1 with required reason, stored for prompt tuning)
  - Category change (dropdown of all valid categories)
  - Source attribution (which feed surfaced each article)
  - Admin status synced dynamically from Discourse admin flag
- **Frontend — DEPLOYED at news.promptgoblins.ai**:
  - Next.js app with SSR, category/tag filtering, time range, sort controls
  - EventModal with full event detail, discuss button, similar events
  - DiscourseConnect SSO auth (sign in via forum)
  - Read/unread tracking with eye toggle on every row
  - Bookmarks/save feature with sidebar filter
  - Signal score filter (tappable number buttons, 5–9)
  - Day group headers with infinite scroll (flat list on week/month)
  - Full-content RSS feed endpoint
  - Save filter preferences to backend
  - Search (ignores filters, sorts newest)
  - Share button (copy link, X, LinkedIn)
  - Community vote buttons (after summary section)
  - Modal persists through refresh (slug in URL)
  - Compact/summary view toggle
  - Theme toggle (light/dark)
  - Mobile-friendly: stacked detail cards, responsive controls, 16px inputs
- **Forum integration — LIVE**:
  - Discuss button creates Discourse topics with markdown-formatted summary + permalink
  - Race condition protection via `SELECT ... FOR UPDATE`
  - AI News category (cat 8) restricted to staff-only topic creation
  - `news` Discourse user with API key for topic creation
- **Model decisions solidified**:
  - All distillation now Sonnet
  - Haiku for normalization, extraction, tagging
  - Sonnet for distillation, scoring, quality checking, editing
- **Removed** (replaced by Agent SDK):
  - Celery worker + beat scheduling
  - Raw Anthropic client (`llm.py`)
  - All pipeline stage modules (Celery-based)

## What Failed

### Clustering v1: Union-Find + Pairwise LLM (March 2026)

**Problem**: 153 of 155 articles ended up in a single mega-cluster.

**Root cause**: Union-Find with transitive closure. When GPT-4o-mini verified pairwise article pairs (title-only, YES/NO), the transitive property of union-find caused chain reactions: A↔B + B↔C → A,B,C merged, even when A and C were unrelated. With 155 articles and a generous candidate threshold, this collapsed everything.

**Key insight**: Embedding cosine similarity is a blunt instrument for event clustering. The gap between "same event" and "related but different" is too narrow for a clean threshold. Raw articles of different lengths/styles produce incomparable embeddings.

### Clustering v3: HyDE (Current — Working)

**Approach**: Normalize articles through Haiku BEFORE embedding. Each article becomes a structured "title + key facts" summary. Same event → nearly identical summaries → nearly identical embeddings. The threshold landscape becomes bimodal.

**Status**: Working well in production. Thresholds: HYDE_SIM=0.80, EVENT_MATCH=0.75, EVENT_MATCH_DAYS=14, DEDUP=0.85.

## Architecture

```
CRON (3x daily: 6am, 2pm, 10pm UTC) → orchestrator.py
  ├─ Poll newsletters (Fastmail JMAP) → extract links → fetch articles → store
  ├─ Poll RSS feeds → store articles
  ├─ HyDE Clustering
  │   ├─ Haiku normalizes articles → title + key facts
  │   ├─ Embed normalized summaries (OpenAI text-embedding-3-small)
  │   └─ Similarity graph → connected components = clusters
  ├─ Event Intelligence agent [sonnet] + MCP tools + subagents
  │   ├─ Distiller [sonnet]
  │   ├─ Scorer [sonnet]
  │   ├─ Tagger [haiku] (primary + optional secondary category)
  │   ├─ Quality Checker [sonnet]
  │   └─ Editor [sonnet]
  ├─ Sentiment Pass 1 [grok-4-1-fast-reasoning] (events scored >= 8)
  │   └─ xAI Responses API + x_search → structured X post sentiment
  ├─ Sentiment Pass 2 (re-check events with no discussion after 24h)
  └─ Post-processing dedup (pgvector, >0.85 auto-merge)
```

Data flows through the database. Each agent reads/writes via MCP tools.

## Two Product Pillars (from Mike)
1. **Comprehensive Discovery** — don't miss stories. Cover all niches/industries since users filter. Newsletters are highest priority source (already curated).
2. **Event Intelligence** — the core product. An "event" is the canonical unit, not a news story. Multiple sources clustered and distilled into one perfectly consumable record. This precision is what makes us hard to replicate.

- **Security hardening — COMPLETE**:
  - FastAPI docs disabled in prod, ILIKE wildcards escaped, admin authz enforced
  - Open redirect fix, rate limiting, CORS headers, secrets cleanup
  - Agent entrypoint env filtering, `claude-agent-sdk` pinned, alembic env override
  - `.env.prod` chmod 600 on server
  - Accepted risk: non-root Docker USER, JWT iss/aud, CSP nonces

## Next Steps
1. Event calendar feature
2. Prompt tuning from admin adjustment data (~2 weeks of collection)
3. Add more sources for broader coverage
4. Consider email digest / notification features

## Active Documents
- Plan: [plan/PLAN.md](plan/PLAN.md)
- Event Intelligence: [plan/plan_section_event_intelligence.md](plan/plan_section_event_intelligence.md)
- Discovery: [plan/plan_section_discovery.md](plan/plan_section_discovery.md)
- Data Model: [plan/plan_section_data_model.md](plan/plan_section_data_model.md)
- Prompts: [plan/plan_section_prompts.md](plan/plan_section_prompts.md)
- Architecture: [plan/plan_section_architecture.md](plan/plan_section_architecture.md)
- Taxonomy: [plan/plan_section_taxonomy.md](plan/plan_section_taxonomy.md)
- Sources: [plan/plan_section_sources.md](plan/plan_section_sources.md)
- Frontend: [plan/plan_section_frontend.md](plan/plan_section_frontend.md)
- Reference: [reference/spec_ai_signal_platform.md](reference/spec_ai_signal_platform.md)

---
**For Agents**: Read this first, then PLAN.md for project overview. All plan sections are written and ready for implementation planning.
