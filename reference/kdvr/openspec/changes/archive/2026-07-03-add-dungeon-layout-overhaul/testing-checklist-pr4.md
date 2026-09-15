# Manual checklist — PR4 (background floor prefetch)

Run: `python -m src.main`

## Main menu prefetch

- [ ] Stay on title screen **3–5 seconds**, then start **New Game** — first floor appears with **no noticeable hitch** (compare to immediate New Game on cold start)
- [ ] PowerShell may show `[prefetch] ready` / `[prefetch] miss` debug lines if enabled

## Descent prefetch

- [ ] Descend to floor 2 — transition should feel **instant** when prefetch completed during floor 1 exploration
- [ ] Descend again immediately (speed-run stairs) — may fall back to sync gen (acceptable); **no crash or soft-lock**

## Invalidation

- [ ] Toggle **F3** water testing or **F4** layout force, press **R** — next floor uses new settings (stale prefetch not served)
- [ ] Return to menu from game — title idle again prefetches depth-1 map

## Process isolation

- [ ] While exploring a floor, movement stays responsive even when PowerShell shows `[map_gen] rejected attempt` from prefetch (work happens off the gameplay core)

## Regression

- [ ] PR0–PR3 behavior unchanged when prefetch misses
- [ ] Door density reasonable (not grid-like); runes/NPCs spawn normally after adopted map

## Automated

- [ ] `pytest tests/test_floor_prefetch.py -q` (or PR4 test module name)