# The Museum of Reperformance

An interactive top-down museum built in `pygame`. The lobby opens onto three doorways — two curated wings that explore what happens when the same lyrics are sung again, and a Reading Room that grounds those exhibits in the museum's own thesis and working vocabulary.

- **Wing I — Same Lyrics, Opposite Register.** Covers that invert the emotional temperature of the original. Five exhibits.
- **Reading Room — Foundational Texts.** Three short readings — the Curatorial Thesis, a Working Vocabulary built on Goffman / Schechner & Turner / Coyle, and a set of Guiding Questions you can pin to a scroll and carry through the museum.
- **Wing II — Songs Reclaimed.** Works taken back or bent away from their author's intent. Three exhibits, including the Chainsmokers' "Paris" reperformed by TikTok in the wake of *Dobbs v. Jackson*.

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
| Enter wing / Reading Room / inspect | `E` or `Space` |
| Toggle welcome card (lobby) | `H` |
| Dismiss welcome card | `X` button on the card |
| Jump to footnote (in exhibit / reading) | click any `[N]` inline marker |
| Play 30 s song preview | click the `▶ Preview` pill on any performance |
| Stop song preview | click the same pill (now `■ Stop`), or close the panel |
| Open media link in browser | click underlined link, or press `1`–`9` |
| Scroll exhibit / reading panel | mouse wheel, `↑` `↓`, `Page Up/Down`, `Home`/`End` |
| Close exhibit / reading panel | `Esc`, `B`, or click the `X` button |
| Pin Guiding Questions to scroll | `P` (inside the Guiding Questions reading) |
| Open / close pinned Guiding Questions | `G` (works from any room once pinned) |
| Back to lobby (from a wing or reading) | `Esc` or `B` |
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
├── content.py               # museum data: Wings, Exhibits, Reading Room, Citations
├── previews.py              # (song, performer) → Deezer track-id lookup
└── scenes/
    ├── start.py             # animated title screen
    ├── lobby.py             # navigable lobby with three doorways (Wing I / Reading Room / Wing II)
    ├── wing.py              # generic wing room (exhibit mounts, approach zones)
    ├── exhibit.py           # scrollable catalog panel overlay
    ├── reading_room.py      # Reading Room scene with three lecterns
    ├── reading_panel.py     # overlay for thesis / vocabulary / guiding questions
    └── guiding_overlay.py   # persistent "scroll" icon for pinned guiding questions

fonts/
    CormorantGaramond-VF.ttf      # variable-weight serif (display, heading, body)
    CormorantGaramond-Italic.ttf  # italic variant

music/
    gallery_ambient.ogg      # looping ambient track for lobby + wings + reading room
    title_ambient.mp3        # title screen ambient
    ui_click.wav             # button / door click SFX
    exhibit_open.wav         # exhibit open SFX
    footstep.wav             # footstep SFX

assets/art/
    title.png                # hero image on the title screen
    backdrops/               # top-down pixel-art room backgrounds
        lobby.png            # the three-doorway lobby
        reading_room.png     # the reading room
        wing_same_lyrics.png
        wing_reclaimed.png
    exhibits/                # exhibit cover images (one per art_key)
    exhibits/frames/         # still frames for the analyses
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

**Substitute previews.** A handful of reperformances are *not* on Deezer (BBC Live Lounge / Piano Room covers — Demi Lovato's "Take Me to Church", Lil Nas X's "Jolene", Rick Astley's "drivers license") or are reperformances *of the same audio file* (TikTok-driven uses of the Chainsmokers' "Paris" after *Dobbs*, Cyndi Lauper's "True Colors" reclaimed as an LGBTQ+ anthem). For those, the preview button still works, but plays the original recording — the panel prints a small italic note above the button so the player is never misled. The actual cover is still one click away via the YouTube link directly above.

**Reading Room.** The middle doorway in the lobby opens onto the Reading Room. Three lecterns — *Curatorial Thesis*, *Working Vocabulary*, *Guiding Questions* — each open a Chicago-style panel with the foundational texts the museum is built on (Goffman 1974, Schechner & Turner 1985, Coyle 2020). Reading the Guiding Questions and pressing **Keep these on hand** drops a small folded-paper icon in the screen corner; pressing **G** from any room thereafter expands the four guiding questions over whatever room you're currently in (with mouse-wheel/arrow-key scrolling), so you can carry them with you as you walk. A secretary stands at the information desk near the south doorway and a couple of visitors browse the rug.

---

## Asset credits

**Player sprite** (`assets/art/sprites/npc_scholar.png`) — original RTP-style charset.

**Ambient NPC sprites** (`assets/art/sprites/npcs/lpc_set_*.png`) — three 576×384 charsets reformatted from the [Universal LPC Spritesheet Character Generator](https://github.com/gaurav0/Universal-LPC-Spritesheet-Character-Generator) by Redshrike. Distributed by `ovate` on the RPG Maker forums under **CC-BY 3.0**.

**Mario sprite** (`assets/art/sprites/npcs/mario.png`) — 16×16 small-Mario walk frames extracted from the Super Mario World *Overworld Sprites* rip on [The Spriters Resource](https://www.spriters-resource.com/snes/smarioworld/sheet/173882/) (uploaded by *Barack Obama*, 2022). Used here as a non-commercial cameo for an academic project; Mario and all related marks are © Nintendo.

**Music & SFX** — `gallery_ambient.ogg` is a public-domain ambient loop; the short `*.wav` SFX were synthesised in-tree.

**Exhibit cover images** — single-frame stills excerpted from the analyzed performances and album-cover thumbnails from public catalog pages, included for academic identification purposes only.

---

## Content

**Wing I — Same Lyrics, Opposite Register**

1. *Dancing on My Own* — Robyn (2010) / Calum Scott (2016)
2. *Do I Wanna Know?* — Arctic Monkeys (2013) / Hozier (2016)
3. *Wake Me Up* — Aloe Blacc & Mike Einziger (2013) / Avicii (2013)
4. *Take Me to Church* — Hozier (2014) / Demi Lovato (2015)
5. *Jolene* — Dolly Parton (1973) / Lil Nas X (2021)

**Wing II — Songs Reclaimed**

1. *Paris* — The Chainsmokers (2017) / TikTok & the overturning of *Roe v. Wade* (2022)
2. *True Colors* — Cyndi Lauper (1986) / AIDS Crisis & LGBTQ+ Anthem (2008–present)
3. *drivers license* — Olivia Rodrigo (2021) / Rick Astley (2024)

**Reading Room — Foundational Texts**

- **Curatorial Thesis** — what the museum is and how to read it.
- **Working Vocabulary** — Goffman's *frame*, Schechner & Turner's *strip of behavior*, Coyle's *antic of authenticity*.
- **Guiding Questions** — four questions to bring with you (pin to a scroll, optional).
