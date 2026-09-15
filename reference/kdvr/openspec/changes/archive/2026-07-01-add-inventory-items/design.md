# Design: Inventory and Data-Driven Items

| Field | Value |
|-------|-------|
| **Status** | Draft (2026-07-01) |
| **Change** | `openspec/changes/add-inventory-items/` |
| **Spec target** | `openspec/specs/inventory-items/spec.md` |

---

## Overview

Wire the four item JSON files into gameplay. Replace the `ItemType` enum and global `a`–`z` “use slot” keys with **inventory instances** keyed by stable slot letters and **category commands** that open filtered modals.

Floor items are ECS entities with `Item` + `Renderable` + optional `ExamineDescription`, spawned from registries built at load time (same ignore-unknown pattern as NPC data).

---

## Inventory model

### Slot assignment

- 26 slots: `a` through `z`
- On pickup: assign **earliest free letter** (same order as today)
- Letter **does not change** while the item remains in inventory
- On drop: slot becomes empty; next pickup of any item may reuse that letter

### Slot contents

Each occupied slot stores an **item instance**:

| Field | Type | Notes |
|-------|------|-------|
| `item_id` | string | Registry key (`dagger`, `health_potion`, …) |
| `category` | enum | `weapon` \| `armor` \| `potion` \| `wand` |
| `durability` | int \| null | Weapons and armor only; starts at `durability_max` |
| `charges` | int \| null | Wands only; starts at `charges_start` from JSON |

Potions have neither durability nor charges.

### Equip state (player)

Separate from slots:

| Field | Type | Notes |
|-------|------|-------|
| `wielded_slot` | string \| null | Letter of wielded weapon, or null if unarmed |
| `worn_slot` | string \| null | Letter of worn armor, or null if unarmored |

Wield/wear references the **slot letter**, not a copy of the item. Dropping a wielded/worn item auto-clears that equip pointer.

---

## Item registries (load time)

Extend `src/data/item_loaders.py` (or sibling modules) to produce frozen definitions per category, keyed by `id`.

### Required fields (gameplay)

**Weapons:** `id`, `display_name`, `glyph`, `fg`, `examine`, `min_damage`, `max_damage`, `accuracy_bonus`, `durability_max`, `spawn_weight`, `spawn_min_depth`, `spawn_max_depth`

**Armor:** `id`, `display_name`, `glyph`, `fg`, `examine`, `ac_bonus`, `digestion_ac`, `durability_max`, `spawn_weight`, `spawn_min_depth`, `spawn_max_depth`

**Potions:** `id`, `display_name`, `glyph`, `fg`, `examine`, `effect`, `heal_amount`, `spawn_weight`, `spawn_min`, `spawn_min_depth`, `spawn_max_depth`

**Wands:** `id`, `display_name`, `glyph`, `fg`, `examine`, `effect`, `charges_max`, `charges_start`, `range`, `min_damage`, `max_damage`, `accuracy`, `spawn_weight`, `spawn_min_depth`, `spawn_max_depth`

### Ignored in v1

`abilities[]` (warn per npc-data pattern), unknown top-level keys.

### Durability (weapons and armor)

- New instances start at `durability == durability_max` (floor spawn and pickup)
- Dropped floor items preserve current durability on the `Item` entity
- Visible in `i` detail and floor examine (`x`) as `Durability: {current}/{max}`
- Floor examine uses the same **full reveal** as `i` detail (all gameplay stats)

#### Weapon degradation

- **−1 durability** on each **successful player hit** (`resolve_attack` returns `hit=True` for player as attacker)
- Applies whether or not final damage after AC is 0
- If durability reaches 0 after degradation: **destroy** item (see below)

#### Armor degradation

