# Visual roadmap

`roadmap.html` is the owner's at-a-glance view of Goblin News: what is shipped, what is being built, what
comes next, what waits on what, and which ideas are parked. It shows **sequence and dependencies only. No dates.**

| File | Role |
|---|---|
| `roadmap.json` | The single source of truth. Agents edit this. |
| `build_roadmap.py` | Validates the JSON and writes `roadmap.html`. Standard library only. |
| `template.html` | The page (CSS and JS). Edit only to change how the page looks or behaves. |
| `roadmap.html` | Generated, committed. Never edit by hand. One self-contained file; opens from `file://`. |

## How to update

1. Edit `roadmap.json`. Set the top-level `updated` to today.
2. Rebuild: `python3 roadmap/build_roadmap.py --copy-to /home/mike/dev/promptgoblins/outbox`
   (`--check` validates without writing).
3. Commit `roadmap.json` and `roadmap.html` together, in the same commit as the docs for the work that changed.

The build refuses to write anything if validation fails, and prints one line per problem.

## Schema

```json
{
  "updated": "YYYY-MM-DD",
  "tracks": [{"id": "trends", "name": "Trends and storylines"}],
  "items": [{
    "id": "kebab-case-id",
    "title": "Short name",
    "track": "<track id>",
    "stage": "shipped | building | next | idea | dropped",
    "one_liner": "What it is, under ~120 characters.",
    "depends_on": ["other-item-id"],
    "story": {
      "intent": "What it is for.",
      "key_features": ["The handful of features that define it"],
      "reasoning": "Why it exists and why it sits where it does in the sequence.",
      "open_questions": ["Anything undecided"]
    },
    "docs": ["features/x.md", "plan/y.md"],
    "status_note": "One short line on where it stands. Optional."
  }]
}
```

Required on every item: `id`, `title`, `track`, `stage`, `one_liner`. `story.intent`, `story.key_features` and
`story.reasoning` are required for `building` and `next` items and expected on the rest. Unknown keys are errors.

## Rules

- **No dates.** No due dates, quarters or estimates on items, and none in the prose. The only date is the
  file-level `updated`. If order matters, express it with `depends_on`.
- **Stages.**
  - `shipped`: live or done. Shown compactly, most recent first.
  - `building`: being worked on now, including work that has been approved and is queued behind another building item.
  - `next`: agreed and sequenced, not started.
  - `idea`: parked; not committed. May carry a condition in `status_note` ("only if the weekly posts earn traffic").
  - `dropped`: decided against. Keep it, with the reason in `story.reasoning`, so the decision is not re-argued.
- **Dependencies.** `depends_on` lists the items that must be shipped first. List direct prerequisites only.
  `unlocks` is derived from `depends_on` and never stored. No cycles. A shipped item cannot depend on unshipped
  work, and a live item cannot depend on a dropped one (the build rejects both).
- **A product story is not a spec.** Intent, key features and reasoning in plain language for the owner: what it is
  for, the four to six features that define it, and why it is sequenced where it is. No file names, table names,
  model settings or thresholds. The detail lives in the files listed under `docs`.
- **`one_liner`** stays under about 120 characters (the build warns above that).
- **`docs`** are paths relative to the docs repo root. They are shown as plain text because links would not work
  from `file://`. The build warns if a path does not exist.
- **`status_note`** is one short line. If you cannot verify a status, say so there instead of guessing.
- **When work ships**, move the stage and update `status_note` in the same commit as the work's docs. When a
  feature's dependencies or intent change, update the item then, not later.
- **Order in the file matters for shipped items**: append newly shipped items after the existing shipped ones.
  The page shows the last eight shipped items first and hides the rest behind "show all". Other columns are
  ordered by dependency depth, then file order.
- Adding a track: add it to `tracks`. The page has colours for `core`, `trends`, `audience`, `trackers` and `ops`;
  a new track id shows in grey until a `--t-<id>` colour is added to `template.html` (light and dark) and the id
  to `KNOWN_TRACK_COLOURS`.

## How the page shows dependencies

- Each card lists **Waits on** (prerequisites not yet shipped, in amber), **Built on** (prerequisites already
  shipped) and **Unlocks** (derived) as chips. Selecting a chip jumps to that card.
- A card with unshipped prerequisites carries a "Waiting on N" badge, and its story panel names them.
- Hovering or focusing a card highlights everything upstream ("needed first", dashed) and downstream
  ("unlocked by this", solid), dims the rest, and on wide screens draws connector lines for that chain.
- Within Building, Next and Ideas, items that wait on nothing come first, then the rest by dependency depth.
- `roadmap.html#item-id` opens that item's story.


## Page design (2026-11-11 redesign)

`template.html` is a page fragment (title, style, markup, script; no html/head/body tags). The build writes `roadmap.fragment.html` (the form a hosted page publisher expects) and `roadmap.html` (the same fragment wrapped in a minimal document for opening locally).

The page is built on progressive disclosure: at rest it shows only live work as a board whose columns are the order of work (Now, Then, After that), computed from dependency depth, with lines between adjacent columns. Pointing at a card traces its whole chain, including the long-range links hidden at rest. Selecting a card opens its story in a side sheet. Ideas, Shipped and Dropped are folded away below. Keep it that way: do not add per-card chips, badges or counters to the board.
