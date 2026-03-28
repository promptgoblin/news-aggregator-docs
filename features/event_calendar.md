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
| **AI Conference** | Dedicated AI event, any size, any organizer. The common thread: this event is about AI. | GTC, NeurIPS, ICML, LangChain Interrupt, Databricks Data+AI Summit, AI Engineer World's Fair, AI Dev 26, AI in Finance Summit, DigitalOcean AI Day |
| **AI Track** | Broad tech conference with significant AI content — enough for an AI practitioner to justify 1+ days of relevant content. | AWS re:Invent, Dreamforce, CES, WWDC, Google I/O, GitHub Universe, Web Summit Vancouver |
| **Community Event** | Local meetups, user groups, community-organized gatherings. Informal, often recurring. | SF AI Engineers, AI Tinkerers, NYC AI/ML Conversations, ML Networking and Drinks |
| **Hackathon** | Cross-cuts all types; standalone filterable label. | GTC hackathons, standalone AI hackathons, offsite hackathons, PokeeClaw, AICamp hackathons |
| **University Event** | Public talks, seminars, workshops from university AI labs. | Stanford HAI talks, MIT CSAIL seminars (must be open to public) |

**Classification rubric:**
- If the event's **primary purpose is AI content/community** → `ai_conference` (regardless of whether the organizer is a company, startup, or nonprofit — GTC is NVIDIA's event but it's an AI conference)
- If the event is a **broad tech conference with AI tracks** → `ai_track`
- If the event is **informal, recurring, community-organized** → `community_event`
- No `vendor_event` type — the vendor vs. non-vendor distinction doesn't help users. Scale, location, and cost filters handle that.

**Hackathon** is a separate filterable label that can co-exist with any type. "GTC Hackathon" is tagged as both a hackathon and associated with the GTC conference.

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

This is the most underserved and most valuable tier. Also the hardest to curate.

**The curation problem (2026-03-27):**
Meetup and Eventbrite are littered with garbage: grifter webinars ("passive income with ChatGPT"), fake expert workshops ($3,000 bullshit from bullshitters), product/service promotion disguised as meetups, and cringe "AI thought leader" events from consultants using meetups for lead gen. Automated discovery from these platforms produces unacceptable noise. An LLM cannot reliably distinguish a legit builder meetup from a grifter's lead gen funnel — the difference is cultural, not textual.

**Decision: No automated local event discovery from aggregator platforms.** No Meetup API. No Eventbrite. Local events flow through human-curated channels only.

**Discovery sources (priority order):**
1. **Curated Luma calendars (primary for lab/company events)** — Luma is the dominant platform for AI community events. Track specific org calendars directly (iCal-subscribable, structured data). This sidesteps the grifter problem entirely — we track calendars we trust, not the whole platform. Known calendars: Anthropic (claudecommunity), DeepMind, W&B, OpenAI NYC, Bond AI SF/NYC, AI Tinkerers chapters. Periodically scan Luma for new quality calendars to add.
2. **Community submissions** — the flywheel. Discourse SSO + simple form + admin approval queue. Submitters are our community (builders), so they self-select quality. Becomes the primary growth driver over time.
3. **Grok X search (xAI API)** — per-metro sweeps to find events from real companies, startups, and builder communities. Must include anti-grifter instructions in prompt. All Grok-discovered local events go through admin approval, never auto-approved. Grok has proven effective at filtering for "genuine indie/hacker/startup organic" vibe when given cultural context in the prompt.
4. **AI lab event pages** — Anthropic (/events), DeepMind (/discover/events/), W&B (/site/resources/events/), FAR.AI (/events), Meta AI (/events/), Cohere (/events). Scrape on a schedule. See `resources/event_calendar_seed/lab_event_sources.md` for full inventory.
5. **Meta-aggregators** — GarysGuide (NYC indie tech), Cerebral Valley (hackathons), Bond AI Community (weekly SF/NYC/Seattle roundups), AI Safety Events Substack (weekly safety event roundups + AISafety.com/events-and-training directory).
6. **University AI lab talks** — add sources as we discover them through research. University AI bulletin boards, lab event pages. Include only events open to the public (not student/faculty-only).
7. **Anthropic Ambassador program events** — Anthropic funds community ambassadors to run local Claude meetups/hackathons with API credits. Community-organized but lab-backed. Auto-approve source.

