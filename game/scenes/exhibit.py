"""Exhibit detail overlay.

Pushed on top of the wing scene. Renders a museum-style catalogue entry:
header with cover art, summary blocks for the original performance and
reperformance(s), the long-form analysis essay broken into sections (with
embedded frame images), and a numbered footnote list at the end. The
content surface is pre-composed once and then scrolled.
"""

from __future__ import annotations

import re
import webbrowser
from typing import List, Optional, Tuple

import pygame

from .. import audio
from ..assets import get_font, load_image
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
from ..content import Citation, EssaySection, Exhibit, MediaLink, Wing
from ..ui import draw_panel, render_tracked, wrap_text


PANEL_MARGIN = 48
LINK_COLOR = (48, 76, 140)
CITATION_RE = re.compile(r"\[(\d+)\]")


class ExhibitScene:
    """Overlay shown on top of the wing. The wing underneath is drawn by
    ``draw`` via the game's ``scene_below`` reference."""

    def __init__(self, game, exhibit: Exhibit, wing: Wing) -> None:
        self.game = game
        self.exhibit = exhibit
        self.wing = wing

        self.title_font = get_font("heading", 24)
        self.big_title_font = get_font("display", 56)
        self.section_font = get_font("heading", 22)
        self.sub_font = get_font("body_bold", 18)
        self.body_font = get_font("body", 18)
        self.body_bold_font = get_font("body_bold", 18)
        self.italic_font = get_font("italic", 18)
        self.small_font = get_font("body", 15)
        self.tiny_font = get_font("body", 12)
        self.tag_font = get_font("body_bold", 13)

        self.scroll = 0
        self.content_height = 0
        self.panel_rect = pygame.Rect(
            PANEL_MARGIN, PANEL_MARGIN, SCREEN_WIDTH - 2 * PANEL_MARGIN, SCREEN_HEIGHT - 2 * PANEL_MARGIN
        )
        self.content_rect = self.panel_rect.inflate(-80, -120)
        self.content_rect.top = self.panel_rect.top + 100
        self.content_rect.height = self.panel_rect.height - 160

        # Ordered media links, used for numeric hotkeys (1..9).
        self._links: List[MediaLink] = []
        for perf in (self.exhibit.original,) + self.exhibit.reperformances:
            for ml in perf.media:
                self._links.append(ml)

        # Hitboxes in content-local coordinates: media links and citation URLs.
        self._link_hitboxes: List[Tuple[pygame.Rect, MediaLink]] = []
        # Inline [N] markers: clicking scrolls to that citation row.
        # Stored as (rect, citation_number).
        self._inline_cite_hitboxes: List[Tuple[pygame.Rect, int]] = []
        # URL lines inside the NOTES section: clicking opens the link.
        self._citation_url_hitboxes: List[Tuple[pygame.Rect, Citation]] = []

        # Citation lookup by number, and y-position of each row in NOTES.
        self._citations_by_num = {c.number: c for c in self.exhibit.citations}
        # Populated during _build_content: maps citation number -> content-local y.
        self._citation_y: dict = {}

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
            number_keys = {
                pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
                pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8,
            }
            if event.key in number_keys:
                idx = number_keys[event.key]
                if 0 <= idx < len(self._links):
                    self._open_url(self._links[idx].url)
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self._max_scroll(), self.scroll - event.y * 50))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._check_clicks(event.pos)

    def update(self, dt: float) -> None:
        pass

    # ------------------------------------------------------------------
    def _max_scroll(self) -> int:
        return max(0, self.content_height - self.content_rect.height)

    def _open_url(self, url: str) -> None:
        audio.play_click()
        try:
            webbrowser.open(url, new=2, autoraise=True)
        except Exception:
            pass

    def _check_clicks(self, pos: Tuple[int, int]) -> None:
        if not self.content_rect.collidepoint(pos):
            return
        cx = pos[0] - self.content_rect.left
        cy = pos[1] - self.content_rect.top + self.scroll
        for rect, ml in self._link_hitboxes:
            if rect.collidepoint(cx, cy):
                self._open_url(ml.url)
                return
        # Inline [N] marker: scroll so that citation row is visible.
        for rect, num in self._inline_cite_hitboxes:
            if rect.collidepoint(cx, cy):
                self._scroll_to_citation(num)
                return
        # URL line in NOTES: open the link.
        for rect, citation in self._citation_url_hitboxes:
            if rect.collidepoint(cx, cy):
                self._open_url(citation.url)
                return

    def _scroll_to_citation(self, num: int) -> None:
        """Scroll the content so the footnote for citation ``num`` is visible."""
        target_y = self._citation_y.get(num)
        if target_y is None:
            return
        audio.play_click()
        # Place the citation row near the top of the visible area with a
        # small top margin so it reads in context.
        margin = 24
        self.scroll = max(0, min(self._max_scroll(), target_y - margin))

    # ------------------------------------------------------------------
    # Content rendering — composed once into an off-screen surface.
    # ------------------------------------------------------------------
    def _build_content(self) -> None:
        w = self.content_rect.width
        # Generously oversize the scratch surface; we crop after.
        scratch = pygame.Surface((w, 12000), pygame.SRCALPHA)
        scratch.fill((0, 0, 0, 0))
        y = 0

        # ------ Wing tag ------
        wing_tag = render_tracked(
            self.tag_font,
            f"{self.wing.title.upper()}   \u00b7   {self.wing.subtitle.upper()}",
            self.wing.accent,
            tracking=3,
        )
        scratch.blit(wing_tag, (0, y))
        y += wing_tag.get_height() + 12

        # ------ Header: cover + title ------
        cover = load_image(f"exhibits/{self.exhibit.art_key}.png")
        cover_size = 168
        title_left = 0
        if cover is not None:
            scaled = pygame.transform.smoothscale(cover, (cover_size, cover_size))
            pygame.draw.rect(
                scratch, (42, 30, 22),
                (0, y - 2, cover_size + 4, cover_size + 4),
            )
            scratch.blit(scaled, (2, y))
            title_left = cover_size + 28

        # Big song title; downscale font if it would overflow.
        song = self.exhibit.song
        title_surf = self.big_title_font.render(song, True, COL_INK)
        max_title_w = w - title_left
        title_font_used = self.big_title_font
        if title_surf.get_width() > max_title_w:
            for size in (48, 42, 36, 32):
                f = get_font("display", size)
                tt = f.render(song, True, COL_INK)
                if tt.get_width() <= max_title_w:
                    title_surf = tt
                    title_font_used = f
                    break

        title_y = y
        scratch.blit(title_surf, (title_left, title_y))
        # Subline beneath title: original performer / years span.
        years = [self.exhibit.original.year] + [p.year for p in self.exhibit.reperformances]
        subline = (
            f"{self.exhibit.original.performer}  /  "
            + "  /  ".join(p.performer for p in self.exhibit.reperformances)
        ) if self.exhibit.reperformances else self.exhibit.original.performer
        sub_surf = self.italic_font.render(subline, True, COL_INK_SOFT)
        scratch.blit(sub_surf, (title_left, title_y + title_surf.get_height() + 4))
        years_surf = self.small_font.render("  \u00b7  ".join(years), True, COL_MUTED)
        scratch.blit(
            years_surf,
            (title_left, title_y + title_surf.get_height() + 4 + sub_surf.get_height() + 2),
        )

        header_block_bottom = max(
            y + cover_size if cover is not None else 0,
            title_y + title_surf.get_height() + sub_surf.get_height() + years_surf.get_height() + 8,
        )
        y = header_block_bottom + 20

        # ------ Decorative double rule ------
        pygame.draw.line(scratch, COL_GOLD, (0, y), (w, y), 2)
        pygame.draw.line(scratch, COL_GOLD_DIM, (0, y + 6), (int(w * 0.45), y + 6), 1)
        y += 24

        # ------ Performance summary blocks ------
        y = self._render_performance_block(
            scratch, y, w,
            heading="Original Performance",
            perf=self.exhibit.original,
        )
        y += 14
        for i, perf in enumerate(self.exhibit.reperformances):
            label = "Reperformance" if len(self.exhibit.reperformances) == 1 else f"Reperformance {i + 1}"
            y = self._render_performance_block(scratch, y, w, heading=label, perf=perf)
            y += 14

        # ------ Long-form essay sections ------
        if self.exhibit.essay:
            y += 10
            pygame.draw.line(scratch, COL_GOLD_DIM, (0, y), (w, y), 1)
            y += 16
            essay_label = render_tracked(
                self.tag_font, "ANALYSIS", self.wing.accent, tracking=3
            )
            scratch.blit(essay_label, (0, y))
            y += essay_label.get_height() + 14

            for sec in self.exhibit.essay:
                y = self._render_essay_section(scratch, y, w, sec)
                y += 12

        # ------ Curator's note ------
        if self.exhibit.curator_note:
            y += 6
            pygame.draw.line(scratch, COL_GOLD_DIM, (0, y), (w, y), 1)
            y += 16
            note_head = self.section_font.render("Curator\u2019s Note", True, COL_INK)
            scratch.blit(note_head, (0, y))
            y += note_head.get_height() + 6
            pygame.draw.line(scratch, COL_GOLD, (0, y), (90, y), 2)
            y += 12
            y = self._draw_text_with_citations(
                scratch, self.exhibit.curator_note, self.italic_font, COL_INK_SOFT,
                0, y, w, line_spacing=5,
            )

        # ------ Citations / Notes ------
        if self.exhibit.citations:
            y += 18
            pygame.draw.line(scratch, COL_GOLD_DIM, (0, y), (w, y), 1)
            y += 14
            notes_head = render_tracked(
                self.tag_font, "NOTES", self.wing.accent, tracking=3
            )
            scratch.blit(notes_head, (0, y))
            y += notes_head.get_height() + 10

            for c in self.exhibit.citations:
                y = self._render_citation(scratch, y, w, c)
                y += 6

        self.content_height = y + 20
        final = pygame.Surface((w, self.content_height), pygame.SRCALPHA)
        final.blit(scratch, (0, 0))
        self._content_surf = final

    # ------------------------------------------------------------------
    def _render_performance_block(
        self, surf: pygame.Surface, y: int, w: int, heading: str, perf,
    ) -> int:
        head = self.section_font.render(heading, True, self.wing.accent)
        surf.blit(head, (0, y))
        year = self.small_font.render(perf.year, True, COL_MUTED)
        surf.blit(year, (w - year.get_width(), y + 4))
        y += head.get_height() + 2
        pygame.draw.line(surf, self.wing.accent, (0, y), (w, y), 1)
        y += 10
        performer = self.sub_font.render(perf.performer, True, COL_INK)
        surf.blit(performer, (0, y))
        y += performer.get_height() + 4
        y = self._draw_label_value(
            surf, "Setting", perf.setting, 0, y, w
        )
        y += 2
        y = self._draw_label_value(
            surf, "Register", perf.register, 0, y, w
        )
        if perf.media:
            y += 8
            for ml in perf.media:
                idx = self._links.index(ml) + 1
                kind_icon = {"article": "\u25a1", "audio": "\u266b"}.get(ml.kind, "\u25b7")
                label = f"[{idx}]  {kind_icon}  {ml.label}"
                link_surf = self.body_font.render(label, True, LINK_COLOR)
                rect = pygame.Rect(0, y, link_surf.get_width(), link_surf.get_height())
                surf.blit(link_surf, (0, y))
                pygame.draw.line(
                    surf, LINK_COLOR,
                    (rect.left, rect.bottom), (rect.right, rect.bottom), 1,
                )
                self._link_hitboxes.append((rect.inflate(10, 8), ml))
                y += link_surf.get_height() + 4
        return y

    def _draw_label_value(
        self, surf: pygame.Surface, label: str, value: str,
        x: int, y: int, w: int,
    ) -> int:
        """Compact two-tone line: bold dim label, then wrapped body."""
        prefix = f"{label} \u2014 "
        prefix_surf = self.body_bold_font.render(prefix, True, self.wing.accent)
        surf.blit(prefix_surf, (x, y))
        # Wrap the value alongside the label.
        first_line_width = w - prefix_surf.get_width()
        lines = wrap_text(value, self.body_font, first_line_width)
        if not lines:
            return y + self.body_font.get_height() + 4
        first = self.body_font.render(lines[0], True, COL_INK)
        surf.blit(first, (x + prefix_surf.get_width(), y))
        line_h = self.body_font.get_height() + 4
        cy = y + line_h
        # Continuation lines wrap to the full column width.
        for cont in lines[1:]:
            extra = wrap_text(cont, self.body_font, w)
            for c in extra:
                cs = self.body_font.render(c, True, COL_INK)
                surf.blit(cs, (x, cy))
                cy += line_h
        return cy

    # ------------------------------------------------------------------
    def _render_essay_section(
        self, surf: pygame.Surface, y: int, w: int, sec: EssaySection,
    ) -> int:
        # Heading row with a thin accent bar to its left, museum-style.
        head_surf = self.section_font.render(sec.heading, True, COL_INK)
        bar_h = head_surf.get_height()
        pygame.draw.rect(surf, self.wing.accent, (0, y + 2, 4, bar_h - 4))
        surf.blit(head_surf, (12, y))
        y += bar_h + 8

        for paragraph in sec.body.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            y = self._draw_text_with_citations(
                surf, paragraph, self.body_font, COL_INK,
                0, y, w, line_spacing=5,
            )
            y += 8

        if sec.image:
            img = load_image(sec.image)
            if img is not None:
                # Constrain to a clean inset width and natural aspect.
                max_w = min(w - 40, 720)
                iw, ih = img.get_size()
                target_w = max_w
                target_h = int(ih * target_w / iw)
                max_h = 360
                if target_h > max_h:
                    target_h = max_h
                    target_w = int(iw * target_h / ih)
                scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                ox = (w - target_w) // 2
                # Frame: thin dark border + subtle drop shadow.
                shadow = pygame.Surface((target_w + 8, target_h + 8), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=2)
                surf.blit(shadow, (ox - 2, y + 4))
                pygame.draw.rect(
                    surf, (42, 30, 22),
                    (ox - 3, y - 3, target_w + 6, target_h + 6),
                )
                surf.blit(scaled, (ox, y))
                y += target_h + 6
                if sec.image_caption:
                    cap_surf = self.italic_font.render(sec.image_caption, True, COL_INK_SOFT)
                    surf.blit(cap_surf, ((w - cap_surf.get_width()) // 2, y + 2))
                    y += cap_surf.get_height() + 6
                y += 6
        return y

    # ------------------------------------------------------------------
    def _draw_text_with_citations(
        self, surf: pygame.Surface, text: str, font: pygame.font.Font, color,
        x: int, y: int, max_width: int, line_spacing: int = 4,
    ) -> int:
        """Render wrapped text, interpreting ``[N]`` markers as inline
        clickable footnote links to ``self.exhibit.citations``. Other
        markers (without a matching citation) are rendered as the literal
        \"[N]\" in the body color so the analysis still reads correctly.
        """
        cite_font = get_font("body_bold", max(11, font.get_height() - 6))
        space_w = font.size(" ")[0]
        line_h = font.get_height() + line_spacing

        # Tokenize: split on whitespace but keep [N] tokens intact.
        words = text.split()

        # Greedy wrap with mixed tokens.
        cursor_x = x
        cursor_y = y

        def newline():
            nonlocal cursor_x, cursor_y
            cursor_x = x
            cursor_y += line_h

        for word in words:
            # A "word" may contain a citation marker glued to surrounding
            # punctuation, e.g. 'Summer."[1]' — split it into its parts so
            # the marker is rendered as a styled footnote.
            parts = self._split_citation_tokens(word)
            # Render the parts as a single visual token (no internal space).
            token_w = self._measure_parts(parts, font, cite_font)
            # Space if not the first token on the line.
            if cursor_x > x:
                if cursor_x + space_w + token_w > x + max_width:
                    newline()
                else:
                    cursor_x += space_w
            else:
                if cursor_x + token_w > x + max_width and token_w <= max_width:
                    newline()
            # Draw parts.
            for part in parts:
                cursor_x = self._draw_part(surf, part, font, cite_font, color, cursor_x, cursor_y)

        return cursor_y + line_h

    def _split_citation_tokens(self, word: str) -> List[Tuple[str, object]]:
        """Split a whitespace-delimited word into a list of typed pieces:
        ('text', str) or ('cite', int). Punctuation glued around a marker
        stays in its own 'text' piece."""
        out: List[Tuple[str, object]] = []
        i = 0
        for m in CITATION_RE.finditer(word):
            if m.start() > i:
                out.append(("text", word[i:m.start()]))
            out.append(("cite", int(m.group(1))))
            i = m.end()
        if i < len(word):
            out.append(("text", word[i:]))
        return out

    def _measure_parts(
        self, parts: List[Tuple[str, object]],
        font: pygame.font.Font, cite_font: pygame.font.Font,
    ) -> int:
        total = 0
        for kind, value in parts:
            if kind == "text":
                total += font.size(value)[0]
            else:
                total += cite_font.size(f"[{value}]")[0]
        return total

    def _draw_part(
        self, surf: pygame.Surface,
        part: Tuple[str, object],
        font: pygame.font.Font, cite_font: pygame.font.Font,
        color, x: int, y: int,
    ) -> int:
        kind, value = part
        if kind == "text":
            s = font.render(value, True, color)
            surf.blit(s, (x, y))
            return x + s.get_width()
        # Citation marker: styled as a superscript link; clicking scrolls to
        # the matching footnote row in the NOTES section (does not open URL).
        num = value  # type: ignore[assignment]
        text = f"[{num}]"
        is_known = num in self._citations_by_num
        marker_color = self.wing.accent if is_known else color
        s = cite_font.render(text, True, marker_color)
        # Slight superscript baseline shift.
        surf.blit(s, (x, y - 2))
        if is_known:
            rect = pygame.Rect(x, y - 2, s.get_width(), s.get_height())
            self._inline_cite_hitboxes.append((rect, num))
        return x + s.get_width()

    # ------------------------------------------------------------------
    def _render_citation(
        self, surf: pygame.Surface, y: int, w: int, c: Citation,
    ) -> int:
        # Record the top of this citation row so inline [N] markers can
        # scroll directly to it.
        self._citation_y[c.number] = y

        # "  N.  Label  —  url"  (label in ink; url in link color, clickable)
        num = self.body_bold_font.render(f"{c.number}.", True, self.wing.accent)
        num_rect = num.get_rect(topleft=(0, y))
        surf.blit(num, num_rect.topleft)
        body_x = num_rect.right + 8

        label = c.label or c.url
        label_lines = wrap_text(label, self.body_font, w - body_x)
        cy = y
        for line in label_lines:
            ls = self.body_font.render(line, True, COL_INK)
            surf.blit(ls, (body_x, cy))
            cy += ls.get_height() + 2

        # URL line, clickable, link-styled.
        url_lines = wrap_text(c.url, self.small_font, w - body_x)
        for line in url_lines:
            us = self.small_font.render(line, True, LINK_COLOR)
            rect = pygame.Rect(body_x, cy, us.get_width(), us.get_height())
            surf.blit(us, rect.topleft)
            pygame.draw.line(surf, LINK_COLOR, (rect.left, rect.bottom), (rect.right, rect.bottom), 1)
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
            surface,
            self.panel_rect,
            bg=COL_PAPER,
            border=self.wing.accent,
            border_width=4,
            shadow=True,
            radius=10,
        )

        # Top bar: tag and close hint.
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
            "Esc / B to close     1\u20139 to open links     [N] jumps to footnote     wheel or arrows to scroll",
            True, COL_MUTED,
        )
        surface.blit(close_hint, close_hint.get_rect(topright=(top_bar.right, top_bar.top + 8)))

        pygame.draw.line(
            surface, COL_GOLD_DIM,
            (self.panel_rect.left + 24, self.panel_rect.top + 82),
            (self.panel_rect.right - 24, self.panel_rect.top + 82), 1,
        )

        # Clip + blit scrolled content.
        if self._content_surf is not None:
            prev = surface.get_clip()
            surface.set_clip(self.content_rect)
            surface.blit(
                self._content_surf,
                (self.content_rect.left, self.content_rect.top - self.scroll),
            )
            surface.set_clip(prev)

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
