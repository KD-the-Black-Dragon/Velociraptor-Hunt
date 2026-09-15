# Proposal: Velociraptor Hunt (project identity)

| Field | Value |
|-------|--------|
| **Change** | `velociraptor-hunt` |
| **Status** | Accepted 2026-09-04 (PR1–PR11 playtested) |
| **Depends on** | Donor snapshot (this folder’s Gladiavore copy + `reference/kdvr/`) |
| **Live specs to extend** | `openspec/specs/hunt/spec.md` (landed with PR10) |
| **Canon** | `DESIGN_CANON.md` in this folder |

---

## Why

This folder is a **copy of Gladiavore** (itself a KDVR spinoff). The originals are
safe elsewhere. The designer wants a **new, small-scope roguelike** here:

A hunter in a Jurassic Park–type park, going after a velociraptor that is going
after them — weather, obscuring terrain, and an animal that is **too clever**, in
the spirit of Muldoon’s “clever girl” scene.

Without a written identity change, agents will keep treating this tree as
Gladiavore (career, arena, Battle Sport) or KDVR (dungeon floors).

---

## What

1. **Product name:** Velociraptor Hunt.
2. **Form:** 7DRL-shaped — **one hunt**, not many floors, not a career campaign.
3. **Fantasy:** tank-facing hunt in the rain; **tranq vs swallow**; raptor
   plays **fair** with senses and **profiles habits**; failure is **pounce and
   devour** with spectacle.
4. **Engineering:** harvest libtcod/ECS, FOV, input, log, save, and vore hooks
   from the donor copy. Do not ship the Gladiavore hub/match loop as the game.
5. **This change:** lock identity, pillars, and a **PR slice plan**.
   Implementation still waits for designer authorization of a **named PR**.

---

## Success criteria (docs / concept)

- `AGENTS.md`, `README.md`, and lineage docs say **Velociraptor Hunt**, and say
  Gladiavore/KDVR are donor/originals elsewhere.
- Open questions are listed instead of invented mechanics.
- No hunt code is written until a named PR is authorized.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Agents keep implementing Gladiavore PRs | Current-change pointer; donor folders labeled historical |
| Scope balloons into a park sim / campaign | 7DRL non-goals in `design.md` |
| Invented raptor AI / weather systems | Open questions; do not invent gameplay |
| Triple editable-install mix-up (`src` package) | Harvest doc warning |
