# Manual testing — PR1 Post-swallow / Endosoma

How to run: `python -m src.main`

## Happy path

- [ ] Options has **Post-swallow: [Digest] ► Endosoma** (after Difficulty)
- [ ] Options does **not** list Oral Vore / Cock Vore / Anal Vore
- [ ] Left/Right (or Enter) cycles Digest ↔ Endosoma; Esc back; relaunch keeps the choice
- [ ] **Digest** (default): swallow lines as before; belly glyphs darken; post-belly **The raptor digests you.**; GAME OVER **You were swallowed and digested.**; Stats **Times digested**
- [ ] **Endosoma**: swallow **The raptor swallows you whole.**; belly does **not** darken; post-belly **The raptor enjoys keeping you within her belly for a long time.**; GAME OVER **The raptor got you.**; Stats **Times swallowed**
- [ ] Esc mid-hunt → Options → flip stance → Continue Hunt: later loss / Stats follow the **new** stance
- [ ] Training Mode follows the same Options stance (still unrecorded)

## Edges

- [ ] First launch: tutorial prompt, then menu (no vore-type onboarding)
- [ ] Missing `post_swallow` in old settings.json behaves as Digest
- [ ] Tranq and time-over GAME OVER boxes unchanged
- [ ] Rain, tank, F1 still work

## Pointer

`openspec/changes/endosoma-friendly/tasks.md` (PR1).
