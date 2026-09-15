# Design: Velociraptor Hunt

Mechanics are **not** law except where listed in `DESIGN_CANON.md`.
Do not invent combat numbers, extra kit, extra animals, or extra endings.

---

## Fantasy

A **nameable hunter** in the **Muldoon role**, Jurassic Park–type jungle
paddock, rain, one velociraptor. Weapons are **tranq only**. The raptor’s
win is **swallow and digest**. One melee connect and the hunter is finished.
The clever-girl beat is earned by **fair senses** and **habit-reading**, not
by the AI peeking at the player’s tile.

---

## Pillars

1. **One hunt.** One paddock, one raptor, one sitting.
2. **Asymmetric lethality.** Tranq vs instant melee devour. No hunter HP sponge.
3. **Scarce, fair information.** Perfect maps; unknown positions; v1 clues are
   sight, mud prints, sound only.
4. **Facing is gameplay.** UnReal World tank controls (both hunter and raptor), 8 facings, aim-narrowed cone vs periphery.
5. **Rain is a mechanic.** Heavier rain: worse vision, muddier tracks, worse
   (or noisier) sound.
6. **A patient, profiling predator.** Circles aimed stares, counts habits,
   sits a winning clock — but **heaves** if the clock would otherwise be a
   certain loss (time-loss = tranq-loss).
7. **Loss has a belly.** Spectacle swallow → playable-but-helpless interior →
   spectacle digest. Not boxes all the way down.
8. **Anti-turtle.** Circular hard-border arena; clock + coarse ring-control.

---

## Non-goals (unless the designer expands later)

- Gladiavore career, downtime, patrons, ranked matches, Battle Sport
- KDVR multi-floor dungeon, ident, monster roster
- Pack-hunting / decoy-raptor (film beat is flavor, not the loop)
- Lethal hunter weapons
- Hunter hit points / chip-down brawl
- Scent tracking or extra fauna in v1
- In-world judges / commentary booth as a required fiction
- Open-world park, multiple facilities
- Expanding AV beyond engulfment and abdominal crushing
- A large modding program
- A struggle minigame that can reverse a landed melee

---

## Weapon roles

| Weapon | Role |
|--------|------|
| Bolt-action rifle | Sniper. **Aim/focus stance required** for a real shot. **Unaimed fire always grazes, even point-blank.** Seeing ≠ scoring. Aiming is a tell; raptor scrambles if it sees the stance. Slow to snap a frontal charge unless **already** aimed that way. |
| Shotgun | Butter zone is dangerously close. **Does not need aim stance.** Long shots graze and burn ammo. Unaimed at very short range can still hit hard. Ready + trigger vs a frontal charge should **usually** tranquilize. |
| Revolver | Mid-range snapshot. Faster to bring on target. Unaimed at very short range can still hit hard. Ready + trigger vs a frontal charge should **usually** tranquilize. |

Vision range sits **a little beyond** effective weapon range for most guns.
Limited ammo on all three.

**A** = aim/focus stance (longer, narrower **cone**, more damage). **A again**
= **deeper aim** (the truly powerful rifle shot). **D** = **stand down**
(hard drop of all aim). **Run** clears aim; walk/sneak do not.

**F** opens **targeting mode** (not a vision reticle). Cursor starts on the
raptor if visible. Player may **blind-fire**; the shot is a **linear
projectile** (DCSS vs an unseen tile). Confirm to fire; factors show
**only in this mode**.

---

## Shot math (no dice)

Same full situation → same damage, always. Factors (range, not aiming,
raptor running, hunter winded from a run, …) are **minuses**. Damage
**below zero** is a miss, even on a visible raptor.

Factors show **only after F**, in targeting mode — e.g. `range 8, no
aiming, raptor currently running perpendicular`. Hidden buffs/debuffs may
still apply. Then commit or abort.

---

## Movement and gait

Numpad, relative to facing (UnReal World):

