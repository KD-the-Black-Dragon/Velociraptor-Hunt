# Tasks: Enhancements 2 — NPC Identity

Implementation follows PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Identity foundation

- [x] Add `Alignment`, `ProperName`, `ExamineDescription` to `components.py`
- [x] Create `src/systems/naming.py` with `entity_log_name`
- [x] Refactor `messages.py` to parameterized combat templates
- [x] Spawn: wolf `evil` + examine text; one random wolf `ProperName("Fang")`; potion examine text
- [x] Tests: naming resolver, Fang spawn, alignment
- [x] `testing-checklist-pr1.md`

## PR 2: Combat messaging

- [x] Wire `combat.py` to naming resolver for all hit/defeat logs
- [x] Remove generic "monster" strings from gameplay paths
- [x] Tests: wolf/Fang-named combat messages

## PR 3: Faction AI

- [x] Evil: nearest hostile + random equidistant tie-break
- [x] Good: chase evil only; player tile blocked for NPC pathing
- [x] Neutral: flee from visible evil; player tile blocked
- [x] Tests: targeting, flee, good/neutral do not step on player
- [x] Removed Fang test spawn (ProperName remains for future NPCs)
- [x] `testing-checklist-pr3.md`

## PR 4: Player swap

- [x] Swap with good/neutral in `try_action`; skip-turn set
- [x] Tests: swap good/neutral, skip turn, stunned no swap
- [x] `testing-checklist-pr4.md`

## PR 5: Vore integration

- [x] `should_attempt_vore` rejects good and neutral
- [x] Migrate naming to shared module; possessive evasion strings
- [x] Tests: Fang evasion log; good/neutral never vore
- [x] `testing-checklist-pr5.md`

## PR 6: Examine and input

- [x] Examine mode (`x`), cursor, modal, free turn
- [x] Engulfed `x` → *"You can't see anything!"*
- [x] `Ctrl+Q` quit; Escape cancel examine only
- [x] Update acceptance test for quit key
- [x] Tests: examine, engulfed block, quit/cancel
- [x] `testing-checklist-pr6.md`

## PR 7: Spec acceptance

- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Update `README.md` controls (`x`, `Ctrl+Q`, Escape)
- [x] Archive change; full test suite green