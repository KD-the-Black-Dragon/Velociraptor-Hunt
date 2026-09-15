# Proposal: Balance play simulator

**Status:** **Superseded** (2026-07-11) — reopened as active change with hybrid per-floor design.  
**Active design:** `openspec/changes/add-balance-simulator/`  
**Change id:** `add-balance-simulator` (this folder retained for history only)

## Why

Balance tuning today relies on manual playtesting. A headless bot that runs many seeded games against **live** `data/` (and enabled mods) can produce depth distributions, death-cause mixes, and rune-collection rates — useful signals when changing `depth_scaling.json`, spawn weights, or floor economy.

## What

1. **Headless runner** — `GameEngine` without SDL window or save coordinator; background CLI process.
2. **Policy bot** — algorithmic player that:
   - explores and seeks floor runes;
   - collects visible upgrades (weapons, armor, potions, wands);
   - equips strictly-better gear;
   - rests to maximize HP when safe;
   - uses consumables freely when threatened (especially multiple visible enemies);
   - avoids sharks rather than fighting them;
   - descends after collecting the floor's rune quota, then repeats until stunned or digested.
3. **Live data** — default entity/item/rune/spawn loaders (`path=None`); enabled mods from user settings; **not** test fixture JSON.
4. **Batch harness** — many seeds, aggregate JSON/CSV summary; default difficulty **Normal** (CLI override).
5. **Spec** — new `openspec/specs/balance-simulator/spec.md` on archive.

## Explicitly out

- Launching the graphical `.exe` / `python -m src.main` loop.
- Perfect or human-like play; macguffin victory pursuit.
- CI performance gating on sim runtime.
- Synthetic keyboard replay through `handle_event` (prefer direct engine/system calls).
- Policy knobs in JSON (v1 hardcoded thresholds in Python; data-driven knobs deferred).

## Success

Designer can run `python tools/sim_balance.py --runs 100` in the background and get a summary (median depth, ending mix, runes/run) using the same content stack as a normal New Game. Bot does not stall on modals or inventory flows.