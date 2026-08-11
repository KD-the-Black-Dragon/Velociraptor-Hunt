# Spec: Gladiavore arena match

## Purpose

Turn-based AUT combat in curated sand-pit arenas for Gladiavore career matches.

**Battle Sport (measure, steep balance, footwork, fuzzy AI):** accepted design contract lives in `openspec/specs/battle-sport/spec.md` and `openspec/changes/battle-pace-program/BATTLE_SPORT_SPEC.md`. Those requirements supersede adjacent-bump-only pace once implemented.

## Requirements

### AUT

- World-time scheduler; player wins readiness ties.
- Step, attacks, abilities, talk, recovery consume AUT per JSON/maneuver data.

### Combat skeleton

- AP regenerates with world AUT; balance meter from actions.
- Smart bump profiles; reaction modal on incoming PC attacks (not while grappled prey).
- Flanking, pushback, abilities via `data/match_combat.json`.
- **Ally bump:** moving into an ally is a **no-op** (no AUT). Message log reports `"{AllyName} is standing there."`

### Match HUD (fight phase)

- **Map** (top-left): tiles + entity glyphs only (fixed-width).
- **Status** (right of map): HP, AUT, AP, balance, card/kind, crowd/difficulty, injuries, non-modal scene prompts (grapple/talk/ability).
- **Action log** (bottom): recent combat/message lines only — not meters, not reaction choices.
- **Reaction modal** (low-right dedicated panel when active): INCOMING announce + choices; must not cover the map, primary status meters, or the action log body.

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
- **Grapple (PC prey):** red low-right crisis modal; copy `{PredatorName} grapples you!` (wrestling stub; full revamp later).
- **Swallow (PC prey):** centered interface-blocking modal (not full-screen); narrative top of panel with padding; bottom `1 - struggle | 2 - conserve strength` (no explanations).
- **Swallow self-escape:** ~**1%** per struggle (`swallow_struggle_escape_chance` in JSON); not grapple break-away odds. Ally damage / predator defeat may free mid-swallow.
- **Conserve strength:** no escape roll; each conserve adds +1 digest endurance once engulfed (**no hard cap**).
- **Green:** control grabs OK; **must release before lethal digest** (swallow phases may run; no finishing digest).
- **Tiles:** wrestling participants occupy **adjacent** tiles (not the same). Swallow/engulfed: prey **co-locates** on predator tile (glyph shows predator).
- **Tile backgrounds:** yellow = predator wrestling; green = ally prey in danger; orange = predator swallowing; red = predator has fully engulfed prey.

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
