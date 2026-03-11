# Feature: Pipeline v2 — Source Quality & Curation Overhaul

---
type: feature
status: planned
priority: P0
tags: [pipeline, sources, ingestion, clustering, quality]
created: 2026-03-11
---

## Context

After the first production pipeline run, we identified systemic issues with article quality and mis-clustering. The root cause isn't the clustering algorithm — it's garbage content entering the pipeline. When `fetch_article_content()` fails (bot-blocked sites, JS-rendered pages, broken redirects), articles enter clustering with just a title or raw HTML. Haiku normalizes these into vague AI-domain summaries that embed too close together, causing unrelated stories to cluster.

### Problems Observed

1. **The Verge**: All 11 articles stored as raw `<figure>` HTML tags. Trafilatura gets nothing — site blocks bots.
2. **Alpha Signal**: 4/7 articles are just headlines (106 chars). Tracking links return 403.
3. **MIT Tech Review**: CSS/JS shell returned, article text loaded client-side. Paywall.
4. **NVIDIA Blog**: Content present in HTML but wrapped in `<div>` + inline styles that confuse trafilatura.
5. **The Batch**: HubSpot tracking URLs resolve to email rendering page, not articles.

These garbage articles then get HyDE-normalized into generic "AI tool released" / "AI research published" fingerprints, which embed close enough (>0.80) to unrelated articles to form false cluster edges. Result: events like "Andrew Ng Context Hub + NVIDIA RTX PRO Server" merged into one.

### Key Insight: Source Roles Have Changed

Original plan treated newsletters as the primary discovery source. In practice:
- **Newsletters are redundant** — 11 newsletters mostly cover the same stories
- **Newsletter extraction is our most fragile code path** (JMAP → HTML → Claude → URL resolution → content fetch)
- **Primary lab/company feeds give better content** — first-party, clean RSS, no extraction needed
- **Publication AI feeds exist** — The Verge, TechCrunch, Ars, etc. have dedicated AI RSS feeds
- **Google News AI RSS** is a catch-all that aggregates from 50+ publications in real-time

We are the curation layer. We don't need newsletters to curate for us. We need comprehensive discovery + quality content + good clustering.

## What Changes

### 1. Content Quality Gate (before clustering)

Articles must pass a quality check before entering the clustering pipeline. No more clustering HTML junk or title-only articles.

**Quality criteria:**
- `raw_content` must be ≥300 chars of actual text (not HTML tags)
- Content must not be primarily HTML (`<figure>`, `<div>`, `<span style=`) — detect with simple heuristic
- Binary content already filtered (PDF, PNG headers)

