# Manual checklist — PR5 (full log overlay Ctrl+P)

Run: `python -m src.main`

## Open / close

- [ ] During play, **Ctrl+P** opens the full-screen message log.
- [ ] **Ctrl+P** again (or **Esc**) closes the overlay and returns to normal play.
- [ ] Overlay uses the proportional log font (PR4) when the bundled TTF is present.

## Scroll

- [ ] On open, the **newest** messages appear at the bottom of the viewport.
- [ ] **Up** / **Y** / numpad **8** scroll toward **older** lines.
- [ ] **Down** / **N** / numpad **2** scroll toward **newer** lines.
- [ ] **PgUp** / **PgDn** jump one page (about one screen of wrapped lines).
- [ ] Footer shows: `Esc: close | Arrows: line | PgUp/PgDn: page`.

## Meta UI (not blocked)

- [ ] Open inventory (**i**), then **Ctrl+P** — overlay works; **Esc** leaves inventory open.
- [ ] During examine (**x**), **Ctrl+P** works.
- [ ] During rest (**5** animation), **Ctrl+P** works.
- [ ] During vore modal, **Ctrl+P** works.

## Capacity

- [ ] Generate many log lines (combat, movement); full log retains substantial history (up to 100 entries).

## Regression

- [ ] HUD log panel (PR1–PR4) unchanged when overlay is closed.
- [ ] **Ctrl+Q** quit confirm still works when overlay is closed.
- [ ] No debug stdout without `DEBUG_STDOUT=1` (PR0).