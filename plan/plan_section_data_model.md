# Plan Section: Data Model

---
type: plan_section
tags: [database, schema, postgresql, pgvector]
last_updated: 2026-03-10
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Data model for Goblin News built on PostgreSQL + pgvector. The core entities are **Event** (canonical unit of content), **Article** (individual source document), **Source** (a newsletter, blog, or feed), and **Channel** (ingestion mechanism). The schema supports vector similarity search, event clustering, three-tier content, and source quality tracking.

## Decision History

**2025-02**: PostgreSQL + pgvector over separate vector DB — keeps everything in one database, simpler ops, pgvector is mature enough for our scale.
**2025-02**: Event as first-class entity (not derived view) — events are created, updated, and queried directly. Articles are linked to events.
**2025-03**: HyDE clustering fields added — `hyde_summary` and `hyde_embedding` on events and articles support the HyDE normalization pipeline (Haiku normalizes articles into title+key facts, then embed for cosine similarity clustering).
**2025-03**: `tier2_understand` and `tier3_deep_dive` changed from TEXT to JSONB — tier2 stores a list of takeaway strings, tier3 stores structured detail table rows.
**2025-03**: `primary_tag` renamed to `category` + `secondary_category` added — supports dual-category taxonomy.
**2025-03**: `sentiment_passes` (JSONB), `is_top_news`, `what_this_means` added to events for richer intelligence output.

## Key Decisions

### Single Database (PostgreSQL + pgvector)
**Choice**: PostgreSQL with pgvector extension for both relational and vector data.
**Rationale**: Eliminates the complexity of syncing between a relational DB and a separate vector store. pgvector handles our scale (thousands of articles/month, not millions). Simpler deployment, backup, and ops.
**Alternatives**:
- PostgreSQL + Pinecone/Weaviate: More powerful vector search but adds operational complexity and cost
- SQLite: Too limited for concurrent workers and vector search

### Soft Deletes
**Choice**: Use `deleted_at` timestamps rather than hard deletes for events and articles.
**Rationale**: Audit trail, ability to recover from bad merges, debugging clustering decisions.

## Design

### Entity Relationship

```
Channel (1) ──→ (N) Source (1) ──→ (N) Article (N) ──→ (1) Event
                         │                  │                │
                         └── trust_score    │                ├── tier1/2/3 content
                                            │                ├── embedding + hyde_embedding
                                            │                ├── tags, category, scores
                                            │                └── sentiment_passes, what_this_means
                                            │
                                            ├── hyde_summary (clustering fingerprint)
                                            └── content_type, processing_status

Event (1) ──→ (N) EventUpdate          Event ←──→ RelatedEvent
Event ←── EventMerge (source → target audit trail)
```

### Event

The canonical unit of content. One real-world occurrence, distilled from multiple sources.

```sql
CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content (three tiers)
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    tier1_scan      TEXT NOT NULL,           -- ~30 words, headline + context
    tier2_understand JSONB,                  -- list of takeaway strings
    tier3_deep_dive JSONB,                   -- structured detail table (rows with number, type, key_point, context)
    key_facts       JSONB DEFAULT '[]',      -- extracted factual claims with source attribution

    -- Clustering & search
    embedding       vector(1536),            -- composite embedding (weighted avg of article embeddings)
    hyde_summary    TEXT,                     -- normalized fingerprint from HyDE clustering
    hyde_embedding  vector(1536),            -- embedding of hyde_summary for event matching

    -- Metadata
    importance_score SMALLINT,
    tags            TEXT[] DEFAULT '{}',
    category        TEXT,                    -- primary category
    secondary_category TEXT,                 -- secondary category
    source_count    SMALLINT DEFAULT 1,      -- auto-computed from distinct source_ids on linked articles
    is_top_news     BOOLEAN DEFAULT FALSE,
    what_this_means TEXT,                    -- plain-language impact summary
    sentiment_passes JSONB,                  -- multi-pass sentiment analysis results

    -- Lifecycle
    status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'merged', 'archived', 'deleted')),
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at    TIMESTAMPTZ,            -- when made visible in feed

    -- Tracking
    primary_article_id UUID,               -- first/most authoritative source
    discourse_topic_id INTEGER,            -- linked Discourse discussion thread
    update_count    SMALLINT DEFAULT 0,    -- number of updates since initial publish

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_events_published ON events (published_at) WHERE status = 'active';
CREATE INDEX idx_events_tags ON events USING GIN (tags);
CREATE INDEX idx_events_importance ON events (importance_score);
CREATE INDEX idx_events_top_news ON events (is_top_news) WHERE is_top_news = true;
```

### Article

A single piece of source content (one newsletter story, one blog post, one tweet).

```sql
CREATE TABLE articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source linkage
    source_id       UUID NOT NULL REFERENCES sources(id),
    event_id        UUID REFERENCES events(id),       -- NULL until clustered

    -- Content
    title           TEXT NOT NULL,
    url             TEXT,                               -- original article URL
    raw_content     TEXT NOT NULL,                      -- cleaned source text
    summary         TEXT,                               -- LLM-generated article summary

    -- Clustering
    embedding       vector(1536),
    hyde_summary    TEXT,                               -- HyDE fingerprint from normalization (Haiku-generated)
    cluster_id      TEXT,                               -- transient grouping ID from clustering
    cluster_confidence REAL,                            -- confidence of event assignment (0.0-1.0)
    is_primary      BOOLEAN DEFAULT FALSE,              -- is this the primary source for its event?

    -- Metadata
    author          TEXT,
    published_at    TIMESTAMPTZ,                        -- original publication date
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    word_count      INTEGER,

    -- Source-specific
    source_metadata JSONB DEFAULT '{}',                 -- newsletter name, RSS feed, tweet ID, etc.
    content_type    TEXT,                               -- news, opinion, analysis, research, quick-link
    is_sponsored    BOOLEAN DEFAULT FALSE,              -- flagged as ad/sponsor content

    -- Tracking
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'clustered', 'failed')),
    retry_count     SMALLINT DEFAULT 0,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_articles_event ON articles (event_id);
CREATE INDEX idx_articles_source ON articles (source_id);
CREATE INDEX idx_articles_ingested ON articles (ingested_at);
CREATE INDEX idx_articles_processing ON articles (processing_status) WHERE processing_status != 'clustered';
```

