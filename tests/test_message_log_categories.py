"""PR2: message log color categories."""

from __future__ import annotations

from src import messages
from src.components import Fighter
from src.engine import GameEngine
from src.message_log import MessageCategory, MessageLog
from src.systems.rest import try_rest_until_healed_or_danger

from tests.ui_test_helpers import default_layout, message_log_rect, render_engine_frame


def test_message_log_add_stores_category() -> None:
    log = MessageLog()
    log.add("routine line")
    log.add("danger line", category=MessageCategory.DANGER)
    log.add("speech line", category=MessageCategory.SPEECH)
    assert log.entries()[0].category is MessageCategory.ROUTINE
    assert log.entries()[1].category is MessageCategory.DANGER
    assert log.entries()[1].fg == MessageCategory.DANGER.fg
    assert log.entries()[2].category is MessageCategory.SPEECH
    assert log.entries()[2].fg == (255, 255, 255)


def test_category_fg_values_match_design() -> None:
    assert MessageCategory.ROUTINE.fg == (192, 192, 192)
    assert MessageCategory.DANGER.fg == (255, 80, 80)
    assert MessageCategory.CAUTION.fg == (255, 220, 80)
    assert MessageCategory.POSITIVE.fg == (80, 220, 120)
    assert MessageCategory.MAGICAL.fg == (100, 220, 255)
    assert MessageCategory.SPEECH.fg == (255, 255, 255)
    assert MessageCategory.RARE.fg == (255, 100, 255)


def test_rest_messages_use_expected_categories() -> None:
    from src.components import AI

    engine = GameEngine()
    for entity in list(engine.world.Q.all_of(components=[AI])):
        if entity is not engine.player:
            entity.clear()
    player = engine.player
    assert player is not None
    player.components[Fighter].hp = 10

    def consume() -> None:
        from src.events import fire_player_combat_targeted

        fire_player_combat_targeted()

    try_rest_until_healed_or_danger(
        player=player,
        game_map=engine.game_map,
        world=engine.world,
        message_log=engine.message_log,
        consume_turn=consume,
        max_turns=1,
    )

    by_text = {entry.text: entry.category for entry in engine.message_log.entries()}
    assert by_text[messages.rest_start()] is MessageCategory.ROUTINE
    assert by_text[messages.rest_interrupted_by_attack()] is MessageCategory.CAUTION


def test_stunned_message_renders_danger_color() -> None:
    engine = GameEngine()
    engine.message_log = MessageLog()
    engine.message_log.add(
        messages.stunned_too_tired_to_move(),
        category=MessageCategory.DANGER,
    )
    console = render_engine_frame(engine)
    rect = message_log_rect(default_layout())
    fg = tuple(
        int(console.rgba[rect.x + 1, rect.y]["fg"][index]) for index in range(3)
    )
    assert fg == MessageCategory.DANGER.fg