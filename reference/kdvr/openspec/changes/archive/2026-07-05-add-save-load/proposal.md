# Proposal: Save / Load System

**Status:** Active — design locked 2026-07-05.

## Why

The game has no run persistence today. Load Game is a stub. Players cannot safely take a break, recover from crashes, or resume after an unexpected shutdown without losing the entire run.

## What

A **single automatic save slot** with **rotating backups**, **background writes**, and **full run fidelity** (map, entities, inventory, runes, FOV memory, AI state, message log, floor depth, RNG, run prefs snapshot, etc.).

| Area | Deliverable |
|------|-------------|
| Persistence | Versioned JSON save document; `{user_data}/saves/` with primary + 3 rotating backups |
| Autosave | Background worker thread; checkpoints at stable gameplay intervals (not every move) |
| Quit save | Ctrl+Q (idle only) → quit confirm + background save together; save even if user cancels quit |
| Manual save | Ctrl+S (idle only) → main-thread save + "Game saved." log line |
| Load | Main menu Load Game restores newest non-corrupt backup; disabled when no save exists |
| New Game guard | Modal if save exists; capital **Y** to proceed; saves deleted only after name confirmed + run starts |
| Permadeath | Game Over → **all save files deleted immediately** |

**Unchanged:** global `settings.json` (Options); manual Explorer backup of save files is allowed.

## Out of scope

- Multiple concurrent save slots / character select
- Turn-perfect autosave (every single move)
- Save recovery after Game Over
- Anti-tamper / encrypted saves
- Saving mid-modal as a first-class guarantee (last stable checkpoint is acceptable)
- High Scores persistence (separate future module)

## Related specs (update on acceptance)

- `openspec/specs/main-menu/spec.md` — Load Game, New Game overwrite, menu enablement
- New `openspec/specs/save-load/spec.md` — normative save/load behavior

## Full design

`design.md` and PR checklist in `tasks.md`.