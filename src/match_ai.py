"""Fuzzy personality AI for match enemies and allies (Battle Sport)."""

from __future__ import annotations

import random
from typing import Any, Callable

import attrs

from src.components import Fighter, Position
from src.match_ai_config import MatchAiConfig
from src.match_combat import CombatantState
from src.match_tactics import chebyshev
from src.weapon_measure import (
    attack_delay,
    effective_band,
    is_footwork_offset,
    measure_mult,
)


@attrs.define(frozen=True)
class AiIntent:
    kind: str  # keep_watch, brace, step, footwork, attack, ability, clinch
    score: float
    dx: int = 0
    dy: int = 0
    target_key: object | None = None
    ability_id: str | None = None
    profile: str = "standard_attack"


def roll_attrs(
    rng: random.Random,
    *,
    overrides: dict[str, Any] | None,
    defaults: dict[str, int],
) -> tuple[int, int, int, int, str, tuple[str, ...]]:
    o = overrides or {}

    def roll(min_k: str, max_k: str, fb: int) -> int:
        lo = int(o.get(min_k, defaults.get(min_k, fb)))
        hi = int(o.get(max_k, defaults.get(max_k, fb)))
        if hi < lo:
            lo, hi = hi, lo
        return int(rng.randint(lo, hi))

    fer = roll("min_ferocity", "max_ferocity", 5)
    cun = roll("min_cunning", "max_cunning", 5)
    ten = roll("min_tenacity", "max_tenacity", 5)
    app = roll("min_appetite", "max_appetite", 5)
    weapon = str(o.get("weapon_id", "") or "")
    abs_raw = o.get("abilities")
    abilities: tuple[str, ...] = ()
    if isinstance(abs_raw, list):
        abilities = tuple(str(x) for x in abs_raw)
    return fer, cun, ten, app, weapon, abilities


def maybe_start_morale_shock(
    state: CombatantState,
    live_hp: int,
    world_aut: float,
    cfg: MatchAiConfig,
    rng: random.Random,
) -> bool:
    """If enough HP lost since last shock end, apply morale shock. Returns True if started."""
    if state.morale_shock_until_aut >= 0 and world_aut < state.morale_shock_until_aut:
        return False
    # Clear expired
    if state.morale_shock_until_aut >= 0 and world_aut >= state.morale_shock_until_aut:
        state.morale_shock_until_aut = -1.0
        state.ferocity = state.true_ferocity
        state.hp_at_shock_end = live_hp

    baseline = state.hp_at_shock_end if state.hp_at_shock_end is not None else state.base_max_hp
    baseline = max(1, int(baseline))
    lost_frac = max(0.0, (baseline - live_hp) / float(max(1, state.base_max_hp)))
    # Tenacity N: shock after ~N*10% of max from baseline
    need = max(0.05, float(state.tenacity) * cfg.tenacity_shock_pct_per_point)
    if state.tenacity <= 0:
        need = 0.05  # paper cut
    if lost_frac + 1e-9 < need:
        return False
    dur = float(rng.uniform(cfg.morale_shock_aut_min, cfg.morale_shock_aut_max))
    state.morale_shock_until_aut = world_aut + dur
    forced = int(
        rng.randint(cfg.morale_forced_ferocity_min, cfg.morale_forced_ferocity_max)
    )
    state.ferocity = forced
    return True


def momentum_evade_mult(
    state: CombatantState,
    dodge_dx: int,
    dodge_dy: int,
    world_aut: float,
    cfg: MatchAiConfig,
) -> float:
    state.clear_expired_statuses(world_aut)
    if state.momentum_until_aut < 0 or world_aut >= state.momentum_until_aut:
        return 1.0
    mdx, mdy = state.momentum_dx, state.momentum_dy
    if mdx == 0 and mdy == 0:
        return 1.0
    # Dot product of direction signs
    def sgn(v: int) -> int:
        return (v > 0) - (v < 0)

    sx, sy = sgn(mdx), sgn(mdy)
    dx, dy = sgn(dodge_dx), sgn(dodge_dy)
    dot = sx * dx + sy * dy
    mo = cfg.momentum
    if dot > 0:
        return float(mo.evade_mult_same)
    if dot < 0:
        return float(mo.evade_mult_reverse)
    return float(mo.evade_mult_side)


def _noise(rng: random.Random, amount: float) -> float:
    return float(rng.uniform(-amount, amount))


