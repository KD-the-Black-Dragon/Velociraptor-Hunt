# inventory-items Specification

## Purpose

**inventory-items** wires **`data/weapons.json`**, **`armor.json`**, **`potions.json`**, **`wands.json`**, and **`throwables.json`** into floor spawn, pickup, equip, consume, evoke, and throw. Players manage a **26-slot letter inventory** (`a`–`z`) through **DCSS-style category commands** instead of global letter-key use.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- Frozen item registries at load time (`ItemRegistry`)
- `InventoryItemInstance` per occupied slot (`item_id`, `category`, `durability`, `charges`, `stack_count` for potions and throwables)
- `EquipState` on player (`wielded_slot`, `worn_slot`)
- Weighted floor item spawn with depth filter and potion `spawn_min`
- Walkover auto-pickup and manual `,` pickup; potion and throwable stacking
- Category modals: `i`, `d`, `w`, `W`, `q`, `v`, `f`, `F`
- Wield/wear combat via `effective_fighter()`; weapon and armor durability
- Armor `digestion_ac` mitigates player digestion ticks (see `digestion` spec)
- Wand `magic_missile` evoke with evil-only Smite targeting
- Player throwables with Path targeting (`f` quick-throw, `F` manual pick)
- Floor examine (`x`) full reveal for all item stats
- Descent preserves slots, instances, durability, charges, stack counts, and equip pointers
- Stock tier catalog, spawn rarity, starter loadout — see `openspec/specs/equipment-catalog/spec.md`

### Out of scope

- Durability repair / smithing
- Identification, cursed items
- Gold, loot tables, XP from items
- Hot-reload mid-run
- Item categories beyond the five JSON files
- Friendly-fire restrictions on wands beyond target validation
- Bows, slings, crossbows, throwable recovery

## Controls (summary)

| Key | Action | Turn on success |
|-----|--------|-----------------|
| `,` | Manual pickup on current tile | No |
| `i` | Inspect inventory (list → detail) | No |
| `d` | Drop item | No |
| `w` | Wield weapon | Yes |
| `W` (Shift+w) | Wear armor | Yes |
| `q` | Quaff potion | Yes |
| `v` | Evoke wand (pick → target cursor) | Yes |
| `f` | Quick throw best throwable → target cursor | Yes |
| `F` (Shift+f) | Pick throwable → target cursor | Yes |

Letter keys `a`–`z` select rows **only inside an open inventory modal**. Unlisted letters are silent no-ops.

**Quit:** lowercase `q` is quaff; quit remains **Ctrl+Q** (`main-menu` spec).

## Requirements

### Requirement: Item registries

The game SHALL load weapon, armor, potion, wand, and throwable definitions from their JSON files at startup. Each definition SHALL have required gameplay fields documented in `data/SCHEMA.md`. Unknown top-level keys SHALL warn once and be ignored. Invalid required fields or unknown `effect` values SHALL fail load.

Potion effects: `heal`, `magic_mapping`, `haste`, `might`, `digestion_ward` (stock antacid), `teleport_delay`, `blink`, `summon_ally`. Wands: `magic_missile`.

#### Scenario: Stock items load

- GIVEN the shipped JSON files
- WHEN the game starts
- THEN dagger, leather armor, health potion, wand of magic missile, and rock throwable are available
- AND leather armor has `digestion_ac`

### Requirement: Inventory slots and instances

The player SHALL have **26 slots** mapped to letters `a` through `z`. On pickup, the game SHALL assign the **earliest free letter**. Letters SHALL remain stable until the item is dropped or consumed. Each occupied slot stores an `InventoryItemInstance`:

| Field | Weapons / armor | Potions | Wands | Throwables |
|-------|-----------------|---------|-------|------------|
| `item_id` | yes | yes | yes | yes |
| `category` | yes | yes | yes | yes |
| `durability` | starts at `durability_max` | — | — | — |
| `charges` | — | — | starts at `charges_start` | — |
| `stack_count` | 1 | stacks same `item_id` | 1 | stacks same `item_id` |

