# Feature: AI Event Calendar

---
type: feature
status: planning
complexity: C3
tags: [calendar, events, discovery, search]
depends_on: [production_deployment]
required_by: []
---

## User Intent

### Goal
A filterable calendar of AI conferences, meetups, and local events. Searchable by location/distance, filterable by type (conference, meetup, workshop, hackathon), and browsable by month. Easier to curate than news since most events are worth including — less discretion, more aggregation.

### Success Criteria
- Calendar view with AI events (conferences, meetups, workshops, hackathons)
- Filter by event type, location (city/radius), date range, topic/tags
- Search by distance from user's location ("events within 50 miles")
- Event detail: name, date(s), location, description, link, type, cost (free/paid)
- Comprehensive coverage of major AI conferences + community meetups
- Easy curation: most events pass the bar, pipeline focuses on finding + labeling

### User Flow
1. User visits news.promptgoblins.ai/calendar
2. Sees calendar/list view of upcoming AI events
3. Filters by type (conferences, meetups), location, date range
4. Enters location → sees events within chosen radius
5. Clicks event → sees details + link to register
6. Can subscribe to filtered calendar via iCal/RSS

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## Implementation

### Approach
New data model for calendar events (separate from news events). Discovery pipeline scrapes known event aggregator sites, Meetup API, Eventbrite API, and curated conference lists. Lower LLM cost than news since events mostly just need labeling, not distillation. Geo-search powered by PostGIS or simple lat/lng distance queries.

### Key Components
- **`calendar_events` table**: Name, dates, location (address + lat/lng), type, description, url, cost, tags
- **Discovery sources**: Eventbrite API, Meetup API, conference aggregator sites, manual curation
- **Geo-search**: Filter by distance from a point (user enters city or allows location)
- **Calendar views**: Month view, list view, map view (stretch goal)
- **iCal export**: `/calendar.ics` with filters

### Data Model
```python
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[uuid.UUID]
    name: Mapped[str]
    description: Mapped[str | None]
    event_type: Mapped[str]  # conference, meetup, workshop, hackathon, summit
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    location_name: Mapped[str]  # "Moscone Center, San Francisco"
    location_city: Mapped[str]
    location_country: Mapped[str]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    url: Mapped[str]
    cost: Mapped[str | None]  # "Free", "$499", "$99-$299"
    is_virtual: Mapped[bool]
    tags: Mapped[list[str]]  # reuse existing tag taxonomy
    source: Mapped[str]  # where we found it
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### Discovery Pipeline
Unlike news, event discovery is simpler:
1. **Seed list**: Major AI conferences (NeurIPS, ICML, CVPR, Google I/O, WWDC AI, etc.)
2. **Meetup/Eventbrite API**: Search for AI/ML meetups by city
3. **Community submissions**: Users can submit events (moderated)
4. **LLM labeling**: Classify event type + relevant tags (Haiku — cheap, fast)
5. **Geocoding**: Convert addresses to lat/lng for distance search

### Distance Search
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
HAVING distance_km <= :radius
ORDER BY start_date
```

## Edge Cases & Considerations

### Handled
- **Virtual events**: `is_virtual=true`, no location filter needed
- **Multi-day events**: `start_date` + `end_date`, show on all days
- **Canceled events**: Soft delete with "canceled" status
- **Duplicate events**: Dedupe by URL + name + date

### Limitations
- Meetup/Eventbrite APIs may have rate limits or cost
- Geocoding needs an API (Google Maps, OpenStreetMap Nominatim)
- Community submissions need moderation workflow

## Definition of Done

### Acceptance Criteria
- [ ] `/calendar` page shows upcoming AI events
- [ ] Filter by type, location radius, date range works
- [ ] Event detail page with register link
- [ ] iCal export with filters
- [ ] At least 50 events seeded (major conferences + top meetups)

## Outstanding
- [ ] Research: Meetup API access (free tier?)
- [ ] Research: Eventbrite API access
- [ ] Decide: PostGIS vs haversine SQL for distance
- [ ] Decide: community submission flow (form vs email vs forum post)
- [ ] Seed list of major AI conferences for 2026
