# Tasks: entity-mod-deep-merge

**Active PR:** PR3 complete — archived  
**Rule:** One PR at a time; do not implement until the user explicitly authorizes that PR.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` reviewed by user
- [x] `AGENTS.md` **Active change** pointer → `entity-mod-deep-merge`
- [x] Resolved decisions confirmed (entities-only; objects deep-merge / arrays replace; stacked deep-merge)
- [x] User authorizes PR1 coding

---

## PR1 — Deep merge + tests

- [x] Pure JSON deep-merge helper (objects recurse; arrays/scalars/`null` replace; type mismatch → replace)
- [x] Entity layering path uses deep merge when `id` already exists in the running catalog; new ids insert as full entries
- [x] Non-entity id catalogs unchanged (full replace by id)
- [x] Validate after each mod’s entity merge; on failure skip that mod’s `entities.json` contribution (existing issue reporting)
- [x] Tests with **pinned** `tmp_path` core/mod fixtures only (no live `data/entities.json`):
  - [x] `spawn.weight: 0` patch inherits other wolf fields
  - [x] Nested `vore_narratives.OV` array replace keeps `CV`/`AV`
  - [x] Mod A then Mod B stacking (name from A, weight from B)
  - [x] New incomplete id fails / skipped with issue
  - [x] Full-copy override still works
  - [x] `abilities: []` clears abilities
  - [x] Disabled mod still ignored
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off

---

## PR2 — Docs and live spec

- [x] Update `openspec/specs/modding/spec.md` (entity deep merge vs other id catalogs; scenarios)
- [x] Update `README.md` Modding section (patch examples)
- [x] Update `data/SCHEMA.md` Modding merge table + short entity patch note
- [x] Update sample mod / `MODDING_README` text in `src/mods/seed_sample.py`
- [x] Refresh `MODDING_README.txt` each launch when missing or contents differ (Sample Mod still create-once)
- [x] `testing-checklist-pr2.md` (doc/read-through + one smoke patch mod)
- [x] Manual playtest / doc sign-off

---

## PR3 — Acceptance and archive

- [x] `testing-checklists.md` + `acceptance-report.md`
- [x] Full pytest suite per AGENTS **Full test suite runs** — **skipped** (designer: defer full regression until release-build anticipation)
- [x] Archive to `openspec/changes/archive/2026-08-30-entity-mod-deep-merge/`
- [x] Clear `AGENTS.md` **Active change** pointer
- [x] Final user sign-off (PR2 “looks good” + authorize PR3)
