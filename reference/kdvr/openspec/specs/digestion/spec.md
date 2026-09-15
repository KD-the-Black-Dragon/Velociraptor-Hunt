# digestion Specification

## Purpose

The **digestion** domain completes the vore loop for engulfed prey. Engulfed entities take periodic **digestion damage**; at 0 HP they accumulate **strikes**; when strikes reach the predator's **`digest_time`** they are **digested** — NPC prey are **removed** (log completion by OV/CV/AV type); the player sees a **digestion modal** then **game over**.

Builds on core, Enhancements 1–3, and vore. Logic lives in `src/systems/digestion.py`, `src/digestion_content.py`, and engine wiring.

**Terminology:** defeated, stunned, digested — no kill/die/death.

**AV content constraint:** engulfment and abdominal crushing/compression only; no expanded AV semantics in messages or modals.

**CP437 rendering:** HUD and message log use `src/text.cp437_safe()` — Unicode punctuation normalized to ASCII for the Alloy CP437 tileset.

## Requirements

### Requirement: Digestion Data Model

Engulf SHALL store `Predator.narrative_type` (`"OV"` | `"CV"` | `"AV"`) on the holding predator. Prey SHALL have optional `DigestionStrikes` (`count` 0..`digest_time`). Evil spawns SHALL receive `DigestionStats` with `damage_per_tick` (alignment default **3** per tick or optional `digestion_damage_per_tick` in `entities.json`) and `digest_time` (alignment default **6** strike ticks at 0 HP or optional `digest_time` in `entities.json`). Completion and player modal lines load from data (`openspec/specs/npc-data/spec.md`).

#### Scenario: Evil spawn has digestion stats

- GIVEN an evil entity spawned from data
- WHEN spawn completes
- THEN the entity has `DigestionStats` with `damage_per_tick >= 1` and `digest_time >= 1`

#### Scenario: Default digest time when omitted

- GIVEN an evil entity definition with no `digest_time` field
- WHEN the entity is spawned
- THEN `DigestionStats.digest_time` is **6**

#### Scenario: Narrative type persisted at engulf

- GIVEN an NPC vore hit with narrative type `AV`
- WHEN engulf completes
- THEN `Predator.narrative_type` is `AV`

### Requirement: NPC Digestion Tick

When an engulfed **NPC** would take its AI turn, the game SHALL apply one digestion tick instead of movement. Ticks SHALL **not** run for the engulfed **player** during the world phase (player ticks on consumed player turns only).

Per tick:

1. If prey `HP > 0`: subtract `DigestionStats.damage_per_tick`; sync stunned for good/neutral at 0 HP; **no strike**.
2. If prey `HP == 0`: add 1 to `DigestionStrikes.count`; **no HP change**.
3. Never HP→0 and +1 strike on the same tick.

At `strikes.count >= DigestionStats.digest_time`: remove prey, log completion when visible (entity `digestion_complete` then fallback `DIGESTION_COMPLETE_POOL[narrative_type]`) or when off-screen (entity `offscreen_digest[type]` only — no global fallback), clear `Predator` on holder, skip holder's extra actions this world phase; holder acts normally **next player turn**.

#### Scenario: HP damage before strikes

- GIVEN an engulfed knight at 5 HP inside a wolf
- WHEN one digestion tick runs
- THEN knight HP is 2
- AND no `DigestionStrikes` component exists

#### Scenario: No strike on HP-to-zero tick

- GIVEN an engulfed knight at 3 HP
- WHEN one digestion tick runs
- THEN knight HP is 0 and stunned
- AND strikes remain absent

#### Scenario: Digest time strikes remove NPC

- GIVEN an engulfed stunned knight at 0 HP inside a predator with `digest_time` 3
- WHEN three digestion ticks run (one per prey AI slot / world phase)
- THEN the knight entity is removed
- AND the predator has no `Predator` component

#### Scenario: Custom digest time requires N strikes

- GIVEN an engulfed stunned knight at 0 HP inside a predator with `digest_time` 5
- WHEN four digestion ticks run
- THEN the knight entity still exists
- WHEN a fifth digestion tick runs
- THEN the knight entity is removed

