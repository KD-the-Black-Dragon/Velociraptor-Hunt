# enhancements-3 Specification

## Purpose

**Enhancements 3** adds **faction NPC content** (knight, rabbit), revamps **NPC AI** with memory and exploration, introduces **NPC stunned/regen**, **NPC↔NPC swap**, and **log-only NPC vore** with headless engulf. Builds on core, Enhancements 1–2, and vore v1.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Scope

### In scope

- Knight (good) and rabbit (neutral) — spawn counts from `entities.json` weights (see `npc-data` spec)
- AI: pursue → last known → explore; evil tiered targeting
- Good/neutral stunned at 0 HP; evil defeated at 0 HP
- NPC regen (good/neutral = player rate; evil slower)
- NPC↔NPC swap by alignment rules
- Evil NPC vore on good/neutral (log pools OV/CV/AV; headless engulf)
- Free engulfed good/neutral by defeating predator

### Out of scope

- ~~Procedural dungeon population / spawn tables~~ — shipped as weight-based data in `npc-data`
- Vore content preference UI (prefs structure future-proofed only)

**Digestion** (damage, strikes, NPC removal, player game over) ships in `openspec/specs/digestion/spec.md`.

## Requirements

### Requirement: Faction NPC Types

The game SHALL spawn **wolves** (evil), **knights** (good), and **rabbits** (neutral) from **`data/entities.json`** weight pools on `new_game()`. Stock weights reproduce land counts **6** / **5** / **6**. Knights SHALL render as cyan **`k`**. Rabbits SHALL render as grey **`r`**. Each SHALL have `DisplayName`, `NPCAlignment`, and `ExamineDescription`. See `openspec/specs/npc-data/spec.md`.

#### Scenario: Weighted population parity

- GIVEN a new game
- WHEN monsters are spawned
- THEN the map contains wolves, knights, and rabbits in land counts (**6** / **5** / **6**)
- AND wolves are evil and `VoreCapable`
- AND knights are good and not `VoreCapable`
- AND rabbits are neutral and not `VoreCapable`
- AND land NPC totals are unchanged when aquatic predators spawn (see `dungeon` spec)

#### Scenario: Sharks on water floors only

- GIVEN a generated floor with deep water
- WHEN aquatic predators spawn
- THEN exactly **two** sharks appear on water tiles
- AND sharks are evil, `VoreCapable`, and `AQUATIC`

- GIVEN a floor with no deep water
- WHEN spawn runs
- THEN no sharks appear

### Requirement: Good and Neutral Stunned at Zero HP

When a **good** or **neutral** NPC reaches 0 HP from damage, it SHALL become **stunned**: remain on the map at 0 HP, gain the `Stunned` tag, and not be removed. The log SHALL report *"{Name} is stunned!"* (sentence-start capitalization). **Evil** NPCs at 0 HP SHALL be **defeated** and removed (unchanged).

Good/neutral NPCs SHALL only be removable via **digestion** (`openspec/specs/digestion/spec.md`). Stunned good/neutral remain on the map until digested or freed from engulf.

#### Scenario: Knight stunned by wolf

- GIVEN a knight with 1 HP
- WHEN a wolf deals 1+ damage
- THEN the knight remains on the map at 0 HP
- AND the log reports the knight is stunned
- AND the knight is not defeated/removed

#### Scenario: Wolf defeated at zero

- GIVEN a wolf at 1 HP
- WHEN damage reduces it to 0 HP
- THEN the wolf is removed
- AND the log reports defeat

#### Scenario: Knight recovers from stunned

- GIVEN a stunned knight at 0 HP
- WHEN natural regen raises HP above 0
- THEN `Stunned` is cleared
- AND the log reports the knight is no longer stunned

### Requirement: NPC Natural Regen

Good and neutral NPCs SHALL regenerate **+1 HP every 8 player turns** when below max HP (same cadence as the player). Evil NPCs SHALL regenerate **+1 HP every 12 player turns** when below max HP. Regen SHALL run during the player-turn regen phase.

### Requirement: Evil AI Priority

Evil NPCs SHALL act every turn unless stunned, holding engulfed prey (sync + optional adjacent attack only; see `digestion` spec), or skipped. Intent priority:

