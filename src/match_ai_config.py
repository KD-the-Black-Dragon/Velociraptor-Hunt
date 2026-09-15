"""Load Battle Sport AI / footwork / momentum JSON config."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

MATCH_AI_PATH = DATA_DIR / "match_ai.json"


@attrs.define(frozen=True)
class FootworkBalanceRule:
    low_threshold: int = -1
    delta_when_low: int = 2
    delta_when_not_low: int = 1
    ceiling: int = 8


@attrs.define(frozen=True)
class FootworkConfig:
    ap_cost_base: float = 1.5
    ap_cost_compound: float = 0.5
    aut_cost: float = 0.55
    balance_delta: int = 2
    compound_window_aut: float = 3.0
    max_chebyshev: int = 2
    balance: FootworkBalanceRule = attrs.field(factory=FootworkBalanceRule)

    def balance_delta_for(self, current_balance: int) -> int:
        """Aggression from footwork; cannot push past ceiling."""
        b = int(current_balance)
        rule = self.balance
        if b >= rule.ceiling:
            return 0
        if b <= rule.low_threshold:
            delta = rule.delta_when_low
        else:
            delta = rule.delta_when_not_low
        if b + delta > rule.ceiling:
            delta = rule.ceiling - b
        return int(max(0, delta))


@attrs.define(frozen=True)
class FeintConfig:
    aut_cost: float = 0.9
    balance_delta: int = 1
    ap_cost: float = 0.0


@attrs.define(frozen=True)
class MomentumConfig:
    duration_aut: float = 2.5
    evade_mult_same: float = 1.15
    evade_mult_side: float = 0.9
    evade_mult_reverse: float = 0.35


@attrs.define(frozen=True)
class MatchAiConfig:
    help_aggression_window_aut: float = 4.0
    order_solid_obey_aut: float = 10.0
    order_forget_ramp_aut: float = 20.0
    order_forget_chance_per_aut: float = 0.08
    help_call_heard_chance_swallow: float = 0.5
    morale_shock_aut_min: float = 8.0
    morale_shock_aut_max: float = 16.0
    morale_forced_ferocity_min: int = 0
    morale_forced_ferocity_max: int = 2
    tenacity_shock_pct_per_point: float = 0.10
    preferred_balance_by_ferocity: dict[int, int] = attrs.field(factory=dict)
    common_sense_balance_max: int = 8
    reset_pressure_balance: int = 9
    appetite_clinch_hp_frac: dict[int, float] = attrs.field(factory=dict)
    cunning_ability_weight: float = 0.12
    cunning_footwork_weight: float = 0.10
    ferocity_close_weight: float = 0.15
    noise: float = 0.35
    default_entity_attrs: dict[str, int] = attrs.field(factory=dict)
    player_default_weapon: str = "short_sword"
    footwork: FootworkConfig = attrs.field(factory=FootworkConfig)
    feint: FeintConfig = attrs.field(factory=FeintConfig)
    momentum: MomentumConfig = attrs.field(factory=MomentumConfig)
    entity_attr_overrides: dict[str, dict[str, Any]] = attrs.field(factory=dict)

    def preferred_balance(self, ferocity: int) -> int:
        f = max(0, min(10, int(ferocity)))
        if f in self.preferred_balance_by_ferocity:
            return int(self.preferred_balance_by_ferocity[f])
        return 0

    def appetite_hp_threshold(self, appetite: int) -> float:
        a = max(0, min(10, int(appetite)))
        if a in self.appetite_clinch_hp_frac:
            return float(self.appetite_clinch_hp_frac[a])
        return 0.5


def _parse(data: dict[str, Any]) -> MatchAiConfig:
    pref: dict[int, int] = {}
    for k, v in (data.get("preferred_balance_by_ferocity") or {}).items():
        pref[int(k)] = int(v)
    app: dict[int, float] = {}
    for k, v in (data.get("appetite_clinch_hp_frac") or {}).items():
        app[int(k)] = float(v)
    fw = data.get("footwork") or {}
    fe = data.get("feint") or {}
    mo = data.get("momentum") or {}
    defaults = data.get("default_entity_attrs") or {}
    overrides = data.get("entity_attr_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}
    return MatchAiConfig(
        help_aggression_window_aut=float(data.get("help_aggression_window_aut", 4.0)),
        order_solid_obey_aut=float(data.get("order_solid_obey_aut", 10.0)),
        order_forget_ramp_aut=float(data.get("order_forget_ramp_aut", 20.0)),
        order_forget_chance_per_aut=float(data.get("order_forget_chance_per_aut", 0.08)),
        help_call_heard_chance_swallow=float(
            data.get("help_call_heard_chance_swallow", 0.5)
        ),
        morale_shock_aut_min=float(data.get("morale_shock_aut_min", 8.0)),
        morale_shock_aut_max=float(data.get("morale_shock_aut_max", 16.0)),
        morale_forced_ferocity_min=int(data.get("morale_forced_ferocity_min", 0)),
        morale_forced_ferocity_max=int(data.get("morale_forced_ferocity_max", 2)),
        tenacity_shock_pct_per_point=float(
            data.get("tenacity_shock_pct_per_point", 0.10)
        ),
        preferred_balance_by_ferocity=pref,
        common_sense_balance_max=int(data.get("common_sense_balance_max", 8)),
        reset_pressure_balance=int(data.get("reset_pressure_balance", 9)),
        appetite_clinch_hp_frac=app,
        cunning_ability_weight=float(data.get("cunning_ability_weight", 0.12)),
        cunning_footwork_weight=float(data.get("cunning_footwork_weight", 0.10)),
        ferocity_close_weight=float(data.get("ferocity_close_weight", 0.15)),
        noise=float(data.get("noise", 0.35)),
        default_entity_attrs={str(k): int(v) for k, v in defaults.items()}
        if isinstance(defaults, dict)
        else {},
        player_default_weapon=str(data.get("player_default_weapon", "short_sword")),
        footwork=FootworkConfig(
            ap_cost_base=float(fw.get("ap_cost_base", 1.5)),
            ap_cost_compound=float(fw.get("ap_cost_compound", 0.5)),
            aut_cost=float(fw.get("aut_cost", 0.55)),
            balance_delta=int(fw.get("balance_delta", 2)),
            compound_window_aut=float(fw.get("compound_window_aut", 3.0)),
            max_chebyshev=int(fw.get("max_chebyshev", 2)),
            balance=FootworkBalanceRule(
                low_threshold=int((fw.get("balance") or {}).get("low_threshold", -1)),
                delta_when_low=int((fw.get("balance") or {}).get("delta_when_low", 2)),
                delta_when_not_low=int(
                    (fw.get("balance") or {}).get("delta_when_not_low", 1)
                ),
                ceiling=int((fw.get("balance") or {}).get("ceiling", 8)),
            ),
        ),
        feint=FeintConfig(
            aut_cost=float(fe.get("aut_cost", 0.9)),
            balance_delta=int(fe.get("balance_delta", 1)),
            ap_cost=float(fe.get("ap_cost", 0)),
        ),
        momentum=MomentumConfig(
            duration_aut=float(mo.get("duration_aut", 2.5)),
            evade_mult_same=float(mo.get("evade_mult_same", 1.15)),
            evade_mult_side=float(mo.get("evade_mult_side", 0.9)),
            evade_mult_reverse=float(mo.get("evade_mult_reverse", 0.35)),
        ),
        entity_attr_overrides={
            str(k): dict(v) for k, v in overrides.items() if isinstance(v, dict)
        },
    )


@lru_cache(maxsize=1)
def load_match_ai_config(path: Path | None = None) -> MatchAiConfig:
    p = path if path is not None else MATCH_AI_PATH
    if not p.is_file():
        return MatchAiConfig(
            preferred_balance_by_ferocity={i: max(-7, min(7, i - 5)) for i in range(11)},
            appetite_clinch_hp_frac={i: i / 10.0 for i in range(11)},
        )
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return MatchAiConfig()
    return _parse(raw)


def reset_match_ai_config_cache() -> None:
    load_match_ai_config.cache_clear()
