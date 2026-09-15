# npc-abilities Specification

## Purpose

**npc-abilities** implements runtime handlers for `abilities[]` tokens on NPC entities in `data/entities.json`. Abilities modify turn budget, intent, ranged engagement, combat hooks, and one-shot summon behavior. They integrate with the shared alignment-aware intent pipeline in `src/systems/ai.py` and preserve shipped vore turn-order semantics (`openspec/specs/vore/spec.md`).

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Baseline AI** without abilities remains defined in `openspec/specs/enhancements-3/spec.md`. This spec documents **deltas only**.

## Scope

### In scope

- Ability token parsing (`src/data/ability_parser.py`)
- Load-time filter (`src/data/abilities.py` — implemented kinds only)
- `Abilities` / `AbilityState` ECS components
- `compute_action_plan()` stacking: Slow → Erratic shape → Fast multiplier
- Shared intent pipeline steps (summon, coward, ranged, vore, alignment chase)
- Combat hooks: Knockback, Lifedrain
- FOV-gated activation logs for Summon, SmiteN smite, RangeN shoot, Knockback, Lifedrain

### Out of scope

- Item `abilities[]` in weapon/armor JSON (warn-only)
- Hot-reload mid-run
- Undocumented ability tokens (warn and drop at load)

## Requirements

### Requirement: Ability load and spawn

Implemented ability tokens SHALL parse at load, attach to spawned entities as `Abilities`, and initialize `AbilityState` on every NPC spawn (`spawn_from_definition`, `spawn_test_npc`).

Unknown tokens SHALL warn once and be omitted. Documented-but-unimplemented tokens SHALL warn once and be omitted. Duplicate `SmiteN`, `RangeN`, and `RangedVoreN` tokens SHALL each collapse to max N within their family with a warning (families are independent).

#### Scenario: Stock wolf loads Range6

- GIVEN shipped `entities.json` wolf with `abilities: ["Range6"]`
- WHEN the registry loads and a wolf spawns
- THEN no ability warnings are emitted for the wolf
- AND the wolf may Path-shoot at distance 2–6 when a clear beam exists

### Requirement: SmiteN ranged engagement

`Smite2`…`Smite9` SHALL enable **Smite** ranged attacks at Chebyshev distance in `[2, N]` with LOS. Adjacent targets SHALL use melee. Stunned 0 HP prey SHALL be closed, not shot.

Ranged damage SHALL use `ranged_accuracy`, `ranged_min_damage`, `ranged_max_damage` when present; else melee stats.

Smite attempts SHALL log FOV-gated **smite** templates (`npc_smites_target`, `npc_smites_target_no_damage`, `npc_smites_at_target_miss`). Smite SHALL ignore entities between shooter and target.

**Hostility:** Smite SHALL only fire at alignment-hostile targets (same policy as Path `shooter_can_damage`). Chase follow targets that are not hostile (e.g. good ally following the player) SHALL NOT be smited; the shooter SHALL fall through to normal Smite target pick (or skip the shot).

**AI:** When no valid Smite shot, walk toward target (unchanged from legacy ranged engagement). No path simulation.

#### Scenario: Slime smites at range 3 not 1

- GIVEN a slime with `Smite3` and LOS at distance 3
- WHEN the slime acts
- THEN a smite attempt may occur
- AND at distance 1 the slime uses melee instead

#### Scenario: Good Smite does not hit the player while following

- GIVEN a good NPC with `Smite5`, line of sight to the player at Chebyshev distance in `[2, 5]`, and no visible evil
- WHEN the ally acts (follow / chase target is the player)
- THEN no Smite attempt targets the player
- AND the player is not damaged by Smite

#### Scenario: Good Smite still hits evil when available

- GIVEN a good NPC with `Smite5`, a visible evil in Smite range, and the player also in range
- WHEN the ally acts
- THEN a Smite attempt may target the evil
- AND SHALL NOT target the player

