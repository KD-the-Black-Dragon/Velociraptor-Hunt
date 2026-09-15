# Proposal: Ally Improvement

## Why

Good allies feel anonymous and mechanically passive when the player needs rescue. Knights use generic log names, do not prioritize the predator swallowing the player, and never thank the player for freeing them.

## What

1. **Name introductions** — Good NPCs adjacent to the player (no evil visible to either) introduce themselves once per run; assign `ProperName` from `data/names.json`; log lines from per-entity `introduction` in `entities.json`.
2. **Player-engulfed rescue priority** — Good AI globally prioritizes attacking the predator holding the player when in LOS.
3. **Player rescue gratitude** — Extra log line when the player defeats a predator holding good prey (`data/rescue_gratitude.json`).

## Out of scope

- **Command Allies** (Follow/Attack shouts on keys 1/2) — deferred; see `openspec/changes/deferred-add-command-allies/`.

## Spec target

`openspec/specs/ally-improvement/spec.md` (PR3)

## Design

`openspec/design-work/6c35498a-design-doc.md`