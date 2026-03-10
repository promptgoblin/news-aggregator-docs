# Project Status

**Last Updated**: 2026-03-10

## Active Phase
**Phase**: Phase 2 — Foundation
**Phase Status**: In Progress — Pipeline live, enrichment and frontend maturing

## Current Session

**Working On**: Event enrichment (sentiment analysis), frontend polish, data quality
**Status**: Secondary categories, Grok sentiment, newsletter URL resolution, sortable UI all shipped
**Blocked By**: Nothing

## Recent Changes

### 2026-03-10

- **Secondary category system**: Events can now have an optional `secondary_category` for cross-category discoverability. API filters match on either primary or secondary category. Tagger runbook updated with guidance on when to assign secondary categories.
- **Newsletter URL resolution at ingestion**: `fetch_article_content()` now captures the resolved URL after following redirects. Beehiiv/TLDR/Alpha Signal tracking URLs are resolved to real destination URLs at ingestion time. Deduplication checks both original and resolved URLs.
- **Grok sentiment analysis live**: Pipeline Step 5 uses xAI Responses API with `x_search` tool (model: `grok-4-1-fast-reasoning`) for real X post search. Runs on events scored >= 8. Structured output: handle/name/role/stance/reaction/context/url.
- **Frontend improvements**: Sortable column headers (Signal, Sources, Posted — click to sort, click again to toggle direction). Removed auto-scroll on re-sort (highlight persists without scrolling). Tracking URLs no longer stored — resolved at ingestion.
- **Data cleanup**: 28/31 beehiiv URLs resolved to real destinations. Score < 6 events archived. Source labels now derived from resolved URL domain.

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
- **Clustering — MAJOR ITERATION** (see [What Failed](#what-failed)):
  - v1 (union-find + pairwise LLM): Mega-cluster problem — all articles merged into 1 cluster
  - v2 (HyDE): Haiku normalizes articles → embed normalized summaries → similarity graph → connected components. In testing.
- **Secondary categories**: Optional `secondary_category` on events for cross-category discoverability. API filters match either primary or secondary.
- **Newsletter URL resolution**: Tracking URLs (beehiiv, TLDR, Alpha Signal) resolved to real destinations at ingestion. Dedup checks both original and resolved URLs.
- **Grok sentiment analysis (Step 5)**: xAI Responses API + `x_search` tool (`grok-4-1-fast-reasoning`). Runs on events scored >= 8. Structured X post sentiment output.
- **Frontend**: Sortable column headers (Signal, Sources, Posted). No auto-scroll on re-sort.
- **Model decisions solidified**:
  - All distillation now Sonnet (was Opus for complex events — unnecessary when clustering is correct)
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

**What we tried**:
- Adjusting thresholds: At 0.80-0.85 auto-merge → still one cluster. At 0.90 → 153 clusters from 155 articles (almost no clustering). No sweet spot existed.
- Title-only embeddings: Better than full content (more focused on the event) but insufficient — the similarity landscape was too flat with no clear bimodal separation.
- All-Opus distillation: Thought Sonnet was producing poor output for low-signal events. Actually, the mega-cluster was the cause — the agent processed high-importance stories first and got lazy/efficient on the rest.

**Key insight**: Embedding cosine similarity is a blunt instrument for event clustering. The gap between "same event" and "related but different" is too narrow for a clean threshold. Raw articles of different lengths/styles produce incomparable embeddings.

### Clustering v2: LLM Sub-Clustering (Proposed, Replaced)

Intermediate approach: embedding candidate groups → GPT-4o-mini sub-clustering per group. Replaced by HyDE before testing because HyDE is simpler and attacks the root cause (embedding quality) rather than patching around it.

### Clustering v3: HyDE (Current)

**Approach**: Normalize articles through Haiku BEFORE embedding. Each article becomes a structured "title + key facts" summary. Same event → nearly identical summaries → nearly identical embeddings. The threshold landscape should become bimodal.

**Status**: Code written, needs first test run.

## Architecture

```
CRON (2x daily) → orchestrator.py
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
  ├─ Sentiment Analysis [grok-4-1-fast-reasoning] (events scored >= 8)
  │   └─ xAI Responses API + x_search → structured X post sentiment
  └─ Post-processing dedup (pgvector, >0.85 auto-merge)
```

Data flows through the database. Each agent reads/writes via MCP tools.

## Two Product Pillars (from Mike)
1. **Comprehensive Discovery** — don't miss stories. Cover all niches/industries since users filter. Newsletters are highest priority source (already curated).
2. **Event Intelligence** — the core product. An "event" is the canonical unit, not a news story. Multiple sources clustered and distilled into one perfectly consumable record. This precision is what makes us hard to replicate.

## Next Steps
1. Validate HyDE cluster quality on larger article volumes
2. Tune CLUSTER_SIM_THRESHOLD based on actual similarity distribution
3. Evaluate Grok sentiment analysis quality and coverage
4. Resolve remaining 3/31 beehiiv tracking URLs
5. Production deployment

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
