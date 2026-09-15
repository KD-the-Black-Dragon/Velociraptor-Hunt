# Archive: add-rest-until-healed-or-danger

**Archived:** 2026-07-04  
**Live spec:** `openspec/specs/enhancements-1/spec.md`

Main keyboard **`5`** runs rest-until: repeated waits until full HP, player-targeted attack, evil in FOV, good ally alarm, or 100 turns. Pre-checks and halt messages use red log color. Rest is incremental (non-blocking loop), supports manual interrupt on any gameplay key, and leaves numpad **`5`** as single-turn wait.

**Delivered PRs:** PR0 only (single slice)