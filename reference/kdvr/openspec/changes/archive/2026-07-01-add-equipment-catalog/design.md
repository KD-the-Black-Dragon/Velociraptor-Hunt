# Design: Equipment Catalog Expansion

| Field | Value |
|-------|-------|
| **Status** | Draft (2026-07-01, revised) |
| **Change** | `openspec/changes/add-equipment-catalog/` |
| **Spec target** | `openspec/specs/equipment-catalog/spec.md` |

---

## Overview

Populate equipment and potion JSON with a **tier skeleton**. Spawn uses existing `spawn_weight` + `spawn_min_depth` / `spawn_max_depth` filtering (`src/spawn.py`). Wands keep `effect: "magic_missile"`. Potions keep `effect: "heal"`.

**Design goals:**

- **Overlap** — many tiers eligible at once; new `spawn_min_depth` on **every** depth band (no “dead” depths like 2, 6, 7, 13, 14, 21)
- **Rarity** — equipment exciting to find; potions more common but not spammed
- **Rotation** — low-tier gear uses `spawn_max_depth` so deep floors are not buried in daggers

**Code touches (small):**

1. Unarmed `PLAYER_*` in `constants.py` — **locked:** 1–2 damage, 1.5 accuracy
2. **`MAX_FLOOR_ITEM_PLACEMENTS`** cap in `spawn.py` — recommended; integer `spawn_weight` cannot go below 1, so a cap is the practical way to keep floors sparse when the eligible pool grows

---

## Unarmed baseline (locked)

| Stat | Value |
|------|-------|
| `PLAYER_ACCURACY` | 1.5 |
| `PLAYER_MIN_DAMAGE` | 1 |
| `PLAYER_MAX_DAMAGE` | 2 |

Clearly weaker than wielding a dagger. Implemented in PR 1.

---

## Spawn policy

### Weight tiers

| Category | `spawn_weight` | Notes |
|----------|----------------|-------|
| Weapons | **1** (all) | Very rare |
| Armor | **1** (all) | Very rare |
| Wands | **1** (all) | Very rare |
| Health potion | **3** | Most common consumable |
| Greater healing | **2** | |
| Power healing | **1** | Still above equipment odds per entry |

### Floor placement cap (recommended code)

```text
placements = min(MAX_FLOOR_ITEM_PLACEMENTS, len(pool), len(candidates))
```

**Proposed `MAX_FLOOR_ITEM_PLACEMENTS = 5`** in `constants.py`. Potion `spawn_min` guarantees (health on shallow floors) run **after** weighted placements, same as today — may add 0–1 extra potions beyond the cap.

### Overlap + rotation

- **`spawn_min_depth`** — when a tier **enters** the pool (stagger every 1–3 depths so each floor depth introduces something new)
- **`spawn_max_depth`** — when a tier **leaves** the pool (weak gear falls off on deep floors so the weighted pool stays small)
- High tiers: `spawn_max_depth: 1000` (always eligible once unlocked)

---

## Depth introduction map

Each depth **1–21** has at least one **new** `spawn_min_depth` unlock. Deeper depths rely on **overlap** (everything with `min ≤ depth ≤ max`).

| Depth | New unlocks (first appearance) |
|-------|--------------------------------|
| 1 | robes, leather armor, dagger, club, health potion, wand of magic missile |
| 2 | short sword, waxed hide armor |
| 3 | spear, wand of double missile, greater healing |
| 4 | mace |
| 5 | ringmail, broadsword |
| 6 | longsword, oiled ringmail, wand of power bolt |
| 7 | chainmail, battleaxe |
| 8 | power healing |
| 9 | greatsword |
| 10 | oiled chainmail |
| 11 | royal rapier |
| 12 | wand of ballista |
| 13 | giant's warhammer, plate armor |
| 14 | hero's blade, indigestion suit |
| 15 | *(overlap only — many mid/high tiers still eligible)* |
| 16–20 | *(overlap)* |
| 21 | wand of extermination |

Depths **15–20** intentionally have no exclusive “first” tier — the pool is already rich from overlap; cap keeps placement sparse.

---

## Comparative ordering (must hold)

### Weapons

| Order | `id` | display_name | Role |
|-------|------|--------------|------|
| — | *(unarmed)* | bare hands | Worse than dagger |
| 1 | `dagger` | dagger | Accuracy > club |
| 2 | `club` | club | Damage > dagger |
| 3 | `short_sword` | short sword | Balanced; beats dagger + club |
| 4 | `spear` | spear | Accuracy > mace |
| 5 | `mace` | mace | Damage > spear |
| 6 | `broadsword` | broadsword | Balanced; beats spear + mace |
| 7 | `longsword` | longsword | Accuracy > battleaxe |
| 8 | `battleaxe` | battleaxe | Damage > longsword |
| 9 | `greatsword` | greatsword | Balanced; beats longsword + battleaxe |
| 10 | `royal_rapier` | royal rapier | Ultimate accuracy |
| 11 | `heroes_blade` | hero's blade | Ultimate balanced |
| 12 | `giants_warhammer` | giant's warhammer | Ultimate damage |

