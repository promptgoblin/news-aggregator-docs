# Plan: Trends v2 — insight from the curated record

---
type: plan
status: proposed — awaiting Mike's go on direction and one recurring cost
last_updated: 2026-11-11
supersedes: the public "trending index" parts of plan_trends_and_enrichment_2026-10-11.md (steps 5-7, 9)
research: outbox/trend_research_methods_2026-11-11.md, outbox/trend_research_storylines_2026-11-11.md,
          product research summarised in section 2 (four slices, held in session 43)
---

## 1. Why a v2

The October plan was grounded in our own production data but in no prior art, and every weight and
threshold was a judgment call. It also wrote its own stop conditions (research doc §7). Three were hit:

| Stop condition | What happened |
|---|---|
| "If the backtest misses the known arcs, the formula is wrong for this corpus" | Missed 2 of 3 (rogue-agent wave, California signings) |
| "If too few keys clear the gate, fall back to a most-covered list" | 1-10 keys per week, often 1-2 |
| "If source additions dominate the charts, do not ship a public momentum index" | Agents control failed (+34%) from the September source expansion |

The research explains why, and it is arithmetic, not tuning:

- Three events in a week is z 3.05 against a 0.2/week baseline but z 1.4 against 1/week. Only brand-new
  keys can pass. A 2x lift on a 3/week theme needs four weeks to reach z 3.
- The log-ratio's standard error with 3 recent and 10 baseline events is about a factor of 1.9, the same
  size as the 2x threshold. That is the 0.56 day-over-day rank correlation.
- With ~105 keys tested daily at z >= 3, roughly one pass a week is chance.
- No published method is validated on a stream of tens of documents a day. Practitioners at this volume
  floor, widen the window, or switch to editorial grouping.

So the gate is a spike detector by construction, and our real arcs are slow drips of 5-10 stories.

## 2. What real products do (research summary)

- **New, rising and biggest are separate lists, never one blended score.** Google (Top vs Rising),
  Hacker News (/newest, front page, /best), Reddit, GitHub, OpenRouter.
- **Story-centric products show position and plain counts, not scores.** Techmeme runs ~50 headlines a
  day, our volume, and shows no number on any story. Ground News shows "448 sources".
- **Tiny bases get a word, not a percentage.** Google "Breakout", OpenRouter "new", arena "Preliminary".
- **The baseline is stated.** "vs previous period", "vs predicted baseline".
- **Composite scores confuse and attract distrust.** Product Hunt renamed upvotes to points because
  order and number disagreed; none of the investor momentum scores publishes weights.
- **The explanation is the product.** Wikipedia's Top 25 exists "to provide commentary on the reasons";
  its notes tie 25 rows into a handful of stories. Trends.vc is one hand-written market a week.
