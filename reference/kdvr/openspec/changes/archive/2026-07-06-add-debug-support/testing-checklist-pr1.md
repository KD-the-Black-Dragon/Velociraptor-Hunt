# Manual checklist — PR1 (session log core)

PR1 creates `{user_data}/logs/` and session files only — **no milestones, no crash handler, no validation gate**.

**Note (post-archive):** Logs live under `{user_data}/logs/` via `src/user_data.py` (not project root).

Run game: `python -m src.main`

Automated: `pytest tests/test_session_log.py -q`

## Session log infrastructure

- [ ] Launch game → `{user_data}/logs/` directory created
- [ ] New session file `{user_data}/logs/session_YYYY-MM-DD_HH-MM-SS.log` appears on launch
- [ ] Quit normally → session file exists (may be empty or minimal this PR)
- [ ] Game plays normally (no regressions)

## Not applicable this PR

- [ ] Milestone lines (Started new game, Seed, etc.) — deferred to PR3
- [ ] Friendly entities.json errors — deferred to PR2
- [ ] `crash.log` — deferred to PR4