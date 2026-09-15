# Tasks: add-come-here

**Active PR:** *(none — change accepted and archived 2026-07-09)*  
**Rule:** One PR at a time; manual playtest between PRs.

---

## PR0 — Design lock

- [x] Midpoint scope locked in `proposal.md` / `design.md` (Come here only)
- [x] Designer locked: cooldown **4**, engulfed fizzle copy + turn, frustration vs blocking evil
- [x] User authorizes PR1 coding

---

## PR1 — Shout plumbing

- [x] Key `1` (main keyboard) → `try_come_here_shout`
- [x] Cooldown **4** turns + hoarse message (no turn on fail)
- [x] Successful shout: turn consume + log + set flags on good in FOV
- [x] Engulfed fizzle message + turn + cooldown, no flags
- [x] Modal block; stunned allowed
- [x] `AIState.come_here` + player/engine last-shout turn; save defaults
- [x] Tests for cooldown / FOV set / engulfed fizzle
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off (cooldown → 4 after PR1)

---

## PR2 — AI behavior

- [x] come-here forces approach-player priority (honest pursuit only)
- [x] Non-blocking evil ignored while coming here
- [x] **Frustration:** blocking evil on path → attack (mirror evil/neutral hallway pattern)
- [x] Adjacency clears come-here immediately
- [x] Lose-track give-up clears come-here
- [x] Engulfed-player rescue still overrides when applicable
- [x] Clear come-here on floor change
- [x] Tests for approach / tag-clear / lose-track / frustration
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off

---

## PR3 — Spec + polish + acceptance

- [x] Help overlay line
- [x] `openspec/specs/command-allies/spec.md`
- [x] Supersession note on deferred Follow/Attack folder
- [x] `testing-checklist-pr3.md`
- [x] Full suite `-n 6`; re-run failures only
- [x] Archive; clear AGENTS pointer
- [x] Manual playtest sign-off (PR1–PR2 + PR3 help)

---

## Out of scope

- [ ] ~~Attack command~~
- [ ] ~~Permanent follow~~
- [ ] ~~Neutral allies~~
