# Design: ai-personality-fuzzy (BP-A)

| Field | Value |
|-------|--------|
| **Module** | `ai-personality-fuzzy` |
| **Program** | `../battle-pace-program/BATTLE_SPORT_SPEC.md` (authoritative) |
| **Status** | Design frozen 2026-08-10 — implement only after whole-batch authorization |
| **Depends on** | weapon-measure; player-combat-commands (footwork + measure attacks); ready-actions preferred; footwork-momentum preferred |
| **Implements** | Enemy fuzzy AI **and** ally fuzzy AI (different scorers) |

---

## Problem

AI that only pathfinds adjacent and bumps recreates roguelike pace and ignores balance. Need personality-weighted fuzzy choice over the **same verbs** as the player, plus ally orders and morale.

---

## 1. Shared infrastructure

### Candidate intents (legal only)

Hold measure / step toward or away / keep watch / brace / footwork / basic attack profiles / seed abilities on kit / clinch approach & grab when legal.

### Scoring method

- CK2-like **fuzzy weights** from attributes + geometry fitness (weapon measure) + order modifiers + noise.
- **No** `if entity_id == "wolf"` logic.
- **No** finite archetype enum as the sole system.

### AP and abilities

- NPCs have AP pools and regen like the player.
- Entity data: ability list; AI may use any **listed** ability that is **legal** now.
- **Cunning** = frequency of ability **and** footwork use among candidates — not “unlocks” abilities.
- Seed subset content this batch; architecture data-driven for all future abilities.

---

## 2. Attributes (0–10, 5 neutral)

Rolled once per spawned instance from entity **min/max inclusive** fields (`min_ferocity` … `max_appetite` or equivalent). No species layer. Bosses = entities.

| Attr | Behavior |
|------|----------|
| **Ferocity** | Close pressure; preferred balance home; reset sloppiness; bolder basic profiles. **10** charge-down. **5** baseline maneuver. **0** watch/brace, hang −6…−8, poke lightly, brace on approach |
| **Cunning** | Technical rate: abilities + footwork. **0 never**; **1–2 rare**; high = purposeful footwork (enter for strike or escape) |
| **Tenacity** | Morale shock resistance; ally protect-vs-panic when hurt |
| **Appetite** | Vore recklessness if vore-capable; else **no-op**. **0** = only downed/helpless. **10** = clinch targets who will likely wrestle free |

### Preferred balance

- Provisional JSON table by Ferocity (see program freeze).
- **Never prefer +9/+10** (common sense reset).
- **+6…+8** allowed as aggressive style for high Ferocity.
- Reset sloppiness scales with Ferocity.

### Morale shock

| Property | Rule |
|----------|------|
| Trigger | ~**Tenacity × 10%** max stamina lost **since last shock ended** (JSON table) |
| Effect | Force **Ferocity to 0–2** for shock duration (implements defensive bias) |
| Duration | **8–16 AUT** each panic (independent roll) |
| After | Restore true Ferocity; still obligated to fight |

---

## 3. Enemy scorer goals

Primary fantasy: **who can I pressure / eat?**

Weights emphasize:

- Measure fitness for equipped/natural weapon
- Ferocity → close vs hold
- Cunning → specials/footwork rate
- Tenacity → post-damage behavior via morale
- Appetite → clinch timing and recklessness
- No mercy timer on re-grab this batch

---

## 4. Ally scorer goals

Primary fantasy: serve employer / stay alive longer — imperfectly.

| Topic | Rule |
|-------|------|
| Verbs | Same candidate set as enemies when legal |
| Appetite | Only if beast/vore-capable |
| Protect | High Tenacity → cover PC even low stam; low → self-save when low stam |
| Orders | See §5 — **always obey** this batch |
| Green vore | Digestion damage OK; at 0 stam prey defeated → **immediate** regurgitate |
| Crisis | No hard auto-spike; player calls Help me! |

---

## 5. Talk orders

`T` → ally **or all** → order.

| Order | Meaning |
|-------|---------|
| **Attack!** | Free play (default at match start; no forget timer until another order) |
| **Help me!** | Prefer enemies with recent **aggressive** acts on PC (incl. feints); window ~3–5 AUT. If none → **Stay close** behavior |
| **Stay close!** | Prefer Chebyshev ≤ **2** from PC |

| Memory | ~10 AUT solid obey, then rising forget chance → free play (JSON) |
| Obedience | Always (no Disobedient this batch) |

---

## 6. Call for help

| PC state | UI |
|----------|-----|
| Downed / grappled | Talk → Help me! (free Talk rules when available) |
| Swallow modal (not fully in) | Option **3**: call help; **advance phase** with **no** escape and **no** conserve |
| Fully swallowed | Modal off; Talk works again |

| Heard | While **swallowing or fully swallowed**, **50%** chance call heard. Downed/grapple Talk: always heard (default). |
| Free Talk | Talk path only; option 3 is not free Talk |

---

## 7. Out of scope

- Perfect tactical search
- Full CK2 trait encyclopedia
- Clinch mercy timers
- Disobedient trait
- Crowd-driven AI
- Replacing entire grapple math

---

## 8. Acceptance

- Enemies are not pure rush-bump-grab robots; Ferocity 5 baseline maneuvers.
- High Ferocity + low Cunning ≈ relentless basic pressure.
- Cunning 0 never footworks or abilities.
- Morale shock visibly makes fighters defensive for 8–16 AUT.
- Allies obey Attack / Help me / Stay close; forget after time.
- Help me tracks feints and attacks; falls back to stay close.
- Swallow option 3 + 50% hear rule work.
- Green ally pipeline regurgitates at 0 stam defeat.
- All weights/timers in JSON.