**If quality check fails:**
- Mark article as `low_content` status (new processing_status value)
- Do NOT send to clustering
- Article still exists in DB for URL dedup purposes (so we don't re-fetch it)
- Can be upgraded later if content becomes available (e.g., scrape.do retry)

### 2. Extraction Chain (fix content extraction failures)

Current extraction is trafilatura-or-nothing. NVIDIA Blog and Microsoft Research have content IN the HTML but trafilatura fails on their WordPress/custom markup (inline styles, `<div>` wrappers, `<figure>` blocks). The Verge and Wired are bot-blocked entirely. Different problems need different tools.

**Extraction chain (cheapest → most expensive):**

```
1. trafilatura              → best for clean HTML, fast, free
2. readability-lxml         → Mozilla Readability algorithm, handles messy WordPress/blog layouts
3. scrape.do                → renders JS, bypasses bot-blocking, handles paywalls. Costs per request.
4. fail → mark low_content
```

Steps 1-2 run on the HTML we already fetched (no additional network call). Step 3 is a separate request through scrape.do's rendering pipeline.

**Implementation in `fetch_article_content()`:**
1. Fetch HTML via httpx (same as today)
2. Try trafilatura on the HTML
3. Quality check: ≥300 chars of real text, not primarily HTML tags?
4. If fails → try `readability-lxml` on the same HTML (different extraction algorithm, often succeeds where trafilatura fails — it's what Firefox Reader View uses)
5. Quality check again
6. If fails AND `SCRAPE_DO_API_KEY` is set → fetch via scrape.do (renders JS, bypasses blocks), then extract with trafilatura + readability-lxml
7. If still fails → return None, let quality gate mark as `low_content`

**Why readability-lxml matters:** NVIDIA Blog stores article text inside `<span style="font-weight: 400;">` tags. Trafilatura sees styled markup and gives up. Readability uses content density heuristics (text-to-tag ratio per block) and correctly identifies the article body. This alone would have fixed ~50% of the extraction failures in the first production run (NVIDIA, Microsoft Research) without needing scrape.do.

**scrape.do config:** `SCRAPE_DO_API_KEY` env var. If not set, chain stops at step 5 (graceful degradation). Use sparingly — only when both local extractors fail. Track per-day usage.

**New dependency:** `readability-lxml` (add to pyproject.toml)

### 3. Restructure Source Tiers

Replace the current flat source list with explicit tiers that reflect each source's role in the pipeline.

**Guiding principle:** Only add AI-specific feeds. No general tech feeds that require us to filter for AI content. If a publication doesn't have an AI-specific RSS feed, skip it — Google News AI will catch their AI stories anyway.

#### Tier 1 — Primary Sources (lab/company blogs)

High trust, always ingest, clean RSS. These are the canonical content sources.

**Keep:**
- OpenAI Blog (have — `openai.com/blog/rss.xml`)
- Google DeepMind Blog (have — `deepmind.google/blog/rss.xml`)
- Microsoft Research Blog (have — `microsoft.com/en-us/research/feed/`)
- NVIDIA AI Blog (have — `blogs.nvidia.com/feed/`)
- Hugging Face Blog (have — `huggingface.co/blog/feed.xml`)
- LangChain Blog (have — `blog.langchain.dev/rss/`)

**Add:**
| Source | Feed URL | Notes |
|--------|----------|-------|
| Google AI Blog | `blog.google/innovation-and-ai/technology/ai/rss` | Gemini, Search AI, broader than DeepMind |
| Microsoft AI Blog | `microsoft.com/en-us/ai/blog/feed` | Copilot, Azure AI, Foundry — broader than Research |
| OpenAI News | `openai.com/news/rss.xml` | Acquisitions, policy, company news (complements /blog/) |
| AWS ML Blog | `aws.amazon.com/blogs/machine-learning/feed/` | Bedrock, SageMaker, enterprise AI |
| Stability AI Blog | `stability.ai/blog?format=rss` | Stable Diffusion, open models |
| Cohere Blog | `txt.cohere.ai/rss/` | Enterprise AI, Aya models |

**No RSS available (covered by Google News AI + publications):**
- Meta AI, Anthropic, Mistral, xAI, Adobe, Baidu, DeepSeek, 01.AI, Alibaba/Qwen

These labs' announcements reliably appear in Google News AI and publication feeds within hours. Not worth building custom scrapers or depending on third-party generated RSS feeds maintained by random GitHub users. As direct feeds become available, we add them.

#### Tier 2 — Publication AI Feeds

Medium trust. Only AI-specific feeds — no general tech feeds that require filtering.

**Keep:**
- The Verge AI (`theverge.com/rss/ai-artificial-intelligence/index.xml`)
- TechCrunch AI (`techcrunch.com/category/artificial-intelligence/feed/`)
- MIT Tech Review (`technologyreview.com/feed/` — general feed, but heavily AI-focused editorially)

**Fix:**
- Ars Technica AI — change feed URL from `/technology-lab` to `arstechnica.com/ai/feed/`

**Add:**
| Source | Feed URL | Notes |
|--------|----------|-------|
| Google News AI | `news.google.com/rss/topics/CAAqIAgKIhpDQkFTRFFvSEwyMHZNRzFyZWhJQ1pXNG9BQVAB?hl=en-US&gl=US&ceid=US%3Aen` | Catch-all aggregator. No title filter needed — it's already AI-scoped. Cap at 50 items per poll. |
| Fast Company AI | `fastcompany.com/section/artificial-intelligence/rss` | AI-specific section feed |
| Computerworld AI | `computerworld.com/artificial-intelligence/feed/` | AI-specific section feed |
| Wired AI | `wired.com/feed/tag/ai/latest/rss` | AI-specific tag feed. Need to verify from server. |

**Drop:**
- VentureBeat AI — last post January 2026, effectively dead
- The Information — hard paywall, 403 on RSS
- NYT AI, FT AI, Guardian AI — paywalled or blocked, and covered by Google News AI

#### Tier 3 — Newsletter Safety Net (3)

Kept simple. Same ingestion pipeline as today, plus quality gate. No architectural changes — just trim the list, add quality checks, and ensure we follow source links instead of storing roundup blurbs.

**Keep (3):**
- **TLDR AI** — broadest mainstream AI coverage, daily
- **AI Daily Brief** — excellent curated link lists with direct source URLs per story. Perfect discovery source.
- **Import AI** — research/niche picks that might not hit mainstream feeds

**Deactivate (8):**
Alpha Signal, The Batch, The Neuron, Ben's Bites, Superhuman AI, AI Breakfast, The Rundown AI, The Algorithm

These are redundant with each other and with our Tier 1+2 feeds. Can reactivate if we find coverage gaps.

#### Aggregator Feeds

**Keep:**
- Hacker News AI (have) — indie/hacker signal
- Hacker News AI Labs (have) — lab-specific discussions

### 4. Newsletter Quality Rules

No architectural overhaul — just add these rules to the existing newsletter pipeline:

1. **Quality gate** — same as RSS. If we can't extract ≥300 chars of real content from the linked URL, mark `low_content` and don't cluster.
2. **No roundup articles** — if a newsletter item's URL points to another aggregator/roundup instead of a primary source, skip it. Only follow links to actual source articles.
3. **Don't hallucinate** — if we can't read a story (fetch fails, paywall, etc.), stop. Don't create an article with just the newsletter's one-line summary. Either get the real content or don't ingest it.
4. **URL dedup before fetch** — check if we already have an article with this URL (resolved or original) from any source. If yes, skip the fetch entirely. This catches overlap with RSS feeds.

### 5. Google News AI Integration

Google News AI RSS is high-volume but already AI-scoped. No Haiku title filter needed.

- **Cap at 50 items per poll** — enough to catch most stories across a poll cycle
- **No title filter** — the feed is already AI-specific. Only add non-AI-specific feeds if they have their own AI RSS feed.
- **URL dedup before fetch** — many items will link to articles we already have from direct RSS feeds. Check resolved URL across all sources before creating a new article. Dedup is fast and local.
- **Cross-run dedup** — Google News AI may surface a story after our direct RSS feed already ingested it (different timing). Must dedup against articles from previous pipeline runs, not just the current batch.
- **Content extraction** — Google News links redirect to original sources. Follow redirects, then run the extraction chain.
- **Not a dependency** — this is a supplement. If Google changes/kills the feed, Tier 1+2 sources still cover 80%+ of stories.

### 6. URL Dedup Enhancement

With overlapping sources, URL-level dedup must work across sources and across pipeline runs.

**Current:** Dedup by exact `(url, source_id)` pair — only prevents the same source from re-ingesting the same URL.

**New:** Dedup by resolved URL across ALL sources:
- Before fetching any article content, resolve the URL (follow redirects) and check if any existing article has this resolved URL
- Store `resolved_url` as a first-class field on Article (currently buried in `source_metadata`)
- Index `resolved_url` for fast lookups
- This prevents: Google News AI + The Verge + TLDR AI all ingesting the same Adobe blog post as 3 separate articles

**Dedup is fast and local** — just a DB lookup. The redundancy across sources is fine because we catch it before any expensive operations (content fetch, embedding, clustering).

### 7. Quality Checker as Second Line of Defense

The QC subagent in Event Intelligence currently does subjective quality checks. Expand its role:

- **Combined event detection** — QC should flag when an event's source articles appear to cover different stories (catches any mis-clustering that slips through Stage 2b Haiku validation)
- **Content coherence** — verify the distilled summary is consistent with all source articles, not just the primary
- **Fail-safe** — if QC detects a combined event, the event should be split or flagged for re-clustering rather than published

This is the second line of defense after Stage 2b cluster validation. Between quality gate (prevents garbage in), cluster validation (catches bad clusters), and QC (catches bad events), we have three layers.

### 8. Cluster Validation (already implemented)

Stage 2b Haiku validation was deployed on 2026-03-11. Validates multi-article clusters before Event Intelligence. Splits clusters where Haiku identifies distinct stories.

Safety net — with better content quality, clusters should form correctly in the first place.

## Implementation Order

1. **Content quality gate** — quickest win, stops garbage from clustering immediately
2. **Extraction chain** — add readability-lxml fallback, then scrape.do when API key available
3. **URL dedup enhancement** — resolved URL dedup across sources and runs
4. **Newsletter quality rules** — no roundups, no hallucinated content, URL dedup before fetch
5. **Expand Tier 1 feeds** — add Google AI, MS AI, AWS, Stability, Cohere, OpenAI News
6. **Add Tier 2 feeds** — Google News AI, Fast Company, Computerworld, Wired, fix Ars Technica
7. **Trim newsletters** — deactivate 8, keep TLDR AI + AI Daily Brief + Import AI
8. **QC enhancement** — combined event detection in quality checker

Steps 1-4 can ship together as the quality foundation. Steps 5-7 are the source expansion. Step 8 is a safety net improvement.

## What Doesn't Change

- **HyDE clustering algorithm** — the approach is sound, the problem was input quality
- **Event Intelligence pipeline** — distiller, scorer, tagger, editor stay the same
- **Newsletter extraction architecture** — same JMAP + Claude pipeline, just with quality rules added
- **Dedup post-processing** — still needed for near-duplicate events
- **Sentiment (Grok)** — unchanged
- **Frontend** — unchanged
- **Thresholds** — HYDE_SIM=0.80, EVENT_MATCH=0.75, etc. remain. May revisit after quality gate proves out.

## Source Coverage Strategy

The direction is comprehensive primary feed coverage enhanced over time:

1. **Now:** Lab blogs with RSS + publication AI feeds + Google News AI catch-all + 3 newsletters as safety net
2. **Ongoing:** As more labs publish RSS feeds (or we find them), add them to Tier 1. The goal is to have direct feeds for every major AI company.
3. **Google News AI covers the long tail** — any AI story from any publication shows up here. We don't need to individually add every publication with an AI section.
4. **Newsletters validate coverage** — if a newsletter consistently surfaces stories we missed, that tells us we need a new direct feed for that source.

## Success Criteria

- Zero HTML-junk articles entering clustering
- Mis-clustered events drop to <5% (from ~20% observed in first run)
- Coverage maintained or improved vs. current 23-source setup
- Newsletter count reduced from 11 to 3 without missing major stories
- scrape.do usage stays under 100 requests/day (cost control)

## Open Questions

- [ ] scrape.do pricing — confirm per-request cost is acceptable for our volume
- [ ] Google News AI feed stability — any known rate limits or format changes?
- [ ] MIT Tech Review feed — is there an AI-specific topic feed, or just the general feed?
- [ ] Wired AI feed — need to verify it works from the production server (blocked from local dev by WebFetch)
