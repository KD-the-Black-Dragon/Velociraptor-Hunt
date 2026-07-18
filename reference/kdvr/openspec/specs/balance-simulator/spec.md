# balance-simulator Specification

## Purpose

Headless **hybrid balance analyzer** for difficulty review: drives `GameEngine` turn-by-turn through `src/sim/` policy, records per-floor outcomes for depths **1–20**, and exports compare-sheet CSV via `tools/sim_balance.py`.

Each default CLI invocation runs two passes:

1. **Trajectory** — full runs from floor 1; builds a loadout bank from median gear at each floor entry.
2. **Isolation** — single-floor runs with injected loadout; measures intrinsic floor difficulty without survivor bias.

This spec records **how to read sim output**, **when a seed is valid for testing**, and **pinned calibration seeds** from stock `data/` (mods disabled in sim paths).

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Related:** `balance` (difficulty profiles), `floor-runes` (spawn rules), `dungeon` (floor-init regen / best-effort fallback).

**Baseline caveat (2026-07-12):** Stock `normal` reflects current `data/` tuning, not a finished designer target. Combat was recently too harsh (e.g. wolf ranged); some knobs were relaxed. Treat sim output as **relative** comparisons after deliberate tweaks, not absolute “correct” difficulty until a balance pass lands.

---

## Tooling

| Path | Role |
|------|------|
| `tools/sim_balance.py` | CLI — hybrid trajectory + isolation analysis |
| `tools/seed_scan_overnight.py` | Offline seed calibration (not player-facing) |
| `src/sim/` | Headless policy, scoring, aggregation |

---

## Requirements

### Requirement: Headless engine execution

The simulator SHALL drive `GameEngine(save_coordinator=None)` without `tcod.context`, without a render loop, and without synthetic `KeyDown` events through `handle_event`. Policy actions SHALL call existing systems/engine APIs directly.

Macguffin pursuit SHALL be out of scope — the bot never pursues macguffin victory.

Modal babysitter SHALL auto-resolve vore, digestion, game-over, and ground-pickup take-all prompts so the turn loop cannot stall.

#### Scenario: Sim does not open a game window

- GIVEN `python tools/sim_balance.py --seconds 5`
- WHEN the analysis completes
- THEN no libtcod window is created
- AND the process exits with code 0

---

### Requirement: Balance analyzer CLI

The project SHALL ship `tools/sim_balance.py` with stock `data/` only (`install_stock_game_data()`).

| Option | Default | Meaning |
|--------|---------|---------|
| `--difficulty` | `normal` | One of `easier`, `normal`, `hard`, `nightmare` |
| `--seconds` | `300` | Total wall-clock budget |
| `--trajectory-fraction` | `0.7` | Fraction of budget for trajectory pass |
| `--output` | `balance_compare.csv` | Compare-sheet or wide CSV path |
| `--format` | `compare` | `compare` (side-by-side) or `wide` (floor rows) |
| `--append` | off | Append run column to existing compare sheet |
| `--label` | auto timestamp | Column header for this run |
| `--curve-output` | none | Optional wide floor-curve file alongside compare |
| `--max-turns` | `50000` | Safety turn cap per run |
| `--seed` | random | RNG root for reproducibility |
| `--floors-max` | `20` | Deepest floor analyzed |
| `--trajectory-only` | off | Skip isolation pass |

#### Scenario: Default hybrid invocation

- GIVEN `python tools/sim_balance.py --difficulty normal --seconds 60`
- WHEN analysis completes
- THEN `meta.trajectory_seconds` and `meta.isolation_seconds` are both greater than zero
- AND compare-sheet rows exist for `traj.f01.*` and `iso.f01.*`

---

### Requirement: Time budget enforcement

The outer `--seconds` budget SHALL be checked **every player turn** so a single run cannot exceed its pass deadline. Trajectory and isolation passes each receive a wall-clock slice; isolation time is split **evenly** across floors `1..floors_max`.

Default split: **70%** trajectory / **30%** isolation (`--trajectory-fraction 0.7`). `--trajectory-only` assigns 100% to trajectory.

