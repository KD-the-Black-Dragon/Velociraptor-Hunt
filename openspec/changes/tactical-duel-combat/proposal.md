# Proposal: Tactical duel combat feel

| Field | Value |
|-------|--------|
| **Change** | `tactical-duel-combat` |
| **Status** | Design Q&A locked 2026-08-15 — not authorized for implementation |
| **Depends on** | Battle Sport; Solo Duels; match HUD |
| **Live specs to extend** | `openspec/specs/battle-sport/spec.md`, `openspec/specs/gladiavore-match/spec.md` |
| **Canon** | DESIGN_CANON combat log vs modal; UnReal World prose; balance from actions |

---

## Why

Solo Duels put one opponent on screen. Fights should feel like **measure, posture, and timing** — fighting-game **automatic counterhits** when you punish recovery — not roguelike RNG chip and constant Incoming spam.

Today Incoming opens too often; reactions include a free Counter; accuracy/evade invent random misses; the log is numeric; the foe’s plan/balance/attrs are invisible; beasts and humans defend the same way.

---

## What

1. **Strike momentum** — pure arbitration from relative balance, weapon measure, defender AUT recovery, ability commitment, buffs/debuffs, beast vulnerability, etc. Player/AI **orders** attack; the game decides severity (jab-level when timid through devastating punish). Debug factor breakdown on HUD.
2. **Incoming** only for **breakthrough+** crises (“that axe is about to hit me”).
3. **Reactions** — Dodge = full 1-tile footwork (AP gate + balance); Block = full brace; Ignore free (accept hurt / slugfest); Counter **removed**; reaction AUT **appends** to remaining cooldown. NPCs simulate the same (beasts: dodge/ignore only, **no brace/block**).
4. **Always land** except **overbalance fumble** (exclusive random fail; fumble wording; no Incoming).
5. **Passive defense** + light chip on non-crisis blocks/parries; beasts take more steel via momentum bonus + higher stamina content.
6. **Narrative log** — no damage numbers; `messages.py` gameplay lines.
7. **Opponent readout** always in the pit (plan, balance, stamina, personality, momentum debug).
8. **AI** more timid: feint/hold/retreat, then commit; punish fast closes.

**Deferred:** shield durability; perk-gated intel; full wrestle rebalance if not a small hook.

---

## Success criteria

- High-momentum punishes feel automatic when you hit recovery/windup.
- Incoming is rare and cinematic; Ignore is a real trade.
- Fumbles read as overbalance, not “miss.”
- Foe panel teaches plan/balance/attrs during development.
- Beasts feel different (glass vs steel defenses, dodge-not-block, stamina).
- Log is prose; meters stay numeric.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Momentum opaque | Debug breakdown + tune JSON |
| Incoming never/always | Tier thresholds playtest |
| Ignore too strong/weak | Crisis damage path vs Block efficacy tables |
| Name clash with footwork momentum | `strike_momentum` vs `footwork_momentum` |
