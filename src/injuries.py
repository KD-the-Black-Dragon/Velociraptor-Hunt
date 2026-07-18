"""Vague region injuries: Injured {Region}: {Severity} → actual-stat penalties."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

INJURIES_PATH = DATA_DIR / "injuries.json"

SEVERITY_ORDER: tuple[str, ...] = ("Minor", "Moderate", "Major")
REGIONS_DEFAULT: tuple[str, ...] = ("Arm", "Leg", "Head", "Torso")


@attrs.define(frozen=True)
class InjuryApplyConfig:
    solid_hit_hp_fraction_min: float = 0.12
    solid_hit_chance: float = 0.35
    critical_hit_hp_fraction_min: float = 0.28
    critical_hit_chance: float = 0.85
    critical_double_step_chance: float = 0.25


@attrs.define(frozen=True)
class InjuryConfig:
    regions: tuple[str, ...] = REGIONS_DEFAULT
    severities: tuple[str, ...] = SEVERITY_ORDER
    penalty_fraction: dict[str, float] = attrs.field(
        factory=lambda: {"Minor": 0.10, "Moderate": 0.20, "Major": 0.30}
    )
    region_effects: dict[str, dict[str, Any]] = attrs.field(factory=dict)
    apply: InjuryApplyConfig = attrs.field(factory=InjuryApplyConfig)
    heal_gold_per_step: dict[str, int] = attrs.field(
        factory=lambda: {"Minor": 40, "Moderate": 70, "Major": 110}
    )


@attrs.define
class InjuryInstance:
    """One region injury at a severity."""

    region: str
    severity: str

    def label(self) -> str:
        return f"Injured {self.region}: {self.severity}"

    def to_dict(self) -> dict[str, str]:
        return {"region": self.region, "severity": self.severity}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InjuryInstance:
        return cls(
            region=str(data.get("region") or "Torso"),
            severity=str(data.get("severity") or "Minor"),
        )


def _parse_config(raw: dict[str, Any]) -> InjuryConfig:
    apply_raw = raw.get("apply") if isinstance(raw.get("apply"), dict) else {}
    apply = InjuryApplyConfig(
        solid_hit_hp_fraction_min=float(
            apply_raw.get("solid_hit_hp_fraction_min", 0.12)
        ),
        solid_hit_chance=float(apply_raw.get("solid_hit_chance", 0.35)),
        critical_hit_hp_fraction_min=float(
            apply_raw.get("critical_hit_hp_fraction_min", 0.28)
        ),
        critical_hit_chance=float(apply_raw.get("critical_hit_chance", 0.85)),
        critical_double_step_chance=float(
            apply_raw.get("critical_double_step_chance", 0.25)
        ),
    )
    pen = raw.get("penalty_fraction") if isinstance(raw.get("penalty_fraction"), dict) else {}
    heal = raw.get("heal_gold_per_step") if isinstance(raw.get("heal_gold_per_step"), dict) else {}
    effects = raw.get("region_effects") if isinstance(raw.get("region_effects"), dict) else {}
    regions = tuple(raw.get("regions") or REGIONS_DEFAULT)
    severities = tuple(raw.get("severities") or SEVERITY_ORDER)
    return InjuryConfig(
        regions=regions,
        severities=severities,
        penalty_fraction={
            "Minor": float(pen.get("Minor", 0.10)),
            "Moderate": float(pen.get("Moderate", 0.20)),
            "Major": float(pen.get("Major", 0.30)),
        },
        region_effects={str(k): dict(v) for k, v in effects.items() if isinstance(v, dict)},
        apply=apply,
        heal_gold_per_step={
            "Minor": int(heal.get("Minor", 40)),
            "Moderate": int(heal.get("Moderate", 70)),
            "Major": int(heal.get("Major", 110)),
        },
    )


@lru_cache(maxsize=1)
def load_injury_config(path: Path | None = None) -> InjuryConfig:
    p = path if path is not None else INJURIES_PATH
    if not p.is_file():
        return InjuryConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return InjuryConfig()
    return _parse_config(raw)


def reset_injury_config_cache() -> None:
    load_injury_config.cache_clear()


def severity_index(severity: str, cfg: InjuryConfig | None = None) -> int:
    c = cfg or load_injury_config()
    try:
        return list(c.severities).index(severity)
    except ValueError:
        return 0


def severity_at(index: int, cfg: InjuryConfig | None = None) -> str:
    c = cfg or load_injury_config()
    idx = max(0, min(len(c.severities) - 1, index))
    return c.severities[idx]


def find_injury(injuries: list[InjuryInstance], region: str) -> InjuryInstance | None:
    for inj in injuries:
        if inj.region == region:
            return inj
    return None


def step_injury(
    injuries: list[InjuryInstance],
    region: str,
    *,
    steps: int = 1,
    cfg: InjuryConfig | None = None,
) -> tuple[list[InjuryInstance], str | None]:
    """Aggravate or create injury on region by ``steps``. Returns (list, new label or None)."""
    c = cfg or load_injury_config()
    if region not in c.regions:
        region = c.regions[0] if c.regions else "Torso"
    steps = max(1, int(steps))
    existing = find_injury(injuries, region)
    if existing is None:
        new_sev = severity_at(steps - 1, c)
        inst = InjuryInstance(region=region, severity=new_sev)
        return [*injuries, inst], inst.label()
    idx = severity_index(existing.severity, c) + steps
    if idx >= len(c.severities):
        idx = len(c.severities) - 1
    # Cap at Major — still "stepped"
    new_sev = severity_at(idx, c)
    if new_sev == existing.severity and idx >= len(c.severities) - 1:
        return injuries, None  # already Major
    updated = [
        InjuryInstance(region=region, severity=new_sev)
        if i.region == region
        else i
        for i in injuries
    ]
    return updated, f"Injured {region}: {new_sev}"


def heal_one_step(
    injuries: list[InjuryInstance],
    region: str,
    *,
    cfg: InjuryConfig | None = None,
) -> tuple[list[InjuryInstance], int, str | None]:
    """Heal one severity step on region. Returns (list, gold_cost, message)."""
    c = cfg or load_injury_config()
    existing = find_injury(injuries, region)
    if existing is None:
        return injuries, 0, None
    cost = int(c.heal_gold_per_step.get(existing.severity, 50))
    idx = severity_index(existing.severity, c)
    if idx <= 0:
        # Remove Minor entirely
        new_list = [i for i in injuries if i.region != region]
        return new_list, cost, f"Cleared Injured {region}: Minor"
    new_sev = severity_at(idx - 1, c)
    new_list = [
        InjuryInstance(region=region, severity=new_sev)
        if i.region == region
        else i
        for i in injuries
    ]
    return new_list, cost, f"Injured {region}: {new_sev}"


def try_apply_from_hit(
    injuries: list[InjuryInstance],
    *,
    damage: int,
    defender_max_hp: int,
    rng: random.Random,
    cfg: InjuryConfig | None = None,
) -> tuple[list[InjuryInstance], str | None]:
    """Maybe add/aggravate injury from a single blow. No gore text."""
    c = cfg or load_injury_config()
    if defender_max_hp <= 0 or damage <= 0:
        return injuries, None
    frac = damage / defender_max_hp
    apply = c.apply
    if frac < apply.solid_hit_hp_fraction_min:
        return injuries, None

    if frac >= apply.critical_hit_hp_fraction_min:
        if rng.random() > apply.critical_hit_chance:
            return injuries, None
        steps = 1
        if rng.random() < apply.critical_double_step_chance:
            steps = 2
    else:
        if rng.random() > apply.solid_hit_chance:
            return injuries, None
        steps = 1

    region = rng.choice(list(c.regions)) if c.regions else "Torso"
    # Prefer aggravating an existing random injury half the time if any
    if injuries and rng.random() < 0.45:
        region = rng.choice([i.region for i in injuries])
    return step_injury(injuries, region, steps=steps, cfg=c)


def injury_stat_multipliers(
    injuries: list[InjuryInstance],
    *,
    cfg: InjuryConfig | None = None,
) -> dict[str, float]:
    """Combined multipliers for accuracy, damage, evade, step_aut, max_hp, ac."""
    c = cfg or load_injury_config()
    mult = {
        "accuracy": 1.0,
        "damage": 1.0,
        "evade": 1.0,
        "step_aut": 1.0,
        "max_hp": 1.0,
        "ac": 1.0,
    }
    for inj in injuries:
        pen = float(c.penalty_fraction.get(inj.severity, 0.1))
        effects = c.region_effects.get(inj.region) or {}
        if effects.get("accuracy") or effects.get("mentality"):
            mult["accuracy"] *= 1.0 - pen
        if effects.get("damage"):
            mult["damage"] *= 1.0 - pen
        if effects.get("evade"):
            mult["evade"] *= 1.0 - pen
        if effects.get("step_aut_mult"):
            mult["step_aut"] *= 1.0 + pen  # slower move
        if effects.get("max_hp_fraction"):
            mult["max_hp"] *= 1.0 - pen * 0.5  # milder on max hp display/cap
        if effects.get("ac"):
            mult["ac"] *= 1.0 - pen
    return mult


def injuries_from_dicts(raw: list[Any] | None) -> list[InjuryInstance]:
    if not raw:
        return []
    out: list[InjuryInstance] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(InjuryInstance.from_dict(item))
    return out


def injuries_to_dicts(injuries: list[InjuryInstance]) -> list[dict[str, str]]:
    return [i.to_dict() for i in injuries]


def format_injury_list(injuries: list[InjuryInstance]) -> list[str]:
    return [i.label() for i in injuries]
