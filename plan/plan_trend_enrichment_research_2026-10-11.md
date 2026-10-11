# Plan (research): Trend engine enrichment layer

---
type: plan
status: research — not approved for build
last_updated: 2026-10-11
depends_on: [entity registry + closed theme list (in progress, parallel), storylines.md M1]
consumers: [public pulse/trending page, storyline pages, SCORER buzz input, historical charts]
---

> **For the implementation agent.** This plan builds on the entity registry and closed theme list being built
> in parallel (entities with aliases, roles subject|mentioned, Haiku-assigned per event, new entities into a
> proposal queue). Do not redesign that layer. Everything below is additive. Read section 0 first: the
> production numbers rule out the naive design.

## 0. Production facts that shape the design (queried 2026-10-11, read-only)

| Fact | Value | Consequence |
|---|---|---|
| Active / merged events | 6,531 / 1,756 (21% merged away) | Count survivors only. Recompute trailing windows nightly so late merges are reflected. |
| Published events per month | Mar 511, Jun 635, Aug 1,278, Sep 1,524 | **Volume tripled from source expansion, not from news.** Raw counts are invalid. Use share of daily mass. |
| Published per weekday, last 90d | Mon 42, Tue–Thu 55–58, Fri 50, Sat 22, Sun 18 | Weekend dips will read as crashes. Normalize by day mass and use weekly windows for display. |
| Old free-text tag `agents` per month | Mar 44, Apr 56, May 38, Jun 13, Jul–Oct 0–1 | The tagger drifted to "AI Agents" / "ai-agents" / "Agentic AI". **Tag history is unusable for trends. Backfill from the new layer.** |
| Regex "agent" share of weekly events | Apr 6 week: 40/141 = 28%. Oct 5 week: 102/397 = 26% | Raw count says "agents up 2.5x". Share says flat. The backtest must show share, never raw counts. |
| source_count | 77% of events have 1 source. Mean distinct sources per event 1.48 | Corroboration is a weak, sparse signal. Use it as a modifier, not a base. |
| update_count | 85% have 0 updates | Update activity identifies the few living arcs. Good storyline seed signal. |
| Events with a `primary` source article | 622 / 6,531 (9.5%) | First-party is rare and informative. Store it. |
| Sentiment coverage by score | 6: 0/2,301. 7: 15/2,908. 8: 1,171/1,173. 9: 143/143 | **Sentiment is gated on score, so it is endogenous.** It must never feed the scorer. It can only modify the index for 8+ events. |
| Mean reactions per sentiment pass | 3.6 | Reaction count carries little information. Stance mix and notable voices carry more. |
| `related_events.relationship_type` | ~150 distinct free-text values | Unusable. Use `event_related_picks` (Jev, 3 clean relations) and storylines instead. |
| Measured cost per Haiku call in the pipeline, last 30d | $37.05 / 13,847 = **$0.0027** | Basis for all Haiku estimates below. |
| Measured cost per Jev call, last 30d | $0.68 / 1,939 = **$0.00035** | Jev is roughly 8x cheaper per call than Haiku. It is the right tool for pairwise membership. |

Known arcs as visible in titles and tier-1 text, weekly counts of matching events:

| Week of | Total | Jev/TypeSafe | "decision model" | rogue-agent | California/Newsom |
|---|---|---|---|---|---|
| Aug 3–24 | 281–332 | 0 | 0 | 0–3 | 3–8 |
| Aug 31 | 280 | 0 | 0 | 4 | 3 |
| Sep 7 | 308 | 0 | 0 | 4 | 4 |
| Sep 14 | 419 | 4 | 2 | 5 | 6 |
| Sep 21 | 381 | 2 | 0 | 2 | 6 |
| Sep 28 | 345 | 8 | 6 | 8 | 7 |
| Oct 5 | 397 | 6 | 7 | 4 | 1 |

These arcs are small: 2–8 events per week. The index must detect a rise from about 0 to 4 events per week against about 350 total. That favors entity-level keys and Poisson-style tests over smooth share ratios.

## 1. Enrichment fields per event

