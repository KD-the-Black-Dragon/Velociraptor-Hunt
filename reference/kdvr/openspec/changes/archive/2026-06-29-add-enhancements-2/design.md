# Design: Enhancements 2 — NPC Identity

## Current state

| Area | Today |
|------|--------|
| `DisplayName` | Species only (`"wolf"`); used in vore via `entity_display_name()` |
| Combat logs | Hard-coded *"monster"* in `messages.py` |
| AI | Single chase target: player; vore before chase |
| Player bump | Always attacks `Fighter` at destination |
| Items | `Item` + `ItemType`; no description |
| Modals | `VoreModalState` for vore narrative |
| Quit | `Escape` quits game |

## Resolved decisions (2026-06-29)

| # | Decision |
|---|----------|
| 1 | **Neutral:** flee from visible evil; indifferent to player. **Swap:** player may swap with good or neutral only; good/neutral never attack or swap onto player. |
| 2 | Examine is **free** (no turn). |
| 3 | **`Ctrl+Q`** quits; **`Escape`** cancels in-progress commands only (examine). |
| 4 | **`x` while engulfed:** log *"You can't see anything!"* — no examine mode. |
| 5 | Evil targets **nearest** hostile; **random** tie-break among equidistant. |
| 6 | **One wolf per game** spawns as `ProperName("Fang")` (random pick among batch). |

## Proposed components

```python
class Alignment(Enum):
    GOOD = auto()
    EVIL = auto()
    NEUTRAL = auto()

@attrs.define(frozen=True)
class ProperName:
    name: str  # e.g. "Fang", "Bob"

@attrs.define(frozen=True)
class ExamineDescription:
    text: str
```

`DisplayName` remains the species/type label (`wolf`, `knight`).

## Naming resolver

`src/systems/naming.py`:

```python
def entity_log_name(entity: Entity, *, sentence_start: bool = False) -> str:
    """ProperName if set, else 'the {species}'. Capitalize when sentence_start."""
```

Migrate `entity_display_name` from `vore.py`. Vore evasion string uses possessive form: *"You evaded Fang's vore attempt."*

## Alignment-driven AI

```text
for each monster (sorted):
  if predator holding prey: sync; continue
  if skip_turn_set contains monster: continue
  if alignment == GOOD or NEUTRAL: player tile not a valid chase destination
  if alignment == NEUTRAL and visible evil exists: flee step (maximize distance)
  elif hostile = pick_hostile_target(evil/good rules): chase/attack hostile
  elif player_engulfed: wander (existing)
  else: idle / wander
```

`pick_hostile_target` (evil only):

- Collect hostiles with LOS: `Player`, good NPCs
- Pick minimum Chebyshev distance
- If tie, `rng.choice` among tied

Good: hostiles = evil NPCs with LOS (nearest + random tie same as evil).

Neutral: no hostile pick; flee overrides when evil visible.

**NPC pathing into player:** `_choose_chase_direction` / `can_move_to` treats player tile as blocked for good and neutral NPCs.

**Vore gate:** `should_attempt_vore` returns False if predator has `Alignment.good` or `Alignment.neutral`.

## Player-initiated swap

In `try_action` when `Player` is actor and destination `Fighter` has `Alignment.good` or `Alignment.neutral`:

1. Swap positions
2. Return True (turn consumed)
3. Add NPC to `skipped_this_phase` before `_run_world_turn`

Evil destinations still use bump attack. Stunned and engulfed gates unchanged (no swap).

## Flee (neutral)

```python
def _choose_flee_direction(..., threat: Position) -> direction | None:
    # Among legal steps, pick one that maximizes distance to threat; rng tie-break
```

Threat = nearest visible evil with LOS.

## Examine mode

```python
@attrs.define
class ExamineState:
    active: bool = False
    cursor: Position = ...
    showing_description: bool = False
```

Input priority: vore modal > examine description modal > examine cursor > gameplay.

| Key | Engulfed + `x` | Examine active | Description open |
|-----|----------------|----------------|------------------|
| `x` | Log can't see | — | — |
| `Escape` | — | Exit examine | Back to cursor |
| `Ctrl+Q` | Quit | Quit | Quit |

Engulfed block happens before examine state is set.

## Spawn changes (v1)

```python
# each wolf
DisplayName(name="wolf")
Alignment(Alignment.EVIL)
ExamineDescription("This wolf looks particularly vicious and ferocious.")

# exactly one wolf per spawn_monsters() call (rng picks index)
ProperName(name="Fang")

# health potion
ExamineDescription("This is a healing potion that can restore one's vigor.")
```

## Quit key migration

- `engine.handle_event`: `KeyDown` with `sym == KeySym.Q` and `Modifier.CTRL` → return True (exit)
- Remove `KeySym.ESCAPE` quit branch
- Update `test_acceptance.py` AC clean-exit scenario to use Ctrl+Q
- Update core spec pointer (Enhancements 2 modifies quit binding)

## Suggested PR plan

| PR | Scope |
|----|--------|
| 1 | Components, naming, messages, spawn (evil, Fang, descriptions) |
| 2 | Combat log wiring (all party names) |
| 3 | Faction AI: evil/good targeting, neutral flee, player-tile blocking |
| 4 | Player swap (good/neutral) + skip turn |
| 5 | Vore alignment gate + possessive evasion strings |
| 6 | Examine mode + engulfed block + Ctrl+Q / Escape |
| 7 | Tests, acceptance, README, archive |

## Test strategy

- `test_entity_log_name_fang_and_species`
- `test_one_fang_per_spawn_batch`
- `test_combat_messages_no_monster_generic`
- `test_evil_nearest_hostile_random_tie`
- `test_neutral_flees_evil`
- `test_good_does_not_step_on_player`
- `test_player_swap_good_and_neutral`
- `test_examine_engulfed_cant_see`
- `test_escape_cancels_examine_not_quit`
- `test_ctrl_q_quits`
- `test_examine_no_turn_cost`
- Regression: full `pytest tests/`