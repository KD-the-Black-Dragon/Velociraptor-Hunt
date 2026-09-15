# Proposal: Entity mod deep merge (selective field override)

**Status:** Active  
**Change id:** `entity-mod-deep-merge`  
**Extends:** `openspec/specs/modding/spec.md` (id-keyed entity merge semantics)

## Why

Mods that touch stock monsters today must **full-replace** the entire entity object for that `id`. That forces authors to copy every combat stat, spawn band, and nested narrative blob just to change one field (e.g. `spawn.weight: 0`, or alternate vore lines).

Stock balance fields change often. Full-replace mods then silently pin stale stats and break when the author only meant to disable a species or rewrite text. The designer wants **selective overrides**: omit a field → keep the layered (core + earlier mods) value; set a field → overwrite it.

## What

1. **Deep merge for `entities.json` only** when a mod entry’s `id` already exists in the running layered catalog.
2. **New entity ids** still require a complete, schema-valid object (no inheritance from nothing).
3. **Merge rules:** nested **objects** merge recursively; **arrays** and scalars **replace** when the key is present.
4. **Mod stacking:** each enabled mod deep-merges onto the **current** result (core → A → B), not only onto bare core.
5. **Validate the merged sum** after each mod’s `entities.json` is applied; on failure, skip that mod file’s contribution (existing bad-mod behavior).
6. **Docs** — README, `data/SCHEMA.md`, sample mod text, and live modding spec updated so authors know the “turn off wolves” / narrative-only patterns.

## Motivating examples (target)

```json
{
  "schema_version": 1,
  "entities": [
    { "id": "wolf", "spawn": { "weight": 0 } }
  ]
}
```

Wolves keep all stock stats and narratives; they simply never spawn.

```json
{
  "schema_version": 1,
  "entities": [
    {
      "id": "wolf",
      "vore_narratives": {
        "OV": [{ "attempt": ["..."], "success": ["..."] }]
      }
    }
  ]
}
```

Only `vore_narratives.OV` is replaced (array replace under a deep-merged object); `CV` / `AV`, combat, and spawn inherit.

## Out of scope

- Deep merge for weapons / armor / potions / wands / throwables / floor_runes / macguffins / names (remain full-replace-by-id)
- Whole-file catalogs (unchanged)
- JSON Patch / tombstones / “delete this optional field back to absent”
- Python mods, assets, new entity schema fields
- Auto-migrating old full-copy mods (they keep working as total field overlays)

## Success

- A one-field wolf `spawn.weight: 0` mod loads, validates, and desawns wolves without restating the rest of the wolf
- Narrative-only and nested `spawn` patches work as documented
- Brand-new ids still fail loudly if mandatory fields are missing
- Existing full-entity override mods still behave correctly
- Automated tests use **pinned fixtures only** (no assertions against live `data/entities.json`)
- Specs and player-facing docs match the new rule

## Phased delivery

See `tasks.md`: PR1 merge + tests; PR2 docs + live spec; PR3 acceptance.
