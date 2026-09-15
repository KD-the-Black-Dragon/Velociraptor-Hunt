# Proposal: Extra NPC prefixes beyond Elite

## Summary

Extend the shipped **NPC prefix** system (`data/npc_prefixes.json`, floor spawn only) with six new evil modifiers alongside stock **Elite**. Prefixes may grant **abilities** and use **entity-aware eligibility** so gated prefixes (e.g. **Sniper** on `RangeN` species only) never appear on invalid hosts.

Roll model: **filter eligible prefixes for this species, then weighted pick once** (no reroll loop).

## Approved prefix roster

| id | Display | Mechanical sketch |
|----|---------|-------------------|
| `elite` | Elite | *(exists)* general evil stat buff |
| `brute` | Brute | `Slow` + higher damage, lower accuracy |
| `berserk` | Berserk | higher damage, lower max HP |
| `veteran` | Veteran | smaller Elite-style stat package |
| `starving` | Starving | `PreferVore`, lower max HP |
| `sniper` | Sniper | +ranged accuracy only; requires `RangeN` (not `SmiteN`) |
| `bloated` | Bloated | `Slow`, higher max HP |

All stock prefixes target **evil** alignments only. Weights are **data-driven** in `npc_prefixes.json` and supplement Elite in the same pool.

## Designer decisions (locked)

| Question | Answer |
|----------|--------|
| Alignment scope | Evil only (same as Elite) |
| Ability grants | In scope — `grant_abilities[]` on prefix rows |
| Elite relationship | **Supplement** — shared weight pool; tune per-prefix `weight` in JSON |
| Weak-only prefixes | **No** — tradeoffs OK; no pure debuff rolls |
| Prefix variety | No fixed count preference — balance via weights |

## Motivation

- Visible floor threat variety without new entity ids.
- Encourage attention and consumable spend (vore pressure, ranged precision, slow bruisers).
- Reuse generic prefix machinery from `add-balance-knobs`; Elite proved the pattern.

## Out of scope

- Good/neutral prefix rolls.
- Prefixes on summons (`roll_prefix=False` unchanged).
- New ability tokens (use existing `Slow`, `PreferVore`).
- Thorns, Marksman-on-Smite, or vetoed brainstorm prefixes.
- Reverting baked stats/abilities on prefix soft-drop at load (existing limitation).

## Success criteria

- Six new prefixes load, filter correctly, apply at floor spawn, save/load `NpcPrefix` id.
- **Sniper** never appears on species without `RangeN`.
- Granted abilities merge with species `abilities[]` and participate in normal stacking rules.
- Live `balance` spec + `data/SCHEMA.md` updated; change archived after playtest sign-off.

## References

- Design: `design.md`
- Live: `openspec/specs/balance/spec.md`, `openspec/specs/npc-abilities/spec.md`
- Origin: `openspec/changes/todo/spec.md` — *Extra NPC prefixes beyond Elite*
- Prior: `openspec/changes/archive/2026-07-09-add-balance-knobs/` (Elite v1)