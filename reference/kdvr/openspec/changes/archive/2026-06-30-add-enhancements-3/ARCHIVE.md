# Archived: add-enhancements-3

**Status:** Completed and accepted  
**Archived:** 2026-06-30  
**Sign-off:** User confirmed working in playtest (PRs 1–7)

## Summary

Delivered faction NPC content and AI revamp per `openspec/specs/enhancements-3/spec.md` across seven PRs: spawn, stunned/regen, AI memory/exploration, NPC swap, NPC vore, rescue, and spec acceptance.

**Notable decisions:**

- Static test population: **6 wolves**, **5 knights**, **6 rabbits** (17 NPCs)
- Good/neutral **stunned** at 0 HP; evil **defeated** at 0 HP
- NPC combat/vore/regen messages **visibility-gated** to player FOV
- NPC vore is **log-only** with headless engulf; player vore modal unchanged
- Predator holding prey renders with **dark red tile background**; engulfed prey glyph hidden
- Engulfed prey **invisible** to all AI targeting

## Verification

- **Automated:** `python -m pytest tests/ -v` — 190 passed (2026-06-30)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** ENHANCEMENTS 3: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/enhancements-3/spec.md`
- Enhancements 2 spec: supersession note added
- README updated with population and faction behavior

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (7-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Consolidated manual playtest checklist |
| `testing-checklist-pr*.md` | Per-PR manual checklists (historical) |
| `acceptance-report.md` | Acceptance evidence |
| `ARCHIVE.md` | This file |

## Deferred (future work)

- Digestion damage and removal of good/neutral prey
- Procedural dungeon population / spawn tables
- Vore content preference UI