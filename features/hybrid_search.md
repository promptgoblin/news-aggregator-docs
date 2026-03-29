# Feature: Hybrid Search (Keyword + Semantic)

---
type: feature
status: planning
complexity: C2
tags: [search, embeddings, pgvector]
depends_on: []
required_by: []
---

## User Intent

### Goal
Search that finds what you mean, not just what you typed. Combine keyword matching (current ILIKE) with semantic vector similarity (pgvector cosine distance) for both news events and calendar events.

### Why
Current search is keyword-only. "nvidia networking" finds events with both words, but "claude subscriptions" won't find "Anthropic revenue doubles" even though they're about the same thing. Semantic search closes this gap.

## Approach

**Hybrid by default** — run keyword and semantic in parallel, merge results, keyword exact matches ranked higher.

### Flow
1. User types query
2. **Keyword path**: existing ILIKE word-split search (fast, no API call)
3. **Semantic path**: embed query via OpenAI `text-embedding-3-small` → cosine similarity against `hyde_embedding` (news) or future embedding column (calendar) → top N above threshold
4. **Merge**: dedupe by event ID, score = blend of keyword rank + vector similarity
5. Return merged results

### Cost
- One OpenAI embedding call per search (~$0.02/million tokens, essentially free)
- ~200-300ms latency for the embedding API call
- Keyword search runs in parallel, so total latency = max(keyword, semantic)

### Infrastructure
Already in place:
- pgvector installed and indexed
- News events have `hyde_embedding` (1536-dim, OpenAI text-embedding-3-small)
- OpenAI API key configured
- Cosine similarity queries already used for related events

Needed:
- Embedding column on `calendar_events` (generate from name + description)
- Query embedding endpoint or inline embedding in search handler
- Merge/ranking logic

### Applies to
- News feed search (`/api/events?q=`)
- Calendar search (`/api/calendar?q=`)

## Status: Planning
**Created**: 2026-03-29
