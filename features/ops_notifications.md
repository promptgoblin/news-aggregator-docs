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
