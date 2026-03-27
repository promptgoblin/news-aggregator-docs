# Plan Section: Taxonomy & Scoring

---
type: plan_section
tags: [tags, scoring, quality, filtering]
last_updated: 2025-02-25
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Tag taxonomy and scoring system for Goblin News events. Tags enable filtering and discovery. Importance scores drive feed ordering and quality thresholds. The taxonomy is LLM-assigned from a fixed list — the auto-tagger cannot create new tags (same principle as the Prompt Goblins forum).

## Key Decisions

### Fixed Taxonomy, LLM-Assigned
**Choice**: Curated tag list, LLM classifies events into existing tags. No tag creation.
**Rationale**: Consistent taxonomy, no tag drift, predictable filtering. Same approach proven on Prompt Goblins forum.

### 1–10 Importance Scale
**Choice**: Integer importance score with detailed rubric.
**Rationale**: Simple, intuitive, maps cleanly to feed filtering (show me 7+ only).

## Design

### Tag Groups

| Group | Purpose | Example Tags |
|-------|---------|-------------|
| **Technology** | What tech area | llm, computer-vision, robotics, nlp, speech, reinforcement-learning, multimodal, agents, embeddings, fine-tuning, rag, hardware, inference, security |
| **Domain** | Application area | healthcare, finance, education, legal, creative, gaming, science, climate, defense, manufacturing |
| **Company** | Key players | openai, anthropic, google, meta, microsoft, nvidia, stability-ai, mistral, cohere, huggingface, apple, amazon, samsung, xai |
| **Content Type** | What kind of news | product-launch, research-paper, funding, acquisition, hire, partnership, policy, regulation, benchmark, open-source, financials |
| **Impact Level** | Significance | breakthrough, industry-shift, incremental, niche |

Total: ~60–80 tags across 5 groups. Start lean, expand based on coverage gaps.

**Tags added after Phase 1 validation (2026-02):**
- `hardware`: Chips, GPUs, TPUs, AI accelerators — needed for Nvidia/semiconductor stories
- `inference`: Inference optimization, serving, edge deployment — distinct from training
- `security`: Audits, jailbreaks, red-teaming, adversarial attacks — growing beat
- `financials`: Earnings, revenue reports, valuation events — distinct from `funding`
- `regulation`: More specific than `policy` — covers laws, compliance, regulatory actions
- `samsung`, `xai`: Recurring company subjects not in original list
- Removed `tutorial` from Content Type (non-event content shouldn't be tagged, it should be filtered out)

### Scoring Rubric

| Score | Label | Criteria | Example |
|-------|-------|----------|---------|
| 10 | Paradigm shift | Redefines the field | GPT-3 launch, transformer paper |
| 9 | Major event | Top labs, significant launches | GPT-5 launch, major model release |
| 8 | Important | Notable releases, big funding | $500M funding round, key researcher move |
| 7 | Noteworthy | Interesting research, meaningful update | New benchmark SOTA, significant API update |
| 6 | Standard | Routine industry news | Minor product update, conference announcement |
| 5 | Modest | Niche but substantive | Specialized tool launch, vertical AI application |
| 4 | Low interest | Very niche, minor | Small startup update, incremental paper |
| 3 | Minimal | Barely significant | Routine hiring, minor feature tweak |
| 2 | Marginal | Questionable newsworthiness | Opinion pieces, rehashed takes |
| 1 | Noise | Should be filtered | Spam, non-news, pure marketing |

### Quality Filters (Preset Feeds)

**Audience presets** (persona-based, top-level):

| Preset | Tags Emphasized | Tags De-emphasized | Use Case |
|--------|----------------|-------------------|----------|
| **Builder** (default) | product-launch, research-paper, open-source, benchmark | financials, hire | Technical users building with AI |
| **Business** | financials, funding, acquisition, partnership, hire, regulation | research-paper | Enterprise/industry-focused users |
| **Full Signal** | All | None | Power users who want everything |

**Topic presets** (can combine with audience presets):

| Filter | Score Threshold | Tags | Use Case |
|--------|----------------|------|----------|
| **Top Stories** | ≥ 8 | All | Major news only |
| **Research** | ≥ 4 | research-paper, benchmark | Academic focus |
| **Open Source** | ≥ 4 | open-source | OSS releases and tools |
| **Enterprise** | ≥ 5 | partnership, regulation, financials | Enterprise AI deployments |

Users can also create custom filters (stored in local storage; synced via forum auth for logged-in users).

### Source Trust Scores

| Source Type | Base Trust | Rationale |
|-------------|-----------|-----------|
| Primary (company blog, press release) | 0.9 | First-party, authoritative |
| Curated newsletter | 0.8 | Expert-curated, pre-filtered |
| Major publication | 0.75 | Professional standards |
| Tech blog | 0.6 | Variable quality |
| Social media | 0.4 | Noisy, unverified |
| Aggregator | 0.3 | Low original value |

Trust scores adjust over time based on accuracy and timeliness metrics.

## Dependencies & Constraints

### Plan Section Dependencies
- Required by [plan_section_prompts.md](plan_section_prompts.md): Tag list used in tagging prompt
- Required by [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Source weights for distillation
- Required by [plan_section_frontend.md](plan_section_frontend.md): Filter presets, tag display

## Open Questions
- [ ] Full tag list — flesh out during Phase 1 as test stories reveal needed tags
- [ ] Should tags have parent/child relationships or stay flat?
- [ ] Per-tag RSS feeds — one feed per tag or only popular tags?

## Implementation Notes
- Store tags in database with display names and groups for API consumption
- Tag list should be easily extensible (just add rows) without code changes
- Consider tag synonyms (e.g., "large language model" → "llm") for better LLM classification
- Log tag assignment confidence to identify tags the LLM struggles with
