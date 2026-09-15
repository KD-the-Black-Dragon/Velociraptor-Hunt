# Acceptance Report: four-k-window-size-memory

**Date:** 2026-08-30  
**Scope:** Dual window size sets for 4K vs normal scaling; restore normal size on toggle Off; position clamp on 4K toggle and on exit fullscreen (windowed).

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_four_k_window_size_memory_pr1.py` | passed (incl. exit-fullscreen clamp) |
| Related window / settings / Options 4K tests | passed with PR1 batch |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1: dual sizes, toggle restore, position clamp, maximized/fullscreen skips — designer sign-off **Looks good**
- Follow-up: exit fullscreen applies same `x≥0` / `y≥30` clamp when restoring windowed — designer sign-off **Looks good**

## Live specs / docs

- `openspec/specs/ui-layout/spec.md` — 4K dual size sets, toggle geometry, window persistence fields, fullscreen exit clamp

## Key implementation

| Area | Change |
|------|--------|
| `WindowPreferences` | Optional `four_k_client_width` / `four_k_client_height` |
| `sync_window_from_sdl` | Writes only the active scaling size set |
| `apply_four_k_toggle_geometry` | Seed 2× / swap / position clamp |
| `restore_after_fullscreen` | Windowed position clamp on exit |
| `App.apply_display_layout_from_settings` | Toggle path uses geometry helper |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-four-k-window-size-memory/`.
