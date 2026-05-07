"""Extract walk frames from the RPG Maker–style Mario sprite sheet
(toppng.com-rpg-maker-sprites-by-rpg-maker-mario-sprites-524x401.png)
and assemble a single-character charset compatible with our LPC layout.

Source sheet layout (835x639, white background):
    band y=  1.. 85  — DOWN  walk (row 0)
    band y= 86..165  — RIGHT walk (row 1)
    band y=166..245  — LEFT  walk (row 2)
    band y=246..325  — UP    walk (row 3, back-facing)
    band y=326..405  — DOWN  idle variants (row 4)

We pick 3 frames per direction: step-A | idle | step-B.
Sprites are larger and higher-resolution than the 8-bit SMW sheet,
so we use 80×80 px cells to give them breathing room. At render time
``target_h=52`` in the SpriteConfig keeps them size-consistent with
the LPC NPCs.

Output: assets/art/sprites/npcs/mario.png  (240×320, 4 rows × 3 cols)
"""

from __future__ import annotations

import os
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "assets", "art", "sprites", "npcs",
                   "toppng.com-rpg-maker-sprites-by-rpg-maker-mario-sprites-524x401.png")
OUT = os.path.join(ROOT, "assets", "art", "sprites", "npcs", "mario.png")

CELL = 80   # output cell size


def is_bg(c) -> bool:
    """White background used in this sheet."""
    return c[0] > 240 and c[1] > 240 and c[2] > 240


def bbox_sprites_in_band(img, y0: int, y1: int, count: int):
    """Return bounding boxes of the first ``count`` sprites in this band."""
    W = img.get_width()
    in_col = False; cs = 0; boxes = []
    for x in range(W):
        has = any(not is_bg(img.get_at((x, y))[:3]) for y in range(y0, y1))
        if has and not in_col:
            in_col = True; cs = x
        elif not has and in_col:
            in_col = False
            ys = [y for y in range(y0, y1)
                  if any(not is_bg(img.get_at((xx, y))[:3]) for xx in range(cs, x))]
            boxes.append((cs, ys[0], x - 1, ys[-1]))
            if len(boxes) == count:
                break
    return boxes


def extract_sprite(img, x0: int, y0: int, x1: int, y1: int) -> pygame.Surface:
    """Crop the bounding-box sprite, knock out white, center on a CELL×CELL canvas."""
    w, h = x1 - x0 + 1, y1 - y0 + 1
    raw = pygame.Surface((w, h), pygame.SRCALPHA)
    raw.fill((0, 0, 0, 0))
    for j in range(h):
        for i in range(w):
            c = img.get_at((x0 + i, y0 + j))
            if not is_bg(c[:3]):
                raw.set_at((i, j), c)
    # Scale to fit inside CELL×CELL preserving aspect
    scale = min(CELL / w, CELL / h, 1.0)   # never upscale beyond 1:1
    tw, th = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    scaled = pygame.transform.smoothscale(raw, (tw, th))
    cell = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    cell.fill((0, 0, 0, 0))
    ox = (CELL - tw) // 2
    oy = CELL - th   # bottom-align so feet land on the same baseline
    cell.blit(scaled, (ox, oy))
    return cell


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    img = pygame.image.load(SRC).convert_alpha()

    # Source row bands and how many sprites to pull (we need 3 per direction)
    BANDS = {
        "down":  (1,   85),
        "right": (86,  165),
        "left":  (166, 245),
        "up":    (246, 325),
        "down_idle": (326, 405),   # better standing idle for DOWN
    }

    # Grab bounding boxes (need up to index 6 from down_idle, so fetch 8)
    sprites = {}
    for key, (y0, y1) in BANDS.items():
        sprites[key] = bbox_sprites_in_band(img, y0, y1, 8)

    # Build the charset: 3 cols × 4 rows.
    # LPC row order: row0=DOWN, row1=LEFT, row2=RIGHT, row3=UP
    # Columns: 0=step-A, 1=idle, 2=step-B
    #
    # DOWN:  step-A=down[0], idle=down_idle[0], step-B=down[2]
    # LEFT:  step-A=left[0], idle=left[1],       step-B=left[2]
    # RIGHT: step-A=right[0], idle=right[1],     step-B=right[2]
    # UP:    step-A=up[0],   idle=up[1],         step-B=up[2]

    def cell(key: str, idx: int) -> pygame.Surface:
        bb = sprites[key][idx]
        return extract_sprite(img, *bb)

    # Frame selection strategy:
    #   DOWN  – col 0: walking stride (row0[0]), col 1: neutral idle (row0[1],
    #           the clean standing pose), col 2: subtle variant (row4[6]).
    #   LEFT/RIGHT – three clean running strides, all with neutral expressions.
    #   UP    – back-facing walk; avoid raised-arm frame (row3[2]) → use row3[3].
    layout = [
        [cell("down",      0), cell("down",      1), cell("down_idle", 6)],  # DOWN
        [cell("left",      0), cell("left",      1), cell("left",      2)],  # LEFT
        [cell("right",     0), cell("right",     1), cell("right",     2)],  # RIGHT
        [cell("up",        0), cell("up",        1), cell("up",        3)],  # UP
    ]

    sheet = pygame.Surface((CELL * 3, CELL * 4), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    for row_i, row in enumerate(layout):
        for col_i, frame in enumerate(row):
            sheet.blit(frame, (col_i * CELL, row_i * CELL))

    pygame.image.save(sheet, OUT)
    print(f"wrote {OUT}  ({sheet.get_width()}x{sheet.get_height()})")
    pygame.quit()


if __name__ == "__main__":
    main()
