# Tasks: match-hud-ux

**Do not implement any PR until the designer authorizes that PR by name.**

---

## Setup (design)

- [x] Create `proposal.md`, `design.md`, `tasks.md`
- [x] Designer accept design (authorized batch PR1–PR3)
- [x] Authorize PR1–PR3 (designer: implement all three)

---

## PR1 — Ally bump no-op

**Auth:** authorized 2026-08-04 (batch with PR2–PR3).  
**Design ref:** `design.md` § Ally bump no-op.

### Checklist

- [x] `messages.py` helper `ally_standing_there(name)`
- [x] `_player_bump`: ally → no-op, no AUT, named message (incl. before downed strike path)
- [x] Targeted tests
- [x] Spec: ally bump requirement

---

## PR2 — Status right of map + bottom action log

**Auth:** authorized 2026-08-04.  
**Design ref:** `design.md` § Target layout, content ownership.

### Checklist

- [x] Split helpers: `match_status_lines`, `match_log_lines`, fullscreen helpers
- [x] `match_hud_bands` geometry (status right of map; log bottom)
- [x] `present_match_frame`: regional status + log (proportional)
- [x] CP437 fallback: same logical regions
- [x] Spec: match HUD layout
- [x] Targeted tests (bands + content split)

---

## PR3 — Reaction modal low-right panel

**Auth:** authorized 2026-08-04.  
**Design ref:** `design.md` § Reaction modal behavior.

### Checklist

- [x] `match_reaction_modal_lines` separated from log/status
- [x] Low-right reaction band when active; log shrinks horizontally
- [x] Distinct panel styling (border / bg) so it reads as modal
- [x] CP437 low-right reaction block
- [x] Spec: reaction panel placement
- [x] Targeted tests
- [x] Manual checklist file + post in chat
- [x] Designer manual sign-off (verified in playtest with grapple-swallow-modals)

---

## Deferred

- Full KDVR PLAY sidebar parity for match NPC lists
- Meter art (ASCII meters remain OK)
- Pixel-perfect reaction coordinates after playtest iteration