#### Scenario: Pickup assigns earliest free slot

- GIVEN slots `a` and `c` occupied and `b` empty
- WHEN the player picks up a floor item
- THEN the item is stored in slot `b`

### Requirement: Equip state

The player SHALL track at most one wielded weapon (`wielded_slot`) and one worn armor (`worn_slot`) by slot letter. Wield/wear switching updates the pointer only; the previous item remains in inventory. Dropping a wielded or worn item SHALL clear the corresponding pointer.

On **new game**, stock starter loadout SHALL place **dagger** in slot `a` (wielded), **robes** in slot `b` (worn), and **5 rocks** in slot `c` per `equipment-catalog` spec.

#### Scenario: Starter dagger wielded and rocks in slot c

- GIVEN a new game
- WHEN the player has not dropped or swapped gear
- THEN `wielded_slot` is `a`
- AND `worn_slot` is `b`
- AND slot `c` holds rock with `stack_count` 5

#### Scenario: Drop clears wield pointer

- GIVEN a weapon wielded from slot `a`
- WHEN the player drops slot `a`
- THEN `wielded_slot` is null
- AND the weapon appears on the floor with current durability

### Requirement: Floor item spawn

Floor items SHALL spawn from a unified weighted pool per floor:

1. Filter each definition by `spawn_min_depth ≤ floor_depth ≤ spawn_max_depth`
2. Add each definition `int(spawn_weight)` times to the pool
3. Shuffle and place up to **`MAX_FLOOR_ITEM_PLACEMENTS`** (default **5**) weighted drops on valid floor tiles away from the player
4. Ensure at least `spawn_min` potions per matching potion definition (stock: one health potion on floor 1) — runs after weighted placement

Multiple floor items MAY share a tile. Pickup processes one item per pickup action (deterministic iteration order). Stock weights and tier list: `equipment-catalog` spec.

#### Scenario: Placement cap limits clutter

- GIVEN many eligible definitions at the current depth
- WHEN the floor generates items
- THEN weighted placements do not exceed `MAX_FLOOR_ITEM_PLACEMENTS`

#### Scenario: Health potion minimum on depth 1

- GIVEN a new game at depth 1
- WHEN the floor generates
- THEN at least one health potion is on the floor

### Requirement: Pickup

**Walkover (automatic):** after a successful move onto a tile with floor items, pick up **all** items on that tile until inventory cannot accept more. Cost: **no turn** (movement already consumed the turn). On first full-inventory rejection, log `Your inventory is full.` **once** and stop.

**Manual (`,`):** standing on items, `,` picks up one item (no turn). Zero items: `There is nothing here to pick up.` One item: immediate pickup. Multiple items: **ground pickup modal**; letter selects one; modal stays open until empty or Escape.

Success log per item: `You pick up {display_name} into slot '{letter}'.` Stacked potions and throwables use the stack message with total count.

#### Scenario: Full inventory stops walkover once

- GIVEN all 26 slots occupied with no stackable potion or throwable match
- WHEN the player walks onto a tile with two floor items
- THEN neither item is picked up
- AND `Your inventory is full.` appears once in the log

### Requirement: Potion and throwable stacking

Potions and throwables with the same `item_id` SHALL stack in one slot (`stack_count`). Weapons, armor, and wands SHALL NOT stack. Full inventory means all 26 letters occupied **and** no matching potion or throwable stack for the floor item.

#### Scenario: Second health potion stacks

- GIVEN a health potion in slot `a` with `stack_count` 1
- WHEN the player picks up another health potion
- THEN slot `a` has `stack_count` 2
- AND no new letter is assigned

#### Scenario: Second rock stacks into starter slot

- GIVEN rocks in slot `c` with `stack_count` 5
- WHEN the player picks up another rock
- THEN slot `c` has `stack_count` 6

### Requirement: Drop

