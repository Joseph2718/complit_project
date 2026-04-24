"""Global constants: screen dims, palette, and scene identifiers."""

from __future__ import annotations

TITLE = "The Museum of Reperformance"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Unified palette — museum-curated.
# Walls: warm bone. Floor: oak.
# Wing accents: teal (Wing I), ochre (Wing II), burgundy (Wing III).
# Gold for highlights and selected frames.
COL_BG = (28, 24, 22)
COL_WALL = (236, 227, 212)
COL_WALL_SHADOW = (208, 196, 178)
COL_FLOOR = (156, 130, 102)
COL_FLOOR_DARK = (132, 108, 84)
COL_INK = (26, 22, 20)
COL_INK_SOFT = (72, 62, 56)
COL_PAPER = (248, 242, 228)
COL_GOLD = (198, 162, 92)
COL_GOLD_DIM = (148, 118, 62)
COL_MUTED = (160, 146, 128)
COL_ACCENT_DEFAULT = (180, 160, 120)

# Wing accent colors — each wing dresses its room with one.
COL_WING_I = (46, 96, 112)          # deep teal — oppositional register
COL_WING_II = (176, 92, 48)         # burnt ochre — reclaimed
COL_WING_III = (128, 48, 70)        # dim burgundy — viral

# Scene IDs
SCENE_START = "start"
SCENE_LOBBY = "lobby"
SCENE_WING = "wing"
SCENE_CREDITS = "credits"

# Movement
PLAYER_SPEED = 240  # pixels per second
INTERACT_RADIUS = 84

# UI
UI_MARGIN = 24
