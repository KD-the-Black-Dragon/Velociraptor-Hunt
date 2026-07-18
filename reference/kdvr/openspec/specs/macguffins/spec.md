# macguffins Specification

## Purpose

**macguffins** adds optional **victory floor objects**: data-driven entities the player activates by stepping on them (like floor runes, not inventory items). Activation opens a **Y/n victory prompt**. Confirming ends the run immediately with a macguffin ending; declining removes the tile but records discovery so a later digestion still credits the macguffin ending in game over recap and Past Runs instead of `Digested by {predator}`.

Builds on **floor-runes** (placement/movement), **save-load** (discovery snapshot), **past-runs** (ending formatter), and **digestion** (game-over hook). Implementation: `src/data/macguffin_loader.py`, `src/data/macguffin_registry.py`, `src/systems/macguffins.py`, `src/macguffin_victory_confirm.py`, `src/macguffin_discovery.py`, hooks in `GameEngine`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- `data/macguffins.json` catalog (id, display_name, glyph, fg, examine, min_depth, max_depth, score)
- Stock content: The Sword of Freedom, The Shield of Justice, The Cup that Heals
- Spawn: one entity per depth-eligible definition per floor; BFS spread after floor runes
- Step-on activation (player only), after `pickup_all_items_at()` and `try_activate_floor_rune()`
- Victory modal: capital **Y** confirms, lowercase **n** declines (quit-confirm pattern)
- Run-level `MacguffinDiscovery` in autosave snapshot
- Victory game over (`ending_kind="macguffin"`) and digestion override when discovery is active
- `Macguffin` entity component in save codec; player movement passthrough; NPC blocking

### Out of scope

- Inventory macguffins or use-key activation
- NPC macguffin interaction
- Hot-reload mid-run
- Showing `score` on game over recap or Past Runs v1 (stored on `PastRunRecord` only)
- Macguffin counter on recap
- Engulfed-player activation (engulfed branch never reaches step-on chain)
- Screen flash on step-on (deliberate omission vs runes)
- Decline log message

## Requirements

### Requirement: Macguffin catalog

The game SHALL load macguffin definitions from `data/macguffins.json` at startup. Fields SHALL match `data/SCHEMA.md`. Glyph SHALL be exactly one character and MUST NOT be `#`. There is no `weight` field — spawn is deterministic: **one per eligible definition per floor**.

#### Scenario: Stock macguffins load

- GIVEN the shipped `macguffins.json`
- WHEN the game starts
- THEN sword, shield, and cup definitions are available with distinct glyphs and depth bands

### Requirement: Macguffin spawn

After `spawn_floor_rune()` on `new_game()` and `descend_floor()`, the game SHALL call `spawn_macguffins()` with rune tile positions as `placed_positions`.

For each definition where `min_depth ≤ floor_depth ≤ max_depth`, exactly **one** macguffin entity SHALL be placed. If no definitions are eligible, spawn returns `[]` silently.

Placement SHALL reuse floor-rune BFS helpers: distinct tiles, FLOOR-only, exclude `enter_xy` and NPC-blocked tiles, exclude rune tiles and prior macguffin tiles, entrance distance ≥ `MIN_PAIRWISE_SPREAD_BFS` (stock: 20). Partial spawn is not allowed — failure raises `RunePlacementError` and triggers floor regen.

Spawn order: NPCs → items → floor runes → macguffins.

Map pre-validation SHALL use worst-case count `RUNES_PER_FLOOR + len(registry.macguffins)` spread objects.

#### Scenario: Depth 1 spawns sword only

- GIVEN a new game at depth 1
- WHEN floor initialization completes
- THEN exactly one macguffin entity exists (sword)
- AND three floor runes exist

#### Scenario: Depth 7 spawns all three stock macguffins

- GIVEN floor depth 7 with sufficient arena space
- WHEN macguffins spawn after three runes
- THEN three macguffin entities exist on distinct tiles disjoint from rune tiles

### Requirement: Player movement on macguffin tiles

Macguffin entities SHALL have `BlocksMovement`. NPCs SHALL NOT enter macguffin tiles. The player SHALL be allowed to step onto macguffin tiles (movement passthrough exception, same as floor runes).

#### Scenario: NPC blocked, player passes

- GIVEN a macguffin on a floor tile
- WHEN an NPC attempts to enter the tile
- THEN the move fails
- AND the player may move onto the tile

### Requirement: Step-on activation and victory modal

After a successful player move, `pickup_all_items_at()`, and `try_activate_floor_rune()`, the engine SHALL call `try_begin_macguffin_activation()`.

Activation SHALL apply only when the actor has the `Player` tag and no victory modal is already active. Engulfed or stunned players cannot reach this branch.

On activation:

1. `MacguffinDiscovery.record(definition)` — last-found wins on multiple discoveries
2. Macguffin entity cleared immediately
3. `MacguffinVictoryConfirmState.open()` — victory modal active
4. Player turn is **not** consumed at step-on; consumption is deferred until modal resolves

