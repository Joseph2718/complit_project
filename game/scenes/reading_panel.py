"""Reading-room overlay panel.

Shown on top of the Reading Room scene when the player inspects a
lectern (Curatorial Thesis / Working Vocabulary / Guiding Questions).

Renders one ``ReadingEntry``: a title, intro paragraph, and the
entry's sub-sections, with Chicago-style ``[N]`` markers rendered as
small raised superscript numerals that scroll the panel to the matching
References row at the bottom.

For the Guiding Questions entry, the panel adds a single primary
button — "Pin to scroll" — which lets the player carry the questions
around the museum on a small folded-paper icon (handled by
``ReadingScrollOverlay``).
"""

from __future__ import annotations

import re
import webbrowser
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
    COL_READING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from ..content import Citation, ReadingEntry
from ..ui import draw_panel, render_tracked, wrap_text


PANEL_MARGIN = 60
# Inner padding on the content rect: keep generous side margins so
# text never reads as touching the panel border.
CONTENT_PAD_X = 56
CONTENT_PAD_TOP = 110
CONTENT_PAD_BOTTOM = 80
LINK_COLOR = (48, 76, 140)
CITATION_RE = re.compile(r"\[(\d+)\]")
_NUM_SUPERSCRIPT = str.maketrans(
    "0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"
)


def _superscript(n: int) -> str:
    return str(n).translate(_NUM_SUPERSCRIPT)


def _cite_pt(body_font: pygame.font.Font) -> int:
    # Smaller-than-body, capped so headings don't end up with giant numerals.
    return max(13, min(17, body_font.get_height() - 3))


