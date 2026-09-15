# Tasks: ranged-npc-overhaul

**Active PR:** PR4 complete — archived  
**Rule:** One PR at a time; do not implement until the user explicitly authorizes that PR.  
**Note:** Designer authorized PR2+PR3 together; combined playtest signed off before PR4.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` written
- [x] `AGENTS.md` **Active change** pointer → `ranged-npc-overhaul`
- [x] Resolved decisions recorded (difficulty knobs; stock 2/2 and nightmare evil 3; silent reload; vore-commit blocks shoot; NoChase clarified; good ally top-up; rejected fairness extras)
- [x] User authorizes PR1 coding

---

## PR1 — Data: ally damage + difficulty shot knobs

- [x] `ram_crossbow` ranged 7–10 → **4–5**; `sheep_cleric` 9–12 → **5–6** (`ceil` half)
- [x] `good_ranged_shots` / `evil_ranged_shots` on each difficulty in `depth_scaling.json` (2/2; nightmare evil **3**)
- [x] Loader + `DifficultyProfile`; omit → 2/2; validate ≥ 1
- [x] `SCHEMA.md` rows
- [x] Tests: stock values present; omit defaults; invalid 0 rejected
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off (deferred into combined PR3 playtest per designer)

---

## PR2 — Shots resource: magazine, spend, reload, save

- [x] `RangedMagazine` (or equivalent) on RangeN/SmiteN NPCs at spawn/summon
- [x] Max from run difficulty × alignment; current starts at max
- [x] Path/Smite engagement requires ≥1 shot; attempt spends 1
- [x] Reload helper: +1 capped; silent; consumes turn
- [x] Save encode/decode; missing → full magazine
- [x] Tests: cannot shoot at 0; spend; reload cap; save round-trip; RangedVore does not spend
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off (combined with PR3)

---

## PR3 — AI policy: reload priority, good top-up, evil hunger

- [x] At 0 shots: prefer reload; melee/vore still outrank
- [x] At 1 shot: reload only when idle (no sighted target / not chasing); never top up to max while engaging
- [x] Good RangeN/SmiteN: prefer reload to max when no enemy in sight
- [x] Evil: on vore-commit, attempt or step toward — no Path/Smite that turn
- [x] Preserve distance-1 no-shoot (centaur melee vulnerability)
- [x] NoChase behavior unchanged (drop pursuit only after LOS loss)
- [x] Tests: priority fixtures for 0/1/idle/good-top-up/vore-commit-blocks-shot
- [x] `testing-checklist-pr3.md`
- [x] Manual playtest sign-off

---

## PR4 — Specs, docs, acceptance

- [x] Update live `npc-abilities` / `balance` specs (and `ranged-targeting` if needed)
- [x] README / SCHEMA polish if anything left (SCHEMA done in PR1; no README change required)
- [x] `testing-checklists.md` + `acceptance-report.md`
- [x] Archive; clear `AGENTS.md` pointer
- [x] Full suite only if designer requests (otherwise targeted only) — **deferred**
- [x] Final sign-off