- **`ac_bonus`** mitigates **combat** damage only (existing `uniform(0, ac)` formula on effective AC)
- **`digestion_ac`** mitigates **digestion** damage only (flat per tick — see Digestion integration)
- Combat damage taken while worn does **not** reduce armor durability
- Digestion durability loss = **points of digestion damage mitigated** that tick (see formula below)
- If durability reaches 0 after degradation: **destroy** item (see below)

#### Destruction at 0 durability

- Item is **removed** from inventory (or from floor if somehow applicable)
- If wielded/worn: clear `wielded_slot` / `worn_slot`
- Log message in **red** foreground (e.g. `Your {display_name} falls apart.`)
- Any inventory alert for breakage/destruction uses red — consistent with future alarm styling
- **Implementation note:** `MessageLog` today stores plain strings; extend to optional per-line `fg` (default white/gray) for red alerts

### Potion `effect`

v1 implements `heal` only. Unknown `effect` values fail load.

### Wand `effect`

v1 implements `magic_missile` only: ranged attack using wand `accuracy`, `min_damage`, `max_damage`, and `range` (Chebyshev). Unknown `effect` values fail load.

---

## Floor spawn

Replace potion-only `spawn_floor_items()` with a unified **weighted item pool** per floor:

1. Filter each definition by `spawn_min_depth ≤ floor_depth ≤ spawn_max_depth`
2. Build pool: each definition appears `floor(spawn_weight)` times (same fractional-weight approach as NPC spawn in PR 2)
3. Shuffle; place on valid floor tiles away from player (`MONSTER_SPAWN_MIN_DISTANCE` or shared item distance constant)
4. **Potion minimum:** after weighted placement, ensure at least `spawn_min` health potions (or per-definition `spawn_min` if multiple potion types later) — stock file has `spawn_min: 1` on `health_potion`

One item entity per placement. Multiple items may occupy the same tile; pickup processes **one item per pickup action** (existing loop order).

---

## Pickup and drop

### Pickup (walkover — automatic)

- Trigger: after successful `try_action` move (same hook as today)
- Cost: **no turn** (movement already consumed the turn)
- Picks up **all** floor items on the tile until inventory cannot accept more
- On first rejection due to full inventory: log `Your inventory is full.` **once**, then stop (no per-item spam)
- Success log per item: `You pick up {display_name} into slot '{letter}'.` (stacked potions use stack message — see Stacking)
- Ordering: deterministic floor-item iteration order (stable per tile)

### Pickup (manual — `,`)

- Trigger: player presses `,` while standing on a tile with floor item(s)
- Cost: **no turn**
- **Zero items** on tile: log `There is nothing here to pick up.`
- **One item** on tile: pick it up immediately (no modal)
- **Multiple items** on tile: open **ground pickup modal** listing each item; letter key selects which to pick up; modal stays open until empty or Escape
- Full inventory: log `Your inventory is full.` (no pickup); same rules as walkover
- Use case: choose which item to pick up when standing still or when multiple items share a tile

### Stacking (potions only)

- Potions of the same `item_id` **stack** in one inventory slot with a `stack_count`
- HUD / list display: `{letter}:{glyph}({count})` when count > 1; pickup log notes total (e.g. `3 total`)
- On pickup: if matching potion stack exists, increment `stack_count` (no new letter); else use earliest free letter
- Weapons, armor, and wands **never** stack (one per slot)
- Full inventory: all 26 letters occupied **and** no stackable potion match for the floor item

### Full inventory

- Walkover and `,` both log `Your inventory is full.` once per attempt when no room remains
- Auto-pickup stops immediately after that message (remaining floor items stay)

### Drop (`d`)

1. If no occupied slots → log `You have nothing to drop.` (no modal) — *new message*
2. Else open **drop modal** listing every occupied slot: `{letter}) {display_name}`
3. Letter key matching a listed row → drop that item on player tile, clear slot, spawn floor entity, clear wielded/worn if needed
4. Log: `You drop {display_name}.`
5. **No turn** on success or cancel
6. Unlisted letters: no-op
7. Escape: close modal, no turn (see Escape rules below)

