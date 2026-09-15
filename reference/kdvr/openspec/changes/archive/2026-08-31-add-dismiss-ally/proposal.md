# Proposal: Dismiss ally (Shift+D targeting)

**Status:** Accepted — archived 2026-08-31  
**Change id:** `add-dismiss-ally`  
**Extends:** `openspec/specs/command-allies/spec.md` (or sibling dismiss section), help / tutorial discovery, `src/messages.py`

## Why

Players sometimes want to **solo**, or to clear a crowded follower pack so the next floor can roll fresh goods under the good-quota system. Today there is no intentional way to remove a living ally short of letting them be defeated or digested.

## What

1. **New free command:** **Shift+D** (Dismiss).
2. Opens a **targeting mode** in the same family as Examine / throw targeting (cursor move, Enter confirm, Esc cancel).
3. **Valid target:** a **good**-aligned NPC that is a normal dismissible ally on the map (not the player; not evil/neutral). Goods do not engulf others; an ally who is **engulfed** is not a practical target (the predator occupies the tile / takes examine priority) — treat as **invalid** if somehow selected.
4. On valid confirm: **immediately remove** that NPC from the game (clean despawn — not defeat, no XP / loot / defeat hooks) and log:  
   **`{NPC name} exits the dungeon.`**
5. On invalid confirm: **no-op** (stay in targeting), log:  
   **`Invalid target. (Allied NPCs only)`**
6. **No turn consumed** for entering targeting, canceling, invalid select, or successful dismiss.
7. **Help overlay** lists the binding; **tutorial** gets a short line if Actions keys are listed there.

## Out of scope

- Ordering allies to leave on their own (pathing off-map)
- Dismissing neutrals or evils
- Multi-select / “dismiss all”
- Confirmation dialog after Enter
- Changing good-quota spawn math (removal simply frees follower budget for later floors)
- Counting dismiss as defeat / past-run stats

## Past-version / release safety

| Surface | Mitigation |
|---------|------------|
| Saves | No new persistent fields required; mid-run dismiss is ephemeral |
| Mods | Any `alignment: good` entity is dismissible — no id hardcoding |
| Keybind | Plain `d` remains Drop; Shift+D mirrors Shift+W Wear pattern |

## Success

- Player can clear unwanted goods without combat
- Invalid tiles/entities never remove anything and show the fixed invalid line
- Dismiss never spends a turn or inflates defeat stats
- Help (and tutorial Actions) discover Shift+D

## Phased delivery

See `tasks.md`: PR1 targeting + despawn + tests; PR2 help/tutorial + live specs + acceptance + archive.
