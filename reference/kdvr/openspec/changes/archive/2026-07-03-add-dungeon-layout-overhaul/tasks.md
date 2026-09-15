# Tasks: add-dungeon-layout-overhaul

- [x] PR0 — Sanity validation & regeneration (land count, spawn-candidate 3×, stair spread BFS ≥ 20, rune-site feasibility, spread-aware stair placement, debug discard logging, giant-room fallback)
- [x] PR1 — Layout archetypes (modular boxy / organic / hybrid; debug 100% force modes; 40/40/20 split; organic 4–6 caverns + chokes + optional lakes)
- [x] PR2 — Doors (tile types, procedural placement ~50%, player open/close, FOV/movement, render `+`/`-`, NPC blocked)
- [x] PR3 — Floor init loop, rune placement fix, spec update, archive acceptance (fold todo rune-cluster bug)
- [x] PR4 — Background floor prefetch (`floor_prefetch.py`; menu + post-floor triggers; sync fallback on miss)

Manual checklists: `testing-checklist-pr0.md` through `testing-checklist-pr4.md`.

- [x] Acceptance — `testing-checklists.md`, `acceptance-report.md`, archive to `openspec/changes/archive/2026-07-03-add-dungeon-layout-overhaul/`