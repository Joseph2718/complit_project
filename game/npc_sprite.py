"""Sprite-sheet rendering for NPCs.

Supports two layouts that share a common 3-frame walk × 4-direction
internal model:

* **Single-character sheet** (e.g. ``mario.png``) at 3x4 cells.
* **RPG Maker VX Ace charset** (e.g. ``lpc_set_a.png``) at 12x8 cells,
  containing 8 separate 3x4 character blocks.

A ``SpriteConfig`` captures the sheet path, cell size, the (col, row)
offset of the desired character within the sheet, and a row-mapping
that maps a cardinal direction to a sheet row. This lets us mix sheets
with different facing-row conventions (LPC: down/left/right/up; the
existing scholar: down/right/left/up).

Frames are cached the first time each (config, dir, col) tuple is
requested, so subsequent queries are pointer-cheap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import pygame

from .assets import load_image


# Standard direction tuples. The NPC stores facing as one of these.
DOWN: Tuple[int, int] = (0, 1)
LEFT: Tuple[int, int] = (-1, 0)
RIGHT: Tuple[int, int] = (1, 0)
UP: Tuple[int, int] = (0, -1)


# Liberated Pixel Cup row order: down, left, right, up.
LPC_ROWS: Dict[Tuple[int, int], int] = {
    DOWN: 0, LEFT: 1, RIGHT: 2, UP: 3,
}

# Existing scholar / Mario ripped charset use this same convention.
STANDARD_ROWS = LPC_ROWS

# Pendulum walk: step-A → idle → step-B → idle.
WALK_CYCLE: Tuple[int, int, int, int] = (0, 1, 2, 1)


@dataclass(frozen=True)
class SpriteConfig:
    """Identifies one character within a sprite sheet."""
    path: str
    cell_w: int = 48
    cell_h: int = 48
    char_col: int = 0          # leftmost column of this character's 3x4 block
    char_row: int = 0          # topmost row of this character's 3x4 block
    target_h: int = 80         # rendered height in pixels (preserves aspect)
    rows: Dict[Tuple[int, int], int] = field(default_factory=lambda: dict(LPC_ROWS))
    idle_col: int = 1          # column index used when not walking


_FRAME_CACHE: Dict[Tuple[str, int, int, int, int, int], pygame.Surface] = {}


def _frame(cfg: SpriteConfig, row: int, col: int) -> Optional[pygame.Surface]:
    """Return the cached, scaled frame for (config, row, col) — both
    indices are *within the character block*, so row 0..3 and col 0..2."""
    key = (cfg.path, cfg.cell_w, cfg.cell_h, cfg.char_col + col, cfg.char_row + row, cfg.target_h)
    cached = _FRAME_CACHE.get(key)
    if cached is not None:
        return cached
    sheet = load_image(cfg.path)
    if sheet is None:
        return None
    src_x = (cfg.char_col + col) * cfg.cell_w
    src_y = (cfg.char_row + row) * cfg.cell_h
    cell = sheet.subsurface(pygame.Rect(src_x, src_y, cfg.cell_w, cfg.cell_h)).copy()
    target_w = int(round(cfg.target_h * cfg.cell_w / cfg.cell_h))
    scaled = pygame.transform.scale(cell, (target_w, cfg.target_h))
    _FRAME_CACHE[key] = scaled
    return scaled


def _cardinal(facing: Tuple[float, float]) -> Tuple[int, int]:
    """Snap a facing vector to its nearest cardinal."""
    fx, fy = facing
    if fx == 0 and fy == 0:
        return DOWN
    if abs(fx) >= abs(fy):
        return RIGHT if fx > 0 else LEFT
    return DOWN if fy > 0 else UP


def render(
    cfg: SpriteConfig,
    facing: Tuple[float, float],
    walk_phase: float,
    is_walking: bool,
) -> Optional[pygame.Surface]:
    """Pick the right frame for the given facing + walk state."""
    row = cfg.rows.get(_cardinal(facing), 0)
    if is_walking:
        col = WALK_CYCLE[int(walk_phase * 7.0) % len(WALK_CYCLE)]
    else:
        col = cfg.idle_col
    return _frame(cfg, row, col)


# ---------------------------------------------------------------------
# Pre-defined NPC sprite catalogue
# ---------------------------------------------------------------------

# Each LPC sheet is 12x8 cells; 8 characters per sheet arranged as
# 4 across the top half (rows 0..3) and 4 across the bottom half (4..7).
# A character's 3x4 block starts at (char_col, char_row) where
# char_col ∈ {0, 3, 6, 9} and char_row ∈ {0, 4}.

_NPC_H = 60   # slightly smaller than the player (80) so they read as background


def _lpc_chars(path: str):
    out = []
    for row in (0, 4):
        for col in (0, 3, 6, 9):
            out.append(SpriteConfig(path=path, char_col=col, char_row=row, target_h=_NPC_H))
    return out


LPC_A = _lpc_chars("sprites/npcs/lpc_set_a.png")
LPC_B = _lpc_chars("sprites/npcs/lpc_set_b.png")
LPC_C = _lpc_chars("sprites/npcs/lpc_set_c.png")

# Curated museum-appropriate NPC pool.
# Only plain-clothes civilian LPC characters — no armor, weapons, or fantasy gear.
GENERIC_NPCS = [
    LPC_A[0],   # dark hair, casual shirt — contemporary male
    LPC_A[1],   # blonde woman in blue dress
    LPC_A[5],   # woman in green — smart-casual female
    LPC_B[2],   # green-shirt casual male
    LPC_B[3],   # casual male, different hair
    LPC_B[4],   # blonde casual male
    LPC_B[7],   # white-haired older person — art-lover type
    LPC_C[0],   # dark hair casual male
    LPC_C[1],   # dark hair casual variant
    LPC_C[2],   # orange-hair with braid — casual female
    LPC_C[4],   # grey-hair older — senior museum visitor
]

# High-res Mario from the RPG Maker sprite sheet (single-character, 80×80 cells).
# Keep him noticeably short so he reads as a fun cameo, not a giant.
# Charset rows: 0=DOWN, 1=RIGHT-facing, 2=LEFT-facing, 3=UP
# (rows 1 and 2 are swapped vs. the LPC convention, so we remap them here)
MARIO = SpriteConfig(
    path="sprites/npcs/mario.png",
    cell_w=80, cell_h=80,
    char_col=0, char_row=0,
    target_h=52,
    rows={DOWN: 0, LEFT: 2, RIGHT: 1, UP: 3},
)
