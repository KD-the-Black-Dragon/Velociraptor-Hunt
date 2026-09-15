# Proposal: More potion effects

**Status:** Design locked (2026-07-09) — coding after PR1 authorization  
**Change id:** `add-potion-effects`

## Why

Stock potions are heal-only. Players need classic magical tools (escape, tempo, info, allies) without a separate scroll category.

## What

1. Generalize potion `effect` dispatch beyond `heal`.
2. Stock potions (plain names, utilitarian examine, no numbers in examine):
   - **Teleportation** — delay 3–5 turns; refresh if re-drunk; **teleport escape** if engulfed; land walkable unoccupied tiles only
   - **Blinking** — “Blink where?”; only **currently visible + LOS** tiles; consume **only** on success
   - **Haste** — **20** turns; 2 player actions per monster phase; accelerates rest via more turns
   - **Might** — 10 turns; +0.15 accuracy, **+5/+5** damage
   - **Alliance** — weighted **good** ally at depth; place as close as possible; no cap
   - **Discovery** — full map `explored`; no free LOS
   - **Antacid** — 20 turns; **nullifies digestion damage and digestion strikes** (vore humor name; effect `digestion_ward`)
3. `PlayerEffects` + status corner + save/load.
4. Keep three heal tiers; retune spawn weights in content PR.

## Explicitly out

Scrolls; potion ID; cancel / levitation / detect / berserk / invis / HoT; ally caps; numeric examine prose.

## Success

All listed effects work, persist, and play cleanly; heal unbroken; designer adds stock mostly via JSON + small handler.
