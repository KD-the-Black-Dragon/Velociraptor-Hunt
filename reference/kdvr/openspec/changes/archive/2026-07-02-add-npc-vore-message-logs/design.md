# Design: add-npc-vore-message-logs

**Authoritative design:** `openspec/design-work/2a662950-design-doc.md`  
**Review:** `openspec/design-work/2a662950-design-review.md` (0 open issues — approved)

## Summary

Consolidates all NPC-on-NPC vore **log** surfaces into one typed-object schema (`OV` / `CV` / `AV` keys), matching `digestion_complete` and `npc_vore_hit` / `npc_vore_miss`.

## On-screen NPC vore logs — shipped before this change

`npc_vore_hit`, `npc_vore_miss`, and `pick_visible_npc_vore_message()` landed without a prior change folder. This design documents them as authoritative and does not rework on-screen behavior (entity-first, global pool fallback).

## Key decisions

| # | Decision |
|---|----------|
| K1 | Migrate flat off-screen fields → `offscreen_vore` / `offscreen_digest` objects |
| K2 | Deprecated flat keys **fail at load** via `_DEPRECATED_OFFSCREEN_KEYS` (not warn-only) |
| K3 | On-screen miss messages in scope; off-screen misses silent |
| K4 | On-screen fallback to `vore_npc_content.py` pools when entity data missing |
| K5 | No off-screen fallback to global pools |
| K6 | NPC log lines independent from `vore_narratives` player modals |
| K7 | Wolf/shark must ship off-screen vore + digest for every `vore_narratives` type (PR1) |

## PR plan

| PR | Scope |
|----|-------|
| **PR0** | Schema migration: objects, deprecated-key fail-hard, parameterized parser, OV nest only, tests, SCHEMA |
| **PR1** | CV/AV off-screen placeholder content (content-only; no runtime changes) |
| **PR2** | Spec updates, design artifact, archive supersession, remove dead code |

See full design doc for file tables, test migrations, and manual checklists.