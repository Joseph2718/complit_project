# The Museum of Reperformance

An interactive top-down museum built in `pygame`. Two curated wings explore what happens when the same lyrics are sung again — by someone else, in a different year, for a different room.

- **Wing I — Same Lyrics, Opposite Register.** Covers that invert the emotional temperature of the original.
- **Wing II — Songs Reclaimed.** Works taken back or bent away from their author's intent.

Walk the lobby, enter a wing, approach any exhibit, and press **E** to open a full catalogue panel with long-form analysis, embedded images, numbered footnotes, and links to the original recordings.

---

## Requirements

- Python **3.10+**
- `pygame` 2.6 or later

All dependencies are listed in `requirements.txt`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **macOS / Apple Silicon:** use an arm64 Python (Homebrew or python.org). A Rosetta-built Python will produce an architecture mismatch error when loading the pygame SDL library.

## Run

```bash
python main.py
```

---

## Controls

| Action | Keys |
| --- | --- |
| Move | `W` `A` `S` `D` or arrow keys |
| Enter wing / inspect exhibit | `E` or `Space` |
| Toggle welcome card (lobby) | `H` |
| Dismiss welcome card | `X` button on the card |
| Jump to footnote (in exhibit) | click any `[N]` inline marker |
| Open media link in browser | click underlined link, or press `1`–`9` |
| Scroll exhibit panel | mouse wheel, `↑` `↓`, `Page Up/Down`, `Home`/`End` |
| Close exhibit / back to lobby | `Esc` or `B` |
| Quit to title | `Esc` from lobby |

---

## Project layout

```
main.py                      # entry point, game loop, scene manager wiring
requirements.txt

game/
├── constants.py             # palette, screen dimensions, shared IDs
├── assets.py                # centralised font + image loading (cached)
├── audio.py                 # single-track music, dedicated SFX channels
├── scene.py                 # SceneManager stack (push / pop / replace)
├── ui.py                    # wrap_text, draw_panel, Prompt, size_placard
├── player.py                # 4-directional sprite-sheet player
├── content.py               # museum data: Wings, Exhibits, Essays, Citations
└── scenes/
    ├── start.py             # animated title screen
    ├── lobby.py             # navigable lobby with two wing doorways
    ├── wing.py              # generic wing room (exhibit mounts, approach zones)
    └── exhibit.py           # scrollable catalogue panel overlay

fonts/
    CormorantGaramond-VF.ttf      # variable-weight serif (display, heading, body)
    CormorantGaramond-Italic.ttf  # italic variant

music/
    gallery_ambient.ogg      # looping ambient track for lobby + wings
    title_ambient.mp3        # title screen ambient
    ui_click.wav             # button / door click SFX
    exhibit_open.wav         # exhibit open SFX
    footstep.wav             # footstep SFX

assets/art/
    title.png                # hero image on the title screen
    backdrops/               # top-down pixel-art room backgrounds
        lobby.png
        wing_same_lyrics.png
        wing_reclaimed.png
    exhibits/                # exhibit cover images (one per art_key)
    exhibits/frames/         # still frames extracted from the analysis PDF
    sprites/                 # player sprite sheet
    textures/                # parquet / wall tile textures (procedural fallback)
```

---

## Design notes

**Movement.** Top-down 4-directional with axis-separated AABB collision. Collision borders are tuned per room to match the painted backdrops: conservative so exploration feels open, tight enough that the player never phases through a visible wall.

**Audio.** A dedicated `game/audio.py` module enforces a single music track at a time (with crossfading), separate SFX channels for clicks, exhibit-open, and footsteps, and guards against stacked sounds on repeated scene entry.

**Typography.** All text uses *Cormorant Garamond* (variable weight + italic). A `render_tracked` helper adds letter-spacing for the museum-catalogue headings. All body copy wraps dynamically against the actual panel width.

**Exhibit panels.** Content is composed once into an off-screen surface at scene creation, then scrolled. Each panel contains: wing tag, cover art, performer/year header, original + reperformance summary blocks, long-form essay sections (with embedded images), and a NOTES section with numbered footnotes. Clicking an inline `[N]` marker scrolls to the matching footnote row. Clicking an underlined URL in the NOTES section opens it in the default browser.

**Content model.** `game/content.py` defines `Wing`, `Exhibit`, `Performance`, `MediaLink`, `EssaySection`, and `Citation` dataclasses. Adding a new exhibit is purely data — no scene code changes required.

---

## Content

TBD: update when all song analyses are complete.
