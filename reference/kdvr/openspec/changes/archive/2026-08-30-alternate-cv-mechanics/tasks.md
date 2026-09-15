# Tasks: alternate-cv-mechanics

**Active PR:** PR4 complete — archived  
**Rule:** One PR at a time; do not implement until the user explicitly authorizes that PR.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` written
- [x] `AGENTS.md` **Active change** pointer → `alternate-cv-mechanics`
- [x] Resolved decisions recorded (depth_scaling knobs; stack daze; snapshot at New Game; No/Yes label; test matrix clarified)
- [x] User authorizes PR1 coding

---

## PR1 — Dazed foundation

- [x] `Dazed(remaining)` component (NPC-only apply)
- [x] `apply_daze` (stack add; FOV “appears dazed” only on first apply)
- [x] AI: skip turn, decrement, clear at 0 + FOV “no longer dazed”
- [x] Render: blue tile background when dazed
- [x] `messages.py` helpers
- [x] Save encode/decode
- [x] Tests (pinned): apply/stack, AI countdown, expire message, save round-trip, ignore Player
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off

---

## PR2 — Data + Options + run snapshot

- [x] `cv_daze_min_turns` / `cv_daze_max_turns` on each difficulty in `depth_scaling.json` (all 5/5)
- [x] Loader + `DifficultyProfile`; omit → default 5/5; validate min≤max, ≥0
- [x] `roll_cv_daze_turns` helper
- [x] Settings `alternate_cv_mechanics` (default False; missing → False)
- [x] Options row **Alternate CV Mechanics** No/Yes
- [x] `GameEngine` + New Game / arena snapshot; save restore (missing → False)
- [x] Tests: settings default, options format/toggle, loader defaults, snapshot persist
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off

---

## PR3 — Wire Alternate CV rules

- [x] `try_struggle`: On + CV → 0 damage; escape chance unchanged
- [x] Player CV escape → daze (not on predator defeat-clear)
- [x] `complete_npc_digestion`: On + CV → daze; keep same-phase skip
- [x] On + OV/AV: no zero-damage, no daze from escape/digest
- [x] Off: full regression vs current CV
- [x] Tests per design matrix
- [x] `testing-checklist-pr3.md`
- [x] Manual playtest sign-off

---

## PR4 — Specs, docs, acceptance

- [x] Update live `vore` / `digestion` specs (and settings notes as needed)
- [x] `data/SCHEMA.md` (+ README Options mention if appropriate)
- [x] `testing-checklists.md` + `acceptance-report.md`
- [x] Archive; clear `AGENTS.md` pointer
- [x] Full suite only if designer requests (otherwise targeted only) — **skipped**
- [x] Final sign-off
