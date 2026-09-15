# Design: NPC Vore Message Logs (Consolidated)

| Field | Value |
|-------|-------|
| **Author** | Systems Design |
| **Date** | 2026-07-02 |
| **Status** | Draft for review |
| **Change id** | `add-npc-vore-message-logs` |
| **Spec targets** | `openspec/specs/vore/spec.md`, `openspec/specs/digestion/spec.md`, `openspec/specs/npc-data/spec.md`, `openspec/specs/enhancements-3/spec.md` |
| **Depends on** | Shipped NPC vore (`try_resolve_npc_vore`), digestion (`complete_npc_digestion`), archived `add-offscreen-vore-messages` |

---

## Summary

This design consolidates **all NPC-on-NPC vore message log surfaces** — on-screen hit/miss and off-screen hit/digest — into one schema and routing model. Part of the system was implemented ahead of design (on-screen `npc_vore_hit` / `npc_vore_miss`); off-screen logging shipped under archived change `add-offscreen-vore-messages` using **six flat JSON fields** that diverge from the dominant entity narrative pattern (typed objects keyed by `OV` / `CV` / `AV`).

**Goals of this change:**

1. Document the full NPC vore log system as the authoritative design.
2. **Migrate** off-screen fields from flat `offscreen_ov` … `offscreen_av_digest` to object fields `offscreen_vore` and `offscreen_digest`.
3. **Fill content gaps**: wolf and shark ship placeholder CV/AV off-screen lines for every narrative type the species supports.
4. Reconcile live specs and `data/SCHEMA.md` with the unified object schema.
5. Leave player `vore_narratives` modals and `digestion_player_modal` paths **unchanged** and independent.

---

## Problem statement

| Issue | Detail |
|-------|--------|
| Design bypass | On-screen NPC vore logs (`npc_vore_hit`, `npc_vore_miss`, `pick_visible_npc_vore_message`) landed without `proposal.md` / `design.md` / `tasks.md`. |
| Schema split | On-screen uses object fields (like `digestion_complete`); off-screen uses six flat top-level arrays. Modders must learn two shapes for the same conceptual axis (narrative type). |
| Content gap | Wolf and shark define full OV/CV/AV on-screen data but only **OV** off-screen vore hit and digest arrays. CV/AV off-screen events are silent when those types roll. |
| Spec drift | Live specs reference flat off-screen keys; `NarrativeIndex` already normalizes flat fields into internal `(entity_id, type)` maps — redundant indirection. |

---

## Current implementation (verified)

### On-screen NPC vore (log-only, no modal)

**Hook:** `try_resolve_npc_vore()` in `src/systems/vore.py`.

When `entity_visible_to_player(predator) OR entity_visible_to_player(prey)`:

- **Hit:** `pick_visible_npc_vore_message(..., hit=True)` → entity `npc_vore_hit[type]` → fallback `NPC_VORE_HIT_POOL` in `src/vore_npc_content.py`.
- **Miss:** same with `npc_vore_miss` → `NPC_VORE_MISS_POOL`.
- Formatting via `format_npc_vore_line()` (`{predator}` / `{prey}` placeholders).

**Data:** `npc_vore_hit` and `npc_vore_miss` on wolf/shark in `data/entities.json` — full OV/CV/AV coverage (placeholder copy).

**Loader:** `_parse_digestion_lines()` (shared parser with `digestion_complete`).

**Index:** `NarrativeIndex.npc_vore_hit` / `npc_vore_miss` keyed `(entity_id, narrative_type)`.

### Off-screen NPC vore hit

**Hook:** same `try_resolve_npc_vore()`, `elif hit` branch when not visible.

- Random line from `NarrativeIndex.pick_offscreen_vore_line(entity_id, type, rng)`.
- **No log** on miss; **no fallback** to on-screen pools when array missing/empty.

### Off-screen NPC digestion complete

**Hook:** `complete_npc_digestion()` in `src/systems/digestion.py`.

When not visible: `pick_offscreen_digest_line()` — entity array only, no `DIGESTION_COMPLETE_POOL` fallback.

### On-screen NPC digestion complete (unchanged, out of migration scope)

When visible: entity `digestion_complete[type]` → fallback `DIGESTION_COMPLETE_POOL`.

### Player paths (independent)

