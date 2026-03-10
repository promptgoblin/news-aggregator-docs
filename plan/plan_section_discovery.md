# Plan Section: Comprehensive Discovery

---
type: plan_section
tags: [sources, ingestion, coverage, newsletters, rss, twitter]
last_updated: 2025-02-25
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Discovery is one of two product pillars: don't miss stories. We cover all AI niches and industries because users filter — our job is comprehensive coverage. Newsletters are the highest priority source (already curated by experts), supplemented by RSS, Twitter/Grok, and agent-driven research. The goal: one feed replaces 5+ newsletters, and covers stories those newsletters miss.

## Decision History

**2025-02**: Newsletters as highest-priority source — already curated, high signal, reduce our pipeline work.
**2025-02**: Multi-channel strategy — no single source covers everything. Newsletters + RSS + social + agent research = comprehensive.
**2025-02**: Grok API for Twitter/X — native access to Twitter data, avoids scraping restrictions.
**2025-02**: Agent research as differentiator — autonomous discovery (arXiv, niche blogs, company announcements) so we're not just parroting newsletters.
**2026-02**: Adaptive source intelligence — system learns where stories come from over time. Auto-discovers new sources, tracks quality metrics, prunes low-value sources. Like a journalist building their beat.
**2026-02**: Broader coverage — enterprise, finance/markets, policy alongside technical. Filtering handles relevance per user. Enterprise AI is underserved.
**2026-02**: Content type rules — research papers = events. Tutorials = not events (unless 2+ sources pick them up). Generic how-to content dropped at ingestion.

## Key Decisions

### Newsletters as Primary Source
**Choice**: Newsletter ingestion is the first source adapter built, and newsletters are treated as high-trust sources.
**Rationale**: Newsletter curators already do discovery + curation. Aggregating from them gives us a comprehensive baseline fast. We add value through event intelligence (clustering, dedup, distillation) — not just by finding stories.
**Trade-offs**: Risk of being derivative if we ONLY use newsletters. Mitigated by additional channels and agent research.

### Sponsor/Ad Filtering
**Choice**: Actively filter sponsored content from newsletters before it enters the pipeline.
**Rationale**: Newsletters mix sponsored stories with editorial. Without filtering, ads pollute our signal. LLM-based detection of sponsor blocks, "presented by", etc.
**Alternatives**:
- Manual curation: Doesn't scale
- Let it through and score low: Risk of eroding trust

### Coverage-First Philosophy
**Choice**: Cast a wide net across all AI niches/industries, let users filter.
**Rationale**: Users in robotics, biotech AI, security AI, etc. don't get served by mainstream AI newsletters. Our coverage gap is their reason to use us. Better to have too many stories (filtered by tags) than miss important niche developments.

### Broader Than Pure Technical
**Choice**: Cover enterprise, finance/markets, and policy alongside technical AI news.
**Rationale**: Our audience is technical but also cares about enterprise adoption, the AI investment landscape, and regulatory developments. Enterprise AI is underserved in existing newsletters. Finance/market events (earnings, valuations, bubble discourse) give context that technical users want but rarely get. Filtering architecture (tags, presets, user preferences) ensures breadth doesn't dilute relevance for any user segment.

### Content Type Ingestion Rules
**Choice**: Research papers are events. Breakthrough techniques are events. Generic tutorials are not.
**Rationale**: A paper hitting arXiv IS a real-world event. A new technique getting picked up by multiple newsletters IS newsworthy. "How to fine-tune Llama" is NOT an event — it's evergreen content. The rule: **if it would make news in the AI community, it's an event regardless of format.** Newsletter extraction tags content type; `tutorial` items get dropped before entering the event pipeline unless they appear in 2+ sources (signal of genuine significance).
**Trade-offs**: May miss the occasional genuinely useful tutorial. Acceptable — better to under-ingest tutorials than pollute the event feed with medium-quality how-to content.

## Design

### Source Hierarchy

| Priority | Channel | Trust | Coverage Role |
|----------|---------|-------|---------------|
| P0 | Newsletters | High | Baseline comprehensive coverage |
| P1 | RSS (company blogs) | High | Primary/authoritative announcements |
| P1 | RSS (tech publications) | Medium-High | Professional journalism |
| P2 | Twitter/X via Grok | Medium | Breaking news, social signal, expert takes |
| P3 | Agent research | Variable | Gap-filling, niche coverage, arXiv |

### Newsletter Ingestion

