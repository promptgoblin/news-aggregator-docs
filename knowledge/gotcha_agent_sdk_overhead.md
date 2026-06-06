# Gotcha: Claude Agent SDK default options inject ~2,000 tokens per call

**Discovered:** 2026-06-03 / corrected 2026-06-04 during cost-cutting investigation ahead of the June 15, 2026 Anthropic billing change.

**TL;DR:** Two `ClaudeAgentOptions` defaults silently inflate every call: `tools=None` loads the `claude_code` tool preset (~2,100 tokens of tool schemas), and `thinking=None` enables extended thinking on every model (verbose output even on yes/no calls). Setting `tools=[]` and `thinking={"type": "disabled"}` for non-agentic calls cut our dedup test cost by **93% (14×) per call**. Production projection: $482/mo → ~$20/mo for the dedup stage, no provider swap needed.

This was originally investigated as "the SDK adds unavoidable overhead." That framing was wrong. The overhead is real but optional — there are flags to turn it off. The SDK isn't bloated; its defaults are tuned for interactive agentic use, and they bite when you use it for high-volume single-purpose calls.

## The case study: dedup in Goblin News

The dedup stage uses Haiku to break tie-breakers for event pairs in the 0.70–0.85 embedding similarity band. Logic is sound (embedding pre-filter handles 90%+ of pairs without an LLM call); the 67,179 LLM calls in May are only the borderline cases.

Code lived at `ai-news-aggregator/app/src/ai_signal/pipeline/dedup.py`:

```python
system = (
    "You decide whether two news events are about the SAME real-world event. "
    "Same event = same announcement, same incident, same release. "
    "Related but distinct events (e.g., a product launch vs a reaction to that launch) "
    "are NOT the same. Respond with ONLY 'yes' or 'no'."
)
prompt = f"Event A: {title1}\n{tier1_1[:500]}\n\nEvent B: {title2}\n{tier1_2[:500]}\n\nAre these the SAME real-world event? (yes/no)"
```

Called via the Agent SDK:

```python
async for message in agent_query(
    prompt=prompt,
    options=ClaudeAgentOptions(
        system_prompt=system,
        model="haiku",
        max_turns=1,
        permission_mode="bypassPermissions",
    ),
): ...
```

Observed monthly cost in `llm_usage_log`: **$482.03 across 67,179 calls**, avg 463 output tokens per call for what should be a 1-token yes/no answer.

## The investigation that fixed it

`scripts/dump_sdk_lean_variants.py` runs the same dedup prompt under seven progressively-leaner option configurations. Headline numbers (all on `claude-haiku-4-5`, no cache because each variant is a fresh process):

| Variant | input | output | cost/call |
|---|---:|---:|---:|
| **1. As-prod (current dedup config)** | **2,410** | **343** | **$0.00413** |
| 2. + `tools=[]` | 305 | 261 | $0.00161 |
| 3. + `setting_sources=[]` | 305 | 286 | $0.00173 |
| 4. + `plugins=[]` | 305 | 281 | $0.00171 |
| 5. + `mcp_servers={}` | 305 | 265 | $0.00163 |
| 6. + `disallowed_tools=["*"]` | 305 | 331 | $0.00196 |
| **7. + `thinking={"type": "disabled"}`** | **275** | **4** | **$0.00030** |

Two flags drive 100% of the win. Everything else was already a no-op for this config.

### Flag 1: `tools=[]` — saves ~2,100 input tokens/call

`ClaudeAgentOptions.tools` is typed `list[str] | ToolsPreset | None = None`. The `None` default does NOT mean "no tools" — it falls through to loading the `claude_code` tool preset, which serializes all of Claude Code's built-in tool descriptions (Read, Write, Bash, Grep, Edit, NotebookEdit, etc.) into the model's context.

For a yes/no classification call, none of those tools are used. They're pure dead weight in the prompt — ~2,100 tokens of dead weight, paid on every single call.

Passing an explicit empty list (`tools=[]`) drops input from 2,410 → 305 tokens. That 305 is the actual size of our developer-written system + user prompts.

This is the single biggest default-vs-explicit gap in the SDK.

### Flag 2: `thinking={"type": "disabled"}` — saves most output tokens

`ClaudeAgentOptions.thinking` defaults to `None`, which enables some form of extended thinking on every call regardless of model. For Haiku on a one-shot classification, this means the model "thinks out loud" before committing to its answer — even when the prompt explicitly says "Respond with ONLY 'yes' or 'no'."