Priority: **MUST** blocks the index. **SHOULD** fixes a known failure mode. **LATER** is useful once it runs.
Costs use measured Haiku at $0.0027 per call. "Fold-in" means the field is added to the Haiku call that the entity layer already makes. That adds about 200–400 output tokens, roughly +$0.001 per event.

### 1a. Fields

| # | Field | Type | Producer | Vis. | Why trending needs it | Backfill over 6.5k | Pri |
|---|---|---|---|---|---|---|---|
| 1 | `event_entities` (entity_id, role subject\|mentioned) | rows | Haiku, parallel layer | public | Primary trend key. Subject drives heat. Mentioned drives co-occurrence, e.g. competitors citing Jev. | Parallel layer's job | MUST |
| 2 | `event_themes` (theme_id) | rows | Haiku, parallel layer | public | Second trend key for long arcs like agents, policy and chips. | Parallel layer | MUST |
| 3 | Requirement on the parallel layer: proposal-queue rows must keep `event_id` and surface form | rows | Haiku | internal | A brand-new entity like Jev is the trend. If it only counts after approval, its first week is lost. Approval must attach history retroactively. | n/a | MUST |
| 4 | `story_class`, `gate`, `class_ceiling`, `passes_8_test`, `raw_score` (pre-rule) | enum, char, int, bool, int | SCORER, already computed in `create_event` and dropped | internal | Separates real releases from satellites, prospective deals and insight pieces. Weights the index. The Jev wave was mostly satellites and prospective items. | Not recoverable. `pipeline_logs` has these only when a rule fired. Re-derive with a Haiku classify, folded into the backfill pass, ≈ $0 extra | MUST |
| 5 | `arc_role` | enum: new, development, reaction, satellite, retrospective | Haiku fold-in. Fallback: satellite from story_class, development when the match gate attached it to an existing event | internal | The novelty signal. A key with many `new` events is an emerging wave. Many `development` events is a living arc. Many `reaction` events is chatter. | fold-in | MUST |
| 6 | `first_seen_day` | date (UTC) | arithmetic: `first_seen_at` | internal | Day attribution. Not `published_at`, which the publish gate can delay. | free | MUST |
| 7 | `source_stats` | jsonb {distinct_sources, distinct_domains, types: {primary, publication, newsletter, aggregator, blog}, has_primary} | arithmetic from articles + sources. Recomputed on update and merge | internal | Hype-farm guard: independent outlet diversity. First-party vs secondary. | free, SQL | MUST |
| 8 | `storyline_id` | uuid FK | storylines job, with Jev as judge | public | Third trend key. Lets a chart show "Jev saga" rather than five unlinked entities. | Jev backfill ≈ $11, see section 5 | MUST for storyline pages. SHOULD for the index |
| 9 | `action` | enum ~18: launch_model, launch_product, open_weights, raise, acquire, partner, compute_deal, earnings_metric, sue, rule, sign_law, propose_law, regulator_action, hire_depart, incident, research_result, deploy_adopt, statement | Haiku fold-in | internal, chart facets | story_class is built for score ceilings and lumps different things together, e.g. funding and partnerships in "deal". `action` gives "launch → clones → revenue" its shape for a key. | fold-in | SHOULD |
| 10 | `is_prospective` | bool | Haiku fold-in. Prior: story_class = prospective | internal | "In talks at $10B" is not "raised $7.5B". Prospective events get down-weighted. They are hype markers. | fold-in | SHOULD |
| 11 | `claim_basis` | enum: self_reported, third_party_data, independent_verification, official_record | Haiku fold-in | internal | Hype guard. The Jev wave had "1T tokens/day" and "25% of Fortune 500" as self-reported claims. A key whose mass is mostly self-reported claims gets a hype flag. | fold-in | SHOULD |
| 12 | `jurisdictions` | text[]: ISO 3166 plus subdivisions such as `US`, `US-CA`, `EU`, `CN` | Haiku fold-in | public facet | The California signing cluster is a jurisdiction trend, not an entity trend. Enables "policy heat by jurisdiction". | fold-in | SHOULD |
| 13 | `event_numbers` | rows: kind, value, unit, currency, as_of, entity_id, is_prospective, claim_basis, key_fact_idx | Haiku fold-in, extracted from `key_facts` | internal first, public on storyline pages | "Hard numbers" stories: ARR, valuation, raise, users, tokens/day, GW, parameters, benchmark, price. Charts such as "Jev ARR claims over time". | fold-in. Mean 5.8 key facts per event | SHOULD |
| 14 | Buzz features from `sentiment_passes` | jsonb {reactions, stance_pos, stance_neg, stance_mixed, notable_voices, sentiment_score, pass2_shift} | arithmetic. Map the 1–2 word stance labels with a dictionary. A notable voice is a role matching a lab, founder, exec or professor pattern | internal | Index modifier on 8+ events only. **Never a scorer input**, because sentiment is chosen by score and runs after scoring. | free, 1,329 events | SHOULD |
| 15 | `actor_type` | on the **entity**, not the event: frontier_lab, big_tech, chinese_lab, startup, oss_project, government, regulator, court, academia, investor, enterprise_adopter, person | registry attribute, set once per entity | public facet | "Startups vs labs" share charts. It is a stable property of the entity, so per-event extraction is waste. | one-time Haiku over the registry, < $1 | SHOULD |
| 16 | `enrichment_version`, `enriched_at`, `enrich_model` | int, ts, text | code | internal | Drift control. Never chart across a version change without backfilling the old range. | n/a | MUST |
| 17 | Activity rows (`event_activity`): event_id, day, kind: created, update, material_update, merge_absorbed, reaction_pass | rows | arithmetic from `event_updates` (summary_fact non-null means material), `event_merges` and sentiment | internal | Living-arc heat. A merge-absorbed duplicate is evidence of more coverage, so it is counted as activity on the survivor, not as an event. | free, SQL. Merges with provenance from Aug 14 on; earlier merges are lost | MUST |
| 18 | Reader engagement: reads, votes, bookmarks per event per day | from `user_read_events`, `event_votes`, `user_bookmarks` | arithmetic | internal | "Readers care" signal, independent of our coverage. Too sparse today. | free | LATER |
| 19 | Emergent topic clusters | rolling 14-day clusters of `hyde_embedding` (HDBSCAN or connected components at about 0.70) | arithmetic plus a Haiku label per new cluster | internal | A closed theme list cannot see a new category such as "decision models" in mid-September. Clusters catch it and feed the theme proposal queue. | free | LATER, SHOULD if the backtest misses Jev at theme level |
| 20 | External volume: HN points, X post counts | ingestion metadata | arithmetic | internal | Independent buzz. The only real defense against our own coverage bias. | partial | LATER |