---

## Category commands and modals

### Shared modal rules

- **Inventory modals** block normal gameplay input (like examine description)
- **Digestion modals** are separate — Escape during digestion does **not** close them; inventory Escape handling runs only when an inventory modal is active
- Category action modals (`d`, `w`, `W`, `q`, `v`): **only letter keys** `a`–`z` select from the filtered list; unlisted letters are silent no-op
- Modal shows **only valid items** for that command with their current slot letters
- Wielded weapon marked `(wielded)`; worn armor marked `(worn)` in list text
- Selecting an invalid state (already wielded/worn) → log error, close modal, **no turn**
- Successful wield / wear / quaff / evoke → close modal, **consume player turn**

### Escape (inventory modals only)

| Context | Escape behavior |
|---------|-----------------|
| Inventory list (`i` step 1) | Close modal; no turn |
| Inventory detail (`i` step 2) | Back to slot list; no turn |
| Drop / wield / wear / quaff / evoke (pick step) | Close modal; no turn |
| Evoke (target step) | Abort evoke; no turn |
| Digestion modal active | **No effect** — digestion keeps Enter-only flow |

### Command table

| Key | Action | Empty inventory message | Modal title (example) |
|-----|--------|-------------------------|------------------------|
| `,` | Manual pickup | `There is nothing here to pick up.` | *(no modal)* |
| `i` | Inspect inventory | `Your inventory is empty.` | `Inventory` |
| `d` | Drop | `You have nothing to drop.` | `Drop which item?` |
| `w` | Wield weapon | `You have no weapons.` | `Wield which weapon?` |
| `W` (Shift+w) | Wear armor | `You have no armor.` | `Wear which armor?` |
| `q` | Quaff potion | `You have no potions.` | `Quaff which potion?` |
| `v` | Evoke wand | `You have no wands.` | `Evoke which wand?` |

### Inventory inspect (`i`) — two-step

**Step 1 — list:** all occupied slots, e.g. `a) dagger (wielded)`. Letter key selects that slot → step 2. Unlisted letters: no-op. No turn.

**Step 2 — detail:** full reveal for the selected item. Escape → back to list.

| Category | Detail fields shown |
|----------|---------------------|
| Weapon | `display_name`, `examine`, damage `min–max`, `accuracy_bonus`, `Durability: cur/max`, wielded note |
| Armor | `display_name`, `examine`, `AC bonus: +N`, `Digestion AC: +N`, `Durability: cur/max`, worn note |
| Potion | `display_name`, `examine`, effect line (e.g. `Heals 10 HP`) |
| Wand | `display_name`, `examine`, effect name, damage `min–max`, `accuracy`, `range`, `Charges: cur/max` |

No hidden stats in `i` detail or floor examine — everything the item JSON defines for gameplay is shown.

### Error messages (exact strings)

| Condition | Message |
|-----------|---------|
| Wrong category for action | `You can't wield that.` / `You can't wear that.` / `You can't evoke that.` / `You can't drink that.` |
| Letter slot empty (internal validation) | `You have no item in that slot.` |
| Already wielded | `You're already wielding that.` |
| Already worn | `You're already wearing that.` |

With filtered modals, wrong-category and empty-slot errors are primarily for defensive validation and tests; unlisted letters remain silent no-op.

### Engulfed gating

While `Engulfed`, all inventory commands (`,`, `d`, `i`, `w`, `W`, `v`, `q`) log `You cannot reach your pack while engulfed.` and do not open modals (extends current letter-key block). Manual `,` pickup is also blocked.

### Stunned

While `Stunned`, inventory commands **are allowed** (consistent with core AC6 potion use). Movement still passes time per enhancements-1.

---

## Wield and wear

### Wield (`w`)

