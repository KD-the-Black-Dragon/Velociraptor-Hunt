# Proposal: Spawn gate by required vore types

**Status:** Accepted and archived 2026-08-30  
**Change id:** `spawn-requires-vore-types`  
**Extends:** `openspec/specs/npc-data/spec.md`, `openspec/specs/modding/spec.md`, `openspec/specs/vore/spec.md` (prefs snapshot), `data/SCHEMA.md`

## Why

This is a vore game: every enemy must be able to vore in at least one **enabled** way. Modders (and future content) need a data way to say “this species only exists when CV is on” (or OV/AV, or both of two types) without hardcoding entity ids in Python.

Without a gate, a CV-only monster still spawns when the player disabled CV — then it cannot initiate any valid vore type, which breaks the design contract.

## What

1. **New optional field** on each entity’s `spawn` object: `requires_vore_types` — array of strings.
2. **Semantics (AND of recognized types):**
   - Missing, `null`, or `[]` → no restriction (current behavior).
   - `["OV"]` → spawn only if OV is enabled (CV/AV irrelevant).
   - `["CV"]` / `["AV"]` → same for that type.
   - `["OV","CV"]` (any pair) → spawn only if **both** listed types are enabled.
   - `["OV","CV","AV"]` → spawn only if **all three** are enabled (same AND rule; unusual but consistent).
   - After ignoring unknown strings, if the recognized set is empty → treat as unrestricted (same as missing / null / `[]`).
   - Unknown tokens are ignored (lenient).
3. **Spawn integration:** gated definitions are **not candidates**. Density / good-quota **target counts are unchanged**; draws simply pick among remaining eligible species. Same gate applies to **all definition-based materialization** (floor population, arena, summons, debug spawn helpers that call `spawn_from_definition`) using the run’s `VoreContentPreferences` snapshot. **Save restore does not despawn** existing NPCs.
4. **Stock data:** every shipped `data/entities.json` entity gets `"requires_vore_types": []` under `spawn` (no gameplay change; documents the field).
5. **Sample Mod:** update embedded `entities.json` template with `requires_vore_types` and missing `engulfed_flavor`; treat Sample Mod `entities.json` as **game-owned** — refresh on launch when missing or contents differ from shipped template (content-equality / hash check; skip identical write). Preserve existing `mod.state` (enabled/order) when present.

## Out of scope

- Inferring requirements from `vore_narratives` keys automatically
- Soft-dropping or rewriting mid-run NPCs when Options change (prefs are snapshotted at New Game)
- Changing density formulas or good-quota caps
- Per-type weight multipliers (binary eligible / not)
- Annotating stock monsters with non-empty requirements (stock supports all three types)

## Past-version / release safety

| Surface | Mitigation |
|---------|------------|
| Old mods / entities omitting the field | Unrestricted (same as today) |
| Stock empty arrays | Additive JSON; loaders default omit → `()` |
| Saves | No wire-format change; restore ignores this gate |
| Sample Mod overwrite | Game-owned template; players who customize should copy to a new folder (README already advises this) |

## Success

- Mod entity with `spawn.requires_vore_types: ["CV"]` never appears when CV is off; appears normally when CV is on
- Floor NPC **count** still matches density target when other species remain eligible
- `[]`, missing, and junk-only arrays behave as unrestricted; `["OV","CV","AV"]` requires all three enabled
- Sample Mod `entities.json` stays in sync with the shipped template without needless disk writes
- Specs / SCHEMA / MODDING_README document the field and Sample Mod refresh rule

## Phased delivery

See `tasks.md`: PR1 loader + spawn gate + tests; PR2 stock/sample/docs refresh; PR3 live specs + acceptance + archive.
