"""PR4: crash modal snapshot labels."""

from __future__ import annotations

from src.app import App, AppPhase
from src.debug.modal_snapshot import active_modal_label
from src.engine import GameEngine
from src.macguffin_discovery import MacguffinDiscovery
from src.new_game_confirm import NewGameConfirmState
from src.quit_confirm import QuitConfirmState
from src.systems.rest import RestSession

from tests.map_test_helpers import isolate_other_ais


def _play_app() -> App:
    app = App()
    app.phase = AppPhase.PLAY
    app.engine = GameEngine(skip_new_game=True)
    isolate_other_ais(app.engine)
    return app


def test_menu_new_game_confirm_has_priority() -> None:
    app = App()
    app.new_game_confirm = NewGameConfirmState()
    app.quit_confirm = QuitConfirmState()
    assert active_modal_label(app) == "new_game_confirm"


def test_menu_phase_labels() -> None:
    app = App()
    app.phase = AppPhase.OPTIONS
    assert active_modal_label(app) == "options"


def test_help_overlay_broader_than_modal_blocks_quit() -> None:
    app = _play_app()
    assert app.engine is not None
    app.engine.help_overlay.open()
    assert not app.engine.modal_blocks_quit()
    assert active_modal_label(app) == "help_overlay"


def test_log_overlay_and_examine_labels() -> None:
    app = _play_app()
    assert app.engine is not None
    app.engine.log_overlay.active = True
    assert active_modal_label(app) == "log_overlay"

    app.engine.log_overlay.close()
    app.engine.examine_state.showing_description = True
    assert active_modal_label(app) == "examine"


def test_game_over_beats_lower_priority_modals() -> None:
    app = _play_app()
    assert app.engine is not None
    from src.game_over_ending import GameOverEnding

    app.engine.digestion_modal.open(predator=object(), phases=["line"])
    app.engine.game_over.open(
        player_name="Hero",
        ending=GameOverEnding(kind="defeated", detail="wolf"),
        monsters_defeated=0,
        runes_collected=0,
        depth=1,
    )
    assert active_modal_label(app) == "game_over"


def test_rest_modal_label() -> None:
    app = _play_app()
    assert app.engine is not None
    app.engine.rest_session = RestSession(active=True)
    assert active_modal_label(app) == "rest"


def test_autoexplore_modal_label() -> None:
    from src.systems.autoexplore import AutoexploreSession

    app = _play_app()
    assert app.engine is not None
    app.engine.autoexplore_session = AutoexploreSession(active=True)
    assert active_modal_label(app) == "autoexplore"


def test_macguffin_discovery_is_not_a_modal_label() -> None:
    app = _play_app()
    assert app.engine is not None
    app.engine.macguffin_discovery = MacguffinDiscovery(
        macguffin_id="orb",
        display_name="Orb",
        score=10,
    )
    assert app.engine.macguffin_discovery.active
    assert active_modal_label(app) is None