| Numpad | Fallback (KDVR/Gladiavore cluster) | Action |
|--------|-------------------------------------|--------|
| 8 | Y / Up | Forward |
| 2 | N / Down | Back |
| 7 / 9 | T / Home · U / PageUp | Rotate 45° left / right |
| 4 / 6 | G / Left · J / Right | Rotate 90° left / right |
| Shift+4 / Shift+6 | Shift+G / Shift+Left · Shift+J / Shift+Right | Sidestep left / right |
| 5 | H / `.` | Wait (donor) |

Gaits: **run / walk / sneak** (noise). Free toggles (**0.0 AUT**): **R** run↔walk (or sneak→run), **S** sneak↔walk (or run→sneak). Always one key to any gait.

Run: worse vision until you slow down; sidestep or backpedal while running **drops to walk**. Sneak: any direction OK.

---

## AUT

Use Gladiavore’s AUT scheduler. **All** command costs live in data. **0.0
is legal.** v1 every command is **0.0 or 1.0** (gait toggles 0.0) so later
tunes can be 0.9 / 1.1. AUT is **always tenths** (`1.0`, never integer `1`).

---

## Loss sequence (hunter)

1. Raptor melee connects (front, side, or behind — including into a ready gun
   if the hunter does not shoot in time).
2. **Spectacle swallow** — narrative from that actual attack and angle.
3. **Playable belly** — hunter glyph boxed in by **eight red `#`**; world
   hidden; still or move waste the turn; no other in-world actions; help/log
   OK. Hunt already lost.
4. **Spectacle digest**.

Do not skip the belly for a stack of boxes. Do not let belly actions save the
hunter.

---

## Information, weather, arena

Both contestants know the terrain. They do **not** know each other’s tile
without a clue.

| Clue (v1) | Notes |
|-----------|--------|
| Eyes-on | Limited FOV; focus extends range, cuts periphery; rain shortens it; raptor may see better in rain |
| Footprints | Heavy rain → obvious mud tracks |
| Movement sound | Heavy rain hides real sounds and/or adds false alarms (rain/wind, not animals) |

No scent, no extra fauna in v1.

Rain **cycles** heavy ↔ easier, with **smooth audio** crossfades.

Procedural jungle paddock: trees, long grass, bushes, openings. **Large**,
**hard-bordered**, **as circular as possible**.

---

## Clock HUD (both sides)

Live, **three states only**: Raptor definitely winning / Close / Hunter
definitely winning. Abstract (not judges). Photo-finishes stay **Close**.
Raptor uses the same bucket: safer when definitely winning; hold center
rather than charge a rim camper when it is already winning the paddock.

If the clock is dying and the hunter is **definitely winning**, the raptor
**heaves** — time-over and being tranquilized are **equally bad**. It will
not hide to “survive.” Any nonzero chance of a melee connect beats a
certain clock loss (full-court shot with one second left).

---

## Raptor AI (PR9)

Same tank body and FOV as the hunter. Can look the wrong way. Perceives
only what it has sensed (eyes-on, last seen, prints in its cone, heard
hunter movement). Profiles: turn rate, sound-reaction, long stares,
edge-camping. Confidence from **counts of observations**. High confidence
→ exploit (edge-camp → hold center; long stare → flank). Does not charge
a facing, aimed hunter just because it has eyes-on (circles a staredown;
scrambles if it sees aim). Holds the center when **Raptor definitely
winning**. **Heaves** toward a clue (or the center) if even a perfect
center sit cannot stop a hunter time-win. Frontal all-in into a ready
shotgun/revolver is rare (`frontal_charge_chance` in `data/hunt_ai.json`)
unless the clock forces a heave.

When the raptor is in sight, HUD shows info, **especially facing**.

---

## Donor harvest (engineering, not fiction)

