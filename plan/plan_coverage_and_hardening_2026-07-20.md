# Goal: 90%+ coverage of top AI stories + full hardening pass

**Started:** 2026-07-20 · **Owner:** Mike (with Claude) · **Status:** in progress — P0/P1/P3 done, P2 partial

## Progress log

**2026-07-20 (session 1):**
- `[x]` **P0** — no-op: audit branch had zero diff vs main (everything already cherry-picked/merged). Branch can be deleted.
- `[x]` **P1** — diagnosed. KEY FINDING: pipeline caught more than the audit suggested (Kimi K3 event score 9 on 07-16, Apple-OpenAI score 9 on 07-10, Moonshot capacity-pause score 8.05 — the audit's 48h window and pre-2pm-run timing made these look missed). TRUE gaps = 4 classes: (1) enterprise/finance deals, (2) regional policy (Australia), (3) HN/Twitter-forward research (Jacobian), (4) Chinese domestic press (Xiaomi). No `gotcha_` doc written — this progress-log entry is the record.
- `[x]` **P3 Grok sweep** — SHIPPED + verified live (commits `029bb27`, `ad7cbe7` in app repo). Runs in ingest_all() every pipeline cycle. First live run: 7 stories, several true gap-fills (Moonshot IPO, Infinity AI $15M). REAL COST: ~$0.01/call (2 calls = $0.02 total) → ~$1/mo at 3/day, far under the $8/mo estimate. Guardrails live: $0.50/day hard cap (skips call), $0.20/call WARNING log, full cost logging to llm_usage_log pipeline='grok_sweep' (visible /admin/usage). Parser skips X-profile-only URLs (keeps /status/ posts), YouTube, bare domains, tag/category/search pages.
- `[x]` **P2.3 Regional Google News** — AU/UK/IN/JP feeds seeded (part of `ad7cbe7`), active from next pipeline run.
- Next session: start at **P2.1 (HN Algolia)** — see "NEXT SESSION" below.

## EDITORIAL QUALITY BAR (Mike, 2026-07-21 — applies to ALL source work)

The goal is catching **major stories people expect us to have**, not maximum
article volume. A story earns ingestion attention if it's meaningful at the
**industry level** to someone keeping up with AI generally:

- **YES:** frontier-lab moves, major model/product releases, national or
  bloc-level policy (EU AI Act, Australia regs, UK AI Minister), major-company
  deals and funding, notable research, significant market events.
- **NO:** local/regional business deals with no industry implications, vendor
  PR ("X helps businesses scale with AI"), local-government adoption stories,
  university program announcements, surveys of local sentiment.

Design consequence: prefer **curated/validated sources** (TechMeme editorial,
HN points threshold, primary lab blogs) over broad geographic/keyword sweeps.
When adding any source, ask: "what fraction of this feed clears the bar?"
If <50%, narrow the query or skip the source — the scorer is the last line
of defense, not the first.

Candidate (deferred per prompt-tuning strategy — collect data first): add an
explicit "industry-level significance" line to the scorer guidance. Revisit
when admin score-adjustment data accumulates.

## Model-review notes (Fable pass, 2026-07-21)

Plan reviewed post-upgrade; adjustments made or noted:

1. `[x]` **P2.3 regional feeds REPLACED** (commit `8593966`) — overnight data
   showed 83 articles/day of noise; geographic targeting does little for an
   English `q=AI` search. Now one focused **Google News AI Policy** query
   (validated clean). AU/UK/IN/JP slugs deactivated.
2. **P2 reordered by signal-to-noise** (see below) — TechMeme first (editorially
   curated = exactly the quality bar), Reddit last (noisiest).
3. **P2.2 Reddit:** unauthenticated `.json` + browser UA got rate-limited on 3
   of 5 subs during the audit. Register a free Reddit OAuth app (100 QPM) or
   use the `.rss` endpoints; don't rely on bare JSON.
4. **P2.5 lab scrape:** check for undocumented RSS before scraping — Meta AI
   has had `ai.meta.com/blog/rss/`; Mistral may expose a feed. scrape.do only
   where truly feedless (Anthropic, xAI).
5. **P2.6 finance:** Bloomberg has no free RSS; The Information is paywalled.
   Don't burn time — TechMeme carries both outlets' headlines (that's the
   proxy). Realistic direct adds: CNBC, NYT Tech, Reuters tech.
6. **P5 addition:** include **Grok cost-cap trips** in the Discourse DM alerts.
   A cap trip currently only WARNs into pipeline.log — the exact silent-signal
   antipattern P4 fixes. Also surface `pipeline_runs` + daily Grok spend on
   `/admin/health`.
7. Grok sweep 24h check: 3 calls, $0.027 — guardrails working, projection
   ~$1/mo (not $8).

**Revised P2 order:** TechMeme (P2.4) → HN Algolia (P2.1) → lab scrape (P2.5)
→ finance RSS (P2.6) → Reddit (P2.2). Policy feed (P2.3 replacement) done.

## INCIDENT (2026-07-21): numpy transitive-dep loss killed clustering for 16h

The 07-20 ~08:00 deploy rebuilt the agent image without numpy (never a direct
dep); clustering ImportError'd every run, swallowed by stage isolation —
pipeline "completed" with zero events while 74 articles piled up pending.
Fixed: numpy pinned (`4026a98`), backlog re-run, deploy skill now mandates an
agent import smoke test + no-deploy-during-pipeline-windows check. Full
writeup: `knowledge/gotcha_transitive_dep_silent_stage_failure.md`.

**Plan impact:** this is the SECOND incident the P5 "0 events in 24h" DM alert
would have caught same-day. **P5 is promoted to the front of the next session's
queue — build alert rule 1 BEFORE continuing P2 sources.** A pipeline that
silently dies makes every coverage improvement moot.

## NEXT SESSION — start here

1. Read this doc top to bottom.
2. **Verify yesterday's work before building:** check regional Google News feeds produced articles (`SELECT s.name, COUNT(*) FROM articles a JOIN sources s ON a.source_id=s.id WHERE s.slug LIKE 'google-news-ai-%' AND a.created_at > NOW() - INTERVAL '1 day' GROUP BY 1;`) and Grok sweep cost stayed sane (`SELECT COUNT(*), SUM(cost_usd) FROM llm_usage_log WHERE pipeline='grok_sweep' AND created_at > NOW() - INTERVAL '1 day';` — expect ≤3 calls, ≤$0.30).
3. **FIRST: P5 alert rule 1 ("0 events in 24h → Discourse DM")** — promoted ahead of everything after the 07-21 numpy incident (see INCIDENT section). Then the revised P2 order: **P2.4 TechMeme → P2.1 HN Algolia → P2.5 lab HTML scrape → P2.6 finance RSS → P2.2 Reddit**. Each: implement, test locally, commit, deploy via deploy skill (remember nginx reload + agent import smoke test), verify articles land. Hold every new source to the EDITORIAL QUALITY BAR section.
4. After P2 complete: P4 (silent-drop) → P5 (alerts) in one session; P6+P7 (security+reliability) in another; P8 (infra) last.
5. Deploy skill: `.claude/skills/deploy-goblin-news/SKILL.md`. **Commit to `main`** (not the audit branch — it's stale/deletable). Check `git branch --show-current` before committing.

> Runnable plan (/goal) that closes the coverage gap surfaced in the 2026-07-20
> source audit AND ships the hardening backlog from the 2026-07-04 audit +
> the silent-drop lessons from the May 9-10 incident. Ordered so each phase
> unblocks or de-risks the next.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## Success criteria (how we know this goal is done)

- **Coverage:** the next 48h audit (same subagent panel) finds ≤2 tier-1/2 misses. Grok daily-sweep runs consistently and injects new events. All 4 RSS-less lab blogs (Anthropic, Meta AI, Mistral, xAI) produce at least one event per week when they publish.
- **Silent-drop visibility:** an active source going to 0 articles for 7 days triggers a Discourse DM. `pipeline_runs` table exists with start/end/duration/events_created/errors per run. `Skipping ...` log lines are INFO with resolved domain.
- **Security:** four `tools=[]` fixes deployed. Agent container runs non-root. `/etc/environment` dump removed from `agent-entrypoint.sh`. Private-IP/non-http SSRF blocked. Injection preamble added to event-intel runbook.
- **Reliability:** one pipeline stage failure no longer aborts downstream stages. Advisory lock always released. DB sessions never held across long HTTP calls. Embedding failures surface an error, not `None`.
- **Infra hygiene:** `/var/log/pipeline.log` rotated + persisted across container restarts. Docker cache reclaim scheduled. pgvector image pinned to a minor. Kernel + apparmor reboot completed.

---

## Cost budget

Additional monthly ops cost from this goal (all-in, worst case):
- Grok daily x_search sweep, 3 runs/day: **~$8/mo** (verified at $0.09/call)
- scrape.do calls for RSS-less lab pages (Anthropic/Meta/Mistral/xAI, daily): **~$1-3/mo**
- Reddit, HN Algolia, Regional Google News, TechMeme, Bloomberg/Reuters/CNBC free RSS: **$0**

**Total: ~$10-15/mo incremental.**

---

## Dependency map

```
P0 SHIP PENDING BRANCH ──► unblocks CSP (Umami), tools=[], TZ fix,
                                        rate-limit proxy-headers, WhatPeopleAreSaying guard
     │
     ▼
P1 DIAGNOSE LEAKS ──► must run BEFORE adding sources
     (why did TechCrunch coverage of Kimi K3 / Apple-OpenAI not surface?)
     │
     ▼
P2 COVERAGE — FREE ──┐
     HN Algolia, Reddit, Regional GNews, TechMeme, lab HTML scrape,
     Bloomberg/Reuters/CNBC free RSS
                     │
P3 COVERAGE — GROK ──┤  (cheap, high signal; safe to do in parallel with P2)
     ~$8/mo daily 3× sweep, injects trending X + web stories as pseudo-articles
                     │
                     ▼
P4 SILENT-DROP REMEDIATION ──► needed to KEEP coverage healthy
     INFO logs on drop paths, persist pipeline.log, pipeline_runs table
     │
     ▼
P5 MONITORING + ALERTING ──► catches future decay
     "0 events in 24h" + "source zero-7d" → Discourse DM
     │
     ▼
P6 SECURITY HARDENING ──┐
     Non-root agent, stop env dump, SSRF block, injection preamble
                         │
P7 RELIABILITY ──────────┤  (P6/P7 can run in parallel)
     Stage isolation, lock leak, session-across-HTTP, embedding-swallow
                         │
                         ▼
P8 INFRA HYGIENE ──► log rotation, docker prune, resource limits, pgvector pin, reboot
```

---

## P0. Ship the pending branch  `[ ]`

**Outcome:** `audit-remediation-2026-07-04` merged to `main`, deployed, verified live. Unblocks CSP for Umami, ships the four `tools=[]` fixes, deploys rate-limit proxy-headers fix, Umami CSP, WhatPeopleAreSaying guard, SortableHeaders default, `category` param unification.

**Note (2026-07-20):** the daily-top TZ fix (`4e5de44`) and UMAMI build-args (`81439ce`/`62efabd`) are already cherry-picked onto main. The remaining audit branch is still needed for the tools=[], rate-limit, WhatPeopleAreSaying, category-param, and Umami-CSP fixes.

**Tasks:**
- `[ ]` Review branch diff vs main: `git diff main..audit-remediation-2026-07-04`
- `[ ]` Resolve any merge conflicts with cherry-picks (should be trivial)
- `[ ]` Merge to main + push
- `[ ]` Deploy via skill (`./deploy/deploy.sh` on server + `docker exec nginx-proxy nginx -s reload`)
- `[ ]` Verify: 200 on site, `/api/health`, no CSP console errors, Umami showing pageviews

---

## P1. Diagnose current leaks  `[ ]`   (30-60 min)

**Outcome:** we know whether stories are missing because (a) source not in list, (b) source ingested but classifier dropped, (c) source URL broken. Different causes need different fixes.

**Tasks:**
- `[ ]` For each of the top 5 misses (Kimi K3, Apple v OpenAI, Anthropic-Meta $10B, Australia AI regs, Big Tech AI capex selloff): query the `articles` table for the last 7 days on likely source domains (techcrunch.com, bloomberg.com). Did we ingest an article and drop it? Or never see it?
- `[ ]` If ingested but not surfaced: look at `pipeline_logs` for that article — was it scored low, classified non-AI, deduped away?
- `[ ]` Document findings in `docs/knowledge/gotcha_2026-07-20-coverage-audit.md`

---

## P2. Coverage — free wins  `[ ]`

### 2.1 HN Algolia API  `[ ]`   (replaces flaky hnrss.org)
- `[ ]` Add ingest adapter using `https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=points>50&query=AI` (with variants for OpenAI, Anthropic, Claude, LLM, etc.)
- `[ ]` Deactivate the two hnrss.org sources; port their queries
- `[ ]` Verify: catches HN posts within the poll window with ≥50 points

### 2.2 Reddit ingest  `[ ]`
- `[ ]` New adapter using `https://www.reddit.com/r/{sub}/top.json?t=day` (with browser UA)
- `[ ]` Seed subs: r/LocalLLaMA, r/singularity, r/artificial, r/OpenAI, r/ClaudeAI, r/machinelearning
- `[ ]` Threshold: score ≥ 100 or comments ≥ 30 to avoid low-signal
- `[ ]` Verify: catches the Jacobian Conjecture / HuggingFace-incident class of posts

### 2.3 Regional Google News feeds  `[ ]`
- `[ ]` Add `https://news.google.com/rss/search?q=%22artificial+intelligence%22&hl=en-{cc}&gl={cc}` for AU, JP, IN, UK
- `[ ]` Score down if same story exists from primary domestic source (avoid dupes)
- `[ ]` Verify: catches the Australia AI regs class of story

### 2.4 TechMeme RSS  `[ ]`
- `[ ]` Add https://www.techmeme.com/feed.xml as an aggregator source (source_type=aggregator, low trust)
- `[ ]` Filter to AI-adjacent headlines (classifier already handles this)

### 2.5 HTML-scrape RSS-less lab news pages  `[ ]`   (uses existing scrape.do)
- `[ ]` New adapter: fetch each lab's news/blog HTML via scrape.do, extract post links + dates, dedupe, ingest as articles
- `[ ]` Sources: https://www.anthropic.com/news, https://ai.meta.com/blog/, https://mistral.ai/news/, https://x.ai/news
- `[ ]` Poll daily (news posts are low-volume)
- `[ ]` Verify: catches Anthropic's next `<h1>` release within 24h

### 2.6 Bloomberg / Reuters / CNBC / NYT free RSS  `[ ]`
- `[ ]` Add feeds where available (Reuters tech, NYT tech, CNBC Tech, Bloomberg via TechMeme mirror)
- `[ ]` Where paywalled with visible headline+dek only, still ingest headline for coverage awareness

---

## P3. Coverage — Grok daily sweep  `[ ]`   (~$8/mo)

**Outcome:** 3× daily (aligned with pipeline cron 06:00 / 14:00 / 22:00 UTC), Grok queries "top 10 AI news stories in the last 8 hours with source URLs" via web+x_search and injects each returned story as a pseudo-article for the pipeline to score/cluster.

**Tasks:**
- `[ ]` New adapter `ingestion/grok_sweep.py` (source_type=aggregator, name "Grok Sweep")
- `[ ]` Simple prompt: `"Search X and the web for the top 10 AI news stories from the last 8 hours. Return: headline | canonical source URL | 1-line summary. Numbered list only, no commentary."`
- `[ ]` Model: `grok-4-fast-reasoning`, `tools: [{type: "x_search"}, {type: "web_search"}]`
- `[ ]` Parse output, extract (headline, url, summary), dedupe against existing articles by URL, insert into articles table with source_type=aggregator
- `[ ]` Cap: 10 stories per call. Cost per call verified ~$0.09.
- `[ ]` Log token counts + cost to `llm_usage_log` per run
- `[ ]` Verify: over 3 days, catches at least one story not otherwise ingested

---

## P4. Silent-drop remediation  `[ ]`

**Outcome:** future decay is visible in logs and queryable in the DB, not hidden at DEBUG level or lost to container restart.

**Tasks:**
- `[ ]` Upgrade these DEBUG log lines to INFO with the resolved domain:
  - `Skipping bare domain URL ...` (newsletter.py)
  - `Skipping newsletter story (no quality content) ...` (newsletter.py)
  - `Could not fetch article from: ...` (newsletter.py)
  - `Anti-bot %d on %s — falling through to scrape.do` (newsletter.py)
- `[ ]` Persist `/var/log/pipeline.log` — mount `~/apps/ai-signal/logs/` into the agent container, add logrotate
- `[ ]` New table `pipeline_runs`: id, started_at, ended_at, duration_s, events_created, articles_ingested, errors_json. Populated by orchestrator.
- `[ ]` Migration + orchestrator wire-up

---

## P5. Monitoring + alerting  `[ ]`

**Outcome:** Discourse DM to Mike when things break. Uses the existing Goblin News bot creds already used for "Discuss on Forum".

**Tasks:**
- `[ ]` Build the alert-checker daily cron (`agent/alerts.py`)
- `[ ]` Alert rule 1: **0 events in 24h** → DM
- `[ ]` Alert rule 2: **any active source with 0 articles in 7d** → weekly DM digest
- `[ ]` Alert rule 3: **>5 rate_limit errors in a single run** → per-run DM
- `[ ]` Alert rule 4: **any newsletter arriving with `No matching source for sender` >3× in a week** → weekly DM digest
- `[ ]` Alert rule 5: **Claude Sonnet weekly usage >80%** → DM (avoids event-calendar-style quota starvation)
- `[ ]` Verify: manually break something (deactivate a source) and confirm the DM lands

**Ref:** `features/ops_notifications.md`, `project_monitoring_needed.md`

---

## P6. Security hardening  `[ ]`

**Outcome:** blast radius of untrusted-content processing reduced. Prompt-injection can no longer hit Bash/Write/Edit.

**Tasks (many already on the audit branch — verify shipped after P0):**
- `[ ]` **Non-root agent container** — add `USER agent` to `Dockerfile.agent`, adjust file perms
- `[ ]` **Stop /etc/environment secret dump** — `deploy/agent-entrypoint.sh:4`, replace with selective export of only what cron needs
- `[ ]` **SSRF block** in `fetch_article_content` and RSS: reject non-http(s) schemes, private-IP ranges (RFC1918, link-local, IPv6 unique-local)
- `[ ]` **Injection preamble** in `agent/runbooks.py` for event-intel (has `publish_to_discourse`/`update_event` — bounded but still worth telling the agent to treat article text as untrusted)
- `[ ]` **Open-redirect** `_safe_return_to` (`auth.py:96`) — also block `/\\` in addition to `//`
- `[ ]` **Add `iss`/`aud` to JWT** — deferred as accepted risk; revisit only if we ever add a second service
- `[ ]` **Rebind clawrxiv-data 3001/4001 to 127.0.0.1** — server-side, coordinate with clawrxiv upstream fix

---

## P7. Reliability  `[ ]`

**Outcome:** one bad stage doesn't kill downstream; long HTTP calls don't hold DB row locks; silent failures surface.

**Tasks:**
- `[ ]` **Stage isolation** — wrap each pipeline stage in the orchestrator with try/except; log stage error to `pipeline_runs`; continue to next stage instead of aborting (avoids sentiment `float()` crash killing everything)
- `[ ]` **Advisory lock try/finally** — `orchestrator.py:44-73`, ensure `pg_advisory_unlock` runs even on exception
- `[ ]` **Session/lock leak across HTTP** — refactor `sentiment.py:204`, `clustering.py:597`, `events.py:590` (discuss) to commit BEFORE the external call, not after
- `[ ]` **Clustering batch commits** — commit per-batch, not just at the end, so a crash mid-run doesn't re-bill Haiku
- `[ ]` **Embedding failures surface** — `rss.py:261`, don't swallow to `None`; raise/log so a dead OpenAI key doesn't silently stall clustering
- `[ ]` **`last_seen_at` write amplification** — `auth.py:145`, only update once per hour (or don't update on GETs), avoid write-per-request

---

## P8. Infra hygiene  `[ ]`

**Outcome:** server stays healthy long-term; kernel patches applied; disk doesn't fill; logs don't lose history.

**Tasks:**
- `[ ]` **Log rotation** for `/var/log/pipeline.log` — logrotate config, daily, 14-day retention
- `[ ]` **Docker cache reclaim** — schedule weekly `docker system prune -a --volumes` (with volume-preservation flag if any user volumes)
- `[ ]` **Resource limits** on containers — `mem_limit` / `cpus` in docker-compose (many services have it; audit the rest)
- `[ ]` **Pin pgvector image** to `pgvector/pgvector:pg17.4` (or current minor) — avoid silent breaking upgrades
- `[ ]` **Cache-Control** — carve out `/api/events*`, `/rss.xml`, other public endpoints from the global `no-store`; use short TTL + CDN-friendly caching
- `[ ]` **Kernel + apparmor reboot** — `/var/run/reboot-required` is set ~1mo; schedule off-peak reboot via Hetzner Robot
- `[ ]` **Docker-compose port bind fix** for clawrxiv-data — upstream commit

---

## Post-goal: run the audit again

Once P0-P5 land, re-run the same 4-subagent audit against a fresh 48h window. Target: ≤2 tier-1/2 misses. If more, iterate on P2/P3 (add more sources or tune Grok prompt).

---

## References

- `project_audit_2026-07-04.md` — full security/bug audit
- `project_monitoring_needed.md` — alert rules + rationale
- `project_security_fixes_pending.md` — history of accepted vs completed
- `features/ops_notifications.md` — Discourse DM feature spec
- `features/pipeline_v2_source_quality.md` — source management architecture
- `sessions/2026-07-04-audit-remediation.md` — worklog for the audit branch
- `reference_umami_analytics.md` — Umami setup + CURRENT_STATE
- `CURRENT_PHASE.md` §0.2 — "Ingestion health audit + build ops alerts" (this goal delivers that)
