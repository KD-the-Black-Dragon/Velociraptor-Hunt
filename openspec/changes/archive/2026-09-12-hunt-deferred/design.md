# Design: Hunt deferred follow-through

Implementation detail for `openspec/changes/hunt-deferred/`. Behavioral law
belongs in `openspec/specs/hunt/spec.md` as PRs land. Locked intent and open
questions: `DESIGN_CANON.md` in this folder.

Do **not** invent numbers, glyphs, or raptor tricks listed as open questions.

---

## Inventory (named deferred items)

Help / strip key-legend already shipped (foundation PR10). **Relative score
always on-screen** is not its own PR: the footer already shows the 3-state
ring; **PR2** moves it to the right panel (D4 / D11).

Everything else is in `tasks.md`.

---

## Why not the mention order

The archive list is a playtest diary. Dependencies:

```text
NumLock strafe          (input only)
        |
        v
Right-side panel        (HUD home; absorbs relative-score)
        |
        v
Adjacency win           (loss RULE — before spectacle)
        |
        +--> Clue glyphs (last-known + one sound symbol)
        |         |
        |         v
        |    Mud prints (TTL / mud-not-grass)     --+
        |                                           |
        +--> Run fatigue (vision/accuracy)          |
        |         |                                 |
        |         v                                 |
        |    Aim off-center (Q1–Q3)                 |
        |         |                                 |
        |         v                                 |
        |    Visible projectile                     |
        |                                           |
        +-------------------+-----------------------+
                            v
                 Loss spectacle (belly + vore modals + game-over)
                            |
                            v
                 Practice dummy (verifies clues / aim / rain)
                            |
              +-------------+-------------+
              v                           v
         Rain wav (assets)         Raptor mind (Q17, last)
```

**Do not** polish belly/modals while the raptor still “attacks on its turn.”
**Do not** animate the dart before aim heading is the real fire line.
**Do not** dissect AI before adjacency and the new clue language exist.

---

## Groups

### A — Tank input

**PR1 Sidestep.** **Ctrl+4/6** only (also Ctrl+G / Ctrl+J / Ctrl+arrows).
Shift does not sidestep — Windows NumLock-on makes Shift+numpad
indistinguishable from unshifted rotate. Unshifted 4/6 always rotate.
Keep keypad scancodes so NumLock-on digit keysyms still turn/strafe
with Ctrl.

### B — HUD home

**PR2 Right-side panel.** Hunt render today uses the full console width and
two footer lines (`src/hunt_session.py` `render_hunt`). Leave a right column
for: 3-state ring, clock, in-sight raptor facing (and later last-known /
coarse readout per Q18). Bottom line stays notices that are **not** sound
prose (shot result, targeting factors until they also move — targeting
factors stay in targeting mode per archive #71; they may sit in the panel
or keep the footer for F-mode only — default: **panel**, footer only for
transient notices).

Do not harvest the Gladiavore/KDVR dungeon **sidebar** as a monster roster.
This is a hunt column, not NPC chrome.

### C — Loss rule (small, early)

**PR3 Adjacency.** Q9 resolved (D14): instant raptor win only if
**Chebyshev 1 and** the hunter is in the **raptor’s own FOV** (existing
cone + LOS, `HuntRaptor.sees`). Adjacent but behind the raptor (or
otherwise not in its cone) is **safe**. No melee-commit action.
Occupying the raptor’s tile stays illegal.

Check after hunter movement, raptor movement, **raptor facing change**
(turning onto an already-adjacent hunter counts), and dummy teleport.
Today swallow waits until the **next** raptor turn if the raptor steps
adjacent during `raptor_act`; that delay goes away **when it can see**.

Until PR9, “instant win” is `begin_swallow` (then belly / digest). When
PR9 lands, that same trigger opens the vore modal.

Consequence: a hunter **behind** an adjacent raptor can still fire
(shotgun/revolver butter at range 1). Walking onto range 1 **in front of
its eyes** finishes the hunt immediately.

