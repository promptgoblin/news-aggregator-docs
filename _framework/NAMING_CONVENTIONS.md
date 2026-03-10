# Naming Conventions Quick Reference

## File Naming Patterns

### Plan Documents
- **Master Plan**: `PLAN.md` (always uppercase, only one)
- **Plan Sections**: `plan_section_[topic].md`
  - Examples: `plan_section_architecture.md`, `plan_section_data_model.md`
  - Use underscores, no spaces
  - Keep topic names short but clear

### Feature Documents
- **Pattern**: `feature_[feature_name].md`
  - Examples: `feature_user_authentication.md`, `feature_payment_processing.md`
  - Use underscores between words
  - Feature = user-facing functionality

- **Sub-features**: `feature_[parent]_[sub_feature].md`
  - Parent feature name comes first, then sub-feature
  - Examples:
    - Parent: `feature_payment_processing.md`
    - Sub: `feature_payment_subscriptions.md`
    - Sub: `feature_payment_invoicing.md`
    - Sub: `feature_payment_refunds.md`
  - Use when a feature is too large and needs breakdown
  - Sub-feature docs should reference parent in "References" section

### Audit Documents
- **Pattern**: `audit_[type]_[date].md`
  - Examples: `audit_security_2024_03.md`, `audit_performance_2024_q1.md`
  - Types: security, performance, accessibility, code_quality
  - Date format: YYYY_MM or YYYY_QN

### Checklists
- **Pattern**: `checklist_[phase].md`
  - Examples: `checklist_deployment.md`, `checklist_launch.md`
  - Phases: deployment, cleanup, launch, migration, testing

### Reference Documents
- **Pattern**: `[prefix]_[name].md`
  - Prefixes:
    - `api_` - External API documentation
    - `spec_` - Specifications and standards
    - `lib_` - Library documentation
    - `guide_` - Third-party guides
  - Examples: `api_stripe_webhooks.md`, `spec_oauth_flow.md`

### Knowledge Base
- **Pattern**: `[type]_[description].md`
  - Types:
    - `gotcha_` - Pitfalls and warnings
    - `solution_` - Specific problem solutions
    - `pattern_` - Reusable patterns
    - `perf_` - Performance optimizations
  - Examples: `gotcha_stripe_test_mode.md`, `solution_hydration_fix.md`

### Session Logs
- **Individual Sessions**: `session_[date]_[brief_topic].md`
  - Examples: `session_2024_03_15_payment_integration.md`
  - Date format: YYYY_MM_DD
  - Keep topic to 2-3 words max

- **Quarterly Summaries**: `q[N]_[YYYY]_summary.md`
  - Examples: `q1_2024_summary.md`, `q4_2025_summary.md`
  - Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
  - Created at end of each quarter to archive individual sessions

## Special Files

### Index Files
- Section indices: `_index.md` (always lowercase with underscore, used in knowledge/ and reference/ folders)
- Master plan: `PLAN.md` (always uppercase)
- Current work state: `_status.md` (always lowercase)
- Project context: `_context.md` (always lowercase)

### Framework Files
- All templates: `template_[TYPE].md`
- Documentation: `README.md`, `NAMING_CONVENTIONS.md`

## Naming Rules

### General Rules
1. **Always use lowercase** (except PLAN.md and README.md)
2. **Use underscores** to separate words, not hyphens or spaces
3. **No special characters** except underscores
4. **Be descriptive but concise** - aim for 2-4 words
5. **Include dates** where relevant (audits, sessions)

### What Makes a Good Name

❌ **Bad**: `doc1.md`, `payment.md`, `new-feature.md`, `stripe stuff.md`

✅ **Good**: `feature_payment_processing.md`, `api_stripe_webhooks.md`

### Hierarchy Rules
- Keep structure flat - avoid deep nesting
- If you need sub-features, prefix with parent: `feature_payment_subscriptions.md`
- Don't create subfolders within main categories

## Quick Decision Tree

```
Is it about planning/architecture?
  └─> plan/plan_section_[topic].md

Is it a user-facing feature?
  └─> features/feature_[name].md

Is it an assessment/review?
  └─> audits/audit_[type]_[date].md

Is it a task list?
  └─> checklists/checklist_[phase].md

Is it external documentation?
  └─> reference/[prefix]_[name].md

Is it a lesson learned?
  └─> knowledge/[type]_[description].md

Is it a coding session log?
  └─> sessions/session_[date]_[topic].md
  └─> sessions/q[N]_[YYYY]_summary.md (quarterly summary)
```

## Examples for Common Scenarios

### Starting a New Feature
```
features/feature_user_registration.md
features/feature_admin_dashboard.md
features/feature_data_export.md
```

### Breaking Down a Large Feature
```
Parent:
features/feature_payment_processing.md

Sub-features:
features/feature_payment_subscriptions.md
features/feature_payment_invoicing.md
features/feature_payment_refunds.md
features/feature_payment_webhooks.md
```

### Adding API Documentation
```
reference/api_sendgrid_templates.md
reference/api_auth0_management.md
reference/api_google_oauth.md
```

### Recording a Problem Solution
```
knowledge/gotcha_react_strict_mode_double_render.md
knowledge/solution_webpack_memory_leak.md
knowledge/pattern_error_boundary_retry.md
```

## Version Control Considerations

- Never rename files once created (breaks links)
- If major revision needed, create new file with v2 suffix
- Archive old versions to `/archive` directory
- Keep redirects or notes in old file pointing to new
