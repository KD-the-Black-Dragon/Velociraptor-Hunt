# 1v1-arena Specification

## Purpose

Secret **Ctrl+B** main-menu flow to duel a single **Evil** entity in a fixed **1×10 hallway**, with player loadout synthesized from the depth-jump algorithm at **`loot_depth = spawn.min_depth − 1`**. Arena runs are out-of-band: no autosave, no Past Runs, `level_warped = true`.

Headless batch bot: **`tools/sim_arena.py`** (10 trials per Evil entity, CSV export).

**Terminology:** defeated, stunned, digested — no kill/die/death.

---

## Requirements

### Requirement: Secret menu entry

From the main menu, **Ctrl+B** SHALL open entity-id entry. **Escape** returns to the main menu. The player name is fixed **`Player`** (no name-entry step). No save-overwrite prompt.

#### Scenario: Ctrl+B opens entity entry

- GIVEN the app is on the main menu
- WHEN the player presses Ctrl+B
- THEN the app enters entity-id entry
- AND does not prompt to overwrite an existing autosave

---

### Requirement: Entity id validation

Entry SHALL be **case-sensitive**. On Enter:

| Condition | Error message |
|-----------|---------------|
| Unknown id | `Unknown entity id.` |
| Non-evil id | `That entity is not Evil alignment.` |

The screen SHALL list all **Evil** ids from the active entity registry (mods included) in **three display-only columns**. **`spawn.weight` is ignored** for eligibility.

#### Scenario: Good entity rejected

- GIVEN entity id `rabbit` is Neutral in the active registry
- WHEN the player enters `rabbit` and presses Enter
- THEN error `That entity is not Evil alignment.` is shown
- AND the fight does not start

---

### Requirement: Arena map and spawn

On valid entry, the game SHALL create a **1-wide × 10-long** floor row with walls above and below, fully explored.

| Role | Position |
|------|----------|
| Player | `x=0`, center row |
| Enemy | `x=9`, center row |

Aquatic enemies (`mobility: aquatic` or `spawn_requires_water`): **one `DEEP_WATER` tile** under the enemy at `x=9`.

No stairs, items, floor runes, macguffins, or random population. Enemy prefix roll is **disabled**.

#### Scenario: Aquatic enemy spawns on water

- GIVEN an aquatic Evil entity is selected
- WHEN the arena starts
- THEN tile `(9, center)` is deep water
- AND the enemy is placed on that tile

---

### Requirement: Depth, difficulty, and loadout

- **Difficulty:** Options → Difficulty at arena start.
- **Displayed depth:** `spawn.min_depth` of the chosen enemy.
- **Enemy stats:** depth-scaled at `spawn.min_depth` for that difficulty, no prefix.
- **Player loadout:** same rules as depth-jump with `target_depth = spawn.min_depth`; `min_depth == 1` uses starter loadout.

`level_warped = true` and `arena_mode = true` for the whole fight.

---

### Requirement: Save isolation

Arena SHALL NOT read or write the autosave slot.

| Action | Behavior |
|--------|----------|
| Autosave hooks | No-op while `arena_mode` |
| Ctrl+S | Shows `Game saved.`; no file write |
| Digestion game-over | Does not delete autosave |

#### Scenario: Ctrl+S in arena

- GIVEN an arena fight is in progress
- WHEN the player presses Ctrl+S
- THEN the log shows `Game saved.`
- AND no autosave file is created or updated

---

### Requirement: Outcomes

**Victory:** enemy `hp <= 0` from any source → combat freezes immediately → modal `You have defeated the {name}!` (log-style name, e.g. `the rat`) → Enter → main menu. No Past Runs entry.

**Defeat:** player digested → normal game-over recap → Enter → main menu. No Past Runs entry. **Stunned is not game-over**; play continues until digested or enemy defeated.

#### Scenario: Victory returns to menu without Past Runs

- GIVEN an arena fight where the enemy is defeated
- WHEN the player dismisses the victory modal with Enter
- THEN the app returns to the main menu
- AND Past Runs is unchanged

---

### Requirement: Headless arena bot CLI

The project SHALL ship **`tools/sim_arena.py`** loading **enabled mods** via `reload_all_game_data()`.

| Option | Default | Meaning |
|--------|---------|---------|
| `--difficulty` | `normal` | `easier`, `normal`, `hard`, or `nightmare` |
| `--seed` | random | Root seed; reported in output and CSV `meta.seed` row |
| `--trials` | `10` | Trials per Evil entity |
| `--max-turns` | `1000` | Turn cap per trial (draw if no winner) |
| `--output` | `arena_compare.csv` | Compare-sheet CSV path |
| `--label` | auto timestamp | Column header for this run |
| `--overwrite` | off | Replace output file; default is append when file exists |

#### Scenario: CLI completes without window

- GIVEN `python tools/sim_arena.py --difficulty normal --trials 2 --max-turns 50`
- WHEN the run completes
- THEN no libtcod window is created
- AND the process exits with code 0

---

### Requirement: Arena bot policy

Each trial SHALL use headless `GameEngine(save_coordinator=None)` and the same arena init as interactive play.

Policy per player turn (after modal babysitter):

1. If nearest **visible Evil** exists → move to bump attack.
2. Else → move **right** `(+1, 0)` (valid while engulfed).

**No** potions, wands, rest, or thrown weapons.

#### Scenario: Bot does not use consumables when stunned

- GIVEN the bot policy decides while the player has `Stunned`
- THEN the action is **WAIT** (no inventory use)

---

### Requirement: Trial outcomes and scoring

| Outcome | Condition |
|---------|-----------|
| Player win | Arena enemy defeated |
| Enemy win | Player digested |
| Draw | Turn cap reached with no winner |

Draws consume a trial slot but increment neither win counter and record no HP sample.

Default output is a **compare sheet** (same spirit as `balance_compare.csv`):

| Column | Content |
|--------|---------|
| `metric` | Stable row key — meta rows, then per entity: `enemy_id`, `min_spawn_depth`, `player_wins`, `enemy_wins`, `player_win_hp_remaining`, `enemy_win_hp_remaining`, blank row, repeat |
| Run columns | One per invocation (`--label` or auto timestamp); **appends** when output file already exists |

Meta rows: `meta.seed`, `meta.difficulty_id`, `meta.trials_per_entity`, `meta.max_turns`.

Per-entity value rows (under each metric name): entity id, min depth, win counts, mean HP% (blank when no samples in that category).

Entity blocks SHALL be ordered by **`min_spawn_depth` ascending**, then **`enemy_id`** for ties (not alphabetical-only by id).

`player_wins + enemy_wins ≤ trials`; any gap implies draws.

#### Scenario: Append produces side-by-side diff

- GIVEN `arena_compare.csv` from a baseline run
- WHEN `python tools/sim_arena.py --label after_tweak --output arena_compare.csv` and the file already exists
- THEN the sheet has a third column `after_tweak`
- AND `metric` rows are unchanged

#### Scenario: Stalemate visible in win columns

- GIVEN 10 trials where 4 are player wins, 3 enemy wins, and 3 draws
- THEN `player_wins` is 4 and `enemy_wins` is 3

---

## Related

- `depth-jump-start` — loadout synthesis
- `past-runs` — `level_warped` skip
- `balance-simulator` — separate tool; arena bot is simpler (1v1 only)