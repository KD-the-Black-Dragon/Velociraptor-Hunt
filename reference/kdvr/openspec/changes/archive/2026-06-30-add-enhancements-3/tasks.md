# Tasks: Enhancements 3 — Faction Content and AI

Implementation follows PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Spawn knights and rabbits

- [x] Static spawn: 3 wolves, 2 knights, 3 rabbits (tunable constants)
- [x] Knight cyan `k`, rabbit grey `r`; examine placeholders
- [x] Tests: spawn counts, alignment, glyphs data
- [x] `testing-checklist-pr1.md`

## PR 2: NPC stunned and regen

- [x] Good/neutral stunned at 0 HP; evil defeated unchanged
- [x] Messages: stunned / no longer stunned
- [x] NPC regen: good/neutral every 8 player turns; evil every 12
- [x] Tests: stunned not removed, regen intervals
- [x] `testing-checklist-pr2.md`

## PR 3: AI memory and exploration

- [x] `AIState` component (last known, explore goal)
- [x] Evil priority stack (primary → neutral → explore)
- [x] Good intent: evil → follow player → last known evil/player → explore; ignore neutral/good targets
- [x] Good bump player: no-op; console-only attempt log
- [x] Neutral intents (flee/explore)
- [x] Stunned NPCs skip voluntary movement
- [x] Tests: priority, memory clear, explore re-pick
- [x] `testing-checklist-pr3.md`

## PR 4: NPC alignment swap

- [x] NPC↔NPC swap in `try_action`; no NPC swap onto player
- [x] Skip-turn for swapped NPC
- [x] Tests: good↔good, evil↔evil, cross-alignment attacks
- [x] `testing-checklist-pr4.md`

## PR 5: NPC vore logs and headless engulf

- [x] `vore_npc_content.py` OV/CV/AV miss/hit pools
- [x] Generalize vore eligibility for good/neutral prey
- [x] Log-only resolution; headless engulf on hit
- [x] Tests: miss/hit logs, engulf state, no modal
- [x] `testing-checklist-pr5.md`

## PR 6: Rescue and integration

- [x] Defeating predator frees NPC prey; good knight can rescue
- [x] Supersede Enhancements 2 spec notes where needed
- [x] Regression: player vore modal unchanged
- [x] Tests: rescue path
- [x] `testing-checklist-pr6.md`

## PR 7: Spec acceptance

- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Update `README.md` population note
- [x] Archive change; full test suite green