# vore Specification

## Purpose

The **vore** domain extends the shipped core roguelike and **Enhancements 1** with predator pressure when the player is weakened: monsters may attempt vore attacks, **multi-phase modal narratives** pace outcomes, and a successful hit places the player in an **engulfed** struggle state with blindness, damage-based escape, and immunity from other attackers.

**Scope**: vore attempts, narrative modals, engulfed struggle, escape, and mercy. **Digestion** (damage, strikes, NPC removal, player game over) is specified in `openspec/specs/digestion/spec.md`.

**Terminology (inherits core policy)**

| Term | Meaning |
|------|---------|
| Defeated | Monster reaches 0 HP and is removed |
| Stunned | Player reaches 0 HP; movement/wait pass turns with tired message until HP > 0 |
| Engulfed | Player swallowed by a predator; co-located, blind, struggling |
| Vore mercy | Brief post-escape immunity: predators cannot target, damage, or vore the player for one world phase |
| Digested | Prey removed (NPC) or player game over after three digestion strikes — see `digestion` spec |

Avoid *death*, *kill*, and *die* in specs, UI, and log messages.

**Modular boundary**

Vore logic lives in `src/systems/vore.py` and optional ECS components. Core movement, FOV, and inventory contracts remain stable. `VORE_ENABLED = False` disables vore **behavior** without removing code.

**Narrative content types (v1)**

Narrative type IDs are an **extensible string list**. v1 ships `"OV"`, `"CV"`, and `"AV"`. Monsters declare which types they support. **Initiation** (new vore attempts) SHALL select modal and log narrative only from types that are both supported by the monster and enabled in the run's content preferences (snapshot from global settings at new game — see `main-menu` spec). Disabled types are **absent from new vore attempts** but do **not** change digestion follow-through for prey already engulfed under a locked `Predator.narrative_type`.

## Requirements

### Requirement: Narrative Content Types and Initiation Filtering

V1 SHALL support narrative types as distinct string labels (`OV`, `CV`, `AV` initially). Each monster SHALL declare its supported types in an open-ended tuple. On **vore initiation**, narrative SHALL be selected with **equal probability** among types that are both on the monster **and** enabled in the run's content preferences. Preferences are a **global initiation filter** snapshotted at new game; they SHALL NOT re-filter digestion or other engulf follow-through (see `main-menu` spec).

#### Scenario: Disabled types are skipped at initiation

- GIVEN a wolf with narrative types `OV`, `CV`, and `AV`
- AND the run's preferences have disabled `CV` and `AV`
- WHEN the wolf initiates a vore attempt
- THEN only `OV` narrative content may be shown in attempt/success modals and initiation logs
- AND no `CV` or `AV` initiation text appears

#### Scenario: Predator cannot initiate when no types overlap

- GIVEN a wolf with narrative types `OV` and `CV`
- AND the run's preferences enable only `AV`
- WHEN the wolf would otherwise attempt vore
- THEN no vore attempt is initiated

#### Scenario: Engulfed follow-through uses locked type

- GIVEN a predator holding prey with `Predator.narrative_type` = `CV`
- AND run preferences later disable `CV`
- WHEN digestion narrative plays
- THEN `CV` digestion content is still used

#### Scenario: Equal weight among enabled types at initiation

- GIVEN a wolf with `OV`, `CV`, and `AV` all enabled
- WHEN many vore attempts are rolled with seeded RNG
- THEN each enabled type appears with roughly equal frequency

### Requirement: Multi-Phase Modal Narrative Queue

When a monster initiates a vore attempt, the game SHALL display a centered message box over the map showing **one narrative phase at a time**. The number of phases SHALL vary by monster, narrative type, and segment (`attempt` or `success`). Only **Enter** SHALL advance to the next phase or resolve the attempt. **Ctrl+Q** SHALL be a **no-op** during the vore modal (see `main-menu` spec). Closing the window (**X**) still terminates the process. **Escape** SHALL be a no-op during the vore modal (see `enhancements-2`). All other keys SHALL be no-op while a modal is active.

Modal text SHALL **never** copy to the scrolling message log.

#### Scenario: Enter advances through attempt phases

