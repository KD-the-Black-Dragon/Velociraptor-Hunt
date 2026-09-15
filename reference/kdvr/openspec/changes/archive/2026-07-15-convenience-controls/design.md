# Design: Convenience controls

| Field | Value |
|-------|-------|
| **Change id** | `convenience-controls` |
| **Status** | Design complete — no implementation until user authorizes a PR |
| **Spec target** | `openspec/specs/convenience-controls/spec.md` (new) |
| **Terminology** | defeated, stunned, digested — never kill/die/death |

---

## Overview

Ship two player-facing conveniences:

1. **Autoexplore** — `` ` `` drives repeated movement until pickups/frontier are exhausted or a **danger interrupt** fires (rest parity).
2. **Force-attack** — **Ctrl + direction** melee-swings an adjacent tile without displacement (DCSS-style).

Both integrate with existing turn consumption, FOV, pickup/rune/macguffin step hooks, and the incremental session loop used by long rest.

---

## Background

### What exists today

| Area | Today |
|------|--------|
| Long rest | `5` → `RestSession` in `src/systems/rest.py`; incremental frames in `main.run_loop` |
| Rest interrupts | Attack event, visible evil, good-ally alarm (`_evaluate_rest_stop`) |
| Rest animation | `rest_visible_fingerprint`, `REST_MAX_SILENT_TURNS_PER_FRAME` (16), `REST_FRAME_SLEEP_SECONDS` |
| Manual cancel | Any `KeyDown` while resting → `cancel_rest()` (no end message) |
| Movement | `try_action()` — move, swap good/neutral, bump-attack, open doors |
| Post-move hooks | `pickup_all_items_at`, `try_activate_floor_rune`, `try_begin_macguffin_activation` |
| Sim exploration | `explore_frontier_tiles`, `player_walk_distances`, `nearest_goal`, `first_step_toward` in `src/sim/navigation.py` |
| Sim loot targets | `visible_loot_positions` / `visible_floor_rune_positions` (FOV-visible only — **narrower** than autoexplore) |
| Ctrl helpers | `is_ctrl_q`, `is_ctrl_s`, etc. in `src/menu.py` |
| Direction map | `DIRECTION_KEYS` in `src/input_handlers.py` |

### Gap

- No autoexplore session, key binding, or goal planner for **known** (explored-memory) pickups.
- No force-attack path that calls `_perform_attack` without `try_move`.
- Danger interrupt logic is rest-private; autoexplore needs a shared core.

---

## Resolved decisions

| # | Topic | Decision |
|---|--------|----------|
| D1 | **Interrupt set** | Autoexplore uses exactly the three **danger** stops from rest: attack targeted, visible evil, ally alarm. No healed/cap stops. |
| D2 | **Interrupt messages** | Reuse existing rest strings: `rest_interrupted_by_attack`, `rest_danger_approaches`, `good_ally_shouts_alarm` (categories unchanged). |
| D3 | **Start pre-checks** | **Engulfed** → `autoexplore_engulfed()` (*You're already exploring something's digestive tract.*). **HP below 50%** (`hp * 2 < max_hp`) → `autoexplore_too_injured()`. **Visible evil at start** → `autoexplore_enemy_in_sight()`. **Stunned** → `stunned_too_tired_to_move()`. All blocks consume no turn. |
| D4 | **Known pickups** | Tile is a pickup goal when `game_map.explored[y,x]` and the tile still has a floor **Item**, **FloorRune**, or **Macguffin** entity. All item categories count (not sim loot subset). |
| D5 | **Macguffin tiles** | Included as pickup goals. Stepping on one triggers the existing macguffin modal; autoexplore session ends because modals block the automation loop (same as manual play). |
| D6 | **Pickup priority** | Nearest BFS distance among reachable pickup goals; ties broken by `(y, x)` ascending (deterministic, reproducible). |
| D7 | **Frontier priority** | When no reachable pickup goals, plan toward nearest **exploration frontier** tile (reuse `explore_frontier_tiles` semantics). |
| D8 | **Completion** | When no reachable pickup goals **and** no reachable frontier tiles → log `autoexplore_complete()` (*Exploration complete.*) and end session. |
| D9 | **Pathfinding** | BFS walkability matches sim `player_walk_predicate` (floor, stairs, open/closed doors). **NPC-occupied tiles** treated as blocked for planning. Deep water blocked for ground player. |
| D10 | **Door opening** | Autoexplore may path through `DOOR_CLOSED`; each step uses `try_action`, which opens doors on bump (existing behavior). |
| D11 | **Failed step** | If chosen direction returns `False` from `try_action`, **do not** consume a turn; replan next frame. If no direction succeeds for a full frame batch, evaluate completion (likely complete). |
| D12 | **Inventory full** | Unpickable items on explored tiles are skipped as goals. When only full-inventory leftovers remain and frontier is exhausted → complete. |
| D13 | **Animation** | Mirror rest: `AutoexploreSession`, `advance_autoexplore_frame`, same fingerprint + batch size + sleep. Reuse `rest_visible_fingerprint` (identical signals). |
| D14 | **Manual cancel** | Any `KeyDown` during autoexplore → `cancel_autoexplore()` with **no** log line (rest parity). Process input before each animation frame. |
| D15 | **Mutual exclusion** | Rest and autoexplore cannot be active simultaneously. Starting one while the other is active is a no-op. |
| D16 | **No turn cap** | Autoexplore runs until completion, danger interrupt, or manual cancel — **no** max-turn safety cap (unlike rest’s 100-turn cap). |
| D17 | **Arena mode** | **No special case** — autoexplore and force-attack work in arena like normal play. |
| D18 | **Start message** | Log `autoexplore_start()` (*You begin exploring.*) on successful begin (default log color). |
| D19 | **Force-attack key** | `KeyDown` with `Modifier.CTRL` and `sym in DIRECTION_KEYS`. Includes **Ctrl+G** (west) in gameplay; no conflict with menu Ctrl+G (different app phase). |
| D20 | **Force-attack combat** | If defender has `Fighter` and is **evil** → `_perform_attack` without moving. Otherwise → log `attack_empty_air()`, consume turn. **No swap** with good/neutral. **No door open**. |
| D21 | **Force-attack stunned** | Allowed: logs `stunned_too_tired_to_move()` and **still consumes turn** on empty swing; if evil adjacent, attack resolves normally (stunned does not block `_perform_attack` from player — verify: `try_action` blocks stunned before attack). **Correction:** `try_action` returns `False` when stunned — force-attack must **also** block melee when stunned; only empty-air path fires tired message + turn. |
| D22 | **Force-attack engulfed** | Ignore Ctrl modifier; route to existing struggle handler for that direction (same as normal movement). |
| D23 | **Shared modules** | Extract danger interrupts + player navigation helpers to `src/systems/` so sim and autoexplore share one implementation. |
| D24 | **Help text** | Add `` ` `` autoexplore and `Ctrl+direction` force-attack rows under Actions in `help_overlay.py`. |

