# Design: requires-vore-types-capability

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Meaning of non-empty list | **Capability set** — types this species can perform |
| Missing / `null` / `[]` / junk-only | Unrestricted: always spawn-eligible; may attempt any prefs-enabled type |
| Spawn gate | **OR**: eligible iff `capability ∩ prefs.enabled ≠ ∅` |
| Former AND pairs / all-three | **Superseded.** `["OV","CV"]` spawns if OV **or** CV is on |
| Initiation | Pool = narrative types ∩ capability (if non-empty) ∩ prefs; uniform pick |
| Who is filtered | **All living monsters** via `SpeciesId` → definition (incl. save-restored) |
| Relation to `vore_narratives` | Keys define content / `VoreNarratives.types`; capability restricts which may be chosen |
| Stock data | Keep `"requires_vore_types": []` — no stock annotations in this change |
| Empty attempt pool | Internal type **`GENERIC`**, prefs-immune last resort |
| GENERIC reachability | **Likely unreachable** while prefs are New Game–snapshotted (immutable mid-run) and spawn OR already excludes zero-intersection species; stub kept for future / odd edges |
| GENERIC trigger | Only when attempt pool is empty but predator is otherwise ready to vore |
| GENERIC coverage | Player attempt/success modal; player digestion modal/complete; NPC hit/miss; off-screen vore/digest — minimal `{predator}`/`{prey}` templates |
| GENERIC in Options | **No** |
| Digestion rules for GENERIC | Standard (OV-like) path; **not** alternate-CV |
| JSON key rename | **No** — keep `requires_vore_types` |
| Save format | No bump; restore does not despawn via this gate |
| Parse rules | Unchanged (unknown tokens ignored; bad type → load error) |

## Semantics (normative)

Let `C` = recognized `{OV,CV,AV}` from `spawn.requires_vore_types`.

### Spawn — `meets_vore_type_requirements`

1. If `C = ∅` → `True`.
2. Else → `bool(C ∩ prefs.enabled)` (`prefs is None` → all v1 types enabled).

### Initiation pool

```
base = VoreNarratives.types
if C non-empty:
    base = [t for t in base if t in C]
pool = [t for t in base if prefs.is_enabled(t)]
if not pool:
    use GENERIC
else:
    rng.choice(pool)
```

### Examples

| Capability | Prefs | Spawn? | Attempts |
|------------|-------|--------|----------|
| `[]` | any | yes | any enabled type |
| `["CV"]` | `{CV}` or all three | yes | CV only |
| `["CV","AV"]` | `{CV}` | yes | CV only |
| `["CV","AV"]` | all three | yes | CV or AV (never OV) |
| `["CV","AV"]` | `{OV}` only | **no** | — |

## Architecture

```
SpawnConfig.requires_vore_types
        ↓
┌──────────────────────────────┬─────────────────────────────────────┐
│ meets_vore_type_requirements │ attemptable_narrative_types(...)    │
│   OR / non-empty intersection│   base ∩ C? ∩ prefs → else GENERIC  │
└──────────────────────────────┴─────────────────────────────────────┘
```

### Hook points

| Concern | Location |
|---------|----------|
| Spawn OR | `src/spawn.py` — `meets_vore_type_requirements` |
| Attempt filter | `src/systems/vore.py` — shared helper for `_vore_base_eligible` + `pick_narrative_type` |
| Definition lookup | `SpeciesId` → entity registry `.spawn.requires_vore_types` |
| GENERIC copy | New module e.g. `src/systems/vore_fallback.py`; wire modal / digest / NPC / off-screen lookups |

### Performance

- Frozenset intersects only on spawn eligibility and vore-attempt evaluation — not per frame.
- Single helper for attempt pool so spawn docs and AI cannot drift.

### Save compatibility

- Live filter via `SpeciesId` — no new save fields.
- Optional bake of filtered `VoreNarratives.types` at spawn is out of scope for correctness (nice-to-have only).

## GENERIC copy contract (PR3)

**Type id:** `GENERIC` (not in `VORE_NARRATIVE_TYPES_V1`).

Illustrative templates (finalize in PR3; keep extremely basic):

| Surface | Template idea |
|---------|----------------|
| Player attempt | `"{predator} attempts to swallow you."` |
| Player success | `"{predator} swallows you."` |
| Player digest | Minimal hold/complete lines with `{predator}` |
| NPC hit / miss | `"{predator} swallows {prey}."` / `"{predator} fails to swallow {prey}."` |
| Off-screen | Same tone, one-liners |

## PR notes

- **PR1:** Spawn OR only; initiation unchanged; docs for spawn semantics.
- **PR2:** Initiation filter; empty pool still means no attempt (GENERIC lands in PR3).
- **PR3:** GENERIC last resort + full minimal copy wiring + tests.
- **PR4:** Live spec scenarios, acceptance, archive, AGENTS pointer clear.