| Path | Surface | Data |
|------|---------|------|
| Player vore attempt | Modal | `vore_narratives` per entity |
| Player digestion complete | Modal | `digestion_player_modal` per entity |

NPC log lines SHALL NOT be used for player-facing modals.

### Dead / legacy code

`pick_npc_vore_message()` in `vore.py` is **unused** after on-screen entity-first wiring; remove in cleanup PR.

---

## Target JSON schema (entities.json)

All NPC vore **log** fields use the same object shape as `digestion_complete`:

```json
"<field_name>": {
  "OV": ["line one", "line two"],
  "CV": ["..."],
  "AV": ["..."]
}
```

| Field | When used | Visibility | Fallback |
|-------|-----------|------------|----------|
| `npc_vore_hit` | NPC vore attempt succeeds | Predator **or** prey in player FOV | `NPC_VORE_HIT_POOL[type]` |
| `npc_vore_miss` | NPC vore attempt fails | Predator **or** prey in player FOV | `NPC_VORE_MISS_POOL[type]` |
| `offscreen_vore` | NPC vore attempt succeeds | **Neither** in player FOV | **None** (silent) |
| `offscreen_digest` | NPC digestion completes | **Neither** in player FOV | **None** (silent) |
| `digestion_complete` | NPC digestion completes | Predator **or** prey in player FOV | `DIGESTION_COMPLETE_POOL[type]` |

### Example (wolf, post-migration)

```json
"npc_vore_hit": {
  "OV": ["{predator} swallows {prey} whole!", "..."],
  "CV": ["{predator} constricts and swallows {prey}!", "..."],
  "AV": ["{predator} draws {prey} inside!", "..."]
},
"npc_vore_miss": {
  "OV": ["{predator} tries to swallow {prey} but fails.", "..."],
  "CV": ["..."],
  "AV": ["..."]
},
"offscreen_vore": {
  "OV": [
    "You hear a distant gulp echo through the halls.",
    "A muffled swallowing sound reaches you from far away."
  ],
  "CV": [
    "A distant crushing sound echoes through the halls.",
    "You hear muffled thrashing somewhere out of sight."
  ],
  "AV": [
    "A faint pull of displaced air reaches you from far away.",
    "Something unseen takes prey in the distance."
  ]
},
"offscreen_digest": {
  "OV": ["A satisfied rumble echoes from somewhere in the dungeon."],
  "CV": ["A wet squelch echoes from somewhere in the dungeon."],
  "AV": ["A distant compression sound fades into silence."]
}
```

### Placeholder rules

| Token | Resolution |
|-------|------------|
| `{predator}` | `entity_log_name(predator)`; sentence-start capitalization when template begins with `{predator}` |
| `{prey}` | `entity_log_name(prey)` |

Placeholders are **optional** on all log surfaces. Off-screen lines may be ambient-only (no names). On-screen lines typically include both tokens.

### Loader rules

| Rule | Behavior |
|------|----------|
| Parser | Parameterize `_parse_digestion_lines(raw, entity_id, field_name)` so `EntityLoadError` messages name the actual field (e.g. `offscreen_vore.CV`, not `digestion_complete.CV`). Apply to `digestion_complete`, `npc_vore_hit`, `npc_vore_miss`, `offscreen_vore`, and `offscreen_digest`. Function rename to `_parse_narrative_type_lines` is optional in PR2. |
| Absent key / `null` | Field → `None` on `EntityDefinition` |
| Empty type array | **Load error** — present key with `[]` for a type is invalid (same as `digestion_complete`). **Semantic change:** flat off-screen fields used `_parse_string_array_field()`, which treated top-level `[]` as `None`; object fields do not. |
| Invalid shape | `EntityLoadError` |
| Deprecated flat keys | See **Deprecated-key handling** below — **fail hard**, not warn-only. |
| Traits whitelist | `_ENTITY_TRAITS` lists `offscreen_vore`, `offscreen_digest`; remove six flat names. |

#### Deprecated-key handling (PR0 — explicit loader step)

Removing the six flat names from `_ENTITY_TRAITS` alone is **insufficient**: unknown keys today flow through `_scan_unknown_traits()` → `LoadWarnings.warn_unknown_trait()` (warn-once, continue loading). Stale mods would silently lose off-screen data.

PR0 SHALL add a `_DEPRECATED_OFFSCREEN_KEYS` map checked in `_parse_entity()` **before** `_scan_unknown_traits()`:

