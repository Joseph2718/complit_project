"""Generic wing scene. Reused for all three wings — the wing data drives
its walls, exhibit positions, and accent color.

Player enters from a south doorway, walks among exhibits mounted on the
north, east, and west walls. Approaching an exhibit shows a prompt;
pressing E opens the exhibit overlay.
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
from ..content import Exhibit, Wing, wing_by_key
from ..player import Player
from ..ui import Prompt, draw_panel, draw_wrapped, render_tracked, size_placard, truncate_to_width, wrap_text


WALL_THICKNESS = 50          # north wall depth — kept equal to side so corners are solid
SIDE_WALL_THICKNESS = 22     # conservative east/west clamp; both wings use the same value
SOUTH_WALL_THICKNESS = 10    # thin south clamp; exit doorway flanks are separate
DOORWAY_WIDTH = 120
FRAME_W = 200
FRAME_H = 240

# Maps wing content key -> pixel-art backdrop filename. Missing keys fall
# back to the procedural floor/wall renderer (so adding a new wing without
# art is a graceful degrade).
WING_BACKDROPS: dict = {
    "wing_i": "backdrops/wing_same_lyrics.png",
    "wing_ii": "backdrops/wing_reclaimed.png",
    "wing_iii": "backdrops/wing_viral.png",
}


@dataclass
class ExhibitMount:
    exhibit: Exhibit
    frame_rect: pygame.Rect     # visual frame on the wall
    approach_rect: pygame.Rect  # larger zone in front of the frame
    accent: Tuple[int, int, int]


class WingScene:
    def __init__(self, game, wing_key: str) -> None:
        self.game = game
        self.wing: Wing = wing_by_key(wing_key)
        self.title_font = get_font("heading", 28)
        self.heading_font = get_font("display", 42)
        self.sub_font = get_font("heading", 22)
        self.body_font = get_font("body", 20)
        self.italic_font = get_font("italic", 20)
        self.small_font = get_font("body", 16)
        self.prompt_font = get_font("body_bold", 20)
        self.tag_font = get_font("body_bold", 16)


        # The room starts below the banner + thesis strip combined.
        room_top = 132
        self.room = pygame.Rect(
            UI_MARGIN, room_top, SCREEN_WIDTH - 2 * UI_MARGIN, SCREEN_HEIGHT - room_top - UI_MARGIN
        )

        self.mounts: List[ExhibitMount] = self._build_mounts()
        self.obstacles: List[pygame.Rect] = self._build_walls()

        # The wing's thesis is already presented on the lobby doorway plaque
        # (teaser) and in the exhibit panel header (in depth). Repeating it
        # in a large room-floor card added clutter and collided with the
        # focus prompts, so the wing room itself no longer carries one.
        # (See ``_draw_thesis_strip`` for the compact top-of-room summary.)
        # Plaque is rendered over the floor but NOT a collider; we don't
        # want to pen the player against the wall if they veer west.

        # Player spawns at south doorway, facing north.
        self.player = Player(
            x=self.room.centerx,
            y=self.room.bottom - 160,
            facing=(0, -1),
        )

        self._focused: Optional[ExhibitMount] = None
        self._prompt: Optional[Prompt] = None
        self._exit_focused = False

    # ------------------------------------------------------------------
    def _build_mounts(self) -> List[ExhibitMount]:
        """Lay exhibits around the walls and build a small, well-sized
        approach rectangle directly in front of each one.

        Approach rects are intentionally narrow (about the frame's width,
        minus a few pixels of inset so neighbors can't overlap) and short
        (~110 px deep from the floor-side of the frame). This guarantees:
          - the player can walk across the room without triggering focus
          - standing in front of a frame always triggers it
          - no two approach rects ever overlap — even when frames are
            packed close together on the same wall.
        """
        r = self.room
        exhibits = list(self.wing.exhibits)
        mounts: List[ExhibitMount] = []

        # Per-frame approach zone depth (how far from the wall the spotlight reaches).
        APPROACH_DEPTH = 110
        SIDE_INSET = 18  # keep neighboring zones from touching

        north_slots = min(len(exhibits), 3)
        north_exhibits = exhibits[:north_slots]
        remaining = exhibits[north_slots:]
        west_exhibits = remaining[: (len(remaining) + 1) // 2]
        east_exhibits = remaining[(len(remaining) + 1) // 2 :]

        if north_exhibits:
            spacing = r.width / (len(north_exhibits) + 1)
            # Clamp approach width to at most spacing - gap so they never overlap.
            max_half = max(FRAME_W // 2 - SIDE_INSET, int(spacing / 2) - SIDE_INSET)
            for i, ex in enumerate(north_exhibits):
                cx = r.left + int((i + 1) * spacing)
                frame = pygame.Rect(0, 0, FRAME_W, FRAME_H)
                frame.midtop = (cx, r.top + WALL_THICKNESS - 6)
                approach = pygame.Rect(
                    cx - max_half, frame.bottom + 6,
                    max_half * 2, APPROACH_DEPTH,
                )
                mounts.append(ExhibitMount(ex, frame, approach, self.wing.accent))

        if west_exhibits:
            spacing = r.height / (len(west_exhibits) + 1)
            max_half = max(FRAME_W // 2 - SIDE_INSET, int(spacing / 2) - SIDE_INSET)
            for i, ex in enumerate(west_exhibits):
                cy = r.top + int((i + 1) * spacing)
                frame = pygame.Rect(0, 0, FRAME_H, FRAME_W)
                frame.midleft = (r.left + SIDE_WALL_THICKNESS - 6, cy)
                approach = pygame.Rect(
                    frame.right + 6, cy - max_half,
                    APPROACH_DEPTH, max_half * 2,
                )
                mounts.append(ExhibitMount(ex, frame, approach, self.wing.accent))

        if east_exhibits:
            spacing = r.height / (len(east_exhibits) + 1)
            max_half = max(FRAME_W // 2 - SIDE_INSET, int(spacing / 2) - SIDE_INSET)
            for i, ex in enumerate(east_exhibits):
                cy = r.top + int((i + 1) * spacing)
                frame = pygame.Rect(0, 0, FRAME_H, FRAME_W)
                frame.midright = (r.right - SIDE_WALL_THICKNESS + 6, cy)
                approach = pygame.Rect(
                    frame.left - APPROACH_DEPTH - 6, cy - max_half,
                    APPROACH_DEPTH, max_half * 2,
                )
                mounts.append(ExhibitMount(ex, frame, approach, self.wing.accent))

        return mounts

    def _build_walls(self) -> List[pygame.Rect]:
        r = self.room
        walls: List[pygame.Rect] = []
        # North: full-width slab — the same depth as the sides so corners
        # are completely closed and the player can't slip above it.
        walls.append(pygame.Rect(r.left, r.top, r.width, WALL_THICKNESS))
        # East / west: run the full height of the room (north wall already
        # blocks the top corners, south flanks handle the bottom corners).
        walls.append(pygame.Rect(r.left, r.top, SIDE_WALL_THICKNESS, r.height))
        walls.append(pygame.Rect(r.right - SIDE_WALL_THICKNESS, r.top, SIDE_WALL_THICKNESS, r.height))
        # South wall: flanks around the exit doorway.
        doorway_cx = r.centerx
        south_y = r.bottom - WALL_THICKNESS
        walls.append(
            pygame.Rect(r.left, south_y, (doorway_cx - DOORWAY_WIDTH // 2) - r.left, WALL_THICKNESS)
        )
        walls.append(
            pygame.Rect(
                doorway_cx + DOORWAY_WIDTH // 2,
                south_y,
                r.right - (doorway_cx + DOORWAY_WIDTH // 2),
                WALL_THICKNESS,
            )
        )
        # Thin full-width clamp at very bottom edge
        walls.append(pygame.Rect(r.left, r.bottom - SOUTH_WALL_THICKNESS, r.width, SOUTH_WALL_THICKNESS))
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
                    self.game.open_exhibit(self._focused.exhibit, self.wing)
                elif self._exit_focused:
                    audio.play_click()
                    self.game.return_to_lobby()
            elif event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.game.return_to_lobby()

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.obstacles)

        r = self.room
        # Walk-through exit: if the player is inside the doorway gap and has
        # moved below the top of the south wall, send them back to the lobby.
        # Check BEFORE clamping so the edge clamp doesn't cage them in.
        in_doorway = abs(self.player.x - r.centerx) < DOORWAY_WIDTH // 2
        exit_threshold = r.bottom - WALL_THICKNESS + self.player.radius
        if in_doorway and self.player.y >= exit_threshold:
            audio.play_click()
            self.game.return_to_lobby()
            return

        pr = self.player.radius
        # Hard clamps that back up the obstacle rects so no slide-through
        # is possible at any corner. North uses WALL_THICKNESS; sides use
        # SIDE_WALL_THICKNESS; south uses WALL_THICKNESS (matching flanks).
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
                min(r.bottom - WALL_THICKNESS - pr, self.player.y),
            )

        # Find approached exhibit. The focus trigger zone is the union of the
        # approach rect (standing in front) and the frame rect (walked up
        # close and hugging the wall). Pick the *closest* mount if multiple
        # overlap so neighbors never fight for focus.
        self._focused = None
        self._prompt = None
        self._exit_focused = False
        prect = self.player.rect
        pc = prect.center
        best_dist = None
        for m in self.mounts:
            hit = prect.colliderect(m.approach_rect) or prect.colliderect(m.frame_rect)
            if not hit:
                continue
            fc = m.frame_rect.center
            d = (pc[0] - fc[0]) ** 2 + (pc[1] - fc[1]) ** 2
            if best_dist is None or d < best_dist:
                best_dist = d
                self._focused = m

        if self._focused is not None:
            self._prompt = Prompt(
                f"Press  E  to inspect \u2014 \u201c{self._focused.exhibit.song}\u201d",
                self.prompt_font,
            )

        # Exit prompt (near south doorway, facing south)
        if not self._focused:
            exit_zone = pygame.Rect(r.centerx - 110, r.bottom - 120, 220, 110)
            if prect.colliderect(exit_zone):
                self._exit_focused = True
                self._prompt = Prompt("Press E to return to the Lobby", self.prompt_font)

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 16, 14))

        # Wing banner at top
        banner = pygame.Rect(0, 0, SCREEN_WIDTH, 78)
        pygame.draw.rect(surface, COL_INK, banner)
        pygame.draw.line(surface, self.wing.accent, (0, 78), (SCREEN_WIDTH, 78), 3)
        title = render_tracked(
            self.title_font,
            f"{self.wing.title.upper()}   {self.wing.subtitle.upper()}",
            COL_PAPER,
            tracking=3,
        )
        surface.blit(title, title.get_rect(midleft=(UI_MARGIN, 39)))
        back_hint = self.small_font.render(
            "B / Esc to return to the Lobby     E to inspect", True, COL_MUTED
        )
        surface.blit(back_hint, back_hint.get_rect(midright=(SCREEN_WIDTH - UI_MARGIN, 39)))

        if not self._draw_backdrop(surface):
            # Procedural fallback if the backdrop image is missing.
            self._draw_floor(surface)
            self._draw_walls(surface)
            self._draw_exit_doorway(surface)
        self._draw_thesis_strip(surface)
        self._draw_exhibit_frames(surface)

        self.player.draw(surface)

        if self._prompt:
            # Anchor above the focused frame's title plaque (clearly tied
            # to the thing being inspected), or above the player when the
            # prompt is about leaving the wing.
            if self._focused:
                fr = self._focused.frame_rect
                self._prompt.draw(surface, fr.centerx, fr.bottom + 40)
            else:
                self._prompt.draw(surface, int(self.player.x), int(self.player.y - self.player.radius - 12))

    def _draw_backdrop(self, surface: pygame.Surface) -> bool:
        """Blit the wing's pixel-art top-down backdrop scaled into the room
        rect. Returns True if the backdrop was drawn, False if it was
        missing (so the caller can fall back to procedural art)."""
        path = WING_BACKDROPS.get(self.wing.key)
        if path is None:
            return False
        bg = load_image(path)
        if bg is None:
            return False
        # Scale to exactly the room rect so gameplay positioning (which
        # uses self.room) matches the visible art.
        if not hasattr(self, "_scaled_backdrop"):
            self._scaled_backdrop = pygame.transform.scale(bg, self.room.size)
        surface.blit(self._scaled_backdrop, self.room.topleft)
        return True

    def _draw_floor(self, surface: pygame.Surface) -> None:
        """Tiled herringbone parquet (CC0 Poly Haven) across the full room,
        with a warm wing-accent runner down the center. Falls back to a
        checker pattern if the texture is missing."""
        r = self.room
        tex = load_image("textures/parquet.jpg")
        if tex is None:
            tile = 48
            for y in range(r.top, r.bottom, tile):
                for x in range(r.left, r.right, tile):
                    color = COL_FLOOR if ((x + y) // tile) % 2 == 0 else COL_FLOOR_DARK
                    pygame.draw.rect(surface, color, (x, y, tile, tile))
        else:
            # Scale the texture once to a reasonable tile size; we want to
            # see the herringbone pattern clearly, so pick ~256 px per tile.
            if not hasattr(self, "_floor_tile"):
                ts = 320
                self._floor_tile = pygame.transform.smoothscale(tex, (ts, ts))
            t = self._floor_tile
            tw, th = t.get_size()
            # Clip to the room so parquet never bleeds onto the walls.
            prev_clip = surface.get_clip()
            surface.set_clip(r)
            for y in range(r.top, r.bottom, th):
                for x in range(r.left, r.right, tw):
                    surface.blit(t, (x, y))
            surface.set_clip(prev_clip)
            # Subtle warm tint overlay so the floor reads slightly darker in
            # the corners (vignette) and the frames pop.
            vignette = pygame.Surface(r.size, pygame.SRCALPHA)
            vignette.fill((24, 16, 10, 60))
            surface.blit(vignette, r.topleft)

        # Wing-tinted runner carpet along center.
        runner = pygame.Rect(r.centerx - 110, r.top + WALL_THICKNESS, 220, r.height - 2 * WALL_THICKNESS)
        carpet = pygame.Surface(runner.size, pygame.SRCALPHA)
        carpet.fill((*self.wing.accent, 210))
        surface.blit(carpet, runner.topleft)
        # Gold edge piping
        pygame.draw.rect(surface, COL_GOLD_DIM, runner, 2)
        pygame.draw.rect(surface, COL_GOLD, runner.inflate(-6, -6), 1)

    def _draw_walls(self, surface: pygame.Surface) -> None:
        """Textured marble walls (CC0 Poly Haven) with a thin ink line and
        a soft inner shadow where they meet the floor."""
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
            # Thin ink outline — 1px on all sides, crisp.
            pygame.draw.rect(surface, (52, 42, 34), wall, 1)
            # Cast a 4-px inner shadow on the floor-facing side so the wall
            # reads as "above" the parquet.
            r = self.room
            if wall.bottom < r.bottom and wall.height <= WALL_THICKNESS + 2:
                shade = pygame.Surface((wall.width, 6), pygame.SRCALPHA)
                for i in range(6):
                    a = int(90 * (1 - i / 6))
                    pygame.draw.line(shade, (0, 0, 0, a), (0, i), (wall.width, i))
                surface.blit(shade, (wall.left, wall.bottom))

    def _draw_exit_doorway(self, surface: pygame.Surface) -> None:
        r = self.room
        doorway = pygame.Rect(r.centerx - DOORWAY_WIDTH // 2, r.bottom - WALL_THICKNESS, DOORWAY_WIDTH, WALL_THICKNESS + 2)
        pygame.draw.rect(surface, (58, 48, 38), doorway)
        # warmer glow toward the lobby
        glow = pygame.Surface(doorway.size, pygame.SRCALPHA)
        for i in range(doorway.height):
            a = int(120 * (i / doorway.height))
            pygame.draw.line(glow, (210, 170, 90, a), (0, i), (doorway.width, i))
        surface.blit(glow, doorway.topleft)
        pygame.draw.rect(surface, COL_GOLD, doorway, 2)
        # "EXIT" placard above-left? Keep it clean: tiny arrow on runner.

    def _draw_exhibit_frames(self, surface: pygame.Surface) -> None:
        highlight_key = id(self._focused) if self._focused else None
        # Pass 1: floor glow for the focused approach zone, drawn UNDER
        # the frames so the effect reads as "this spot is hot."
        if self._focused:
            self._draw_approach_glow(surface, self._focused)
        # Pass 2: all frames.
        for m in self.mounts:
            hot = id(m) == highlight_key
            self._draw_frame(surface, m, hot)

    def _draw_approach_glow(self, surface: pygame.Surface, m: ExhibitMount) -> None:
        """Soft golden spotlight on the floor in front of the focused
        exhibit — a clear visual signal of 'stand here to interact.'"""
        glow = pygame.Surface(m.approach_rect.size, pygame.SRCALPHA)
        cx, cy = glow.get_width() // 2, glow.get_height() // 2
        max_r = max(cx, cy)
        for r in range(max_r, 0, -6):
            alpha = int(90 * (1 - r / max_r))
            pygame.draw.ellipse(
                glow,
                (COL_GOLD[0], COL_GOLD[1], COL_GOLD[2], alpha),
                (cx - r, cy - int(r * 0.55), r * 2, int(r * 1.1)),
            )
        surface.blit(glow, m.approach_rect.topleft)

    def _draw_frame(self, surface: pygame.Surface, m: ExhibitMount, hot: bool) -> None:
        r = m.frame_rect
        # Compute the full interactable bounding box: frame + tag below.
        tag_h = 34
        tag_gap = 10
        group_rect = pygame.Rect(
            r.left - 8, r.top - 8,
            r.width + 16, r.height + tag_gap + tag_h + 16,
        )

        # Outer glow while hot — 5 expanding gold rectangles with falling alpha.
        if hot:
            glow = pygame.Surface(group_rect.inflate(40, 40).size, pygame.SRCALPHA)
            gx, gy = 20, 20  # padding inside the surface
            inner = pygame.Rect(gx, gy, group_rect.width, group_rect.height)
            for i, alpha in enumerate([26, 40, 60, 90, 140]):
                pad = (5 - i) * 4
                pygame.draw.rect(
                    glow, (COL_GOLD[0], COL_GOLD[1], COL_GOLD[2], alpha),
                    inner.inflate(pad * 2, pad * 2), border_radius=6,
                )
            surface.blit(glow, (group_rect.left - 20, group_rect.top - 20))

        # Frame: thick wooden outer, paper mat, then cover image.
        pygame.draw.rect(surface, (42, 30, 22), r)  # dark wood
        inner = r.inflate(-12, -12)
        pygame.draw.rect(surface, COL_PAPER, inner)  # mat
        art_rect = inner.inflate(-14, -14)

        cover = load_image(f"exhibits/{m.exhibit.art_key}.png")
        if cover is not None:
            scaled = pygame.transform.smoothscale(cover, art_rect.size)
            surface.blit(scaled, art_rect.topleft)
        else:
            self._draw_procedural_cover(surface, art_rect, m)

        # Gold fillet inside the mat
        pygame.draw.rect(surface, COL_GOLD_DIM, art_rect.inflate(4, 4), 1)
        # Outer accent border — accent color when cold, gold when hot.
        border_color = COL_GOLD if hot else COL_INK
        pygame.draw.rect(surface, border_color, r, 3 if hot else 2)

        # Title plate beneath — wider than the frame, museum-style plaque.
        tag_rect = pygame.Rect(0, 0, r.width + 60, tag_h)
        tag_rect.midtop = (r.centerx, r.bottom + tag_gap)
        draw_panel(
            surface, tag_rect,
            bg=COL_PAPER,
            border=COL_GOLD if hot else m.accent,
            border_width=2 if hot else 1,
            shadow=True,
            radius=3,
        )
        label = truncate_to_width(m.exhibit.song, self.tag_font, tag_rect.width - 16)
        label_surf = self.tag_font.render(label, True, COL_INK)
        surface.blit(label_surf, label_surf.get_rect(center=tag_rect.center))

    def _draw_procedural_cover(
        self, surface: pygame.Surface, rect: pygame.Rect, m: ExhibitMount
    ) -> None:
        """Fallback cover art when no PNG is available: a tinted gradient
        with the song title letterset on top. Way nicer than sound-bands."""
        ar, ag, ab = m.accent
        # Vertical gradient from dark accent at top to lighter below.
        strip = pygame.Surface((rect.width, rect.height))
        for i in range(rect.height):
            t = i / max(1, rect.height - 1)
            r_ = int(ar * (0.35 + 0.35 * t))
            g_ = int(ag * (0.35 + 0.35 * t))
            b_ = int(ab * (0.35 + 0.35 * t))
            pygame.draw.line(strip, (r_, g_, b_), (0, i), (rect.width, i))
        surface.blit(strip, rect.topleft)
        # Faint horizon
        pygame.draw.line(
            surface, (255, 255, 255, 40),
            (rect.left, rect.centery), (rect.right, rect.centery), 1,
        )
        # Song letters center
        label_font = get_font("display", 30)
        from ..ui import render_tracked
        label = render_tracked(label_font, m.exhibit.song.upper(), COL_PAPER, tracking=3)
        # Fit-if-too-wide
        if label.get_width() > rect.width - 16:
            label = pygame.transform.smoothscale(
                label,
                (rect.width - 16, int(label.get_height() * (rect.width - 16) / label.get_width())),
            )
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_thesis_strip(self, surface: pygame.Surface) -> None:
        """A single italic line of thesis summary, drawn as a hairline
        band directly beneath the banner. Reads as a museum gallery
        introduction card — always visible, never in the way."""
        strip_top = 78 + 4
        strip_h = self.italic_font.get_height() + 20
        strip = pygame.Rect(UI_MARGIN, strip_top, SCREEN_WIDTH - 2 * UI_MARGIN, strip_h)
        band = pygame.Surface(strip.size, pygame.SRCALPHA)
        band.fill((248, 242, 228, 220))  # translucent parchment
        surface.blit(band, strip.topleft)
        pygame.draw.line(
            surface, self.wing.accent,
            (strip.left, strip.top), (strip.right, strip.top), 1,
        )
        pygame.draw.line(
            surface, self.wing.accent,
            (strip.left, strip.bottom - 1), (strip.right, strip.bottom - 1), 1,
        )
        # One-line summary — first sentence of the thesis, or first 140 chars.
        first = self.wing.thesis.split(". ")[0] + "."
        line = truncate_to_width(first, self.italic_font, strip.width - 40)
        surf = self.italic_font.render(line, True, COL_INK_SOFT)
        surface.blit(surf, surf.get_rect(center=strip.center))
