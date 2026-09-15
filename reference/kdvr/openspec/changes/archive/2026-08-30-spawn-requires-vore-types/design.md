# Design: spawn-requires-vore-types

## Resolved decisions

| Topic | Decision |
|-------|----------|
| JSON key | `spawn.requires_vore_types` (under `spawn`, not top-level) |
| Name | `requires_vore_types` |
| Missing / null / `[]` | Unrestricted |
| Pair / single / all three | **AND**: every **recognized** listed type must be enabled (including `["OV","CV","AV"]`) |
| Empty recognized set | Unrestricted (missing / null / `[]` / junk-only) |
| Unknown tokens | Ignore; do not fail load |
| Wrong JSON type (not array / null) | **Load error** (schema violation) — leniency is for *values inside* the array only |
| Stock content | Add `"requires_vore_types": []` to every stock entity `spawn`; no non-empty stock gates |
| Spawn paths | **All** definition-based creation via `spawn_from_definition` (and floor eligibility pools that feed it). Save/load restore is **out** |
| Density | Do not reduce target count; ineligible defs are absent from the weighted pool |
| Prefs source | Run snapshot `engine.vore_content_prefs` (Options at New Game); tests pass prefs explicitly |
| Sample Mod | Game-owned `entities.json`: rewrite when missing or contents ≠ shipped template; **preserve** `mod.state` |
| Sample Mod extras | Add `requires_vore_types: []` and `engulfed_flavor` stubs to the sample template |
| Create Sample Mod | Ensure folder + template `entities.json` on **every** launch (not first-run-only), same ownership model as README refresh |

## Semantics (normative)

Let `raw` be the JSON value of `spawn.requires_vore_types`.

1. If key absent or value is `null` or `[]` → required set `R = ∅` (unrestricted).
2. Else `R = { t ∈ raw | t ∈ {"OV","CV","AV"} }` (order irrelevant; duplicates collapse).
3. If `R = ∅` → unrestricted.
4. Else eligible iff `∀ t ∈ R: prefs.is_enabled(t)` (so `R = {"OV","CV","AV"}` requires all three on).

Canonical storage after load: `SpawnConfig.requires_vore_types: frozenset[str]` of recognized types only (empty frozenset = unrestricted). Do **not** special-case all-three at parse time.

## Architecture

```
entities.json spawn.requires_vore_types
        ↓
entity_loader._parse_spawn → SpawnConfig.requires_vore_types
        ↓
meets_vore_type_requirements(def, prefs)  # pure helper
        ↓
┌───────────────────────────────┬────────────────────────────┐
│ Floor: _eligible_definitions  │ spawn_from_definition(...) │
│ (+ good quota pools)          │ returns None if gated out  │
└───────────────────────────────┴────────────────────────────┘
```

### Loader

- Add `requires_vore_types` to `_SPAWN_TRAITS`.
- Parse: omit/null/[] → `frozenset()`.
- Non-list non-null → `EntityLoadError`.
- List: keep only OV/CV/AV strings (including all three when present).
- Optional one-time warning for unknown tokens (nice-to-have; not required for PR1 if noisy).

### Spawn

- `meets_vore_type_requirements(definition, prefs) -> bool` in `src/spawn.py` (or small helper module next to spawn).
- `_eligible_definitions` / `eligible_good_definitions` take `vore_prefs` and skip failing defs.
- Thread prefs from `spawn_floor_population` ← engine.
- `spawn_from_definition(..., vore_prefs: VoreContentPreferences | None = None)`:
  - `None` → treat as **all types enabled** (test convenience / callers that already filtered).
  - Else if not `meets_...` → return `None` (update return type `Entity | None`).
- Update summon / arena / helpers to handle `None` (skip that summon / skip placement).

### Density invariant

`compute_target_npc_count` unchanged. Draws run `target` times among **remaining** eligible non-good defs. If the eligible pool is empty, place nothing for that pass (pre-existing empty-pool behavior). Filtering must not shrink `target` itself.

### Sample Mod refresh

Replace create-once-only policy for `entities.json`:

| Path | Behavior |
|------|----------|
| `mods/MODDING_README.txt` | Unchanged: rewrite when missing or text differs |
| `mods/Sample Mod/entities.json` | **New:** rewrite when missing or text differs from `SAMPLE_ENTITIES_JSON` |
| `mods/Sample Mod/mod.state` | If missing on create, write disabled + order 1; **never** overwrite an existing `mod.state` |
| Folder missing | Create folder + entities + mod.state (disabled) on every launch path that seeds mods (not only first-run onboarding) |

Content check: read file and compare to shipped string (same pattern as README; hash optional equivalent). Skip write when identical.

Update `openspec/specs/modding/spec.md` scenarios that currently say Sample Mod is create-once and never overwritten.

### Stock / sample content

- Scripted or careful edit: every `spawn` object in `data/entities.json` gains `"requires_vore_types": []`.
- Sample template: same empty array; add `engulfed_flavor` with short OV/CV/AV placeholder lines consistent with other sample narrative stubs.

## Performance

- Per definition: O(1) frozenset subset check (`R <= prefs.enabled`).
- Eligibility still one linear pass over registry per terrain (existing).
- No per-frame work. Sample Mod compare is one small file read per launch.

## Save compatibility

- No save fields. Prefs already snapshotted.
- NPCs already on a floor remain after load even if a future mod would have gated them (restore ≠ spawn).

## Test plan (pinned fixtures only)

- Parse: omit / null / [] / singles / pairs / all three / unknowns / bad type.
- `meets_vore_type_requirements` truth table vs prefs.
- Floor eligibility: CV-only def excluded when CV off; included when on; sibling unrestricted def still fills density target.
- `spawn_from_definition` returns `None` when gated.
- Sample Mod: missing → write; stale → rewrite; identical → no write; existing `mod.state` preserved; enabled flag preserved.
- Do **not** assert against live stock balance weights.

## Alternatives considered

| Approach | Why not |
|----------|---------|
| Infer from `vore_narratives` keys | Too magical; stub narratives ≠ “only method”; modders need explicit control |
| Top-level field | Designer chose under `spawn` |
| OR semantics | Designer specified AND for multi-entry arrays |
| Create-once Sample Mod | Designer wants game-owned template sync like README |
