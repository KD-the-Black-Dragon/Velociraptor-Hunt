# Design: Endosoma-friendly post-swallow

Implementation detail for `openspec/changes/endosoma-friendly/`. Behavioral
law lands in `openspec/specs/hunt/spec.md` with the PR. Locked intent:
`DESIGN_CANON.md` in this folder.

Do **not** implement until the designer authorizes the named PR.

---

## Intent

Post-swallow is a **presentation stance**:

| Stance | Meaning |
|--------|---------|
| **Digest** (default) | Current game. Heat, digestion copy, belly glyphs darken, **Times digested**, GAME OVER *You were swallowed and digested.* |
| **Endosoma** | Same loss. Capture and containment. Own swallow lines. Belly with **no** glyph darkening. Raptor struts. Hunter is mortified. Colleagues will laugh. Stats say **Times swallowed**. GAME OVER *The raptor got you.* |

The hunt is still over. No struggle-out, no “safe vore” continue.

---

## Options

### Post-swallow row

Same chrome as Difficulty / Fullscreen:

```text
Post-swallow:  [Digest] ► Endosoma
Post-swallow:  Digest ► [Endosoma]
```

**Placement:** after **Difficulty**, before **Fullscreen**.

**Persistence:** `settings.json` key `post_swallow`: `"digest"` | `"endosoma"`.
Missing or invalid → `"digest"`. Write immediately on change.

**When it applies (E13):** read the **live** setting when composing swallow
lines, belly fade, post-belly modal, GAME OVER, and when drawing Stats.
Not stored on the hunt autosave.

### Hide donor vore-type rows (E14)

Do **not** show Oral Vore / Cock Vore / Anal Vore on Options. Drop them
from the highlight list so Up/Down never lands on hidden rows.

Skip first-run **vore prefs onboarding** (the screen that toggles OV/CV/AV).
After the tutorial prompt, go to the menu. Keep
`src/ui/vore_prefs_onboarding.py` and `SettingsStore.vore_content` /
`vore_prefs_onboarding_complete`. On boot, if that flag is false, **mark
it complete** (or treat hidden-UI as already complete) so old installs
do not trap players on a screen they can no longer reach. Do not delete
the module.

Hunt content is **OV** for now. Storage may still list CV/AV enabled;
nothing in the hunt loop reads those flags.

---

## Stats

- Persisted field remains `digested` on each difficulty board.
- Outcome string for a raptor swallow win stays `"digested"` internally.
- Label **Times digested** vs **Times swallowed** follows the **live**
  Options stance. Switching does not rewrite history.

---

## Loss sequence (same shape)

Swallow modal → playable belly → post-belly narrative modal → GAME OVER
→ main menu.

| Stage | Digest | Endosoma |
|-------|--------|----------|
| Swallow modal | Current `swallow_front` / `_side` / `_behind` | Matching **endosoma** swallow-angle **path** from JSON |
| Belly | Current void, carry, glyphs darken | Same carry / void; **glyphs do not darken** |
| Post-belly modal | One **digest path** from the session bag | One **endosoma path** from the session bag |
| GAME OVER | `GAME OVER` + `You were swallowed and digested.` | `GAME OVER` + `The raptor got you.` |

---

## Data: narrative paths

```json
{
  "belly_turns": 6,
  "belly_step_chance": 0.5,
  "swallow_front": [ "…" ],
  "swallow_side": [ "…" ],
  "swallow_behind": [ "…" ],
  "endosoma_swallow_front": [
    [ "Clever girl.", "She takes you in one gulp — show, not supper." ]
  ],
  "endosoma_swallow_side": [
    [ "A blur at your flank.", "Folded up. Displayed. Not dinner." ]
  ],
  "endosoma_swallow_behind": [
    [ "It was behind you.", "The paddock hears a smug swallow. You are a prize." ]
  ],
  "digest_paths": [
    [
      "Heat. The walls of flesh tighten.",
      "The hunt is over. You are being digested."
    ]
  ],
  "endosoma_paths": [
    [
      "She has you. The belly is a trophy case, not a furnace.",
      "The raptor struts the paddock, immensely pleased with herself.",
      "You can already hear the radio: they are never going to let this go."
    ]
  ]
}
```

**Loader rules:**

- Digest swallow keys stay **one sequence per angle** (today’s shape).
- Endosoma swallow keys are **pools of paths** per angle (list of list of
  lines). One path is one modal’s lines. Ship at least one path per angle.
- `digest_paths` / `endosoma_paths`: same, for the post-belly modal.
  Empty pool is a load error.
- If a leftover top-level `"digest": [ … ]` exists and `digest_paths` is
  missing, treat that array as a single digest path.

**Placeholder Endosoma lines above are drafts (Q7).** Designer rewrites
before or during the PR. Code must not hardcode those sentences.

---

## Session shuffle bag (E12)

In-memory, process-lifetime (held on `App` or a tiny helper owned by App,
**not** the hunt autosave, **not** `settings.json`):

- One bag per pool id, e.g. `digest_paths`, `endosoma_paths`,
  `endosoma_swallow_front`, `endosoma_swallow_side`,
  `endosoma_swallow_behind`.
- Draw: if the bag is empty, fill it with a shuffle of that pool’s
  indices; pop one. Next loss of the same pool cannot repeat until every
  path has been shown, then reshuffle.
- Single-path pools always draw that path (shuffle of one).
- New Hunt / Training / Continue Hunt **do not** reset bags. **Process
  exit** does.

---

## Belly fade (E10)

`belly_fade_t` still exists. When composing the overlay, Endosoma forces
`t = 0` (start colors). Digest uses the current turn-based lerp. Do not
fork a second overlay renderer.

---

## Code touchpoints (when authorized)

| Area | Notes |
|------|--------|
| `src/options_menu.py` | Hide `VORE_OPTION_ROWS` from nav/render; add Post-swallow cycle |
| `src/settings_store.py` | `post_swallow`; load default; setter |
| `src/app.py` | Skip vore-prefs onboarding; own shuffle bags; pass live stance into hunt/stats |
| `src/ui/vore_prefs_onboarding.py` | Keep file; unused on the happy path |
| `data/hunt_loss.json` | Pools as above |
| `src/hunt_loss.py` | Load pools; draw from a bag |
| `src/hunt_session.py` / `hunt_modals.py` | Stance for swallow lines, fade, post-belly, GAME OVER |
| `src/hunt_stats.py` | Label from live stance |
| `src/messages.py` | Endosoma GAME OVER second line |
| Tests | Options persist; hidden vore rows; skipped onboarding; default Digest copy; Endosoma label/lines/no-fade; bag cycles; JSON migration |

Hunt session may read a callback `post_swallow()` so Continue Hunt +
Options stay live without snapshotting onto the save.

Keep `HuntMode.DIGEST` as the post-belly modal mode name.

---

## What this does **not** change

- Adjacency swallow rule, belly turn count, 50/50 carry, hidden paddock.
- Tranq / time-over GAME OVER boxes.
- Stats JSON schema (except settings).
- Donor vore-type **code** and saved `vore_content` object.

---

## Performance

Trivial: one settings string, tiny in-memory bags, `t = 0` on Endosoma
belly. No per-frame cost beyond today’s overlay.

---

## Open questions

Q7 (copy) and Q8 (README/help) in `DESIGN_CANON.md`. Do not invent shipping
prose beyond the placeholders without designer rewrite.
