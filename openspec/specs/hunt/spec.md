# Spec: Velociraptor Hunt

## Purpose

One-hunt 7DRL-style paddock hunt: a nameable hunter tranquilizes a single
velociraptor, or is swallowed and digested. Live product behavior for
Velociraptor Hunt (not Gladiavore career/match, not a KDVR dungeon crawl).

Terminology: hunter success is **tranquilized**; melee connect is **finished**
then **swallowed** / **digested**. Do not use kill / die / death.

## Requirements

### Identity and loop

- The product name is Velociraptor Hunt. Main menu is New Hunt, Training Mode, Stats, Options, Quit (Continue Hunt when a live hunt is saved).
- New Hunt → rifle / shotgun / revolver → one paddock hunt. No name entry. Results return to the main menu.
- **Training Mode** is a separate unrecorded hunt on a **fixed** arena (open grassland west, long grass east, patrol across both). No name or weapon select at start (default rifle). **F2** (this mode only) opens dummy commands and on-the-fly weapon swap. Wins and losses work (same D14 adjacency) but do **not** write stats, abandon, or Continue Hunt.

### Body, facing, vision

- UnReal World tank controls (numpad primary; TYUGHJBNM / arrows fallback). Eight facings. Vision is a facing cone (walk/sneak playtest range **12**; raptor **14**; aim longer). Sidestep is **Ctrl+4/6** (or Ctrl+G / Ctrl+J / Ctrl+arrows). Shift does not sidestep. Unshifted 4/6 always rotate. Main-keyboard 4/6 are not tank keys.
- Gaits: **Q** quick, **W** walk, **R** run, **S** sneak. Run **mode** does not shorten vision. AUT is tenths, walk is the baseline: walk **0.8**, quick **0.7**, run **0.4**, sneak **1.6** (2× walk). Sidestep/back use the current gait’s step cost. Rotate / wait / aim / fire follow walk **0.8**. Each **run step** adds a fatigue stack (cap 4). Quick steps hold fatigue. **Walk, wait, and sneak** share a recovery streak: any mix of those three recovers 1 stack every **3** such turns. Quick and run **reset** a partial streak. Rotate / aim / fire do not recover. Run + sidestep/back drops to walk. **Run or quick steps** drop aim; toggling gait without moving does not. Walk and sneak steps keep aim.
- **A** opens an aim reticle on a **currently visible** tile (not outside the live cone; not a noise you cannot see). Confirm (Enter or A) sets aim heading on that point (depth 1). **A** again is deep aim (depth 2) on the same heading. **D** stands down. **Rifle** aim/deep-aim is a **scoped line** (no peripheral), longer, **blind within 3 tiles**. Shotgun and revolver keep a wedge. Aim heading may sit off the 8 tank ticks; FOV uses that heading. **Ctrl+7 / Ctrl+9** yaw by **one-third** of the cone (two-thirds overlap: lose one third, gain one third). Official facing tracks the nearest 8-tick to the aim heading as you yaw (exact halfway is random). Unshifted **7/9/4/6** (and letter/arrow equivalents) **drop aim** and snap body + cone to the next 45° in that rotate direction (from the aim heading, not a leftover body tick). **D** or a run/quick step snaps to the nearest 45° (exact halfway is random between the two). Aim 1 blinds Chebyshev-1 tiles; aim 2 blinds Chebyshev 1–2. The hunter’s own tile stays visible.

### Fire and tranquilize

- F opens targeting; cursor starts on a visible raptor; blind fire is a linear projectile to weapon max range. The shot heading must be **generally the current facing** (that 8-tick’s 45° slice). If it is not, show “You must fire in the same direction you're facing.” and stay in targeting (no ammo spent). Factors show only in targeting. F or Enter confirms; Esc aborts. The dart then **flies along the shot tiles** (`*` cyan, KDVR timing: 1 frame/tile, 0.024s) while hunt time is paused (no AUT, no raptor turn, no tank input). Damage is already determined; it applies when the dart arrives.
- Damage is deterministic (same situation → same result). Damage below zero is a miss. Rifle unaimed at long range (rain, a moving raptor, crossing motion) often goes to **zero**; a still target at close range may still graze. Shotgun and revolver keep their existing numbers. If the raptor is **on the dart's path**, it treats that as being aimed at (break contact).
- Raptor 0 HP: fire line, bright tranquilized on the frozen map, then You win results. Dismiss results with Enter or Esc only.

