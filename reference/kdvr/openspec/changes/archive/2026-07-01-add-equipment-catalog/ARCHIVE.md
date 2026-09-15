# Archived: add-equipment-catalog

**Status:** Completed and accepted  
**Archived:** 2026-07-01  
**Sign-off:** User playtest across PRs 1–5

## Summary

Expanded stock item JSON into depth-escalating catalogs per `openspec/specs/equipment-catalog/spec.md`:

- **12 weapons**, **9 armors**, **5 wands**, **3 potions**
- **Overlap + rotation** via `spawn_min_depth` / `spawn_max_depth`
- **Rarity:** weight 1 equipment; potions 3/2/1; **5** weighted placements per floor
- **Unarmed:** 1–2 dmg, 1.5 acc
- **Starter:** dagger `a` wielded, robes `b` worn

## Verification

- **Automated:** `python -m pytest tests/ -v` — 455 passed (2026-07-01)
- **Manual:** `testing-checklists.md` in this folder

## Spec merge

- Live spec: `openspec/specs/equipment-catalog/spec.md`
- Updated: `inventory-items`, `README.md`, `data/SCHEMA.md`

## Artifacts

| File | Purpose |
|------|---------|
| `proposal.md`, `design.md`, `tasks.md` | Change planning |
| `testing-checklist-pr*.md` | Per-PR playtest |
| `testing-checklists.md` | Combined checklist |
| `acceptance-report.md` | Evidence |
| `ARCHIVE.md` | This file |