### Requirement: RangeN Path ranged engagement

`Range2`…`Range9` SHALL enable **Path** ranged attacks at Chebyshev distance in `[2, N]` with LOS and a clear bresenham beam per `ranged-targeting` spec. Adjacent targets SHALL use melee. Stunned 0 HP prey SHALL be closed, not shot.

Ranged damage SHALL use `ranged_accuracy`, `ranged_min_damage`, `ranged_max_damage` when present; else melee stats.

Path shoot attempts SHALL log FOV-gated **shoot** templates (`npc_shoots_target`, `npc_shoots_target_no_damage`, `npc_shoots_at_target_miss`). Same-alignment fighters on the beam cancel the shot before firing.

**Target selection:** Among candidates in `[2, N]` with LoS, filter to those where `path_shot_valid(shooter, intended_target)` — no same-alignment blockers and beam reaches a damageable fighter. Pick **nearest** Chebyshev (tie random).

**No valid shot:**

| Alignment | Behavior |
|-----------|----------|
| **Evil** | **Kite:** prefer Chebyshev distance **N** (step away if too close, closer if too far, else explore/chase) |
| **Good** | If player visible and within **N** tiles: maintain **1–2 tiles** from player while seeking a shot; else chase visible evils |

Path shots SHALL queue cyan projectile animation when FOV-gated at queue time.

#### Scenario: Wolf shoots at range 2 not 1

- GIVEN a wolf with `Range6` and a clear Path at distance 4
- WHEN the wolf acts
- THEN a shoot attempt may occur with *shoots* log
- AND at distance 1 the wolf uses melee instead

#### Scenario: Ally blocks Path shot

- GIVEN an evil wolf with `Range6` and a good NPC on the beam to the player
- WHEN the wolf evaluates a Path shot
- THEN the shot is cancelled (no shoot log, no damage)

### Requirement: NPC Path/Smite magazine (shots)

NPCs with `RangeN` and/or `SmiteN` SHALL carry a **RangedMagazine** (`current`, `maximum`). Maximum SHALL come from the run difficulty profile:

| Alignment | Difficulty field | Stock |
|-----------|------------------|-------|
| Good | `good_ranged_shots` | **2** on all difficulties |
| Evil / neutral | `evil_ranged_shots` | **2** on easier/normal/hard; **3** on nightmare |

Omit → default **2** / **2**. Values MUST be integers **≥ 1**. Current SHALL start at maximum at spawn/summon. Depth bake and prefixes SHALL NOT change `maximum`.

**Spend:** A Path or Smite attempt (hit or miss) SHALL spend **1** shot when the attack actually fires. At `current == 0`, Path/Smite SHALL NOT fire. **`RangedVoreN` SHALL NOT spend** a shot. Player throws / player Smite are out of scope.

**Reload:** A dedicated silent NPC turn recovers **+1** shot (capped at maximum). No message log.

**AI priority (after summon / flee / in-range vore):**

1. **Evil hunger:** While engaging a vore-eligible quarry out of adjacent/`RangedVoreN` range, roll the usual vore decision (`PreferVore` → always). On commit: **step toward** the quarry that turn; **do not** Path/Smite. (In-range vore remains the normal modal/NPC vore path.) Compatible with `NoChase` while quarry is visible.
2. Adjacent **melee** (and prior in-range **vore**) outrank reload.
3. At **0** shots: prefer reload unless adjacent melee is available.
4. If shots remain and a legal Path/Smite exists: shoot.
5. **Good** RangeN/SmiteN: prefer reload up to maximum whenever **no evil is in sight**.
6. At **1** shot: reload only when **idle** (no sighted chase target and not memory-chasing). NEVER reload to maximum while seeing or actively chasing a target.
7. Else existing reposition / chase / explore (including distance-1 no-shoot).

Intentional feel: DCSS centaur-like — strong at range, inefficient, weak once adjacent (existing Chebyshev 1 no-shoot preserved).

