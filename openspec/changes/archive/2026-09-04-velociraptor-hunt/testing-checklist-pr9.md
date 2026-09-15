# Manual testing — PR9 raptor mind

How to run: `python -m src.main`

## Happy path

- [ ] The raptor does **not** sprint at you the instant it has eyes-on
- [ ] If you **stare at it**, it **circles** rather than walking down the barrel
- [ ] If it **sees you aiming** (A / deep A), it **scrambles** off the line
- [ ] When the footer says **Raptor definitely winning**, it **hangs around the center** instead of suiciding into a rim camp
- [ ] If you are **Hunter definitely winning** and the clock is almost gone, it **heaves** — a foolish-looking all-in is intended
- [ ] A long period of staring one way, then it tries to **come in from behind**
- [ ] Shotgun / revolver ready and facing it: a frontal rush is **rare**, not the default
- [ ] It still only acts on **sight / prints / sound** — it can look the wrong way

## Edges

- [ ] Adjacent melee swallow from PR8 still happens if it **does** reach you
- [ ] Tranq win, time-over, rain/clues, tank/aim/fire still work
- [ ] False noises can still pull its facing when it has no better clue

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR9).
