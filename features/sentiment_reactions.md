# Feature: Public Sentiment & Reactions (Grok)

---
type: feature
status: implemented
complexity: C2
tags: [grok, sentiment, xai, pipeline]
depends_on: []
required_by: []
---

## User Intent

### Goal
Add a "What People Are Saying" section to event detail views showing public reaction and sentiment from X (Twitter), powered by Grok's real-time search. Run sentiment analysis twice: once at distillation time, and again 3-7 days later to capture how sentiment evolves. Surface significant shifts; quietly record stable results.

### Success Criteria
- Events have a sentiment section with overall mood, prominent reactions, and fault lines
- Two-pass analysis: initial (at event creation) + follow-up (3-7 days later)
- If sentiment shifts significantly between passes, event gets an "Updated" badge and is re-surfaced in feed
- If sentiment is stable or shifts slightly, update is recorded quietly (no badge, no re-surfacing)
- All sentiment data recorded regardless of shift magnitude (for analytics)
- Only scored for events above a threshold (score >= 8, configured via `SENTIMENT_SCORE_THRESHOLD`)

### User Flow
1. Event is created by pipeline → Grok sentiment fetched (Pass 1)
2. "What People Are Saying" section appears on event detail
3. 3-7 days later, cron triggers Pass 2 for eligible events
4. If sentiment flipped (positive → negative, or vice versa):
   - Event gets "Updated" badge
   - Sentiment section shows both passes with delta callout
   - Event re-appears in feed (sorted by update time if user sorts by "newest")
5. If sentiment is stable: Pass 2 data recorded, no user-facing change

## Status: Implemented
**Started**: 2026-03-09
**Last Updated**: 2026-03-10

## References
- Grok API: xAI Responses API (`/v1/responses` endpoint with `x_search` tool)
- Related: [plan/plan_section_discovery.md] (Twitter/Grok as P2 source)

## Implementation

### Approach
Add a `sentiment_passes` JSONB column to the events table that stores an array of sentiment analysis results. Grok is called via the xAI Responses API (`/v1/responses`) with the `x_search` tool, which enables real-time X post search. Pass 1 runs as a post-processing step after event creation. Pass 2 runs from a daily cron that finds events 3-7 days old with only 1 pass. A shift detector compares passes and decides whether to badge the event.

### Key Components
- **Grok API client**: xAI Responses API (`/v1/responses`) with `x_search` tool, model `grok-4-1-fast-reasoning`
- **`sentiment_passes`** JSONB column on events table
- **Pass 1 runner**: Called after event creation in pipeline
- **Pass 2 cron**: Daily job, finds events needing follow-up
- **Shift detector**: Compares passes, decides badge/re-surface

### Data Model
```python
# Addition to Event model
sentiment_passes: Mapped[list | None] = mapped_column(JSONB, nullable=True)

# Each pass:
{
    "pass_number": 1,
    "analyzed_at": "2026-03-09T12:00:00Z",
    "overall_sentiment": "Broadly excited, skeptics focused on pricing",
    "prominent_reactions": [
        {
            "handle": "@sarahchen",
            "name": "Sarah Chen",
            "role": "CEO @SmallTeamAI",
            "stance": "Excited",
            "reaction": "This changes everything for small teams",
            "context": "Replying to announcement thread",
            "url": "https://x.com/sarahchen/status/1234567890"
        }
    ],
    "fault_lines": "~80/20 positive/skeptical. Enthusiasts focus on capabilities, skeptics worry about lock-in.",
    "sentiment_score": 0.7  # -1.0 to 1.0 for shift detection
}
```

### Shift Detection
```python
def detect_shift(pass1: dict, pass2: dict) -> tuple[bool, str]:
    """Returns (is_significant, description)."""
    score_delta = abs(pass2["sentiment_score"] - pass1["sentiment_score"])
    if score_delta >= 0.4:  # Flipped or major shift
        return True, f"Sentiment shifted from {pass1['overall_sentiment']} to {pass2['overall_sentiment']}"
    return False, "Sentiment stable"
```

Significant shift (delta >= 0.4):
- Add "Updated" badge to event
- Update `updated_at` timestamp (re-surfaces in "newest" sort)
- Add event_update record with type "sentiment_shift"

Stable/minor shift (delta < 0.4):
- Record Pass 2 data silently
- No badge, no re-surfacing
- Data available for analytics and on event detail page

