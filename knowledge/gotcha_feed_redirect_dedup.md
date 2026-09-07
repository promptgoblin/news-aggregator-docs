# Gotcha: a feed whose links redirect to another host defeats URL dedup

**Date:** 2026-09-07
**Area:** Ingestion — `src/ai_signal/ingestion/rss.py` (`_existing_urls`), `aggregators.py`

## Symptom

`Ingested 12 new articles from RSS: Google DeepMind Blog` on every single run
since 2026-08-13. Those 12 were the same 12 posts each time. Each copy went
through embedding, HyDE normalization, clustering, and a Sonnet Event
Intelligence pass that matched it to its existing event and did a link-only
update (~$0.3 per run). 825 duplicate article rows in 25 days, 239
`event_updates` rows made from duplicates, one event carrying 116 copies of
two posts. Canary 1 of the 2026-09-07 scorer deploy spent its entire batch on
them.

## Cause

DeepMind's feed links `deepmind.google/blog/<slug>/`, which redirects to
`blog.google/innovation-and-ai/...`. The article row stored the resolved URL in
both `url` and `resolved_url`; the feed link survived only in
`source_metadata.original_url`, which the dedup query never consulted. Until
2026-08-13 the post-bootstrap watermark cutoff hid this; that cutoff was
removed (it dropped legitimately late entries) on the assumption that "URL
dedup drops re-seen entries". It did, for every feed whose links don't change
host on redirect — DeepMind was the only one that does.

## Fix

- `_existing_urls` now matches `url`, `resolved_url`, and
  `source_metadata->>'original_url'`; the aggregator dedup reuses it.
- `scripts/repair_duplicate_articles.py` cleans the backlog (keeps the
  earliest row per source+url, deletes the rest and the updates/logs made from
  them, recomputes `update_count` and `source_count`). Dry run by default.

## The cleanup's own mistake (same day)

The first production run of the cleanup grouped by (source, url) across ALL
sources. For the Grok sweep a URL is a *citation*, not an identity: one sweep
returns several distinct stories that all cite the same X post or digest
page. 142 such rows were deleted as "duplicates" and 12 events lost their only
article. Recovery: restored the nightly `pg_dump` into a scratch database in
the same Postgres container, `COPY ... TO STDOUT | COPY ... FROM STDIN` the
affected rows into prod-side temp tables, re-inserted the missing rows and
the update rows that referenced them, recomputed `update_count` and
`source_count`, dropped the scratch DB. The script is now RSS-feeds-only.

## Rules of thumb

- Before a bulk delete, diff the plan against what the rows are linked to: an
  event whose only article is in the delete set is a red flag. Better still,
  run the delete, then `scripts/check_invariants.py` — `source_count_matches_linked`
  caught this within a minute.

- Dedup identity must include the URL *as the source gave it to us*, not only
  the URL we ended up fetching. Redirect targets change; feed links don't.
- A source that reports the same "new" count run after run is re-ingesting.
  `SELECT name, count(*), count(DISTINCT url) FROM articles ... GROUP BY name`
  over the last 7 days finds it in one query.
- When removing a safety net (the watermark), grep for the assumption that
  replaces it and test the odd case (redirecting links), not the common one.