### Weather, clock, loss

- Rain cycles (same light→medium→heavy→medium loop; each step playtest **40.0 AUT**). Hunter cone is slightly better in light rain; raptor is clearly better in moderate and **much** better in heavy (heavy is her prime window). Heavier rain also hides movement sounds and adds false rain/wind. Three rain beds (`Sounds/LightRain.mp3`, `MediumRain.mp3`, `HeavyRain.mp3`) play together; the current weather is at full volume and the others are silent, with a wall-clock crossfade on change. Each 10-minute bed self-crossfades when it loops so the join is hidden. Missing files must not crash.
- Terrain tiles: **mud** `.` (prints), **open field** `'`, **long grass** `,` (partial vision), **tree** `T` (blocks vision and shots). Legacy bush counts as long grass (same `,`). Footprints only on **mud**. Each print stores the rain TTL from when it was made; heavier rain → longer life; they expire individually. Live paddock **center is a bullseye**: a **tiny** mud disk, then a ring of long-grass patches (thick enough for 3-deep hides) with open ground between them; ring-control is a plateau across that inner disk+ring so spinning on the mud does not uniquely win. Outside that ring generation is freer. Training Mode keeps its fixed handmade arena.
- Long grass is a **counted veil**. Hunter in light/medium rain sees **2** consecutive grass tiles; in heavy rain **1**. Raptor sees **2** consecutive regardless of weather. Grass you stand on does not count, so a raptor 3 deep can see the field while the hunter cannot see in. Map gen marks those 3-deep tiles as hide spots.
- Last-known raptor: never seen → nothing; currently in LOS → live `r` only; seen before but not now → dim `r` on the last seen tile (cleared when seen again, or when the hunter has FOV on that tile and the raptor is not there).
- Sounds are one map `?` (real movement and rain/wind false alarms). Real step chance: run 100 / quick 67 / walk 33 / sneak 0; medium −10, heavy −20; the mark is the tile **left**. Two adjacent heard steps in a short AUT window are a near-certain hunter smear. Live `r` (in FOV) beats last-known dim `r` beats `?`. No bottom-line “Movement N / Rain in the canopy / Wind from the SE.”
- Hunt clock and center-weighted ring live at the top of a **right-side panel**, then a reserved slot for raptor info, then always-on hunter stats in lime (Facing, Weapon, Ammo, Speed, Aim level, Fatigue). Weather is on its own line (light blue / medium indigo / heavy purple). Targeting adds yellow **Range: N**. When the raptor is in hunter sight the reserved slot lists **Velociraptor**, Chebyshev **Distance**, **Facing** (append **!** only if the raptor currently sees the hunter), **State**, and fuzzy **Health** (Perfect / Steady / Rattled / Wavering / Weary; overlapping bands keep the last label while HP stays inside it). The bottom line is notices and end-prompt only.
- Hunt clock duration is data (`duration_aut`; playtest **320.0**, ~400 walk-steps at walk 0.8). Time-over is a hunter win only if Hunter definitely winning; Close or raptor-ahead is a time-over loss. A **lower-right proportional log** (same TTF as the donor log) shows hunt notices and a live raptor-thought line.
- Instant raptor win (swallow) when Chebyshev 1 **and** the hunter is in the **raptor’s own FOV**. Adjacent but behind / out of its cone is safe. Check after hunter step, raptor step, and raptor facing change. Swallow angle is still front / side / behind from the geometry. Swallow, digest, and GAME OVER are **opaque centered modals** (dark fill, centered text). After swallow, the paddock stays **hidden** through belly, digest, and GAME OVER. Belly: **full black** void; eight `#` around the raptor’s map tile; camera is **locked at the swallow tile** so a raptor step **slides the ring**. Each wasted still/move: **50%** idle, **50%** a random walkable step (hunter is carried). Only `@` and `#` **darken** toward GAME OVER; the background stays black. Tranq bask stays a frozen map; **results** and **time-over** are opaque centered GAME OVER boxes.

