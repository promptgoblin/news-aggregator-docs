# Gotcha: sitemap `lastmod` is not "new" — a site rebuild stamps everything

**Date:** 2026-09-22 · **Where:** `ingestion/aggregators.py` `sitemap` adapter (Anthropic)

## What happened
anthropic.com/news renders its list by script (11 links in the HTML) and puts model launch
pages at the site root (`/claude-opus-5-5`), so the index scrape missed every launch. The
fix read `sitemap.xml` and took URLs with `lastmod` inside 14 days. First live poll ingested
ten 2024-era `/research/` pages and skipped the Opus 5.5 page: a site deploy that day had
stamped hundreds of unrelated pages with one timestamp (`21:47:12`), and the 20-candidate
cap, ordered by that identical timestamp, fell on the wrong ones.

## Rule
Novelty comes from the URL set: a page is new when its URL is not in `articles`. `lastmod`
is ordering only. That needs a first poll that records the whole matching set as seen
(`config.bootstrap_done`, set by the poller), because a converted source already has
articles and "never ingested" can't gate it.

## Containment used
Stale articles were set `processing_status='filtered'` and re-set in a loop until the
Event Intelligence phase started (clustering had already loaded them in memory and would
have written `clustered` over the filter). Check afterwards: no cluster, no event.
