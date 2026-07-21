# Gotcha: transitive-dep loss + stage isolation = invisible pipeline death

**Date:** 2026-07-21 · **Severity:** production outage (16h, zero new events) · **Fix:** `4026a98`

## What happened

A routine deploy at 2026-07-20 ~08:00 UTC rebuilt the agent image. The fresh
pip resolution no longer installed **numpy** — it had never been a direct
dependency in `pyproject.toml`, only a transitive one that some package
previously dragged in. `clustering.py` imports numpy for cosine similarity.

Every pipeline run after the rebuild (14:00, 22:00, next-day 06:00):
- **Ingestion worked** (no numpy needed) → articles kept arriving
- **Clustering raised ImportError** → swallowed by stage isolation → logged
  only to `/var/log/pipeline.log` (lost on next container recreate)
- **Event-intel ran on leftover clusters** → 1-2 events, then starvation
- **Run reported "complete"** → looked like a slow news day, not a break

Detected only because Mike noticed no fresh stories. 74 articles stranded
`pending`; the article backlog was invisible because nothing queries it.

## Diagnosis path that worked

1. `pg_locks` — no advisory-lock wedge
2. `llm_usage_log` grouped by stage — showed event-intel making 1-2 calls/run
   instead of dozens, and NO clustering-stage calls
3. `articles` by `processing_status` + `MAX(CASE WHEN cluster_id IS NOT NULL
   THEN ingested_at END)` — pinpointed the last successful clustering to the
   exact run before the deploy
4. Standalone import of the stage module in the container → instant
   `ModuleNotFoundError`

Step 4 is the shortcut: **when a stage silently underperforms, try importing
its module in the container first** — before any log archaeology.

## Rules going forward

1. **Every direct import gets an explicit pin in pyproject.toml.** Never rely
   on transitive resolution (numpy now pinned `>=1.26,<3`).
2. **Deploy skill now mandates an agent import smoke test** after any agent
   rebuild (imports orchestrator + all stage + ingestion modules).
3. **Don't deploy during pipeline windows** (06/14/22 UTC + ~2.5h) — a
   deploy mid-run kills the orchestrator and strands its batch. Check
   `pgrep -f agent.orchestrator` first. (Same incident: the 06:11 deploy
   killed the 06:00 run.)
4. This is the **second** silent-decay incident that the unbuilt "0 events
   in 24h → Discourse DM" alert would have caught within a day. It's P5 in
   `plan/plan_coverage_and_hardening_2026-07-20.md` — build it.
