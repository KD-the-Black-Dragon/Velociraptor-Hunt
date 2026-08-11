# Design: player-combat-commands (BP-P)

| Field | Value |
|-------|--------|
| **Module** | `player-combat-commands` |
| **Program** | `../battle-pace-program/BATTLE_SPORT_SPEC.md` |
| **Status** | Design frozen 2026-08-10 — implement only after whole-batch authorization |
| **Depends on** | weapon-measure (for directed attack PRs); ready-actions recommended before calling module “done” |
| **Blocks** | footwork-momentum; AI footwork/attack candidates |

---

## Problem

Matches still play like classic roguelike adjacent bump. Need **optimistic intent**, **footwork**, and **easy measure attacks**.

---

## Requirements

### Shared intent rules

| Rule | Detail |
|------|--------|
| Invalid | **No-op** — no AUT, AP, or balance change |
| Targeting Esc | Cancel without cost |
| Empty air / wrong context | Never “swing at air and look foolish” |
| R5+ | No useful basic combat intent → no-op |
| R3–4 | Feint / false lunge when full steel is inappropriate for weapon/band |
| Aggressive act tagging | Basics, abilities that attack, **feints** count as aggressive for ally **Help me!** windows |

### Footwork (`f`)

| Property | Rule |
|----------|------|
| Input | `f` → targeting mode |
| Legal destinations | **2 tiles straight** (orthogonal or diagonal line) **or knight-move** |
| Destination | Free / valid tile rules (no illegal enter) |
| Costs | AP (≈1–2 JSON), AUT ≠ normal step, **aggression** balance; **compound** on successive footworks |
| Cancel | Esc or invalid = no-op |
| Fantasy | Practiced **bursty martial technique** — not a free faster step |

### Directed basic attack

| Property | Rule |
|----------|------|
| Input | **ctrl + direction** |
| Targeting | Cone / general direction; homes to foe in cone (incl. knight band-2 where applicable) |
| Resolution | Weapon **attack_delay** + measure band effectiveness |
| Smart bump | Remains optimistic at R1; prefer shared resolver |

### Feint ladder

- At R3–4 (and data-defined cases): spend intent as **feint** — pressure / tag aggressive without full steel shame.
- Exact balance/AP/AUT for feint in JSON.
- Still **no-op** when nothing sensible is in range (R5+).

### Help / footer

- Update match help strings for new keys (`.`/5, `d`, `f`, ctrl+dir).

### Out of scope

- Momentum → evade matrix (→ footwork-momentum)
- AI using these verbs (→ ai-personality-fuzzy)
- Jump vault; full openings matrix
- Grapple fairness

---

## Implementation sketch (non-binding)

Internal sub-steps when coding:

1. Intent resolver core (no-op policy, cone pick)
2. Footwork targeting + costs + compound
3. Directed attack + weapon bands live
4. Feint ladder + messages
5. Help + regression tests

---

## Acceptance

- Bouts can happen at R2 with directed attack.
- Footwork is first-class.
- No key wastes a turn for wrong context.
- Spear vs sword measure is player-visible with directed attack.
