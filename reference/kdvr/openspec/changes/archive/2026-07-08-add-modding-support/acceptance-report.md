# Acceptance: add-modding-support

**Date:** 2026-07-08  
**Status:** Archived (implementation complete)

## Delivered

| Area | Result |
|------|--------|
| Discovery / `mod.state` | PR1 |
| Entities layering + bad-mod popup | PR2 |
| Options → Mods UI + save wipe | PR3 |
| Id catalogs | PR4 |
| Whole-file domains | PR5 |
| Save fingerprint, crash mods, docs | PR6 |
| Live spec | `openspec/specs/modding/spec.md` |
| Startup fix | `load_entities_user_facing` uses module `ENTITIES_PATH` as layered core (monkeypatchable) |

## Full suite (PR7)

```text
python -m pytest tests/ -n 6
1187 passed, 1 failed in ~8m 50s
```

**Failed once:** `tests/test_npc_abilities_rangen.py::test_primary_at_three_preferred_over_neutral_at_two_for_ranged_pick`  
**Re-run only that test:** failed once, then **passed twice** — pre-existing flake (entity identity / target pick), not modding-related. No suite re-run of the full tree after that.

Earlier full runs with `-n auto` (12 workers) hit OpenBLAS OOM; policy updated to **`-n 6`** and **re-run only failed tests**.

## Manual

End-to-end checklist in `testing-checklists.md` (PR7 section) and per-PR checklists. User signed off PR1–PR6 playtests; final archive on PR7 completion.
