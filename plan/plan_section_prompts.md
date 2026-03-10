# Plan Section: LLM Prompts

---
type: plan_section
tags: [prompts, llm, claude, pipeline, grok]
last_updated: 2026-03-10
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

LLM prompt templates for every stage of the AI Signal pipeline. All prompts live in `agent/runbooks.py` as system prompts (runbooks) for the Claude Agent SDK agents and subagents. The pipeline uses Haiku for high-volume extraction and classification, Sonnet for synthesis and scoring, and Grok for sentiment analysis via X search.

## Decision History

**2025-02**: Claude as primary LLM — best at structured output, long-context synthesis, and following complex instructions.
**2025-02**: Sonnet/Opus split — Sonnet handles routine calls, Opus for complex distillation.
**2026-03**: All distillation moved to Sonnet — Opus unnecessary when HyDE clustering produces clean, focused clusters.
**2026-03**: HyDE normalization prompt added — Haiku extracts title + key facts for embedding-based clustering.
**2026-03**: Prompts consolidated into `agent/runbooks.py` (7 runbooks: NEWSLETTER_EXTRACTOR, ARTICLE_CLASSIFIER, EVENT_INTELLIGENCE, DISTILLER, SCORER, TAGGER, QUALITY_CHECKER, EDITOR).
**2026-03**: QC and Editor downgraded to Haiku — structural checks moved to code, these agents now handle subjective judgment and straightforward comparison only.
**2026-03**: Grok sentiment analysis added — uses xAI Responses API with `x_search` tool for real-time X post search.
**2026-03**: Two-tier tag system replaced flat tags — primary category (1, fixed list) + secondary tags (2-6, from taxonomy groups).
**2026-03**: Secondary category added to tagger for events that clearly span two categories.

## Key Decisions

### Structured JSON Output
**Choice**: All pipeline prompts return structured JSON (not prose).
**Rationale**: Pipeline stages need machine-parseable output. JSON schema is specified directly in each prompt.

### Model Selection Per Stage
**Choice**: Match model to task complexity to control cost. Defined in `agent/config.py` MODELS dict.

| Stage | Model | Rationale |
|-------|-------|-----------|
| Newsletter extraction | Haiku | Structured extraction, high volume |
| Article extraction | Haiku | Structured extraction (trafilatura as primary, Haiku fallback) |
| HyDE normalization | Haiku | Extract title + key facts — simple, high volume |
| Article classifier | Haiku | Only handles ambiguous post-clustering cases now |
| Event intelligence (orchestrator) | Sonnet | Coordinates subagents, reads clusters, makes routing decisions |
| Distiller | Sonnet | Synthesis quality is the product — Sonnet for all events |
| Distiller (complex, 4+ sources) | Sonnet | Was Opus; Sonnet sufficient with clean HyDE clusters |
| Scorer | Sonnet | Needs nuance for score calibration |
| Tagger | Haiku | Classification from fixed taxonomy |
| Quality checker | Haiku | Structural checks now in code; QC does subjective judgment only |
| Editor verification | Haiku | Fact-checking against source material is straightforward |
| Sentiment analysis | Grok (grok-4-1-fast-reasoning) | Real-time X search via `x_search` tool |
| Embedding | OpenAI text-embedding-3-small | Dedicated embedding model (1536 dims) |

### Budget Limits
Defined in `agent/config.py` BUDGETS dict. Generous — quality matters more than cost savings.

| Agent Session | Budget (USD) |
|---------------|-------------|
| Classifier batch | $5.00 |
| Event intelligence | $50.00 |
| Newsletter extraction | $0.10 |

### Score-First Fast Path
The Event Intelligence orchestrator runs the SCORER before the DISTILLER. Events scoring 5 or below are skipped entirely — no distiller, tagger, QC, or editor runs. The `create_event` tool also rejects events scored 5 or below as a safety net. This saves significant cost on low-value clusters.

## Design

### Stage 1: Newsletter Extraction

**Prompt**: `NEWSLETTER_EXTRACTOR` in `agent/runbooks.py`
**Model**: Haiku

Parses newsletter emails and extracts individual news stories. Key behaviors:

