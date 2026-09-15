# Manual testing checklist — PR2 (message catalog)

**Change:** `engineering-maintainability`  
**PR:** 2 — Message catalog policy + remaining log-string migration

## How to run

```text
python -m src.main
```

## Base smoke (required every PR)

- [ ] Game launches (main menu appears; no traceback on start)
- [ ] New Game starts a run (map, log, player visible)
- [ ] Play until game over is reachable (e.g. digestion defeat)
- [ ] No crash during the above

## PR2-specific

Gameplay wording should be unchanged. Confirm common log lines still look normal:

- [ ] Welcome / new game log looks normal
- [ ] Bump-fight: hit / miss / defeated lines look normal
- [ ] Pickup or quaff something if easy — log tone unchanged
- [ ] Optional: load autosave (sanitize/difficulty notices only if relevant content)

## Automated (already run)

- `python -m pytest tests/test_message_catalog_pr2.py tests/test_save_sanitize.py tests/test_save_snapshot.py tests/test_text_ux_pr1.py tests/test_message_log_categories.py -v` → **26 passed**

## Sign-off

Designer: smoke OK → authorize PR3 (save hardening).
