# Tasks: requires-vore-types-capability

## PR1 — Spawn OR semantics + spawn docs

- [x] Change `meets_vore_type_requirements` from AND (`required <= enabled`) to OR (`bool(required & enabled)`)
- [x] Update docstring / comments on that helper
- [x] Update `tests/test_spawn_requires_vore_types_pr1.py` truth table (pairs/all-three with partial prefs → eligible)
- [x] Update `data/SCHEMA.md` spawn.requires_vore_types blurb (capability / OR)
- [x] Update `README.md` and `src/mods/seed_sample.py` MODDING_README / sample notes for OR
- [x] Update live `openspec/specs/npc-data/spec.md` spawn requirement section to OR + capability wording (attempt filter can wait for PR2/PR4 polish)
- [x] Add `testing-checklist-pr1.md`
- [x] Run targeted tests

## PR2 — Initiation capability filter

- [x] Add helper for attemptable narrative types (narrative types ∩ capability if non-empty ∩ prefs)
- [x] Wire `_vore_base_eligible` and `pick_narrative_type` (all try_* paths) through the helper
- [x] Empty pool → still no attempt in this PR (GENERIC in PR3)
- [x] Tests: restricted capability never picks outside list; spawn+attempt happy path with partial prefs
- [x] Add `testing-checklist-pr2.md`
- [x] Run targeted tests; post manual checklist in chat

## PR3 — GENERIC fallback

- [x] Add `GENERIC` constant (not in Options / `VORE_NARRATIVE_TYPES_V1`)
- [x] Hardcoded minimal pools: player attempt/success, player digestion, NPC hit/miss, off-screen vore/digest
- [x] When attempt pool empty → pick `GENERIC`; wire lookups for modal / digest / NPC / off-screen
- [x] Digestion uses standard (non-alternate-CV) path for `GENERIC`
- [x] Tests for empty-pool → GENERIC player and NPC paths
- [x] Add `testing-checklist-pr3.md`
- [x] Run targeted tests; post manual checklist in chat

## PR4 — Spec polish + acceptance + archive

- [x] Align `openspec/specs/{npc-data,vore,modding}/spec.md` scenarios with OR + attempts + GENERIC
- [x] `acceptance-report.md` + `testing-checklists.md` as needed
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-requires-vore-types-capability/`
- [x] Clear `AGENTS.md` active-change pointer
- [x] Full pytest suite only after final user sign-off (AGENTS procedure) — deferred at archive