### Armor

| Order | `id` | display_name | Notes |
|-------|------|--------------|-------|
| 1 | `robes` | robes | Weakest |
| 2 | `leather_armor` | leather armor | Existing id |
| 3 | `waxed_hide_armor` | waxed hide armor | AC < leather; digestion > leather |
| 4 | `ringmail` | ringmail | |
| 5 | `oiled_ringmail` | oiled ringmail | AC < ringmail; digestion > ringmail |
| 6 | `chainmail` | chainmail | |
| 7 | `oiled_chainmail` | oiled chainmail | AC < chainmail; digestion > chainmail |
| 8 | `plate_armor` | plate armor | Highest combat AC |
| 9 | `indigestion_suit` | indigestion suit | ~0 AC; extreme digestion |

### Wands

All `effect: "magic_missile"`. Escalating damage / range / charges.

| Order | `id` | display_name |
|-------|------|--------------|
| 1 | `wand_of_magic_missile` | wand of magic missile |
| 2 | `wand_of_double_missile` | wand of double missile |
| 3 | `wand_of_power_bolt` | wand of power bolt |
| 4 | `wand_of_ballista` | wand of ballista |
| 5 | `wand_of_extermination` | wand of extermination |

### Potions

All `effect: "heal"`. Escalating `heal_amount`.

| Order | `id` | display_name | heal_amount (draft) |
|-------|------|--------------|---------------------|
| 1 | `health_potion` | health potion | 10 (existing) |
| 2 | `greater_healing` | greater healing | 25 |
| 3 | `power_healing` | power healing | 50 |

---

## Visual policy

### Armor — DCSS-style

- **Glyph:** `[` for **all** armor (Dungeon Crawl Stone Soup convention)
- **Color** distinguishes tier; oiled/waxed variants **match** their plain tier color

| id | fg (RGB) | Notes |
|----|----------|-------|
| robes | `[200, 200, 200]` | Light grey |
| leather_armor | `[139, 90, 43]` | Brown (stock) |
| waxed_hide_armor | `[139, 90, 43]` | Same brown |
| ringmail | `[120, 120, 120]` | Medium grey |
| oiled_ringmail | `[120, 120, 120]` | Same |
| chainmail | `[80, 80, 80]` | Dark grey |
| oiled_chainmail | `[80, 80, 80]` | Same |
| plate_armor | `[180, 180, 180]` | Light grey |
| indigestion_suit | `[255, 105, 180]` | Pink (wild) |

### Potions

- **Glyph:** `!` for all (stock convention)
- **Color:** health magenta (stock), greater red, power gold — arbitrary but distinct

| id | fg (RGB) |
|----|----------|
| health_potion | `[220, 60, 220]` |
| greater_healing | `[200, 40, 40]` |
| power_healing | `[220, 180, 40]` |

### Weapons / wands

- Unique glyphs per weapon (visual variety on sparse drops)
- Wands keep `/` or tint variants — TBD in PR 3; stock wand uses `/`

---

## Draft stat tables

### Weapons

| id | min | max | acc_bonus | durability | glyph | min_d | max_d | wt |
|----|-----|-----|-----------|------------|-------|-------|-------|-----|
| dagger | 1 | 4 | +0.10 | 80 | `)` | 1 | 10 | 1 |
| club | 2 | 6 | +0.00 | 90 | `(` | 1 | 12 | 1 |
| short_sword | 3 | 6 | +0.12 | 100 | `/` | 2 | 18 | 1 |
| spear | 2 | 5 | +0.18 | 90 | `\|` | 3 | 22 | 1 |
| mace | 4 | 8 | +0.02 | 110 | `{` | 4 | 24 | 1 |
| broadsword | 4 | 8 | +0.14 | 120 | `}` | 5 | 28 | 1 |
| longsword | 3 | 7 | +0.22 | 130 | `=` | 6 | 32 | 1 |
| battleaxe | 5 | 10 | +0.04 | 140 | `+` | 7 | 34 | 1 |
| greatsword | 5 | 9 | +0.18 | 150 | `&` | 9 | 40 | 1 |
| royal_rapier | 2 | 6 | +0.35 | 120 | `'` | 11 | 1000 | 1 |
| heroes_blade | 6 | 11 | +0.25 | 160 | `"` | 14 | 1000 | 1 |
| giants_warhammer | 4 | 14 | +0.00 | 180 | `%` | 13 | 1000 | 1 |

### Armor

