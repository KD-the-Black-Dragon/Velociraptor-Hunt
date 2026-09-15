# past-runs Specification

## Purpose

The **past-runs** domain records **every completed run** (not only “high” scores), shows run statistics on the **game over recap**, and provides a scrollable **Past Runs** screen from the main menu. A run is recorded only when **game over** opens (digestion today; future victory endings use the same hook). Quit-to-menu does **not** record a run.

Builds on **main-menu**, **save-load**, **digestion**, **floor-runes**, and **macguffins**. Implementation: `src/run_stats.py`, `src/game_over_ending.py`, `src/past_runs/`, `src/ui/past_runs_screen.py`, hooks in `GameEngine` and `App`.

**Terminology:** defeated, stunned, digested — no kill/die/death. Past Runs UI uses **Enemies Defeated** (player-credited monster defeats).

**User data directory** (`KD's Vore Roguelike`, via `src/user_data.py`): Windows `%LOCALAPPDATA%\KD's Vore Roguelike\`; Linux `~/.local/share/KD's Vore Roguelike/`; macOS `~/Library/Application Support/KD's Vore Roguelike/`.

## Requirements

### Requirement: Run Statistics

Each active run SHALL maintain `RunStats` on `GameEngine`:

| Field | Meaning |
|-------|---------|
| `monsters_defeated` | Player-credited defeats only |
| `runes_collected` | Floor runes consumed this run (one per successful step-on activation) |

Counters SHALL reset on `new_game()` and SHALL persist in the autosave snapshot (`run_stats` key; default `{0, 0}` when missing on load).

#### Scenario: Player melee defeat increments counter

- GIVEN an evil NPC at 1 HP adjacent to the player
- WHEN the player bump-attacks and removes the NPC
- THEN `monsters_defeated` increases by 1

#### Scenario: NPC-only defeat does not increment

- GIVEN an evil NPC defeated by another NPC without player involvement
- WHEN the defender is removed
- THEN `monsters_defeated` is unchanged

#### Scenario: Floor rune increments counter

- GIVEN a floor rune on the player's tile
- WHEN `try_activate_floor_rune` succeeds
- THEN `runes_collected` increases by 1

#### Scenario: Run stats round-trip in save

- GIVEN a run with `monsters_defeated` 4 and `runes_collected` 2
- WHEN snapshot → restore runs
- THEN both counters match the pre-save values

### Requirement: Game Over Ending Model

Game over SHALL use structured `GameOverEnding { kind, detail }`. Display text SHALL come from `format_game_over_ending()`:

| `kind` | Display |
|--------|---------|
| `digested` | `Digested by {detail}` |
| `macguffin` | If `detail` starts with `The ` → `found {detail}!`; else → `found the {detail}!` |
| `boss` | `Defeated the boss` |

Digestion sets `kind="digested"` and `detail` to the predator display name unless `macguffins` discovery override applies. Macguffin victory sets `kind="macguffin"` and `detail` to the macguffin `display_name`.

#### Scenario: Digested ending formats correctly

- GIVEN `GameOverEnding(kind="digested", detail="wolf")`
- WHEN formatted for display
- THEN the text is `Digested by wolf`

#### Scenario: Macguffin ending formats with article rule

- GIVEN `GameOverEnding(kind="macguffin", detail="The Sword of Freedom")`
- WHEN formatted for display
- THEN the text is `found The Sword of Freedom!`

#### Scenario: Macguffin digestion override in Past Runs

- GIVEN the player found a macguffin, declined victory, and was later digested
- WHEN `GameOverState.open()` completes
- THEN the past-run entry uses `ending_kind="macguffin"`
- AND the summary line shows the macguffin ending (not `Digested by {predator}`)

### Requirement: Game Over Recap Stats

When game over is active, the recap modal SHALL show:

- Player display name
- Formatted ending line
- `Monsters defeated: {n}`
- `Runes collected: {n}`
- `Depth: {n}`

The recap SHALL **not** show turn count, score, difficulty, or similar metrics. **Enter** SHALL return to the main menu. Difficulty is recorded for the Past Runs board only (see below).

Values SHALL be copied from `RunStats` and `floor_depth` at `GameOverState.open()`.

#### Scenario: Recap shows run stats

- GIVEN a player named `Alex` digested with 3 monsters defeated, 1 rune, depth 5
- WHEN the game over recap is rendered
- THEN the screen includes `Alex`, digested-by fate, `Monsters defeated: 3`, `Runes collected: 1`, and `Depth: 5`
- AND does not include `Score:` or turn count

### Requirement: Past Runs Persistence

Completed runs SHALL append to `{user_data}/past_runs.json` inside `GameOverState.open()`.

Envelope:

```json
{
  "past_runs_format_version": 1,
  "runs": [ { ... } ]
}
```

Each entry:

| Field | Source |
|-------|--------|
| `character_name` | Player display name |
| `ending_kind` | `GameOverEnding.kind` |
| `ending_detail` | `GameOverEnding.detail` |
| `monsters_defeated` | Run stats at game over |
| `runes_collected` | Run stats at game over |
| `depth` | `floor_depth` at game over |
| `date` | Local calendar date `MM/DD/YYYY` at record time |
| `macguffin_score` | Optional; macguffin victory weight when `ending_kind` is `macguffin` (stored only, not shown in Past Runs v1) |

Capacity SHALL be **65535** entries; when full, the **oldest** entry is dropped before append. Writes SHALL use atomic temp-file replace.

#### Scenario: Game over appends one record

- GIVEN a digestion game over for player `Morgan`
- WHEN `GameOverState.open()` completes
- THEN `{user_data}/past_runs.json` contains a new entry with matching name, ending, stats, depth, and date

#### Scenario: Quit to menu does not append

- GIVEN an in-progress run
- WHEN the player confirms quit to menu via Ctrl+Q
- THEN no new past-run entry is written

#### Scenario: Abandoned run not recorded

- GIVEN the player returns to menu without game over
- WHEN the main menu is shown
- THEN the past-runs file is unchanged by that action

### Requirement: Past Runs Sort Order

Display order SHALL sort by: depth descending, runes descending, monsters defeated descending, date ascending (older first). Remaining ties need not be ordered.

#### Scenario: Deeper run listed first

- GIVEN runs at depth 3 and depth 7
- WHEN Past Runs screen builds display lines
- THEN depth 7 appears before depth 3

### Requirement: Past Runs Menu Gating

`Past Runs` SHALL appear on the main menu only when `PastRunsStore.probe()` is true (≥1 valid entry). When empty, the option is **omitted** (same pattern as Load Game).

#### Scenario: No history omits Past Runs

- GIVEN no valid past-runs file or zero entries
- WHEN the main menu is built
- THEN `Past Runs` is not listed

#### Scenario: After game over Past Runs appears

- GIVEN at least one completed run on disk
- WHEN the main menu is shown
- THEN `Past Runs` is listed among options

### Requirement: Past Runs Screen

Selecting **Past Runs** SHALL open a full-screen scrollable list on the root console.

Layout (scroll lines):

```text
PAST RUNS