### Grok API Call
```python
import httpx

async with httpx.AsyncClient(timeout=120) as client:
    response = await client.post(
        "https://api.x.ai/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.xai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "grok-4-1-fast-reasoning",
            "input": [{"role": "user", "content": prompt}],
            "tools": [{"type": "x_search"}],
        },
    )
```

The `x_search` tool lets Grok search X posts in real time rather than relying on training data. Response is parsed from the `output` list (look for `type: "message"` items with `output_text` content parts). JSON may be wrapped in a markdown code block, so the parser strips that if present.

### Reusable Grok Prompt

The prompt instructs Grok to search X for real posts and return structured JSON. Key design decisions:

- **Anti-fabrication guardrail**: "Only include posts you actually found via search. Do NOT fabricate quotes, usernames, or URLs."
- **Structured reaction format**: Each reaction includes `handle`, `name`, `role`, `stance`, `reaction`, `context`, and `url` — enough for the frontend to render rich cards with links back to the original posts.
- **Source quality guidance**: Tiered credibility (journalists/researchers > practitioners > anyone substantive). "Fewer quality reactions beat more low-quality ones."
- **Graceful empty state**: If little discussion exists, returns `"Limited public discussion so far"` with empty reactions array.
- **Two inputs**: `{event_title}` and `{what_this_means}` (falls back to `tier1_scan` if `what_this_means` is null).

See `pipeline/sentiment.py` `_SENTIMENT_PROMPT` for the full prompt text.

### Frontend Display

**Component**: `WhatPeopleAreSaying` — rendered in `EventExpanded`, `EventModal`, and the event detail page.

**Event detail — "What People Are Saying" section:**
- Below "What This Means"
- Shows latest pass by default
- If 2 passes exist and shift was significant: show callout banner
  - "Sentiment update (Mar 15): Community reaction shifted from broadly positive to mixed after reports of [issue]"
- If 2 passes, no significant shift: show latest pass, small "Updated Mar 15" timestamp
- Collapsible "Previous sentiment" to see Pass 1

### Pipeline Integration
- **Pass 1**: After `create_event` in event intelligence pipeline, if `importance_score >= SENTIMENT_SCORE_THRESHOLD` (currently 8). Entry point: `run_sentiment_pass1()` in `pipeline/sentiment.py`.
- **Pass 2**: Daily cron job, separate from main pipeline
  - Finds events where: `importance_score >= 8 AND len(sentiment_passes) == 1 AND created_at between 3-7 days ago`
  - Runs Grok for each, appends Pass 2 to `sentiment_passes`
  - Checks shift, applies badge if significant

## Edge Cases & Considerations

### Handled
- **Grok API down**: Skip sentiment, event still created. Retry on next cron run.
- **No Twitter discussion**: Grok returns empty/minimal reactions — display "Limited public discussion so far"
- **Event too niche**: Low-score events (< 8) skip sentiment entirely — saves API costs
- **Old events with no sentiment**: Graceful — section doesn't render if `sentiment_passes` is null

### Cost
- Grok API: ~$0.01-0.05 per call (depending on model/tokens)
- Pass 1: ~10-20 events per pipeline run × $0.03 = ~$0.30-0.60/run
- Pass 2: ~10-20 events per day × $0.03 = ~$0.30-0.60/day
- Monthly estimate: ~$20-40 for sentiment (manageable)

### Security
- xAI API key stored in env var
- Grok output is untrusted text — sanitize before DB insert and display
- Don't expose API key or raw Grok responses to frontend

## Definition of Done

### Acceptance Criteria
- [x] Events with score >= 8 get sentiment analysis on creation
- [ ] Pass 2 runs 3-7 days after event creation
- [ ] Significant shifts trigger "Updated" badge
- [ ] Stable sentiment recorded without re-surfacing
- [ ] "What People Are Saying" section renders on event detail
- [ ] Missing sentiment (old events, API failures) handled gracefully

## Outstanding
- [x] Get xAI API key — done, stored in env var
- [x] Test Grok structured output — using Responses API with `x_search`, JSON extracted from response (handles markdown code block wrapping)
- [x] Decide: score threshold for sentiment — `SENTIMENT_SCORE_THRESHOLD = 8` in `agent/config.py`
- [ ] Decide: exact timing for Pass 2 (3 days? 5 days? 7 days?)
- [ ] Decide: can this run before production deploy (locally) or after?