| id | ac | dig | durability | glyph | fg | min_d | max_d | wt |
|----|-----|-----|------------|-------|-----|-------|-------|-----|
| robes | 0 | 0 | 40 | `[` | 200,200,200 | 1 | 8 | 1 |
| leather_armor | 2 | 1 | 80 | `[` | 139,90,43 | 1 | 14 | 1 |
| waxed_hide_armor | 1 | 3 | 70 | `[` | 139,90,43 | 2 | 18 | 1 |
| ringmail | 4 | 1 | 100 | `[` | 120,120,120 | 5 | 24 | 1 |
| oiled_ringmail | 3 | 4 | 95 | `[` | 120,120,120 | 6 | 28 | 1 |
| chainmail | 6 | 2 | 130 | `[` | 80,80,80 | 7 | 34 | 1 |
| oiled_chainmail | 5 | 5 | 125 | `[` | 80,80,80 | 10 | 38 | 1 |
| plate_armor | 8 | 2 | 160 | `[` | 180,180,180 | 13 | 1000 | 1 |
| indigestion_suit | 0 | 8 | 100 | `[` | 255,105,180 | 14 | 1000 | 1 |

### Wands

| id | min | max | acc | range | ch_start | ch_max | min_d | max_d | wt |
|----|-----|-----|-----|-------|----------|--------|-------|-------|-----|
| wand_of_magic_missile | 2 | 6 | 1.00 | 5 | 3 | 5 | 1 | 14 | 1 |
| wand_of_double_missile | 3 | 8 | 1.00 | 5 | 3 | 5 | 3 | 22 | 1 |
| wand_of_power_bolt | 4 | 10 | 1.05 | 6 | 4 | 6 | 6 | 30 | 1 |
| wand_of_ballista | 6 | 12 | 1.10 | 6 | 4 | 6 | 12 | 40 | 1 |
| wand_of_extermination | 8 | 16 | 1.15 | 7 | 5 | 7 | 21 | 1000 | 1 |

### Potions

| id | heal | spawn_min | min_d | max_d | wt |
|----|------|-----------|-------|-------|-----|
| health_potion | 10 | 1 | 1 | 1000 | 3 |
| greater_healing | 25 | 0 | 3 | 1000 | 2 |
| power_healing | 50 | 0 | 8 | 1000 | 1 |

`spawn_min: 1` on health potion only — guarantees one health potion on eligible floors when placement tiles remain (existing behavior). Greater/power never forced.

---

## Eligible pool size examples (with rotation)

Approximate **pool weight sum** at key depths (before cap):

| Depth | Eligible entries (weight sum) | After cap 5 |
|-------|-------------------------------|-------------|
| 1 | ~6 equipment (6) + potion pool (3) ≈ 9 | 5 weighted + up to 1 spawn_min potion |
| 7 | ~10 equipment + 5 potion weights ≈ 15 | 5 + spawn_min |
| 14 | ~14 equipment + 6 potion ≈ 20 | 5 + spawn_min |
| 25 | ~12 endgame equipment + 6 potion ≈ 18 | 5 + spawn_min |

Equipment stays **exciting** because most floors place only **5** weighted drops from a large eligible set.

---

## JSON / code scope

| Change | Required? |
|--------|-----------|
| `weapons.json`, `armor.json`, `wands.json`, `potions.json` | Yes |
| `PLAYER_*` unarmed | Yes (PR 1) |
| `MAX_FLOOR_ITEM_PLACEMENTS` | **Yes** (PR 1) — rarity requirement |
| New item fields / wand effects | No |
| NPC changes | No |

---

## Resolved decisions

| # | Question | Resolution |
|---|----------|------------|
| 1 | Unarmed stats? | **1–2 dmg, 1.5 acc** |
| 2 | Armor glyphs? | **All `[`**, color by tier; indigestion suit **pink** |
| 3 | Floor clutter? | **Weight 1** equipment; potions 1–3; **`MAX_FLOOR_ITEM_PLACEMENTS = 5`** |
| 4 | Depth gaps? | **Staggered min_depth** through 21; **spawn_max_depth** rotates weak gear out |
| 5 | Potions? | **greater healing**, **power healing** added |
| 6 | Wand effects? | All `magic_missile` |
| 7 | PR split? | Weapons → armor → wands → potions → spec |
| 8 | Starter loadout? | **Dagger slot `a` wielded; robes slot `b` worn** on new game |

---

## PR plan

| PR | Scope |
|----|-------|
| 1 | `weapons.json`, unarmed constants, spawn placement cap, weapon tests |
| 2 | `armor.json` (`[` + colors), armor tests |
| 3 | `wands.json`, wand tests |
| 4 | `potions.json`, potion tests |
| 5 | `equipment-catalog` spec, SCHEMA, README, acceptance, archive |

---

## Testing notes

- Every depth 1–14 and 21 has at least one item with `spawn_min_depth == depth` (unit table test).
- At depth 7, `longsword` and `chainmail` eligible; `dagger` eligible only if `7 ≤ max_depth` (dagger max 10 — still overlaps).
- At depth 15, `dagger` rotated out (`max_depth 10`).
- Pool weight cap: spawned weighted count ≤ 5 on large maps.
- Ordering smoke: dagger acc > club; waxed hide ac < leather; heal tiers monotonic.