#### Scenario: Increasing budget increases sample size

- GIVEN two runs with the same `--seed` and `--difficulty normal`
- WHEN the first uses `--seconds 30` and the second uses `--seconds 120`
- THEN the second run's `traj.f01.runs_reached` SHALL be greater than or equal to the first

---

### Requirement: Compare-sheet CSV output

Default output format SHALL be a **compare sheet** for LibreOffice Calc / Excel:

| Column | Content |
|--------|---------|
| `metric` | Stable row key (`meta.timestamp`, `traj.f07.digest_rate`, `_section.iso`, …) |
| `label` | Human-readable row label (fixed across runs) |
| Run columns | One per analysis pass (`--label` or auto timestamp) |

Metadata SHALL appear as `meta.*` rows (not comment headers). Section separators: `_section.traj` (`--- trajectory ---`), `_section.iso` (`--- isolation ---`).

`--append` SHALL add a new column when `meta.data_fingerprint` matches row order (`floors_max` unchanged). Mismatched fingerprints SHALL still append but designer MUST treat diffs cautiously.

Optional `--curve-output` writes a wide floor table (one run) for charting.

#### Scenario: Append produces side-by-side diff

- GIVEN `balance_compare.csv` from a baseline run
- WHEN `python tools/sim_balance.py --label after_tweak --append --output balance_compare.csv`
- THEN the sheet has a third column `after_tweak`
- AND `metric` / `label` rows are unchanged

---

### Requirement: Stock data only

Sim production paths SHALL load stock `data/` with mods disabled (`install_stock_game_data()`). Compare-sheet runs SHALL record `meta.data_fingerprint` so incompatible tuning diffs are visible.

#### Scenario: Sim matches shipped balance JSON

- GIVEN `install_stock_game_data()` before a trajectory run
- WHEN the run uses default entity/item/rune loaders
- THEN values match shipped `data/` for that install
- AND mod overlays do not apply

---

### Requirement: Two different reasons for “zero runes”

Trajectory metrics distinguish **map placement** from **bot behavior**. Conflating them produces false policy bugs.

| Symptom | Field to check | Meaning |
|---------|----------------|---------|
| Runes never existed on the floor | `runes_on_map = 0` (placement phase) | Floor init used **best-effort** rune placement after `MAX_GEN_ATTEMPTS` failed (`dungeon` spec). Bot cannot collect runes that were never spawned. **Not a sim-policy failure.** |
| Runes existed but bot collected none | `runes_on_map ≥ quota` and `runes_collected = 0` | Placement OK; investigate policy, survival (PR3+), or turn budget. |
| Bot collected some | `runes_collected ≥ 1` | Policy reached and activated at least one floor rune. |

#### Scenario: Placement-failed seed looks like a broken bot

- GIVEN seed **7** (representative placement-failed seed in stock scan seeds 1–100)
- WHEN `new_game(seed=7)` completes
- THEN `runes_on_map` MAY be **0** while `quota` is **3**
- AND a trajectory run MAY end with `runes_collected = 0` without indicating a navigation regression

#### Scenario: Viable seed with working navigation

- GIVEN seed **23** on **normal** difficulty
- WHEN a trajectory run plays up to **5000** player turns
- THEN `runes_on_map` SHALL be **3** at floor entry
- AND `depth_reached` SHALL be **≥ 2**
- AND `runes_collected` MAY be **0** after PR3 if `bail_for_survival` latched early (starter loadout has no heal potions); pre-PR3 scan had **≥ 16** runes on the same seed

---

### Requirement: Interpreting trajectory run fields

| Field | Meaning |
|-------|---------|
| `depth_reached` | Deepest `floor_depth` entered before termination (descent success). |
| `runes_collected` | **Run-wide** floor-rune pickups (`run_stats.runes_collected`), not per-floor quota satisfaction. |
| `runes_on_map` | Floor-rune **entities** present after `new_game` (placement viability). |
| `quota` | `engine.runes_per_floor()` for that difficulty (normal stock: **3**; easier override: **4**). |
| `termination` | Why the run stopped (see table below). |
| `turns_played` | Player turns consumed (`player_turn_count`). |
| `hp_at_end` | Player HP when the run ended; **0** means **stunned** (still alive in vore pipeline), not digested. |
| `monsters_defeated` | Run-wide defeated evil count. |

