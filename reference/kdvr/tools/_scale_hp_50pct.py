"""One-shot: scale HP-related data by +50% (ceil). Not part of runtime."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def scale(n: int | float) -> int:
    return math.ceil(n * 1.5)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    # Player starting HP
    path = DATA / "global_tuning.json"
    data = load(path)
    old = data["player"]["max_hp"]
    data["player"]["max_hp"] = scale(old)
    save(path, data)
    print(f"player max_hp: {old} -> {data['player']['max_hp']}")

    # Vitality rune
    path = DATA / "floor_runes.json"
    data = load(path)
    for rune in data["runes"]:
        effect = rune.get("effect") or {}
        if effect.get("type") == "max_hp" and "amount" in effect:
            old = effect["amount"]
            effect["amount"] = scale(old)
            print(f"rune {rune['id']}: {old} -> {effect['amount']}")
    save(path, data)

    # Healing potions
    path = DATA / "potions.json"
    data = load(path)
    for pot in data["potions"]:
        if "heal_amount" in pot:
            old = pot["heal_amount"]
            pot["heal_amount"] = scale(old)
            print(f"potion {pot['id']}: {old} -> {pot['heal_amount']}")
    save(path, data)

    # Prefix max_hp bonuses only
    path = DATA / "npc_prefixes.json"
    data = load(path)
    for pref in data["prefixes"]:
        sb = pref.get("stat_bonuses") or {}
        if "max_hp" in sb:
            old = sb["max_hp"]
            sb["max_hp"] = scale(old)
            print(f"prefix {pref['id']} max_hp: {old} -> {sb['max_hp']}")
    save(path, data)

    # All entities
    path = DATA / "entities.json"
    data = load(path)
    for ent in data["entities"]:
        if "max_hp" in ent:
            old = ent["max_hp"]
            ent["max_hp"] = scale(old)
            print(f"entity {ent['id']}: {old} -> {ent['max_hp']}")
    save(path, data)

    # Depth-scaling max_hp growth (evil curve additives)
    path = DATA / "depth_scaling.json"
    data = load(path)
    for diff_id, diff in data.get("difficulties", {}).items():
        stats = (diff.get("stats") or {}).get("max_hp")
        if not stats:
            continue
        for key in ("bank_amount", "per_floor"):
            if key in stats and stats[key]:
                old = stats[key]
                stats[key] = scale(old)
                print(f"depth_scaling {diff_id} max_hp.{key}: {old} -> {stats[key]}")
    save(path, data)
    print("done")


if __name__ == "__main__":
    main()
