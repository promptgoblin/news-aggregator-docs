# Plan: step-6 match gate (cluster → existing event) — 2026-10-05

**Problem.** Clustering Stage 3 attaches a new cluster to the most similar active event of the last 14 days
(cosine ≥ 0.75) and the Event Intelligence runbook said a matched cluster is "an update, never a second
event". Similarity cannot tell a launch from a saga that mentions it. Measured over 30 days: 30% of updates
(219/724) landed on events older than 5 days; 11 events have 6+ updates (GPT-6 Astra: 24); 10% of frontier-lab
posts were filed as updates to events >3 days old. Concrete misfiles: OpenAI's "Introducing GPT-6.1 Sol" →
the Sep 22 price-war event; the Claude Code Mods story → the Sonnet 5.5 launch.

**Fix.** `pipeline/match_gate.py`: after a similarity match, Jev answers "is the new story the SAME occurrence
the existing event describes, or a distinct development?" (same question family as the dedup gate; event age
passed as text). Policy (`match_decision`): p ≥ 0.7 keep · p < 0.2 drop (cluster becomes a new event; the
dropped event is handed to the agent as a `related_event_id` hint) · in between: "uncertain" — kept, but the
agent is told (`match_confidence`) and the runbook now lets it create a NEW event + link related; an uncertain
match to an event older than 5 days defaults to drop (the saga pattern). Every judgment is recorded in
`cluster_match_judgments` (b28). `CLUSTER_MATCH_GATE` = off | shadow | live. Dedup (Jev ≥0.7 + Sonnet with the
product definition) is the backstop for any wrong drop.

## Evals

1. **Offline bench (done 2026-10-05, `resources/jev_eval/step6/`):** 1,014 matches from 30 days replayed
   through the gate question; 201 blind-judged (all p < 0.5 + 60 sampled agreements).
   - p ≥ 0.7: 56/56 matches were right. p < 0.2 on events > 5 d: 0/38 were right. 0.2–0.5 on old events: 33% right.
   - Policy on the judged set: **0 wrong keeps** (nothing buried), 16 wrong drops (8%, mostly late
     commentary on old stories — the staleness gate skips those rather than duplicating).
   - The two real misfiles, replayed against the events they were wrongly filed under: GPT-6.1 Sol → p 0.39,
     old → **drop**; Mods → p 0.04 → **drop**. Control (Sonnet 5.5 on Bedrock → Sonnet 5.5 launch): 0.27 → uncertain → agent.
2. **Shadow (deploying 2026-10-05):** gate records decisions without acting. After ≥ 2 days: export
   `cluster_match_judgments`, run `scripts/jev_eval/step6_report.py`, blind-judge every drop and a sample
   of keeps (`judge.py` on the export). Go live if: wrong-keep rate stays ~0 on keeps, drop precision ≥ 85%,
   drop share ≤ ~15% of matches, Jev no-answer share < 2%.
3. **Live KPIs (weekly, vs the 30-day baseline):**
   - updates landing on events > 5 d old: baseline 30% → target < 15%
   - events gaining ≥ 6 updates in a month: baseline 11 → target ≤ 4
   - frontier-lab posts filed as updates to events > 3 d old: baseline 10% → target < 3%
   - launches fragmented into > 1 event (manual check on the week's model releases): baseline GPT-6.1 Sol = 3
   - regression replay after any question/threshold/Jev change: GPT-6.1 Sol → price-war saga and Mods → Sonnet 5.5
     must stay **drop**; GPT-6 Astra "for work" (Sep 9) → the Sep 3 Astra launch must stay **keep** (p 0.91 on
     2026-10-05) — Mike, 2026-10-06: the same model reaching a new product a few days later is an update, not a new story.

## What to watch for (signs it is hurting)

- **Over-dropping → duplicates.** Dedup merges per day (`event_merges` reason jev-merge + sonnet-merge) rising
  above the pre-live baseline, or `events_created` per run up > 20% with no news reason. A duplicate costs one
  Sonnet distillation (~$0.20) and a dedup merge; the signal to tighten `CLUSTER_MATCH_DROP_MAX` / raise `SAGA_DAYS`.
- **Uncertain flood.** If "uncertain" exceeds ~15% of matches the agent is doing the gate's job; move the bands.
- **Agent ignoring the flag.** An uncertain cluster that the agent still files as an update to a > 5 d event
  shows up as updates-to-old-events not falling; check `pipeline_logs` decisions for "uncertain" clusters.
- **Jev drift.** Model pinned (jev-1.13.0); `jev_model` recorded per row. Re-run the bench before any bump
  (`deploy/runbooks/jev-release-benchmark.md`).
- **Cost/latency.** ~270 judgments/week × $0.00003 = pennies; one Jev call (~0.3–0.7 s) per matched cluster
  inside Stage 3, i.e. ~1–2 min per run at most.
