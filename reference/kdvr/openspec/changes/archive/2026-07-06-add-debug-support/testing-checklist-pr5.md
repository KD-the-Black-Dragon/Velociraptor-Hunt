# Manual checklist — PR5 (acceptance)

Run game: `python -m src.main`

Automated: `pytest tests/ -q`

## Full regression

- [ ] New game → milestones in session log (PR3)
- [ ] Broken `entities.json` → friendly stderr, no window (PR2)
- [ ] Normal quit → `Quit` in session log; crash → no `Quit` (PR4)
- [ ] `{user_data}/logs/` exists; `{user_data}/saves/` unchanged

## Documentation

- [ ] `openspec/specs/debug-support/spec.md` exists and matches shipped behavior
- [ ] `log-interpretation-guide.md` matches shipped `crash.log` and session line formats
- [ ] `README.md` points players to `{user_data}/logs/` and the log guide for bug reports (no modding promises)
- [ ] `acceptance-report.md` in change folder

## Spec scenarios (spot-check)

- [ ] 9 session line formats documented
- [ ] Crash report field list matches `crash.log` sample in design
- [ ] Unknown abilities documented as soft warnings only