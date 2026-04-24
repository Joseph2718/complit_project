"""Top-down 4-directional visitor character.

Sprite sheet: ``assets/art/sprites/npc_scholar.png``
Format: RPG Maker VX Ace charset — 48 × 48 px cells, 12 cols × 8 rows.
The walk animation for the first character occupies the top-left 3 × 4 block:

    row 0  facing DOWN  — cols 0, 1, 2  (step-A, idle, step-B)
    row 1  facing LEFT  — cols 0, 1, 2
    row 2  facing RIGHT — cols 0, 1, 2
    row 3  facing UP    — cols 0, 1, 2

Walk cycle plays columns in order 0 → 1 → 2 → 1 (pendulum) so both feet
alternate and idle is only a brief pass-through, not a full held frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import pygame

from .assets import load_image
from .constants import PLAYER_SPEED


SPRITE_PATH = "sprites/npc_scholar.png"
CELL_W, CELL_H = 48, 48

_ROW_BY_FACING: Dict[Tuple[int, int], int] = {
    (0,  1): 0,  # down
    (1,  0): 1,  # right
    (-1, 0): 2,  # left
    (0, -1): 3,  # up
}

# Pendulum: step-A → idle → step-B → idle. Smooth on any framerate.
_WALK_CYCLE = (0, 1, 2, 1)

TARGET_H = 80
TARGET_W = int(round(TARGET_H * (CELL_W / CELL_H)))

_FRAME_CACHE: Dict[Tuple[int, int], pygame.Surface] = {}


def _load_frame(row: int, col: int) -> Optional[pygame.Surface]:
    key = (row, col)
    cached = _FRAME_CACHE.get(key)
    if cached is not None:
        return cached
    sheet = load_image(SPRITE_PATH)
    if sheet is None:
        return None
    cell = sheet.subsurface(pygame.Rect(col * CELL_W, row * CELL_H, CELL_W, CELL_H)).copy()
    scaled = pygame.transform.scale(cell, (TARGET_W, TARGET_H))
    _FRAME_CACHE[key] = scaled
    return scaled


def _cardinal(facing: Tuple[int, int]) -> Tuple[int, int]:
    """Snap an arbitrary facing vector to the nearest cardinal.
    Horizontal takes priority on ties."""
    fx, fy = facing
    if fx == 0 and fy == 0:
        return (0, 1)
    if abs(fx) >= abs(fy):
        return (1, 0) if fx > 0 else (-1, 0)
    return (0, 1) if fy > 0 else (0, -1)


@dataclass
class Player:
    x: float
    y: float
    radius: int = 18
    facing: Tuple[int, int] = (0, 1)
    walk_phase: float = 0.0
    is_walking: bool = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def update(
        self,
        dt: float,
        keys: pygame.key.ScancodeWrapper,
        obstacles: Iterable[pygame.Rect],
    ) -> None:
        dx = 0
        dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        if dx != 0 and dy != 0:
            inv = 1.0 / (2 ** 0.5)
            dx_f = dx * inv
            dy_f = dy * inv
        else:
            dx_f = float(dx)
            dy_f = float(dy)

        moving = dx != 0 or dy != 0
        self.is_walking = moving
        if moving:
            # Prefer the horizontal axis so side profiles show while walking diagonally.
            if dx != 0:
                self.facing = (dx, 0)
            else:
                self.facing = (0, dy)
            self.walk_phase += dt
        else:
            self.walk_phase = 0.0

        step = PLAYER_SPEED * dt
        nx = self.x + dx_f * step
        ny = self.y + dy_f * step

        test = pygame.Rect(
            int(nx - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2
        )
        if not any(test.colliderect(o) for o in obstacles):
            self.x = nx
        test = pygame.Rect(
            int(self.x - self.radius), int(ny - self.radius), self.radius * 2, self.radius * 2
        )
        if not any(test.colliderect(o) for o in obstacles):
            self.y = ny

    def _current_frame(self) -> Optional[pygame.Surface]:
        row = _ROW_BY_FACING.get(_cardinal(self.facing), 0)
        if self.is_walking:
            col = _WALK_CYCLE[int(self.walk_phase * 7.0) % len(_WALK_CYCLE)]
        else:
            col = 1
        return _load_frame(row, col)

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)

        sprite = self._current_frame()
        if sprite is not None:
            rect = sprite.get_rect()
            rect.midbottom = (cx, cy + self.radius + 2)
            surface.blit(sprite, rect)
            return

        pygame.draw.circle(surface, (58, 62, 78), (cx, cy), self.radius)
        pygame.draw.circle(surface, (232, 208, 176), (cx, cy - 2), self.radius - 7)
