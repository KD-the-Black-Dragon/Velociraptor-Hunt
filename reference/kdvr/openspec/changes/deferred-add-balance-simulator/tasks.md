# Tasks: Balance play simulator

**Change:** `add-balance-simulator`  
**Design:** `design.md` (locked 2026-07-10)  
**Status:** **Superseded** — see `openspec/changes/add-balance-simulator/tasks.md`.

---

## PR checklist

- [ ] **PR1** — Runner shell, modal babysitter, struggle stub, single-seed CLI, `SimRunResult`
- [ ] **PR2** — Navigation (explore, rune seek, stairs, shark flee), per-floor quota, descend
- [ ] **PR3** — Threat detection, potion/wand use, rest-to-full when safe, imperfection roll
- [ ] **PR4** — Visible loot goals, weapon/armor pickup + strict-better equip
- [ ] **PR5** — Batch `--runs`, JSONL output, aggregate summary, optional `--jobs`
- [ ] **PR6** — `openspec/specs/balance-simulator/spec.md`, testing checklists, acceptance

---

## Current PR

*(none — deferred)*

---

## Manual validation (after PR5)

Designer runs batch sim in background and confirms:

- [ ] `python tools/sim_balance.py --seed 42` completes without hang
- [ ] `python tools/sim_balance.py --runs 20` finishes in reasonable time
- [ ] Output includes depth, ending, runes, turns
- [ ] Normal difficulty uses live `data/` + enabled mods
- [ ] Bot collects runes and descends (not stuck on floor 1)
- [ ] Bot rests when hurt; uses items when facing multiple enemies
- [ ] Bot avoids sharks when possible

Full steps: `testing-checklists.md` (created in PR6).