### 1b. Persisting the SCORER output (MUST, about an hour of work)

`agent/tools.py` `create_event` receives `story_class`, `gate`, `class_ceiling` and `passes_8_test`, passes them to `apply_score_rules`, and then drops them. They only reach `pipeline_logs` when a rule fires. Write them, plus `raw_score`, into `event_enrichment` in the same transaction. Do the same in any rescoring path in `update_event`. With this, every event from deploy day on is labeled by the same rubric that scores it.

### 1c. One Haiku extraction call, not five

Fold fields 5 and 9–13 into the entity/theme Haiku call the parallel layer adds. That call already reads title, tier1, tier2, key_facts and what_this_means. Output schema additions: `arc_role`, `action`, `is_prospective`, `claim_basis`, `jurisdictions[]`, `numbers[]`. Use closed enums, validate in code, and send rejects to `pipeline_logs`. This follows the "pin the spec, not the model" rule. If the parallel call cannot be extended, run a separate call at about $0.003 per event, about $0.18 per day.

Re-enrich on update only when the `EventUpdate` has a non-null `summary_fact`, because that marks a material change. That is about 10–20 calls per day.

## 2. Signals and the index

### 2a. Keys and contributions

Keys are `(key_type, key_id)` with key_type in entity, theme, storyline and jurisdiction. Entity×theme pairs come later.

Each event `e` contributes mass to each key `k` it carries on `first_seen_day`:

```
w(e,k) = role(e,k) × imp(e) × nov(e) × hype(e) / fanout(e,key_type)

role:   subject 1.0 | mentioned 0.25           (themes, storyline, jurisdiction: 1.0)
imp:    6→0.7  7→1.0  8→1.5  9→2.2               (deliberately flat: see 4c)
nov:    new 1.0 | development 0.8 | reaction 0.5 | satellite 0.4 | retrospective 0.15
hype:   × 0.6 if is_prospective, × 0.8 if claim_basis = self_reported   (floor 0.5 combined)
fanout: sqrt(number of keys of this key_type on the event)   (themes: ≥1; caps a mega-story at about √n total)
```

