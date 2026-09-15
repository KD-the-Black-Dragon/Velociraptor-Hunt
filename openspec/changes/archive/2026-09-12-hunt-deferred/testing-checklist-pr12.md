# Manual testing — PR12 raptor mind

How to run: `python -m src.main`

## Tempo and hunter body

- [ ] Walk / quick / run / sneak feel different on the clock (run clearly faster, sneak slower)
- [ ] Four runs cover ground about twice as fast as four walks
- [ ] Quick feels like a sustainable jog between walk and run
- [ ] Fatigue: run stacks; quick holds; any mix of **walk / wait / sneak** recovers 1 per 3 turns; quick or run resets a partial streak
- [ ] Run + sidestep/back still drops to walk

## Vision and paddock

- [ ] Raptor is **much** faster than you (about 2×); she can close if you look away
- [ ] Spinning on the tiny center mud should **not** be a free win
- [ ] Rain stays in each phase longer (~40 AUT)
- [ ] Heavy rain: you see much less; she can see you without being seen
- [ ] When evading, she should not walk back into your last aimed cone
- [ ] Cones: light/medium you see **two** long-grass tiles deep, heavy only **one**
- [ ] Raptor in 3-deep grass can see the open while you cannot see it
- [ ] Light rain: you can see farther than the raptor tends to (you spot it first at long range more often)
- [ ] Medium / heavy: the raptor sees you first more often; heavy is marked
- [ ] Live paddock has **mud in the center** and a **ring of long-grass patches** with open ground between; outside is still jungle
- [ ] Training Mode arena is still the fixed west-open / east-grass map

## Mind (Training F2 **normal**, or a live hunt)

- [ ] It does **not** instantly charge from long range just because it has eyes-on
- [ ] Early: it watches from behind at range
- [ ] If you stare one way a long time: it sneaks, then **sprints** when close
- [ ] If you walk/turn a lot: it uses **long grass**
- [ ] If you stare **back** (not aiming): it keeps distance and **sidesteps** around
- [ ] If you **aim** at it or **shoot at it** (and you are farther than 4): it **breaks contact**, strafes, circles from another angle
- [ ] Rifle hipfire at long range / in heavy rain / at a moving raptor is usually a wasted round (0); shotgun/revolver feel as before
- [ ] Idle raptor stays near center; if you edge-camp it does not wander out to you; if you take center it contests; if it is winning it milks grass
- [ ] Heavy rain, no idea where you are: it **runs between** grass hides
- [ ] Inside **4 tiles** with eyes-on: it **runs at you** no matter what (aiming, staring, whatever)
- [ ] Walking/jogging nearby: it investigates sounds that fit; it does **not** chase every `?` after it just looked there
- [ ] A **gunshot** it cannot see: it treats a **region**, not a pinpoint (thought log says gunshot)
- [ ] Raptor definitely winning: stalks grass, does not sit in open mud
- [ ] Clock almost a hunter win: it heaves
- [ ] In sight, State can show Walking / Running / Sneaking (not always Walking)
- [ ] Lower-right log is **proportional text** with notices and raptor thoughts
- [ ] Training F2 gait override still sticks; **normal** uses this mind

## Regression

- [ ] Dart / belly / rain beds / Esc to menu still work
- [ ] Continue Hunt loads; raptor is not omniscient on load

## Pointer

`openspec/changes/hunt-deferred/tasks.md` (PR12).
