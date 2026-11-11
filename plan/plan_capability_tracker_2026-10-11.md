# Plan: Capability Tracker ("Releases" tab) — 2026-10-11

**Problem.** Goblin News keeps Mike current on *what happened*. It does not keep him current on *what the tools
can do now*. Claude Code ships ~6 releases and ~270 changelog lines a week; Codex, Cursor and Windsurf add
more; model releases change what is possible. Features like `/code-review` and `/security-review` went
unnoticed for weeks by someone who uses the tool all day. The vetting backtest (2026-09-26,
`outbox/capability-tracker-vetting/REPORT.md`) showed: Jev separates material changes from noise (known
features 0.86–0.95, bug fixes mean 0.11; ~10 notable + ~20 minor items/week for Claude Code), the X reaction
pass returns real practitioner signal, and `/security-review` was **never announced in the changelog** — so
the changelog alone is not enough.

**Product.** A second content type with the same mechanics as the news feed (skim / medium / deep dive,
swipe, bookmarks, read marks, filters, search, RSS), shown as a second tab. The unit is a **capability
change**: one feature, change, removal or model release of one tracked product. Every change gets a
distilled entry (what it is, why it matters, when and when not, how to use, examples, sources) written only
from the vendor's own text. Notable changes and all model releases also get an **"In practice"** section from
X reaction passes at T+3 and T+7 (what it's good at, complaints, how people use it, tips), attributed by
handle. The corpus is backfilled so the tab is a reference from day one, and the feed/RSS is the diff.

**Mike's constraints (2026-10-11):** progressive disclosure, built to be skimmed or deep-dived, "no bullshit,
all distilled, perfect info"; same mechanics as news, different card layout; RSS; Grok scoped to the notable
tier and timed for reactions, scheduled passes only (ad-hoc calls allowed only to tune the prompt before it
runs on schedule); pipeline fetches go through load.party in dev and prod.

**Name (Mike, 2026-10-11): tab = "Releases"**, page label "Release notes, distilled." Internal name stays
capability tracker. Routes `/releases`, `/release/[slug]`, `?release=`; API `/api/releases/…`.

## Quick decisions

- **Same app, same DB, second content type.** Not a separate service. Shares auth, header, theme, API
  plumbing, usage logging, alerts, deploy. Routes `/releases`, `/release/[slug]`, `?release=`; API `/api/releases/…`.
- **Sources are vendor-owned only.** Release notes/changelogs + the product docs site. No press, no blogs.
  Docs are *diffed*, because features land undocumented in changelogs (`/security-review`).
- **Gate = Jev, then Haiku for the gray band.** Same questions as the backtest (kind, material, admin_only).
  Notable ≥ 0.85, candidate 0.60–0.85 (Haiku decides + groups), minor < 0.60 (corpus only, shows as
  one-liners under the version on the product timeline).
- **Writer = Sonnet via the Agent SDK** (same pattern as Event Intelligence), tools restricted to reading the
  collected source texts and writing the entry. Grounding is enforced in code: an entry cannot cite a doc that
  wasn't fetched; every practitioner claim must carry a handle present in the reaction data.
- **Reactions = Grok x_search**, notable tier + every model release, at T+3 and T+7, skipped (section hidden)
  when volume is sparse. Reaction passes re-render only the "In practice" section, never the entry body.
- **Follows and alerts are v2.** RSS per product/filter covers "subscribe to the diff" in v1.
- **Unit = one card per change, not per version.** A feature spanning several versions is one card with
  updates. The product page gives the per-version reading (notable cards + minor one-liners under each
  version). The daily run processes the day's releases together in one budgeted writer session.
- **Models: launch post + model docs page + tool changelog lines are the sources.** System/model cards are
  linked, and only a capabilities/limitations section is extracted if present. Never the primary source.
- **Release register from the news product (news → releases, one direction) = the completeness check.**
  The news side writes a `release_register` row whenever an event concerns a tracked product: a model
  release (fast-lane question fired, or the scorer classed the event as a model release) **or a feature**
  (event title/tags/source URLs match a tracked product's aliases or vendor domains, e.g. "Cursor launches
  Projects", "Claude Code adds …"). The Releases run reads unconsumed rows and asks Jev "is this already
  covered by one of the product's recent changes?" Covered → link the event to the change. Not covered →
  create the change seeded from the event's vendor source URL **and log a coverage gap** (alert in the
  weekly digest, per source), because a gap means a poller or parser missed something. Links run both
  ways in the UI (event shows "Release entry", entry shows "News coverage"). The docs diff is the other
  backstop. Nothing on the news side waits on the releases side.

## Scope rule and waves (Mike, 2026-10-11)

Track a product when: the forum's people build with it daily, it has a machine-readable changelog or docs we
can diff, and its changes alter how you work. The tracked list is visible in the UI with a "request a
tracker" link to a forum thread.

- **Wave 1 (ship):** tools — Claude Code, Codex (CLI + cloud + IDE, one tracker), Cursor, Devin/Windsurf
  (one tracker), Gemini CLI, GitHub Copilot; models — Anthropic, OpenAI, Google.
- **Wave 2 (after wave 1 proves the pipeline):** Claude API + Agent SDK, OpenAI API + Agents SDK, Gemini API,
  MCP spec. Same adapters; Anthropic publishes a dated API release-notes page.
- **Wave 3 (on request):** app builders (Lovable, Replit, v0, Bolt), other agents (Amp, Cline, Aider,
  OpenCode), xAI / DeepSeek / Mistral models.

## Sources (wave 1 trackers)

| Tracker | Release notes | Docs to diff | Notes |
|---|---|---|---|
| Claude Code | `raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` (+ dates from `code.claude.com/docs/en/changelog.md`) | `code.claude.com/docs/llms.txt` → every `/docs/en/*.md` (257 pages) | highest volume; prefixes Added/Fixed/Improved/Changed/Removed |
| Codex CLI | GitHub releases API `openai/codex` (dated, sectioned New Features / Bug Fixes) | `developers.openai.com/codex/llms.txt` → `.md` pages | web changelog page includes raw PR lists; releases are cleaner; ignore `-alpha` tags |
| Cursor | `cursor.com/changelog/rss.xml` (50 posts, back to Mar 2026) | `cursor.com/docs` (check for llms.txt) | prose launch posts; one post = 1–3 changes |
| Windsurf (Devin Desktop) | `docs.devin.ai` changelog page (112 releases, dated) | Windsurf docs section of docs.devin.ai | moved under Cognition after the June 2026 rename |
| Gemini CLI | GitHub releases `google-gemini/gemini-cli` | gemini-cli docs in repo | |
| GitHub Copilot | github.blog/changelog feed filtered to Copilot (already a news source) | docs.github.com Copilot pages | |
| Anthropic models | release register + anthropic.com sitemap + `docs.claude.com` models overview `.md` | model docs pages | model release = a change on the tracker |
| OpenAI models | release register + openai.com news + platform model docs | model docs pages | same |
| Google models | release register + DeepMind/Google AI blogs + Gemini API model docs | model docs pages | same |

Adding a tracker = one row in
`tracked_products` + one or more `capability_sources` rows; no code for sources that use an existing adapter.

## Data model (migration b30)

```
tracked_products      id, slug, name, vendor, kind (tool|model_family), logo, docs_home, is_active
capability_sources    id, product_id, kind (changelog_md|github_releases|rss|docs_index|html_versions),
                      url, config JSONB, last_polled_at, last_hash, is_active
release_entries       id, product_id, source_id, version, released_at, section, text, text_hash (unique),
                      source_url, jev_kind, jev_material, jev_admin, jev_model, haiku_verdict, tier
                      (notable|candidate|minor|noise), change_id (nullable), ingested_at
docs_pages            id, product_id, source_id, url, title, content_hash, content_text, fetched_at
docs_deltas           id, page_id, product_id, seen_at, added_text, removed_text, jev_material, tier,
                      change_id (nullable)
capability_changes    id, product_id, slug (unique), title, kind (new_feature|change|deprecation|model_release),
                      version_first, version_latest, released_at, materiality (1–10),
                      tier1_scan (text, skim bullets), tier2 JSONB {what_it_is, why_it_matters,
                      when_to_use[], when_not_to[]}, tier3 JSONB {how_to_use, examples[], gotchas[],
                      config_refs[]}, in_practice JSONB {volume, good_at[], complaints[], usage[], tips[],
                      mood, as_of} | null, reaction_passes JSONB [], sources JSONB [{url, kind, quote}],
                      status (active|superseded|deleted), first_seen_at, last_updated_at, update_count,
                      embedding vector
capability_change_updates  id, change_id, seen_at, version, summary, entry_ids[]
user_change_bookmarks / user_change_reads   (user_id, change_id, created_at)  — parallel to the event tables
release_register      id, product_id, kind (model|feature), title, url, event_id, source (fastlane|scorer|
                      product_match), seen_at, consumed_at, change_id (nullable), coverage_gap bool
                      — written by the news side, read by the releases run; gaps feed the weekly digest
```

`release_entries` + `docs_deltas` are the full raw corpus (every line, scored). `capability_changes` is what
users see. One change can absorb many entries over time (`/ultrareview` added 2.1.111, improved 2.1.113,
CLI subcommand 2.1.120 → one change with three updates).

## Pipeline (`src/ai_signal/capabilities/`, cron in the agent container)

Stages, run daily at 05:00 UTC (`python -m agent.orchestrator --capabilities`), own advisory lock,
own `pipeline_runs` rows with `stage_stats.capabilities`, `llm_usage_log.pipeline = "capabilities"`:

1. **Poll** every active `capability_sources` row through load.party `load_raw`. Parsers per source kind
   produce `release_entries` (dedup by `text_hash`); docs pollers hash each page, store the new text, and
   write a `docs_deltas` row with the added/removed paragraphs when the hash changes. First poll of a docs
   source is a baseline (no deltas). Changelog first poll = backfill (see below).
2. **Gate** each new entry/delta with Jev (kind, material, admin_only; `jev_client.py`). Tier by the
   thresholds above. Candidates go to Haiku in batches of ~25 with the product name and version: "which of
   these would a daily user want to know, and which lines describe the same feature?" → tier + group key.
3. **Group** notable/candidate items into changes: Jev "same feature?" against the product's open changes of
   the last 45 days (match-gate pattern, p ≥ 0.7 = update to the existing change) else a new change. Model
   releases on a model-family tracker always create a new change.
4. **Write** each new/updated change with Sonnet via the SDK. Runbook `CAPABILITY_WRITER`: tools are
   `get_change_sources` (the grouped entries, deltas, and the matching docs page text — the writer may ask
   for one more docs page by URL from the stored `docs_pages`, never the open web), `create_change`,
   `update_change`. Output shape validated in code (schema, bullet caps, no empty "how to use" — write
   "Not documented by the vendor" instead). Budget $5/run, largest-first like EI, deferred to next run.
5. **Reactions** (`capabilities/reactions.py`, adapted from `pipeline/sentiment.py`): for notable changes and
   all model releases, at `released_at + 3d` and `+ 7d`, Grok x_search with the practitioner prompt from the
   vetting probe. Store the pass; if volume ≠ sparse, a Haiku call renders `in_practice` from the passes
   only, every claim tagged with its handle (validator rejects untagged claims). Change gets the "Updated"
   badge and re-surfaces, same as events. Cap $2/day.
6. **Register reconcile**: consume `release_register`; covered → link; uncovered → seed a change + mark
   `coverage_gap`. Weekly digest reports gaps per product/source so the poller gets fixed.
7. **Invariants + alerts**: `capabilities_run_produced_nothing`, `capability_source_failed` (poll error or
   a docs index shrinking > 20%), `capabilities_cost_anomaly`, weekly digest line in the existing weekly DM.
   Model drift alerts reuse `resolved_model`.

**Backfill** (one-off script, batched): Claude Code full changelog (771 entries ≥ 0.7 → grouped), Windsurf
(254), Cursor (50 posts), Codex (releases since 2026-04). Writer runs in batches of 50 with the quota probe
from EI; no reaction passes for anything older than 30 days. Estimated ~300–400 changes, ~$35 of Sonnet on
the sub, spread over a few nights. Docs pages get a baseline snapshot, no backfilled deltas.

**Cost, steady state:** Jev pennies; Haiku < $0.50/wk; Sonnet ~40 entries/wk × ~10k tokens (< 1% of the
weekly quota); Grok ~10 notable × 2 passes × $0.14 ≈ $3/wk.

## API

- `GET /api/capabilities` — list; filters `products`, `kinds`, `tier` (notable|all), `range`, `after/before`,
  `q`, `sort` (newest|materiality), `limit/offset`. Light rows (no tier3/in_practice).
- `GET /api/capabilities/{slug}`, `/{slug}/updates`, `/{slug}/related` (same product, same kind, embedding).
- `GET /api/capabilities/feed.xml` — RSS with the same filters; per-product feeds are just `?products=claude-code`.
- `GET /api/capabilities/products` — trackers with counts and last-change date (for the sidebar and product pages).
- `/api/user/change-bookmarks`, `/api/user/change-reads` — parallel to the event endpoints.
- Admin: `/api/admin/capabilities/sources` (health per source, last poll, last hash), re-poll, tier override,
  "regenerate entry" and "delete change" (prompt-tuning dataset, same as score adjustments).

## Frontend

- **Content-type config** (`lib/contentTypes.ts`): api base, URL base, modal param, row component, modal
  section list, sidebar filter lists, RSS builder, per-user state endpoints. `FeedList`, `EventModal`
  (→ `DetailModal`), `Sidebar`, `FeedWithSidebar` take the config; the events config reproduces today's
  behaviour exactly. The permalink page and the modal share one section-stack component (today they are two
  copies).
- **Header tabs:** News | Capabilities, active by `usePathname`.
- **Row (skim):** product badge/logo, version, kind badge (New / Changed / Removed / Model), title,
  materiality dot, "In practice" indicator when present, bookmark/read/discuss. Summaries mode shows
  `tier1_scan` bullets.
- **Deep dive sections:** header → tier1 bullets → what it is / why it matters → when to use / when not →
  how to use (code blocks, config refs) → examples → In practice (good at / complaints / how people use it /
  tips, each with handle links; mood line) → sources (vendor links with the quoted line) → update history →
  related changes.
- **Product page** `/capabilities/[product]`: timeline by version; notable/candidate as cards, minor as
  one-liners under their version; RSS link for the product.
- **Sidebar filters:** products (checkboxes), kind, tier (notable only / everything), range, read status,
  bookmarks, search, sort. Per-user saved defaults keyed by content type.
- Dark mode, mobile swipe, prefetch, infinite scroll: inherited.

## Phases and gates

0. **Spike (1 day):** pollers + parsers + Jev gate + raw corpus tables, run on dev through the tunnel against
   all six trackers; one docs baseline + a forced re-poll to prove deltas work. **Gate:** entries/day and
   deltas/day in the expected range; `/security-review`-style docs-only feature shows up as a delta.
1. **Backend (3 days):** b30, grouping, writer runbook + tools + validators, reactions module, API + RSS,
   alerts, tests (parsers, gate tiers, grouping, validators, RSS). **Gate:** 20 live-generated entries
   reviewed by Mike for "no bullshit" — every sentence traceable to a source line.
2. **Frontend (3 days):** content-type refactor with events unchanged, tab, rows, modal, product page,
   bookmarks/read, filters, RSS link. **Gate:** Playwright pass on both tabs, light + dark, mobile swipe.
3. **Reactions + ops (1 day):** T+3/T+7 scheduler, In-practice renderer, Updated badge, crontab, deploy,
   canary (`--capabilities` single-batch run + `check_last_run`). **Gate:** one real notable change goes
   through day 0 → day 3 → day 7 on prod.
4. **Backfill + launch (2 nights):** batched backfill, spot-check 30 random entries, then make the tab
   visible. **Gate:** Mike's call.

v2 candidates: follows + alerts (email digest shares infra with `features/email_digest.md`), "what changed
since I last looked" per product, Gemini CLI / Copilot trackers, forum auto-threads for notable changes.

## Risks and what to watch

- **Materiality tuning.** Expect to move thresholds in the first two weeks; keep the Jev scores on every row
  so a re-tier is a query, not a re-run. Admin tier overrides feed the tuning set.
- **Grouping errors** (one feature split across changes, or two merged). Updates are reversible: a change
  can be split by re-assigning `release_entries.change_id`; add the admin action in Phase 1.
- **Docs noise.** Docs sites restructure; a mass delta day must not become 200 changes. Cap deltas per page
  per day and alert on index shrink/growth > 20%. Reword-only deltas should score low on `material`;
  verify in the spike.
- **Grounding drift.** The vetting run produced one unattributed phrase. Validators, not prompts, enforce
  attribution and source-quote presence; the writer gets the rejection reason and one retry.
- **Quota.** Writer and backfill run under the same 5-hour-window probe as EI; backfill batches defer when
  the window is tight. Reactions are the only real-money line and are capped.
- **Cursor backfill** is 50 posts via RSS; older posts are not needed for v1.

## Spike results (2026-10-11, offline against local copies of the real sources)

Code: `src/ai_signal/releases/` (trackers, fetch via load.party, parsers, gate, poll), models
`models/release.py`, migration **b30** (applied on the dev DB), tests `tests/test_releases_parsers.py` (11).
Dev DB: dedicated `ai-signal-dev-db` container on 127.0.0.1:3204 (portreg `ai-signal-dev-db`); the old
`.env` pointed at 5435, which torippu-db now owns.

| Source | entries | notable | candidate | note |
|---|---|---|---|---|
| Claude Code changelog | 6,424 (405 versions, all dated via the docs mirror) | 215 | 818 | 51 s incl. Jev |
| Codex releases (last 40, 5 stable) | 44 | 5 | 10 | `## Changelog` PR lists skipped |
| Cursor RSS (50 posts) | 50 | 31 | 13 | enterprise/admin posts land in noise/minor as intended |
| Windsurf docs changelog | 724 (111 versions) | 90 | 185 | |
| Gemini CLI releases (13 stable) | 210 | 1 | 7 | bodies are PR titles ("feat(evals): …"); terse → low scores; acceptable, revisit |
| Copilot (github.blog feed, 10 items → 5) | 5 | 3 | 1 | feed is shallow; "weekly releases" round-up posts need splitting by the grouper |

Docs path proved: 3-page mini index → baseline → re-poll with a fabricated feature paragraph in skills.md
(**0.88 notable**) and a "last reviewed" line in settings.md (**0.03 noise**); second changelog poll = 0 new
(dedupe). Live Jev calls ~90–150 ms.

Open before the live run: load.party token for the app is not in the dev `.env` (reading `/etc/load/env` on
the load box is a production read — Mike installs `LOAD_URL=http://127.0.0.1:3201`, `LOAD_TOKEN`,
`LOAD_PRIMARY=true`). Codex docs index links to `learn.chatgpt.com/docs/…` (config updated). Daily docs
re-fetch volume (Claude Code 257 pages + Codex ~190 + models) must respect the 1,000/day app cap shared
with news → `page_budget` rotation (70/50/20 per run) means a docs-only feature can take up to ~4 days to
surface; raise the cap or add a second app token if that is too slow.

---

# FINAL DESIGN (2026-11-11) — supersedes anything above that conflicts

Mike accepted all review recommendations on 2026-11-11 and added: everything lives on
news.promptgoblins.ai (News | Releases | Guides in the header), the three certification guides move
into the site in this release, later curated views ("what happened this week") will join them.
Code lives on branch `feat/releases` (worktree `ai-news-aggregator/wt-releases`).

## What changed versus the October plan

1. **Jev is a noise filter, not a ranker.** `kept = jev_material >= KEEP_MIN (0.60)`. No notable/candidate
   tiers. Importance is the editor's 1-10 `score` (same scale and filter UI as news).
2. **Audience and surface are facets, not demotions.** `audience` ∈ user | builder (hooks, SDK, headless,
   CI, MCP authors) | admin (enterprise policy, gateways, billing). `surface` is parsed from the line
   prefix (`[VSCode]`, `[Claude Tag]`, `[Cloud sessions]`, `[Claude Code on the web]`, `SDK:`, `Windows:` …)
   → cli | vscode | jetbrains | web | slack | sdk | desktop | windows | other. Only admin plumbing is scored low.
3. **Docs diff from one file per product** (`llms-full.txt`, split on `# Title\nSource: <url>`), except
   where the export exceeds load.party's 5 MiB cap (Claude Code: 10 MB) → `docs_index` with a `hot` page
   list fetched daily and the rest in rotation. `fetch_text` raises on a body at the cap.
4. **Single grounded calls, no agent loop.** `releases/llm.py::ask_json(stage, system, prompt)`.
   Code collects the sources; one call writes; a blind QC call checks claims against the sources.
5. **Register = a query over news data.** Events with `event_tags.role='subject'` on a product's
   `entity_slugs` and `event_enrichment.action in (launch_model, launch_product)`.
6. **Vertical slice.** `tracked_products.is_live` gates writing and display. Claude Code goes live first;
   others are polled into the corpus from day one and switched on after their entries pass review.
7. **Backfill = 90 days of full entries** (`ENTRY_WINDOW_DAYS`). Older kept lines stay timeline-only.
   **Weekly per-product digest** is the skim layer, the default RSS item, and a forum DM to Mike.
8. **Guides** are a third section: source files in the repo, rendered in the site's design.

## Pipeline (`src/ai_signal/releases/`, entrypoint `python -m ai_signal.releases.run`)

Own advisory lock (43), own `pipeline_runs` row (`stage_stats.releases = {...}`), `llm_usage_log.pipeline =
"releases"`. Never touches news tables except reading events/tags for the register. Constants in
`releases/config.py`. Daily cron 05:10 UTC (`--daily`); digests Monday 07:10 UTC (`--digests`).

| # | Stage | Module / function | What it does |
|---|---|---|---|
| 1 | poll | `poll.run(only=None)` (exists) | fetch every active source through load.party, parse, dedupe by `text_hash`, Jev-gate new lines, store. Docs: snapshot + `docs_deltas`. First docs poll = baseline. |
| 2 | gate | `gate.gate()` (exists; extend) | Jev: `kind`, `material`, `audience` (choice user/builder/admin). `kept = material >= KEEP_MIN`. Surface parsed in code. Docs deltas use the docs wording. |
| 3 | editor | `editor.run_editor(product_slug=None, limit_calls=None) -> dict` | per live product: pending kept lines + kept docs deltas (oldest first, ≤ `EDITOR_MAX_LINES` per call) plus the product's changes of the last `GROUP_WINDOW_DAYS` as merge targets → JSON: groups `{title, one_liner, kind, score, score_reason, audience[], surfaces[], line_ids[], existing_change_id|null}` and `dropped [{line_id, reason}]`. Code validates every id is accounted for, creates/updates `release_changes` (+ `release_change_updates` when merging into an existing change), sets `editor_state`. Round-up posts (Copilot weekly, Cursor prose) may yield several groups from one line. |
| 4 | writer | `writer.run_writer(budget_usd=WRITER_BUDGET_USD, limit=None) -> dict` | changes with `score >= WRITE_MIN`, released within `ENTRY_WINDOW_DAYS`, product live, `has_entry = false or needs_rewrite`. Sources assembled in code: the change's lines, linked docs deltas, and docs paragraphs retrieved by the backticked identifiers / command names in those lines (`sources.collect_sources(change)`). One Sonnet call → entry JSON. Validators (code): schema, bullet caps, every `sources[].quote` is a normalised substring of a provided source, every backticked token in `how_to_use`/`examples` occurs in the sources, "Not documented by the vendor." when the sources are silent. One retry with the rejection reasons. |
| 5 | qc | `qc.check(change, sources) -> dict` | blind Haiku call: list sentences in the entry not supported by the sources. Any → one rewrite with those sentences named; still failing → entry stored with `qc.failed = true` and NOT shown (`has_entry` stays false). |
| 6 | reactions | `reactions.run_reactions() -> dict` | changes with `score >= REACTION_MIN` or `kind = 'model'`, at `released_at + 3d / + 7d`, not yet done. Grok `x_search` with `from_date = released_at` (35% of news reactions predated the story without it) and the aggregator-handle exclusion list from `pipeline/sentiment.py`. Cost from `cost_in_usd_ticks`. Posts validated in code: URL is an x.com status URL, tweet-ID snowflake time ≥ `released_at`. Volume none/sparse → pass stored, section stays hidden. Else Haiku renders `in_practice {volume, good_at[], complaints[], usage[], tips[], mood, as_of, posts[]}`; every item must end with a handle that is in `posts` (validator) → `release_change_updates(kind='in_practice')`, `last_updated_at` bumped. Daily cap `REACTION_DAILY_CAP_USD`. Never called outside the schedule except by `scripts/` tuning helpers. |
| 7 | register | `register.run_register() -> dict` | upsert `release_register` from news (query above, last 14 days). Unconsumed rows: Jev "is this event the same release as one of these changes?" against the product's changes ±10 days → `covered` (link both ways via `news_events`), else `gap` (logged; digest DM lists gaps). Model-family products: a `launch_model` event with no change **seeds** one (`kind='model'`, sources = the lab's own article text from `articles` + model docs page) → `seeded`. |
| 8 | digest | `digest.run_digests(week_start=None) -> dict` | per live product with ≥1 change that week: `release_digests` row (items sorted by score, minor count, versions) + one Haiku lede (2 sentences, from the items only). One forum DM to Mike with all products' digests + register gaps (reuse the alerts DM sender). |
| 9 | alerts | `alerts.check_releases(run_stats)` | `releases_source_failed` (≥2 consecutive failures or truncation), `releases_run_produced_nothing` (new kept lines but zero changes), `releases_writer_rejects` (validator/QC reject share > 30%), `releases_cost_anomaly`. Via `agent.alerts._send` with cooldowns. |