- GIVEN a vore modal showing the first attempt phase (e.g. *"The wolf leaps toward you with its jaws open wide!"*)
- WHEN the player presses Enter
- AND more attempt phases remain
- THEN the modal shows the next attempt phase

#### Scenario: Enter advances through success phases on hit

- GIVEN a vore attempt that rolled a hit
- AND the player has advanced through all attempt phases
- WHEN the player presses Enter
- THEN success narrative phases display one at a time (e.g. swallowing progression)
- AND engulfed state applies only after Enter on the **last** success phase

#### Scenario: Movement blocked during modal

- GIVEN a vore modal is visible
- WHEN the player presses a movement key
- THEN the player does not move
- AND no new player turn advances

#### Scenario: Ctrl+Q is no-op during modal

- GIVEN a vore modal is visible
- WHEN the player presses Ctrl+Q
- THEN the vore modal remains active
- AND no quit confirmation is shown

#### Scenario: Escape does not quit during modal

- GIVEN a vore modal is visible
- WHEN the player presses Escape alone
- THEN the game continues running

### Requirement: Vore Attempt Eligibility and Decision

When the player has HP at or below 50% of max HP, monsters with line of sight MAY decide each turn to attempt vore instead of a normal chase step. **Adjacent** attempts use the modal path at distance 1. **`RangedVoreN`** predators MAY attempt vore at Chebyshev distance `[2, N]` (see `npc-abilities` spec) — on hit, prey co-locates on the predator tile before engulf/modal success phases. The decision is random and not guaranteed unless the predator has `PreferVore` (then 100% when otherwise legal). Above 50% HP, monsters SHALL never attempt vore. At 0 HP, monsters SHALL always pursue vore when adjacent; predators with `RangedVoreN` MAY also attempt ranged vore without closing (not subject to Path/Smite stunned-plink skip). Otherwise **move closer** (chase). Accidental bump-attack while closing is acceptable but not intended primary behavior.

#### Scenario: Ineligible above half health

- GIVEN a player at 16/30 HP
- AND an adjacent wolf with line of sight and `VoreCapable`
- WHEN the wolf's turn executes
- THEN the wolf does not attempt vore
- AND the wolf chases or bump-attacks normally

#### Scenario: Progressive decision chance

- GIVEN a player at 8/30 HP (eligible)
- AND an adjacent `VoreCapable` wolf with line of sight
- WHEN the wolf's turn executes many times with seeded RNG
- THEN some turns attempt vore and some chase normally
- AND decision probability increases as HP approaches 0

#### Scenario: Always attempt at zero HP when adjacent

- GIVEN a stunned player at 0/30 HP
- AND an adjacent `VoreCapable` wolf with line of sight
- WHEN the wolf's turn executes
- THEN the wolf always opens a vore attempt (subject to hit roll)

#### Scenario: Chase closer at zero HP when not adjacent

- GIVEN a stunned player at 0/30 HP
- AND a `VoreCapable` wolf with line of sight but not adjacent
- AND the wolf has no `RangedVoreN` ability
- WHEN the wolf's turn executes
- THEN the wolf moves toward the player (chase)
- AND does not attempt vore until adjacent

#### Scenario: RangedVore at zero HP without closing

- GIVEN a stunned player at 0/30 HP at distance 3 with LOS
- AND a `VoreCapable` owl mage with `RangedVore5`
- WHEN the owl acts
- THEN a vore modal may open without the owl taking a chase step

#### Scenario: No attempt while engulfed

- GIVEN a player already engulfed
- WHEN any monster's turn executes
- THEN no monster attempts vore against that player

### Requirement: Vore Hit and Miss Resolution

A vore attempt SHALL roll hit chance independently of the decision roll when the modal opens. Hit chance SHALL increase as player HP decreases. A miss SHALL waste the attempting monster's turn. After the player advances through all **attempt** phases and the attempt missed, the modal SHALL dismiss and the scrolling log SHALL report evasion. A hit SHALL proceed to **success** narrative phases before engulfed state applies.

#### Scenario: Miss dismisses modal and logs evasion