1. **Fight** visible good NPCs or the player (nearest hostile, random tie-break)
2. **Move toward** last known position of a good NPC or player if recently seen
3. **Fight** visible neutral NPCs (nearest, random tie-break)
4. **Move toward** last known neutral position if recently seen
5. **Explore:** BFS-reachable far landmark goal and BFS one-step movement (see **NPC Explore and Wander**)

A higher-priority target SHALL preempt lower-priority intent immediately (e.g. seeing the player while chasing a rabbit switches to the player).

Evil SHALL update last-known positions when hostiles are visible. Last-known SHALL clear when that tile is reached.

#### Scenario: Wolf prefers knight over rabbit

- GIVEN a wolf with line of sight to both a knight and a rabbit
- AND the knight is not farther than the rabbit (or is the only primary hostile)
- WHEN the wolf acts
- THEN it pursues the knight (or player if visible as primary)

#### Scenario: Wolf chases rabbit when quiet

- GIVEN a wolf with no line of sight to player or good NPCs
- AND line of sight to a rabbit
- WHEN the wolf acts
- THEN it pursues the rabbit while the rabbit flees

### Requirement: Good AI Priority

Good NPCs SHALL **ignore** neutral NPCs and other good NPCs as AI targets (no chase, follow, or memory toward them). Chase/follow pathing SHALL NOT treat **other good NPC** tiles as valid steps toward the player or evil (may wait behind an ally); **neutral** tiles may be treated as swappable corridor steps. Incidental same-alignment bump swap may still occur outside chase pathing.

Priority:

1. **Fight** visible evil NPCs (highest)
2. Else if **player** visible: **follow** — move to stay close to the player
3. Else move toward **last known evil** position (if any); clear when reached
4. Else move toward **last known player** position (if any); clear when reached
5. Else **explore:** BFS-reachable far landmark goal and BFS one-step movement (see **NPC Explore and Wander**)

Evil in line of sight SHALL preempt follow, memory, and explore immediately.

**Follow / player bump:** Good NPCs MAY path toward the player and attempt to step onto the player tile. That step SHALL be a **no-op** (no swap, no damage, no message-log line). The game MAY emit a **console-only** debug line: *"the knight attempted to swap with the player"* (identity-filled via naming resolver). The player SHALL NOT see in-game feedback for this.

Good NPCs SHALL NOT attack the player.

#### Scenario: Knight attacks evil over following player

- GIVEN a knight with line of sight to both a wolf and the player
- WHEN the knight acts
- THEN it pursues or attacks the wolf
- AND does not prioritize following the player

#### Scenario: Knight follows player when quiet

- GIVEN a knight with line of sight to the player
- AND no evil NPC in line of sight
- WHEN the knight acts repeatedly
- THEN it moves to stay close to the player

#### Scenario: Knight moves toward last known player

- GIVEN a knight that previously saw the player
- AND the player is no longer visible
- AND no evil is visible
- WHEN the knight acts
- THEN it moves toward the player's last known tile

#### Scenario: Knight bump into player is silent no-op

- GIVEN a knight adjacent to the player
- AND the knight's follow step would enter the player tile
- WHEN the knight acts
- THEN the player position is unchanged
- AND no line is added to the scrolling message log

### Requirement: Neutral AI

Neutral NPCs with **HP > 0** SHALL flee from visible evil (maximize distance). At **0 HP (stunned)**, neutral NPCs SHALL NOT move voluntarily. When not fleeing and not stunned, neutral NPCs SHALL explore using the shared **NPC Explore and Wander** rules (player tile blocked for goals/steps; player-adjacent tiles allowed).

Neutral NPCs SHALL NOT attack.

### Requirement: NPC Alignment Swap

When an NPC bumps another NPC of a compatible alignment, they SHALL **swap positions** instead of attacking:

| Actor | May swap with |
|-------|----------------|
| Good | good, neutral |
| Neutral | good, neutral |
| Evil | *(none — bump combat)* |

**No NPC** SHALL initiate swap with the **player**. The **player** MAY still initiate swap with good or neutral only (Enhancements 2). Cross-alignment NPC bumps SHALL resolve as combat (or vore if eligible).

