# Gotcha: live calibration exemplars ran 100% upgrades and inflated every score

**Date:** 2026-09-07 (diagnosed 2026-09-04)
**Area:** Event Intelligence — SCORER subagent (`agent/runbooks.py`, `agent/orchestrator.py`)

## Symptom

Several 9s on days with one flagship release (Sep 3: GPT-6 Astra plus a Flash
variant, a benchmark satellite and a lawsuit filing, all 9). Only 3 of the 36
nines in the 30 days to Sep 4 were model releases; 12 were markets, 8 safety.
The 6-and-under share of published events fell from ~35% (July) to 25%.

## Root causes

1. **The live exemplar feed was one-sided.** From 2026-08-13 the SCORER prompt
   embedded the last 90 days of `score_adjustments`, "balanced" 7 up / 7 down.
   Every adjustment from May through August was an upgrade (14 up, 0 down),
   and `_format_calibration` filled the empty side from the other side, so for
   three weeks the scorer saw fourteen "the editor raised this" examples and
   none the other way.
2. **Editor notes went into the prompt verbatim.** Reasons are written for the
   engineer ("How in the fuck is 'in talks to invest' a 9?", a question about
   per-day weighting cut mid-word). They are tuning input, not rules.
3. **A rubric with floors.** "Floor of 8 for major-lab features", score = max
   (significance, buzz), "+1 for 5+ sources", a per-batch distribution target
   the per-cluster scorer could never see, and a 9 defined as a vibe ("if you
   missed this you're out of the loop"). Floors give permission without
   classification; caps only bite after the model classifies the story, and
   it can describe a story to dodge the class.
4. **Volume.** The 9 rate per event was a flat ~3% since July while event
   volume doubled after the late-July coverage fixes. A fuzzy definition
   behaves like a percentage; a must-read definition has to be volume-invariant.

## Fix (app commit on 2026-09-07)

- `SCORER` rewritten as one rubric: an ordered procedure (what is new → class →
  9 gate → placement against the week), a **closed 9 GATE** (flagship
  generation / operative ruling / closed structural deal / live
  practitioner-impacting incident) and **class ceilings** instead of floors.
  New classes for the failure modes: prospective deals, satellites of a
  headline event, AI-behavior incidents, lawsuits filed, earnings.
- **Curated, balanced exemplars** (`SCORER_CALIBRATION`) replace the live
  fetch. Editor reasons are distilled into the rule behind each correction by
  hand. Never paste raw adjustment reasons into a prompt.
- **Week-context anchors** (`RECENT_TOP_SENTINEL`, `_fetch_recent_top_stories`):
  the week's 8+ events go into the scorer prompt so it places each candidate
  relative to them. Anchors, not a quota — a second gate-passing 9 is still a 9.
- Scorer JSON gained `story_class` and `gate`; the EI runbook clamps a 9 with
  no gate to 8 and routes satellites to updates.
- `score_inflation` alert: more than 2 nines in 24h or 8+ above 35% over 3 days.
- `scripts/eval_scorer.py`: offline replay of a candidate prompt against real
  past clusters (summary-only, chronological, anchors from its own results).
  Run it before shipping any scorer change.

## Rules of thumb

- Adjustment reasons are the dataset; the prompt gets rules derived from them.
- Keep exemplars balanced; a one-sided set steers the model in that direction.
- Prefer ceilings over floors. If you add a floor, expect it to be found.
- Define a top grade as a closed list, then check the frequency it implies.
- The scorer scores one cluster at a time: any rule about distribution or
  relative placement needs context injected, not a target stated.