```python
_DEPRECATED_OFFSCREEN_KEYS: dict[str, str] = {
    "offscreen_ov": "offscreen_vore",
    "offscreen_cv": "offscreen_vore",
    "offscreen_av": "offscreen_vore",
    "offscreen_ov_digest": "offscreen_digest",
    "offscreen_cv_digest": "offscreen_digest",
    "offscreen_av_digest": "offscreen_digest",
}
```

For each deprecated key present on the entity raw dict, raise `EntityLoadError` with text like:

`entity 'wolf': 'offscreen_ov' is deprecated; use 'offscreen_vore' object keyed by OV/CV/AV`

**Contrast with genuinely unknown traits:** those continue to warn-only per `npc-data` loader policy. Deprecated schema keys are a different class — intentional **fail** to prevent silent regression (see K2).

### EntityDefinition (target)

```python
npc_vore_hit: dict[str, tuple[str, ...]] | None = None
npc_vore_miss: dict[str, tuple[str, ...]] | None = None
offscreen_vore: dict[str, tuple[str, ...]] | None = None
offscreen_digest: dict[str, tuple[str, ...]] | None = None
```

Remove: `offscreen_ov`, `offscreen_cv`, `offscreen_av`, `offscreen_ov_digest`, `offscreen_cv_digest`, `offscreen_av_digest`.

### NarrativeIndex (target)

`from_registry()` reads object fields directly — no `offscreen_vore_fields` / `offscreen_digest_fields` mapping dict. Internal storage unchanged:

```python
offscreen_vore: dict[tuple[str, str], tuple[str, ...]]   # (entity_id, OV|CV|AV)
offscreen_digest: dict[tuple[str, str], tuple[str, ...]]
```

Public pickers unchanged: `pick_offscreen_vore_line`, `pick_offscreen_digest_line`, `npc_vore_hit_lines`, `npc_vore_miss_lines`.

---

## Runtime routing table

Visibility gate (shared):

```python
on_screen = (
    entity_visible_to_player(game_map, predator)
    or entity_visible_to_player(game_map, prey)
)
```

| Event | `on_screen` | Outcome | Message source | Log? |
|-------|-------------|---------|----------------|------|
| `try_resolve_npc_vore` | yes | hit | `npc_vore_hit[type]` → `NPC_VORE_HIT_POOL` | yes |
| `try_resolve_npc_vore` | yes | miss | `npc_vore_miss[type]` → `NPC_VORE_MISS_POOL` | yes |
| `try_resolve_npc_vore` | no | hit | `offscreen_vore[type]` only | if data exists |
| `try_resolve_npc_vore` | no | miss | — | **no** |
| `complete_npc_digestion` | yes | complete | `digestion_complete[type]` → `DIGESTION_COMPLETE_POOL` | yes |
| `complete_npc_digestion` | no | complete | `offscreen_digest[type]` only | if data exists |

**Narrative type** comes from `Predator.narrative_type` (digestion) or `pick_narrative_type(monster_narrative_types(predator), prefs, rng)` (vore attempt), filtered by `VoreContentPreferences`.

**Scope:** Evil predators only (`try_resolve_npc_vore`); good/neutral may define fields but runtime ignores them for NPC vore.

---

## Migration: flat off-screen → object fields

### Recommendation: **Migrate now** (one-time, PR0)

| Factor | Assessment |
|--------|------------|
| Data volume | Only wolf and shark have off-screen content |
| Code volume | `entity_registry`, `entity_loader`, `narrative_index`, tests, 2 JSON entities |
| Consistency | Aligns with `digestion_complete`, `npc_vore_hit`, `npc_vore_miss`, `vore_narratives` |
| Internal model | `NarrativeIndex` already keys by `(entity_id, type)` — flat fields are an extra mapping layer |
| Cost of deferring | Every new evil species copies wrong pattern; dual docs in SCHEMA/specs |

### Migration steps

**PR0 only:**

1. Add `offscreen_vore` / `offscreen_digest` to `EntityDefinition` and loader (parameterized parser + `_DEPRECATED_OFFSCREEN_KEYS` fail-hard check).
2. Move wolf/shark JSON: nest **existing OV arrays only** under `"OV"` keys — **no** CV/AV placeholders in PR0.
3. Remove six flat attributes and trait entries.
4. Simplify `NarrativeIndex.from_registry()` loop.
5. Update tests and `data/SCHEMA.md` (see PR0 test tasks below).

