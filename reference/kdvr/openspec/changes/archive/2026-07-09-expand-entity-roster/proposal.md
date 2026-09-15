# Proposal: Expand entity roster (placeholders + themed mid cast)

**Status:** Approved for implementation (designer lock 2026-07-09)  
**Change id:** `expand-entity-roster`

## Why

Balance and progression need a deeper cast than bat/wolf + thin fillers. New species should land as **themed vore identities** (not plain animals), with spawn bands that ramp toward a soft deep-floor “you’ve gone far enough” pressure (Skifree-yeti, not a hard wall at 1000).

## What

1. **Retheme** `cave_rat` → ROUS: oil, slobber, yellow teeth, tail-grab, tightness (no disease/smell).
2. **Deprecate** `giant_spider` (`spawn.weight: 0`; id kept for old saves).
3. **Add** themed stock entities (placeholder flag; quality text where theme is locked):

| id | Role |
|----|------|
| `slime` | Silent alien gel; envelop / unmake |
| `tarantula` | Placeholder only (designer pipeline later) |
| `fox_archer` | Anthro fox adventurer; strong ranged, weak melee; casual “another enemy” confidence |
| `gnoll_mercenary` | Anthro scavenger; loot-hunter; weak ranged, solid melee |
| `roc` | Haughty ~3× player flyer nobility |
| `owl_mage` | Anthro mage; narrative micro-vore spell; science curiosity |
| `wyvern` | Deep placeholder |
| `drake` | Deep placeholder (wingless dragon) |
| `gryphon` | Deep placeholder |
| `dragon` | Deep soft-stopper placeholder |

4. **Spawn bands** so early floors favor weak/scrappy cast; deep floors introduce sparse heavies.
5. **No new code systems** this change (no real shrink mechanic, no loot steal) — narrative + combat stats only.

## Out of scope

- Full final narratives for tarantula / deep dragons (stubs OK)
- kobold / tunnel_slug retheme (deferred)
- Narrowing bat/wolf max_depth (optional later)
- Micro-vore as engine size flag
- New abilities beyond existing tokens

## Success

- Stock `entities.json` loads; all new ids spawn in intended bands.
- `giant_spider` never spawns new; old saves soft-handle via existing id.
- Designer can playtest progression and revise text later.
