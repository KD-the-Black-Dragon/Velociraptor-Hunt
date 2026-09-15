from __future__ import annotations

import attrs
import tcod.console

from src.components import PlayerEffects, PlayerProgression
from src.text import cp437_safe
from src.ui.regions import STATUS_CORNER_BACKGROUND

STATUS_DEPTH_FG = (210, 220, 235)
STATUS_STUNNED_FG = (255, 200, 120)
STATUS_ENGULFED_FG = (255, 160, 100)
STATUS_HP_FG = (80, 220, 120)
STATUS_DAMAGE_FG = (255, 80, 80)
STATUS_ACCURACY_FG = (255, 220, 80)
STATUS_AC_FG = (100, 220, 255)
STATUS_EVADE_FG = (180, 200, 230)
STATUS_FAST_FG = (255, 230, 120)
STATUS_MIGHT_FG = (255, 140, 90)
STATUS_WARD_FG = (160, 220, 160)
STATUS_TELE_FG = (180, 160, 255)


@attrs.define(frozen=True)
class StatusBonusRow:
    text: str
    fg: tuple[int, int, int]


@attrs.define(frozen=True)
class PlayerStatusEffects:
    """Run context and player ailments for the status corner panel."""

    floor_depth: int
    stunned: bool = False
    engulfed: bool = False
    extra_rows: tuple[StatusBonusRow, ...] = ()


def _format_bonus_value(value: float | int) -> str:
    if isinstance(value, float):
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"+{text}"
    return f"+{value}"


def _compact_stat_row(
    *,
    label: str,
    bonus_text: str | None,
    pieces: int,
    need: int,
    fg: tuple[int, int, int],
    max_width: int,
) -> StatusBonusRow | None:
    """Completed and/or partial piece progress on one compact line."""
    parts: list[str] = []
    if bonus_text:
        parts.append(f"{label} {bonus_text}")
    if pieces > 0 and need > 1:
        if bonus_text:
            parts.append(f"{pieces}/{need}")
        else:
            parts.append(f"{label} {pieces}/{need}")
    if not parts:
        return None
    return StatusBonusRow(" ".join(parts)[:max_width], fg)


def progression_extra_rows(
    progression: PlayerProgression,
    *,
    max_width: int = 10,
) -> tuple[StatusBonusRow, ...]:
    """Build rune bonus rows: completed first, then partials (drop past height)."""
    rows: list[StatusBonusRow] = []

    # Completed-only or compact completed+partial
    if progression.bonus_max_hp > 0 or progression.pieces_max_hp > 0:
        row = _compact_stat_row(
            label="HP",
            bonus_text=(
                f"+{progression.bonus_max_hp}" if progression.bonus_max_hp > 0 else None
            ),
            pieces=progression.pieces_max_hp,
            need=progression.pieces_need_max_hp,
            fg=STATUS_HP_FG,
            max_width=max_width,
        )
        if row:
            rows.append(row)

    if progression.bonus_accuracy > 0 or progression.pieces_accuracy > 0:
        bonus = (
            _format_bonus_value(progression.bonus_accuracy)
            if progression.bonus_accuracy > 0
            else None
        )
        row = _compact_stat_row(
            label="Acc",
            bonus_text=bonus,
            pieces=progression.pieces_accuracy,
            need=progression.pieces_need_accuracy,
            fg=STATUS_ACCURACY_FG,
            max_width=max_width,
        )
        if row:
            rows.append(row)

    min_dmg = progression.bonus_min_damage
    max_dmg = progression.bonus_max_damage
    dam_pieces = max(progression.pieces_min_damage, progression.pieces_max_damage)
    dam_need = max(
        progression.pieces_need_min_damage,
        progression.pieces_need_max_damage,
    )
    if min_dmg > 0 or max_dmg > 0 or dam_pieces > 0:
        if min_dmg > 0 or max_dmg > 0:
            if min_dmg == max_dmg:
                dam_bonus = f"+{min_dmg}"
            else:
                dam_bonus = f"+{min_dmg}-{max_dmg}"
        else:
            dam_bonus = None
        # Prefer min bank remainder for n/m display when both partial
        pieces = progression.pieces_min_damage or progression.pieces_max_damage
        need = (
            progression.pieces_need_min_damage
            if progression.pieces_min_damage > 0
            else progression.pieces_need_max_damage
        )
        if pieces <= 0:
            pieces, need = dam_pieces, dam_need
        row = _compact_stat_row(
            label="Dam",
            bonus_text=dam_bonus,
            pieces=pieces,
            need=need,
            fg=STATUS_DAMAGE_FG,
            max_width=max_width,
        )
        if row:
            rows.append(row)

    if progression.bonus_ac > 0 or progression.pieces_ac > 0:
        row = _compact_stat_row(
            label="AC",
            bonus_text=f"+{progression.bonus_ac}" if progression.bonus_ac > 0 else None,
            pieces=progression.pieces_ac,
            need=progression.pieces_need_ac,
            fg=STATUS_AC_FG,
            max_width=max_width,
        )
        if row:
            rows.append(row)

    if progression.bonus_evade > 0 or progression.pieces_evade > 0:
        if progression.bonus_evade > 0:
            be = progression.bonus_evade
            bonus_text = f"+{int(be)}" if float(be) == int(be) else f"+{be:g}"
        else:
            bonus_text = None
        row = _compact_stat_row(
            label="Ev",
            bonus_text=bonus_text,
            pieces=progression.pieces_evade,
            need=progression.pieces_need_evade,
            fg=STATUS_EVADE_FG,
            max_width=max_width,
        )
        if row:
            rows.append(row)

    return tuple(rows)


