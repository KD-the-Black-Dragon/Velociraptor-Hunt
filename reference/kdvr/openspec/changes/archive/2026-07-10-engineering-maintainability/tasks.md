# Tasks: engineering-maintainability

**Active PR:** PR12 complete — **archived** 2026-07-10  
**Rules:** One PR at a time. Gameplay freeze. **Mandatory smoke + designer sign-off before next PR.** Prefer extra splits over large diffs.

---

## PR0 — OpenSpec + pointer

- [x] `proposal.md`, `design.md`, `tasks.md`
- [x] `AGENTS.md` current change pointer
- [x] `todo/spec.md` five items pulled into this change
- [x] Designer answered Q1–Q4; design locked
- [x] Designer authorizes **PR1** coding

---

## PR1 — Test helpers (spawn-at-depth / difficulty)

- [x] Helpers for species @ depth under difficulty (+ fixture-friendly path)
- [x] Docstring vs `spawn_test_npc` / digest fixtures
- [x] Unit tests (no live balance number pins)
- [x] Targeted pytest green (`test_spawn_depth_helpers` + related spawn/depth: 40 passed)
- [x] **Manual smoke** (base: launch, new game, game-over path) + chat checklist
- [x] Designer sign-off

---

## PR2 — Message catalog discipline

- [x] `openspec/specs/engineering/spec.md` policy
- [x] Migrate **all remaining** player-facing message-log literals into `messages.py`
- [x] Preserve wording; entity narratives stay in JSON
- [x] Targeted tests green (26 related passed)
- [x] **Manual smoke** + chat checklist
- [x] Designer sign-off

---

## PR3 — Save codec / schema hardening

- [x] Field inventory + agent checklist (save-load spec and/or `src/save` docs)
- [x] Additive default tests + compact round-trip
- [x] `migrate_run` identity stub (no version bump)
- [x] Targeted save tests green (46 save-related passed)
- [x] **Manual smoke** (include save/load if practical) + chat checklist
- [x] Designer sign-off

---

## PR4 — Engine extract: floor only

- [x] Extract floor lifecycle only (init / descend / spawn / prefetch glue)
- [x] `from src.engine import GameEngine` still works
- [x] No gameplay logic changes; no deep renames yet
- [x] Targeted tests green (104 related passed)
- [x] **Manual smoke** (+ descend / floor paths) + chat checklist
- [x] Designer sign-off

---

## PR5 — Engine extract: turn only

- [x] Extract turn pipeline only (consume turn, world phase, regen, digestion hooks, haste + rest)
- [x] No gameplay logic changes
- [x] Targeted tests green (178+ related; 1 flaky re-ran PASS)
- [x] **Manual smoke** (+ combat/world phase, rest) + chat checklist
- [x] Designer sign-off

---

## PR6 — Engine extract: input only

- [x] Extract input / modal / gameplay key handlers into `engine_input.py`
- [x] No gameplay logic changes
- [x] Targeted tests green (135 related; 1 patch path fix; re-run 55 PASS)
- [x] **Manual smoke** (+ inventory, examine, pickup, doors as practical) + chat checklist
- [x] Designer sign-off

---

## PR7 — Engine deeper cleanup

- [x] Clearer private names / module layout; update call sites
- [x] Document public `GameEngine` surface; drop proven dead code only
- [x] No behavior / save shape changes
- [x] Targeted + broader engine tests green (98 passed)
- [x] **Manual smoke** (full base + inventory/rest/descend + game over) + chat checklist
- [x] Designer sign-off

---

## PR8 — AI extract: package + explore

- [x] Package/scaffold + move **explore** only
- [x] Re-exports keep existing `src.systems.ai` imports working
- [x] No AI decision changes
- [x] Explore-related tests green (59+ core suite; patch paths updated for package)
- [x] **Manual smoke** (+ monsters move/explore) + chat checklist
- [x] Designer sign-off

---

## PR9 — AI extract: chase + targeting

- [x] Move chase + targeting only (split further if diff too large)
- [x] Re-exports maintained
- [x] No AI decision changes
- [x] Chase / targeting / come-here related tests green (84+ passed)
- [x] **Manual smoke** (+ fight / chase) + chat checklist
- [x] Designer sign-off

---

## PR10 — AI extract: movement + visit + orchestration

- [x] Move movement, visit, `run_monster_turns` leftovers
- [x] Re-exports maintained
- [x] No AI decision changes
- [x] Broad AI / vore-ai / abilities tests green (147 passed)
- [x] **Manual smoke** (+ fight, save/load) + chat checklist
- [x] Designer sign-off

---

## PR11 — AI deeper cleanup

- [x] Public API docs + explicit package layout notes in `__init__.py`
- [x] Production imports prefer submodules (`targeting` for rest/ally)
- [x] Dead code: removed unused `_erratic_pursuit_direction`; cleaned movement/visit/pipeline imports
- [x] Fixed missing `coward_should_flee` import on neutral explore path in movement
- [x] No AI decision or throttle/explore **semantic** changes
- [x] Broad AI tests green (162 related passed, `-n 6`)
- [x] **Manual smoke** (fight, explore, ally/come-here if easy, save/load, game over) + chat checklist
- [x] Designer sign-off

---

## PR12 — Acceptance + archive

- [x] Full suite exercised during PR12; remaining failures hardened via targeted stress (designer accepted)
- [x] `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-10-engineering-maintainability/`
- [x] Mark five engineering items completed in `todo/spec.md`
- [x] Clear `AGENTS.md` active change pointer
- [x] **Final sign-off** — designer: archive authorized 2026-07-10

---

## Out of scope

- [ ] ~~Externalize vore narratives from entities.json~~
- [ ] ~~Turn-pipeline performance budget module~~
- [ ] ~~Thrown weapons / abilities / runes / prefixes / deep allies / balance~~
- [ ] ~~Door spite distant approach (still todo gameplay)~~