def score_enemy_intents(
    *,
    rng: random.Random,
    ai_cfg: MatchAiConfig,
    state: CombatantState,
    pos: Position,
    targets: list[tuple[object, Position, Fighter]],
    world_aut: float,
    can_enter: Callable[[int, int], bool],
    can_clinch: bool,
) -> AiIntent:
    """Pick a fuzzy intent for an enemy (or free-play ally)."""
    state.clear_expired_statuses(world_aut)
    fer = state.effective_ferocity(world_aut)
    cun = state.cunning
    app = state.appetite if state.vore_capable else 0
    pref = ai_cfg.preferred_balance(fer)
    bal = state.balance
    candidates: list[AiIntent] = []

    # Reset pressure at extreme overextension
    if bal >= ai_cfg.reset_pressure_balance:
        candidates.append(AiIntent("keep_watch", 8.0 + _noise(rng, 0.2)))
        candidates.append(AiIntent("brace", 7.5 + _noise(rng, 0.2)))
        # slight chance to still attack if very high ferocity and bal only 9
        if fer >= 9 and bal <= 9:
            for tid, tpos, tf in targets:
                band = effective_band(pos, tpos)
                mm = measure_mult(state.weapon_id, band)
                if mm > 0.05 and band <= 4:
                    candidates.append(
                        AiIntent(
                            "attack",
                            2.0 + fer * 0.1 + _noise(rng, ai_cfg.noise),
                            target_key=tid,
                            profile="jab",
                        )
                    )
        return max(candidates, key=lambda c: c.score)

    # Balance home seek
    bal_err = bal - pref
    if bal_err > 2:
        candidates.append(AiIntent("brace", 3.0 + bal_err * 0.4 + _noise(rng, ai_cfg.noise)))
        candidates.append(AiIntent("keep_watch", 2.5 + bal_err * 0.3 + _noise(rng, ai_cfg.noise)))
    if bal_err < -2:
        # too defensive — poke
        for tid, tpos, tf in targets:
            band = effective_band(pos, tpos)
            if band <= 2:
                candidates.append(
                    AiIntent(
                        "attack",
                        3.0 - bal_err * 0.2 + _noise(rng, ai_cfg.noise),
                        target_key=tid,
                        profile="jab",
                    )
                )

    # Always option: keep watch / brace for low ferocity
    candidates.append(
        AiIntent(
            "keep_watch",
            1.5 + (5 - fer) * 0.35 + _noise(rng, ai_cfg.noise),
        )
    )
    candidates.append(
        AiIntent(
            "brace",
            1.0 + (5 - fer) * 0.4 + _noise(rng, ai_cfg.noise),
        )
    )

    best_target = None
    best_dist = 999
    for tid, tpos, tf in targets:
        d = chebyshev(pos, tpos)
        if d < best_dist:
            best_dist = d
            best_target = (tid, tpos, tf)

    if best_target is not None:
        tid, tpos, tf = best_target
        band = effective_band(pos, tpos)
        mm = measure_mult(state.weapon_id, band)
        ideal = 1 if measure_mult(state.weapon_id, 1) >= measure_mult(state.weapon_id, 2) else 2
        # prefer band with best mult
        for btry in (1, 2, 3, 4):
            if measure_mult(state.weapon_id, btry) > measure_mult(state.weapon_id, ideal):
                ideal = btry

        # Attack if in useful measure
        if mm >= 0.2 and band <= 4:
            bold = "all_out" if fer >= 8 else ("jab" if fer <= 3 else "standard_attack")
            atk_score = (
                2.0
                + mm * 3.0
                + fer * ai_cfg.ferocity_close_weight
                + (1.0 if band == ideal else 0.0)
                + _noise(rng, ai_cfg.noise)
            )
            # High ferocity prefers attacking when adjacent
            if band == 1:
                atk_score += fer * 0.25
            candidates.append(
                AiIntent("attack", atk_score, target_key=tid, profile=bold)
            )

        # Clinch
        if can_clinch and state.vore_capable and band == 1:
            hp_frac = tf.hp / max(1, tf.max_hp)
            thresh = ai_cfg.appetite_hp_threshold(app)
            if app <= 0:
                clinch_ok = tf.hp <= 0 or hp_frac <= 0.05
            else:
                clinch_ok = hp_frac <= thresh + 1e-9
            if clinch_ok:
                candidates.append(
                    AiIntent(
                        "clinch",
                        1.5 + app * 0.45 + (1.0 - hp_frac) * 2.0 + _noise(rng, ai_cfg.noise),
                        target_key=tid,
                    )
                )

        # Step toward / away
        dx = (tpos.x > pos.x) - (tpos.x < pos.x)
        dy = (tpos.y > pos.y) - (tpos.y < pos.y)
        if band > ideal and fer >= 3:
            tx, ty = pos.x + dx, pos.y + dy
            if can_enter(tx, ty):
                candidates.append(
                    AiIntent(
                        "step",
                        1.8 + fer * ai_cfg.ferocity_close_weight + _noise(rng, ai_cfg.noise),
                        dx=dx,
                        dy=dy,
                        target_key=tid,
                    )
                )
        if band < ideal or fer <= 2:
            # step away / side
            adx, ady = -dx, -dy
            if fer <= 2 and band <= 1:
                # brace preferred already; step back
                if can_enter(pos.x + adx, pos.y + ady):
                    candidates.append(
                        AiIntent(
                            "step",
                            2.5 + (5 - fer) * 0.3 + _noise(rng, ai_cfg.noise),
                            dx=adx,
                            dy=ady,
                        )
                    )
            elif band < ideal and can_enter(pos.x + adx, pos.y + ady):
                candidates.append(
                    AiIntent(
                        "step",
                        2.0 + _noise(rng, ai_cfg.noise),
                        dx=adx,
                        dy=ady,
                    )
                )

        # Footwork (cunning)
        if cun > 0:
            fw_rate = cun * ai_cfg.cunning_footwork_weight
            if cun <= 2:
                fw_rate *= 0.35
            for fdx in range(-2, 3):
                for fdy in range(-2, 3):
                    if not is_footwork_offset(fdx, fdy):
                        continue
                    nx, ny = pos.x + fdx, pos.y + fdy
                    if not can_enter(nx, ny):
                        continue
                    npos = Position(nx, ny)
                    nband = effective_band(npos, tpos)
                    nmm = measure_mult(state.weapon_id, nband)
                    improve = nmm - mm
                    # escape if low fer or low hp
                    escape = 0.0
                    if nband > band and fer <= 4:
                        escape = 1.0
                    score = (
                        fw_rate * 4.0
                        + improve * 3.0
                        + escape
                        + _noise(rng, ai_cfg.noise)
                    )
                    if score > 1.0:
                        candidates.append(
                            AiIntent(
                                "footwork",
                                score,
                                dx=fdx,
                                dy=fdy,
                                target_key=tid,
                            )
                        )

        # Abilities (cunning + kit)
        if cun > 0 and state.ability_ids and state.ap >= 2:
            ab_w = cun * ai_cfg.cunning_ability_weight
            if cun <= 2:
                ab_w *= 0.3
            for ab_id in state.ability_ids:
                if band == 1:
                    candidates.append(
                        AiIntent(
                            "ability",
                            1.2 + ab_w * 5.0 + _noise(rng, ai_cfg.noise),
                            target_key=tid,
                            ability_id=ab_id,
                        )
                    )

    if not candidates:
        return AiIntent("keep_watch", 1.0)
    return max(candidates, key=lambda c: c.score)


