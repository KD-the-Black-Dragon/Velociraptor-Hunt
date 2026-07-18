"""Match combat: AP, balance, maneuvers/abilities from JSON, actual stats + injuries."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.components import Fighter
from src.constants import DATA_DIR
from src.injuries import InjuryInstance, injury_stat_multipliers, load_injury_config

MATCH_COMBAT_PATH = DATA_DIR / "match_combat.json"


@attrs.define(frozen=True)
class MatchAbilityDef:
    letter: str
    id: str
    name: str
    ap_cost: int
    aut_cost: float
    balance_delta: int
    description: str
    damage_mult: float = 1.0
    accuracy_mult: float = 1.0
    damage_mult_open: float | None = None
    accuracy_mult_open: float | None = None
    damage_mult_guarded: float | None = None
    accuracy_mult_guarded: float | None = None
    openness_threshold: float = 0.55
    turtle_damage_bonus: float = 1.0
    turtle_accuracy_bonus: float = 1.0
    push_tiles: int = 1


@attrs.define(frozen=True)
class ManeuverDef:
    id: str
    aut_cost: float = 1.0
    ap_cost: float = 0.0
    balance_delta: int = 0
    damage_mult: float = 1.0
    accuracy_mult: float = 1.0


@attrs.define(frozen=True)
class BalancePassiveConfig:
    overextended_start: int = 4
    cowering_start: int = -4
    extreme_acc_penalty: float = 0.15
    extreme_evade_penalty: float = 0.15
    extreme_damage_bonus: float = 0.2
    moderate_acc_bonus: float = 0.05
    moderate_evade_bonus: float = 0.05


@attrs.define(frozen=True)
class MatchCombatConfig:
    ap_max: float = 10.0
    ap_regen_per_aut: float = 1.0
    balance_min: int = -10
    balance_max: int = 10
    balance_on_wait: int = -1
    balance_on_step: int = 0
    balance_on_attack: int = 1
    balance_passive: BalancePassiveConfig = attrs.field(factory=BalancePassiveConfig)
    abilities: tuple[MatchAbilityDef, ...] = ()
    maneuvers: dict[str, ManeuverDef] = attrs.field(factory=dict)
    free_talk_refresh_aut: float = 1.0

    def maneuver(self, key: str) -> ManeuverDef:
        if key in self.maneuvers:
            return self.maneuvers[key]
        defaults = {
            "step": ManeuverDef("step", 0.45, 0, 0),
            "wait": ManeuverDef("wait", 1.0, 0, -1),
            "jab": ManeuverDef("jab", 1.0, 0, 1, 0.65, 1.15),
            "standard_attack": ManeuverDef("standard_attack", 1.2, 0, 1),
            "all_out": ManeuverDef("all_out", 1.5, 0, 2, 1.25, 1.05),
            "talk_paid": ManeuverDef("talk_paid", 1.0, 1, 0),
        }
        return defaults.get(key, ManeuverDef(key))


@attrs.define
class CombatantState:
    """Per-fighter match state (AP, balance, base combat numbers, injuries)."""

    ap: float
    ap_max: float
    ap_regen_per_aut: float
    balance: int
    base_accuracy: float
    base_evade: float
    base_ac: int
    base_min_damage: int
    base_max_damage: int
    base_max_hp: int = 30
    last_world_aut: float = 0.0
    injuries: list[InjuryInstance] = attrs.field(factory=list)
    # Recovery / down
    downed: bool = False
    recovery_bar: float = 0.0
    second_wind_uses_left: int = 1
    debuff_until_aut: float = -1.0
    debuff_accuracy_mult: float = 1.0
    debuff_evade_mult: float = 1.0

    @classmethod
    def from_fighter(
        cls,
        fighter: Fighter,
        cfg: MatchCombatConfig,
        *,
        world_aut: float = 0.0,
        injuries: list[InjuryInstance] | None = None,
        second_wind_uses: int = 1,
    ) -> CombatantState:
        return cls(
            ap=float(cfg.ap_max),
            ap_max=float(cfg.ap_max),
            ap_regen_per_aut=float(cfg.ap_regen_per_aut),
            balance=0,
            base_accuracy=float(fighter.accuracy),
            base_evade=float(fighter.evade),
            base_ac=int(fighter.ac),
            base_min_damage=int(fighter.min_damage),
            base_max_damage=int(fighter.max_damage),
            base_max_hp=int(fighter.max_hp),
            last_world_aut=float(world_aut),
            injuries=list(injuries or []),
            second_wind_uses_left=second_wind_uses,
        )

    def tick_ap(self, world_aut: float) -> None:
        if world_aut <= self.last_world_aut:
            self.last_world_aut = world_aut
            return
        elapsed = world_aut - self.last_world_aut
        self.last_world_aut = world_aut
        if self.ap_regen_per_aut <= 0 or self.downed:
            return
        self.ap = min(self.ap_max, self.ap + elapsed * self.ap_regen_per_aut)

    def spend_ap(self, cost: float) -> bool:
        if self.ap + 1e-9 < cost:
            return False
        self.ap = max(0.0, self.ap - cost)
        return True

    def shift_balance(self, delta: int, cfg: MatchCombatConfig) -> None:
        self.balance = max(
            cfg.balance_min,
            min(cfg.balance_max, self.balance + int(delta)),
        )


def actual_fighter(
    state: CombatantState,
    cfg: MatchCombatConfig,
    *,
    live_hp: int | None = None,
) -> Fighter:
    """Base → balance → injuries → temp debuffs. Always use for resolution."""
    bp = cfg.balance_passive
    bal = state.balance
    acc = state.base_accuracy
    evade = state.base_evade
    min_d = float(state.base_min_damage)
    max_d = float(state.base_max_damage)
    ac = float(state.base_ac)
    max_hp = float(state.base_max_hp)

    if 1 <= bal < bp.overextended_start:
        acc *= 1.0 + bp.moderate_acc_bonus
        min_d *= 1.0 + bp.moderate_acc_bonus * 0.5
        max_d *= 1.0 + bp.moderate_acc_bonus * 0.5
    elif bp.cowering_start < bal <= -1:
        evade *= 1.0 + bp.moderate_evade_bonus

    if bal >= bp.overextended_start:
        t = min(1.0, (bal - bp.overextended_start + 1) / 4.0)
        acc *= 1.0 - bp.extreme_acc_penalty * t
        evade *= 1.0 - bp.extreme_evade_penalty * t
        min_d *= 1.0 + bp.extreme_damage_bonus * t
        max_d *= 1.0 + bp.extreme_damage_bonus * t
    elif bal <= bp.cowering_start:
        t = min(1.0, (bp.cowering_start - bal + 1) / 4.0)
        acc *= 1.0 - bp.extreme_acc_penalty * t * 0.8
        evade *= 1.0 - bp.extreme_evade_penalty * t * 0.5
        min_d *= 1.0 - 0.15 * t
        max_d *= 1.0 - 0.15 * t

    inj_m = injury_stat_multipliers(state.injuries, cfg=load_injury_config())
    acc *= inj_m["accuracy"]
    evade *= inj_m["evade"]
    min_d *= inj_m["damage"]
    max_d *= inj_m["damage"]
    ac *= inj_m["ac"]
    max_hp *= inj_m["max_hp"]

    if state.debuff_until_aut >= 0:
        # caller must clear when world_aut exceeds; still apply if active
        acc *= state.debuff_accuracy_mult
        evade *= state.debuff_evade_mult

    hp = int(live_hp) if live_hp is not None else 0
    return Fighter(
        hp=hp,
        max_hp=max(1, int(round(max_hp))),
        accuracy=max(0.01, acc),
        evade=max(0.0, evade),
        ac=max(0, int(round(ac))),
        min_damage=max(0, int(round(min_d))),
        max_damage=max(0, int(round(max_d))),
    )


def step_aut_multiplier(state: CombatantState) -> float:
    inj_m = injury_stat_multipliers(state.injuries, cfg=load_injury_config())
    return float(inj_m.get("step_aut", 1.0))


def awareness_openness(defender_balance: int, defender_hp: int, defender_max_hp: int) -> float:
    if defender_balance <= -3:
        open_bal = 0.15
    elif defender_balance <= 0:
        open_bal = 0.35
    elif defender_balance >= 4:
        open_bal = 0.85
    else:
        open_bal = 0.55
    if defender_max_hp > 0:
        hp_frac = defender_hp / defender_max_hp
        open_hp = 1.0 - hp_frac * 0.5
    else:
        open_hp = 0.5
    return max(0.0, min(1.0, 0.55 * open_bal + 0.45 * open_hp))


def choose_bump_profile(openness: float) -> str:
    if openness < 0.35:
        return "jab"
    if openness >= 0.75:
        return "all_out"
    return "standard"


def _parse_maneuver(key: str, raw: dict[str, Any]) -> ManeuverDef:
    return ManeuverDef(
        id=key,
        aut_cost=float(raw.get("aut_cost", 1.0)),
        ap_cost=float(raw.get("ap_cost", 0)),
        balance_delta=int(raw.get("balance_delta", 0)),
        damage_mult=float(raw.get("damage_mult", 1.0)),
        accuracy_mult=float(raw.get("accuracy_mult", 1.0)),
    )


def _parse_ability(row: dict[str, Any]) -> MatchAbilityDef | None:
    letter = str(row.get("letter", "")).lower()[:1]
    if not letter:
        return None
    return MatchAbilityDef(
        letter=letter,
        id=str(row.get("id", letter)),
        name=str(row.get("name", letter)),
        ap_cost=int(row.get("ap_cost", 1)),
        aut_cost=float(row.get("aut_cost", 1.0)),
        balance_delta=int(row.get("balance_delta", 0)),
        description=str(row.get("description", "")),
        damage_mult=float(row.get("damage_mult", 1.0)),
        accuracy_mult=float(row.get("accuracy_mult", 1.0)),
        damage_mult_open=(
            float(row["damage_mult_open"]) if "damage_mult_open" in row else None
        ),
        accuracy_mult_open=(
            float(row["accuracy_mult_open"]) if "accuracy_mult_open" in row else None
        ),
        damage_mult_guarded=(
            float(row["damage_mult_guarded"]) if "damage_mult_guarded" in row else None
        ),
        accuracy_mult_guarded=(
            float(row["accuracy_mult_guarded"])
            if "accuracy_mult_guarded" in row
            else None
        ),
        openness_threshold=float(row.get("openness_threshold", 0.55)),
        turtle_damage_bonus=float(row.get("turtle_damage_bonus", 1.0)),
        turtle_accuracy_bonus=float(row.get("turtle_accuracy_bonus", 1.0)),
        push_tiles=int(row.get("push_tiles", 1)),
    )


def _parse_config(data: dict[str, Any]) -> MatchCombatConfig:
    bp_raw = data.get("balance_passive") or {}
    if not isinstance(bp_raw, dict):
        bp_raw = {}
    bp = BalancePassiveConfig(
        overextended_start=int(bp_raw.get("overextended_start", 4)),
        cowering_start=int(bp_raw.get("cowering_start", -4)),
        extreme_acc_penalty=float(bp_raw.get("extreme_acc_penalty", 0.15)),
        extreme_evade_penalty=float(bp_raw.get("extreme_evade_penalty", 0.15)),
        extreme_damage_bonus=float(bp_raw.get("extreme_damage_bonus", 0.2)),
        moderate_acc_bonus=float(bp_raw.get("moderate_acc_bonus", 0.05)),
        moderate_evade_bonus=float(bp_raw.get("moderate_evade_bonus", 0.05)),
    )
    abilities: list[MatchAbilityDef] = []
    for row in data.get("abilities") or []:
        if isinstance(row, dict):
            ab = _parse_ability(row)
            if ab:
                abilities.append(ab)
    maneuvers: dict[str, ManeuverDef] = {}
    man_raw = data.get("maneuvers") if isinstance(data.get("maneuvers"), dict) else {}
    free_talk = 1.0
    for key, val in man_raw.items():
        if key == "free_talk_refresh_aut":
            free_talk = float(val)
            continue
        if isinstance(val, dict):
            maneuvers[str(key)] = _parse_maneuver(str(key), val)
    if "free_talk_refresh_aut" in data:
        free_talk = float(data["free_talk_refresh_aut"])
    return MatchCombatConfig(
        ap_max=float(data.get("ap_max", 10)),
        ap_regen_per_aut=float(data.get("ap_regen_per_aut", 1.0)),
        balance_min=int(data.get("balance_min", -10)),
        balance_max=int(data.get("balance_max", 10)),
        balance_on_wait=int(data.get("balance_on_wait", -1)),
        balance_on_step=int(data.get("balance_on_step", 0)),
        balance_on_attack=int(data.get("balance_on_attack", 1)),
        balance_passive=bp,
        abilities=tuple(abilities),
        maneuvers=maneuvers,
        free_talk_refresh_aut=free_talk,
    )


@lru_cache(maxsize=1)
def load_match_combat_config(path: Path | None = None) -> MatchCombatConfig:
    p = path if path is not None else MATCH_COMBAT_PATH
    if not p.is_file():
        return MatchCombatConfig()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return MatchCombatConfig()
    return _parse_config(raw)


def reset_match_combat_cache() -> None:
    load_match_combat_config.cache_clear()


def ability_by_letter(cfg: MatchCombatConfig, letter: str) -> MatchAbilityDef | None:
    key = letter.lower()[:1]
    for ab in cfg.abilities:
        if ab.letter == key:
            return ab
    return None


def format_ap_meter(ap: float, ap_max: float, *, width: int = 10) -> str:
    if ap_max <= 0:
        return "[" + " " * width + "]"
    filled = int(round(width * max(0.0, min(1.0, ap / ap_max))))
    return "[" + ("#" * filled) + ("." * (width - filled)) + "]"


def format_balance_meter(balance: int, *, lo: int = -10, hi: int = 10, width: int = 11) -> str:
    if width % 2 == 0:
        width += 1
    mid = width // 2
    cells = ["."] * width
    cells[mid] = "|"
    span = max(1, hi - lo)
    pos = int(round((balance - lo) / span * (width - 1)))
    pos = max(0, min(width - 1, pos))
    cells[pos] = "D" if balance < 0 else ("A" if balance > 0 else "|")
    if balance == 0:
        cells[mid] = "N"
    return "[" + "".join(cells) + f"] {balance:+d}"


def format_recovery_meter(bar: float, full: float = 1.0, *, width: int = 10) -> str:
    if full <= 0:
        return "[" + " " * width + "]"
    filled = int(round(width * max(0.0, min(1.0, bar / full))))
    return "[" + ("=" * filled) + ("." * (width - filled)) + "]"
