# Design: Digestion

## Current state (post–Enhancements 3)

| Area | Today |
|------|--------|
| Engulf | Player (modal) + NPC (headless log); `Predator.prey`, no `narrative_type` |
| Predator while holding | **Fully frozen** — `sync_engulfed_position` then `continue` (no move, no attack) |
| Engulfed prey turn | Skipped in `run_monster_turns` |
| Prey at 0 HP | Good/neutral **stunned**, not removed |
| Mercy | `VoreMercy` on **player** only after escape/release |
| Regen | Player + NPC natural regen; no strike gate |
| Digestion | Explicitly deferred in vore + E3 specs |

## Goals

1. Engulfed prey take **digestion damage** on a fixed cadence.
2. At 0 HP, **strikes** accumulate; at **3 strikes**, prey is **digested**.
3. NPC digestion → **remove** prey, **log** completion by OV/CV/AV type, predator returns to normal **next player turn**.
4. Player digestion → **modal** then **game over** (phase 2).
5. No re-engulf before freedom: **NPC mercy** parity with player.

## Resolved decisions (2026-06-30)

| # | Decision |
|---|----------|
| 1 | Digestion ticks **once per world phase** when the **prey's AI slot** would run (skip + digest). |
| 2 | Predator while holding: **may bump-attack**; **cannot move** or **initiate vore**. Not fully frozen. |
| 3 | `digestion_damage` is **per predator species** (wolf = **3** initially). |
| 4 | **Good** prey: **10%** chance per tick for plea line if player has **LOS** (predator or prey tile). **Neutral** prey: **silent** on every tick. |
| 5 | **Completion** on digest: OV/CV/AV pools, shared across evil NPCs, `{predator}` / `{prey}` placeholders. |
| 6 | `DigestionStrikes` on prey; **reset to 0 on freedom**. No re-engulf before freedom (mercy). |
| 7 | `strikes >= 1` → **block natural regen** (player + NPC). Potions still heal. Freedom resets strikes → regen OK. |
| 8 | Per tick: **if HP > 0**, reduce HP only; **elif HP == 0**, add 1 strike. **Never** HP→0 and +1 strike same tick. |
| 9 | NPC digested → `entity.clear()`; clear `Predator` on wolf; predator acts **next player turn** only. |
| 10 | Player digested → **modal** (not log-only for completion). NPC digested → **log only**. |
| 11 | Game over: stub name `"Player"`, score `0` (or `player_turn_count` — use turns survived stub); Enter → **exit** (menu stub later). |
| 12 | **AV content:** engulfment + abdominal crushing only; no assumed expansion. |

## Components

```python
@attrs.define
class DigestionStrikes:
    count: int = 0  # 0..3; reset on freedom


@attrs.define
class Predator:
    prey: Entity
    narrative_type: str  # "OV" | "CV" | "AV" — set at engulf
    failed_struggles: int = 0  # existing — player struggle only
```

**Per-predator digestion damage** — prefer a small component on vore-capable spawns:

```python
@attrs.define(frozen=True)
class DigestionStats:
    damage_per_tick: int
```

Wolf spawn: `DigestionStats(damage_per_tick=3)`. Future evil species set their own values in `spawn.py`.

**Mercy:** reuse `VoreMercy` tag on **any** prey after `release_engulfed` / `release_npc_engulfed`. Combat and `should_attempt_vore` must treat `VoreMercy` on **NPC defenders**, not only player.

## Digestion tick algorithm

Called from `run_monster_turns` when an engulfed NPC would act (before `continue`):

```text
apply_digestion_tick(prey, predator, world, game_map, message_log, rng):
  damage = predator DigestionStats.damage_per_tick
  fighter = prey Fighter
  hp_was_positive = fighter.hp > 0

  if hp_was_positive:
    fighter.hp = max(0, fighter.hp - damage)
    sync_stunned_state(prey)  # good/neutral → Stunned at 0
    maybe_good_plea_message(...)  # 10% if good + visible
    return

  # hp already 0
  strikes = prey DigestionStrikes (create if missing, count=0)
  strikes.count += 1
  maybe_good_plea_message(...)

  if strikes.count >= 3:
    complete_digestion(prey, predator, ...)  # NPC: remove + log + clear Predator
```

