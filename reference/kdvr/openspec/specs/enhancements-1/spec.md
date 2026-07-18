# enhancements-1 Specification

## Purpose

Quality-of-life improvements on the shipped core roguelike: **wait/pass turn**, **TYUGHJBNM keyboard movement**, **passive natural HP recovery**, and **stunned movement/wait that passes time**. Ships before the on-hold vore module.

**Terminology** inherits core policy: defeated, stunned, digested — no kill/die/death.

## Controls (summary)

| Input | Action |
|-------|--------|
| Arrows / numpad | 8-direction movement (unchanged) |
| `Y` `G` `J` `N` (Shift) | Cardinal movement (north, west, east, south) |
| `T` `U` `B` `M` (Shift) | Diagonal movement |
| `H` (Shift), numpad `5`, `.` | Wait / pass turn |
| `5` (main keyboard) | Rest until healed or danger |
| `,` `i` `d` `w` `W` `q` `v` | Inventory category commands (see `inventory-items` spec) |

```text
T   U
  Y
G H J
  N
B   M
```

## Requirements

### Requirement: Pass Turn

The player SHALL pass their turn using numpad **5**, **period** (`.`), or **`H`**. Wait is silent when not stunned. When stunned, wait SHALL show *"You're too tired to move."* Monsters SHALL act afterward.

#### Scenario: Conscious wait

- GIVEN a player who is not stunned
- WHEN the player presses `H`, numpad 5, or period
- THEN the message log does not add a wait message
- AND monster turns execute

#### Scenario: Stunned wait

- GIVEN a stunned player
- WHEN the player presses `H`, numpad 5, or period
- THEN the message log shows *"You're too tired to move."*
- AND monster turns execute

### Requirement: Keyboard Movement

The player SHALL move in eight directions using **`TYUGHJBNM`** in addition to arrows and numpad. `H` SHALL NOT move the player (wait only).

#### Scenario: TYUGHJBNM cardinal move

- GIVEN a walkable tile north of the player
- WHEN the player presses `Y`
- THEN the player moves north

### Requirement: Natural Recovery

Every **8** player turns, if player HP is below max HP, the player SHALL recover **1** HP silently. At max HP, no recovery. If recovery brings HP above 0 from stunned, the log SHALL show *"You are no longer stunned."*

#### Scenario: Regen on eighth turn

- GIVEN a player at 20/30 HP
- WHEN the player consumes 8 player turns
- THEN the player has 21/30 HP
- AND no regen message is logged

#### Scenario: Regen clears stunned

- GIVEN a stunned player at 0 HP
- WHEN natural regen restores HP to 1 on the 8th turn boundary
- THEN stunned state is cleared
- AND the message log shows *"You are no longer stunned."*

### Requirement: Stunned Movement Turn

When stunned, pressing a movement key SHALL NOT move or attack. The message log SHALL show *"You're too tired to move."* and the world phase SHALL advance. This applies to any direction key including into walls.

#### Scenario: Stunned movement passes time

- GIVEN a stunned player at 0 HP
- WHEN the player presses a movement key
- THEN the player does not move
- AND the message log shows *"You're too tired to move."*
- AND monster turns execute

### Requirement: Player Turn Accounting

A player turn SHALL be consumed when: the player waits, successfully moves or bump-attacks, attempts movement while stunned, or successfully wields, wears, quaffs, or evokes an item. Pickup (walkover and `,`), drop, and inventory inspect SHALL NOT consume a turn. Wall-blocked moves (non-stunned) and unrecognized keys SHALL NOT consume a turn.

### Requirement: Player Turn Hook

The game SHALL expose `on_player_turn_consumed` so other modules can run logic after each consumed player turn without modifying the engine.

### Non-Requirement: Inventory While Stunned

Only **movement** (and wait) uses the tired message while stunned. Inventory category commands SHALL NOT show the tired message while stunned. Successful quaff while stunned SHALL advance the world phase per core AC6. Engulfed pack blocking is specified in `inventory-items` and `vore` specs.

### Requirement: Rest Until Healed or Danger

The player SHALL press main keyboard **`5`** (not numpad **5**) to **rest**: repeated wait turns until a stop condition. Numpad **5** SHALL remain a single-turn wait. Rest turns are **silent** (no per-turn tired message while stunned). Rest **begins** with *"You start resting."* (**`ROUTINE`** grey).

**Pre-checks** (no turn consumed):

