"""One-shot: strip dungeon imports from app.py for career-only product."""
from __future__ import annotations

from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src" / "app.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
out: list[str] = []
i = 0
prefixes = (
    "from src.engine import",
    "from src.arena import",
    "from src.depth_entry import",
    "from src.entity_entry import",
    "from src.macguffin_victory_confirm import",
)
while i < len(lines):
    line = lines[i]
    if any(line.startswith(p) for p in prefixes):
        # multi-line import
        buf = line
        while i < len(lines) and "(" in buf and ")" not in buf:
            i += 1
            if i < len(lines):
                buf += lines[i]
        i += 1
        continue
    out.append(line)
    i += 1
text = "".join(out)
if "from src.floor_prefetch import" not in text:
    text = text.replace(
        "from src.input_handlers import is_ctrl_q\n",
        "from src.floor_prefetch import FloorPrefetch, menu_prefetch_params\n"
        "from src.input_handlers import is_ctrl_q\n",
    )
# Type-only stubs so remaining annotations don't explode
if "GameEngine" not in text.split("class App")[0]:
    insert = (
        "from __future__ import annotations\n\n"
        "from typing import Any\n\n"
        "GameEngine = Any  # dungeon engine lives under reference/kdvr\n"
        "EngineEventResult = Any\n"
        "DepthEntryState = Any\n"
        "EntityEntryState = Any\n"
        "InventoryModalMode = Any\n"
    )
    # only if future annotations already there
    if "GameEngine = Any" not in text:
        text = text.replace(
            "from __future__ import annotations\n",
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            "# Dungeon types live under reference/kdvr; stubs keep career App importable.\n"
            "GameEngine = Any\n"
            "EngineEventResult = Any\n"
            "DepthEntryState = Any\n"
            "EntityEntryState = Any\n"
            "InventoryModalMode = Any\n",
            1,
        )
path.write_text(text, encoding="utf-8")
print("ok", path, "lines", len(text.splitlines()))