- GIVEN a vore attempt that rolled a miss
- AND the player has advanced through all attempt phases
- WHEN the player presses Enter on the last attempt phase
- THEN the modal dismisses
- AND the message log reports *"You evaded the wolf's vore attempt."* (predator display name substituted)
- AND modal attempt text does not appear in the log
- AND remaining monsters in the current world phase continue their turns
- AND no engulfed state is applied

#### Scenario: Hit proceeds to success phases

- GIVEN a vore attempt that rolled a hit
- WHEN the player advances through all attempt phases
- THEN success narrative phases display in the modal
- AND engulfed state applies only after Enter on the last success phase

### Requirement: Engulfed State

On successful vore, the player SHALL enter an engulfed state: co-located on the predator's tile, visually blind (only the player glyph visible), able to struggle via movement keys, and immune to bump attacks from other monsters. Natural HP regen (Enhancements 1) SHALL continue while engulfed.

#### Scenario: Co-location and blindness

- GIVEN the player was just engulfed
- WHEN the next frame renders
- THEN the player glyph appears on the predator's tile
- AND map tiles and other entities are not drawn
- AND dark-red `#` glyphs are drawn on all eight adjacent tiles as a decorative overlay (visual only)
- AND the HUD shows an engulfed indicator

#### Scenario: Struggle deals damage

- GIVEN an engulfed player with HP above 0
- WHEN the player presses a movement key
- THEN the message log shows a random struggle line (e.g. *"You struggle to break free."*)
- AND the predator loses a fixed amount of HP
- AND a player turn is consumed

#### Scenario: Escape on roll in entered direction

- GIVEN an engulfed player and a living predator
- WHEN a struggle move's escape roll succeeds
- AND the entered direction leads to a valid escape tile
- THEN the player is placed in that direction from the predator
- AND engulfed state is cleared

#### Scenario: Escape falls back when direction blocked

- GIVEN an engulfed player
- WHEN escape succeeds but the entered direction is invalid (wall, blocked)
- THEN the player is ejected to a random valid adjacent tile

#### Scenario: Ground prey cannot escape onto deep water

- GIVEN an engulfed **ground** player (or NPC prey)
- AND an adjacent deep water tile is otherwise free
- WHEN escape placement is resolved
- THEN the prey SHALL NOT be placed on the water tile
- AND fallback adjacent-then-nearby rules apply (see `dungeon` spec)

#### Scenario: Aquatic prey may escape onto deep water

- GIVEN an engulfed prey with **`AQUATIC`** mobility
- AND an adjacent deep water tile is free
- WHEN escape succeeds toward that tile
- THEN the prey MAY be placed on the water tile

#### Scenario: Escape displaces occupant when fully surrounded

- GIVEN an engulfed player
- WHEN escape succeeds but all adjacent tiles are invalid
- THEN the player is ejected to a random direction tile
- AND any entity on that tile is teleported to a random floor tile elsewhere

#### Scenario: Escape chance escalates per engulfment

- GIVEN an engulfed player who has failed two struggle escape rolls this engulfment
- WHEN the player struggles again without defeating the predator
- THEN the escape roll uses 25% chance (15% base + 5% × 2 failures)
- AND a subsequent escape resets the failure counter to zero for the next engulfment

#### Scenario: Immediate escape on predator defeat

- GIVEN an engulfed player
- AND a predator at 1 HP
- WHEN the player struggles
- THEN the predator is defeated
- AND the player escapes immediately

#### Scenario: Immunity from other attackers

- GIVEN an engulfed player sharing a tile with a predator
- AND a third monster adjacent to that tile
- WHEN the third monster bump-attacks the tile
- THEN the predator takes damage
- AND the engulfed player is not targeted

#### Scenario: Predator attack-only while holding prey

- GIVEN a predator holding engulfed prey
- WHEN the predator's world phase runs
- THEN the predator may bump-attack one adjacent hostile
- AND the predator does not move, chase, or initiate vore
- AND engulfed prey remains co-located

#### Scenario: Wait in belly passes turn without struggle

- GIVEN an engulfed player
- WHEN the player presses wait (`H`, numpad 5, or `.`)
- THEN a player turn is consumed
- AND no struggle damage or escape roll occurs
- AND monster turns execute afterward

