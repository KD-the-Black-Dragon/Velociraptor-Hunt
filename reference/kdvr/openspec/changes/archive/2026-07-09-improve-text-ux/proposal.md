# Proposal: Improve text UX (placeholders, layout, chrome, fonts)

**Status:** Accepted — archived 2026-07-09  
**Change id:** `improve-text-ux`

## Why

Several text surfaces are wrong or hard to read: `{predator}` is not substituted in NPC→player vore modals; SCHEMA omits markup category lists; min-size windows clip long prompts; many dialogs are bare unstyled text; narrative and other word-heavy UI still uses fixed-width tiles instead of the log proportional font; new-game overwrite warning collides with the title logo.

## What

1. Substitute `{predator}` in NPC→player **vore** modal phases (same name rules as logs). No `{prey}` in those modals.
2. Document full log color markup categories (+ aliases) in `data/SCHEMA.md`.
3. Word-wrap and clamp menu/dialog prompts to the console; keep content on-screen at minimum window size.
4. Shared simple dialog chrome (panel + padding + border) for bare Y/n and similar notices.
5. **Log font for all word-heavy / sentence UI** (modals and popups). Fixed-width remains only for map, short labels (sidebar names, status corner), main menu chrome, Options/Mods lists. **Full sentences in fixed-width = bug.** Trial one proportional modal first, then roll out after playtest OK.
6. New-game overwrite prompt uses the same lower band as the mod-mismatch notice (below title logo).
7. Quit / mods-enter / macguffin confirms share layout + chrome with other menu dialogs. Help overlay unchanged.
8. **Default log color `caution`** when the player **witnesses** (in FOV) a predator **successfully** swallowing or **finishing digestion of** an NPC — no per-line markup required. **Not** applied to failed vore attempts or offscreen “heard only” lines.

## Out of scope

- Help overlay redesign
- Rewriting stock narrative copy
- Code mods / new narrative systems
- Changing map/sidebar/status tile rendering

## Success

- `{predator}` never appears literally when data uses it correctly in player vore modals
- SCHEMA lists valid markup categories
- New-game and similar prompts readable at min size and clear of the logo
- Word-heavy surfaces use log font after rollout; designer accepts trial
- Bare prompts no longer look like raw floating text