### Requirement: Player Digestion Tick

Each **consumed player turn** while engulfed SHALL apply one digestion tick **after** struggle resolution (if any) and **before** natural regen. Digestion SHALL be the only HP change while engulfed: **no natural regen** while engulfed; **no external combat damage** to engulfed defenders.

Worn armor **`digestion_ac`** (from `armor.json` via `inventory-items` spec) SHALL mitigate player digestion tick damage flat per tick: `mitigated = min(raw_tick, digestion_ac)`, `hp_loss = raw_tick - mitigated`, and worn armor durability SHALL decrease by `mitigated`. Pack commands remain blocked while engulfed; mitigation is passive.

#### Scenario: Worn armor mitigates digestion tick

- GIVEN an engulfed player wearing leather armor (`digestion_ac` 2) and wolf digestion 3 per tick
- WHEN one player digestion tick applies
- THEN the player loses 1 HP (not 3)
- AND armor durability decreases by 2

At `strikes.count >= DigestionStats.digest_time`: open center **digestion modal** (placeholder per `PLAYER_DIGESTION_MODAL[narrative_type]`); skip world phase that turn. Enter on modal → game over recap showing the player's **display name** (from New Game entry) and formatted ending — **Digested by {predator}** by default, or macguffin ending when `MacguffinDiscovery` is active (`macguffins` spec; no predator mention on override). **No** turns survived or score line. Enter on recap → **main menu** (not process exit). While any vore, digestion, macguffin victory, or recap modal is active, **Ctrl+Q** is a no-op (see `main-menu` spec).

Each strike increment (not HP damage ticks) SHALL log *"You are being digested!!"*

#### Scenario: Player strike cadence

- GIVEN an engulfed player at 0 HP held by a predator with `digest_time` 3
- WHEN three consumed player turns pass
- THEN strike count reaches 3
- AND the digestion modal opens on the third

#### Scenario: Engulfed combat immunity

- GIVEN an engulfed player co-located with a holding wolf
- WHEN another wolf bump-attacks that tile
- THEN the engulfed player takes no damage
- AND no *"hits you"* log line appears

#### Scenario: No regen while engulfed

- GIVEN an engulfed stunned player at 0 HP on a regen turn
- WHEN a player turn is consumed with a digestion strike
- THEN HP remains 0
- AND *"You are no longer stunned."* does not appear from regen

### Requirement: Regen Gate

Natural regen (player and NPC) SHALL be skipped when `DigestionStrikes.count >= 1`. Potions and direct `heal()` SHALL bypass this gate. Freedom (escape/release) SHALL clear `DigestionStrikes`.

### Requirement: Good Plea and Neutral Silence

On each NPC digestion tick, **good** prey SHALL have a **10%** chance to log a plea line from `GOOD_PLEA_POOL` when the player has LOS to predator or prey tile. **Neutral** prey SHALL be silent on ticks (no plea, no strike log).

### Requirement: Predator While Holding

A predator with `Predator` SHALL sync engulfed prey position, MAY perform **one adjacent bump-attack** per world phase (evil never melee-damages evil), and SHALL NOT move, chase, or initiate vore. Holding predators SHALL NOT take a full AI turn after digest completes in the same world phase.

### Requirement: NPC Dazed

NPCs MAY carry a **`Dazed(remaining)`** component (never the player). While dazed, the entity's visible tile background SHALL be blue (holding-predator dark-red BG takes precedence while `Predator` is present). On each AI opportunity, a dazed NPC SHALL skip its action, decrement `remaining` by 1, and if `remaining` reaches ≤ 0 clear Dazed. The turn that expires daze is still skipped; the NPC MAY act on a later turn.

Applying daze with positive turns: if not already dazed, set `remaining` and — when the entity is in player FOV — log *"{Name} appears dazed."* (sentence-capitalized name). If already dazed, **add** the new turns to `remaining` without a second “appears” line. On expire in FOV, log *"{Name} is no longer dazed."*

