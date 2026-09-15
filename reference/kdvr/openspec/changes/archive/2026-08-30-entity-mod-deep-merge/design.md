# Design: Entity mod deep merge

**Change id:** `entity-mod-deep-merge`  
**Primary code:** `src/mods/pipeline.py` (`_merge_id_list` / entity layering path)  
**Live spec to update:** `openspec/specs/modding/spec.md`  
**Docs:** `README.md`, `data/SCHEMA.md`, `src/mods/seed_sample.py` (MODDING_README text)

---

## Resolved decisions

| Topic | Decision | Notes |
|-------|----------|--------|
| Catalog scope | **`entities.json` only** | Other id-keyed catalogs stay full-replace-by-id until a later change |
| Nested objects | **Recursive deep merge** | e.g. `spawn.weight` keeps other `spawn` keys |
| Arrays | **Replace entire array** when the key is present | Includes `abilities`, `fg`, `introduction`, `vore_narratives.OV`, etc. |
| Mod-on-mod | **Deep-merge each mod onto the running catalog** | Core → A → B; B only overwrites keys it sets |
| When to deep-merge vs insert | Id **already in current layered list** → deep merge; **unknown id** → insert as full entry | “Current” includes core + earlier successful mods |
| Validation | Parse/validate **after** merging a mod’s entities into the running list | Same skip-file-on-error as today |
| Optional field removal | **Not supported** | No tombstone; omit = inherit; present (including `null` / `[]`) = overwrite |
| Backward compatibility | Full-copy override mods **keep working** | Providing every key is just a total overlay via the same merge |
| `MODDING_README.txt` | **Refresh each launch** when missing or contents differ | Game-owned doc under `mods/`; Sample Mod still create-once, never overwritten |

---

## Current behavior (baseline)

`_merge_id_list` in `src/mods/pipeline.py` does **full replace by id**:

```text
by_id[entity_id] = entry  # overlay object wholesale
```

`layer_id_list_catalog` then `parse`s the merged raw list. A minimal `{id, spawn:{weight:0}}` fails entity validation because mandatory fields are missing — so the “turn off wolves” patch is impossible without copying the whole wolf.

---

## Target behavior

### Merge algorithm (entities only)

For each enabled mod’s `entities.json`, in load order:

1. Load overlay list.
2. For each overlay entry with string `id`:
   - If `id` **not** in current list → append overlay entry as-is (new species).
   - If `id` **is** present → `current[id] = deep_merge(current[id], overlay)`.
3. Build `{schema_version, entities: merged_list}` and run the existing entity parse/validate.
4. On success → adopt as the new current list. On failure → record `ModLoadIssue`, **do not** apply any of that mod’s entity changes (unchanged skip semantics).

### `deep_merge(base, overlay)` 

JSON-value rules:

| Overlay value type | Behavior |
|--------------------|----------|
| object (`dict`) | Recurse: for each key in overlay, merge into a **copy** of base; keys only in base kept |
| array (`list`) | **Replace** — use overlay array |
| scalar / `null` | **Replace** — use overlay value |
| Missing key in overlay | Keep base value |

Pseudo:

```text
deep_merge(base, overlay):
  if overlay is not a dict OR base is not a dict:
    return overlay
  out = shallow copy of base
  for key, value in overlay:
    if key in out and both out[key] and value are dicts:
      out[key] = deep_merge(out[key], value)
    else:
      out[key] = value   # scalars, arrays, null, or type mismatch → replace
  return out
```

Type mismatch (base has array, overlay has object for same key, etc.) → **replace with overlay** (no clever coercion).

### Why arrays replace (important for narratives)

Stock `vore_narratives` looks like:

```json
"vore_narratives": {
  "OV": [ { "attempt": ["..."], "success": ["..."] } ],
  "CV": [ ... ],
  "AV": [ ... ]
}
```

Deep-merging the **object** `vore_narratives` while **replacing** the `OV` array lets a mod rewrite oral lines only and keep CV/AV. Index-wise array merge would be surprising and brittle for variant lists — rejected.

Same for `abilities`, `fg`, `introduction`, and per-type arrays under `digestion_complete` / `npc_vore_*` / `offscreen_*`.

### Validation story

- **Core** still hard-fails on invalid stock data.
- **New id** in a mod: merged result is just the overlay object → must include all mandatory fields or the mod’s `entities.json` is skipped with a player-facing error.
- **Existing id** patch: validate the **sum** (inherited + overrides). Invalid override (e.g. `max_hp: -1`, bad `mobility`) fails the whole mod entities file for that load pass.
- Do **not** add a separate “partial schema” validator; one schema after merge is enough.

