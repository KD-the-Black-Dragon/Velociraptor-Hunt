# Proposal: Come here! (ally summon shout)

**Status:** Accepted — archived 2026-07-09  
**Change id:** `add-come-here`  
**Supersedes:** Follow/Attack command-allies draft (`deferred-add-command-allies/`)

## Why

Good allies sometimes get stuck in dumb standoffs (e.g. lake shoreline staring contest with an unreachable wolf). The player needs a light, temporary way to peel them off that goal without permanent pet-follow micromanagement.

## What

One player shout: **“Come here!”**

- **One key** (proposed: main keyboard `1`, not numpad).
- **Costs a player turn**.
- Affects **good** NPCs in **player FOV** at shout time only.
- Each affected ally enters a temporary **come-here** AI mode: top priority is become **Chebyshev-adjacent** to the player.
- On **any adjacency** (even one instant), the ally **immediately** returns to standard good AI.
- No laser-homing: normal FOV / last-known pursuit / give-up rules only. If they hopelessly lose track of the player, abandon come-here and resume standard AI.
- **Cooldown 4 turns** between successful shouts; spam → *"You'll go hoarse if you shout too much."* (no turn consumed).
- **Frustration:** if evil blocks a narrow path to the player, good ally attacks that evil (same incremental-progress idea as evil blocked by neutral).

## Out of scope

- Attack / permanent Follow / stick-close modes  
- Multi-order menus  
- Neutrals (rabbits)  
- Allies outside FOV at shout time  
- Changing lake/standoff combat in general  

## Success

- Player can unstick a good ally stuck on an unreachable evil by shouting once.  
- After the ally tags the player, they freely return to normal priorities.  
- Shout spam is limited.  
- No new permanent companion AI.
