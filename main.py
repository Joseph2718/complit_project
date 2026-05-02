"""The Museum of Reperformance — entry point.

Run from the project root:

    python main.py

The main loop delegates all state to a ``SceneManager``. ``Game`` is the
thin façade the scenes call back into (``start_game``, ``enter_wing``,
``open_exhibit``, ``return_to_lobby``, ``close_exhibit``, ...).
"""

from __future__ import annotations

import sys

import pygame

from game import audio
from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.content import Exhibit, Wing
from game.scene import SceneManager
from game.scenes.exhibit import ExhibitScene
from game.scenes.lobby import LobbyScene
from game.scenes.start import StartScene
from game.scenes.wing import WingScene


class Game:
    def __init__(self) -> None:
        pygame.init()
        if not audio.init():
            print("[museum] audio unavailable — continuing silently", file=sys.stderr)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.scenes = SceneManager()
        self.running = True

        # Player-controlled UI preferences that should persist across
        # scene transitions (so closing the welcome card before stepping
        # into a wing keeps it closed when the player returns).
        self.placard_visible = True

        self.scenes.replace(StartScene(self))

    # ------------------------------------------------------------------
    # Navigation API used by scenes
    # ------------------------------------------------------------------
    def start_game(self) -> None:
        self.scenes.replace(LobbyScene(self))

    def enter_wing(self, wing_key: str) -> None:
        self.scenes.replace(WingScene(self, wing_key))

    def return_to_lobby(self) -> None:
        self.scenes.replace(LobbyScene(self))

    def open_exhibit(self, exhibit: Exhibit, wing: Wing) -> None:
        self.scenes.push(ExhibitScene(self, exhibit, wing))

    def close_exhibit(self) -> None:
        self.scenes.pop()

    def confirm_quit_to_title(self) -> None:
        # From the lobby, Esc goes back to title. From wings, Esc goes to lobby.
        self.scenes.replace(StartScene(self))

    # ------------------------------------------------------------------
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.scenes.handle_event(event)

            if not self.running:
                break
            self.scenes.update(dt)
            self.scenes.draw(self.screen)
            pygame.display.flip()

        audio.shutdown()
        pygame.quit()


def main() -> int:
    Game().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