Activity mass on day `d` per key, for development heat: material_update 0.4×imp, plain update 0.15×imp, merge_absorbed 0.2. Daily activity mass per key is capped at 1.0 so one live-blogged event cannot dominate.

Buzz modifier, for 8+ events with sentiment only: `× (1 + 0.1·min(notable_voices,3))`, at most 1.3. It is a modifier, never a base. Events without sentiment are not penalized.

### 2b. Normalization and momentum

```
M_k(d)     = Σ_e w(e,k) on day d  +  activity_k(d)
M_all(d)   = Σ over all published events of imp·nov  (the day's total mass)
share_k(d) = M_k(d) / M_all(d)                         → removes source growth and weekend dips

heat_k(d)  = EWMA of share_k, half-life 4 days
base_k(d)  = mean share_k over days d-90 … d-15        (excludes the last 14d so a rising key does not eat its own baseline)
prior      = share equivalent of 0.5 events/week of mass at imp 1.0
momentum_k = ln( (heat_k + prior) / (base_k + prior) )     → shown as "×N vs usual"

burst_k    = Poisson test on effective 7d count: n7 = Σ_7d M_k / mean event mass,
             λ = base_k × Σ_7d M_all / mean event mass;  z = (n7 − λ)/√(λ + 1)
```

Use momentum for ranking and burst z for the "trending" gate. EWMA alone lags small arcs by about a week. A Kleinberg-style burst state machine comes later if z-tests flicker.

A key with fewer than 21 days of history, or `base_k = 0`, gets a **NEW** flag instead of a momentum value. Jev on Sep 15 is NEW, not "×∞".

### 2c. The "trending" gate (public)

All conditions must hold over the last 7 days:

| Condition | Guards against |
|---|---|
| momentum ≥ ln 2 and burst z ≥ 3 | noise |
| ≥ 3 distinct active events with the key as subject, or theme/storyline member | a single mega-story |
| top event's share of the key's 7d mass ≤ 60% | one event plus its updates |
| ≥ 3 distinct outlet domains across those events, ≥ 1 not an aggregator | hype farms, single-newsletter echo |
| ≥ 1 event with score ≥ 7 and not prospective | pure talk |
| self-reported share of mass < 70%, otherwise shown with an internal `hype` flag and kept off the public page | vendor-claim waves |

### 2d. Failure modes and their mitigations

| Failure | Evidence | Mitigation |
|---|---|---|
| Tagger vocabulary drift | `agents` fell to 0 after June | Closed themes + registry ids. `enrichment_version`. Theme renames are migrations with a rename map. A new theme backfills its history with a Haiku pass over a 180-day embedding candidate set before it is charted. |
| Coverage growth looks like a trend | 3x volume Mar→Sep | Share normalization. Annotate charts with "instrument changes" (source additions, from `sources.created_at`). Per-source cap: no single source contributes more than 40% of a key's 7d mass. |
| Dedup merges shrink counts after the fact | 21% merged, about 15–20% post-publication | Count active survivors only. Merges become activity. Recompute the trailing 30 days nightly. Rows older than 30 days are frozen. |
| Slow-news weekends | Sat/Sun at about 35% of weekday | Share is weekday-invariant. Display weekly buckets. Do not alert on Mon vs Sun deltas. |
| Mega-story inflates every theme | One flagship launch carries 5–6 themes | √fanout, the top-event ≤ 60% gate, and the activity cap. |
| Hype farms and self-reported waves | Jev claims; aggregators provide 2,815 article links | Domain diversity gate, claim_basis and prospective down-weights, the existing publish gate (content-farm-only events never publish). |
| Score–trend feedback loop | trend raises scores and scores weight the trend | Flat `imp`, scorer bump capped at 6→7, and `imp` uses `raw_score` before any trend effect (see 4c). |
| Sentiment selection bias | sentiment only exists on 8+ | Modifier only, never in the scorer, never a base. |
| Late enrichment | Haiku fails, event enriched next run | Nightly recompute window covers it. Alert when more than 5% of the last 24h events are unenriched. |
| Entity proposal latency | the new entity is the trend | Retroactive attach on approval (field 3). Internal index counts pending proposals under a provisional key. |

