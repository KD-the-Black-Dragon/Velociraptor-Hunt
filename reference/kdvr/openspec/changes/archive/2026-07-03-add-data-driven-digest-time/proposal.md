# Proposal: Data-Driven Digest Time

## Why

Digestion completion uses a **strike** phase after prey reach 0 HP: each digestion tick at 0 HP adds one strike; when strikes reach the threshold, prey are **digested**. Today that threshold is **hardcoded to 3** for every evil predator (`strikes.count >= 3` in `src/systems/digestion.py`). `digestion_damage_per_tick` is already per-entity in `entities.json`, but **digest duration is not** — wolves, sharks, and future dragons all behave identically in the strike phase.

Playtesting needs per-species pacing: fast predators (dragon = 1 strike), standard (wolf = 3), slow (shark = 10) without code changes.

## What Changes

- Add optional **`digest_time`** to `entities.json` (evil entities): integer ≥ 1 = number of **0-HP digestion ticks** (strikes) before digest completes.
- Evil alignment default **`digest_time` = 6** when the field is omitted or null; JSON omits the field when the value would be 6.
- Extend **`DigestionStats`** on spawned evil entities with `digest_time` resolved at spawn (same pattern as `damage_per_tick`).
- Replace hardcoded `>= 3` checks in NPC and player digestion ticks with `>= stats.digest_time`.
- Update **`openspec/specs/digestion/spec.md`**, **`data/SCHEMA.md`**, and tests to assert **mechanics** via fixtures — not fixed balance values from live `data/`.

## Out of Scope

- Changing the HP-damage phase (`digestion_damage_per_tick`) or strike-vs-HP tick rules.
- Per-prey or per-narrative-type digest time (always per **predator** entity).
- Mid-engulf mutation of digest time (buffs/debuffs) — v1 reads predator `DigestionStats` at tick time, same as damage.
- UI progress indicator for strikes (e.g. "2/10") — strike count stays internal unless added later.

## Capabilities

### Modified

- **`digestion`** — strike threshold data-driven per predator species.
- **`npc-data`** — new optional entity field; loader validation.

## Impact (anticipated)

| Area | Files |
|------|--------|
| Components | `src/components.py` — `DigestionStats.digest_time` |
| Alignment / spawn | `src/data/alignment_profiles.py`, `src/spawn.py` |
| Entity data | `src/data/entity_loader.py`, `src/data/entity_registry.py` |
| Digestion logic | `src/systems/digestion.py` |
| Content | `data/entities.json`, `data/SCHEMA.md` |
| Tests | `tests/digest_test_helpers.py` (new), `tests/test_digestion.py` |
| Specs | `openspec/specs/digestion/spec.md` |

## Success Criteria

- Scenarios in updated `digestion/spec.md` pass with fixture-backed tests.
- Omitting `digest_time` on evil entities keeps default **6** strikes.
- Setting `digest_time: 10` on a test predator requires 10 strike ticks at 0 HP before digest (NPC removal or player modal).
- Full `pytest tests/` green on acceptance PR.
- Manual checklist per PR.

## Design

`openspec/changes/add-data-driven-digest-time/design.md`