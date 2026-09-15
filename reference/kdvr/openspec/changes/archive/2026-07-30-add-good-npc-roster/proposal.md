# Proposal: Add good NPC roster (anthro allies)

**Status:** Accepted and archived 2026-07-30  
**Change id:** `add-good-npc-roster`

## Why

The dungeon currently has a full evil progression ladder and only **one** good ally species (`knight` / dog knight), which spawns from depth 3 through the entire soft cap. That under-serves early floors, over-extends a single archetype into late game, and leaves no good-side counterparts to mid-depth specialists (fox archer Path, owl mage Smite).

## What

1. **Expand good-aligned stock** in `data/entities.json` with anthro animal allies whose **rank titles rise** with depth.
2. **Dog Squire** at the bottom (spawn **2–4**); handles early vermin.
3. **Dog Knight** becomes clear **2nd tier**: spawn **5–7**, **combat stats strengthened** (examine / intros / Sir name pool kept).
4. **Equal-length melee bands (3 floors each):** ferret Guard → lion Warrior → otter Warden → boar-at-arms → badger Champion.
5. **Specialists on parallel tracks:** **Ram Crossbow** (`Range5`) and **Sheep Cleric** (`Smite5`); **identical** melee and ranged accuracy/damage.
6. **Badger Champion** peer-scaled vs **gryphon**; spawn **17–1000**.
7. **Boar-at-arms** naming (no “man”); names like `Garrick-at-arms`.
8. **Presentation:** cyan `fg`; unique glyphs where free.
9. **Names / intros:** each new type has its own pools; **Sir only for knights**.
10. **Balance:** goods win ~**95%+** 1v1 vs band peer (sim-backed); packs / out-of-depth can defeat them. Goods may be strong (no struggle-free when swallowed).

## Out of scope

- New Python systems, AI, abilities, or combat rules
- Evil rebalance, depth_scaling, dungeon density
- Neutral roster, rabbit revival
- Vore narratives (goods never vore)
- Rewriting knight examine / introduction lines / Sir name list
- Depth scaling for goods
- Full automated regression suite on final acceptance (**designer waived**)

## Success

- Stock loads; new ids spawn in designed bands.
- Playtest: squire from depth 2; knight mid-early only and stronger; short hand-offs through otter/boar; champion late; ram/sheep specialists with equal melee/ranged punch.
- Goods dominate fair 1v1 peers; get eaten when swarmed or out of depth.
- Naming schemes match design (Sir / Squire / Guard / … / `-at-arms` / Champion / Crossbow / Cleric).

## Non-goals / explicit non-hacks

- Do not delete files to “make room”; soft-remove only via project Recycle Bin policy if ever needed.
- Do not rename `knight` id.
