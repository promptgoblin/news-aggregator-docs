# Feature: AI Event Calendar

---
type: feature
status: archived
complexity: C3
tags: [calendar, events, discovery, search, sourcing, archived]
depends_on: [production_deployment]
required_by: []
archived_on: 2026-04-07
archived_by: mike
last_working_sha: 0ce897beb59b7919d6d2cafd27bd575b7dd14b30
---

> **🗄️ ARCHIVED 2026-04-07.** This feature shipped to production in March 2026 and was killed
> in April 2026. The pipeline, API, models, frontend, and seed scripts have been deleted from
> the codebase. The DB tables (`calendar_events`, `event_hosts`) have been dropped via Alembic
> migration. **All planning content from the original feature doc is preserved verbatim under
> [Original Planning (Historical)](#original-planning-historical) below.** The new top section
> documents what we actually built, why we killed it, and what to do if reviving.
>
> **If reviving this feature**, start with [How to Revive This](#how-to-revive-this), not the
> original planning section. We learned a lot during build that the planning section doesn't
> reflect.

## Why This Was Killed

**Headline:** The Sonnet quota burn from event enrichment was competing with the news pipeline
for the same finite resource (Mike's Claude Code Max subscription), and the feature didn't
solve a recurring user problem the way news aggregation does.

**Decision date:** 2026-04-07
**Decision maker:** Mike (sole maintainer)

### The Sonnet Quota Incident

The event calendar agent pipeline ran inside the existing `ai-signal-agent` container and
authenticated through the Claude Code subscription via `claude_agent_sdk` (same pattern as the
news pipeline — we have no separate Anthropic API key). Within ~2 days of launching the daily
Luma sync, freshness checks, and Sonnet enrichment, the weekly Sonnet quota was exhausted on
the 5x Max plan. Mike upgraded to the 20x Max plan and was at ~50% of the weekly Sonnet limit
mid-week, with the news pipeline being the only OTHER consumer of that quota.

This wasn't measured in dollars (Anthropic API equivalent cost was estimated at ~$48/month),
it was measured in **subscription quota** — and since the news pipeline shared that quota,
the event calendar was actively starving the product that was actually working.

**The lesson:** any agent SDK pipeline that runs inside Claude Code's subscription envelope
must respect the shared quota budget. Daily Sonnet enrichment of 50+ items is too aggressive
for a single Max plan to support alongside another active pipeline. If reviving, either:
1. Use a separate Anthropic API key (not the subscription), OR
2. Run heavy enrichment monthly, not daily, AND only on conferences (low volume), OR
3. Use Haiku for enrichment and accept lower data quality

### The Demand Question

> "I will do this like 1-2x a year." — Mike, 2026-04-07

News aggregation solves a daily problem: keeping up with AI announcements is genuinely
time-consuming and Mike does it every day. The event calendar tried to solve a problem Mike
faces twice a year. Querying Grok directly ("what AI conferences are coming up?") is good
enough for that frequency. There was no compounding value, no flywheel — and the community
submission flywheel never spun up because there were no users yet.

**General pattern:** If you can't articulate the daily-or-weekly use case for a feature,
don't build automation for it. Manual one-off queries are fine for low-frequency needs.

### The Luma Redundancy Problem

90%+ of the events the daily Luma sync ingested were already on Luma's own browsable directory
(`lu.ma/discover`, `lu.ma/ai`, individual calendar pages). We were spending Sonnet tokens to
mirror data that Luma already serves better. The differentiated value was supposed to be
either (a) the conference layer that Luma doesn't index well, OR (b) the long-tail community
events. Conferences worked — but were also a small fraction of the data. Community events
were mostly Luma redundant.

### The Conferences-Only Pivot (and Re-Kill)

On 2026-04-06, we tried to scope the feature down to conferences-only (delete community/uni
events, keep AI conferences + tech conferences with AI tracks, focus pipeline on Grok
discovery + monthly freshen, drop daily Luma sync entirely). The DB was wiped from 194 events
to 55 conferences, the pipeline orchestrator was rewritten, the frontend was simplified.

**That refactor was completed but never deployed**, because Mike concluded the next day that
even the conferences-only version didn't justify the maintenance burden vs. just asking Grok
directly twice a year. The conferences-only refactor IS preserved in the archive section
below as a useful reference if reviving — it represents a much lower-cost shape of the feature.

## What Actually Shipped

**Backend (~2500 LOC):**
- `agent/event_orchestrator.py` (1792 lines) — full pipeline with three modes (`--daily`,
  `--freshen`, `--discover`), Luma iCal sync, conference circuit scraping, lab event page
  scraping, Grok per-metro discovery, dedup, classification, enrichment, geocoding, host
  trust, host profiling.
- `agent/event_runbooks.py` — 7 system prompts (CLASSIFIER, PAGE_EXTRACTOR, DEDUP_CHECKER,
  FRESHENER, PRICING_FINDER, GROK_DISCOVERY, HOST_PROFILER).
- `agent/event_tools.py` (553 lines) — MCP tool server for the agent (was built but never
  wired up; the orchestrator went with direct function calls instead).
- `src/ai_signal/api/calendar.py` (711 lines) — full FastAPI router: list with multi-filter
  + haversine distance + multi-region, detail by slug, iCal feed export, geocode endpoint,
  authenticated submission endpoint, admin pending/approve/reject/edit/delete endpoints,
  Discourse notification on submission.
- `src/ai_signal/models/calendar_event.py` (141 lines) — `CalendarEvent` (40+ fields) and
  `EventHost` (trust ladder, approval/rejection counters) SQLAlchemy models.
- Alembic migrations b13/b14/b15 created the tables and added `host_url` + recurring fields.

**Frontend (~2000 LOC):**
- `app/events/page.tsx` — list view with sidebar filters
- `app/events/[slug]/page.tsx` — event detail page
- `app/events/submit/page.tsx` — two-path submission form (URL+name+note OR full manual entry)
- `app/events/admin/page.tsx` — admin queue with approve/reject/edit/delete
- `components/CalendarEventList.tsx`, `CalendarEventRow.tsx`, `CalendarEventModal.tsx`,
  `CalendarEventFilters.tsx`, `CalendarEventSidebar.tsx`
- `lib/calendarUtils.ts` — country flag emoji map + COUNTRY_LIST
- `lib/api.ts` — `getCalendarEvents`, `getCalendarEvent`, `submitCalendarEvent`,
  `geocodeLocation`, admin endpoints
- `lib/types.ts` — `CalendarEventSummary`, `CalendarEventDetail`, `PendingCalendarEvent`
- Nav: News | Events | About tab in `Header.tsx`

**Data:**
- 64 events seeded initially across major conferences, AI conferences, AI tracks at tech
  conferences, regional/global community events
- 62 of 64 geocoded with lat/lng via Nominatim
- ~12 events enriched with real costs/descriptions via the Sonnet scraper
- After community/university/hackathon wipe on 2026-04-06: 55 conferences (40 AI + 15 tech)
- Final state at table drop: 55 conferences, 40+ event host profiles

**Discourse integration:**
- `events` bot user created on the forum
- API key `DISCOURSE_API_KEY_EVENTS` stored in `.env`, with `topics:write` + `chat:create_message` scopes
- `event-submissions` Discourse category (id 30) — destination for new-submission notifications
- `discourse_api_username_events` and `discourse_events_category_id` settings in
  `src/ai_signal/config.py`

**Cron schedule (in `deploy/cron/pipeline-cron`):**
- Daily 11:00 UTC: `--daily` (Luma + circuits + labs + process new)
- Weekly Mon 11:30 UTC: `--freshen` (re-confirm upcoming events)
- Monthly 1st 12:00 UTC: `--discover` (Grok per-metro sweeps)

## What Worked (Patterns Worth Preserving)

These are the parts that, if reviving, you should NOT have to redesign. Use them as-is.

### 1. Two-stage enrichment: Haiku finds the pricing page, then Sonnet reads both

Conference main pages almost never list prices. Pricing lives on `/tickets`, `/register`,
`/pricing`, etc. The fix is a cheap Haiku pre-pass to discover the pricing page URL, then
fetch both pages and feed combined content to Sonnet for extraction.

```python
# Step 1: Cheap Haiku pre-pass — find the pricing page URL
pricing_prompt = (
    f"Event page URL: {event_url}\n\n"
    f"Page content:\n{content[:3000]}\n\n"
    + EVENT_PRICING_FINDER  # see prompt below
)
pricing_url_result = await _call_agent_sdk(
    pricing_prompt, model="haiku", budget=0.05, stage="pricing_find"
)
pricing_url = pricing_url_result.strip().strip('"').strip("'")

# Handle relative URLs returned by the LLM
if pricing_url and pricing_url.startswith("/"):
    pricing_url = urljoin(event_url, pricing_url)

if pricing_url and pricing_url.upper() != "NONE" and pricing_url.startswith("http"):
    pricing_page, _ = await _fetch_page(pricing_url)
    if pricing_page:
        # Concatenate with a separator the LLM can recognize
        pricing_content = (
            f"\n\n--- PRICING/REGISTRATION PAGE ({pricing_url}) ---\n\n"
            + pricing_page[:3000]
        )

# Step 2: Sonnet extracts all fields from main page + pricing page
full_content = content[:MAX_CONTENT_CHARS]
if pricing_content:
    full_content = content[:MAX_CONTENT_CHARS - len(pricing_content)] + pricing_content
prompt = EVENT_PAGE_EXTRACTOR.format(
    event_name=event_name, event_url=event_url, content=full_content
)
result = await _call_agent_sdk(
    prompt, model="sonnet", budget=0.10, stage="enrich"
)
```

Without this two-stage approach, ~70% of conference enrichments returned `cost: TBD`. With
it, ~85% returned an actual price tier or "Free".

### 2. The fuzzy dedup ladder

Cost-bounded dedup that only escalates to LLM when necessary:

```python
async def _fuzzy_name_date_match(name: str, start_date: date) -> CalendarEvent | None:
    """URL match → exact name match → word-overlap heuristic → LLM tiebreak."""
    window_start = start_date - timedelta(days=3)  # for community events; widen for conferences
    window_end = start_date + timedelta(days=3)

    async with async_session() as db:
        result = await db.execute(
            select(CalendarEvent)
            .where(CalendarEvent.start_date >= window_start)
            .where(CalendarEvent.start_date <= window_end)
            .where(CalendarEvent.status.in_(["active", "pending"]))
        )
        candidates = result.scalars().all()

    if not candidates:
        return None

    # Stage 1: exact match on lowercased+stripped name
    name_lower = name.lower().strip()
    for c in candidates:
        if c.name.lower().strip() == name_lower:
            return c

    # Stage 2: too many candidates? skip LLM, use word-overlap heuristic
    if len(candidates) > 10:
        for c in candidates:
            if _name_overlap(name, c.name):
                return c
        return None

    # Stage 3: ≤10 candidates, use Haiku for fuzzy matching
    candidate_list = "\n".join(
        f"  {i+1}. \"{c.name}\" ({c.start_date})" for i, c in enumerate(candidates)
    )
    prompt = (
        f"Is this new event a duplicate of any existing event?\n\n"
        f"New event: \"{name}\" ({start_date})\n\n"
        f"Existing events:\n{candidate_list}\n\n"
        f"Return ONLY the number (1-{len(candidates)}) of the matching event, "
        f"or NONE if no match. No explanation."
    )
    # ... call Haiku, parse number or NONE


def _name_overlap(name1: str, name2: str) -> bool:
    """Quick heuristic: shared significant words ≥ 60% of smaller name."""
    words1 = set(re.findall(r"\w{3,}", name1.lower()))
    words2 = set(re.findall(r"\w{3,}", name2.lower()))
    if not words1 or not words2:
        return False
    overlap = words1 & words2
    return len(overlap) >= min(len(words1), len(words2)) * 0.6
```

### 3. Postgres advisory lock for pipeline overlap prevention

```python
# Distinct lock ID per pipeline. News uses 42, events used 43.
ADVISORY_LOCK_ID = 43

async def run(args):
    from sqlalchemy import text
    async with async_session() as db:
        acquired = (await db.execute(
            text(f"SELECT pg_try_advisory_lock({ADVISORY_LOCK_ID})")
        )).scalar()
        if not acquired:
            logger.warning("Pipeline already running, skipping")
            return
    try:
        await _run_pipeline(args)
    finally:
        async with async_session() as db:
            await db.execute(text(f"SELECT pg_advisory_unlock({ADVISORY_LOCK_ID})"))
```

This prevents two cron-triggered runs from clobbering each other if a long run goes past
the next scheduled trigger.

### 4. Haversine SQL distance filter with online-event passthrough

```python
# In the list endpoint, when lat/lng/radius_mi are provided:
radius_km = radius_mi * 1.60934
distance_expr = (
    6371 * func.acos(
        func.cos(func.radians(literal_column(str(lat))))
        * func.cos(func.radians(CalendarEvent.latitude))
        * func.cos(
            func.radians(CalendarEvent.longitude)
            - func.radians(literal_column(str(lng)))
        )
        + func.sin(func.radians(literal_column(str(lat))))
        * func.sin(func.radians(CalendarEvent.latitude))
    )
)
# CRITICAL: Online events should ALWAYS show up regardless of distance
query = query.where(
    (CalendarEvent.format == "online")
    | (
        CalendarEvent.latitude.isnot(None)
        & CalendarEvent.longitude.isnot(None)
        & (distance_expr <= radius_km)
    )
)
```

PostGIS would be cleaner but haversine in raw SQL is sufficient up to ~10K events and
avoids the PostGIS dependency. Online-event passthrough is a usability requirement that's
easy to forget — without it, the distance filter hides every virtual event.

### 5. Region bucketing instead of country dropdowns

After 30 conferences across 12+ countries, the country dropdown is unusable. The fix:

```python
REGION_COUNTRIES = {
    "north_america": {"United States", "Canada", "Mexico"},
    "europe": {
        "United Kingdom", "Germany", "France", "Netherlands", "Spain", "Italy",
        "Portugal", "Switzerland", "Austria", "Belgium", "Sweden", "Norway",
        "Denmark", "Finland", "Ireland", "Poland", "Czech Republic", "Hungary",
        "Greece", "Turkey", "Estonia", "Latvia", "Lithuania", "Croatia",
        "Serbia", "Bulgaria", "Slovakia", "Slovenia", "Luxembourg", "Iceland",
        "Romania", "Malta",
    },
    "asia": {
        "Japan", "South Korea", "China", "India", "Singapore", "Indonesia",
        "Thailand", "Vietnam", "Philippines", "Malaysia", "Taiwan", "Hong Kong",
        "Pakistan", "Bangladesh", "Sri Lanka", "Nepal",
    },
}

# Filter logic — handle "other" by inverting the union of known regions:
all_known = set().union(*REGION_COUNTRIES.values())
if "other" in regions:
    query = query.where(
        CalendarEvent.location_country.is_(None)
        | ~CalendarEvent.location_country.in_(all_known)
    )
```

Always normalize country names BEFORE storing: `US → United States`, `UK → United Kingdom`.
Otherwise the bucket lookup misses.

### 6. Two-pass host trust ladder

```python
def should_auto_approve(event_data: dict, source_name: str) -> bool:
    """Source-based trust check (cheap, no DB hit)."""
    source = event_data.get("source", "")
    # Subscribing to a curated calendar IS the trust decision
    if source.startswith("luma:"):
        return True
    for name in AUTO_APPROVE_SOURCES:  # set of trusted org names
        if name.lower() in source_name.lower():
            return True
    return False

async def _check_host_trust(host_name: str) -> bool:
    """DB-based trust check (escalation step if source check failed)."""
    if not host_name:
        return False
    async with async_session() as db:
        result = await db.execute(
            select(EventHost.trust_level)
            .where(EventHost.name.ilike(f"%{host_name}%"))
            .limit(1)
        )
        return result.scalar() == "auto_approve"

# Usage:
auto_approve = should_auto_approve(raw, source_name)
if not auto_approve:
    host_name = enrichment.get("host_name") or source_name
    auto_approve = await _check_host_trust(host_name)
status = "active" if auto_approve else "pending"
```

The two-pass design avoids hitting the DB for known-trusted sources while still letting
admin-curated host trust override the default of "send to admin queue".

### 7. JSON-LD for discovery, Sonnet for data

The Luma calendar pages embed `application/ld+json` blocks listing events. **Use them ONLY
to discover candidate event URLs.** Do NOT trust the embedded data — it's frequently stale,
partial, or lacks critical fields like cost/eligibility. Pattern:

```python
def _extract_jsonld_events(html: str) -> list[dict]:
    """Pull event URLs from JSON-LD blocks. Discovery only."""
    candidates = []
    for match in re.finditer(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        # Handle @graph wrapper, single event, or array
        items = data.get("@graph", []) if isinstance(data, dict) else data
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if item.get("@type") == "Event" and item.get("url"):
                candidates.append({
                    "url": item["url"],
                    "name": item.get("name"),  # use as fallback only
                })
    return candidates

# Then for each candidate URL: _enrich_event_from_url() → Sonnet reads the actual page.
```

### 8. The "Free?" vs "Free" vs "TBD" distinction

When extracting cost, three states have different meaning:

| Value   | Meaning                                                    |
|---------|------------------------------------------------------------|
| `Free`  | Page explicitly says free / $0 / no cost                   |
| `Free?` | Community meetup with no listed cost (probably free, unconfirmed) |
| `TBD`   | Conference with no listed cost (definitely paid, just not announced yet) |

Without this distinction, all three collapse and the "free events" filter becomes useless.
Embed this rule in the extractor prompt explicitly.

## What Didn't Work (Mistakes To Avoid On Revival)

### 1. Daily Sonnet enrichment via Claude Code subscription
**The killer.** See the [Sonnet Quota Incident](#the-sonnet-quota-incident). If reviving,
either use a separate Anthropic API key OR cap heavy enrichment to monthly cadence.

### 2. Per-metro Grok loop for discovery
The original design ran Grok 15 times per month, once per metro (SF, NYC, Seattle, Austin,
LA, Boston, Chicago, Denver, DC, Miami, Atlanta, Dallas, London, Toronto, Berlin). Result:
massive duplicates (the same event posted from multiple cities), high admin triage burden,
and conferences (which aren't metro-bound) were poorly served. **Better:** 4-6 global queries
with topical scopes (e.g. "major AI conferences", "academic AI/ML", "AI safety summits",
"tech conferences with AI tracks").

### 3. The two-path submit form
`/events/submit` had two paths: **Path A** (URL + name + note → we enrich) and **Path B**
(full manual form with location/cost/eligibility/etc.). Path B was used **zero** times in
production. The community submission flywheel never spun up because there were no users yet.
**Better:** ship Path A only, period. If users start using it heavily, then add Path B.

### 4. Hackathon as a dedicated filter dimension
Hackathons were a top-level toggle in the UI. Used by nobody. **Hackathon is a tag, not a
filter dimension.** Tag-based search handles it fine.

### 5. The `free` filter
Same story. Users don't filter for free events; they filter for "events I can attend".
The `free` boolean was a wasted UI slot.

### 6. Country dropdown with full COUNTRY_LIST
30+ countries with a long tail of single-event entries makes the dropdown unusable.
**Use region buckets** (4 buckets: NA / EU / Asia / Other) — see pattern #5 above.

### 7. Trying to scrape Microsoft Build / certain JS-heavy conference sites
MS Build is fully JS-rendered behind anti-bot detection. Even `scrape.do` couldn't get
usable content. Plan for **manual entry** on a small percentage of major conferences whose
sites are scrape-hostile. Don't try to engineer around this.

### 8. Recurring-event support
The original schema had `is_recurring`, `recurrence_rule`, `series_id`, `next_occurrence`,
`recurrence_status`. The freshener even had pause-detection logic (`if no future date in
60+ days, mark as paused`). **Most events flagged as "recurring" by Grok were one-offs**
that the LLM mistakenly tagged because the organizer had previously hosted similar events.
The recurring infrastructure added schema complexity for ~zero correct tagging in practice.
**Better:** drop recurring entirely. Each instance is a separate event row. Period.

### 9. Hand-curated allowlists drift
`AUTO_APPROVE_SOURCES` was a hardcoded Python set:
```python
AUTO_APPROVE_SOURCES = {
    "Anthropic", "Google DeepMind", "Weights & Biases", "OpenAI",
    "LangChain", "Cerebral Valley", "AI Tinkerers", "AI Furnace",
    "AI Salon", "AGI Builders", "FAR.AI", "Redwood Research",
    "CAIS", "AI Engineer", "Bond AI",
    "NeurIPS", "ICML", "ICLR", "CVPR", "AAAI", "ACL",
}
```
This list rotted. New trusted orgs got added inconsistently. **Better:** make the auto-approve
allowlist a DB table from day 1, with admin UI to add/remove.

### 10. MCP `list`/`dict` parameter types arrive as empty strings
This was a generic gotcha that bit the agent tools server: when an MCP tool is declared with
`list` or `dict` parameter types via `@tool`, the values arrive as empty strings, not parsed
JSON. **Workaround:** declare params as `str` and parse with a `_safe_json_parse()` helper.
This is documented in `docs/knowledge/` for the news pipeline; it bit the events code too.

## Cost Reality (Measured, Not Estimated)

The original planning section estimated **~$5-8/month**. This was wrong by an order of
magnitude in dollar terms, and meaningless in subscription terms (the actual constraint).

### What we measured (Anthropic API equivalent dollars)

| Pipeline run | Sonnet calls | Haiku calls | Approx $ equivalent |
|---|---|---|---|
| Daily `--daily` (44 events processed) | ~44 enrich + ~44 host_profile | ~44 classify + ~44 pricing_find + ~10 dedup | ~$1.38 |
| Weekly `--freshen` (~30 events checked) | ~30 enrich | ~30 pricing_find | ~$0.95 |
| Monthly `--discover` (15 metros) | 0 (Grok only) | 0 | ~$0.50 (xAI) |
| **Monthly total (Anthropic)** | | | **~$42** |
| **Monthly total (xAI)** | | | **~$0.50** |

That's the "if billed at API rates" view. **The actual constraint was Sonnet quota on the
Claude Code subscription**, where:
- 5x Max plan: ran out within 2 days of launch
- 20x Max plan: ~50% used mid-week (sharing with news pipeline)

### Lesson for revival

Estimate cost in TWO units: dollar-equivalent AND subscription-quota-percentage. Subscription
quota is the binding constraint when you're using Agent SDK with Claude Code auth. If your
pipeline can't fit comfortably in <30% of the weekly Sonnet quota, it doesn't fit.

## Embedded Working Prompts

These are the actual prompts that shipped to production. They're already iterated — don't
start from scratch on revival.

### EVENT_PAGE_EXTRACTOR (Sonnet) — the most valuable artifact

The single most important piece of prompt engineering in the whole feature. Iterations
over weeks of seeing wrong field placements. Use as-is on revival.

```text
You are extracting structured event details from an event web page. Read the
ENTIRE page carefully. Information may appear anywhere — in headers, in the body
text, in sidebar details, even casually mentioned in a paragraph. Extract
everything you can find.

Event: {event_name}
URL: {event_url}

Page content:
{content}

FIELD PLACEMENT RULES (critical — do not mix these up):
- location_name = ONLY the venue/building name (e.g. "Moscone Center", "The House
  by Edge & Node"). This is NOT the host/organizer. If a page shows "The House by
  Edge & Node" as the venue and "Sentient Foundation" as the host — the venue is
  "The House by Edge & Node" and the host is "Sentient Foundation".
- location_address = street address of the venue (e.g. "747 Howard St"). Some
  pages show this in a "Location" section at the bottom, or link it to Google
  Maps. Look for it there. null if hidden/"Register to see address".
- location_city = the CITY from the event location header (near the date/time).
  On Luma: "City, State" appears right below the date. Use THAT, not neighborhoods
  or suburbs from the host name or description.
- host_name = the ORGANIZER name. Look for "Hosted by", "Presented by", or the
  organization name. NOT the venue.

WHERE TO LOOK FOR EACH FIELD:
- Price/cost: Check ticket section, "Get Tickets" area, AND the body text. Phrases
  like "free for all", "open and free", "no cost", "$50 per person", "tickets start
  at $X" count. Even casual mentions like "this event is free for founders and
  developers" means cost=Free.
- Eligibility: Check both the formal details AND body text. "Open and free for all
  AI founders and developers" → eligibility is "AI founders and developers".
  "Anyone can attend" → "Open to all".
- Venue/Address: Check BOTH the location shown near the date AND any "Location"
  section lower on the page. Some pages show venue name at top but full address at
  bottom.
- Description: Write a specific, useful 2-3 sentence summary. What will attendees
  DO at this event? What topics are covered? Who is speaking? Don't be generic.
- Normalized description: One sentence, max 120 chars, that someone can skim in 2
  seconds and know what the event is.

{
  "location_name": "Venue/building name only. null if not shown.",
  "location_address": "Street address. Check Location section at bottom of page too. null if hidden.",
  "location_city": "City from event header near the date. ALWAYS extractable.",
  "location_state": "State/province/region. null if not applicable.",
  "location_country": "Full country name (e.g. 'United States', not 'US'). Always extractable.",
  "cost": "Rules: 'Free' if page says free/$0/no cost. 'Free' if body text says 'free for X'. Extract tiers if shown (e.g. '$499 Early Bird / $999 Standard'). 'Free?' if community meetup with nothing listed. 'TBD' if conference with nothing listed.",
  "format": "in_person | online | hybrid",
  "event_type": "ai_conference | ai_track | community_event | university_event",
  "is_hackathon": true or false,
  "description": "2-3 specific sentences. What happens at this event? Topics, speakers, activities. Not generic marketing fluff.",
  "normalized_description": "One crisp sentence, max 120 chars. Skimmable.",
  "eligibility": "Who can attend — check body text too. 'Open to all', 'AI founders and developers', 'Application required', etc.",
  "estimated_attendance": "If mentioned anywhere on the page. null otherwise.",
  "host_name": "The organizer — look for 'Hosted by' or 'Presented by'. NOT the venue name.",
  "host_url": "URL to the host/organizer's page. Look for linked organizer names, 'Hosted by' links, organizer profile URLs. On Luma this is the calendar/profile link. On conference sites it might be the company URL. null if not found.",
  "key_speakers": "Notable speakers if listed anywhere, comma-separated. null if none.",
  "sold_out": true or false,
  "waitlist": true or false
}

Return ONLY valid JSON. No markdown fences, no explanation.
```

### EVENT_PRICING_FINDER (Haiku) — cheap pre-pass

```text
You find the pricing or registration page URL from event page content.

Given the text content of an event page and its URL, find the link to the
pricing, tickets, or registration page.

Look for links containing: tickets, register, pricing, passes, buy, attend,
sign up, RSVP

If pricing information is already on this page (you can see actual dollar
amounts or "Free"), return NONE.
If no pricing/registration link is found, return NONE.

Return ONLY a single full URL, or the word NONE. No other text.
```

### EVENT_CLASSIFIER (Haiku) — type taxonomy

```text
You classify AI events into our taxonomy.

Given an event's name, description, and source, return a JSON object:
{
  "event_type": "ai_conference" | "ai_track" | "community_event" | "university_event",
  "is_hackathon": true | false,
  "format": "in_person" | "online" | "hybrid",
  "tags": ["tag1", "tag2"],
  "eligibility": "Open to public" | "Application required" | etc.
}

Classification rubric:
- ai_conference: Event's PRIMARY purpose is AI content/community. Includes events
  by AI companies (GTC, LangChain Interrupt, AI Engineer World's Fair), research
  conferences (NeurIPS, ICML), and dedicated AI events of any size.
- ai_track: BROAD tech conference with significant AI tracks/content. Not primarily
  about AI but an AI practitioner would find 1+ days of relevant content. Examples:
  AWS re:Invent, Dreamforce, CES, WWDC.
- community_event: Informal, recurring, community-organized. Meetups, build nights,
  demo evenings, networking for builders.
- university_event: Public talks, seminars, workshops from university AI labs.
- is_hackathon: true if the event involves building/coding in a competitive or
  collaborative format. Can be true for any event_type.

Tags: Use from this taxonomy — labs (anthropic, openai, google, meta, etc.),
models (claude, chatgpt, gemini, llama, etc.), technology (agents, mcp, rag,
fine-tuning, etc.), domain (security, robotics, creative, enterprise, etc.)

Return ONLY valid JSON, no explanation.
```

### EVENT_DEDUP_CHECKER (Haiku) — fuzzy match tiebreak

```text
You determine if two events are the same event.

Given:
- NEW event: name, date, location, URL
- EXISTING event: name, date, location, URL

Determine if they are the same event (just listed differently across sources).

Consider:
- Same event may have slightly different names: "AI Tinkerers SF: April" vs
  "SF AI Tinkerers April Meetup"
- Same event may have slightly different dates if one source is wrong
- Same URL = definitely same event
- Same org + same city + within 3 days = likely same event
- Completely different orgs or cities = different events

Return ONLY one word: SAME or DIFFERENT
```

### EVENT_FRESHENER (Haiku) — change detection

```text
You check if an event's details have changed.

Given:
- STORED event data (our current record)
- CURRENT page content (freshly scraped from the event URL)

Compare and report any changes. Check for:
- Date changes (moved, extended, shortened)
- Venue/location changes
- Cost/pricing changes
- Sold out or waitlist status
- Cancellation
- New speakers announced
- Description updates

Return JSON:
{
  "has_changes": true | false,
  "changes": [
    {"field": "cost", "old": "$499", "new": "$599", "note": "Price increased"},
    {"field": "status", "old": "active", "new": "canceled", "note": "Event canceled per website"}
  ],
  "canceled": true | false,
  "sold_out": true | false,
  "waitlist": true | false
}

If no changes detected, return:
{"has_changes": false, "changes": [], "canceled": false, "sold_out": false, "waitlist": false}

Return ONLY valid JSON, no explanation.
```

### GROK_EVENT_DISCOVERY (Grok per-metro variant) — what shipped

Note: this is the per-metro variant (the one we actually used). The conferences-only
global variant from the 2026-04-06 refactor is below.

```text
Search X for AI and machine learning meetups, events, hackathons, and
community gatherings in or within 50 miles of {metro} happening in the
next 3 months.

For each event, provide as a JSON array:
[
  {
    "name": "Event name",
    "date": "YYYY-MM-DD or 'TBD'",
    "end_date": "YYYY-MM-DD or null",
    "location_name": "Venue name",
    "location_city": "City",
    "location_country": "Country",
    "url": "Event page or RSVP link",
    "organizer": "Who is running this",
    "type": "community_event or ai_conference or hackathon",
    "cost": "Free or price",
    "description": "One sentence description",
    "format": "in_person or online or hybrid"
  }
]

Include:
- Company-hosted AI events and mini-conferences
- Local AI/ML meetup groups and their upcoming events
- AI hackathons (standalone or at conferences)
- University AI lab talks open to the public
- Startup demo days focused on AI

Exclude:
- Events that are student/faculty only
- Paid courses or bootcamps over $500
- Grifter events: "passive income with AI", "monetize AI", fake expert workshops
- Consultancies using meetups for lead generation
- Events where the organizer is posturing as an AI authority without credentials
- "AI thought leader" summits with no technical substance

The vibe: engineers in a room hacking on AI, showing each other what they
built. Not suits talking about AI transformation over cocktails.

Return ONLY valid JSON array. If no qualifying events found, return [].
```

### GROK_CONFERENCE_DISCOVERY (Grok global variant) — from the 2026-04-06 refactor

This is the never-deployed conferences-only version from the day-before-kill refactor.
It's narrower and arguably better suited if reviving with a conference-only scope.

```text
Search X (Twitter) and the web for conferences matching this query:

{query_seed}

Find real, scheduled conferences with confirmed dates. For each, return JSON:
[
  {
    "name": "Conference name (e.g. 'NeurIPS 2026', 'AI Engineer World's Fair 2026')",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD or null if single day",
    "location_name": "Venue if known, else null",
    "location_city": "City",
    "location_country": "Full country name (e.g. 'United States')",
    "url": "Official conference website URL",
    "host": "Organizing body / company / society",
    "event_type": "ai_conference or tech_conference",
    "cost": "Price range if known (e.g. '$499-$1499') or null",
    "description": "1-2 sentence description of what the conference covers",
    "format": "in_person, online, or hybrid"
  }
]

CLASSIFICATION:
- ai_conference: Primary purpose is AI/ML content. Examples: NeurIPS, ICML,
  AI Engineer, GTC, LangChain Interrupt, anything with "AI" or "ML" in the name.
- tech_conference: Broad tech conference with significant AI tracks. Examples:
  AWS re:Invent, KubeCon, Web Summit, Dreamforce, CES, WWDC.

INCLUDE:
- Major recurring conferences (annual, well-known)
- Newer / emerging conferences with confirmed dates
- Academic and industry conferences
- AI safety / alignment / interpretability summits

EXCLUDE:
- Local meetups, community gatherings, or recurring weekly/monthly events
- Hackathons (unless part of a multi-day conference)
- Paid courses, bootcamps, training programs
- Vendor sales events disguised as conferences
- "AI thought leader" summits with no technical substance
- Speculative or unconfirmed events

Only include conferences where you have a real URL and a confirmed (or at
least announced) date. If the event is annual but the next date isn't
announced yet, skip it.

Return ONLY a valid JSON array. If no qualifying conferences found, return [].
```

The query seeds used in the conferences-only refactor:
- `"major upcoming AI conferences worldwide in the next 12 months (NeurIPS, ICML, ICLR, AI Engineer, GTC, similar tier)"`
- `"tech conferences with significant AI tracks in the next 12 months (AWS re:Invent, KubeCon, Web Summit, Dreamforce, similar)"`
- `"academic AI/ML research conferences and workshops in the next 12 months (CVPR, ACL, EMNLP, AAAI, COLM, similar)"`
- `"AI safety, alignment, and interpretability conferences and summits in the next 12 months"`

### HOST_PROFILER (Sonnet) — short, effective

```text
Who is {host_name}? Write a 2-3 sentence profile for an AI events calendar.
What kind of organization are they? What do they do? Are they a company,
community group, nonprofit, research lab? Keep it factual and brief.

Return ONLY the profile text, no JSON, no markdown, no preamble.
```

## Source Inventories (the curated data)

### Luma calendars subscribed

```python
LUMA_CALENDARS = [
    # Priority calendars
    ("claudecommunity", "Anthropic"),
    ("deepmind", "Google DeepMind"),
    ("wandb", "Weights & Biases"),
    ("openainyc", "OpenAI NYC"),
    ("langchain", "LangChain"),
    ("cerebralvalley", "Cerebral Valley"),
    ("genai-sf", "Bond AI SF"),
    ("genai-ny", "Bond AI NYC"),
    ("genai-collective", "GenAI Collective"),
    ("ai-furnace", "AI Furnace NYC"),
    ("ai-furnace-uk", "AI Furnace London"),
    ("ai-furnace-boston", "AI Furnace Boston"),
    ("agibuilders", "AGI Builders"),
    ("ai-builders", "AI Builders Europe"),
    ("aisalon", "AI Salon"),
    # Safety
    ("AISafetyBerlin", "AI Safety Berlin"),
    ("paperclip-club", "Paperclip Club"),
    ("AISecurityCollective", "AI Security Collective"),
    # City-specific
    ("artificialintelligencenyc", "AI NYC"),
    ("sf-mlops-community", "SF MLOps"),
    ("nyc.mlops", "NYC MLOps"),
    ("london-mlops", "London MLOps"),
    ("parisai", "Paris AI"),
    ("aimadlab", "Norway AI Mad Lab"),
    ("DeepStation", "Miami DeepStation"),
    ("infer", "Vancouver Infer"),
]
```

To fetch a Luma calendar's events: `https://lu.ma/{slug}` (HTML with embedded JSON-LD), or
if iCal is exposed `https://lu.ma/{slug}.ics`. JSON-LD discovery is the more reliable path.

### Conference circuit pages (multi-city event series scraped from a single source)

```python
CIRCUIT_PAGES = [
    ("https://www.ai.engineer/#upcoming-events", "AI Engineer"),
    ("https://aitinkerers.org/ai-meetups", "AI Tinkerers"),
]
```

### AI lab event pages

```python
LAB_EVENT_PAGES = [
    ("https://www.anthropic.com/events", "Anthropic"),
    ("https://deepmind.google/discover/events/", "Google DeepMind"),
    ("https://wandb.ai/site/resources/events/", "Weights & Biases"),
    ("https://far.ai/events", "FAR.AI"),
    ("https://ai.meta.com/events/", "Meta AI"),
    ("https://cohere.com/events", "Cohere"),
]
```

### Auto-approve source allowlist (hardcoded — should be a DB table on revival)

```python
AUTO_APPROVE_SOURCES = {
    "Anthropic", "Google DeepMind", "Weights & Biases", "OpenAI",
    "LangChain", "Cerebral Valley", "AI Tinkerers", "AI Furnace",
    "AI Salon", "AGI Builders", "FAR.AI", "Redwood Research",
    "CAIS", "AI Engineer", "Bond AI",
    # Major conferences
    "NeurIPS", "ICML", "ICLR", "CVPR", "AAAI", "ACL",
}
```

### Metros for the per-metro Grok loop (DEPRECATED — see lessons)

```python
METRO_AREAS = [
    "San Francisco Bay Area", "New York City", "Seattle", "Austin",
    "Los Angeles", "Boston", "Chicago", "Denver", "Washington DC",
    "Miami", "Atlanta", "Dallas", "London", "Toronto", "Berlin",
]
```

If reviving, use the global discovery query approach instead. This list is preserved for
historical context only.

## Database Schema (as it actually shipped)

The schema differs from the original planning section in several ways: we added `host_url`,
`recurrence_status`, `last_confirmed`, `ai_track_notes`, `is_dates_tbd`, `tbd_usual_month`,
`approval_notes`, `approved_by`, `approved_at` during build.

```python
class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Content
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    normalized_description: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    # Values: ai_conference, ai_track, community_event, university_event
    # (after 2026-04-06 conferences-only refactor: ai_conference, tech_conference)
    is_hackathon: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calendar_events.id"), nullable=True
    )
    format: Mapped[str] = mapped_column(String, nullable=False)  # in_person | online | hybrid

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_dates_tbd: Mapped[bool] = mapped_column(Boolean, default=False)
    tbd_usual_month: Mapped[str | None] = mapped_column(String)

    # Recurring (DEPRECATED — see lessons; most "recurring" tags were wrong)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(String)
    series_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    next_occurrence: Mapped[date | None] = mapped_column(Date)
    recurrence_status: Mapped[str | None] = mapped_column(String)

    # Location
    location_name: Mapped[str | None] = mapped_column(Text)  # venue, NOT host
    location_address: Mapped[str | None] = mapped_column(Text)
    location_city: Mapped[str | None] = mapped_column(String)
    location_state: Mapped[str | None] = mapped_column(String)
    location_country: Mapped[str | None] = mapped_column(String)  # always full name, not US/UK
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Details
    url: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[str | None] = mapped_column(String)  # Free | Free? | TBD | "$499 Early Bird / $999 Standard"
    eligibility: Mapped[str | None] = mapped_column(String)
    estimated_attendance: Mapped[str | None] = mapped_column(String)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    ai_track_notes: Mapped[str | None] = mapped_column(Text)  # for ai_track events: what AI content

    # Host/Source
    host_name: Mapped[str | None] = mapped_column(String)
    host_url: Mapped[str | None] = mapped_column(Text)
    host_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("event_hosts.id"), nullable=True
    )
    source: Mapped[str | None] = mapped_column(String)  # luma:claudecommunity, grok_discover, etc.
    submitted_by: Mapped[int | None] = mapped_column(Integer)  # discourse user id

    # Status/Approval
    status: Mapped[str] = mapped_column(String, default="active")  # active | pending | pending_approval | rejected | canceled
    approval_notes: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(Integer)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Freshness
    last_confirmed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    host = relationship("EventHost", back_populates="calendar_events")
    parent_event = relationship("CalendarEvent", remote_side="CalendarEvent.id")

    __table_args__ = (
        Index("idx_calendar_events_slug", "slug", unique=True),
        Index("idx_calendar_events_start_date", "start_date"),
        Index("idx_calendar_events_status", "status"),
        Index("idx_calendar_events_event_type", "event_type"),
        Index("idx_calendar_events_tags", "tags", postgresql_using="gin"),
    )


class EventHost(Base):
    __tablename__ = "event_hosts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)  # 2-3 sentence profile from HOST_PROFILER
    trust_level: Mapped[str] = mapped_column(
        String, default="requires_review"
    )  # auto_approve | requires_review | blacklisted
    blacklist_reason: Mapped[str | None] = mapped_column(Text)
    approval_count: Mapped[int] = mapped_column(Integer, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    calendar_events = relationship("CalendarEvent", back_populates="host")
```

The schema was created by Alembic migrations **b13** (initial), **b14** (host_url + recurring),
and **b15** (host profile description). To recreate the schema, write a new migration that
mirrors these — or `alembic downgrade` to b12 if those revisions still exist in `alembic/versions/`.

## How to Revive This

Step-by-step recipe if Mike (or future-Mike) decides this feature is worth bringing back.
Read this BEFORE the original planning section — the original is naive about what we learned.

### Step 0: Validate demand FIRST

Before writing any code, confirm:
1. Are users (real users on the forum, not Mike) asking for this?
2. Is anyone manually maintaining a list of conferences in a forum thread? (That's the
   real demand signal — not Mike speculating about what would be cool.)
3. Is the friction of asking Grok directly actually a problem worth automating?

If none of those are true, stop here. The kill decision was correct.

### Step 1: Pick a scope. The conferences-only scope is the safe one.

Don't try to build the full vision (conferences + meetups + community + university + Luma
sync + per-metro Grok). Build conferences-only:
- AI conferences (NeurIPS, ICML, GTC, AI Engineer, etc.)
- Tech conferences with AI tracks (re:Invent, KubeCon, Web Summit, etc.)
- **Skip community events entirely.** They're 90% Luma redundant. Link to Luma directly
  if users want meetups.
- **Skip per-metro discovery.** Use 4-6 global Grok queries instead.
- **Skip recurring events.** Each instance is a separate row.

### Step 2: Solve the auth/quota problem first

Decide BEFORE you write code:
- Will this run via the Claude Code subscription or a separate Anthropic API key?
- If subscription: cap heavy enrichment to monthly cadence ONLY. No daily Sonnet runs.
- If separate API key: budget the dollar cost separately, monitor it.

Either way: measure both dollar-cost AND Claude Code quota percentage during the first
week of operation. Pull the plug at 25% of weekly Sonnet quota.

### Step 3: Lift, don't rebuild

Use the embedded prompts above as-is. Don't iterate them from scratch. They're already
well-tuned. Use the code patterns above as-is — fuzzy dedup ladder, two-stage enrichment,
haversine SQL, region bucketing, host trust ladder.

### Step 4: Ship the simplest possible UI first

- One page: `/conferences` (or `/events` if you want to keep the URL)
- Filters: search, type (AI/Tech), region, format. **Nothing else.** No date shortcuts,
  no hackathon filter, no free filter, no country dropdown.
- One submission path: URL + name + optional note. **No two-path form.**
- Admin queue: pending list, approve, reject, edit. **No host blacklist UI** until you
  see actual abuse.

### Step 5: Cron schedule

```cron
# Discover NEW conferences via Grok (monthly, 1st)
0 12 1 * * cd /app && python -m agent.event_orchestrator --discover

# Re-scrape stale conferences (monthly, 15th)
0 12 15 * * cd /app && python -m agent.event_orchestrator --freshen
```

**No daily anything.** No weekly anything. Conferences move slowly. Monthly is plenty.

### Step 6: Validate AFTER 30 days

Check:
- Did Mike actually use this in the first 30 days? (Look at admin approval logs.)
- Are forum users submitting? (Look at the submission queue.)
- Is the data quality holding up? (Spot check 10 random conferences.)
- Did the Sonnet quota stay <25%?

If any of those are no, kill it again. This is a feature you should be willing to kill
twice before committing real ongoing maintenance to it.

### Step 7: Schema revival

Either:
- (a) Write a new Alembic migration that creates the tables from the schema in the
  "Database Schema" section above, OR
- (b) `alembic downgrade` to the revision before the kill migration. The kill migration
  is `<TBD — captured at commit time>`. This only works if you haven't made other unrelated
  schema changes since then.

Option (a) is safer. Option (b) is faster.

The kill commit's Alembic migration is `alembic/versions/b18_drop_calendar_tables.py`.
Its `downgrade()` is intentionally a stub — see that file for instructions on writing a
fresh recreate migration.

## Backups & Git Pointers

### Git
- **Last working commit (full event calendar pipeline + UI + DB):** `0ce897beb59b7919d6d2cafd27bd575b7dd14b30`
  - This is the SHA before the conferences-only refactor or the kill commit.
  - To browse the original code: `git show 0ce897b:agent/event_orchestrator.py` (etc.)
  - To revert all event-calendar code in a new branch: `git checkout -b revive-events 0ce897b -- agent/event_orchestrator.py agent/event_runbooks.py agent/event_tools.py src/ai_signal/api/calendar.py src/ai_signal/models/calendar_event.py frontend/src/app/events frontend/src/components/CalendarEvent*.tsx frontend/src/components/CalendarEventSidebar.tsx frontend/src/lib/calendarUtils.ts`
- **The kill commit:** `26ea97722c14d63a115d3ca157cb33f7921bcdd1`. The Alembic migration
  `b18_drop_calendar_tables.py` in this commit drops the calendar tables.

### Server backups (Hetzner: 135.181.18.246, ssh port 6969)
- `~/apps/ai-signal/backups/calendar_events_wipe_2026-04-06.jsonl` — the 139 community/university/hackathon/test rows deleted on 2026-04-06 during the conferences-only refactor.
- `~/apps/ai-signal/backups/event-calendar-archive/` — full nightly DB backup snapshot taken
  just before the table drop, plus README explaining contents. **This is the long-term
  archive of the final production state.**
- The daily DB backups in `~/server-infrastructure/` continue to retain calendar tables for
  ~30 days (their normal rotation). After ~2026-05-07, those rotations will no longer
  contain calendar table data — only the archive snapshot will.

### What's NOT preserved
- Production data (event rows, host trust scores, admin approval notes). These won't be
  useful on revival anyway because they'll be stale. The schema and code are what matter.
- Discourse `events` bot user, API key, `event-submissions` category — to be deleted manually.
  Recreating these on revival is a 5-minute Discourse admin task.

## Forum Cleanup TODO (manual)

These items live on the Discourse forum (not in the code) and need to be killed by hand
via the Discourse admin UI:

1. **`events` bot user** — system user created for posting submission notifications. Find
   under Admin → Users, search "events". Delete or anonymize.
2. **API key for the events bot** — `DISCOURSE_API_KEY_EVENTS` in `.env`. Find under
   Admin → API → API Keys. Revoke. After revoking, the env var can be removed from
   `forum-management/.env` and from `src/ai_signal/config.py` (settings).
3. **`event-submissions` category (id 30)** — destination for new-submission notifications.
   Find under Admin → Categories. Delete (or archive if you want to keep the topic history).

Mike will do these manually. None block the kill commit.

---

## Original Planning (Historical)
*(Everything below this line is the original feature doc as it was at planning time.
Preserved verbatim. Read the sections above first — they reflect what we actually
learned during build.)*

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
