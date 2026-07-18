"""Assemble structured crash context from the live app and exception."""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

from src.components import Fighter, Position
from src.constants import PROJECT_ROOT
from src.debug.modal_snapshot import active_modal_label
from src.debug.session_log import session_log
from src.debug.version_info import GAME_VERSION, collect_platform_info
from src.save.codec import encode_rng_state

if TYPE_CHECKING:
    from src.app import App


@dataclass(frozen=True)
class CrashContext:
    """Snapshot fields written to ``logs/crash.log``."""

    timestamp_utc: str
    game_version: str
    python_version: str
    platform_string: str
    os_string: str
    exc_type_name: str
    exc_message: str
    traceback_text: str
    app_phase: str | None
    active_modal: str | None
    floor: int | None
    turn: int | None
    run_seed: int | None
    rng_state: str | None
    player_position: str | None
    player_hp: str | None
    macguffin_discovered: str | None
    loaded_mods: str
    session_log_path: str | None


def _relative_log_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def build_crash_context(
    app: App | None,
    exc: BaseException,
    *,
    exc_type: type[BaseException] | None = None,
    exc_tb: TracebackType | None = None,
) -> CrashContext:
    """Collect platform, exception, and optional game-state fields for a crash report."""
    resolved_type = exc_type if exc_type is not None else type(exc)
    tb = exc_tb if exc_tb is not None else exc.__traceback__
    traceback_text = "".join(
        traceback.format_exception(resolved_type, exc, tb),
    ).rstrip()
    platform_string, os_string = collect_platform_info()

    app_phase: str | None = None
    active_modal: str | None = None
    floor: int | None = None
    turn: int | None = None
    run_seed: int | None = None
    rng_state: str | None = None
    player_position: str | None = None
    player_hp: str | None = None
    macguffin_discovered: str | None = None

    if app is not None:
        app_phase = app.phase.name
        active_modal = active_modal_label(app)
        engine = app.engine
        if engine is not None:
            floor = engine.floor_depth
            turn = engine.player_turn_count
            run_seed = engine.run_seed
            rng_state = str(encode_rng_state(engine.rng.getstate()))
            if engine.player is not None:
                pos = engine.player.components.get(Position)
                if pos is not None:
                    player_position = f"({pos.x}, {pos.y})"
                fighter = engine.player.components.get(Fighter)
                if fighter is not None:
                    player_hp = f"{fighter.hp}/{fighter.max_hp}"
            macguffin_discovered = (
                "yes" if engine.macguffin_discovery.active else "no"
            )

    from src.mods.fingerprint import format_loaded_mods_for_crash

    return CrashContext(
        timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        game_version=GAME_VERSION,
        python_version=sys.version.replace("\n", " "),
        platform_string=platform_string,
        os_string=os_string,
        exc_type_name=resolved_type.__name__,
        exc_message=str(exc),
        traceback_text=traceback_text,
        app_phase=app_phase,
        active_modal=active_modal,
        floor=floor,
        turn=turn,
        run_seed=run_seed,
        rng_state=rng_state,
        player_position=player_position,
        player_hp=player_hp,
        macguffin_discovered=macguffin_discovered,
        loaded_mods=format_loaded_mods_for_crash(),
        session_log_path=_relative_log_path(session_log.session_path),
    )