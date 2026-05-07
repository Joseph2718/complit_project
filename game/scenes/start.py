"""Title screen. No movement — a composed piece of typography.

The background can be a generated image at ``assets/art/title.png`` if
present, otherwise a procedural museum façade (three archways, gold rule)
is drawn so the scene works out of the box.
"""

from __future__ import annotations

import math

import pygame

from .. import audio
from ..assets import get_font, load_image
from ..constants import (
    COL_BG,
    COL_GOLD,
    COL_GOLD_DIM,
    COL_INK,
    COL_INK_SOFT,
    COL_PAPER,
    COL_WALL,
    COL_WALL_SHADOW,
    COL_READING,
    COL_WING_I,
    COL_WING_II,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class StartScene:
    def __init__(self, game) -> None:
        self.game = game
        self.time = 0.0
        # Pre-render title text
        self.title_font = get_font("display", 82)
        self.subtitle_font = get_font("italic", 30)
        self.cta_font = get_font("heading", 22)
        self.footnote_font = get_font("body", 18)
        from ..ui import render_tracked
        self.title_surf = render_tracked(
            self.title_font, "THE MUSEUM OF", COL_PAPER, tracking=6
        )
        self.title_surf2 = render_tracked(
            self.title_font, "REPERFORMANCE", COL_GOLD, tracking=6
        )
        self.subtitle_surf = self.subtitle_font.render(
            "— a song is never a fixed object —", True, COL_PAPER
        )
        self.cta_surf = render_tracked(
            self.cta_font, "PRESS ENTER TO BEGIN", COL_INK, tracking=4
        )

    def on_enter(self, **kwargs) -> None:
        audio.play_music("title_ambient.mp3", volume=0.55)

    def on_exit(self) -> None:
        # Don't fade — the next scene will crossfade into its own track.
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                audio.play_click()
                self.game.start_game()
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.game.running = False

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        hero = load_image("title.png")
        if hero:
            scaled = pygame.transform.smoothscale(hero, (SCREEN_WIDTH, SCREEN_HEIGHT))
            surface.blit(scaled, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
        else:
            self._draw_procedural_backdrop(surface)

        cx = SCREEN_WIDTH // 2

        # Title block: two lines, large display serif, tracked letters.
        title_top = 160
        row1 = self.title_surf.get_rect(center=(cx, title_top))
        row2 = self.title_surf2.get_rect(midtop=(cx, row1.bottom + 6))
        surface.blit(self.title_surf, row1)
        surface.blit(self.title_surf2, row2)

        # Gold rule (museum plinth underline)
        rule_y = row2.bottom + 22
        pygame.draw.line(
            surface, COL_GOLD, (cx - 260, rule_y), (cx + 260, rule_y), 2
        )

        # Subtitle italic
        sub_rect = self.subtitle_surf.get_rect(center=(cx, rule_y + 36))
        surface.blit(self.subtitle_surf, sub_rect)

        # CTA: warm parchment button, gently pulsing gold border
        pulse = 180 + int(50 * (0.5 + 0.5 * math.sin(self.time * 2.5)))
        cta_bg = pygame.Rect(0, 0, 460, 62)
        cta_bg.center = (cx, SCREEN_HEIGHT - 140)
        pygame.draw.rect(surface, COL_PAPER, cta_bg, border_radius=10)
        pygame.draw.rect(surface, (pulse, pulse - 40, 60), cta_bg, 3, border_radius=10)
        surface.blit(self.cta_surf, self.cta_surf.get_rect(center=cta_bg.center))

        # Footnote
        foot = self.footnote_font.render(
            "WASD / Arrows to walk     E to inspect     Esc to step back",
            True,
            COL_PAPER,
        )
        surface.blit(foot, foot.get_rect(center=(cx, SCREEN_HEIGHT - 60)))

    def _draw_procedural_backdrop(self, surface: pygame.Surface) -> None:
        # Deep ground wash
        surface.fill((18, 16, 14))
        # Vertical gradient suggestion: lighter upper, darker lower
        for y in range(0, SCREEN_HEIGHT, 2):
            t = y / SCREEN_HEIGHT
            r = int(18 + (40 - 18) * (1 - t))
            g = int(16 + (34 - 16) * (1 - t))
            b = int(14 + (30 - 14) * (1 - t))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Three illuminated archways
        arch_w = 220
        gap = 60
        total = arch_w * 3 + gap * 2
        base_x = (SCREEN_WIDTH - total) // 2
        base_y = SCREEN_HEIGHT - 220
        for i in range(3):
            x = base_x + i * (arch_w + gap)
            self._draw_arch(surface, x, base_y, arch_w, 180, i)

        # Floor stripe
        pygame.draw.rect(surface, (52, 44, 36), (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        pygame.draw.line(
            surface, COL_GOLD_DIM, (0, SCREEN_HEIGHT - 40), (SCREEN_WIDTH, SCREEN_HEIGHT - 40), 2
        )

    def _draw_arch(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, idx: int) -> None:
        # warm glow behind arch
        glow = pygame.Surface((w + 80, h + 80), pygame.SRCALPHA)
        for r in range(6, 0, -1):
            a = 12 * r
            pygame.draw.rect(
                glow,
                (210, 170, 90, a),
                (40 - r * 6, 40 - r * 6, w + r * 12, h + r * 12),
                border_radius=w // 2,
            )
        surface.blit(glow, (x - 40, y - 40))
        # archway (lit interior)
        arch_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (58, 48, 38), arch_rect, border_radius=w // 2)
        # inner halo — tinted by wing accent
        tints = [COL_WING_I, COL_READING, COL_WING_II]
        inner = pygame.Rect(x + 16, y + 16, w - 32, h - 16)
        pygame.draw.rect(surface, tints[idx], inner, border_radius=(w - 32) // 2)
        shade = pygame.Surface(inner.size, pygame.SRCALPHA)
        for i in range(inner.height):
            a = int(120 * (1 - i / inner.height))
            pygame.draw.line(shade, (0, 0, 0, a), (0, i), (inner.width, i))
        surface.blit(shade, inner.topleft)
        # gold border
        pygame.draw.rect(surface, COL_GOLD, arch_rect, 3, border_radius=w // 2)
