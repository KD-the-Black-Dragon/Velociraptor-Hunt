# Velociraptor Hunt

Small-scope roguelike: **one hunt** in a Jurassic Park–type setting. You are trying
to take a velociraptor that is trying to take you — weather, tall grass, and an
animal that uses every dirty trick, in the spirit of the *Jurassic Park* “clever
girl” scene.

Built in Python with libtcod (ASCII, turn-based). The intended shape is closer to
a **Seven Day Roguelike** than a long career or a many-floor dungeon.

## This folder vs other projects

This tree is a **copy** of **Gladiavore**, which itself spun off **K.D.'s Vore
Roguelike (KDVR)**. Those two games live in **other folders** and stay untouched.

This copy exists so hunt work can **harvest** engine code (FOV, input, message log,
saves, UI chrome, vore hooks) without risking the originals.

| | This folder | Not this folder |
|--|-------------|-----------------|
| Product | **Velociraptor Hunt** | Gladiavore, KDVR |
| Loop (target) | One enclosed hunt | Career hub / dungeon crawl |
| Current `src/` | Hunt loop (menu → weapon → paddock); last change archived `openspec/changes/archive/2026-09-12-hunt-deferred/` | — |

See [`AGENTS.md`](AGENTS.md) and [`KDVR_REFERENCE.md`](KDVR_REFERENCE.md).

## Setup

```bash
pip install -e ".[dev]"
```

Requires the tileset at `data/Alloy_curses_12x12.png` (included).

## Run

```bash
python -m src.main
```

Opens a **main menu**: New Hunt, Stats, Options, Quit.

## User data

Saves, settings, and logs live under **Velociraptor Hunt**. Override with
`VELOCIRAPTOR_HUNT_USER_DATA_DIR` (legacy: `GLADIAVORE_USER_DATA_DIR`,
`KDS_USER_DATA_DIR`).

| OS | Target path |
|----|-------------|
| Windows | `%LOCALAPPDATA%\Velociraptor Hunt\` |
| Linux | `~/.local/share/Velociraptor Hunt/` |
| macOS | `~/Library/Application Support/Velociraptor Hunt/` |

## Design docs

| Path | Role |
|------|------|
| `AGENTS.md` | Project rules for agents |
| `KDVR_REFERENCE.md` | Lineage and harvest policy |
| `openspec/changes/archive/2026-09-04-velociraptor-hunt/` | Accepted foundation (`DESIGN_CANON.md`, PR1–PR11) |

Gladiavore OpenSpec folders remaining in this copy are **historical donor docs**.

## Verify

```bash
python -m pytest tests/ -v -n 4
```
