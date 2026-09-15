# Design: Offscreen Vore Message Logs

**Change id:** `add-offscreen-vore-messages`  
**Status:** Draft for review  
**Depends on:** shipped vore v1 (`openspec/specs/vore/spec.md`), NPC vore (`try_resolve_npc_vore`), digestion (`complete_npc_digestion`)

---

## Summary

When an **evil** predator successfully vores or digests prey **outside the player's FOV**, the game SHALL emit a single atmospheric line to the scrolling message log — as if the player hears distant sounds in the dungeon. Lines come from **per-entity string arrays** in `data/entities.json`. On-screen events keep today's behavior (visible pools / modals); offscreen pools are never used when either combatant is visible.

**No log** for offscreen **failed** vore attempts.

---

## Motivation

NPC-on-NPC vore and digestion already resolve off-screen but are silent unless predator or prey is in FOV. That wastes modding surface and loses ambient dungeon feedback. Entity-authored offscreen lines give species-specific flavor without exposing full modal narratives.

---

## JSON schema (entities.json)

Six optional top-level fields per entity. Keys use **snake_case** (project convention); map from conceptual names:

| JSON key | User name | When used |
|----------|-----------|-----------|
| `offscreen_ov` | OffscreenOV | Successful NPC vore hit, narrative type OV, off-screen |
| `offscreen_cv` | OffscreenCV | Successful NPC vore hit, CV, off-screen |
| `offscreen_av` | OffscreenAV | Successful NPC vore hit, AV, off-screen |
| `offscreen_ov_digest` | OffscreenOVDigest | NPC digestion complete, OV, off-screen |
| `offscreen_cv_digest` | OffscreenCVDigest | NPC digestion complete, CV, off-screen |
| `offscreen_av_digest` | OffscreenAVDigest | NPC digestion complete, AV, off-screen |

Each value is a **non-empty string array** when present. Omitted key, `null`, or `[]` → no offscreen line for that event (graceful skip).

Example (wolf):

```json
"offscreen_ov": [
  "You hear a distant gulp echo through the halls.",
  "A muffled swallowing sound reaches you from far away."
],
"offscreen_ov_digest": [
  "A satisfied rumble echoes from somewhere in the dungeon."
]
```

### Placeholders

Same as existing digestion / NPC vore templates:

- `{predator}` — log name of predator (`entity_log_name`, sentence-start when template begins with `{predator}`)
- `{prey}` — log name of prey

Offscreen lines may omit placeholders (ambient-only) or include them for specificity.

### Loader rules

- Add keys to `_ENTITY_TRAITS` in `entity_loader.py`.
- Parser: `_parse_string_array_field(raw, entity_id, field_name)` — if key absent → `None`; if present must be `list[str]` with at least one non-empty string (or allow empty list → treat as no lines; **prefer**: empty array = no lines, no load error).
- **Optional on all alignments** — good/neutral may define fields; they are ignored at runtime (only evil predators trigger NPC vore/digestion).
- **Optional on evil** — missing field → silent offscreen (no fallback to global `NPC_VORE_HIT_POOL` or `DIGESTION_COMPLETE_POOL`).
- Invalid type → `EntityLoadError` (same strictness as `digestion_complete` value shape).

Store on `EntityDefinition` as `offscreen_ov: tuple[str, ...] | None`, etc.

---

## Runtime behavior

### Visibility gate (shared)

Reuse existing helper pattern:

```python
on_screen = (
    entity_visible_to_player(game_map, predator)
    or entity_visible_to_player(game_map, prey)
)
```

Offscreen path runs when `not on_screen`.

### Event 1 — Successful NPC vore hit

**Hook:** `try_resolve_npc_vore()` in `src/systems/vore.py` (after `hit` resolved, before `engulf_npc`).

| Condition | Message source |
|-----------|----------------|
| `hit` and `on_screen` | Unchanged: `NPC_VORE_HIT_POOL` via `pick_npc_vore_message` |
| `hit` and `not on_screen` | Random line from predator's `offscreen_{type}` array via narrative index |
| `not hit` | **No message** (on- or off-screen; visible miss still uses miss pool today — unchanged) |
| `hit` and offscreen array missing/empty | **No message** |

Only applies to **NPC vore** (`try_resolve_npc_vore`). Player-target vore uses modal (`try_open_vore_modal`) — unchanged.