**Termination values (trajectory):**

| Value | Typical read |
|-------|----------------|
| `TURN_CAP` | Hit `--max-turns` safety cap; run may still have descended and collected runes. |
| `DIGESTED` | Player digested (`game_over` ending). |
| `DEPTH_CAP` | Reached sim floor cap (`floors_max`). |
| `TIME_BUDGET` | Outer `--seconds` deadline hit mid-run. |

**Common pattern before PR3 survival:** `TURN_CAP` + `hp_at_end = 0` + `depth_reached ≥ 2` — bot navigates and descends but often ends **stunned** after combat; upgrade with rest/consumables/bail (PR3), not navigation.

#### Scenario: Good navigation despite stunned ending

- GIVEN seed **23**, normal, `max_turns = 5000`
- WHEN the trajectory run ends with `termination = TURN_CAP` and `hp_at_end = 0`
- THEN `depth_reached` MAY still be **≥ 2**
- AND `runes_collected` MAY be **> 0**

---

### Requirement: Pinned calibration seeds (stock data, 2026-07-12 scan)

Automated integration tests and manual smoke checks SHALL use **pinned** seeds known viable on stock `data/`. Do not use arbitrary low seeds (e.g. **7**, **2–13**) for rune-collection or descent tests without verifying `runes_on_map ≥ quota`.

**Stock scan baseline (seeds 1–100, `tools/seed_scan_overnight.py`, ~7 h):**

- **Placement:** 71 viable (`runes_on_map ≥ quota`), **25** with `runes_on_map = 0`
- **Placement-failed examples:** 2–13, 76–83 (not exhaustive; re-scan after large `data/` changes)
- **Data fingerprint at scan:** `50f7ce079e5abd6513f06b05cf4f401543f5c0ee4b7e417134d48fc7c7d140ff`

**Pinned seeds:**

| Pin | Difficulty | Use | Expectation (stock scan) |
|-----|------------|-----|-------------------------|
| **23** | normal | Primary integration / navigation smoke | `depth_reached ≥ 6`, `runes_collected ≥ 16` in 5000 turns |
| **25** | easier | Deep descent / long-run smoke | `depth_reached ≥ 8`, `runes_collected ≥ 30` in 12000 turns |
| **4242** | easier | PR3 bail / early-descent smoke (post-PR3) | `depth_reached ≥ 2`, `bail_for_survival` on ≥1 floor in 8000 turns |
| **7**, **2–13** | any | **Avoid** for rune/descent tests | `runes_on_map = 0` common |

Re-pin after material changes to dungeon gen, `runes_per_floor`, spread constants, or difficulty overrides.

#### Scenario: Integration test uses pinned normal seed

- GIVEN `tests/test_sim_navigation.py` trajectory integration
- WHEN asserting descent behavior on stock data
- THEN seed **23** and difficulty **normal** SHALL be used unless the test documents a narrower scope

---

### Requirement: Seed scan calibration tool

The project SHALL ship `tools/seed_scan_overnight.py` for offline calibration (not player-facing CLI).

**Outputs:**

| File | Content |
|------|---------|
| `balance_seed_scan.csv` | Incremental rows: `phase`, `seed`, `difficulty`, `max_turns`, `runes_on_map`, `quota`, `depth_reached`, `runes_collected`, `termination`, `hp_at_end`, `elapsed_s` |
| `balance_seed_scan.log` | Human progress log |
| `balance_seed_scan_summary.txt` | Top performers; written on completion |

**Phases:**

1. `placement` — `runes_on_map` vs `quota` per seed
2. `sim_normal` — viable seeds, 5000 turns, normal
3. `sim_easier` — viable seeds ≤60, 8000 turns, easier
4. `sim_deep_*` — promising seeds, 12000 turns (follow-up)

