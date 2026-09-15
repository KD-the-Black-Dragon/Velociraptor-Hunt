# Archived: add-digestion

**Status:** Completed and accepted  
**Archived:** 2026-06-30  
**Sign-off:** User confirmed PRs 1–3 and playtest fixes

## Summary

Delivered digestion per `openspec/specs/digestion/spec.md` across four PRs: foundation (mercy, holding, data model), NPC digestion ticks, player digestion + game over, and spec acceptance.

**Notable decisions:**

- Wolf digestion damage **3** per tick; three strikes at 0 HP → digest
- Predator **attack-only** while holding (not fully frozen)
- NPC **VoreMercy** on rescue; combat/vore honor mercy for all prey
- Player digestion on consumed turn (after struggle); modal then game over
- Engulfed player **immune** to external combat; **no regen** while engulfed
- Strike increments log *"You are being digested!!"*
- CP437-safe log text (`src/text.py`)

## Verification

- **Automated:** `python -m pytest tests/ -q` — 218 passed (2026-06-30)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** DIGESTION: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/digestion/spec.md`
- Updated: `vore`, `enhancements-3`, `core-roguelike`
- README updated with digestion behavior

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (4-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Consolidated manual checklist |
| `testing-checklist-pr*.md` | Per-PR checklists (historical) |
| `acceptance-report.md` | Acceptance evidence |
| `ARCHIVE.md` | This file |