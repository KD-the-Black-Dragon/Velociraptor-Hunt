# Acceptance Report: add-npc-abilities

**Date:** 2026-07-02  
**Scope:** `openspec/specs/npc-abilities/spec.md` and PR0–PR12 ability handlers

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 632 passed, 0 failed (2026-07-02)

| Area | Tests | Result |
|------|-------|--------|
| Framework + parser | `test_ability_parser.py`, `test_npc_data_pr1.py` | PASS |
| RangeN | `test_npc_abilities_rangen.py` | PASS |
| Summon | `test_npc_abilities_summon1.py`, `test_npc_abilities_summonn.py` | PASS |
| Coward / Supercoward | `test_npc_abilities_coward.py`, `test_npc_abilities_supercoward.py` | PASS |
| Erratic | `test_npc_abilities_erratic.py` | PASS |
| Slow / Fast | `test_npc_abilities_slow.py`, `test_npc_abilities_fast.py` | PASS |
| Knockback / Lifedrain | `test_npc_abilities_knockback.py`, `test_npc_abilities_lifedrain.py` | PASS |
| Vore turn order | `test_vore_turn_order.py` | PASS |
| Baseline evil AI | `test_enhancements_3.py` | PASS |
| Full suite | all `tests/` | PASS |

## Manual verification

- [x] User playtest sign-off across PR0–PR12
- [x] Per-PR manual checklists completed
- [x] Stock wolf reverted to `abilities: []`

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Ability load/spawn | `test_npc_data_pr1.py`, spawn helpers |
| RangeN engagement | `test_npc_abilities_rangen.py` |
| SummonN | `test_npc_abilities_summon1.py`, `test_npc_abilities_summonn.py` |
| Coward / Supercoward | `test_npc_abilities_coward.py`, `test_npc_abilities_supercoward.py` |
| Erratic triple-step | `test_npc_abilities_erratic.py` |
| Slow parity | `test_npc_abilities_slow.py` |
| Fast double-step + vore abort | `test_npc_abilities_fast.py`, `test_vore_turn_order.py` |
| Knockback | `test_npc_abilities_knockback.py` |
| Lifedrain | `test_npc_abilities_lifedrain.py` |
| Wolf baseline (no abilities) | `test_stock_wolf_has_no_abilities`, `test_npc_data_pr3.py` |

## Open Questions

All design-doc open questions resolved or deferred per `openspec/specs/npc-abilities/spec.md` table (wolf showcase bundle deferred — stock `[]`).

## Spec updates

- `openspec/specs/npc-abilities/spec.md` — live normative spec (new)
- `openspec/specs/npc-data/spec.md` — cross-link to npc-abilities
- `data/SCHEMA.md` — ability token reference table
- `data/entities.json` — wolf `abilities: []`

## Verdict

**add-npc-abilities: ACCEPTED**