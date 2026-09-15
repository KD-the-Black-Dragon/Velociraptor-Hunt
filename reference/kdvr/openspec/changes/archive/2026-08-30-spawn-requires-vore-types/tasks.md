# Tasks: spawn-requires-vore-types

## PR1 — Loader + spawn gate + tests

- [x] Extend `SpawnConfig` with `requires_vore_types: frozenset[str]` (default empty = unrestricted)
- [x] Parse `spawn.requires_vore_types` in `entity_loader` (`_SPAWN_TRAITS`; omit/null/[] → empty; keep OV/CV/AV including all-three; ignore unknown tokens; bad type → load error)
- [x] Add `meets_vore_type_requirements(definition, prefs) -> bool`
- [x] Filter floor eligibility / good-quota pools by prefs; thread `engine.vore_content_prefs` into floor spawn
- [x] `spawn_from_definition` accepts prefs and returns `None` when gated; update summon/arena/call sites
- [x] Targeted unit tests (parse matrix, eligibility, density target unchanged with alternate eligible species, summon skip)
- [x] Manual checklist: `testing-checklist-pr1.md`

## PR2 — Stock data, Sample Mod refresh, docs

- [x] Add `"requires_vore_types": []` to every `spawn` in `data/entities.json`
- [x] Update Sample Mod template: `requires_vore_types`, `engulfed_flavor` stubs
- [x] Refresh Sample Mod `entities.json` every launch when missing or contents differ; preserve `mod.state`; create folder if absent (not first-run-only)
- [x] Update `MODDING_README` / README / `data/SCHEMA.md` for the field + Sample Mod ownership
- [x] Tests for Sample Mod refresh (stale rewrite, identical skip, mod.state preserved)
- [x] Manual checklist: `testing-checklist-pr2.md`

## PR3 — Live specs + acceptance + archive

- [x] Update `openspec/specs/npc-data/spec.md` (spawn gate + density invariant)
- [x] Update `openspec/specs/modding/spec.md` (Sample Mod game-owned refresh; field mention as needed)
- [x] Cross-link / brief note in `openspec/specs/vore/spec.md` if useful (prefs drive spawn eligibility)
- [x] Acceptance report + testing-checklists rollup
- [x] Archive change; set AGENTS **Active change:** *(none)*
- [ ] Full pytest only after designer final sign-off (per AGENTS)
