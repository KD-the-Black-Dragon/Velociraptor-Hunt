# Design: weapon-measure (BP-W)

| Field | Value |
|-------|--------|
| **Module** | `weapon-measure` |
| **Program** | `../battle-pace-program/BATTLE_SPORT_SPEC.md` (authoritative freeze) |
| **Status** | Design frozen 2026-08-10 — implement only after whole-batch authorization |
| **Depends on** | Foundation match combat / AUT |
| **Blocks** | Player directed attacks at measure; AI measure fitness |

---

## Problem

Weapons are mostly damage/accuracy bags. Measure-first sport needs each weapon to declare **attack delay** and **effectiveness by range band**, including **natural weapons**.

---

## Requirements

### Always armed

- Every combatant has exactly one **active weapon** (steel or natural).
- No fully unarmed fighters.
- **No disarming.**
- Cannot remove the only weapon; **swap only** when replacing with another legal weapon.
- Weapon / loadout data includes boolean **`swappable`** (default true for shop steel; **false** for typical beast natural weapons so the player cannot strip “wolf teeth”).

### Schema (JSON — illustrative field names; implementer may normalize)

Per weapon id:

| Field | Role |
|-------|------|
| `attack_delay` | Basic attack AUT (DCSS-like); same across bands for basics |
| `measure` / band table | Effectiveness mults (accuracy and/or damage and/or technique tier) for R1, R2, R3, R4, R5+ |
| `swappable` | If false, equip UI cannot replace this weapon |
| Existing | damage, accuracy_bonus, examine, glyph, etc. |

Natural weapons are normal weapon rows (e.g. `wolf_teeth`) assigned as default loadout on entities.

### Geometry

- Shared helper: range band from actor position → target position.
- Distance metric: **Chebyshev**.
- Knight-move geometry treated as **band-2-reachable** where footwork/attack rules require (same helper family as player-combat-commands).

### Resolution

- Basic attacks spend AUT = weapon `attack_delay`.
- Apply band effectiveness from attacker’s active weapon vs current band to target.
- R5+ basic combat intent is **no useful steel** → caller treats as **no-op** (player-combat-commands owns input policy).

### Seed archetypes (minimum)

| Id fantasy | Intent |
|------------|--------|
| Gladius-like sword | R1 full; R2 comfortable |
| Spear | R1 near-useless; wants longer measure (JSON curve; not hug-optimal) |
| Heavy (axe or mace) | Strong close commit; longer delay |
| Short blade / dagger | Strong R1; faster falloff |
| At least one natural (teeth/claws) | For beast entities |

Exact mult tables are **provisional in JSON** until playtest retune.

### Out of scope for this module alone

- New player keys, footwork UI, AI personality
- Full shop content explosion
- Feint presentation (player-combat-commands uses band data)

---

## Implementation notes

- Prefer extending `data/weapons.json` + match loadout assignment over hardcoding.
- Career equip / roster must respect `swappable`.
- Save: new fields default safely for old careers (e.g. missing measure → neutral mult 1.0 only as temporary migrate; prefer shipping complete data with content).

---

## Acceptance (automated + eventual manual)

- Spear at R1 clearly worse than sword at R1 when both can attack.
- Delays differ by weapon.
- Natural weapon entities fight with their weapon profile.
- Non-swappable weapons cannot be swapped out in equip.
- All knobs in JSON.
