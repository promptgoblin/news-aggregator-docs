# Gotcha: Rate Limit Cascade (April 1-3, 2026)

## What Happened

Event pipeline iteration (5-6 full Sonnet enrichment runs in 2 days while tuning prompts) exhausted the weekly Claude Sonnet credit allocation. This caused the news pipeline's Agent SDK calls to fail with rate limit errors. The news pipeline retried repeatedly, hammering the OpenAI embeddings API with batch requests on each retry attempt. OpenAI rate limited us too. Result: **2 days of zero new stories on the news site.**

## Root Cause

1. Event pipeline uses Sonnet for enrichment (~$1.40-2.20 per run, 40-50 events)
2. Multiple manual re-ingestion runs during prompt iteration burned through weekly Sonnet credits
3. Claude subscription has a separate Sonnet cap that hit 100% before the "all models" cap
4. News pipeline couldn't make Agent SDK calls → retried → hammered OpenAI embeddings → OpenAI 429s too
5. One rate limit cascaded into another

## Resolution

- Upgraded from $100 to $200 Claude plan (5x → 20x usage)
- Topped up OpenAI credits
- Manually triggered pipeline to catch up on backlogged articles

## Prevention / Monitoring Required

Both pipelines need proper monitoring with alerting. Mike will set up external monitoring with webhooks. The pipelines need to expose:

- **Success/failure status** per run
- **Key metrics**: events created, articles ingested, errors, rate limit hits
- **Cost per run** (Agent SDK already tracks this)

### What to monitor:
- Claude subscription usage (Sonnet % and All Models %, weekly + hourly)
- OpenAI API rate limits (embedding RPM)
- Pipeline health: did the last run produce events? Zero output for 12+ hours = alert
- Pipeline errors: count of rate_limit/blocked/failed decisions per run
- Event pipeline cost per run

### What to alert on:
- 0 new news stories in 24 hours
- >5 rate_limit errors in a single pipeline run
- OpenAI returning 429 more than 10 times in a run
- Any pipeline run that completes with 0 events created when articles were ingested

### Design considerations:
- Webhook endpoints for pipeline completion/failure
- Both pipelines should log structured status (JSON) that monitoring can parse
- OpenAI embedding calls need better exponential backoff
- Track credits consumed per run to understand burn rate and predict weekly usage
- Once in steady state, evaluate if $100 plan is sufficient (event pipeline should be ~$15-20/mo steady state vs ~$50-70 during iteration)

## Steady State Estimates

- **News pipeline**: runs 3x daily, main cost driver
- **Event pipeline daily**: ~$0.30-0.50/day once most events are dedup skips (vs $1.40-2.20 during initial ingestion)
- **Event pipeline freshen (weekly)**: ~$2-3
- **Event pipeline discover (monthly)**: ~$1
- **Combined steady state**: should be well within $100 plan limits once iteration stops
