"""Thin patron system: 3 patrons, per-match objectives, gold bonus on hit."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

PATRONS_PATH = DATA_DIR / "patrons.json"


@attrs.define(frozen=True)
class PatronDef:
    patron_id: str
    name: str
    epithet: str
    tone: str = ""


@attrs.define(frozen=True)
class ObjectiveDef:
    objective_id: str
    label: str
    bonus_gold: int
    kind: str  # win | win_under_aut | win_no_pc_down | win_allies_alive | win_after_talk
    requires_kind: str | None = None  # green | red | None
    requires_allies: bool = False
    max_aut: float | None = None


@attrs.define(frozen=True)
class ActivePatronObjective:
    """Assigned for one match."""

    patron_id: str
    patron_name: str
    patron_epithet: str
    objective_id: str
    label: str
    bonus_gold: int
    kind: str
    max_aut: float | None = None

    def hub_line(self) -> str:
        return (
            f"{self.patron_name} ({self.patron_epithet}): {self.label} "
            f"(+{self.bonus_gold} gold)"
        )

    def short_line(self) -> str:
        return f"{self.patron_name}: {self.label} (+{self.bonus_gold}g)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "patron_id": self.patron_id,
            "patron_name": self.patron_name,
            "patron_epithet": self.patron_epithet,
            "objective_id": self.objective_id,
            "label": self.label,
            "bonus_gold": self.bonus_gold,
            "kind": self.kind,
            "max_aut": self.max_aut,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActivePatronObjective | None:
        if not data:
            return None
        return cls(
            patron_id=str(data.get("patron_id") or ""),
            patron_name=str(data.get("patron_name") or "Patron"),
            patron_epithet=str(data.get("patron_epithet") or ""),
            objective_id=str(data.get("objective_id") or ""),
            label=str(data.get("label") or "Win"),
            bonus_gold=int(data.get("bonus_gold", 0)),
            kind=str(data.get("kind") or "win"),
            max_aut=(
                float(data["max_aut"])
                if data.get("max_aut") is not None
                else None
            ),
        )


@attrs.define(frozen=True)
class PatronsConfig:
    patrons: tuple[PatronDef, ...] = ()
    objectives: tuple[ObjectiveDef, ...] = ()


@attrs.define
class MatchPatronStats:
    """Facts collected during a match for objective evaluation."""

    pc_was_downed: bool = False
    talk_used: bool = False
    ally_was_lost: bool = False  # digested / red permanent or green down
    end_kind: str = ""  # win | loss | surrender | digested
    world_aut: float = 0.0


@lru_cache(maxsize=1)
def load_patrons_config(path: Path | None = None) -> PatronsConfig:
    p = path if path is not None else PATRONS_PATH
    if not p.is_file():
        return _fallback()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback()
    return _parse(raw)


def reset_patrons_cache() -> None:
    load_patrons_config.cache_clear()


def _fallback() -> PatronsConfig:
    patrons = (
        PatronDef("vex", "Lady Vex", "the Blood Sport", "cruel"),
        PatronDef("halm", "Patron Halm", "of the Mercy Seat", "measured"),
        PatronDef("rusk", "Gold-Finger Rusk", "of the Coin Pit", "greedy"),
    )
    objectives = (
        ObjectiveDef("win_any", "Win the bout", 25, "win"),
        ObjectiveDef("win_red", "Win a red match", 35, "win", requires_kind="red"),
        ObjectiveDef(
            "win_fast", "Win before 14 AUT", 40, "win_under_aut", max_aut=14.0
        ),
    )
    return PatronsConfig(patrons=patrons, objectives=objectives)


def _parse(raw: dict[str, Any]) -> PatronsConfig:
    patrons: list[PatronDef] = []
    for item in raw.get("patrons") or []:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "")
        if not pid:
            continue
        patrons.append(
            PatronDef(
                patron_id=pid,
                name=str(item.get("name") or pid),
                epithet=str(item.get("epithet") or ""),
                tone=str(item.get("tone") or ""),
            )
        )
    objectives: list[ObjectiveDef] = []
    for item in raw.get("objectives") or []:
        if not isinstance(item, dict):
            continue
        oid = str(item.get("id") or "")
        if not oid:
            continue
        rk = item.get("requires_kind")
        requires_kind = str(rk).lower() if rk else None
        if requires_kind not in ("green", "red"):
            requires_kind = None
        max_aut = item.get("max_aut")
        objectives.append(
            ObjectiveDef(
                objective_id=oid,
                label=str(item.get("label") or oid),
                bonus_gold=max(0, int(item.get("bonus_gold", 0))),
                kind=str(item.get("kind") or "win"),
                requires_kind=requires_kind,
                requires_allies=bool(item.get("requires_allies", False)),
                max_aut=float(max_aut) if max_aut is not None else None,
            )
        )
    if not patrons or not objectives:
        return _fallback()
    return PatronsConfig(patrons=tuple(patrons), objectives=tuple(objectives))


def objective_eligible(
    obj: ObjectiveDef,
    *,
    card_kind: str,
    has_deployed_allies: bool,
) -> bool:
    """Sanity-check: never assign impossible objectives for this bout."""
    if obj.requires_kind is not None and obj.requires_kind != card_kind:
        return False
    if obj.requires_allies and not has_deployed_allies:
        return False
    return True


def assign_patron_objective(
    *,
    card_kind: str,
    has_deployed_allies: bool,
    rng: random.Random,
    cfg: PatronsConfig | None = None,
) -> ActivePatronObjective | None:
    """Pick a patron + eligible objective for this match."""
    c = cfg if cfg is not None else load_patrons_config()
    if not c.patrons:
        return None
    eligible = [
        o
        for o in c.objectives
        if objective_eligible(
            o, card_kind=card_kind, has_deployed_allies=has_deployed_allies
        )
    ]
    if not eligible:
        # Always can at least win
        eligible = [o for o in c.objectives if o.kind == "win" and not o.requires_kind]
    if not eligible:
        eligible = list(c.objectives)
    if not eligible:
        return None
    patron = rng.choice(list(c.patrons))
    obj = rng.choice(eligible)
    label = obj.label
    if obj.max_aut is not None and "{max_aut}" in label:
        label = label.replace("{max_aut}", str(int(obj.max_aut)))
    return ActivePatronObjective(
        patron_id=patron.patron_id,
        patron_name=patron.name,
        patron_epithet=patron.epithet,
        objective_id=obj.objective_id,
        label=label,
        bonus_gold=obj.bonus_gold,
        kind=obj.kind,
        max_aut=obj.max_aut,
    )


def evaluate_objective(
    active: ActivePatronObjective | None,
    stats: MatchPatronStats,
) -> tuple[bool, int, str]:
    """
    Returns (hit, bonus_gold, recap_line).
    Miss = no bonus; never a penalty.
    """
    if active is None:
        return False, 0, ""
    hit = _check(active, stats)
    if hit:
        line = (
            f"{active.patron_name}: objective met — {active.label} "
            f"(+{active.bonus_gold} gold)"
        )
        return True, active.bonus_gold, line
    line = (
        f"{active.patron_name}: objective missed — {active.label} "
        f"(no bonus)"
    )
    return False, 0, line


def _check(active: ActivePatronObjective, stats: MatchPatronStats) -> bool:
    won = stats.end_kind == "win"
    if active.kind == "win":
        return won
    if active.kind == "win_under_aut":
        if not won:
            return False
        limit = active.max_aut if active.max_aut is not None else 999.0
        return stats.world_aut <= limit
    if active.kind == "win_no_pc_down":
        return won and not stats.pc_was_downed
    if active.kind == "win_allies_alive":
        return won and not stats.ally_was_lost
    if active.kind == "win_after_talk":
        return won and stats.talk_used
    # Unknown kinds: treat as win-only
    return won


def format_patrons_roster_line(cfg: PatronsConfig | None = None) -> str:
    c = cfg if cfg is not None else load_patrons_config()
    if not c.patrons:
        return ""
    names = ", ".join(f"{p.name}" for p in c.patrons)
    return f"Patrons: {names}"