#### Scenario: Empty magazine blocks Smite

- GIVEN an NPC with `Smite5` and `RangedMagazine.current == 0`
- WHEN `try_smite_engagement` would otherwise be legal
- THEN no Smite fires and current stays 0

#### Scenario: Good ally tops up with no evil visible

- GIVEN a good `Smite5` ally with `current == 1` and no visible evils
- WHEN the ally acts
- THEN it reloads to `current == 2` (silent)

#### Scenario: Evil hunger closes instead of shooting

- GIVEN an evil `Range5` predator, PreferVore, and a visible ≤50% HP quarry beyond adjacent range
- WHEN the predator acts
- THEN it steps toward the quarry
- AND does not Path/Smite that turn

### Requirement: Erratic and ranged incompatibility

`RangeN` and `SmiteN` SHALL NOT combine with `Erratic`. Erratic action plans bypass normal chase/ranged engagement; ranged abilities on an Erratic entity will not fire. Thematically intentional — erratic creatures melee and dart, not aimed shots.

#### Scenario: Erratic bat does not shoot

- GIVEN a bat with `Erratic` and a hypothetical `Range2` token
- WHEN the bat acts
- THEN no Path or Smite shot occurs
- AND Erratic plan shape applies instead

### Requirement: SummonN

`SummonN <entity_id>` SHALL fire once per entity when alignment-appropriate hostiles first enter LOS, spawning N adjacent entities on legal tiles. Invalid entity ids SHALL fail load.

#### Scenario: Summon1 rabbit on first sight

- GIVEN `Summon1 rabbit` and a visible hostile
- WHEN the summoner acts and summon not yet consumed
- THEN one rabbit spawns on a legal adjacent tile
- AND a FOV-gated summon log line appears when the summoner is visible

### Requirement: Coward and Supercoward

`Coward` SHALL flee when `hp * 2 < max_hp` and a visible alignment threat exists. `Supercoward` SHALL flee at any HP while alive when flee is legal.

Flee SHALL run before vore on `VoreCapable` evil entities. No activation log.

#### Scenario: Coward knight below half flees wolf

- GIVEN a good knight with `Coward` below half HP and a visible evil
- WHEN the knight acts
- THEN it flees instead of pursuing

### Requirement: Erratic

`Erratic` SHALL use plan `[MOVE, ATTACK, MOVE]` per world-phase visit:

1. **Intentional MOVE** — full AI destination intent (visible chase, memory pursuit, explore/flee as appropriate). **Not** random. Skipped **only** when already adjacent to a valid attack target (“why move? target is right here”). While exploring or otherwise pathing somewhere, the NPC **wants** this step and SHALL attempt it (no explore idle chance on this step). Door spite/shock still stands still when active.
2. **ATTACK** — adjacent only (vore modal, NPC vore, or melee); no-op when none in range
3. **Random MOVE** — mandatory; equal weight among all legal adjacent steps **and** remaining still. If step 1 moved the NPC, the tile they left is **forbidden** (they cannot reverse the intentional step). Stay is always allowed.

No reordering, no extra attacks or intentional moves beyond the plan shape.

### Requirement: Slow

`Slow` SHALL skip the entire visit when `player_turn_count % 2 == 1` (global parity). Stunned monsters skip before parity evaluation.

### Requirement: Fast

`Fast` SHALL double the base plan (concatenate twice). With baseline evil: `[MOVE_OR_BUMP, MOVE_OR_BUMP]`.

Vore modal opened mid-plan SHALL abort remaining steps; `plan_step_index` resets to 0. Vore miss SHALL waste the opener's turn (`resume_monster_index = i + 1`); no step replay in the same phase.

### Requirement: Knockback

On melee or ranged hit with `damage > 0`, attackers with `Knockback` SHALL push the defender one tile along the attack vector when the destination is legal. Failed push SHALL not log.

FOV-gated second line: *"You are knocked back!"* / *"{Target} is knocked back!"*

