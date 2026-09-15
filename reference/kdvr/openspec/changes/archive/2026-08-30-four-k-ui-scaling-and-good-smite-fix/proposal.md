# Proposal: 4K UI scaling + good Smite ally fix

**Status:** Accepted and archived 2026-08-30  
**Change id:** `four-k-ui-scaling-and-good-smite-fix`

## Why

The game is **publicly released**. Two player-facing issues need past-version-safe fixes:

1. **4K monitors** — stock `tile_scale` (2 → ~24 px cells) looks tiny on 3840×2160. Players need an Options toggle for large UI, **off by default**, with missing settings key = off (old installs unchanged).
2. **Sheep cleric Smite** — good allies with Smite can hit the **player** while following. That violates good-alignment combat rules. Designer needs the cleric **temporarily eligible on depth 1** to playtest the fix, then stock spawn restored before archive.

## What

1. **Options → 4K UI scaling** (Off by default): when On, apply **2× effective `tile_scale`** (stock 2 → 4). Persist in `settings.json`; live-apply like Fullscreen / UI layout.
2. **Fix good Smite targeting**: do not trust chase `entity_target` when it is not a legal hostile for that alignment (mirror Path’s hostility gate). No entity-id hardcoding.
3. **Playtest aid**: temporarily widen `sheep_cleric` spawn to include depth 1; **restore 12–14** before final acceptance / archive.
4. Update live specs (`ui-layout`, combat/abilities or enhancements as needed).

## Out of scope

- Freeform UI scale slider / fractional scales
- Changing stock `ui_layout.json` `tile_scale` default for everyone
- Evil Smite rebalance or new abilities
- Permanent early-depth cleric roster change (unless designer later asks)
- Reworking `integer_scaling` / non-integer present blit
- Full pytest suite until final acceptance (targeted tests per PR)

## Past-version / release safety

| Surface | Mitigation |
|---------|------------|
| `settings.json` missing `four_k_scaling` | Default **False** — old installs unchanged |
| Saves / autosaves | No wire-format change for Smite; combat behavior only |
| Mods | No required mod schema change |
| Temp depth-1 cleric | **Must not ship** in final archive; restore `min_depth`/`max_depth` 12–14 |

## Success

- Options shows 4K UI scaling Off by default; On doubles effective cell size; Off restores prior look.
- Good Smite never damages the player; still smites visible evils in range.
- Designer can meet a sheep cleric on depth 1 during the playtest PR; final package uses 12–14 again.
- Existing settings/saves continue to load.

## Non-goals

- `if id == "sheep_cleric"` combat branches
- Shipping permanent depth-1 cleric without a separate content decision