1. If zero weapons in inventory → `You have no weapons.` (no modal)
2. Modal lists weapon slots
3. Select letter:
   - Already `wielded_slot` → `You're already wielding that.`, no turn
   - Else set `wielded_slot`, log `You wield {display_name}.`, consume turn

Switching weapons updates `wielded_slot` only (previous weapon stays in inventory).

### Wear (`W`)

Same pattern with `worn_slot` / `You wear {display_name}.` / `You're already wearing that.`

### Combat effective stats

When resolving player attacks and player as defender:

```
if wielded weapon:
    min_damage, max_damage = weapon.min_damage, weapon.max_damage
    accuracy = PLAYER_ACCURACY + weapon.accuracy_bonus
else:
    min_damage, max_damage = PLAYER_MIN_DAMAGE, PLAYER_MAX_DAMAGE
    accuracy = PLAYER_ACCURACY

if worn armor:
    ac = PLAYER_AC + armor.ac_bonus
else:
    ac = PLAYER_AC
```

`evade` and `max_hp` unchanged. Helper `effective_fighter(player)` builds a transient `Fighter` or mutates a cached view — implementation choice in PR 3.

### Digestion integration (worn armor)

When applying a digestion tick to the **player** (and only the player wears inventory armor in v1):

```
raw_tick     = DigestionStats.damage_per_tick
mitigated    = min(raw_tick, worn_armor.digestion_ac)   # 0 if no worn armor
hp_loss      = raw_tick - mitigated
durability  -= mitigated   # on worn armor instance only
```

- Worn armor passive effect applies **while engulfed** even though pack commands are blocked
- NPC prey digestion unchanged (no inventory armor on NPCs in v1)
- Update `apply_player_digestion_tick` in `src/systems/digestion.py`
- Stock `leather_armor` ships with `digestion_ac: 1` (tunable in JSON)

---

## Quaff (`q`)

1. If zero potions → `You have no potions.`
2. Modal lists potion slots
3. Select letter → apply `effect`:
   - `heal`: restore `heal_amount` up to max HP (same as today); consume item from slot
   - Log heal or `You drink {display_name} but are already at full health.`
4. Consume turn on success (even if 0 HP healed — same as current potion behavior)

---

## Evoke wand (`v`)

Two-step modal flow:

### Step 1 — wand selection

Same as other category modals. On select, if charges `≤ 0`, treat as validation error (should not appear in list if charges 0 — empty wand removed on last use).

### Step 2 — target selection

- Build candidate list: entities with `Fighter` within wand `range` (Chebyshev) of player, plus player tile
- Require line-of-sight from player to target tile (FOV / `game_map` blocking)
- **Default target:** nearest **evil** NPC (`NPCAlignment.EVIL`) by Chebyshev distance; if none, default to **player**
- UI: modal line `Select target (arrows move, Enter confirms)` + highlight/cursor on current target (reuse examine-style cursor or indexed list)
- Direction keys cycle/move among valid targets; Enter confirms; Escape aborts without turn
- On confirm: resolve wand attack (`resolve_attack` with wand accuracy/damage) against target `Fighter`
- Decrement charges; at 0 remove item from slot
- Log hit/miss/defeat using standard combat messages
- Consume turn on successful evoke (attack resolved, charge spent)

v1 does not implement friendly-fire restrictions beyond player choosing target.

---

## Rendering

### HUD inventory summary

Update `_inventory_summary` to show slot letter + item glyph from registry (already partially there). Optional: `*` suffix on wielded weapon letter, `+` on worn armor in HUD compact view.

### Inventory modal (`i`)

**List step:**

```
Inventory
 a) dagger (wielded)
 b) leather armor (worn)
 c) health potion
 d) wand of magic missile
Esc: close
```

**Detail step (example — weapon):**

```
dagger (wielded)
A short blade.
Damage: 1-4
Accuracy bonus: +0.05
Durability: 87/100
Esc: back
```

**Detail step (example — armor):**