**PR1 only:**

6. Add CV/AV placeholder lines to wolf/shark `offscreen_vore` and `offscreen_digest` objects.

### Semantic shifts (call out for implementers)

| Layer | Flat fields (today) | Object fields (target) |
|-------|---------------------|------------------------|
| Top-level `[]` on flat key | `None` (no lines) | N/A — flat keys rejected |
| Present type key with `[]` | N/A | `EntityLoadError` |
| Missing type key in object | N/A | Runtime silent (no log for that type) |

### No gameplay behavior change for OV (PR0)

Wolf/shark OV off-screen lines remain the same strings after nesting; only JSON shape changes. CV/AV off-screen silence persists until PR1 content lands.

---

## Content requirements

### Evil vore-capable species (wolf, shark)

For each narrative type **T** present in the entity's `vore_narratives` (stock: OV, CV, AV):

| Surface | Required for ship? | Fallback | Notes |
|---------|-------------------|----------|-------|
| `npc_vore_hit[T]` | Recommended | Global hit pool | Already present (placeholder) |
| `npc_vore_miss[T]` | Recommended | Global miss pool | Already present (placeholder) |
| `digestion_complete[T]` | Recommended | Global digest pool | Already present |
| `offscreen_vore[T]` | **Yes** | None | OV exists; **CV/AV missing — must add** |
| `offscreen_digest[T]` | **Yes** | None | OV exists; **CV/AV missing — must add** |

Placeholder tone: atmospheric; may omit `{predator}`/`{prey}`. Author replaces with final copy later (user-confirmed).

- **Wolf:** dungeon/hall ambience (echoes, muffled sounds, distant rumbles).
- **Shark:** aquatic/flooded-hall ambience (splashes, currents, rolls beneath the surface) — distinct from wolf copy.

### Good / neutral entities

No requirement. Fields ignored at runtime for NPC vore/digestion logging.

### Future species

When adding a new evil vore-capable entity, define all five log surfaces for each enabled type, or accept silent off-screen behavior for missing types.

---

## Tests and spec updates

### PR0 test tasks (`tests/test_offscreen_vore_data.py` and related)

| Task | Detail |
|------|--------|
| Replace `test_loader_parses_offscreen_fields` | Assert `offscreen_vore` / `offscreen_digest` **objects** on `EntityDefinition`, not six flat attrs |
| Replace `test_loader_treats_empty_offscreen_array_as_none` | With `test_loader_rejects_empty_offscreen_vore_type_array` — `offscreen_vore: { "OV": [] }` → `EntityLoadError` |
| Replace `test_loader_rejects_invalid_offscreen_type` | With `test_loader_rejects_invalid_offscreen_vore_shape` — e.g. `offscreen_vore: "nope"` or invalid entry type → `EntityLoadError` naming `offscreen_vore` (not deprecated `offscreen_ov` string-array message) |
| Add `test_loader_rejects_deprecated_flat_offscreen_keys` | e.g. `offscreen_ov` present → error names `offscreen_vore` migration target |
| Add `test_loader_parses_offscreen_vore_object` | Object-field parse + `NarrativeIndex` lookup; **subsumes** `test_narrative_index_picks_offscreen_lines` (remove or merge) |
| Parameterized error strings | Assert `offscreen_vore.CV` appears in error text, not `digestion_complete` |

`tests/test_offscreen_vore_messages.py` and `tests/test_offscreen_digest_messages.py`: OV integration tests unchanged in PR0; silence tests still patch `CV` (wolf lacks CV until PR1).

### PR1 test tasks

| Task | Detail |
|------|--------|
| Add positive tests | `test_offscreen_vore_hit_cv_logs`, `test_offscreen_vore_hit_av_logs`; CV/AV digest off-screen cases |
| **Rewrite** `test_offscreen_vore_hit_silent_when_array_missing` | After wolf gains `offscreen_vore.CV`, patch an **absent** type (e.g. `"XX"`) or use a minimal test entity with only `OV` — preserves "missing type → silent" without conflicting with new CV content |
| **Rewrite** `test_offscreen_digest_silent_when_array_missing` | Same pattern for digest |
| Extend `test_load_default_entities_json` | Assert wolf/shark `offscreen_vore` / `offscreen_digest` are objects; every key in `vore_narratives` has matching off-screen type keys (enforces K7 on stock data) |