### D21 clarification (stunned force-attack)

`try_action` short-circuits stunned players before combat. Force-attack matches that: when stunned, **never** call `_perform_attack`; log tired message and consume a turn (same feel as wait-while-stunned).

---

## Resolved questions (2026-07-15)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Include macguffins as autoexplore goals? | **Yes** (D5) |
| Q2 | Block start when evil already visible? | **Yes** — `autoexplore_enemy_in_sight()` (*There's an enemy in sight!*), not the rest string |
| Q3 | Block start when injured? | **Yes** — below **50% HP** (`hp * 2 < max_hp`) → `autoexplore_too_injured()` |
| Q4 | Autoexplore max turn cap? | **None** — runs until complete, danger interrupt, or manual cancel (D16) |
| Q5 | Start log line? | **Yes** (D18) |
| Q6 | Force-attack into good/neutral tile? | **Empty air**, no swap (D20) |
| Q7 | Arena disables both features? | **No** — no arena special case (D17) |

---

## Autoexplore algorithm

### Keys and constants

```python
# src/input_handlers.py
AUTOEXPLORE_KEY: Final[KeySym] = KeySym.GRAVE  # `
```

Reuse `REST_MAX_SILENT_TURNS_PER_FRAME` and `REST_FRAME_SLEEP_SECONDS` from rest (no autoexplore-specific cap constant).

### Session shape

```python
@dataclass
class AutoexploreSession:
    active: bool = True
    consumed: int = 0  # diagnostic / tests only; no cap enforced
    attack_interrupt: bool = False  # same listener pattern as RestSession
```

`GameEngine` fields (mirror rest):

- `autoexplore_session: AutoexploreSession | None`
- `_autoexplore_attack_listener: Callable[[], None] | None`

### Begin pre-checks (`begin_autoexplore`)

| Order | Condition | Message | Turn consumed |
|-------|-----------|---------|---------------|
| 1 | Session already active | — | No |
| 2 | `Engulfed` | `autoexplore_engulfed()` | No |
| 3 | `fighter.hp * 2 < fighter.max_hp` | `autoexplore_too_injured()` | No |
| 4 | `Stunned` | `stunned_too_tired_to_move()` | No |
| 5 | Visible evil in FOV | `autoexplore_enemy_in_sight()` | No |
| 6 | Else | `autoexplore_start()` | No (movement consumes later) |

Pre-check messages (rows 2–5) use `MessageCategory.DANGER` (rest pre-check parity).

### Per-turn loop (`advance_autoexplore_turn`)

Each iteration:

1. Clear `attack_interrupt`; attach `on_player_combat_targeted` listener (shared helper with rest).
2. **Plan** direction via `pick_autoexplore_step(...)`.
3. If direction is `None` → stop reason `COMPLETE` (before consuming turn).
4. Call `try_action(...)` for that direction.
   - If `False` → stop reason `STUCK` (no turn consumed) **or** replan within same turn batch (implementation: replan up to N attempts per turn; if still none, do not consume).
   - If `True` → run post-move hooks (pickup, rune, macguffin) identical to `engine_input` movement branch.
5. `consume_player_turn()` via engine callback.
6. Evaluate **danger interrupt** (shared function).

**Recommended step 4 implementation:** single direction per consumed turn (simpler). If `try_action` fails, end frame without consuming; next frame replans. Persistent failure across a batch triggers `COMPLETE` check.

### Goal selection (`pick_autoexplore_step`)

```
origin ← player position
distances ← player_walk_distances_with_blockers(world, map, origin)

pickup_goals ← tiles where explored and (items or rune or macguffin)
pickup_goals ← filter reachable via distances
if pickup_goals not empty:
    goal ← nearest_goal(origin, pickup_goals, distances, deterministic_tiebreak)
    return first_step_toward(origin, goal, bfs_from(goal))

frontier ← explore_frontier_tiles(map)
frontier ← filter reachable
if frontier not empty:
    goal ← nearest_goal(origin, frontier, distances, deterministic_tiebreak)
    return first_step_toward(origin, goal, bfs_from(goal))

return None  # complete
```

### `player_walk_distances_with_blockers`

Extend sim predicate:

- Base: `player_walk_predicate` (includes closed doors, excludes deep water).
- Additionally reject tiles occupied by `BlocksMovement` entities other than player-forgiving rune/macguffin passthrough tiles.

Reuse `_blocking_entity_at` from `movement.py` for consistency.

### Stop reasons and messages

| Reason | When | Message |
|--------|------|---------|
| `ATTACK` | Player targeted this turn | `rest_interrupted_by_attack()` |
| `DANGER` | Visible evil after turn | `rest_danger_approaches()` |
| `ALLY_ALARM` | Ally alarm after turn | `good_ally_shouts_alarm(name)` |
| `COMPLETE` | No goals reachable | `autoexplore_complete()` |
| `STUCK` | *(internal)* | Fall through to COMPLETE check |
| `CANCEL` | Manual key | *(silent)* |

### Incremental animation

Identical control flow to rest in `main.run_loop`:

```text
while autoexplore_in_progress:
    poll one KeyDown → cancel session if any
    advance_autoexplore_frame()
    sleep REST_FRAME_SLEEP_SECONDS
    render if screen_dirty
```

`App.autoexplore_in_progress()` mirrors `rest_in_progress()`.

`can_issue_idle_command()` also returns `False` during autoexplore.

`active_modal_label` → `"autoexplore"` when session active.

---

## Force-attack algorithm

### Input detection

```python
def is_ctrl_direction(event: KeyDown) -> tuple[int, int] | None:
    if not (event.mod & Modifier.CTRL):
        return None
    return DIRECTION_KEYS.get(event.sym)
```

Handled in `handle_gameplay_event` **before** plain direction movement. Requires `not modal_blocks_action()`.

### Handler (`try_force_attack`)

| State | Behavior |
|-------|----------|
| `Engulfed` | Delegate to `try_struggle` + consume turn (ignore Ctrl) |
| `Stunned` | `stunned_too_tired_to_move()` + consume turn; no attack |
| Else compute dest tile | |
| Evil `Fighter` at dest | `_perform_attack(player, defender, ...)` + consume turn |
| Else | `attack_empty_air()` + consume turn |

Do **not** open closed doors, swap allies, or move player.

### Relationship to `close_door_pending`

Ctrl+direction clears `close_door_pending` and performs force-attack (does not close doors).

---

## Refactor: shared modules

### `src/systems/danger_interrupts.py` (new)

Extract from `rest.py`:

- `DangerInterruptReason` enum: `ATTACK`, `VISIBLE_EVIL`, `ALLY_ALARM`
- `evaluate_danger_interrupt(player, map, world, log, *, attack_flag) -> DangerInterruptReason | None`
- `attach_attack_interrupt_listener(session)` / `detach_...` accepting a protocol with `attack_interrupt: bool`

`rest.py` `_evaluate_rest_stop` becomes: danger checks first, then rest-specific `HEALED` and `CAP`.

### `src/systems/player_navigation.py` (new)

Move from `src/sim/navigation.py`:

- `player_walk_predicate`
- `player_walk_distances` (+ new `player_walk_distances_with_blockers`)
- `explore_frontier_tiles`
- `nearest_goal` (add deterministic tie-break helper)
- `first_step_toward`

`src/sim/navigation.py` re-exports from `player_navigation` to avoid sim churn in PR1.

### `src/systems/autoexplore.py` (new)

Session lifecycle, goal picking, frame advance — parallel structure to `rest.py`.

### `src/systems/combat.py`

Add `try_force_attack(...) -> bool` (returns whether turn consumed).

---

## Messages (`src/messages.py`)

| Function | Text |
|----------|------|
| `autoexplore_start()` | *You begin exploring.* |
| `autoexplore_complete()` | *Exploration complete.* |
| `autoexplore_engulfed()` | *You're already exploring something's digestive tract.* |
| `autoexplore_enemy_in_sight()` | *There's an enemy in sight!* |
| `autoexplore_too_injured()` | *You are too injured to autoexplore.* |
| `attack_empty_air()` | *You attack the empty air.* |

Interrupt strings: **reuse rest** (no duplicates).

---

## File touch list

| File | PR | Change |
|------|-----|--------|
| `src/systems/danger_interrupts.py` | PR1 | **New** — shared interrupt evaluation |
| `src/systems/player_navigation.py` | PR1 | **New** — BFS helpers |
| `src/sim/navigation.py` | PR1 | Re-export / thin wrapper |
| `src/systems/autoexplore.py` | PR1 | **New** — session + planner |
| `src/systems/rest.py` | PR1 | Use `danger_interrupts` |
| `src/input_handlers.py` | PR1–2 | `AUTOEXPLORE_KEY`, `is_ctrl_direction` |
| `src/messages.py` | PR1–2 | New strings |
| `src/engine_turn.py` | PR1 | begin/cancel/advance autoexplore |
| `src/engine.py` | PR1 | Session fields + delegates |
| `src/engine_input.py` | PR1–2 | Key handlers |
| `src/app.py` | PR1 | `autoexplore_in_progress`, cancel on key |
| `src/main.py` | PR1 | Animation loop branch |
| `src/debug/modal_snapshot.py` | PR1 | `"autoexplore"` label |
| `src/ui/help_overlay.py` | PR1–2 | Help rows |
| `openspec/specs/convenience-controls/spec.md` | PR1–2 | Live spec |
| `tests/test_autoexplore.py` | PR1 | **New** |
| `tests/test_force_attack.py` | PR2 | **New** |
| `tests/test_rest_until_healed.py` | PR1 | Adjust if interrupt extract changes imports only |

---

## Spec outline (`openspec/specs/convenience-controls/spec.md`)

### Requirements

1. **Autoexplore activation** — `` ` `` key, pre-checks (engulfed, injured, stunned, enemy in sight), start message.
2. **Autoexplore goals** — known pickups then frontier; deterministic nearest tie-break.
3. **Autoexplore completion** — message when no reachable goals.
4. **Autoexplore danger interrupts** — rest parity (three cases, shared messages).
5. **Autoexplore animation** — incremental frames, fingerprint batching, manual cancel (any key); **no turn cap**.
6. **Force-attack activation** — Ctrl + movement keys.
7. **Force-attack resolution** — melee if evil adjacent; else empty air; no move/swap/door.
8. **Force-attack stunned/engulfed** — per D21/D22.

Each requirement gets GIVEN/WHEN/THEN scenarios in the spec PR.

---

## PR plan

### PR1 — Autoexplore + shared infrastructure

| Step | Work |
|------|------|
| 1 | Extract `danger_interrupts.py`; refactor `rest.py` (no behavior change) |
| 2 | Extract `player_navigation.py`; sim re-export |
| 3 | Implement `autoexplore.py` + engine/session wiring + main loop |
| 4 | Messages, help row for `` ` `` |
| 5 | `openspec/specs/convenience-controls/spec.md` (autoexplore sections) |
| 6 | `tests/test_autoexplore.py` |

**Exit criteria:** targeted tests green; manual checklist PR1.

### PR2 — Force-attack

| Step | Work |
|------|------|
| 1 | `try_force_attack` in `combat.py` |
| 2 | `is_ctrl_direction` + `engine_input` handler |
| 3 | Messages + help row |
| 4 | Spec force-attack requirements |
| 5 | `tests/test_force_attack.py` |

**Exit criteria:** targeted tests green; manual checklist PR2.

---

## Test plan (automated)

### PR1 `tests/test_autoexplore.py`

| Test | Intent |
|------|--------|
| `test_autoexplore_key_is_grave` | `` ` `` binding, not unbound |
| `test_begin_blocked_engulfed` | Pre-check → `autoexplore_engulfed` |
| `test_begin_blocked_visible_evil` | Pre-check → `autoexplore_enemy_in_sight` |
| `test_begin_blocked_below_half_hp` | Pre-check → `autoexplore_too_injured` |
| `test_begin_allowed_at_half_hp` | `hp * 2 == max_hp` → session starts |
| `test_begin_blocked_stunned` | Pre-check |
| `test_start_message` | `autoexplore_start` logged |
| `test_picks_up_known_item_on_explored_tile` | Item on explored tile not in current FOV |
| `test_frontier_when_no_pickups` | Moves toward unseen |
| `test_complete_message` | Walled map → `autoexplore_complete` |
| `test_danger_interrupt_visible_evil` | Evil enters FOV mid-run |
| `test_attack_interrupt` | Player targeted event |
| `test_manual_cancel_silent` | KeyDown → no complete/interrupt message |

Fixtures: minimal map helpers from `tests/*_test_helpers`; **pin small inline maps**, not live `data/` balance.

### PR2 `tests/test_force_attack.py`

| Test | Intent |
|------|--------|
| `test_hits_adjacent_evil_without_moving` | Position unchanged, damage dealt |
| `test_empty_air_consumes_turn` | Message + turn count |
| `test_does_not_swap_good` | Knight on tile → empty air |
| `test_does_not_open_door` | Closed door → empty air |
| `test_stunned_empty_air` | Tired message, no damage |
| `test_engulfed_routes_to_struggle` | Struggle path, not empty air |

---

## Manual testing (summary)

Full checklists in `testing-checklist-pr1.md` and `testing-checklist-pr2.md`.

**Run:** `python -m src.main`

PR1 happy path:

- [ ] Clear a floor with `` ` ``; pickups happen in path order; frontier reveals map.
- [ ] Evil entering FOV stops with *Danger approaches!*
- [ ] Ally alarm stops exploration (same as rest).
- [ ] Getting hit stops with attack interrupt message.
- [ ] Walled dead-end ends with *Exploration complete.*
- [ ] Any key cancels silently.

PR2 happy path:

- [ ] Ctrl+direction hits adjacent evil without moving.
- [ ] Ctrl+direction into empty tile wastes turn with *You attack the empty air.*
- [ ] Useful vs erratic wolf (deliberate miss turn).

---

## Performance notes

- Per turn: one BFS over map (≤ ~80×50 tiles) plus entity scans for pickup goals — acceptable same class as monster explore AI; runs only during autoexplore, not every player turn.
- Batch up to 16 turns/frame when fingerprint static (rest parity).
- No per-frame full-map allocation if distance maps reuse buffers (optional optimization; not required for v1).

---

## Save compatibility

No new persisted fields. `AutoexploreSession` is ephemeral (cleared on load / floor change like `RestSession`).

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Sim/nav extraction breaks balance sim | Re-export wrapper; run `tests/test_balance_pr*.py` in PR1 |
| Macguffin modal mid-autoexplore feels abrupt | Expected; modal blocks input; session cancelled when modal opens |
| Inventory full on item tile loops | Skip unreachable pickup goals; complete when frontier empty |
| Ctrl+G west vs menu Ctrl+G | Phase-gated handlers — only gameplay movement |

---

## Archive / todo

When accepted, no `todo/spec.md` item to remove (never listed). Update `AGENTS.md` active change pointer when implementation starts.