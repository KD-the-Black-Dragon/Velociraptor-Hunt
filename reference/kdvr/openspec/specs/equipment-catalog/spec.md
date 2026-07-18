# equipment-catalog Specification

## Purpose

**equipment-catalog** defines the **stock item tiers** shipped in JSON: weapons, armor, potions, and wands that escalate with **floor depth**. Gameplay mechanics (pickup, wield, wear, quaff, evoke) remain in `openspec/specs/inventory-items/spec.md`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- Stock entries in `data/weapons.json` (12), `armor.json` (9), `potions.json` (10), `wands.json` (5), `throwables.json` (9)
- Depth-gated spawn with **overlap** (`spawn_min_depth` / `spawn_max_depth`)
- **Rarity policy** — low weights, placement cap
- **Unarmed baseline** and **starter loadout** on new game
- Comparative ordering (accuracy/damage branches, AC/digestion tradeoffs, heal/wand tiers)

### Out of scope

- NPC equipment drops
- New item effects beyond those listed in `inventory-items` / `data/SCHEMA.md` potion and wand effect tables
- Perfect numeric balance (JSON tunable in playtest)

## Requirements

### Requirement: Unarmed baseline

Bare hands are **not** an item. Unarmed combat SHALL use `PLAYER_MIN_DAMAGE` **1**, `PLAYER_MAX_DAMAGE` **2**, `PLAYER_ACCURACY` **1.5** from `src/constants.py`. Any wielded weapon SHALL be a clear upgrade.

#### Scenario: Unarmed weaker than dagger

- GIVEN an unarmed player
- AND a dagger definition with higher max damage and accuracy bonus
- WHEN effective stats are compared
- THEN wielding the dagger improves combat output over bare hands

### Requirement: Starter loadout

On **new game**, the player SHALL begin with:

| Slot | Item | Equip |
|------|------|-------|
| `a` | `dagger` | wielded |
| `b` | `robes` | worn |
| `c` | `rock` × 5 | throwable stack |

Implemented via `apply_starter_loadout()` in `src/systems/inventory.py`. First empty pickup slot after start SHALL be `d`.

#### Scenario: New game inspect shows starter gear

- GIVEN a new game
- WHEN the player opens inventory inspect
- THEN slot `a` shows dagger (wielded)
- AND slot `b` shows robes (worn)
- AND slot `c` shows rock with quantity 5

### Requirement: Spawn rarity and placement cap

Floor item spawn SHALL:

1. Build a weighted pool from eligible definitions (`spawn_min_depth ≤ depth ≤ spawn_max_depth`, `int(spawn_weight)` entries each)
2. Place at most **`MAX_FLOOR_ITEM_PLACEMENTS`** (default **5**) weighted drops per floor generation
3. Apply potion `spawn_min` guarantees **after** weighted placement (health potion: `spawn_min: 1`)

**Weight policy (stock):**

| Category | `spawn_weight` |
|----------|----------------|
| Weapons | 1 each |
| Armor | 1 each |
| Wands | 1 each |
| Health potion | 4 |
| Greater healing | 2 |
| Power healing | 1 |
| Utility potions (discovery, blink, …) | 1–2 (see potion catalog) |
| Throwables | 1–4 (see throwable catalog) |

Weak tiers and early utility potions MAY use finite `spawn_max_depth` so they rotate out on deep floors.

#### Scenario: Weighted placements capped

- GIVEN a floor depth with a large eligible pool
- WHEN items are spawned
- THEN weighted placements do not exceed `MAX_FLOOR_ITEM_PLACEMENTS`

#### Scenario: Health potion guaranteed on depth 1

- GIVEN a new floor at depth 1
- WHEN items spawn
- THEN at least one `health_potion` appears when candidate tiles exist

### Requirement: Weapon catalog ordering

Stock weapons (weakest → strongest): dagger, club, short sword, spear, mace, broadsword, longsword, battleaxe, greatsword, royal rapier, hero's blade, giant's warhammer.

Branch rules:

- Dagger more accurate than club; club higher average damage than dagger
- Balanced tiers beat the previous accuracy/damage pair on **at least one** axis (damage or accuracy)
- Ultimates: royal rapier (accuracy), hero's blade (balanced), giant's warhammer (damage)

#### Scenario: Club outdamages dagger

- GIVEN stock JSON loaded
- WHEN average damage is compared
- THEN club average exceeds dagger average

### Requirement: Armor catalog ordering and visuals

Stock armor (weakest → strongest AC): robes, leather armor, waxed hide armor, ringmail, oiled ringmail, chainmail, oiled chainmail, plate armor, indigestion suit.

- **Glyph:** `[` for **all** armor (DCSS convention)
- **Color** distinguishes tier; oiled/waxed variants match their plain tier color
- **Tradeoff variants:** waxed hide, oiled ringmail, oiled chainmail have **lower** `ac_bonus` and **higher** `digestion_ac` than their plain counterpart
- **Indigestion suit:** ~0 `ac_bonus`, extreme `digestion_ac`, pink `[`

#### Scenario: Waxed hide trades AC for digestion

