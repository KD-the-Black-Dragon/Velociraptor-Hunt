# Tasks: 4K UI scaling + good Smite ally fix

**Change id:** `four-k-ui-scaling-and-good-smite-fix`  
**Rule:** One PR at a time. Do not implement until the user authorizes that PR by name.

---

## PR1 — Good Smite does not attack the player

- [x] Gate `_engagement_target_for_chase` / Smite engagement so `entity_target` is kept only when smite-legal **and** alignment-hostile (reuse/generalize Path `shooter_can_damage`; no entity-id branches)
- [x] Regression tests: good Smite + follow/player in range, no evil → no player smite; evil in range → smites evil; evil Smite vs player still works
- [x] Spec touch if needed (good must not ranged-attack player)
- [x] Targeted pytest for touched tests (`-n 4` if multi-file)
- [x] Manual checklist in chat + `testing-checklist-pr1.md`

## PR2 — Temporary depth-1 sheep cleric (playtest aid)

- [x] Widen `sheep_cleric.spawn` so depth **1** is eligible (keep weight data-driven; no Python hardcoding)
- [x] Note in checklist: New Game / new floor required; restore happens in PR4
- [x] Manual checklist in chat + `testing-checklist-pr2.md`

## PR3 — Options: 4K UI scaling (default Off)

- [x] `SettingsStore.four_k_scaling` default **False**; missing key → False; persist + setter
- [x] Effective `tile_scale *= 2` when enabled (after layout load)
- [x] Options row `4K UI scaling` Off/On; live apply (layout reload, resize, **log font reload**)
- [x] Min-window / design-pixel floor handled so chrome still fits when On
- [x] Update `openspec/specs/ui-layout/spec.md` (and settings/options docs if present)
- [x] Tests: missing key; toggle evolves scale; options row
- [x] Targeted pytest
- [x] Manual checklist in chat + `testing-checklist-pr3.md`
- [x] **F10** global hotkey toggles 4K UI scaling (same live-apply + persist; help/spec updated)

## PR4 — Restore cleric spawn + acceptance / archive

- [x] Restore `sheep_cleric` spawn to **min_depth 12 / max_depth 14** *(done early with PR3 per designer)*
- [x] Designer sign-off on Smite + 4K
- [x] Full pytest procedure (`tests/ -n 4`) per AGENTS.md *(step 8 interrupted; live-data content tests recycled)*
- [x] Archive change; clear `AGENTS.md` active pointer
- [x] `testing-checklists.md` / `acceptance-report.md` as required

---

## Manual testing pointers

| PR | Focus |
|----|--------|
| PR1 | Ally with Smite near player, no enemies: must **not** smite you; with evil in range: smites evil |
| PR2 | New run depth 1: sheep cleric can appear (quota / luck); use to verify PR1 |
| PR3 | Options Off = current look; On = larger UI; survives restart; old settings without key stay Off |
| PR4 | Confirm cleric no longer depth-1; release package must not include temp spawn |