### PR2 test tasks

| Task | Detail |
|------|--------|
| Re-run `tests/test_enhancements_3.py` NPC vore tests | `test_npc_vore_miss_log`, `test_npc_vore_hit_engulfs_without_modal` — fix **only** if PR1 entity string edits change expected log substrings; both pass today |

### Spec deltas (PR2)

Replace flat key references in:

- `openspec/specs/vore/spec.md` — Requirement: Offscreen NPC Vore Hit Messages; note flat keys are **invalid** (not merely undocumented)
- `openspec/specs/digestion/spec.md` — Requirement: Offscreen NPC Digestion Complete Messages
- `openspec/specs/npc-data/spec.md` — Requirement: Vore narratives from data
- `openspec/specs/enhancements-3/spec.md` — NPC Vore (Log Only) technical notes

Add explicit cross-reference that on-screen `npc_vore_hit` / `npc_vore_miss` are normative in `vore` + `enhancements-3` (already stated; consolidate wording).

---

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| K1 | **Migrate** off-screen from six flat fields to `offscreen_vore` and `offscreen_digest` objects | User preference; matches majority entity narrative pattern; only two entities affected; removes `NarrativeIndex` field-mapping indirection. |
| K2 | **Reject** deprecated flat keys at load time via `_DEPRECATED_OFFSCREEN_KEYS` (no dual-read, no warn-only) | Only wolf/shark ever shipped flat keys; stock JSON migrates in PR0; warn-only would silently drop stale mod data. **Distinct from Q1:** missing type keys inside valid objects are a separate, softer problem (runtime silent; stock-data test enforcement — see Q1 resolution). |
| K3 | On-screen schema stays `npc_vore_hit` / `npc_vore_miss` objects (already shipped) | Matches `digestion_complete`; entity-first with global pool fallback is acceptable. |
| K4 | Off-screen misses remain **silent** | User-confirmed; atmospheric hits only. |
| K5 | Off-screen arrays have **no** global fallback | Preserves species-specific distant flavor; missing type = silent (tested today for CV on wolf). |
| K6 | Player `vore_narratives` / `digestion_player_modal` remain independent | User-confirmed; NPC logs are scrolling log only. |
| K7 | Wolf/shark must ship **all enabled types** for off-screen vore + digest | Closes user-identified gap; placeholders until author writes final copy. |
| K8 | Visibility gate: predator **or** prey in player FOV | Existing project convention; unchanged. |

*Terminology (defeated / stunned / digested) follows `openspec/config.yaml` and `openspec/WORKFLOW.md` — project-wide, not change-specific.*

---

## Resolved decisions

| # | Topic | Resolution |
|---|-------|------------|
| R1 | Object vs flat off-screen shape | **Objects** keyed by OV/CV/AV |
| R2 | Include `npc_vore_miss` for visible attempts? | **Yes**; off-screen misses out of scope |
| R3 | Fallback for on-screen entity miss? | **Yes** — `NPC_VORE_MISS_POOL` / `NPC_VORE_HIT_POOL` when entity data absent |
| R4 | Fallback for off-screen? | **No** |
| R5 | Naming alignment | Typed objects like `digestion_complete`, not `offscreen_ov` style |
| R6 | Content quality | Current wolf/shark lines are **placeholders** |
| R7 | Independence from player modals | **Confirmed** separate surfaces |
| R8 | Off-screen failed vore | **Silent** |
| R9 | FOV gating | NPC log visibility gated on player FOV (project convention) |

---

## Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should loader validate that every `vore_narratives` type has matching `offscreen_vore` / `offscreen_digest` keys? | **Deferred to follow-up change.** K7 is enforced on **stock data** via `test_load_default_entities_json` extension in PR1 (wolf/shark must have every `vore_narratives` key in both off-screen objects). Custom/mod entities are not blocked at load — missing type keys remain runtime-silent. Warn-only loader validation may be added later without contradicting K2's fail-hard rule for deprecated flat keys. |
| Q2 | Rename `_parse_digestion_lines` → `_parse_narrative_type_lines`? | Cosmetic; optional in PR2 cleanup. PR0 **must** add `field_name` parameter regardless of rename. |
| Q3 | Global off-screen fallback pools in a future modding pass? | Out of scope; user rejected for now. |

