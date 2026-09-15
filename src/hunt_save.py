"""Hunt run snapshot for the KDVR rotating autosave slot."""

from __future__ import annotations

import random
from typing import Any

from src.aut import AutScheduler
from src.hunt_facing import heading_from_facing
from src.hunt_map import HuntMap, HuntTerrain, collect_hide_spots
from src.hunt_raptor import HuntRaptor, RaptorMind, RAPTOR_ACTOR
from src.hunt_session import HUNTER_ACTOR, HuntMode, HuntSession
from src.hunt_stance import Gait
from src.hunt_weather import MudPrint, SoundMark
from src.save.store import SaveNotFoundError, SaveStore, SaveStoreError

HUNT_KIND = "hunt"


def snapshot_hunt(session: HuntSession) -> dict[str, Any]:
    if session.projectile_in_progress() or session.pending_shot is not None:
        session.flush_projectile()
    mmap = session.map
    raptor = session.raptor
    rng = session.rng if session.rng is not None else random.Random(session.seed)
    return {
        "kind": HUNT_KIND,
        "hunter_name": session.hunter_name,
        "weapon_id": session.weapon_id,
        "weapon_name": session.weapon_name,
        "difficulty_id": session.difficulty_id,
        "seed": session.seed,
        "player_x": session.player_x,
        "player_y": session.player_y,
        "facing": session.facing,
        "gait": session.gait.value,
        "aim_depth": session.aim_depth,
        "aim_heading_deg": session.aim_heading_deg,
        "run_fatigue": session.run_fatigue,
        "fatigue_recovery_streak": session.fatigue_recovery_streak,
        "ammo": session.ammo,
        "mode": session.mode.name,
        "cursor_x": session.cursor_x,
        "cursor_y": session.cursor_y,
        "notice": session.notice,
        "win_lines": list(session.win_lines),
        "time_over_win": session.time_over_win,
        "swallow_angle": session.swallow_angle,
        "belly_turns": session.belly_turns,
        "belly_cam_x": session.belly_cam_x,
        "belly_cam_y": session.belly_cam_y,
        "shots_fired": session.shots_fired,
        "shots_landed": session.shots_landed,
        "shots_perfect": session.shots_perfect,
        "shots_one_shot": session.shots_one_shot,
        "outcome": session.outcome,
        "hunter_ring": session.hunter_ring,
        "raptor_ring": session.raptor_ring,
        "last_known_x": session.last_known_x,
        "last_known_y": session.last_known_y,
        "rain_audio": session.rain_audio,
        "raptor_heard_xy": (
            list(session.raptor_heard_xy) if session.raptor_heard_xy is not None else None
        ),
        "world_aut": session.scheduler.world_aut,
        "ready_at": {
            HUNTER_ACTOR: session.scheduler.ready_at(HUNTER_ACTOR),
            RAPTOR_ACTOR: session.scheduler.ready_at(RAPTOR_ACTOR),
        },
        "rng": _rng_to_json(rng),
        "map": {
            "width": mmap.width,
            "height": mmap.height,
            "radius": mmap.radius,
            "center_x": mmap.center_x,
            "center_y": mmap.center_y,
            "tiles": [[t.value for t in row] for row in mmap.tiles],
        },
        "raptor": None if raptor is None else {
            "x": raptor.x,
            "y": raptor.y,
            "facing": raptor.facing,
            "hp": raptor.hp,
            "max_hp": raptor.max_hp,
            "gait": raptor.gait.value,
            "last_move_facing": raptor.last_move_facing,
            "shown_health": raptor.shown_health,
            "mind": attrs_mind(raptor.mind),
        },
        "prints": [
            {
                "x": p.x,
                "y": p.y,
                "facing": p.facing,
                "owner": p.owner,
                "placed_aut": p.placed_aut,
                "ttl": p.ttl,
            }
            for p in session.prints
        ],
        "sound_marks": [
            {
                "x": s.x,
                "y": s.y,
                "false_alarm": s.false_alarm,
                "expires_aut": s.expires_aut,
            }
            for s in session.sound_marks
        ],
    }


def attrs_mind(mind: RaptorMind) -> dict[str, Any]:
    return {
        "last_seen_x": mind.last_seen_x,
        "last_seen_y": mind.last_seen_y,
        "last_seen_facing": mind.last_seen_facing,
        "last_seen_aim": mind.last_seen_aim,
        "observations": mind.observations,
        "rotate_hits": mind.rotate_hits,
        "stare_streak": mind.stare_streak,
        "edge_hits": mind.edge_hits,
        "sound_events": mind.sound_events,
        "sound_reacts": mind.sound_reacts,
        "last_obs_facing": mind.last_obs_facing,
        "intent": mind.intent,
        "thought": mind.thought,
        "fix_x": mind.fix_x,
        "fix_y": mind.fix_y,
        "fix_aut": mind.fix_aut,
        "hunter_busy": mind.hunter_busy,
        "last_seen_heading": mind.last_seen_heading,
        "last_seen_cone": mind.last_seen_cone,
        "last_seen_half": mind.last_seen_half,
        "last_seen_grass": mind.last_seen_grass,
        "last_seen_blind": mind.last_seen_blind,
    }


