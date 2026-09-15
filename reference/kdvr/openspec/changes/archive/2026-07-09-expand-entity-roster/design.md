# Design: expand-entity-roster

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Status** | Locked for PR1 content |
| **Spec** | Extend `openspec/specs/npc-data/spec.md` lightly (roster note only) |

## Themes (locked)

| id | Theme spine | Text quality this PR |
|----|-------------|----------------------|
| `cave_rat` | ROUS: oily fur, yellow teeth, sticky slobber, tail as grab, **tight / oily / slimy** guts. Not disease, not stink theater. | Full-quality attempt |
| `slime` | Silent alien gel — curious cling without voice or cuteness | Full-quality attempt |
| `tarantula` | Reserved for designer pipeline | Stub + examine hook |
| `fox_archer` | Anthro archer; elegant practiced vore; PC as one of a hundred; light RPG taunt (XP / stats) | Full-quality attempt |
| `gnoll_mercenary` | Hyena scavenger anthro; extraction-shooter loot hunger; gear-focused taunts | Full-quality attempt |
| `roc` | Sky aristocracy; ~3× player; cargo → meal; contemptuous dignity | Full-quality attempt |
| `owl_mage` | Shrink spell → micro-vore; science “never eaten your kind” | Full-quality attempt (narrative-only shrink) |
| `wyvern` / `drake` / `gryphon` / `dragon` | Deep ramp / soft yeti zone | Stubs |

## Spawn philosophy

Depth **1000** remains a soft asymptotic cap. Deep heavies are sparse and brutal so runs that push far meet “the game has had enough,” not a literal wall.

| Band (approx) | Cast |
|---------------|------|
| 1–6 | bat, cave_rat, slime (+ wolf still present until later retune) |
| 4–12 | tarantula mid |
| 5–16 | fox_archer, gnoll_mercenary |
| 10–24 | roc, owl_mage |
| 18+ | wyvern → drake → gryphon → dragon (increasing severity) |

Exact `min_depth` / `max_depth` / `weight` live in JSON and may be playtest-tuned without code.

## Save compatibility

- New ids: additive.
- `giant_spider`: **`spawn.weight: 0`** (deprecated; keep definition for in-flight saves).

## Implementation

- Data-only: `data/entities.json`
- Tests: load registry; assert new ids present; spider weight 0; optional spawn-band smoke
- No Python combat/AI changes

## Resolved decisions

| Topic | Decision |
|-------|----------|
| giant_spider | Deprecate weight 0; tarantula is separate id |
| Micro-vore | Narrative only |
| Deferred species | kobold, tunnel_slug rethemes; unlisted animals |
| Feral vs anthro | More ferals overall; this PR still adds several anthros as designed |
