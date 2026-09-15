# Acceptance Report: engineering-maintainability

**Date:** 2026-07-10  
**Scope:** Five-item player-invisible maintainability pass (PR0–PR12): test helpers, message catalog, save hardening, engine floor/turn/input extract + cleanup, AI package extract + cleanup. Mid-change playtest fixes for door-path memory chase, cold-trail timeout, door shock, and Erratic cadence (documented in live specs).

## Delivered

| Area | Outcome |
|------|---------|
| **PR1** | Spawn-at-depth / difficulty test helpers (`spawn_depth_helpers`) |
| **PR2** | Message catalog discipline + remaining log strings → `messages.py`; `openspec/specs/engineering/spec.md` |
| **PR3** | Save field inventory, additive defaults, `migrate_run` identity stub; `src/save/FIELDS.md` |
| **PR4–PR6** | Engine extract: `engine_floor.py`, `engine_turn.py`, `engine_input.py`; `GameEngine` facade kept |
| **PR7** | Engine deeper cleanup (names, public surface, dead code) |
| **PR8–PR10** | AI package: `explore`, `targeting`, `chase`, `movement`, `visit`, `pipeline` shim |
| **PR11** | AI public API docs, import hygiene, dead `_erratic_pursuit_direction` removed |
| **Playtest fixes** (with this change) | Memory BFS detour; cold-trail timeout (12–18); door shock (2–4); Erratic intentional explore + random stay/no-reverse |

## Out of scope (unchanged)

- Externalize vore narratives from `entities.json`
- Turn-pipeline performance budget module
- Gameplay content backlog (weapons, abilities, balance packs)

## Automated verification

### Full suite (last broad run during PR12)

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Approx. count |
|--------|----------------|
| Passed | ~1370+ |
| Skipped | 2 (perf budget, by design) |
| Failures seen | Density-spawn / session-log patch flakes |

### Acceptance decision (designer)

Designer accepted **targeted stress** of previously failing tests as sufficient (no further full-suite loops):

- Serial ×10 and xdist `-n 6` ×8 on the hardened failure set → **0 fails**
- Fixes: session_log monkeypatch paths, vore resume index snapshot, `ensure_wolf(s)` density pins, Erratic stay-allowed, explore `allow_idle=False` where needed

## Manual verification

Designer signed off PR1–PR11 smoke and mid-stream AI playtests (door pathing, trail timeout, Erratic). Final archive authorized 2026-07-10 without additional full-suite gate.

## Live specs touched

- `openspec/specs/engineering/spec.md` (message policy)
- `openspec/specs/save-load/spec.md` / `src/save/FIELDS.md`
- `openspec/specs/enhancements-3/spec.md` (memory path, door shock, trail timeout)
- `openspec/specs/npc-abilities/spec.md` (Erratic cadence)
