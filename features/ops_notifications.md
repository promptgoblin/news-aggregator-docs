# Feature: Ops Notifications via Forum Bot

---
type: feature
status: planning
complexity: C1
tags: [ops, discourse, monitoring]
depends_on: [production_deployment]
required_by: []
---

## User Intent

### Goal
Use the Goblin News bot user on Discourse to notify Mike about operational issues — OAuth token expiry, pipeline failures, cost warnings, rate limits. No separate monitoring stack needed; notifications arrive as forum DMs.

### Success Criteria
- Mike gets a forum DM when the pipeline fails
- Progressive OAuth token expiry reminders (60/30/15/7/daily)
- Cost warnings when approaching budget limit
- Rate limit alerts with pattern summary
- All notifications via the same "Goblin News" bot user used for Discuss threads

### User Flow
1. Pipeline runs, encounters issue (or cron checks token expiry)
2. System calls Discourse API to send DM to Mike (user id: 1)
3. Mike sees notification on forum (badge, email digest, etc.)
4. Mike takes action (refresh token, check logs, adjust budget)

## Status: Planning
**Started**: 2026-03-09
**Last Updated**: 2026-03-09

## Implementation

### Approach
A lightweight notification module that sends DMs via the Discourse API. Called from the pipeline orchestrator on errors, and from a daily cron that checks token expiry and cost tracking. Uses the same bot API key as the Discuss feature.

### Notification Types

| Type | Trigger | Urgency | Frequency |
|------|---------|---------|-----------|
| Pipeline failure | Any unhandled exception in orchestrator | High | Per run |
| OAuth token expiry | Days until expiry: 60, 30, 15, 7, then daily | Progressive | Daily cron check |
| Cost warning | Run cost > 80% of daily budget | Medium | Per run |
| Rate limit hit | >3 rate limits in a single run | Medium | Per run |
| Ingestion failure | Source fails 3+ consecutive polls | Low | Daily digest |
| Model update | Claude Code version changes | Info | On detection |

### Key Components
- **`notify_forum(subject, body, target_user_id=1)`** — sends DM via Discourse API
- **`check_token_expiry()`** — reads OAuth token metadata, calculates days remaining
- **`check_cost_budget()`** — reads pipeline_logs, sums costs for current billing period
- **Daily cron job** — runs checks independent of pipeline

### Discourse API Call
```python
async def notify_forum(subject: str, body: str, target_user_id: int = 1):
    """Send a DM to Mike via the Goblin News bot on Discourse."""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://promptgoblins.ai/posts.json",
            headers={"Api-Key": DISCOURSE_BOT_API_KEY, "Api-Username": "ai-signal"},
            json={
                "title": subject,
                "raw": body,
                "target_recipients": "mike",
                "archetype": "private_message",
            },
        )
```

### OAuth Token Expiry Tracking
- When token is refreshed, write expiry date to `/home/agent/.claude/token_expiry`
- Daily cron reads this file, calculates days remaining
- Sends DM at 60, 30, 15, 7, then daily thresholds
- Message includes the command to run for refresh:
  `"Run: ssh -p 6969 mike@server 'docker exec -it ai-signal-agent ./scripts/refresh-claude-auth.sh'"`

### Claude Code Version Tracking
- On each pipeline run, check `claude --version`
- Compare to stored version in DB or file
- If changed, send info DM: "Claude Code updated from X to Y. Consider running a test pipeline to verify output quality."

## Edge Cases & Considerations

### Handled
- **Discourse down**: Log notification locally, retry on next cron run
- **Spam prevention**: Dedup notifications — don't send same alert type more than once per day
- **Bot user doesn't exist yet**: Fail gracefully, log error

### Security
- Bot API key scoped to minimum permissions (create PM only)
- No sensitive data in notification body (no tokens, no passwords)
- Rate limit our own notification sending (max 10 DMs per day)

## Definition of Done

### Acceptance Criteria
- [ ] Pipeline failure triggers DM to Mike on forum
- [ ] OAuth expiry reminders arrive at correct intervals
- [ ] Cost warning fires when budget threshold crossed
- [ ] Notifications are deduped (no spam)

