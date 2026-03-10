# Project Context

**Last Updated**: 2026-03-09

## Project Overview

**AI Signal** — Event intelligence platform for AI news. Subdomain of Prompt Goblins (news.promptgoblins.ai). Aggregates from newsletters, RSS, HN. Distills into canonical events with three-tier content depth. Core product is the quality of event distillation, not just features.

**Key Insight**: The unit of content is an **event**, not a news story. Multiple articles, tweets, and takes about the same thing get clustered and distilled into one comprehensive, efficiently consumable unit.

## Feature Status
- ✅ Event Intelligence Pipeline — Live (pipeline running, clustering under iteration)
- ✅ Newsletter Ingestion — Live (Fastmail JMAP, 11 sources)
- ✅ RSS Ingestion — Live (16 feeds including 2 HN feeds)
- ✅ Three-Tier Content — Live (tier1_scan, tier3_deep_dive, what_this_means)
- ✅ Scoring & Tagging — Live (Sonnet scorer, Haiku tagger, two-tier taxonomy)
- ✅ Frontend Feed — Live (Next.js, detail modal, view toggle)
- 📋 Production Deployment — Planning
- 📋 Grok Sentiment — Planning
- 📋 Discourse Integration — Planning
- 💡 RSS Output Feeds — Proposed
- 💡 User Preferences — Proposed

## Recent Changes
- **2026-03-09**: HyDE clustering implemented (replaces failed union-find approach)
- **2026-03-09**: All distillation switched to Sonnet (removed Opus for complex events)
- **2026-03-09**: First full pipeline run — 212 articles, 113 events, identified clustering as critical issue
- **2026-03-08**: Pipeline fully operational — ingestion, clustering, event intelligence, dedup all working
- **2026-02-27**: Agent SDK pipeline redesign complete
- **2025-02-25**: Project created, docs framework provisioned, PLAN.md written

## Quick Links
- Master Plan: [plan/PLAN.md](plan/PLAN.md)
- Knowledge Base: [knowledge/_index.md](knowledge/_index.md)
- External Docs: [reference/_index.md](reference/_index.md)
- Original Spec: [reference/spec_ai_signal_platform.md](reference/spec_ai_signal_platform.md)

---
**For Agents**: Read [_status.md](_status.md) first for current state. Read this for project history and context.
