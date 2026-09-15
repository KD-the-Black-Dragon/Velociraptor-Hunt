# Proposal: Command Allies (deferred)

**Status:** Deferred — not active. Do not implement until user opens this change.

**Split from:** `add-ally-improvement` (2026-07-02). Name introductions, player-engulfed rescue AI, and player rescue gratitude ship in `add-ally-improvement` first.

## Why

Good allies need player-directed **Follow** and **Attack** commands so the player can coordinate nearby allies without micromanaging every bump. This was scoped out of the narrowed Ally Improvement module to keep PRs focused.

## What (future)

- Main keyboard **1** → shout *"Follow me!"* — good allies in player FOV enter follow mode
- Main keyboard **2** → shout *"Attack!"* — revert affected allies to default good AI
- Follow persistence, loss-of-track behavior, and turn/input rules per resolved decisions in `design.md`

## Out of scope (handled elsewhere)

- Runtime name introductions → `add-ally-improvement`
- Player-engulfed rescue AI priority → `add-ally-improvement`
- Player rescue gratitude lines → `add-ally-improvement`

## Full design

`design.md` in this folder (resolved decisions + open questions preserved from 2026-07-02 design session).