**Mechanism**: Gmail API adapter
1. Dedicated inbox receives newsletter subscriptions
2. Polling job checks for new emails on schedule (every 15 min)
3. Parse email HTML → extract individual story links/summaries
4. **Sponsor filter**: LLM classifies each story block as editorial vs. sponsored
5. Extract: headline, summary text, linked URL, newsletter source
6. Follow links to get full article text when available
7. Feed extracted articles into event intelligence pipeline

**Initial Newsletter List** (Phase 2):

| Newsletter | Focus | Frequency |
|------------|-------|-----------|
| AI Daily Brief | Broad AI, links to stories discussed | Daily |
| The Batch (Andrew Ng) | ML/AI research + industry | Weekly |
| Import AI | Research-focused | Weekly |
| The Neuron | Broad AI, accessible | Daily |
| TLDR AI | Broad AI, brief format | Daily |
| Ben's Bites | AI products + startups | Daily |
| Superhuman AI | AI tools + productivity | Weekly |
| AI Breakfast | Industry + business AI | Daily |
| The Rundown AI | Broad AI | Daily |
| The Algorithm (MIT Tech Review) | Research + policy | Weekly |
| Hugging Face Newsletter | Open source ML | Bi-weekly |
| Paper with Code Newsletter | Research papers | Weekly |

Target: 15–20 newsletters at launch covering broad AI, research, industry, tools, and policy.

### RSS Ingestion

**Mechanism**: RSS/Atom feed polling
1. Feed list maintained in database with poll intervals
2. Celery beat scheduler triggers feed checks
3. Parse feed entries → extract new items since last check
4. Clean and extract article content (readability extraction from full URL)
5. Feed into event intelligence pipeline

**Initial RSS Sources**:

| Category | Sources |
|----------|---------|
| Company blogs | OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft Research, Stability AI, Mistral, Cohere |
| Research | arXiv cs.AI/cs.CL/cs.LG (filtered), Distill.pub, Google Research Blog |
| Publications | The Verge (AI), TechCrunch (AI), Ars Technica (AI), MIT Tech Review |
| Industry | VentureBeat AI, The Information, Semafor AI |
| Open source | Hugging Face blog, LangChain blog, LlamaIndex blog |

### Twitter/X via Grok (Phase 4)

**Mechanism**: Grok API for native Twitter data access
1. Monitor curated list of AI accounts (researchers, company accounts, founders)
2. Track trending AI topics and hashtags
3. Extract tweets and threads that indicate new events
4. Feed into pipeline with lower trust weight (noisy channel)

**Value**: Breaking news (often hits Twitter first), expert commentary, social signal for scoring.

### Agent Research (Phase 4+)

**Mechanism**: Claude Agent SDK, autonomous discovery
1. **arXiv monitor**: Daily scan of new papers in cs.AI, cs.CL, cs.LG, cs.CV — filter by citation velocity, author prominence, topic relevance
2. **Gap detection**: Identify topics/companies with low coverage, proactively search for developments
3. **Company tracker**: Monitor known AI companies for announcements not caught by other channels
4. **Niche explorer**: Periodically search for AI applications in under-covered domains (healthcare, climate, education, defense, finance)

**Differentiator**: This is what separates us from just re-packaging newsletters. Our agent finds stories nobody else is covering.

### Coverage Goals

| Dimension | Target | How |
|-----------|--------|-----|
| Major announcements | 99% within 2 hours | Newsletters + RSS + Twitter |
| Research papers | Top 20 papers/week identified | arXiv monitor + research newsletters |
| Industry moves | 95% (funding, acquisitions, partnerships) | Industry newsletters + RSS + agent |
| Niche/vertical AI | 80% coverage across 10+ verticals | Agent research + niche newsletters |
| Open source releases | 90% of significant releases | HF + GitHub trending + dev newsletters |
| Policy/regulation | 90% of major policy moves | Policy newsletters + RSS |

### Adaptive Source Intelligence

The system should learn where stories come from and get smarter over time — like a journalist building their beat. Not a static source list, but a living intelligence network.

**Source Discovery (continuous):**
- When a new company or product appears in multiple stories, check if we're following their blog/press releases — if not, auto-suggest adding them as an RSS source
- When we find a high-quality newsletter or news source we're not tracking, flag it for addition
- When a new AI vertical emerges (e.g., AI in agriculture), proactively search for niche sources covering it
- Agent research identifies coverage gaps → agent finds sources to fill those gaps

**Source Learning (automated metrics):**
- Track which sources break stories first (timeliness score)
- Track which sources contribute unique information vs. just repeating others (uniqueness score)
- Track which sources have highest signal-to-noise (accuracy score — what % passes quality filter)
- When multiple sources cover the same event, learn which is the best/most complete (best-of-redundant)
- Identify low-quality sources that consistently produce noise → auto-reduce poll frequency or deactivate

