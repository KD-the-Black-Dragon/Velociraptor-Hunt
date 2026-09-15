# Manual checklist — PR3 (activation modal — no game over yet)

Run game: `python -m src.main`

- [ ] Stepping on macguffin shows victory prompt with object name
- [ ] Capital Y is accepted but does **not** open game over yet (PR4 wires this)
- [ ] Lowercase n declines (uppercase N rejected)
- [ ] Invalid keys show enforcement message
- [ ] Decline removes tile; movement resumes; turn consumed on n
- [ ] Ctrl+Q blocked while prompt is open
- [ ] Save/load after decline preserves discovery state

Automated: `pytest tests/test_macguffins_pr3.py -q`