`run.py`: `--daily` = 1,3,4(+5),6,7,9 · `--digests` = 8 · `--stage X` · `--only-product slug` · `--dry-run`.
Each stage returns a stats dict; a stage exception is recorded in `pipeline_runs.errors` and the run continues.

### Scoring rubric (editor)

10 flagship model generation or a product-defining capability · 9 new top-tier model version / a new mode
of working (e.g. background agents, plugins) · 8 a new command or feature most daily users will adopt, or
a default that changes behaviour for everyone · 7 a useful new command/flag/setting for a real subset ·
6 a notable improvement or option worth knowing · 5 small but real change to behaviour · 4 minor option,
niche surface · 3 cosmetic/admin plumbing · ≤2 should have been dropped. Removals and breaking changes
score by how many people must act. Admin-only plumbing ≤ 4 unless it changes what individual users can do.

### Entry shape (writer output = `release_changes` columns)

`tier1_scan` 2-4 bullets ≤ 140 chars each · `what_it_is` 2-3 sentences · `why_it_matters` 2-3 sentences,
concrete · `when_to_use[]` / `when_not_to[]` ≤ 4 each · `how_to_use` markdown ≤ 900 chars, fenced code
allowed, or exactly "Not documented by the vendor." · `examples[] {title, code, note}` ≤ 3, only from
sources · `gotchas[]` ≤ 4 · `watch_for` one line or null · `sources[] {url, label, kind: changelog|docs|post,
quote}`. Voice: plain, no hype, no marketing adjectives, no "we".

