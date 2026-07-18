# Spec: command-allies (Come here!)

## Purpose

Player can shout **“Come here!”** so good allies in view temporarily prioritize reaching the player, then resume normal good AI after tagging the player. Midpoint scope only — no permanent follow, no Attack order.

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Depends on:** `enhancements-3` (good AI), `ally-improvement` (engulfed rescue priority), `ui-layout` / help overlay.

---

## Requirements

### Requirement: Come here shout

The game SHALL bind main keyboard **`1`** (`KeySym.N1`, not numpad) to a player shout that:

1. On **cooldown** (fewer than **4** player turns since last successful or engulfed fizzle shout): log *"You'll go hoarse if you shout too much."* and **not** consume a turn.
2. When the player is **engulfed**: log *"You shout, but you're not sure anyone heard you."*, consume a turn, start cooldown, and **not** set ally orders.
3. Otherwise: log *You shout, "Come here!"*, consume a turn, start cooldown, and set `AIState.come_here = True` on every **good** NPC currently on a tile in **player FOV**.

Allies outside FOV at shout time SHALL NOT receive the order. Neutrals and evils SHALL NOT receive the order.

Shout SHALL be blocked while gameplay modals block other action keys (inventory, vore, examine, etc.). Stunned players MAY shout.

#### Scenario: Successful shout

- GIVEN a good knight in player FOV
- WHEN the player presses main keyboard `1` and is not on cooldown
- THEN the log shows *You shout, "Come here!"*
- AND the knight has come-here active
- AND a player turn is consumed

#### Scenario: Cooldown

- GIVEN the player shouted successfully on turn T
- WHEN they press `1` again before turn T+4
- THEN the log shows the hoarse message
- AND no turn is consumed

#### Scenario: Engulfed fizzle

- GIVEN the player is engulfed
- WHEN they press `1` off cooldown
- THEN the not-sure-anyone-heard message appears
- AND no ally gains come-here
- AND a turn is consumed

### Requirement: Come-here AI

While `come_here` is true, good AI SHALL:

1. **Clear come-here** immediately when Chebyshev-adjacent to the player (not engulfed), then use standard good AI that turn.
2. Keep **engulfed-player rescue** as top priority when the ally has LOS to the predator holding the player.
3. Otherwise approach the player with honest pursuit (LOS → follow player; else last-known player memory). **Not** seek non-blocking evil as a primary goal.
4. If an **evil** stands between the ally and the player (same frustration geometry as evil vs neutral blockers), **attack that evil**.
5. On chase give-up / lose-track of the player, **clear come-here**.
6. If neither LOS nor player memory remains, **clear come-here** and use standard good AI.

Come-here flags SHALL be cleared for all entities on **floor descent**.

#### Scenario: Tag ends order

- GIVEN a knight with come-here active becomes adjacent to the player
- WHEN the knight’s AI runs
- THEN come-here is cleared
- AND the knight may pursue evil again under standard good AI

#### Scenario: Frustration

- GIVEN a knight with come-here, an evil between the knight and the player
- WHEN the knight’s AI runs
- THEN the knight targets that evil for attack

### Requirement: Help discovery

The help overlay SHALL list: `1 - shout "Come here!" (good allies in view)`.

---

## Out of scope

- Permanent follow / stick-close  
- Attack command / multi-order UI  
- Neutral allies  
- Omniscient pathing to the player outside FOV/memory  

## Implementation notes (non-normative)

- `src/systems/come_here.py`, `src/systems/ai.py` (`pick_good_chase`)
- `COME_HERE_KEY` in `src/input_handlers.py`
- Historical Follow/Attack draft: `openspec/changes/deferred-add-command-allies/` (superseded)
