# Tasks: engulfed-flavor-text

**Active PR:** PR3 complete — archived  
**Rule:** One PR at a time; do not implement until the user explicitly authorizes that PR.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` written
- [x] `AGENTS.md` **Active change** pointer → `engulfed-flavor-text`
- [x] Resolved decisions recorded
- [x] User authorizes PR1 coding

---

## PR1 — Data pipeline

- [x] `engulfed_flavor` on `EntityDefinition` + `_ENTITY_TRAITS`
- [x] Parse allowing omit / empty arrays (no-op pools); reject bad shapes
- [x] `NarrativeIndex` lines / pick helpers
- [x] `data/SCHEMA.md` documentation
- [x] Loader tests (pinned JSON snippets)
- [x] `testing-checklist-pr1.md`
- [x] Manual / doc sign-off

---

## PR2 — Runtime emit

- [x] `Predator.engulfed_flavor_phases` + save codec (default 0)
- [x] `maybe_emit_engulfed_flavor` at end of `run_world_turn`
- [x] Every 3rd phase; SPEECH category; placeholders; no blank logs
- [x] Tests: cadence, type gate, empty silent, reset on re-engulf
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off

---

## PR3 — Specs and archive

- [x] Update live `vore` spec (+ SCHEMA already in PR1)
- [x] `testing-checklists.md` + `acceptance-report.md`
- [x] Archive; clear `AGENTS.md` pointer
- [x] Full suite only if designer requests — **skipped**
- [x] Final sign-off
