# Manual checklist — PR4 (proportional log font)

Run: `python -m src.main`

## Proportional message log

- [ ] Start a new game; message log text uses **Source Sans 3** (smooth, proportional — `iii` is visibly narrower than `WWW`).
- [ ] Map tiles, sidebar HP bars, status corner, and menus still use the **CP437 tileset**.
- [ ] Category colors from PR2 still apply (grey routine, red danger, white speech introductions, etc.).
- [ ] Multi-color markup rows from PR3 still render correctly in the TTF log.

## Readability

- [ ] Long wrapped lines remain readable and fit within the log panel width.
- [ ] Log background color unchanged (dark panel behind text).

## Fallback (optional)

To verify fallback: temporarily rename `data/fonts/DejaVuSansMono.ttf`, restart the game.
- [ ] Game starts without crashing; log reverts to CP437 glyphs.
- [ ] A **single** warning appears in the terminal about the missing font.

Restore the font file after testing.

## Regression

- [ ] Word wrap (PR1), category colors (PR2), and inline markup (PR3) still work.
- [ ] No debug stdout without `DEBUG_STDOUT=1` (PR0).