"""Runtime game version for crash reports and diagnostics."""

from __future__ import annotations

import platform
import tomllib
from importlib.metadata import PackageNotFoundError, version

from src.constants import PROJECT_ROOT


def get_game_version() -> str:
    """Resolve version: installed package metadata, then pyproject.toml, else dev."""
    for dist_name in ("velociraptor-hunt", "gladiavore", "kds-vore-roguelike"):
        try:
            return version(dist_name)
        except PackageNotFoundError:
            continue
    try:
        pyproject = PROJECT_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return str(data["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        pass
    return "dev"


GAME_VERSION = get_game_version()


def collect_platform_info() -> tuple[str, str]:
    """Return ``(platform_string, os_string)`` for crash report headers."""
    system = platform.system()
    release = platform.release()
    os_string = f"{system} {release}".strip()
    return platform.platform(), os_string