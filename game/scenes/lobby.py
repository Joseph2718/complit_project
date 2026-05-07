"""Museum lobby. Three doorways on the north wall (Wing I, Reading
Room, Wing II) and a welcome placard. Walk into a doorway or press E
to enter; press H to toggle the welcome card."""

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
from ..content import MUSEUM_THESIS, WINGS, wing_by_key
from ..constants import COL_READING
from .. import npc as npc_mod
from .. import npc_sprite
from ..player import Player
from ..ui import Prompt, draw_panel, draw_wrapped, render_tracked, size_placard, wrap_text


# Wall thicknesses + doorway width are tuned to the painted lobby art.
NORTH_WALL_FRACTION = 0.165
SIDE_WALL_THICKNESS = 30
SOUTH_WALL_THICKNESS = 8
DOORWAY_WIDTH = 110

# Doorway center-x and carpet-bottom positions (fractions of the painted
# lobby art): Wing I left, Reading Room middle, Wing II right.
DOORWAY_LAYOUTS: tuple = (
    ("wing",         "wing_i",       0.1675, 0.235),
    ("reading_room", "reading_room", 0.4997, 0.235),
    ("wing",         "wing_ii",      0.8325, 0.235),
)


@dataclass
class Doorway:
    rect: pygame.Rect       # trigger region
    label_rect: pygame.Rect # banner above
    kind: str               # 'wing' | 'reading_room'
    key: str                # wing key, or 'reading_room'
    title: str              # banner heading (e.g. "Wing I: Same Lyrics")
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

        placard_width = 480
        placard_inner_width = placard_width - 56
        placard_header_h = self.heading_font.get_height() + 18
        placard_height = size_placard(
            MUSEUM_THESIS, self.body_font, placard_inner_width,
            header_height=placard_header_h, top_pad=10, bottom_pad=14, line_spacing=5,
        )
        self.placard_rect = pygame.Rect(0, 0, placard_width, placard_height)
        banner_bottom = max(d.label_rect.bottom for d in self.doorways)
        self.placard_rect.midtop = (self.room.centerx, banner_bottom + 28)
        self.placard_close_rect = pygame.Rect(0, 0, 28, 28)
        self.placard_close_rect.topright = (
            self.placard_rect.right - 8, self.placard_rect.top + 8,
        )

        # Visibility persists across transitions; ``placard_grace`` keeps
        # the card opaque on first show even if the player spawns inside it.
        self.placard_visible = getattr(self.game, "placard_visible", True)
        self.placard_grace = True

        # Spawn just below the doorway most recently exited, if any.
        last_key = getattr(self.game, "last_room_key", None)
        spawn_door = next((d for d in self.doorways if d.key == last_key), None)
        if spawn_door is not None:
            spawn_x = spawn_door.label_rect.centerx
            spawn_y = spawn_door.label_rect.bottom + 60
        else:
            spawn_x = self.room.centerx
            spawn_y = self.room.bottom - 56
        self.player = Player(x=spawn_x, y=spawn_y)
        self.game.last_room_key = None

        wall_depth = int(self.room.height * NORTH_WALL_FRACTION)
        self.npc_walkable = pygame.Rect(
            self.room.left + SIDE_WALL_THICKNESS + 32,
            self.room.top + wall_depth + 60,
            self.room.width - 2 * SIDE_WALL_THICKNESS - 64,
            self.room.height - wall_depth - SOUTH_WALL_THICKNESS - 80,
        )
        rng = __import__("random").Random(7)
        generic_pool = list(npc_sprite.GENERIC_NPCS)
        rng.shuffle(generic_pool)
        configs = generic_pool[:5] + [npc_sprite.MARIO]
        spawn_obstacles = list(self.obstacles) + [self.placard_rect.inflate(24, 24)]
        self.npcs = npc_mod.populate(
            self.npc_walkable, configs, spawn_obstacles, seed=11,
        )

        self._prompt: Optional[Prompt] = None
        self._focused: Optional[Doorway] = None

    def _build_doorways(self) -> List[Doorway]:
        r = self.room
        wall_depth = int(r.height * NORTH_WALL_FRACTION)
        doors: List[Doorway] = []
        for kind, key, frac_x, carpet_frac in DOORWAY_LAYOUTS:
            cx = r.left + int(r.width * frac_x)
            trigger = pygame.Rect(
                cx - DOORWAY_WIDTH // 2, r.top,
                DOORWAY_WIDTH, wall_depth + 8,
            )
            carpet_bottom = r.top + int(r.height * carpet_frac)
            label = pygame.Rect(cx - 175, carpet_bottom, 350, 96)
            if kind == "reading_room":
                title = "Reading Room: Foundational Texts"
                accent = COL_READING
            else:
                wing = wing_by_key(key)
                title = f"{wing.title}: {wing.subtitle}"
                accent = wing.accent
            doors.append(
                Doorway(
                    rect=trigger,
                    label_rect=label,
                    kind=kind,
                    key=key,
                    title=title,
                    accent=accent,
                )
            )
        return doors

    def _build_walls(self) -> List[pygame.Rect]:
        r = self.room
        walls: List[pygame.Rect] = []
        wall_depth = int(r.height * NORTH_WALL_FRACTION)
        walls.append(pygame.Rect(r.left, r.bottom - SOUTH_WALL_THICKNESS, r.width, SOUTH_WALL_THICKNESS))
        walls.append(pygame.Rect(r.right - SIDE_WALL_THICKNESS, r.top, SIDE_WALL_THICKNESS, r.height))
        walls.append(pygame.Rect(r.left, r.top, SIDE_WALL_THICKNESS, r.height))
        # North wall: thick slab pierced only by the doorway columns.
        segments = [r.left]
        for d in self.doorways:
            segments.append(d.rect.left)
            segments.append(d.rect.right)
        segments.append(r.right)
        for i in range(0, len(segments), 2):
            x1 = segments[i]
            x2 = segments[i + 1]
            if x2 > x1:
                walls.append(pygame.Rect(x1, r.top, x2 - x1, wall_depth))
        return walls

    def _enter_focused(self, d: Doorway) -> None:
        if d.kind == "reading_room":
            self.game.enter_reading_room()
        else:
            self.game.enter_wing(d.key)

    def on_enter(self, **kwargs) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)

    def on_resume(self) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                if self._focused:
                    audio.play_click()
                    self._enter_focused(self._focused)
            elif event.key == pygame.K_h:
                self.placard_visible = not self.placard_visible
                self.placard_grace = self.placard_visible
                self.game.placard_visible = self.placard_visible
                audio.play_click()
            elif event.key == pygame.K_ESCAPE:
                self.game.confirm_quit_to_title()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.placard_visible and self.placard_close_rect.collidepoint(event.pos):
                self.placard_visible = False
                self.game.placard_visible = False
                audio.play_click()

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.obstacles)

        # NPCs treat the player and (when visible) the welcome placard as
        # obstacles, EXCEPT for any NPC whose body is currently inside the
        # placard — for them the placard isn't an obstacle until they've
        # walked out, so they can leave naturally instead of being stuck.
        player_block = self.player.rect.inflate(8, 8)
        placard_block = self.placard_rect.inflate(16, 16) if self.placard_visible else None
        for n in self.npcs:
            obs = list(self.obstacles) + [player_block]
            if placard_block is not None and not n.rect.colliderect(placard_block):
                obs.append(placard_block)
            n.update(dt, obs)

        # keep player inside the room (in case of teleport spawns)
        r = self.room
        self.player.x = max(r.left + self.player.radius + 2, min(r.right - self.player.radius - 2, self.player.x))
        self.player.y = max(r.top + self.player.radius + 2, min(r.bottom - self.player.radius - 2, self.player.y))

        # End grace once the player has stepped off the welcome card.
        if self.placard_grace and self.placard_visible:
            if not self.placard_rect.colliderect(self.player.rect):
                self.placard_grace = False

        # Doorway focus + walk-in entry.
        self._focused = None
        self._prompt = None
        prect = self.player.rect
        for d in self.doorways:
            approach = pygame.Rect(d.rect.left, d.rect.bottom, d.rect.width, 140)
            if prect.colliderect(approach):
                self._focused = d
                self._prompt = Prompt(f"Press E to enter — {d.title}", self.prompt_font)
                break
        for d in self.doorways:
            if (
                d.rect.left < self.player.x < d.rect.right
                and self.player.y < d.rect.top + d.rect.height // 2
            ):
                audio.play_click()
                self._enter_focused(d)
                return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 16, 14))
        banner_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 78)
        pygame.draw.rect(surface, COL_INK, banner_rect)
        pygame.draw.line(surface, COL_GOLD, (0, 78), (SCREEN_WIDTH, 78), 2)
        title = render_tracked(
            self.title_font, "THE MUSEUM OF REPERFORMANCE", COL_PAPER, tracking=3
        )
        surface.blit(title, title.get_rect(midleft=(UI_MARGIN, 39)))
        hint = self.small_font.render(
            "WASD to walk    E to enter    H to toggle welcome    Esc to step back",
            True, COL_MUTED,
        )
        surface.blit(hint, hint.get_rect(midright=(SCREEN_WIDTH - UI_MARGIN, 39)))

        if not self._draw_backdrop(surface):
            self._draw_floor(surface)
            self._draw_walls_behind_player(surface)

        for d in self.doorways:
            self._draw_doorway_banner(surface, d)
        self._draw_placard(surface)

        actors = sorted([("p", self.player)] + [("n", n) for n in self.npcs],
                         key=lambda a: a[1].y)
        for _, a in actors:
            a.draw(surface)

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
            vignette = pygame.Surface(r.size, pygame.SRCALPHA)
            vignette.fill((24, 16, 10, 60))
            surface.blit(vignette, r.topleft)

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
        # Tinted doorway interior + gold lintel for each painted arch.
        for d in self.doorways:
            interior = pygame.Rect(d.rect.left, r.top - 2, d.rect.width, WALL_THICKNESS + 2)
            pygame.draw.rect(surface, d.accent, interior)
            shade = pygame.Surface(interior.size, pygame.SRCALPHA)
            for i in range(interior.height):
                a = int(150 * (1 - i / interior.height))
                pygame.draw.line(shade, (0, 0, 0, a), (0, i), (interior.width, i))
            surface.blit(shade, interior.topleft)
            lintel = pygame.Rect(d.rect.left - 8, r.top - 8, d.rect.width + 16, 10)
            pygame.draw.rect(surface, COL_GOLD, lintel)
            pygame.draw.rect(surface, COL_GOLD_DIM, lintel, 2)

    def _draw_doorway_banner(self, surface: pygame.Surface, d: Doorway) -> None:
        rect = d.label_rect
        draw_panel(surface, rect, bg=COL_PAPER, border=d.accent, border_width=3, radius=4)
        top, _, bottom = d.title.partition(": ")
        # Auto-fit: drop point size until the tracked title fits the panel.
        max_w = rect.width - 24
        title_font = self.title_font
        for sz in (30, 28, 26, 24, 22):
            f = get_font("heading", sz)
            cand = render_tracked(f, top.upper(), d.accent, tracking=4)
            if cand.get_width() <= max_w:
                title_font = f
                t1 = cand
                break
        else:
            t1 = render_tracked(title_font, top.upper(), d.accent, tracking=2)
        t1_rect = t1.get_rect(midtop=(rect.centerx, rect.top + 10))
        surface.blit(t1, t1_rect)
        rule_y = t1_rect.bottom + 6
        pygame.draw.line(
            surface, d.accent, (rect.left + 30, rule_y), (rect.right - 30, rule_y), 1,
        )
        y = rule_y + 8
        for line in wrap_text(bottom, self.italic_font, rect.width - 28):
            s = self.italic_font.render(line, True, COL_INK)
            surface.blit(s, s.get_rect(midtop=(rect.centerx, y)))
            y += self.italic_font.get_height() + 1

    def _draw_placard(self, surface: pygame.Surface) -> None:
        if not self.placard_visible:
            text = "Press H to show welcome"
            hint = self.small_font.render(text, True, COL_PAPER)
            pad_x, pad_y = 14, 6
            pill = pygame.Rect(0, 0, hint.get_width() + 2 * pad_x, hint.get_height() + 2 * pad_y)
            pill.midbottom = (self.room.centerx, self.room.bottom - 8)
            shadow = pygame.Surface(pill.size, pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 130), shadow.get_rect(), border_radius=pill.height // 2)
            surface.blit(shadow, pill.move(0, 3).topleft)
            pygame.draw.rect(surface, COL_INK, pill, border_radius=pill.height // 2)
            pygame.draw.rect(surface, COL_GOLD, pill, 1, border_radius=pill.height // 2)
            surface.blit(hint, (pill.left + pad_x, pill.top + pad_y))
            return

        rect = self.placard_rect
        # Translucent on overlap once the initial grace period has ended.
        overlap = (not self.placard_grace) and rect.colliderect(self.player.rect)
        alpha = 150 if overlap else 245

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel_bg = (*COL_PAPER, alpha)
        pygame.draw.rect(panel, panel_bg, panel.get_rect(), border_radius=6)
        pygame.draw.rect(panel, COL_INK, panel.get_rect(), 2, border_radius=6)
        surface.blit(panel, rect.topleft)

        header = self.heading_font.render("Welcome, traveler!", True, COL_INK)
        header.set_alpha(alpha)
        surface.blit(header, header.get_rect(midtop=(rect.centerx, rect.top + 6)))
        rule_y = rect.top + self.heading_font.get_height() + 12
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
            rect.left + 28,
            rule_y + 8,
            rect.width - 56,
            line_spacing=5,
        )

        cr = self.placard_close_rect
        pygame.draw.rect(surface, COL_INK, cr, border_radius=4)
        pygame.draw.line(surface, COL_PAPER, (cr.left + 7, cr.top + 7), (cr.right - 7, cr.bottom - 7), 2)
        pygame.draw.line(surface, COL_PAPER, (cr.right - 7, cr.top + 7), (cr.left + 7, cr.bottom - 7), 2)
