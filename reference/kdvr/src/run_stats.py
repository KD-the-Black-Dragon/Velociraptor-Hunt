"""Per-run statistical counters (monsters defeated, runes collected)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import attrs

if TYPE_CHECKING:
    from tcod.ecs import Entity


@attrs.define
class RunStats:
    """Counters for the current run; reset on new game, restored from save."""

    monsters_defeated: int = 0
    runes_collected: int = 0

    def record_monster_defeated(self, *, defeated_entity: Entity | None = None) -> None:
        self.monsters_defeated += 1
        if defeated_entity is not None:
            from src.debug.session_log import session_log
            from src.systems.naming import entity_log_name

            name = entity_log_name(defeated_entity, sentence_start=True)
            session_log.log(f"Defeated {name}")

    def record_rune_collected(self) -> None:
        self.runes_collected += 1

    def reset(self) -> None:
        self.monsters_defeated = 0
        self.runes_collected = 0


def encode_run_stats(stats: RunStats) -> dict[str, int]:
    return {
        "monsters_defeated": stats.monsters_defeated,
        "runes_collected": stats.runes_collected,
    }


def decode_run_stats(data: Any) -> RunStats:
    if not isinstance(data, dict):
        return RunStats()
    return RunStats(
        monsters_defeated=max(0, int(data.get("monsters_defeated", 0))),
        runes_collected=max(0, int(data.get("runes_collected", 0))),
    )