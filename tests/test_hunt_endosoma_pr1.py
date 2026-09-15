"""PR1 endosoma-friendly: post-swallow option, dual loss copy, hidden vore rows."""

from __future__ import annotations

import json
import random

import tcod.console
from tcod.event import KeySym

from src.hunt_loss import (
    HuntNarrativeDecks,
    load_hunt_loss,
    pick_post_belly_lines,
    pick_swallow_lines,
)
from src.hunt_modals import ENGULFED_OVERLAY_FG
from src.hunt_panel import map_view_size
from src.hunt_session import HuntMode, handle_hunt_event, render_hunt
from src.hunt_stats import hunt_stats_lines
from src.messages import hunt_digested_over, hunt_endosoma_over, hunt_game_over
from src.options_menu import (
    POST_SWALLOW_ROW_INDEX,
    OptionsMenuState,
    format_post_swallow_line,
    handle_options_event,
    render_options_menu,
)
from src.settings_store import SettingsStore
from tests.test_hunt_deferred_pr9 import _belly_session
from tests.test_hunt_pr2 import _key, _session
from tests.test_hunt_pr10 import _console_text
from tests.ui_test_helpers import make_console


def test_missing_post_swallow_defaults_to_digest() -> None:
    store = SettingsStore.from_dict({})
    assert store.post_swallow == "digest"


def test_invalid_post_swallow_defaults_to_digest() -> None:
    store = SettingsStore.from_dict({"post_swallow": "safe-vore"})
    assert store.post_swallow == "digest"


def test_set_post_swallow_persists(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    settings.set_post_swallow("endosoma")
    loaded = SettingsStore.load(path)
    assert loaded.post_swallow == "endosoma"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["post_swallow"] == "endosoma"


def test_options_row_cycles_and_hides_vore_types(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = SettingsStore.load(path)
    state = OptionsMenuState(highlight=POST_SWALLOW_ROW_INDEX)
    handle_options_event(state, _key(KeySym.RIGHT), settings=settings)
    assert settings.post_swallow == "endosoma"
    handle_options_event(state, _key(KeySym.LEFT), settings=settings)
    assert settings.post_swallow == "digest"
    assert format_post_swallow_line("digest") == "Post-swallow:  [Digest] ► Endosoma"
    console = tcod.console.Console(80, 42, order="F")
    render_options_menu(console, state, settings=settings)
    text = "".join(
        chr(int(console.rgba[x, y]["ch"])) if int(console.rgba[x, y]["ch"]) else " "
        for y in range(console.height)
        for x in range(console.width)
    )
    assert "Post-swallow:" in text
    assert "Oral Vore" not in text
    assert "Cock Vore" not in text
    assert "Anal Vore" not in text


def test_digest_stats_label_is_default() -> None:
    text = "\n".join(line.text for line in hunt_stats_lines())
    assert "Times digested:" in text
    assert "Times swallowed:" not in text


def test_endosoma_stats_label_uses_same_counter() -> None:
    from src.hunt_stats import HuntCareerStats, empty_board

    data = empty_board()
    data.digested = 3
    text = "\n".join(
        line.text for line in hunt_stats_lines(data, post_swallow="endosoma")
    )
    assert "Times swallowed: 3" in text
    assert "Times digested" not in text
    assert isinstance(data, HuntCareerStats)


def test_digest_swallow_and_post_belly_copy() -> None:
    session = _session()
    session.begin_swallow()
    assert "You are swallowed whole." in session.win_lines
    session.mode = HuntMode.BELLY
    session.belly_turns = 99
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.mode is HuntMode.DIGEST
    assert session.win_lines == ("The raptor digests you.",)
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.win_lines == (hunt_game_over(), hunt_digested_over())


def test_endosoma_swallow_post_belly_and_game_over() -> None:
    session = _session()
    session.post_swallow = lambda: "endosoma"
    session.begin_swallow()
    assert session.win_lines == ("The raptor swallows you whole.",)
    session.mode = HuntMode.BELLY
    session.belly_turns = 99
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert session.win_lines == (
        "The raptor enjoys keeping you within her belly for a long time.",
    )
    handle_hunt_event(session, _key(KeySym.RETURN))
    assert session.mode is HuntMode.GAME_OVER
    assert session.win_lines == (hunt_game_over(), hunt_endosoma_over())


def test_endosoma_belly_does_not_darken() -> None:
    session = _belly_session(x=5, y=5)
    session.post_swallow = lambda: "endosoma"
    session.belly_turns = load_hunt_loss().belly_turns - 1
    console = make_console()
    render_hunt(console, session)
    view_w, view_h = map_view_size(console.width, console.height)
    cam_x = max(0, min(5 - view_w // 2, max(0, session.map.width - view_w)))
    cam_y = max(0, min(5 - view_h // 2, max(0, session.map.height - view_h)))
    hx, hy = 5 - cam_x + 1, 5 - cam_y
    late = tuple(int(c) for c in console.rgba[hx, hy]["fg"][:3])
    assert late == ENGULFED_OVERLAY_FG


def test_live_stance_applies_at_loss_compose() -> None:
    session = _session()
    box = ["digest"]

    def _stance() -> str:
        return box[0]

    session.post_swallow = _stance
    session.begin_swallow()
    assert "You are swallowed whole." in session.win_lines
    box[0] = "endosoma"
    session.mode = HuntMode.BELLY
    session.belly_turns = 99
    handle_hunt_event(session, _key(KeySym.PERIOD))
    assert "keeping you within her belly" in session.win_lines[0]


def test_shuffle_bag_sees_each_path_once() -> None:
    decks = HuntNarrativeDecks()
    rng = random.Random(1)
    paths = (("a",), ("b",), ("c",))
    seen = [decks.draw("pool", paths, rng)[0] for _ in range(3)]
    assert set(seen) == {"a", "b", "c"}


def test_legacy_digest_array_becomes_one_path(tmp_path) -> None:
    path = tmp_path / "hunt_loss.json"
    path.write_text(
        json.dumps(
            {
                "belly_turns": 2,
                "digest": ["old digest line"],
                "swallow_front": ["front"],
            }
        ),
        encoding="utf-8",
    )
    load_hunt_loss.cache_clear()
    cfg = load_hunt_loss(path)
    assert cfg.digest_paths == (("old digest line",),)
    rng = random.Random(0)
    decks = HuntNarrativeDecks()
    assert pick_post_belly_lines(stance="digest", decks=decks, rng=rng, cfg=cfg) == (
        "old digest line",
    )
    assert pick_swallow_lines(
        "front", stance="digest", decks=decks, rng=rng, cfg=cfg,
    ) == ("front",)
    load_hunt_loss.cache_clear()
