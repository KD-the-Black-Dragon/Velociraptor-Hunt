# Proposal: Gladiavore foundation (project rebirth)

## Problem

This repository is a **safe clone** of **K.D.'s Vore Roguelike (KDVR)** — a dungeon-crawl roguelike with bump combat, multi-floor exploration, and relatively fast vore resolution. The designer is building a **new game**, **Gladiavore**, in this folder.

Gladiavore is not a reskin of KDVR. It needs:

- A **career** loop (WWAATD-inspired) with downtime, economy, roster, and ranked matches
- **Curated arena** combat that feels like a short tactical fight (staredown, shield work, openings), not dungeon bump-spam
- **Stamina-like HP**, separate **injuries**, and **digestion-only** permanent removal for the PC
- **Grapple/vore as a multi-turn crisis**, not a single dice roll
- Clear **product identity** (name, user data, docs) so agents and players never confuse the two games

Without a foundation change, work will either stay trapped in KDVR assumptions or reinvent systems that already exist under the wrong fiction.

## Solution

Open a long-lived OpenSpec change **`gladiavore-foundation`** that:

1. Locks **design pillars**, non-goals, and the **MVP → ambition** ladder.
2. Defines the **career + match + downtime** loop and green/red risk model.
3. Defines the **combat philosophy** (balance meter from actions, ability points, abilities, talk orders, vulnerability states) even where v1 only stubs numbers.
4. Defines **re-identity** and a **KDVR reference** strategy so reusable systems are harvested without treating the tree as “still KDVR.”
5. Plans **PRs** that rebrand first, then hub shell, then match slice, then deepen combat/vore — **one authorized PR at a time**.

## Product summary

| Item | Detail |
|------|--------|
| **Name** | Gladiavore |
| **Form** | Career roguelike; 7DRL-shaped interface (ASCII/libtcod, turn-based, top-down, roguelike keys) |
| **Inspirations** | *We Who Are About To Die* (career, training, patrons light), *Battle Brothers* (named allies, serious injuries), DCSS (ability/talk UX patterns) |
| **Combat feel** | Tactical gladiator bouts in **small curated arenas**; every turn ~few seconds of fight time |
| **Fetish core** | Predators may engulf and digest fighters in **red** matches; PC never vores; some allies may be vore-capable |
| **PC removal** | Digested only (typical red loss). 0 HP = stunned/exhausted, never lethal |
| **Engine lineage** | Python 3.11+, libtcod, light ECS — harvest KDVR systems where appropriate |

## Scope

### In scope (this change)

- Full design record (this folder): pillars, loop, combat skeleton, vore/grapple direction, economy, roster, patrons stub, renown-as-score
- **PR plan** for rebrand, hub, match vertical slice, combat skeleton, grapple-vore v1
- Living **Resolved decisions** table
- Guidance for specs that will eventually live under `openspec/specs/` as features land
- KDVR reference documentation for agents (`KDVR_REFERENCE.md` at repo root when PR1 lands, or earlier as design-adjacent doc)

### Out of scope (unless designer expands later)

- Full WWAATD feature parity (deep patron politics, city sim)
- Dwarf Fortress–level simulation
- PC-initiated vore
- Large procedural dungeons as the primary mode
- Finishing KDVR balance-pass or shipping KDVR content as the product
- Implementing combat depth beyond what each authorized PR lists

## Success criteria

- Designer accepts `proposal.md` / `design.md` / `tasks.md` as the foundation
- Product is clearly **Gladiavore** in identity docs and (after PR1) in runnable branding
- First playable vertical slice is defined well enough that implementers do not invent core rules
- Ambition systems (balance meter, grapple vore, injuries, patrons) are **specified enough to stub** without painting into a corner
- No code ships without explicit authorization of a named PR

## Relationship to KDVR

| | KDVR (original, safe elsewhere) | This repo → Gladiavore |
|--|----------------------------------|-------------------------|
| Fantasy | Dungeon crawl | Gladiatorial career + arena matches |
| Space | Procgen multi-floor | Curated arenas + downtime hub |
| Combat | Bump-centric | Tactical actions, openings, specials |
| Vore | Fast attempt → swallow on roll | Grab → multi-turn grapple crisis |
| HP | Fight until stun → digest path | Stamina/will; injuries separate |
| Fate | Digested ends run | Same for PC on red; allies permanent loss |

**Reuse policy:** Prefer harvesting combat/FOV/UI/save plumbing/JSON pipelines over greenfield rewrites. **Do not** preserve dungeon-delve as the default game loop. Eventually remove residual KDVR-only assets; until then, document what is reference vs live.

## Related

| Artifact | Role |
|----------|------|
| `design.md` (this change) | Full design + PR plan + resolved decisions |
| `tasks.md` (this change) | Authorization-gated PR checklists |
| `KDVR_REFERENCE.md` (root; create with re-identity) | How agents treat the clone lineage |
| `openspec/changes/balance-pass/` | KDVR-era change — **superseded / do not continue** as product work |
| Clone `src/`, `data/`, tests | Harvest pool, not product truth |

## Non-goals for “done soon”

Foundation is **design-complete when the designer says so**, then implemented **PR by PR**. This is not a one-week forced 7DRL calendar unless the designer later imposes one; it is **in the spirit of** short, sharp roguelike matches with an ambitious combat fantasy.