## API contract (`src/ai_signal/api/releases.py`, prefix `/api/releases`)

Only changes with `status='active'` on live products are served.

- `GET /api/releases` — `products`, `kinds`, `audience`, `surfaces` (comma lists), `score_min` (default 6),
  `range` (week|month|3m|all, default month), `after`, `before`, `q` (title/one_liner/text ILIKE, escaped),
  `sort` (newest|score, default newest), `limit` ≤ 100, `offset` → `{items: ChangeSummary[], total, limit, offset}`
- `ChangeSummary`: `id, slug, title, one_liner, kind, score, audience[], surfaces[], product {slug, name,
  vendor, kind}, version_first, version_latest, released_at, last_updated_at, update_count, has_entry,
  has_in_practice, tier1_scan`
- `GET /api/releases/products` → `[{slug, name, vendor, kind, docs_home, is_live, change_count, last_change_at}]` (live first, `sort_order`)
- `GET /api/releases/products/{slug}/timeline?limit=20&offset=0` → `{product, versions: [{version, released_at,
  changes: ChangeSummary[], minor: [{text, surface, kind}], line_count, fix_count}], total_versions}`
- `GET /api/releases/digests?products=&limit=20&offset=0` → `{items: Digest[]}` ; `GET /api/releases/digests/{slug}` → `Digest`
  (`id, slug, title, lede, week_start, product, items[], minor_count, versions[], published_at`)
