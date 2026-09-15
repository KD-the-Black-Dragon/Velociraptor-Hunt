# ranged-targeting Specification

## Purpose

**ranged-targeting** defines the two combat targeting models used for physical projectiles and magic arcs: **Smite** (LoS + distance band, ignores intermediates) and **Path** (Bresenham beam with alignment blocks and first-valid-fighter hit). Player throwables, NPC `RangeN` abilities, wand evoke, and NPC `SmiteN` abilities all route through these rules.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- Smite targeting (`Smite2`…`Smite9`, wand `magic_missile`)
- Path targeting (`Range2`…`Range9` NPC abilities, player throwables)
- Alignment path-block table (pre-fire cancel)
- Beam first-fighter hit (intended target may not be struck)
- Shared combat resolution (`resolve_attack`, knockback/lifedrain along beam axis)
- Projectile animation (cosmetic; FOV-gated at queue time)
- Log verb split: *smites* vs *shoots* vs player throw miss

### Out of scope

- Bows, slings, crossbows, launcher equip slots
- Throwable recovery / durability
- Friendly fire (same-alignment on path cancels shot)
- Item `abilities[]` on weapons/armor JSON
- NPC Path/Smite **magazine** / reload AI (see `npc-abilities` + `balance` `good_ranged_shots` / `evil_ranged_shots`)
- Player ammo limits

## Requirements

### Requirement: Smite targeting

**Smite** SHALL resolve an attack on the **intended** target when:

1. Shooter has line of sight to the target tile
2. Chebyshev distance ∈ `[2, N]` (ability `N` or wand `range`)

Entities between shooter and target SHALL be ignored. Walls and closed doors that break LoS SHALL prevent the shot.

**Used by:** `SmiteN` NPC abilities, wand `magic_missile` evoke.

**NPC magazine:** NPC `SmiteN` shots SHALL obey the Path/Smite magazine rules in `npc-abilities` (spend one shot per fired attempt). Player wand Smite SHALL NOT use that magazine.

**Logs:** `npc_smites_target`, `npc_smites_target_no_damage`, `npc_smites_at_target_miss` for NPCs; player wand templates use *smite* verbs. Smite SHALL NOT use `npc_shoots_*` templates.

**Animation:** Brief **magenta `*`** flash on source tile, then target tile (no travel beam). FOV-gated at queue time.

#### Scenario: Wand smites through ally

- GIVEN a wand evoke with a good NPC between player and an evil target
- WHEN the player confirms a valid evil target in range and LoS
- THEN the attack resolves on the evil target
- AND the good NPC does not block the shot

#### Scenario: Smite at distance 1 uses melee

- GIVEN an NPC with `Smite3` adjacent to a valid target
- WHEN the NPC acts
- THEN ranged Smite does not fire
- AND melee engagement applies instead

### Requirement: Path beam trace

**Path** SHALL trace `tcod.los.bresenham` from shooter tile toward the intended target tile.

Tiles considered start **after** the shooter origin and walk toward the target. The trace stops at the first blocking condition.

**Blocking terrain:** Wall or closed door — if the line cannot reach the target, the shot is invalid.

#### Scenario: Wall blocks path shot

- GIVEN a shooter with LoS around a wall corner but no clear bresenham path to the target
- WHEN a Path shot is evaluated
- THEN the shot is not valid

### Requirement: Path alignment pre-fire cancel

Before firing a Path shot, the game SHALL walk the bresenham line (excluding shooter origin, before the intended target cell). If any tile contains a `Fighter` the shooter **must not damage** (same-alignment block table), the shot SHALL **cancel** with no attack resolve:

| Shooter | Blocks path |
|---------|-------------|
| Player | Good, Neutral |
| Evil | Evil |
| Good | Good, Player, Neutral |

Player cancel message: `Something is in the way.` (no turn consumed).

#### Scenario: Good ally blocks player throw

- GIVEN a visible evil target with a good NPC on the beam between player and target
- WHEN the player confirms the throw
- THEN the log reports `Something is in the way.`
- AND no stack is consumed
- AND no turn is consumed

### Requirement: Path beam hit resolution

On fire, Path SHALL walk the bresenham line and strike the **first `Fighter`** the shooter **may** damage. Hit, miss, and damage use `resolve_attack()`. The intended cursor target MAY differ from the entity actually struck.

**NPC distance:** Chebyshev ∈ `[2, N]` for `RangeN` abilities. At distance 1, NPCs use melee (or flee / other non-ranged intents — not forced to melee for Coward).

