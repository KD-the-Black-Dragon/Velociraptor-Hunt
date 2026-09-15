# Proposal: Data-driven balance knobs

**Status:** Design review (revised — prefixes/Elite, Past Runs difficulty, rejections)  
**Change id:** `add-balance-knobs`

## Why

Early development has only a handful of species and coarse balance levers. The player gains permanent power from **equipment and floor runes** faster than the dungeon escalates, so game-over risk collapses after a few floors. We need **orthogonal, JSON-tunable knobs** — named difficulty presets whose main lever is **how hard the game gets per floor**, plus **visible elite variants** without authoring full new species.

## Progression philosophy

**Exploration-based**, not kill-based. Player strength comes from finding gear and floor runes. **XP / leveling is not a direction.**

## What

1. **Difficulty presets** — Easy / Normal / Hard / Nightmare in JSON. Chosen in **Options**; **New Game snapshots** into the run. Profiles include dual-int depth curves, **density**, and **rune economy** (whole-number `rune_pieces_multiplier`). Harder modes **steepen descent**, not floor-1 flats.
2. **Depth scaling** — Bake combat + **digestion damage** at spawn. Integer dual knobs (`per_floor` + every-N bank). **No `digest_time` scaling.** Accuracy and min/max damage schedules are **separate**.
3. **Piece-based floor runes** — Zelda thresholds; **separable** accuracy / min / max damage banks.
4. **NPC prefixes (Elite first)** — Generic prefix system: not a new entity id; `DisplayName` becomes `Elite Wolf` / `Elite Bat`; flat stat bonuses from `data/npc_prefixes.json`; chance from difficulty `prefix_spawn`. Future prefixes are data rows only.
5. **Placeholder entity workflow** — flag + docs; weighted fillers in content PR.
6. **Past Runs** — **must show difficulty**; **no** in-run difficulty HUD.
7. **SHOULD:** data-driven `runes_per_floor` (spawn + map feasibility).

**Content tune (PR5)** is in this change (real curves / elite chance / fillers).

## Explicitly out

- XP / kill-leveling  
- Digestion strike-count (`digest_time`) scaling  
- **Loot austerity by difficulty**  
- **Natural regen rate by difficulty**  
- **In-run difficulty on HUD / status corner**  
- Mid-run difficulty change; mid-floor re-bake of living NPCs  

## Success

- Designer tunes difficulties and elite pressure almost entirely in JSON.  
- Players recognize elites by name (`Elite …`).  
- Past Runs board shows difficulty for every completed run.  
- Floor 1 stays approachable; deep floors threaten on higher difficulties.  
- Soft-drop unknown prefixes; fixture-pinned tests; archived after acceptance.

## Designer decisions (summary)

| Topic | Decision |
|-------|----------|
| Who scales | Evil only |
| Followers | No re-bake on descent |
| Difficulty UI | Options → snapshot at New Game |
| Stock ids | easy / normal / hard / nightmare |
| Economy | density + rune overrides; whole-number pieces multiplier |
| min/max damage | Separate schedule keys |
| Elites | Prefix system; `Elite ` + base name |
| Past Runs difficulty | **Yes** |
| In-run difficulty HUD | **No** |
| Loot austerity / regen by difficulty | **No** |
| XP | Out of direction |
