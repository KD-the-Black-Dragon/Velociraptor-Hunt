# Proposal: Deferred Bugfixes (UI + AI)

## Why

Eleven items in `openspec/changes/todo/spec.md` were deferred to a **dedicated bugfix module**. They span message-log UX (wrap, colors, font, full log, help), rune HUD visibility, narrative capitalization, and AI pathing (neutral oscillation, corner pursuit, good–neutral corridor swap). Performance throttling remains a separate future module.

Players need readable logs, discoverable controls, visible rune progression, properly capitalized vore text, and allies that keep up in narrow corridors.

## What Changes

### Message log & overlays

- Word-wrap long log lines in the HUD panel.
- Six-color message category system (grey, red, yellow, green, cyan, magenta) with constants ready for future content.
- Experimental per-word JSON coloring in its own revertible PR.
- Proportional (non-fixed-width) font for the message log only; map/sidebar stay CP437.
- Full-screen scrollable log on **Ctrl+P** (free meta command, available anytime including modals).
- Full-screen help on **F1** and **?**; **Esc** dismisses both.
- Increase log history capacity to **100** entries.

### HUD

- Display collected rune bonuses in the status corner (including max HP rune bonus as its own row).

### Text pipeline

- Smart sentence capitalization after `{predator}`/`{prey}` substitution (Option 1); own revertible PR.

### AI

- Chase momentum after LOS loss (3–6 turn continuation, 8–12 turn give-up).
- Neutral explore anti-oscillation when no other stimuli.
- Good NPCs swap with blocking neutrals during follow/chase (corridor fix); neutrals never initiate swap.

### Debug hygiene

- Gate stdout debug prints (`map_gen`, `floor_init`, `prefetch`, AI frustration) behind an env flag.

### Deferred to `better-npc-exploration`

- Reachable BFS explore goals, explore frustration re-pick, door-in-face pack dispersal (discovered PR9 playtest). See `openspec/changes/better-npc-exploration/`.

## Out of Scope

- Performance / busy-floor AI throttling (separate module).
- Debug keys removal (pre-release; help will not list them).
- Map/sidebar font changes.
- Poison, MacGuffins, bosses (magenta category is reserved only).

## Capabilities

### Modified

- **`ui-layout`** — wrap, colors, log font, full log overlay, help overlay.
- **`floor-runes`** — status-corner bonus display (v1 was log-only for non-HP buffs).
- **`vore`** / **`digestion`** — capitalization on template paths.
- **`enhancements-3`** (or new **`npc-ai`** notes) — pursuit momentum, neutral anti-stuck, good–neutral swap pathing.

## Impact (anticipated)

| Area | Files |
|------|--------|
| Message log | `src/message_log.py`, `src/systems/render.py` |
| Overlays | `src/engine.py`, `src/app.py`, new `src/ui/log_overlay.py`, `src/ui/help_overlay.py` |
| Colors | All `message_log.add` call sites |
| Font | `src/main.py`, log render path |
| Rune HUD | `src/engine.py`, `src/ui/status_corner.py`, `src/systems/floor_runes.py` |
| Capitalization | `src/text.py` or `src/systems/naming.py`, vore/digestion formatters |
| AI | `src/systems/ai.py`, `src/systems/movement.py` or chase helpers |
| Debug | `src/map_gen.py`, `src/engine.py`, `src/floor_prefetch.py`, `src/systems/ai.py` |
| Tests | New/updated tests per PR |
| Docs | `README.md`, live specs, remove todo items |

## Success Criteria

- Long log lines wrap instead of clipping.
- Message colors match the six-category scheme for all current messages.
- Log text uses a proportional font; dungeon rendering unchanged.
- Ctrl+P and F1/? work during gameplay modals; Esc dismisses.
- Rune bonuses visible in status corner after collection.
- Vore/digestion template lines capitalize sentence starts and post-`.!?` boundaries.
- Good allies swap past neutrals in 1-wide corridors while following.
- Evil/good pursuit continues briefly after corner LOS loss; neutrals stop ping-ponging in corners.
- No debug stdout unless env flag is set.