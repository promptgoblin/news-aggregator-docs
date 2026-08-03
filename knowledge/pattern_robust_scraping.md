# Pattern: Robust Scraping (cross-project playbook)

---
type: knowledge
status: current
tags: [scraping, scrape-do, cost, cross-project]
---

**Canonical copy.** Shared by Goblin News (`ai-news-aggregator`) and
giftmochi (`~/dev/giftmochi/docs/knowledge/pattern_robust_scraping.md` is a
pointer here). Solve once: if you improve the pattern in one project, update
this doc and port the change.

## The incident that produced this doc

July 2026: Goblin News burned scrape.do's entire 1,000-request/month free
tier in **3 days** and then silently lost beehiiv newsletter resolution for a
week (Alpha Signal, AI Daily Brief, Import AI → 0 articles; logs showed only
generic 401s). Meanwhile giftmochi had been living happily on the same free
tier for months. The difference was pure usage discipline, not luck.

What burned the quota: new aggregator sources (TechMeme/HN/Grok) surfaced
links to FT, Bloomberg, NYT, Politico. Each 403'd → reflexive scrape.do
fallback **with render=true (5 credits)** → returned a paywall teaser →
failed the quality gate anyway. ~60 guaranteed-failure calls/day × 5 credits.

## The rules

1. **Direct fetch first, with a real browser UA.** Most sites serve
   datacenter IPs fine if the UA looks like Chrome. Free, fast.
2. **Paid proxy (scrape.do) is allowlist-gated, not failure-triggered.**
   A 403 is NOT a reason to spend credits — ask *"can the proxy actually
   succeed here, and is the content worth it?"* first.
   - giftmochi: `DIFFICULT_SITES` list (Amazon/Walmart/LEGO) — only those go
     through scrape.do at all.
   - Goblin News: `_HARD_PAYWALL_DOMAINS` denylist (FT, Bloomberg, WSJ, NYT,
     Economist, The Information, WaPo, SeekingAlpha) — the proxy can beat
     bot walls but not server-side paywalls; skip instantly, 0 credits.
   - Goblin News, since 2026-08-03: ALSO allowlist-gated, same as giftmochi —
     `_JS_RENDER_DOMAINS` (beehiiv/OpenAI/DeepMind, render) +
     `_SCRAPE_DO_RENDERLESS_DOMAINS` (CNBC/Reuters, 1 credit). The original
     "News's URL universe is open-ended, so denylist" rationale died once
     rule 7's summary fallback existed: a long-tail 403 now degrades for
     free, so failure-triggered credits (~30-50 attempts/day observed) buy
     almost nothing.
3. **`render=true` costs 5× — never default to it.** Most anti-bot walls are
   IP-reputation checks; the proxy's IPs beat them without a browser
   (1 credit). Keep an explicit `_JS_RENDER_DOMAINS` list for the few sites
   that genuinely need JS (beehiiv tracker redirects, openai.com,
   deepmind.google). Escalate renderless→render only on evidence.
4. **Cache / dedupe before fetching.** giftmochi: `unfurl_cache` table,
   normalized URL keys (tracking params stripped), 24-48h TTL. Goblin News:
   articles are deduped by URL/resolved_URL against the DB before any fetch.
   Same principle: never pay twice for the same URL.
5. **Monitor the quota, loudly.** `GET https://api.scrape.do/info?token=…`
   returns `RemainingMonthlyRequest`. Goblin News DMs Mike at <150 remaining
   (daily alert cron) and again when the quota recovers after an exhaustion.
   Exhaustion is a silent-decay multiplier — several unrelated-looking
   features degrade at once.
   **Gotcha (learned 2026-08-03): the monthly window is anniversary-based,
   not calendar-month.** The July 2026 exhaustion did NOT reset on Aug 1 —
   "wait for the 1st" is wrong; watch `/info` (the recovery alert does).
6. **Poll frequency matches content velocity.** Lab blogs post a few times a
   month → scrape their index once a day, not every pipeline run.
7. **Degrade to the curator's summary — never silently drop a curated story.**
   Corollary of rules 2-3: once you stop paying to beat paywalls, you must
   not let "couldn't fetch" mean "story doesn't exist." The July 2026 coverage
   audit found the SK-Nvidia $500B deal, the Kimi K3 weights drop, and the
   Nvidia-OpenAI $250B backstop all *discovered* (TechMeme/Grok sweep) then
   *dropped* because the linked page was paywalled, bot-walled, or a junk URL
   — in one run TechMeme surfaced 15 candidates and 2 survived. Curated feeds
   ship an accurate one-paragraph summary with every link; headline + curator
   summary is enough to cluster and score. Goblin News:
   `build_fallback_content()` in `newsletter.py` (used by newsletter,
   TechMeme, and Grok-sweep ingestion), `content_fallback` metadata flag
   exempts the short content from the min-length clustering gate, and
   `curator_summary` is surfaced to the scoring agent so it judges the story,
   not the fetch quality.

## Budget math (free tier = 1,000/month ≈ 33/day)

| Call | Credits |
|---|---|
| renderless proxy fetch | 1 |
| `render=true` | 5 |
| `super=true` (residential) | 10+ |

A "fallback on any 403" reflex at news volume ≈ 300 credits/day. The rules
above hold Goblin News under ~15/day (beehiiv links + rare lab-index misses).

## Where the implementations live

- Goblin News: `src/ai_signal/ingestion/newsletter.py`
  (`_HARD_PAYWALL_DOMAINS`, `_JS_RENDER_DOMAINS`, `_extract_with_scrape_do`),
  `aggregators.py` (`_fetch_index_html` renderless-first, lab-scrape daily
  gating), `agent/alerts.py` (`check_scrape_do_quota`). Tests:
  `tests/test_guards.py::TestScrapeDoPolicy`.
- giftmochi: `app/lib/scrape-do.ts` (`DIFFICULT_SITES`, `requiresScrapeDo`),
  `app/lib/unfurl-cache.ts`.
- giftmochi follow-up candidate: port the quota alert (rule 5) — it has no
  low-quota warning today.