| Area | Why it might matter |
|------|---------------------|
| libtcod app, tileset, keys, menus | Window, 8-direction input, name entry |
| FOV / map / message log | Hunt is seeing and not seeing |
| KDVR/Gladiavore vore + belly | Loss sequence (adapt: **helpless** belly, not a winnable struggle) |
| Save / settings / user-data | After rebrand |
| Audio (new) | Rain layers — likely **not** in the donor |

Do **not** harvest career hub or duel-meter combat as the product loop.

---

## Win and menu

Tranq: `You fire your {weapon}!` then bright `The raptor is tranquilized!!`
while the **final paddock state stays on screen**. Any key → You win + scores.
No narrative. Then **main menu**. **Stats screen** off the menu:

- Total games played; times raptor tranquilized; times digested; wins by
  time over; losses by time over
- Per rifle / shotgun / revolver: shots fired; shots landed (any damage);
  perfect shots (theoretical 100% damage, including on an already-injured
  raptor); one-shot KOs (100% → 0% in one shot only)

(UI may say “One-shot KOs”; 0% is still **tranquilized**.)

---

## Open questions

Do not fill these in at implementation time.

1. Keys **inside** targeting mode to confirm vs abort (recommend: confirm
   **F** or **Enter**, abort **Esc** — wait for designer if that feels wrong).
2. Tuneables later (not design-law): ammo, HP, ranges, rain, clock, Close
   band, the **shot-factor table**, per-command AUT 0.0 vs 1.0 besides gait.

## Deferred (not current PR)

See `tasks.md` **Deferred**. Shipped PR3 still uses run-mode shorter cone as a stand-in.

1. Aim can sit **off-center** of a 45° tick; the hunter must **confirm the aim point**.
2. Vision/accuracy penalties come from a **running fatigue debuff**, not from merely being in run mode.
3. **Last-known raptor** mark after LOS loss (three cases: never seen / live / last known).
4. **Right-side panel** for score differential and raptor info (do not keep stuffing the bottom two lines).
5. **Visible projectile travel** across the map (animation). Shots already continue along the aim line to weapon max range.
6. **Practice dummy mode** — raptor on rails (run/sneak loops) so clues and stances can be playtested.
7. Centered **game-over modal**; sounds as one map symbol; mud-only footprints with per-print rain TTL; ring score always visible. (**Help** `?`/F1 and stripping the bottom key-legend shipped in PR10.)
8. **KDVR-exact belly** — match KDVR wall color; keep the camera on the swallow tile; raptor **walks a little** during belly and **takes the hunter with it** (KDVR prey-in-belly monsters stay put; this walk is hunt-only).
9. **Vore narratives as KDVR modal windows** (swallow / digest), not map overlay text alone.
10. **Raptor win = adjacency.** Reaching a tile next to the hunter finishes the hunt. No attack commit required. Recorded 2026-09-01; PR8/PR9 still swallow on the raptor’s turn at Chebyshev 1.
11. **Shift+numpad strafe with NumLock on.** Sidestep already works with NumLock off. Recorded 2026-09-01.

---

## PR slice plan

One authorized PR at a time. Each PR should be playable. Do **not** pick
up leftover Gladiavore match PRs.

Harvest: libtcod app, AUT scheduler, FOV, message log, name entry, settings,
vore/belly presentation. Do not keep career hub as New Game.

v1 AUT defaults (data): gait **0.0**; enter targeting / abort **0.0**;
everything else **1.0** until tuned.

