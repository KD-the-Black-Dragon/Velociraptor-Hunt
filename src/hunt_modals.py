"""Hunt end-of-run ASCII modals and belly overlay."""

from __future__ import annotations

import tcod.console

from src.text import cp437_safe
from src.ui.menu_dialog import DIALOG_BG, _draw_dialog_chrome

ENGULFED_OVERLAY_FG = (100, 20, 20)
_HUNTER_FG = (220, 220, 200)
_TITLE_FG = (255, 240, 210)
_BODY_FG = (255, 240, 210)
_FOOTER_FG = (180, 170, 150)

MODAL_FOOTER = "Enter or Esc"
_VOID_BG = (0, 0, 0)
_HASH_START = ENGULFED_OVERLAY_FG
_HASH_END = (28, 6, 6)
_HUNTER_END = (50, 20, 20)


def _lerp_rgb(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
    t: float,
) -> tuple[int, int, int]:
    t = min(1.0, max(0.0, t))
    return (
        int(round(a[0] + (b[0] - a[0]) * t)),
        int(round(a[1] + (b[1] - a[1]) * t)),
        int(round(a[2] + (b[2] - a[2]) * t)),
    )


def belly_fade_t(*, turns: int, total: int) -> float:
    """0 at first belly turn, 1 when digestion is due."""
    if total <= 1:
        return 1.0
    return min(1.0, max(0.0, float(turns) / float(total)))


def fill_loss_void(console: tcod.console.Console) -> None:
    """Full-black void; only @ and # fade, not the background."""
    console.draw_rect(
        0, 0, console.width, console.height, ch=ord(" "), fg=_VOID_BG, bg=_VOID_BG,
    )


def render_centered_modal(
    console: tcod.console.Console,
    lines: tuple[str, ...],
    *,
    title: str | None = None,
    footer: str = MODAL_FOOTER,
) -> None:
    """Opaque centered box (KDVR dialog chrome); body text is centered."""
    body = [cp437_safe(line) for line in lines if line is not None]
    title_s = cp437_safe(title) if title else ""
    footer_s = cp437_safe(footer)
    inner = max([len(s) for s in body] + [len(title_s), len(footer_s), 16])
    inner = min(inner, max(16, console.width - 8))
    rows = (1 if title_s else 0) + len(body) + 1
    box_w = min(console.width, inner + 4)
    box_h = min(console.height, rows + 4)
    x0 = max(0, (console.width - box_w) // 2)
    y0 = max(0, (console.height - box_h) // 2)
    _draw_dialog_chrome(console, x0, y0, box_w, box_h)
    text_w = max(1, box_w - 4)
    y = y0 + 2
    if title_s:
        console.print(
            x0 + 2, y, title_s[:text_w].center(text_w),
            fg=_TITLE_FG, bg=DIALOG_BG,
        )
        y += 1
    for line in body:
        if y >= y0 + box_h - 2:
            break
        console.print(
            x0 + 2, y, line[:text_w].center(text_w),
            fg=_BODY_FG, bg=DIALOG_BG,
        )
        y += 1
    console.print(
        x0 + 2, y0 + box_h - 2, footer_s[:text_w].center(text_w),
        fg=_FOOTER_FG, bg=DIALOG_BG,
    )


def render_belly_overlay(
    console: tcod.console.Console,
    *,
    origin_sx: int,
    origin_sy: int,
    fade_t: float = 0.0,
) -> None:
    """Eight `#` around the hunter-in-belly tile (raptor position on screen)."""
    hash_fg = _lerp_rgb(_HASH_START, _HASH_END, fade_t)
    hunter_fg = _lerp_rgb(_HUNTER_FG, _HUNTER_END, fade_t)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            x, y = origin_sx + dx, origin_sy + dy
            if 0 <= x < console.width and 0 <= y < console.height:
                console.print(x, y, "#", fg=hash_fg, bg=(0, 0, 0))
    if 0 <= origin_sx < console.width and 0 <= origin_sy < console.height:
        console.print(origin_sx, origin_sy, "@", fg=hunter_fg, bg=(0, 0, 0))
