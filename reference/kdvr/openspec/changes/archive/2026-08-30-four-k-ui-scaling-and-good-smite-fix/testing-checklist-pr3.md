# Manual testing — PR3 (4K UI scaling) + cleric spawn restore

Run: `python -m src.main`

## Cleric spawn restore

- [ ] Confirm stock intent: sheep cleric is **not** expected on depth 1 anymore (`min_depth` 12–14 again)

## 4K UI scaling

- [ ] Options shows **4K UI scaling: [Off] ► On** (default Off)
- [ ] Turn **On**: glyphs and message log text get larger; layout still usable; setting survives restart
- [ ] With 4K **On**, Options (and other menus) stay **centered** — not stuck in the upper-left; window may grow to the scaled minimum if it was smaller
- [ ] Toggle 4K **on the Options screen** itself: options stay centered (no top-left jump)
- [ ] **Name entry**, depth-jump entry, and Ctrl+B entity entry use the same 4K scale and stay centered
- [ ] Turn **Off**: returns to prior look; menus remain centered

- [ ] Fresh / old `settings.json` without the key behaves as **Off**
- [ ] Fullscreen + UI Layout still work with 4K On or Off
- [ ] Resize window with 4K On: map flexes; window does not shrink below a raised pixel floor
- [ ] **F10** toggles 4K from main menu, Options, and during play; Options row reflects the new state after toggle; survives restart
- [ ] Help (F1) lists F10

## New Game / Load with 4K already On

- [ ] Set 4K On, quit to menu (or restart with it saved On)
- [ ] **Maximized or fullscreen** → New Game: map/UI fill the window correctly (not a tiny square); no need to press F10
- [ ] Same for **Load Game** if a save exists
- [ ] Free-floating window still fine

## Regression

- [ ] Main menu / Options / New Game still navigable
- [ ] Good Smite still does not hit the player (PR1)
