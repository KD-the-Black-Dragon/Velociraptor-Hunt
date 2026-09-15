# Tasks: Thrown weapons and ranged pathing

**Change:** `add-thrown-weapons-and-ranged-pathing`  
**Design:** `design.md` (locked 2026-07-10)

---

## PR checklist

- [x] **PR1** — `SmiteN` rename: parser, `SmiteAbility`, collapse rules, specs/SCHEMA/tests; split `npc_smites_*` messages; wire Smite NPC + wand to smite logs (no Path yet)
- [x] **PR2** — Path core: `ranged_path.py`, bresenham, alignment block, beam first-fighter hit, `perform_npc_path_attack` + shoot logs
- [x] **PR3** — NPC `RangeN` (Path) ability + AI: path-valid target filter, kite (evil), near-player (good), distance ≥ 2
- [x] **PR4** — Projectile animation (FOV-gated) for Path player + NPC shots
- [x] **PR5** — `throwables.json`, loader/registry, `ItemCategory.THROWABLE`, spawn pool, stacking, starter 5 rocks slot `c`
- [x] **PR6** — Player `f` / `F` fire: auto best-damage pick, manual modal, target cursor, Path resolve, exact error strings, turn consume
- [x] **PR7** — Stock catalog (9 throwables depth 1–20), fox archer `Range5`, help overlay (`f` / `F`)
- [x] **PR8** — Live specs (`ranged-targeting`, updates to `inventory-items`, `equipment-catalog`, `npc-abilities`), testing checklists, acceptance

---

## Current PR

**Complete** — PR1–PR8 shipped; change archived 2026-07-11.

---

## Per-PR testing notes

| PR | Targeted tests (indicative) |
|----|----------------------------|
| PR1 | `test_ability_parser.py`, npc ability tests using `Smite2`, message tests |
| PR2 | `tests/test_ranged_path.py` (new) |
| PR3 | `tests/test_npc_abilities_range_path.py` (new), knockback/lifedrain with Path |
| PR4 | Manual + optional render smoke |
| PR5 | `tests/test_throwables_pr5.py` (new), starter loadout |
| PR6 | `tests/test_player_throw_pr6.py` (new) |
| PR7 | Content validation, entity load |
| PR8 | Full `pytest tests/ -v -n 4` per AGENTS.md acceptance workflow |

---

## Manual validation (after PR7)

Run: `python -m src.main`

- [ ] New game: slot `c` has 5 rocks; `a` dagger wielded, `b` robes worn
- [ ] `f` at visible evil opens cursor with best throwable ready (rock early); throw consumes stack
- [ ] `F` lists throwables; can pick weaker item
- [ ] Good/neutral in path → *"Something is in the way."*
- [ ] Enter on empty tile → *"There's no target there."*
- [ ] Miss line: *"Your throw misses the …"*
- [ ] Wand still works (Smite); no path block for wand through ally
- [ ] Fox archer shoots (not smites); ally blocking prevents shot
- [ ] Projectile glyph visible when in FOV
- [ ] Help lists `f` and `F`

Full checklist: `testing-checklists.md` (PR8).