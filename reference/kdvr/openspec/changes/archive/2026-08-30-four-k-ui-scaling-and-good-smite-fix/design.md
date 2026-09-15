# Design: 4K UI scaling + good Smite ally fix

## Resolved decisions

| Topic | Decision |
|-------|----------|
| 4K scale factor | **2× effective `tile_scale`** (stock 2 → 4). Standard 1080p→4K linear UI compensation (AAA/MMO-style ~200% UI scale), not 4×. |
| Default | **Off**. Missing `settings.json` key → Off. |
| Options label | `4K UI scaling` with Off/On like Fullscreen. |
| Hotkey | **F10** toggles 4K UI scaling globally (any phase); same live-apply + persist as Options. |
| Apply path | Multiply after layout load (`attrs.evolve`); do not edit stock JSON default. |
| Live toggle | Reload baseline → **`enforce_minimum_window_size`** (grow window if below new floor) → resize console + **reload log font**. Avoids console larger than window (top-left clip / Options looking uncentered). |
| New Game / Load | Must use `layout_for_preset(..., four_k_scaling=settings.four_k_scaling)` — never raw `load_ui_layout` alone. Also `_prepare_run_console` runs the F10 apply path so maximized/fullscreen starts correctly without toggling F10. |
| Smite bug | Chase `entity_target` in follow mode is the player; `_engagement_target_for_chase` returned it blindly. |
| Smite fix | Only keep `entity_target` if smite-legal **and** alignment-hostile (reuse/generalize Path `shooter_can_damage`). Else `pick_*_smite_target`. No entity-id branches. |
| Priest id | Stock ally is **`sheep_cleric`**, not `priest`. |
| Depth-1 playtest | Temporary spawn widen in PR2; **restore 12–14** (done early with PR3 per designer; still gated before archive). |
| PR order | PR1 Smite fix → PR2 temp depth-1 → PR3 4K option (+ early spawn restore) → PR4 accept/archive. |

---

## 4K UI scaling

### Why 2× (not 4×)

A 4K panel (3840×2160) has ~2× pixels per axis vs 1080p. Games whose UI was authored for ~1080p typically expose ~200% UI scale (or a “4K UI” checkbox that does the same) so text/chrome keep similar physical size on a same-size monitor. Quadrupling linear scale (4×) would be oversized for that reference.

### Data / settings

- Field: `four_k_scaling: bool` on `SettingsStore` (top-level, with vore/ui prefs).
- Load: `bool(data.get("four_k_scaling", False))`.
- Save: include in `to_dict()`; `set_four_k_scaling` persists immediately.

### Layout apply

All glyph/log sizing already uses `layout.tile_px * layout.tile_scale`. Hook after `load_active_layout` / `reload_baseline_from_settings`:

```text
if settings.four_k_scaling:
    layout = attrs.evolve(layout, tile_scale=layout.tile_scale * 2)
```

### Options + App

- Insert row near Fullscreen; bump `option_row_count()`.
- On toggle: save setting → reload layout baseline → `resize_app_console` → reload `LogFontState` with new `tile_scale`.

### Min-window caveat

`DESIGN_PIXEL_*` floor is absolute pixels. Larger cells reduce cell count for the same window; if chrome minimums fight the floor, scale the design pixel floor with effective cell size when 4K is on (preferred) or document that 4K mode expects a large display.

### Files (expected)

- `src/settings_store.py`
- `src/options_menu.py`
- `src/ui/bootstrap.py` and/or layout load helpers
- `src/app.py` (toggle apply + font reload)
- `src/main.py` if first-load font path needs the same effective scale
- `openspec/specs/ui-layout/spec.md`
- Tests: settings default/missing key; options row; layout evolve when flag on

### Past-version

Additive optional bool; missing → False. No autosave migration.

---

## Good Smite vs player

### Call chain

```text
pick_good_chase (no evil) → (player, None, "follow")
  → try_smite_engagement(..., entity_target=player)
    → _engagement_target_for_chase  # BUG: returns entity_target raw
      → perform_npc_smite_attack(player)
```

Path engagement already rejects non-hostile targets via `shooter_can_damage` in `src/systems/ranged_path.py`. Smite must match that policy.

### Fix detail

In `src/systems/abilities.py` `_engagement_target_for_chase`:

1. If `entity_target` is not None **and** `_can_smite_target(...)` **and** shooter may damage that target (shared helper or `shooter_can_damage`), return it.
2. Else fall through to `pick_evil_smite_target` / `pick_good_smite_target`.

Optional hardening: assert/guard in `perform_npc_smite_attack` that good cannot damage player (defense in depth). Prefer single shared hostility helper to avoid drift.

### Tests

- Good Smite + LoS player @ dist 2..N, no evil → `try_smite_engagement` False / no player HP loss / no “smites you”.
- Same setup + evil in range → smites evil.
- Evil Smite vs player still works (no regression).

### Files (expected)

- `src/systems/abilities.py`
- Possibly small extract/share with `src/systems/ranged_path.py`
- `tests/test_npc_abilities_smite.py` (extend)
- Spec note under npc-abilities / enhancements good-combat rules if not already explicit for ranged

---

## Temporary depth-1 `sheep_cleric`

### PR2 only

In `data/entities.json` → `sheep_cleric.spawn`: set `min_depth` to **1** (keep `max_depth` 14 or as agreed) so good quota on depth 1 can pick the cleric.

### PR4 restore

Restore `"min_depth": 12`, `"max_depth": 14`, `weight: 1` before archive. Hard release gate.

Do **not** encode temporary depths in live permanent specs; tasks + checklist only.

---

## Performance

- 4K: larger tiles → fewer cells → generally **less** console work; font atlas may be larger — acceptable.
- Smite: one extra hostility check per engagement attempt — negligible.
