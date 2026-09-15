# Proposal: Ranged NPC overhaul

**Status:** Active  
**Change id:** `ranged-npc-overhaul`  
**Extends:** `openspec/specs/npc-abilities/spec.md`, `openspec/specs/balance/spec.md`, `openspec/specs/ranged-targeting/spec.md` (as needed); `data/entities.json`; `data/depth_scaling.json`

## Why

Stock Path/Smite NPCs can fire every turn indefinitely. That makes evil shooters oppressive at range and good allies overly strong as permanent DPS. The designer wants a **DCSS centaur-like** feel: shooters pincushion from range, stay a bit “dumb” (no clever kiting overhaul), and become much less threatening once the player closes to melee — where they stop shooting and rely on weak melee / vore.

## What

1. **Good ally ranged damage (data only):** Halve `ranged_min_damage` / `ranged_max_damage` on stock good RangeN/SmiteN entities (`ram_crossbow`, `sheep_cleric`), rounding **up** on odd values. No runtime multiplier.

2. **Shots resource (all RangeN / SmiteN NPCs):** Each such NPC has current shots and a max from the run’s difficulty profile:
   - `good_ranged_shots` — max for **good** RangeN/SmiteN NPCs
   - `evil_ranged_shots` — max for **evil** RangeN/SmiteN NPCs  
   Stock: **2 / 2** on easier, normal, hard; **2 / 3** on nightmare (good / evil). Firing Path or Smite costs 1 shot; cannot fire at 0. Player throws/smite unchanged.

3. **Reload turn:** Dedicated NPC action recovers **+1** shot (capped at max). Silent (no log). Priority:
   - At **0** shots: prefer reload; only **melee** and **vore** outrank it.
   - At **1** shot: reload only when idle (no target in sight and not actively chasing). Never reload to max while seeing or chasing a target.
   - **Good** RangeN/SmiteN: also prefer reloading up to max whenever **no enemy is in sight** (even at 1 shot).

4. **Evil hunger override:** Evil ranged/smite NPCs engaging a target always roll the usual vore-commit decision when eligible. On commit, that turn they **must** attempt vore (if in range) or **step toward** the target — no Path/Smite that turn. Hunger overrides “play it safe at range.” Compatible with `NoChase` (NoChase only stops pursuit after LOS is lost; visible quarry still allows approach).

## Out of scope

- Player ammo / player Smite changes
- Per-entity max_shots overrides (difficulty alignment knobs only)
- Reload / shots UI telegraph
- Soft accuracy after reload
- Redesigning Path hold/kite into smarter DCSS-perfect AI (intentional “dumb” ranged)
- Changing evil ranged damage numbers (except via existing depth scaling)
- RangedVoreN spending shots

## Success

- Good stock allies deal ~half prior ranged damage via authored JSON
- RangeN/SmiteN NPCs cannot infinite-fire; cadence gated by shots + reload
- Difficulty knobs drive good vs evil max shots; nightmare evil has 3
- Evil vore-commit forces close/attempt instead of another shot
- Good allies top up shots when no enemy visible
- Melee adjacency still stops Path/Smite (existing distance==1 rule) — centaur-like close vulnerability preserved
- Saves restore shots; missing field → full magazine for that entity’s max
- Tests use fixtures / pinned values, not live balance pins beyond stock JSON presence checks where appropriate

## Phased delivery

See `tasks.md`.
