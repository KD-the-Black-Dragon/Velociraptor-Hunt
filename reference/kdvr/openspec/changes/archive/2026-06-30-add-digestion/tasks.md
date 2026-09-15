# Tasks: Digestion

Implementation follows PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Foundation — mercy, predator holding, data model

- [x] `DigestionStrikes` component; `DigestionStats` on wolf (`damage_per_tick=3`)
- [x] `Predator.narrative_type` set at engulf (player + NPC paths)
- [x] NPC `VoreMercy` on `release_npc_engulfed`; combat/vore honor mercy for NPC defenders
- [x] Predator attack-only while holding (no move, no new vore)
- [x] Tests: mercy, attack-only, narrative type persisted
- [x] `testing-checklist-pr1.md`

## PR 2: NPC digestion

- [x] Digestion tick at engulfed prey AI slot (HP then strikes rule)
- [x] Regen blocked when `strikes >= 1`; reset strikes on freedom
- [x] Good 10% plea pool (LOS); neutral silent on tick
- [x] OV/CV/AV completion pools on NPC digest
- [x] Prey removed; predator cleared; predator acts next player turn
- [x] Tests: strike cadence, digest removal, messages, regen gate
- [x] `testing-checklist-pr2.md`

## PR 3: Player digestion and game over

- [x] Digestion tick on player turn while engulfed (after struggle)
- [x] Third strike → digestion modal (OV/CV/AV placeholders)
- [x] Game over screen (name/score stubs, digested-by line)
- [x] Enter dismisses → exit game
- [x] Tests: player strike cadence, modal, game over
- [x] `testing-checklist-pr3.md`

## PR 4: Spec and acceptance

- [x] `openspec/specs/digestion/spec.md`
- [x] Update `vore`, `enhancements-3`, `core-roguelike` spec notes
- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Update `README.md`
- [x] Archive change; full test suite green