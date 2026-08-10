# Proposal: Grapple / swallow modals + swallow escape retune

## Problem

1. **Grapple UI** lives in the status column (`GRAPPLE — you are held!`), while incoming attacks already use a distinct red low-right modal. Grapple is equally urgent and should match that presentation, with predator-named copy.
2. **Swallow** is a multi-phase coup de grâce, but it currently reuses the same thrash/break-away path as wrestling. Escape chance is roughly `break_away_chance × 0.35` (**~12–26% per struggle**), so players escape mid-swallow far too often.
3. Designer intent: **grappling = real wrestling chance to break free**; **swallow = exhausting coup de grâce** where escape is **miraculous (~1% per struggle)**. Swallow should feel **distracting** — a larger, interface-blocking interactive modal with narrative room and a meaningful choice (struggle vs conserve strength for the stomach), not a dismiss-with-Enter cutscene.

## Solution

OpenSpec change **`grapple-swallow-modals`**:

| Area | Change |
|------|--------|
| Grapple (PC prey, `VorePhase.GRAPPLE`) | Red modal (same family as INCOMING); title/line **`{PredatorName} grapples you!`**; keep interactive 1 break / 2 counter / brace |
| Swallow (PC prey, `VorePhase.SWALLOW`) | **Large interface-blocking** interactive modal; narrative body (stub lines first, expandable later); choices: **struggle** (tiny escape chance) vs **conserve strength** (no escape; improve later endurance inside) |
| Math | Swallow struggle escape **~1%** (JSON); stop using grapple break-away formula × 0.35 |
| Engulfed | Still interactive (existing thrash); conserve-strength bonus applies when digestion starts (exact bonus in design) |

## Non-goals

- Full Wrestling fairness rebalance for the grapple HP war (except copy/UI)
- Full multi-paragraph vore prose library (seed stub + structure for more later)
- Ally-as-prey modal polish (log/status OK unless freebie)

## Success

- Grapple reads like INCOMING urgency with predator name.
- Swallow blocks the fight UI; player still chooses struggle vs conserve each prey turn.
- Swallow self-escape is rare enough that it feels miraculous; real escapes stay in the grapple phase (or ally damage / regurg rules).
