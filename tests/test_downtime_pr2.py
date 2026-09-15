"""PR2: career downtime hub shell."""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeySym, Modifier, Scancode

from src.app import AppPhase
from src.career import CAMPAIGN_STYLE_COMPANY, STARTING_GOLD, new_career
from src.career_store import CareerStore
from src.downtime_hub import (
    HubView,
    handle_downtime_event,
    hub_root_options,
    render_downtime_hub,
    stub_cards_for_round,
)
from tests.save_test_helpers import app_with_isolated_save
from tests.ui_test_helpers import make_console


def _key(sym: KeySym, *, mod: int = 0) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(sym=sym, scancode=Scancode.UNKNOWN, mod=mod)


def test_new_career_enters_downtime_not_dungeon(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    career = new_career(player_name="Rix")
    app._enter_downtime(career)
    assert app.phase is AppPhase.DOWNTIME
    assert app.engine is None
    assert app.career is not None
    assert app.career.gold >= 0
    assert app.career.renown >= 0
    assert app.career_store.probe()


def test_career_store_roundtrip(tmp_path) -> None:
    store = CareerStore(tmp_path / "saves")
    career = new_career(player_name="Rix", difficulty_id="hard")
    career.gold = 250
    career.renown = 12
    career.round_index = 3
    store.save(career)
    loaded = store.load()
    assert loaded.player_name == "Rix"
    assert loaded.gold == 250
    assert loaded.renown == 12
    assert loaded.round_index == 3
    assert loaded.difficulty_id == "hard"


def test_career_store_reload_restores_career(tmp_path) -> None:
    app = app_with_isolated_save(tmp_path)
    console = make_console()
    app._enter_downtime(new_career(player_name="alex"))
    assert app.phase is AppPhase.DOWNTIME
    name = app.career.player_name if app.career else ""
    app._return_to_menu()
    assert app.phase is AppPhase.MENU
    assert app.career is None
    app._load_career_or_dungeon(console)
    assert app.phase is AppPhase.DOWNTIME
    assert app.career is not None
    assert app.career.player_name == name


def test_match_select_shows_green_and_red() -> None:
    # Round 1 is a green round: pool includes both kinds. Offers are a random 3.
    from src.match_cards import eligible_card_defs

    pool_kinds = {c.kind for c in eligible_card_defs(1, difficulty_id="normal")}
    assert "green" in pool_kinds
    assert "red" in pool_kinds
    # Offers still return up to 3 cards
    cards = stub_cards_for_round(1, seed=1)
    assert 1 <= len(cards) <= 3


def test_hub_navigate_to_match_select() -> None:
    career = new_career(player_name="Test")
    from src.downtime_hub import DowntimeHubState

    hub = DowntimeHubState()
    opts = hub_root_options(career)
    select_idx = next(i for i, label in enumerate(opts) if label.startswith("Select"))
    hub.highlight = select_idx
    handle_downtime_event(hub, career, _key(KeySym.RETURN))
    assert hub.view is HubView.MATCH_SELECT
    assert 1 <= len(hub.cards) <= 3
    # Solo: only 1v1 cards
    for card in hub.cards:
        assert len(card.enemies) == 1 and card.enemies[0][1] == 1


def test_hub_preserves_highlight_when_returning() -> None:
    # Company style still has Assign team (on ice path)
    career = new_career(player_name="Test", campaign_style=CAMPAIGN_STYLE_COMPANY)
    career.starter_picks_done = True
    from src.downtime_hub import DowntimeHubState

    hub = DowntimeHubState()
    opts = hub_root_options(career)
    assign_idx = next(i for i, label in enumerate(opts) if label.startswith("Assign"))
    hub.highlight = assign_idx
    handle_downtime_event(hub, career, _key(KeySym.RETURN))
    assert hub.view is HubView.ASSIGN_TEAM
    handle_downtime_event(hub, career, _key(KeySym.ESCAPE))
    assert hub.view is HubView.ROOT
    assert hub.highlight == assign_idx

    select_idx = next(i for i, label in enumerate(opts) if label.startswith("Select"))
    hub.highlight = select_idx
    handle_downtime_event(hub, career, _key(KeySym.RETURN))
    assert hub.view is HubView.MATCH_SELECT
    handle_downtime_event(hub, career, _key(KeySym.ESCAPE))
    assert hub.view is HubView.ROOT
    assert hub.highlight == select_idx


def test_render_downtime_shows_gold_renown() -> None:
    career = new_career(player_name="Goldie")
    career.gold = 77
    career.renown = 3
    from src.downtime_hub import DowntimeHubState

    hub = DowntimeHubState()
    console = tcod.console.Console(80, 50, order="F")
    render_downtime_hub(console, career, hub)

    def row_text(y: int) -> str:
        chars: list[str] = []
        for x in range(80):
            ch = int(console.rgba[x, y]["ch"])
            chars.append(chr(ch) if ch else " ")
        return "".join(chars)

    joined = "\n".join(row_text(y) for y in range(8))
    assert "Goldie" in joined
    assert "77" in joined
    assert "3" in joined
    assert "DOWNTIME" in joined