### Requirement: Lifedrain

On hit with `damage > 0`, attackers with `Lifedrain` SHALL heal by damage dealt (capped at `max_hp`). FOV-gated second line when heal applies: *"{Actor} appears healthier."*

### Requirement: PreferVore

`PreferVore` SHALL skip the `vore_decision_chance` RNG when a vore attempt (adjacent or `RangedVoreN`) is otherwise legal. It SHALL NOT bypass eligibility guards (`VoreCapable`, alignment, LOS, range, `VoreMercy`, `Engulfed`, narrative prefs, HP threshold, predator already holding prey).

No activation log beyond existing vore attempt lines.

#### Scenario: Partial HP always commits when PreferVore

- GIVEN a predator with `PreferVore` and legal adjacent vore against prey at 40% HP
- WHEN `should_attempt_vore` runs with an RNG that would fail the decision roll
- THEN the attempt is committed (returns true)

### Requirement: Wander

`Wander` SHALL prevent chase mode and animosity targeting. When not fleeing and not in a combat-forced action, intent SHALL be explore only (weighted-random far goals). The entity MAY still bump-damage in passing and SHALL NOT pursue after contact.

`Wander` SHALL NOT block `SummonN` on first sight or vore attempts when legal. SHALL NOT combine with `NoChase` in stock content (redundant; not a load error).

No activation log.

#### Scenario: Slime drifts without chase

- GIVEN an evil slime with `Wander` and a visible player
- WHEN the slime acts
- THEN it does not enter evil chase targeting
- AND it picks an explore goal step when movement is legal

### Requirement: NoChase

`NoChase` is meaningful on **evil** predators only. While quarry is visible: normal evil chase (melee, ranged, vore as usual). When quarry leaves LOS: immediately give up — no last-known pursuit, memory-blind trail, or chase momentum. Memory fields SHALL clear on turns with no visible quarry.

No activation log. SHALL NOT combine with `Wander` in stock content.

#### Scenario: Tarantula stops when player breaks LOS

- GIVEN a tarantula with `NoChase` that was fighting a visible player
- WHEN the player leaves LOS before the next tarantula turn
- THEN the tarantula does not step toward the last-known tile
- AND memory pursuit fields are cleared

### Requirement: Hands

During movement (explore, chase, flee, erratic), bumping a **closed door** SHALL open it without moving (player bump-open semantics — turn consumed, actor stays put). **80%** → `DOOR_OPEN`; **20%** → `FLOOR` (break).

Explore/chase BFS MAY treat closed doors as passable for reachability; the step onto a closed door is the bump interaction above.

Door spite/shock wait turns SHALL NOT apply to `Hands` holders. `Hands` holders with `RangeN` SHALL defer Path shots when a closed door lies toward the target.

FOV-gated logs: *"{Name} opens the door."* / *"Something opens the door."* (routine); *"{Name} breaks down the door!"* / *"Something breaks down the door!"* (caution).

#### Scenario: Kobold bump-opens without moving

- GIVEN a kobold with `Hands` adjacent to a closed door in its step direction
- WHEN it attempts that step
- THEN the door opens or breaks
- AND the kobold remains on its origin tile

### Requirement: RangedVoreN

`RangedVore2`…`RangedVore9` SHALL enable vore attempts against eligible prey at Chebyshev distance `[2, N]` with LOS. Distance 1 SHALL use the adjacent vore path only.

Eligible prey and decision rules match adjacent vore (`vore_decision_chance` unless `PreferVore`). Hit SHALL use `resolve_vore_hit()`; on hit prey SHALL co-locate on the predator tile then normal engulf/modal flow. On miss: no position change; predator turn consumed.

Stunned 0 HP prey at range MAY be targeted (not subject to Path/Smite close-on-stunned).

**AI order (evil intent pipeline):** adjacent player modal → ranged player modal → adjacent NPC vore → ranged NPC vore → chase engagement (`RangedVore` considered before Path when prey ≤50% HP; failed decision falls through to Path).