| Condition | Message | Color |
|-----------|---------|-------|
| Engulfed | *"This is no time to rest!"* | **`DANGER`** red |
| HP at max | *"You are already at full health."* | **`ROUTINE`** grey |
| Evil in player FOV | *"It's too dangerous to rest now!"* | **`DANGER`** red |

**Stop conditions** (priority order; first match ends rest):

| Priority | Condition | Message | Color |
|----------|-----------|---------|-------|
| 1 | Player targeted by melee or ranged attack (hit, miss, or 0 damage) | *"It's hard to rest while under attack!"* | **`CAUTION`** yellow |
| 2 | Evil enters player FOV | *"Danger approaches!"* | **`CAUTION`** yellow |
| 3 | Good ally in player LOS sees Evil (ally LOS) | *"{Name} shouts in alarm!"* | **`CAUTION`** yellow |
| 4 | HP reaches max | *"You are fully healed."* | **`POSITIVE`** green |
| 5 | **100** rest turns elapsed | *"You finish resting."* | **`ROUTINE`** grey |

Good NPC alarm shouts SHALL occur **only** during an active rest loop — never while the player is not resting.

Stunned players MAY rest when pre-checks pass.

Rest SHALL run **incrementally** across main-loop frames (not one blocking input handler). While resting, the loop SHALL `present()` every frame so the OS does not treat the app as hung. The screen SHALL re-render when visible state changes (HP, stunned, FOV-visible entity positions, log entries); otherwise up to **16** silent turns MAY batch per frame without re-rendering.

Any **KeyDown** during rest SHALL **cancel** rest (no automatic end message) and then run the normal handler for that key — movement, wait, inventory, rest, quit confirm, etc. Input is polled before each rest animation frame.

#### Scenario: Manual rest interrupt

- GIVEN the player is resting
- WHEN the player presses any gameplay key (e.g. `i`, numpad `5`, an arrow)
- THEN rest stops without an automatic end-reason message
- AND that key's usual action runs (inspect inventory, wait one turn, move, etc.)

#### Scenario: Pre-check at full health

- GIVEN a player at max HP
- WHEN the player presses main keyboard `5`
- THEN the log shows *"You are already at full health."* in red
- AND no turn is consumed

#### Scenario: Pre-check evil in sight

- GIVEN an evil NPC visible in player FOV
- WHEN the player presses main keyboard `5`
- THEN the log shows *"It's too dangerous to rest now!"* in red
- AND no turn is consumed

#### Scenario: Rest heals to full

- GIVEN an injured player with no evil in player FOV
- WHEN the player presses main keyboard `5` and rest runs until HP reaches max
- THEN the log shows *"You start resting."*
- AND later *"You are fully healed."*
- AND each rest iteration runs the normal world phase

#### Scenario: Attack interrupts rest

- GIVEN the player is resting
- WHEN an enemy melee or ranged attack targets the player (including a miss)
- THEN rest ends with *"It's hard to rest while under attack!"* in red

#### Scenario: Ally alarm during rest

- GIVEN the player is resting
- AND a good NPC in player LOS sees an evil NPC the player does not see in FOV
- WHEN the rest loop evaluates after a turn
- THEN the log shows *"{Name} shouts in alarm!"* in red
- AND rest ends
- AND good NPCs never shout in alarm when the player is not resting

#### Scenario: Numpad five unchanged

- GIVEN an injured player
- WHEN the player presses numpad `5`
- THEN exactly one turn is consumed
- AND rest does not start

## Technical Constants (defaults)

| Constant | Default |
|----------|---------|
| `NATURAL_REGEN_HP` | 1 |
| `NATURAL_REGEN_EVERY_N_PLAYER_TURNS` | 8 |
| `REST_UNTIL_MAX_TURNS` | 100 |
| `REST_MAX_SILENT_TURNS_PER_FRAME` | 16 |
| `REST_FRAME_SLEEP_SECONDS` | 0.016 |

## Acceptance Criteria

1. Wait via `H`, numpad 5, `.` — silent when conscious; tired message when stunned.
2. `TYUGHJBNM` provides 8-direction movement; `H` waits only.
3. Every 8 player turns, +1 HP below max (silent); wake message when regen clears stunned.
4. Stunned movement always passes turn with tired message.
5. `on_player_turn_consumed` fires on each consumed turn.
6. Core acceptance tests pass; `tests/test_enhancements_1.py` covers new behavior.