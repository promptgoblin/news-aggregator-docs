# Phase 1: Prompt Validation Results

---
type: knowledge
tags: [phase-1, validation, prompts, testing]
last_updated: 2026-02-26
---

## Test Dataset

**Source**: `test_dataset_feb2026.json` (project root)
**Stories collected**: 62 from 6 sources (Google AI Blog, OpenAI Blog, Anthropic News, TechCrunch, CNBC, web search aggregation)
**Event clusters identified**: 10 natural clusters with cross-source overlap
**Collection date**: 2026-02-26

## Clustering Prompt Validation

**Test**: 12 story pairs covering all three classifications (same, related, unrelated)
**Model**: Sonnet
**Result**: **12/12 correct** (100%), average confidence 0.88

| Pair | Test Case | Expected | Got | Conf |
|------|-----------|----------|-----|------|
| 1 | Vercept acquisition (Anthropic vs TechCrunch) | SAME | SAME | 0.98 |
| 2 | Nvidia earnings (TechCrunch vs CNBC) | SAME | SAME | 0.97 |
| 3 | Nvidia earnings vs Vera Rubin angle (same call) | SAME | SAME | 0.80 |
| 4 | SpaceX-xAI merger → co-founder departures (9 days later) | RELATED | RELATED | 0.95 |
| 5 | OpenAI India vs Anthropic India (different companies) | RELATED | RELATED | 0.88 |
| 6 | AI energy rate hikes vs infra opposition | RELATED | RELATED | 0.85 |
| 7 | Samsung Unpacked / Gemini Android (different angles) | SAME | SAME | 0.72 |
| 8 | Samsung Unpacked vs Samsung adds Perplexity (2 days apart) | RELATED | RELATED | 0.82 |
| 9 | Google AI Summit (Pichai vs India post) | SAME | SAME | 0.88 |
| 10 | GPT-5.2 physics vs Vercept acquisition | UNRELATED | UNRELATED | 0.99 |
| 11 | Claude Sonnet 4.6 vs Gemini 3.1 Pro (competing launches) | RELATED | RELATED | 0.78 |
| 12 | Google AI Summit (overview vs Pichai) | SAME | SAME | 0.93 |

### Observations
- The "new headline" heuristic is the key differentiator — works well across all cases
- Same-source multi-angle articles (Pair 3) have lower confidence but correct classification
- Thematic similarity (Pairs 5, 6, 11) correctly NOT over-merged
- Time gap is a strong supporting signal for related vs same

### Prompt Refinements Applied
1. Added rule: same-publisher multi-angle coverage of one event = SAME EVENT
2. Added rule: roundup articles covering multiple events → classify each event individually
3. Added examples to cover these cases

### Implementation Note
Clustering needs transitivity: if A=B and A=C, infer B=C without direct comparison.

## Distillation Prompt Validation

**Test**: 3-article Nvidia Q4 FY2026 earnings cluster
**Sources**: Fortune (weight 1.0), Kiplinger (0.8), TechCrunch (0.7)
**Model**: Sonnet
**Result**: **High quality, production-viable**

### Output Quality Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| T1 accuracy | Excellent | Scannable in <5 seconds, captures the gist |
| T1 word count | Good | ~30 words, on target |
| T2 self-contained | Excellent | Readable without T3, covers what/why/details |
| T2 word count | Good | ~250 words (high end of range) |
| T3 comprehensiveness | Excellent | Captured 95%+ of substantive facts across sources |
| T3 structure | Good | Sectioned with headers, scannable |
| Source weighting | Excellent | Fortune dominated (correct), TechCrunch minimal (correct) |
| No fabrication | Pass | All claims traceable to sources |
| Key facts extraction | Excellent | 18 granular, attributed facts |
| Source attribution | Good | Disagreements would be noted (none in this cluster) |

### Prompt Refinements Identified
1. Add harder word cap for T2 (currently a range, should be a max)
2. Add temporal context for sources (pre/post-event, chronological order)
3. Clarify how updates should be framed in tiers (conditional instruction block)
4. Add weight scale anchoring (1.0 = authoritative, 0.5 = secondary, 0.3 = low-trust)
5. Specify entity ordering (by relevance)
6. Clarify where disagreements should surface (T2 if significant, T3 always)

