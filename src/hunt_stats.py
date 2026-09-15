"""Persistent hunt stats screen (menu → Stats)."""

from __future__ import annotations

import json
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

from src.difficulties import load_difficulties, resolve_difficulty
from src.hunt_loss import POST_SWALLOW_ENDOSOMA, normalize_post_swallow
from src.text import cp437_safe
from src.ui.help_overlay import (
    HELP_BODY_FG,
    HELP_FOOTER_FG,
    HELP_SECTION_FG,
    HELP_TITLE_FG,
    HelpTextLine,
)
from src.user_data import HUNT_STATS_PATH

HUNT_STATS_FORMAT_VERSION = 2
TMP_FILENAME = "hunt_stats.tmp"
WEAPON_IDS: tuple[str, ...] = ("rifle", "shotgun", "revolver")
WEAPON_LABELS: dict[str, str] = {
    "rifle": "Rifle",
    "shotgun": "Shotgun",
    "revolver": "Revolver",
}
DIFFICULTY_ORDER: tuple[str, ...] = ("easier", "normal", "hard", "nightmare")


class HuntStatsAction(Enum):
    NONE = auto()
    BACK = auto()
    CYCLE = auto()


@attrs.define
class WeaponShotStats:
    fired: int = 0
    landed: int = 0
    perfect: int = 0
    one_shot_kos: int = 0


@attrs.define
class HuntCareerStats:
    games_played: int = 0
    abandoned: int = 0
    tranquilized: int = 0
    digested: int = 0
    time_wins: int = 0
    time_losses: int = 0
    weapons: dict[str, WeaponShotStats] = attrs.field(factory=dict)

    def __attrs_post_init__(self) -> None:
        for wid in WEAPON_IDS:
            if wid not in self.weapons:
                self.weapons[wid] = WeaponShotStats()


@attrs.define
class HuntStatsScreenState:
    difficulty_id: str = "normal"


def _empty_weapons() -> dict[str, WeaponShotStats]:
    return {wid: WeaponShotStats() for wid in WEAPON_IDS}


def empty_board() -> HuntCareerStats:
    return HuntCareerStats(weapons=_empty_weapons())


def _cycle_id(current: str, ids: list[str], step: int) -> str:
    if not ids:
        return current
    if current not in ids:
        return ids[0]
    return ids[(ids.index(current) + step) % len(ids)]


def difficulty_ids() -> tuple[str, ...]:
    cfg = load_difficulties()
    ids = [i for i in DIFFICULTY_ORDER if i in cfg.by_id]
    for i in cfg.by_id:
        if i not in ids:
            ids.append(i)
    return tuple(ids or ("normal",))


def _weapon_from_raw(raw: Any) -> WeaponShotStats:
    if not isinstance(raw, dict):
        return WeaponShotStats()
    return WeaponShotStats(
        fired=int(raw.get("fired", 0)),
        landed=int(raw.get("landed", 0)),
        perfect=int(raw.get("perfect", 0)),
        one_shot_kos=int(raw.get("one_shot_kos", 0)),
    )


def stats_from_dict(raw: dict[str, Any]) -> HuntCareerStats:
    weapons_raw = raw.get("weapons", {})
    weapons = _empty_weapons()
    if isinstance(weapons_raw, dict):
        for wid in WEAPON_IDS:
            weapons[wid] = _weapon_from_raw(weapons_raw.get(wid))
    return HuntCareerStats(
        games_played=int(raw.get("games_played", 0)),
        abandoned=int(raw.get("abandoned", 0)),
        tranquilized=int(raw.get("tranquilized", 0)),
        digested=int(raw.get("digested", 0)),
        time_wins=int(raw.get("time_wins", 0)),
        time_losses=int(raw.get("time_losses", 0)),
        weapons=weapons,
    )


def stats_to_dict(stats: HuntCareerStats) -> dict[str, Any]:
    return {
        "games_played": stats.games_played,
        "abandoned": stats.abandoned,
        "tranquilized": stats.tranquilized,
        "digested": stats.digested,
        "time_wins": stats.time_wins,
        "time_losses": stats.time_losses,
        "weapons": {
            wid: {
                "fired": stats.weapons[wid].fired,
                "landed": stats.weapons[wid].landed,
                "perfect": stats.weapons[wid].perfect,
                "one_shot_kos": stats.weapons[wid].one_shot_kos,
            }
            for wid in WEAPON_IDS
        },
    }


def _empty_boards() -> dict[str, HuntCareerStats]:
    return {did: empty_board() for did in difficulty_ids()}


def boards_from_document(document: dict[str, Any]) -> dict[str, HuntCareerStats]:
    boards = _empty_boards()
    version = document.get("hunt_stats_format_version")
    if version == 1:
        boards["normal"] = stats_from_dict(document)
        return boards
    raw_boards = document.get("by_difficulty")
    if not isinstance(raw_boards, dict):
        if "games_played" in document:
            boards["normal"] = stats_from_dict(document)
        return boards
    for did, raw in raw_boards.items():
        if did in boards and isinstance(raw, dict):
            boards[did] = stats_from_dict(raw)
    return boards


