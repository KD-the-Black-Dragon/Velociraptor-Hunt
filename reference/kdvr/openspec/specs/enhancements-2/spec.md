# enhancements-2 Specification

## Purpose

**Enhancements 2** increases **NPC identity**: every entity is named in logs, carries an alignment that drives faction combat, may carry an optional proper name and examine text, and supports a roguelike-style **examine** command. Ships on top of core, Enhancements 1, and vore v1.

**Terminology** inherits project policy: defeated, stunned, digested — no kill/die/death.

**v1 scope of this enhancement**

- Refactor messaging and AI for identity/alignment
- Wolves remain the only spawned NPC species (evil); no `ProperName` on default spawns
- No good or neutral NPCs spawned yet — but **every NPC must have an alignment** at spawn
- Placeholder examine descriptions acceptable

**Out of scope**

- Dialogue, quests, reputation, shops
- Procedural name generation on spawn
- Good or neutral NPC spawns (behavior is specified; content deferred)

## Superseded by enhancements-3

When **enhancements-3** is active, the following behaviors from this spec are updated (see `enhancements-3` for normative detail):

- Evil **secondary** pursuit of neutral NPCs replaces “evil ignores neutral for hostility”
- Good/neutral **stunned** at 0 HP replaces immediate defeat/removal at 0 HP
- **NPC↔NPC swap** by alignment is additive; player-initiated swap with good/neutral is unchanged
- Evil **NPC vore** on good/neutral (log-only, headless engulf); player vore modal is unchanged

## Controls (summary)

| Input | Action |
|-------|--------|
| `x` | **Examine** — enter cursor mode (blocked while engulfed; see below) |
| Arrows / numpad / `TYUGHJBNM` | Move examine cursor (does not move player) |
| `Enter` | Show description modal for top entity/item on cursor tile |
| `Escape` | Cancel examine mode or examine description modal; dismiss inventory modals per `inventory-items` spec. Does **not** quit. Digestion modals unaffected. |
| `Ctrl+Q` | Quit the game (replaces Escape-as-quit from core) |

## Identity model

| Field | Component | Log example | When absent |
|-------|-----------|-------------|-------------|
| Species / type | `DisplayName` (species string) | *the wolf* | Fallback `"creature"` |
| Proper name | `ProperName` (optional) | *Bob* | Species used instead |
| Alignment | `Alignment` enum | drives AI | **Invalid** — required on NPCs |
| Examine text | `ExamineDescription` | modal body | Generic placeholder per type |

**Log name rule:** If `ProperName` is set, use it verbatim (no article). Otherwise use `"the {species}"` with lowercase species unless sentence-initial.

**Examples**

| ProperName | DisplayName | Log example |
|------------|-------------|-------------|
| — | wolf | *You hit the wolf for 2 damage.* |
| Bob | knight | *Bob hits the wolf for 1 damage.* |
| — | knight | *You hit the knight for 2 damage.* — **swap** if knight is good/neutral |

## Requirements

### Requirement: Species-Based Combat Messages

All gameplay log messages that refer to an NPC SHALL use the shared identity resolver. Generic strings such as *"the monster"* SHALL NOT appear in player-visible combat or defeat messages.

#### Scenario: Player hits wolf by species

- GIVEN a wolf with `DisplayName(name="wolf")` and no `ProperName`
- WHEN the player bump-attacks the wolf
- THEN the log reports *"You hit the wolf for {damage} damage."* (or no-damage variant)

#### Scenario: Proper name overrides species in NPC combat

- GIVEN an NPC with `ProperName(name="Bob")` and `DisplayName(name="knight")`
- WHEN Bob attacks the wolf
- THEN the log reads *"Bob hits the wolf for {damage} damage."*
- AND does not say *"the knight hits the wolf"*

### Requirement: NPC Alignment

