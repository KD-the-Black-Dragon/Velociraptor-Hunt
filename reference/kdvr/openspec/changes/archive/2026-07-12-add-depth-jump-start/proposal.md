# Proposal: Start at depth (secret menu)

## Problem

Playtesting and balance iteration often need to reach mid- or late-dungeon floors without playing through every prior floor. Today **New Game** always starts at depth 1 with the starter loadout (dagger, robes, rocks, no rune bonuses). There is no supported way to jump to floor 10+ with a reasonable loadout.

## Solution

Add a **hidden main-menu shortcut** (proposed **Ctrl+G**) that opens a two-step flow:

1. **Name entry** — same rules as normal New Game.
2. **Depth entry** — integer **1–20**; invalid input shows an error and allows correction until valid.

On confirm, start a normal run on the chosen floor with a **dynamically computed loadout** derived entirely from loaded JSON (stock + enabled mods):

- Equipment and consumables use eligibility at **`target_depth - 1`** (what could have been collected before arriving).
- Prior-floor **rune bonuses** are simulated mathematically (weighted random picks per floor 1…`target_depth - 1`).

This is a designer/playtest tool, not a player-facing menu option.

## Scope

- Secret key chord on main menu
- Reused name-entry UX
- New depth-entry screen with validation message
- Engine bootstrap at chosen depth (map gen + population for that depth)
- Data-driven loadout builder (weapon, armor, throwables, potions, wands, simulated runes)
- New `data/depth_jump_start.json` for tunable counts and depth cap
- Automated tests for eligibility, strength ranking, rune simulation, and menu flow
- Live spec: `openspec/specs/depth-jump-start/spec.md` (on archive)

## Out of scope

- Visible Options menu entry
- Depths above 20 (cap is config-driven; stock **20**)
- Simulating macguffins, allies, gold, or floor loot beyond the described loadout
- Perfect fidelity to a skilled human run (rough power level only)
- Persisting “last jump depth” in settings

## PR plan

| PR | Scope |
|----|--------|
| PR1 | Menu flow, depth bootstrap, loadout builder, config JSON, tests, spec |

Single PR unless playtest reveals size pain.