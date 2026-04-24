"""Exhibit detail overlay.

Pushed on top of the wing scene. Shows the song title, its original
performance, its reperformances, and a curator's note — all in a
scrollable, wrapped column. Numbered links (1…9) open in the browser.
"""

from __future__ import annotations

import webbrowser
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from .. import audio
from ..assets import get_font
from ..constants import (
    COL_GOLD,
    COL_GOLD_DIM,
    COL_INK,
    COL_INK_SOFT,
    COL_MUTED,
    COL_PAPER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from ..content import Exhibit, MediaLink, Wing
from ..ui import draw_panel, draw_wrapped, measure_wrapped_height, render_tracked, wrap_text


PANEL_MARGIN = 48


class ExhibitScene:
    """Overlay shown on top of the wing. The wing underneath is drawn by
    ``draw`` via the game's scene_below reference."""

    def __init__(self, game, exhibit: Exhibit, wing: Wing) -> None:
        self.game = game
        self.exhibit = exhibit
        self.wing = wing

        self.title_font = get_font("heading", 26)
        self.big_title_font = get_font("display", 58)
        self.heading_font = get_font("heading", 24)
        self.sub_font = get_font("body_bold", 20)
        self.body_font = get_font("body", 20)
        self.italic_font = get_font("italic", 20)
        self.small_font = get_font("body", 16)
        self.tag_font = get_font("body_bold", 13)


        self.scroll = 0
        self.content_height = 0
        self.panel_rect = pygame.Rect(
            PANEL_MARGIN, PANEL_MARGIN, SCREEN_WIDTH - 2 * PANEL_MARGIN, SCREEN_HEIGHT - 2 * PANEL_MARGIN
        )
        self.content_rect = self.panel_rect.inflate(-80, -120)
        self.content_rect.top = self.panel_rect.top + 100
        self.content_rect.height = self.panel_rect.height - 160

        # Build ordered list of media links across performances for hotkeys.
        self._links: List[MediaLink] = []
        for perf in (self.exhibit.original,) + self.exhibit.reperformances:
            for ml in perf.media:
                self._links.append(ml)

        # Link hitboxes (content-local coords), populated while rendering.
        self._link_hitboxes: List[Tuple[pygame.Rect, MediaLink]] = []
        # Render content once into an off-screen surface for smooth scrolling.
        self._content_surf: Optional[pygame.Surface] = None
        self._build_content()

    # ------------------------------------------------------------------
    def on_enter(self, **kwargs) -> None:
        pass

    def on_resume(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                audio.play_click()
                self.game.close_exhibit()
                return
            if event.key == pygame.K_DOWN:
                self.scroll = min(self._max_scroll(), self.scroll + 40)
            elif event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 40)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll = min(self._max_scroll(), self.scroll + self.content_rect.height - 40)
            elif event.key == pygame.K_PAGEUP:
                self.scroll = max(0, self.scroll - (self.content_rect.height - 40))
            elif event.key == pygame.K_HOME:
                self.scroll = 0
            elif event.key == pygame.K_END:
                self.scroll = self._max_scroll()
            # Numeric link hotkeys
            number_keys = {
                pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
                pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8,
            }
            if event.key in number_keys:
                idx = number_keys[event.key]
                if 0 <= idx < len(self._links):
                    self._open_link(self._links[idx])
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self._max_scroll(), self.scroll - event.y * 40))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._check_link_click(event.pos)

    def update(self, dt: float) -> None:
        pass

    # ------------------------------------------------------------------
    def _max_scroll(self) -> int:
        return max(0, self.content_height - self.content_rect.height)

    def _open_link(self, link: MediaLink) -> None:
        audio.play_click()
        try:
            webbrowser.open(link.url, new=2, autoraise=True)
        except Exception:
            pass

    def _check_link_click(self, pos: Tuple[int, int]) -> None:
        # Translate to content space
        if not self._link_hitboxes:
            return
        cx = pos[0] - self.content_rect.left
        cy = pos[1] - self.content_rect.top + self.scroll
        for rect, link in self._link_hitboxes:
            if rect.collidepoint(cx, cy):
                self._open_link(link)
                return

    # ------------------------------------------------------------------
    # Content rendering (pre-composed to a tall surface)
    # ------------------------------------------------------------------
    def _build_content(self) -> None:
        w = self.content_rect.width
        # Over-allocate a tall scratch surface; we'll crop to actual height.
        temp_height = 6000
        surf = pygame.Surface((w, temp_height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        y = 0
        # Wing + song header (tracked small-caps accent).
        wing_tag = render_tracked(
            self.tag_font,
            f"{self.wing.title.upper()}   \u00b7   {self.wing.subtitle.upper()}",
            self.wing.accent,
            tracking=3,
        )
        surf.blit(wing_tag, (0, y))
        y += wing_tag.get_height() + 10

        # Header row: album cover on the left, big song title on the right.
        from ..assets import load_image
        cover = load_image(f"exhibits/{self.exhibit.art_key}.png")
        cover_size = 160
        title_left = 0
        if cover is not None:
            scaled = pygame.transform.smoothscale(cover, (cover_size, cover_size))
            # thin dark frame around the cover
            pygame.draw.rect(
                surf, (42, 30, 22),
                (0, y - 2, cover_size + 4, cover_size + 4),
            )
            surf.blit(scaled, (2, y))
            title_left = cover_size + 24

        song = self.exhibit.song
        title_surf = self.big_title_font.render(song, True, COL_INK)
        max_title_w = w - title_left
        if title_surf.get_width() > max_title_w:
            f = get_font("display", 44)
            title_surf = f.render(song, True, COL_INK)
        title_y = y + (cover_size - title_surf.get_height()) // 2 if cover else y
        surf.blit(title_surf, (title_left, title_y))

        # Decorative double rule under the header row.
        y = max(y + cover_size, title_y + title_surf.get_height()) + 12
        pygame.draw.line(surf, COL_GOLD, (0, y), (w, y), 2)
        pygame.draw.line(surf, COL_GOLD_DIM, (0, y + 6), (int(w * 0.6), y + 6), 1)
        y += 24

        # Two-column style: Original | Reperformances. On this width we can
        # afford a full-width stack for readability.
        y = self._render_performance_block(
            surf, y, w, heading="Original Performance", perf=self.exhibit.original, is_original=True
        )
        y += 18
        for i, perf in enumerate(self.exhibit.reperformances):
            label = "Reperformance" if len(self.exhibit.reperformances) == 1 else f"Reperformance {i + 1}"
            y = self._render_performance_block(
                surf, y, w, heading=label, perf=perf, is_original=False
            )
            y += 14

        # Curator's note
        y += 12
        note_head = self.heading_font.render("Curator's Note", True, COL_INK)
        surf.blit(note_head, (0, y))
        y += note_head.get_height() + 6
        pygame.draw.line(surf, COL_GOLD, (0, y), (90, y), 2)
        y += 12
        y = draw_wrapped(
            surf, self.exhibit.curator_note, self.body_font, COL_INK, 0, y, w, line_spacing=6
        )

        self.content_height = y + 20

        # Crop the surface to actual content height + a little padding.
        final = pygame.Surface((w, self.content_height), pygame.SRCALPHA)
        final.blit(surf, (0, 0))
        self._content_surf = final

    def _render_performance_block(
        self, surf: pygame.Surface, y: int, w: int, heading: str, perf, is_original: bool
    ) -> int:
        # Header row
        head = self.heading_font.render(heading, True, self.wing.accent)
        surf.blit(head, (0, y))
        year = self.small_font.render(perf.year, True, COL_MUTED)
        surf.blit(year, (w - year.get_width(), y + 4))
        y += head.get_height() + 2
        pygame.draw.line(surf, self.wing.accent, (0, y), (w, y), 1)
        y += 10
        # Performer as bold
        performer = self.sub_font.render(perf.performer, True, COL_INK)
        surf.blit(performer, (0, y))
        y += performer.get_height() + 4
        # Setting (italic-ish)
        y = draw_wrapped(surf, f"Setting — {perf.setting}", self.body_font, COL_INK_SOFT, 0, y, w, line_spacing=4)
        y += 4
        y = draw_wrapped(surf, f"Register — {perf.register}", self.body_font, COL_INK, 0, y, w, line_spacing=4)
        y += 4
        # Media links. Display: "[1] Link label \u2197" — no raw URL dumped.
        if perf.media:
            y += 6
            for ml in perf.media:
                idx = self._links.index(ml) + 1
                kind_icon = {"article": "\u25a1", "audio": "\u266b"}.get(ml.kind, "\u25b7")
                label = f"[{idx}]  {kind_icon}  {ml.label}"
                link_color = (48, 76, 140)
                link_surf = self.body_font.render(label, True, link_color)
                rect = pygame.Rect(0, y, link_surf.get_width(), link_surf.get_height())
                surf.blit(link_surf, (0, y))
                pygame.draw.line(
                    surf, link_color,
                    (rect.left, rect.bottom), (rect.right, rect.bottom), 1,
                )
                self._link_hitboxes.append((rect.inflate(10, 8), ml))
                y += link_surf.get_height() + 6
        return y

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        # Draw the wing scene underneath via the manager, then a dim overlay,
        # then the exhibit panel.
        below = self.game.scenes.scene_below
        if below:
            below.draw(surface)
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((12, 10, 8, 200))
        surface.blit(dim, (0, 0))

        draw_panel(
            surface,
            self.panel_rect,
            bg=COL_PAPER,
            border=self.wing.accent,
            border_width=4,
            shadow=True,
            radius=10,
        )

        # Top bar: close and wing label
        top_bar = pygame.Rect(
            self.panel_rect.left + 20, self.panel_rect.top + 18,
            self.panel_rect.width - 40, 60,
        )
        wing_label = render_tracked(
            self.title_font,
            f"EXHIBIT   \u00b7   {self.wing.title.upper()}",
            self.wing.accent,
            tracking=3,
        )
        surface.blit(wing_label, (top_bar.left, top_bar.top + 4))

        close_hint = self.small_font.render(
            "Esc / B to close     1-9 to open links     wheel or arrows to scroll",
            True, COL_MUTED,
        )
        surface.blit(close_hint, close_hint.get_rect(topright=(top_bar.right, top_bar.top + 8)))

        pygame.draw.line(
            surface, COL_GOLD_DIM,
            (self.panel_rect.left + 24, self.panel_rect.top + 82),
            (self.panel_rect.right - 24, self.panel_rect.top + 82), 1,
        )

        # Clip and blit scrolled content
        if self._content_surf is not None:
            prev = surface.get_clip()
            surface.set_clip(self.content_rect)
            surface.blit(
                self._content_surf,
                (self.content_rect.left, self.content_rect.top - self.scroll),
            )
            surface.set_clip(prev)

        # Scrollbar
        self._draw_scrollbar(surface)

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        if self.content_height <= self.content_rect.height:
            return
        track = pygame.Rect(
            self.content_rect.right + 12, self.content_rect.top,
            6, self.content_rect.height,
        )
        pygame.draw.rect(surface, (220, 210, 190), track, border_radius=3)
        frac_visible = self.content_rect.height / self.content_height
        handle_h = max(30, int(track.height * frac_visible))
        handle_y = track.top + int((track.height - handle_h) * (self.scroll / self._max_scroll()))
        handle = pygame.Rect(track.left, handle_y, track.width, handle_h)
        pygame.draw.rect(surface, self.wing.accent, handle, border_radius=3)
