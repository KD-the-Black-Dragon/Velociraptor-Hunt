# Manual testing checklist — PR8 (grapple / vore v1)

## How to run

```bash
python -m src.main
```

## Grab & grapple war

- [ ] In a **red** match, get adjacent to a foe while low HP or downed → eventually **seized** (log: “seizes you”)
- [ ] HUD shows **GRAPPLE** + **Grapple HP** while held
- [ ] Footer: `1 Break away | 2 Counter | . brace`
- [ ] **1** sometimes frees you (“wrench free”); sometimes fails (“grip holds”)
- [ ] **2** damages the predator; occasionally also frees you
- [ ] Predator **crush** lowers stamina + grapple HP; **secure** lowers grapple HP
- [ ] When grapple HP hits **0**, **SWALLOWING** phases begin (slow AUT, multi-phase)

## Scene isolation (critical fairness)

- [ ] While **held**, other enemies do **not** open reaction modals / pile free attacks on you
- [ ] Grapple UI is not stacked with **INCOMING!** reaction choices
- [ ] Only the grappling foe’s crush/secure/swallow/digest pressure hits you as prey
- [ ] With allies out: they prefer hitting the **predator** (rescue), not stabbing the grapple mess blindly
- [ ] Multi-rat fight: while one holds you, others idle/seek free targets rather than free damage

## Red 0-stamina magnet

- [ ] On red, reach **0 HP / DOWN** and get grabbed → swallow can start **without** a full grapple war

## Green rules

- [ ] Green match: grab still possible for control
- [ ] After swallow phases complete on **green**, foe **must let go** (exhibition message) — **no** permanent digest
- [ ] Green loss recap still “hauled out” / appearance fee — not career end

## Engulfed & digest (red)

- [ ] After full swallow on **red**, HUD **ENGULFED**; footer thrash
- [ ] `.` or move while engulfed → “thrash uselessly” (input still works)
- [ ] Digest strikes tick in the log; after enough strikes → **Digested** recap + flaunt line
- [ ] Enter after Digested recap → **main menu**; career save **gone** (New Game, not Continue)

## Ally assist / regurg

- [ ] With an ally out: while you are held, ally/PC hits on the predator can force **release** after enough damage
- [ ] Critically hurting the predator mid-grapple can force **regurgitate / release**

## Beast flag (data)

- [ ] Optional: hire market — wolf/rat hires store `vore_capable` (future ally predators); kobold default false
- [ ] Enemies remain always vore-capable; PC never initiates grab

## Still OK (regression)

- [ ] Log font for non-map HUD/log; map tiles still tile font
- [ ] Reaction modal, Talk, abilities, Second Wind, injuries still work when **not** grappled
- [ ] Normal win/loss still returns to **downtime** (not menu), career saved

## JSON tune (optional)

- [ ] Tweak `data/match_vore.json` (e.g. `grab_chance_if_downed`, `swallow_phase_aut`) and relaunch — behavior changes without code edits