{Name} - {ending} - {date}
{Difficulty} - Depth {depth} - {runes} Runes - {enemies} Enemies Defeated

{next run...}
```

- **PAST RUNS** title line (distinct color)
- Blank line before the first entry
- Two lines per run; blank line **between** runs (not after the last)
- Difficulty display name (or id) from the run snapshot; **omitted** for legacy records without the field
- No column header row
- Footer: `Esc: back | Arrows: line | PgUp/PgDn: page`
- **Escape** returns to main menu
- Arrow keys scroll one line; Page Up/Down scroll one viewport (same bindings as log overlay)

Long lines MAY truncate with ellipsis to fit console width.

#### Scenario: Past Runs screen shows entry format

- GIVEN a stored run for `Alex`, digested by wolf, date `07/05/2026`, depth 7, 3 runes, 12 enemies defeated
- WHEN Past Runs is opened
- THEN the list includes `Alex - Digested by wolf - 07/05/2026`
- AND `Depth 7 - 3 Runes - 12 Enemies Defeated`

#### Scenario: Escape backs out

- GIVEN the Past Runs screen is shown
- WHEN the player presses Escape
- THEN the main menu is shown

### Requirement: Game Over and Autosave

`GameOverState.open()` SHALL delete all autosave files (per `save-load`). Before wipe, `SaveCoordinator.prepare_for_game_over_wipe()` SHALL flush/cancel pending background writes so a post-wipe autosave cannot resurrect the slot.

Past-run append and autosave wipe are independent: quit-to-menu leaves autosave intact and does not append past runs.

## Supersedes

| Area | Change |
|------|--------|
| `main-menu/spec.md` | High Scores stub → Past Runs; recap includes stats, not score |
| `save-load/spec.md` | Snapshot includes `run_stats`; game-over wipe coordinates with coordinator |

## Acceptance Criteria

1. Run stats increment per design; persist through save/load.
2. Game over recap shows name, ending, monsters, runes, depth; no turn count.
3. Past runs append on game over only; file capped at 65535; gitignored.
4. Past Runs menu option gated; screen uses two-line format with scroll.
5. Automated tests cover store, sort, menu gating, recap render, and stat rules.