### Source

A specific newsletter, blog, RSS feed, or Twitter account that produces articles.

```sql
CREATE TABLE sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name            TEXT NOT NULL,                      -- "The Batch", "OpenAI Blog"
    slug            TEXT UNIQUE NOT NULL,
    channel_id      UUID NOT NULL REFERENCES channels(id),
    url             TEXT,                               -- website/feed URL

    -- Quality tracking
    trust_score     REAL DEFAULT 0.5 CHECK (trust_score BETWEEN 0.0 AND 1.0),
    source_type     TEXT NOT NULL CHECK (source_type IN ('primary', 'newsletter', 'publication', 'blog', 'social', 'aggregator')),

    -- Ingestion config
    config          JSONB DEFAULT '{}',                 -- channel-specific settings (feed URL, email filter, account ID)
    poll_interval_minutes INTEGER DEFAULT 15,
    last_polled_at  TIMESTAMPTZ,

    -- Stats
    total_articles  INTEGER DEFAULT 0,
    avg_articles_per_day REAL DEFAULT 0,

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Channel

An ingestion mechanism (newsletter, RSS, Twitter, agent).

```sql
CREATE TABLE channels (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name            TEXT UNIQUE NOT NULL,               -- 'newsletter', 'rss', 'twitter', 'agent'
    adapter_class   TEXT NOT NULL,                      -- Python class path for ingestion adapter
    is_active       BOOLEAN DEFAULT TRUE,

    config          JSONB DEFAULT '{}',                 -- global channel config
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Tag

Tag definitions for the taxonomy system.

```sql
CREATE TABLE tags (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,               -- 'llm', 'computer-vision', 'openai'
    display_name    TEXT NOT NULL,                      -- 'LLMs', 'Computer Vision', 'OpenAI'
    tag_group       TEXT NOT NULL,                      -- 'labs', 'models', 'technology', 'domain'
    tier            TEXT NOT NULL DEFAULT 'secondary',  -- 'primary' or 'secondary'
    description     TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Supporting Tables

```sql
-- Related event links (story timelines — bidirectional)
CREATE TABLE related_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(id),
    related_event_id UUID NOT NULL REFERENCES events(id),
    relationship_type TEXT DEFAULT 'related',           -- related, follow_up, predecessor
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(event_id, related_event_id)
);

CREATE INDEX idx_related_events_event ON related_events (event_id);
CREATE INDEX idx_related_events_related ON related_events (related_event_id);

-- Event updates (tracked changes when same-event articles merge in)
CREATE TABLE event_updates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(id),
    update_summary  TEXT NOT NULL,                      -- what's new in this update
    article_ids     UUID[] DEFAULT '{}',                -- articles that triggered this update
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_event_updates_event ON event_updates (event_id, created_at DESC);

-- Event merge history for audit trail
CREATE TABLE event_merges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_event_id UUID NOT NULL,                     -- event that was merged away (may no longer exist)
    target_event_id UUID NOT NULL REFERENCES events(id),
    merged_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason          TEXT,
    confidence      REAL
);
```

## Dependencies & Constraints

### Dependencies
- **PostgreSQL 15+**: Required for pgvector compatibility
- **pgvector extension**: `CREATE EXTENSION vector;`
- **Embedding dimension**: 1536 (matches OpenAI text-embedding-3-small; adjust if using Voyage AI)

### Constraints
- Embedding dimension locked to chosen model — switching models requires re-embedding all content
- IVFFlat index requires periodic `REINDEX` as data grows (or switch to HNSW for auto-maintenance)
- Event slugs must be unique and URL-safe

### Plan Section Dependencies
- Required by [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Event and Article schemas
- Required by [plan_section_discovery.md](plan_section_discovery.md): Source and Channel schemas
- Related to [plan_section_taxonomy.md](plan_section_taxonomy.md): Tag schema and event tag relationships

## Risks

### Embedding Model Lock-in
- **Probability**: Medium
- **Impact**: Medium — switching models means re-embedding everything
- **Mitigation**: Store model identifier with embeddings. Build re-embedding script early. At our scale (thousands, not millions), re-embedding is feasible.

### Schema Evolution
- **Probability**: High (early stage)
- **Impact**: Low — using migrations
- **Mitigation**: Alembic for schema migrations from day 1. JSONB fields for flexible metadata.

## Open Questions
- [x] Embedding dimension: **Settled at 1536** — using text-embedding-3-small
- [ ] IVFFlat vs. HNSW index for pgvector? HNSW is better for incremental inserts but uses more memory
- [ ] Should we store raw email HTML for newsletters or just extracted text?

## References
- pgvector: https://github.com/pgvector/pgvector
- Alembic: Database migrations for SQLAlchemy