def _rng_to_json(rng: random.Random) -> list[Any]:
    kind, mt, pos = rng.getstate()
    return [kind, list(mt), pos]


def _rng_from_json(raw: Any) -> random.Random:
    rng = random.Random()
    if not isinstance(raw, list) or len(raw) != 3:
        return rng
    kind, mt, pos = raw
    rng.setstate((kind, tuple(mt), pos))
    return rng


def _aim_heading_from_run(run: dict[str, Any]) -> float | None:
    raw = run.get("aim_heading_deg")
    if raw is not None:
        return float(raw)
    if int(run.get("aim_depth", 0)) > 0:
        return heading_from_facing(int(run.get("facing", 0)))
    return None


def hunt_from_snapshot(run: dict[str, Any]) -> HuntSession:
    map_raw = run.get("map") or {}
    tiles = [
        [HuntTerrain(cell) for cell in row]
        for row in map_raw.get("tiles") or []
    ]
    mmap = HuntMap(
        width=int(map_raw.get("width", 0)),
        height=int(map_raw.get("height", 0)),
        tiles=tiles,
        radius=float(map_raw.get("radius", 0.0)),
        center_x=int(map_raw.get("center_x", 0)),
        center_y=int(map_raw.get("center_y", 0)),
    )
    mmap.hide_spots = collect_hide_spots(mmap)
    raptor = None
    raw_r = run.get("raptor")
    if isinstance(raw_r, dict):
        mind_raw = raw_r.get("mind") if isinstance(raw_r.get("mind"), dict) else {}
        gait_r = str(raw_r.get("gait", "walk"))
        try:
            raptor_gait = Gait(gait_r)
        except ValueError:
            raptor_gait = Gait.WALK
        move_raw = raw_r.get("last_move_facing")
        last_move = int(move_raw) if move_raw is not None else None
        raptor = HuntRaptor(
            x=int(raw_r.get("x", 0)),
            y=int(raw_r.get("y", 0)),
            facing=int(raw_r.get("facing", 0)),
            hp=int(raw_r.get("hp", 100)),
            max_hp=int(raw_r.get("max_hp", 100)),
            gait=raptor_gait,
            last_move_facing=last_move,
            shown_health=(str(raw_r["shown_health"]) if raw_r.get("shown_health") else None),
            mind=RaptorMind(
                last_seen_x=mind_raw.get("last_seen_x"),
                last_seen_y=mind_raw.get("last_seen_y"),
                last_seen_facing=mind_raw.get("last_seen_facing"),
                last_seen_aim=int(mind_raw.get("last_seen_aim", 0)),
                observations=int(mind_raw.get("observations", 0)),
                rotate_hits=int(mind_raw.get("rotate_hits", 0)),
                stare_streak=int(mind_raw.get("stare_streak", 0)),
                edge_hits=int(mind_raw.get("edge_hits", 0)),
                sound_events=int(mind_raw.get("sound_events", 0)),
                sound_reacts=int(mind_raw.get("sound_reacts", 0)),
                last_obs_facing=mind_raw.get("last_obs_facing"),
                intent=str(mind_raw.get("intent", "wander")),
                thought=str(mind_raw.get("thought", "")),
                fix_x=(int(mind_raw["fix_x"]) if mind_raw.get("fix_x") is not None else None),
                fix_y=(int(mind_raw["fix_y"]) if mind_raw.get("fix_y") is not None else None),
                fix_aut=float(mind_raw.get("fix_aut", 0.0)),
                hunter_busy=int(mind_raw.get("hunter_busy", 0)),
                last_seen_heading=(
                    float(mind_raw["last_seen_heading"])
                    if mind_raw.get("last_seen_heading") is not None else None
                ),
                last_seen_cone=int(mind_raw.get("last_seen_cone", 12)),
                last_seen_half=float(mind_raw.get("last_seen_half", 55.0)),
                last_seen_grass=int(mind_raw.get("last_seen_grass", 2)),
                last_seen_blind=int(mind_raw.get("last_seen_blind", 0)),
            ),
        )
    heard = run.get("raptor_heard_xy")
    heard_xy = None
    if isinstance(heard, (list, tuple)) and len(heard) == 2:
        heard_xy = (int(heard[0]), int(heard[1]))
    gait_raw = str(run.get("gait", "walk"))
    try:
        gait = Gait(gait_raw)
    except ValueError:
        gait = Gait.WALK
    mode_raw = str(run.get("mode", "PLAY"))
    try:
        mode = HuntMode[mode_raw]
    except KeyError:
        mode = HuntMode.PLAY
    scheduler = AutScheduler(world_aut=float(run.get("world_aut", 0.0)))
    ready = run.get("ready_at") if isinstance(run.get("ready_at"), dict) else {}
    scheduler.register(HUNTER_ACTOR, ready_at=float(ready.get(HUNTER_ACTOR, scheduler.world_aut)))
    scheduler.register(RAPTOR_ACTOR, ready_at=float(ready.get(RAPTOR_ACTOR, scheduler.world_aut)))
    prints = [
        MudPrint(
            x=int(p.get("x", 0)),
            y=int(p.get("y", 0)),
            facing=int(p.get("facing", 0)),
            owner=str(p.get("owner", "")),
            placed_aut=float(p.get("placed_aut", 0.0)),
            ttl=float(p.get("ttl", 16.0)),
        )
        for p in run.get("prints") or []
        if isinstance(p, dict)
    ]
    marks = [
        SoundMark(
            x=int(s.get("x", 0)),
            y=int(s.get("y", 0)),
            false_alarm=bool(s.get("false_alarm", False)),
            expires_aut=float(s.get("expires_aut", 0.0)),
        )
        for s in run.get("sound_marks") or []
        if isinstance(s, dict)
    ]
    session = HuntSession(
        hunter_name=str(run.get("hunter_name", "")),
        weapon_id=str(run.get("weapon_id", "rifle")),
        weapon_name=str(run.get("weapon_name", "Bolt-action rifle")),
        difficulty_id=str(run.get("difficulty_id", "normal")),
        seed=int(run.get("seed") or 1),
        paddock=mmap,
        player_x=int(run.get("player_x", 0)),
        player_y=int(run.get("player_y", 0)),
        facing=int(run.get("facing", 0)),
        gait=gait,
        aim_depth=int(run.get("aim_depth", 0)),
        aim_heading_deg=_aim_heading_from_run(run),
        run_fatigue=int(run.get("run_fatigue", 0)),
        fatigue_recovery_streak=int(run.get("fatigue_recovery_streak", 0)),
        raptor=raptor,
        rng=_rng_from_json(run.get("rng")),
        ammo=int(run.get("ammo", 0)),
        mode=mode,
        cursor_x=int(run.get("cursor_x", 0)),
        cursor_y=int(run.get("cursor_y", 0)),
        notice=str(run.get("notice", "")),
        win_lines=tuple(str(x) for x in (run.get("win_lines") or ())),
        prints=prints,
        sound_marks=marks,
        raptor_heard_xy=heard_xy,
        last_known_x=(int(run["last_known_x"]) if run.get("last_known_x") is not None else None),
        last_known_y=(int(run["last_known_y"]) if run.get("last_known_y") is not None else None),
        rain_audio=float(run.get("rain_audio", 0.25)),
        hunter_ring=float(run.get("hunter_ring", 0.0)),
        raptor_ring=float(run.get("raptor_ring", 0.0)),
        time_over_win=bool(run.get("time_over_win", False)),
        swallow_angle=str(run.get("swallow_angle", "")),
        belly_turns=int(run.get("belly_turns", 0)),
        belly_cam_x=(int(run["belly_cam_x"]) if run.get("belly_cam_x") is not None else None),
        belly_cam_y=(int(run["belly_cam_y"]) if run.get("belly_cam_y") is not None else None),
        shots_fired=int(run.get("shots_fired", 0)),
        shots_landed=int(run.get("shots_landed", 0)),
        shots_perfect=int(run.get("shots_perfect", 0)),
        shots_one_shot=int(run.get("shots_one_shot", 0)),
        outcome=run.get("outcome"),
        scheduler=scheduler,
        restoring=True,
    )
    return session


def is_hunt_snapshot(run: dict[str, Any] | None) -> bool:
    return isinstance(run, dict) and run.get("kind") == HUNT_KIND


def load_hunt_snapshot(store: SaveStore) -> dict[str, Any] | None:
    try:
        run = store.load_best()
    except (SaveNotFoundError, SaveStoreError):
        return None
    if not is_hunt_snapshot(run):
        return None
    return run


def probe_hunt_save(store: SaveStore) -> bool:
    return load_hunt_snapshot(store) is not None
