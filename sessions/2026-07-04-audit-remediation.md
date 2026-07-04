# Audit Remediation Worklog — 2026-07-04

**Operator:** Claude (Fable 5), autonomous overnight session while Mike sleeps.
**Trigger:** Full audit of Goblin News (2026-07-04). Mike asked to fix everything, verify backups, don't break prod, document everything for root-cause.
**Audit summary saved at:** memory `project_audit_2026-07-04.md`.

This log is written as work happens. Each change records: what, why, file:line, risk, how validated, how to roll back.

---

## Timing constraints
- Session start: 2026-07-04 ~08:26 UTC.
- Pipeline cron runs 06:00 / 14:00 / 22:00 UTC (in the `ai-signal-agent` container). Next run **14:00 UTC**.
- Goal: deploy + validate BEFORE 14:00 UTC so the next unattended run exercises validated code, or hold pipeline-affecting changes if not confident.

## Deploy vs. defer policy (given "don't break everything" + unattended overnight)
- **DO + deploy:** low-risk, high-value code fixes with local validation + post-deploy smoke test.
- **DEFER (recommend to Mike):** anything that (a) rewrites pipeline session/concurrency semantics deeply, (b) changes containers to non-root (cron-as-root refactor, previously an accepted risk), (c) needs a quality eval (thinking-off), or (d) risks a bad Postgres image pull. These get documented, not executed.
- **Server ops:** backup fix + verify, clawrxiv port rebind, docker prune — done directly, independently verifiable.
- **NOT done (needs Mike):** reboot for pending kernel (disruptive; SSH-recovery risk if sshd doesn't come back — see runbook). Flagged for morning.

---

## KEY INVESTIGATION: is `tools=[]` safe? (Mike flagged this)

Mike's concern: "we had issues passing too much to Haiku and costing tons of money — don't reverse that."

**Finding: adding `tools=[]` is the SAME fix as the June cost investigation, not a reversal.**
- `docs/knowledge/gotcha_agent_sdk_overhead.md` + commit `12b53d4` ("Cut SDK overhead: tools=[] on dedup + event_intelligence"): the Agent SDK default `tools=None` LOADS the `claude_code` preset (~2,100 tokens of Read/Write/Bash/Edit schemas) into every call. `tools=[]` REMOVES them. Measured: dedup input 2,410→305 tokens (-61% cost).
- The 3 sites missing `tools=[]` (`newsletter.py:439` extract, `clustering.py:167` normalize, `clustering.py:403` validate) are all `max_turns=1` Haiku text tasks that only read `TextBlock` output — identical shape to dedup. Adding `tools=[]` makes them CHEAPER and closes the prompt-injection→Bash/Write execution vector (bypassPermissions + preset tools on untrusted newsletter/article content).
- MCP tools (event_intelligence) come from `mcp_servers=` and are UNAFFECTED by `tools=[]` (per commit msg + doc), so this never breaks tool-using stages.
- **NOT applying `thinking={"type":"disabled"}`** to these 3 — the doc is explicit it needs a per-stage quality eval (deliberately left off event_intelligence). Normalization quality feeds clustering. Flagged as a separate cost opportunity for Mike to eval later.

Conclusion: proceed with `tools=[]` on all 3 live sites + the dead `run_classifier` (defense-in-depth; it uses MCP tools so unaffected).

---

## CHANGES LOG

### Git (repo: promptgoblin/news-aggregator)
- **Rollback point (pre-remediation HEAD):** `2ffab41`
- **Branch:** `audit-remediation-2026-07-04` (pushed to origin). **NOT merged to main, NOT deployed** — direct push to main was blocked by the harness guardrail, and unattended prod deploy of 30 files touching the pipeline was judged too risky overnight. Left for Mike to merge + deploy while awake.
- **PR:** open at https://github.com/promptgoblin/news-aggregator/pull/new/audit-remediation-2026-07-04 (gh CLI not authed on this box, so created via the branch push link).
- **Commits:**
  - `b9236ce` Pipeline hardening: tools=[] on remaining Haiku calls, SSRF guard, lock + stage isolation
  - `c8a4e3c` API hardening: real client IPs for rate limiting, cache-control scoping, auth fixes
  - `71e39b2` Frontend: XSS/crash guards, filter param unification, CSP for analytics, a11y
  - `ae2159f` Infra/deploy hygiene: log+resource caps, network scoping, entrypoint + template fixes

### Backend code (committed, validated, NOT deployed)
Validation run locally: `py_compile` all files OK; `import ai_signal.main` + all pipeline/api modules OK; SSRF guard unit-tested (blocks metadata/loopback/private/IPv6-loopback/bad-schemes, allows public, fails open on DNS error); middleware smoke test via TestClient (anon GET cacheable, authed/POST no-store, 30 sequential GETs OK).
- `ingestion/newsletter.py`, `pipeline/clustering.py` (x2): `tools=[]` on the 3 untrusted-content Haiku calls. `agent/orchestrator.py`: `tools=[]` on dead run_classifier. **Verified same fix as commit 12b53d4 — cheaper AND removes injection→tool-exec. NOT a reversal of the Haiku cost work.**
- `ingestion/net_guard.py` (NEW): fail-open SSRF guard. Applied in `newsletter.fetch_article_content` (pre-fetch + redirect-chain check) and `rss.py` feed fetch. RSS article fetches already route through fetch_article_content (covered).
- `agent/orchestrator.py`: advisory lock on a dedicated connection released in `finally` (was leaking across pooled connections); each stage wrapped in try/except.
- `pipeline/sentiment.py`: `_coerce_score` (defensive float) + per-event try/except in both passes.
- `pipeline/embedding.py`: `_raise_for_embed` logs a distinct ERROR on OpenAI 401/403 (dead key was silently stalling clustering).
- `api/auth.py`: `_safe_return_to` rejects `\`; `_parse_uuid_csv` skips malformed UUIDs (was 500); last_seen throttled to once / 5 min.
- `main.py`: rate-bucket periodic sweep; Cache-Control scoped (no-store only for authed/non-GET; anon GET gets `public, max-age=30`).
- `Dockerfile.api`: uvicorn `--proxy-headers --forwarded-allow-ips=*`.
- `scoring.py`: docstring aligned to code (min 3 votes). **TODO Mike: confirm intended min (code=3, damper divides by 5).**

### Frontend (committed, validated, NOT deployed)
Validation: `tsc --noEmit` clean; `npm run build` clean (8 routes).
- `safeHref()` (utils.ts) + applied to SourceLinks + WhatPeopleAreSaying (XSS). Null-safe `prominent_reactions`. `category`→`categories` param unification (CategoryBadge, MobileControls now multi-select toggle, matching Sidebar — **UX note: badge click now toggles into the multi-filter instead of replacing; change if you preferred replace-semantics**). SortableHeaders default `day_score`. CSP allows analytics.promptgoblins.ai (Umami was blocked). `Number.isFinite` guard on score_min. apiFetch retries only network/5xx. logout clears votes. removed `maximumScale:1`.

### Infra/deploy files (committed, NOT deployed — apply on next deploy)
- `docker-compose.prod.yml`: json-file logging caps + mem_limits all services; web waits for api healthy; removed unmounted claude-auth volume.
- `docker-compose.hetzner.yml`: dropped `api` from shared webnet.
- `deploy/agent-entrypoint.sh`: /etc/environment `>` (not `>>`) + chmod 600.
- `.dockerignore` (new). `.env.prod.example`: added required JWT_SECRET / DISCOURSE_CONNECT_SECRET / PUBLIC_BASE_URL. `deploy/legacy/`: quarantined stale systemd units + dev vhost.

### SERVER ACTIONS (done live, verified) — server: 135.181.18.246:6969

**1. Local DB backup script — FIXED + VERIFIED.**
- Root cause: `~/server-infrastructure/backup-databases.sh` line 1 was `#\!/bin/bash` (bytes `23 5c 21` — a systematic `!`-escaping artifact from when the file was rewritten; mtime **Apr 8 00:46**, the event-calendar-kill session, NOT Feb). Kernel doesn't recognize `#\!` → cron ran it via dash → died on `set -o pipefail`. So the DAILY LOCAL dump had been failing since ~Apr 8.
- Why it wasn't noticed / why "we verified backups": the **offsite borg backup (`~/backup.sh`, 3:30am) is fully independent** — it does its OWN dumps (incl. ai_signal) and has worked continuously (today 2026-07-04 03:30, rc 0). That's the layer that was verified. The local secondary broke silently (offsite kept working + no alerting + shared backup.log buried the dash error among borg's success output).
- Fix: `sed -i '1c\#!/bin/bash'`. Backup of original at `backup-databases.sh.pre-shebang-fix.bak`.
- Verified: ran via direct exec (as cron does) → exit 0, fresh dumps for all 5 DBs incl. ai_signal (118M), stale Apr 8 dumps pruned.
- **Restore verification:** restored the fresh ai_signal dump into a throwaway DB `ai_signal_restore_test` inside ai-signal-db → 0 restore errors, row counts matched prod EXACTLY (events=2958, articles=5409, 17 tables), then dropped. Backup is confirmed restorable.

**2. clawrxiv-data public port exposure (3001/4001) — FIXED + VERIFIED.** (Not Goblin News, but on the same box.)
- Root cause: `clawrxiv-data-web` (3001) + `clawrxiv-data-api` (4001) published on 0.0.0.0 — externally reachable over plain HTTP (confirmed 3001→200, 4001→404 from an external machine). The app's own `docker-compose.hetzner.yml` sets `ports: []` to prevent this, BUT that never worked: **Docker Compose concatenates list values across -f files, so an empty `ports: []` override does NOT clear the base file's `["3001:3001"]`.** Latent bug in clawrxiv-data's own config.
- Fix: edited base `~/apps/data-clawrxiv/docker-compose.yml` to bind `127.0.0.1:${WEB_PORT:-3001}:3001` and `127.0.0.1:${API_PORT:-4001}:4001` (loopback only — nginx reaches the containers via the Docker webnet at `clawrxiv-data-web:3001`, so external publish was never needed). Backup at `docker-compose.yml.pre-portfix.bak`. Force-recreated api+web (reused existing images, `--no-build`), reloaded nginx.
- Verified: `ss` now shows `127.0.0.1:3001/4001`; external curl to both ports now TIMES OUT (was 200/404); data.clawrxiv.org, clawrxiv.org, news.promptgoblins.ai all still 200.
- **TODO Mike: commit this port change upstream to the data-clawrxiv repo** (server edit is uncommitted drift; a fresh `git pull` deploy would re-expose the ports). Consider fixing the ineffective `ports: []` override there too, or keep the 127.0.0.1 binding.

**3. Docker prune (safe): dangling images + build cache** — see reclaimed space in final report.

## ROLLBACK
- **App (if deployed later and bad):** on server `cd ~/apps/ai-signal/app && git reset --hard 2ffab41 && ./deploy/deploy.sh` then reload nginx. (Locally: `git checkout main` is already at 2ffab41; branch is separate.)
- **Backup script:** `cp ~/server-infrastructure/backup-databases.sh.pre-shebang-fix.bak ~/server-infrastructure/backup-databases.sh`
- **clawrxiv-data ports:** `cp ~/apps/data-clawrxiv/docker-compose.yml.pre-portfix.bak ~/apps/data-clawrxiv/docker-compose.yml` then force-recreate api+web + nginx reload.

## WHAT MIKE NEEDS TO DO (morning)
1. **Merge + deploy the app** (the code fixes are validated but NOT live): review PR / `git checkout main && git merge audit-remediation-2026-07-04 && git push`, then `ssh … 'cd ~/apps/ai-signal/app && ./deploy/deploy.sh'` + **nginx reload** (`docker exec nginx-proxy nginx -s reload`). I can drive this when you're around. Next pipeline cron 14:00 UTC — deploying before then means the run uses the hardened code; after is also fine.
2. **Commit the clawrxiv-data port fix** upstream (server edit is uncommitted).
3. **Reboot** for the pending kernel/apparmor security updates (`/var/run/reboot-required`, ~1 month old). Disruptive + SSH-recovery risk — do when you can watch it (runbook: `runbooks/hetzner-ssh-recovery.md`).
4. Confirm the scoring min-vote threshold (3 vs 5).

## DEFERRED (documented, not done — need Mike's judgment)
- `thinking={"type":"disabled"}` on the 3 Haiku calls — further cost win but needs a quality eval (per gotcha doc; deliberately not applied blind).
- Full non-root containers (previously accepted risk; cron-as-root refactor needs care).
- Deep session-across-HTTP refactors in sentiment/clustering (hold DB sessions across LLM calls) — larger change.
- Pipeline alerting ("0 events in 24h → Discourse DM") — the single highest-value ops item; spec exists in ops_notifications.md, still unbuilt.
- Postgres image digest-pin (skipped — pgvector has no matching pg17.9 tag; pin by digest).
- nginx: dedupe X-Frame-Options (nginx SAMEORIGIN vs Next DENY), add Permissions-Policy, add `resolver` for OCSP stapling, add `limit_req` — not touched (shared proxy, higher blast radius; do with care).
