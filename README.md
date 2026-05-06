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
| Play 30 s song preview | click the `▶ Preview` pill on any performance |
| Stop song preview | click the same pill (now `■ Stop`), or close the panel |
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
├── assets.py                # centralized font + image loading (cached)
├── audio.py                 # single-track music, dedicated SFX channels
├── scene.py                 # SceneManager stack (push / pop / replace)
├── ui.py                    # wrap_text, draw_panel, Prompt, size_placard
├── player.py                # 4-directional sprite-sheet player
├── npc.py                   # ambient NPC class with wandering AI
├── npc_sprite.py            # multi-character sprite-sheet rendering + catalog
├── content.py               # museum data: Wings, Exhibits, Essays, Citations
├── previews.py              # (song, performer) → Deezer track-id lookup
└── scenes/
    ├── start.py             # animated title screen
    ├── lobby.py             # navigable lobby with two wing doorways
    ├── wing.py              # generic wing room (exhibit mounts, approach zones)
    └── exhibit.py           # scrollable catalog panel overlay

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
    sprites/npcs/            # ambient-NPC sprite sheets (LPC + Mario)
    textures/                # parquet / wall tile textures (procedural fallback)
```

---

## Design notes

**Movement.** Top-down 4-directional with axis-separated AABB collision. Collision borders are tuned per room to match the painted backdrops: conservative so exploration feels open, tight enough that the player never phases through a visible wall.

**Audio.** A dedicated `game/audio.py` module enforces a single music track at a time (with crossfading), separate SFX channels for clicks, exhibit-open, and footsteps, and guards against stacked sounds on repeated scene entry.

**Typography.** All text uses *Cormorant Garamond* (variable weight + italic). A `render_tracked` helper adds letter-spacing for the museum-catalog headings. All body copy wraps dynamically against the actual panel width.

**Exhibit panels.** Content is composed once into an off-screen surface at scene creation, then scrolled. Each panel contains: wing tag, cover art, performer/year header, original + reperformance summary blocks, long-form essay sections (with embedded images), and a Notes section with numbered footnotes. Clicking an inline `[N]` marker scrolls to the matching footnote row. Clicking an underlined URL in the Notes section opens it in the default browser.

**Content model.** `game/content.py` defines `Wing`, `Exhibit`, `Performance`, `MediaLink`, `EssaySection`, and `Citation` dataclasses. Adding a new exhibit is purely data — no scene code changes required.

**Ambient NPCs.** Each room is populated with a small cast of museum-goers that walk around, pause to look at things, and turn at random — a state machine in `game/npc.py` switching between `idle` and `walking` with axis-separated collision against the same obstacle list as the player. NPC sprites are loaded by `game/npc_sprite.py`, which understands both single-character sheets and the standard RPG-Maker 12×8 charset layout (8 characters per sheet).

**In-game song previews.** Each performance with a known recording shows a `▶ Preview` button that plays the 30-second clip in-game. We pin the stable Deezer track ID per `(song, performer)` in `assets/previews.json` (regenerable via `tools/fetch_previews.py`); at click-time, `game/audio.py` resolves a fresh signed URL from `https://api.deezer.com/track/{id}`, downloads the MP3 on a worker thread, then plays it on a dedicated channel that ducks the gallery ambient. The button shows `Loading…`, then `■ Stop  0:04 / 0:30` with a subtle progress fill while playing. We chose Deezer over Spotify because Spotify deprecated `preview_url` for new applications in November 2024, and over the iTunes Search API because pygame's SDL_mixer can play Deezer's MP3 previews natively but cannot decode iTunes's AAC/M4A.

---

## Asset credits

**Player sprite** (`assets/art/sprites/npc_scholar.png`) — original RTP-style charset.

**Ambient NPC sprites** (`assets/art/sprites/npcs/lpc_set_*.png`) — three 576×384 charsets reformatted from the [Universal LPC Spritesheet Character Generator](https://github.com/gaurav0/Universal-LPC-Spritesheet-Character-Generator) by Redshrike. Distributed by `ovate` on the RPG Maker forums under **CC-BY 3.0**.

**Mario sprite** (`assets/art/sprites/npcs/mario.png`) — 16×16 small-Mario walk frames extracted from the Super Mario World *Overworld Sprites* rip on [The Spriters Resource](https://www.spriters-resource.com/snes/smarioworld/sheet/173882/) (uploaded by *Barack Obama*, 2022). Used here as a non-commercial cameo for an academic project; Mario and all related marks are © Nintendo.

**Music & SFX** — `gallery_ambient.ogg` is a public-domain ambient loop; the short `*.wav` SFX were synthesised in-tree.

**Exhibit cover images** — single-frame stills excerpted from the analyzed performances and album-cover thumbnails from public catalog pages, included for academic identification purposes only.

---

## Content

TBD: update when all song analyses are complete.