`Dazed` SHALL persist in autosaves. Stock difficulty profiles provide `cv_daze_min_turns` / `cv_daze_max_turns` (default **5**/**5** if omitted) used by Alternate CV (see `vore` spec).

#### Scenario: Dazed NPC skips then recovers

- GIVEN a visible wolf with `Dazed(remaining=1)`
- WHEN its AI turn runs
- THEN it takes no action
- AND Dazed is cleared
- AND the log shows it is no longer dazed (FOV-gated)

### Requirement: Alternate CV NPC digest-complete daze

When Alternate CV Mechanics is snapshotted **Yes** on the run and `complete_npc_digestion` clears a **CV** hold, the predator SHALL gain **Dazed** for a rolled duration from the run difficulty profile (stacking add). OV/AV digest-complete and Alternate CV **No** SHALL NOT apply this daze. Same-phase `skip_turn_entities` after digest SHALL remain.

#### Scenario: CV NPC digest dazes under Alternate CV

- GIVEN Alternate CV **Yes** on the run
- AND a wolf finishes digesting a rabbit with `narrative_type` **CV**
- WHEN digestion completes
- THEN the wolf has `Dazed` with remaining in the profile range

#### Scenario: OV NPC digest does not daze under Alternate CV

- GIVEN Alternate CV **Yes** on the run
- AND a wolf finishes digesting prey with `narrative_type` **OV**
- WHEN digestion completes
- THEN the wolf is not dazed from that completion

### Requirement: NPC Vore Mercy

`release_npc_engulfed` SHALL grant `VoreMercy` on the prey. Combat and `should_attempt_vore` SHALL honor `VoreMercy` on **any** prey (not only the player). `VoreMercy` SHALL clear from all tagged entities at end of world phase.

#### Scenario: Freed NPC cannot be re-engulfed same phase

- GIVEN a knight freed from a defeated wolf
- WHEN the wolf or another wolf attempts vore the same world phase
- THEN the attempt does not succeed

## Technical Constants (defaults)

| Constant / component | Default | Meaning |
|---------------------|---------|---------|
| Evil `DigestionStats.damage_per_tick` | 3 | Per-tick digestion damage |
| Evil `DigestionStats.digest_time` | 6 | Strike ticks at 0 HP before digest |
| `DigestionStrikes.count` | 0..digest_time | Strikes at 0 HP |
| Good plea chance | 10% | Per NPC tick, LOS-gated |
| Player game over name | display name from New Game | `"Anonymous"` if blank at entry |
| Player game over score | — | **Out of scope** — recap shows name and fate only |

### Requirement: Offscreen NPC Digestion Complete Messages

When `complete_npc_digestion` runs and **neither** predator nor prey is in player FOV, the game SHALL log one random line from the predator entity's `offscreen_digest` object (keyed by narrative type `OV`, `CV`, `AV`). Legacy flat digest keys are invalid at load. Missing type keys SHALL NOT log and SHALL NOT fall back to `DIGESTION_COMPLETE_POOL`. On-screen completion SHALL remain unchanged (entity `digestion_complete` then global pool).

#### Scenario: Offscreen digest logs entity line

- GIVEN a wolf digesting a knight off-screen
- AND the wolf defines `offscreen_digest.OV`
- WHEN digestion completes
- THEN one offscreen digest line appears in the message log

#### Scenario: Offscreen digest silent without data

- GIVEN digestion completes off-screen
- AND the predator has no `offscreen_digest` line for the rolled type
- THEN no completion message is logged

## Acceptance Criteria

1. NPC digestion removes good/neutral prey after HP drain + predator `digest_time` strikes; completion log by OV/CV/AV when visible; offscreen atmospheric lines when not visible and entity data exists.
2. Player digestion opens modal then recap with display name and fate (no score); Enter returns to main menu.
3. Predator attack-only while holding; freed prey mercy (player + NPC).
4. Engulfed player immune to external damage; digestion-only HP changes; strike message on strike ticks only.
5. Regen blocked at `strikes >= 1`; potions still heal.
6. All scenarios demonstrable via `tests/test_digestion.py` and manual PR checklists.
7. Full `pytest tests/` green; prior acceptance tests still pass.