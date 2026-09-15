# Design: Data-Driven Digest Time

## Current State

| Area | Today |
|------|--------|
| HP phase | `DigestionStats.damage_per_tick` from `entities.json` or evil default **3** |
| Strike phase | At prey `HP == 0`, each tick increments `DigestionStrikes.count` |
| Completion | Hardcoded `strikes.count >= 3` in `apply_digestion_tick` and `apply_player_digestion_tick` |
| Data | `digestion_damage_per_tick` per entity; **no** strike-threshold field |
| Spec | `openspec/specs/digestion/spec.md` documents "three strikes" as global constant |

Relevant code:

```311:311:src/systems/digestion.py
    if strikes.count >= 3:
```

```219:219:src/systems/digestion.py
    if strikes.count >= 3:
```

Spawn attaches only `damage_per_tick`:

```128:133:src/spawn.py
    digestion_damage = digestion_damage_for(
        definition.alignment,
        definition.digestion_damage_per_tick,
    )
    if digestion_damage is not None:
        entity.components[DigestionStats] = DigestionStats(damage_per_tick=digestion_damage)
```

## Goals

1. Per-evil-entity **`digest_time`** in `entities.json` controls how many **strike ticks at 0 HP** complete digestion.
2. Default **6** when omitted or null — faster predators (wolf **3**, shark **10**) set explicit values in JSON.
3. Same threshold for **NPC prey** and **player prey** held by that predator species.
4. Tests pin values via helpers; live `data/entities.json` balance is playtester's prerogative.

## Terminology

| Term | Meaning |
|------|---------|
| **Digest time** | Count of digestion ticks applied while prey `HP == 0` before digest completes. One tick → one strike. Not wall-clock seconds. |
| **Strike** | One `DigestionStrikes.count` increment at 0 HP (unchanged semantics). |
| **Digested** | Prey removed (NPC) or player game-over flow triggered — unchanged. |

Use defeated / stunned / digested — never kill / die / death.

## JSON Schema

### New field: `digest_time`

| Property | Type | Required | Applies to |
|----------|------|----------|------------|
| `digest_time` | int ≥ 1 | No (evil default 6) | Evil entities with digestion |

**Semantics:** After prey HP reaches 0, the holding predator must apply exactly `digest_time` digestion ticks (each adding one strike) before `complete_npc_digestion` or the player digestion modal opens.

**Examples (content tuning — not test assertions):**

```json
{ "id": "wolf",  "digest_time": 3 }
{ "id": "shark", "digest_time": 10 }
{ "id": "dragon", "digest_time": 1 }
```

### Validation (`entity_loader.py`)

| Input | Result |
|-------|--------|
| Field omitted or `null` on evil entity | OK — runtime default **6** via alignment profile |
| `digest_time: 1` | OK — digest on first 0-HP strike tick |
| `digest_time: 0` or negative | **Load error** |
| Non-integer | **Load error** |
| Present on good/neutral entity | **Load error** (digestion fields are evil-only, same as `digestion_damage_per_tick`) |

Document in `data/SCHEMA.md` alongside `digestion_damage_per_tick`.

## Runtime Model

### `DigestionStats` component (extended)

```python
@attrs.define(frozen=True)
class DigestionStats:
    damage_per_tick: int
    digest_time: int  # strikes required at 0 HP; default 6 for evil
```

Frozen dataclass stays immutable on the predator for the entity's lifetime.

### Alignment profile default

Extend `AlignmentProfile` in `alignment_profiles.py`:

```python
DEFAULT_DIGEST_TIME = 6

@attrs.define(frozen=True)
class AlignmentProfile:
    ...
    default_digest_time: int
```

Evil profile: `default_digest_time=6`. Good/neutral: `0` (unused — no `DigestionStats` attached).

### Resolution helper (mirror `digestion_damage_for`)

```python
def digest_time_for(entity_alignment: Alignment, explicit: int | None) -> int | None:
    """Return strike threshold for evil entities; None for non-evil."""
    profile = alignment_profile(entity_alignment)
    if not profile.digests:
        return None
    if explicit is not None:
        return explicit
    return profile.default_digest_time
```

### Spawn (`spawn.py`)

When attaching `DigestionStats`:

```python
digest_time = digest_time_for(definition.alignment, definition.digest_time)
entity.components[DigestionStats] = DigestionStats(
    damage_per_tick=digestion_damage,
    digest_time=digest_time,
)
```

### Tick algorithm change

In both `apply_digestion_tick` and `apply_player_digestion_tick`, replace:

```python
if strikes.count >= 3:
```

with:

```python
if strikes.count >= stats.digest_time:
```

All other tick rules unchanged:

- HP > 0 → damage only, no strike.
- HP == 0 → strike only, no HP change.
- Never HP→0 and +1 strike on the same tick.

### Why not snapshot on `Predator`?

`narrative_type` is snapshotted on engulf because player vore preferences can change mid-run. `digest_time` comes from predator entity data at spawn and is not user-configurable mid-engulf. Reading `predator.components[DigestionStats].digest_time` at tick time matches how `damage_per_tick` is read today. If future buffs/debuffs alter digest speed, we can add a snapshot or modifier then.

### `DigestionStrikes` component

Keep `count: int` with no max baked into the type. Effective range is `0 .. digest_time` before completion. Regen gate (`count >= 1`) unchanged.

## Spec Updates (`openspec/specs/digestion/spec.md`)

Replace global "three strikes" with:

