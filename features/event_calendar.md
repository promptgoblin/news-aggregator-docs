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
8. **Conference circuit organizers** — Some orgs run global event circuits from a single source page. Scrape periodically for new events across cities:
   - AI Engineer (ai.engineer) — World's Fair, Europe, NYC, Code Summit + regional AIEi partner events
   - AI Tinkerers (aitinkerers.org/ai-meetups) — 205 city chapters, monthly meetups
   - AI Furnace — NYC, London, Boston, Paris, Dubai
   - MLOps Community — 10+ city chapters
   - AI Salon — 37 cities

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

## Production Pipeline Architecture

The event calendar pipeline runs as a separate orchestrator in the existing agent container, alongside the news pipeline. Uses Agent SDK (same auth pattern as news).

### Pipeline Overview

```
CRON SCHEDULE:
  Daily (6am UTC):     Luma calendar sync + conference circuit scrape
  Weekly (Monday 8am): Freshness re-confirmation for upcoming events
  Monthly (1st, 8am):  Grok X search sweeps per metro + new source discovery

SUBMISSION FLOW (on-demand):
  User submits → pending_approval → admin approves → auto-enrich if has_event_page

PIPELINE STAGES:
  1. INGEST     — pull events from sources (Luma, circuits, lab pages)
  2. DEDUP      — match against existing events (URL + name + date fuzzy match)
  3. CLASSIFY   — determine event_type, is_hackathon, format, tags (Haiku)
  4. ENRICH     — scrape event page for cost, description, speakers, etc. (trafilatura → scrape.do → Haiku)
  5. GEOCODE    — Nominatim lat/lng from location
  6. APPROVE    — auto-approve from trusted sources, queue others for admin
  7. FRESHEN    — re-check existing events for date/venue/cost/status changes
```

### Stage 1: INGEST

Three source types, each with its own ingestion method:

**1a. Luma Calendar Sync (daily)**
- Subscribe to curated Luma calendar iCal feeds (see `resources/event_calendar_seed/luma_calendar_directory.md` for full list)
- Priority calendars (subscribe first): Anthropic/claudecommunity, DeepMind, W&B, OpenAI NYC, Cerebral Valley, LangChain, Bond AI SF/NYC, GenAI Collective, AI Furnace, AGI Builders, AI Builders Europe, AI Salon
- For each calendar: fetch iCal feed → parse VEVENT entries → extract name, dates, location, URL, description
- Luma iCal feeds are structured and reliable — minimal LLM needed at this stage
- New calendars added periodically via admin or quarterly discovery sweep