**Player** (phase 2): same strike logic on `on_player_turn_consumed` or engulfed player-turn path after struggle resolution; third strike opens digestion modal, then game over.

### Regen gate

In `_apply_natural_regen` (player and NPC loops):

```text
if entity has DigestionStrikes and strikes.count >= 1:
  skip regen for this entity
```

Potions bypass this gate (direct `heal()`).

## Predator behavior while holding

Replace full freeze block in `run_monster_turns`:

```text
if monster has Predator:
  sync_engulfed_position(monster)
  if adjacent bump-attack legal (try_action toward adjacent hostile):
    try_action(...)  # one attack only; no chase step
  continue  # no move, no vore attempt
```

`try_resolve_npc_vore` / `try_open_vore_modal`: skip if predator already has `Predator` component.

## Engulf — persist narrative type

On `engulf_npc` / `engulf_player`:

```python
predator.components[Predator] = Predator(
    prey=prey,
    narrative_type=chosen_type,  # from vore attempt resolution
)
```

Player modal path already knows `modal.narrative_type` at success. NPC path passes type from `try_resolve_npc_vore`.

## Freedom and mercy

`release_npc_engulfed`:

- Clear `Engulfed`, pop `Predator`, restore `BlocksMovement`, place adjacent tile
- `prey.tags.add(VoreMercy)`
- `prey.components.pop(DigestionStrikes, None)` or `strikes.count = 0`
- Existing rescue log (`npc_freed_from_predator`)

`release_engulfed` (player): same strike reset + existing `VoreMercy`.

**Combat:** `_perform_attack` — if `VoreMercy in defender.tags` for **any** entity (not only player).

**Vore:** `should_attempt_vore` — if `VoreMercy in prey.tags` (already player-only check; generalize to all prey).

Engine: discard `VoreMercy` from **all** entities with tag at end of world phase (or only player today — extend to NPCs).

## NPC digestion completion

`complete_npc_digestion(predator, prey, message_log, game_map)`:

1. Pick random line from `DIGESTION_COMPLETE_POOL[narrative_type]`
2. Format `{predator}`, `{prey}` via `entity_log_name`
3. Log if predator or prey tile visible to player
4. `prey.clear()`
5. `predator.components.pop(Predator, None)`
6. Do **not** let predator take extra actions this world phase

Example pools (extensible arrays in `src/digestion_content.py`):

| Type | Example line |
|------|----------------|
| OV | `{predator} burps triumphantly — {prey} has been digested.` |
| CV | `{predator} releases what's left of {prey} as white slime.` |
| AV | `{predator}'s abdomen compresses — {prey} has been digested.` |

**AV wording:** crushing / compression / internal pressure only.

Good plea pool (10% per tick, good prey only):

- `From inside {predator}, {prey} begs for rescue.`
- `From inside {predator}, {prey} grunts helplessly.`

## Player digestion (phase 2)

| Step | Behavior |
|------|----------|
| Tick timing | Each **consumed player turn** while engulfed (after struggle attempt); digestion runs **before** natural regen on that turn |
| Strike 1–2 | Log *"You are being digested!!"* (strike increments only, not HP damage ticks) |
| Strike 3 | Open `DigestionModal` with placeholder line per OV/CV/AV + predator display name |
| Immunity | Engulfed player ignores **all** external combat damage; no natural regen while engulfed |
| After modal | `GameOverState`: `"Player"`, score stub, `"Digested by {predator}"` |
| Enter | `SystemExit` (or stub main menu) |

Placeholder modals (wolf, CP437-safe ASCII in `PLAYER_DIGESTION_MODAL`):

- OV: *"The wolf howls in triumph as it digests a great prize - you."*
- CV: *"The wolf expels what's left of you as white slime onto the stony floor."*
- AV: *"The wolf howls in triumph as its abdomen compresses on a great prize - you."*

Struggle and digestion on the same player turn: struggle resolves first (existing), then digestion tick (design confirmation 2026-06-30).

## World-phase ordering (NPC)

