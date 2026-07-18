# Gladiavore

Career roguelike: curated arena matches, downtime management, and beast-pit combat.
Built in Python with libtcod (ASCII, turn-based / AUT-based tactical combat).

This repository began as a clone of **K.D.'s Vore Roguelike (KDVR)**. The product is
**Gladiavore**. See [`KDVR_REFERENCE.md`](KDVR_REFERENCE.md) and
[`openspec/changes/gladiavore-foundation/`](openspec/changes/gladiavore-foundation/)
for design and harvest rules.

## Setup

```bash
pip install -e ".[dev]"
```

Requires the tileset at `data/Alloy_curses_12x12.png` (included).

## Run

```bash
python -m src.main
```

Or, after install: `gladiavore`

The game opens to a **main menu**. Gameplay is mid-migration from the KDVR dungeon
loop toward the Gladiavore career/hub/match loop (see foundation design).

## User data

Saves, settings, past-run history, and diagnostic logs are stored outside the game
directory under **Gladiavore**:

| OS | Path |
|----|------|
| Windows | `%LOCALAPPDATA%\Gladiavore\` |
| Linux | `~/.local/share/Gladiavore/` |
| macOS | `~/Library/Application Support/Gladiavore/` |

| File / folder | Contents |
|---------------|----------|
| `saves/` | Autosave chain |
| `past_runs.json` | Completed run history |
| `settings.json` | Preferences, UI layout, window state |
| `mods/` | Player mods (if enabled) |
| `logs/` | Crash reports, session logs |

Override for tests/dev: env `GLADIAVORE_USER_DATA_DIR` (legacy: `KDS_USER_DATA_DIR`).

## Design docs (agents & contributors)

| Path | Role |
|------|------|
| `AGENTS.md` | Project rules |
| `KDVR_REFERENCE.md` | Clone lineage / harvest policy |
| `openspec/changes/gladiavore-foundation/` | Active foundation change (`proposal.md`, `design.md`, `tasks.md`) |

## Windows alpha release

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip install --upgrade build pyinstaller
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_alpha.ps1
```

Output defaults to `dist/gladiavore/` and a zip archive (see script).

## Verify

```bash
python -m pytest tests/ -v -n 4
```