Swapped NPCs SHALL skip their next turn in the current world phase.

#### Scenario: Knights pass in corridor

- GIVEN two good knights bumping in a corridor
- WHEN one steps into the other
- THEN they swap positions
- AND no damage is dealt

#### Scenario: Wolves bump combat

- GIVEN two evil wolves adjacent in a corridor
- WHEN one steps into the other
- THEN they do **not** swap positions
- AND bump combat resolves normally

### Requirement: NPC Explore and Wander

When an NPC is in **explore** or **wander** (not visible chase, follow, flee, or memory pursuit), all alignments SHALL share the same explore pipeline:

**Goal pick:** BFS from the NPC over mobility-passable terrain (closed doors block unless a future `hands` ability stub applies). Goals SHALL be chosen from the reachable set via **weighted random** favoring farther tiles. If the current goal is not reachable (e.g. door closed), re-pick immediately. On **explore frustration** give-up (8–12 failed steps), clear the goal, **force one farthest-endpoint pick**, then resume weighted-random far picks.

**Explore step:** Among legal adjacent moves, prefer the tile with lowest BFS path distance to the goal (one step on a shortest route). If no step reduces path distance, **sidestep** (any legal move). Zero legal moves: stand still (counts as failed step). **20% idle chance** per explore turn to wait (never during pursuit/chase).

**Frustration:** Failed step = no move or no BFS path-distance progress; progress resets frustration. Sidestep without progress counts as failed.

**Oscillation:** 4-step ABAB position or path-distance pattern SHALL trigger immediate opposite-goal re-pick.

**Explore pathing:** Other NPC-occupied tiles SHALL be treated as blocked (plan around allies).

**Unreachable memory:** When a last-known quarry tile is no longer terrain-reachable, clear it immediately (do not memory-chase through closed doors).

**Door spite:** When unreachable memory was blocked only by a closed door, clear memory and start `door_spite_turns_left` (8–12), stand still (no memory chase, no explore) until expired, then explore. Quarry becoming visible cancels spite.

**Door shock (detour case):** When last-known is still terrain-reachable but a closed door is an adjacent Euclidean step toward that tile (door slammed in face), start a short shock wait (2–4 turns) **without** clearing memory, then resume path-aware memory pursuit (detour). Shock only triggers early in a blind trail (not every time the NPC revisits a door).

**Memory trail timeout (mandatory fairness):** While holding any last-known quarry and the quarry is **not** visible, each monster visit increments `memory_blind_turns`. On first blind tick of an episode, roll `memory_blind_limit` in **12–18**. When `memory_blind_turns >= memory_blind_limit`, clear all last-known (and come-here) as if giving up chase — the trail is cold even if a path still exists. Re-acquiring LOS resets the blind counter. This prevents perfect long-range homing via map pathing.

**Memory pursuit pathing:** When pursuing a last-known tile (no visible quarry), steps SHALL follow **BFS path distance** to that tile over explore-walkable terrain (same door/hands rules as explore reachability). Do not Euclidean-greedy into a closed door when a longer open path exists. No legal path-progress step increments chase frustration; give-up clears memory as today. Trail timeout (above) also ends pursuit.

**Neutral only:** Player tile SHALL be blocked for explore goal pick and steps (`_forbidden_tiles`); player-adjacent tiles remain valid.

**Unchanged:** Visible chase, follow, and flee remain **greedy** one-step (not BFS explore routing).

#### Scenario: Explore goal respects closed door

- GIVEN a wolf on one side of a closed door
- WHEN it picks an explore goal
- THEN the goal is on the wolf's reachable side of the door

#### Scenario: Wolf door spite then disperses

- GIVEN a wolf whose quarry fled behind a closed door
- WHEN memory is cleared and door spite expires
- THEN the wolf picks a reachable far goal and wanders away from the door

#### Scenario: Memory chase takes detour around closed door

- GIVEN a wolf with last-known primary still terrain-reachable only via a long open path
- AND a closed door on the short Euclidean route
- WHEN the wolf memory-pursues after a short door shock
- THEN it follows the open detour rather than dancing on the door face indefinitely
- AND if the wolf never re-acquires LOS within the trail timeout (12–18 blind turns), it gives up even if the path remains

