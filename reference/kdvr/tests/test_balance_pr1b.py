"""PR1b: Options difficulty, run snapshot, density/rune economy, Past Runs."""

from __future__ import annotations

from tcod.ecs import Registry

from src.components import Alignment, Fighter, Player, PlayerProgression, Position
from src.constants import PLAYER_MAX_HP, RUNES_PER_FLOOR
from src.data.depth_scaling_config import (
    DepthScalingConfig,
    DifficultyProfile,
    StatSchedule,
    cycle_difficulty_id,
    validate_difficulty_id,
)
from src.data.dungeon_spawn_config import (
    DensityDefaults,
    DungeonSpawnConfig,
    compute_target_npc_count,
)
from src.data.floor_rune_registry import FloorRuneDefinition, FloorRuneRegistry, RuneEffect
from src.options_menu import (
    DIFFICULTY_ROW_INDEX,
    OptionsMenuState,
    format_difficulty_line,
    handle_options_event,
)
from src.past_runs.schema import PastRunRecord, parse_record, record_to_dict
from src.settings_store import SettingsStore
from src.spawn import spawn_from_definition
from src.systems.floor_runes import apply_rune_effect
from src.ui.past_runs_screen import format_past_run_stats_line
from src.data.entity_registry import EntityDefinition, SpawnConfig
from src.components import MobilityType
import random

import tcod.event
from tcod.event import KeySym


def _config_with(
    *,
    density: float = 1.0,
    runes: int | None = None,
    pieces: int = 1,
    stats: dict | None = None,
) -> DepthScalingConfig:
    profile = DifficultyProfile(
        id="hard",
        display_name="Hard",
        apply_to_alignments=frozenset({Alignment.EVIL}),
        stats=stats or {},
        density_multiplier=density,
        runes_per_floor_override=runes,
        rune_pieces_multiplier=pieces,
    )
    return DepthScalingConfig(
        schema_version=1,
        default_difficulty_id="hard",
        difficulties={"hard": profile},
    )


class TestDifficultyHelpers:
    def test_cycle_difficulty_ids(self) -> None:
        from src.data.depth_scaling_loader import default_depth_scaling_config

        cfg = default_depth_scaling_config()
        ids = list(cfg.list_difficulty_ids())
        assert ids == ["easier", "normal", "hard", "nightmare"]
        assert cycle_difficulty_id("normal", step=1, config=cfg) == "hard"
        assert cycle_difficulty_id("easier", step=-1, config=cfg) == "nightmare"

    def test_validate_unknown_falls_back(self) -> None:
        assert validate_difficulty_id("nope") == "normal"

    def test_validate_legacy_easy_maps_to_easier(self) -> None:
        assert validate_difficulty_id("easy") == "easier"


class TestSettingsDifficulty:
    def test_settings_roundtrip(self, tmp_path) -> None:
        path = tmp_path / "settings.json"
        store = SettingsStore(path=path)
        store.set_difficulty_id("nightmare")
        loaded = SettingsStore.load(path)
        assert loaded.difficulty_id == "nightmare"

    def test_settings_unknown_difficulty_defaults(self, tmp_path) -> None:
        path = tmp_path / "settings.json"
        path.write_text('{"difficulty_id": "bogus"}\n', encoding="utf-8")
        loaded = SettingsStore.load(path)
        assert loaded.difficulty_id == "normal"


class TestOptionsDifficultyRow:
    def test_format_line_brackets_active(self) -> None:
        line = format_difficulty_line("hard")
        assert "[Hard]" in line
        assert "Easier" in line
        # Display must be "Easier", not bare "Easy"
        assert "Easy ►" not in line and "Easy " not in line

    def test_cycle_on_difficulty_row(self, tmp_path) -> None:
        settings = SettingsStore(path=tmp_path / "s.json", difficulty_id="normal")
        state = OptionsMenuState(highlight=DIFFICULTY_ROW_INDEX)
        event = tcod.event.KeyDown(sym=KeySym.RIGHT, scancode=None, mod=0)
        handle_options_event(state, event, settings=settings)
        assert settings.difficulty_id == "hard"