## Outstanding
- [ ] Create "Goblin News" bot user on Discourse (shared with discuss feature)
- [ ] Generate scoped API key for bot
- [ ] Decide: should notifications also go to a public "ops" topic for transparency?

---

## Add-on: Invariant check integration (deferred — added 2026-04-08)

### Context
`scripts/check_invariants.py` (committed 9bb1a37) runs post-cron data-integrity
assertions and exits non-zero on failure with row-level detail. Currently
runs manually only — nothing consumes its output. Three invariants caught
real bugs on 2026-04-07 retroactively:
- Ghost cluster re-scoring leak
- `create_event` orphaned cluster siblings
- Status/event_id drift

The invariant check should be wired into the cron chain and should notify
Mike on any failure. Discourse is the short-term destination until Goblin
Ops lands.

### Why this is a separate line item
Mike's note (2026-04-08): setting up a new Discourse bot user takes real
time — create user, create private category, create API key with scoped
permissions, add env vars to `.env.prod`, store credentials in
`forum-management/.env`. This is ~30 min of clicky work on the forum side
plus code changes. Not doing it ad-hoc; wants to batch it.

### Setup checklist (forum side)
- [ ] Decide: **reuse Goblin News bot user** (already exists, used by
      discuss feature) OR **create a new `goblin-ops` user** for clean
      separation between user-facing forum activity and admin alerts.
      Recommendation: separate user. Makes it easier to mute one without
      the other and avoids alert spam in the main bot's DM thread.
- [ ] If separate user: create account `goblin-ops@promptgoblins.ai`,
      username `goblin-ops`, trust level 4 (leader) or admin.
- [ ] Create a private Discourse category `ops-alerts`, visible only to
      admins. All invariant failures post here as new topics; Mike gets
      notifications via normal Discourse mechanisms (email, web, mobile).
- [ ] Generate a scoped API key for the bot user with minimum permissions:
      create topic in `ops-alerts` category only. Store in
      `forum-management/.env` + server `.env.prod` as `DISCOURSE_OPS_API_KEY`
      and `DISCOURSE_OPS_USERNAME`.
- [ ] Decide posting behavior: new topic per failure, or daily digest
      topic that gets new posts appended. Recommendation: new topic per
      failure for visibility; dedup via a "last-alert hash" check so we
      don't spam the same failure twice in 24h.

### Setup checklist (code side)
- [ ] Add `DISCOURSE_OPS_API_KEY` / `DISCOURSE_OPS_USERNAME` /
      `DISCOURSE_OPS_CATEGORY_ID` to `ai_signal/config.py` settings.
- [ ] Add a `post_to_ops_category()` helper in a new
      `src/ai_signal/alerting.py` module. Should take title + body,
      POST to Discourse, return topic URL or None on failure.
- [ ] Modify `scripts/check_invariants.py`: on any failure, after
      printing to stdout, call `post_to_ops_category()` with a formatted
      body listing the failing invariants and sample rows. Wrap in
      try/except — failing to alert should NOT change the script's
      exit code or block the cron.
- [ ] Add dedup: write the last-alert hash to a small file
      (`/tmp/goblin-ops-last-alert.txt` or a DB row) and skip posting if
      the same hash was posted in the last 24h.
- [ ] Append `; python -m scripts.check_invariants` to the news
      pipeline cron line in `deploy/cron/pipeline-cron` so the check
      runs after every pipeline run. Use `;` not `&&` — the check
      should run even if the orchestrator failed, because that's
      exactly when we most want to see the DB state.

### When to do this
Bank until Mike has 30 min of forum-setup time available. Low urgency
given the invariant check is a regression-catcher, not a blast radius
multiplier — the worst case today is "one of the fixed bugs silently
comes back and goes unnoticed for 24–48h instead of being alerted."

### Migration path to Goblin Ops
When Goblin Ops ships, swap `post_to_ops_category()` for
`goblin_ops.post_alert()` (webhook or SDK call). The dedup logic,
invariant check itself, and cron integration stay the same — only the
transport changes.