## Phase 1 Gate Assessment

### Clustering: PASS
- 100% accuracy on 12 pairs spanning all classification types
- Edge cases handled correctly (thematic similarity, time gaps, multi-angle)
- Confidence levels appropriately calibrated
- Prompt refinements are minor additions, not structural changes

### Distillation: PASS (with minor refinements)
- Output quality is publishable for T1 and T2
- T3 may benefit from light editorial pass but structurally sound
- Source weighting works as designed
- Key facts extraction is clean and useful

## Scoring Prompt Validation

**Test**: 8 events ranging from paradigm-shifting to noise
**Model**: Sonnet
**Result**: **Well-calibrated, intuitive ranking**

| Event | Score | Tier | Assessment |
|-------|-------|------|------------|
| GPT-5.2 derives new physics result | 9 | featured | Correct — novel scientific contribution |
| SpaceX/xAI $1.25T merger | 9 | featured | Correct — largest merger in history |
| Claude Sonnet 4.6 release | 8 | featured | Correct — frontier model launch |
| Nvidia Q4 FY2026 earnings | 8 | featured | Correct — record quarter, industry signal |
| Anthropic acquires Vercept | 7 | standard | Correct — noteworthy acquisition |
| OpenAI CPO hire | 5 | scan_only | Correct — routine organizational news |
| Gushwork $9M seed | 4 | scan_only | Correct — small startup, niche |
| Google Photos tips article | 2 | scan_only | Correct — promotional content, not news |

### Refinements Applied
1. Added note: 10s should be rare (0-2/month)
2. Clarified primary source modifier: applies to substantive announcements, not tips/promo
3. Added audience-fit note: technical releases weight higher than financial for AI engineering audience
4. Added `-1` modifier for single-source speculative/rumor claims

## Tagging Prompt Validation

**Test**: 6 events across different types
**Model**: Sonnet
**Result**: **Functional, taxonomy gaps identified and fixed**

### Taxonomy Gaps Found and Resolved
| Added Tag | Group | Why Needed |
|-----------|-------|-----------|
| `hardware` | Technology | Nvidia/semiconductor stories had no honest tech tag |
| `security` | Technology | Agent security audit had no home |
| `inference` | Technology | Distinct from training, growing beat |
| `financials` | Content Type | Earnings ≠ funding ≠ product-launch |
| `regulation` | Content Type | More specific than `policy` |
| `samsung`, `xai` | Company | Recurring subjects missing from list |

### Other Findings
- `nlp` vs `llm` may be redundant in 2026 — most NLP news is LLM news
- Removed `tutorial` from Content Type (non-event content should be filtered, not tagged)
- "At least one technology/domain tag" rule breaks for pure financial events — `hardware` fixes this

## Quality Filter Prompt Validation

**Test**: 4 events (2 should pass, 2 should fail)
**Model**: Sonnet
**Result**: **100% correct — passed good content, rejected bad**

| Event | Expected | Got | Quality Score |
|-------|----------|-----|---------------|
| Nvidia earnings (clean) | Pass | Pass | 0.95 |
| Vercept acquisition (standard) | Pass | Pass (with notes) | 0.82 |
| Clickbait/inflated score | Fail | Fail | 0.12 |
| Listicle/non-event | Fail | Fail | 0.25 |

