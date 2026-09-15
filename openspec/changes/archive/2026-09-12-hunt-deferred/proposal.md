# Proposal: Hunt deferred follow-through

| Field | Value |
|-------|--------|
| **Change** | `hunt-deferred` |
| **Status** | PR1–PR12 implemented; **PR13–PR15 raptor intelligence pack** planned (not authorized) |
| **Depends on** | Foundation accepted: `openspec/changes/archive/2026-09-04-velociraptor-hunt/` (PR1–PR11) |
| **Live specs to extend** | `openspec/specs/hunt/spec.md` |
| **Canon** | Archive `DESIGN_CANON.md` plus this folder’s `DESIGN_CANON.md` (amendments + open questions) |

---

## Why

The hunt foundation is playable (paddock, tank, rain, fire, clock, swallow/belly,
stats, autosave). Along the way the designer named a **deferred pack**: clue
language, hunter vision (fatigue + off-center aim), HUD home, loss spectacle,
input bugs, dummy paddock, rain samples, and a later raptor-mind pass.

Those items were recorded in the order they came up in playtest. Implementing
them in that order would redo HUD and loss presentation twice, leave the raptor
winning on the old adjacency rule through most of the pack, and polish a
projectile before the aim line it follows is finished.

This change is the written plan to land **all named deferred items**, grouped
by dependency, **one authorized PR at a time**.

---

## What (named items — not chronological)

| Item | From archive `tasks.md` Deferred |
|------|----------------------------------|
| Ctrl+4/6 sidestep (Shift dropped; NumLock-safe) | Input |
| Right-side hunt panel | HUD home for score + raptor readout |
| Relative score always on-screen | **Absorbed** by the panel (no throwaway footer PR) |
| Last-known raptor mark | Map tell |
| Sounds are map symbols only (one shared “might have been a raptor”) | Map tell |
| Mud prints: always, mud not grass, per-print rain TTL | Clue simulation |
| Run fatigue, not run-mode cone | Hunter vision / accuracy |
| Aim off-center of a 45° facing; confirm what you are aiming at | Hunter vision |
| Visible projectile travel | Fire presentation |
| Raptor win on adjacency + raptor FOV (no melee commit) | Loss **rule**; live hunt and dummy |
| KDVR-exact belly (wall color, camera, raptor walks carrying hunter) | Loss **spectacle** |
| Vore narratives as KDVR modals | Loss spectacle |
| Centered game-over modal | Loss spectacle |
| Practice dummy mode | Fixed custom arena; F2 command menu; W/L enabled but unrecorded |
| Rain audio samples (wav) | Asset-gated |
| Raptor-mind dissection | Last; after the new clues and win rule |

Help `?`/F1 and stripping the bottom key-legend already shipped in foundation PR10.

---

## Grouping (why this order)

See `design.md` for the graph. Short version:

1. **Fix the tank** (NumLock) so later playtests are not fighting input.
2. **Give the HUD a home** (right panel) so score, ring, and raptor info leave
   the two-line footer — and the “relative score until panel” item is done.
3. **Change the loss rule** (adjacency) before polishing swallow/belly, so
   every later eat-playtest uses the real finish.
4. **Rewrite the clue language** (last-known + one sound glyph, then mud TTL)
   as one information-model pass.
5. **Rewrite hunter vision** (fatigue, then off-center aim), then the **dart
   animation** that follows that aim line.
6. **One loss-spectacle PR** (belly + vore modals + game-over modal) — one
   sequence, one playtest.
7. **Dummy paddock** after clues/aim exist, so it can verify them.
8. **Rain wav** when files exist; **raptor mind** last, after adjacency and
   clues, with a Q&A gate so we do not invent new tricks.
9. **Intelligence pack (PR13–PR15)** after PR12: scoped rifle, fair memory,
   rain plan, stalk, difficulty JSON. Designer asked to batch playtest.

---

## Success criteria

- Every named deferred item is either a PR checkbox, explicitly absorbed, or
  asset-gated with a wait condition.
- Live `openspec/specs/hunt/spec.md` is updated as each PR lands.
- No leftover Gladiavore PRs are treated as this work.
- No hunt code until the designer authorizes a **named PR**.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Inventing aim-offset or fatigue numbers | Q&A gates on those PRs; values in JSON after designer says |
| Inventing raptor-mind tricks | Last PR; dissection only of what playtest names |
| Rain wav with no assets | PR waits on files; fade stub stays until then |
| Belly camera vs canon “world hidden” | Recorded as a named amendment; confirm in Q&A |
| Fat PRs | Clues split (glyphs vs mud sim); loss spectacle kept together because it is one player sequence |
