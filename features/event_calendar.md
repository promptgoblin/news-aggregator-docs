# Feature: AI Event Calendar

---
type: feature
status: planning
complexity: C3
tags: [calendar, events, discovery, search, sourcing]
depends_on: [production_deployment]
required_by: []
---

## User Intent

### Goal
A filterable calendar of AI conferences, meetups, hackathons, and local events. Searchable by location/distance, filterable by type, and browsable by month. The most differentiated value is **comprehensive local/community event coverage** — the long tail that nobody else aggregates well.

### Success Criteria
- Calendar view with AI events across all tiers (major conferences → local meetups)
- Filter by event type, location (city/radius), date range, topic/tags
- Search by distance from user's location ("events within 50 miles")
- Event detail: name, date(s), location, description, link, type, cost, eligibility
- Hackathons are a first-class filterable category (dedicated audience hunts for these)
- Community submission flow with admin approval queue
- Comprehensive coverage of major AI conferences + growing local event coverage
- Every event includes: who can attend + cost

### User Flow
1. User visits news.promptgoblins.ai/events (tab: News | **Events** | About)
2. Sees calendar/list view of upcoming AI events
3. Filters by type (conferences, vendor events, meetups, hackathons), location, date range
4. Enters location → sees events within chosen radius
5. Clicks event → sees details + link to register
6. Can subscribe to filtered calendar via iCal/RSS
7. Can submit an event (requires Discourse SSO login) → admin approval queue

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-27

## Event Type Taxonomy

| Type | Description | Examples |
|------|-------------|---------|
| **AI Conference** | Dedicated AI/ML conferences | GTC, NeurIPS, ICML, ICLR, CVPR, AAAI, AI World's Fair |
| **AI Track** | Tech conferences with significant AI content | AWS re:Invent, Dreamforce, CES, WWDC, Google I/O, GitHub Universe |
| **Vendor Event** | Company-organized AI events, mini-conferences | DigitalOcean AI Day, Anthropic meetups, startup demo days |
| **Community Event** | Local meetups, user groups, community-organized | SF AI Meetup, local ML reading groups |
| **Hackathon** | Cross-cuts all levels; standalone label | GTC hackathons, standalone AI hackathons, offsite hackathons at conferences |
| **University Event** | Public talks, seminars, workshops from university AI labs | Stanford HAI talks, MIT CSAIL seminars (must be open to public) |

**Hackathon** is a separate filterable label that can co-exist with a parent event. "GTC Hackathon" is tagged as both a hackathon and associated with the GTC conference.

**Eligibility rule**: Only include events open to the public. Exclude student/faculty-only events. Every event must have: who can attend + cost.

## Sourcing Architecture

Sourcing is the product. The calendar UI and geo-search are solved problems. The hard part is comprehensive, accurate, fresh event data — especially the long tail of local events.

### Tier 1 — Major AI Conferences (low volume, high value)

**Discovery:**
- Initial seed via manual Grok X search (prompts provided separately)
- Sonnet sub-agent web research sweeps (quarterly) to catch new conferences
- X announcements are the primary signal — conferences are announced on X months before they generate news coverage