#### Scenario: Designer reads overnight results

- GIVEN `balance_seed_scan_summary.txt` exists
- WHEN reviewing calibration
- THEN start with **Best normal** and **Best easier** rows
- AND use `runes_on_map = 0` rows only to build an avoid-list, not to judge policy

---

### Requirement: Per-floor navigation policy

When survival priorities (stunned, bail, rest, lethal consumables) do not apply, policy SHALL:

1. Path to and activate visible floor runes (WAIT on rune tile)
2. Attack adjacent visible evil when safe
3. Flee visible aquatic evil within threat radius
4. Descend when this floor's rune quota is met and player stands on stairs
5. Otherwise explore via BFS frontier

Descend SHALL require `runes_this_floor ≥ engine.runes_per_floor()` unless `bail_for_survival` is latched.

#### Scenario: Bot descends after quota on pinned seed

- GIVEN seed **23**, difficulty **normal**, trajectory run with sufficient turn budget
- WHEN the run completes
- THEN `depth_reached` SHALL be **≥ 2**

---

### Requirement: Event scoring and trajectory aggregation

Each `FloorOutcomeSnapshot` SHALL receive `event_score` (0–100) via `src/sim/scoring.py`:

| Outcome | Score |
|---------|-------|
| Digested on floor | **100** |
| Otherwise | Weighted sum capped at **99** |

**v1 weights:** runes missed (max 30), consumables spent (max 25), upgrade not improved (10 weapon + 10 armor), early-bail overlay (+10 when descended below quota with bail flag).

`aggregate_trajectory_metrics` SHALL populate all `traj_*` wide/ compare-sheet columns from floor visit snapshots.

**Loadout bank:** median `entry_loadout` per floor stored in `LoadoutBank` on trajectory pass completion. Floors with `traj_runs_reached < 5` fall back to the previous floor profile (floor 1 uses starter dagger/robes medians).

#### Scenario: Compare sheet includes difficulty mean

- GIVEN a completed trajectory pass with floor-1 visits
- WHEN `write_balance_report` emits compare CSV
- THEN `traj.f01.difficulty_mean` SHALL be non-zero when visits recorded sacrifices

---

### Requirement: Isolation pass and iso aggregation

After the trajectory pass, a default CLI invocation SHALL run an **isolation pass** unless `--trajectory-only` is set. Isolation time is `seconds_budget * (1 - trajectory_fraction)` (default **30%**).

**Per-floor bootstrap:** `start_isolation_floor` generates a single floor at depth *d* via `initialize_floor_isolation`, injects loadout from `LoadoutBank.profile_for_floor(d)` (or starter medians when trajectory data is sparse), and plays until digest, descend, turn cap, or slice deadline.

**Time split:** remaining isolation seconds are divided **evenly** across floors `1..floors_max`. Within each floor slice, run as many isolation sims as fit.

**Seeds:** `isolation_seed(base_seed, depth, run_index)` — deterministic per floor/run.

**Loadout injection:** closest stock weapon by `(min_damage + max_damage)`, closest armor by `ac_bonus`, potions/wand counts from profile.

`merge_isolation_into_rows` SHALL populate all `iso_*` wide/compare-sheet columns (same metrics as `traj_*`, with `iso_runs` instead of `traj_runs_reached`).

#### Scenario: Compare sheet includes isolation runs

- GIVEN a completed hybrid analysis with `--seconds ≥ 10` and `floors_max = 3`
- WHEN `write_balance_report` emits compare CSV
- THEN `meta.isolation_runs_total` SHALL be **≥ 1**
- AND `iso.f01.runs` SHALL be **≥ 1** when floor-1 slice had time for at least one run

#### Scenario: Trajectory-only skips isolation

- GIVEN `tools/sim_balance.py --trajectory-only`
- WHEN analysis completes
- THEN `meta.isolation_seconds` SHALL be **0**
- AND all `iso.f*.*` metric rows SHALL be **0**

---

### Requirement: Visible loot and equip

