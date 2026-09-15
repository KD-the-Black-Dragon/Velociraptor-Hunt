# Proposal: 4K window size memory + position clamp

**Status:** Accepted and archived 2026-08-30  
**Change id:** `four-k-window-size-memory`

## Why

Turning **4K UI scaling** On in windowed mode grows the OS window (via the raised minimum client floor). Turning it **Off** does not shrink the window back — so a non-4K player who experimented can be stuck with a window larger than their desktop. Separately, window position can end up extremely negative, hiding the title bar.

## What

1. **Dual window size sets** in `settings.json` `window` block:
   - `client_width` / `client_height` — **normal (non-4K) only**; never overwritten when enabling 4K.
   - `four_k_client_width` / `four_k_client_height` — preferred size while 4K is On (optional until first enable).
2. **Toggle behavior (windowed, not maximized):**
   - **First enable** (no 4K size saved yet): seed 4K size as **2×** the current windowed client size at the current coordinates; apply that size; leave normal sizes untouched.
   - **Later toggles:** swap the live window between the two saved size sets (no blind re-doubling).
   - **Disable:** restore `client_width` / `client_height` so the window shrinks back.
3. **Position clamp on every 4K toggle** (windowed, not maximized): if `x < 0` → `0`; if `y < 30` → `30`.
4. **Resize/move while 4K On** updates only the 4K size set; while Off, only the normal set. Shared `x` / `y`.
5. **Fullscreen / maximized:** size swap and position apply are **windowed-only**; stay maximized when toggling; fullscreen unchanged.

## Out of scope

- Changing tile_scale / 4K glyph math
- Multi-monitor-aware clamp beyond the simple x/y floors
- Separate 4K x/y position sets
- Freeform UI scale slider
- Full pytest suite until final acceptance (targeted tests per PR)

## Past-version / release safety

| Surface | Mitigation |
|---------|------------|
| Missing `four_k_client_*` keys | Treat as “never enabled”; first On seeds 2× current size |
| Older settings with bloated `client_*` after prior 4K experiments | Toggle Off still restores whatever is in `client_*`; user can resize once; first new On seeds from live size into 4K set without further bloating normal |
| Saves / autosaves | No save wire change |
| Mods | No mod schema change |

## Success

- Toggle Off restores a usable normal window size (not a stuck giant frame).
- Preferred normal and 4K sizes persist independently after the first 4K enable.
- Enabling 4K never mutates stored normal `client_width` / `client_height`.
- Negative / off-screen title-bar positions are corrected on toggle (`x≥0`, `y≥30`).