Every NPC with `AI` SHALL have an `Alignment` of `good`, `evil`, or `neutral`. Spawn code SHALL assign alignment explicitly. v1 wolf spawns SHALL be `evil` with no default `ProperName`.

#### Scenario: Wolf spawns evil

- GIVEN a new game
- WHEN monsters are spawned
- THEN each wolf has `Alignment.evil`

#### Scenario: Missing alignment is invalid

- GIVEN an NPC with `AI` and no `Alignment`
- WHEN the game would run monster turns
- THEN behavior is undefined; tests SHALL require alignment on all spawned NPCs

### Requirement: Evil Alignment Combat

Evil NPCs SHALL treat **good NPCs** and the **player** as hostile when they have line of sight. Evil NPCs SHALL pursue and bump-attack hostile targets. When multiple hostiles are visible, evil SHALL target the **nearest** hostile (Chebyshev distance). When several hostiles tie for nearest distance, evil SHALL pick one **at random**. Evil SHALL NOT treat neutral NPCs as hostiles.

#### Scenario: Evil wolf attacks player on sight

- GIVEN an evil wolf with line of sight to the player
- WHEN the wolf acts
- THEN the wolf moves toward or attacks the player

#### Scenario: Evil attacks good NPC

- GIVEN an evil wolf and a good knight with mutual line of sight
- WHEN the wolf acts
- THEN the wolf may move toward or attack the knight

#### Scenario: Evil picks nearest hostile

- GIVEN an evil wolf with line of sight to both the player and a good knight
- AND the player is farther away than the knight
- WHEN the wolf acts
- THEN the wolf targets the knight

#### Scenario: Evil random tie-break among equidistant hostiles

- GIVEN an evil wolf with line of sight to the player and a good knight
- AND both are the same Chebyshev distance from the wolf
- WHEN the wolf acts repeatedly with varied RNG
- THEN the wolf sometimes targets the player and sometimes the knight

#### Scenario: Evil ignores neutral NPC

- GIVEN an evil wolf and a neutral NPC with line of sight
- WHEN the wolf acts
- THEN the wolf does not path toward the neutral NPC as a hostile target
- AND does not bump-attack the neutral NPC unless blocked by movement collision

### Requirement: Good Alignment Combat

Good NPCs SHALL treat **evil NPCs** as hostile and pursue/attack them on sight. Good NPCs SHALL **not** attack the player, SHALL NOT bump or swap with the player, and SHALL NOT initiate vore against any target.

#### Scenario: Good attacks evil

- GIVEN a good knight and an evil wolf with line of sight
- WHEN the knight acts
- THEN the knight moves toward or attacks the wolf

#### Scenario: Good ignores player

- GIVEN a good knight with line of sight to the player and no adjacent evil
- WHEN the knight acts
- THEN the knight does not attack the player
- AND does not attempt to move onto the player's tile

#### Scenario: Good bumping player does nothing

- GIVEN a good knight adjacent to the player
- WHEN the knight's AI would step onto the player tile
- THEN the knight does not attack or swap with the player
- AND the knight does not occupy the player tile

#### Scenario: Good never attempts vore

- GIVEN a good NPC with `VoreCapable` tag (misconfigured spawn)
- AND a stunned player at 0 HP adjacent
- WHEN the good NPC's turn executes
- THEN no vore modal opens

### Requirement: Neutral Alignment

Neutral NPCs SHALL be **indifferent to the player**: they do not attack, pursue, or swap with the player. When a **evil** NPC with line of sight is within flee range, neutral NPCs SHALL **flee** (move away from the nearest visible evil). Neutral NPCs SHALL NOT initiate vore. Neutral NPCs SHALL NOT attack evil unless a future rule adds retaliation (v1: flee only, no counter-attack).

#### Scenario: Neutral does not hunt player

- GIVEN a neutral NPC with line of sight to the player
- WHEN the NPC acts
- THEN it does not path toward the player for combat

#### Scenario: Neutral flees from evil