class TestDensityMultiplier:
    def test_doubling_increases_target(self) -> None:
        config = DungeonSpawnConfig(
            schema_version=1,
            defaults=DensityDefaults(
                density_pct=0.1,
                density_variance=0.0,
                min_npcs=0,
                max_npcs=None,
            ),
            depth_bands=(),
        )
        rng = random.Random(0)
        base = compute_target_npc_count(100, 1, config, rng, density_multiplier=1.0)
        rng = random.Random(0)
        doubled = compute_target_npc_count(100, 1, config, rng, density_multiplier=2.0)
        assert doubled >= base
        assert doubled == min(100, round(100 * 0.1 * 2.0))


class TestRunePiecesMultiplier:
    def test_multiplier_one_applies_immediately(self) -> None:
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
        effect = RuneEffect(type="natural_ac", amount=1)
        text = apply_rune_effect(player, effect, rune_pieces_multiplier=1)
        assert text == "+1 AC"
        assert player.components[PlayerProgression].bonus_ac == 1

    def test_multiplier_two_needs_two_pieces(self) -> None:
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
        effect = RuneEffect(type="natural_ac", amount=1, pieces_per_bonus=1)
        first = apply_rune_effect(player, effect, rune_pieces_multiplier=2)
        assert "1/2" in first or "AC 1/2" in first
        assert player.components[PlayerProgression].bonus_ac == 0
        second = apply_rune_effect(player, effect, rune_pieces_multiplier=2)
        assert player.components[PlayerProgression].bonus_ac == 1


class TestPastRunsDifficulty:
    def test_stats_line_includes_difficulty(self) -> None:
        record = PastRunRecord(
            character_name="Alex",
            ending_kind="digested",
            ending_detail="wolf",
            monsters_defeated=3,
            runes_collected=1,
            depth=7,
            date="01/01/2026",
            difficulty_id="hard",
            difficulty_display="Hard",
        )
        line = format_past_run_stats_line(record)
        assert line.startswith("Hard - Depth 7")

    def test_legacy_record_omits_difficulty(self) -> None:
        record = PastRunRecord(
            character_name="Alex",
            ending_kind="digested",
            ending_detail="wolf",
            monsters_defeated=3,
            runes_collected=1,
            depth=7,
            date="01/01/2026",
        )
        line = format_past_run_stats_line(record)
        assert line == "Depth 7 - 1 Runes - 3 Enemies Defeated"

    def test_record_roundtrip(self) -> None:
        record = PastRunRecord(
            character_name="Alex",
            ending_kind="digested",
            ending_detail="wolf",
            monsters_defeated=1,
            runes_collected=0,
            depth=2,
            date="02/02/2026",
            difficulty_id="nightmare",
            difficulty_display="Nightmare",
        )
        parsed = parse_record(record_to_dict(record))
        assert parsed is not None
        assert parsed.difficulty_id == "nightmare"
        assert parsed.difficulty_display == "Nightmare"


class TestEngineSnapshotDifficulty:
    def test_new_game_snapshots_difficulty(self) -> None:
        from src.engine import GameEngine

        engine = GameEngine(
            difficulty_id="hard",
            skip_new_game=True,
        )
        assert engine.difficulty_id == "hard"
        assert engine.difficulty_profile().display_name == "Hard"
        assert engine.runes_per_floor() == RUNES_PER_FLOOR

    def test_runes_override_from_profile(self) -> None:
        from unittest.mock import patch

        from src.data.depth_scaling_loader import parse_depth_scaling_config
        from src.engine import GameEngine

        raw = {
            "schema_version": 1,
            "default_difficulty_id": "hard",
            "difficulties": {
                "hard": {
                    "display_name": "Hard",
                    "apply_to_alignments": ["evil"],
                    "stats": {},
                    "runes_per_floor_override": 1,
                    "rune_pieces_multiplier": 2,
                }
            },
        }
        cfg = parse_depth_scaling_config(raw)
        with patch(
            "src.data.depth_scaling_loader.default_depth_scaling_config",
            return_value=cfg,
        ):
            engine = GameEngine(difficulty_id="hard", skip_new_game=True)
            assert engine.runes_per_floor() == 1
            assert engine.difficulty_profile().rune_pieces_multiplier == 2
