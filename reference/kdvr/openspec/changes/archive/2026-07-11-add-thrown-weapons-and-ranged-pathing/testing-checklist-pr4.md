# Manual checklist — PR4 Path projectile animation

Run: `python -m src.main`

## Test enemies (PR3 assignments)

| Species | Ability | Type | Log |
|---------|---------|------|-----|
| **wolf** | `Range6` | Path | *shoots* |
| **slime** | `Smite3` | Smite | *smites* (no projectile — Smite only) |

Bat and cave rat no longer carry ranged abilities (Erratic + ranged is as-designed incompatible).

## Happy path

- [ ] Wolf shoots at distance 2–6: **cyan `*`** starts on the wolf, steps along each beam tile, ends on you (in FOV)
- [ ] Animation does not block turns beyond a brief cosmetic pause (same world state after it ends)
- [ ] Off-screen wolf shot: no projectile drawn (FOV-gated)

## Regression

- [ ] Slime smite still works with no beam animation
- [ ] Melee, movement, vore unchanged
- [ ] Rest animation still works

Automated: `python -m pytest tests/test_projectile_anim.py tests/test_npc_abilities_range_path.py -v`