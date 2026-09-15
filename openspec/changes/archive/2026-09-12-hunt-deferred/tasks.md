# Tasks: Hunt deferred follow-through

**Do not implement any PR until the designer names it.** Canon addendum and
open questions: `DESIGN_CANON.md`. Slice notes: `design.md`.

Foundation (PR1–PR11) is archived; do not reopen it. Do **not** pick up
leftover Gladiavore PRs.

---

## PR0 — Open this change (docs)

- [x] `proposal.md`, `design.md`, `tasks.md`, `DESIGN_CANON.md`
- [x] Point `AGENTS.md` and `openspec/config.yaml` at `hunt-deferred`
- [x] Dependency-based PR order (not mention order)
- [x] Designer reviews grouping / answers blocking Qs for the first code PR

---

## Q&A (before the PR that needs it)

Not all questions block PR1. Answer when that PR is next.

- [x] **Q9** adjacency — Chebyshev 1 **and** hunter in raptor FOV (D14); behind the raptor is safe
- [x] **Q6, Q7** last-known dim `r`; one sound `?`
- [x] **Q8** mud vs open grassland vs long grass; prints only on mud
- [x] **Q4, Q5** playtest JSON stacks; R toggle is not fatigue
- [x] **Q1, Q2, Q3** aim off-center (before **PR7**)
- [x] **Q12** projectile timing (before **PR8**; KDVR default OK if designer says so)
- [x] **Q13, Q14, Q15** loss spectacle (before **PR9**)
- [x] **Q10** how the player **starts** practice dummy (before **PR10**). F2 menu and loops are locked (D7b).
- [x] **Q16** rain wav files (before **PR11**; skip PR if no files)
- [x] **Q17** raptor mind playtest notes (before **PR12**) — stub feel; D16. Tempo numbers still open in the PR12 section.
- [x] **Q18** right-panel raptor block — Velociraptor / Distance / Facing[!] / State (PR2)

---

## PR1 — Ctrl sidestep (NumLock-safe)

Tiny, isolated. Unblocks later tank playtests.

- [x] Sidestep is **Ctrl+4/6** only (numpad and Ctrl+G / Ctrl+J / Ctrl+arrows)
- [x] Shift is **not** a sidestep modifier
- [x] Unshifted numpad 4/6 rotate with NumLock on or off
- [x] Targeted tests + `testing-checklist-pr1.md`

## PR2 — Right-side hunt panel

HUD home. **Absorbs** “relative score always on-screen.”

- [x] Right column: clock, 3-state ring, in-sight raptor facing (Q18 extras not in this PR)
- [x] Footer no longer the home for score / raptor info
- [x] Targeting factors and ammo in the panel (not the default footer)
- [x] Targeted tests + `testing-checklist-pr2.md`

## PR3 — Raptor win on adjacency

Loss **rule** before spectacle. **Q9 resolved** (D14).

- [x] Instant swallow only if Chebyshev 1 **and** the hunter is in the raptor’s own FOV (`sees`)
- [x] Adjacent but not in raptor FOV (e.g. behind it) does **not** finish the hunter
- [x] Check after hunter move, raptor move, and raptor facing change (do not wait for the next raptor turn)
- [x] No separate melee-commit action
- [x] Swallow angle still front / side / behind from the actual geometry
- [x] Targeted tests + `testing-checklist-pr3.md`

## PR4 — Map tells (last-known + sounds as one symbol)

Needs **Q6, Q7**.

- [x] Last-known mark: never / live / last-known only (erase when seen again, or when FOV shows the tile empty)
- [x] One shared sound glyph for real movement and rain/wind false alarms
- [x] No bottom-line “Movement N / Rain in the canopy / Wind from the SE”
- [x] Hunt snapshot: last-known tile (additive)
- [x] Targeted tests + `testing-checklist-pr4.md`

## PR5 — Mud prints (always, mud only, per-print rain TTL)

Needs **Q8**.