class HuntStatsStore:
    """JSON file store for per-difficulty hunt tallies."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else HUNT_STATS_PATH

    def load_all(self) -> dict[str, HuntCareerStats]:
        if not self.path.is_file():
            return _empty_boards()
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return _empty_boards()
        if not isinstance(document, dict):
            return _empty_boards()
        version = document.get("hunt_stats_format_version")
        if version not in (1, HUNT_STATS_FORMAT_VERSION):
            return _empty_boards()
        return boards_from_document(document)

    def load(self, difficulty_id: str | None = None) -> HuntCareerStats:
        did = resolve_difficulty(difficulty_id).difficulty_id
        boards = self.load_all()
        return boards.get(did, empty_board())

    def save_all(self, boards: dict[str, HuntCareerStats]) -> None:
        payload = {
            "hunt_stats_format_version": HUNT_STATS_FORMAT_VERSION,
            "by_difficulty": {
                did: stats_to_dict(boards.get(did, empty_board()))
                for did in difficulty_ids()
            },
        }
        data = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.parent / TMP_FILENAME
        with tmp_path.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, self.path)

    def record_session(self, session: Any) -> None:
        """Merge one hunt's shots and (if finished or abandoned) outcome."""
        if getattr(session, "stats_recorded", False):
            return
        if getattr(session, "training", False):
            return
        did = resolve_difficulty(getattr(session, "difficulty_id", None)).difficulty_id
        boards = self.load_all()
        stats = boards.get(did, empty_board())
        wid = str(getattr(session, "weapon_id", ""))
        if wid in stats.weapons:
            bucket = stats.weapons[wid]
            bucket.fired += int(getattr(session, "shots_fired", 0))
            bucket.landed += int(getattr(session, "shots_landed", 0))
            bucket.perfect += int(getattr(session, "shots_perfect", 0))
            bucket.one_shot_kos += int(getattr(session, "shots_one_shot", 0))
        outcome = getattr(session, "outcome", None)
        if outcome == "tranquilized":
            stats.games_played += 1
            stats.tranquilized += 1
        elif outcome == "digested":
            stats.games_played += 1
            stats.digested += 1
        elif outcome == "time_win":
            stats.games_played += 1
            stats.time_wins += 1
        elif outcome == "time_loss":
            stats.games_played += 1
            stats.time_losses += 1
        elif outcome == "abandoned":
            stats.games_played += 1
            stats.abandoned += 1
        boards[did] = stats
        self.save_all(boards)
        session.stats_recorded = True


def handle_hunt_stats_event(
    event: tcod.event.Event,
    state: HuntStatsScreenState | None = None,
) -> HuntStatsAction:
    if not isinstance(event, tcod.event.KeyDown):
        return HuntStatsAction.NONE
    if event.sym == KeySym.ESCAPE:
        return HuntStatsAction.BACK
    if state is None:
        return HuntStatsAction.NONE
    ids = list(difficulty_ids())
    if event.sym in {KeySym.LEFT, KeySym.KP_4, KeySym.G}:
        state.difficulty_id = _cycle_id(state.difficulty_id, ids, -1)
        return HuntStatsAction.CYCLE
    if event.sym in {KeySym.RIGHT, KeySym.KP_6, KeySym.J}:
        state.difficulty_id = _cycle_id(state.difficulty_id, ids, 1)
        return HuntStatsAction.CYCLE
    return HuntStatsAction.NONE


def hunt_stats_lines(
    stats: HuntCareerStats | None = None,
    *,
    difficulty_id: str = "normal",
    post_swallow: str = "digest",
) -> tuple[HelpTextLine, ...]:
    data = stats if stats is not None else empty_board()
    label = resolve_difficulty(difficulty_id).label
    swallowed_label = (
        "Times swallowed"
        if normalize_post_swallow(post_swallow) == POST_SWALLOW_ENDOSOMA
        else "Times digested"
    )
    lines: list[HelpTextLine] = [
        HelpTextLine(f"STATISTICS — {label}", HELP_TITLE_FG),
        HelpTextLine("", HELP_BODY_FG),
        HelpTextLine(f"Total games played: {data.games_played}", HELP_BODY_FG),
        HelpTextLine(f"Games abandoned: {data.abandoned}", HELP_BODY_FG),
        HelpTextLine(f"Times raptor tranquilized: {data.tranquilized}", HELP_BODY_FG),
        HelpTextLine(f"{swallowed_label}: {data.digested}", HELP_BODY_FG),
        HelpTextLine(f"Wins by time over: {data.time_wins}", HELP_BODY_FG),
        HelpTextLine(f"Losses by time over: {data.time_losses}", HELP_BODY_FG),
    ]
    for wid in WEAPON_IDS:
        w = data.weapons[wid]
        lines.append(HelpTextLine("", HELP_BODY_FG))
        lines.append(HelpTextLine(WEAPON_LABELS[wid], HELP_SECTION_FG))
        lines.append(HelpTextLine(f"  Shots fired: {w.fired}", HELP_BODY_FG))
        lines.append(HelpTextLine(f"  Shots landed: {w.landed}", HELP_BODY_FG))
        lines.append(HelpTextLine(f"  Perfect shots: {w.perfect}", HELP_BODY_FG))
        lines.append(HelpTextLine(f"  One-shot KOs: {w.one_shot_kos}", HELP_BODY_FG))
    return tuple(lines)


def hunt_stats_footer() -> str:
    return "Left/Right: difficulty   Esc: back"


def render_hunt_stats(
    console: tcod.console.Console,
    stats: HuntCareerStats | None = None,
    *,
    difficulty_id: str = "normal",
    post_swallow: str = "digest",
) -> None:
    console.clear()
    y = 2
    for line in hunt_stats_lines(
        stats, difficulty_id=difficulty_id, post_swallow=post_swallow,
    ):
        if y >= console.height - 2:
            break
        console.print(2, y, cp437_safe(line.text)[: console.width - 4], fg=line.fg)
        y += 1
    console.print(
        2,
        console.height - 1,
        hunt_stats_footer()[: console.width - 4],
        fg=HELP_FOOTER_FG,
    )