**Ongoing:**
- Track conference websites; scrape for date/venue updates (weekly or monthly — conference dates don't change often)
- Freshness re-confirmation: monthly scrape + Haiku check → weekly within 30 days of event

### Tier 2 — AI-Adjacent / AI Track Conferences (low volume, medium value)

**Discovery:** Same as Tier 1. Labeled "AI Track" with note on what AI content they feature.

**Value prop:** AI practitioners want to know which non-AI conferences have good AI content. "AWS re:Invent — major AI/ML track, keynote covers Bedrock/SageMaker" is useful context nobody else curates.

### Tier 3 — Local & Community Events (high volume, highest differentiation)

This is the most underserved and most valuable tier.

**Discovery sources (priority order):**
1. **Grok X search (xAI API)** — per-metro monthly sweeps. X is where local events get announced. Use existing Grok API (same as news sentiment).
2. **Community submissions** — the flywheel. Once people check the calendar, they'll want their events listed. Discourse SSO + simple form + admin approval queue. Becomes the primary growth driver over time.
3. **Meetup API** — add later if Grok + submissions leave gaps. Requires Meetup Pro ($30/mo). GraphQL API supports keyword + lat/lon + radius search. Defer until we validate the gap.
4. **Lu.ma** — monitor `luma.com/ai` category manually or via light scraping. Major AI community calendars (Bond AI, The AI Collective) are rich sources. No discovery API — organizer-only. Consider following their community calendars on X (Grok catches these).
5. **University AI lab talks** — add sources as we discover them through research. University AI bulletin boards, lab event pages.

**Per-metro search approach:**
Start with 15 tech-weighted metros: SF/Bay Area, NYC, Seattle, Austin, LA, Boston, Chicago, Denver/Boulder, DC, Miami, Atlanta, Dallas/Fort Worth, London, Toronto, Berlin. Monthly Grok sweeps per city.

### Cross-Cutting

**Freshness / Re-confirmation:**
Events change dates, get canceled, change venues. Stale data is worse than missing data.
- Monthly scrape of event URL + Haiku extraction: "Is this still happening? Same dates? Same venue? Any changes?"
- Increase frequency as event approaches: monthly → weekly within 30 days
- Flag "updated" events so users see changes
- Detect cancellations

**Dedup:** Match by URL + name + date range. Events may appear in multiple sources.

**Geocoding:** Convert addresses/city names to lat/lng for distance search. Nominatim (free, OSM-based) for MVP. Google Maps Geocoding API as upgrade if needed.

## API Research Results (2026-03-27)

### Eventbrite — Dead End
- Search endpoint (`/v3/events/search/`) **killed in February 2020**, never replaced
- Remaining API only retrieves events by specific ID or organization — no discovery
- API reportedly "deprecated and unsupported" as of 2025
- **Decision: Skip entirely**

### Meetup — Viable, Paywalled
- GraphQL API supports keyword + location (lat/lon + radius) search
- Rich event data (title, date, venue, description, cost, RSVP counts, group info)
- **Requires Meetup Pro subscription (~$30/mo)** just to register an OAuth app
- No free tier. Rate limits undocumented.
- **Decision: Defer. Validate Grok + submissions first. Add if local coverage gap exists.**

### Lu.ma — Great Data, No Discovery API
- Official API is organizer-only (manage your own events, no search/browse)
- Dedicated AI category (`luma.com/ai`) with ~3K events, major community calendars
- Site is scrapeable (Next.js, Apify has working scrapers with 40+ fields)
- ToS technically prohibits automated access
- **Decision: Monitor manually. Follow community calendars on X (Grok catches announcements). Consider light scraping of AI category page if needed. Revisit if Lu.ma opens a discovery API.**

## Model Decisions

| Task | Model | Reasoning |
|------|-------|-----------|
| Event extraction from scraped pages | **Haiku** | High volume, structured extraction. Eval carefully to ensure quality. |
| Event classification & labeling | **Haiku** | Taxonomy is clear, low judgment needed |
| Conference research sweeps | **Sonnet** (sub-agents) | Needs web research + judgment about what qualifies |
| Scoring / vetting | **Sonnet** | Only if rubric isn't sufficient for Haiku. Start with Haiku + clear rubric, upgrade if quality drops. |
| X search for event discovery | **Grok** (grok-4-1-fast-reasoning) | Same model as news sentiment. x_search for real X post search. |
| Freshness re-confirmation | **Haiku** | Scrape page + extract "still happening? dates? venue?" — simple structured task |

**No Opus needed** if scoring/vetting rubric is very clear. Clear rubric → Haiku can handle it. Save Sonnet for judgment calls.

## Data Model

```python
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[uuid.UUID]
    name: Mapped[str]
    description: Mapped[str | None]
    event_type: Mapped[str]  # ai_conference, ai_track, vendor_event, community_event, university_event
    is_hackathon: Mapped[bool]  # cross-cutting label, can co-exist with any type
    parent_event_id: Mapped[uuid.UUID | None]  # e.g., GTC Hackathon → GTC
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    location_name: Mapped[str]  # "Moscone Center, San Francisco"
    location_city: Mapped[str]
    location_country: Mapped[str]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    url: Mapped[str]
    cost: Mapped[str | None]  # "Free", "$499", "$99-$299"
    eligibility: Mapped[str | None]  # "Open to public", "Requires registration", etc.
    is_virtual: Mapped[bool]
    tags: Mapped[list[str]]  # reuse existing tag taxonomy
    source: Mapped[str]  # where we found it
    submitted_by: Mapped[int | None]  # discourse user id, if community-submitted
    status: Mapped[str]  # active, canceled, pending_approval
    ai_track_notes: Mapped[str | None]  # for AI Track type: what AI content is featured
    last_confirmed: Mapped[datetime | None]  # last freshness check
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

## Community Submission Flow

1. User clicks "Submit Event" on /events page
2. Must be logged in (Discourse SSO — same as news app)
3. Simple form: name, dates, location, URL, type, cost, description, eligibility
4. Submits → stored with `status=pending_approval`
5. Admin sees queue in admin panel, approves/rejects/edits
6. Approved events go live immediately
7. Haiku auto-fills missing fields (geocoding, tags) on approval

## Distance Search

```sql
-- Simple haversine distance (no PostGIS needed for MVP)
SELECT *, (
  6371 * acos(
    cos(radians(:lat)) * cos(radians(latitude))
    * cos(radians(longitude) - radians(:lng))
    + sin(radians(:lat)) * sin(radians(latitude))
  )
) AS distance_km
FROM calendar_events
WHERE start_date >= :today
  AND status = 'active'
HAVING distance_km <= :radius
ORDER BY start_date
```

## Edge Cases & Considerations

### Handled
- **Virtual events**: `is_virtual=true`, no location filter needed
- **Multi-day events**: `start_date` + `end_date`, show on all days
- **Canceled events**: `status=canceled`, visible but clearly marked
- **Duplicate events**: Dedupe by URL + name + date range
- **Hackathons at conferences**: `is_hackathon=true` + `parent_event_id` links to conference
- **AI Track disclosure**: `ai_track_notes` explains what AI content is featured
- **Eligibility**: Every event must state who can attend. Student-only = excluded.

### Limitations
- Grok X search may miss events not posted on X
- Geocoding accuracy varies (especially for "TBD" venues)
- Community submissions require moderation effort
- No Eventbrite API for discovery (killed 2020)
- Meetup API requires $30/mo paid subscription

## Definition of Done

### Acceptance Criteria
- [ ] `/events` page shows upcoming AI events (tab in nav: News | Events | About)
- [ ] Filter by event type, location radius, date range works
- [ ] Hackathon filter works as cross-cutting label
- [ ] Event detail page with register link, eligibility, cost
- [ ] iCal export with filters
- [ ] Community submission form (requires SSO login) + admin approval queue
- [ ] At least 50 events seeded (major conferences + initial local events)
- [ ] Freshness pipeline running (monthly re-confirmation)

## Outstanding

- [x] Research: Meetup API access → paywalled ($30/mo), defer
- [x] Research: Eventbrite API access → dead end, skip
- [x] Research: Lu.ma API access → organizer-only, no discovery, monitor manually
- [ ] Decide: PostGIS vs haversine SQL for distance (haversine for MVP)
- [ ] Decide: geocoding provider (Nominatim for MVP)
- [ ] Run initial Grok seeding (major conferences, AI track, per-metro)
- [ ] Design admin approval queue UI
- [ ] Design submission form
- [ ] Seed list of major AI conferences for 2026-2027
