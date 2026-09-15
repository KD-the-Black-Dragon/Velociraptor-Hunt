# Proposal: Debug Support

**Status:** Approved for implementation — OpenSpec bootstrap for review.

**Note (post-archive):** Logs and other user-writable data now live under `{user_data}/` via `src/user_data.py` (not project root `logs/`).

## Why

Players who hit bugs today have little to attach to a report: no crash capture, no session trail, and broken stock `entities.json` surfaces as Python tracebacks. That makes player-reported issues hard to reproduce without source access. **Official modding is not supported** — friendly JSON errors apply to the shipped `data/entities.json` only.

## What

| Area | Deliverable |
|------|-------------|
| Crash reports | On unhandled exception, overwrite `{user_data}/logs/crash.log` with version, OS, Python, timestamp, exception, stack trace, floor, turn, RNG seed/state, player position/HP, active modal, reserved `Loaded mods` stub (`(none)`), session log filename |
| Crash UX | Brief in-window tcod message (`A crash was logged to {user_data}/logs/crash.log`) before exit; stderr fallback pre-window |
| Session log | One `{user_data}/logs/session_YYYY-MM-DD_HH-MM-SS.log` per launch; milestone-only lines on a background worker thread (SaveCoordinator pattern) |
| Session milestones | New game, seed, floor changes, load game, quit, game over, item pickup, enemy defeated (+ `Quit to menu`, debug `Dungeon regenerated`) |
| JSON validation | Friendly plain-English errors for hard `entities.json` failures; **stderr + dialog + `{user_data}/logs/startup_error.log`** (append, timestamped); fixed heading **Unable to start the game due to JSON error.** |
| Soft warnings | Unknown abilities remain warn-and-ignore via existing `LoadWarnings` — not upgraded to hard errors |

**Always on.** Logs live under `{user_data}/logs/` (via `src/user_data.py`; not shipped `data/`). No internet, no settings toggle. Diagnostics fail gracefully — logging errors never crash the game.

`src/debug_log.py` (`DEBUG_STDOUT`) stays unchanged and orthogonal.

## Out of scope (v1)

- Validating loaders other than `entities.json`
- Per-movement or per-turn logging
- Remote crash reporting / analytics
- Log rotation, retention policy, or in-game log viewer
- External mod packages (crash report reserves `Loaded mods: (none)` until `deferred-add-modding-support`)
- `KDS_ENTITIES_PATH` env override
- Upgrading soft ability warnings to hard errors
- `SaveCoordinator.close()` in `main()` shutdown

## Capabilities

### New

- `debug-support` — crash reports, session logs, friendly entity validation

### Modified

- `src/main.py` — session lifecycle, deferred `App` import, validation gate, crash handler (by PR)
- `src/spawn.py` — lazy registry load (enables pre-window validation)
- `src/app.py`, `src/engine.py`, combat/inventory/digestion systems — milestone hooks (PR3)

## User decisions (final)

| Topic | Choice |
|-------|--------|
| Log location | `{user_data}/logs/` |
| Enablement | Always on |
| Validation scope | `entities.json` only |
| Unknown abilities | Soft warnings only |
| Crash UX | In-window tcod message |
| Session milestones | New game, seed, floors, load, quit, game over, pickup, defeat |

## PR order

**PR1 → PR2 → PR3 → PR4 → PR5** — sequential: session core → validation → milestones → crash → acceptance.

## Related specs (on acceptance)

- New `openspec/specs/debug-support/spec.md`

## Log interpretation (for bug triage + AI agents)

Players may send `{user_data}/logs/` weeks later; conversation context will be gone. The change includes a durable **`log-interpretation-guide.md`** — field-by-field `crash.log` reference, session line glossary, modal label dictionary, triage workflow, and a suggested prompt for Grok Build. Shipped in PR5; linked from README and live spec.

## Full design

`design.md`, `log-interpretation-guide.md`, and PR checklist in `tasks.md`.