### Event 2 — NPC digestion complete

**Hook:** `complete_npc_digestion()` in `src/systems/digestion.py`.

| Condition | Message source |
|-----------|----------------|
| `on_screen` | Unchanged: entity `digestion_complete` → fallback `DIGESTION_COMPLETE_POOL` |
| `not on_screen` | Random line from predator's `offscreen_{type}_digest` |
| offscreen digest array missing/empty | **No message** (no fallback to global pool off-screen) |

Player digestion modal / game over — unchanged (not offscreen log).

### Narrative index

Extend `NarrativeIndex` in `src/data/narrative_index.py`:

```python
offscreen_vore: dict[tuple[str, str], tuple[str, ...]]       # (entity_id, OV|CV|AV)
offscreen_digest: dict[tuple[str, str], tuple[str, ...]]   # (entity_id, OV|CV|AV)

def pick_offscreen_vore_line(entity_id, narrative_type, rng) -> str | None
def pick_offscreen_digest_line(entity_id, narrative_type, rng) -> str | None
```

Lookup key: `(entity_type_id(predator), narrative_type)`.

---

## Content policy

- **Evil species with vore** (wolf, shark): ship sample offscreen lines in PR2 for at least OV; CV/AV optional per species.
- **Good/neutral**: no requirement; unused if present.
- Terminology: defeated / stunned / digested — not kill/die/death.

---

## PR plan

| PR | Title | Scope |
|----|-------|-------|
| **PR0** | Data layer | `EntityDefinition` fields, loader, `NarrativeIndex` pickers, `data/SCHEMA.md`, unit tests for parse/lookup; **no gameplay wire** |
| **PR1** | Offscreen vore hit | `try_resolve_npc_vore` branch; tests: visible hit unchanged, offscreen hit logs entity line, offscreen miss silent, empty array silent |
| **PR2** | Offscreen digestion + content | `complete_npc_digestion` branch; wolf/shark sample arrays; `openspec/specs/vore/spec.md` delta; acceptance + archive |

Dependencies: PR1 → PR0; PR2 → PR1.

---

## Tests (targeted)

| Test | Assert |
|------|--------|
| Loader accepts six fields | Parsed tuples on `EntityDefinition` |
| Loader rejects non-string array | `EntityLoadError` |
| Offscreen vore hit | Predator/prey off-screen, hit → one log line from entity array |
| Offscreen vore miss | No log line |
| Offscreen digest | `complete_npc_digestion` off-screen → digest array line |
| Visible parity | On-screen still uses `NPC_VORE_HIT_POOL` / `digestion_complete` |
| Missing arrays | No crash, no log |
| `reset_narrative_index` | Tests isolated |

Harness: carve tiles, `isolate_other_ais`, place predator/prey outside player FOV, patch `resolve_vore_hit` → `True` where needed.

---

## Spec placement

- **`openspec/specs/vore/spec.md`** — offscreen successful NPC vore hit requirement
- **`openspec/specs/digestion/spec.md`** — offscreen NPC digestion complete requirement
- **`data/SCHEMA.md`** + **`data/Readme.txt`** — field reference

---

## Resolved decisions

| # | Decision |
|---|----------|
| 1 | JSON keys: snake_case (`offscreen_ov`, …) |
| 2 | No offscreen message on failed vore |
| 3 | No fallback to global pools when offscreen arrays empty |
| 4 | Visible events unchanged; offscreen arrays never used on-screen |
| 5 | Good/neutral may define fields; evil-only runtime |
| 6 | Player vore modal path unchanged |

## Open questions

| # | Question | Proposal |
|---|----------|----------|
| 1 | Should offscreen lines require `{predator}`/`{prey}`? | **No** — optional placeholders; ambient-only lines allowed |
| 2 | Shark water-only — same offscreen rules? | **Yes** — same FOV gate |

---

## Files touched (by PR)

| PR | Files |
|----|-------|
| PR0 | `entity_registry.py`, `entity_loader.py`, `narrative_index.py`, `data/SCHEMA.md`, `tests/test_offscreen_vore_data.py` |
| PR1 | `vore.py`, `tests/test_offscreen_vore_messages.py` |
| PR2 | `digestion.py`, `entities.json`, `tests/test_offscreen_digest_messages.py`, specs, archive |