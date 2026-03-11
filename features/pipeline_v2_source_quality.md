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
| Anthropic News | `raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml` | Generated RSS — verify reliability |
| Mistral News | `raw.githubusercontent.com/0xSMW/rss-feeds/main/feeds/feed_mistral_news.xml` | Generated RSS — verify reliability |
| Stability AI Blog | `stability.ai/blog?format=rss` | Stable Diffusion, open models |
| Cohere Blog | `txt.cohere.ai/rss/` | Enterprise AI, Aya models |

**No RSS available (skip for now, covered by Google News AI + publications):**
- Meta AI, xAI, Adobe, Baidu, DeepSeek, 01.AI, Alibaba/Qwen

These labs' announcements reliably appear in Google News AI and publication feeds within hours. Not worth building custom scrapers when the discovery pipeline catches them anyway.

#### Tier 2 — Publication AI Feeds

Medium trust. These have dedicated AI RSS feeds that are pre-filtered. Provides coverage of stories that don't originate from company blogs (lawsuits, policy, acquisitions, independent analysis).

**Keep:**
- The Verge AI (`theverge.com/rss/ai-artificial-intelligence/index.xml`)
- TechCrunch AI (`techcrunch.com/category/artificial-intelligence/feed/`)
- MIT Tech Review (`technologyreview.com/feed/` — needs AI topic feed if available)

**Fix:**
- Ars Technica AI — change feed URL from `/technology-lab` to `arstechnica.com/ai/feed/`

**Add:**
| Source | Feed URL | Notes |
|--------|----------|-------|
| Google News AI | `news.google.com/rss/topics/CAAqIAgKIhpDQkFTRFFvSEwyMHZNRzFyZWhJQ1pXNG9BQVAB?hl=en-US&gl=US&ceid=US%3Aen` | Catch-all aggregator. Cap at 30 items per poll. Haiku title filter required. |
| Fast Company AI | `fastcompany.com/section/artificial-intelligence/rss` | Innovation + society angle |
| Computerworld AI | `computerworld.com/artificial-intelligence/feed/` | Enterprise/IT angle |
| Wired AI | `wired.com/feed/tag/ai/latest/rss` | Need to verify from server (blocked by WebFetch) |

**Drop (not worth the friction):**
- VentureBeat AI — last post January 2026, effectively dead
- The Information — hard paywall, 403 on RSS
- NYT AI, FT AI — paywalled, content not extractable

**Do NOT add (too noisy, too slow, or off-topic):**
- Science News AI, ScienceDaily AI — biweekly cadence, academic focus
- MIT News — general MIT news, heavy filtering needed
- The Conversation — mostly off-topic results
- The Guardian AI — blocked, and covered by Google News AI anyway

#### Tier 3 — Newsletter Safety Net (2 max)

Low priority. Discovery-only role — we use them to find stories we might have missed, not as content sources.

**Keep (2):**
- **TLDR AI** — broadest mainstream AI coverage, daily
- **Import AI** — research/niche picks that might not hit mainstream feeds

**Deactivate (9):**
Alpha Signal, AI Daily Brief, The Batch, The Neuron, Ben's Bites, Superhuman AI, AI Breakfast, The Rundown AI, The Algorithm

These are redundant with each other and with our Tier 1+2 feeds. Can reactivate if we find coverage gaps.

#### Aggregator Feeds

**Keep:**
- Hacker News AI (have) — indie/hacker signal
- Hacker News AI Labs (have) — lab-specific discussions

### 4. Newsletter Pipeline Changes

Newsletters shift from "ingest content" to "discover stories."

**Current flow:** Extract stories → fetch article content → create Article → cluster
**New flow:** Extract story references → check if URL already ingested from another source → if not, fetch + quality gate → create Article → cluster

Key change: if a newsletter mentions a story we already have from an RSS feed, we just note the newsletter mention (source count +1) without creating a duplicate article. The newsletter validates our discovery but doesn't add content.

### 5. Google News AI Integration

Google News AI RSS is high-volume (50-100+ items/day). Needs special handling:

- **Cap at 30 items per poll** (most recent)
- **Haiku title filter** — before fetching content, batch article titles through Haiku to filter non-AI stories (Google's AI topic feed still includes tangential tech stories)
- **URL dedup** — many items will link to articles we already have from direct RSS feeds. Skip those.
- **Content extraction** — Google News links go through `news.google.com` redirects to the original source. Must follow redirects. Then standard fetch + scrape.do fallback.
- **Don't over-depend** — this is a catch-all supplement, not the backbone. If Google changes/kills the feed, our Tier 1+2 sources still cover 80%+ of stories.

### 6. Dedup Enhancement

With more overlapping sources, URL-level dedup becomes more important:

- **Current:** Dedup by exact `(url, source_id)` pair
- **New:** Also dedup by resolved URL across sources. If The Verge and Google News AI both link to the same Adobe blog post, ingest it once.
- Store `resolved_url` on Article model (we partially do this already via `source_metadata`)
- Check resolved_url before creating new articles

### 7. Cluster Validation (already implemented)

Stage 2b Haiku validation was deployed on 2026-03-11. Validates multi-article clusters before Event Intelligence. Splits clusters where Haiku identifies distinct stories.

This is a safety net — with better content quality, clusters should form correctly in the first place. The validation catches edge cases.

## Implementation Order

1. **Content quality gate** — quickest win, stops garbage from clustering immediately
2. **scrape.do fallback** — improves content extraction for bot-blocked sites
3. **Expand Tier 1 feeds** — add Google AI, MS AI, AWS, Anthropic, Mistral, Stability, Cohere
4. **Add Tier 2 feeds** — Google News AI (with Haiku filter), Fast Company, Computerworld, Wired, fix Ars Technica
5. **URL dedup enhancement** — resolved URL dedup across sources
6. **Trim newsletters** — deactivate 9, keep TLDR AI + Import AI
7. **Restructure newsletter pipeline** — discovery-only flow

Steps 1-2 can ship independently. Steps 3-5 are the main source expansion. Steps 6-7 happen after we confirm Tier 1+2 coverage is sufficient.

## What Doesn't Change

- **HyDE clustering algorithm** — the approach is sound, the problem was input quality
- **Event Intelligence pipeline** — distiller, scorer, tagger, QC, editor all stay the same
- **Dedup post-processing** — still needed for near-duplicate events
- **Sentiment (Grok)** — unchanged
- **Frontend** — unchanged
- **Thresholds** — HYDE_SIM=0.80, EVENT_MATCH=0.75, etc. remain. May revisit after quality gate proves out.

## Success Criteria

- Zero HTML-junk articles entering clustering
- Mis-clustered events drop to <5% (from ~20% observed in first run)
- Coverage maintained or improved vs. current 23-source setup
- Newsletter count reduced from 11 to 2 without missing major stories
- scrape.do usage stays under 100 requests/day (cost control)

## Open Questions

- [ ] scrape.do pricing — confirm per-request cost is acceptable for our volume
- [ ] Anthropic/Mistral generated RSS feeds — how reliable are these GitHub-hosted feeds? Who maintains them?
- [ ] Google News AI feed stability — any known rate limits or format changes?
- [ ] Should we track "discovery source" separately from "content source" on articles? (e.g., "discovered via TLDR AI, content from openai.com")
