# Plan Section: Event Intelligence

---
type: plan_section
tags: [core, pipeline, clustering, distillation]
last_updated: 2026-03-09
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Event Intelligence is the core product — the thing that makes Goblin News hard to replicate. An **event** is the canonical unit of content, not a news story. When 15 newsletters and 5 blog posts all cover the same announcement, they become one event record with all signal distilled and zero noise. This section defines how raw articles become events: ingestion → HyDE normalization → clustering → event intelligence → dedup.

## Decision History

**2025-02**: Event as canonical unit (not story/article) — Mike's core product insight. Multiple sources about the same thing → one consumable record.
**2025-02**: Three-tier content model — Scan / Understand / Deep Dive. Different users need different depth.
**2025-02**: Three-way classification (same/related/new) instead of binary merge — prevents over-merging of ongoing stories.
**2026-02**: Agent SDK replaces Celery — pipeline runs as orchestrated agent with MCP tools and subagents.
**2026-03**: Structural guardrails — `create_event` requires `article_ids`, `source_count` auto-computed, tier3 field normalization.
**2026-03**: Union-find clustering FAILED — transitive closure caused mega-cluster (153/155 articles in one cluster). See [What Failed](#what-failed).
**2026-03**: HyDE clustering adopted — Haiku normalizes articles before embedding. Attacks root cause (embedding quality) not symptoms.
**2026-03**: All distillation moved to Sonnet — Opus unnecessary when clustering delivers correct, focused clusters to the distiller.
**2026-03**: Event matching timeboxed to 14 days — prevents exponential comparison growth.

## Key Decisions

### The "Event" Unit
**Choice**: An event is a real-world occurrence (announcement, release, paper, incident) — not a news story about it.
**Rationale**: Users don't want to read 12 takes on the same announcement. They want to know what happened, why it matters, and optionally go deep. One event, one record, all sources folded in.

### Clustering Strategy: HyDE (Hypothetical Document Embedding)
**Choice**: Three-stage clustering — Haiku normalization → embed normalized summaries → similarity graph.
**Rationale**: Raw article embeddings are too noisy for threshold-based clustering. A 200-word RSS blurb and a 3000-word analysis about the same event produce wildly different vectors. HyDE normalizes every article into the same format (title + key facts) BEFORE embedding, making same-event articles cluster tightly.

**Previous approach (failed)**: Two-phase embedding + LLM pairwise verification with union-find. See [What Failed](#what-failed).

**Alternatives considered**:
- Pure vector cosine similarity: Too flat — no clean threshold separates "same event" from "related but different"
- Pairwise LLM verification + union-find: Transitive closure errors collapse everything into mega-clusters
- LLM sub-clustering per candidate group: Viable but more complex than HyDE, attacks symptoms not root cause
- Keyword/entity matching: Too brittle, misses paraphrased coverage

### Model Selection: Sonnet for All Distillation
**Choice**: Sonnet handles all distillation regardless of source count (was Opus for 4+ sources).
**Rationale**: When clustering is correct, the distiller's job is straightforward — synthesize facts already in front of it. Opus is overkill. Tested: 4-o (GPT) produced decent distillation for similar tasks; Sonnet should be fine.

### Three-Tier Content Generation
**Choice**: Generate structured tiers per event from all clustered sources.

| Tier | Name | Format | Purpose |
|------|------|--------|---------|
| T1 | Scan | JSON array of 3-4 bullet takeaways | Quick understanding in <10 seconds |
| T3 | Deep Dive | JSON table with typed rows + legend | Comprehensive detail for deep readers |
| WTM | What This Means | 2-4 sentence prose | Significance for a smart generalist |

Note: T2 was removed during implementation. T1 (bullet scan) + T3 (detail table) + WTM covers all depth levels without the middle tier being awkward.

## Design

### Pipeline Flow (Current)

```
CRON → orchestrator.py
  │
  ├─ INGESTION (pure Python + APIs)
  │   ├─ poll_newsletters() → Fastmail JMAP → extract stories → fetch articles → store
  │   └─ poll_all_feeds() → RSS → fetch articles → store
  │
  ├─ HyDE CLUSTERING (Haiku + embeddings)
  │   ├─ backfill_missing_embeddings() → content embeddings for any gaps
  │   ├─ Stage 1: Haiku normalizes each article → title + 3-5 key facts
  │   ├─ Stage 2: Embed normalized summaries → similarity graph (0.85) → clusters
  │   └─ Stage 3: Match clusters to existing events (content embeddings, last 14 days)
  │
  ├─ EVENT INTELLIGENCE (Claude Agent SDK)
  │   └─ For each cluster:
  │       ├─ DISTILLER [sonnet] → synthesize articles into tiers
  │       ├─ SCORER [sonnet] → importance 1-10
  │       ├─ TAGGER [haiku] → classify into taxonomy
  │       ├─ QUALITY CHECKER [sonnet] → verify publication readiness
  │       └─ EDITOR [sonnet] → verify factual accuracy vs sources
  │
  └─ DEDUP (pure SQL + pgvector)
      └─ Auto-merge events with embedding similarity > 0.85
```

### HyDE Clustering (Stage Detail)

**Why HyDE works**: The core problem is that different-length articles about the same event produce incomparable embeddings. A 200-word RSS summary focuses on the headline fact; a 3000-word analysis buries it under context and opinion. HyDE normalizes both into the same structure:

```
Original: "OpenAI has released GPT-5, its most powerful model yet, featuring
unprecedented reasoning capabilities according to CEO Sam Altman, who spoke
at a press event in San Francisco on Tuesday. The model, which has been in
testing since... [3000 more words of analysis, benchmarks, reactions]"

Normalized by Haiku:
"GPT-5 Released by OpenAI
- OpenAI released GPT-5 on March 5, 2026
- Scores 92% on MMLU, 15-point jump over GPT-4.5
- Available in ChatGPT Plus and API immediately
- Pricing: $15/1M input, $60/1M output"
```

Two articles about the same event, regardless of length/style, produce nearly identical normalized summaries → nearly identical embeddings → high cosine similarity → correct clustering.

**Configuration** (`agent/config.py`):
- `CLUSTER_HYDE_LEDE_CHARS = 1000` — First N chars sent to Haiku (captures the lede)
- `CLUSTER_HYDE_BATCH_SIZE = 30` — Articles per Haiku call
- `CLUSTER_SIM_THRESHOLD = 0.85` — Cosine sim on HyDE embeddings for cluster edges
- `CLUSTER_EVENT_MATCH_THRESHOLD = 0.75` — Content embedding sim for existing event matching
- `CLUSTER_EVENT_MATCH_DAYS = 14` — Only match events from the last N days
- `CLUSTER_MAX_SIZE = 15` — Safety net: oversized clusters split to singletons

**Cost**: ~$0.02 per run (Haiku normalization + OpenAI embeddings). Negligible.

### Event Intelligence Agent

The main orchestrator agent receives clusters and spawns subagents:

1. **DISTILLER** [sonnet] — Synthesizes source articles into structured event content. Mandatory for every event.
2. **SCORER** [sonnet] — Rates importance 1-10 with detailed rubric and distribution targets.
3. **TAGGER** [haiku] — Classifies into two-tier taxonomy (1 primary category + 2-6 secondary tags).
4. **QUALITY CHECKER** [sonnet] — Validates structural integrity and publication readiness.
5. **EDITOR** [sonnet] — Verifies factual accuracy of distilled content vs source material.

All agents run via Claude Agent SDK using Mike's Claude subscription. No separate API key needed.

### Structural Guardrails
- `create_event` requires `article_ids` — rejects events with no linked articles
- Articles auto-linked atomically (event_id + processing_status=processed in same transaction)
- `source_count` auto-computed from distinct source_ids on linked articles
- Tier3 field normalization: any invented field names normalized to `{number, type, key_point, context}`
- Frontend `DetailTable` also normalizes via `rowColumns()` as defense-in-depth

### Related Event Linking (Story Timelines)

When events are connected but distinct, they get bidirectional links:
- Types: "related", "follow_up", "predecessor"
- Creates story timelines in the UI

### Event Updates (Same-Event Merges)

When new articles merge into an existing event:
1. Add article to event's source list
2. Re-distill content incorporating new material
3. Generate update summary (what's new)
4. Track in `event_updates` table

## What Failed

### Clustering v1: Union-Find + Pairwise LLM Verification

**What we built**: Title-only embeddings (OpenAI text-embedding-3-small) → pairwise cosine similarity → union-find grouping. Pairs in the 0.40-0.90 range sent to GPT-4o-mini for YES/NO "same story?" verification.

**What happened**: 153 of 155 articles ended up in one cluster.

**Root cause**: Union-find transitive closure. If GPT-4o-mini says A↔B (YES) and B↔C (YES), union-find merges A+B+C even if A and C are completely unrelated. With 155 articles and thousands of candidate pairs, even a small false-positive rate creates chain reactions that collapse everything.

**Why thresholds couldn't fix it**:
- Auto-merge at 0.80-0.85 → everything in one cluster (too many edges for union-find)
- Auto-merge at 0.90 → 153 clusters from 155 articles (almost no clustering)
- The similarity landscape was too flat — no clean bimodal separation between "same event" and "different event"

**Why title-only wasn't enough**: Titles are more focused than full content, but AI news titles share too much vocabulary ("launches", "announces", "AI", "model") to create clear separation. Different events from the same company (e.g., "OpenAI launches X" vs "OpenAI announces Y") had 0.70-0.85 title similarity.

**Downstream impact**: The event intelligence agent received one mega-cluster, tried to re-cluster and distill everything. It processed high-importance stories first and got lazy/efficient on the rest — producing 1-2 word details for lower-signal events.

**Key lesson**: Embeddings are good at finding *candidates* (related articles) but bad at the *decision* (same event vs. related but different). The decision needs either an LLM or a much cleaner embedding input — which is what HyDE provides.

### Opus vs Sonnet for Distillation

Initially assumed Opus was needed for complex events (4+ sources). After investigation, the poor quality on lower-signal events was caused by the mega-cluster (agent fatigue), not model capability. Sonnet should be sufficient when each cluster is correctly scoped.

## Dependencies & Constraints

### Dependencies
- **pgvector**: Vector similarity search for event matching and dedup
- **Claude Agent SDK**: All agent processing (normalizer, distiller, scorer, etc.)
- **OpenAI API**: Embeddings (text-embedding-3-small, 1536 dims)
- **Article ingestion**: Requires clean article text from source adapters

### Constraints
- **Latency**: New events should publish within hours of first source arriving (2x daily pipeline)
- **Cost**: HyDE clustering ~$0.02/run, event intelligence ~$5-15/run (depends on article count)
- **Accuracy**: Target <5% duplicate events, <5% false merges

### Plan Section Dependencies
- Depends on [plan_section_data_model.md](plan_section_data_model.md): Event, Article schemas
- Depends on [plan_section_prompts.md](plan_section_prompts.md): Clustering and distillation prompt templates
- Required by [plan_section_frontend.md](plan_section_frontend.md): Feed display, three-tier UI
- Required by [plan_section_sources.md](plan_section_sources.md): Source adapters feed into this pipeline

## Risks

### HyDE Clustering Quality
- **Probability**: Medium — untested at scale
- **Impact**: High — clustering quality is the #1 determinant of output quality
- **Mitigation**: First test run will reveal similarity distribution. Threshold (0.85) is tunable. Fallback: combine HyDE with LLM sub-clustering if embeddings alone aren't sufficient.

### Haiku Normalization Accuracy
- **Probability**: Low — Haiku is good at structured extraction
- **Impact**: Medium — bad normalization → bad embeddings → bad clusters
- **Mitigation**: Log normalized summaries for inspection. Fallback to raw titles if Haiku fails.

### LLM Cost at Scale
- **Probability**: Low — Haiku + Sonnet pipeline is very cheap
- **Impact**: Low — running on Claude subscription, not per-API-call billing
- **Mitigation**: Batch sizes tunable. Can reduce pipeline frequency if needed.

## Open Questions
- [ ] Optimal CLUSTER_SIM_THRESHOLD — 0.85 is starting point, needs validation against actual distribution
- [ ] Should HyDE embeddings be persisted or remain in-memory? Persisting enables incremental clustering.
- [ ] How long should events stay "open" for new source merges? Currently 14 days via EVENT_MATCH_DAYS.
- [ ] Should we add Haiku-normalized embeddings to events for better event-to-event matching?
- [x] ~~Embedding model~~ — OpenAI text-embedding-3-small (1536 dims), working well
- [x] ~~Opus vs Sonnet for distillation~~ — Sonnet for all distillation, Opus was unnecessary

## References
- HyDE paper: "Precise Zero-Shot Dense Retrieval without Relevance Labels" (Gao et al., 2022)
- Original Spec: [reference/spec_ai_signal_platform.md](../reference/spec_ai_signal_platform.md)
- Claude Agent SDK: Used for all agent processing via Claude subscription