#### Scenario: No natural regen while engulfed

- GIVEN an engulfed player below max HP
- WHEN the player consumes turns while still engulfed
- THEN natural regen does not apply
- AND only digestion changes HP (see `digestion` spec)

### Requirement: Post-Escape Mercy Invincibility

When the player breaks free of an engulfment (`release_engulfed`), or an NPC is freed via `release_npc_engulfed`, the prey SHALL receive **vore mercy** for the remainder of that world phase (monster turns immediately following the escape). During mercy, predators SHALL still take their turns normally, but any attempted vore, bump attack, or other hostile action against the player SHALL be quietly nullified (no damage, no modal, no log). Mercy SHALL clear at the end of `_run_world_turn`. The player MAY act normally on their next turn.

#### Scenario: Mercy blocks adjacent vore after escape

- GIVEN a player who just escaped via struggle
- AND an adjacent `VoreCapable` wolf with line of sight
- WHEN remaining monsters act in the same world phase
- THEN no vore modal opens against the player
- AND the player is not damaged

#### Scenario: Mercy blocks bump damage after escape

- GIVEN a player who just escaped via struggle
- AND a monster that would bump-attack the player this world phase
- WHEN the monster acts
- THEN the player takes no damage
- AND no hit message appears in the log

#### Scenario: Mercy expires next player turn

- GIVEN a player who escaped and received mercy
- WHEN the world phase completes and the player acts again
- THEN mercy is cleared
- AND predators may target the player normally again

### Requirement: Stunned and Engulfed Interaction

Vore does not change stunned rules. A stunned player at 0 HP SHALL remain eligible for vore attempts and **may be vored while stunned**. While engulfed at 0 HP (stunned), movement keys SHALL **not** struggle; they SHALL show *"You're too tired to move."* and pass the turn (same as stunned movement elsewhere). While engulfed with HP above 0, movement keys SHALL route to struggle. Wait while engulfed SHALL pass a turn (with tired message if stunned). All inventory category commands (`,`, `d`, `i`, `w`, `W`, `q`, `v`) SHALL be blocked while engulfed per `inventory-items` spec. Worn armor digestion mitigation still applies passively.

#### Scenario: Vore attempt against stunned player

- GIVEN a stunned player at 0 HP
- AND an adjacent `VoreCapable` wolf with line of sight
- WHEN the wolf's turn executes
- THEN the wolf may initiate a vore attempt
- AND stunned state does not block vore eligibility

#### Scenario: No struggle while stunned and engulfed at zero HP

- GIVEN a stunned player at 0 HP who is engulfed
- WHEN the player presses a movement key
- THEN the message log reports *"You're too tired to move."*
- AND no struggle damage or escape roll occurs
- AND a player turn is consumed
- AND pack commands do not open modals or consume items

#### Scenario: Stunned persists after escape at zero HP

- GIVEN a stunned engulfed player at 0 HP
- WHEN the player escapes via struggle
- THEN HP remains 0
- AND stunned state remains until HP rises above 0 via regen or potion

### Requirement: Species narrative from data

Vore attempt and success modal phases SHALL load from **`data/entities.json`** `vore_narratives` keyed by entity `id` (random variant per attempt). Hardcoded `src/vore_content.py` is removed.

#### Scenario: Wolf narrative on attempt

- GIVEN a vore attempt from a spawned wolf
- WHEN the modal opens
- THEN attempt-phase text references the wolf (not a generic monster label)
- AND text matches a variant from the wolf entry in `entities.json`

### Requirement: Offscreen NPC Vore Hit Messages

When an evil predator successfully vores adjacent good/neutral prey via `try_resolve_npc_vore`, and **neither** predator nor prey is in player FOV, the game SHALL log one random atmospheric line from the predator entity's `offscreen_vore` object in `entities.json` (keyed by narrative type `OV`, `CV`, `AV`). Legacy flat keys (`offscreen_ov`, etc.) are invalid at load. Optional `{predator}` / `{prey}` placeholders SHALL format like on-screen NPC vore logs.