### 2e. What "reliable" means, and the test

Reliable has four parts. The index recovers known arcs in the right week. It does not invent arcs on flat keys. It is stable day to day. It is robust to the confounds above. Build `scripts/backtest_trends.py` to replay as-of each day from 2026-04-01, using only events with `first_seen_at ≤ d`. Merges cannot be undone historically, which is acceptable.

| Test | Pass criterion |
|---|---|
| Jev arc | TypeSafe/Jev is NEW by Sep 16. It is top 5 entity by momentum in the Sep 14–21 and Sep 28–Oct 5 weeks. PostHog, Cloudflare and Stanford events carry Jev as `mentioned`, so the co-mention edge appears. `event_numbers` holds $40M seed, $10B talks (prospective), $7.5B valuation and $100M ARR with correct `is_prospective`/`claim_basis`. The storyline groups 10 or more of the 15 events. |
| Rogue-agent wave | The agent-safety-incident theme (or equivalent) passes the trending gate in the weeks of Aug 31 and Sep 28. It does not pass in Apr–Jul. |
| California signings | `US-CA` jurisdiction plus the policy theme trends in Sep 7–Oct 1. It returns to baseline by mid-October. |
| Agents long trend (control) | The 6-month share chart for the agents theme is within ±25% of flat, matching the measured 28% → 26%. A raw-count chart, shown side by side, must not be used. |
| Flat-key controls | Microsoft, Nvidia, "enterprise adoption": burst z ≥ 3 on at most 2 days per month each. Earnings days are allowed. |
| Synthetic duplicate injection | Clone one event 5x as if dedup failed. Its key's momentum moves less than ln 1.5 because of the top-event and domain gates. |
| Stability | Spearman correlation of the top-20 keys day over day ≥ 0.7 on weekdays. |
| Editorial precision | For 3 weeks, Mike gets a weekly DM of the top-10 movers. At least 7 of 10 should be judged "yes, that is hot". This is the ship gate for the public page. |

## 3. Storage

| Object | Kind | Contents | Written |
|---|---|---|---|
| `event_enrichment` | table, 1:1 with events, PK event_id | fields 4–7, 9–12, 14, 16 | at create_event and material updates. Buzz after sentiment passes |
| `event_numbers` | table | field 13. Index on (entity_id, kind, as_of) | with enrichment |
| `event_entities`, `event_themes`, `entities`, `themes` | tables | parallel layer | parallel layer |
| `event_activity` | table (event_id, day, kind, weight) | field 17 | at update, merge and sentiment time. Rebuildable from source tables |
| `storylines`, `storyline_events` | tables | per storylines.md §4, plus `storyline_judgments` (pair, Jev p, model, verdict) for audit | storylines job, after the pipeline |
| `trend_daily` | table, PK (day, key_type, key_id) | mass, events, subj_events, n8plus, distinct_domains, self_reported_mass, activity_mass, share, heat, base, momentum, burst_z, flags, calc_version | nightly job at 23:30 UTC, after the 22 UTC run. Recomputes the trailing 30 days. Older rows frozen. Light refresh of today's row after each pipeline run |
| `trend_day_totals` | table (day, total_mass, events) | denominators | same job |
| `mv_trend_current` | materialized view | latest day, ranked, gate pass/fail and reasons | refreshed at the end of the trend job. Read by the API and the scorer payload builder |
| `trend_snapshots` | table (taken_at, consumer: public\|scorer\|digest, key, rank, momentum, payload) | what was actually shown | at each consumer read. Retain 1 year. Audit and backtest ground truth |
| `trend_weekly_notes` | table (week, model, body_md, keys[]) | weekly narrative | LATER |

Retention: keep `trend_daily` forever. Rows exist only on days a key has mass or is inside its EWMA tail (heat > 1e-4). Estimate 1–2k active keys × 365 days, sparse, well under 100 MB per year. Historical charts read `trend_daily` directly. Bump `calc_version` and rebuild all history when weights or formulas change. The rebuild is pure SQL plus Python over about 7k events and takes minutes.

