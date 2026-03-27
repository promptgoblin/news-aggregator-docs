# Plan: Goblin News

> Event intelligence platform for AI news — one source, zero noise.

## Vision

Build the go-to source for efficient AI news consumption. We aggregate from newsletters, RSS, Twitter/X, and other channels, then distill stories into canonical **events** — deduplicated, scored, tagged, and presented at three depth levels. The core differentiator is not summarization — it's the precision and thoroughness of distilling multiple sources about the same event into one perfectly consumable unit of information.

**Status**: Planning
**Current Focus**: Project setup, prompt validation, architecture decisions
**Last Updated**: 2025-02-25

## Quick Decisions

- **Backend**: Python + FastAPI — async, fast, great for LLM work
- **Database**: PostgreSQL + pgvector — relational + vector search in one
- **Pipeline**: Claude Agent SDK — agents with MCP tools, cron-triggered (no Celery)
- **LLM Processing**: Claude Agent SDK (Haiku for cheap tasks, Sonnet for routine, Opus for complex)
- **Twitter/X**: Grok API — native access to Twitter data
- **Embeddings**: Voyage AI or OpenAI — TBD during Phase 1
- **Frontend**: Next.js + Tailwind — must match Prompt Goblins theme exactly
- **Hosting**: news.promptgoblins.ai (subdomain, separate app, unified UX)
- **Agent Pipeline**: Claude Agent SDK with OAuth token, hosted on web server (not dev machine)
- **Forum Integration**: Discourse API — "Discuss" button creates/links threads in AI News category (cat 8)

## Plan Sections

- [plan_section_architecture.md](plan_section_architecture.md): System design, pipeline flow, hosting
- [plan_section_data_model.md](plan_section_data_model.md): Event, Article, Source, Channel schemas
- [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Core algorithm — clustering, dedup, distillation, the "event" unit
- [plan_section_prompts.md](plan_section_prompts.md): LLM prompt templates for all pipeline stages
- [plan_section_taxonomy.md](plan_section_taxonomy.md): Tag system, scoring rubrics, quality filters
- [plan_section_sources.md](plan_section_sources.md): Discovery channels, initial source list, trust scores
- [plan_section_frontend.md](plan_section_frontend.md): UI design, three-tier content display, filtering

## Features

### Core (Day 1)
- [Not Started] Event Intelligence Pipeline: Clustering, dedup, distillation into canonical events - **C3**
- [Not Started] Newsletter Ingestion: Fastmail JMAP adapter, sponsor/ad filtering - **C2**
- [Not Started] RSS Ingestion: Blog/company feed monitoring - **C2**
- [Not Started] Three-Tier Content: Scan / Understand / Deep Dive generation - **C2**
- [Not Started] Scoring & Tagging: Importance scoring, tag classification, quality filtering - **C2**
- [Not Started] Frontend Feed: Main feed, tag filters, score threshold, time range - **C2**
- [Not Started] Discourse Integration: "Discuss" button → forum thread creation - **C2**

### Secondary
- [Not Started] Twitter/X via Grok: Social signal monitoring - **C2**
- [Not Started] RSS Output Feeds: Main, per-tag, custom filtered, multiple formats - **C1**
- [Not Started] User Preferences: Local storage prefs, saved filters, presets - **C2**
- [Not Started] Source Quality Dashboard: Trust scores, authority tracking - **C1**

### Future
- Customizable user newsletters (daily/weekly digest, filtered by tags/score)
- Customizable RSS output feeds (per-tag, per-score, custom filters)
- Agent-driven research (autonomous story discovery, arXiv monitoring)
- Podcast transcript ingestion
- User accounts with synced preferences
- Breaking news notifications
- Expand to other topics (crypto, biotech, etc.)

### Phase 5: AI Directory (future project)
The news aggregator feeds into a comprehensive **AI Directory** — a catalog of AI labs, models, tools, conferences, and companies. News events naturally surface new directory entries (new labs, model launches, conference announcements, tool releases). The directory complements the aggregator and is a monetization vehicle.
- Directory of AI labs, companies, and startups
- Model registry (capabilities, benchmarks, pricing)
- Tool/product catalog
- Conference/event calendar
- Auto-populated from news intelligence (new entity detection)
- Monetization: featured listings, sponsored profiles, lead gen

## Dependencies & Parallel Groups

```
Phase 1 (Prompt Validation — no infra needed):
  Prompts for: distillation, scoring, tagging, quality filtering, clustering

Phase 2 (Foundation — can parallelize):
  Parallel Group A: database_setup, newsletter_ingestion, rss_ingestion
  Parallel Group B (requires A): processing_pipeline, event_intelligence

Phase 3 (Product):
  frontend_feed → discourse_integration
  three_tier_content (can parallel with frontend)
  scoring_tagging (can parallel with frontend)

Phase 4 (Expansion):
  twitter_grok, rss_output, user_preferences
```

## Phases

### Phase 1: Prompt Validation [Not Started]
- [ ] Manually collect 20-30 AI stories from past week
- [ ] Build and validate prompts for distillation, scoring, tagging, quality filtering
- [ ] Test event clustering logic with LLM (can we reliably detect "same event"?)
- [ ] Validate the "event" data model against real stories
- **Gate**: Prompts produce consistent, high-quality output on test stories

### Phase 2: Foundation [In Progress]
- [ ] PostgreSQL + pgvector schema
- [ ] Newsletter ingestion (Fastmail JMAP)
- [ ] RSS ingestion (company blogs, news outlets)
- [ ] Processing pipeline (Claude Agent SDK)
- [ ] Event intelligence — clustering, dedup, merge
- **Gate**: Stories flowing in, clustering into events, three tiers generating

### Phase 3: Product [Not Started]
- [ ] Frontend MVP (Next.js, matches Prompt Goblins theme)
- [ ] Feed with filters, scoring, time range
- [ ] Story detail view (three content tiers)
- [ ] Discourse "Discuss" integration
- [ ] RSS output feeds
- **Gate**: Usable product, ready for soft launch

### Phase 4: Expansion [Not Started]
- [ ] Twitter/X via Grok API
- [ ] User preferences
- [ ] Agent-driven research / arXiv monitoring
- [ ] Performance optimization

## Success Metrics
- **Coverage**: Captures 90%+ of significant AI news within 4 hours
- **Dedup quality**: <5% duplicate events in feed
- **Distillation quality**: Tier 3 captures 95%+ of substantive facts from source material
- **Speed**: New events published within 1 hour of first source
- **User value**: One feed replaces 5+ newsletters

## External Resources
- [Original Spec](../reference/spec_ai_signal_platform.md): Mike's full product vision document
- [Prompt Goblins Forum](https://promptgoblins.ai): Parent platform
- [AI News Category](https://promptgoblins.ai/c/ai-news/8): Discourse integration target
