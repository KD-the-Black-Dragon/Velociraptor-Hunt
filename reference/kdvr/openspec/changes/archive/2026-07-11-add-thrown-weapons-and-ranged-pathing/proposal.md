# Proposal: Thrown weapons and ranged pathing

**Status:** Active (design locked 2026-07-10)  
**Change id:** `add-thrown-weapons-and-ranged-pathing`

## Why

The player has melee and wand (Smite) combat but no physical ranged option. NPC ranged today is a single LoS model (`RangeN` in data, effectively Smite). Splitting **Smite** vs **Path** targeting clarifies magic vs physical projectiles, enables cover/allies-in-the-way tactics, and completes the combat vocabulary with consumed throwables — without bows, slings, or crossbows.

## What

1. **Rename** existing `Range2`…`Range9` ability tokens to **`Smite2`…`Smite9`** (same behavior; wands remain Smite).
2. **Add Path ranged** via reclaimed **`Range2`…`Range9`** — Bresenham beam, alignment path blocks, first valid `Fighter` along the line takes the hit.
3. **Player throwables** — `data/throwables.json`, stacking ammo, Path resolve, full player LoS range (adjacent throws allowed).
4. **Controls** — `f` auto-readies highest-`max_damage` throwable → target cursor; `F` modal to pick a throwable manually.
5. **NPC Path AI** — nearest valid target with clear path; kite at optimal distance when denied; good allies stay near player when repositioning.
6. **Projectile animation** — brief glyph travel along beam (FOV-gated).
7. **Log verbs** — NPC Smite: *smites*; NPC Path: *shoots*; player throw miss: *Your throw misses the {target}.*
8. **Content** — throwables depth 1–20; starter **5 rocks** in slot `c`; fox archer ships with `Range5`.

## Out of scope

- Bows, slings, crossbows, quivers, launcher equip slots.
- Throwable recovery / durability (always consumed).
- Mod backward-compat aliases for old `RangeN` Smite tokens (game not live).
- Item `abilities[]` on weapons/armor JSON.
- Friendly fire (same-alignment on path cancels shot).
- Macguffins, balance simulator updates.

## Spec targets (on archive)

| Spec | Action |
|------|--------|
| `openspec/specs/inventory-items/spec.md` | Throwables, `f`/`F`, starter rocks |
| `openspec/specs/equipment-catalog/spec.md` | Throwable tier catalog |
| `openspec/specs/npc-abilities/spec.md` | `SmiteN` + `RangeN` (Path) |
| New `openspec/specs/ranged-targeting/spec.md` | Smite vs Path rules (shared) |

## Success

Player can `f`-throw rocks at visible evils with path blocking; `F` overrides weapon choice; wands still Smite; fox archer shoots (Path) with ally-block awareness; Smite NPCs *smite* and Path NPCs *shoot* in the log; projectile anim visible when in FOV.