Policy priority **4** (after lethal-risk consumables, before runes): BFS to nearest visible floor loot in categories **weapon, armor, potion, wand**. On tile pickup, auto-equip wielded/worn gear that is **strictly better** than current:

- **Weapon:** higher `(min_damage + max_damage)`; tiebreak `accuracy_bonus`
- **Armor:** higher `ac_bonus`

Per-floor snapshots track:

| Flag | Meaning |
|------|---------|
| `upgrade_weapon_spawned` / `upgrade_armor_spawned` | Strictly-better item vs **floor-entry** loadout was visible at least once |
| `upgrade_weapon_taken` / `upgrade_armor_taken` | Bot wielded/wore strictly-better gear vs floor entry |
| `weapon_improved` / `armor_improved` | Exit loadout strictly better than entry loadout |

While `bail_for_survival` is latched, skip loot goals (straight to stairs).

#### Scenario: Bot paths to visible potion

- GIVEN a visible healing potion on carved floor with no threats
- WHEN policy decides
- THEN action kind is **MOVE** toward the potion tile

---

### Requirement: Survival policy priorities

When not blocked by modals, rest animation, or engulfment, `SimPolicy` SHALL follow this order (see change `design.md` for full table):

1. **Stunned** — quaff heal potion, else teleport delay, else WAIT (doomed)
2. **Bail** — path to stairs; descend when standing on stairs (may descend below rune quota; sets `bail_for_survival`)
3. **Rest** — `begin_rest` when hurt and rest pre-checks pass; ~10% skip when HP ≥ 70% max
4. **Lethal-risk consumable** — heal → wand (non-shark evil) → might → haste when threat thresholds met
5. **PR2 navigation** — runes, adjacent attack, shark flee, quota stairs, explore

Really-bad bail latches when: HP &lt; 25% max without heal potion and visible evil; or ≥3 visible evils; or ≥2 adjacent evils without lethal consumables.

**Post-PR3 note:** Starter loadout has no heal potions. Bail may latch before any floor rune is collected; that is **valid play** (design: bail is not bot failure). Rune-collection trajectory smoke on stock data is re-validated after **PR4** visible-loot pickup supplies consumables.

#### Scenario: Bail flag recorded on snapshot

- GIVEN policy latched `bail_for_survival` on a floor visit
- WHEN the player descends
- THEN `FloorOutcomeSnapshot.bail_for_survival` is true for that floor

---

### Requirement: Pathfinding uses goal-distance BFS

Sim navigation `first_step_toward` SHALL use BFS distances **from the goal tile**, not from the player origin. Using origin distances causes incorrect cardinal bias (always favoring north when all neighbors are distance 1).

When the player stands on a visible floor-rune tile, policy SHALL **WAIT** and activate the rune on that turn (not wander off via explore/attack priority).

#### Scenario: On-rune activation

- GIVEN a visible floor rune at the player’s tile
- WHEN policy executes
- THEN `run_stats.runes_collected` increments
- AND the floor-rune entity is removed

---

### Requirement: Cross-reference balance difficulty

Sim `--difficulty` SHALL select one `depth_scaling.json` profile per invocation (`easier` | `normal` | `hard` | `nightmare`). `runes_per_floor_override` on that profile SHALL affect both placement quota and descend quota in policy.

#### Scenario: Easier requires more runes per floor

- GIVEN difficulty **easier** on stock data
- WHEN `engine.runes_per_floor()` is queried
- THEN quota SHALL be **4** (stock override)
- AND normal quota SHALL remain **3**

---

## Out of scope

- Macguffin pursuit or victory
- Modded `data/` in production sim paths
- Closed-form difficulty calculator (must simulate layout/spawn/loot)
- CI gate on sim runtime
- JSONL per-event export (deferred)

## Related

| Spec / doc | Relation |
|------------|----------|
| `balance/spec.md` | Difficulty profiles; density, runes, prefix spawn |
| `floor-runes/spec.md` | Quota and piece economy |
| `dungeon/spec.md` | Floor init, rune placement fallback |
| `openspec/changes/archive/2026-07-12-add-balance-simulator/` | Design history and PR checklists |