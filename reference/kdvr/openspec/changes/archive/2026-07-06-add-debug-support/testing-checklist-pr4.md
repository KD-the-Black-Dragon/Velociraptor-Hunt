# Manual checklist — PR4 (crash reports)

Automated: `pytest tests/test_crash_report.py tests/test_modal_snapshot.py -q`

**Crash testing is destructive to the current session** — use a throwaway run.

## Force crash (F6)

During **PLAY**, press **F6** to raise a test exception (`ForceCrashError: F6 debug force-crash`). The normal crash path runs: `{user_data}/logs/crash.log`, brief overlay, no spurious `Quit` in the session log.

Tip: open **F1** help first, then **F6**, to verify `help_overlay` appears in the crash log.

## Crash log contents

After F6 (or any unhandled crash). Check:

- [ ] `{user_data}/logs/crash.log` exists and was overwritten
- [ ] Contains: game version, OS, Python version, timestamp, exception, stack trace
- [ ] Contains game state when in PLAY: floor, turn, RNG seed/state, player position, HP, active modal (if any)
- [ ] References current session log filename
- [ ] `Loaded mods: (none)` stub present

## Crash UX

- [ ] Brief in-window message visible before exit (when window was open)
- [ ] Message mentions crash log path (full `{user_data}/logs/crash.log` at runtime)

## Quit milestone on crash

- [ ] Session log from crashed run does **not** end with `Quit`

## Modal snapshot (optional manual)

- [ ] Crash with help overlay (F1) open → crash log reports `help_overlay` (or equivalent label)

## Regression

- [ ] Normal quit still appends `Quit` to session log
- [ ] Validation failure (broken entities.json) still skips `Quit` (PR2)
- [ ] PR3 milestones still appear in session log