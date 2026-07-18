# Depth-jump start (secret menu)

Hidden playtest entry: start a run on floor 2–20 with synthesized mid-run loadout.

## Trigger

- **Ctrl+G** on the **main menu** opens the depth-jump flow.
- Not available during play or other app phases.

## Flow

1. **Name entry** — same rules as **New Game** (`name_entry` spec).
2. **Depth entry** — digits only; **Enter** confirms; **Escape** cancels to main menu.
3. Valid depths: **1** through `max_target_depth` from `data/depth_jump_start.json` (stock **20**).
4. Invalid depth on **Enter** shows **"Please input an integer from 1 to 20"** and keeps the buffer editable.
5. Save overwrite: same **Y/n** prompt as **New Game** when a save exists.

### Depth 1

Choosing depth **1** starts a **normal New Game** (floor 1, starter loadout, `level_warped` false).

### Depth 2–20

Starts on the chosen floor with synthesized loadout and `level_warped = true`.

## Loadout reference depth

For target depth **N ≥ 2**, loot eligibility uses **`N - 1`**.

Items must satisfy stock spawn rules: `spawn_min_depth ≤ depth ≤ spawn_max_depth` and `spawn_weight > 0`. Mods apply via the active item registry.

## Equipment grants

| Category | Rule |
|----------|------|
| Wielded weapon | Strongest eligible: highest `min_damage`, then `max_damage`, then `accuracy_bonus`; ties broken randomly |
| Worn armor | Highest `ac_bonus`; ties broken randomly |
| Throwables | Strongest eligible (same tuple as weapons), stack size from `throwable_stack_count` (stock **5**) |
| Potions | `potion_count` weighted-random picks (stock **3**); duplicates allowed |
| Wands | `wand_count` weighted-random picks (stock **3**); duplicates allowed |

Empty pools omit that category. Durability and wand charges use definition defaults (`durability_max`, `charges_start`).

## Simulated runes

For each floor **1 … N − 1**:

- Let `base = runes_per_floor()` for the active difficulty.
- Simulate `randint(ceil(base × min_num / min_den), base)` runes (stock **⅔–100%**).
- Each rune: weighted random from runes eligible on that floor.
- Apply via `apply_rune_effect` with the run's `rune_pieces_multiplier`.
- Increment `run_stats.runes_collected` per simulated rune.
- After simulation, set player HP to max HP.

## Run metadata

- `level_warped = true` on depth-jump starts (depth ≥ 2).
- Persisted in save snapshots as optional `level_warped` (default false on load).
- Game-over recording **skips** past-runs append when `level_warped` is true.

## Data

`data/depth_jump_start.json` — tunable counts and depth cap. See `data/SCHEMA.md`.