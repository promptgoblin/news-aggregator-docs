# Feature: Curated Blogs & Research Feeds

---
type: feature
status: planning
complexity: C2
tags: [discovery, curation, research, blogs]
depends_on: [production_deployment]
required_by: []
---

## User Intent

### Goal
Go beyond passively consuming RSS feeds and newsletters. Actively curate blogs and research papers — finding content that's worth covering even if it doesn't appear in our existing sources. This differentiates AI Signal from just being a newsletter aggregator.

### Success Criteria
- Discover notable blog posts from individual AI practitioners and researchers
- Surface important papers from arXiv, conference proceedings, etc.
- Quality bar: content is insightful or notable, not just "exists"
- Integrates into existing event pipeline (blog post or paper becomes an event)
- Gradually ramp — start with seed list, expand via discovery

### User Flow
1. Pipeline discovers a notable blog post or paper
2. Content ingested as article, clustered, potentially becomes its own event
3. User sees it in their feed like any other story
4. Category/tags distinguish it (e.g., "research", "deep-dive", "tutorial")

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## References
- Plan: [plan/plan_section_discovery.md] (P2-P3 sources)
- Related: [plan/plan_section_sources.md]

## Implementation

### Approach
Three discovery channels, ramped over time:

**Phase A — Seed list (manual curation)**
- Curate a list of ~50 notable AI blogs and research groups
- Add as RSS sources with `content_type=blog` or `content_type=research`
- Existing pipeline handles the rest

**Phase B — arXiv integration**
- Monitor arXiv RSS feeds for cs.AI, cs.CL, cs.CV, cs.LG
- Filter by engagement signals (Twitter mentions, HN discussion, citations)
- LLM classifier (Haiku) decides: "Is this paper notable enough for a general AI audience?"

**Phase C — Active discovery (future)**
- Agent-driven research: "Find notable AI blog posts from this week"
- Use Grok/Twitter to find viral technical content
- Community submissions (from forum integration)

### Blog Seed List (Phase A)
```
# Individual practitioners
- Simon Willison (simonwillison.net)
- Lilian Weng (lilianweng.github.io)
- Jay Alammar (jalammar.github.io)
- Chip Huyen (huyenchip.com)
- Sebastian Raschka (magazine.sebastianraschka.com)

# Research groups
- Google Research Blog
- Meta AI Blog
- Anthropic Research
- EleutherAI Blog

# Technical deep-dives
- The Gradient
- Distill.pub (if active)
- Machine Learning Mastery (selected posts)
```

### arXiv Integration (Phase B)
- RSS feeds: `https://arxiv.org/rss/cs.AI`, `cs.CL`, `cs.CV`, `cs.LG`
- High volume — need filtering:
  1. Check if paper is discussed on HN (hnrss.org search)
  2. Check if paper is tweeted about (Grok search, if available)
  3. LLM filter: "Is this paper notable for a general AI audience?"
- Only papers passing 2+ signals get ingested as articles

## Edge Cases & Considerations

### Handled
- **Volume**: arXiv has hundreds of papers daily — aggressive filtering required
- **Duplicates**: Papers may appear in multiple feeds — existing dedup handles this
- **Quality bar**: Blog posts have lower bar than news (fewer sources needed for an event)

### Limitations
- Active discovery (Phase C) is open-ended and expensive
- arXiv filtering may miss important niche papers
- Blog RSS feeds may go stale — need monitoring

## Definition of Done

### Acceptance Criteria (Phase A only)
- [ ] 20+ blog sources added to sources table
- [ ] Blog posts appear in feed with appropriate category/tags
- [ ] Content quality is comparable to newsletter-sourced events

## Outstanding
- [ ] Compile full blog seed list
- [ ] Research arXiv RSS feed format and volume
- [ ] Decide: separate "blog" category or use existing categories?
- [ ] Decide: should blog posts be events or a different content type?