#### Scenario: Cold trail ends memory chase

- GIVEN a wolf holding last-known primary with no LOS
- WHEN blind turns reach the rolled trail limit without seeing the quarry again
- THEN last-known is cleared and the wolf stops pathing to that tile

#### Scenario: Neutral rabbit uses corridor explore

- GIVEN a rabbit exploring in a corridor with no flee stimulus
- WHEN it steps toward an explore goal
- THEN it follows BFS shortest-route steps (not greedy wall-cutting)

### Requirement: NPC Vore (Log Only)

Evil NPCs with `VoreCapable` MAY attempt vore on adjacent **good** or **neutral** NPCs using the same eligibility and hit rolls as player vore (HP threshold, RNG). Good and neutral SHALL never attempt vore.

Attempts SHALL **not** open a modal. When predator or prey is in player FOV, miss and hit outcomes SHALL log a randomly chosen line from the predator entity's `npc_vore_hit` / `npc_vore_miss` objects (keyed by narrative type **OV**, **CV**, **AV**), falling back to built-in pools only when entity data is missing. Narrative type selection remains filtered by `VoreContentPreferences`. When **both** are off-screen, successful hits MAY log from `offscreen_vore[type]`; misses SHALL be silent (see `vore` spec). Messages SHALL use identity naming for predator and prey when placeholders are present.

On **hit**, the prey SHALL enter **headless engulf** (co-located with predator, `Engulfed` + `Predator` with `narrative_type`, prey does not act). Digestion ticks apply per `digestion` spec.

#### Scenario: Miss logs attempt

- GIVEN an adjacent stunned knight and a wolf that rolled a vore attempt miss
- WHEN the attempt resolves
- THEN a miss line appears in the message log
- AND no modal opens

#### Scenario: Hit engulfs without modal

- GIVEN a wolf that rolled a vore hit on a stunned knight
- WHEN the attempt resolves
- THEN a hit line appears in the message log
- AND the knight is engulfed headlessly
- AND no modal opens

### Requirement: Rescue Engulfed Allies

When a predator holding a good or neutral prey is **defeated** (0 HP, evil defeat path), the prey SHALL be released (same as player release path, adapted for NPCs). The player and good NPCs MAY defeat the predator via normal bump combat to free the prey.

### Requirement: Good Allies Follow on Descent

When the player descends to a new floor (`Shift+.` on downstairs), any **good** NPC with **line of sight** to the player at descent time SHALL follow: the entity is preserved and placed on the new floor as close as possible to the entrance (mobility-aware valid land tiles). **Neutral** and **evil** NPCs do not follow. Knights that follow are not re-spawned again on the new floor (deducted from fresh knight spawn count). See `openspec/specs/dungeon/spec.md`.

#### Scenario: Knight in LOS follows downstairs

- GIVEN a good knight visible to the player
- AND the player descends from a downstairs tile
- WHEN the new floor is generated
- THEN the knight appears on the new floor near the entrance
- AND the knight is not duplicated by fresh knight spawns

### Requirement: Supersedes Enhancements 2

- Evil **secondary** pursuit of neutral NPCs replaces “evil ignores neutral for hostility”
- Good/neutral **stunned** replaces immediate defeat at 0 HP
- NPC↔NPC swap is additive; player swap rules unchanged

## Technical notes (non-normative)

- `AIState` component for memory, explore goals, explore frustration, door spite, chase frustration/momentum
- Explore implementation in `src/systems/ai.py` (`explore_reachable_distances`, `_choose_explore_direction`, `_complete_explore_step`)
- NPC vore log objects in `entities.json`: `npc_vore_hit`, `npc_vore_miss`, `offscreen_vore`, `offscreen_digest`; `src/vore_npc_content.py` as on-screen fallback pools
- Spawn via `spawn_floor_population()` and `data/entities.json` (`openspec/specs/npc-data/spec.md`)
- Good-ally descent follow in `src/systems/descent.py`
- Manual `testing-checklist-prN.md` per PR before merge