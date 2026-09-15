# Tasks: add-macguffins

One PR at a time. Check off when merged and playtested.

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` in change folder
- [x] `testing-checklist-pr0.md` … `testing-checklist-pr5.md` stubs
- [x] `openspec/WORKFLOW.md` active change pointer updated
- [x] No gameplay code

## PR1 — Macguffin data catalog

- [x] `data/macguffins.json` with stock three (Sword, Shield, Cup) — depths per design table (Sword max_depth 8)
- [x] `src/data/macguffin_loader.py` + `src/data/macguffin_registry.py`
- [x] `data/SCHEMA.md` — `macguffins.json` section
- [x] `tests/test_macguffins_pr1.py` (load, validation, depth eligibility)
- [x] Targeted pytest for PR1

## PR2 — Spawn, movement, save entity codec

- [x] `Macguffin` component in `src/components.py`
- [x] `src/systems/macguffins.py` — `spawn_macguffins()` (empty eligible → `[]`), entity spawn helper
- [x] Engine hook in `_spawn_floor_population_and_runes` after `spawn_floor_rune`
- [x] Player passthrough in `src/systems/movement.py`
- [x] `Macguffin` encode/decode in `src/save/codec.py`
- [x] `MACGUFFINS_PER_FLOOR_MAX = len(registry.macguffins)` + `map_gen.py` feasibility count bump
- [x] `tests/test_macguffins_pr2.py` — include depth-7 fixture: 3 runes + 3 macguffins
- [x] Targeted pytest for PR2
- [x] Manual playtest checklist PR2

## PR3 — Step-on, modal, discovery (no game over yet)

- [x] `src/macguffin_victory_confirm.py` + `MacguffinVictoryConfirmState` (attrs definition)
- [x] `src/macguffin_discovery.py` + `encode/decode` helpers
- [x] `build_run_snapshot` encode + **`apply_run_snapshot` decode** + `macguffin_victory_confirm.reset()` (lifecycle matrix)
- [x] `new_game()` reset both; `descend_floor()` preserve discovery, reset modal
- [x] `try_begin_macguffin_activation()` in `macguffins.py`
- [x] Engine move branch: deferred `_consume_player_turn()` (pseudocode in design.md)
- [x] `handle_event` / render / `modal_blocks_quit` — **CONFIRM stubbed** (`pass`, no game over)
- [x] `tests/test_macguffins_pr3.py` — modal, discovery, turn deferral, snapshot round-trip; **no** ending-string or game-over assertions
- [x] Targeted pytest for PR3
- [x] Manual playtest checklist PR3

## PR4 — Game over, digestion override, formatter

- [x] Wire CONFIRM → `_complete_macguffin_victory()`
- [x] `format_game_over_ending` — article rule (`The ` prefix → `found {detail}!`)
- [x] Extend `GameOverState.open()` with `macguffin_score` kwarg
- [x] Extend `PastRunRecord` + `record_to_dict` / `parse_record` with `macguffin_score`
- [x] Digestion path override + **`macguffin_score` on both victory Y and digestion paths**
- [x] Interim update `openspec/specs/past-runs/spec.md` macguffin display row
- [x] Update `tests/test_game_over_ending.py`
- [x] `tests/test_macguffins_pr4.py` — Y → game over, digestion override, mid-modal load turn count
- [x] Targeted pytest for PR4
- [x] Manual playtest checklist PR4

## PR5 — Spec sync and acceptance

- [x] New `openspec/specs/macguffins/spec.md`
- [x] Update `floor-runes`, `past-runs`, `save-load` specs (incl. ephemeral UI list for `macguffin_victory_confirm`)
- [x] `README.md` — `data/macguffins.json` pointer
- [x] `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-add-macguffins/`
- [x] Full `pytest tests/`
- [x] Final manual playtest checklist