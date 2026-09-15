# Tasks: Add Basic Vore Mechanics

Implementation follows the 8-PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Foundation

- [x] Add `VoreCapable`, `Engulfed`, `DisplayName`, `VoreNarratives`, `Predator` to `components.py`
- [x] Add vore constants, `VORE_ENABLED`, `VoreContentPreferences` (OV forced) to `constants.py`
- [x] Create `src/vore_content.py` — wolf `NARRATIVE_PACKS` (attempt/success phase tuples per OV/CV/AV)
- [x] Add vore message templates to `messages.py`
- [x] Add vore event hooks to `events.py`
- [x] Tag spawned monsters with `VoreCapable`, `DisplayName(name="wolf")`, `VoreNarratives(OV,CV,AV)`; all types on by default
- [x] Create `src/systems/vore.py` with probability helpers, `pick_narrative_type`, `get_narrative_phases`, `debug_weaken_all_monsters`
- [x] Add `GameEngine.rng` seeded in `new_game`
- [x] Wire `F2` debug key (before inventory routing)
- [x] Add `tests/test_vore_constants.py`

## PR 2: Headless AI decisions

- [x] Implement `should_attempt_vore` (includes LOS) and `resolve_vore_hit`
- [x] Sort monsters deterministically in `run_monster_turns`
- [x] Vore decision before chase; pass `rng` from engine
- [x] Add `tests/test_vore_ai.py` (seeded boundary tests)

## PR 3: Modal UI

- [x] Add `VoreModalSegment`, `VoreModalState` (dynamic phase queue) to engine
- [x] Input gating: Enter advances one phase, Escape quits, gameplay keys blocked
- [x] `render_vore_modal` centered box (current phase only; never copies to log)
- [x] AI returns `True` when opening modal; load attempt phases at open
- [x] Manual playtest: multi-phase attempt/success queues; miss logs evasion after last attempt phase

## PR 4: Turn-order resume

- [x] `VoreModalState.reset()` on swallow, miss-complete, `new_game`
- [x] `_advance_vore_modal` single-call miss-resume with chained-modal early return
- [x] Resume index convention: store `i`, resume at `i+1`
- [x] Add `tests/test_vore_turn_order.py`

## PR 5: Engulfed state

- [x] `engulf_player`, `release_engulfed`, `sync_engulfed_position`
- [x] `_fighter_at` co-tile rules (skip Engulfed, prefer Predator)
- [x] Predator freeze in AI; skip vore on engulfed prey
- [x] Add `tests/test_vore_engulfed.py`

## PR 6: Struggle and escape

- [x] `try_struggle`, `apply_struggle_damage` (flat damage); escalating escape (15% + 5% per fail)
- [x] Directional `release_engulfed` with random-adjacent and displacement-teleport fallbacks
- [x] Engine struggle routing → `_run_world_turn`; wait-in-belly passes turn (not struggle); block inventory
- [x] Escape at 0 HP leaves stunned; regen continues while engulfed
- [x] Add `tests/test_vore_struggle.py` (1 HP predator immediate escape via `F2`; directional escape)

## PR 7: Blindness render

- [x] Blind map/entity rendering when engulfed
- [x] HUD `** ENGULFED **` indicator
- [x] Add `tests/test_vore_render.py`

## PR 8: Spec and acceptance

- [x] Finalize `openspec/specs/vore/spec.md` (incl. ad-hoc: struggle messages, 0 HP block, mercy, overlay)
- [x] Update core spec modular boundary / AC8
- [x] Add `test_core_systems_no_vore_import` + vore smoke test
- [x] Update `README.md` controls (`F2`, vore summary)
- [x] Write `testing-checklists.md` and `acceptance-report.md`

## Post-plan ad-hoc (shipped before archive)

- [x] Random struggle log messages (`pick_struggle_message`)
- [x] No struggle at 0 HP while engulfed (tired message)
- [x] Post-escape mercy invincibility (`VoreMercy` tag)
- [x] Engulfed dark-red `#` overlay ring around player