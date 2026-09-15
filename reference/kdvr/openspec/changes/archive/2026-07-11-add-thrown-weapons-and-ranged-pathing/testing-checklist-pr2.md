# Manual checklist — PR2 Path core

PR2 is engine-only — no player-facing Path UI yet. Verify Smite (PR1) still works.

Run: `python -m src.main`

- [ ] Wand evoke still uses **smite** log lines
- [ ] Melee combat unchanged
- [ ] No new keys or inventory behavior

Automated: `python -m pytest tests/test_ranged_path.py -v`