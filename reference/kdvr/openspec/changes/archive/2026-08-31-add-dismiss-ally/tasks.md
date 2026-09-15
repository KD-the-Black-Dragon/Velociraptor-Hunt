# Tasks: add-dismiss-ally

**Active PR:** *(none — archived)*  
**Rule:** One PR at a time; manual playtest between PRs. Do not code until the user authorizes the named PR.

---

## PR1 — Dismiss targeting + despawn

- [x] Shift+D enters dismiss targeting (Examine-like cursor; Esc cancels)
- [x] Enter on good free ally → remove entity; log `{name} exits the dungeon.`
- [x] Enter on invalid → stay in mode; log `Invalid target. (Allied NPCs only)`
- [x] No turn consumed (open / cancel / invalid / success)
- [x] No `fire_entity_defeated` / XP / defeat stats
- [x] Messages via `src/messages.py`
- [x] Blocked while other gameplay modals active (same class as Examine)
- [x] Automated tests (valid dismiss, invalid target, no turn, not defeat)
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off

---

## PR2 — Discovery + specs + acceptance

- [x] Help overlay line for Shift+D
- [x] Tutorial Actions line for dismiss
- [x] Update live `openspec/specs/command-allies/spec.md` (Dismiss requirement)
- [x] `testing-checklist-pr2.md` / acceptance report
- [ ] Full suite per AGENTS **Full test suite runs** (after final sign-off / release anticipation)
- [x] Archive to `openspec/changes/archive/2026-08-31-add-dismiss-ally/`; clear AGENTS pointer
- [ ] Manual playtest sign-off

---

## Out of scope

- [ ] ~~Dismiss all / multi-target~~
- [ ] ~~Neutral dismiss~~
- [ ] ~~Walk-off-map AI~~