```
leather armor (worn)
Light leather protection.
AC bonus: +2
Digestion AC: +1
Durability: 45/80
Esc: back
```

### Category modals

Centered box listing valid rows; same typography as `render_centered_modal`.

---

## Engine integration

### New state object

`InventoryModalState` (or general `ItemModalState`) tracls:

- `mode`: `none` \| `inspect_list` \| `inspect_detail` \| `drop` \| `wield` \| `wear` \| `quaff` \| `evoke_pick` \| `evoke_target`
- `selected_slot`: letter \| null (inspect detail, evoke target step)

Insert in `handle_event` **after** digestion/vore/game-over modals. Inventory Escape handler runs only when `mode != none`. Digestion modal Escape remains unchanged (no-op). `modal_blocks_quit()` includes active inventory modals.

### Remove

- `INVENTORY_KEYS` global routing in `_handle_gameplay_event`
- `ItemType` enum (migrate tests)
- `HEALTH_POTION_HEAL` constant usage → `heal_amount` from registry

---

## File layout (target)

```
data/
  weapons.json, armor.json, potions.json, wands.json
  SCHEMA.md                    # extend item sections

src/data/
  item_registry.py             # frozen definitions per category
  item_loaders.py              # strict required fields for gameplay

src/systems/
  inventory.py                 # pickup, drop, quaff, wield, wear, evoke
  item_spawn.py                # floor placement (or section in spawn.py)
  item_modals.py               # modal state + render helpers

src/components.py              # InventoryInstance, EquipState; Item holds item_id
```

---

## Resolved decisions

| # | Question | Resolution |
|---|----------|------------|
| 1 | Direct `a`–`z` use? | Removed; category modals only |
| 2 | Pickup turn cost? | Free (walkover and `,`) |
| 3 | Drop turn cost? | Free |
| 4 | Inventory inspect turn cost? | Free |
| 5 | Multiple items one tile? | Pick one per pickup action |
| 6 | Wand self-target default? | Yes, when no evil in range |
| 7 | Wand at 0 charges? | Removed from inventory |
| 8 | Durability tracked? | Yes — weapons and armor; visible in `i` and floor examine (full reveal) |
| 9 | Weapon durability loss? | −1 per successful player hit |
| 10 | Armor durability loss? | −1 per point of digestion damage mitigated; combat does not degrade armor |
| 11 | Armor digestion stat? | New `digestion_ac` field in `armor.json` |
| 12 | At 0 durability? | Item destroyed; log in **red**; clear wielded/worn if applicable |
| 13 | `i` detail Escape? | Back to list; list Escape closes modal |
| 14 | Escape scope? | Inventory modals only; digestion unaffected |
| 15 | Descent preservation? | Slots, durability, charges, wielded/worn preserved |
| 16 | Worn armor while engulfed? | Passive digestion mitigation still applies; pack commands blocked |

---

## PR plan

| PR | Scope |
|----|-------|
| 1 | Item registries, instance model (durability + charges), floor spawn, walkover + `,` pickup |
| 2 | Modal framework, `i` list/detail, `d`, Escape rules, remove global letter-use, engulfed gate |
| 3 | Wield/wear + `effective_fighter` + durability + digestion_ac on player ticks |
| 4 | Quaff from data (`effect: heal`) |
| 5 | Wand evoke two-step + targeting + charges |
| 6 | `inventory-items` spec, cross-spec updates, README, acceptance, archive |

---

## Testing notes

- PR 1: `tests/test_inventory_items_pr1.py` — registry load, spawn count bounds, pickup assigns earliest letter
- PR 2: modal open/close, empty-category messages, drop frees slot, no turn on drop
- PR 3: wield changes damage; wear changes ac; already-wielded message
- PR 4: quaff heals from JSON amount; stunned quaff still works
- PR 5: evoke default target evil; charge decrement; 0 charges removes wand
- PR 6: full suite + update `test_ac7` / `test_ac6` for new UX