# Proposal: Comprehensive data balance pass

> **Superseded for product direction (2026-07-16).** This repository is now **Gladiavore**. Do not continue KDVR stock balance work here unless the designer explicitly revives it. Active change: `openspec/changes/gladiavore-foundation/`.

## Problem

Systems for difficulty profiles, depth scaling, density, prefixes, gear, runes, and a headless balance simulator are shipped, but **stock numbers are not a finished designer target**. Recent content (more species, abilities, prefixes, throwables, potions, depth-jump) changed the feel of early and mid game; soft-yet-deep pressure and early approachability still need iterative, playtest-driven tuning.

Without a dedicated change, balance tweaks scatter across chats with no durable record of latitude rules, resolved decisions, or what was tried.

## Solution

Open a long-lived **balance-pass** OpenSpec change that:

1. Inventories every practical **data/** (and last-resort constant) knob.
2. Records designer **latitude** (free / careful / last-resort / frozen).
3. Drives iterative tweaks in `data/*.json` from playtest feedback (sim only after a designer-approved baseline).
4. Logs resolutions, baselines, and rejected experiments for future re-entry.
5. Proposes **code** when data cannot express intent (notably **player evade** from armor/runes); implements only with explicit authorization of a named PR.

**Primary target difficulty:** **Normal** — not a free ride, but OK most of the time if you use items; not super-brutal. F20+ dragons remain intentional “Yeti” doom. Easier/Hard/Nightmare are secondary this pass.

## Scope

### In scope

- Tweaking stock JSON under `data/` that affects combat, spawn, economy, progression, and difficulty feel
- Documenting latitude, goals per difficulty, and iteration log in this change’s `design.md`
- **PR-evade:** player evade from base + armor `evade_bonus` + `natural_evade` runes + `effective_fighter` (designed; auth required)
- **PR-curve-1+:** Normal mon accuracy/evade/TTK and later depth curve (designed outline; auth required)
- Spec/SCHEMA updates when balance systems gain fields (evade_bonus, natural_evade)
- Optional sim **after** designer certifies a balanced Normal baseline

### Out of scope (unless designer later expands)

- New species, abilities, prefixes, or UI features (except stock `evasion_rune` content for PR-evade)
- XP / player leveling
- Narrative rewrites, AV content expansion
- Mid-run difficulty change or in-run difficulty HUD
- `digest_time` depth scaling (already rejected in balance knobs)
- Macguffins and `depth_jump_start.json` (out of this balance pass)
- Code refactors for “cleaner balance” without a data/design gap
- Pinning live balance numbers in automated tests
- Making Normal “super brutal” or fair-ifying F20+ dragons

## Success criteria

- Designer says the pass is complete
- Latitude and major decisions are recorded in `design.md`
- Stock `data/` reflects the accepted curves for Easier / Normal / Hard / Nightmare (as far as designer cares for this pass)
- No unauthorized code changes

## Related

| Artifact | Role |
|----------|------|
| `openspec/specs/balance/spec.md` | Difficulty + depth bake + prefixes economy |
| `openspec/specs/balance-simulator/spec.md` | Headless analyzer |
| `openspec/changes/todo/spec.md` | “Balance iteration” backlog item |
| Archive `2026-07-09-add-balance-knobs` | Systems that made this pass possible |
| Archive `2026-07-12-add-balance-simulator` | Sim tooling |
| `How to Run Balance Simulator.txt` | Operator guide |

## Non-goals for “done soon”

This is **not** a fixed PR count or calendar sprint. Completion is designer sign-off after iterative play.
