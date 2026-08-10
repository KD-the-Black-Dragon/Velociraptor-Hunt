# Proposal: Match HUD layout + reaction panel + ally bump no-op

## Problem

During arena fights, the current match present path (`present_match_frame` + `match_text_lines`) dumps **stats, prompts, reaction choices, and the action log** into a single band **below the map**. That leaves a large empty region **to the right of the map**, crowds the bottom with non-log content, and places the **incoming-attack “INCOMING!” UI in the log stream** instead of a true modal panel.

Separately, **bumping an ally** routes through smart melee (`_player_melee_smart`), so a blocked, ineffective contact still spends **AUT** and advances the fight clock.

## Solution

A short OpenSpec change **`match-hud-ux`** that:

1. **Splits fight chrome by screen region** (log font for all non-map text; map tiles unchanged):
   - **Bottom band** = action log only (+ shared footer keys if already global).
   - **Right of map** = combat status: HP, AUT, AP, balance, card/kind, crowd/diff, injuries, non-modal scene lines (grapple status when not a separate full overlay).
2. **Renders the reaction UI as a dedicated low-right modal panel** that does not cover the map, the action log, or primary status meters. Exact pixels may iterate; region is intentional.
3. **Ally bump = no-op**: no AUT commit; log `"{ally name} is standing there."` with dynamic ally name.

## Scope

| In | Out |
|----|-----|
| Match fight present (proportional + CP437 fallback) | Hub / menu redesign |
| Reaction announce panel placement | Battle-pace measure/footwork |
| Ally (and optionally other non-enemy friendly) bump no-op | Full shop/roster UI polish |
| Spec + tests for no-op + structural present helpers | Hard KDVR prune |

## Success

- Designer can read meters beside the arena while the bottom is clearly a **log**.
- Incoming attack UI is visually distinct and **not** buried in log lines.
- Walking into an ally does not advance world AUT; message names the ally.
- Manual playtest checklist for one PR (or two if split).
