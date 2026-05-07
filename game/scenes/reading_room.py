"""Reading Room scene.

Three inspectable lecterns sit on the room's two reading desks (and a
small stand near the south wall): the museum's Curatorial Thesis on the
left desk, the Working Vocabulary on the right desk, and the Guiding
Questions on a podium near the exit.

The aim is *first room*: a player walks in, reads three short, focused
items, and walks back out with the museum's framing in mind. After
visiting Guiding Questions, the player may pin them to a small "scroll"
icon that follows them through every other scene (handled by
``ReadingScrollOverlay``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from .. import audio
from .. import npc as npc_mod
from .. import npc_sprite
from ..assets import get_font, load_image
from ..constants import (
    COL_GOLD,
    COL_GOLD_DIM,
    COL_INK,
    COL_INK_SOFT,
    COL_MUTED,
    COL_PAPER,
    COL_READING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_MARGIN,
)
from ..content import READING_ENTRIES, ReadingEntry, reading_entry_by_key
from ..player import Player
from ..ui import Prompt, draw_panel, render_tracked, wrap_text


# The painted reading_room.png is wider than it is tall; the room rect we
# play inside fills the screen below the banner. Wall thicknesses match
# the painted dark stone trim around the edge of the art.
WALL_THICKNESS = 50
SIDE_WALL_THICKNESS = 32
SOUTH_WALL_THICKNESS = 26
DOORWAY_WIDTH = 130


@dataclass
class Lectern:
    """One inspectable item — a station the player walks up to."""
    entry_key: str          # 'thesis' | 'vocab' | 'questions'
    title: str
    podium_rect: pygame.Rect    # the small visible podium drawn over the floor
    approach_rect: pygame.Rect  # player-only trigger zone
    icon: str = ""              # symbolic glyph drawn above the title


class ReadingRoomScene:
    def __init__(self, game) -> None:
        self.game = game
        self.title_font = get_font("heading", 28)
        self.heading_font = get_font("display", 36)
        self.body_font = get_font("body", 19)
        self.italic_font = get_font("italic", 19)
        self.small_font = get_font("body", 16)
        self.tag_font = get_font("body_bold", 14)
        self.prompt_font = get_font("body_bold", 20)

        room_top = 90
        self.room = pygame.Rect(
            UI_MARGIN, room_top,
            SCREEN_WIDTH - 2 * UI_MARGIN,
            SCREEN_HEIGHT - room_top - UI_MARGIN,
        )

        self.lecterns: List[Lectern] = self._build_lecterns()
        self.obstacles: List[pygame.Rect] = self._build_walls()

        # Player spawns at the south doorway, facing in.
        self.player = Player(
            x=self.room.centerx,
            y=self.room.bottom - 90,
            facing=(0, -1),
        )

        self._focused: Optional[Lectern] = None
        self._prompt: Optional[Prompt] = None
        self._exit_focused = False

        # ----- Ambient room population --------------------------------
        # A "secretary" sprite stationed near the south doorway (between
        # the lower bookshelves), plus two visitors wandering the open
        # central rug between the desks and the south wall. The
        # secretary is a normal NPC pinned to a tiny walkable rect so
        # they fidget in place rather than roam.
        npc_top = self.lecterns[0].podium_rect.bottom + 60
        npc_bottom = self.room.bottom - 110
        npc_left = self.room.left + 70
        npc_right = self.room.right - 70
        self.npc_walkable = pygame.Rect(
            npc_left, npc_top,
            npc_right - npc_left, max(80, npc_bottom - npc_top),
        )
        wanderer_pool = list(npc_sprite.GENERIC_NPCS)
        rng = __import__("random").Random(0xC1)
        rng.shuffle(wanderer_pool)
        wanderers = npc_mod.populate(
            self.npc_walkable, wanderer_pool[:2], list(self.obstacles),
            seed=0xC1, min_separation=70,
        )
        # Secretary: a small stationary box near the south doorway, off
        # to the player's left as they enter, so they read as the
        # information desk.
        sec_x = self.room.centerx - 220
        sec_y = self.room.bottom - 92
        # Walkable wide enough to safely contain the NPC's radius clamp;
        # state_timer is huge so they never re-roll a destination, and
        # idle state means update() only adjusts facing.
        sec_walkable = pygame.Rect(sec_x - 30, sec_y - 30, 60, 60)
        secretary = npc_mod.NPC(
            x=sec_x, y=sec_y,
            config=npc_sprite.LPC_A[5],   # smart-casual woman in green
            walkable=sec_walkable,
            facing=npc_sprite.DOWN,
            state="idle", state_timer=99999.0,
            name="Secretary",
        )
        self.npcs = [secretary] + wanderers

    # ------------------------------------------------------------------
    def _build_lecterns(self) -> List[Lectern]:
        """Three stations.

        The painted reading_room.png shows two desks in the upper third
        and an open central rug. We anchor the Thesis lectern on the
        left desk, Vocabulary on the right desk, and Guiding Questions
        on a podium near the south side, just inside the doorway. The
        podiums are sized to read as proper standees from across the
        room, with a symbolic glyph above the title.
        """
        r = self.room
        desk_y = r.top + int(r.height * 0.40)
        left_cx = r.left + int(r.width * 0.27)
        right_cx = r.left + int(r.width * 0.73)
        questions_cx = r.centerx
        questions_y = r.top + int(r.height * 0.78)

        def station(cx: int, cy: int, key: str, title: str, icon: str) -> Lectern:
            podium = pygame.Rect(0, 0, 200, 86)
            podium.center = (cx, cy)
            approach = podium.inflate(140, 110)
            return Lectern(key, title, podium, approach, icon)

        # Icons are drawn vector-style in _draw_podium so they look
        # like museum pictograms, not Unicode glyphs (which our serif
        # font does not provide). Keys: 'scroll' (thesis), 'book'
        # (vocab), 'question' (questions).
        return [
            station(left_cx, desk_y, "thesis", "Curatorial Thesis", "scroll"),
            station(right_cx, desk_y, "vocab", "Working Vocabulary", "book"),
            station(questions_cx, questions_y, "questions", "Guiding Questions", "question"),
        ]

    def _build_walls(self) -> List[pygame.Rect]:
        r = self.room
        walls: List[pygame.Rect] = []
        walls.append(pygame.Rect(r.left, r.top, r.width, WALL_THICKNESS))
        walls.append(pygame.Rect(r.left, r.top, SIDE_WALL_THICKNESS, r.height))
        walls.append(pygame.Rect(r.right - SIDE_WALL_THICKNESS, r.top,
                                 SIDE_WALL_THICKNESS, r.height))
        # South wall flanks (doorway in the middle).
        doorway_cx = r.centerx
        south_y = r.bottom - SOUTH_WALL_THICKNESS
        walls.append(pygame.Rect(
            r.left, south_y,
            (doorway_cx - DOORWAY_WIDTH // 2) - r.left, SOUTH_WALL_THICKNESS,
        ))
        walls.append(pygame.Rect(
            doorway_cx + DOORWAY_WIDTH // 2, south_y,
            r.right - (doorway_cx + DOORWAY_WIDTH // 2), SOUTH_WALL_THICKNESS,
        ))
        return walls

    # ------------------------------------------------------------------
    def on_enter(self, **kwargs) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)

    def on_resume(self) -> None:
        audio.play_music("gallery_ambient.ogg", volume=0.22)
        audio.stop_preview()

    def on_exit(self) -> None:
        pass

    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                if self._focused:
                    audio.play_open()
                    self.game.open_reading_entry(self._focused.entry_key)
                elif self._exit_focused:
                    audio.play_click()
                    self.game.return_to_lobby()
            elif event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.game.return_to_lobby()

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.obstacles)

        # Ambient NPCs roam between podiums.
        npc_obstacles = (
            list(self.obstacles)
            + [lec.podium_rect.inflate(20, 20) for lec in self.lecterns]
            + [self.player.rect.inflate(8, 8)]
        )
        for n in self.npcs:
            n.update(dt, npc_obstacles)

        r = self.room
        in_doorway = abs(self.player.x - r.centerx) < DOORWAY_WIDTH // 2
        exit_threshold = r.bottom - SOUTH_WALL_THICKNESS + self.player.radius
        if in_doorway and self.player.y >= exit_threshold:
            audio.play_click()
            self.game.return_to_lobby()
            return

        pr = self.player.radius
        self.player.x = max(
            r.left + SIDE_WALL_THICKNESS + pr,
            min(r.right - SIDE_WALL_THICKNESS - pr, self.player.x),
        )
        north_min = r.top + WALL_THICKNESS + pr
        if in_doorway:
            self.player.y = max(north_min, self.player.y)
        else:
            self.player.y = max(
                north_min,
                min(r.bottom - SOUTH_WALL_THICKNESS - pr, self.player.y),
            )

        # Lectern focus: closest approach rect wins.
        self._focused = None
        self._prompt = None
        self._exit_focused = False
        prect = self.player.rect
        pc = prect.center
        best = None
        for lec in self.lecterns:
            if not prect.colliderect(lec.approach_rect):
                continue
            d = (pc[0] - lec.podium_rect.centerx) ** 2 + (pc[1] - lec.podium_rect.centery) ** 2
            if best is None or d < best[0]:
                best = (d, lec)
        if best is not None:
            self._focused = best[1]
            self._prompt = Prompt(
                f"Press E to read \u2014 {best[1].title}",
                self.prompt_font,
            )
        else:
            exit_zone = pygame.Rect(r.centerx - 110, r.bottom - 120, 220, 110)
            if prect.colliderect(exit_zone):
                self._exit_focused = True
                self._prompt = Prompt(
                    "Press E to return to the Lobby", self.prompt_font,
                )

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 16, 14))

        banner = pygame.Rect(0, 0, SCREEN_WIDTH, 78)
        pygame.draw.rect(surface, COL_INK, banner)
        pygame.draw.line(surface, COL_READING, (0, 78), (SCREEN_WIDTH, 78), 3)
        title = render_tracked(
            self.title_font, "READING ROOM   FOUNDATIONAL TEXTS", COL_PAPER, tracking=3,
        )
        surface.blit(title, title.get_rect(midleft=(UI_MARGIN, 39)))
        hint = self.small_font.render(
            "WASD to walk    E to read    B / Esc to return",
            True, COL_MUTED,
        )
        surface.blit(hint, hint.get_rect(midright=(SCREEN_WIDTH - UI_MARGIN, 39)))

        self._draw_backdrop(surface)
        self._draw_podiums(surface)

        # Player + NPCs in y-order so foreground/background depth reads.
        actors = sorted(
            [("p", self.player)] + [("n", n) for n in self.npcs],
            key=lambda a: a[1].y,
        )
        for _, a in actors:
            a.draw(surface)

        if self._prompt:
            if self._focused:
                pr = self._focused.podium_rect
                self._prompt.draw(surface, pr.centerx, pr.top - 40)
            else:
                self._prompt.draw(
                    surface, int(self.player.x),
                    int(self.player.y - self.player.radius - 12),
                )

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        bg = load_image("backdrops/reading_room.png")
        if bg is None:
            pygame.draw.rect(surface, (60, 42, 30), self.room)
            return
        if not hasattr(self, "_scaled_backdrop"):
            self._scaled_backdrop = pygame.transform.scale(bg, self.room.size)
        surface.blit(self._scaled_backdrop, self.room.topleft)

    def _draw_podiums(self, surface: pygame.Surface) -> None:
        focused_key = id(self._focused) if self._focused else None
        for lec in self.lecterns:
            hot = id(lec) == focused_key
            self._draw_podium(surface, lec, hot)

    def _draw_podium(self, surface: pygame.Surface, lec: Lectern, hot: bool) -> None:
        rect = lec.podium_rect
        if hot:
            glow = pygame.Surface((rect.width + 80, rect.height + 80), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*COL_GOLD, 70), glow.get_rect())
            surface.blit(glow, (rect.left - 40, rect.top - 40))

        bg = COL_PAPER
        border = COL_GOLD if hot else COL_READING
        bw = 3 if hot else 2
        draw_panel(surface, rect, bg=bg, border=border, border_width=bw, radius=6)

        # Pictogram band (top half of plaque).
        icon_rect = pygame.Rect(0, 0, 36, 36)
        icon_rect.center = (rect.centerx, rect.top + 22)
        self._draw_pictogram(surface, lec.icon, icon_rect, hot)

        # Hairline rule.
        rule_y = icon_rect.bottom + 4
        pygame.draw.line(
            surface, COL_GOLD,
            (rect.left + 14, rule_y), (rect.right - 14, rule_y), 1,
        )

        # Title line: pick the largest body_bold size that still fits.
        text = lec.title
        chosen = get_font("body_bold", 13)
        for size in (19, 18, 17, 16, 15, 14, 13):
            f = get_font("body_bold", size)
            if f.size(text)[0] <= rect.width - 18:
                chosen = f
                break
        ts = chosen.render(text, True, COL_INK)
        title_y = rule_y + 6
        surface.blit(ts, ts.get_rect(midtop=(rect.centerx, title_y)))

        pass

    def _draw_pictogram(
        self, surface: pygame.Surface, kind: str, rect: pygame.Rect, hot: bool,
    ) -> None:
        """Vector-drawn museum pictogram. Cormorant Garamond does not
        carry pictographic glyphs, so we render simple geometric icons
        that read at 36×36 px from across the room."""
        col = COL_GOLD if hot else COL_READING
        if kind == "scroll":
            # Horizontal scroll with two end-cap rolls.
            cap_w = 6
            body = pygame.Rect(rect.left + cap_w, rect.top + 6,
                               rect.width - 2 * cap_w, rect.height - 12)
            pygame.draw.rect(surface, COL_PAPER, body)
            pygame.draw.rect(surface, col, body, 2)
            for i in range(3):
                ly = body.top + 6 + i * 6
                pygame.draw.line(surface, col, (body.left + 4, ly), (body.right - 4, ly), 1)
            for cx in (rect.left + cap_w // 2, rect.right - cap_w // 2):
                pygame.draw.rect(surface, col, (cx - cap_w // 2, body.top - 2,
                                                cap_w, body.height + 4))
                pygame.draw.rect(surface, COL_INK, (cx - cap_w // 2, body.top - 2,
                                                   cap_w, body.height + 4), 1)
        elif kind == "book":
            # Closed book standing upright: thick spine on left, page
            # block on right, horizontal rules suggesting page edges.
            spine_w = 6
            bk = pygame.Rect(rect.left + 2, rect.top + 3, rect.width - 4, rect.height - 6)
            # Page block (right portion)
            pages = pygame.Rect(bk.left + spine_w, bk.top, bk.width - spine_w, bk.height)
            pygame.draw.rect(surface, COL_PAPER, pages)
            pygame.draw.rect(surface, col, pages, 2)
            # Spine (left strip)
            spine = pygame.Rect(bk.left, bk.top, spine_w, bk.height)
            pygame.draw.rect(surface, col, spine)
            # Page-edge lines on right side (fanned look)
            for i in range(4):
                ly = pages.top + 4 + i * (pages.height - 8) // 3
                pygame.draw.line(surface, col,
                    (pages.right - 5, pages.top + i * 2),
                    (pages.right - 5, ly), 1)
        else:  # question
            # Bold "?" inside a small disc — high-contrast even at distance.
            cx, cy = rect.center
            radius = min(rect.width, rect.height) // 2 - 2
            pygame.draw.circle(surface, COL_PAPER, (cx, cy), radius)
            pygame.draw.circle(surface, col, (cx, cy), radius, 2)
            qf = get_font("display", 28)
            qs = qf.render("?", True, col)
            surface.blit(qs, qs.get_rect(center=(cx, cy + 1)))
