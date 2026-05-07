"""Persistent "Guiding Questions on a scroll" overlay.

Rendered every frame (independently of the SceneManager) once the player
has visited the Reading Room's Guiding Questions and pressed *Pin to
scroll*. It shows up as a small folded-paper icon in the top-right
corner; clicking it (or pressing G) toggles a compact overlay
listing the four guiding questions verbatim.

This stays small and self-contained so it can never block scene
interactions: the icon is in the screen corner and the panel is
centered without intercepting other clicks.
"""

from __future__ import annotations

from typing import Optional

import pygame

from .. import audio
from ..assets import get_font
from ..constants import (
    COL_GOLD,
    COL_INK,
    COL_INK_SOFT,
    COL_PAPER,
    COL_READING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from ..content import READING_QUESTIONS
from ..ui import draw_panel, wrap_text


ICON_W, ICON_H = 56, 64
ICON_MARGIN_X = 14
ICON_MARGIN_Y = 92  # below the top banner so it never collides with scene titles


class GuidingScrollOverlay:
    """Lifecycle hooks: the parent ``Game`` calls ``handle_event`` /
    ``draw`` after the scene's. ``visible`` is a pure UI state (not
    saved across runs)."""

    def __init__(self, game) -> None:
        self.game = game
        self.expanded = False
        self.icon_rect = pygame.Rect(
            SCREEN_WIDTH - ICON_W - ICON_MARGIN_X, ICON_MARGIN_Y, ICON_W, ICON_H,
        )
        self.close_rect = pygame.Rect(0, 0, 28, 28)
        self.title_font = get_font("heading", 24)
        self.body_font = get_font("body", 17)
        self.body_bold_font = get_font("body_bold", 17)
        self.small_font = get_font("body", 13)

        # Scrollable interior. The panel is a fixed-size card; if the
        # questions don't fit (and they often don't, between heading +
        # 3-line answers), we render once into a tall surface and clip
        # to a viewport that the player can scroll with wheel/arrows.
        self._content_surf: Optional[pygame.Surface] = None
        self._content_height = 0
        self._scroll = 0

    @property
    def pinned(self) -> bool:
        return bool(getattr(self.game, "guiding_pinned", False))

    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when the event was consumed by this overlay."""
        if not self.pinned:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.expanded = not self.expanded
                if self.expanded:
                    self._scroll = 0
                audio.play_click()
                return True
            if self.expanded:
                if event.key in (pygame.K_ESCAPE,):
                    self.expanded = False
                    audio.play_click()
                    return True
                if event.key == pygame.K_DOWN:
                    self._scroll = min(self._max_scroll(), self._scroll + 36)
                    return True
                if event.key == pygame.K_UP:
                    self._scroll = max(0, self._scroll - 36)
                    return True
                if event.key == pygame.K_PAGEDOWN:
                    self._scroll = min(self._max_scroll(), self._scroll + self._viewport_h() - 24)
                    return True
                if event.key == pygame.K_PAGEUP:
                    self._scroll = max(0, self._scroll - (self._viewport_h() - 24))
                    return True
                if event.key == pygame.K_HOME:
                    self._scroll = 0
                    return True
                if event.key == pygame.K_END:
                    self._scroll = self._max_scroll()
                    return True
        if event.type == pygame.MOUSEWHEEL and self.expanded:
            self._scroll = max(0, min(self._max_scroll(), self._scroll - event.y * 36))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.expanded:
                if self.close_rect.collidepoint(event.pos):
                    self.expanded = False
                    audio.play_click()
                    return True
                # Click outside the panel closes it; clicks inside the panel
                # are absorbed (no per-citation links, just plain copy).
                panel = self._panel_rect()
                if not panel.collidepoint(event.pos):
                    self.expanded = False
                    audio.play_click()
                    return True
                return True
            if self.icon_rect.collidepoint(event.pos):
                self.expanded = True
                self._scroll = 0
                audio.play_click()
                return True
        return False

    # ------------------------------------------------------------------
    def _viewport_h(self) -> int:
        # Available content height inside the panel chrome.
        return self._panel_rect().height - 110

    def _max_scroll(self) -> int:
        return max(0, self._content_height - self._viewport_h())

    # ------------------------------------------------------------------
    def _panel_rect(self) -> pygame.Rect:
        # A bit larger than before so the questions fit at this density;
        # any overflow is handled by the scrollbar below.
        w = min(700, SCREEN_WIDTH - 80)
        h = min(520, SCREEN_HEIGHT - 80)
        return pygame.Rect(
            (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2 - 10, w, h,
        )

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.pinned:
            return

        self._draw_icon(surface)

        if self.expanded:
            self._draw_panel(surface)

    def _draw_icon(self, surface: pygame.Surface) -> None:
        r = self.icon_rect
        # Folded-paper rectangle with a corner curl + gold seal.
        shadow = pygame.Surface((r.width + 6, r.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 110), shadow.get_rect(), border_radius=4)
        surface.blit(shadow, (r.left - 1, r.top + 3))

        body = pygame.Rect(r.left, r.top, r.width, r.height)
        pygame.draw.rect(surface, COL_PAPER, body, border_radius=3)
        pygame.draw.rect(surface, COL_INK, body, width=2, border_radius=3)

        # Three thin "lines of writing".
        for i in range(3):
            y = r.top + 14 + i * 9
            pygame.draw.line(
                surface, COL_INK_SOFT,
                (r.left + 8, y), (r.right - 14, y), 1,
            )

        # Folded corner at top-right (small triangle with shading).
        fold_size = 12
        pts = [
            (r.right - fold_size, r.top),
            (r.right, r.top),
            (r.right, r.top + fold_size),
        ]
        pygame.draw.polygon(surface, (224, 214, 192), pts)
        pygame.draw.polygon(surface, COL_INK, pts, 1)

        # Gold seal at the bottom.
        seal_cx = r.right - 14
        seal_cy = r.bottom - 12
        pygame.draw.circle(surface, COL_READING, (seal_cx, seal_cy), 7)
        pygame.draw.circle(surface, COL_GOLD, (seal_cx, seal_cy), 7, 1)

        # Tiny "G" letter cue under the icon (key hint).
        hint = self.small_font.render("G", True, COL_INK)
        surface.blit(hint, hint.get_rect(midtop=(r.centerx, r.bottom + 2)))

    def _draw_panel(self, surface: pygame.Surface) -> None:
        # Soft dim behind the panel only (don't take over the whole frame —
        # the player should still feel rooted in the underlying scene).
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((10, 8, 6, 130))
        surface.blit(dim, (0, 0))

        panel = self._panel_rect()
        draw_panel(
            surface, panel,
            bg=COL_PAPER, border=COL_READING, border_width=3,
            shadow=True, radius=8,
        )

        title = self.title_font.render(
            "Guiding Questions \u2014 take with you", True, COL_INK,
        )
        surface.blit(title, (panel.left + 22, panel.top + 18))
        pygame.draw.line(
            surface, COL_GOLD,
            (panel.left + 22, panel.top + 18 + title.get_height() + 6),
            (panel.right - 80, panel.top + 18 + title.get_height() + 6),
            1,
        )

        # Close button (X).
        self.close_rect.topright = (panel.right - 14, panel.top + 14)
        pygame.draw.rect(surface, COL_INK, self.close_rect, border_radius=6)
        pygame.draw.line(
            surface, COL_PAPER,
            (self.close_rect.left + 8, self.close_rect.top + 8),
            (self.close_rect.right - 8, self.close_rect.bottom - 8), 2,
        )
        pygame.draw.line(
            surface, COL_PAPER,
            (self.close_rect.right - 8, self.close_rect.top + 8),
            (self.close_rect.left + 8, self.close_rect.bottom - 8), 2,
        )

        # Scrollable body. Render to a tall scratch surface, then blit
        # the slice that corresponds to the current scroll offset into a
        # clipped viewport inside the panel.
        body_x_inset = 28
        body_w = panel.width - 2 * body_x_inset - 14   # 14 px scrollbar gutter
        viewport = pygame.Rect(
            panel.left + body_x_inset,
            panel.top + 18 + title.get_height() + 26,
            body_w,
            panel.bottom - (panel.top + 18 + title.get_height() + 26) - 38,
        )
        if self._content_surf is None:
            self._content_surf = self._build_content_surface(body_w)

        max_scroll = self._max_scroll()
        if self._scroll > max_scroll:
            self._scroll = max_scroll

        prev_clip = surface.get_clip()
        surface.set_clip(viewport)
        surface.blit(self._content_surf, (viewport.left, viewport.top - self._scroll))
        surface.set_clip(prev_clip)

        # Scrollbar (only when content overflows).
        if self._content_height > viewport.height:
            track = pygame.Rect(viewport.right + 6, viewport.top, 6, viewport.height)
            pygame.draw.rect(surface, (220, 210, 190), track, border_radius=3)
            frac = viewport.height / self._content_height
            handle_h = max(28, int(track.height * frac))
            denom = max(1, max_scroll)
            py = track.top + int((track.height - handle_h) * (self._scroll / denom))
            handle = pygame.Rect(track.left, py, track.width, handle_h)
            pygame.draw.rect(surface, COL_READING, handle, border_radius=3)

        hint = self.small_font.render(
            "G or X / click outside  to close   wheel/arrows scroll",
            True, (140, 130, 116),
        )
        surface.blit(hint, hint.get_rect(bottomright=(panel.right - 16, panel.bottom - 10)))

    def _build_content_surface(self, body_w: int) -> pygame.Surface:
        """Compose the full questions list onto a tall surface that we
        then scroll inside the visible viewport."""
        scratch = pygame.Surface((body_w, 4000), pygame.SRCALPHA)
        cy = 0
        for i, (heading, body) in enumerate(READING_QUESTIONS.sections, start=1):
            num = self.body_bold_font.render(f"{i}.", True, COL_READING)
            scratch.blit(num, (0, cy))
            head_x = num.get_width() + 8
            head_w = body_w - head_x
            for hi, line in enumerate(wrap_text(heading, self.body_bold_font, head_w)):
                s = self.body_bold_font.render(line, True, COL_INK)
                scratch.blit(s, (head_x if hi == 0 else 18, cy))
                cy += s.get_height() + 2
            cy += 4
            for line in wrap_text(body, self.body_font, body_w - 18):
                s = self.body_font.render(line, True, COL_INK_SOFT)
                scratch.blit(s, (18, cy))
                cy += s.get_height() + 2
            cy += 14
        self._content_height = cy
        final = pygame.Surface((body_w, max(1, cy)), pygame.SRCALPHA)
        final.blit(scratch, (0, 0))
        return final