Event time vs nightly: nothing in the index is computed at event time except enrichment and activity rows. The scorer reads `mv_trend_current`, which is at most one pipeline run stale. That is acceptable for a 6→7 nudge.

## 4. Scoring hook

### 4a. Payload line

The payload builder adds at most one line, and only when one of the candidate cluster's **subject** entities, or its storyline, passes the trending gate in `mv_trend_current`. Hype-flagged keys are excluded.

```
TREND: "<key display name>" is running ×<round(exp(momentum),1)> its usual coverage share
(<n7> events from <domains> outlets in 7 days). Treat as evidence of BUZZ only.
```

Themes are not used here. A theme being hot says nothing about this event. Mentioned entities are not used either. Satellites and prospective classes are already capped at 7, so the line is useless for them. Omit it when the payload's own class is one of those.

### 4b. Rule (append to the BUZZ paragraph of SCORER)

```
A TREND line is buzz evidence and nothing more. It can move a 6 to a 7.
It never moves a 7 to an 8, never changes passes_8_test, class_ceiling or the gate,
and never makes a 9. Decide the 8 test before you read the TREND line.
```

### 4c. Why the bump must stay at most +1 and under the ceiling

- **The 6/7 boundary is the only place buzz is legitimate under the rubric.** 8 means "a builder would be behind for missing it", which is substance. 9 is gate-only. Coverage volume is not substance, and "Sources: corroboration makes a story real, not bigger" already says so.
- **Feedback loop.** The index is weighted by score. If trend could lift 7→8, a hot key would lift its own events, which raises its mass, which lifts more events. With a 6→7 cap and a flat `imp` curve (0.7 vs 1.0), the loop gain stays below 1. `imp` uses `raw_score` before rules, and the trend effect is not separately visible. Record `trend_line_shown` in `event_enrichment` so its effect can be measured and removed from `imp` if needed.
- **Hype waves are exactly when the scorer is most at risk.** The Jev clones scored 6–7. A +1 cap means the worst case is a clone wave reading 7 instead of 6. That is the existing BUZZ behavior, not a new failure.
- **Enforced in code, not only in the prompt.** `passes_8_test=false` already clamps to ≤ 7, and a 9 already needs a gate in `apply_score_rules`. Add one more rule there: when `trend_line_shown` is true, `raw_score ≥ 8` and `passes_8_test` is false, log a `trend_overreach` row. It is clamped anyway.
- **Rollout:** 2 weeks in shadow first. Compute and log the line but do not send it. Then go live and compare the 7-rate of trend-shown vs matched not-shown events. Expect +5 to +15 points on the 6/7 split and nothing at 8+.

## 5. LLM judgment vs arithmetic, with cost

Volume basis: about 60 new events per day. Measured: Haiku $0.0027 per call, Jev $0.00035 per call.

| Job | Tool | Why not arithmetic | Per event | Per day | Backfill |
|---|---|---|---|---|---|
| Entities and themes | Haiku (parallel layer) | aliasing, roles | parallel | parallel | parallel |
| arc_role, action, prospective, claim_basis, jurisdictions, numbers | Haiku, folded into the same call | reading comprehension | about +$0.001 folded, or $0.003 standalone | $0.06–0.18 | 6.5k × $0.003 ≈ **$20**, or about $35 with story_class re-derivation. Run in nightly chunks of about 500 against the dedicated account's weekly quota, not in one shot |
| Re-enrich on material update | Haiku | same | $0.003 | about $0.05 | n/a |
| Storyline membership | Jev: "same storyline?" on top-5 candidate pairs from centroid cosine | pairwise semantic judgment. Jev already beats Haiku on the related "same event" gold set | 5 × $0.00035 = $0.002 | about **$0.10** | 6.5k × 5 pairs ≈ **$11** |
| Storyline membership, gray band only (Jev p between 0.35 and 0.65) | Haiku tiebreak | Jev unvalidated on this question | $0.003 on about 15% of events | about $0.03 | about $3 |
| Storyline narrative | DeepSeek via `llm_client` per storylines.md (user-facing rule) | synthesis | only on change | pennies | a few $ |
| Entity actor_type | Haiku, once per registry entity | stable attribute | n/a | about $0 | < $1 |
| Emergent cluster label | Haiku, once per new 14-day cluster | naming | n/a | < $0.02 | n/a |
| Weekly "pulse" narrative over the top movers | Fable, 1 call per week, about 30k tokens in, 2k out. Internal DM first | rare, high-judgment, low volume | n/a | about $0 averaged; verify Fable list price before build | n/a |
| Momentum, burst, gates, source stats, buzz features, activity | **arithmetic** | deterministic, testable, rebuildable | $0 | $0 | $0 |

