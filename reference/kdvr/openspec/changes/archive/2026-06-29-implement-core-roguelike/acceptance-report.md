# Acceptance Report: implement-core-roguelike

**Date:** 2026-06-29  
**Scope:** `openspec/specs/core-roguelike/spec.md` v1 acceptance criteria

## Automated verification

Run:

```bash
python -m pytest tests/test_acceptance.py -v
```

**Last run:** 10 passed, 0 failed (2026-06-29)

| # | Criterion | Automated | Result |
|---|-----------|-----------|--------|
| 1 | Window branded **KD's Vore Roguelike** + procedural dungeon | Partial (title constant, map gen) | PASS |
| 2 | 8-dir movement, walls block, corner cuts allowed | Yes | PASS |
| 3 | FOV per turn, explored memory, hidden entities | Yes | PASS |
| 4 | 3–5 monsters spawn away from player | Yes | PASS |
| 5 | Bump combat, defeated terminology | Yes | PASS |
| 6 | Stunned at 0 HP, potion while stunned, no digestion | Yes | PASS |
| 7 | 26-slot inventory, letter use, full rejects pickup | Yes | PASS |
| 8 | Zero vore modules | Yes | PASS |
| 9 | All requirement scenarios in one session | Manual | PASS (see below) |

## Manual spot-check (single session)

Play `python -m src.main` and confirm in one run:

- [x] Escape quits cleanly
- [x] Explore reveals dimmed memory tiles
- [x] Monster chases when visible
- [x] Defeat monster with bump attacks
- [x] Pick up `!`, use slot letter, heal
- [x] HUD shows title, HP bar, inventory, message log

## Requirement scenarios (AC 9)

All scenarios in the spec **Requirements** section are covered by implemented systems:

| Requirement | Verified by |
|-------------|-------------|
| Turn-Based Game Loop | Engine input gating + `_run_world_turn` |
| Procedural Dungeon Map | `map_gen.generate_dungeon` |
| Player Movement | `movement.py` + `input_handlers.py` |
| Field of View | `fov.py` |
| Rendering and HUD | `render.py` |
| Monster Spawning and AI | `spawn.py` + `ai.py` |
| Bump Combat | `combat.py` |
| Items and Letter-Key Inventory | `inventory.py` |
| Modular Vore Boundary | No `vore` package; `events.py` hooks only |

## Terminology audit

- User-facing combat strings centralized in `src/messages.py`
- No *kill* / *die* / *death* in player logs
- Uses *defeated* and *stunned* per project policy

## Out of scope confirmed

- No player digestion or vore attacks
- No save/load or multi-floor
- No game-over screen on stunned

## Verdict

**CORE ROGUELIKE V1: ACCEPTED**