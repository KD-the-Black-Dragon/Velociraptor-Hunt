# Manual checklist — PR2 (window & fullscreen)

Run: `python -m src.main`

Settings file: `%LOCALAPPDATA%\KD's Vore Roguelike\settings.json` (Windows)

## First launch (optional — use fresh settings or delete `window` block)

- [ ] With no `window` section in settings, game opens **windowed** (not fullscreen, not maximized)
- [ ] Window fits on screen with margin (not under taskbar/title bar edge-to-edge)
- [ ] Client area is at least **1360×768**

## Persistence

- [ ] Resize the window — quit — relaunch: **same client size** restored
- [ ] Move the window — quit — relaunch: **same position** restored
- [ ] Maximize — quit — relaunch: opens **maximized**
- [ ] After resize, `settings.json` gains/updates a `window` block (may lag slightly during drag — async worker)

## Minimum size

- [ ] Shrink window — stops at **1360×768** client minimum; layout remains usable

## Fullscreen (Options)

- [ ] Options shows **Fullscreen: Off | On** row below UI Layout
- [ ] Toggle **On** — immediately enters fullscreen
- [ ] Toggle **Off** — returns to **prior windowed or maximized** state (same size/position/mode as before fullscreen)
- [ ] Chain: windowed → maximize → fullscreen → off → should be **maximized** again
- [ ] `fullscreen: true` persists in settings when enabled
- [ ] Fresh install default: fullscreen **Off** until user enables

## Regression

- [ ] Map grey colors from PR1 still correct
- [ ] Vore toggles and UI Layout preset still save and work
- [ ] Load Game / New Game / resize during gameplay still work