| PR | Playable beat | In | Out |
|----|---------------|----|-----|
| **1** Identity + hunt shell | Menu says Velociraptor Hunt; New Hunt → name → weapon → stub paddock | Product strings, user-data dir name, menu (New Hunt / Stats stub / Options / Quit), name, weapon select, hunt App state replacing career hub | Procgen quality, raptor, guns that work |
| **2** Paddock + tank + AUT | Walk a circular jungle with facing and a vision cone | Circular hard border, basic procgen (trees, grass, bushes, openings), tank keys, cone FOV, wait, hunt AUT JSON | Raptor, rain, guns |
| **3** Gait + aim stances | Run/sneak/aim change noise, cone, and vision | R/S gait; run vision + no run sidestep/back; A / A / D; run clears aim | Fire, raptor |
| **4** Raptor body | One raptor on the map; HUD facing when seen | Same tank/FOV as hunter; fair eyes-on; stub AI (no tile cheat); in-sight facing | Profiling, shots, melee finish |
| **5** Fire + tranq win | You can put the raptor down | F targeting, auto-cursor if seen, blind linear shot, factors, confirm, ammo, deterministic damage stub, 0 HP = tranq bask → win modal | Clock, rain, loss vore |
| **6** Rain + clues | Weather and mud/sound matter | Rain cycle; vision/sound tradeoff; footprints; false rain/wind sounds; audio fade if cheap else stub | Full AI |
| **7** Clock + ring | Time and center-control can end the hunt | Clock; 3-state HUD both sides; time-over win/loss | Heave AI |
| **8** Loss vore | One melee finishes you | Angle-based swallow spectacle; KDVR eight `#` belly; digest spectacle | Deep AI |
| **9** Raptor mind | It feels like the clever girl | Profile counts; scramble vs aim; hold center when winning; clock heave; frontal-charge caution | Content pack expansion |
| **10** Stats + polish | Menu stats persist | Locked tally fields; leftover HUD/help; `openspec/specs/` for landed behavior | Tune pass as its own later work |

**Playable milestones:** PR2 walk; PR4 stalk; PR5 can win; PR8 can lose; PR9 is the game.

---

## Resolved decisions

Canonical detail lives in `DESIGN_CANON.md`. Summary:

| Decision | Resolution | Date |
|----------|------------|------|
| Product / folder | Velociraptor Hunt; Gladiavore copy for harvest | 2026-08-31 |
| Scope | One hunt, 7DRL, one raptor | 2026-08-31 |
| PC | Nameable hunter, Muldoon role | 2026-08-31 |
| Stakes | Tranq only vs swallow/digest; no hunter HP; one melee finishes | 2026-08-31 |
| Loss UX | Spectacle swallow → KDVR eight `#` belly (helpless) → spectacle digest | 2026-08-31 |
| Win UX | Fire line → bright tranquilized line on frozen map → win modal/scores; no narrative | 2026-08-31 |
| Session | Results → main menu; running stats as a menu screen | 2026-08-31 |
| Kit | Rifle / shotgun / revolver; limited ammo; butter zones including revolver snapshot | 2026-08-31 |
| Body | URW numpad tank + TYUGHJBNM/arrows fallback; raptor same FOV; R/S gait; A / A / D aim; F targeting | 2026-08-31 |
| Shots | Deterministic damage; miss = below zero; loose factor readout before commit | 2026-08-31 |
| AUT | Data-driven tenths; v1 costs 0.0 or 1.0 | 2026-08-31 |
| Stats | Per difficulty (Easier–Nightmare); games, abandoned, tranq, digested, time wins/losses; per-gun fired/landed/perfect/one-shot | 2026-09-01 |
| Autosave | KDVR rotating slot; Continue Hunt; New Hunt abandon prompt; Ctrl+Q and window close write a save | 2026-09-01 |
| Space | Procgen jungle, circular hard border, rain cycles + audio | 2026-08-31 |
| Info | Fair senses; perfect maps; v1 = eyes, mud, sound; no scent, no fauna | 2026-08-31 |
| Clock | Abstract; 3-state HUD both sides; raptor safer when winning; **heaves** if certain time-loss | 2026-08-31 |
| AI | Patient, profiles habits, same tank FOV, can look wrong way, false-noise distractible | 2026-08-31 |
| Front | Allowed even into a ready gun; SG/revolver usually punish if they shoot; rifle needs pre-aim | 2026-08-31 |
| Implementation | Not authorized | 2026-08-31 |
