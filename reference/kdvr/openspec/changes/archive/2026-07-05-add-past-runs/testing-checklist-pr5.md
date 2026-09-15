# Manual checklist — PR5 (Acceptance)

Run: `python -m src.main`

Final sign-off for **add-past-runs** change.

## End-to-end

- [ ] New Game → play → get digested → recap shows name, fate, monsters, runes, depth
- [ ] Enter → main menu; Load Game absent; **Past Runs** present
- [ ] Past Runs shows your run in two-line format with blank lines as designed
- [ ] Escape → menu; New Game still works

## Gating

- [ ] Delete or rename `{user_data}/past_runs.json` → restart → Past Runs absent from menu
- [ ] Complete another run → Past Runs reappears

## No false records

- [ ] Start run → Ctrl+Q → Y → Past Runs unchanged (no new entry for quit)

## Regression

- [ ] Load Game when save exists
- [ ] Options / Exit
- [ ] Autosave + game over still wipes save slot

Automated gate + full suite: see `acceptance-report.md`.