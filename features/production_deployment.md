# Feature: Production Deployment & Architecture

---
type: feature
status: in-progress
complexity: C3
tags: [infrastructure, docker, security]
depends_on: []
required_by: [discourse_integration, forum_auth, ops_notifications]
---

## User Intent

### Goal
Deploy AI Signal to news.promptgoblins.ai on the Hetzner server, with the agent pipeline isolated in its own container to limit blast radius from prompt injection or pipeline failures.

### Success Criteria
- news.promptgoblins.ai serves the frontend (Next.js)
- API (FastAPI) serves event data
- Agent pipeline runs on a cron (3x daily) in an isolated container
- Pipeline container has NO inbound network access — only outbound to Claude API, xAI API, RSS sources, Fastmail JMAP, and the database
- Claude Code OAuth token can be refreshed without rebuilding
- All services recover automatically on server reboot

### User Flow
1. User visits news.promptgoblins.ai
2. nginx-proxy routes to frontend container
3. Frontend fetches from API container
4. Pipeline runs 3x daily (cron), writes to shared DB
5. Mike refreshes OAuth token every ~6 months via utility script

## Status: In Progress
**Started**: 2026-03-09
**Last Updated**: 2026-03-10

## References
- Plan: [plan/plan_section_architecture.md]
- Server: mike@135.181.18.246:6969 — see ~/server-admin-notes.md
- Related: [features/ops_notifications.md]

## Implementation

### Approach
Four Docker containers on the existing Hetzner server (AMD Ryzen 7 3700X, 64GB RAM, 906GB disk — massive headroom). Connected via the `webnet` Docker network for nginx routing. A dedicated PostgreSQL 16 + pgvector container (separate from existing postgres instances for isolation). The agent pipeline container is network-isolated — it connects only to its own DB and has outbound-only internet for API calls. Claude Code runs inside the agent container, authenticated via OAuth token stored in a mounted volume.

### Container Architecture

```
Internet → Cloudflare → nginx-proxy (existing)
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               │
        ai-signal-web   ai-signal-api         │
        (Next.js SSR)   (FastAPI)             │
        port 3002       port 8001             │
              │               │               │
              └───────┬───────┘               │
                      ↓                       │
               ai-signal-db ←────── ai-signal-agent
               (PostgreSQL 16       (Pipeline + Claude Code)
                + pgvector)         NO inbound network
                                    Outbound: Claude API, xAI API,
                                              RSS, Fastmail JMAP,
                                              OpenAI Embeddings
                                    Cron: 6am, 2pm, 10pm UTC
```

### Key Components
- **ai-signal-web**: Next.js frontend (SSR mode, port 3002)
- **ai-signal-api**: FastAPI backend, serves event/tag/search endpoints (port 8001)
- **ai-signal-db**: PostgreSQL 16 + pgvector extension, localhost-only port
- **ai-signal-agent**: Isolated pipeline container with Claude Code installed

### Docker Networks
- `ai-signal-network` (internal): web ↔ api ↔ db (no external access)
- `server-infrastructure_webnet` (existing): web + api exposed to nginx-proxy
- `ai-signal-agent-network` (internal): agent ↔ db only
- Agent container also needs outbound internet (for Claude API, xAI API, RSS, Fastmail JMAP, OpenAI embeddings) — use default bridge for outbound, but no ports exposed

### Key Files
- `docker-compose.yml` — All 4 services
- `docker-compose.hetzner.yml` — Hetzner overrides (webnet, localhost ports)
- `Dockerfile.web` — Next.js frontend
- `Dockerfile.api` — FastAPI backend
- `Dockerfile.agent` — Pipeline + Claude Code + cron
- `deploy/nginx/news.promptgoblins.ai.conf` — nginx vhost
- `scripts/refresh-claude-auth.sh` — OAuth token refresh utility

### Agent Container Isolation

The agent container is the highest-risk component — it ingests untrusted content from RSS feeds and newsletters, which creates prompt injection risk. Isolation strategy:

1. **Network isolation**: Agent connects ONLY to ai-signal-db. No access to other containers, no access to web/api containers, no access to other databases on the server.
2. **No inbound ports**: No EXPOSE, no port bindings. Container only makes outbound connections.
3. **Separate Docker network**: `ai-signal-agent-network` connects only agent ↔ db. Agent also on default bridge for outbound internet.
4. **DB-scoped permissions**: Agent's DB user has access ONLY to the ai-signal database. Even if prompt injection causes unexpected SQL, it cannot reach other databases.
5. **No Docker socket**: Never mounted. Agent cannot control other containers.
6. **Budget guards**: Pipeline has per-stage budget limits ($5 classifier, $50 event intel, $0.10 newsletter). Agent SDK enforces these.
7. **Permission mode**: Agent SDK runs with `bypassPermissions` but only has MCP tools scoped to pipeline operations (no shell access, no file write outside DB).

```dockerfile
# Dockerfile.agent
FROM python:3.12-slim

# Install Claude Code CLI (for Agent SDK auth)
RUN curl -fsSL https://claude.ai/install.sh | sh

# Install project dependencies
COPY pyproject.toml .
RUN pip install -e .

# Cron: 3x daily
COPY deploy/cron/pipeline-cron /etc/cron.d/pipeline-cron

# OAuth token volume mount point
VOLUME /home/agent/.claude

# No EXPOSE — no inbound ports
CMD ["cron", "-f"]
```

