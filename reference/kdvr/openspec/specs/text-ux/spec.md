# Spec: text-ux

Proportional log font and dialog chrome for word-heavy UI.

## Requirements

### Narrative modals
- Player **digestion**, **vore** attempt/success, and **examine** description use the digestion dialog model when the log TTF is available: log face +2, shared chrome, content-hugging width, ~1.28× body line spacing.
- CP437 fallback when the font is missing or disabled.
- **Screen haze:** while the player has `DigestionStrikes` (0 HP digestion phase), the playfield darkens linearly with strike count, maxing at **5 strikes** (full veil = same alpha as digestion-completion / game-over overlay). Digestion completion modal and game over use full veil.

### Utilitarian lists
- Inventory (inspect list, drop, wield, wear, quaff, evoke pick) and ground pickup use multi-column layout (dynamic 1–3 columns by item count and width; fill down then next; wrap in cell; content-hugging width).
- Same digestion dialog font for list panels; item detail is single-column narrative style.

### Sentence confirms
- Quit, new-game overwrite, mods-enter wipe, macguffin victory, and main-menu load/mod notices use the proportional confirm panel when the log font is available (whole dialog including footers/errors).

### Game over
- Title **GAME OVER** remains fixed-width (tile) presentation.
- Body (name, fate line, stats) and footer use log font when available.

### Log color defaults
- Witnessed on-screen NPC swallow success and NPC digestion-complete lines default to `MessageCategory.CAUTION`.
- Miss / offscreen atmospheric lines are not forced to caution.

### Placeholders
- NPC→player vore modal phases format `{predator}` safely (unknown keys left literal).

## Non-goals
- Help overlay redesign.
- `{prey}` in player modals.
- Stock narrative rewrite.
