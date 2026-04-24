"""Scene base class and manager.

Scenes are independent chunks of game (start screen, lobby, wing, etc.).
The manager owns a stack so overlays (exhibit panel) can push on top of a
room and pop cleanly to return — matching the museum flow of "enter a
gallery, stop at a piece, step back to the room."
"""

from __future__ import annotations

from typing import List, Optional

import pygame


class Scene:
    """Override any of handle_event / update / draw. Default is a no-op."""

    def __init__(self, game: "Game") -> None:
        self.game = game

    def on_enter(self, **kwargs) -> None:  # called when pushed or replaced to
        pass

    def on_exit(self) -> None:  # called when replaced/popped
        pass

    def on_resume(self) -> None:  # called when an overlay above us pops
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class SceneManager:
    def __init__(self) -> None:
        self._stack: List[Scene] = []

    @property
    def current(self) -> Optional[Scene]:
        return self._stack[-1] if self._stack else None

    @property
    def scene_below(self) -> Optional[Scene]:
        """The scene immediately under the top — useful for overlays that
        want to draw the gallery behind themselves."""
        return self._stack[-2] if len(self._stack) >= 2 else None

    def replace(self, scene: Scene, **kwargs) -> None:
        while self._stack:
            self._stack.pop().on_exit()
        self._stack.append(scene)
        scene.on_enter(**kwargs)

    def push(self, scene: Scene, **kwargs) -> None:
        self._stack.append(scene)
        scene.on_enter(**kwargs)

    def pop(self) -> None:
        if not self._stack:
            return
        self._stack.pop().on_exit()
        if self._stack:
            self._stack[-1].on_resume()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        # Overlays (exhibit panel) draw the room below themselves through
        # their own draw — but if a scene doesn't implement that, it's fine.
        if self.current:
            self.current.draw(surface)