- GIVEN a neutral NPC and an evil wolf with mutual line of sight
- WHEN the neutral NPC acts
- THEN it moves to increase distance from the wolf when a legal flee step exists

#### Scenario: Neutral bumping player does nothing

- GIVEN a neutral NPC adjacent to the player
- WHEN the neutral NPC's AI would step onto the player tile
- THEN the neutral does not attack or swap with the player
- AND the neutral does not occupy the player tile

### Requirement: Player-Initiated Swap with Good or Neutral NPCs

Only the **player** may initiate a position swap. When the player bumps a **good** or **neutral** NPC, the game SHALL **swap positions** instead of dealing damage. The swap SHALL consume a player turn and advance the world phase. The swapped NPC SHALL **skip its next scheduled turn** in that world phase. Evil NPCs are never swapped — bump attacks resolve normally.

#### Scenario: Swap with good NPC

- GIVEN a conscious player adjacent to a good knight
- WHEN the player moves into the knight's tile
- THEN the player and knight exchange positions
- AND no damage is dealt
- AND no attack message is logged
- AND monster turns run with the knight skipped once

#### Scenario: Swap with neutral NPC

- GIVEN a conscious player adjacent to a neutral NPC
- WHEN the player moves into the neutral's tile
- THEN the player and neutral exchange positions
- AND the neutral is skipped once this world phase

#### Scenario: Player may still attack evil

- GIVEN a player adjacent to an evil wolf
- WHEN the player moves into the wolf's tile
- THEN a normal bump attack resolves
- AND identity-named hit/defeat messages appear

#### Scenario: Stunned player cannot swap

- GIVEN a stunned player adjacent to a good or neutral NPC
- WHEN the player presses a movement key into that NPC
- THEN the tired message appears
- AND no swap occurs
- AND a turn is consumed (Enhancements 1 stunned movement rule)

### Requirement: NPC Versus NPC Combat

When an NPC bump-attacks another NPC, damage and defeat SHALL resolve using the same combat rules as player bump combat. Messages SHALL name both parties (proper name or species as appropriate).

#### Scenario: Evil defeats good

- GIVEN an evil wolf bump-attacking a good knight
- WHEN damage reduces the knight to 0 HP
- THEN the log reports the knight defeated using its identity string
- AND the knight entity is removed

#### Scenario: Good defeats evil

- GIVEN a good knight defeating an evil wolf
- WHEN the wolf reaches 0 HP
- THEN the log reports defeat using the wolf's identity string (e.g. *"The wolf was defeated."*)

### Requirement: Examine Command

The player SHALL press **`x`** to examine. Examine SHALL **not** consume a player turn. While **engulfed**, pressing `x` SHALL NOT enter examine mode; the message log SHALL report *"You can't see anything!"* During normal play, `x` enters **examine mode** with cursor on the player tile. Movement keys move the cursor within map bounds. **`Enter`** opens a centered description modal for the top inspectable entity on that tile. **`Escape`** cancels examine mode or dismisses an open examine description modal back to cursor mode. Examine mode blocks normal gameplay input.

#### Scenario: Enter examine from gameplay

- GIVEN normal gameplay (not engulfed)
- WHEN the player presses `x`
- THEN examine mode activates with cursor on the player tile
- AND the player does not move
- AND no turn is consumed

#### Scenario: Examine blocked while engulfed

- GIVEN an engulfed player
- WHEN the player presses `x`
- THEN examine mode does not activate
- AND the message log reports *"You can't see anything!"*
- AND no turn is consumed

#### Scenario: Examine wolf description

- GIVEN examine cursor on a wolf tile
- WHEN the player presses Enter
- THEN a modal shows the wolf's `ExamineDescription` text
- AND modal text does not copy to the message log

#### Scenario: Examine potion on floor

- GIVEN examine cursor on a health potion tile
- WHEN the player presses Enter
- THEN a modal shows full item stats (heal amount, examine text) per `inventory-items` spec