Pressing `d` with no occupied slots SHALL log `You have nothing to drop.` (no modal). Otherwise open a drop modal listing occupied slots. Letter key drops that item on the player tile, clears the slot, spawns a floor entity preserving durability/charges/stack, and logs `You drop {display_name}.` Drop SHALL NOT consume a turn.

#### Scenario: Drop preserves weapon durability

- GIVEN a dagger in slot `b` with durability 42
- WHEN the player drops slot `b`
- THEN a floor item entity has durability 42

### Requirement: Inventory inspect

`i` with empty inventory logs `Your inventory is empty.` Otherwise a two-step modal:

1. **List** — all occupied slots; wielded weapon marked `(wielded)`; worn armor marked `(worn)`; letter selects slot
2. **Detail** — full gameplay stats from JSON (damage, AC, digestion AC, durability, charges, heal amount, stack count, examine text)

Escape on detail → back to list; Escape on list → close. Inspect SHALL NOT consume a turn.

#### Scenario: Weapon detail shows durability

- GIVEN a wielded dagger with durability 87/100
- WHEN the player inspects that slot
- THEN detail includes `Durability: 87/100`

#### Scenario: Throwable detail shows stack count

- GIVEN rocks in slot `c` with `stack_count` 5
- WHEN the player inspects that slot
- THEN detail includes damage range, accuracy bonus, and quantity 5

### Requirement: Wield and wear

`w` lists weapons only; `W` lists armor only. Zero valid items → immediate log (`You have no weapons.` / `You have no armor.`) without modal. Already wielded/worn → error log, no turn. Success → `You wield {name}.` / `You wear {name}.` and **consume a turn**.

Combat SHALL use `effective_fighter()`:

- Wielded weapon replaces `min_damage`/`max_damage`; `accuracy = PLAYER_ACCURACY + accuracy_bonus`
- Unarmed uses `PLAYER_*` constants
- Worn armor adds `ac_bonus` to `PLAYER_AC`

#### Scenario: Wielded dagger changes damage range

- GIVEN an unarmed player and a wielded dagger (1–4 damage)
- WHEN the player bump-attacks
- THEN damage rolls use the dagger range, not unarmed defaults

### Requirement: Durability

Weapons and armor track current/max durability visible in `i` detail and floor examine.

- **Weapon:** −1 durability per **successful player hit** (`hit=True`), including zero-damage hits
- **Armor:** `ac_bonus` mitigates combat only; `digestion_ac` mitigates digestion ticks only; combat damage does **not** degrade armor; digestion durability loss = points mitigated that tick
- **At 0 durability:** remove item; clear wielded/worn if applicable; log `Your {display_name} falls apart.` in **red**

#### Scenario: Weapon destroyed at zero durability

- GIVEN a weapon at 1 durability after a hit
- WHEN degradation applies
- THEN the weapon is removed from inventory
- AND the log line uses red foreground

### Requirement: Quaff potions

`q` lists potions only. Zero potions → `You have no potions.` Select letter → apply `effect: heal` using `heal_amount` from JSON; consume one from stack; log heal or full-health message; **consume a turn** even when 0 HP healed.

Stunned players MAY quaff (consistent with enhancements-1 stunned item use).

#### Scenario: Stunned quaff heals

- GIVEN a stunned player at 0 HP with a health potion
- WHEN the player quaffs via `q` modal
- THEN HP increases
- AND stunned clears if HP > 0

### Requirement: Evoke wands

`v` is two-step:

1. **Wand pick** — category modal; only wands with charges > 0
2. **Target** — **no centered modal**; examine-style cursor on map only. Valid targets: entities with `Fighter` within wand `range` (Chebyshev) and line of sight. **Only evil NPCs** (`NPCAlignment.EVIL`) are valid strike targets.

On wand pick, if no evil target exists in range/LoS → `No valid targets in range.` (abort, no target step, no turn).

