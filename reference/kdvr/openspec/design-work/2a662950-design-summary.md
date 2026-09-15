# Design Summary: NPC Vore Message Logs

**Design doc:** `openspec/design-work/2a662950-design-doc.md`  
**Proposed change id:** `add-npc-vore-message-logs`  
**Date:** 2026-07-02 (revised post review)

---

## What was produced

A consolidated design document that:

1. **Documents the full NPC vore log system** — on-screen hit/miss (`npc_vore_hit`, `npc_vore_miss`) and off-screen hit/digest — with a single runtime routing table and FOV visibility gate.
2. **Reconciles shipped code** with an intended unified JSON schema (typed objects keyed by `OV` / `CV` / `AV`, matching `digestion_complete`).
3. **Recommends migrating** flat off-screen fields to `offscreen_vore` and `offscreen_digest` objects — with explicit `_DEPRECATED_OFFSCREEN_KEYS` **fail-hard** loader check (not warn-only unknown-trait path).
4. **Closes the content gap** — wolf and shark gain CV/AV off-screen placeholders in **PR1** (PR0 nests OV only).
5. **Includes draft** `proposal.md` and `tasks.md` for `openspec/changes/add-npc-vore-message-logs/`.
6. **Defines a 3-PR implementation plan** with explicit test migrations, parser `field_name` fix in PR0, and PR2 design/archive reconciliation.

---

## Key decisions (headline)

| Decision | Outcome |
|----------|---------|
| Off-screen JSON shape | **Migrate** to `offscreen_vore` / `offscreen_digest` objects |
| Deprecated flat keys | **Fail at load** via `_DEPRECATED_OFFSCREEN_KEYS` before `_scan_unknown_traits()` |
| Missing type keys (mods) | Runtime silent; K7 enforced on stock wolf/shark via `test_load_default_entities_json` (PR1) |
| On-screen miss messages | **In scope** (`npc_vore_miss`); off-screen misses stay silent |
| Fallbacks | Entity-first on-screen → global pools; **no** off-screen fallback |
| Player modals | **Independent** from NPC log lines |
| PR1 scope | **Content-only** — no `vore.py` / `digestion.py` changes |

---

## Current vs target

| Already working | Needs work |
|-----------------|------------|
| `pick_visible_npc_vore_message()` + entity `npc_vore_hit`/`npc_vore_miss` | Flat → object off-screen migration (PR0) |
| Off-screen OV hit/digest for wolf/shark | CV/AV off-screen placeholders (PR1) |
| `NarrativeIndex` pickers | Parameterized parser errors; deprecated-key fail-hard |
| FOV-gated logging | Spec/SCHEMA wording + archive supersession (PR2) |

---

## PR plan (ordered)

| PR | Title | Main files |
|----|-------|------------|
| **PR0** | Off-screen schema migration | `entity_loader.py` (parser + deprecated keys), `entity_registry.py`, `narrative_index.py`, `entities.json` (OV nest only), `SCHEMA.md`, off-screen data tests |
| **PR1** | CV/AV content (no runtime) | `entities.json` (wolf/shark), rewrite silence tests, `test_load_default_entities_json` K7 checks |
| **PR2** | Specs + design artifact + archive | Live specs, `design.md` in change folder, archive supersession note, remove `pick_npc_vore_message()` |

---

## Open questions (resolved / deferred)

| Item | Status |
|------|--------|
| Q1 load-time validation for missing off-screen types | **Deferred** to follow-up; stock data enforced by test in PR1 |
| Q2 parser rename | Optional PR2; `field_name` parameter required PR0 |
| Q3 global off-screen pools | Out of scope |

---

## Next step

Design revised per review (`2a662950-design-review.md`). On approval, create `openspec/changes/add-npc-vore-message-logs/` and begin **PR0** only.