### Error reporting

Reuse `ModLoadIssue(mod_name, filename, reason)`. Prefer reasons that remain understandable when the failure is in a nested field after merge (existing parse errors usually name the field/path already).

---

## Worked examples

### Turn off wolves

```json
{
  "schema_version": 1,
  "entities": [
    { "id": "wolf", "spawn": { "weight": 0 } }
  ]
}
```

Result: stock wolf with `spawn.weight == 0`; `min_depth` / `max_depth` / `terrain` unchanged.

### Narrative-only OV rewrite

```json
{
  "schema_version": 1,
  "entities": [
    {
      "id": "wolf",
      "vore_narratives": {
        "OV": [
          {
            "attempt": ["Custom attempt."],
            "success": ["Custom success A.", "Custom success B."]
          }
        ]
      }
    }
  ]
}
```

`CV`/`AV` and all combat/spawn fields inherit.

### Two mods stacking

- Mod A (order 1): `{ "id": "wolf", "display_name": "Dire Wolf", "spawn": { "weight": 5 } }`
- Mod B (order 2): `{ "id": "wolf", "spawn": { "weight": 0 } }`

Result: `display_name` = `"Dire Wolf"` (from A), `spawn.weight` = `0` (from B), other spawn keys from core (unless A set them).

### New species

```json
{ "id": "cool_dragon", "display_name": "Cool Dragon", ...all mandatory... }
```

Still required in full. A stub `{ "id": "cool_dragon", "spawn": { "weight": 1 } }` → validation failure → skip.

### Strip abilities

`{ "id": "wolf", "abilities": [] }` replaces the abilities array with empty (intentional). There is no “inherit abilities” once the key is present.

---

## Implementation notes

- Prefer a small pure helper (e.g. `deep_merge_json` / `_deep_merge_entity_dict`) unit-tested without the filesystem.
- Keep item/id-list full-replace path for non-entity catalogs; either branch inside `_merge_id_list` via a `merge_mode=` flag, or a dedicated `_merge_entity_id_list` used only by `load_entities_layered`. Avoid changing weapons/etc. by accident.
- Do **not** deep-merge `names.json` pools (out of scope; pools are whole arrays per entity key).
- Tests: extend `tests/test_mod_entities_pipeline.py` (and/or a focused `test_mod_entity_deep_merge.py`) with **pinned** core JSON in `tmp_path` — never assert against live `data/entities.json`.
- Update seed sample guidance: prefer patch overrides; “Prefer new ids over overwriting stock…” can soften to “patch stock ids with only the fields you mean to change.”

### Performance

Entity catalogs are small (tens of species). One recursive merge per overlay entry per mod at load/reload time is negligible. No per-frame cost.

### Save compatibility

No save schema change. Spawn weight 0 still means “do not spawn”; old saves with wolf entities remain valid. Mod fingerprint behavior unchanged.

---

## Spec delta (intent)

In `openspec/specs/modding/spec.md`:

- Split **entities** from other id-keyed catalogs.
- Entities: merge by id with **selective deep merge** as above; scenarios for weight-0 patch, nested narrative patch, new-id completeness, stacked mods.
- Other catalogs: keep “full replace of that entry.”
- Purpose blurb: remove/adjust any “no deep merge” wording that would contradict entity field merge (whole-file / dungeon-band deep merge remains unsupported).

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Authors expect array element patching | Document OV/CV/AV array replace clearly with examples |
| Accidental empty `abilities: []` clears stock abilities | Document “present key replaces”; examples in SCHEMA/README |
| Type mismatch surprises | Document replace-on-mismatch; tests |
| Scope creep into items | Explicit out of scope; separate merge path for entities |

---

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| Full recursive merge including arrays-by-index | Surprising for narrative variant lists |
| Top-level keys only (no nested `spawn` merge) | Forces restating whole `spawn` to change weight |
| Deep-merge only against core (later mod full-owns id) | Breaks cooperative stacking (A renames, B disables spawn) |
| All id-keyed catalogs in one PR | Larger blast radius; entities are the stated use case |

---

## PR plan (summary)

| PR | Scope |
|----|--------|
| **PR1** | Deep-merge helper + entity pipeline wiring + automated tests (pinned fixtures) |
| **PR2** | Live modding spec + README + SCHEMA + seed sample text |
| **PR3** | Acceptance artifacts, AGENTS archive pointer, final sign-off |

No gameplay systems change beyond load-time entity composition.