Default cursor: nearest evil NPC by Chebyshev distance. Direction keys cycle among **all** in-range LoS fighters (including player, good, neutral for cursor movement); **Enter** on invalid target (self, good, neutral) → `Not the best target.`, full modal reset, no turn.

On valid confirm: resolve `magic_missile` **Smite** attack; decrement charges; at 0 charges remove wand and log `Your {display_name} breaks!` in **red**; consume turn.

#### Scenario: Invalid target aborts evoke

- GIVEN evoke target step with cursor on the player
- WHEN the player presses Enter
- THEN the log reports `Not the best target.`
- AND no charge is spent
- AND no turn is consumed

#### Scenario: No evil in range

- GIVEN a wand and only good/neutral NPCs in range
- WHEN the player selects the wand
- THEN the log reports `No valid targets in range.`
- AND targeting mode does not open

### Requirement: Throw throwables

**`f` (quick throw):** Among occupied throwable slots with `stack_count > 0`, auto-select by:

1. Highest `max_damage` from definition
2. Tie: highest `min_damage`
3. Tie: earliest inventory letter (`a` before `b`)

If no throwables → `You have nothing to throw.` (no modal, no turn). Otherwise skip pick modal and open **target step** directly.

**`F` (manual pick):** Category modal listing throwables with `stack_count > 0`; letter selects slot → target step.

**Target step:** Map cursor only (cyan `X`), no centered modal. Log `Throw {display_name} at which target?` on entry. Valid confirm targets: **evil NPCs** in player LoS only. Cursor cycles **valid evil targets** sorted near-to-far (Chebyshev). Forward cycle (including numpad6): next nearer→farther; backward cycle (including numpad4): previous; from index 0 backward wraps to farthest.

On throwable pick, if no evil in LoS → `No valid targets in range.` (abort, no target step, no turn).

| Confirm on | Result |
|------------|--------|
| Evil with clear Path | Resolve Path beam; consume 1 from stack; clear slot at 0; consume turn |
| Good / Neutral | `Not the best target.` — reset, no turn |
| Empty / no `Fighter` | `There's no target there.` — no turn |
| Evil but path blocked | `Something is in the way.` — no turn |

Path rules, animation deferral, and miss string: `ranged-targeting` spec.

#### Scenario: Quick throw consumes one rock

- GIVEN 5 rocks in slot `c` and a visible evil with clear path
- WHEN the player presses `f` and confirms
- THEN slot `c` has `stack_count` 4
- AND a turn is consumed

#### Scenario: Manual pick weaker throwable

- GIVEN rocks and a weaker throwable in separate slots
- WHEN the player presses `F` and selects the weaker item
- THEN targeting opens for that item (not auto best-damage pick)

### Requirement: Category modal input and Escape

Inventory modals block normal gameplay input (like examine). Digestion modals are unaffected — Escape during digestion does not close inventory modals and inventory Escape does not close digestion modals.

| Context | Escape |
|---------|--------|
| Inspect list | Close; no turn |
| Inspect detail | Back to list; no turn |
| Drop / wield / wear / quaff / evoke pick / throw pick | Close; no turn |
| Evoke target / throw target | Abort; no turn |

`modal_blocks_quit()` SHALL include active inventory modals.

#### Scenario: Escape on inspect detail returns to list

- GIVEN inventory inspect detail open
- WHEN the player presses Escape
- THEN the slot list is shown
- AND no turn is consumed

### Requirement: Engulfed gating

While `Engulfed`, all pack commands (`,`, `d`, `i`, `w`, `W`, `q`, `v`, `f`, `F`) SHALL log `You cannot reach your pack while engulfed.` and SHALL NOT open modals. Worn armor **digestion_ac** still mitigates digestion passively.

#### Scenario: Pack blocked while engulfed

- GIVEN an engulfed player
- WHEN the player presses `i`
- THEN the pack-blocked message appears
- AND no inventory modal opens

### Requirement: Floor examine full reveal

