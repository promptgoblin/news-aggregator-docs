# Plan Section: Architecture

---
type: plan_section
tags: [architecture, infrastructure, deployment]
last_updated: 2026-03-10
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

System architecture for Goblin News. Python/FastAPI backend with Claude Agent SDK for async pipeline processing, PostgreSQL+pgvector for storage, Next.js frontend. Hosted at news.promptgoblins.ai on the same web server as the Prompt Goblins forum — co-located for simplicity and shared resources. Agent pipeline runs on this server, not on a dev machine.

## Decision History

**2025-02**: Python + FastAPI for backend. Async by default, great for LLM API calls.
**2025-02**: Co-located on existing web server with Prompt Goblins forum.
**2026-02**: **Celery + Redis REMOVED** — replaced by Claude Agent SDK pipeline. Simpler, more capable, runs on Claude subscription.
**2026-03**: Newsletter ingestion switched from Gmail API to Fastmail JMAP (simpler auth, no OAuth dance).
**2026-03**: Embeddings: OpenAI text-embedding-3-small (1536 dims). Considered Voyage AI but OpenAI is simpler and works well.
**2026-03**: Grok sentiment analysis added via xAI Responses API with `x_search` tool.
**2026-03**: QC and Editor subagents downgraded from Sonnet to Haiku — structural checks moved to code, LLM only handles subjective judgment and fact-checking against source material.

## Key Decisions

### Python + FastAPI Backend
**Choice**: Python with FastAPI for the API layer.
**Rationale**: Async by default, excellent for LLM API calls, great Python ecosystem for NLP/ML, fast development. Type hints + Pydantic for request/response validation.

### Claude Agent SDK Pipeline (Replaced Celery)
**Choice**: Claude Agent SDK with MCP tools for all pipeline processing.
**Rationale**: Agent SDK provides a more capable pipeline than Celery workers. Agents can make decisions, spawn subagents, use tools, and handle complex multi-step workflows. Runs on Mike's Claude subscription — massively subsidized vs per-API-call billing.
**Previous**: Celery + Redis broker. Removed because Agent SDK is simpler and more capable for this use case.

### Separate Backend/Frontend Apps
**Choice**: FastAPI API + Next.js frontend as separate deployable apps.
**Rationale**: Clean separation. API serves both the frontend and potential future consumers (RSS feeds, API access). Frontend is statically optimizable.

### Agent Pipeline on Web Server
**Choice**: Claude Agent SDK agents run on the web server, not dev machine.
**Rationale**: Reliability — agents should run 24/7 on scheduled tasks. Dev machine uptime is unreliable.

## Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        news.promptgoblins.ai                     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Next.js    │───→│   FastAPI    │───→│   PostgreSQL     │   │
│  │   Frontend   │    │   API        │    │   + pgvector     │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│                                                   ↑              │
│                      ┌────────────────────────────┤              │
│                      │  Agent Pipeline (cron)     │              │
│                      │                            │              │
│                      │  orchestrator.py            │              │
│                      │  ├─ 1. Ingestion           │              │
│                      │  │  └─ RSS + JMAP          │              │
│                      │  ├─ 2. HyDE Clustering     │              │
│                      │  │  └─ Haiku (Agent SDK)   │              │
│                      │  ├─ 3. Event Intelligence  │              │
│                      │  │  └─ Sonnet (Agent SDK)  │              │
│                      │  ├─ 4. Dedup (pgvector)    │              │
│                      │  └─ 5. Sentiment (Grok)    │              │
│                      └────────────────────────────┘              │
│                              │                                   │
│                              ├──→ OpenAI API (embeddings only)   │
│                              ├──→ xAI API (Grok sentiment)       │
│                              ├──→ Fastmail JMAP (newsletters)    │
│                              └──→ RSS Feeds (27 sources)         │
└─────────────────────────────────────────────────────────────────┘
```

### API Layer (FastAPI)

**Endpoints**:
```
GET  /api/events              — Feed (paginated, filterable by tags, score, time)
GET  /api/events/{slug}       — Single event with all tiers + updates + related events
GET  /api/events/{slug}/updates — Update history for an event
GET  /api/events/{slug}/related — Related events (story timeline)
GET  /api/tags                — Available tags and groups
GET  /api/sources             — Source list with trust scores
GET  /api/admin/stats         — Pipeline stats
```

### Agent Pipeline (5 Stages)

Pipeline runs via cron (2x daily) and orchestrated by `agent/orchestrator.py`. All five stages run sequentially on each invocation.

#### Step 1: Ingestion

Pure Python IO — no LLM agent needed for the core fetching.

- **RSS feeds**: `poll_all_feeds()` fetches articles from 27 sources via RSS, extracts full text with trafilatura, generates embeddings at ingestion time, and stores in PostgreSQL.
- **Newsletters**: `poll_newsletters()` connects to Fastmail via JMAP API, pulls emails from a dedicated mailbox, and uses a one-shot Haiku agent to extract story links/headlines from newsletter HTML.
- **URL resolution**: Newsletter links (especially from beehiiv, Substack, etc.) are tracking redirects, not real URLs. `fetch_article_content()` follows redirects (`httpx` with `follow_redirects=True`) to resolve the final destination URL. The resolved URL is stored as the canonical article URL, and a second dedup check runs against it to catch cases where the same article was already ingested via RSS.
- After extraction, emails are archived in Fastmail to keep the inbox clean.

#### Step 2: HyDE Clustering

Embedding-based clustering with Haiku normalization to group articles about the same event.

1. **Haiku normalization** (Agent SDK, batched): First N chars of each article (`CLUSTER_HYDE_LEDE_CHARS=1000`) are sent to Haiku in batches of `CLUSTER_HYDE_BATCH_SIZE=30`. Haiku normalizes each into a canonical `title + key facts` summary, stripping source-specific framing.
2. **Embed + similarity graph**: Normalized summaries are embedded (OpenAI text-embedding-3-small). A cosine similarity graph is built — edges connect articles above `CLUSTER_SIM_THRESHOLD=0.80`. Connected components form clusters.
3. **Match to existing events**: Each cluster is matched against active events from the last `CLUSTER_EVENT_MATCH_DAYS=14` days using content embedding similarity (`CLUSTER_EVENT_MATCH_THRESHOLD=0.75`). Matched clusters update existing events rather than creating new ones.
4. **Safety net**: Clusters larger than `CLUSTER_MAX_SIZE=15` are split to singletons to prevent transitive closure mega-clusters.

#### Step 3: Event Intelligence

Claude Agent SDK orchestrator (Sonnet) processes clustered articles in batches of `EVENT_INTEL_BATCH_SIZE=5` clusters per session to keep context lean. Budget: `$50.00` total, divided evenly across batches (minimum $5 per batch).

The orchestrator spawns specialized subagents for each cluster:

| Subagent | Model | Role |
|----------|-------|------|
| **Distiller** | Sonnet | Synthesize multi-source content into tiered event summary (tier1 scan, tier2 brief, tier3 detail) |
| **Scorer** | Sonnet | Calibrate importance score (1-10) with nuance |
| **Tagger** | Haiku | Taxonomy classification — category, secondary_category, tags |
| **Quality Checker** | Haiku | Subjective publication-readiness judgment (structural checks are in code) |
| **Editor** | Haiku | Fact-checking against source material |

**Structural guardrails** (enforced in code, not by agents):
- `create_event` requires `article_ids` — rejects events with no linked articles
- Articles auto-linked atomically (event_id + processing_status=processed in same transaction)
- `source_count` auto-computed from distinct source_ids on linked articles
- `_parse_tier3()` normalizes any invented field names to canonical `{number, type, key_point, context}`

#### Step 4: Dedup

Post-processing deduplication using pgvector embedding similarity. Two passes:

1. **Auto-merge** (similarity > `DEDUP_SIMILARITY_THRESHOLD=0.85`): Pairs above this threshold are merged automatically. The event with higher importance score (or more sources on tie) becomes the target; the other is soft-deleted with `status='merged'`. Articles are reassigned and `source_count` is recomputed.
2. **Haiku review** (similarity `0.70`–`0.85`): Pairs in this range are sent to Haiku for a yes/no merge decision. Catches semantic duplicates that vector similarity alone misses (e.g., "GPT-5.4 Launch" vs "GPT-5.4 System Card"). Cost: ~$0.001 per pair.

#### Step 5: Sentiment Analysis

Grok-powered real-time sentiment from X (Twitter) via xAI's Responses API.

- **Trigger**: Only runs on active events with `importance_score >= SENTIMENT_SCORE_THRESHOLD` (currently 8) that don't already have sentiment data.
- **Model**: `grok-4-1-fast-reasoning` with the `x_search` tool enabled, so Grok actually searches X posts in real time.
- **Output**: Structured JSON stored in `event.sentiment_passes` (JSONB array) — includes `overall_sentiment`, `prominent_reactions` (3-5 credible voices with handles, stances, and post URLs), `fault_lines`, and a `sentiment_score` (-1.0 to 1.0).
- **Two-pass system**: Pass 1 runs at event creation. Pass 2 runs days later for shift detection (delta >= 0.4 is flagged as significant).

### Data Model (Event)

Key fields on the Event model relevant to pipeline output:

- `title`, `slug` — event identity
- `tier1_scan`, `tier2_brief`, `tier3_detail` — tiered content from Distiller
- `what_this_means` — plain-language impact summary
- `importance_score` (1-10) — from Scorer
- `category`, `secondary_category` — primary and optional secondary taxonomy from Tagger
- `tags` — array of taxonomy tags from Tagger
- `source_count` — auto-computed from linked articles (not agent-provided)
- `sentiment_passes` — JSONB array of Grok sentiment analysis results
- `embedding` — pgvector embedding for dedup and similarity search
- `status` — `active`, `merged`, etc.

### Agent SDK Integration

All LLM processing uses Claude Agent SDK authenticated via Mike's Claude Code subscription:
- **No separate Anthropic API key needed**
- **Cannot nest inside Claude Code** — pipeline must `unset CLAUDECODE` when running from dev
- **MCP tools** provide database access: 13 tools for CRUD, vector search, Discourse publishing
- **Subagents** are spawned by the Event Intelligence agent for specialized tasks
- **Models**: Haiku for cheap tasks (extraction, tagging, normalization, QC, fact-checking), Sonnet for synthesis and scoring
- **MCP param bug**: `list`/`dict` param types in `@tool` arrive as empty strings via MCP. Use `str` + `_safe_json_parse()` as workaround.

### Discourse Integration

"Discuss" button on events creates a thread in the AI News category on promptgoblins.ai:
1. Agent calls `publish_to_discourse` tool for events with importance >= 6
2. Creates topic with event title + tier1 summary + link back
3. Stores `discourse_topic_id` on the event record

### Deployment

**Hosting**: Co-located on the same web server as the Prompt Goblins forum.

- Docker Compose: FastAPI + PostgreSQL + Next.js
- Nginx reverse proxy: news.promptgoblins.ai → Next.js + /api → FastAPI
- Cron: 2x daily pipeline runs (6am + 6pm UTC)
- Let's Encrypt for SSL
- Redis removed (was for Celery, no longer needed)

## Dependencies & Constraints

### Dependencies
- Existing web server (co-located with Prompt Goblins forum)
- Domain DNS: news.promptgoblins.ai
- Claude Code subscription (Agent SDK authentication)
- OpenAI API key (embeddings only)
- xAI API key (Grok sentiment analysis)
- Fastmail account with JMAP token (newsletter ingestion)
- Discourse API key (forum integration)

### Constraints
- Shared server — Goblin News must not starve forum resources
- Agent pipeline must be reliable (not dependent on dev machine uptime)
- Frontend must match Prompt Goblins theme (light/dark modes)

### Plan Section Dependencies
- Depends on [plan_section_data_model.md](plan_section_data_model.md): Database schema
- Required by all feature implementations

## Risks

### Single Server Bottleneck
- **Probability**: Low (at initial scale)
- **Impact**: Medium
- **Mitigation**: Docker Compose makes it easy to split services later.

## Open Questions
- [ ] Monitoring: simple (Uptime Robot + error emails) or proper (Grafana)?
- [x] ~~VPS provider~~ — Co-located on existing forum web server
- [x] ~~Job queue~~ — Celery removed, Agent SDK pipeline via cron
- [x] ~~Newsletter auth~~ — Fastmail JMAP (not Gmail OAuth)
