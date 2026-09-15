# Acceptance Report: add-potion-effects

**Date:** 2026-07-09  
**Scope:** Generalized potion effects beyond heal — discovery, blink, delayed teleport, haste, might, alliance, antacid; PlayerEffects infrastructure; status corner; save/load.

## Automated verification

### Change-scoped

```bash
python -m pytest tests/test_player_effects_pr1.py tests/test_potion_effects_pr2.py tests/test_potion_teleport_pr3.py tests/test_potion_blink_pr4.py tests/test_potion_summon_pr5.py -v
```

| Result | Detail |
|--------|--------|
| **PASS** | Effects, tick/haste 2:1, teleport escape, blink targeting, summon ally |

### Full suite

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed (first run) | 1354 |
| Failed (first run) | 1 |
| Skipped | 2 |
| Duration | ~10m 7s |

**First-run failure (re-run only):**

| Test | Re-run | Notes |
|------|--------|--------|
| `test_player_engulfed_blocks_introduction` | **PASS** | Flake (`StopIteration`); unrelated to potions |

After re-run of the single failure: **PASS**.

## Manual verification

Designer signed off PR1–PR6 playtests (2026-07-09), including haste 2:1, antacid wording, blink invalid messages, summon “A dog knight…”, and stock catalog feel.

## Live specs / data

| Artifact | Notes |
|----------|--------|
| `openspec/specs/inventory-items/spec.md` | Potion effect list |
| `openspec/specs/equipment-catalog/spec.md` | 10 stock potions |
| `data/SCHEMA.md` | Potion effect fields |
| `data/potions.json` | Full stock catalog |

## Stock potions

| id | effect |
|----|--------|
| healing / greater / power | heal |
| potion_of_discovery | magic_mapping |
| potion_of_blinking | blink |
| potion_of_teleportation | teleport_delay |
| potion_of_haste | haste (20 turns, 2:1) |
| potion_of_might | might |
| potion_of_alliance | summon_ally |
| potion_of_antacid | digestion_ward |

TEMP playtest starter potions removed on acceptance.
