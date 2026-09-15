# Acceptance Report: fix-deferred-bugfixes

**Date:** 2026-07-04  
**Scope:** Message log UX (wrap, categories, markup, font, full log, help), rune status corner, narrative capitalization, debug stdout gate, pursuit momentum, neutral explore anti-stuck shim, good–neutral corridor swap (PR0–PR11)

## Automated verification

### Change gate (targeted)

```bash
python -m pytest tests/test_debug_log.py tests/test_message_log_wrap.py tests/test_message_log_categories.py tests/test_log_markup.py tests/test_log_font.py tests/test_log_overlay.py tests/test_help_overlay.py tests/test_status_corner_runes.py tests/test_narrative_capitalization.py tests/test_chase_pursuit_momentum.py tests/test_neutral_explore_antistuck.py tests/test_good_neutral_corridor_swap.py tests/test_ui_message_log.py tests/test_ui_status_corner.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **107** |

### Full suite

```bash
python -m pytest -q
```

| Result | Count |
|--------|-------|
| Passed | 829 |
| Failed | 7 |
| Warnings | 102 |
| Duration | ~26 min |

**Failures (not introduced by this change):**

| Test | Likely cause |
|------|----------------|
| `test_load_default_entities_json` | Stale assertion vs loaded spawn weight (env/cache) |
| `test_good_prioritizes_engulfing_predator_over_closer_evil` | `iter_wolves` empty — spawn/density setup |
| `test_engulfed_player_immune_to_combat_damage` | Second wolf not spawned |
| `test_evil_priority_primary_over_neutral` | Target pick order / FOV layout flake |
| `test_engulfed_good_npc_invisible_to_evil_ai` | Insufficient wolves on floor |
| `test_erratic_at_range_one_pursuit_and_one_random_move` | Movement distance tie (flake) |
| `test_primary_at_three_preferred_over_neutral_at_two_for_ranged_pick` | Ranged target pick with diagonal neutral |

No failures in change-gate tests. Follow-up: stabilize wolf-count-dependent tests separately.

## Manual verification

- [x] PR0–PR11 incremental playtest sign-off (user)
- [x] PR10 partial sign-off — ping-pong fixed; broader explore deferred to `better-npc-exploration`
- [x] PR11 sign-off — knight swaps through neutrals; two-knight freeze fixed (good pathing excludes good bumps)
- [x] Final acceptance sign-off (2026-07-04)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR0 | `DEBUG_STDOUT` env gate for map/AI/prefetch prints |
| PR1 | Message log word wrap |
| PR2 | Six message categories + migration |
| PR3 | Per-word JSON log markup (experimental) |
| PR4 | Proportional TTF for log panel |
| PR5 | Full log overlay (Ctrl+P), capacity 100 |
| PR6 | Help overlay (F1, ?) |
| PR7 | Rune bonuses in status corner |
| PR8 | `{predator}`/`{prey}` sentence capitalization |
| PR9 | Chase memory frustration + momentum + give-up |
| PR10 | Neutral explore anti-oscillation shim (partial) |
| PR11 | Good chase pathing through neutrals; no good→good chase steps |

## Spec updates

- `openspec/specs/ui-layout/spec.md` — log overlay, help, wrap, font
- `openspec/specs/floor-runes/spec.md` — status corner rune rows
- `openspec/specs/enhancements-3/spec.md` — good chase pathing, pursuit notes
- `openspec/changes/better-npc-exploration/` — PR10 follow-up scope expanded
- `README.md` — Ctrl+P, F1, help keys

## Deferred / follow-up

- **Performance throttling** — remains in `openspec/changes/todo/spec.md`
- **Better NPC exploration** — BFS reachable goals, explore frustration, retire PR10 shim (`openspec/changes/better-npc-exploration/`)

## Verdict

**fix-deferred-bugfixes: ACCEPTED**