**Per-metro Grok search:**
Start with 15 tech-weighted metros: SF/Bay Area, NYC, Seattle, Austin, LA, Boston, Chicago, Denver/Boulder, DC, Miami, Atlanta, Dallas/Fort Worth, London, Toronto, Berlin. Monthly sweeps per city.

**What qualifies as a local event:**
- Startup-organized AI events and meetups (e.g., OpenClaw meetup with the founder)
- Company-hosted open events (e.g., DigitalOcean AI day)
- Builder/hacker community meetups (people actually doing things)
- University lab public talks and seminars
- Local hackathons (standalone or offsite at conferences)

**What does NOT qualify:**
- Grifter webinars and "make money with AI" events
- Overpriced workshops from unqualified "experts"
- Product/service promotion disguised as meetups
- Consultants using meetups for lead generation
- Events where the organizer is posturing as an AI authority without real credentials

### Cross-Cutting

**Freshness / Re-confirmation:**
Events change dates, get canceled, change venues. Stale data is worse than missing data.
- Monthly scrape of event URL + Haiku extraction: "Is this still happening? Same dates? Same venue? Any changes?"
- Increase frequency as event approaches: monthly → weekly within 30 days
- Flag "updated" events so users see changes
- Detect cancellations

**Recurring Events:**
Many of the best community events are recurring (SF AI Engineers monthly, Flushing Tech bi-weekly, AI Tinkerers build nights, etc.). These need special handling:
- Store the **series** as a parent entity with recurrence pattern, not just individual instances
- Auto-generate upcoming instances based on recurrence rule
- **Freshness checks are critical** — recurring events pause, stop, change dates/venues, or skip months without notice. Check before each occurrence:
  - Is this series still active? (scrape organizer page / Meetup / Luma)
  - Has the next date/time/venue changed?
  - Any announcements about hiatus or cancellation?
- Display recurring events distinctly in the calendar (e.g., "Monthly" badge, series view)
- Users should be able to "follow" a recurring series and get notified of upcoming instances
- If a recurring event hasn't had a confirmed next date in 60+ days, mark series as `paused` and stop generating instances until re-confirmed

**Dedup:** Events will appear in multiple sources (Luma calendar + Grok X search + community submission for the same event). Match by URL + name + date range + location. Fuzzy match on name since the same event may be listed slightly differently across sources ("AI Tinkerers SF: April" vs "SF AI Tinkerers April Meetup"). Haiku can resolve ambiguous matches. Dedup runs on every pipeline ingestion, not just at seed time.

**Geocoding:** Convert addresses/city names to lat/lng for distance search. Nominatim (free, OSM-based) for MVP. Google Maps Geocoding API as upgrade if needed.

## API Research Results (2026-03-27)

### Eventbrite — Dead End
- Search endpoint (`/v3/events/search/`) **killed in February 2020**, never replaced
- Remaining API only retrieves events by specific ID or organization — no discovery
- API reportedly "deprecated and unsupported" as of 2025
- **Decision: Skip entirely**