### Raptor mind

- Fair senses only (eyes-on, last seen, hunter prints in its cone, heard movement, identified gunshots). It keeps a **heatmap** of where the hunter might be (recent scans + last occupancy). Eyes-on or a hunter print collapses that guess; prints are stale eyes-on. A **gunshot** is always heard and known to be a shot, but poorly localized (jittered apparent center, then a **flat** blur disk). Other sounds are pursued only if they still fit the heatmap (no re-check of a just-scanned patch; ignore extras right after a sighting). Same tank verbs as the hunter, including **sidestep**. Raptor body AUT is **half** the hunter's (2× speed), including turns. While evading it will not step into the hunter's **last-known cone**. **Danger-close** (eyes-on, Chebyshev ≤ 4): run and close, no exceptions. Idle: stay near center — outskirts patrol if the score is close, contest the mud if the hunter is winning the ring, milk long-grass hides if the raptor is winning; heavy rain with no fix → run between hide spots. Eyes-on: observe/stalk. Hunter still with back turned a long time: sneak then sprint. Hunter erratic: keep watching, strafe, wait for an opening. Long-range staredown is OK. Aimed at (and not danger-close): break contact with urgency, strafe while facing the heatmap peak, circle from another angle. Training **normal** uses this mind; F2 gait override still wins.

### Stats and help

- Stats screen (main menu) persists **per difficulty** (Easier, Normal, Hard, Nightmare): total games, games abandoned, tranquilized, digested, time-over wins/losses; per weapon shots fired, landed, perfect (would deal 100% damage), one-shot KOs (100% HP to 0% in one shot). Left/Right cycles boards.
- In-progress hunts autosave (KDVR rotating `autosave.json` chain). Ctrl+Q and closing the window write a save. Continue Hunt resumes. Esc to menu pauses (save, no game counted). New Hunt with a save prompts to abandon; Yes counts a game and a game abandoned for that hunt’s difficulty, then wipes the save.
- In-hunt F1 or ? lists hunt commands. Esc closes help without leaving. Bottom hunt chrome does not list movement keys.

## Scenarios

### New Hunt reaches the paddock

- **GIVEN** the main menu
- **WHEN** the player confirms New Hunt, enters a name, and picks a weapon
- **THEN** a hunt session starts in the paddock (not a Gladiavore career hub)

### Tranq win dismisses only on Enter or Esc

- **GIVEN** the raptor is at 0 HP (tranquilized bask or results)
- **WHEN** the player presses a letter key
- **THEN** the hunt does not return to the menu
- **WHEN** the player presses Enter or Esc on results
- **THEN** the hunt returns to the main menu and Stats records a tranquilized game

### Stats persist across menu visits

- **GIVEN** a finished hunt that fired shots
- **WHEN** the player opens Stats from the main menu
- **THEN** totals and the used weapon’s shot fields include that hunt

### Abandoning a saved hunt counts a game

- **GIVEN** an in-progress hunt autosave
- **WHEN** the player selects New Hunt and confirms abandon with capital Y
- **THEN** that hunt’s difficulty board increments total games played and games abandoned, and the save is wiped

### Stats boards are per difficulty

- **GIVEN** the Stats screen
- **WHEN** the player presses Left or Right
- **THEN** the visible totals switch among Easier, Normal, Hard, and Nightmare

### Ctrl sidestep

- **GIVEN** a hunt in play
- **WHEN** the player holds Ctrl and presses numpad 4 or 6 (NumLock on or off)
- **THEN** the hunter sidesteps without changing facing
- **WHEN** the player presses numpad 4 or 6 with Shift or with no modifier
- **THEN** the hunter rotates 90°
- **WHEN** the player holds Ctrl and presses the main-keyboard 4 or 6
- **THEN** that is not a sidestep

### Help does not abandon the hunt

