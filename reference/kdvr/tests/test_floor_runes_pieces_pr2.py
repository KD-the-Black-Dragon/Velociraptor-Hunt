"""PR2: piece-based floor runes (separable Acc/Dam, sticky freeze)."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import Fighter, Player, PlayerProgression
from src.constants import PLAYER_MAX_HP
from src.data.floor_rune_loader import FloorRuneLoadError, parse_floor_rune_registry
from src.data.floor_rune_registry import RuneEffect
from src.systems.floor_runes import apply_rune_effect
from src.ui.status_corner import progression_extra_rows


def _player() -> tuple[Registry, object]:
    world = Registry()
    player = world[object()]
    player.tags.add(Player)
    player.components[Fighter] = Fighter(
        hp=PLAYER_MAX_HP,
        max_hp=PLAYER_MAX_HP,
        accuracy=1.0,
        evade=0,
        ac=1,
        min_damage=1,
        max_damage=2,
    )
    player.components[PlayerProgression] = PlayerProgression()
    return world, player


class TestPiecesPerBonus:
    def test_default_one_grants_immediately(self) -> None:
        _, player = _player()
        text = apply_rune_effect(
            player, RuneEffect(type="natural_ac", amount=1)
        )
        assert text == "+1 AC"
        assert player.components[PlayerProgression].bonus_ac == 1

    def test_four_pieces_for_one_ac(self) -> None:
        _, player = _player()
        effect = RuneEffect(
            type="natural_ac", amount=1, pieces_per_bonus=4, pieces_granted=1
        )
        for i in range(3):
            text = apply_rune_effect(player, effect)
            assert player.components[PlayerProgression].bonus_ac == 0
            assert f"{i + 1}/4" in text
        text = apply_rune_effect(player, effect)
        assert player.components[PlayerProgression].bonus_ac == 1
        assert "complete" in text or "+1 AC" in text

    def test_pieces_granted_can_overshoot(self) -> None:
        _, player = _player()
        effect = RuneEffect(
            type="natural_ac", amount=1, pieces_per_bonus=3, pieces_granted=5
        )
        # 5 pieces → complete once (3) remainder 2
        text = apply_rune_effect(player, effect)
        assert player.components[PlayerProgression].bonus_ac == 1
        assert player.components[PlayerProgression].pieces_ac == 2


class TestSeparableAccuracyDamage:
    def test_damage_only_accuracy_damage_does_not_touch_accuracy_bank(self) -> None:
        _, player = _player()
        effect = RuneEffect(
            type="accuracy_damage",
            accuracy=0.0,
            min_damage=1,
            max_damage=1,
            pieces_per_bonus=2,
            pieces_granted=1,
        )
        apply_rune_effect(player, effect)
        prog = player.components[PlayerProgression]
        assert prog.pieces_min_damage == 1
        assert prog.pieces_max_damage == 1
        assert prog.pieces_accuracy == 0
        assert prog.bonus_accuracy == 0.0
        apply_rune_effect(player, effect)
        assert prog.bonus_min_damage == 1
        assert prog.bonus_max_damage == 1
        assert prog.bonus_accuracy == 0.0

    def test_pure_accuracy_separate_from_damage(self) -> None:
        _, player = _player()
        acc = RuneEffect(type="accuracy", amount=0.03, pieces_per_bonus=2)
        dmg = RuneEffect(
            type="accuracy_damage",
            accuracy=0.0,
            min_damage=1,
            max_damage=1,
            pieces_per_bonus=2,
        )
        apply_rune_effect(player, acc)
        apply_rune_effect(player, dmg)
        prog = player.components[PlayerProgression]
        assert prog.pieces_accuracy == 1
        assert prog.pieces_min_damage == 1
        assert prog.bonus_accuracy == 0.0
        assert prog.bonus_min_damage == 0


class TestStickyFreeze:
    def test_need_does_not_change_after_cycle(self) -> None:
        _, player = _player()
        four = RuneEffect(
            type="natural_ac", amount=1, pieces_per_bonus=4, pieces_granted=1
        )
        two = RuneEffect(
            type="natural_ac", amount=1, pieces_per_bonus=2, pieces_granted=1
        )
        for _ in range(4):
            apply_rune_effect(player, four)
        prog = player.components[PlayerProgression]
        assert prog.bonus_ac == 1
        assert prog.pieces_ac == 0
        assert prog.pieces_need_ac == 4
        assert prog.pieces_ac_need_frozen is True
        # Later grant with different pieces_per_bonus must not unfreeze need
        apply_rune_effect(player, two)
        assert prog.pieces_need_ac == 4
        assert prog.pieces_ac == 1


class TestLoaderPieces:
    def test_parse_pieces_fields(self) -> None:
        raw = {
            "schema_version": 1,
            "runes": [
                {
                    "id": "ward",
                    "display_name": "ward",
                    "glyph": "0",
                    "fg": [1, 2, 3],
                    "examine": "x",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 10,
                    "effect": {
                        "type": "natural_ac",
                        "amount": 1,
                        "pieces_per_bonus": 4,
                        "pieces_granted": 1,
                    },
                }
            ],
        }
        reg = parse_floor_rune_registry(raw)
        assert reg.runes[0].effect.pieces_per_bonus == 4

    def test_pieces_per_bonus_must_be_positive(self) -> None:
        raw = {
            "schema_version": 1,
            "runes": [
                {
                    "id": "ward",
                    "display_name": "ward",
                    "glyph": "0",
                    "fg": [1, 2, 3],
                    "examine": "x",
                    "weight": 1,
                    "min_depth": 1,
                    "max_depth": 10,
                    "effect": {
                        "type": "natural_ac",
                        "amount": 1,
                        "pieces_per_bonus": 0,
                    },
                }
            ],
        }
        try:
            parse_floor_rune_registry(raw)
            raise AssertionError("expected load error")
        except FloorRuneLoadError as exc:
            assert "pieces_per_bonus" in str(exc)


class TestStatusPartial:
    def test_partial_ac_row(self) -> None:
        prog = PlayerProgression(pieces_ac=2, pieces_need_ac=4, pieces_ac_need_frozen=True)
        rows = progression_extra_rows(prog, max_width=10)
        texts = [r.text for r in rows]
        assert any("AC" in t and "2/4" in t for t in texts)

    def test_completed_and_partial_compact(self) -> None:
        prog = PlayerProgression(
            bonus_ac=1,
            pieces_ac=1,
            pieces_need_ac=4,
            pieces_ac_need_frozen=True,
        )
        rows = progression_extra_rows(prog, max_width=10)
        assert any("AC +1" in r.text and "1/4" in r.text for r in rows)


class TestMultiplierTimesPieces:
    def test_pieces_times_difficulty_multiplier(self) -> None:
        _, player = _player()
        # pieces_per_bonus 2 * multiplier 2 = need 4
        effect = RuneEffect(
            type="natural_ac", amount=1, pieces_per_bonus=2, pieces_granted=1
        )
        for _ in range(3):
            apply_rune_effect(player, effect, rune_pieces_multiplier=2)
        assert player.components[PlayerProgression].bonus_ac == 0
        apply_rune_effect(player, effect, rune_pieces_multiplier=2)
        assert player.components[PlayerProgression].bonus_ac == 1
        assert player.components[PlayerProgression].pieces_need_ac == 4
