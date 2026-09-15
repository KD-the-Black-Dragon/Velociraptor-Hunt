# Acceptance Report: add-dungeon-layout-overhaul

**Date:** 2026-07-03  
**Scope:** Map sanity regeneration, layout archetypes, doors, floor init + rune spread, background floor prefetch

## Automated verification

### Targeted gate (change tests)

```bash
python -m pytest tests/test_dungeon_layout_pr0.py tests/test_dungeon_layout_pr1.py tests/test_dungeon_layout_pr2.py tests/test_dungeon_layout_pr3.py tests/test_floor_prefetch.py tests/test_dungeon_pr2.py tests/test_floor_runes_pr3.py tests/test_acceptance.py -q
```

| Area | Tests | Result |
|------|-------|--------|
| Sanity / regen (PR0) | `test_dungeon_layout_pr0.py` | PASS |
| Layout archetypes (PR1) | `test_dungeon_layout_pr1.py` | PASS |
| Doors (PR2) | `test_dungeon_layout_pr2.py` | PASS |
| Floor init / runes (PR3) | `test_dungeon_layout_pr3.py`, `test_floor_runes_pr3.py` | PASS |
| Prefetch (PR4) | `test_floor_prefetch.py` | PASS |
| Dungeon regression | `test_dungeon_pr2.py` | PASS |
| Core acceptance | `test_acceptance.py` | PASS |

### Full suite

```bash
python -m pytest tests/ -q
```

| Run | Result |
|-----|--------|
| Targeted gate (2026-07-03) | 74 passed |
| Full suite (2026-07-03) | **721 passed** |

Post-acceptance fixes: four regression tests updated for rune pairwise defaults, larger spawn-tile medians, carved AI arena, and tiered wand damage (defeat-or-damage assertion).

(User-approved skip if flaky: `test_ui_modals.py::test_vore_modal_drawn_on_root_console_over_sidebar`, `test_vore_render.py::test_render_skips_engulfed_npc_prey_glyph`.)

## Manual verification

- [x] PR0–PR1 playtest — layout variety, stair spread, discard logging
- [x] PR2 playtest — doors at corridor mouths; open/close; entity blocking
- [x] PR3 playtest — rune spread (≥20 from entrance); floor init regen
- [x] PR4 playtest — prefetch hit on menu/descent; **no movement hitch** during background prefetch (process pool)
- [x] Consolidated checklist: `testing-checklists.md`

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Map sanity regeneration | PR0 tests, `[map_gen]` logging |
| Layout archetypes 40/40/20 | PR1 tests, F4 force modes |
| Doors at corridor mouths | PR2 tests + playtest |
| Floor init loop | PR3 `initialize_floor` tests |
| Rune ≥20 entrance + inter-rune spread | PR3 tests, `floor-runes` spec |
| Process-isolated prefetch | PR4 tests + playtest |
| Todo rune-cluster resolved | Removed from `openspec/changes/todo/spec.md` |

## Spec updates

- `openspec/specs/dungeon/spec.md` — sanity regen, archetypes, doors, floor init, prefetch, stair spread
- `openspec/specs/floor-runes/spec.md` — item non-blocking, entrance/pairwise spread rules

## Ad-hoc changes folded in (post-PR2)

- Close door: **`c`** then direction (not Ctrl+C)
- Door density: `DOOR_CORRIDOR_MOUTH_CHANCE` 0.55; stricter 1-wide corridor mouth heuristic
- Rune entrance hard floor: never relax below 20 BFS from `enter_xy` (all three runes)
- Prefetch: thread → **`ProcessPoolExecutor`** after GIL stall during gameplay (D25)

## Verdict

**add-dungeon-layout-overhaul: ACCEPTED**