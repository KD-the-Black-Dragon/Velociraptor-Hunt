# Tasks: Extra NPC prefixes beyond Elite

**Status:** Complete — archived 2026-07-11.  
**Rule:** One PR at a time.

Full design: `design.md`. Summary: `proposal.md`.

---

## Phase 0 — Design gate

- [x] Designer prefix shortlist (Brute, Berserk, Veteran, Starving, Sniper, Bloated; all else vetoed)
- [x] Filter-then-roll model confirmed
- [x] Designer answers: evil-only; ability grants; supplement Elite; no weak-only; weights in JSON
- [x] `proposal.md`, `design.md`, `tasks.md`
- [x] AGENTS.md **Current change pointer** → `add-extra-npc-prefixes`
- [x] User authorizes PR1

---

## Phase 1 — Implementation

- [x] **PR1** — Prefix infrastructure
  - `requirements` + `grant_abilities` loader/registry
  - `ranged_accuracy` in `stat_bonuses`
  - `eligible_for_entity(definition)` filter in `try_roll_prefix`
  - Ability merge in `apply_prefix_definition`
  - `data/SCHEMA.md` schema section
  - Tests: filter gate (Sniper / `RangeN`), grants (Slow/PreferVore), ranged_accuracy isolation, elite regression

- [x] **PR2** — Stock content
  - Add six prefix rows to `data/npc_prefixes.json` with starting flats/weights
  - Tune `elite` weight alongside new entries (designer/playtest)
  - Optional `prefix_spawn` curve tweak if needed
  - Content fixture tests (pinned minimal JSON, not live balance numbers)

- [x] **PR3** — Live spec merge, acceptance, archive
  - Extend `openspec/specs/balance/spec.md` (requirements, grants, filter-then-roll)
  - `acceptance-report.md`, `testing-checklists.md`
  - Archive → `openspec/changes/archive/YYYY-MM-DD-add-extra-npc-prefixes/`
  - Mark todo item shipped; clear AGENTS pointer