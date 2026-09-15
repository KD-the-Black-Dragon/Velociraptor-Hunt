# Testing checklists: add-past-runs

Consolidated manual checklists from PR1–PR5. Run: `python -m src.main`

## PR1 — Run statistics (internal)

- [ ] Game starts normally; combat, runes, struggle unchanged
- [ ] Load Game restores run if save exists

## PR2 — Past runs persistence

- [ ] Game over writes `{user_data}/past_runs.json` with correct fields
- [ ] Quit-to-menu does not append

## PR3 — Game over modal stats

- [ ] Recap shows monsters defeated, runes collected, depth
- [ ] No score / turn-count line

## PR4 — Past Runs menu

- [ ] Past Runs omitted when empty; present after game over
- [ ] Scroll works; Escape returns to menu

## PR5 — Acceptance (full flow)

- [ ] Two-line Past Runs format (playtest feedback applied)
- [ ] All PR1–PR4 regression items still pass