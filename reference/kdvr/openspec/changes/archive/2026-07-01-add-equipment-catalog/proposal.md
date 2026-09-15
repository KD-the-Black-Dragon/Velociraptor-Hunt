# Proposal: Equipment Catalog Expansion

## Why

The shipped item JSON files contain only **one weapon**, **one armor**, **one wand**, and **one potion**. Descent has little gear variety to discover. Players need a **depth-escalating catalog** with **overlapping tiers** and **sparse floors** — exciting finds, not clutter — without changing NPCs or inventory mechanics.

## What Changes

- **12 weapons**, **9 armors**, **5 wands**, **3 potions** (add greater / power healing)
- **Overlapping depth windows** — `spawn_min_depth` staggered so depths 2, 6, 7, 13, 14, 21 (and others) each introduce new entries; `spawn_max_depth` retires weak gear on deep floors
- **Low global weights** — equipment and wands at weight **1**; potions somewhat higher (3 / 2 / 1)
- **Floor placement cap** — `MAX_FLOOR_ITEM_PLACEMENTS` (default **5**) so large eligible pools do not litter the map
- **Bare hands** — `PLAYER_*` set to **1–2 damage**, **1.5 accuracy** (locked)
- **Starter loadout** — dagger in slot `a` (wielded), robes in slot `b` (worn) on new game
- **Armor visuals** — all armor glyph **`[`** (DCSS-style); tiers distinguished by **color** (leather brown, chain dark grey, plate light grey, indigestion suit pink)
- **Docs** — spec, SCHEMA, README

## Out of Scope

- NPC equipment or loot tables
- New wand/potion effects, armor `evade_bonus`, weapon abilities
- Identification, cursed items, shops, gold, crafting, repair
- Perfect numeric tuning (playtest adjusts JSON)

## Capabilities

### New

- `equipment-catalog` — stock item list, spawn overlap/rotation, rarity policy

### Modified

- `inventory-items` — stock catalog reference; unarmed baseline; spawn cap note
- `dungeon` — depth exposes wider overlapping pool (placement still capped)

## Success Criteria

- All catalog entries load; comparative ordering holds
- Each depth 1–14 and 21 introduces at least one new `spawn_min_depth` tier
- Typical floor has ≤5 weighted item placements (+ health `spawn_min` when applicable)
- Full `pytest tests/` green

## Decisions (locked for v1)

| # | Decision |
|---|----------|
| 1 | JSON item definitions + small spawn cap + unarmed constants |
| 2 | All wands `magic_missile`; all potions `heal` |
| 3 | All armor glyph `[`; color by tier |
| 4 | Unarmed: **1–2 dmg**, **1.5 acc** |
| 5 | Equipment/wand weight **1**; potions **3/2/1**; **max 5** floor placements |
| 6 | Keep existing ids for dagger, leather_armor, health_potion, wand_of_magic_missile |
| 7 | Indigestion suit: ~0 AC, high digestion; pink `[` |