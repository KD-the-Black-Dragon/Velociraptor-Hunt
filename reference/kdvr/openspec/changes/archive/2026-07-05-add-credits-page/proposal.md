# Proposal: Credits Page

**Status:** Draft  
**Date:** 2026-07-05

## Why

The main menu has no way to view authorship, support links, or third-party attributions. Players who want to credit K.D., find Patreon/FurAffinity pages, or understand which fonts and libraries power the game must look outside the application.

## What

| Area | Deliverable |
|------|-------------|
| Main menu | New **Credits** option, always visible, placed **above Exit** |
| Credits screen | Full-screen informational page (help/log visual style): title, credits, links, font/library attributions |
| Navigation | **Esc** returns to main menu (same phase pattern as Past Runs and Options) |
| Presentation | `MESSAGE_LOG_BACKGROUND`, colored static lines, proportional Source Sans 3 when `LogFontState` is loaded (like F1 help) |
| Spec | Extend `openspec/specs/main-menu/spec.md` with Credits requirement |

## Out of scope

- Clickable URLs or OS browser launch
- In-game credits overlay (main menu only)
- Scrolling (21 content lines + footer fit 44-row stock layout without scroll)
- New dependencies or font files
- Adding `attrs` to `pyproject.toml` (document as transitive MIT attribution only)

## Related specs (update on acceptance)

- `openspec/specs/main-menu/spec.md` — Credits option placement, screen behavior, Esc back

## Full design

`design.md` and PR checklist in `tasks.md`.