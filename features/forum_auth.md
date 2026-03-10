# Feature: Forum Authentication & User Preferences

---
type: feature
status: planning
complexity: C2
tags: [auth, discourse, preferences, ux]
depends_on: [production_deployment]
required_by: [discourse_integration]
---

## User Intent

### Goal
Let users log in to AI Signal using their Prompt Goblins forum account. Once logged in, they can save display preferences (view mode, default filters, theme) and mark stories as read to keep their feed clean.

### Success Criteria
- Users log in via Discourse SSO (DiscourseConnect) — single account for forum + news
- Display preferences persist across sessions (view mode, filters, sort order)
- Stories can be marked as read (manual or auto on click/scroll)
- "Archive" or "mark all read" to clear the feed
- Logged-out users get a functional but non-personalized experience

### User Flow
1. User clicks "Sign In" on AI Signal
2. Redirected to Discourse login (or signup if new)
3. Discourse authenticates → redirects back with SSO payload
4. AI Signal creates/updates local user record
5. User's saved preferences load (filters, view mode, etc.)
6. Feed shows unread indicators on stories they haven't seen
7. Clicking a story (or expanding it) marks it as read
8. "Mark all as read" button clears current view

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## References
- Discourse DiscourseConnect: https://meta.discourse.org/t/discourseconnect-official-single-sign-on-for-discourse-sso/13045
- Related: [features/discourse_integration.md]
- Related: [features/rss_feeds.md] (user filters feed RSS too)

## Implementation

### Approach
Use Discourse as the identity provider via DiscourseConnect (formerly Discourse SSO). AI Signal acts as the SSO consumer — when a user clicks "Sign In", we redirect to Discourse with an HMAC-signed payload. Discourse authenticates and redirects back with user info. We store a minimal user record locally and a JWT session cookie. Preferences and read state are stored in our DB.

### Key Components
- **DiscourseConnect flow**: HMAC-SHA256 signed nonce exchange
- **`users` table**: Local user record (discourse_user_id, username, avatar_url, preferences)
- **`user_read_events` table**: Which events a user has seen
- **JWT session**: HttpOnly cookie, 30-day expiry, refresh on activity
- **Preferences API**: GET/PUT /api/user/preferences

### Data Model
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    discourse_user_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str]
    avatar_url: Mapped[str | None]
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    # preferences: {view_mode, default_sort, default_range, default_categories, theme}
    created_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]

class UserReadEvent(Base):
    __tablename__ = "user_read_events"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"), primary_key=True)
    read_at: Mapped[datetime]
```

### Preferences Shape
```json
{
  "view_mode": "summary",
  "default_sort": "newest",
  "default_range": "week",
  "default_categories": ["products", "research"],
  "mark_read_on_click": true,
  "theme": "system"
}
```

### Mark as Read
- **Manual**: Click "mark as read" button on event row
- **Auto (optional)**: Mark as read when user clicks into modal/detail (configurable in preferences)
- **Bulk**: "Mark all as read" button in feed header
- **Unread count**: Show badge/count of unread events in current filter view
- Read state scoped to user — doesn't affect other users

## Edge Cases & Considerations

### Handled
- **Discourse down**: Login fails gracefully, show error, allow anonymous browsing
- **User deleted from Discourse**: Next login attempt fails, local record stays (soft handling)
- **Preference migration**: New preference keys added with defaults, old prefs preserved
- **Multiple tabs**: JWT cookie shared, read state syncs on next fetch

### Security
- DiscourseConnect secret stored in env var (never in frontend)
- JWT signed with separate secret, HttpOnly + Secure + SameSite=Lax
- No passwords stored locally — Discourse owns authentication
- CSRF protection on preference mutation endpoints

### Limitations
- Read state is per-user, stored in our DB (not synced to Discourse)
- No real-time sync between tabs (refreshes on navigation)
- Discourse must be reachable for login (no offline auth)

## Definition of Done

### Acceptance Criteria
- [ ] "Sign In" button redirects to Discourse and back
- [ ] User avatar + name shown when logged in
- [ ] Preferences persist across sessions
- [ ] Stories show unread indicator for logged-in users
- [ ] "Mark as read" works (single + bulk)
- [ ] Logged-out users see full feed without personalization

## Outstanding
- [ ] Enable DiscourseConnect provider in Discourse admin settings
- [ ] Generate DiscourseConnect secret
- [ ] Decide: auto-mark-read default (on click vs manual only)
- [ ] Decide: show read count/badge in nav or just in feed?
