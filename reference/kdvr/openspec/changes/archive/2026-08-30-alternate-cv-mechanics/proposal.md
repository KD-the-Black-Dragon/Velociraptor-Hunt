# Proposal: Alternate CV Mechanics + NPC Dazed

**Status:** Active  
**Change id:** `alternate-cv-mechanics`  
**Extends:** `openspec/specs/vore/spec.md`, `openspec/specs/digestion/spec.md`; Options/settings; `depth_scaling`; new **Dazed** NPC status

## Why

A player requested an optional **Alternate CV** mode: CV stays narratively CV, but player struggles deal **no** damage (escape chance unchanged), and a successful player **CV escape** or finishing an **NPC via CV digestion** leaves the predator **dazed** for a data-driven turn range.

With the setting **Off**, CV must behave exactly as it does today (same as other vore types).

## What

1. **Options** — **Alternate CV Mechanics**: **No** / **Yes** (default **No**; missing/null → No). Snapshotted onto the run at **New Game** (like vore prefs / difficulty); mid-run Options changes do not affect the current run.
2. **Per-difficulty knobs** in `data/depth_scaling.json`: `cv_daze_min_turns` / `cv_daze_max_turns` (stock **5** / **5** on every difficulty). Inclusive RNG when applying daze. Omit on a profile → default 5/5 (mod-friendly).
3. When Alternate CV is **Yes** and `Predator.narrative_type == "CV"`:
   - Player struggle → **0** damage; escape chance / fail increments unchanged.
   - Player escapes CV → predator gains **Dazed** for a rolled duration.
   - Predator finishes digesting an **NPC** via CV → predator gains **Dazed** for a rolled duration.
4. **Dazed** (NPCs only): blue tile background; skip AI turn and decrement by 1; at 0 clear and log off; FOV-gated on/off messages; persist in saves. Stacking: new applications **add** rolled turns onto remaining daze.

## Out of scope

- Changing OV/AV, or Alternate-CV-Off CV
- Player being dazed
- NPC prey struggle
- New narrative / modal copy for Alternate CV
- Daze on player digestion game-over

## Success

- Off: no observable CV behavior change
- On + CV: zero struggle damage; escape still works; daze on CV player escape and CV NPC digest-complete with correct messages/render/AI skip
- On + OV/AV: normal struggle damage; no escape/digest daze from those types
- Old saves: missing setting → No; missing Dazed → fine

## Phased delivery

See `tasks.md`.