**Source Pruning:**
- Sources with trust scores below 0.3 for 30+ days → auto-deactivate, flag for review
- Sources that are consistently redundant with a higher-quality source → reduce poll frequency
- Sources that go inactive (no new content for 60 days) → auto-deactivate
- Sources whose quality degrades significantly → flag for manual review

**The goal**: Over months, the system develops an increasingly refined understanding of the AI news landscape — knowing exactly where to look for specific types of stories, which sources to trust for what, and which sources are noise. Just like a senior reporter who knows their beat cold.

### Source Quality Tracking

Each source gets a trust score that evolves over time:

```
trust_score = base_trust × accuracy_modifier × timeliness_modifier × uniqueness_modifier

base_trust: Set per source type (newsletter=0.8, blog=0.7, social=0.4)
accuracy_modifier: What % of stories from this source are substantive (not spam/ads)
timeliness_modifier: How early does this source typically report vs. others
uniqueness_modifier: What % of this source's stories add info not found elsewhere
```

Trust scores influence:
- Event intelligence: source weighting in distillation
- Scoring: events from high-trust sources get baseline score boost
- Quality filtering: low-trust-only events may need more sources before publishing
- Poll frequency: higher trust = more frequent polling
- Source pruning: low trust over time = auto-deactivation candidate

## Dependencies & Constraints

### Dependencies
- **Gmail API**: OAuth setup for newsletter inbox
- **RSS parser**: feedparser or similar library
- **Grok API**: Access for Twitter data (Phase 4)
- **Claude Agent SDK**: Autonomous research agents (Phase 4+)

### Constraints
- **Newsletter parsing variability**: Every newsletter has different HTML structure. Need robust extraction.
- **Rate limits**: Gmail API, Grok API, RSS feeds all have rate limits to respect
- **Cost**: Agent research uses LLM calls — budget per-run limits needed
- **Legal**: Respect robots.txt, ToS for content extraction. We link back, attribute, and drive traffic.

### Plan Section Dependencies
- Required by [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Supplies raw articles
- Depends on [plan_section_data_model.md](plan_section_data_model.md): Source, Article, Channel schemas
- Related to [plan_section_taxonomy.md](plan_section_taxonomy.md): Source categories map to tag taxonomy

## Impact on Features
- Newsletter Ingestion feature: Defined here
- RSS Ingestion feature: Defined here
- Twitter/X via Grok feature: Phase 4, outlined here
- Source Quality Dashboard feature: Uses trust scores defined here

## Risks

### Newsletter HTML Parsing Fragility
- **Probability**: High
- **Impact**: Medium — broken parsing = missed stories
- **Mitigation**: LLM-assisted extraction (send HTML to Claude, ask for structured story list). More expensive but dramatically more robust than regex/CSS selectors. Per-newsletter templates as fallback.

### Source Dependency
- **Probability**: Low
- **Impact**: High — if key newsletters shut down or go paid-only
- **Mitigation**: Diversify across 15+ newsletters. RSS and agent research provide independent coverage. No single source should represent >15% of total story volume.

### Over-Coverage (Too Many Stories)
- **Probability**: Medium
- **Impact**: Low — this is the good kind of problem
- **Mitigation**: Quality filtering, scoring thresholds, user-configurable filters. Better to have comprehensive coverage with good filtering than miss stories.

## Open Questions
- [ ] Gmail API vs. IMAP for newsletter ingestion? (Gmail API is cleaner but requires Google Cloud setup)
- [ ] How many newsletters is optimal at launch? Start with 12–15, expand based on coverage gaps?
- [ ] Should we also monitor Reddit (r/MachineLearning, r/artificial)?
- [ ] Podcast transcripts (YouTube auto-captions) — worth the parsing complexity?

## References
- Original Spec: [reference/spec_ai_signal_platform.md](../reference/spec_ai_signal_platform.md)
- Gmail API: https://developers.google.com/gmail/api
- Grok API: For Twitter/X data access

## Implementation Notes
- Newsletter parsing is the riskiest part — prototype early in Phase 1 with 3–4 diverse newsletters
- Use LLM extraction for newsletters rather than brittle HTML parsing — more expensive but handles format changes
- Build a "coverage dashboard" early to track: stories per source per day, overlap %, unique story rate
- Start with the "AI Daily Brief" newsletter — it links to all stories discussed, making it a perfect baseline source
- RSS feeds are the easiest to implement — start there for quick wins while newsletter parsing is developed
