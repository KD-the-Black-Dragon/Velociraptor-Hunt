# Tasks: Balance difficulty analyzer

**Change:** `add-balance-simulator`  
**Design:** `design.md` (approved 2026-07-11, Option 4 hybrid)  
**Status:** **Archived** 2026-07-12

---

## PR checklist

- [x] **PR1** — Runner shell, snapshots, modal babysitter, stock data loader, time-budget loop, CSV skeleton
- [x] **PR2** — Navigation (explore, rune, stairs, loot, shark flee), per-floor quota, descend
- [x] **PR3** — Lethal-risk consumables, rest, stunned heal/teleport, bail-for-stairs
- [x] **PR4** — Visible loot, strict-better equip, upgrade spawn/take tracking
- [x] **PR5** — Trajectory scoring + aggregation, all `traj_*` CSV columns, loadout bank
- [x] **PR6** — Isolation pass, loadout injection, all `iso_*` CSV columns
- [x] **PR7** — `openspec/specs/balance-simulator/spec.md`, testing checklists, acceptance

---

## Current PR

**Complete** — archived 2026-07-12

---

## Manual validation (after PR7)

Designer confirms:

- [ ] `python tools/sim_balance.py --difficulty normal --seconds 60` completes without hang
- [ ] CSV has rows for floors 1–20 with `traj_*` and `iso_*` columns
- [ ] Increasing `--seconds` increases `traj_runs_reached` on floor 1
- [ ] Stock `data/` only (mods disabled in sim)
- [ ] Bot collects runes and descends on early floors (not stuck)
- [ ] Bot rests when hurt; uses consumables under threat; bails when really bad
- [ ] Bot avoids aquatic threats
- [ ] Re-run after a deliberate spawn tweak produces CSV diff visible in Excel
- [ ] `traj_digest_when_weapon_spawned` vs `traj_digest_when_weapon_not_spawned` columns populate

Full steps: `testing-checklists.md` (created in PR7).