**NPC magazine:** NPC `RangeN` shots SHALL obey the Path/Smite magazine rules in `npc-abilities`. Player throwables SHALL NOT use that magazine.

**Player throwables:** No Chebyshev cap beyond **player LoS** (`can_see`); **distance 1 allowed**. Accuracy = `PLAYER_ACCURACY + accuracy_bonus`; damage from item `min_damage` / `max_damage`.

**Stunned 0 HP prey:** Not shot; predators close for melee (unchanged).

**Engulfed targets:** Not valid Path targets.

#### Scenario: Beam hits front evil not cursor target

- GIVEN two evil NPCs in a line with the nearer one damageable
- WHEN the rear shooter fires Path at the farther evil
- THEN the nearer evil receives the attack
- AND the farther evil is not struck on that shot

### Requirement: Path log verbs

NPC Path attacks SHALL log FOV-gated **shoot** templates (`npc_shoots_target`, `npc_shoots_target_no_damage`, `npc_shoots_at_target_miss`). NPC Smite attacks SHALL NOT use shoot templates.

Player throw miss SHALL log: `Your throw misses the {target}.`

#### Scenario: Fox archer shoots not smites

- GIVEN a fox archer with `Range5` and a valid Path shot
- WHEN the archer fires
- THEN the log uses *shoots* (not *smites*)

### Requirement: Path projectile animation

After a confirmed Path attack (player throw or NPC `RangeN` shot), the engine SHALL queue a cosmetic animation before advancing the world phase when the shooter is the player.

**Path render:**

- Fixed **cyan `*`** glyph along the full bresenham trail (shooter → impact)
- Cumulative trail drawn without per-tile FOV culling during animation
- FOV-gated at **queue** time — off-screen shots skip animation entirely

**Smite render:**

- **Magenta `*`** on source, then target (no travel)

**Turn model:** Player Path shots SHALL defer `run_world_turn` until animation completes (`pending_world_turn`). NPC Path shots animate within the same world phase without deferring subsequent NPC steps beyond the cosmetic render loop.

#### Scenario: Player throw anim before NPC move

- GIVEN a player throw that queues a Path projectile
- WHEN the throw resolves
- THEN the cyan trail animates to completion
- AND NPC movement begins only after the animation finishes

### Requirement: Shared combat hooks

Path and Smite hits SHALL use the same combat hooks as existing ranged hits:

- Player hits: `fire_player_combat_targeted()` (rest-under-attack gate)
- Knockback / Lifedrain apply on Path hits with vector along the beam axis
- `resolve_attack()` for hit roll and damage

## Error messages (player Path — exact strings)

| Condition | Message |
|-----------|---------|
| No throwables | `You have nothing to throw.` |
| No evil in LoS after pick | `No valid targets in range.` |
| Target step prompt | `Throw {display_name} at which target?` |
| Path blocked | `Something is in the way.` |
| Empty / no Fighter on tile | `There's no target there.` |
| Good / neutral confirm | `Not the best target.` |
| Throw miss | `Your throw misses the {target}.` |

## Technical notes (non-normative)

- Path core: `src/systems/ranged_path.py`
- Player throw: `src/systems/player_throw.py`, `src/systems/item_modals.py`
- Animation: `src/systems/projectile_anim.py`; deferral in `src/engine_turn.py`
- Tests: `tests/test_ranged_path.py`, `tests/test_player_throw_pr6.py`, `tests/test_projectile_anim.py`, `tests/test_npc_abilities_range_path.py`, `tests/test_npc_abilities_smite.py`

## Related specs

| Spec | Relationship |
|------|----------------|
| `inventory-items/spec.md` | Player `f` / `F` throw flow, throwables |
| `npc-abilities/spec.md` | `SmiteN` vs `RangeN` ability handlers and AI |
| `equipment-catalog/spec.md` | Throwable tier catalog |
| `core-roguelike/spec.md` | Combat, stunned prey behavior |

## Acceptance Criteria

1. Smite ignores intermediates; Path blocks on same-alignment fighters in the beam.
2. Path first-fighter hit may differ from intended target.
3. NPC Smite logs *smites*; NPC Path logs *shoots*; player throw miss uses exact miss string.
4. Player throw defers world turn until Path animation completes; cyan trail spans full beam.
5. Smite uses magenta flash; no travel beam.
6. All requirement scenarios covered by automated tests and manual checklists.