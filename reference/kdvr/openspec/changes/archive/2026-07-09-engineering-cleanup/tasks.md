# Tasks: engineering-cleanup

**Active PR:** PR3 complete — archived  
**Rule:** One PR at a time; authorize coding after design review.

---

## PR0 — OpenSpec + AGENTS.md

- [x] `proposal.md`, `design.md`, `tasks.md`
- [x] AGENTS.md: mods shipped; save forward-compat policy wording
- [x] AGENTS active change pointer
- [x] Designer reviews design (save policy + flake plan)
- [x] User authorizes PR1 coding

---

## PR1 — Save soft-drop + spawn weight 0 deprecate

- [x] Spec notes + AGENTS: save-break discipline; prefer defaults / soft-drop
- [x] `spawn.weight` / `spawn_weight` allow **0** (never spawn; keep definition)
- [x] Sanitize after load: unknown inventory/floor items + unknown SpeciesId NPCs
- [x] Caution log notice when anything stripped
- [x] Tests: weight 0 loads; unknown item/entity dropped
- [ ] Version-range migration hook (optional follow-up — not required for additive work)
- [x] Manual playtest sign-off (designer 2026-07-09)

---

## PR2 — Flaky tests (per designer)

- [x] **Skip** perf p95 budget test (keep profiler tool for manual use)
- [x] Summon1: Summon1 wolf + knight target + room; player FOV silent
- [x] Vore modal: ensure_wolf + isolate; player HP 0
- [x] RangeN: isolate to wolf/knight/rabbit only; carved-arena preference test
- [x] Full suite `-n 6` green
- [x] Bonus harden: frustration DEBUG snarl tests (no distant-throttle flake)

---

## PR3 — Optional + acceptance

- [x] tcod FutureWarning migration freebie: tests use `console.rgba` not deprecated `console.tiles`
- [x] Full suite green; acceptance report; archive; clear AGENTS

---

## Out of scope

- [ ] ~~Door spite gameplay~~ (stays in todo)
- [ ] ~~New features~~
