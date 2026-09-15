# Archived: add-main-menu

**Status:** Completed and accepted  
**Archived:** 2026-06-30  
**Sign-off:** User confirmed PRs 1–4; PR 5 spec acceptance

## Summary

Delivered main menu per `openspec/specs/main-menu/spec.md` across five PRs: menu shell, name entry, options persistence, flow integration, and spec acceptance.

**Notable decisions:**

- Boot to **main menu**; **New Game** → name entry (`Anonymous` if blank)
- HUD title shows **player display name** during play
- **Options** toggles Oral/Cock/Anal Vore; at-least-one rule; `{user_data}/settings.json` auto-save
- OV **not** forced always-on; prefs gate **initiation only** (snapshotted at new game)
- **Ctrl+Q** on menu → no-op; in gameplay → quit confirmation (`Y` → menu, `n` → resume)
- **Ctrl+Q** no-op during vore/digestion/recap modals
- Digestion recap → **main menu** (no score line)
- Load Game / High Scores → **Coming soon** stubs

## Verification

- **Automated:** `python -m pytest tests/ -q` — 271 passed (2026-06-30)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** MAIN MENU: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/main-menu/spec.md`
- Updated: `vore`, `digestion`, `core-roguelike`
- README updated with menu controls and status

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (5-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Consolidated manual checklist |
| `testing-checklist-pr*.md` | Per-PR checklists (historical) |
| `acceptance-report.md` | Acceptance evidence |
| `ARCHIVE.md` | This file |