```text
for monster in sorted_monsters:
  if Engulfed:
    apply_digestion_tick(...)
    continue
  if Predator:
    sync_engulfed_position
    try adjacent attack only
    continue
  ... normal AI ...
```

Digestion for prey runs at **prey index** in sort order, not predator index.

## Visibility and logging

| Event | Gate |
|-------|------|
| Good plea (tick) | Player LOS to predator **or** prey position |
| NPC digest complete | Same as combat logs |
| Strike / silent tick | No log (except 10% plea) |

**CP437 rendering:** HUD and `MessageLog` use `src/text.cp437_safe()` — Unicode em dashes and similar punctuation are normalized to ASCII before display (Alloy CP437 tileset lacks those glyphs).

## Suggested PR plan

| PR | Scope | Manual verify |
|----|--------|----------------|
| 1 | `DigestionStrikes`, `DigestionStats`, `Predator.narrative_type`; NPC `VoreMercy`; predator attack-only | Freed rabbit not re-vored same turn; holding wolf can attack adjacent knight |
| 2 | NPC digestion tick, strikes, regen gate, plea + completion pools | Wolf digests stunned knight over time; completion log by type |
| 3 | Player digestion tick + modal + game over screen | Engulfed player reaches game over; Enter exits |
| 4 | `digestion` spec, spec updates, acceptance, archive | Full pytest + checklist |

Each PR ships `testing-checklist-prN.md`.

## Test strategy

### PR 1

- `test_npc_release_grants_vore_mercy`
- `test_vore_mercy_blocks_npc_re_engulf`
- `test_predator_attack_only_while_holding`
- `test_predator_cannot_move_while_holding`
- `test_engulf_stores_narrative_type_on_predator`

### PR 2

- `test_digestion_reduces_hp_before_strikes`
- `test_no_strike_on_same_tick_as_hp_to_zero`
- `test_three_strikes_digests_npc`
- `test_digestion_resets_strikes_on_freedom`
- `test_regen_blocked_when_strikes_ge_1`
- `test_good_plea_message_probabilistic`
- `test_neutral_silent_on_digestion_tick`
- `test_completion_message_uses_narrative_type`
- `test_predator_unbound_after_digest_next_turn`

### PR 3

- `test_player_digestion_strike_cadence`
- `test_player_third_strike_opens_modal`
- `test_game_over_screen_shows_digested_by`
- `test_struggle_and_digestion_same_turn`

### Regression

- Player vore modal, struggle, escape, mercy unchanged
- NPC rescue, render highlight, visibility-gated logs
- Full `pytest tests/`

## Supersedes

| Spec | Update |
|------|--------|
| `vore/spec.md` | Digestion in scope; predator holding behavior; player game over |
| `enhancements-3/spec.md` | Good/neutral removal via digestion; no longer deferred |
| `core-roguelike/spec.md` | Game over via digestion (player path only) |

## Files (new / touched)

```
src/
  components.py          # DigestionStrikes, DigestionStats; Predator.narrative_type
  constants.py             # optional WOLF_DIGESTION_DAMAGE if not on component only
  digestion_content.py     # DIGESTION_COMPLETE_POOL, GOOD_PLEA_POOL
  spawn.py                 # DigestionStats on wolf
  systems/
    digestion.py           # apply_digestion_tick, complete_npc_digestion (new)
    vore.py                # narrative_type on engulf; mercy on NPC release
    ai.py                  # prey tick; predator attack-only
    combat.py              # VoreMercy for all defenders
    engine.py                # regen gate; game over + digest modal (PR 3)
  messages.py              # thin wrappers if needed
tests/
  test_digestion.py
openspec/
  specs/digestion/spec.md  # authored at PR 4 or start of PR 1
```

## Risks

| Risk | Mitigation |
|------|------------|
| Predator attack-only complexity | Single adjacent `try_action`; no chase |
| Sort order / double tick | Digest only in `Engulfed` branch |
| Mercy not on NPC | PR 1 explicit tests |
| AV scope creep | Review pools; author constraint in spec |

## Out of scope

- High score persistence
- Player name entry
- Main menu stub (exit acceptable)
- Digestion damage to predator from prey (struggle unchanged)
- Multiple prey per predator