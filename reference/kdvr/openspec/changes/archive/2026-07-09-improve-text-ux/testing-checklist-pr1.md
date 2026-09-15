# Manual testing checklist — PR1 (placeholders, SCHEMA, new-game layout)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_text_ux_pr1.py tests/test_narrative_capitalization.py -n 6 -q`

## Automated (agent)

- [x] PR1 unit tests + narrative capitalization — passed

## `{predator}` in vore modals

Stock text may not use `{predator}`; verify with a temp mod or by editing a local copy if needed:

- [ ] With a mod/entity whose vore `attempt`/`success` lines use `{predator}`, get engulfed → modal shows the predator name (not the literal `{predator}`)
- [ ] Typo like `{predtaor}` appears literally (no crash)

## New-game overwrite layout

- [ ] Have a save → **New Game** → warning sits **below the title logo** (not overlapping)
- [ ] Shrink window toward minimum → full prompt still readable (wraps, stays on screen)
- [ ] Capital **Y** / **n** / Esc still work; invalid key still shows error under the prompt

## SCHEMA

- [ ] `data/SCHEMA.md` “Inline log color markup” lists categories + aliases (spot-check)

## Regression

- [ ] Load Game mod-mismatch notice still appears in the lower band
- [ ] Digestion / NPC log lines still format `{predator}` / `{prey}` as before

## Out of scope this PR

- Dialog chrome panel (PR2)
- Proportional font (PR3+)
