# Archived: add-dungeon-enhancement

**Status:** Completed and accepted  
**Archived:** 2026-06-30  
**Sign-off:** User confirmed PRs 1–4; PR 5 spec acceptance

## Summary

Delivered dungeon enhancement per `openspec/specs/dungeon/spec.md` across five PRs: tiles/mobility, map generation, floor depth/descent, aquatic combat/sharks, and spec acceptance.

**Notable decisions:**

- **Deep water** (`~`) transparent to FOV; impassable to ground; shaped lakes/rivers with connectivity validation
- **Mobility** component: `GROUND` / `FLY` / `AQUATIC`; player always ground in v1
- **Aquatic shore combat** — bump melee from water to adjacent land without entering land
- **Three `>` downstairs** per floor; **`Shift+.` (`>`)** descends; **`.`** remains wait
- **Floor depth** on HUD; good knights in LOS follow on descent
- **Sharks** — 2 aquatic evil predators when floor has water; land NPC counts unchanged
- **Vore escape** respects prey mobility for water tiles
- **F3** debug toggles water-heavy map generation for playtesting

## Verification

- **Automated:** `python -m pytest tests/ -q` — 318 passed (2026-06-30)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** DUNGEON ENHANCEMENT: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/dungeon/spec.md`
- Updated: `core-roguelike`, `vore`, `enhancements-3`
- README updated with dungeon controls and status

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