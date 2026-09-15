"""PR2: Alternate CV settings, Options row, depth_scaling knobs, run snapshot."""

from __future__ import annotations

import json
import random

import tcod.console
import tcod.event
from tcod.event import KeySym, Scancode

from src.data.depth_scaling_loader import (
    DepthScalingLoadError,
    default_depth_scaling_config,
    parse_depth_scaling_config,
    reset_depth_scaling_cache,
)
from src.engine import GameEngine
from src.options_menu import (
    ALTERNATE_CV_ROW_INDEX,
    OptionsMenuState,
    format_alternate_cv_mechanics_line,
    handle_options_event,
    option_row_count,
    render_options_menu,
)
from src.settings_store import SettingsStore
from src.systems.dazed import roll_cv_daze_turns
from tests.map_test_helpers import isolate_other_ais


def _key(sym: KeySym) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=0)


def test_option_row_count_includes_alternate_cv() -> None:
    # vore(3) + UI + difficulty + fullscreen + 4K + alternate CV + tutorial + mods
    assert option_row_count() == 10


def test_format_alternate_cv_mechanics_line() -> None:
    assert (
        format_alternate_cv_mechanics_line(False)
        == "Alternate CV Mechanics:  [No] ► Yes"
    )
    assert (
        format_alternate_cv_mechanics_line(True)
        == "Alternate CV Mechanics:  No ► [Yes]"
    )


def test_alternate_cv_row_index() -> None:
    state = OptionsMenuState(highlight=ALTERNATE_CV_ROW_INDEX)
    assert state.on_alternate_cv_row is True
    assert state.on_four_k_scaling_row is False
    assert state.on_tutorial_row is False


def test_settings_alternate_cv_defaults_false_and_missing(tmp_path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore.load(path)
    assert store.alternate_cv_mechanics is False

    path.write_text(json.dumps({"ui_preset": "standard"}), encoding="utf-8")
    loaded = SettingsStore.load(path)
    assert loaded.alternate_cv_mechanics is False

    path.write_text(
        json.dumps({"alternate_cv_mechanics": None, "ui_preset": "standard"}),
        encoding="utf-8",
    )
    # bool(None) is False
    loaded_null = SettingsStore.from_dict(
        {"alternate_cv_mechanics": None, "ui_preset": "standard"}
    )
    assert loaded_null.alternate_cv_mechanics is False


def test_toggle_alternate_cv_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.path = path
    state = OptionsMenuState(highlight=ALTERNATE_CV_ROW_INDEX)
    handle_options_event(state, _key(KeySym.RETURN), settings=settings)
    assert settings.alternate_cv_mechanics is True
    reloaded = SettingsStore.load(path)
    assert reloaded.alternate_cv_mechanics is True
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert settings.alternate_cv_mechanics is False


def test_render_options_shows_alternate_cv_row() -> None:
    console = tcod.console.Console(80, 42, order="F")
    settings = SettingsStore()
    render_options_menu(console, OptionsMenuState(), settings=settings)
    found = False
    for y in range(console.height):
        chars = [
            chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
            for x in range(console.width)
        ]
        if "Alternate CV Mechanics" in "".join(chars):
            found = True
            break
    assert found


def test_stock_depth_scaling_has_cv_daze_fives() -> None:
    reset_depth_scaling_cache()
    cfg = default_depth_scaling_config()
    for did in cfg.list_difficulty_ids():
        profile = cfg.profile_for(did)
        assert profile.cv_daze_min_turns == 5
        assert profile.cv_daze_max_turns == 5


def test_depth_scaling_omitted_cv_daze_defaults() -> None:
    raw = {
        "schema_version": 1,
        "default_difficulty_id": "normal",
        "difficulties": {
            "normal": {
                "display_name": "Normal",
                "apply_to_alignments": ["evil"],
                "stats": {},
            }
        },
    }
    cfg = parse_depth_scaling_config(raw)
    profile = cfg.profile_for("normal")
    assert profile.cv_daze_min_turns == 5
    assert profile.cv_daze_max_turns == 5


def test_depth_scaling_rejects_min_greater_than_max() -> None:
    raw = {
        "schema_version": 1,
        "default_difficulty_id": "normal",
        "difficulties": {
            "normal": {
                "display_name": "Normal",
                "apply_to_alignments": ["evil"],
                "stats": {},
                "cv_daze_min_turns": 7,
                "cv_daze_max_turns": 3,
            }
        },
    }
    try:
        parse_depth_scaling_config(raw)
        raise AssertionError("expected DepthScalingLoadError")
    except DepthScalingLoadError as exc:
        assert "cv_daze_min_turns" in str(exc)


def test_roll_cv_daze_turns_inclusive() -> None:
    reset_depth_scaling_cache()
    profile = default_depth_scaling_config().profile_for("normal")
    assert roll_cv_daze_turns(profile, random.Random(0)) == 5

    raw = {
        "schema_version": 1,
        "default_difficulty_id": "t",
        "difficulties": {
            "t": {
                "display_name": "T",
                "apply_to_alignments": ["evil"],
                "stats": {},
                "cv_daze_min_turns": 3,
                "cv_daze_max_turns": 7,
            }
        },
    }
    ranged = parse_depth_scaling_config(raw).profile_for("t")
    rolls = {roll_cv_daze_turns(ranged, random.Random(i)) for i in range(200)}
    assert rolls <= {3, 4, 5, 6, 7}
    assert min(rolls) >= 3
    assert max(rolls) <= 7


def test_engine_snapshots_alternate_cv_flag() -> None:
    engine = GameEngine(alternate_cv_mechanics=True, skip_new_game=True)
    isolate_other_ais(engine)
    # Minimal playable state for snapshot: need player from new_game
    engine.new_game()
    assert engine.alternate_cv_mechanics is True
    snap = engine.build_run_snapshot()
    assert snap["alternate_cv_mechanics"] is True

    restored = GameEngine.from_run_snapshot(snap)
    assert restored.alternate_cv_mechanics is True


def test_engine_snapshot_missing_alternate_cv_defaults_false() -> None:
    engine = GameEngine(skip_new_game=True)
    engine.new_game()
    snap = engine.build_run_snapshot()
    snap.pop("alternate_cv_mechanics", None)
    restored = GameEngine.from_run_snapshot(snap)
    assert restored.alternate_cv_mechanics is False
