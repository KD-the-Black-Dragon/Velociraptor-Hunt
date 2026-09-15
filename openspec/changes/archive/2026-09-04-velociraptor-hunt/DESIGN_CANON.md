# Velociraptor Hunt — design canon

Locked designer decisions. Read after compact. **Do not re-ask** these.
Mechanics not listed here are **open** — ask; do not invent numbers, extra
weapons, extra fauna, or extra win conditions.

Gladiavore `openspec/changes/gladiavore-foundation/DESIGN_CANON.md` in this
copy is **not** product canon.

---

## Identity

| # | Decision | Locked |
|---|----------|--------|
| 1 | Product name is **Velociraptor Hunt**. | 2026-08-31 |
| 2 | This folder is a **copy of Gladiavore** (KDVR spinoff) used as a harvest base. Gladiavore and KDVR originals live in **other folders** and must not be edited from hunt work. | 2026-08-31 |
| 3 | Do **not** continue Gladiavore career/hub/match or KDVR dungeon crawl as the product loop. | 2026-08-31 |
| 4 | Scope is **one hunt**, 7DRL-shaped, not a long campaign or many floors. | 2026-08-31 |
| 5 | There is **one velociraptor**, not a pack. (The film decoy-pack beat is not the product.) | 2026-08-31 |
| 6 | The player character is a **nameable hunter in the Muldoon role** (same job and fiction; not a celebrity lock-in, not a roster/career). | 2026-08-31 |

---

## Fantasy and stakes

| # | Decision | Locked |
|---|----------|--------|
| 7 | Setting is a **Jurassic Park–type** outdoor jungle paddock. Reference beat: Muldoon / “clever girl.” | 2026-08-31 |
| 8 | **Asymmetric goals.** The hunter’s weapons are **tranquilizing only**. A successful hunt **never kills** the raptor; it is **tranquilized**. The raptor has **no such constraint**: its goal is to **swallow the player whole and digest them**. | 2026-08-31 |
| 9 | AV stays **clean scope**: engulfment and abdominal crushing, unless the designer later expands it. | 2026-08-31 |
| 10 | **The hunter has no hit points.** If the raptor **executes one melee attack**, the hunter is **finished**. The contest is firearms vs an instant melee takedown. | 2026-08-31 |
| 11 | **Raptor has HP** so grazes matter (e.g. shotgun at long range, a difficult rifle shot). The raptor **can** be one-shot tranquilized, but only if the shot falls in that weapon’s **butter zone**. | 2026-08-31 |
| 12 | Loss sequence: **spectacle swallow** (narrative depends on the **actual final attack** and **front / side / behind**) → **playable belly** → **spectacle digest**. No struggle minigame; the hunt is already lost. Belly is **exactly KDVR-shaped**: hunter glyph enclosed on **all eight sides** by **red `#`**; **the rest of the world is hidden**; still or move **spend the turn and do nothing**; **no other in-world actions**; meta (help, action log) is OK. The belly exists so the player can **be stuck inside** before digestion — not boxes all the way down. | 2026-08-31 |
| 13 | Terminology in code, logs, specs, and agent prose: hunter success is **tranquilized**; melee connect is **finished** then **swallowed** / **digested**. Never kill / die / death. | 2026-08-31 |

---

## Loadout

| # | Decision | Locked |
|---|----------|--------|
| 14 | Hunt starts with **weapon select**. Shipped trio: **bolt-action rifle**, **shotgun**, **revolver**. | 2026-08-31 |
| 15 | **Limited ammo.** Wasting shots (e.g. shotgun grazing at max range every time the raptor is spotted) must be able to **starve the hunter**. | 2026-08-31 |
| 16 | **Rifle** is the sniper weapon. It **must be in the aim/focus stance** for a real shot — that slowness is its downside. **Unaimed / quick-fire rifle always grazes, even point-blank.** Seeing the raptor at distance must often **not** be enough to score. Rifle hunters have to **confuse** the raptor, not win a staring contest. | 2026-08-31 |
| 17 | **Shotgun** butter zone is **dangerously close**. It does **not** need the aim stance — it needs range. Long-range shotgun hits are grazes. **Unaimed shotgun at very short range can still be highly damaging.** | 2026-08-31 |
| 18 | **Revolver** butter zone is a **mid-range snapshot**: closer than the rifle, farther than the shotgun’s suicide-close. Faster to bring on target. Weaker one-shot unless fairly close. **Unaimed revolver at very short range can still be highly damaging.** | 2026-08-31 |
| 19 | Hunter **vision range is a little higher than effective weapon range** on most weapons. You can often see a target you cannot yet put down. | 2026-08-31 |
| 20 | If the raptor **sees the hunter aiming**, it **scrambles**. Aiming is a visible, exploitable tell. | 2026-08-31 |