### Refinements Applied
- Added Check 8: Content type gate (event vs. evergreen — reject evergreen)
- Added Check 9: Entity completeness (unnamed entities can't be canonical)
- Added Check 10: Source trust signal (single low-trust source → flag)

## Update Summary Prompt Validation (Stage 3b)

**Test**: 3 scenarios — substantial new info, minimal new info, related event misrouted
**Model**: Sonnet
**Result**: **Correct classification on all 3, critical finding on related events**

| Scenario | has_new_info | significance | Assessment |
|----------|-------------|-------------|------------|
| Nvidia + analyst/Meta/DeepSeek coverage | true | major | Correct |
| Vercept + TechCrunch (same facts) | false | minor | Correct |
| SpaceX merger → co-founder departures | true | major | Correct, but... |

### Critical Finding
Scenario 3 (co-founder departures) correctly identified new info but exposed a pipeline gap: if clustering accidentally routes a **related event** to the update prompt, it gets merged instead of becoming a separate event. Fix: added `is_related_event` escape hatch to the output format with temporal guidance.

### Refinements Applied
- Added `is_related_event` boolean + `related_event_reason` to output
- Added temporal context guidance (>3-5 day gap increases related event likelihood)
- Defined significance levels explicitly (minor/moderate/major)

## Newsletter Extraction Prompt Validation

**Test**: TLDR AI newsletter (Feb 25, 2026) — real newsletter with mixed content
**Model**: Sonnet
**Test data**: 7 real newsletters fetched (4 TLDR AI, 2 Superhuman AI, 1 Radical Data Science)
**Result**: **Functional, two key refinements needed**

### Results
- Extracted 18 items (16 editorial + 2 sponsored)
- Correctly identified both sponsored items (You.com, Salesforce TDX)
- Correctly excluded top-of-newsletter sponsor banner (Wispr Flow)
- Quick Links extracted with thin summaries (acceptable)
- Opinion/analysis pieces included without content type distinction

### Refinements Applied
- Added `content_type` field: news, opinion, analysis, research, quick-link
- Expanded sponsor detection keywords: `(Sponsor)`, `[Sponsor]`, `[Ad]`, `[Paid]`
- Added guidance that "news story" means external verifiable event

## Editor Agent Prompt Validation (Stage 8 — NEW)

**Test**: 2 scenarios — clean distillation and distillation with 6 planted errors
**Model**: Sonnet
**Result**: **Caught all 6 errors with appropriate severity**

### Scenario 1 (Clean)
- Verified: true, confidence 0.96
- Only flag: 73% vs 73.2% rounding — correctly rated minor, no correction needed

### Scenario 2 (6 Planted Errors)
| Error | Caught | Severity |
|-------|--------|----------|
| Fabricated $50M price | Yes | Critical |
| Austin vs. Seattle (wrong city) | Yes | Critical |
| Google vs. Microsoft (wrong employer) | Yes | Critical |
| "Automation" vs. "accessibility" | Yes | Moderate |
| Fabricated analyst praise | Yes | Moderate |
| Unsourced team placement claim | Yes | Minor |

### Refinements Applied
- Added Check 7: Undisclosed specifics (most dangerous fabrication mode)
- Noted: run on every event, fast-path auto-approve if verified + no issues

## Phase 1 Gate Assessment — FINAL

### All Prompts Validated

| Stage | Prompt | Status | Key Finding |
|-------|--------|--------|-------------|
| 1 | Newsletter Extraction | PASS | Added content_type field |
| 2 | Article Extraction | Not tested (standard) | Low risk — readability extraction |
| 3 | Cluster Decision | PASS (12/12) | "New headline" heuristic works |
| 3b | Update Summary | PASS | Added is_related_event escape hatch |
| 4 | Three-Tier Distillation | PASS | Production-quality output |
| 5 | Scoring | PASS (8/8 calibrated) | Added audience-fit context |
| 6 | Tagging | PASS | Fixed taxonomy gaps |
| 7 | Quality Filter | PASS (4/4) | Added 3 new checks |
| 8 | Editor Agent | PASS (6/6 errors caught) | Worth running on every event |

### Verdict: Phase 1 Gate PASSED
All prompts produce consistent, high-quality output on real stories. Refinements have been applied. Ready to proceed to Phase 2.

### Remaining Before Phase 2
- [ ] Full pipeline simulation on all 62 test stories (optional — prompts are validated individually)
- [ ] Finalize embedding model choice (Voyage AI vs OpenAI) — can decide during Phase 2
- [ ] Set up project infrastructure (Docker, FastAPI, PostgreSQL, Celery)

## Test Data Assets
- `test_dataset_feb2026.json` — 62 stories, 10 event clusters
- `test_data/newsletters/` — 7 real newsletter editions (TLDR AI, Superhuman AI, Radical Data Science)
