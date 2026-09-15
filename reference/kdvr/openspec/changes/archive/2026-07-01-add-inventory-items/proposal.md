# Proposal: Inventory and Data-Driven Items

## Why

The game has a minimal letter-key inventory (health potions only) and item JSON stubs that load but do not affect gameplay. Players cannot wield weapons, wear armor, quaff by category, evoke wands, drop items, or inspect inventory through dedicated commands. Modders cannot add items without Python changes.

This change wires **`data/weapons.json`**, **`armor.json`**, **`potions.json`**, and **`wands.json`** into floor spawn, pickup, and use — with DCSS-style **category commands** (`, ` / `d` / `i` / `w` / `W` / `v` / `q`) and **stable slot letters** assigned on pickup.

## What Changes

- **Floor items** — spawn from item JSON (weight + depth; potions keep `spawn_min` floor minimum)
- **Auto-pickup** — walkover picks up items for free (no turn); earliest free letter `a`–`z`
- **Manual pickup** — `,` picks up one floor item on the current tile (no turn); backup when standing still
- **Slot letters** — assigned on pickup only; stable until drop; drop frees slot for reassignment
- **Category modals** — `w` wield, `W` wear, `v` evoke (+ target step), `q` quaff, `d` drop
- **Inventory inspect** — `i` opens list modal; letter selects **full item detail** (stats, durability, charges)
- **Durability** — weapons and armor track current/max durability; visible in `i` detail and floor examine (`x` full reveal)
- **Armor digestion AC** — new `digestion_ac` on armor; mitigates digestion ticks; durability loss equals mitigated amount
- **Equip state** — track wielded weapon and worn armor; combat uses effective stats
- **Turn rules** — successful wield, wear, quaff, evoke consume a turn; pickup, drop, and inventory inspect do not
- **Escape** — dismisses inventory-related modals only (not digestion modals)
- **Retire direct `a`–`z` use** — letter keys only work inside inventory modals (not globally)

## Out of Scope

- Durability repair / smithing
- Ranged melee (`RangeN` abilities), item identification, cursed items, stacking
- Gold, loot tables, XP from items
- Hot-reload mid-run
- New item categories beyond the four JSON files

## Capabilities

### New

- `inventory-items` — data-driven items, slot model, category commands, equip, consume, evoke

### Modified

- `core-roguelike` — replace letter-key direct use with category modals; extend item requirement
- `enhancements-1` — turn consumption rules for inventory commands
- `enhancements-2` — examine descriptions for all item types on floor
- `dungeon` — preserve wielded/worn state and item instances on descent
- `digestion` — armor `digestion_ac` mitigates tick damage; worn armor degrades per mitigated point
- `vore` — inventory command gating while engulfed (replaces “inventory keys” wording)
- `npc-data` — item stubs become gameplay-wired (update out-of-scope note)

## Success Criteria

- Stock JSON items (dagger, leather armor, health potion, wand of magic missile) spawn, pick up, and work through category commands
- Wielded weapon and worn armor change player combat stats; messages match spec
- Wand evoke targets nearest evil NPC by default (else player); consumes charge and turn on success
- All user-facing error strings implemented exactly as listed in `design.md`
- Full `pytest tests/` green after implementation

## Decisions (locked)

| # | Decision |
|---|----------|
| 1 | Item identity: JSON `id` string (replaces `ItemType` enum) |
| 2 | One wielded weapon, one worn armor; switching unwears/unwields previous |
| 3 | Unarmed player uses `PLAYER_*` combat constants from `constants.py` |
| 4 | Effective combat: weapon replaces `min_damage`/`max_damage`; `accuracy += accuracy_bonus`; armor adds `ac_bonus` |
| 5 | Category modals list only valid items; unlisted letter keys are silent no-op |
| 6 | Zero valid items → immediate log message, no modal |
| 7 | Pickup (walkover and `,`), drop (`d`), and inventory inspect (`i`) do not consume a turn |
| 8 | Wand at 0 charges: item removed from inventory (consumed) |
| 9 | Weapons and armor track durability (`durability_max` from JSON); visible in `i` detail and floor examine |
| 10 | Weapon durability −1 per successful player hit; armor durability −1 per point of digestion damage mitigated (not combat) |
| 11 | Armor has `ac_bonus` (combat) and `digestion_ac` (digestion ticks) |
| 12 | At 0 durability: item destroyed (removed); alert log uses **red** foreground |
| 13 | `i` detail Escape → back to list; list Escape → close modal |
| 14 | Escape dismisses inventory modals only — digestion modals unaffected |
| 15 | Quit remains **Ctrl+Q**; lowercase `q` is quaff |