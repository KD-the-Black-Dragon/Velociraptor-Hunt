# Design Document Review: NPC Vore Message Logs (Consolidated)

**Reviewed:** `openspec/design-work/2a662950-design-doc.md` (final)  
**Reviewer:** Systems design review (codebase-verified)  
**Date:** 2026-07-02  
**Round:** 3 (final)

---

## Summary

**0 open issues — approve for implementation.**

Round-2 findings are resolved in the design doc. PR2 correctly splits `pick_npc_vore_message()` removal (`vore.py`) from the optional Q2 parser rename (`entity_loader.py`). PR0 test tasks now include replacement of `test_loader_rejects_invalid_offscreen_type` and note that `test_narrative_index_picks_offscreen_lines` is subsumed by `test_loader_parses_offscreen_vore_object`.

The document is internally consistent across loader rules, migration steps, PR scopes, test tasks, and draft `tasks.md`. Codebase claims from prior rounds remain valid; no implementation drift detected.

**Next step:** Create `openspec/changes/add-npc-vore-message-logs/` from draft artifacts and begin **PR0** only.

---

## Issues

No new issues.

---

## Strengths

1. **Complete and actionable PR0 scope** — parameterized parser, `_DEPRECATED_OFFSCREEN_KEYS` fail-hard check, OV-only JSON nest, full flat→object test migration list, SCHEMA update.

2. **Clear PR1 content-only boundary** — CV/AV placeholders, silence-test rewrites, K7 enforcement via `test_load_default_entities_json`, wolf/shark tone guidance.

3. **PR2 closes the loop** — live spec deltas, design artifact with on-screen authority note, archive supersession, dead-code removal, optional Q2 rename in the correct module.

4. **User-resolved decisions fully reflected** — object schema, fail-hard deprecated keys, off-screen silence/fallback rules, player-modal independence, FOV gating.

5. **Accurate as-built baseline** — runtime routing, entity-first on-screen fallback, off-screen index-only pickers, and wolf/shark OV-only flat data match shipped code.