Offscreen **failed** vore attempts SHALL NOT log. Missing type keys or empty type arrays SHALL NOT log and SHALL NOT fall back to on-screen pools.

When either combatant is visible, hit and miss lines SHALL come from the predator entity's `npc_vore_hit` / `npc_vore_miss` arrays (keyed by narrative type), with fallback to built-in `NPC_VORE_HIT_POOL` / `NPC_VORE_MISS_POOL` only when entity data is absent.

#### Scenario: Offscreen hit logs entity line

- GIVEN a wolf and stunned knight off-screen with a successful vore hit
- AND the wolf defines `offscreen_vore.OV`
- WHEN `try_resolve_npc_vore` resolves
- THEN one offscreen line appears in the message log
- AND no global hit-pool swallow line appears

#### Scenario: Offscreen miss is silent

- GIVEN predator and prey off-screen
- WHEN vore misses
- THEN no message is added to the log

#### Scenario: Visible hit uses entity data

- GIVEN predator and prey in player FOV
- AND the predator defines `npc_vore_hit` for the rolled type
- WHEN vore hits
- THEN a line from the predator's `npc_vore_hit` array appears (not offscreen arrays)

### Requirement: Modular Vore Boundary

Core movement, FOV, inventory, and stunned recovery SHALL remain functional when `VORE_ENABLED` is false. Core systems SHALL NOT import vore logic at module load time.

#### Scenario: Vore disabled

- GIVEN `VORE_ENABLED` is false
- WHEN the player plays a session
- THEN no vore attempts or modals occur
- AND core gameplay behaves as before vore shipped

#### Scenario: Core systems independent

- GIVEN the vore module is present on disk
- WHEN core movement and inventory modules are imported
- THEN they do not import `src/systems.vore`

## Technical Constants (defaults)

| Constant | Default | Meaning |
|----------|---------|---------|
| `VORE_HP_THRESHOLD` | 0.5 | Above: never attempt |
| `VORE_HIT_MIN` | 0.25 | Hit chance floor at threshold |
| `VORE_HIT_MAX` | 1.0 | Hit chance at 0 HP |
| `VORE_ESCAPE_BASE` | 0.15 | Initial escape chance per struggle |
| `VORE_ESCAPE_PER_FAIL` | 0.05 | Bonus per failed struggle during current engulfment |
| `VORE_STRUGGLE_DAMAGE` | 2 | Flat damage to predator per struggle |
| `VoreMercy` tag | — | Post-escape immunity for one world phase |
| Engulfed overlay | `#` at `(100,20,20)` | Decorative ring on eight adjacent tiles while blind |
| Content prefs (v1) | OV+CV+AV on | Global settings from Options; snapshotted at new game |

## Acceptance Criteria

1. At ≤50% HP, adjacent wolves sometimes attempt vore; at >50% HP, never.
2. At 0 HP, wolves chase to adjacency and always attempt vore when adjacent.
3. Vore attempts can miss; miss logs *"You evaded the {name}'s vore attempt."*; modal text never copies to log.
4. Modal appears center-screen; Enter advances through dynamic attempt/success phase queues; other gameplay keys blocked; Ctrl+Q no-op during modal.
5. Successful vore shows variable success narrative phases before engulfed state.
6. Engulfed player sees only `@` with a dark-red `#` overlay ring; struggle damages predator; escape is directional with fallback; defeat causes immediate escape.
7. Each struggle logs a random placeholder message; stunned engulfed player at 0 HP cannot struggle (tired message only).
8. Wait in belly passes turn without struggle; no natural regen while engulfed (digestion spec).
9. Engulfed player cannot be bump-attacked; third monsters hit the predator.
10. Escape grants mercy invincibility for one world phase; predators act but cannot harm or vore the player until the phase ends.
11. Escape at 0 HP leaves player stunned until regen/potion.
12. Escape tile validity respects prey mobility: ground cannot land on deep water; aquatic and fly may use water tiles when valid (`dungeon` spec).
13. `F2` debug sets all monster HP to 1.
14. All requirement scenarios demonstrable in one play session or via automated tests.
15. Core and Enhancements 1 acceptance tests still pass; import-boundary test confirms core systems do not load vore at module import time.