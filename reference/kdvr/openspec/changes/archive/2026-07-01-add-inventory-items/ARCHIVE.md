# Archived: add-inventory-items

**Status:** Completed and accepted  
**Archived:** 2026-07-01  
**Sign-off:** User playtest across PRs 1–5; PR 6 spec acceptance

## Summary

Delivered data-driven inventory and items per `openspec/specs/inventory-items/spec.md` across six PRs: registries/spawn/pickup, modals/drop/inspect, wield/wear/durability, quaff, wand evoke, and spec acceptance.

**Notable decisions:**

- **Category commands** — `,` `i` `d` `w` `W` `q` `v`; letter keys only inside modals
- **Turn rules** — pickup, drop, inspect free; wield, wear, quaff, evoke consume turn on success
- **Durability** — weapons per hit; armor per digestion point mitigated; red destroy logs
- **Wand evoke** — evil-only valid targets; cursor-only target step; exact error strings
- **Engulfed** — pack blocked; worn armor digestion mitigation passive
- **Render** — player and NPC glyphs over floor items

## Verification

- **Automated:** `python -m pytest tests/ -v`
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** INVENTORY ITEMS: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/inventory-items/spec.md`
- Updated: `core-roguelike`, `enhancements-1`, `enhancements-2`, `dungeon`, `vore`, `digestion`, `npc-data`
- README + `data/SCHEMA.md` updated

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (6-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Consolidated manual checklist |
| `testing-checklist-pr*.md` | Per-PR checklists (historical) |
| `acceptance-report.md` | Acceptance evidence |
| `ARCHIVE.md` | This file |