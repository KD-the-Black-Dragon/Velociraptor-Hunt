# Tasks: add-modding-support

**Active PR:** PR7 complete — archived  
**Rule:** One PR at a time; wait for manual playtest sign-off before the next.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` reviewed by user
- [x] `AGENTS.md` **Active change** pointer → `add-modding-support`
- [x] `AGENTS.md` Modding line points at active change (not “not implemented”)
- [x] `deferred-add-modding-support/proposal.md` marked superseded
- [x] User authorizes PR1 coding

---

## PR1 — Discovery and `mod.state`

- [x] `MODS_DIR` on user data paths
- [x] Scan mod folders; ignore non-directories
- [x] Read/write/repair `mod.state` (`E`/`D` + order)
- [x] Default new mods Enabled + append order; alpha assignment on bulk first discovery
- [x] Duplicate-order renumber rewrite
- [x] Unit tests with temp roots (`tests/test_mod_discovery.py`)
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off (user authorized PR2)

---

## PR2 — Entities layered load

- [x] Core `entities.json` then enabled mods by order
- [x] Same `id` → full replace of definition
- [x] Partial mod (only entities) works
- [x] Bad mod entities file: popup (mod + file + reason) + log; skipped contribution; core + others still load
- [x] Registry/cache invalidation API used by later reload (`reload_game_data_caches`)
- [x] Wire startup load path through pipeline (entities)
- [x] Tests: override wolf, add new id, corrupt file reports (mod/file) without silent success, order matters
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off (user authorized PR3)

---

## PR3 — Options → Mods UI + save gate + reload

- [x] Options row **Mods** → submenu
- [x] List / toggle enable / reorder; persist `mod.state`
- [x] Capital-**Y** warning when autosave exists; on confirm delete save chain; end PLAY if active
- [x] Exit Mods → full data reload (entities path complete; other domains still core-only until PR4–5)
- [x] Tests for state toggles/order; save deleted on confirm; no enter without Y when save present
- [x] `testing-checklist-pr3.md`
- [x] Manual playtest sign-off (user authorized PR4)

---

## PR4 — Remaining id catalogs

- [x] weapons, armor, potions, wands, floor_runes, macguffins, names
- [x] Same layering + skip-bad rules
- [x] Tests per domain (fixture JSON, not live balance pins)
- [x] `testing-checklist-pr4.md`
- [x] Manual playtest sign-off (user authorized PR5)

---

## PR5 — Whole-file domains

- [x] dungeon_spawn, rescue_gratitude, ui_layout whole-file replace when present
- [x] ui_layout: Options presets reflect reloaded file after Mods exit
- [x] Tests + `testing-checklist-pr5.md`
- [x] Manual playtest sign-off (user authorized PR6)

---

## PR6 — Saves, diagnostics, docs

- [x] Save fingerprint `enabled_in_order` (names)
- [x] Load Game refuses mismatch/missing mods; stay on main menu; save file kept
- [x] Pre-modding saves ≡ empty mod list
- [x] Crash report real Loaded mods list
- [x] README user-data `mods/` + how to mod; SCHEMA cross-link
- [x] `testing-checklist-pr6.md`
- [x] Manual playtest sign-off (user authorized PR7)

---

## PR7 — Acceptance

- [x] Full `pytest tests/ -n 6` (1187 passed; 1 flake re-run only — passed)
- [x] `openspec/specs/modding/spec.md` from design requirements
- [x] `testing-checklists.md` / `acceptance-report.md`
- [x] Archive change; clear AGENTS active pointer
- [x] Final acceptance packaging (user playtest optional residual checklist)

---

## Out of scope checklist (do not implement)

- [ ] ~~Code mods / custom Python~~
- [ ] ~~Tileset/font mods~~
- [ ] ~~Deep merge spawn bands~~
- [ ] ~~Keep run alive across mod changes~~
