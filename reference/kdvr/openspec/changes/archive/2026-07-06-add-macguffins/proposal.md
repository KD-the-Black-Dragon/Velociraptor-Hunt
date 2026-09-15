# Proposal: Victory Objects (Macguffins)

**Status:** Design — not yet implemented.

## Why

Runs today end only in digestion. There is no optional victory path, no discoverable “holy grail” objects, and the past-runs / game-over layer already stubs `ending_kind="macguffin"` with placeholder text. Players who find a legendary object should be able to **end the run in victory** or **keep playing** — and if they keep playing and are later digested, history should still credit the discovery instead of showing only “Digested by {predator}”.

## What

| Area | Deliverable |
|------|-------------|
| Data | `data/macguffins.json` — id, display_name, glyph, fg, examine, min_depth, max_depth, **score** (no weight) |
| Stock content | The Sword of Freedom, The Shield of Justice, The Cup that Heals |
| Spawn | For each definition where `min_depth ≤ floor_depth ≤ max_depth`, **exactly one** instance on that floor; placement mirrors floor-rune BFS spread (distinct tiles, FLOOR-only, NPC blocking) |
| Activation | Step-on (player only), after `pickup_all_items_at()` and `try_activate_floor_rune()` — **not** inventory pickup |
| Victory prompt | `You have found [object name]! Would you like to end your run in victory?` — **Y/n** with capital **Y** / lowercase **n** enforcement (`src/quit_confirm.py` pattern) |
| Confirm (Y) | Immediate game over; ending display via formatter (e.g. **`found The Sword of Freedom!`** when `display_name` starts with `"The "`) |
| Decline (n) | Tile consumed; run continues; discovery recorded for digestion override |
| Digestion override | If any macguffin was found (even after declining victory), digestion game over and Past Runs show **macguffin ending only** (no predator mention) instead of `Digested by {predator}` |
| Movement | `BlocksMovement` for NPCs; player passthrough (same as floor runes) |
| Persistence | Run-level discovery state in autosave snapshot; macguffin entities in entity codec |

**Unchanged:** quit-to-menu does not record a run; autosave wipe on game over stays as today.

## Out of scope

- Inventory macguffins or use-key activation
- NPC macguffin interaction
- Hot-reload mid-run
- Showing `score` on game over recap or Past Runs in v1 (field stored for future use)
- Boss / alternate victory endings beyond macguffins
- Macguffin stat counter on recap (unless user approves in Open Questions)
- Engulfed-player macguffin activation (v1: engulfed branch never reaches step-on chain)
- Screen flash on macguffin step-on (v1: deliberate omission vs runes)

## Capabilities

### New

- `macguffins` — catalog, spawn, step-on activation, optional victory, digestion-ending override

### Modified

- `floor-runes` — shared placement helpers (import or extract); spawn order extended
- `past-runs` — `format_game_over_ending` for `macguffin` kind; optional `macguffin_score` on record (stored, not displayed v1)
- `save-load` — snapshot field for macguffin discovery; `Macguffin` entity component in codec
- `digestion` — game-over ending selection consults macguffin discovery override

## Related specs (create or extend on acceptance)

- New `openspec/specs/macguffins/spec.md`
- `openspec/specs/floor-runes/spec.md` — spawn order note
- `openspec/specs/past-runs/spec.md` — macguffin ending format
- `openspec/specs/save-load/spec.md` — discovery snapshot field
- `data/SCHEMA.md` — `macguffins.json` section

## Full design

`design.md` and PR checklist in `tasks.md`.