---

## PR Plan

One PR at a time per `openspec/WORKFLOW.md`. Targeted tests per PR; full `pytest tests/` on final acceptance PR only.

### PR0 — Off-screen schema migration (flat → object)

**Depends on:** none (design approved)

**Scope:** Data layer + JSON reshape; **no** new gameplay lines beyond re-nesting existing OV strings; **no** CV/AV content (deferred to PR1).

| File | Action |
|------|--------|
| `src/data/entity_registry.py` | Replace six flat attrs with `offscreen_vore`, `offscreen_digest` |
| `src/data/entity_loader.py` | Parameterize `_parse_digestion_lines(..., field_name)`; add `_DEPRECATED_OFFSCREEN_KEYS` fail-hard check before `_scan_unknown_traits()`; parse new object keys; remove flat traits |
| `src/data/narrative_index.py` | Read object fields directly |
| `data/entities.json` | Wolf/shark: nest `offscreen_vore.OV`, `offscreen_digest.OV` from current flat arrays only |
| `data/SCHEMA.md` | Document unified four-field NPC log schema; flat keys invalid |
| `tests/test_offscreen_vore_data.py` | Replace flat-field tests with object-field tests; `test_loader_rejects_deprecated_flat_offscreen_keys`; `test_loader_rejects_empty_offscreen_vore_type_array`; parameterized error-string assertions |
| `tests/test_offscreen_vore_messages.py` | OV integration unchanged; silence tests still use CV patch (valid until PR1) |
| `tests/test_offscreen_digest_messages.py` | Same as vore messages |

**Manual checklist:** Off-screen OV wolf hit and digest still log same atmospheric lines; on-screen wolf hit/miss unchanged; CV off-screen still silent (expected until PR1).

---

### PR1 — Off-screen CV/AV content + type coverage tests

**Depends on:** PR0

**Scope:** **Content-only PR — no runtime file changes** (`vore.py`, `digestion.py`, `narrative_index.py` pickers unchanged). Placeholder content + tests proving CV/AV off-screen paths log.

| File | Action |
|------|--------|
| `data/entities.json` | Add `offscreen_vore.CV/AV`, `offscreen_digest.CV/AV` for wolf (dungeon tone) and shark (aquatic tone) |
| `tests/test_offscreen_vore_messages.py` | Add `test_offscreen_vore_hit_cv_logs`, `test_offscreen_vore_hit_av_logs`; **rewrite** `test_offscreen_vore_hit_silent_when_array_missing` to patch absent type (`"XX"`) or minimal entity |
| `tests/test_offscreen_digest_messages.py` | CV/AV digest off-screen positive tests; **rewrite** `test_offscreen_digest_silent_when_array_missing` |
| `tests/test_load_default_entities_json` (or equivalent) | Assert wolf/shark off-screen objects contain every `vore_narratives` type key |
| `openspec/changes/add-npc-vore-message-logs/testing-checklist-pr1.md` | Create |

**Manual checklist:** Off-screen wolf CV vore → dungeon crushing atmospheric line; shark CV/AV → aquatic placeholders; wolf AV digest → compression line; OV regression; verify shark lines differ in tone from wolf.

---

### PR2 — Spec consolidation, cleanup, acceptance

**Depends on:** PR1

**Scope:** Normative spec updates, dead code removal, change archive, design artifact reconciliation.

| File | Action |
|------|--------|
| `openspec/changes/add-npc-vore-message-logs/design.md` | Copy/link this consolidated design; include **"On-screen NPC vore logs — shipped before this change; documented here for authority"** subsection under Problem / Current implementation |
| `openspec/specs/vore/spec.md` | `offscreen_vore` object wording; flat keys invalid |
| `openspec/specs/digestion/spec.md` | `offscreen_digest` object wording |
| `openspec/specs/npc-data/spec.md` | Unified NPC log field list |
| `openspec/specs/enhancements-3/spec.md` | Technical notes alignment |
| `src/systems/vore.py` | Remove unused `pick_npc_vore_message()` |
| `src/data/entity_loader.py` | Optional `_parse_digestion_lines` → `_parse_narrative_type_lines` rename (Q2 cleanup) |
| `openspec/changes/archive/2026-07-02-add-offscreen-vore-messages/` | Add supersession note pointing to `add-npc-vore-message-logs` object schema |
| `openspec/changes/add-npc-vore-message-logs/` | `acceptance-report.md`, archive to `openspec/changes/archive/2026-07-02-add-npc-vore-message-logs/` |
| `openspec/changes/add-npc-vore-message-logs/testing-checklist-pr2.md` | Create |
| `tests/test_enhancements_3.py` | Re-run NPC vore tests; fix only if entity string edits broke expected substrings |