Floor examine (`x` → Enter) SHALL show the same gameplay stats as `i` detail for items (including durability, charges, and stack count), not examine prose alone.

#### Scenario: Examine floor dagger

- GIVEN a dagger on the floor with durability 55/100
- WHEN the player examines it
- THEN the modal shows durability and damage stats

### Requirement: Rendering order

On a tile with both a floor item and an entity, the **entity glyph SHALL render above the item glyph** (player and NPCs over dropped items).

#### Scenario: Player over dropped item

- GIVEN the player standing on a dropped potion tile
- WHEN the map renders
- THEN the player `@` is visible, not obscured by the item glyph

### Requirement: Descent preservation

Successful descent SHALL preserve inventory slots, item instances (durability, charges, stack counts), and `wielded_slot` / `worn_slot`. Fresh floor items respawn per spawn rules.

#### Scenario: Wielded weapon survives descent

- GIVEN a wielded weapon in slot `a` at depth 2
- WHEN the player descends to depth 3
- THEN slot `a` still holds the same weapon instance
- AND `wielded_slot` is still `a`

## Error messages (exact strings)

| Condition | Message |
|-----------|---------|
| Wrong category (defensive) | `You can't wield that.` / `You can't wear that.` / `You can't evoke that.` / `You can't drink that.` |
| Empty slot (defensive) | `You have no item in that slot.` |
| Already wielded | `You're already wielding that.` |
| Already worn | `You're already wearing that.` |
| No throwables | `You have nothing to throw.` |
| Throw path blocked | `Something is in the way.` |
| Throw miss | `Your throw misses the {target}.` |

Filtered modals make wrong-category errors rare; unlisted modal letters remain silent no-ops.

## Technical notes (non-normative)

- Registry: `src/data/item_registry.py`, loaders in `src/data/item_loaders.py`
- Systems: `src/systems/inventory.py`, `item_modals.py`, `wand_evoke.py`, `player_throw.py`
- Spawn: unified pool in item spawn (see `src/spawn.py` or `item_spawn`)
- Tests: `tests/test_inventory_items_pr1.py` … `tests/test_inventory_items_pr5.py`, `tests/test_throwables_pr5.py`, `tests/test_player_throw_pr6.py`
- Red alerts: `MessageLog` optional per-line `fg`; `ALERT_MESSAGE_FG` for destruction/breakage

## Related specs

| Spec | Relationship |
|------|----------------|
| `core-roguelike/spec.md` | Bump combat, stunned recovery, HUD |
| `enhancements-1/spec.md` | Turn consumption; stunned quaff |
| `enhancements-2/spec.md` | Floor examine; Escape scope |
| `dungeon/spec.md` | Descent preserves inventory and equip |
| `equipment-catalog/spec.md` | Stock tiers, spawn rarity, starter loadout |
| `ranged-targeting/spec.md` | Path vs Smite; throw resolve and animation |
| `vore/spec.md` | Pack blocked while engulfed |
| `digestion/spec.md` | Armor `digestion_ac` on player ticks |
| `npc-data/spec.md` | Shared JSON load patterns |

## Acceptance Criteria

1. Stock JSON items spawn, pick up, wield, wear, quaff, evoke, and throw through category commands.
2. Wielded weapon and worn armor change combat stats; durability and destruction logs match spec (red alerts).
3. Wand evoke: evil-only valid targets; Smite resolve; cursor-only target UI; exact error strings for invalid/no-target cases.
4. Throw: `f` auto-pick, `F` manual pick, Path resolve, stack consume, exact error strings.
5. Pickup, drop, and inspect do not consume turns; wield, wear, quaff, successful evoke, and successful throw do.
6. Engulfed blocks all pack commands; worn armor still mitigates digestion.
7. Player and NPC glyphs render over floor items on the same tile.
8. All requirement scenarios covered by `test_inventory_items_pr*.py`, `test_throwables_pr*.py`, `test_player_throw_pr6.py`, and manual checklists.
9. Full `pytest tests/` green.