### Meetup — Viable, Paywalled, Trash Content
- GraphQL API supports keyword + location (lat/lon + radius) search
- Rich event data (title, date, venue, description, cost, RSVP counts, group info)
- **Requires Meetup Pro subscription (~$30/mo)** just to register an OAuth app
- No free tier. Rate limits undocumented.
- **Content quality is abysmal** — dominated by grifter webinars, fake expert workshops, lead gen meetups, and "passive income with AI" garbage. Signal-to-noise ratio makes automated discovery impractical.
- **Decision: Skip. Not worth $30/mo for content we'd reject 90%+ of.**

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
    event_type: Mapped[str]  # ai_conference, ai_track, community_event, university_event
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
    format: Mapped[str]  # in_person, online, hybrid
    is_dates_tbd: Mapped[bool]  # true for annual events with unannounced dates
    tbd_usual_month: Mapped[str | None]  # "March", "November-December" — for TBD annual events
    tags: Mapped[list[str]]  # reuse existing tag taxonomy
    normalized_description: Mapped[str | None]  # our rewritten, consistently formatted description
    source: Mapped[str]  # where we found it
    # Recurring event support
    is_recurring: Mapped[bool]  # true for recurring series (monthly meetups, bi-weekly hacks, etc.)
    recurrence_rule: Mapped[str | None]  # human-readable: "First Wednesday monthly", "Bi-weekly Fridays"
    series_id: Mapped[uuid.UUID | None]  # links all instances of a recurring event
    next_occurrence: Mapped[date | None]  # next scheduled date (for recurring; auto-updated)
    recurrence_status: Mapped[str | None]  # active, paused, ended (tracked via freshness checks)
    host_name: Mapped[str | None]  # organizer/host name (for trust tracking)
    host_id: Mapped[uuid.UUID | None]  # FK to event_hosts table
    submitted_by: Mapped[int | None]  # discourse user id, if community-submitted
    status: Mapped[str]  # active, canceled, pending_approval, rejected
    approval_notes: Mapped[str | None]  # admin notes on approve/reject (builds training data)
    approved_by: Mapped[int | None]  # admin discourse user id
    approved_at: Mapped[datetime | None]
    ai_track_notes: Mapped[str | None]  # for AI Track type: what AI content is featured
    last_confirmed: Mapped[datetime | None]  # last freshness check
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

class EventHost(Base):
    __tablename__ = "event_hosts"
    id: Mapped[uuid.UUID]
    name: Mapped[str]  # organizer/host name
    url: Mapped[str | None]  # host website
    trust_level: Mapped[str]  # auto_approve, requires_review, blacklisted
    blacklist_reason: Mapped[str | None]
    approval_count: Mapped[int]  # how many events approved from this host
    rejection_count: Mapped[int]  # how many rejected
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

## Curation & Approval System

### Trust Tiers

**Auto-approve (high trust):**
- Major AI conferences from known sources
- Events from known companies and labs (Anthropic, OpenAI, Google, NVIDIA, etc.)
- Events from known developer communities (MLOps Community, Latent Space, Papers We Love, etc.)
- University lab public events
- Events from hosts previously approved by admin (with guardrails — see below)

**Admin-approve (everything else):**
- Community submissions
- Grok-discovered local events
- Anything from an unknown host/organizer
- Events from Lu.ma or other sources

**No allow-list needed for company/lab events.** Instead, analyze: Is this a real tech company/startup (not a consultancy)? Does this event pass the grifter rubric (score pass/fail)? This is a Sonnet judgment call, not a lookup.

### Admin Approval Queue

1. Admin sees pending events with source info and any auto-analysis
2. **Approve** — event goes live. Optional: add notes explaining why (builds dataset for future automation)
3. **Reject** — event stays hidden. Optional: add notes explaining why
4. **Blacklist host** — admin can blacklist the host/organizer on reject. Future events from this host are auto-rejected.
5. All approval/rejection decisions with notes are stored for training future curation automation

### Host Trust (learned over time)

When an event is approved, the host/organizer earns trust. Future events from the same host can be auto-approved **with guardrails:**
- Host name/org must match
- Event must still pass the basic grifter rubric (prevents a legitimate host from later hosting a grifter event or pivoting to lead gen)
- If a previously trusted host submits something that fails the rubric, it goes to admin queue instead of auto-approving

**Concern addressed:** A "generic" host gets approved for one good event, then hosts something shitty later. The rubric check on every event (even from trusted hosts) prevents this. Trust speeds up approval but doesn't bypass quality checks.

### Community Submission Flow

1. User clicks "Submit Event" on /events page
2. Must be logged in (Discourse SSO — same as news app)
3. Simple form: name, dates, location, URL, type, cost, description, eligibility
4. Submits → stored with `status=pending_approval`
5. Admin sees queue with submission details + submitter info
6. Admin approves/rejects/edits with optional notes
7. Approved events go live; Haiku auto-fills missing fields (geocoding, tags)

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
