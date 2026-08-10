# Manual testing — grapple-swallow-modals PR1–PR2

## How to run

```bash
python -m src.main
```

## Grapple modal (stub wrestling)

- [ ] Enter a **red** match (or force a grab via play until grabbed)
- [ ] When held in **grapple** (not yet swallowing):
  - [ ] Red **low-right** modal appears (same family as INCOMING)
  - [ ] Headline is **`{enemy name} grapples you!`** (not “GRAPPLE — you are held!”)
  - [ ] Status column does **not** duplicate the full grapple control block
  - [ ] `1` break away / `2` counter / `.` brace still work (stub odds OK)
  - [ ] Map + meters + action log remain visible

## Swallow modal + odds

- [ ] Reach **swallowing** (grapple HP to 0, or red downed grab)
- [ ] Large **interface-blocking** modal (arena hazed / hard to read surroundings)
- [ ] Narrative line present; phase counter visible
- [ ] Only **`1` Struggle** and **`2` Conserve strength** advance the crisis (movement does nothing)
- [ ] Struggle almost always fails (miracle free is rare — do not expect frequent escapes)
- [ ] Conserve logs a save-strength line; counter may show strength conserved
- [ ] Green match still releases before lethal digest after swallow completes

## Conserve → engulfed

- [ ] On red: conserve 1–2 times during swallow, then finish phases to **engulfed**
- [ ] Digestion takes **longer** than without conserving (extra strikes)
- [ ] Engulfed thrash (`.` / move) still works; career can still end by digest

## Regression

- [ ] Incoming attack modal still works when not grappled
- [ ] Ally bump no-op / HUD layout from match-hud-ux still OK
- [ ] Win/loss/recap paths still work without grapple