### OAuth Token Management
- Token stored in a Docker volume (`ai-signal-claude-auth`)
- Mounted to agent container at `/home/agent/.claude`
- `refresh-claude-auth.sh` runs `claude` interactively to get login URL
- Mike opens URL in browser, pastes code back
- Token persists in volume across container rebuilds
- Ops notification bot reminds Mike at 60/30/15/7/daily before expiry

### Pipeline Schedule
- 3x daily: 6:00 UTC, 14:00 UTC, 22:00 UTC
- Each run: ingest → cluster → event intelligence → dedup → sentiment
- Pipeline stages:
  1. **Ingest**: Poll RSS feeds + Fastmail JMAP newsletters, resolve tracking URLs
  2. **Cluster**: HyDE normalization (Haiku) → embed → cosine similarity graph
  3. **Event Intelligence**: Claude Agent SDK (Sonnet) with subagents (Distiller, Scorer, Tagger, QC, Editor)
  4. **Dedup**: pgvector embedding similarity (auto-merge >0.85, Haiku review 0.70-0.85)
  5. **Sentiment**: Grok via xAI Responses API with x_search (events scored >= 8)
- Cost target: ~$8-15 per run, ~$25-45/day, ~$750-1350/month
- Budget guard: per-stage limits enforced by Agent SDK

### Rate Limit Handling
- Detect hourly limit responses from Claude API
- Exponential backoff with jitter (1min, 2min, 4min, max 15min)
- If limit persists >30min, abort run and notify via forum bot
- Log all rate limit hits for pattern analysis

## Dependencies

### External Services
- Cloudflare: DNS + CDN for news.promptgoblins.ai
- Let's Encrypt: SSL cert via certbot (same as other sites on server)
- Claude API: Via Claude Code subscription OAuth (Agent SDK)
- xAI API: Grok sentiment analysis via Responses API with x_search
- Fastmail JMAP: Newsletter ingestion (replaces Gmail API)
- OpenAI API: Embeddings (text-embedding-3-small)

## Edge Cases & Considerations

### Security — Prompt Injection Threat Model
The pipeline ingests content from 27+ external sources (RSS feeds, newsletters, HN). Any of these could contain adversarial content designed to manipulate the LLM pipeline. Mitigations:

- **Agent container isolation**: Cannot reach other containers or databases. Even a full compromise of the agent process can only affect ai-signal-db.
- **MCP tool scoping**: Agent has access to pipeline-specific tools only (get_articles, create_event, vector_search, etc.). No shell, no filesystem, no network tools.
- **Budget limits**: Each pipeline stage has a hard USD cap. An injection that causes runaway API calls will hit the budget guard.
- **Structural guardrails**: `create_event` validates all fields (category from fixed list, score 1-10, min 3 tier1 bullets, etc.). Injected content that produces structurally invalid output is rejected.
- **Content sanitization**: All LLM output sanitized before DB insert (strip null bytes, validate UTF-8).
- **No privilege escalation path**: Agent SDK runs with `bypassPermissions` for its own tools, but has no access to host system, Docker socket, or other services.

### Other Security
- **DB credentials**: Stored in `.env.prod` (chmod 600), mounted as env vars
- **Claude token**: In a named volume, not in the image
- **No Docker socket**: Never mounted into any container
- **API keys**: xAI, OpenAI, Fastmail tokens in `.env.prod` only

### Handled
- Server reboot: `restart: unless-stopped` on all containers
- Discourse network disconnect after rebuild: Same `ensure-webnet.sh` pattern
- Pipeline failure: Ops bot notifies Mike on forum
- Token expiry: Progressive reminders via forum bot (60/30/15/7/daily)

### Limitations
- Claude subscription tier determines rate limits — monitor and adjust schedule
- OAuth token requires manual browser interaction (can't fully automate)
- Pipeline runs are sequential (not parallelized across containers)

## Deploy Process

Following the established pattern from clawrXiv / data.clawrXiv:

```bash
# On server:
cd /home/mike/apps/ai-signal
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.hetzner.yml --env-file .env.prod up -d --build
```

Deploy key: `~/.ssh/deploy_ai_signal` (read-only, scoped to repo)

## Definition of Done

### Automated Checks
- [ ] `docker compose -f docker-compose.yml -f docker-compose.hetzner.yml config` validates
- [ ] `curl -s https://news.promptgoblins.ai/api/health` returns 200
- [ ] `docker exec ai-signal-agent python -m agent.orchestrator` succeeds (full pipeline)
- [ ] `docker inspect ai-signal-agent --format '{{.NetworkSettings.Ports}}'` shows no exposed ports

### Acceptance Criteria
- [ ] news.promptgoblins.ai loads frontend
- [ ] API returns events at /api/events
- [ ] Pipeline runs successfully on cron (check logs)
- [ ] Agent container cannot be reached from other containers (network test)
- [ ] OAuth token refresh utility works
- [ ] SSL cert auto-renews

## Outstanding
- [ ] Create GitHub repo + deploy key for server
- [ ] Set up Cloudflare DNS for news.promptgoblins.ai
- [ ] Build Docker files (docker-compose.yml, Dockerfiles, hetzner override)
- [ ] Create nginx vhost config for news.promptgoblins.ai
- [ ] Create .env.prod template
- [ ] Initial deploy + first pipeline run on production
- [ ] Determine exact Claude subscription tier ($20 vs $100)
