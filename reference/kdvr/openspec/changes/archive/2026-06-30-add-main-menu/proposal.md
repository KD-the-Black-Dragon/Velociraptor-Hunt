# Proposal: Main Menu

## Why

The game currently boots straight into a dungeon and exits on digestion game over or Ctrl+Q. `VoreContentPreferences` defaults all narrative types on with a deferred "main menu" comment. Player display name is stubbed as `"Player"`. Load, high scores, and persistent options are placeholders in digestion design.

A main menu unifies entry, exit, settings, and post-run flow before save/load and leaderboard work lands.

## What Changes

- Black minimalist title screen with five options
- New Game → name prompt (`Anonymous` if blank)
- Load Game / High Scores → stubs (back out only)
- Options → Oral Vore / Cock Vore / Anal Vore toggles wired to `VoreContentPreferences`, persisted, at least one enabled
- Exit and window close → quit process; Ctrl+Q on menu → no-op
- Ctrl+Q in gameplay → quit confirmation (Y → menu, n → resume)
- Post-digestion recap → dynamic name and fate only (no score); Enter → main menu
- HUD shows player name instead of static game title during play
- Supersedes forced-OV-always-on and digestion's exit-on-recap stub

## Capabilities

### New

- `main-menu` — see `openspec/specs/main-menu/spec.md`

### Modified

- `vore` — content prefs from menu; OV not forced on
- `digestion` — recap → menu
- `core-roguelike` — app entry flow

## Success Criteria

- Normative spec scenarios covered by tests and manual checklist
- Full `pytest tests/` green
- Settings survive restart