class ReadingPanelScene:
    def __init__(self, game, entry: ReadingEntry) -> None:
        self.game = game
        self.entry = entry

        self.title_font = get_font("display", 46)
        self.section_font = get_font("heading", 24)
        self.body_font = get_font("body", 19)
        self.body_bold_font = get_font("body_bold", 19)
        self.italic_font = get_font("italic", 19)
        self.small_font = get_font("body", 15)
        self.tag_font = get_font("body_bold", 13)

        self.scroll = 0
        self.content_height = 0

        self.panel_rect = pygame.Rect(
            PANEL_MARGIN, PANEL_MARGIN,
            SCREEN_WIDTH - 2 * PANEL_MARGIN,
            SCREEN_HEIGHT - 2 * PANEL_MARGIN,
        )
        # Reserve a wider gutter on the right for the scrollbar so text
        # never bleeds into it. Bottom pad leaves room for the action
        # button row (Guiding Questions only).
        self.content_rect = pygame.Rect(
            self.panel_rect.left + CONTENT_PAD_X,
            self.panel_rect.top + CONTENT_PAD_TOP,
            self.panel_rect.width - 2 * CONTENT_PAD_X - 14,
            self.panel_rect.height - CONTENT_PAD_TOP - CONTENT_PAD_BOTTOM,
        )

        self._citations_by_num = {c.number: c for c in entry.citations}
        self._citation_y: dict = {}
        self._inline_cite_hitboxes: List[Tuple[pygame.Rect, int]] = []
        self._citation_url_hitboxes: List[Tuple[pygame.Rect, Citation]] = []

        # Close button (X) — top-right of the panel header. Drawn once
        # in ``draw`` against the panel rect (not the scrolled content),
        # so it's always visible.
        self.close_rect = pygame.Rect(0, 0, 30, 30)
        self.close_rect.topright = (
            self.panel_rect.right - 14, self.panel_rect.top + 14,
        )

        # Action button shown only for the Guiding Questions entry. It
        # copies the questions to a small folded-paper icon in the
        # screen corner that can be re-opened with G from any room.
        self.pin_rect: Optional[pygame.Rect] = None
        if self.entry.key == "questions":
            w, h = 320, 38
            self.pin_rect = pygame.Rect(
                self.panel_rect.right - w - 22,
                self.panel_rect.bottom - h - 16,
                w, h,
            )

        self._content_surf: Optional[pygame.Surface] = None
        self._build_content()

    # ------------------------------------------------------------------
    def on_enter(self, **kwargs) -> None: pass
    def on_resume(self) -> None: pass
    def on_exit(self) -> None: pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                audio.play_click()
                self.game.scenes.pop()
                return
            if event.key == pygame.K_p and self.pin_rect is not None:
                self._toggle_pin()
                return
            if event.key == pygame.K_DOWN:
                self.scroll = min(self._max_scroll(), self.scroll + 50)
            elif event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 50)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll = min(self._max_scroll(), self.scroll + self.content_rect.height - 40)
            elif event.key == pygame.K_PAGEUP:
                self.scroll = max(0, self.scroll - (self.content_rect.height - 40))
            elif event.key == pygame.K_HOME:
                self.scroll = 0
            elif event.key == pygame.K_END:
                self.scroll = self._max_scroll()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self._max_scroll(), self.scroll - event.y * 50))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                audio.play_click()
                self.game.scenes.pop()
                return
            if self.pin_rect is not None and self.pin_rect.collidepoint(event.pos):
                self._toggle_pin()
                return
            self._check_clicks(event.pos)

    def _toggle_pin(self) -> None:
        cur = getattr(self.game, "guiding_pinned", False)
        self.game.guiding_pinned = not cur
        # Visiting the entry counts as having read it.
        self.game.guiding_unlocked = True
        audio.play_click()

    def update(self, dt: float) -> None:
        pass

    # ------------------------------------------------------------------
    def _max_scroll(self) -> int:
        return max(0, self.content_height - self.content_rect.height)

    def _check_clicks(self, pos: Tuple[int, int]) -> None:
        if not self.content_rect.collidepoint(pos):
            return
        cx = pos[0] - self.content_rect.left
        cy = pos[1] - self.content_rect.top + self.scroll
        for rect, num in self._inline_cite_hitboxes:
            if rect.collidepoint(cx, cy):
                target_y = self._citation_y.get(num)
                if target_y is not None:
                    self.scroll = max(0, min(self._max_scroll(), target_y - 24))
                    audio.play_click()
                return
        for rect, c in self._citation_url_hitboxes:
            if rect.collidepoint(cx, cy):
                audio.play_click()
                try:
                    webbrowser.open(c.url, new=2, autoraise=True)
                except Exception:
                    pass
                return

    # ------------------------------------------------------------------
    def _build_content(self) -> None:
        w = self.content_rect.width
        scratch = pygame.Surface((w, 12000), pygame.SRCALPHA)
        y = 0

        tag = render_tracked(
            self.tag_font, "READING ROOM", COL_READING, tracking=3,
        )
        scratch.blit(tag, (0, y))
        y += tag.get_height() + 8

        title = self.title_font.render(self.entry.title, True, COL_INK)
        scratch.blit(title, (0, y))
        y += title.get_height() + 6

        pygame.draw.line(scratch, COL_GOLD, (0, y), (w, y), 2)
        pygame.draw.line(scratch, COL_GOLD_DIM, (0, y + 6), (int(w * 0.45), y + 6), 1)
        y += 22

        # Intro
        if self.entry.intro:
            y = self._draw_text_with_citations(
                scratch, self.entry.intro, self.italic_font, COL_INK_SOFT,
                0, y, w, line_spacing=5,
            )
            y += 16

        # Sections
        for heading, body in self.entry.sections:
            # Heading may contain Chicago-style markers like "[1]" that
            # need to render as clickable superscript numerals — same
            # behavior as the body text uses below.
            bar_h = self.section_font.get_height()
            pygame.draw.rect(scratch, COL_READING, (0, y + 2, 4, bar_h - 4))
            y_after = self._draw_text_with_citations(
                scratch, heading, self.section_font, COL_INK,
                12, y, w - 12, line_spacing=4,
            )
            y = max(y + bar_h + 8, y_after + 4)
            for paragraph in body.split("\n\n"):
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                y = self._draw_text_with_citations(
                    scratch, paragraph, self.body_font, COL_INK,
                    0, y, w, line_spacing=5,
                )
                y += 8
            y += 8

        # References
        if self.entry.citations:
            y += 12
            pygame.draw.line(scratch, COL_GOLD_DIM, (0, y), (w, y), 1)
            y += 14
            head = render_tracked(self.tag_font, "References", COL_READING, tracking=3)
            scratch.blit(head, (0, y))
            y += head.get_height() + 10
            for c in self.entry.citations:
                y = self._render_citation(scratch, y, w, c)
                y += 6

        self.content_height = y + 20
        final = pygame.Surface((w, self.content_height), pygame.SRCALPHA)
        final.blit(scratch, (0, 0))
        self._content_surf = final

    # ------------------------------------------------------------------
    def _draw_text_with_citations(
        self, surf, text: str, font, color,
        x: int, y: int, max_width: int, line_spacing: int = 4,
    ) -> int:
        cite_pt = _cite_pt(font)
        cite_font = get_font("body_bold", cite_pt)
        space_w = font.size(" ")[0]
        line_h = font.get_height() + line_spacing
        cur_x, cur_y = x, y

        def newline():
            nonlocal cur_x, cur_y
            cur_x = x
            cur_y += line_h

        for word in text.split():
            parts: List[Tuple[str, object]] = []
            i = 0
            for m in CITATION_RE.finditer(word):
                if m.start() > i:
                    parts.append(("text", word[i:m.start()]))
                parts.append(("cite", int(m.group(1))))
                i = m.end()
            if i < len(word):
                parts.append(("text", word[i:]))

            # Measure
            tw = 0
            for kind, val in parts:
                if kind == "text":
                    tw += font.size(val)[0]
                else:
                    n = int(val)
                    if n in self._citations_by_num:
                        tw += cite_font.size(_superscript(n))[0]
                    else:
                        tw += font.size(f"[{n}]")[0]

            if cur_x > x:
                if cur_x + space_w + tw > x + max_width:
                    newline()
                else:
                    cur_x += space_w
            else:
                if cur_x + tw > x + max_width and tw <= max_width:
                    newline()

            for kind, val in parts:
                if kind == "text":
                    s = font.render(val, True, color)
                    surf.blit(s, (cur_x, cur_y))
                    cur_x += s.get_width()
                else:
                    n = int(val)
                    if n in self._citations_by_num:
                        s = cite_font.render(_superscript(n), True, COL_READING)
                        lift = max(2, (font.get_height() - cite_font.get_height()) // 2)
                        surf.blit(s, (cur_x, cur_y - lift))
                        rect = pygame.Rect(
                            cur_x, cur_y - lift, s.get_width(), s.get_height()
                        )
                        self._inline_cite_hitboxes.append((rect, n))
                        cur_x += s.get_width()
                    else:
                        s = font.render(f"[{n}]", True, color)
                        surf.blit(s, (cur_x, cur_y))
                        cur_x += s.get_width()
        return cur_y + line_h

    def _render_citation(self, surf, y: int, w: int, c: Citation) -> int:
        self._citation_y[c.number] = y
        num = self.body_bold_font.render(f"{c.number}.", True, COL_READING)
        nr = num.get_rect(topleft=(0, y))
        surf.blit(num, nr.topleft)
        body_x = nr.right + 8
        prose = (c.label or c.url).strip()
        if prose and prose[-1] not in ".!?":
            prose += "."
        cy = y
        for line in wrap_text(prose, self.body_font, w - body_x):
            ls = self.body_font.render(line, True, COL_INK)
            surf.blit(ls, (body_x, cy))
            cy += ls.get_height() + 2
        for line in wrap_text(c.url, self.small_font, w - body_x):
            us = self.small_font.render(line, True, LINK_COLOR)
            rect = pygame.Rect(body_x, cy, us.get_width(), us.get_height())
            surf.blit(us, rect.topleft)
            pygame.draw.line(
                surf, LINK_COLOR,
                (rect.left, rect.bottom), (rect.right, rect.bottom), 1,
            )
            self._citation_url_hitboxes.append((rect.inflate(8, 4), c))
            cy += us.get_height() + 2
        return cy

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        below = self.game.scenes.scene_below
        if below:
            below.draw(surface)
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((12, 10, 8, 200))
        surface.blit(dim, (0, 0))

        draw_panel(
            surface, self.panel_rect,
            bg=COL_PAPER, border=COL_READING, border_width=4,
            shadow=True, radius=10,
        )

        # Top-bar tag and footer hint.
        tag = render_tracked(
            get_font("heading", 22),
            "READING ROOM",
            COL_READING,
            tracking=3,
        )
        surface.blit(tag, (self.panel_rect.left + 24, self.panel_rect.top + 22))
        hint = self.small_font.render(
            "Esc / B / X to close   note refs scroll to References   wheel/arrows scroll",
            True, COL_MUTED,
        )
        surface.blit(
            hint,
            hint.get_rect(
                topright=(self.close_rect.left - 12, self.panel_rect.top + 26)
            ),
        )

        # X close button.
        cr = self.close_rect
        pygame.draw.rect(surface, COL_INK, cr, border_radius=6)
        pygame.draw.line(
            surface, COL_PAPER,
            (cr.left + 8, cr.top + 8), (cr.right - 8, cr.bottom - 8), 2,
        )
        pygame.draw.line(
            surface, COL_PAPER,
            (cr.right - 8, cr.top + 8), (cr.left + 8, cr.bottom - 8), 2,
        )

        # Scrolled content.
        if self._content_surf is not None:
            prev = surface.get_clip()
            surface.set_clip(self.content_rect)
            surface.blit(
                self._content_surf,
                (self.content_rect.left, self.content_rect.top - self.scroll),
            )
            surface.set_clip(prev)

        self._draw_scrollbar(surface)

        if self.pin_rect is not None:
            pinned = getattr(self.game, "guiding_pinned", False)
            label = (
                "\u2713  Carrying these with me  (P)"
                if pinned
                else "Take these with me  (P)"
            )
            bg = COL_READING if pinned else COL_PAPER
            fg = COL_PAPER if pinned else COL_READING
            txt = self.body_bold_font.render(label, True, fg)
            # Resize the button rect to fit the text with padding.
            pad_x, pad_y = 20, 0
            btn = txt.get_rect().inflate(pad_x * 2, pad_y * 2)
            btn.center = self.pin_rect.center
            pygame.draw.rect(surface, bg, btn, border_radius=8)
            pygame.draw.rect(surface, COL_READING, btn, width=2, border_radius=8)
            surface.blit(txt, txt.get_rect(center=btn.center))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        if self.content_height <= self.content_rect.height:
            return
        track = pygame.Rect(
            self.content_rect.right + 12, self.content_rect.top,
            6, self.content_rect.height,
        )
        pygame.draw.rect(surface, (220, 210, 190), track, border_radius=3)
        frac = self.content_rect.height / self.content_height
        h = max(30, int(track.height * frac))
        ymax = self._max_scroll() or 1
        py = track.top + int((track.height - h) * (self.scroll / ymax))
        handle = pygame.Rect(track.left, py, track.width, h)
        pygame.draw.rect(surface, COL_READING, handle, border_radius=3)