- **The most-cited AI trend sources lead with a claim and one number.** Epoch ("doubling every 9
  months"), METR ("doubling time of around 7 months"), AI Index takeaways.
- **No AI newsletter computes trends from its own corpus.** They borrow tracker numbers. Readers asked
  how they keep up name curators and "why it matters", never dashboards.
- **Slow arcs are handled by people or by storylines,** not statistics: Techmeme editors, Wikipedia's
  nested "Ongoing", Google's Full Coverage timeline. The published recipe for storyline membership
  (embedding retrieval, then a pairwise judge) is the stack we already run for dedup.
- **Explaining the spike is now standard, and its absence is the best-documented complaint.** Twitter
  added written context after 500,000 "why is this trending?" tweets; Meltwater, Brandwatch Iris and
  Mentionlytics attach the cause to every alert.
- **Acceleration-only trending hides the biggest sustained stories** (Occupy Wall Street never trended
  in New York), which users read as suppression. Pair "spiking" with a separate "most covered".
- **Co-firing triggers must be merged into one item** (Brandwatch names this as a hard problem): an
  entity key and a theme key firing on the same story are one thing to the reader.
- **Fully automatic trend lists with no verification failed publicly** (Facebook Trending, 2016-2018).
- **LLM trend prose is the risky piece:** 20-45% hallucinated insights in multi-document news
  summaries, concentrated in closing takeaway sentences. Grounding and validation are mandatory.

## 3. The principle

We do not measure the world. We hold a rich, curated record: every event has subjects, roles, themes,
a score, an arc role, a claim basis, extracted numbers and an update history. The product is **what
that record shows changing, stated as claims with the events behind them** — not a volume chart.

## 4. What we build

### A. Three plain lists (from what is already built)

| List | Definition | Shown |
|---|---|---|
| New this week | first seen in the last 7 days, 2+ events | name, event count, the events |
| Most covered | top keys by heat (stable at 0.92) | name, "N events this week, usually M" |
| Building | passes a 28-day cumulative test on weekly bins (new, see D) | name, weekly counts, the events |

Rules: no momentum number, no percentage on small bases, counts beside every label, lists stay
separate, nothing shown below a floor of 3 events. The current trending gate becomes an internal
"Spiking" signal only.

### B. Storylines — the unit for arcs

- Membership: retrieve candidates by embedding, then a pairwise judge decides against the storyline's
  one-to-two-sentence scope statement (not the nearest member), with an explicit "same topic only" answer.
- Arc role as a linking rule: a development, reaction or retrospective must find a parent; "new" seeds.
  "Development with no parent" is a free recall metric.
- Ledger per storyline, built from existing fields: date, actor, jurisdiction, arc role, claim basis,
  numbers, score. The storyline page shows the ledger as a timeline. No generated prose at first.
- Lifecycle: one primary storyline per event; dormant at 30 days, closed at 90 (crude on purpose).

**Ship gate before anything public:** a known-arc test set of 15-20 arcs we know happened (Jev,
rogue-agent wave, California signings, and others drafted from the data) plus ~200 gold pairs. The
membership judge must recover the arcs. This replaces the failed burst backtest as the test of record.

### C. "What changed this week" — the insight layer

Code selects storylines and computes every count. The model writes two or three sentences per item,
each citing event ids. A validator checks ids, dates and numbers; uncited closing sentences are banned;
empty sections are allowed. Sections, in order of distinctiveness:

1. **Numbers that moved** — extracted numbers aligned into named series; what was revised, escalated or contradicted.
2. **Claimed, then confirmed** — open promises and self-reported claims later corroborated or disputed.
3. **What changed** — per active storyline, the week's delta against the standing summary.
4. **New players and spread** — who entered a storyline, new jurisdictions, who initiates vs reacts.
5. **New this week / Most covered / Building** — the lists from A.

It goes to Mike as a weekly DM for three weeks first. That is the editorial-precision test the original
plan already required (7 of 10 judged right) and it is the ship gate for a public page.

### D. Small statistical changes worth making (internal signals)

- 28-day cumulative test on weekly bins for the Building list, baseline taken from before the window.
- Shrunk, variance-normalised score for any ranking by change (Monroe et al.), with a baseline floor.
- A date-shuffle null run to measure the real false-pass rate of the gate.
- Fix range parsing in extracted numbers (1,076 dropped) before section C1 depends on them.

### E. What we drop

- **A public momentum index or trending score.** Hit all three stop conditions.
- **The scorer hook** (old step 7). It would feed an unvalidated signal with ~1 chance pass a week into
  scoring, with a feedback risk, for a 6-to-7 nudge.
- **Per-key-type gate tuning** (the jurisdiction burst-gate question). Jurisdictions become a filter and
  a storyline ledger column. Closed.

## 5. Cost

| Item | Basis | Cost |
|---|---|---|
| Storyline judge, steady state | ~60 events/day x ~5 candidate pairs, Jev at $0.00035/call (measured) | ~$0.10/day; ~$0.20 with Haiku tie-breaks |
| Storyline backfill | ~9,000 events x 5 pairs | ~$15 one-off |
| Weekly briefing | one grounded pass over ~420 rows plus per-storyline blurbs | under $1/week on the sub |
| Lists, ledger, statistics | arithmetic | $0 |

Jev is unvalidated on "same storyline?" (it was validated on "same event?"); the gold pairs settle
whether it or Haiku judges.

## 6. Order

1. Known-arc test set and gold pairs (drafted from the data by a strong model; Mike spot-checks if he wants).
2. Storyline membership plus backfill; evaluate against 1. Stop here if arcs are not recovered.
3. Lists (A) and ledger pages on an internal admin page; statistics changes (D).
4. Briefing sections C1-C5 with the validator; weekly DM to Mike for three weeks.
5. Public surface only after the DM passes 7 of 10.

## 7. Where the evidence is thin

- Nothing published shows the storyline recipe recovers slow arcs at our volume; step 1-2 is how we find out.
- No published evaluation of an LLM-written trend note at this scale. The validator and the three-week DM are the guard.
- The claim that distilled records hallucinate less than raw articles is our inference.
- Thresholds in A and the lifecycle numbers in B are guesses until the null run and the test set say otherwise.
