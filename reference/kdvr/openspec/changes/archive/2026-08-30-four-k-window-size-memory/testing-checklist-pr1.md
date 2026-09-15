# Manual testing — PR1 (4K window size memory)

How to run: `python -m src.main`

## Happy path

- [ ] Windowed, 4K **Off**, note size/position
- [ ] Enable **4K UI scaling** (Options or F10): window grows (~2× first time); glyphs scale up
- [ ] Disable 4K: window **returns to the previous normal size** (not stuck giant)
- [ ] Enable 4K again: returns to the **remembered 4K size** (not doubled again from current)
- [ ] With 4K On, resize to a custom size; toggle Off then On: custom 4K size restored; normal size unchanged
- [ ] With 4K Off, resize normal; toggle On then Off: new normal size restored; 4K size unchanged

## Position clamp

- [ ] If you can place the window partly off-screen left/above, toggle 4K: `x` not left of 0, `y` not above ~30 — title bar reachable

## Modes

- [ ] Maximized + toggle 4K: stays maximized; layout/glyphs still update
- [ ] Fullscreen + toggle 4K: stays fullscreen; no weird size fight
- [ ] Exit fullscreen to windowed with a negative/off-screen saved position: `x≥0`, `y≥~30` (title bar reachable)
- [ ] Exit fullscreen to maximized: stays maximized (no forced position move)
- [ ] Quit/relaunch with 4K On: opens at saved 4K size
- [ ] Quit/relaunch with 4K Off: opens at saved normal size

## Regression

- [ ] UI Layout / Fullscreen rows still work
- [ ] Menus stay centered under 4K On/Off
- [ ] New Game / Load still respect 4K tile scale
