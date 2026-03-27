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
Go beyond passively consuming RSS feeds and newsletters. Actively curate blogs and research papers — finding content that's worth covering even if it doesn't appear in our existing sources. This differentiates Goblin News from just being a newsletter aggregator.

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

## Status: Deferred (2026-03-27)
**Started**: 2026-03-09
**Last Updated**: 2026-03-27

### Decision: Defer Dedicated Research & Blog Pipelines

**Decision**: Do not build dedicated research paper or blog curation pipelines. Remove Research and Blogs tabs from the frontend. Keep the news pipeline as the single pipeline, which already picks up noteworthy research and blog content organically when it gets newsletter/media coverage.

**Reasoning**:

1. **Cost** — arXiv publishes 100+ AI papers/day. Even reading abstracts with Haiku adds up, and processing full papers for distillation burns serious tokens on content that may score low. Blog discovery has similar volume-to-signal problems.

2. **Source diversity for blogs** — Without massive source breadth, a blog feed would oversample the same handful of sources (model lab blogs, etc.) and look like promotion rather than curation. The news pipeline already covers these when the posts are newsworthy.

3. **Signal quality** — The news pipeline works because sources pre-curate: newsletter editors already filtered, journalists already decided something was worth covering. arXiv and random blogs have no such filter. Building editorial judgment from scratch in prompts is expensive to tune and easy to get wrong. LLMs tend to rate things as "interesting" based on how the content presents itself (hype in a blog post, novelty in a paper abstract) rather than actual importance.

4. **Forum is the better venue** — Research papers and tutorials are exactly the kind of content that users surface organically in community discussion — in response to questions, because something is genuinely useful, or because a practitioner found it valuable. This is more meaningful curation than any automated pipeline.

5. **Current pipeline already works** — Noteworthy research that gets newsletter/media coverage already appears in the news feed. A paper that doesn't get coverage probably isn't news. The existing research category filter still works for users who want to see what research the news pipeline picks up.

**What we kept**: Research and blog content that enters via the existing news pipeline (newsletters, RSS) continues to be processed normally. The category taxonomy still includes "research" for filtering. If research or blog content scores poorly or clutters the feed, we tune the existing pipeline rather than building new ones.

**Revisit when**: Revenue supports high token spend AND we have data showing users want dedicated research/blog feeds that the news pipeline can't satisfy.

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