Victory prompt SHALL show two lines with a blank line between:

```text
You have found {display_name}!

Would you like to end your run in victory? (Y/n)
```

Input enforcement SHALL match quit confirm: capital **Y** confirms, lowercase **n** cancels; other keys show *"Please type capital 'Y' or lowercase 'n' only."*

While the modal is active, `modal_blocks_quit()` SHALL be true (Ctrl+Q and Ctrl+S no-op).

#### Scenario: Step-on opens modal without consuming turn

- GIVEN the player moves onto a macguffin tile
- WHEN activation resolves
- THEN the victory modal is active
- AND `player_turn_count` is unchanged
- AND the macguffin entity is removed

#### Scenario: Decline consumes turn

- GIVEN the victory modal is active after step-on
- WHEN the player presses lowercase **n**
- THEN the modal closes
- AND `player_turn_count` increases by 1
- AND discovery remains recorded
- AND no message-log line is added

### Requirement: Victory game over

When the player confirms with capital **Y**, the game SHALL call `_complete_macguffin_victory()`:

- Reset victory modal
- `GameOverState.open()` with `ending_kind="macguffin"`, `detail=display_name`, and `macguffin_score` from definition
- Autosave wipe per `save-load` spec
- Past-run append per `past-runs` spec

Formatted ending SHALL use `format_game_over_ending()`: if `detail` starts with `The ` → `found {detail}!`; else → `found the {detail}!`.

#### Scenario: Victory Y ends run with macguffin ending

- GIVEN the player confirms victory on The Sword of Freedom
- WHEN game over opens
- THEN recap shows `found The Sword of Freedom!`
- AND `ending_kind` is `macguffin` on the past-run record

### Requirement: Digestion override

When digestion completes and `MacguffinDiscovery.active`, `_advance_digestion_modal()` SHALL open game over with macguffin ending (same formatter and `macguffin_score`) instead of `digested`. Recap and Past Runs SHALL show **macguffin ending only** — no predator mention.

#### Scenario: Declined victory then digested

- GIVEN the player found a macguffin and declined victory
- WHEN the player is later digested
- THEN game over shows the macguffin ending string
- AND does not show `Digested by {predator}`

### Requirement: Discovery persistence

`MacguffinDiscovery` SHALL encode in the run snapshot as `macguffin_discovery` (`macguffin_id`, `display_name`, `score`). Empty discovery omits fields or uses empty object; decode yields inactive discovery.

`MacguffinVictoryConfirmState` SHALL NOT persist — `apply_run_snapshot()` resets the modal.

| Hook | `macguffin_discovery` | `macguffin_victory_confirm` |
|------|----------------------|------------------------------|
| `new_game()` | reset | reset |
| `descend_floor()` | preserve | reset |
| `apply_run_snapshot()` | decode | reset |

#### Scenario: Discovery survives save after decline

- GIVEN the player declined victory after finding a macguffin
- WHEN snapshot → restore runs
- THEN discovery state matches pre-save
- AND victory modal is inactive

#### Scenario: Mid-modal load drops modal

- GIVEN the player stepped on a macguffin and the victory modal is open
- WHEN snapshot → restore runs
- THEN discovery is preserved
- AND victory modal is inactive
- AND `player_turn_count` matches step-on value

### Requirement: Entity codec

Unpicked macguffins on the floor SHALL round-trip via `Macguffin` component encode/decode in `src/save/codec.py`. Consumed macguffins are absent from entities; discovery state covers post-activation.

## Stock macguffins

| id | display_name | glyph | min_depth | max_depth | score |
|----|--------------|-------|-----------|-----------|-------|
| `sword_of_freedom` | The Sword of Freedom | `/` | 1 | 8 | 100 |
| `shield_of_justice` | The Shield of Justice | `[` | 4 | 12 | 150 |
| `cup_that_heals` | The Cup that Heals | `"` | 6 | 16 | 200 |

## Technical notes (non-normative)

- Tests: `tests/test_macguffins_pr1.py` … `tests/test_macguffins_pr4.py`
- Victory confirm: `src/macguffin_victory_confirm.py`
- Discovery: `src/macguffin_discovery.py`

## Related specs

| Spec | Relationship |
|------|----------------|
| `floor-runes/spec.md` | Shared placement helpers; spawn order extended |
| `past-runs/spec.md` | Macguffin ending format; optional `macguffin_score` on record |
| `save-load/spec.md` | `macguffin_discovery` snapshot; ephemeral victory modal |
| `digestion/spec.md` | Game-over ending selection consults discovery override |

## Acceptance criteria

1. Depth-eligible macguffins spawn one per definition after runes on distinct spread tiles.
2. Player step-on opens Y/n modal; Y → victory game over; n → continue with discovery recorded.
3. Digestion override shows macguffin ending when discovery is active.
4. Discovery persists in snapshot; victory modal does not.
5. `tests/test_macguffins_pr1.py` through `tests/test_macguffins_pr4.py` green.