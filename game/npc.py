"""Ambient museum NPCs.

Each NPC walks slowly around a designated walkable rectangle, pausing
at random intervals to "look at" exhibits. They collide with the
scene's static obstacles (walls, fixtures) but only softly with the
player and each other (we just stop, we don't push).

State machine
-------------
- ``WALKING``: a destination ``(tx, ty)`` is set; the NPC moves toward
  it. On reaching the target (or after a max walk duration) it
  transitions to ``IDLE``.
- ``IDLE``: the NPC stands still for a random duration (2-6 s),
  occasionally turning to face a different direction. Then it picks a
  new destination and resumes walking.

Movement uses axis-separated AABB collision against ``obstacles`` so
tight corners don't trap the NPC. If a step is fully blocked, the NPC
gives up on its current destination and re-rolls.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

import pygame

from . import npc_sprite
from .npc_sprite import SpriteConfig


# Slower than the player so they read as "ambient background life."
NPC_SPEED = 60.0   # px/sec


@dataclass
class NPC:
    x: float
    y: float
    config: SpriteConfig
    walkable: pygame.Rect             # the area this NPC roams in
    radius: int = 14
    facing: Tuple[int, int] = (0, 1)
    state: str = "idle"               # "idle" | "walking"
    state_timer: float = 0.0          # seconds remaining in current state
    target: Optional[Tuple[float, float]] = None
    walk_phase: float = 0.0
    rng: random.Random = field(default_factory=random.Random)
    # Optional display name for future dialogue; not used for movement.
    name: str = ""
    # Stuck detection: track distance to target and how long it hasn't improved.
    _prev_dist: float = field(default=9999.0, repr=False)
    _stuck_time: float = field(default=0.0, repr=False)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    @property
    def is_walking(self) -> bool:
        return self.state == "walking"

    # ------------------------------------------------------------------
    def _pick_destination(self) -> None:
        """Pick a random reachable point inside ``walkable`` that's at
        least 60 px away from the current position so the walk reads."""
        for _ in range(8):
            tx = self.rng.uniform(self.walkable.left + self.radius + 4,
                                   self.walkable.right - self.radius - 4)
            ty = self.rng.uniform(self.walkable.top + self.radius + 4,
                                   self.walkable.bottom - self.radius - 4)
            if (tx - self.x) ** 2 + (ty - self.y) ** 2 > 60 * 60:
                self.target = (tx, ty)
                self.state = "walking"
                # cap how long they'll commit to this destination so a
                # blocked path doesn't get them stuck forever.
                self.state_timer = self.rng.uniform(3.0, 7.0)
                return
        # Couldn't find a far-enough target; just idle a beat.
        self._enter_idle(short=True)

    def _enter_idle(self, short: bool = False) -> None:
        self.state = "idle"
        self.state_timer = self.rng.uniform(0.6, 1.8) if short else self.rng.uniform(2.2, 6.0)
        self.target = None
        self._prev_dist = 9999.0
        self._stuck_time = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float, obstacles: Iterable[pygame.Rect]) -> None:
        self.state_timer -= dt
        if self.state == "idle":
            # Occasionally glance to a different cardinal while idling
            # so they don't look frozen.
            if self.rng.random() < dt * 0.4:
                self.facing = self.rng.choice([
                    npc_sprite.DOWN, npc_sprite.LEFT,
                    npc_sprite.RIGHT, npc_sprite.UP,
                ])
            if self.state_timer <= 0:
                self._pick_destination()
            return

        # WALKING
        if self.target is None or self.state_timer <= 0:
            self._enter_idle()
            return

        obs_list = list(obstacles)

        # If the destination is now inside an obstacle (e.g. welcome panel
        # appeared after the target was chosen), abandon immediately.
        tx, ty = self.target
        target_rect = pygame.Rect(int(tx) - self.radius, int(ty) - self.radius,
                                  self.radius * 2, self.radius * 2)
        if any(target_rect.colliderect(o) for o in obs_list):
            self._enter_idle(short=True)
            return

        dx = tx - self.x
        dy = ty - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 3.0:
            self._enter_idle()
            return

        # Stuck detection: if we haven't closed distance by ≥2 px/s for
        # 0.5 s straight, give up so we don't slide against a wall forever.
        if dist < self._prev_dist - 2.0 * dt:
            self._prev_dist = dist
            self._stuck_time = 0.0
        else:
            self._stuck_time += dt
            if self._stuck_time > 0.5:
                self._enter_idle(short=True)
                return

        # Normalised step
        ux = dx / dist
        uy = dy / dist
        step = NPC_SPEED * dt

        # Update facing toward dominant axis (so we don't flicker
        # between left/right while moving diagonally).
        if abs(ux) >= abs(uy):
            self.facing = npc_sprite.RIGHT if ux > 0 else npc_sprite.LEFT
        else:
            self.facing = npc_sprite.DOWN if uy > 0 else npc_sprite.UP

        # Axis-separated AABB collision (same pattern as the Player).
        nx = self.x + ux * step
        ny = self.y + uy * step
        moved = False

        test = pygame.Rect(int(nx - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)
        if not any(test.colliderect(o) for o in obs_list):
            self.x = nx
            moved = True

        test = pygame.Rect(int(self.x - self.radius), int(ny - self.radius),
                           self.radius * 2, self.radius * 2)
        if not any(test.colliderect(o) for o in obs_list):
            self.y = ny
            moved = True

        # Clamp inside walkable so they never wander into a doorway.
        self.x = max(self.walkable.left + self.radius + 2,
                     min(self.walkable.right - self.radius - 2, self.x))
        self.y = max(self.walkable.top + self.radius + 2,
                     min(self.walkable.bottom - self.radius - 2, self.y))

        if moved:
            self.walk_phase += dt
        else:
            # Couldn't move on either axis — abandon target.
            self._enter_idle(short=True)
            return

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        sprite = npc_sprite.render(self.config, self.facing, self.walk_phase, self.is_walking)
        if sprite is None:
            # Fallback: a simple placeholder dot so missing assets are obvious.
            pygame.draw.circle(surface, (200, 80, 80), (int(self.x), int(self.y)), self.radius)
            return
        rect = sprite.get_rect()
        rect.midbottom = (int(self.x), int(self.y) + self.radius + 2)
        surface.blit(sprite, rect)


def populate(
    walkable: pygame.Rect,
    configs: List[SpriteConfig],
    obstacles: Iterable[pygame.Rect],
    seed: int = 0,
    min_separation: int = 56,
    max_attempts_per_npc: int = 30,
) -> List[NPC]:
    """Place ``len(configs)`` NPCs at non-overlapping random positions
    inside ``walkable`` that don't collide with any obstacle. Each NPC
    starts in the IDLE state with a short timer so they don't all begin
    walking on the same frame."""
    rng = random.Random(seed)
    npcs: List[NPC] = []
    obs_list = list(obstacles)
    for cfg in configs:
        for _ in range(max_attempts_per_npc):
            x = rng.uniform(walkable.left + 24, walkable.right - 24)
            y = rng.uniform(walkable.top + 24, walkable.bottom - 24)
            r = pygame.Rect(int(x) - 16, int(y) - 16, 32, 32)
            if any(r.colliderect(o) for o in obs_list):
                continue
            if any((x - n.x) ** 2 + (y - n.y) ** 2 < min_separation ** 2 for n in npcs):
                continue
            npc = NPC(
                x=x, y=y, config=cfg, walkable=walkable, rng=rng,
                state_timer=rng.uniform(0.5, 3.5),
            )
            # Random initial facing so they're not all looking down.
            npc.facing = rng.choice([
                npc_sprite.DOWN, npc_sprite.LEFT,
                npc_sprite.RIGHT, npc_sprite.UP,
            ])
            npcs.append(npc)
            break
    return npcs