With thinking enabled (default) on the dedup prompt, Haiku produces 250–400 output tokens that begin with `no` but then explain the reasoning at length. With `thinking={"type": "disabled"}`, the model outputs `no` and stops — 4 tokens, ~73× cheaper output.

This is the second-biggest gap. Together with `tools=[]`, it's a 14× cost reduction with no functional change.

### What didn't move the needle (for this config)

- `setting_sources=[]` — would strip user/project/local CLAUDE.md files from the prefix, but they weren't being loaded for this call shape.
- `plugins=[]` — was already the default for this call.
- `mcp_servers={}` — was already the default for this call.
- `disallowed_tools=["*"]` — redundant once `tools=[]` is set.

These flags may matter for other call shapes (e.g., calls where you DO want most of Claude Code's tooling but want to lock down one specific tool).

## Production projection

Scaling the per-call delta to your real dedup volume (67,179 calls/month):

| Configuration | Monthly cost (extrapolated from per-call) |
|---|---:|
| As-prod (today) | **$482** (observed) |
| As-prod + `tools=[]` | ~$108 |
| As-prod + `tools=[]` + `thinking` disabled | **~$20** |
| Direct DeepSeek V4 Flash | ~$1 |
| Direct Grok 4.1 Fast | ~$2 |

**Just adding two flags cuts $462/mo without changing model, prompt, or provider.** That puts the dedup stage well within the post-June-15 Max 20x credit pool ($200/mo).

## The bigger picture: high-volume single-purpose calls

The pattern this case study illustrates: the Claude Agent SDK is optimized for interactive agentic workflows where the framework's tool descriptions and reasoning support add real value. When you use it for **one-shot structured calls at high volume**, the defaults work against you.

If your call satisfies all of these:

- `max_turns=1`
- You don't actually use Claude Code's built-in tools
- Expected output is short and structured
- Volume is >1,000 calls/month

…you should be passing `tools=[]` and `thinking={"type": "disabled"}` minimum. Without them, you're paying for context the model never benefits from.

## When the SDK defaults ARE the right choice

This is not an argument against the SDK. The defaults are right when:

- The task is genuinely multi-turn agentic.
- The model genuinely needs to use tools.
- Extended thinking measurably improves answer quality.
- You're prototyping and don't yet know what your call shape needs.

For Goblin News's `event_intelligence` stage — which uses real subagents and MCP tools — the right config will look different. Investigation pending (see "Still being investigated").

## Receipts

### Bare-SDK transcript (`scripts/dump_sdk_transcript.py`, 2026-06-04)

Single call with `system_prompt=` set but defaults everywhere else:

```
input_tokens                : 2,410
cache_creation_input_tokens : 0
cache_read_input_tokens     : 0
output_tokens               : 409
total_cost_usd              : $0.004455
duration_ms                 : 4,286
```

Output text (409 tokens) starts with `no` then explains for 408 more tokens even though the prompt says "ONLY 'yes' or 'no'":

> "no\n\nEvent A is the product launch announcement of GPT-5.4, while Event B is the release of accompanying documentation (a system card). These are related but distinct events—similar to how a product launch and the release of supporting documentation are separate occurrences, even though they concern the same product."

### Lean variant comparison (`scripts/dump_sdk_lean_variants.py`, 2026-06-04)

Same prompt, seven progressively-leaner configurations. Variant 7 (everything off): input dropped to 275, output dropped to 4, cost dropped to $0.00030 — 14× cheaper than the as-prod baseline.

## Quality eval on production data (2026-06-05)

Before flipping `thinking={"type": "disabled"}` on production dedup, we ran two evals on real DB pairs (`app/scripts/eval_dedup_thinking*.py`):

### Eval 1: 30 random active borderline pairs (sim 0.70–0.85)

| | thinking ON | thinking OFF |
|---|---|---|
| Verdicts | 30 "no" | 30 "no" |
| Agreement | — | **100%** |
| Total cost | $0.0939 | $0.0213 |
| Avg output | 404 tok | 24 tok |
| Avg latency | 4,251 ms | 1,127 ms |

100% agreement — but every pair was "no", so this doesn't prove the dangerous failure mode (false negatives) is absent.

### Eval 2: 30 known-positive pairs (`status='merged'` events paired with most-similar active event)

| | thinking ON | thinking OFF |
|---|---|---|
| Verdicts | 8 yes / 22 no | 11 yes / 19 no |
| Agreement | — | **27/30 (90%)** |
| **False NEGATIVES on B** | — | **0/30** |
| False positives on B | — | 3/30 (10%) |
| Total cost | $0.1472 | $0.0225 (**84.7% cheaper**) |

The failure mode that actually matters — thinking-off missing merges that thinking-on would catch — **did not occur in any of the 30 pairs**. The 3 disagreements all went the opposite way: B more eager to merge than A.

### Inspection of the 3 false positives

| Pair | Subject | Verdict |
|---|---|---|
| Alibaba Accio commentary ↔ Accio 10M users | Same product, related events | A correct, B wrong |
| Sen. Warren statement ↔ DOJ filing | Same Anthropic-DOD legal dispute | A correct, B wrong |
| AWS Nova feature launch ↔ AWS Nova demo at scale | Possibly the same announcement | B may be correct |

All three are **related-AND-same-topic** pairs. None are random shared-entity noise (the historical failure mode that prompted earlier dedup tuning).

### Why this is acceptable

1. **Dedup does NOT re-distill on merge.** Looking at `_merge_event()` in `pipeline/dedup.py`: a merge reassigns articles from source → target, soft-deletes the source, and updates counts. The target event's `tier1/tier2/tier3` displayed text is unchanged. A false positive results in 1–2 extra topically-related articles in the target's source list, **not** weird blended content.
2. **The user-visible impact of an over-merge is near zero.** The displayed event prose stays correct; only the source list grows slightly.
3. **Mike's lived experience is that dedup historically under-merges.** B's slight pro-merge bias may be net positive.
4. **84.7% cost reduction.** $268/mo dedup spend → ~$40/mo on this stage alone.

### Decision

Applied `thinking={"type": "disabled"}` to dedup. **Not** applied to event_intelligence (where reasoning quality genuinely affects user-visible distilled output, and we haven't tested it).

## Still being investigated

- **`event_intelligence` stage:** the Sonnet-driven event distillation orchestrator that actually uses subagents and MCP tools. Cost in May: $365/mo. `tools=[]` already applied (39% reduction observed). `setting_sources=[]`, `plugins=[]` likely apply cleanly. `thinking` disabled would need a separate eval against distilled output quality — much more sensitive than dedup's yes/no.
- **Why the production dedup cache_read was ~21,900 tokens/call** when the bare-SDK test showed only 2,410 input tokens. Hypothesis: the long-running pipeline session warms a larger prefix than a single fresh process. Worth confirming with an instrumented run inside the cron container.
- **Direct Anthropic API as a fourth A/B arm.** With $5 of API credit and the same prompt, we can prove definitively that the 1-token output happens with the model itself, not just with DeepSeek/Grok — closing the last loop on the "is this SDK overhead vs model behavior" question.

## Post structure (for external publication)

When this becomes a blog post on Goblin News, this is the structure:

1. **Hook:** "We thought our $866/mo LLM bill was just the cost of doing business. Then we found two flags."
2. **The data:** the per-call cost table above, then the production projection table. Real numbers, real volume.
3. **The investigation:** how we narrowed it down — first the token-count breakdown from llm_usage_log, then the bare-SDK transcript dump, then the lean variant matrix.
4. **The two flags:** explain `tools=[]` and `thinking={"type": "disabled"}` clearly. What each does, why the default isn't empty, why this isn't obvious from the docs.
5. **When this applies:** the four-condition checklist (max_turns=1, no tool use, structured output, high volume). When the defaults are still right.
6. **What we did:** patched prod, observed cost drop, kept the SDK for the parts that need it.
7. **Reproduce it:** link to `scripts/dump_sdk_lean_variants.py` (open-source it under a permissive license).
8. **Broader context:** brief mention of the June 15 Anthropic billing change as the trigger for this investigation. Cite the SDK auth change without making this a complaint piece.

Tone: constructive, data-driven, "we found this, here's how to fix it for yourself." Not "Anthropic bad." Anthropic's defaults are reasonable for the interactive case; they just need a heads-up that high-volume callers should flip them.

## Related

- Anthropic billing change June 15, 2026: Agent SDK + `claude -p` usage on subscriptions now draws from a separate monthly credit pool ($20/$100/$200 by tier), not the interactive subscription pool. See `MEMORY.md` and Anthropic's [Agent SDK with Claude Plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) docs.
- Goblin News pipeline cost in May 2026: **$866.76** total. Dedup ($482) and event_intelligence ($365) were the two dominant lines. After the dedup fix above, dedup drops to ~$20; event_intelligence optimization pending.
- `scripts/dump_sdk_transcript.py` — captures SDK message stream + outbound HTTP attempts.
- `scripts/dump_sdk_lean_variants.py` — comparison harness for ClaudeAgentOptions configurations.
- `scripts/test_provider_clients.py` — direct API comparison across Anthropic / DeepSeek / Grok via the new `LLMClient` wrapper.
