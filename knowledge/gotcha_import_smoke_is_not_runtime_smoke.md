# Gotcha: Import Smoke Test Is Not a Runtime Test (2026-09-02)

## What Happened

A one-line change added `today = datetime.now(timezone.utc)...` inside
`_run_event_intel_batch` in `agent/orchestrator.py`. That module only had
**function-local** `from datetime import …` statements, so the name did not
exist at module scope. Every check passed:

- local unit tests (306 green)
- CI import smoke test (`import agent.orchestrator …` → `IMPORTS OK`)
- the deploy skill's in-container import smoke test (`OK`)
- containers healthy, API 200, nginx reloaded

Then all three cron runs of the day failed every Event Intelligence batch
with `NameError`. The stalled-batch guard aborted each stage after two
batches, `stage_failures` DMed once (then sat in its 20h cooldown), and
`zero_events_24h` needs a full day. **The site published nothing for ~28h**
until Mike asked "No runs today?".

## Root Cause

Two layers, both about what "verified" meant:

1. **Static:** a `NameError` inside a function body is invisible to an
   import. Nothing in the pipeline ran a linter for undefined names.
2. **Runtime:** nothing after a deploy exercised the pipeline. "Healthy"
   meant "the process started", not "a batch produced an event".

And the alerting named the symptom ("3 pipeline stage issue(s)"), not the
impact ("zero stories published").

## Fix (app commits f2ce95a + the canary commit, 2026-09-03)

| Layer | Guard |
|---|---|
| Static | `ruff check --select F821,F811,F823 src agent scripts tests` in CI and in the deploy pre-flight. ruff lives in the app venv. |
| Unit | `tests/test_deploy_canary.py` **executes** `_run_event_intel_batch` with the SDK client stubbed — taxonomy/calibration fetch, `ClaudeAgentOptions`, `build_subagents`, the dispatch prompt, the message loop, usage recording all run for real. |
| Deploy | `deploy/canary.sh`: one real pipeline pass with `EI_MAX_BATCHES=1` (the rest of the backlog defers like a budget-cap hit), then `scripts/check_last_run.py` judges the run row via `agent/run_health.run_verdict`. Exit 1 = roll back. Mandatory in the deploy skill for any pipeline change. |
| Alert | `check_run_produced_nothing`: fires after **every** run that ingested articles and created 0 events, subject "🚨 latest run published ZERO stories", 4h cooldown, escalates on the second consecutive empty run. |

## Lessons

- **"It imports" proves nothing about a function body.** Verification must
  execute the code path that changed. For LLM-driven stages that means a
  test with the client stubbed plus a real one-batch run after deploy.
- **A deploy is done when the pipeline has produced output on the new code,
  not when the containers are up.**
- **Alert subjects must name the user-visible impact** ("zero stories"),
  not the internal symptom, and must re-fire per run, not per day, for a
  3x/day pipeline.
- **Roll back first, debug second.** With a canary verdict in hand there is
  no reason to leave a broken pipeline live while reading tracebacks.
- Module style trap: `agent/orchestrator.py` imports `datetime` per
  function. A new module-level use needs its own import.
