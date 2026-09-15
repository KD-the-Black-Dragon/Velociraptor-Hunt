# Acceptance Report: requires-vore-types-capability

**Date:** 2026-08-31  
**Scope:** Reinterpret `spawn.requires_vore_types` as a **capability** set: spawn OR (non-empty ∩ prefs), initiation filter for living predators, prefs-immune `GENERIC` stub (likely unreachable under New Game prefs snapshot).

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_spawn_requires_vore_types_pr1.py` | passed |
| `tests/test_requires_vore_types_initiation_pr2.py` | passed |
| `tests/test_vore_generic_fallback_pr3.py` | passed |
| Related: offscreen vore/digest, digestion, vore AI/modal, enhancements NPC vore | passed (targeted) |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1–PR3: designer playtest / sign-off before archive
- Stock `requires_vore_types: []` — no visible change in normal play
- `GENERIC` retained as stub; noted likely unreachable with immutable run prefs + spawn OR

## Live specs / docs

- `openspec/specs/npc-data/spec.md` — capability / OR spawn + initiation scenarios
- `openspec/specs/vore/spec.md` — capability initiation + GENERIC stub + reachability note
- `openspec/specs/modding/spec.md` — docs requirement for capability + GENERIC note
- `data/SCHEMA.md`, `README.md`, `src/mods/seed_sample.py` (MODDING_README text)

## Key implementation

| Area | Change |
|------|--------|
| `src/spawn.py` | `meets_vore_type_requirements` AND → OR |
| `src/systems/vore.py` | capability lookup, attemptable pool, `pick_attempt_narrative_type` |
| `src/systems/vore_fallback.py` | `GENERIC` + minimal hardcoded copy |
| `src/systems/digestion.py` | GENERIC player modal + NPC digest / off-screen |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-31-requires-vore-types-capability/`.