- GIVEN stock JSON loaded
- WHEN leather armor and waxed hide armor are compared
- THEN waxed hide has lower `ac_bonus` and higher `digestion_ac`

### Requirement: Wand catalog ordering

Stock wands (weakest → strongest): wand of magic missile, double missile, power bolt, ballista, extermination. All use `effect: "magic_missile"`. Glyph `/` with tiered purple `fg`. Average damage and accuracy SHALL increase monotonically across tiers.

#### Scenario: Extermination only on deep floors

- GIVEN floor depth 15
- WHEN the spawn pool is built
- THEN `wand_of_extermination` is not eligible
- AND at depth 22 it is eligible

### Requirement: Potion catalog ordering

Stock potions all use glyph `!`. Examine text is utilitarian and **number-free** (heal amounts live in data only).

| id | Role | Typical intro depth |
|----|------|---------------------|
| `healing_potion` | Heal 10; `spawn_min: 1`; weight 4 | 1 |
| `greater_healing` | Heal 25; weight 2 | 5 |
| `power_healing` | Heal 50; weight 1 | 10 |
| `potion_of_discovery` | Magic map | 1 (rotates out mid/deep) |
| `potion_of_blinking` | Targeted blink | 1 (rotates out mid/deep) |
| `potion_of_teleportation` | Delayed random teleport | 2 |
| `potion_of_haste` | Temporary Fast | 3 |
| `potion_of_might` | Temporary combat buff | 3 |
| `potion_of_alliance` | Summon good ally | 4 |
| `potion_of_antacid` | Digestion ward | 4 |

Only `healing_potion` has `spawn_min: 1`. Effect mechanics: `inventory-items` / SCHEMA.

#### Scenario: Greater healing from depth 5

- GIVEN floor depth 4
- WHEN the spawn pool is built
- THEN `greater_healing` is not eligible
- AND at depth 5 it is eligible

#### Scenario: Utility potions load with heals

- GIVEN stock `potions.json`
- WHEN the item registry loads
- THEN all ten potion ids above are present
- AND each non-heal effect parses without error

### Requirement: Throwable catalog ordering

Stock throwables (weakest → strongest by typical damage): rock, brick, dart, throwing knife, throwing axe, shuriken, javelin, chakram, ceramic pot.

| id | display_name | Typical intro depth | Role |
|----|--------------|---------------------|------|
| `rock` | rock | 1 | Starter + common blunt |
| `brick` | brick | 2 | Early blunt upgrade |
| `dart` | dart | 3 | Accurate, light |
| `throwing_knife` | throwing knife | 5 | Mid damage |
| `throwing_axe` | throwing axe | 6 | Heavy hit |
| `shuriken` | shuriken | 8 | High accuracy |
| `javelin` | javelin | 10 | High damage |
| `chakram` | chakram | 12 | Deep accuracy/damage |
| `ceramic_pot` | ceramic pot | 14 | Deep slow blunt |

Throwables are **consumed** on throw (`stack_count` decrements). No `range` field — player throws use full LoS per `ranged-targeting` spec. Rock uses light brown `.` glyph for floor visibility. Exact numbers JSON-tunable; tests use fixtures.

#### Scenario: Rock eligible on depth 1

- GIVEN floor depth 1
- WHEN the spawn pool is built
- THEN `rock` is eligible
- AND `ceramic_pot` is not eligible

#### Scenario: Javelin from depth 10

- GIVEN floor depth 9
- WHEN the spawn pool is built
- THEN `javelin` is not eligible
- AND at depth 10 it is eligible

### Requirement: Depth introduction coverage

Stock `spawn_min_depth` values SHALL ensure new item tiers appear across descent, including depths **1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 21** (combined across categories). Depths without exclusive unlocks rely on **overlap** from earlier tiers.

## Stock catalog counts

| File | Count |
|------|-------|
| `weapons.json` | 12 |
| `armor.json` | 9 |
| `potions.json` | 10 |
| `wands.json` | 5 |
| `throwables.json` | 9 |

Full stat tables and depth windows: `openspec/changes/archive/2026-07-01-add-equipment-catalog/design.md`.

## Related specs

| Spec | Relationship |
|------|----------------|
| `inventory-items/spec.md` | Pickup, equip, consume, evoke mechanics |
| `dungeon/spec.md` | `floor_depth` drives spawn eligibility |
| `digestion/spec.md` | Armor `digestion_ac` on player ticks |
| `core-roguelike/spec.md` | Player combat defaults |

## Acceptance Criteria

1. All stock catalog entries load without error.
2. New game starts with starter weapon wielded, starter armor worn, and 5 rocks in slot `c`.
3. Floors place ≤5 weighted items; potion `spawn_min` guarantees work when configured.
4. Depth overlap and `spawn_max_depth` rotation observable in play.
5. Throwable tiers escalate with depth; rock visible on floor at early depths.
6. Item **mechanics** tests (`test_inventory_items_pr*.py`, `test_throwables_pr*.py`) use isolated fixtures — not fixed stock JSON values. Full `pytest tests/` green.