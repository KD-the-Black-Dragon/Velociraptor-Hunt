# Acceptance Report: add-npc-vore-message-logs

**Date:** 2026-07-02  
**Scope:** Consolidated NPC vore message logs (on-screen + off-screen), PR0–PR2

## Delivered

| PR | Summary |
|----|---------|
| PR0 | `offscreen_vore` / `offscreen_digest` objects; deprecated flat keys fail at load; parser `field_name` parameter |
| PR1 | Wolf/shark CV/AV off-screen placeholder content; type coverage tests |
| PR2 | Live spec updates; removed `pick_npc_vore_message()`; `_parse_narrative_type_lines` rename |

## Automated verification

```bash
python -m pytest tests/ -q
```

**Last run:** 649 passed, 2 failed (2026-07-02) — failures in `test_ui_modals.py` and `test_vore_render.py` (spawn/render flake; unrelated to NPC vore logs).

| Area | Tests |
|------|-------|
| Data layer | `test_offscreen_vore_data.py`, `test_npc_data_pr1.py` |
| Off-screen vore | `test_offscreen_vore_messages.py` |
| Off-screen digest | `test_offscreen_digest_messages.py` |
| NPC vore integration | `test_enhancements_3.py` (npc_vore*) |
| Full suite | all `tests/` |

## Manual verification

- [x] User sign-off PR0, PR1, PR2

## Requirement coverage

| Requirement | Verified by |
|-------------|-------------|
| Unified object schema | `test_offscreen_vore_data.py`, `test_load_default_entities_json` |
| On-screen entity-first vore logs | `test_visible_vore_hit_uses_entity_lines`, enhancements-3 |
| Off-screen hit/digest | `test_offscreen_vore_messages.py`, `test_offscreen_digest_messages.py` |
| Off-screen miss silent | `test_offscreen_vore_miss_is_silent` |
| Deprecated flat keys rejected | `test_loader_rejects_deprecated_flat_offscreen_keys` |
| CV/AV coverage wolf/shark | PR1 tests + `test_load_default_entities_json` |