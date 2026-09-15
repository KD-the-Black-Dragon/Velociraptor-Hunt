# Acceptance Report: add-dismiss-ally

**Date:** 2026-08-31  
**Scope:** Shift+D dismiss targeting removes free good allies (no turn, not defeat); Help + Tutorial discovery.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_dismiss_ally_pr1.py` | passed (8) |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1: targeting, valid/invalid dismiss, no turn, plain `d` Drop — designer playtest
- PR2: Help + Tutorial lines + PR1 spot-check — designer playtest

## Live specs / docs

- `openspec/specs/command-allies/spec.md` — Dismiss requirement + Help/Tutorial discovery

## Key implementation

| Area | Change |
|------|--------|
| `src/systems/dismiss.py` | `DismissState`, confirm / despawn |
| `src/engine_input.py` | Shift+D enter; cursor handler; Drop requires no Shift |
| `src/messages.py` | exit + invalid lines |
| `src/ui/help_overlay.py` | Shift+D help line |
| `src/ui/tutorial_screen.py` | Actions dismiss line |

## Outcome

**Accepted** (full-suite deferred; pending designer manual sign-off on PR2 checklist). Archive to `openspec/changes/archive/2026-08-31-add-dismiss-ally/`.
