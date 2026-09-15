# debug-support Specification

## Purpose

The **debug-support** domain provides always-on, local-only diagnostics: **crash reports**, **milestone session logs**, and **friendlier hard failures** for stock `data/entities.json`. It helps **players** attach reproducible context to bug reports without network access or developer tooling.

Implementation lives in `src/debug/`. `src/debug_log.py` (`DEBUG_STDOUT`) remains orthogonal developer stdout logging.

**Modding:** Crash reports list enabled mod folder names in load order, or `(none)`. See `openspec/specs/modding/spec.md`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Log triage:** See `openspec/changes/archive/2026-07-06-add-debug-support/log-interpretation-guide.md` (field glossary, modal labels, session lines, agent workflow).

**User data directory** (`KD's Vore Roguelike`, via `src/user_data.py`): Windows `%LOCALAPPDATA%\KD's Vore Roguelike\`; Linux `~/.local/share/KD's Vore Roguelike/`; macOS `~/Library/Application Support/KD's Vore Roguelike/`.

## Requirements

### Requirement: Log Directory

Diagnostic files SHALL live under `{user_data}/logs/`. The game SHALL create the directory when needed. Logging failures SHALL be swallowed — diagnostics MUST NOT crash the game.

| File | Behavior |
|------|----------|
| `{user_data}/logs/crash.log` | Overwritten on each unhandled crash |
| `{user_data}/logs/session_YYYY-MM-DD_HH-MM-SS.log` | One file per process launch; local timestamp in filename |
| `{user_data}/logs/startup_error.log` | Append-only JSON validation failures at startup |

#### Scenario: Normal launch creates session file

- GIVEN `python -m src.main` starts
- WHEN `session_log.start_session()` runs
- THEN `{user_data}/logs/` exists
- AND an empty `session_*.log` file is reserved for this launch

### Requirement: Session Log Worker

Milestone lines SHALL be enqueued on the main thread and written by a daemon background worker (`SessionLogCoordinator`), mirroring the save-coordinator pattern. `log()` SHALL be a no-op before `start_session()`. `main()` SHALL call `close()` in `finally` to flush and stop the worker.

#### Scenario: Milestones appear after flush

- GIVEN a started session
- WHEN `session_log.log("Entered floor 1")` is called and the worker drains
- THEN the line appears in the session file with a trailing newline

### Requirement: Session Milestone Lines

The session log SHALL record **milestones only** — plain text, no per-line timestamps. v1 formats:

| Line | When |
|------|------|
| `Started new game` | `App._start_new_game()` before `_enter_play()` |
| `Seed: {n}` | `_initialize_floor_new` when `log_session_milestones=True` |
| `Entered floor {n}` | Floor init (new game or descend) when milestones enabled |
| `Loaded game` | Successful save load |
| `Collected {display_name}` | Item added to inventory |
| `Defeated {name}` | `RunStats.record_monster_defeated(defeated_entity=...)` |
| `Game over` | `GameOverState.open()` |
| `Quit to menu` | `App._return_to_menu()` |
| `Quit` | `main()` `finally` when `should_log_quit_milestone()` |
| `Dungeon regenerated` | Debug hotkey **R** only (`log_session_milestones=False` on regen) |

Canonical new-game order: `Started new game` → `Seed: {n}` → `Entered floor 1`.

#### Scenario: Debug R does not duplicate seed/floor

- GIVEN the player presses **R** during PLAY
- WHEN the dungeon regenerates
- THEN the session log contains `Dungeon regenerated`
- AND does not append new `Seed:` or `Entered floor` lines from that regen

### Requirement: Process Exit Quit Milestone

`Quit` SHALL be logged only from `main()` `finally` when `should_log_quit_milestone()` is true. `skip_quit_milestone(reason=...)` SHALL suppress `Quit` for:

| Reason | Caller |
|--------|--------|
| `startup_validation` | `main()` before `sys.exit(1)` on `entities.json` hard failure |
| `crash` | Crash excepthook and belt-and-suspenders `run_loop` handler |

Normal menu **Exit**, window **X**, and successful shutdown SHALL log `Quit`. `Quit to menu` remains separate in `_return_to_menu()`.

#### Scenario: Crash skips Quit

- GIVEN an unhandled exception during PLAY
- WHEN the crash handler runs and `finally` executes
- THEN `{user_data}/logs/crash.log` is written
- AND the session file does not end with `Quit`

### Requirement: Crash Reports

On unhandled exception (not `SystemExit`, not `KeyboardInterrupt`), the game SHALL:

1. Build context from registered `App` / `GameEngine` (may be partial pre-window)
2. Overwrite `{user_data}/logs/crash.log` synchronously on the crashing thread
3. Show brief UX: in-window overlay with the full path to `crash.log` when tcod context is registered; otherwise stderr (no sleep)
4. Call `skip_quit_milestone(reason="crash")` and exit with code 1

`install_crash_handler()` SHALL run after `start_session()` and before `App` construction. `register_app` / `register_ui` wire live context.

Crash log sections: header (timestamp UTC ISO-8601, game version, Python, platform, OS), exception, stack trace, game state (phase, active modal, floor, turn, RNG seed/state, player position/HP, macguffin discovered, `Loaded mods: (none)`), session log path.

`active_modal_label(app)` SHALL use the full priority table (broader than `modal_blocks_quit()`). `macguffin_discovery` is game-state only — not a modal label. No active overlay SHALL render as `Active modal: (none)`.

#### Scenario: F6 force-crash during PLAY

- GIVEN the player is in PLAY
- WHEN they press debug hotkey **F6**
- THEN `ForceCrashError: F6 debug force-crash` is raised
- AND `{user_data}/logs/crash.log` is written with game state and session log reference

### Requirement: entities.json Startup Validation

Before deferred `App` import, `main()` SHALL call `load_entities_user_facing()`. On hard failure:

1. **stderr** — heading `Unable to start the game due to JSON error.` plus formatted detail
2. **Dialog** — tkinter modal with same heading and scrollable detail (skipped when `KDS_SKIP_STARTUP_DIALOG=1`)
3. **`{user_data}/logs/startup_error.log`** — append with local timestamp prefix per entry
4. `skip_quit_milestone(reason="startup_validation")` then `sys.exit(1)` — no gameplay window

Friendly format SHALL be plain English, no Python traceback on the user-facing path. Scope is **stock `data/entities.json` only**.

Unknown abilities SHALL remain soft warnings via `LoadWarnings` / `filter_known_abilities()` — warn-and-ignore, not hard errors.

`src/spawn.py` SHALL lazy-load the entity registry (PEP 562 `__getattr__`) so validation can run before `App` import.

#### Scenario: Broken JSON blocks startup

- GIVEN `entities.json` is syntactically invalid
- WHEN `python -m src.main` runs
- THEN exit code is 1
- AND stderr contains the fixed heading and `Problem:`
- AND no `Quit` line is written to the session log

### Requirement: Game Version

`GAME_VERSION` SHALL resolve: installed package metadata → `pyproject.toml` → `"dev"`.

## Related specs

- **npc-data** — `entities.json` schema validated at startup (hard errors only in v1)
- **save-load** — session logs do not include save contents; crash log references session filename only

## Implementation map

| Concern | Location |
|---------|----------|
| User data paths | `src/user_data.py` |
| Entry wiring | `src/main.py` |
| Session log | `src/debug/session_log.py` |
| Crash handler | `src/debug/crash_report.py` |
| Crash context | `src/debug/context.py` |
| Modal snapshot | `src/debug/modal_snapshot.py` |
| Startup errors | `src/debug/startup_error.py` |
| Entity validation UX | `src/data/entity_validation.py` |
| Force-crash debug key | `src/debug/force_crash.py`, `GameEngine` **F6** |
| Milestone hooks | `src/app.py`, `src/engine.py`, `src/run_stats.py`, `src/systems/*.py` |

**Archived change:** `openspec/changes/archive/2026-07-06-add-debug-support/`