---

## Body, facing, vision

| # | Decision | Locked |
|---|----------|--------|
| 21 | **Tank controls** and **specific facing**, **same as UnReal World** for basic movement. **Numpad is the main mode.** | 2026-08-31 |
| 22 | **Eight facings**: cardinal + ordinal. | 2026-08-31 |
| 23 | **A** is **aim/focus stance**, not a tile reticle. It **lengthens but narrows** the vision cone and makes shots **more damaging**. It does nothing for a raptor **outside that cone**. This is a **facing / cone / stance** game. (Earlier “aim at a specific tile” is **retracted**.) | 2026-08-31 |
| 24 | View range is **limited in general**. Rain and foliage make it worse. **Run** also **cuts vision until the hunter slows down**. | 2026-08-31 |
| 54 | Numpad (relative to current facing): **8** forward, **2** back, **7** rotate 45° left, **9** rotate 45° right, **4** rotate 90° left, **6** rotate 90° right, **Shift+4** sidestep left, **Shift+6** sidestep right. | 2026-08-31 |
| 54b | Non-numpad fallback is the **same cluster as KDVR/Gladiavore** (`TYUGHJBNM`, plus arrows), mapped to the **same tank commands** as the matching numpad keys: **Y**/Up = 8, **N**/Down = 2, **T**/Home = 7, **U**/PageUp = 9, **G**/Left = 4, **J**/Right = 6, **Shift+G** / **Shift+Left** sidestep left, **Shift+J** / **Shift+Right** sidestep right. **H** / numpad **5** / **`.`** wait (donor). **B** / **M** / numpad **1**/**3** have no tank command unless later specified. | 2026-08-31 |
| 55 | **The raptor uses the same body rules**: tank facing, eight directions, and a **field of view**. It can be looking the **wrong way**. It tries hard to keep track of the hunter but can only **guess** from clues, so it may guess wrong or get **distracted by false noises**. | 2026-08-31 |

---

## Arena, weather, terrain

| # | Decision | Locked |
|---|----------|--------|
| 25 | **Outdoor jungle**: trees, long grass, bushes, and **some open areas**. | 2026-08-31 |
| 26 | **Procedural generation is intended** for the paddock. (A handmade map is only a scaffold if needed to test systems.) | 2026-08-31 |
| 27 | Arena is **fairly large** but has **hard borders**. Neither side can leave. | 2026-08-31 |
| 28 | Shape is **as circular as possible** so edge-camping still leaves a wide arc you cannot watch. | 2026-08-31 |
| 29 | The hunt is always in **rain**. Rain **periodically gets heavier or eases**. | 2026-08-31 |
| 30 | **Rain audio** is a backdrop that **fades smoothly** between heaviness levels. | 2026-08-31 |
| 31 | Rain strength is a **tradeoff**, not just mood: heavier rain **worsens vision** and **hides real movement sounds** (and/or produces **more false-alarm sounds**). | 2026-08-31 |
| 32 | Heavy rain makes **footprints obvious** (mud). | 2026-08-31 |

---

## Clock and ring control (anti-turtle)

| # | Decision | Locked |
|---|----------|--------|
| 33 | A hunt **clock** and **ring-control score** exist so camping the rim is not a free win. More points for **staying closer to the center**. | 2026-08-31 |
| 34 | Clock + ring-control are **abstract game rules**, not in-world judges. | 2026-08-31 |
| 35 | The HUD is **live but coarse**: three states only — **Raptor definitely winning** / **Close** / **Hunter definitely winning**. A photo-finish on points stays in **Close** (winning on time by a hair is **risky**). Losing the paddock by a mile is **not** a surprise. | 2026-08-31 |
| 36 | **The raptor sees the same three states.** If the state is **Raptor definitely winning**, its **overall risk-taking goes down**. If it is ahead on control, it may **hold the center and win on time** rather than charge an edge camper. | 2026-08-31 |
| 64 | The raptor has a **strong dislike for losing on the clock**. Time-over loss and being tranquilized are **equally bad** — it does **not** think “at least I survive.” If doing nothing means a **definite** time-loss and going in has a **nonzero** chance, it goes in: the basketball **full-court heave** with one second left. Foolish-looking is fine. | 2026-08-31 |

---

## Information model (both sides play fair)

The raptor is cunning, not omniscient.

| # | Decision | Locked |
|---|----------|--------|
| 37 | Both sides may have **perfect map knowledge**. Vision is **fog of war on the opponent**, not “I never knew that grass was there.” The hunter is **familiar with this stretch of jungle**. The raptor is too. | 2026-08-31 |
| 38 | Neither side knows where the other **is**, except through **clues**. **v1 clues:** **eyes-on**, **footprints**, **movement sounds**. | 2026-08-31 |
| 39 | **v1 ships no scent** and **no other fauna**. False alarms come from **rain / wind**, not animals. Empty paddock: hunter and raptor only. | 2026-08-31 |
| 40 | The raptor **plays fair**: it may have **better vision or other abilities**, but it **only acts on what it actually perceives**. No cheating player coordinates. | 2026-08-31 |
| 41 | “Dirty tricks” means **tactics** (cover, circling, waiting, exploiting habits, using rain) — **not** breaking the information model. | 2026-08-31 |

---

## Raptor mind

| # | Decision | Locked |
|---|----------|--------|
| 42 | Default posture: use **superior rain-vision** to **stay out of weapon danger** until it sees a **vulnerability**. Seeing the hunter is **not** by itself a reason to charge. | 2026-08-31 |
| 43 | If the hunter is **staring back**, the raptor **circles** rather than eating an aimed shot. | 2026-08-31 |
| 44 | The raptor **profiles the player**: how often they **turn**, how they **react to sounds**, whether they **stare one way for a long time**, whether they **edge-camp**. It **counts turns / incidences** until it has **high confidence**, then it **moves in to exploit** that habit. | 2026-08-31 |
| 45 | Edge-camping, once recognized, makes the raptor **trend toward winning on clock and points**, not a suicide rush — unless the clock **forces** a heave (#64). | 2026-08-31 |

---

## Frontal showdown

| # | Decision | Locked |
|---|----------|--------|
| 46 | The raptor **may finish from the front**, even into a **ready gun**. That charge is usually a **bad decision**. | 2026-08-31 |
| 47 | **Shotgun** or **revolver** hunter, weapon ready and **trigger pulled**, should **usually win** that setup (point-blank / snapshot butter). | 2026-08-31 |
| 48 | **Rifle** takes longer to set up. If the hunter is **not already aiming that way**, they are **too slow**. If they **are** pre-aimed and shoot, they can still punish. | 2026-08-31 |
| 49 | If the hunter **does not pull the trigger** and misses the window, the raptor **can finish from the front**. | 2026-08-31 |

---

## Win presentation and session loop

| # | Decision | Locked |
|---|----------|--------|
| 51 | Tranq success is **not a narrative scene**. Beat: log/line **You fire your {weapon}!** then **The raptor is tranquilized!!** in a **bright** font (white or green). The player **basks** a moment on the **final map layout and game state**. **Any key** → **You win!** modal and **score tabulation**. Then done. | 2026-08-31 |
| 52 | After results, return to the **main menu** (no one-button rematch into a new hunt). | 2026-08-31 |
| 53 | A **grand running statistics tally** exists as **its own screen from the main menu**. Fields are locked in #62–63. | 2026-08-31 |

---

## Gait (run / walk / sneak)

| # | Decision | Locked |
|---|----------|--------|
| 56 | Three gaits: **run**, **walk** (normal), **sneak**. They change how likely the hunter is to **make noise**. | 2026-08-31 |
| 57 | **Run** extra downside: **reduced vision** until the hunter **slows down**. Cannot **run + sidestep** or **run + backpedal** — those inputs **automatically slow to walk**. | 2026-08-31 |
| 58 | **Sneak** is legal in **any** direction (including sidestep and back). | 2026-08-31 |
| 59 | Gait is a **free toggle** (does not spend the hunt action by itself). **R** = run, or **walk if already running**. **S** = sneak, or **walk if already sneaking**. **Always one key to any gait** (R from sneak goes to run; S from run goes to sneak). | 2026-08-31 |

---

## Aim and fire

| # | Decision | Locked |
|---|----------|--------|
| 60 | **A** is **aim/focus stance** (longer, narrower cone + better damage). **F** opens **targeting mode**, then a **confirm** actually fires. **F is not “hip-fire” as a concept.** | 2026-08-31 |
| 70 | **F-then-confirm:** Press **F** → targeting mode. Cursor is **automatically on the raptor if it is visible**. The player may **blind-fire** (DCSS shooting an unseen tile). The projectile travels **linearly**; if that line **happens to hit** the raptor, the shot is valid even if the raptor was not seen. | 2026-08-31 |
| 71 | Shot **factors appear only after F** (in targeting mode). The hunter decides “I might want to take a shot here,” **then** sees the loose factors, **then** commits or aborts. | 2026-08-31 |
| 72 | **A** once = aim/focus. **A again** = **deeper aim** (how you get a **truly powerful rifle shot**). Two aim depths; no third stack. | 2026-08-31 |
| 73 | **D** = **Stand down**: **hard** drop of aiming (all aim depth → none in one press). | 2026-08-31 |
| 74 | **Running automatically interrupts aiming.** **Walking** and **sneaking do not.** | 2026-08-31 |

---

## In-sight HUD

| # | Decision | Locked |
|---|----------|--------|
| 61 | While the raptor is **in sight**, the HUD gives information about it, **especially its current facing**. | 2026-08-31 |

---

## Career stats (menu screen)

UI may keep the designer’s labels (including **One-shot KOs**). In prose and code comments, 0% raptor is still **tranquilized**, never killed.

| # | Decision | Locked |
|---|----------|--------|
| 62 | Tally these, persistently, on the stats screen: **Total games played**; **Games abandoned**; **Times raptor tranquilized**; **Times digested**; **Wins by time over**; **Losses by time over**. | 2026-09-01 |
| 63 | Per weapon (**rifle**, **shotgun**, **revolver**): **Shots fired**; **Shots landed** (any damage); **Perfect shots** (a shot that would have dealt **100%** damage — **including** when the raptor was already injured); **One-shot KOs** (only shots that took the raptor from **100% to 0%** in one shot). | 2026-08-31 |
| 75 | Stats are **per difficulty** (Easier / Normal / Hard / Nightmare). Left/Right on the Stats screen cycles boards. A hunt records against the difficulty selected in Options when that hunt started. | 2026-09-01 |
| 76 | In-progress hunts **autosave** with the KDVR rotating autosave slot. Ctrl+Q and closing the window both write a save. **Continue Hunt** resumes it. **New Hunt** with a save prompts to **abandon**; Yes increments total games and games abandoned for that hunt’s difficulty. | 2026-09-01 |

---

## Shot resolution (deterministic)

| # | Decision | Locked |
|---|----------|--------|
| 65 | Damage is **purely algorithmic**. The **same situation** (including buffs/debuffs the player may not see) **always** yields the **same** result. **No random accuracy roll.** | 2026-08-31 |
| 66 | A **visible** raptor can still be a **miss** when stacked minuses drive damage **below zero** (out of effective range, raptor mid-run, hunter still recovering from running / out of breath / shaking hands, etc.) — **not** “the dice failed.” | 2026-08-31 |
| 67 | Each bad factor is a **minus to damage**. Factors are shown **loosely**, **not** the formula (e.g. “range 8, no aiming, raptor currently running perpendicular”), **only in targeting mode** (#71). The readout may be **incomplete**; hidden modifiers still apply. | 2026-08-31 |

---

## Time (AUT)

Harvest Gladiavore’s AUT scheduler (action cooldown / who acts next). Hunt-specific costs are new data.

| # | Decision | Locked |
|---|----------|--------|
| 68 | **Every command** has a **data-driven AUT cost**. **0.0 is legal.** v1: every command is **0.0 or 1.0** so costs are easy to retune later (0.9, 1.1, …). Gait toggles stay **0.0** (already free). | 2026-08-31 |
| 69 | AUT is **always tenths** — decimals to **one place**, **never integers** in data or displays (`1.0` not `1`). | 2026-08-31 |

---

## Process

| # | Decision | Locked |
|---|----------|--------|
| 50 | OpenSpec + PR implementation gate still apply. No hunt code until the designer authorizes a named PR. | 2026-08-31 |

---

## Not locked (do not invent)

See `design.md` **Open questions**. Remaining gaps:

- Confirm / abort keys **inside** targeting mode (second F vs Enter vs both; Esc to abort is the usual donor pattern — not locked)
- Exact ammo, HP, ranges, rain timings, clock length, the numeric gap that counts as **Close** vs **definitely**, and the **shot-factor table** (tune later; not design-law)
- Live specs under `openspec/specs/` when PRs land
