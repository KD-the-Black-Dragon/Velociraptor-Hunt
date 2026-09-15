# Proposal: Good NPC spawn quota

**Status:** Accepted and archived 2026-08-15  
**Change id:** `good-npc-spawn-quota`

## Why

Good allies currently compete in the **same density-weighted spawn pool** as evil and neutral NPCs. That makes ally presence random: a floor may get zero goods even when eligible species exist, or more goods than the player can reasonably manage alongside followers from the previous floor. Descent only **reduces total NPC budget** by follower count (capped by sum of good weights); it does not guarantee or cap good presence.

Design intent: floors that **can** host goods should **always** aim for a small, predictable ally count (followers first, then weighted new spawns), with the cap **data-driven by difficulty**.

## What

1. Replace the current “goods mixed into density + follower density deduction” model with a **good spawn quota**:
   - Per-difficulty **limit** (stock: **Normal / Hard / Nightmare = 2**, **Easier = 3**).
   - On each floor population: if **no** good species is eligible to spawn at this depth (weights, depth window, terrain/water gates), spawn **zero** new goods (no loops).
   - Count **brought good followers** toward the limit with **`>= limit` → at cap** (over-cap from descent is fine; spawn **no** new goods).
   - If under the limit and eligible goods exist, **weighted-spawn** new goods until at the limit (or tiles/eligibility run out).
2. Make the limit **data-driven** on the difficulty profile (`depth_scaling.json`), not hardcoded game logic beyond a safe default when omitted.
3. Update **npc-data** / **dungeon** / **balance** specs and SCHEMA for the new field and spawn algorithm.
4. Remove or retire **`good_follower_reduction` / `good_aligned_weight_at_depth` density deduction** in favor of the quota.

## Out of scope

- Changing who follows on descent (LOS / good alignment rules stay as-is)
- Good AI, combat, intro lines, or entity roster content
- Evil/neutral density formulas (beyond excluding goods from that pool — see design)
- Depth scaling of good **stats**
- Full suite regression beyond targeted tests for this change (unless designer asks)

## Success

- Depth with no eligible goods (e.g. floor 1 stock): **0** new goods; no hang.
- 0 followers + eligible goods: **exactly `limit`** new goods when tiles allow (Normal: 2).
- 1 follower: **`limit - 1`** new goods.
- `>= limit` followers: **0** new goods.
- Easier: limit **3**; Normal: **2**.
- General density spawn no longer randomly adds goods beyond the quota.
- Playtest: allies feel reliably present without stacking endless knight trains from pure RNG.

## Non-goals

- Hardcoding `if id == "knight"` (or any single species)
- Soft-deleting mods or save fields