- [x] Prints on mud steps always (hunter and raptor), not grass/bush
- [x] Each print stores rain-at-stamp; heavier rain → longer individual life
- [x] Expire per print, not by the current rain’s global TTL
- [x] Snapshot additive defaults
- [x] Targeted tests + `testing-checklist-pr5.md`

## PR6 — Run fatigue, not run-mode cone

Needs **Q4, Q5**. Amends archive #24 / #57 vision part.

- [x] Run **mode** does not shorten the cone
- [x] Run **steps** apply a decaying fatigue stack (vision + accuracy)
- [x] Values in JSON; targeting factors can mention fatigue loosely
- [x] Run still clears aim; run + sidestep/back still drops to walk
- [x] Targeted tests + `testing-checklist-pr6.md`

## PR7 — Aim off-center

Needs **Q1, Q2, Q3**. After fatigue so cones compose.

- [x] Aim heading may sit off the 8 tank ticks
- [x] Hunter can see / confirm what the cone actually covers (pick from current FOV)
- [x] FOV and fire line use aim heading
- [x] Not a return to tile-reticle aim (archive #23) — pick sets a heading/cone
- [x] Targeted tests + `testing-checklist-pr7.md`

## PR8 — Visible projectile

After the real aim line. **Q12** or KDVR timing default.

- [x] Dart travels along the shot line, then the existing deterministic resolve
- [x] Harvest KDVR projectile-anim **pattern** into hunt code (no `reference` import)
- [x] Targeted tests + `testing-checklist-pr8.md`

## PR9 — Loss spectacle (belly + vore modals + game-over)

One sequence. Needs **Q13–Q15**. After PR3 so the finish is adjacency.

- [x] Swallow / digest as KDVR-style centered modals (not map overlay text)
- [x] Belly `#` uses KDVR engulf color `(100, 20, 20)`
- [x] Camera locked to the hunter-in-belly tile (raptor tile; follows the pair)
- [x] Raptor walks a little during belly and carries the hunter (50/50)
- [x] Final game-over is a centered modal (all endings; tranq bask first)
- [x] Belly still/move still waste the turn; meta OK
- [x] Targeted tests + `testing-checklist-pr9.md`

## PR10 — Practice dummy

Needs **Q10** (entry path only). After clues / fatigue / aim so it can
verify them. Behavior list is locked (D7 / D7b / D7c).

- [x] Custom arena, **identical** every session (open ground + long grass + teleport anchors)
- [x] Separate mode; F2 opens the command menu **in this mode only**
- [x] F2 commands: walk back and forth (teleport); stand still in long grass (teleport); stand still in open (teleport); stop moving (no teleport); cancel stop (resume, no teleport); seek/chase ASAP; gait sneak/walk/run; normal behavior
- [x] F2 loadout: swap rifle / shotgun / revolver on the fly
- [x] Tranq / clock / swallow wins and losses work
- [x] Same D14 rule as live hunt (adjacent **and** in raptor FOV)
- [x] Outcomes not recorded (no stats, no abandon, not Continue Hunt)
- [x] Targeted tests + `testing-checklist-pr10.md`

## PR11 — Rain wav layers

**Asset-gated** (Q16). Skip and leave the fade stub if files are not in tree.

- [x] Three concurrent beds (light / medium / heavy); weather swaps are a wall-clock crossfade
- [x] Each bed self-crossfades at the 10-minute loop so the join is hidden
- [x] No crash if a file is missing
- [x] Targeted tests + `testing-checklist-pr11.md`

## PR12 — Raptor mind dissection

**Last.** **Q17 / D16–D20.** Do **not** invent cheat senses. Includes
supporting AUT, fatigue, rain vision, and live-paddock bullseye so the
mind has terrain and tempo to use.

- [x] Hunter gait AUT: sneak 2× walk; walk 0.8 / quick 0.7 / run 0.4 (D17)
- [x] Fatigue: +1 run step; quick holds; recover 1 per 3 **walk / wait / sneak** (any mix; D18)
- [x] Rain vision: hunter better in light; raptor better in medium; markedly in heavy (D19)
- [x] Live paddock center bullseye: mud middle, grass/open ring; outside still procgen (D20). Training map unchanged
- [x] Raptor tank: forward, back, rotate, **sidestep**; gait on the State line
- [x] Raptor uses the same step AUT as the hunter for its current gait
- [x] Heatmap: occupancy + recent scans; eyes-on or hunter print **resets** it; prints = stale eyes-on
- [x] Sounds (real or false) weighted by heatmap — no obsessive re-check of a just-scanned patch; ignore extras right after a sighting
- [x] Gunshot: always heard, identified as a shot; apparent center jittered then **flat** blur disk (D21)
- [x] Early: max distance, observe from behind. Stare-habit: sneak then sprint when too late to turn. Active hunter: long-grass ambush. Shy if stared back at
- [x] Staredown not aiming: max distance, sidestep circle
- [x] Sees aim: sprint diagonal-away and/or perpendicular
- [x] Raptor-winning: stalk via long grass (not open-center camping)
- [x] Clock emergency: find and rush
- [x] Danger-close: eyes-on and Chebyshev ≤ 4 → run and close ASAP; beats other postures (D23)
- [x] Training **normal behavior** uses this mind; F2 gait override still wins
- [x] Lower-right hunt log, proportional font: notices + raptor thought (D22)
- [x] Targeted tests + `testing-checklist-pr12.md`

**PR12 playtest** is folded into the intelligence pack below. Designer asked
to **batch implementation** and skip per-PR manual tests until the pack is in.

## PR13 — Rifle scope, sounds, glyph priority

Hunter-facing. No raptor-brain rewrite.

- [x] Rifle aim / deep-aim: **line FOV**, longer, **close-blind 3**. Shotgun/revolver cones unchanged (D27)
- [x] Movement sound chance: light 100/67/33/0; medium −10; heavy −20; mark the **from** tile (D34)
- [x] Draw: live `r` > last-known `r` > `?` > terrain (D35)
- [x] Targeted tests + notes in `testing-checklist-pr13.md` (pack playtest is after PR15)

## PR14 — Memory, rain plan, locomotion, stalk, bait

The mind. Fair senses only. Mud crossing / own prints on mud are **allowed** (D30).

- [x] Decaying last-known cone; sweep union of recent facings; aim-line corridor; burned “I was seen here” tiles; leave if the cone is sweeping onto her (D28)
- [x] Rain plan: turtle in light; daring in heavy; conservative **before** light; sit-then-relocate hides; tree for dart, grass for eyes (D29)
- [x] Orbit grass ring, not mud — except **heavy-rain rear rush** if she is confident (D29)
- [x] Diagonal-forward; strafe-first; never pause in remembered LOS; one peek then cut (D31)
- [x] Stalk clock + commit math; heave still breaks cone; **no** ammo/reload tell (D32)
- [x] Fair sound bait (D33)
- [x] Double-step tell: two adjacent heard sounds in a short AUT window collapse heatmap (D37)
- [x] Targeted tests

## PR15 — Hunt difficulty JSON

- [x] `data/hunt_difficulty.json` (or hunt keys on existing difficulties): speeds, rain phase AUT, optional cone, LOS-hot / stalk knobs (D36)
- [x] Nightmare may be numerically unfair; **never** omniscience
- [x] Targeted tests + **pack** `testing-checklist-pr13.md` (one manual playtest for PR13–PR15)

---

## Deferred (later change)

- [ ] **Sound bait (D33)** — `bait_chance` in JSON; idle fake-`?` act not wired
- [ ] **Peek once, then cut (D31 remainder)** — no same-gap-twice memory
- [ ] **Balance pass** — provisional sign-off; more playtest later

---

## Absorbed / not a PR

- [x] **Relative score until panel** — PR2 is the home; footer already shows ring until then
- [x] **Help `?`/F1** and **strip bottom key-hints** — foundation PR10

---

When a PR is authorized: implement **only** that PR, targeted tests, check it
off. For **PR13–PR15** the designer waived per-PR playtest; post the **pack**
checklist after PR15 and wait for sign-off then.