def score_ally_intents(
    *,
    rng: random.Random,
    ai_cfg: MatchAiConfig,
    state: CombatantState,
    pos: Position,
    player_pos: Position,
    order: str,
    enemies: list[tuple[object, Position, Fighter]],
    help_targets: set[object],
    world_aut: float,
    can_enter: Callable[[int, int], bool],
    can_clinch: bool,
) -> AiIntent:
    """Ally fuzzy scorer with order modifiers."""
    # Stay close / help_me filters
    effective_order = order
    if order == "help_me" and not help_targets:
        effective_order = "stay_close"

    # Bias target list
    targets = enemies
    if effective_order == "help_me" and help_targets:
        focused = [t for t in enemies if t[0] in help_targets]
        if focused:
            targets = focused

    intent = score_enemy_intents(
        rng=rng,
        ai_cfg=ai_cfg,
        state=state,
        pos=pos,
        targets=targets,
        world_aut=world_aut,
        can_enter=can_enter,
        can_clinch=can_clinch and state.vore_capable,
    )

    if effective_order == "stay_close":
        dist = chebyshev(pos, player_pos)
        if dist > 2:
            dx = (player_pos.x > pos.x) - (player_pos.x < pos.x)
            dy = (player_pos.y > pos.y) - (player_pos.y < pos.y)
            if can_enter(pos.x + dx, pos.y + dy):
                # Override toward player unless already a strong attack
                if intent.kind not in ("attack", "clinch", "ability") or dist > 3:
                    return AiIntent(
                        "step",
                        10.0,
                        dx=dx,
                        dy=dy,
                    )
        elif intent.kind == "step" and dist <= 2:
            # Prefer watch near player if step would leave bubble
            nx, ny = pos.x + intent.dx, pos.y + intent.dy
            if chebyshev(Position(nx, ny), player_pos) > 2:
                return AiIntent("keep_watch", 6.0)

    # Low tenacity + low HP → self-preservation (brace / step away)
    if enemies:
        live = None
        # approximate using first enemy's not needed — use state base
        pass
    return intent


def should_forget_order(
    issued_at: float,
    world_aut: float,
    cfg: MatchAiConfig,
    rng: random.Random,
) -> bool:
    elapsed = world_aut - issued_at
    if elapsed < cfg.order_solid_obey_aut:
        return False
    # Rising chance after solid period
    over = elapsed - cfg.order_solid_obey_aut
    chance = min(0.85, over * cfg.order_forget_chance_per_aut)
    return rng.random() < chance