Swallow **angle** (front / side / behind) still uses the actual relative
facing at finish (archive #12). Live hunt and practice dummy share D14.

### D — Clue language

**PR4 Map tells.** Last-known mark (D3) + sounds as **one** map symbol and
**no** footer “Movement N / Rain in the canopy / Wind from the SE” (D9).
Today: live `r`, prints `"`, sound `!` vs `?`, plus `session.notice` strings
in `src/messages.py` (`hunt_sound_move`, `hunt_false_rain`, `hunt_false_wind`).

Design the glyph language once:

| Thing | Glyph (Q6/Q7 locked) |
|-------|-------------------------------------|
| Live raptor in LOS | `r` (current) |
| Last-known | dim `r` on that tile; gone when seen again, never seen, or FOV on an empty last-known tile |
| Sound (real or false) | one `?` — hunter cannot tell rain from raptor by glyph |
| Print | `"` on mud (PR5) |

Last-known is **player FoW**, not a raptor cheat. Raptor mind already has
its own `last_seen_*` for fair AI; do not couple the player mark to that
beyond “the hunter saw the raptor on this tile.”

**PR5 Mud prints.** Always leave a print on a **mud** tile when hunter or
raptor steps there. Store `rain_level` (or TTL computed at place time) on
`MudPrint`; expire per print, not by the **current** rain’s global TTL.
Heavier rain at stamp time → longer life. Grass (and bush) do not take
prints. Recommended Q8 default: **open** tiles are mud (bare earth);
`HuntTerrain.GRASS` / `BUSH` do not. No new biome unless the designer
asks. Persist new print fields in the hunt snapshot (additive; default TTL
on old saves).

Raptor AI already inspects prints in its cone (`src/hunt_ai.py`). Keep
that; longer-lived mud prints are a real clue upgrade.

### E — Hunter vision and fire

**PR6 Run fatigue.** `vision_profile_for` today uses gait `run` for a
shorter cone. D2: run **mode** uses walk/sneak cone until a run **step**
applies fatigue. Fatigue is a decaying stack that penalizes cone range
and shot damage (factors in targeting). Values in `data/hunt_*.json` after
Q4/Q5. Running still clears aim (archive #74) and still cannot sidestep/
backpedal (archive #57 except the vision part).

**PR7 Aim off-center.** After fatigue so vision is: base cone + fatigue +
aim heading. Tank movement stays 8-tick (archive #21–22, #54). Off-center
is an **aim heading** inside/beside that tick (Q1–Q3). **A** opens a reticle
on a currently visible tile; confirm centers the heading there. Live FOV
is the confirm. **Ctrl+7/9** yaw by `2 * cone_half_degrees` (next cone,
shared edges, no overshoot). Aim 1/2 blinds Chebyshev 1 / 1–2. Run/quick
drop aim only when a step actually happens; drop snaps body to nearest 45°.
Fire line default and FOV use the aim heading, not only `facing_delta(facing)`.

**PR8 Visible projectile.** After PR7. Harvest the idea of
`reference/kdvr/src/systems/projectile_anim.py` (copy into hunt; do not
import `reference` at runtime): step the dart along the existing Bresenham
shot line, then apply the already-deterministic hit. Q12: KDVR defaults
(`*`, cyan, 1 frame/tile, 0.024s); hunt time pauses during flight.
Animation is cosmetic; damage does not roll again per tile.

### F — Loss spectacle (one playtest)

**PR9** is swallow modal → belly (KDVR color, camera on the pair, raptor
walks a little carrying the hunter) → digest modal → centered game-over
modal.

Harvest: KDVR `render_engulfed_overlay` color `(100, 20, 20)`; narrative
modals via existing proportional dialog (`src/ui/proportional_dialog.py`)
the same **pattern** as KDVR engulf/digest modals — not overlay `win_lines`
at the top of the map. Do not import `reference.kdvr` at runtime.

Belly walk is hunt-only. During BELLY, hunter still/move still spend the
turn and do nothing; meta (help, log) stays OK. Camera follows the
hunter-in-belly tile (raptor position). Autosave must include raptor
position during belly if it can move (additive fields).

Q13–Q15 must be answered before this PR. Tranq bask (#51) stays a frozen
map, not this modal path, unless Q13 expands it.

### G — Verification and audio

**PR10 Practice dummy.** Separate mode. **Fixed handmade arena** (same
layout every time), not a random paddock seed. Must include a patrol
path that crosses **open ground and long grass**, a stand-still tile in
long grass, and a stand-still tile in open ground (teleport anchors).

**F2** (practice only) opens a command menu. Live hunt does not bind F2
to this menu. Help in this mode lists F2.

| Command | Teleport? | Raptor does |
|---------|-----------|-------------|
| Walk back and forth (open ↔ long grass) | Yes, onto the patrol | Patrol that path |
| Stand still in long grass | Yes, onto the grass anchor | Idle there |
| Stand still in open ground | Yes, onto the open anchor | Idle there |
| Stop moving | No | Freeze in place |
| Cancel stop moving | No | Resume the script that was interrupted |
| Seek and chase hunter ASAP | No | Time-almost-over urgency: go get adjacent |
| Gait: sneak / walk / run | No | Speed overlay; orthogonal to the script |
| Normal behavior | No | Live raptor mind (`raptor_act`) |

Wins and losses work under the **same** adjacency rule as the live hunt
(D14): Chebyshev 1 **and** hunter in the raptor’s FOV. Outcomes **do not**
increment stats, abandon, or difficulty boards. Do not leave a practice
run on **Continue Hunt**. Entry is **Training Mode** on the main menu (Q10). No name entry in the
product. Training skips weapon select (default rifle); F2 also swaps
weapon on the fly. Unrecorded; not Continue Hunt.

**PR11 Rain beds.** `Sounds/LightRain.mp3`, `MediumRain.mp3`, `HeavyRain.mp3`
(10 min). All three loop concurrently. Weather id picks the 100% bed;
the others sit at 0%. Swap is a wall-clock crossfade
(`layer_crossfade_seconds`). Each bed self-crossfades
(`loop_crossfade_seconds`) so the 10-minute loop does not click.
Missing files are skipped. Playback **streams** via miniaudio (a few ms
of PCM at a time). Do **not** fully decode MP3s into `Sound` buffers —
that hitch froze the window at New Hunt / Training. Loop joins use two
decoder voices per bed (tail overlaps a fresh stream of the same file).
The audio device is opened at window start and **stays running**; Esc
mutes and drops streams without `device.stop()` (that WASAPI teardown
was the menu pause). Hunt start / Training / Continue Hunt **fade in**
from silence over `layer_crossfade_seconds` rather than popping in at
full volume.

### H — Raptor mind (last)

**PR12** is D16–D20 (Q17). Supporting systems (AUT, fatigue, rain vision,
live-paddock bullseye) ship in this PR because the mind is written against
them. Training arena stays D7.

#### Gait AUT (D17)

Walk is the baseline. All values tenths. Smallest tenths that match the
four-turn speed brief:

| Gait | AUT / step | 4 steps | Tiles / AUT vs walk |
|------|------------|---------|---------------------|
| Walk | **0.8** | 3.2 | 1× |
| Quick | **0.7** | 2.8 | same as run+walk+walk+walk (0.4+0.8×3=2.8) |
| Run | **0.4** | 1.6 | **2×** walk |
| Sneak | **1.6** | 6.4 | ½ walk |

Sidestep/back use the current gait’s step cost. Rotate/wait/aim/fire
follow walk **0.8** unless a later playtest says otherwise.

Clock: today `duration_aut` 400.0 assumed walk 1.0 (~400 walk-steps).
**Proposal:** set duration to **320.0** so the hunt is still ~400 walk
steps (320/0.8). Designer may keep 400 if they want a longer hunt.

Raptor spends the AUT of the gait it actually used that turn (not a
fixed `wait`). Dummy F2 gait override still wins.

#### Fatigue (D18)

Run step +1 (cap 4). Quick step holds. Every 3 **walk / wait / sneak**
turns (any mix) recover 1. Quick and run **reset** a partial streak.
Rotate / aim / fire do not recover.

#### Rain vision (D19)

Playtest JSON (hunter walk cone 8, raptor base 8, penalties):

| Rain | Hunter penalty | Raptor penalty | Effective (walk) |
|------|----------------|----------------|------------------|
| Light | 0 | 2 | hunter **8** > raptor **6** |
| Medium | 2 | 0 | hunter **6** < raptor **8** |
| Heavy | 4 | 0 | hunter **4** ≪ raptor **8** |

Aim still lengthens the hunter cone on top of this.

#### Center bullseye (D20)

Hand-place (then jitter slightly by seed): mud disk at center; around it
a ring of long-grass patches alternating with open grassland so a raptor
in grass can appear from any sector. Trees/bushes/mud blobs stay **outside**
that ring. Training map unchanged.

#### Heatmap (the guess, not a cheat)

A per-tile belief the raptor maintains. It is **not** player coordinates.

- Recent **FOV scans** mark tiles as “I already looked here.”
- Occupancy smears from last authority at **hunter speed** (walk/quick/run
  Chebyshev budget from AUT since last fix).
- **Eyes-on** or a **hunter print** in cone: authority — collapse the
  heatmap around that tile (prints = stale eyes-on). Raptor prints are
  ignored as hunter-location (it can tell the feet apart).
- Right after a sighting, belief is a tight disk; noises outside it are
  ignored (hunter cannot teleport).
- Sounds (real footsteps or false rain/wind) add weight only where belief
  is still plausible **and** not recently scanned. No equal-value
  obsession with every `?`.
- **Gunshot (D21):** heard anywhere, tagged as a shot. Sample apparent
  center `C` uniformly among walkable tiles with Chebyshev ≤ `gunshot_jitter`
  of the true fire tile. Paint a **flat** plateau: every walkable tile with
  Chebyshev ≤ `gunshot_blur` of `C` gets the same weight (the raptor does
  not prefer `C`). JSON playtest: jitter 3, blur 4. Does not spawn a hunter
  `?` (that glyph is footsteps / false rain-wind).

#### Intent table

| Situation | Intent |
|-----------|--------|
| **Danger-close:** eyes-on and Chebyshev ≤ `danger_close` (JSON, playtest **4**) | **Rush:** run, close ASAP. Beats observe / shy / circle / scramble / grass-stalk. Sidestep only if a tree is in the way; do not back off |
| Hunter staring one way a long time | **Sneak** up behind; **run** once too close to turn in time |
| Hunter walking/turning a lot | Long-grass **ambush**; standing still to stare is OK |
| Hunter staring **back** | Shy: break contact, grass, max distance |
| Staredown, not aiming | Max distance, **sidestep** circle |
| Sees hunter aiming | **Run** diagonal-away and/or perpendicular (worst tracking geometry). Shot table does **not** yet have crossing penalties — this is dodge geometry unless the designer later adds factors |
| Raptor definitely winning | Careful stalk, **stick to long grass** (bullseye ring is the tool) |
| Clock would be a hunter win | Emergency: find (heatmap) and **rush** |
| No good clue | Patrol / scan to feed the heatmap |

#### Hunt log (D22)

Harvest the donor **proportional TTF** log (same font as KDVR) into hunt.
Place it in the **lower right panel** under weather (the unused column
below stats) — not CP437. Lines wrap in pixels.

Content:

- Existing hunt notices (`You fire your rifle!`, facing errors, …)
- One **raptor-thought** line per raptor turn (intent in plain language),
  e.g. watching from behind, sneaking up, sprinting off the aim line,
  gunshot somewhere in that grass, ignoring a noise that does not fit.
  All copy through `messages.py`.

Always on for this PR so the mind can be playtested. Hide or tone down
later if it spoils the hunt; do not invent a debug key unless asked.

Do **not** give it live player coordinates, scent, or packmates.

### I — Raptor intelligence pack (PR13–PR15)

PR12 shipped a real mind; playtest still found stillness, aim-line walking,
and a scoped rifle that sees too much. This pack is **number-one priority**.
Designer waived per-PR playtest until PR15.

**Vetoes:** do not forbid mud; do not treat own mud prints as a problem
beyond “not a hunter clue”; do not teach ammo/reload/empty gun.

#### PR13 — Rifle, sound, draw order

Rifle aimed FOV is a **Bresenham line** along aim heading, playtest range
**22** (aim) / **28** (deep), **close-blind 3**. Hipfire/walk cone unchanged.
Shotgun/revolver keep today’s aim/deep half-angles.

Gait sound **chance** then hear-range. Base (light): run 1.00, quick 0.67,
walk 0.33, sneak 0.00. Medium **−0.10**, heavy **−0.20** (sneak stays 0).
Emit at the tile **left**. Medium/heavy raise false-alarm rate (static).

**Double-step (D37):** if she hears two events on adjacent tiles within
`double_step_aut` (playtest 2.0), collapse heatmap on that pair (authority
smear). One `?` is still weak; two in a row next to each other is the hunter.

Render: if hunter sees the raptor, always `r`. Else last-known dim `r` if
that tile is not in current FOV. Else `?`. Never `?` on top of a live raptor.

#### PR14 — Mind

Memory (from last fair see, not live cheat):

- Cone snapshot **plus** a short ring of recent facings (sweep).
- Hot tiles: do not enter while evading; decay in JSON AUT.
- Aim-line (last heading Bresenham): sprint across, do not idle on it.
- Burned tiles: where she was in hunter FOV; avoid return until cool.
- If the sweeping cone is about to include her tile, leave now.

Rain: she knows the cycle index from world AUT (same formula as weather —
not a cheat, the storm is public). N AUT before light → turtle. Light →
3-deep sit, grass-only relocate. Heavy → hide-to-hide, flanks, rear rush
if she can commit (D32) even if clock/points are fine.

Hides: sit facing out; after a few turns or if burned/stared-at, sprint to
another hide. Prefer a tree on the old aim line when breaking contact.

Locomotion: diagonal-forward = step `facing±1`, facing unchanged. Hunter
cannot. When a tree blocks the nose, **step around** (diag/side/greedy
progress) — do not rotate in place. Evasion: **run to nearest deep hide
first**, then open distance from another angle.

Stalk clock: JSON turns of watch; reset on hunter turn/aim. Commit if not
in remembered cone **and** Chebyshev / raptor-run-AUT < hunter yaw-to-bear
AUT. Heave ignores that.

Sound bait: one short run in unseen grass, then freeze and watch heading
change.

#### PR15 — Difficulty

New hunt keys (defaults = current Normal). Nightmare may raise raptor
`speed_mult` and `cycle_aut` / heavy dwell. Optional raptor cone bonus.
**Forbidden:** current hunter xy, scent, “she just knows.”

---

## Harvest (allowed)

| Need | Copy from (adapt into `src/hunt_*.py`) |
|------|----------------------------------------|
| Projectile frames | `reference/kdvr/src/systems/projectile_anim.py` |
| Belly `#` color | `ENGULFED_OVERLAY_FG` in `reference/kdvr/src/systems/render.py` |
| Narrative modal chrome | `src/ui/proportional_dialog.py` / KDVR engulf modal flow |
| Numpad/scancodes | `tcod.event` KeyDown `scancode` / `sym` |

Do not implement leftover Gladiavore changes (`tactical-duel-combat`, etc.).

---

## Persistence

| PR | Save note |
|----|-----------|
| PR2 | None required if panel is derived |
| PR3 | None (rule only) |
| PR4 | Last-known tile on the hunter side |
| PR5 | `MudPrint` rain-at-stamp / per-print TTL; default on load if missing |
| PR6 | Fatigue stack |
| PR7 | Aim heading if not equal to facing |
| PR9 | Raptor xy during belly if it moves |
| PR10 | Dummy should not use the live autosave slot as a career hunt |
| PR12 | Heatmap / last authority default empty on load; gait AUT and clock duration are data (old saves play the new costs) |

Additive fields; default on load (AGENTS.md save rules).

---

## Performance

Paddock is one map, two actors. Projectile animation is a short frame loop
(keep it event-driven, not a busy-wait that skips input forever). Belly
walk is a few idle steps. Last-known is one tile. Do not scan the whole
map per frame for prints beyond the viewport.

---

## Resolved decisions

Fill as Q&A lands (copy into `DESIGN_CANON.md` open-question table).

| Decision | Resolution | Date |
|----------|------------|------|
| Relative score is not its own PR | Absorbed by PR2 panel | 2026-09-04 |
| Mention order is not PR order | This design’s graph | 2026-09-04 |
| Practice dummy is a fixed arena + F2 command menu | D7 / D7b / D7c; Q11 resolved | 2026-09-04 |
| Practice W/L not recorded | No stats, no abandon, not Continue Hunt | 2026-09-04 |
| Adjacent + raptor FOV = instant raptor win | Behind / out of raptor FOV is safe (D14; Q9) | 2026-09-04 |
| Sidestep is Ctrl-only | Shift removed; Windows NumLock steals Shift+numpad (D15) | 2026-09-04 |
| Aim pick / yaw / close-blind / drop-on-move | Q1–Q3; see DESIGN_CANON | 2026-09-04 |
| Conventional rotate drops aim | Unshifted 7/9/4/6 cancel aim and snap to the next 45° in that direction from the aim heading (playtest) | 2026-09-04 |
| Yaw is one-third of the cone | Ctrl+7/9 lose/gain one third; facing tracks nearest 8-tick while aimed | 2026-09-04 |
| Fire along facing | Blind fire OK; shot heading must sit in the current facing’s 45° slice or the hunter stays in targeting | 2026-09-04 |
| Visible dart uses KDVR timing | `*`, cyan, 1 frame/tile, 0.024s; time pauses until it lands (Q12) | 2026-09-04 |
| Loss spectacle Q13–Q15 | Every ending is a centered GAME OVER (tranq bask first). Belly is black; `#` on the raptor tile; 50/50 idle vs random step | 2026-09-04 |
| Training Mode / no names | Main menu Training Mode; product has no name entry; F2 dummy + weapon swap; unrecorded | 2026-09-04 |
| Rain beds | Three concurrent MP3s; 100%/0% with wall-clock crossfade; self-crossfade at loop | 2026-09-04 |
