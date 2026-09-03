# Knowledge Base Index

<!--
AGENT: DON'T read this file sequentially - it's a search index.
USAGE: grep/search for your keyword → load specific referenced file(s)
-->

## Search by Keyword

**Auth/Security**: [gotcha_jwt_refresh_race_condition.md], [gotcha_cors_preflight_cookies.md], [gotcha_oauth_popup_blockers.md]
**Database**: [gotcha_prisma_json_typing.md], [gotcha_postgres_timezone.md], [gotcha_transaction_deadlocks.md], [perf_database_n_plus_one.md]
**React**: [gotcha_react_strict_mode_double.md], [gotcha_nextjs_hydration_mismatch.md], [gotcha_state_closure_stale.md], [perf_react_memo_strategy.md]
**API/External**: [gotcha_stripe_webhook_test_mode.md], [gotcha_vercel_env_vars_rebuild.md]
**Performance**: [perf_react_memo_strategy.md], [perf_database_n_plus_one.md], [perf_image_optimization.md], [perf_bundle_splitting.md]
**Patterns**: [pattern_repository_abstraction.md], [pattern_error_boundary_retry.md], [pattern_feature_flags.md], [pattern_audit_logging.md]
**Solutions**: [solution_optimistic_updates_rollback.md], [solution_infinite_scroll_virtualization.md], [solution_real_time_collaboration.md], [solution_file_upload_progress.md]

## Search by Problem

**"Build broken"**: [gotcha_module_resolution_paths.md], [solution_dependency_conflicts.md], [gotcha_typescript_versions.md]
**"Auth not working"**: [gotcha_jwt_refresh_race_condition.md], [gotcha_cors_preflight_cookies.md], [solution_session_management.md]
**"Works locally, fails production"**: [gotcha_env_var_differences.md], [gotcha_timezone_issues.md], [gotcha_build_vs_runtime.md]
**"App slow"**: [perf_react_memo_strategy.md], [perf_database_n_plus_one.md], [solution_caching_strategy.md]
**"Tests flaky"**: [gotcha_async_test_timing.md], [solution_test_isolation.md], [pattern_deterministic_tests.md]

## Search by Severity

**Critical (cost >4 hours)**:
- [gotcha_jwt_refresh_race_condition.md] - 6 hours
- [gotcha_cors_preflight_cookies.md] - 4 hours
- [gotcha_transaction_deadlocks.md] - production incident
- [gotcha_stripe_webhook_test_mode.md] - 3 hours

**Common (hits most developers)**:
- [gotcha_react_strict_mode_double.md]
- [gotcha_nextjs_hydration_mismatch.md]
- [gotcha_prisma_json_typing.md]

## Goblin News Pipeline
**Clustering**: [gotcha_unionfind_transitive_closure.md] — Union-find + embedding similarity causes mega-clusters via transitive closure. Fixed with HyDE (Haiku normalization before embedding).
**Deploy verification**: [gotcha_import_smoke_is_not_runtime_smoke.md] — a NameError inside a function body passed every import check and CI, killed all three runs of the day, zero stories for ~28h. Now: ruff F821 gate, a test that executes the EI batch function, deploy/canary.sh one-batch canary with rollback rule, and a per-run "ZERO stories" alert.
**Stale news / recency**: [gotcha_stale_story_republished.md] — months-old Grok sweep story published as a score-9 top story: no dates, no clock in the agents, merge-fed saga aged out of the match window, a dedup "stale" verdict then over-merged 47 fresh events and was removed. Six date-blind layers, fixed 2026-09-01..03.
**LLM Cost**: [gotcha_agent_sdk_overhead.md] — Wrapping a yes/no LLM call in Claude Agent SDK costs ~155× more tokens per call than a direct API call. Dedup stage was $482/mo; direct API would be ~$1–5/mo at the same model.

## Recent Additions
- **2026-09-03**: [gotcha_import_smoke_is_not_runtime_smoke.md] - Import smoke ≠ runtime smoke; canary + rollback rule + zero-stories alert (production outage, ~28h no stories)
- **2026-09-01**: [gotcha_stale_story_republished.md] - Old story republished as breaking news; date gates + agent clock + stale dedup verdict (production trust incident)
- **2026-06-03**: [gotcha_agent_sdk_overhead.md] - Claude Agent SDK adds ~21,500 tokens/call of hidden scaffolding (critical for high-volume single-purpose calls)
- **2026-03-09**: [gotcha_unionfind_transitive_closure.md] - Union-find transitive closure destroys clustering (4+ hours, critical)

## Contributing

**Add entry when**:
- Debug >30 min (→ gotcha_*.md)
- Solution reusable (→ solution_*.md)
- Pattern used 2+ times (→ pattern_*.md)
- Measured perf gain (→ perf_*.md)

**Entry must have**:
- Working code examples
- Measured impact (time/performance)
- "When to use" and "when NOT to use"
- Reference to codebase usage

---
**Token Savings**: Reading this index = ~350 tokens. Full old version = 1,630 tokens. Load specific files only.
