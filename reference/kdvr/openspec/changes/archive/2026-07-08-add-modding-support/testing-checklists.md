# Testing checklists — add-modding-support

Aggregate pointer for all PRs. Prefer the per-PR files for playtest sessions.

| PR | Focus | Checklist |
|----|--------|-----------|
| PR1 | Discovery / `mod.state` | `testing-checklist-pr1.md` |
| PR2 | Entities layering + bad-mod popup | `testing-checklist-pr2.md` |
| PR3 | Options → Mods UI + save wipe | `testing-checklist-pr3.md` |
| PR4 | Id catalogs (items, runes, macguffins, names) | `testing-checklist-pr4.md` |
| PR5 | Whole-file domains | `testing-checklist-pr5.md` |
| PR6 | Save fingerprint, crash mods, docs | `testing-checklist-pr6.md` |
| PR7 | Acceptance / full suite | This file + `acceptance-report.md` |

## Final acceptance (PR7)

**Run:** `python -m src.main`  
**Full suite:** `python -m pytest tests/ -v -n auto`

### End-to-end smoke

- [ ] Create mod folder with custom entity + optional weapon; New Game sees content
- [ ] Override stock `wolf` or `dagger`; confirm session uses override
- [ ] Options → Mods: toggle, reorder; Escape reloads data
- [ ] With save: Mods entry requires capital **Y**; cancels with **n**
- [ ] Load Game with mismatched mods refused; save kept
- [ ] Bad mod JSON → dialog names mod + file; game continues
- [ ] F6 crash lists enabled mods in `crash.log`
- [ ] No mods → stock game

### Automated

- [x] Full `pytest tests/ -v -n auto` (see acceptance-report.md)
