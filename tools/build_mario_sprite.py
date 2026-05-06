"""Extract small Mario walk frames from a Super Mario World overworld
sprite rip and assemble a 144x192 single-character charset compatible
with our scholar/LPC RPG-Maker layout (3 cols x 4 rows of 48x48).

Source sheet layout (small Mario portion, 16x16 frames on magenta bg):
    walk DOWN     y= 16..31, x = { 8, 32, 56, 80 }
    walk UP       y= 40..55, same x
    walk SIDEWAYS y= 64..79, same x  (right-facing)

The sheet has 4 frames per direction. Our charset is 3 frames per
direction: we use frames (1, 0, 2) as (step-A, idle, step-B), giving a
0->1->2->1 pendulum walk.

For the LEFT-facing row we mirror the right-facing frames horizontally.

Magenta (FF00FF or close) is treated as the transparent backdrop. The
green outer background is also stripped just in case the bounding box
overshoots a pixel.

This script depends only on pygame (no Pillow). Run once; the output is
committed.
"""

from __future__ import annotations

import os

import pygame


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = "/tmp/sprite_dl/mario_smw_overworld.png"
OUT = os.path.join(ROOT, "assets", "art", "sprites", "npcs", "mario.png")


SRC_FRAME = 16            # frames are 16x16 on the source
DEST_CELL = 48            # output cell size (matches scholar / LPC)
SCALE = DEST_CELL // SRC_FRAME  # integer 3x upscale, nearest-neighbor

# (y, [x0, x1, x2, x3]) — top-left of each 16x16 frame for one direction.
FRAME_X = [8, 32, 56, 80]
ROW_DOWN = (16, FRAME_X)
ROW_UP = (40, FRAME_X)
ROW_SIDE = (64, FRAME_X)   # right-facing in source

# Source has 4 frames; pick 3 that give a clean step-A / idle / step-B.
# Frame 0 = stance, 1 = left-foot-forward, 2 = stance, 3 = right-foot-forward.
# Using indices (1, 0, 3) gives a proper pendulum walk.
FRAME_PICK = (1, 0, 3)


def is_magenta(c) -> bool:
    """Match the SMW overworld rip's pink transparency mask. The actual
    pink reads ~ (228, 0, 228) at full intensity; allow a wide margin so
    every pixel of the rectangular fill is caught."""
    r, g, b = c[0], c[1], c[2]
    return r > 180 and g < 80 and b > 180


def is_green_bg(c) -> bool:
    """The green page background (tight match — don't strip Mario's own greens)."""
    r, g, b = c[0], c[1], c[2]
    return abs(r - 10) < 6 and abs(g - 104) < 6 and abs(b - 32) < 6


def extract_frame(src: pygame.Surface, x: int, y: int) -> pygame.Surface:
    """Crop a 16x16 frame, knock out the magenta + green backdrop, and
    return an upscaled 48x48 RGBA surface (nearest-neighbor)."""
    cell = pygame.Surface((SRC_FRAME, SRC_FRAME), pygame.SRCALPHA)
    cell.fill((0, 0, 0, 0))
    for j in range(SRC_FRAME):
        for i in range(SRC_FRAME):
            c = src.get_at((x + i, y + j))
            if is_magenta(c) or is_green_bg(c):
                continue
            cell.set_at((i, j), c)
    return pygame.transform.scale(cell, (DEST_CELL, DEST_CELL))


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    src = pygame.image.load(SRC).convert_alpha()

    # Output charset: 3 cols x 4 rows of 48x48. Row order matches LPC
    # convention: 0=down, 1=left, 2=right, 3=up.
    sheet = pygame.Surface((DEST_CELL * 3, DEST_CELL * 4), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))

    def place(row: int, col: int, frame: pygame.Surface, flip: bool = False) -> None:
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        sheet.blit(frame, (col * DEST_CELL, row * DEST_CELL))

    # Walk-down row
    y, xs = ROW_DOWN
    for col, src_idx in enumerate(FRAME_PICK):
        place(0, col, extract_frame(src, xs[src_idx], y))

    # Walk-up row
    y, xs = ROW_UP
    for col, src_idx in enumerate(FRAME_PICK):
        place(3, col, extract_frame(src, xs[src_idx], y))

    # Walk-right row (use source sideways frames as-is)
    y, xs = ROW_SIDE
    for col, src_idx in enumerate(FRAME_PICK):
        place(2, col, extract_frame(src, xs[src_idx], y))

    # Walk-left row: mirror the right-facing frames
    y, xs = ROW_SIDE
    for col, src_idx in enumerate(FRAME_PICK):
        place(1, col, extract_frame(src, xs[src_idx], y), flip=True)

    pygame.image.save(sheet, OUT)
    print(f"wrote {OUT}  ({sheet.get_width()}x{sheet.get_height()})")
    pygame.quit()


if __name__ == "__main__":
    main()
