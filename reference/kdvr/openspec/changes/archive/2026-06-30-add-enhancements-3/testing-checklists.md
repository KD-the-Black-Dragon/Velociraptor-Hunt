# Enhancements 3 — Manual Testing Checklist

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/test_vore_ai.py tests/test_vore_engulfed.py tests/test_vore_render.py -q
python -m pytest tests/ -q
```

All tests should pass.

---

## Population and identity (PR 1)

- [ ] **6** red **`o`** wolves (evil)
- [ ] **5** cyan **`k`** knights (good)
- [ ] **6** grey **`r`** rabbits (neutral)
- [ ] **17** NPCs total on a new game
- [ ] Examine placeholders for wolf, knight, rabbit

## Stunned and regen (PR 2)

Use **F2** to weaken NPCs for faster tests.

- [ ] Knight/rabbit at 0 HP → **stunned**, not removed
- [ ] Wolf at 0 HP → **defeated** and removed
- [ ] Stunned knight regains 1 HP after 8 player waits → *"The knight is no longer stunned."* (when visible)
- [ ] Wolf regen slower (every 12 player turns)

## AI memory and exploration (PR 3)

- [ ] Wolves hunt knights/player; pursue neutrals as secondary
- [ ] Knights follow you when no evil visible; attack wolves on sight
- [ ] Rabbits flee wolves when HP > 0
- [ ] Stunned NPCs do not move voluntarily
- [ ] Off-screen NPC combat/regen messages **not** logged

## NPC swap (PR 4)

- [ ] Two knights or knight+rabbit bump → **swap**, no damage
- [ ] Two wolves bump → swap
- [ ] Wolf bumps knight → **attack**
- [ ] Knight does not swap onto player tile
- [ ] Player bump knight/rabbit → player swap (unchanged)

## NPC vore (PR 5)

- [ ] Wolf vores stunned knight/rabbit → **log line**, **no modal**
- [ ] Predator tile: wolf glyph on **dark red** background
- [ ] Engulfed prey glyph **never** shown
- [ ] Engulfed prey invisible to other AI targeting

## Rescue (PR 6)

- [ ] Defeat holding wolf → prey freed on adjacent tile
- [ ] *"The rabbit is freed from the wolf."* when visible
- [ ] Knight can rescue by defeating wolf

## Player vore regression

- [ ] Stunned player → wolf still opens **vore modal**
- [ ] Engulf, struggle, mercy, blind render unchanged

## Core regression

- [ ] Examine, **Ctrl+Q**, potions, wait/regen, **R**/**S**/**F2**
- [ ] Combat logs use species names; no *monster*

**Pass criteria:** All items behave per `openspec/specs/enhancements-3/spec.md`; pytest green.