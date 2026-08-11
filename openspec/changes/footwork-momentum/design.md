# Design: footwork-momentum (BP-M)

| Field | Value |
|-------|--------|
| **Module** | `footwork-momentum` |
| **Program** | `../battle-pace-program/BATTLE_SPORT_SPEC.md` |
| **Status** | Design frozen 2026-08-10 — implement only after whole-batch authorization |
| **Depends on** | player-combat-commands footwork; foundation reaction modal dodge |

---

## Problem

Emergency evade (reaction dodge) must respect **inertia** after footwork: same direction OK; reverse very hard.

---

## Requirements

### Momentum component

| Property | Rule |
|----------|------|
| Apply | On successful footwork resolve |
| Shape | Directional vector / facing of the footwork move |
| Duration | JSON, measured in world AUT |
| Refresh | New footwork overwrites / refreshes (JSON policy; default overwrite with new direction + full duration) |

### Emergency evade modifiers

| Relationship to momentum | Effect |
|--------------------------|--------|
| Same / similar direction | Bonus or normal success (JSON mult) |
| Sideways | Mild penalty or neutral (JSON) |
| **Opposite / reverse** | **Very hard** — heavy penalty (JSON) |

Applies only to **reaction-modal dodge** (emergency evade), not to normal step or footwork itself.

### AI

- When AI footworks, same momentum tags apply to its future emergency evade if it becomes PC… (AI as defender is N/A for PC modal). If allies/enemies ever use dodge reactions, same rules. Primary consumer: **player** dodge after player footwork; enemies may store momentum for future systems.

### Out of scope

- Redesign full reaction option list (parry/block/counter remain as today unless JSON-only tweaks)
- New footwork shapes

---

## Data

Suggested keys (illustrative):

- `momentum_duration_aut`
- `evade_mult_same_dir`, `evade_mult_side`, `evade_mult_reverse`

---

## Acceptance

- After footwork west, dodging east is clearly harder than dodging west.
- Magnitudes tunable in JSON.
- Automated tests cover direction relationship without pinning live balance tables as identity.
