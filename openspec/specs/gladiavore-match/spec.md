# Spec: Gladiavore arena match

## Purpose

Turn-based AUT combat in curated sand-pit arenas for Gladiavore career matches.

## Requirements

### AUT

- World-time scheduler; player wins readiness ties.
- Step, attacks, abilities, talk, recovery consume AUT per JSON/maneuver data.

### Combat skeleton

- AP regenerates with world AUT; balance meter from actions.
- Smart bump profiles; reaction modal on incoming PC attacks (not while grappled prey).
- Flanking, pushback, abilities via `data/match_combat.json`.

### Injuries & recovery

- Separate injury debuffs (region + severity labels); not gore.
- 0 HP = downed/stunned; crawl + recovery bar + optional Second Wind.
- Bout ends when player side is incapacitated (PC downed + no living allies) or all enemies defeated.

### Grapple / vore (stub depth)

- Grab → grapple HP (= current stamina) war → multi-phase swallow → digest strikes.
- Red 0-HP may skip grapple war into swallow; green aborts before lethal digest.
- **Scene isolation:** grappled prey only takes damage from current predator; other enemies do not free-pile; reaction modal does not stack over grapple input.
- PC never initiates vore; PC digested ends career.
- Ally digest (red): roster remove + gold refund fraction.

### Green surrender

- Mid-match only (`G`); denied if too early or on red; scaled appearance fee.

### Crowd (stub)

- Favor meter shifts on hits/misses and match end; recap mood + optional high-favor gold.

### Difficulty (stub)

- Tiers in JSON: enemy HP/damage mult, grab chance mult, payout mult, extra green rounds flag.

## Terminology

- Enemies are **defeated**; 0 HP fighters are **stunned**/downed; permanent removal is **digested**.
- Do not use kill/die/death in product prose.

## Non-goals

- Full Wrestling fairness pass.
- Real crowd force simulation.
- Full opening/counter matrix content.
