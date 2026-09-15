# Proposal: `requires_vore_types` as capability (OR spawn + attempt filter + generic fallback)

**Status:** Accepted and archived 2026-08-31  
**Change id:** `requires-vore-types-capability`  
**Extends / corrects:** `openspec/specs/npc-data/spec.md`, `openspec/specs/vore/spec.md`, `openspec/specs/modding/spec.md`, `data/SCHEMA.md`  
**Supersedes spawn semantics from:** `openspec/changes/archive/2026-08-30-spawn-requires-vore-types/` (AND gate)

## Why

Every enemy must be able to execute **at least one** vore type the player has enabled. Some species (and mods) can only perform a **subset** of OV / CV / AV.

The existing `spawn.requires_vore_types` field was shipped as an **AND** spawn gate (“every listed type must be enabled”). That is too strict: a CV+AV species should still spawn for a CV-only player. It also never restricted **which types the monster attempts**, so a “CV-only” species could still roll OV/AV when the player had all three enabled.

## What

Reinterpret non-empty `spawn.requires_vore_types` as the species’ **capability set**:

1. **Spawn eligibility = OR (non-empty intersection)**  
   - Missing / `null` / `[]` / junk-only → unrestricted (unchanged).  
   - Non-empty recognized set `C` → eligible iff `C ∩ prefs.enabled ≠ ∅`.  
   - Example: `["OV","CV"]` spawns when OV **or** CV (or both) is enabled; blocked only when the player has neither.

2. **Initiation filter**  
   - Unrestricted (`C` empty) → attempt pool = existing narrative types ∩ prefs (today’s behavior).  
   - Non-empty `C` → attempt pool = (narrative types ∩ `C` ∩ prefs).  
   - Applies to **all living** monsters (`SpeciesId` → definition), including save-restored NPCs — not only new spawns.

3. **Generic fallback type (`GENERIC`)**  
   - When a VoreCapable predator would attempt vore but the attempt pool is empty, use an internal prefs-immune type `GENERIC` with hardcoded minimal copy (player modal attempt/success, player digestion, NPC-vs-NPC on-screen hit/miss, off-screen vore/digest).  
   - Not shown in Options; cannot be disabled by prefs. Escape hatch for empty capability∩prefs (data mismatch, deliberate mid-run fiddling, etc.).

4. **Stock**  
   - All shipped entities keep `"requires_vore_types": []` (unrestricted; may attempt any enabled type).

5. **Docs**  
   - SCHEMA, README, MODDING_README / Sample Mod text, live specs updated from AND → capability/OR + attempt filter + GENERIC note.

## Out of scope

- Assigning non-empty `requires_vore_types` to stock enemies  
- Removing or renaming the JSON key  
- Inferring capability solely from `vore_narratives` keys (keys still supply narrative content / `VoreNarratives.types`; `requires_vore_types` is the explicit capability restriction when set)  
- Changing density / good-quota math  
- Exposing `GENERIC` in Options or onboarding

## Past-version / release safety

| Surface | Mitigation |
|---------|------------|
| Old mods with AND expectation | Behavior loosens (more spawn cases); document OR semantics |
| Stock `[]` | No gameplay change |
| Saves | No wire-format bump; restore still does not despawn; attempt filter uses live definition |
| Mid-run Options | Run prefs snapshot unchanged; GENERIC covers empty-pool edge cases |

## Success

- `["CV","AV"]` + prefs `{CV}` → spawns; attempts **only** CV  
- Same species + prefs all three → spawns; attempts only CV or AV (never OV)  
- Same species + prefs `{OV}` only → does **not** spawn  
- `[]` / missing → unrestricted spawn + any prefs-enabled type  
- Empty attempt pool → `GENERIC` minimal vore/digest copy still works  
- Targeted tests cover OR table, initiation filter, and GENERIC paths

## Phased delivery

See `tasks.md`: PR1 spawn OR + docs/tests; PR2 initiation filter; PR3 GENERIC fallback; PR4 live specs polish + acceptance + archive.
