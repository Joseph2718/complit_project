"""Entry point. Run with ``python main.py`` from the project root."""

from __future__ import annotations

import sys

import pygame

from game import audio
from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.content import Exhibit, Wing, reading_entry_by_key
from game.scene import SceneManager
from game.scenes.exhibit import ExhibitScene
from game.scenes.guiding_overlay import GuidingScrollOverlay
from game.scenes.lobby import LobbyScene
from game.scenes.reading_panel import ReadingPanelScene
from game.scenes.reading_room import ReadingRoomScene
from game.scenes.start import StartScene
from game.scenes.wing import WingScene


class Game:
    def __init__(self) -> None:
        pygame.init()
        if not audio.init():
            print("[museum] audio unavailable — continuing silently", file=sys.stderr)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        # Suppress the macOS IMK console warning by disabling text input.
        pygame.key.stop_text_input()
        self.clock = pygame.time.Clock()
        self.scenes = SceneManager()
        self.running = True

        # State that persists across scene transitions.
        self.placard_visible = True
        self.guiding_unlocked = False
        self.guiding_pinned = False
        self.guiding_overlay = GuidingScrollOverlay(self)
        # Last wing/reading-room visited; used to spawn the player near
        # that doorway when they return to the lobby.
        self.last_room_key: str | None = None

        self.scenes.replace(StartScene(self))

    # Navigation API used by scenes -----------------------------------
    def start_game(self) -> None:
        self.scenes.replace(LobbyScene(self))

    def enter_wing(self, wing_key: str) -> None:
        self.last_room_key = wing_key
        self.scenes.replace(WingScene(self, wing_key))

    def enter_reading_room(self) -> None:
        self.last_room_key = "reading_room"
        self.scenes.replace(ReadingRoomScene(self))

    def open_reading_entry(self, entry_key: str) -> None:
        self.scenes.push(ReadingPanelScene(self, reading_entry_by_key(entry_key)))

    def return_to_lobby(self) -> None:
        self.scenes.replace(LobbyScene(self))

    def open_exhibit(self, exhibit: Exhibit, wing: Wing) -> None:
        self.scenes.push(ExhibitScene(self, exhibit, wing))

    def close_exhibit(self) -> None:
        audio.stop_preview()
        self.scenes.pop()

    def confirm_quit_to_title(self) -> None:
        self.scenes.replace(StartScene(self))

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                # The pinned guiding-questions scroll gets events first.
                if self.guiding_overlay.handle_event(event):
                    continue
                self.scenes.handle_event(event)

            if not self.running:
                break
            audio.poll()
            self.scenes.update(dt)
            self.scenes.draw(self.screen)
            self.guiding_overlay.draw(self.screen)
            pygame.display.flip()

        audio.shutdown()
        pygame.quit()


def main() -> int:
    Game().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
