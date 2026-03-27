# Plan Section: Frontend

---
type: plan_section
tags: [frontend, nextjs, ui, design]
last_updated: 2025-02-25
---

**Parent**: [plan/PLAN.md](PLAN.md)

## Overview

Next.js + Tailwind frontend at news.promptgoblins.ai. Must match the Prompt Goblins theme exactly (Goblin Mode light / Chill Mode dark). Core UI: event feed with filters, three-tier content expansion, tag browsing, and "Discuss" button linking to forum threads. Presentation is important but not where the hard decisions are — the pipeline is the product.

## Key Decisions

### Next.js + Tailwind
**Choice**: Next.js with Tailwind CSS.
**Rationale**: Fast development, SSR for SEO (news content should be indexable), matches modern stack expectations. Tailwind allows rapid theme matching.

### Theme Matching
**Choice**: Must exactly match Prompt Goblins visual identity — colors, fonts, spacing, light/dark modes.
**Rationale**: news.promptgoblins.ai is a subdomain. Users should feel like they're on the same platform. Brand consistency.

### Three-Tier Progressive Disclosure
**Choice**: Feed shows T1 (scan) by default. Click expands to T2. Second click or "Deep Dive" button shows T3.
**Rationale**: Efficient consumption. Most users scan. Some want details. Few want the full deep dive. Don't force depth on scanners.

## Design

### Page Structure

```
news.promptgoblins.ai
├── /                   — Main feed (filterable)
├── /event/{slug}       — Single event detail page (SEO-friendly)
├── /tag/{tag}          — Tag-filtered feed
└── /about              — About page, source list
```

### Feed Layout

```
┌─────────────────────────────────────────────────┐
│  [Logo] Goblin News      [Search] [Theme Toggle] │
├─────────────────────────────────────────────────┤
│  Filters: [Score ▼] [Tags ▼] [Time ▼] [Presets] │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌─── Event Card ─────────────────────────────┐  │
│  │ [8] Title of the event                      │  │
│  │     T1 scan line — headline + context        │  │
│  │     [tag1] [tag2] [tag3]  ·  3 sources       │  │
│  │     2h ago  ·  [Discuss (4)]                 │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  ┌─── Event Card (expanded) ──────────────────┐  │
│  │ [9] Major announcement title                │  │
│  │     T2 understand content — what happened,   │  │
│  │     why it matters, key details...           │  │
│  │     [Deep Dive ↓]                            │  │
│  │     [tag1] [tag2]  ·  7 sources              │  │
│  │     4h ago  ·  [Discuss (12)]                │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  [Load More]                                      │
└─────────────────────────────────────────────────┘
```

### Event Card States

1. **Collapsed** (default): Score badge + title + T1 scan + tags + metadata
2. **Expanded**: Above + T2 understand content + "Deep Dive" button
3. **Deep Dive**: Full T3 content inline or separate page (for SEO)

Events with updates show a subtle "Updated" badge and update count on the card.

### Single Event Page (`/event/{slug}`)

For SEO and sharing. Shows all three tiers, source list with links, related events, Discuss button.

**Content tabs on events with updates:**
- **Scan** (T1) — always visible at top
- **Understand** (T2) — default expanded view
- **Deep Dive** (T3) — full synthesis
- **Updates** — chronological list of what changed since initial publish (only shown when event has updates). Shows T2-level summary at top + timestamped update entries below, so users can quickly see "what's new" without re-reading the full distillation.

**Story Timeline** (for events with related events):
```
📰 Story Timeline
├── Jan 15: OpenAI hires Jony Ive for wearable project
├── Mar 22: Details emerge about OpenAI wearable design
└── Jun 8: OpenAI wearable device unveiled  ← you are here
```
Each timeline entry links to the related event's detail page.

### Filter & Sort Controls

**Sort options:**
- **Newest** (default) — by `first_seen_at` descending
- **Last Updated** — by `last_updated_at` descending, surfaces events that have evolved with new info
- **Top Scored** — by `importance_score` descending

**Filters:**
- **Score threshold**: Slider or dropdown (5+ default, 7+, 8+, all)
- **Tags**: Multi-select from tag groups, persistent via URL params
- **Time range**: Today, This Week, This Month, All
- **Presets**: Top Stories, Research, Business, Open Source (from taxonomy)
- Filters update URL for shareability: `?score=7&tags=openai,llm&range=week&sort=updated`

### Dark/Light Mode

Match Prompt Goblins exactly:
- **Light (Goblin Mode)**: White backgrounds (#FFFFFF), dark text
- **Dark (Chill Mode)**: Dark backgrounds (#1E1E2E), light text
- Auto-detect system preference, toggle in header
- Store preference in localStorage

### Discourse Integration UI

- "Discuss" button on each event card
- Shows reply count from Discourse API (cached, updated periodically)
- First click creates thread if none exists, subsequent clicks navigate to thread
- Thread opens in new tab on promptgoblins.ai

## Dependencies & Constraints

### Dependencies
- FastAPI backend API must be running
- Prompt Goblins theme colors, fonts, spacing specs
- Discourse API for thread creation and reply counts

### Constraints
- SEO: Event pages must be server-rendered for search engine indexing
- Performance: Feed should load < 2s, feel snappy on mobile
- Accessibility: Keyboard navigation, screen reader support, color contrast

### Plan Section Dependencies
- Depends on [plan_section_architecture.md](plan_section_architecture.md): API endpoints
- Depends on [plan_section_taxonomy.md](plan_section_taxonomy.md): Tags, scoring, filter presets
- Depends on [plan_section_event_intelligence.md](plan_section_event_intelligence.md): Three-tier content model

## Open Questions
- [ ] Mobile layout: single column with swipe gestures, or just responsive cards?
- [ ] Infinite scroll vs. pagination for feed?
- [ ] Should Tier 3 be lazy-loaded (API call on click) or pre-rendered?
- [ ] RSS icon in header? Prominent or subtle?

## Implementation Notes
- Start with desktop feed, add responsive/mobile after core works
- Use Next.js App Router with Server Components for feed pages
- SWR or React Query for client-side data fetching (filters, lazy T3)
- Extract Prompt Goblins theme tokens (colors, fonts, spacing) into Tailwind config
- og:image generation for social sharing of event pages