**Dual tongue:** `RangeN` + `RangedVoreN` same N — prey **>50% HP**: damage ranged only; prey **≤50% HP**: both considered; vore uses decision roll / `PreferVore`.

Save codec SHALL round-trip `RangedVoreN` tokens.

#### Scenario: Owl mage ranged vore at weakened player

- GIVEN an owl mage with `RangedVore5` and a player at 40% HP at distance 4 with LOS
- WHEN the owl acts and the vore decision roll commits
- THEN a vore modal may open (same flow as adjacent)
- AND on hit the player co-locates on the owl tile before engulf

#### Scenario: Path still fires when vore decision fails

- GIVEN a predator with `Range5` and `RangedVore5` and weakened prey at distance 5
- WHEN the ranged vore decision roll fails
- THEN a Path shoot attempt may still occur that turn

### Requirement: Ability stacking precedence

| Step | Rule |
|------|------|
| 1 | Slow odd turn → `[SKIP]` |
| 2 | Erratic → base `[MOVE, ATTACK, MOVE]` else `[MOVE_OR_BUMP]` |
| 3 | Fast → concatenate base twice |

Documented combinations: Slow+Fast, Slow+Erratic, Fast+Erratic (see design doc stacking table).

### Requirement: Log visibility

Summon, ranged smite, ranged shoot, knockback, and lifedrain activation lines SHALL use the same FOV helpers as NPC combat (`entity_visible_to_player` / `_npc_combat_visible_to_player`). Coward, Supercoward, Erratic, Slow, Fast SHALL NOT emit activation logs.

## Open Questions (resolved)

| # | Resolution |
|---|------------|
| 1 | Coward flee uses `_choose_flee_direction` from alignment threat |
| 2 | Erratic ATTACK includes vore for evil `VoreCapable` |
| 3 | Slow wins over Fast on odd `player_turn_count` |
| 4 | Summon: random legal adjacent tile; partial spawn OK |
| 5 | Smite: no shot → walk closer; Path: kite or near-player reposition; turn consumed on shot attempt |
| 6 | Knockback: away along bump direction or ranged axis sign |
| 7 | Stacking precedence table; combinatorial tests for Fast+Slow, Fast+Erratic |
| 8 | Stock wolf ships `Range6` Path shooter (playtest overrides reverted at PR6) |
| 9 | Coward flee before vore on evil |
| 10 | Duplicate SmiteN / RangeN → max N per family |
| 11 | Good/neutral use shared pipeline; vore gated by `VoreCapable` |
| 12 | SmiteN vs RangeN engagement priority per ability family |
| 13 | Optional `ranged_*` fields in entities.json |

## Stock content notes

- **Wolf** (`Range6`): Path shooter; logs *shoots*
- **Slime** (`Smite3`, `Wander`): mindless smite hazard; drifts, does not chase
- **Fox archer** (`Range5`): Path shooter from depth 5+
- **Kobold / gnoll mercenary** (`Hands`): bump-open closed doors
- **Owl mage** (`Hands`, `Range5`, `RangedVore5`): dual-tongue telekinetic grab + door use
- **Tarantula** (`NoChase`): opportunistic — fights in LOS, no pursuit after break
- **Tunnel slug** (`stationary`, `NoChase`): turret; holds spawn tile
- **Rabbit**: no `Wander` (neutral flee + explore baseline)
- **Bat / cave rat**: `Erratic` only — no ranged abilities (Erratic + ranged incompatible)

## References

- `data/SCHEMA.md` — ability token syntax
- `openspec/specs/ranged-targeting/spec.md` — Smite vs Path rules
- `openspec/specs/npc-data/spec.md` — entity loader and spawn
- `openspec/specs/enhancements-3/spec.md` — baseline faction AI
- `openspec/specs/vore/spec.md` — modal interrupt and turn order