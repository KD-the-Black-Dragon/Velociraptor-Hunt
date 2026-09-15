# Hunt deferred — canon addendum

Foundation canon stays in
`openspec/changes/archive/2026-09-04-velociraptor-hunt/DESIGN_CANON.md`.
**Do not re-ask** those locked decisions.

This file records **amendments** the deferred pack makes to that canon, and
**open questions** this change must not invent.

---

## Named intent (locked as “we want this”; details may still be open)

These are the designer’s deferred items, not agent inventions.

| # | Decision | Recorded |
|---|----------|----------|
| D1 | Aim may sit **off-center of a 45° facing**. The hunter must be able to **confirm exactly what they are aiming at**. Aim is still a facing/cone/stance game (archive #23) — not a return to “aim at a specific tile.” | 2026-08-31 |
| D2 | **Run mode** does not cut vision. **Actually running** applies a short-term **fatigue / frantic** debuff. That debuff gives **progressive** penalties to **vision and accuracy**. | 2026-08-31 |
| D3 | **Last-known raptor:** never seen → nothing; currently in LOS → live raptor only; seen before but not now → last-known mark only (erase when seen again, or when the hunter has FOV on that tile and it is empty). | 2026-09-04 |
| D4 | Score differential and raptor info live on a **right-side hunt panel**, not the two bottom lines. | 2026-08-31 |
| D5 | The hunter’s dart **travels visibly** across the map. | 2026-08-31 |
| D6 | Rain audio **cross-fades real wav layers** when assets exist (foundation shipped a 0–1 fade stub). | 2026-08-31 |
| D7 | **Training Mode** (main menu) is a separate unrecorded hunt on a **custom arena that is always built the same way** (open ground and long grass, plus fixed teleport anchors). **F2** (this mode only) opens dummy commands and on-the-fly weapon swap. Wins and losses are **fully enabled** but **not recorded** (no stats, no abandon, not Continue Hunt). | 2026-09-04 |
| D7b | Practice F2 commands: **walk back and forth** (in and out of open ground and long grass) — **teleport** on command; **stand still in long grass** — teleport there; **stand still in open ground** — teleport there; **stop moving** — no teleport; **cancel stop moving** (resume the previous script) — no teleport; **seek and chase the hunter ASAP** (time-almost-over urgency); **force gait** sneak / walk / run (orthogonal to the script); **normal behavior** (live raptor mind). | 2026-09-04 |
| D7c | Practice dummy uses the **same adjacency rule as the live hunt** (D14). | 2026-09-04 |
| D8 | Final **game over** is a **centered modal**, not overlay text on the map. | 2026-08-31 |
| D9 | **Sounds are map symbols only.** No bottom-line “Rain in the canopy / Wind from the SE / Movement N.” **One shared symbol** for “that might have been a raptor.” | 2026-08-31 |
| D10 | Footprints are **always created** (not only in heavy rain). Each print remembers the **rain when it was made**; heavier rain → longer life; they fade individually. **Only mud tiles, not grass.** | 2026-08-31 |
| D11 | Ring / relative score stays visible; its **home is the right-side panel** (D4). No separate throwaway footer PR. | 2026-08-31 |
| D12 | **Belly:** paddock hidden through digest / GAME OVER. Eight `#` in KDVR color `(100, 20, 20)` around the **raptor’s actual tile**. Camera **locks at the swallow tile** so a step slides the ring. Background stays **full black**; only `@` and `#` darken toward GAME OVER. Raptor 50/50 idle vs random step and **carries the hunter**. Modals are opaque with centered text. | 2026-09-04 |
| D13 | Swallow / digest lines are **KDVR-style modal windows**, not overlay-only text. | 2026-09-01 |
| D14 | Instant raptor win (start swallow / vore modal) only when **both** are true: Chebyshev 1 **and** the hunter is in the **raptor’s own FOV** (cone + LOS, same `sees` as fair play). Adjacent but **behind** the raptor, or otherwise not in its FOV, is **safe**. No melee-commit action. Check after hunter movement, raptor movement, raptor facing change, and dummy teleport. Live hunt and practice dummy share this rule. | 2026-09-04 |
| D15 | Sidestep is **Ctrl+4/6** only (numpad or Ctrl+G / Ctrl+J / Ctrl+Left / Ctrl+Right). **Shift is not a sidestep modifier.** Unshifted 4/6 always rotate, NumLock on or off. | 2026-09-04 |
| D16 | **PR12 raptor mind** is a real hunt (not a stub). Fair senses only. **Heatmap** of where the hunter might be (recent scans + last occupancy). Eyes-on or **hunter** prints in cone are **authority** and collapse the heatmap. Prints are stale eyes-on. **Gunshots** are identified as gunshots but poorly localized (D21). Other sounds are pursued only if they fit the heatmap (do not re-check a recently scanned patch; ignore extras after a fresh sighting — the hunter cannot teleport). Same tank verbs as the hunter including **sidestep**. Gait sneak/walk/run with real AUT. **Danger-close** (D23): eyes-on within 4 → run rush, no exceptions. Early match: max distance, observe from behind. If the hunter stares one way a long time: sneak up, then **sprint** once it is too late to turn. If the hunter is busy walking/turning: stick to **long grass** and ambush. Shy when stared back at. Staredown (not aiming): max distance, circle with sidesteps. Sees aim: **sprint** diagonal-away and/or perpendicular (worst aim geometry). Raptor-winning: careful stalk in long grass, not a center sit in the open. Clock about to be a hunter win: emergency find-and-rush. | 2026-09-10 |
| D17 | **Gait AUT** is proportional, tenths, **walk is the baseline**. Sneak costs **2× walk**. Run is **2× walk speed**. Four quicks match **run+walk+walk+walk**. Playtest numbers (smallest tenths that fit): walk **0.8**, quick **0.7**, run **0.4**, sneak **1.6**. Sidestep/back at a gait use that gait’s step cost. Hunter run+sidestep/back still drops to walk. | 2026-09-10 |
| D18 | **Fatigue** (amends Q4): **walk, wait, and sneak** share one recovery streak — any mix of those three recovers 1 stack every **3** such turns. **Quick** holds (no gain, no recover) and **resets** a partial streak. **Run** is wind sprints (+1 per run step, cap 4) and **resets** a partial streak. Toggle still does nothing (Q5). | 2026-09-12 |
| D19 | **Rain vision**: hunter cone is **better in light rain**; raptor is **better in moderate** and **markedly better in heavy**. Numbers in paddock/weather JSON. | 2026-09-10 |
| D20 | Live paddock **center is a bullseye**: mud open in the middle; a ring of **long-grass patches** with **open patches** between them so the raptor can burst from grass. Outside that ring, generation stays more free. Training Mode arena stays D7 (fixed handmade). | 2026-09-10 |
| D21 | A **gunshot** is always heard paddock-wide and is known to be a gunshot (not a footstep). Localization is bad: pick a random **apparent center** within Chebyshev `gunshot_jitter` of the true tile, then treat every walkable tile within Chebyshev `gunshot_blur` of that apparent center as **equally** likely (flat plateau — do not peak at the apparent center). Playtest: jitter **3**, blur **4** (jitter ≤ blur so the true tile stays inside the plateau). | 2026-09-10 |
| D22 | Hunt gets a **lower-right message log** (KDVR-style), **proportional TTF** not CP437. It shows hunt notices and a live **raptor-thought** line so the designer can see the mind. Copy lives in `messages.py`. | 2026-09-10 |
| D23 | **Danger-close:** if the raptor has **eyes-on** and Chebyshev distance is ≤ `danger_close` (playtest **4**), it **rushes** — run gait, close ASAP. Circumstance does not matter (sneak finisher, grass ambush, reflex, even a staredown or an aimed hunter). This beats observe / shy / circle / scramble. Clock emergency and this rush are the same closer; heatmap still aims the path if LOS is lost mid-rush. | 2026-09-10 |
| D24 | Long grass is a **counted veil** (not a second bush tile). Hunter: 2 consecutive in light/medium, 1 in heavy. Raptor: 2 always. Standing in grass does not count that tile. Hide spots are 3-deep grass looking into the open. Idle raptor stays near center (score as a loose hunter-location clue); winning milks grass; heavy rain with no fix runs between hides. Aimed-at (not danger-close): break contact, strafe, circle a new angle facing the heatmap peak. | 2026-09-12 |
| D25 | A dart **on the raptor's tile** is treated like being aimed at (break contact). Rifle unaimed long shots stack extra range, rain, motion, and crossing-move penalties (often 0). Aimed side-profile is a small rifle bonus. Shotgun and revolver numbers stay as they were. | 2026-09-12 |
| D26 | Raptor body AUT is hunter cost / **2**. Tiny center mud; ring score plateaus across mud+grass ring. Rain step **40 AUT**. Hunter walk cone 12, raptor 14; heavy rain hunter penalty 7. Evasion remembers last-known hunter cone and will not step into it. | 2026-09-12 |
| D27 | **Rifle scope:** aimed and deep-aim rifle FOV is a **straight line** (no peripheral). Longer than today’s aim. **Close-blind 3** (playtest). Shotgun and revolver keep current aimed cones. Walk/hipfire cone unchanged. | 2026-09-12 |
| D28 | Raptor **memory:** last-known cone is a decaying no-go; **sweep union** of recent hunter facings; **aim-line corridor** is a kill lane (sprint across, never linger); **burned tiles** where she was seen — she does not return until time/rain cools them. “About to be aimed” (cone sweeping onto her) is leave-now. | 2026-09-12 |
| D29 | **Rain plan:** she can count the deterministic cycle. Turtle in **light**; daring in **heavy**; **before light** she is already conservative. Sit 3-deep then relocate; trees for dart cover, grass for eyes. Orbit the grass ring, not the mud bullseye — except a **confident rear rush in heavy rain** is always legal (clock/points do not veto it). | 2026-09-12 |
| D30 | **Veto — mud indifference.** She may cross mud and leave prints. She still does not treat her **own** prints as hunter-location. | 2026-09-12 |
| D31 | Raptor locomotion: forward, back, sidestep, **diagonal-forward** (facing ±1, facing unchanged). **No diagonal-back.** Hunter stays forward / sidestep / back only. Threatened: strafe-first, face heatmap peak; never pause in remembered LOS. Peek once from a gap, then cut 90°; do not peek the same gap twice. | 2026-09-12 |
| D32 | **Stalk clock:** eyes-on starts a timer. Still / back turned → close. Turning or aiming **resets** and she relocates. Commit only if (a) not in remembered cone and (b) she can reach danger-close before a scope yaw catches her. Heave still breaks the cone rule. **Veto:** she does not know ammo, reload, or empty gun. | 2026-09-12 |
| D33 | **Sound bait (fair):** she may run a short burst in grass you cannot see so you get a `?` off your heading, then go quiet and watch whether you turn. | 2026-09-12 |
| D34 | **Movement sounds:** base chance by gait — run **100%**, quick **67%**, walk **33%**, sneak **0%**. Light rain uses that table. Medium **−10** → 90 / 57 / 23 / 0. Heavy **−20** → 80 / 47 / 13 / 0. Sneak stays **0**. The `?` / heard tile is where they stepped **from**. Hear-range still caps who hears. Medium/heavy also make **more false** rain/wind `?`. No omniscience, no scent. | 2026-09-12 |
| D35 | Draw order: live `r` (in hunter FOV) beats last-known dim `r` beats `?` beats terrain. Last-known `r` is never shown on a tile the hunter currently sees. | 2026-09-12 |
| D36 | **Hunt difficulty JSON** (easier / normal / hard / nightmare): hunter AUT mult, raptor speed mult, rain phase AUT, optional raptor cone, LOS-hot duration, stalk-clock, etc. Nightmare may be numerically unfair (faster raptor, longer heavy). **Never** omniscience. | 2026-09-12 |
| D37 | **Double-step tell:** two heard sounds (real or what she believes is movement) on **Chebyshev-adjacent** tiles within a short AUT window (JSON, playtest **2.0** hunter-walk AUT) are a **near-certain** hunter location — heatmap collapses on that pair like a print/eyes-on smear. Isolated `?` and weather static stay weak. Hear-range still applies; two runs across the paddock do not stitch. | 2026-09-12 |

---

## Deferred (not in this change)

Named for a later balance / mind revisit. Do **not** implement from this archive.

| Item | Note |
|------|------|
| **Sound bait (D33)** | JSON `bait_chance` exists; the idle “run a `?` then freeze” act is **not wired**. |
| **Peek once, then cut (D31 remainder)** | Relocate-from-hide and tree-around exist; **same-gap-twice** memory does not. |
| **Balance pass** | Designer signed off provisionally; raptor speed, rifle scope, rain, and mind still need more playtest. |

Archive #54 / #54b **Shift+4/6** sidestep is **superseded** by D15 (Ctrl only).
Archive #24 / #57 (run-mode shorter cone) is **superseded** by D2 when that PR
lands. Archive #12 (“rest of the world is hidden” in belly) is **amended** by
D12: the paddock remains drawn; the eight `#` overlay the hunter; the camera
locks to the pair. Confirm D12 vs “world hidden” in Q&A before the loss-spectacle PR.

---

## Open questions (do not invent)

Fill these in this table when the designer answers. Implementation of the
matching PR waits on the answers that PR lists in `tasks.md`.

| ID | Topic | Question |
|----|--------|----------|
| Q1 | Aim off-center | **Resolved 2026-09-04** — **A** picks a currently visible tile; confirm centers aim heading on that point. **Ctrl+7 / Ctrl+9** yaw **one-third** of the cone (2/3 overlap). Run/quick drop aim only on a **move**, not a gait toggle. |
| Q2 | Aim confirm | **Resolved 2026-09-04** — live cone **is** the confirm: you pick from tiles you currently see, then the aimed FOV is the new cone. Reticle during pick; after confirm, FOV uses the heading. Fire must still be generally along official facing. |
| Q3 | Aim vs facing | **Resolved 2026-09-04** — tank **body** stays on 8 ticks for movement. Aim **heading** is continuous while aimed. As you yaw, facing tracks the nearest 8-tick (halfway random). Unshifted 7/9/4/6 **drop aim** and snap to the next 45° in that direction (from the aim heading). On stand-down / run-quick step, body snaps to the nearest 45°. |
| Q4 | Fatigue numbers | **Amended 2026-09-12 (D18)** — +1 per **run step**, cap 4. Recover 1 per **3** walk/wait/sneak turns (any mix). Quick holds and resets a partial streak. Run resets a partial streak. |
| Q5 | Fatigue vs toggle | **Resolved 2026-09-04** — pressing **R** with no step does not apply vision/accuracy penalties. |
| Q6 | Last-known glyph | **Resolved 2026-09-04** — dim `r` (not the sound symbol). Live in-LOS is bright `r` only. |
| Q7 | Sound glyph | **Resolved 2026-09-04** — one `?` for real movement and rain/wind false alarms. |
| Q8 | Mud | **Resolved 2026-09-04** — **mud** is its own open terrain (prints). **Open grassland** is a separate see-through floor (no prints). Long grass and bush still take no prints. |
| Q9 | Adjacency / hunter step | **Resolved 2026-09-04** — Chebyshev 1 **and** hunter in the raptor’s FOV → instant swallow. Adjacent but not in raptor FOV (e.g. behind it) → hunter safe. |
| Q10 | Practice dummy entry | **Resolved 2026-09-04** — main menu **Training Mode**. No name entry in the product. Training skips weapon select (default rifle); F2 menu includes dummy commands **and** on-the-fly weapon swap. Unrecorded (D7). |
| Q11 | Dummy loops | **Resolved 2026-09-04** — see D7b. Not a remaining question. |
| Q12 | Projectile | **Resolved 2026-09-04 (KDVR default)** — glyph `*`, cyan `(0, 255, 255)`, 1 frame per tile, 0.024s per frame. Hunt **time pauses** during the flight (no AUT, no raptor act, tank keys ignored). Resolve is the existing deterministic hit when the dart arrives. |
| Q13 | Game-over modal | **Resolved 2026-09-04** — **every** ending: digest GAME OVER, time-over win/loss, and tranq **results** (bask stays a frozen map first). |
| Q14 | Belly world | **Resolved 2026-09-04** — **black screen**. `#` ring around the **raptor’s map position**; camera follows. Not a ring glued to console center. |
| Q15 | Belly walk | **Resolved 2026-09-04** — each wasted turn: **50%** no move, **50%** a random walkable step; hunter rides; camera follows. |
| Q16 | Rain wav | **Resolved 2026-09-04** — `Sounds/LightRain.mp3`, `MediumRain.mp3`, `HeavyRain.mp3` (10 min each). All three play; one at 100%, others at 0%; weather change is a smooth crossfade. Each track self-crossfades when it loops. |
| Q17 | Raptor mind | **Resolved 2026-09-10** — Stub feel. Full hunt is D16–D20: heatmap, staged stalk/ambush, sidestep, gait AUT, rain vision, center bullseye, emergency rush. |
| Q18 | Right panel | In-sight raptor block includes fuzzy **Health**: Perfect 100; Steady 75–99; Rattled 50–79; Wavering 25–59; Weary 0–24. Overlaps keep the last shown label. |