**Manual checklist:** Full NPC vore log matrix (visible hit/miss, off-screen hit silent miss, off-screen digest all types); player vore modal still uses `vore_narratives`; re-run `test_npc_vore_miss_log` and `test_npc_vore_hit_engulfs_without_modal` — both should pass without changes unless PR1 copy edits affected assertions.

---

## Files reference (full system)

| Layer | Files |
|-------|-------|
| Data | `data/entities.json`, `data/SCHEMA.md` |
| Load | `src/data/entity_loader.py`, `src/data/entity_registry.py` |
| Index | `src/data/narrative_index.py` |
| Runtime | `src/systems/vore.py`, `src/systems/digestion.py` |
| Fallback pools | `src/vore_npc_content.py`, digestion pool in `digestion.py` |
| Tests | `tests/test_offscreen_vore_data.py`, `tests/test_offscreen_vore_messages.py`, `tests/test_offscreen_digest_messages.py`, `tests/test_enhancements_3.py` |
| Specs | `vore`, `digestion`, `npc-data`, `enhancements-3` |
| Prior art | `openspec/changes/archive/2026-07-02-add-offscreen-vore-messages/` (superseded off-screen shape) |

---

## Draft change artifacts

The following sections are suitable to copy into `openspec/changes/add-npc-vore-message-logs/` when implementation begins.

### Draft `proposal.md`

```markdown
# Proposal: NPC Vore Message Logs (Consolidated)

## Why

NPC-on-NPC vore logging was partially implemented ahead of design. Off-screen logging shipped with six flat JSON fields that diverge from the dominant typed-object pattern. Wolf and shark lack CV/AV off-screen content, so those events are silent.

## What

- Consolidated design for all NPC vore **log** surfaces (on-screen hit/miss, off-screen hit, off-screen digest)
- Migrate `offscreen_ov` … `offscreen_av_digest` → `offscreen_vore` and `offscreen_digest` objects keyed by OV/CV/AV
- Add placeholder CV/AV off-screen lines for wolf and shark
- Update specs and SCHEMA to match
- Remove dead `pick_npc_vore_message()` helper

## Out of scope

- Player `vore_narratives` modals and `digestion_player_modal`
- Off-screen failed vore messages
- Global fallback pools for off-screen events
- New evil species beyond content updates to wolf/shark

## Spec targets

`openspec/specs/vore/spec.md`, `digestion/spec.md`, `npc-data/spec.md`, `enhancements-3/spec.md` (PR2)
```

### Draft `tasks.md`

```markdown
# Tasks: add-npc-vore-message-logs

- [ ] PR0 — Off-screen schema migration (`offscreen_vore` / `offscreen_digest` objects; parameterized parser; `_DEPRECATED_OFFSCREEN_KEYS` fail-hard; index; wolf/shark OV nest only; test migrations; SCHEMA)
- [ ] PR1 — Off-screen CV/AV placeholder content (wolf/shark, content-only) + type coverage tests + rewrite silence tests + `test_load_default_entities_json` K7 assertions
- [ ] PR2 — Spec consolidation (flat keys invalid), design.md artifact, archive supersession note, remove `pick_npc_vore_message`, acceptance + archive
```

---

## Appendix: As-implemented vs target diff

| Surface | Shipped? | Schema today | Schema target |
|---------|----------|--------------|---------------|
| Visible vore hit | Yes | `npc_vore_hit` object | unchanged |
| Visible vore miss | Yes | `npc_vore_miss` object | unchanged |
| Off-screen vore hit | Yes | flat `offscreen_{type}` | `offscreen_vore` object |
| Off-screen digest | Yes | flat `offscreen_{type}_digest` | `offscreen_digest` object |
| Visible digest | Yes | `digestion_complete` object | unchanged |
| Wolf/shark off-screen OV | Yes | present | nested under object |
| Wolf/shark off-screen CV/AV | **No** | absent | **add placeholders** |