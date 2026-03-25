# Feature: Community Voting

---
type: feature
status: implemented
complexity: C3
tags: [voting, reputation, signal-score, discourse, community]
depends_on: [forum_auth, admin_score_adjust]
required_by: []
---

## User Intent

### Goal
Let users up/down vote events to organically adjust signal scores, weighted by their community reputation. Incentivizes forum participation and surfaces community-validated signal.

### Success Criteria
- Logged-in users can up/down vote any event (one vote per event)
- Votes are transparent — no visible vote counts, just signal score movement
- Signal scores become fractional (2 decimal places) once community voting is active
- Score movement follows diminishing returns — going 5→6 is easier than 9→10
- Votes are weighted by user reputation (Discourse trust level + likes received)
- Consensus mechanism: overwhelming agreement accelerates score movement, but dampened at high scores
- Score movement scales with total membership (more members = more votes needed)
- 10s remain unicorns — extremely hard to reach via voting alone

### User Flow
1. User sees an event, clicks up or down arrow
2. Score adjusts fractionally based on their reputation weight and current score
3. If enough users vote the same way, consensus threshold triggers faster movement
4. User can change their vote (switches direction), but cannot remove it

## Status: Implemented
**Started**: 2026-03-23
**Shipped**: 2026-03-25
**Last Updated**: 2026-03-25

## Design Decisions (from planning discussion)

### Score Display
- Fractional with 2 decimal places (e.g., 7.42) — makes the feed feel alive and algorithmic
- Pipeline still assigns whole-number base scores; fractions come from community voting

### Reputation Weighting
- **Primary signals**: Discourse trust level (0–4) + likes received
- **Secondary signals** (low weight): topics entered, posts read count — activity alone doesn't indicate trust
- Pull reputation data from Discourse API, cache locally
- Reputation weighting helps prevent spam and incentivizes forum participation (flywheel)

### Diminishing Returns Curve
- Going from 5→6 is significantly easier than 9→10
- Logarithmic or exponential dampening as scores increase
- Exact formula TBD — needs modeling with expected vote volumes

### Consensus Mechanism
- If users overwhelmingly agree (e.g., 80%+ in one direction), score moves faster
- But dampened as scores get higher — consensus alone can't easily push to 10
- Threshold for "consensus" scales with total membership to prevent gaming with small groups

### Membership Scaling
- Vote impact decreases as membership grows (more possible voters = need more consensus)
- Prevents early members from having outsized influence as community scales
- Formula should normalize by active voter count, not total membership

### Interaction with Admin Adjustments
- Admin +/- adjustments (from admin_score_adjust feature) are separate from community votes
- Both contribute to final displayed score: `base_score + admin_adjustment + community_adjustment`
- Admin adjustments are not subject to diminishing returns

### Anti-Gaming
- One vote per user per event
- Reputation weighting naturally limits spam accounts (low trust level = near-zero weight)
- New accounts (trust level 0) should have negligible voting power
- Could add rate limiting on votes per hour if needed

## Open Questions (for planning session)
- Exact diminishing returns formula — logistic curve? custom piecewise?
- How to handle score going below 5 (current minimum display threshold)
- Should downvoting be limited to higher trust levels to prevent drive-by negativity?
- Cache invalidation strategy for reputation data from Discourse
- Should we show the user that their vote was counted (subtle animation)?
- Can a sufficiently downvoted event auto-archive (score drops below 3)?
- How does this interact with the "not AI related" flag idea?

## Data Model (preliminary)

```sql
-- New table for vote tracking
CREATE TABLE event_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id),
    user_id UUID NOT NULL REFERENCES users(id),
    direction SMALLINT NOT NULL CHECK (direction IN (-1, 1)),
    reputation_weight NUMERIC(6,4) NOT NULL,  -- snapshot at vote time
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (event_id, user_id)
);

-- Cached reputation from Discourse
CREATE TABLE user_reputation (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    discourse_trust_level INT NOT NULL DEFAULT 0,
    discourse_likes_received INT NOT NULL DEFAULT 0,
    computed_weight NUMERIC(6,4) NOT NULL DEFAULT 0.0,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Events get a new column
ALTER TABLE events ADD COLUMN community_score_adj NUMERIC(6,2) DEFAULT 0.0;
```

## Dependencies
- **forum_auth**: Users must be logged in to vote
- **admin_score_adjust**: Admin adjustments should be built first (simpler, informs this design)
- **Discourse API**: Need to pull trust level + likes received for reputation weighting

## References
- Discourse Trust Level docs: trust levels 0–4 with progressive permissions
- Related: admin_score_adjust feature (builds the +/- UI pattern this extends)

## Definition of Done

### Acceptance Criteria
- [ ] Up/down vote buttons on event rows and modal
- [ ] Score updates visually within ~1 second of voting
- [ ] Reputation weight correctly pulled from Discourse and applied
- [ ] Diminishing returns verified — voting from 9→10 requires significantly more consensus than 5→6
- [ ] Score displayed as fractional (2 decimal places)
- [ ] Cannot vote without being logged in
- [ ] One vote per user per event enforced
- [ ] Admin adjustments and community votes both reflected in displayed score

### Docs (Standard)
- [ ] Implementation Notes updated
- [ ] Knowledge entry created if algorithm tuning takes >30 min
- [ ] No [PLACEHOLDER] markers remain
