# Acceptance Report: add-data-driven-digest-time

**Date:** 2026-07-03  
**Scope:** Per-entity `digest_time` in `entities.json`; strike threshold data-driven per predator

## Automated verification

### Targeted gate (change tests)

```bash
python -m pytest tests/test_digestion.py tests/test_npc_data_pr1.py tests/test_npc_data_pr3.py tests/digest_test_helpers.py -q
```

| Area | Tests | Result |
|------|-------|--------|
| Digestion mechanics (PR0) | `test_digestion.py` | PASS |
| Entity load + alignment | `test_npc_data_pr1.py` | PASS |
| Spawn integration | `test_npc_data_pr3.py` | PASS |

### Full suite

Skipped per user request (targeted gate sufficient for this change).

| Run | Result |
|-----|--------|
| Targeted gate (PR0) | 84 passed |
| Full suite | Skipped |

## Manual verification

- [x] PR0 playtest — default 6 strikes at 0 HP
- [x] PR1 playtest — wolf 3, shark 10 per `testing-checklist-pr1.md` (user sign-off 2026-07-03)

## Requirement coverage

| Requirement | Verified by |
|-------------|-------------|
| `digest_time` per evil entity | `entities.json`, `test_load_default_entities_json` |
| Default 6 when omitted | `test_digest_time_default_when_omitted` |
| Custom N strikes | `test_custom_digest_time_requires_n_strikes` |
| Good entity load error | `test_digest_time_load_error_on_good_entity` |
| NPC + player tick threshold | `test_digest_time_strikes_digests_npc`, player strike cadence tests |
| Spec | `openspec/specs/digestion/spec.md`, `openspec/specs/npc-data/spec.md` |

## Content shipped (PR1)

| Entity | `digest_time` |
|--------|---------------|
| wolf | 3 |
| shark | 10 |
| other evil (future) | omit → 6 |