- **GIVEN** a hunt in play (or belly)
- **WHEN** the player presses F1 or ?
- **THEN** a help overlay lists tank, gait, aim, and fire keys
- **WHEN** the player presses Esc
- **THEN** help closes and the hunt continues

### Right-side panel holds clock and ring

- **GIVEN** a hunt in play
- **WHEN** the paddock is drawn
- **THEN** clock remaining and the three-state ring appear in a right-side column
- **AND** the bottom line does not show the clock or ring
- **WHEN** the raptor is in sight
- **THEN** the panel shows Velociraptor, Distance, Facing (with ! if it sees the hunter), and State
- **WHEN** targeting mode is open
- **THEN** shot factors and ammo appear in the panel, not as the default footer

### Last-known raptor after LOS loss

- **GIVEN** the hunter has seen the raptor
- **WHEN** the raptor leaves the hunter’s FOV
- **THEN** a dim `r` remains on the last seen tile
- **WHEN** the raptor is in FOV again
- **THEN** only the live `r` is shown
- **WHEN** the hunter has FOV on the last-known tile and the raptor is not there
- **THEN** the dim `r` is cleared
- **GIVEN** the hunter has never seen the raptor
- **THEN** there is no last-known mark

### Sounds are one map glyph

- **GIVEN** a heard movement or a rain/wind false alarm
- **WHEN** the map is drawn
- **THEN** that tile shows `?`
- **AND** the bottom line does not describe rain, wind, or “Movement N”

### Adjacent and seen is an instant raptor win

- **GIVEN** the raptor is Chebyshev 1 from the hunter and the hunter is in the raptor’s FOV
- **WHEN** that becomes true (hunter step, raptor step, or raptor turn)
- **THEN** swallow starts immediately (no melee commit)
- **GIVEN** the raptor is Chebyshev 1 but facing away so it does not see the hunter
- **WHEN** the hunter is otherwise still in play
- **THEN** the hunt is not lost on adjacency alone

### Loss spectacle

- **GIVEN** the raptor swallows the hunter
- **WHEN** the swallow modal is dismissed
- **THEN** the screen is black, eight `#` sit on the raptor’s tile, and the hunter is inside that ring
- **WHEN** the hunter wastes still/move turns
- **THEN** each turn the raptor has a 50% chance to take a random step (hunter carried, camera follows)
- **WHEN** belly ends
- **THEN** a digest modal, then a GAME OVER modal, dismissible with Enter or Esc only

### Dart flies then resolves

- **GIVEN** the hunter confirms a legal shot
- **WHEN** the dart is in the air
- **THEN** a cyan `*` steps along the shot tiles and hunt time does not advance
- **WHEN** the dart arrives
- **THEN** the already-determined hit, miss, block, or tranquilize applies (one resolve, not per tile)

### Aim pick, yaw, and close-blind

- **GIVEN** the hunter is in play and not yet aiming
- **WHEN** they press **A**
- **THEN** a reticle appears on a currently visible tile (never outside the live cone)
- **WHEN** they confirm on that tile
- **THEN** aim depth is 1 and the vision cone is centered on that heading
- **WHEN** they press **Ctrl+7** or **Ctrl+9** while aimed
- **THEN** the cone yaws by about one-third of its width (two-thirds overlap) and official facing tracks the nearest 8-tick to the new heading
- **WHEN** they rotate with unshifted 7/9/4/6 while aimed
- **THEN** aim cancels and body + cone snap to the next 45° in that direction
- **WHEN** they stand down or a run/quick **step** drops aim
- **THEN** body facing snaps to the nearest 45°
- **WHEN** aim is 1
- **THEN** adjacent tiles (Chebyshev 1) are not visible
- **WHEN** aim is 2
- **THEN** Chebyshev 1 and 2 are not visible

### Time-over uses the three-state ring

- **GIVEN** the clock has reached 0.0
- **WHEN** the ring is Hunter definitely winning
- **THEN** the hunter wins by time over
- **WHEN** the ring is Close or Raptor definitely winning
- **THEN** the hunter loses by time over
