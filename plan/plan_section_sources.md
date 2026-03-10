# Plan Section: Sources

---
type: plan_section
tags: [sources, newsletters, rss, initial-list]
last_updated: 2025-02-25
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Initial source list and source management strategy. This is the concrete "who do we ingest from" complement to [plan_section_discovery.md](plan_section_discovery.md) which covers the strategy. Sources are curated, each assigned a type and trust score. No single source should represent >15% of total article volume.

## Initial Source List

### Newsletters (P0 — Phase 2)

| Source | Frequency | Focus | Trust |
|--------|-----------|-------|-------|
| AI Daily Brief | Daily | Broad AI, links to all stories discussed | 0.85 |
| The Batch (Andrew Ng) | Weekly | ML/AI research + industry | 0.85 |
| Import AI | Weekly | Research-focused | 0.80 |
| The Neuron | Daily | Broad AI, accessible | 0.75 |
| TLDR AI | Daily | Broad AI, brief format | 0.75 |
| Ben's Bites | Daily | AI products + startups | 0.75 |
| Superhuman AI | Weekly | AI tools + productivity | 0.70 |
| AI Breakfast | Daily | Industry + business AI | 0.70 |
| The Rundown AI | Daily | Broad AI | 0.70 |
| The Algorithm (MIT Tech Review) | Weekly | Research + policy | 0.85 |
| Hugging Face Newsletter | Bi-weekly | Open source ML | 0.80 |
| Papers with Code Newsletter | Weekly | Research papers | 0.80 |

### RSS Feeds (P1 — Phase 2)

**Company Blogs** (trust: 0.90 — primary sources):
OpenAI Blog, Anthropic Blog, Google DeepMind Blog, Meta AI Blog, Microsoft Research Blog, Stability AI Blog, Mistral Blog, Cohere Blog, NVIDIA AI Blog

**Research** (trust: 0.80):
arXiv cs.AI (filtered), arXiv cs.CL (filtered), arXiv cs.LG (filtered), Google Research Blog, Distill.pub

**Publications** (trust: 0.75):
The Verge /ai, TechCrunch /ai, Ars Technica /ai, MIT Tech Review, Wired /ai

**Industry** (trust: 0.70):
VentureBeat AI, The Information (limited — paywalled), Semafor AI

**Open Source / Developer** (trust: 0.75):
Hugging Face Blog, LangChain Blog, LlamaIndex Blog, PyTorch Blog

### Twitter/X Accounts (P2 — Phase 4)

Key accounts to monitor via Grok API:
@OpenAI, @AnthropicAI, @GoogleDeepMind, @MetaAI, @ylecun, @kaboringML, @sama, @demaborish, @emaborish, leading researchers (curated list ~50 accounts)

## Source Management

### Adding Sources
1. Identify coverage gap (topic/vertical with <80% coverage)
2. Find candidate source, evaluate: relevance, quality, frequency, uniqueness
3. Add to database with appropriate type and initial trust score
4. Monitor for 1 week, adjust trust score based on observed quality

### Removing Sources
- Trust score drops below 0.3 for 30+ days → auto-deactivate, flag for review
- Source goes inactive (no new content for 60 days) → auto-deactivate
- Source quality degrades significantly → manual deactivation

### Trust Score Evolution
Recalculated weekly:
- **Accuracy factor**: % of articles that pass quality filter (not spam, not ads)
- **Timeliness factor**: Average time-to-publish vs. first source on same event
- **Uniqueness factor**: % of articles that contribute unique info not found elsewhere

## Plan Section Dependencies
- Strategy defined in [plan_section_discovery.md](plan_section_discovery.md)
- Source schema in [plan_section_data_model.md](plan_section_data_model.md)
- Trust scores used by [plan_section_event_intelligence.md](plan_section_event_intelligence.md) for source weighting

## Open Questions
- [ ] Exact arXiv filtering criteria — by section? Citation threshold? Author list?
- [ ] Paywalled sources (The Information) — worth partial ingestion or skip?
- [ ] Any non-English sources worth including? (Chinese AI news is significant)
