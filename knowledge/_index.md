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

## AI Signal Pipeline
**Clustering**: [gotcha_unionfind_transitive_closure.md] — Union-find + embedding similarity causes mega-clusters via transitive closure. Fixed with HyDE (Haiku normalization before embedding).

## Recent Additions
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
