# Proposal: Endosoma-friendly post-swallow

| Field | Value |
|-------|--------|
| **Change** | `endosoma-friendly` |
| **Status** | Accepted 2026-09-14; archived `openspec/changes/archive/2026-09-14-endosoma-friendly/` |
| **Depends on** | Hunt loop live; deferred pack archived `2026-09-12-hunt-deferred` |
| **Live specs to extend** | `openspec/specs/hunt/spec.md` |
| **Canon** | Archive hunt canons plus this folder’s `DESIGN_CANON.md` |

---

## Why

The hunt’s default loss is **swallow then digest** (heat, crushing, digestion copy).
Some players want the same mechanical loss — the raptor **has you**, the hunt is
over — but a **containment / victory-strut** reading instead of digestion horror.

That stance is an **Options** preference, not a second win condition. Digest
stays the default. Endosoma only changes **labels and loss presentation**, not
adjacency, belly length, or scoring.

---

## What

1. Options row **Post-swallow**: **Digest** (default) and **Endosoma**.
   Persists immediately. Live at loss/Stats time.
2. **Digest:** current swallow lines, belly darkening, digest modal, GAME OVER
   *You were swallowed and digested.*, Stats **Times digested**.
3. **Endosoma:**
   - Own data-driven swallow-angle path pools.
   - Same belly carry, **no glyph darkening**.
   - Own post-belly path pool (strut / colleagues-will-laugh).
   - GAME OVER *The raptor got you.*
   - Stats **Times swallowed** (same `digested` counter).
4. Path pick: session shuffle bag (see once each, then reshuffle; not saved).
5. Hide leftover **OV/CV/AV** Options rows and the first-run vore-prefs
   screen **for everyone**; keep that code for a later type revival. Hunt
   MVP is oral.

---

## Success criteria

- Default install plays identically to today (Digest), minus hidden unused
  vore-type toggles / onboarding.
- Flipping to Endosoma never changes hunt rules — only presentation and
  the Stats wording for that counter.
- Authors can add another path in JSON and see the session bag use it.
- Old `settings.json` without `post_swallow` behaves as Digest.

---

## Out of scope

- New hunt mechanics, escape-from-belly, or a non-loss endosoma ending.
- Deleting vore-type modules (hide only).
- Balance, raptor mind, rain, or deferred hunt items.
- README/help rewrite until Q8.

---

## Risks

- Skipping vore-prefs onboarding must not strand old flags or break tests
  that boot through that phase — update those tests in PR1.
- Shuffle bags must not be written into autosave (E12 / E13).
