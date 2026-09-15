# Acceptance Report: add-main-menu

**Date:** 2026-06-30  
**Scope:** `openspec/specs/main-menu/spec.md` (menu shell, name entry, options, quit flow, recap → menu)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 271 passed, 0 failed (2026-06-30)

| Area | Tests | Result |
|------|-------|--------|
| Main menu shell (PR 1) | `test_main_menu.py` | PASS |
| Name entry + HUD/recap (PR 2) | `test_name_entry.py` | PASS |
| Options + settings (PR 3) | `test_options_menu.py`, `test_settings_store.py`, `test_vore_constants.py` | PASS |
| Flow integration (PR 4) | `test_flow_pr4.py` | PASS |
| Core acceptance | `test_acceptance.py` | PASS |
| Digestion / vore regression | `test_digestion.py`, `test_vore_*.py`, `test_enhancements_*.py` | PASS |
| Full suite | `tests/` | PASS |

## Manual verification

- [x] User playtest sign-off PRs 1–4
- [x] Consolidated checklist: `testing-checklists.md`

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Boot to main menu | `test_main_menu.py`, manual PR 1 |
| Menu navigation, Exit, Ctrl+Q no-op on menu | `test_main_menu.py` |
| Name entry, Anonymous default, HUD name | `test_name_entry.py` |
| Options toggles, at-least-one rule, persistence | `test_options_menu.py`, `test_settings_store.py` |
| Vore prefs initiation filter | `test_vore_constants.py`, `test_options_menu.py` |
| Quit confirmation Y/n | `test_flow_pr4.py` |
| Recap → menu, no score | `test_name_entry.py`, `test_flow_pr4.py` |
| Stub screens Coming soon | `test_flow_pr4.py` |
| Ctrl+Q no-op during modals | `test_flow_pr4.py` |

## Spec updates

- `openspec/specs/main-menu/spec.md` — new live spec (created PR 1)
- `openspec/specs/vore/spec.md` — initiation prefs; Ctrl+Q no-op in modal; OV not forced on
- `openspec/specs/digestion/spec.md` — recap → menu; display name; no score
- `openspec/specs/core-roguelike/spec.md` — menu entry; HUD name; quit confirmation
- `README.md` — main menu controls and status

## Verdict

**MAIN MENU: ACCEPTED**