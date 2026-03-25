# Feature: Forum Authentication & User Preferences

---
type: feature
status: implemented
complexity: C2
tags: [auth, discourse, sso, preferences, ux, reputation]
depends_on: [production_deployment]
required_by: [discourse_integration]
---

## User Intent

### Goal
Let users log in to AI Signal using their Prompt Goblins forum account. Once logged in, they can save display preferences (view mode, default filters, theme), mark stories as read, and start forum discussions.

### Success Criteria
- Users log in via Discourse OAuth2 — single account for forum + news
- Display preferences persist across sessions (view mode, filters, sort order)
- Stories can be marked as read (manual or auto on click/scroll)
- "Archive" or "mark all read" to clear the feed
- Logged-out users get a fully functional but non-personalized experience

### UX Principle: Prompted on Action

No login wall. No nag banners. The news site is open and fast by default. Login only surfaces when a user tries to do something that requires identity:

- **Click "Discuss"** → "Sign in with your Prompt Goblins account to start a discussion" → OAuth flow → creates topic after login
- **Click "Save filters"** → same prompt → saves preferences after login
- **Click "Mark as read"** → same prompt → starts tracking read state

Everything else (browsing, filtering, reading, searching) works without any account. The forum account is a natural extension when they want more, not a gate.

### User Flow — OAuth2 (Already Logged into Forum)
1. User clicks action requiring auth (Discuss, Save, etc.)
2. Prompt explains what signing in enables
3. Redirect to Discourse OAuth2 authorize endpoint
4. User is already logged in → auto-grants (or one-click approve first time)
5. Redirect back to AI Signal with auth code (~2 seconds, feels instant)
6. AI Signal exchanges code for token, fetches user info
7. Creates/updates local user record, sets JWT session cookie
8. Completes the original action (create topic, save prefs, etc.)

### User Flow — Not Logged into Forum
1. User clicks action requiring auth
2. Redirect to Discourse OAuth2 → Discourse login page
3. User logs in (or signs up if new)
4. Approves AI Signal access (first time only)
5. Redirect back → logged in, original action completes

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-11

## References
- Discourse as OAuth2 Provider: enable `discourse_as_oauth2_provider` site setting
- OAuth2 Authorization Code flow (standard RFC 6749)
- Related: [features/discourse_integration.md]
- Related: [features/rss_feeds.md] (user filters feed RSS too)

## Implementation

### Approach
Use Discourse as a standard OAuth2 provider. Enable the `discourse_as_oauth2_provider` setting on the forum, register AI Signal as an OAuth2 application to get a client_id and client_secret. Standard Authorization Code flow — redirect to forum, user authenticates, redirect back with code, exchange for access token, fetch user info from Discourse API. Store a minimal local user record and a JWT session cookie.

**Why OAuth2 over DiscourseConnect:**
- Standard protocol with broad library support
- Discourse natively supports being an OAuth2 provider
- Not coupled to Discourse's proprietary SSO format
- If we ever change forum software, just swap the OAuth2 provider
- Familiar "Sign in with X" pattern users already understand

### Key Components
- **OAuth2 flow**: Standard Authorization Code grant
- **Discourse settings**: `discourse_as_oauth2_provider` enabled, AI Signal registered as OAuth2 app
- **`/api/auth/discourse`**: Initiates OAuth2 flow (stores return URL + intended action)
- **`/api/auth/discourse/callback`**: Handles redirect, exchanges code, creates session
- **`users` table**: Local user record (discourse_user_id, username, avatar_url, preferences)
- **`user_read_events` table**: Which events a user has seen
- **JWT session**: HttpOnly cookie, 30-day expiry, refresh on activity
- **Preferences API**: GET/PUT /api/user/preferences

### OAuth2 Flow Detail
```
1. User triggers auth-required action
2. Frontend calls /api/auth/discourse?return_to=/&action=discuss&event_id=xxx
3. Backend generates state param (CSRF), stores in session/cookie
4. Redirect to: https://promptgoblins.ai/oauth/authorize
     ?client_id=AI_SIGNAL_CLIENT_ID
     &response_type=code
     &redirect_uri=https://news.promptgoblins.ai/api/auth/discourse/callback
     &scope=read
     &state={state_param}
5. Discourse authenticates user (or auto-grants if already logged in)
6. Redirect to callback with ?code=xxx&state=xxx
7. Backend exchanges code for access token:
     POST https://promptgoblins.ai/oauth/token
8. Fetch user info: GET https://promptgoblins.ai/oauth/userinfo
9. Create/update local User record
10. Set JWT cookie, redirect to return_to URL
11. Frontend detects auth, completes original action
```

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

### Config (env vars)
```
DISCOURSE_OAUTH_CLIENT_ID=...
DISCOURSE_OAUTH_CLIENT_SECRET=...
JWT_SECRET=...  # separate from Discourse, for signing our session cookies
```

## Edge Cases & Considerations

### Handled
- **Discourse down**: Login fails gracefully, show error, allow anonymous browsing
- **User deleted from Discourse**: Token refresh fails, clear local session, prompt re-login
- **Preference migration**: New preference keys added with defaults, old prefs preserved
- **Multiple tabs**: JWT cookie shared, read state syncs on next fetch
- **Action intent preservation**: Return URL + action stored in state param, completed after auth

### Security
- OAuth2 client_secret stored in env var (never in frontend)
- JWT signed with separate secret, HttpOnly + Secure + SameSite=Lax
- No passwords stored locally — Discourse owns authentication
- CSRF protection via OAuth2 state parameter
- Rate limit auth endpoints

### Limitations
- Read state is per-user, stored in our DB (not synced to Discourse)
- No real-time sync between tabs (refreshes on navigation)
- Discourse must be reachable for login (no offline auth)

## Definition of Done

### Acceptance Criteria
- [ ] Auth-required actions prompt login with clear explanation
- [ ] OAuth2 flow redirects to Discourse and back seamlessly
- [ ] Already-logged-in forum users get through in ~2 seconds
- [ ] User avatar + name shown when logged in
- [ ] Preferences persist across sessions
- [ ] Stories show unread indicator for logged-in users
- [ ] "Mark as read" works (single + bulk)
- [ ] Logged-out users see full feed without personalization

## Outstanding
- [ ] Enable `discourse_as_oauth2_provider` in Discourse admin
- [ ] Register AI Signal as OAuth2 application, get client_id/secret
- [ ] Decide: auto-mark-read default (on click vs manual only)
- [ ] Decide: show read count/badge in nav or just in feed?
- [ ] Decide: "Sign in with Prompt Goblins" button copy/placement
