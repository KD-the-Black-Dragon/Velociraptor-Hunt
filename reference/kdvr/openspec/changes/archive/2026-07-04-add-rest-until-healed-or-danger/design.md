# Design: Rest Until Healed or Danger

## Source Requirement (todo)

Key **`5`** (main keyboard, not numpad) starts repeated waiting until: **100 turns**, **full health**, **Evil in player sight**, **player receives an attack**, or **Good ally in player LOS spots Evil** (ally alarm). Pre-checks and halt messages use **red** log color (`ALERT_MESSAGE_FG`).

## Incremental animation (2026-07-04 playtest fix)

Rest MUST NOT run all turns inside one input handler. `GameEngine` holds an active `RestSession`; `main.run_loop` calls `advance_rest_animation()` each frame while resting.

| Rule | Behavior |
|------|----------|
| Windows responsiveness | Non-blocking `tcod.event.get()` + `present()` every frame while resting (~16ms sleep) |
| Screen updates | Re-render only when `rest_visible_fingerprint` changes (HP, stunned, visible entity positions, log length) |
| Silent batching | Up to `REST_MAX_SILENT_TURNS_PER_FRAME` (16) turns per frame when fingerprint unchanged |
| Heartbeat | `present()` every frame even when render skipped (same buffer keeps OS responsive) |
| Manual interrupt | Any **KeyDown** cancels rest (no end message) then runs the normal key handler; input polled before each rest frame |

## Resolved Decisions (2026-07-04)

| # | Decision |
|---|----------|
| 1 | Rest turns are **silent** until the end message (no per-turn tired message while stunned) |
| 2 | Rest **begins** with *"You start resting."* (default log color) |
| 3 | **Stunned** players may rest; evil in player FOV still blocks at pre-check |
| 4 | Stunned-wake + full-heal same turn — no special handling |
| 5 | Halt on **any attack against the player** (melee or ranged, hit or miss, damage or no damage) — not HP delta only; future invisible attackers will interrupt when their combat line logs |
| 6 | **Good ally alarm** — only while resting: Good NPC in **player LOS** that **sees Evil** (LOS) shouts e.g. *"Sir Bob shouts in alarm!"* in red; this is the **only** alarm-shout case in the game; halts rest (no duplicate *"Danger approaches!"*) |
| 7 | All messages that **halt or prevent** rest use **`ALERT_MESSAGE_FG`** (red) |
| 8 | Successful ends (*"You are fully healed."*, *"You finish resting."*) use default log color |

## Current State

| Area | Today |
|------|--------|
| Single wait | `WAIT_KEYS`: `KeySym.KP_5`, `KeySym.PERIOD`, `KeySym.H` |
| Regen | `NATURAL_REGEN_EVERY_N_PLAYER_TURNS = 8`; silent `+1 HP` |
| Evil in player FOV | `_player_has_visible_evil` in `ally_introduction.py` |
| Good sees evil | `_visible_good_evils(ally, world, game_map)` in `ai.py` |
| Red alerts | `ALERT_MESSAGE_FG` in `message_log.py` (inventory destruction, wand break) |
| Digit **5** | Unbound (`KeySym.N5`) |

## Controls

| Key | Action |
|-----|--------|
| `5` (main keyboard) | Rest until healed or danger |
| `KP_5`, `.`, `H` | Wait one turn (unchanged) |

## Rest Algorithm

### Pre-checks (no turn consumed; all **red**)

| Condition | Message |
|-----------|---------|
| `Engulfed` on player | *"This is no time to rest!"* |
| `fighter.hp >= fighter.max_hp` | *"You are already at full health."* |
| Evil in player FOV | *"It's too dangerous to rest now!"* |

### Start

Log *"You start resting."* (default color). Then enter loop.

### Loop (max **100** iterations)

Each iteration:

1. Clear attack-interrupt flag; register `on_player_combat_targeted` callback.
2. `_consume_player_turn()`.
3. Unregister callback.
4. Evaluate stop conditions **in priority order**:

| Priority | Condition | Message | Color |
|----------|-----------|---------|-------|
| 1 | Player targeted in combat this turn (attack event) | *"It's hard to rest while under attack!"* | red |
| 2 | Evil in player FOV | *"Danger approaches!"* | red |
| 3 | Good ally in player LOS sees evil | *"{Name} shouts in alarm!"* | red |
| 4 | `fighter.hp >= fighter.max_hp` | *"You are fully healed."* | default |
| 5 | `rest_turns >= 100` | *"You finish resting."* | default |

5. Log end message if matched; exit.

**Ally alarm:** Pick first good ally (sorted by `y`, `x`, `id`) that is in `entity_visible_to_player` and has non-empty `_visible_good_evils`. Never fires outside an active rest loop.

**Attack interrupt:** `fire_player_combat_targeted()` from `combat.py` when player is defender after `resolve_attack` (melee `_perform_attack`, ranged `perform_npc_ranged_attack`) — includes misses and 0-damage hits.

## Messages (`src/messages.py`)

| Function | Text | Color when logged |
|----------|------|-------------------|
| `rest_start()` | *"You start resting."* | default |
| `rest_engulfed_no_time()` | *"This is no time to rest!"* | red |
| `rest_already_full_health()` | *"You are already at full health."* | red |
| `rest_too_dangerous_now()` | *"It's too dangerous to rest now!"* | red |
| `rest_finish()` | *"You finish resting."* | default |
| `rest_fully_healed()` | *"You are fully healed."* | default |
| `rest_danger_approaches()` | *"Danger approaches!"* | red |
| `rest_interrupted_by_attack()` | *"It's hard to rest while under attack!"* | red |
| `good_ally_shouts_alarm(name)` | *"{name} shouts in alarm!"* | red |

## Implementation

| File | Change |
|------|--------|
| `src/input_handlers.py` | `REST_UNTIL_KEY = KeySym.N5` |
| `src/systems/fov.py` | `player_has_visible_evil()` (moved from ally_introduction) |
| `src/systems/rest.py` | Pre-checks, loop, ally alarm scan |
| `src/events.py` | `on_player_combat_targeted` + `fire_player_combat_targeted()` |
| `src/systems/combat.py` | Fire event when player is attack target |
| `src/messages.py` | Rest + alarm strings |
| `src/engine.py` | `N5` handler |
| `src/systems/ally_introduction.py` | Import `player_has_visible_evil` from fov |

## Spec (`openspec/specs/enhancements-1/spec.md`)

Add **Requirement: Rest Until Healed or Danger** with scenarios for pre-checks, start message, silent loop, attack/danger/ally/full/cap ends, red alert coloring, ally alarm exclusivity.

Constant: `REST_UNTIL_MAX_TURNS = 100`.

## PR Plan

Single **PR0** — full feature, tests, README, spec.

## Manual Playtest (PR0)

See `testing-checklist-pr0.md`.