def player_effects_extra_rows(
    effects: PlayerEffects,
    *,
    max_width: int = 10,
) -> tuple[StatusBonusRow, ...]:
    """Temporary potion buff rows (Fast / Might / Ward / pending tele)."""
    rows: list[StatusBonusRow] = []
    if effects.haste_turns > 0:
        text = f"Fast {effects.haste_turns}"[:max_width]
        rows.append(StatusBonusRow(text, STATUS_FAST_FG))
    if effects.might_turns > 0:
        text = f"Might {effects.might_turns}"[:max_width]
        rows.append(StatusBonusRow(text, STATUS_MIGHT_FG))
    if effects.digestion_ward_turns > 0:
        label = "Antacid" if max_width >= 10 else "Antac"
        text = f"{label} {effects.digestion_ward_turns}"[:max_width]
        rows.append(StatusBonusRow(text, STATUS_WARD_FG))
    if effects.teleport_pending_turns is not None:
        text = f"Tele? {effects.teleport_pending_turns}"[:max_width]
        rows.append(StatusBonusRow(text, STATUS_TELE_FG))
    return tuple(rows)


def _depth_line(floor_depth: int, *, width: int) -> str:
    full = f"Depth {floor_depth}"
    if len(full) <= width:
        return full
    return f"D{floor_depth}"[:width]


def _status_rows(
    effects: PlayerStatusEffects,
    *,
    width: int,
) -> list[tuple[str, tuple[int, int, int]]]:
    rows: list[tuple[str, tuple[int, int, int]]] = []
    rows.append((_depth_line(effects.floor_depth, width=width), STATUS_DEPTH_FG))
    if effects.stunned:
        rows.append(("STUN", STATUS_STUNNED_FG))
    if effects.engulfed:
        rows.append(("ENGLF", STATUS_ENGULFED_FG))
    for bonus_row in effects.extra_rows:
        clipped = cp437_safe(bonus_row.text)[:width]
        if clipped:
            rows.append((clipped, bonus_row.fg))
    return rows


def render_status_corner(
    console: tcod.console.Console,
    effects: PlayerStatusEffects,
) -> None:
    """Draw depth + ailment rows into the status_corner sub-console."""
    console.draw_rect(
        0,
        0,
        console.width,
        console.height,
        ch=0,
        fg=None,
        bg=STATUS_CORNER_BACKGROUND,
    )
    line_limit = max(1, console.width)
    for row_index, (text, fg) in enumerate(_status_rows(effects, width=line_limit)):
        if row_index >= console.height:
            break
        console.print(0, row_index, text[:line_limit], fg=fg)