- `GET /api/releases/feed.xml` (changes, same filters) · `GET /api/releases/digests/feed.xml` (digests, `products`)
- `GET /api/releases/sitemap` → `{changes: [{slug, lastmod}], digests: [{slug, lastmod}], products: [slug]}`
- `GET /api/releases/{slug}` → `ChangeDetail` = ChangeSummary + `what_it_is, why_it_matters, when_to_use[],
  when_not_to[], how_to_use, examples[], gotchas[], watch_for, sources[], in_practice, news_events[],
  updates [{seen_at, version, kind, summary}], lines [{version, released_at, text, source_url, surface}],
  related ChangeSummary[] (same product, ≤3)`. **Static paths are declared before `/{slug}`.**
- User (auth): `GET/POST/DELETE /api/user/release-bookmarks[/{change_id}]`, `GET/POST /api/user/release-reads[/{change_id}]`
  → same shapes as the event equivalents (`{ids: [...]}`).
- Admin (`require_admin`): `GET /api/admin/releases/sources`, `POST /api/admin/releases/changes/{id}/score
  {score, reason}`, `POST …/{id}/hide`, `POST …/{id}/rewrite`.

## Frontend (own components; the news feed code is not refactored)

`/releases` feed (rows: product badge, kind badge, score, title, version, "In practice" marker; summaries
mode shows `tier1_scan` or `one_liner`; modal deep dive with swipe/arrow keys and `?release=slug`;
sidebar: products, kind, audience, surface, score_min, range, read status, bookmarks, search, sort; RSS link) ·
`/release/[slug]` permalink (same section stack as the modal, per-page canonical, TechArticle JSON-LD) ·
`/releases/[product]` product page (digests + version timeline with minor one-liners) ·
`/releases/digest/[slug]` · sitemap + robots updated. Shared primitives may be extracted (swipe hook,
modal shell) but `FeedList`, `EventModal`, `Sidebar`, `EventRow` keep their behaviour byte-for-byte.

## Guides (`/guides`, `/guides/[slug]`)

Source: `frontend/content/guides/<slug>.md` (GFM + frontmatter: title, description, version, updated,
pdf, forum_topic, order) with images in `frontend/public/guides/<slug>/`. Article template in site
typography with a sticky table of contents, version badge, PDF download, "Discuss / changelog" link to the
forum topic. The three certification guides (`content-hub/site/*`) are converted from their single-file
HTML; PDFs are copied to `frontend/public/guides/<slug>/`. `promptgoblins.ai/library/*` gets permanent
redirects to `news.promptgoblins.ai/guides/*` after the new pages are verified live.