- Prey optional `DigestionStrikes`; threshold = predator `DigestionStats.digest_time`.
- Evil spawns: `digest_time` from entity JSON or default **6**.
- Scenarios: parameterized examples (wolf explicit 3; shark explicit 10; generic evil default 6; custom predator with `digest_time: 5` needs 5 ticks).

Update Technical Constants table:

| Constant / field | Default | Meaning |
|------------------|---------|---------|
| `digest_time` (evil) | 6 | Strike ticks at 0 HP before digest |
| `DigestionStrikes.count` | 0..digest_time | Strikes at 0 HP |

## Test Policy

Per `tests/conftest.py`: mechanics tests **must not** assert fixed values from production `data/entities.json`.

### New: `tests/digest_test_helpers.py`

- `minimal_entity_with_digest(entity_id, *, digest_time=3, digestion_damage_per_tick=3)` — tmp_path JSON fragment or registry install pattern consistent with `item_test_helpers` / `rune_test_helpers`.
- `spawn_predator_with_digest_stats(world, *, digest_time, damage_per_tick=3)` — attaches `DigestionStats` directly for unit tests bypassing full spawn pipeline where appropriate.
- `run_strike_ticks_until_digest(...)` — helper loop for N ticks.

### Refactor `tests/test_digestion.py`

| Test | Change |
|------|--------|
| `test_wolf_spawn_has_digestion_stats` | Assert `digest_time` **present** on evil spawn; do not assert production balance values |
| `test_three_strikes_digests_npc` | Rename → `test_digest_time_strikes_digests_npc`; use predator with pinned `digest_time=3` |
| `test_player_digestion_strike_cadence` | Pin `digest_time=3` on wolf stats |
| `test_player_third_strike_opens_modal` | Pin `digest_time=3`; name can stay or generalize |
| New | `test_custom_digest_time_requires_n_strikes` — e.g. `digest_time=5` needs 5 ticks |
| New | `test_digest_time_default_when_omitted` — loader + spawn with minimal evil entity, no field → **6** |
| New | `test_digest_time_load_error_on_good_entity` — validation |

Production JSON smoke (optional, separate): `entities.json` parses and evil entries that define `digest_time` have int ≥ 1 — no fixed wolf/shark values.

## PR Plan

### PR0 — Mechanics and spec

**Title:** Data-driven digest time (loader, spawn, digestion ticks, tests)

**Files:**

- `src/components.py` — extend `DigestionStats`
- `src/data/alignment_profiles.py` — default + `digest_time_for`
- `src/data/entity_registry.py`, `src/data/entity_loader.py` — field parse/validate
- `src/spawn.py` — attach `digest_time`
- `src/systems/digestion.py` — threshold from stats
- `tests/digest_test_helpers.py` — new
- `tests/test_digestion.py` — fixture refactor + new cases
- `openspec/specs/digestion/spec.md` — behavioral requirements

**Dependencies:** none

**Description:** Wire `digest_time` end-to-end; replace hardcoded 3; tests use fixtures. Do **not** require production `entities.json` edits yet (default **6** applies to entities without the field).

### PR1 — Content, docs, acceptance

**Title:** Entity digest_time content and acceptance

**Files:**

- `data/entities.json` — wolf `"digest_time": 3`, shark `"digest_time": 10`; other evil entities omit (default 6)
- `data/SCHEMA.md` — document field
- `openspec/changes/add-data-driven-digest-time/testing-checklists.md`, `acceptance-report.md`
- Archive change to `openspec/changes/archive/YYYY-MM-DD-add-data-driven-digest-time/`

**Dependencies:** PR0

**Description:** Content tuning explicit in JSON; full `pytest tests/` on acceptance; manual playtest checklist.

## Manual Playtest Checklist (PR1)

- [ ] Engulf knight with wolf — digest still feels ~3 strike ticks at 0 HP (if wolf `digest_time: 3`).
- [ ] If shark `digest_time: 10` — engulfed prey lingers noticeably longer at 0 HP before removal.
- [ ] Player engulf + 0 HP — modal opens after predator's `digest_time` strikes, not early/late.
- [ ] Strike message *"You are being digested!!"* still only on 0-HP ticks.
- [ ] Rescue/release still clears strikes; regen still blocked at `strikes >= 1`.

Run: `python -m src.main`

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Field name **`digest_time`** | User-requested; reads as "how long this predator takes to digest" in strike ticks. |
| 2 | `digest_time` = strike count at 0 HP only | Preserves two-phase digestion (HP drain, then strikes); no change to damage phase. |
| 3 | Evil default **6** when omitted or null | Slower baseline digest; fast predators set explicit lower values. Omit in JSON when value is 6. |
| 4 | Minimum value **1** | `digest_time: 1` = digest on first 0-HP strike tick; `0` is invalid. |
| 5 | Store on `DigestionStats` at spawn | Consistent with `damage_per_tick`; single predator component for digestion. |
| 6 | Read live from predator `DigestionStats` at tick | No engulf-time snapshot needed in v1; matches damage lookup. |
| 7 | Good/neutral must not define field | Aligns with evil-only digestion fields; fail fast at load. |
| 8 | Tests use fixtures, not production JSON | User tunes `data/` freely during playtest. |

## Resolved Decisions (2026-07-03)

| # | Decision |
|---|----------|
| 1 | `digest_time` = strike ticks at **0 HP only**; HP damage phase unchanged. |
| 2 | Code default **6** when field omitted or `null`; omit in JSON when value would be 6. |
| 3 | No upper bound at load — any integer ≥ 1. |
| 4 | PR1 content: wolf **3**, shark **10** explicit; other evil entities rely on default 6. |
| 5 | Field name `digest_time` on evil entities only; good/neutral defining it is a load error. |