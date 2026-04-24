"""Reusable UI primitives: wrapped text, panels, buttons, prompts.

All long copy must pass through ``wrap_text`` or ``draw_wrapped`` — never
blit raw strings — so that every placard and description honors the panel
width we actually designed the UI around.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import pygame

from .constants import (
    COL_GOLD,
    COL_GOLD_DIM,
    COL_INK,
    COL_INK_SOFT,
    COL_MUTED,
    COL_PAPER,
)


Color = Tuple[int, int, int]


def render_tracked(
    font: pygame.font.Font,
    text: str,
    color: Color,
    tracking: int = 3,
) -> pygame.Surface:
    """Render ``text`` with extra pixels of letter-spacing between every
    glyph. Used for museum-style uppercase title plates: 'GALLERY I'."""
    if not text:
        return font.render("", True, color)
    glyphs = [font.render(ch, True, color) for ch in text]
    w = sum(g.get_width() for g in glyphs) + tracking * max(0, len(glyphs) - 1)
    h = max(g.get_height() for g in glyphs)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    x = 0
    for g in glyphs:
        surf.blit(g, (x, 0))
        x += g.get_width() + tracking
    return surf


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Greedy word-wrap. Respects explicit ``\\n`` line breaks (useful for
    paragraph breaks within a single string)."""
    lines: List[str] = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
            continue
        words = paragraph.split(" ")
        cur = words[0]
        for w in words[1:]:
            candidate = cur + " " + w
            if font.size(candidate)[0] <= max_width:
                cur = candidate
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 4,
) -> int:
    """Render wrapped text at (x, y). Returns the y-coordinate immediately
    after the block — handy for stacking paragraphs."""
    lines = wrap_text(text, font, max_width)
    cy = y
    lh = font.get_height() + line_spacing
    for line in lines:
        if line:
            surf = font.render(line, True, color)
            surface.blit(surf, (x, cy))
        cy += lh
    return cy


def measure_wrapped_height(
    text: str, font: pygame.font.Font, max_width: int, line_spacing: int = 4
) -> int:
    lines = wrap_text(text, font, max_width)
    return max(1, len(lines)) * (font.get_height() + line_spacing)


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    bg: Color = COL_PAPER,
    border: Color = COL_INK,
    border_width: int = 2,
    shadow: bool = True,
    radius: int = 6,
) -> None:
    """Draw a museum placard panel: soft paper fill with an inked border.
    Optional drop shadow gives the sense of a card mounted on the wall."""
    if shadow:
        shadow_rect = rect.move(6, 6)
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, 70),
            shadow_surf.get_rect(),
            border_radius=radius,
        )
        surface.blit(shadow_surf, shadow_rect.topleft)
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, border_width, border_radius=radius)


def draw_hairline(
    surface: pygame.Surface, x1: int, y: int, x2: int, color: Color = COL_INK_SOFT
) -> None:
    pygame.draw.line(surface, color, (x1, y), (x2, y), 1)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    on_click: Optional[object] = None  # callable
    hot: bool = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        bg = COL_PAPER if not self.hot else (255, 249, 232)
        border = COL_GOLD if self.hot else COL_INK
        draw_panel(surface, self.rect, bg=bg, border=border, border_width=2, shadow=False, radius=3)
        label_surf = font.render(self.label, True, COL_INK)
        surface.blit(
            label_surf,
            label_surf.get_rect(center=self.rect.center),
        )


class Prompt:
    """A parchment toast anchored to a world position — used to show
    'Press E to inspect \u2014 "Song Title"' above an approachable exhibit.
    The prompt auto-sizes to the full text (no truncation), and flips
    its anchor when near a screen edge so it stays visible.
    """

    def __init__(self, text: str, font: pygame.font.Font) -> None:
        self.text = text
        self.font = font

    def draw(self, surface: pygame.Surface, cx: int, cy: int) -> None:
        label = self.font.render(self.text, True, COL_INK)
        pad_x, pad_y = 16, 10
        w = label.get_width() + 2 * pad_x
        h = label.get_height() + 2 * pad_y
        rect = pygame.Rect(0, 0, w, h)
        rect.midbottom = (cx, cy)
        # Clamp horizontally inside the surface.
        sw, sh = surface.get_size()
        rect.left = max(8, min(sw - rect.width - 8, rect.left))
        # Flip below if the top would clip off-screen.
        flipped = False
        if rect.top < 88:  # below the banner
            rect.top = cy + 8
            flipped = True
        # Soft shadow
        shadow = pygame.Rect(rect)
        shadow.move_ip(0, 3)
        shadow_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, shadow.topleft)
        # Parchment
        pygame.draw.rect(surface, COL_PAPER, rect, border_radius=8)
        pygame.draw.rect(surface, COL_GOLD, rect, 2, border_radius=8)
        surface.blit(label, (rect.x + pad_x, rect.y + pad_y))
        # Little tail pointing toward the anchor.
        tail_x = max(rect.left + 16, min(rect.right - 16, cx))
        if flipped:
            pygame.draw.polygon(
                surface, COL_PAPER,
                [(tail_x - 7, rect.top), (tail_x + 7, rect.top), (tail_x, rect.top - 7)],
            )
            pygame.draw.line(
                surface, COL_GOLD, (tail_x - 7, rect.top), (tail_x, rect.top - 7), 2,
            )
            pygame.draw.line(
                surface, COL_GOLD, (tail_x + 7, rect.top), (tail_x, rect.top - 7), 2,
            )
        else:
            pygame.draw.polygon(
                surface, COL_PAPER,
                [(tail_x - 7, rect.bottom), (tail_x + 7, rect.bottom), (tail_x, rect.bottom + 7)],
            )
            pygame.draw.line(
                surface, COL_GOLD, (tail_x - 7, rect.bottom), (tail_x, rect.bottom + 7), 2,
            )
            pygame.draw.line(
                surface, COL_GOLD, (tail_x + 7, rect.bottom), (tail_x, rect.bottom + 7), 2,
            )


def size_placard(
    text: str,
    body_font: pygame.font.Font,
    inner_width: int,
    *,
    header_height: int = 0,
    top_pad: int = 12,
    bottom_pad: int = 14,
    line_spacing: int = 4,
) -> int:
    """Compute the pixel height a placard needs to fit its wrapped body
    text, given the header height and vertical padding."""
    body = measure_wrapped_height(text, body_font, inner_width, line_spacing)
    return header_height + body + top_pad + bottom_pad


def truncate_to_width(text: str, font: pygame.font.Font, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text
    # binary-ish trim
    ell = "\u2026"
    lo, hi = 0, len(text)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid].rstrip() + ell
        if font.size(candidate)[0] <= max_width:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best or ell


__all__ = [
    "Button",
    "Prompt",
    "draw_hairline",
    "draw_panel",
    "draw_wrapped",
    "measure_wrapped_height",
    "render_tracked",
    "size_placard",
    "truncate_to_width",
    "wrap_text",
    "COL_GOLD",
    "COL_GOLD_DIM",
    "COL_INK",
    "COL_INK_SOFT",
    "COL_MUTED",
    "COL_PAPER",
]