#### Scenario: Examine empty floor

- GIVEN examine cursor on an empty floor tile
- WHEN the player presses Enter
- THEN a modal reports nothing inspectable (or bare floor message)

#### Scenario: Cancel examine with Escape

- GIVEN examine mode active
- WHEN the player presses Escape
- THEN examine mode ends
- AND no player turn is consumed
- AND the game does not quit

#### Scenario: Gameplay blocked during examine

- GIVEN examine mode active
- WHEN the player presses a movement key
- THEN only the examine cursor moves
- AND the player entity does not move

### Requirement: Quit and Cancel Keys

**`Ctrl+Q`** opens quit confirmation during gameplay (see `main-menu` spec). **`Escape`** SHALL cancel examine mode and examine description modals, and SHALL dismiss inventory modals (not digestion modals) per `inventory-items` spec. **`Escape`** SHALL NOT quit the game. During vore and digestion narrative modals, **`Escape`** SHALL remain a no-op.

#### Scenario: Ctrl+Q quits from gameplay

- GIVEN normal gameplay
- WHEN the player presses `Ctrl+Q`
- THEN the game window closes without error

#### Scenario: Escape does not quit from gameplay

- GIVEN normal gameplay
- WHEN the player presses Escape alone
- THEN the game continues running

#### Scenario: Escape cancels examine only

- GIVEN examine mode active
- WHEN the player presses Escape
- THEN examine mode ends
- AND the game continues running

### Requirement: Enhanced Descriptions on All Inspectables

Every spawned NPC and floor item SHALL have an `ExamineDescription` string at spawn. Placeholder prose is acceptable in v1.

#### Scenario: Wolf examine placeholder

- GIVEN a spawned wolf
- WHEN examined
- THEN description text is non-empty
- AND references the wolf's vicious/ferocious nature (placeholder acceptable)

#### Scenario: Potion examine placeholder

- GIVEN a spawned health potion
- WHEN examined
- THEN description mentions restoring vigor/health (placeholder acceptable)

### Requirement: Vore and Identity Integration

Vore logs and modals SHALL use predator identity (species or proper name). Vore attempts SHALL remain **player-targeted only**. Good and neutral alignment SHALL never attempt vore. Evil alignment vore rules are otherwise unchanged from the `vore` spec.

#### Scenario: Vore evasion uses predator identity

- GIVEN a wolf's vore attempt misses
- WHEN the modal resolves
- THEN the log reports *"You evaded the wolf's vore attempt."*

#### Scenario: Good adjacent to stunned player

- GIVEN a good NPC adjacent to a stunned player at 0 HP
- WHEN the good NPC acts
- THEN no vore attempt occurs

## Technical notes (non-normative)

- Shared helper: `entity_log_name(entity, *, sentence_start: bool)` in `src/systems/naming.py`
- `DisplayName` retained as species/type label; optional `ProperName` added
- Flee AI: pick legal step that maximizes Chebyshev distance to nearest visible evil
- Good/neutral stepping onto player: treat player tile as non-walkable for NPC pathing
- Swap skip-turn: `skipped_this_phase` set on engine, cleared end of `_run_world_turn`
- Quit: handle `KeySym.q` with `Modifier.CTRL` in engine; remove Escape quit branch

## Acceptance Criteria

1. No player-visible log string says "monster" when referring to a known NPC species.
2. Wolves spawn evil with examine description; potions have examine description.
3. Evil wolves attack player; evil targets nearest hostile with random tie-break; good (in tests) attacks evil only.
4. Player swaps with good/neutral; good/neutral never attack or swap onto player.
5. Neutral flees from visible evil (in tests when spawned).
6. Good/neutral never open vore modal.
7. Examine is free; engulfed `x` logs *"You can't see anything!"*; Escape cancels examine; Ctrl+Q quits.
8. Proper name overrides species in all relevant log templates.
9. Core, Enhancements 1, and vore automated tests updated and remain green.