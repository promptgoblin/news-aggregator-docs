# Feature: Custom RSS Feeds

---
type: feature
status: planning
complexity: C1
tags: [rss, api, feeds]
depends_on: [production_deployment]
required_by: []
---

## User Intent

### Goal
Offer RSS feeds from Goblin News that users can subscribe to in their RSS reader. Feeds are filterable by category, tags, score threshold, and other parameters — so users get exactly the slice of AI news they want.

### Success Criteria
- `/feed.xml` returns a valid RSS 2.0 / Atom feed of all events
- Filter params work: `?categories=research,products&tags=openai&score_min=7`
- Feeds are bookmarkable URLs (all config in query params)
- Feed items include title, summary (tier1_scan), link to event page, published date
- Feed validates against standard RSS validators

### User Flow
1. User visits news.promptgoblins.ai/feed
2. Sees a feed builder UI (optional) or just constructs URL manually
3. Copies feed URL with desired filters
4. Adds to RSS reader (Feedly, NetNewsWire, etc.)
5. New events matching their filters appear in their reader

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## Implementation

### Approach
A single `/feed.xml` endpoint on the FastAPI backend that accepts the same filter params as the events list API. Renders RSS 2.0 XML. Optionally, a simple feed builder page on the frontend to help users construct their URL.

### Key Components
- **`GET /feed.xml`** — FastAPI endpoint, returns `application/rss+xml`
- **Filter params**: `categories`, `tags`, `score_min`, `range`, `sort`, `top_news`
- **Feed builder page** (optional): `/feed` on frontend with checkboxes → generates URL

### Feed Item Structure
```xml
<item>
  <title>{event.title}</title>
  <link>https://news.promptgoblins.ai/event/{event.slug}</link>
  <description>{event.tier1_scan}</description>
  <pubDate>{event.published_at RFC 822}</pubDate>
  <category>{event.category}</category>
  <guid isPermaLink="true">https://news.promptgoblins.ai/event/{event.slug}</guid>
</item>
```

### Caching
- Cache feed response for 15 minutes (pipeline runs 2x daily, so feeds are relatively stable)
- `Cache-Control: public, max-age=900`
- ETags for conditional requests

## Edge Cases & Considerations

### Handled
- **Empty feed**: Return valid XML with 0 items (not an error)
- **Too many items**: Cap at 50 most recent events per feed
- **Special characters in titles**: XML-escape all content
- **Invalid filter params**: Ignore unknown params, use defaults for invalid values

### Performance
- Reuses the same query logic as the events API (no duplication)
- Caching prevents DB hammering from RSS readers polling frequently

## Definition of Done

### Acceptance Criteria
- [ ] `/feed.xml` returns valid RSS 2.0
- [ ] Filters work: categories, tags, score_min
- [ ] Feed renders correctly in at least 2 RSS readers
- [ ] Feed auto-discovery tag in HTML `<head>` of frontend pages

## Outstanding
- [ ] Decide: RSS 2.0 vs Atom vs both
- [ ] Decide: feed builder UI now or later?
- [ ] Decide: include tier1_scan only in description, or also key points?