- Extracts per story: headline, summary (newsletter's words, not rewritten), URL, is_sponsored flag, and content_type (news/opinion/analysis/research/quick-link).
- Filters out newsletter housekeeping (subscribe, share, etc.).
- Detects sponsored content via explicit markers ("sponsored by", "[Ad]", etc.) AND sneaky placements — stories that read like product pitches or appear under distinct sponsored sections without obvious labels (e.g., Alpha Signal style).
- Preserves the newsletter's original framing of each story.
- Returns JSON with newsletter_name, stories array, total_stories, and sponsored_count.

### Stage 2: HyDE Clustering (Embedding-Based)

**Code**: `src/ai_signal/pipeline/clustering.py`
**Prompt**: `_NORMALIZE_SYSTEM` in clustering.py (not in runbooks.py)
**Model**: Haiku (for normalization), OpenAI embeddings (for similarity)

Replaced the earlier LLM-based pairwise classification approach. The core insight: raw article embeddings are noisy because a 200-word RSS blurb and a 3000-word analysis about the same event produce wildly different vectors. HyDE normalizes every article into the same format BEFORE embedding, making same-event articles cluster tightly.

**Three stages:**

**Stage 2a — Normalize (Haiku):** Each article's lede (first 1000 chars, configurable via `CLUSTER_HYDE_LEDE_CHARS`) is sent to Haiku in batches of 30 (`CLUSTER_HYDE_BATCH_SIZE`). Haiku produces an "event fingerprint" per article: a normalized title (~10-15 words, factual, "[Entity] [Action] [Object]" format) plus one factual sentence (~20-30 words). Total output ~40-50 words per article — brevity is critical to avoid divergence between sources covering the same event.

Key normalization rules:
- Strip opinions, analysis, editorial framing, competitor comparisons — only the core event.
- Identify the UNDERLYING EVENT, not the document type (a system card published alongside a launch is fingerprinted as the launch).
- AI relevance filter: each article flagged `ai_relevant` true/false. Non-AI articles are filtered out (status set to "filtered").

**Stage 2b — Embed + Cluster:** Normalized summaries are embedded via OpenAI text-embedding-3-small. A cosine similarity graph is built (threshold 0.80, configurable via `CLUSTER_SIM_THRESHOLD`). Connected components via BFS form clusters. Oversized clusters (>15 articles, `CLUSTER_MAX_SIZE`) are split into singletons as a safety net against transitive closure mega-clusters.

**Stage 2c — Match to Existing Events:** Each cluster's representative article (highest trust_score) is compared against active events from the last 14 days (`CLUSTER_EVENT_MATCH_DAYS`) using both HyDE embeddings and content embeddings (takes the higher similarity). Match threshold is 0.75 (`CLUSTER_EVENT_MATCH_THRESHOLD`). Matched clusters get linked to existing events; unmatched clusters become candidates for new events.

**Primary source selection:** Within each cluster, articles are ranked by trust_score. Up to 2 primary sources are selected (`CLUSTER_MAX_PRIMARY_SOURCES`), deduplicated by source (one article per source). Only primary articles are read by the Event Intelligence agent — non-primary article titles from the cluster summary are sufficient context.

### Stage 3: Article Classifier (Post-Clustering)

**Prompt**: `ARTICLE_CLASSIFIER` in `agent/runbooks.py`
**Model**: Haiku

Handles residual classification after HyDE clustering. For each pending article:

1. Runs `vector_search` with article title + first 500 chars to find similar existing events.
2. Makes a three-way classification:
   - **SAME_EVENT**: Same real-world occurrence, same news cycle. Merge into existing event.
   - **RELATED_EVENT**: Connected story but distinct new occurrence (new milestone, weeks/months later). If a journalist would write a NEW headline, it's related.
   - **NEW_EVENT**: No meaningful connection. Default when uncertain or similarity below threshold.
3. Calls `update_article_status(status="clustered")` for EVERY article. Sets event_id only for SAME_EVENT merges. Processes all pending articles (calls `get_pending_articles` repeatedly until exhausted).
4. On first run with empty events table, all articles classified as NEW_EVENT — expected behavior.

Confidence threshold: SAME_EVENT requires >= 0.8. Articles processed oldest-first.

### Stage 4: Event Intelligence (Orchestrator)

**Prompt**: `EVENT_INTELLIGENCE` in `agent/runbooks.py`
**Model**: Sonnet

The orchestrator agent that takes clustered articles and produces event records by spawning specialized subagents. Processes clusters in batches of 5 (`EVENT_INTEL_BATCH_SIZE`).

**Process per cluster:**

1. Calls `get_cluster_summary` to see pre-grouped clusters from HyDE clustering. Reads ONLY `is_primary=True` articles (fetched in one `get_articles_batch` call, not individually). Non-primary article titles from summary are sufficient.
2. **Score-first fast path**: Runs SCORER subagent first. If importance_score <= 5, skips the entire cluster (no distiller, tagger, QC, or editor). Logs the skip and moves on.
3. For events scoring 6+, spawns subagents in order:
   - **DISTILLER** — synthesizes content (may spawn multiple in parallel).
   - **SCORER** — determines importance (already done in fast path, but result used here).
   - **TAGGER** — classifies into taxonomy (uses `get_tag_taxonomy` tool).
   - **QUALITY_CHECKER** — verifies publication readiness.
   - **EDITOR** — verifies factual accuracy against source material (only if QC passes).
4. Creates events via `create_event` with `article_ids` (auto-links articles, auto-computes source_count). Updates existing events via `update_event` with new `article_ids`.
5. Links related events via `link_related_events`. Publishes passing events as status="active".

**Context management**: Processes clusters one at a time or in small parallel groups. After creating an event, all cluster data is discarded. Does not accumulate results across clusters.

### Stage 5: Distiller (Subagent)

**Prompt**: `DISTILLER` in `agent/runbooks.py`
**Model**: Sonnet (both standard and complex variants use Sonnet now)
**Tools**: None (content passed in by orchestrator)

Synthesizes source articles into structured event content. Produces four outputs:

**Title**: Skimmable, semantically dense, up to ~120 chars. Format: "Company: What Happened" or natural phrasing. No clickbait.

**tier1_scan (Summary)**: A JSON ARRAY of 3-4 short takeaway strings (~8-15 words each). NOT a paragraph. Each takeaway is a complete thought boiled to its essence. Ordered by importance. The prompt includes explicit good/bad examples to prevent common failures (returning a string instead of an array, too-short fragments, vague statements).

**tier3_deep_dive (Detail Table)**: A JSON object with `rows` array and `legend` string. Each row has `number` (int), `type` (from closed enum), `key_point` (concise complete thought), and `context` (the "so what?" — substantive explanation, not a restatement). All fields required and non-empty. Allowed types: Stat, New Tech, Product Launch, Industry Update, Financials, Partnership, Research, Tech Info, Insight, Policy, Legal, Security Alert, Market Impact, Infrastructure, Strategy, Context, Other. Common type mistakes are called out in the prompt (e.g., "Financial" must be "Financials").

**what_this_means**: 2-4 sentences explaining significance to a smart generalist. Implications, who is affected, why someone should care.

**Key rules**:
- Factual precision: report actions and facts, not interpretations. When parties disagree, state what happened neutrally.
- Never fabricate. Higher-trust sources have more influence.
- Never mention source names or publications — write as the original reporter.
- For updates: first bullet/row covers what's new, remaining provide context.
- Also returns `key_facts` and `primary_entities`.

### Stage 6: Scorer (Subagent)

**Prompt**: `SCORER` in `agent/runbooks.py`
**Model**: Sonnet
**Tools**: None

Scores event importance on a 1-10 scale with a detailed calibration rubric:

| Score | Meaning | Example |
|-------|---------|---------|
| 10 | Paradigm shift (0-2/year) | AGI achieved |
| 9 | Must-read event | GPT-5 release, Pentagon banning an AI company |
| 8 | Significant | $1B+ funding, major open-source milestone |
| 7 | Solid news (baseline for coverage) | New model variant, notable benchmark |
| 6 | Decent but not broadly important | Routine lab updates, minor releases |
| 5 | Niche | Specialized research, minor tool updates |
| 4-1 | Diminishing interest | Very niche to noise |

**Distribution target** for a batch of 25-30 events: 1-3 at 9-10, 3-5 at 8, 10-15 at 7, rest at 6 and below.

**Two dimensions**: SIGNIFICANCE (how much it matters) and BUZZ (how much it's being discussed). Final score reflects the HIGHER of the two — a moderately significant tool going viral deserves 8-9.

**Modifiers**: +1 for 5+ independent sources, -1 for low-trust aggregator sources only, -1 for single speculative/rumor source.

### Stage 7: Tagger (Subagent)

**Prompt**: `TAGGER` in `agent/runbooks.py`
**Model**: Haiku
**Tools**: None (taxonomy passed in by orchestrator via `get_tag_taxonomy`)

Two-tier classification system:

**Primary category** (exactly 1, from fixed list — cannot create new categories):
- products, model-releases, research, enterprise, open-source, markets, safety, policy, security, creative, infrastructure

Key disambiguation guidance in the prompt:
- **products vs research**: Blog posts sharing techniques, tutorials, how-tos, and developer experience posts go in "products" — NOT research. Research requires a novel scientific contribution (e.g., arXiv paper). A HuggingFace blog about training tips is "products".
- **model-releases vs products**: model-releases is for new model launches and major version upgrades. Other product features and platform updates go in "products".

**Secondary tags** (2-6 from taxonomy groups: labs, models, technology, domain):
- Always tag specific models when mentioned (both lab + model tag).
- Always include at least one from "technology" or "domain" group.
- Don't over-tag.

**Secondary category** (optional, use sparingly): When an event CLEARLY belongs in two categories. Examples: a product launch targeting enterprise (products + enterprise), an open-source model release (open-source + model-releases), a policy decision about safety (policy + safety). The bar: "Would someone browsing the secondary category be surprised NOT to see this?"

**New tags** (optional): May propose new secondary tags for specific entities not in taxonomy. Must check existing tags first to avoid duplicates (e.g., don't create "donald-trump" if "trump" exists). Lowercase, hyphenated, specific entities only.

### Stage 8: Quality Checker (Subagent)

**Prompt**: `QUALITY_CHECKER` in `agent/runbooks.py`
**Model**: Haiku
**Tools**: None

Verifies event readiness for publication. Checks:

1. Title: clear, accurate, non-clickbait.
2. tier1_scan: JSON array of 3-4 short takeaway strings, scannable in under 5 seconds.
3. tier3_deep_dive: JSON object with "rows" array. Each row has number, type, key_point, context. Context must be substantive (not a restatement of key_point — auto-fail if it is). Type assignments validated against the closed enum.
4. what_this_means: present, 2-4 sentences, plain English.
5. Importance score matches content.
6. Two-tier tag validation: valid primary category, tags from valid groups.
7. Substantive event check: reject product pages, listicles, spam. Allow blog/research if substantive.
8. Key entities named.

**Structural auto-fail conditions**: tier1_scan not an array or wrong count, tier3_deep_dive missing rows or fewer than 3 rows with substantive context, empty what_this_means, invalid category or tags.

### Stage 9: Editor (Subagent)

**Prompt**: `EDITOR` in `agent/runbooks.py`
**Model**: Haiku
**Tools**: None

Last line of defense against inaccuracies. Verifies distilled content against source material across seven dimensions:

1. **Numerical accuracy**: numbers, percentages, dates, dollar amounts exactly correct.
2. **Attribution**: claims attributed to the right source/person.
3. **Overgeneralization**: consensus implied where sources disagree.
4. **Implied causation**: facts connected in ways sources didn't.
5. **Missing critical facts**: important facts absent from all tiers.
6. **Fabrication**: anything not traceable to sources.
7. **Undisclosed specifics**: specific figures stated that sources mark as undisclosed — the most dangerous fabrication mode.

Returns verified (bool), confidence (0.0-1.0), and issues array. If editor finds issues, the orchestrator re-runs the distiller once with corrections noted. If it fails again, the event is logged and skipped.

### Stage 10: Sentiment Analysis (Grok)

**Code**: `src/ai_signal/pipeline/sentiment.py`
**Model**: Grok (grok-4-1-fast-reasoning) via xAI Responses API
**Tool**: `x_search` (real-time X post search)

Runs on high-scoring events only (importance_score >= 8, configurable via `SENTIMENT_SCORE_THRESHOLD`). Two-pass system: Pass 1 at event creation, Pass 2 days later for shift detection.

The prompt instructs Grok to search X for real posts discussing the story and return structured JSON:

- **overall_sentiment**: One-line mood summary (e.g., "Mostly critical with some defenders", "Polarized — engineers positive, policy people alarmed").
- **prominent_reactions** (3-5): Each with handle, name, role (specific — "Senior Reporter @Verge", not just "journalist"), stance (1-2 word label), reaction (exact quote or close paraphrase), optional context (only if notable, e.g., breaking from usual position), and URL to the actual post.
- **fault_lines**: Where people disagree, with rough split estimate (e.g., "~70/30 positive/negative").
- **sentiment_score**: -1.0 (overwhelmingly negative) to 1.0 (overwhelmingly positive).

**Source quality hierarchy**: Best (journalists, researchers, professors, founders, policymakers, known independents like Karpathy/Gary Marcus), Good (domain practitioners with real credentials), Acceptable (anyone with a substantive take and real professional identity), Skip (meme replies, one-word reactions, pure hype accounts, newsletter aggregators resharing headlines).

**Critical rule**: Only include posts actually found via search. Never fabricate quotes, usernames, or URLs. If quality discussion is scarce, return honestly with fewer or zero reactions.

**Shift detection**: `detect_shift()` compares Pass 1 and Pass 2 sentiment scores. A delta >= 0.4 is flagged as significant.

## Dependencies & Constraints

### Dependencies
- **Claude Agent SDK**: All agent/subagent orchestration (authenticates via Claude Code subscription, not separate API key)
- **xAI API**: Grok sentiment analysis (requires `XAI_API_KEY`)
- **OpenAI API**: text-embedding-3-small for HyDE and content embeddings
- **PostgreSQL + pgvector**: Vector similarity for event matching and dedup
- **Tag taxonomy**: Tagger requires current tag list via `get_tag_taxonomy` tool
- **Source trust scores**: Used in primary source selection, distiller weighting, scorer modifiers

### Constraints
- **Agent SDK nesting**: Agent SDK cannot nest inside Claude Code — must `unset CLAUDECODE` before running pipeline
- **MCP param types**: `list`/`dict` param types in `@tool` arrive as empty strings via MCP. Use `str` + `_safe_json_parse()` workaround.
- **Context management**: Event intelligence processes clusters in batches of 5, discards data after each event creation to keep context lean.
- **Cluster safety**: MAX_CLUSTER_SIZE=15 splits oversized clusters to singletons to prevent transitive closure mega-clusters.

### Thresholds Summary (from `agent/config.py`)

| Parameter | Value | Purpose |
|-----------|-------|---------|
| CLUSTER_HYDE_LEDE_CHARS | 1000 | Chars of content sent to Haiku for normalization |
| CLUSTER_HYDE_BATCH_SIZE | 30 | Articles per Haiku normalization call |
| CLUSTER_SIM_THRESHOLD | 0.80 | Cosine sim threshold for cluster edges |
| CLUSTER_EVENT_MATCH_THRESHOLD | 0.75 | Sim threshold for matching to existing events |
| CLUSTER_EVENT_MATCH_DAYS | 14 | Only match against events from last N days |
| CLUSTER_MAX_PRIMARY_SOURCES | 2 | Primary articles per cluster for distillation |
| CLUSTER_MAX_SIZE | 15 | Oversized clusters split to singletons |
| DEDUP_SIMILARITY_THRESHOLD | 0.85 | Auto-merge threshold for event dedup |
| DEDUP_REVIEW_THRESHOLD | 0.70 | Haiku reviews pairs in 0.70-0.85 range |
| EVENT_INTEL_BATCH_SIZE | 5 | Clusters per event intelligence session |
| SENTIMENT_SCORE_THRESHOLD | 8 | Only run Grok sentiment on events scored >= this |

### Plan Section Dependencies
- Depends on [plan_section_taxonomy.md](plan_section_taxonomy.md): Tag list for tagger
- Depends on [plan_section_data_model.md](plan_section_data_model.md): Output shapes match schema
- Required by [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Clustering and distillation prompts

## Risks

### Prompt Inconsistency
- **Probability**: Low (mitigated by HyDE normalization)
- **Impact**: High — inconsistent output breaks the pipeline
- **Mitigation**: HyDE clustering removes the most inconsistency-prone step (pairwise LLM classification). Remaining prompts validated on real stories.

### Scoring Subjectivity
- **Probability**: Medium
- **Impact**: Medium — scores may drift
- **Mitigation**: Detailed rubric with calibration examples, distribution targets, two-dimension scoring (significance + buzz), and explicit modifiers. Score-first fast path means low scores don't waste distillation budget.

### Sentiment Fabrication
- **Probability**: Low-Medium
- **Impact**: Medium — fake quotes attributed to real people
- **Mitigation**: Prompt explicitly forbids fabrication, requires real posts found via search. Returns honest "limited discussion" when quality sources are scarce. Frontend should link to actual post URLs for verification.

### Grok API Availability
- **Probability**: Low
- **Impact**: Low — sentiment is additive, not critical path. Events publish without it.
- **Mitigation**: Graceful degradation. Sentiment failures are logged and events proceed without sentiment data.