Steady state: **about $0.20–0.35 per day** on top of the parallel entity layer. One-time backfill is about **$35–50**.

Two decisions for Mike:
1. Jev on "same storyline?" is a different question from "same event?". It needs its own gold set of about 200 labeled pairs drawn from the Jev, rogue-agent and California arcs plus random pairs before it gates public storyline pages. Use Mike's confirmed rule: near-launch reactions belong to the launch, long-term reactions are separate.
2. A Fable weekly narrative conflicts with the rule that user-facing generation goes through DeepSeek. Keep it internal, as a DM to Mike, unless he approves it for public use.

## 6. Build order and effort

| Step | Deliverable | Effort | Prerequisite |
|---|---|---|---|
| 0 | Entity registry and themes live. Proposal rows keep event_id and surface form (field 3) | parallel work | — |
| 1 | `event_enrichment` table. Persist scorer fields plus `raw_score` in `create_event` and rescoring paths | **S** | none. Ship first: every day without it is unlabeled history |
| 2 | `source_stats`, `first_seen_day`, `event_activity` (rebuildable from source tables), buzz features from sentiment | **S** | 1 |
| 3 | Fold the enrichment fields into the Haiku entity call, with enum validation. `event_numbers` table | **M** | 0, 1 |
| 4 | Backfill 3 over 6.5k events in nightly chunks. Re-derive story_class for pre-step-1 events | **S** (plus about 2 weeks of wall clock) | 3 |
| 5 | `trend_daily` and `trend_day_totals` nightly job, `mv_trend_current`, `scripts/backtest_trends.py` with the section 2e tests | **M** | 2, 4 |
| 6 | Internal admin page plus a weekly top-10 movers DM to Mike for 3 weeks. Tune weights. **Ship gate: section 2e passes** | **S** | 5 |
| 7 | Scorer hook in shadow for 2 weeks, then live | **S** | 6 |
| 8 | Storylines M1 using a Jev judge, after the gold-set eval. Storyline keys join the index | **L** (storylines.md) | 0, gold set |
| 9 | Public pulse page: top movers labeled "most covered this week", 6-month share charts with instrument-change annotations, "part of" badges | **M** | 6, 8 |
| 10 | Emergent clusters, reader engagement, external volume, Fable weekly note | **M** each, LATER | 9 |

## 7. Risks that would stop the build

- **The corpus is the instrument.** We measure our own coverage. Source additions, such as the August–September 31-source expansion, change the instrument. Share normalization removes volume effects but not topic mix effects. If backtest charts are dominated by source-addition steps even after the per-source cap, ship storylines and plain counts and **do not ship a public momentum index**.
- **Too little mass.** About 60 events per day and most entities appear less than once per week. If fewer than about 50 keys have enough history to clear the gates in a typical week, the public page will be thin and jumpy. Fall back to a weekly "most covered" list.
- **The backtest misses the known arcs.** If Jev, rogue agents and California are not recovered as specified in section 2e, the formula is wrong for this corpus. Do not tune on the public page.
- **Scorer drift.** If the shadow phase shows the trend line shifting anything at 8 or above, or the 6→7 shift exceeds about 20 points, drop the hook. The index is still useful without it.
- **Labeling.** A public "trending" list rewards hype waves like Jev's. Label it as coverage ("most covered", "rising in our coverage"), never as importance. Keep hype-flagged keys internal.

Do NOT build if step 1 (persisting scorer fields) and the parallel entity layer are not both live. Without them there is no clean history to trend over, and the July–October tag history proves free-text cannot substitute.
