"""Museum lobby: a top-down room with a grand hall, three wing doorways on
the north wall, a welcome placard on the south wall, and an exit in the
center of the south wall.

Entering a wing: walk up to a doorway and press E/Space, or simply walk
into it. Walls collide; doorways don't.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from .. import audio
from ..assets import get_font, load_image
from ..constants import (
    COL_FLOOR,
    COL_FLOOR_DARK,
    COL_GOLD,
    COL_GOLD_DIM,
    COL_INK,
    COL_INK_SOFT,
    COL_MUTED,
    COL_PAPER,
    COL_WALL,
    COL_WALL_SHADOW,
    INTERACT_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_MARGIN,
)
from ..content import MUSEUM_THESIS, WINGS
from ..player import Player
from ..ui import Prompt, draw_panel, draw_wrapped, render_tracked, size_placard, wrap_text


WALL_THICKNESS = 28
DOORWAY_WIDTH = 120
DOORWAY_HEIGHT = WALL_THICKNESS + 4


@dataclass
class Doorway:
    rect: pygame.Rect       # trigger region
    label_rect: pygame.Rect # banner above
    wing_key: str
    title: str
    accent: Tuple[int, int, int]


class LobbyScene:
    def __init__(self, game) -> None:
        self.game = game
        self.title_font = get_font("heading", 30)
        self.heading_font = get_font("display", 40)
        self.body_font = get_font("body", 20)
        self.italic_font = get_font("italic", 20)
        self.small_font = get_font("body", 16)
        self.prompt_font = get_font("body_bold", 20)


        # Room geometry. The lobby is the entire window; walls form an inner frame.
        self.room = pygame.Rect(
            UI_MARGIN, 90, SCREEN_WIDTH - 2 * UI_MARGIN, SCREEN_HEIGHT - 90 - UI_MARGIN
        )

        self.doorways: List[Doorway] = self._build_doorways()
        self.obstacles: List[pygame.Rect] = self._build_walls()

        # Welcome placard: a freestanding interpretive panel near the center
        # of the lobby, auto-sized so the thesis never clips. Kept narrower
        # than the spacing between doorways so the player still has a clear
        # walk-path to every wing entrance even with the placard as a solid.
        placard_width = 560
        placard_inner_width = placard_width - 60
        placard_header_h = self.heading_font.get_height() + 24
        placard_height = size_placard(
            MUSEUM_THESIS, self.body_font, placard_inner_width,
            header_height=placard_header_h, top_pad=12, bottom_pad=16, line_spacing=5,
        )
        self.placard_rect = pygame.Rect(0, 0, placard_width, placard_height)
        # Placement: below the three doorway label plaques (which end at
        # room.top + 240) with a clear breathing gap so Wing II's subtitle
        # isn't clipped by the Welcome placard.
        self.placard_rect.midtop = (
            self.room.centerx,
            self.room.top + 260,
        )
        # The placard is deliberately NOT a collider. All three wing
        # doorways must remain reachable by straight-line approach, so we
        # render it as graphics only. In practice the player walks around
        # it anyway — the visual presence does the work.

        # Player spawn — center of room, south of the placard.
        self.player = Player(
            x=self.room.centerx,
            y=self.room.bottom - 80,
        )

        self._prompt: Optional[Prompt] = None
        self._focused: Optional[Doorway] = None

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    def _build_doorways(self) -> List[Doorway]:
        """Place the three clickable doorway regions over the painted doors
        in the lobby backdrop. The backdrop (``assets/art/backdrops/lobby.png``)
        has three colored thresholds at roughly 17% / 51% / 83% of the room
        width; matching those positions here keeps gameplay and art aligned
        regardless of window size."""
        r = self.room
        # Fractions measured from the lobby backdrop's colored doorways
        # (teal, gold, burgundy) so the clickable regions sit directly on
        # top of the painted doors.
        fractions = (0.169, 0.509, 0.831)
        # Map each active wing to one of the three painted doorways in
        # left-to-right order. If the team later removes a wing, the same
        # fractions are still used so the remaining wings still line up.
        slots = fractions[: len(WINGS)]
        doors: List[Doorway] = []
        for frac, wing in zip(slots, WINGS):
            cx = r.left + int(r.width * frac)
            trigger = pygame.Rect(
                cx - DOORWAY_WIDTH // 2,
                r.top - 4,
                DOORWAY_WIDTH,
                DOORWAY_HEIGHT + 10,
            )
            # Small engraved-sign style plaque sits just below the painted
            # doorway — narrower than the door spacing so all three labels
            # stay legible without overlapping.
            label = pygame.Rect(cx - 160, r.top + 152, 320, 88)
            doors.append(
                Doorway(
                    rect=trigger,
                    label_rect=label,
                    wing_key=wing.key,
                    title=f"{wing.title}: {wing.subtitle}",
                    accent=wing.accent,
                )
            )
        return doors

    def _build_walls(self) -> List[pygame.Rect]:
        """North wall broken by doorways; south/east/west walls solid."""
        r = self.room
        walls: List[pygame.Rect] = []
        # South wall
        walls.append(pygame.Rect(r.left, r.bottom - WALL_THICKNESS, r.width, WALL_THICKNESS))
        # East wall
        walls.append(
            pygame.Rect(r.right - WALL_THICKNESS, r.top, WALL_THICKNESS, r.height)
        )
        # West wall
        walls.append(pygame.Rect(r.left, r.top, WALL_THICKNESS, r.height))

        # North wall with doorway gaps
        segments = [r.left]
        for d in self.doorways:
            segments.append(d.rect.left)
            segments.append(d.rect.right)
        segments.append(r.right)
        # pair up
        for i in range(0, len(segments), 2):
            x1 = segments[i]
            x2 = segments[i + 1]
            if x2 > x1:
                walls.append(pygame.Rect(x1, r.top, x2 - x1, WALL_THICKNESS))
        return walls

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------
    def on_enter(self, **kwargs) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)

    def on_resume(self) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)

    def on_exit(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Events + update
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                if self._focused:
                    audio.play_click()
                    self.game.enter_wing(self._focused.wing_key)
            elif event.key == pygame.K_ESCAPE:
                self.game.confirm_quit_to_title()

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.obstacles)

        # keep player inside the room (in case of teleport spawns)
        r = self.room
        self.player.x = max(r.left + self.player.radius + 2, min(r.right - self.player.radius - 2, self.player.x))
        self.player.y = max(r.top + self.player.radius + 2, min(r.bottom - self.player.radius - 2, self.player.y))

        # Check doorway triggers: near a doorway trigger region.
        self._focused = None
        self._prompt = None
        prect = self.player.rect
        for d in self.doorways:
            # proximity via expanded rect
            approach = d.rect.inflate(0, 120)  # extends south into room
            if prect.colliderect(approach):
                self._focused = d
                self._prompt = Prompt(f"Press E to enter — {d.title}", self.prompt_font)
                break

        # If the player walks fully through the doorway region, also enter.
        if self._focused and self.player.y < self._focused.rect.bottom + 6:
            audio.play_click()
            self.game.enter_wing(self._focused.wing_key)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 16, 14))

        # Top banner: museum name
        banner_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 78)
        pygame.draw.rect(surface, COL_INK, banner_rect)
        pygame.draw.line(surface, COL_GOLD, (0, 78), (SCREEN_WIDTH, 78), 2)
        title = render_tracked(
            self.title_font, "THE MUSEUM OF REPERFORMANCE", COL_PAPER, tracking=3
        )
        surface.blit(title, title.get_rect(midleft=(UI_MARGIN, 39)))
        hint = self.small_font.render(
            "WASD to walk    E to enter    Esc to step back", True, COL_MUTED
        )
        surface.blit(hint, hint.get_rect(midright=(SCREEN_WIDTH - UI_MARGIN, 39)))

        if not self._draw_backdrop(surface):
            self._draw_floor(surface)
            self._draw_walls_behind_player(surface)

        # Wing-identifying banner plaques over each doorway. Drawn on top
        # of the backdrop (or procedural walls) so the player can always
        # see which door leads to which wing.
        for d in self.doorways:
            self._draw_doorway_banner(surface, d)

        # Welcome placard (on south wall, inside the room)
        self._draw_placard(surface)

        # Player
        self.player.draw(surface)

        # Prompt anchored above the focused doorway plaque, not the player.
        if self._prompt:
            if self._focused:
                self._prompt.draw(
                    surface,
                    self._focused.label_rect.centerx,
                    self._focused.label_rect.bottom + 40,
                )
            else:
                self._prompt.draw(
                    surface,
                    int(self.player.x),
                    int(self.player.y - self.player.radius - 12),
                )

    def _draw_backdrop(self, surface: pygame.Surface) -> bool:
        """Scaled pixel-art top-down lobby. Returns False if missing so
        the procedural fallback can kick in."""
        bg = load_image("backdrops/lobby.png")
        if bg is None:
            return False
        if not hasattr(self, "_scaled_backdrop"):
            self._scaled_backdrop = pygame.transform.scale(bg, self.room.size)
        surface.blit(self._scaled_backdrop, self.room.topleft)
        return True

    def _draw_floor(self, surface: pygame.Surface) -> None:
        r = self.room
        tex = load_image("textures/parquet.jpg")
        if tex is None:
            tile = 48
            for y in range(r.top, r.bottom, tile):
                for x in range(r.left, r.right, tile):
                    color = COL_FLOOR if ((x + y) // tile) % 2 == 0 else COL_FLOOR_DARK
                    pygame.draw.rect(surface, color, (x, y, tile, tile))
        else:
            if not hasattr(self, "_floor_tile"):
                self._floor_tile = pygame.transform.smoothscale(tex, (320, 320))
            t = self._floor_tile
            tw, th = t.get_size()
            prev_clip = surface.get_clip()
            surface.set_clip(r)
            for y in range(r.top, r.bottom, th):
                for x in range(r.left, r.right, tw):
                    surface.blit(t, (x, y))
            surface.set_clip(prev_clip)
            # Soft vignette warms the edges.
            vignette = pygame.Surface(r.size, pygame.SRCALPHA)
            vignette.fill((24, 16, 10, 60))
            surface.blit(vignette, r.topleft)

        # Centered cream rug to ground the welcome placard.
        rug = pygame.Rect(0, 0, r.width - 240, r.height - 240)
        rug.center = r.center
        rug_surf = pygame.Surface(rug.size, pygame.SRCALPHA)
        rug_surf.fill((212, 188, 148, 200))
        surface.blit(rug_surf, rug.topleft)
        pygame.draw.rect(surface, COL_GOLD_DIM, rug, 2, border_radius=14)
        pygame.draw.circle(surface, COL_GOLD, rug.center, 30, 2)
        pygame.draw.circle(surface, COL_GOLD_DIM, rug.center, 18, 2)

    def _draw_walls_behind_player(self, surface: pygame.Surface) -> None:
        tex = load_image("textures/wall.jpg")
        if tex is not None and not hasattr(self, "_wall_tile"):
            self._wall_tile = pygame.transform.smoothscale(tex, (400, 400))
        for wall in self.obstacles:
            if tex is None:
                pygame.draw.rect(surface, COL_WALL, wall)
            else:
                prev_clip = surface.get_clip()
                surface.set_clip(wall)
                tw, th = self._wall_tile.get_size()
                for y in range(wall.top, wall.bottom, th):
                    for x in range(wall.left, wall.right, tw):
                        surface.blit(self._wall_tile, (x, y))
                surface.set_clip(prev_clip)
            pygame.draw.rect(surface, (52, 42, 34), wall, 1)

        r = self.room
        # draw wing doorway interiors (peek of color on the "far side")
        for d in self.doorways:
            # tinted doorway interior visible through the north wall
            interior = pygame.Rect(d.rect.left, r.top - 2, d.rect.width, WALL_THICKNESS + 2)
            pygame.draw.rect(surface, d.accent, interior)
            # darker gradient into the interior
            shade = pygame.Surface(interior.size, pygame.SRCALPHA)
            for i in range(interior.height):
                a = int(150 * (1 - i / interior.height))
                pygame.draw.line(shade, (0, 0, 0, a), (0, i), (interior.width, i))
            surface.blit(shade, interior.topleft)
            # gold lintel
            lintel = pygame.Rect(d.rect.left - 8, r.top - 8, d.rect.width + 16, 10)
            pygame.draw.rect(surface, COL_GOLD, lintel)
            pygame.draw.rect(surface, COL_GOLD_DIM, lintel, 2)

    def _draw_doorway_banner(self, surface: pygame.Surface, d: Doorway) -> None:
        rect = d.label_rect
        draw_panel(surface, rect, bg=COL_PAPER, border=d.accent, border_width=3, radius=4)
        wing_header = d.title.split(": ", 1)
        top = wing_header[0]
        bottom = wing_header[1] if len(wing_header) > 1 else ""
        # Wing numeral: tracked uppercase small-caps feel.
        t1 = render_tracked(self.title_font, top.upper(), d.accent, tracking=4)
        t1_rect = t1.get_rect(midtop=(rect.centerx, rect.top + 10))
        surface.blit(t1, t1_rect)
        # Thin rule between title and subtitle.
        rule_y = t1_rect.bottom + 6
        pygame.draw.line(
            surface, d.accent, (rect.left + 30, rule_y), (rect.right - 30, rule_y), 1
        )
        # Subtitle italic, wrapped.
        y = rule_y + 8
        for line in wrap_text(bottom, self.italic_font, rect.width - 28):
            s = self.italic_font.render(line, True, COL_INK)
            surface.blit(s, s.get_rect(midtop=(rect.centerx, y)))
            y += self.italic_font.get_height() + 1

    def _draw_placard(self, surface: pygame.Surface) -> None:
        rect = self.placard_rect
        draw_panel(surface, rect, bg=COL_PAPER, border=COL_INK, border_width=2, radius=6)
        header = self.heading_font.render("Welcome", True, COL_INK)
        surface.blit(header, header.get_rect(midtop=(rect.centerx, rect.top + 6)))
        rule_y = rect.top + self.heading_font.get_height() + 14
        pygame.draw.line(
            surface, COL_GOLD,
            (rect.left + 40, rule_y),
            (rect.right - 40, rule_y), 1,
        )
        draw_wrapped(
            surface,
            MUSEUM_THESIS,
            self.body_font,
            COL_INK_SOFT,
            rect.left + 30,
            rule_y + 10,
            rect.width - 60,
            line_spacing=5,
        )
