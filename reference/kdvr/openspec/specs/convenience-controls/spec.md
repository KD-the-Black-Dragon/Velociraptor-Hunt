# convenience-controls Specification

## Purpose

Player convenience commands: **autoexplore** and **force-attack**.

**Terminology:** defeated, stunned, digested — no kill/die/death.

---

## Requirements

### Requirement: Autoexplore activation

The game SHALL bind **`` ` ``** (grave / backtick, `KeySym.GRAVE`) to start incremental autoexplore when pre-checks pass.

Pre-checks (no turn consumed; `MessageCategory.DANGER` unless noted):

| Condition | Message |
|-----------|---------|
| `Engulfed` on player | *You're already exploring something's digestive tract.* |
| `fighter.hp * 2 < fighter.max_hp` | *You are too injured to autoexplore.* |
| `Stunned` on player | *You're too tired to move.* |
| Evil in player FOV | *There's an enemy in sight!* |

On success the game SHALL log *You begin exploring.* and start an `AutoexploreSession`.

Autoexplore SHALL NOT start while long rest is active. Long rest SHALL NOT start while autoexplore is active.

#### Scenario: Injured block

- GIVEN player HP is 4/10
- WHEN the player presses `` ` ``
- THEN *You are too injured to autoexplore.* appears
- AND no autoexplore session starts

#### Scenario: Enemy in sight block

- GIVEN an evil NPC is in player FOV
- WHEN the player presses `` ` ``
- THEN *There's an enemy in sight!* appears
- AND no session starts

### Requirement: Autoexplore goals

While autoexplore is active, each step SHALL prioritize:

1. Nearest reachable **known pickup** on an explored tile (floor item, floor rune, or macguffin).
2. Else nearest reachable **frontier** tile (explored tile adjacent to unexplored walkable space).

Tie-breaks SHALL use lowest `(y, x)`.

Pathfinding SHALL use **8-directional** steps (same as player movement). NPC-occupied tiles SHALL be blocked. Closed doors MAY be path targets (opened on step via normal movement).

Autoexplore SHALL advance **one dungeon step** per main-loop iteration, then `render` + `present` (no `REST_FRAME_SLEEP_SECONDS`), so movement animates and the OS message pump stays responsive.

#### Scenario: Known item off-screen

- GIVEN a dagger on an explored tile outside current FOV
- WHEN autoexplore runs
- THEN the player paths to the tile and auto-pickup runs

### Requirement: Autoexplore completion

When no reachable pickup goals and no reachable frontier tiles remain, the game SHALL log *Exploration complete.* and end the session.

There SHALL be **no** max-turn cap.

#### Scenario: Fully mapped floor

- GIVEN the whole floor is explored with no remaining pickups
- WHEN autoexplore runs
- THEN *Exploration complete.* appears promptly

### Requirement: Autoexplore danger interrupts

After each consumed autoexplore turn, the game SHALL evaluate the same danger stops as long rest:

1. Player targeted in combat → *It's hard to rest while under attack!*
2. Evil in player FOV → *Danger approaches!*
3. Good ally in player LOS sees evil → ally alarm line

#### Scenario: Danger mid-run

- GIVEN autoexplore is active on a safe floor
- WHEN an evil NPC enters player FOV after a step
- THEN exploration stops with *Danger approaches!*

### Requirement: Autoexplore animation and cancel

Autoexplore SHALL use the incremental session model shared with long rest (batched steps per frame, fingerprint-based redraw, `REST_FRAME_SLEEP_SECONDS`).

Any **KeyDown** during autoexplore SHALL cancel the session **silently** (no completion or interrupt message), then process the key normally.

`can_issue_idle_command()` SHALL be false during autoexplore.

#### Scenario: Manual cancel

- GIVEN autoexplore is active
- WHEN the player presses any key
- THEN the session ends with no end message

### Requirement: Force-attack activation

The game SHALL treat **Ctrl** + any movement key (arrows, numpad, TYUGHJBNM) as a force-attack when no modal blocks gameplay input.

Ctrl+direction SHALL clear a pending close-door choice without closing a door.

#### Scenario: Adjacent evil

- GIVEN an evil NPC is adjacent in the chosen direction
- WHEN the player presses Ctrl+direction
- THEN melee resolves against that NPC
- AND the player does not change position

### Requirement: Force-attack resolution

When the destination tile has an evil `Fighter`, the game SHALL call normal player melee (`_perform_attack`) without moving.

Otherwise the game SHALL log *You attack the empty air.* and consume a turn. Force-attack SHALL NOT swap with good/neutral NPCs, open closed doors, or move the player.

#### Scenario: Empty swing

- GIVEN an empty floor tile adjacent in the chosen direction
- WHEN the player presses Ctrl+direction
- THEN *You attack the empty air.* appears
- AND a turn is consumed

#### Scenario: Good ally on tile

- GIVEN a good NPC occupies the destination tile
- WHEN the player presses Ctrl+direction
- THEN *You attack the empty air.* appears
- AND the ally does not swap position with the player

### Requirement: Force-attack stunned and engulfed

When the player is **stunned**, Ctrl+direction SHALL log *You're too tired to move.*, consume a turn, and SHALL NOT resolve melee (even if evil is adjacent).

When the player is **engulfed**, Ctrl+direction SHALL be ignored as a modifier and SHALL route to the normal struggle handler for that direction (same as unmodified movement).

#### Scenario: Stunned empty swing

- GIVEN the player is stunned
- WHEN the player presses Ctrl+direction
- THEN *You're too tired to move.* appears
- AND no attack damage is dealt

#### Scenario: Engulfed struggle

- GIVEN the player is engulfed
- WHEN the player presses Ctrl+direction
- THEN struggle behavior runs (not *You attack the empty air.*)