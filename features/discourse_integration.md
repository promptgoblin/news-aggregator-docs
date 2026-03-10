# Feature: Discourse Integration — "Discuss" Button

---
type: feature
status: planning
complexity: C2
tags: [discourse, forum, integration]
depends_on: [production_deployment, forum_auth]
required_by: []
---

## User Intent

### Goal
Let users start or join discussions about news events on the Prompt Goblins forum. A "Discuss" button on each event creates a forum thread (or links to an existing one), with a bot-authored first post summarizing the story.

### Success Criteria
- Clicking "Discuss" on an event takes you to its forum thread
- If no thread exists, one is created automatically with a bot summary
- Race conditions handled: two users clicking "Discuss" at the same time don't create duplicate threads
- Users who aren't logged in get routed through signup/login first, then redirected back
- Bot posts are attributed to a dedicated "AI Signal" user on the forum

### User Flow — Thread Exists
1. User clicks "Discuss" on event
2. System checks `discourse_topic_id` on event record
3. Thread exists → redirect to `promptgoblins.ai/t/{slug}/{topic_id}`

### User Flow — Thread Doesn't Exist, Logged In
1. User clicks "Discuss"
2. No thread exists → API call creates thread via Discourse API
3. Bot posts first message (event title + key points or "What This Means")
4. Store `discourse_topic_id` on event record (atomic)
5. Redirect user to new thread

### User Flow — Thread Doesn't Exist, Not Logged In
1. User clicks "Discuss"
2. No thread exists, user not authenticated
3. Redirect to Discourse login/signup with return URL
4. User logs in or signs up
5. Redirect back to AI Signal with intent to discuss
6. **Re-check**: does thread exist now? (someone else may have created it)
7. If yes → redirect to existing thread
8. If no → create thread (same as logged-in flow)
9. Redirect to thread

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## References
- Discourse API: `POST /posts` to create topic
- Forum: promptgoblins.ai (category 8 = AI News)
- Related: [features/forum_auth.md]

## Implementation

### Approach
The "Discuss" button hits an API endpoint on ai-signal-api. The endpoint handles the check-then-create flow with a database lock to prevent race conditions. Thread creation uses the Discourse API (system user or dedicated bot user API key). The event record stores `discourse_topic_id` after creation.

### Key Components
- **`discourse_topic_id`** column on `events` table (nullable int, indexed)
- **`POST /api/events/{id}/discuss`** endpoint — orchestrates the flow
- **Discourse API client** — creates topics in the AI News category
- **Bot user** on Discourse — "AI Signal" or "NewsBot" with its own API key
- **Frontend Discuss button** — on EventRow, EventModal, and event detail page

### Race Condition Handling
```python
# Use SELECT FOR UPDATE to lock the event row
async with db.begin():
    event = await db.execute(
        select(Event).where(Event.id == event_id).with_for_update()
    )
    if event.discourse_topic_id:
        # Someone beat us — redirect to existing thread
        return {"topic_url": f"https://promptgoblins.ai/t/{event.discourse_topic_id}"}

    # Create thread via Discourse API
    topic = await discourse_client.create_topic(...)
    event.discourse_topic_id = topic["topic_id"]
    await db.commit()

    return {"topic_url": f"https://promptgoblins.ai/t/{topic['slug']}/{topic['topic_id']}"}
```

### Bot First Post Content
```markdown
# {event.title}

{event.tier1_scan}

**Key points:**
{formatted tier3 key points, 3-5 bullets}

---
*This discussion was started from [AI Signal](https://news.promptgoblins.ai/event/{slug}).
What do you think about this story?*
```

Avoids duplicating "What This Means" verbatim (SEO concern). Uses key points + tier1 scan instead.

### Data Model
```python
# Addition to Event model
discourse_topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
```

## Edge Cases & Considerations

### Handled
- **Race condition**: SELECT FOR UPDATE prevents duplicate thread creation
- **Auth redirect loop**: Store intent in URL params (`?discuss=event_id`), process on return
- **Discourse API failure**: Return error, don't store topic_id, user can retry
- **Event deleted/merged**: Check event status before creating thread
- **Duplicate content SEO**: Bot post uses key points, not full "What This Means"

### Security
- Discourse API key stored in env var, never exposed to frontend
- Bot user has minimal permissions (create topics in AI News category only)
- Rate limit the discuss endpoint (prevent spam thread creation)
- Validate event_id exists before any Discourse API call

## Definition of Done

### Automated Checks
- [ ] `POST /api/events/{id}/discuss` returns topic URL for existing thread
- [ ] Two concurrent requests to same event don't create duplicate threads
- [ ] Bot post appears correctly formatted on Discourse

### Acceptance Criteria
- [ ] "Discuss" button visible on event cards and detail views
- [ ] Thread created with bot summary on first click
- [ ] Subsequent clicks redirect to existing thread
- [ ] Unauthenticated users redirected through login flow
- [ ] Post-login redirect correctly checks for existing thread before creating

## Outstanding
- [ ] Create "AI Signal" bot user on Discourse
- [ ] Generate API key for bot user
- [ ] Decide: which Discourse category? (category 8 = AI News, or new subcategory?)
- [ ] Decide: should high-score events auto-create threads (without user click)?
