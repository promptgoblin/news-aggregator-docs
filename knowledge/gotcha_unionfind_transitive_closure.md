# Gotcha: Union-Find Transitive Closure in Embedding Clustering

---
type: knowledge
tags: [clustering, embeddings, pipeline, gotcha]
severity: critical
time_lost: 4+ hours
last_updated: 2026-03-09
---

## Problem

Using union-find (disjoint set) data structure for clustering articles by embedding similarity causes **transitive closure chain reactions** that collapse all articles into a single mega-cluster.

## What Happened

155 articles about different AI news events were being clustered. Union-find was used: if article A↔B had cosine similarity above threshold, they were merged. Then if B↔C was also above threshold, A+B+C all ended up in one cluster — even if A and C were completely unrelated.

With 155 articles and a candidate threshold of 0.40 (for LLM pairwise verification), thousands of pairs were evaluated. Even a small false-positive rate (LLM incorrectly saying "YES, same story") created chain reactions. Result: 153/155 articles in one cluster.

## Root Cause

**Union-find is transitive**: `union(A,B) + union(B,C) → A,B,C all in same set`. This is mathematically correct but semantically wrong for "same event" relationships, which are NOT transitive. Two articles can each be related to a third without being related to each other.

**Embedding similarity landscape is flat**: With raw article embeddings, the gap between "same event" similarity (0.75-0.90) and "different event, same topic" similarity (0.60-0.80) is too narrow. No clean threshold separates them. Combined with transitive closure, any threshold that captures same-event pairs also captures enough false positives to chain-react everything together.

## Solution: HyDE Clustering

1. **Normalize before embedding**: Use Haiku to extract "title + key facts" from each article's lede. This strips length/style variance and focuses embeddings on the event itself.
2. **Connected components instead of union-find**: Same computational approach but cleaner semantics — a group is formed by transitive similarity, which works correctly when the similarity landscape is bimodal (clear gap between same-event and different-event).
3. **Threshold tuning**: HyDE embeddings should produce a bimodal distribution where 0.85 cleanly separates same-event from different-event pairs.

## When This Applies

- Any time you use embedding cosine similarity + union-find for clustering
- Especially dangerous with high-volume, same-domain content (e.g., all AI news)
- The more articles, the more likely chain reactions destroy your clusters

## When This Does NOT Apply

- If your similarity threshold produces genuinely bimodal results with a clear gap
- If transitive closure is semantically correct for your domain (e.g., exact duplicate detection)

## Key Insight

> Embeddings are good at finding *candidates* (related content) but bad at the *decision* (same event vs. related but different). The decision needs either an LLM or a much cleaner embedding input.

## References

- `src/ai_signal/pipeline/clustering.py` — current HyDE implementation
- `docs/plan/plan_section_event_intelligence.md` — full decision history
