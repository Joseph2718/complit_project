"""Centralized asset loading: fonts and images.

All audio goes through ``game.audio`` — that module owns the mixer
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(ROOT, "fonts")
ART_DIR = os.path.join(ROOT, "assets", "art")

_fonts: Dict[tuple, pygame.font.Font] = {}
_images: Dict[str, pygame.Surface] = {}

# Single-family typographic system: Cormorant Garamond at several weights.
# A unified serif gives the game a museum-catalog feel; pygame cannot
# pick weights from a variable font, so we use the Roman face for Regular
# and SemiBold (bold=True), and the Italic face for italics.
FONT_ROMAN = os.path.join(FONTS_DIR, "CormorantGaramond-VF.ttf")
FONT_ITALIC = os.path.join(FONTS_DIR, "CormorantGaramond-Italic.ttf")


def get_font(role: str, size: int) -> pygame.font.Font:
    """Resolve a semantic role + size to a cached pygame Font.

    Roles:
      - ``display``: large-cap titles on the start screen and exhibit panel.
      - ``heading``: serif SemiBold for section heads.
      - ``body``:   long-form wrapped prose.
      - ``body_bold``: bold pulls inside a body paragraph (performer names).
      - ``italic``: italic prose (set-in quotes, register captions).
      - ``caption``: smaller body text (hints, metadata).
    """
    key = (role, size)
    if key in _fonts:
        return _fonts[key]

    font: pygame.font.Font
    if role == "italic":
        font = pygame.font.Font(FONT_ITALIC, size)
    else:
        font = pygame.font.Font(FONT_ROMAN, size)
        if role in ("display", "heading", "body_bold"):
            font.set_bold(True)
    _fonts[key] = font
    return font


def load_image(relpath: str) -> Optional[pygame.Surface]:
    """Load an image from assets/art/ if present. Missing files return None;
    callers are expected to fall back to procedural rendering."""
    if relpath in _images:
        return _images[relpath]
    full = os.path.join(ART_DIR, relpath)
    if not os.path.isfile(full):
        return None
    try:
        surf = pygame.image.load(full).convert_alpha()
    except pygame.error:
        return None
    _images[relpath] = surf
    return surf


