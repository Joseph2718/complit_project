# The Museum of Reperformance

An interactive top-down museum you can walk through, built in `pygame`. Three curated wings examine what happens when the same lyrics are sung again, under different hands, in different times, for different audiences.

- **Wing I — Same Lyrics, Opposite Register.** Covers that invert the emotional temperature of the original.
- **Wing II — Songs Reclaimed.** Works taken back or bent away from their author's intent.
- **Wing III — Viral Reperformance.** How the feed — TikTok, streaming, memes — reperforms a song by relocating it.

The game is a navigation-and-inspection museum: walk, approach an exhibit, press **E** to read the wall text, open linked audio/video in your browser, return to the lobby.

## Requirements

- Python **3.10+**
- `pygame` 2.6 or later (installed automatically below)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On macOS, make sure you're using an arm64 Python on Apple Silicon (e.g. the one installed via Homebrew or python.org).

## Run

```bash
python main.py
```

## Controls

| Action | Keys |
| --- | --- |
| Move | `W A S D` or arrow keys |
| Interact / enter doorway | `E` or `Space` |
| Open highlighted media link | `1`…`9` inside an exhibit panel |
| Close exhibit / back to lobby | `Esc` or `B` |
| Quit | `Q` from the title screen, window close button anywhere |

## Project layout

```
main.py                     # entry point, main loop, scene manager plumbing
game/
├── constants.py            # palette, screen dims, scene ids
├── assets.py               # centralized image/font/sound loading
├── scene.py                # Scene base class + SceneManager
├── ui.py                   # wrapped text, panels, buttons, exhibit overlay
├── player.py               # 4-directional top-down player
├── content.py              # museum data: wings + exhibits + media links
└── scenes/
    ├── start.py            # title screen
    ├── lobby.py            # navigable lobby with 3 doorways
    └── wing.py             # generic wing scene (reused for each wing)
fonts/                      # typography
music/                      # ambient + UI sfx
assets/art/                 # optional generated hero art (procedural fallback if missing)
```

## Design notes

- **Movement.** Top-down 4-directional, like an art-museum stroll. Walls and fixtures use axis-aligned rectangle collision.
- **Art.** One palette (cream walls, oak floor, teal/ochre/burgundy wing accents, black text, gold frames). All rooms are drawn procedurally in pygame so mixed-source assets stay cohesive. A generated painting can drop into `assets/art/title.png` to replace the procedural title.
- **Text.** All long copy is wrapped at render time against the actual panel width; exhibit overlays scroll with mouse wheel or arrow keys.
- **Links.** Each exhibit lists numbered media references that open in the user's default browser via `webbrowser.open`.

## Content

Each wing has 2–3 exhibits. Every exhibit pairs an **original performance** with one or more **reperformances**, a short curator's note, and live links to recordings. See `game/content.py` — editing that file is all that's needed to add, remove, or rewrite exhibits.

## Credits

Typography from the project's original `fonts/` folder: *Press Start 2P* (Codeman38), *Harukaze*, *Kashima Demo 2*. Ambient audio reused from the project's `music/` folder, renamed for this theme.