**1b. Conference Circuit Scrape (daily)**
- Scrape directory/event pages from orgs that run multi-city event series:
  - ai.engineer (World's Fair, Europe, NYC, Code Summit, AIEi partner events)
  - aitinkerers.org/ai-meetups (205 city chapters)
  - AI Furnace (NYC, London, Boston, Paris, Dubai)
  - MLOps Community (10+ city chapters)
  - AI Salon (37 cities)
- For each: fetch page → extract event listings → parse into candidate events
- Haiku extracts structured data from HTML when needed

**1c. Lab Event Page Scrape (daily)**
- Scrape event pages from AI labs/companies:
  - anthropic.com/events
  - deepmind.google/discover/events/
  - wandb.ai/site/resources/events/
  - far.ai/events
  - ai.meta.com/events/
  - cohere.com/events
  - Mistral (X + dedicated microsites)
- Extraction chain: direct fetch → trafilatura → readability → scrape.do (same as news pipeline)

**1d. Grok X Search Sweeps (monthly)**
- Per-metro search using xAI Responses API + x_search
- 15 priority metros: SF, NYC, Seattle, Austin, LA, Boston, Chicago, Denver, DC, Miami, Atlanta, Dallas, London, Toronto, Berlin
- Anti-grifter prompt with cultural context (proven effective in manual seeding)
- All Grok-discovered events go to admin queue (never auto-approved)

**1e. Submission Enrichment (on-demand)**
- When admin approves a "has_event_page" submission: trigger enrichment pipeline on the URL
- Same extraction chain as scraper script: fetch page → find pricing page → Haiku extracts structured details
- Updates the CalendarEvent record with extracted data

### Stage 2: DEDUP

Before inserting any new event, check for duplicates:
1. **Exact URL match** — same URL = same event (update, don't create)
2. **Name + date fuzzy match** — Haiku compares candidate vs existing events within ±7 days: "Are these the same event?" YES/NO
3. **On match**: update existing record with any new/better data (e.g., cost was TBD, now known)
4. **On no match**: proceed to classify + enrich

### Stage 3: CLASSIFY (Haiku)

For each new event, Haiku determines:
- `event_type`: ai_conference | ai_track | community_event | university_event
- `is_hackathon`: true/false
- `format`: in_person | online | hybrid
- `tags`: from existing tag taxonomy
- `eligibility`: who can attend

**Classification rubric** (in prompt):
- Primary purpose is AI → ai_conference
- Broad tech conference with AI tracks → ai_track (user-facing label: "Tech Conference")
- Informal, recurring, community-organized → community_event
- Hackathon label cross-cuts all types

### Stage 4: ENRICH

Scrape the event's URL to fill in details:
1. Fetch main page (trafilatura → readability → scrape.do chain)
2. Haiku: find pricing/registration page URL from content
3. If found, fetch pricing page too
4. Haiku: extract structured details from combined content:
   - cost (pricing tiers)
   - description (2-3 sentences)
   - normalized_description (our consistent format)
   - eligibility
   - estimated_attendance
   - host info
   - key speakers
   - sold_out / waitlist status
5. Only overwrite fields that have better data than what exists

### Stage 5: GEOCODE

For events with location but no lat/lng:
- Build query from location_address + location_city + location_country
- Call Nominatim (1 req/sec rate limit, User-Agent: GoblinNews/1.0)
- Store lat/lng for distance search
- Skip online events

### Stage 6: APPROVE

**Auto-approve sources** (no admin review needed):
- AI Tinkerers (all chapters) — format enforces quality
- Anthropic Ambassador events
- Cerebral Valley
- Events from known AI labs (Anthropic, DeepMind, OpenAI, etc.)
- Events from known conferences (NeurIPS, ICML, GTC, etc.)
- Any host with trust_level = "auto_approve" in EventHost table

**Admin queue** (everything else):
- Set status = "pending_approval"
- Post notification to Discourse event-submissions category (30)
- Admin reviews at /events/admin, approves/rejects with notes
- Approved → status = "active", triggers enrichment if needed
- Rejected → optionally blacklist host

### Stage 7: FRESHEN

Re-check existing events for changes:
- **Schedule**: weekly for events within 60 days, monthly for events further out
- **Within 7 days of event**: check daily
- Scrape event URL → Haiku compares current content vs stored data
- Detect: date changes, venue changes, cancellations, sold out status, price changes
- Update CalendarEvent record + set last_confirmed timestamp
- If recurring event hasn't posted next date in 60+ days → mark recurrence_status = "paused"
- Log all changes for admin review

### Pipeline Agent Structure (Agent SDK)

```python
# agent/event_orchestrator.py — main entry point for event pipeline

# Runs inside the existing agent container
# Separate from news orchestrator (agent/orchestrator.py)
# Triggered by cron on its own schedule

AGENTS:
  event_orchestrator    [sonnet] — coordinates pipeline, makes judgment calls
    ├── luma_ingestor   [haiku]  — parses iCal feeds, extracts events
    ├── circuit_scraper [haiku]  — scrapes conference circuit pages
    ├── lab_scraper     [haiku]  — scrapes lab event pages
    ├── grok_discoverer [grok]   — X search for local events (monthly)
    ├── dedup_checker   [haiku]  — fuzzy match against existing events
    ├── classifier      [haiku]  — event type, tags, format
    ├── enricher        [haiku]  — scrape + extract structured details
    ├── geocoder        [none]   — Nominatim API calls, no LLM needed
    └── freshener       [haiku]  — re-check existing events for changes

MCP TOOLS (new, event-specific):
  - get_calendar_events(filters) — query existing events for dedup
  - upsert_calendar_event(data) — create or update event
  - get_event_hosts(filters) — check host trust level
  - update_event_host(id, trust_level) — update host trust
  - mark_event_confirmed(id) — update last_confirmed timestamp
  - fetch_and_extract(url) — trafilatura/scrape.do extraction chain
  - geocode(location) — Nominatim lookup
```

### Cron Configuration

```
# Event pipeline cron (add to deploy/cron/pipeline-cron)
# Daily: Luma + circuit + lab sync
0 6 * * * cd /app && PYTHONPATH=/app/src python -m agent.event_orchestrator --daily
# Weekly: freshness checks (Monday 8am UTC)
0 8 * * 1 cd /app && PYTHONPATH=/app/src python -m agent.event_orchestrator --freshen
# Monthly: Grok sweeps + source discovery (1st of month, 8am UTC)
0 8 1 * * cd /app && PYTHONPATH=/app/src python -m agent.event_orchestrator --discover
```

### Cost Estimates

| Stage | Model | Frequency | Est. Cost/Run |
|-------|-------|-----------|---------------|
| Luma ingest | Haiku | Daily | ~$0.01 (parsing, minimal LLM) |
| Circuit scrape | Haiku | Daily | ~$0.05 (HTML extraction) |
| Lab scrape | Haiku | Daily | ~$0.05 (HTML extraction) |
| Dedup | Haiku | Per event | ~$0.001 per check |
| Classify | Haiku | Per new event | ~$0.001 per event |
| Enrich | Haiku | Per new event | ~$0.01 per event (2 pages + extraction) |
| Freshen | Haiku | Weekly | ~$0.10 (re-check ~60 events) |
| Grok discover | Grok | Monthly | ~$0.50 (15 metro searches) |
| **Total daily** | | | **~$0.15** |
| **Total monthly** | | | **~$5-8** |

### Luma Calendar Feed URLs

Priority calendars to subscribe first (from luma_calendar_directory.md):

```
# AI Labs & Companies
https://lu.ma/claudecommunity        # Anthropic
https://lu.ma/deepmind               # Google DeepMind
https://lu.ma/wandb                  # Weights & Biases
https://lu.ma/openainyc              # OpenAI NYC
https://lu.ma/langchain              # LangChain
https://lu.ma/cohere                 # Cohere (calendar URL in directory)

# Top Communities
https://lu.ma/cerebralvalley          # Cerebral Valley (SF)
https://lu.ma/genai-sf               # Bond AI SF
https://lu.ma/genai-ny               # Bond AI NYC
https://lu.ma/genai-collective       # GenAI Collective (70K+)
https://lu.ma/ai-furnace             # AI Furnace NYC
https://lu.ma/ai-furnace-uk          # AI Furnace London
https://lu.ma/ai-furnace-boston       # AI Furnace Boston
https://lu.ma/agibuilders            # AGI Builders SF
https://lu.ma/ai-builders            # AI Builders Europe
https://lu.ma/aisalon                # AI Salon (37 cities)

# Safety
https://lu.ma/AISafetyBerlin         # AI Safety Berlin
https://lu.ma/paperclip-club         # Paperclip Club
https://lu.ma/AISecurityCollective   # AI Security Collective

# City-specific (add more over time)
https://lu.ma/artificialintelligencenyc  # AI NYC
https://lu.ma/sf-mlops-community     # SF MLOps
https://lu.ma/nyc.mlops              # NYC MLOps
https://lu.ma/london-mlops           # London MLOps
https://lu.ma/parisai                # Paris AI
https://lu.ma/aimadlab               # Norway AI Mad Lab
https://lu.ma/DeepStation            # Miami
https://lu.ma/infer                  # Vancouver (Latent Space)
```

To get iCal feeds from Luma: append `.ics` to calendar URLs or check for iCal subscribe links on each calendar page. Research needed during build to confirm exact iCal endpoint format.

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

- [x] Research: Meetup API access → paywalled ($30/mo), skip (trash content)
- [x] Research: Eventbrite API access → dead end, skip
- [x] Research: Lu.ma API access → organizer-only, subscribe to curated calendars instead
- [x] Research: AI lab event pages → 15 orgs inventoried (lab_event_sources.md)
- [x] Research: Luma calendars → 80+ cataloged (luma_calendar_directory.md)
- [x] Decide: PostGIS vs haversine SQL → haversine for MVP (deployed)
- [x] Decide: geocoding provider → Nominatim (deployed)
- [x] Run initial Grok seeding → 64 events seeded across all categories
- [x] Design admin approval queue UI → /events/admin (deployed)
- [x] Design submission form → /events/submit two-path (deployed)
- [x] Seed list of major AI conferences for 2026-2027
- [x] Verify seed events → sub-agents verified all events, corrections applied
- [x] Build event scraper script (scrape_event_details.py)
- [ ] **BUILD: Production pipeline** (Agent SDK, see architecture above)
- [ ] Confirm Luma iCal feed format (research during build)
- [ ] Add --all mode to scraper for comprehensive freshness checks
- [ ] Hybrid search (keyword + semantic) — separate feature doc
- [ ] Cost normalization (structured schema)
