# The Museum of Reperformance

An interactive top-down museum built in `pygame`. The lobby opens onto three doorways — two curated wings of song-pair exhibits and a Reading Room that grounds those exhibits in the museum's own thesis, working vocabulary, and guiding questions.

- **Wing I — Same Lyrics, Opposite Register.** Five exhibits on covers that invert the emotional temperature of the original.
- **Reading Room — Foundational Texts.** Three short readings (Curatorial Thesis, Working Vocabulary, Guiding Questions) drawn from Goffman, Schechner & Turner, and Coyle.
- **Wing II — Songs Reclaimed.** Three exhibits on songs taken back or bent away from their author's intent.

Walk the lobby, enter a wing, approach any exhibit, and press **E** to open a full catalog panel with long-form analysis, embedded images, numbered footnotes, and a 30-second audio preview of every performance.

---

## Requirements

- **Python 3.10 or later** ([download here](https://www.python.org/downloads/))
- The **pygame** library (installed in the next step)

> **macOS / Apple Silicon:** use an arm64 Python (Homebrew or python.org). A Rosetta-built Python will fail to load the pygame SDL library.

---

## Setup

Open a terminal (Terminal on macOS, PowerShell or Command Prompt on Windows) and run:

### 1. Get the project

If you have git installed:

```bash
git clone https://github.com/Joseph2718/complit_project.git
cd complit_project
```

Otherwise, download the project as a zip, extract it, and `cd` into the extracted folder.

### 2. Create a virtual environment (recommended, but optional)

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows (PowerShell or CMD)
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

That's it.

---

## Run the game

```bash
python main.py
```

A window opens on the title screen. Press any key to enter the museum.

---

## How to play

1. You spawn in the **Lobby**. A welcome card greets you; press **H** to dismiss or bring it back, or click the **X** on the card.
2. Walk with **W A S D** (or the arrow keys). You can walk through any open doorway.
3. The **middle doorway (Reading Room)** is the recommended first stop — the secretary at the desk lays out the museum's thesis, its working vocabulary, and a set of guiding questions. Inside, walk up to a lectern and press **E** to open the reading. From the Guiding Questions reading, press **Take these with me (P)** to drop a small scroll icon in the corner of every other room — press **G** any time to expand or hide it.
4. Step into **Wing I** (left) or **Wing II** (right). Approach any framed exhibit until it glows; press **E** to open its catalog panel.
5. In an exhibit panel:
  - Click **▶ Preview** on any performance to play a 30-second clip; ambient music ducks beneath it. Click again (now **■ Stop**) to stop.
  - Click any superscript number in the body text to jump straight to that footnote.
  - Click any underlined link or use **1** – **9** to open it in your browser.
  - Scroll with the mouse wheel, **↑** **↓**, **Page Up/Down**, or **Home** / **End**.
  - Press **Esc**, **B**, or click the **X** to close.
6. Back to the lobby with **Esc** or **B**. From the lobby, **Esc** returns to the title screen.

### Controls reference


| Action                                      | Keys                                                           |
| ------------------------------------------- | -------------------------------------------------------------- |
| Move                                        | **W A S D** or arrow keys                                      |
| Enter wing / Reading Room / inspect exhibit | **E** or **Space**                                             |
| Toggle welcome card (lobby)                 | **H**                                                          |
| Open / close pinned Guiding Questions       | **G** (after pinning them in the Reading Room)                 |
| Pin Guiding Questions to scroll             | **P** (inside the Guiding Questions reading)                   |
| Play / stop song preview                    | click the **▶ Preview** / **■ Stop** pill                      |
| Open media link                             | click the underlined link, or press **1** – **9**              |
| Jump to footnote                            | click any superscript citation number                          |
| Scroll a panel                              | mouse wheel, **↑** **↓**, **Page Up/Down**, **Home** / **End** |
| Close exhibit / reading panel               | **Esc**, **B**, or the **X** button                            |
| Back to lobby                               | **Esc** or **B**                                               |
| Quit to title (from lobby)                  | **Esc**                                                        |


---

## Project layout

```
main.py                          entry point: game loop + scene wiring
requirements.txt
game/
├── constants.py                 palette, screen dimensions
├── assets.py                    cached font + image loading
├── audio.py                     music, SFX, song-preview playback
├── scene.py                     SceneManager stack
├── ui.py                        text wrapping + panel helpers
├── player.py                    4-directional player sprite
├── npc.py                       wandering NPC AI
├── npc_sprite.py                multi-character sprite-sheet rendering
├── content.py                   museum data (wings, exhibits, readings)
├── previews.py                  song-preview lookup (Deezer + local files)
└── scenes/
    ├── start.py                 title screen
    ├── lobby.py                 lobby with three doorways
    ├── wing.py                  generic wing room
    ├── exhibit.py               exhibit catalog panel
    ├── reading_room.py          Reading Room with three lecterns
    ├── reading_panel.py         overlay for the readings
    └── guiding_overlay.py       persistent corner-scroll overlay
fonts/                           Cormorant Garamond (regular + italic)
music/                           ambient + SFX + 30 s cover clips
assets/art/                      backdrops, exhibit images, sprites, textures
assets/previews.json             Deezer track-id catalog
```

---

## Design notes

**Movement.** Top-down 4-directional with axis-separated AABB collision, tuned per room to match the painted backdrops.

**Audio.** A single ambient track at a time (with crossfading), separate SFX channels, and a dedicated preview channel that ducks ambient music while a clip plays. Previews are hard-capped at 30 seconds.

**Typography.** All text uses *Cormorant Garamond* (variable weight + italic). Body copy wraps dynamically against panel widths.

**Exhibit panels.** Composed once into an off-screen surface and scrolled. Each panel has a header (cover art + title), original and reperformance summary blocks, long-form essay sections with embedded images, and a Notes section with numbered footnotes. Inline superscript citations are clickable and scroll to the matching footnote.

**Content model.** `game/content.py` defines `Wing`, `Exhibit`, `Performance`, `MediaLink`, `EssaySection`, `Citation`, and `ReadingEntry` dataclasses. Adding a new exhibit is purely data — no scene changes needed.

**Ambient NPCs.** Each room is populated with museum-goers (LPC charsets plus Mario in the lobby) that wander, pause, and turn via a small idle/walking state machine in `game/npc.py`.

**Song previews.** Each cataloged performance shows a **▶ Preview** button. Most clips come from the Deezer API: we pin a stable track id in `assets/previews.json`, resolve a fresh signed URL at click-time, download the MP3 on a worker thread, and play it through a dedicated channel. Three BBC Live Lounge / Piano Room covers (Demi Lovato's "Take Me to Church", Lil Nas X's "Jolene", Rick Astley's "drivers license") aren't on Deezer, so they ship as 30-second local MP3 clips in `music/`. Two reperformances *are* the same audio file as the original (TikTok use of "Paris", "True Colors" reclaimed as an LGBTQ+ anthem) — there the preview plays the original recording and the panel prints a small italic note so it's never misleading.

**Reading Room.** Three lecterns — Curatorial Thesis, Working Vocabulary, Guiding Questions. Each opens a Chicago-style overlay. Pinning the Guiding Questions drops a small folded-paper icon in the corner that you can re-open from any room with **G**.

---

## Asset credits

- **Player sprite** — original RTP-style charset.
- **Ambient NPC sprites** — reformatted from the [Universal LPC Spritesheet Character Generator](https://github.com/gaurav0/Universal-LPC-Spritesheet-Character-Generator) by Redshrike, distributed by `ovate` on the RPG Maker forums under **CC-BY 3.0**.
- **Mario sprite** — extracted from the Super Mario World *Overworld Sprites* rip on [The Spriters Resource](https://www.spriters-resource.com/snes/smarioworld/sheet/173882/). Mario and related marks © Nintendo. Used here as a non-commercial cameo for an academic project.
- **Music & SFX** — `gallery_ambient.ogg` is a public-domain ambient loop; short SFX were synthesized in-tree. The three BBC cover clips in `music/` are 30-second excerpts used for academic identification only.
- **Exhibit images** — extracted from the analyzed performances and public album thumbnails, included for academic identification purposes only.

---

## Content

**Wing I — Same Lyrics, Opposite Register**

1. *Dancing on My Own* — Robyn (2010) / Calum Scott (2016)
2. *Do I Wanna Know?* — Arctic Monkeys (2013) / Hozier (2016)
3. *Wake Me Up* — Aloe Blacc & Mike Einziger (2013) / Avicii (2013)
4. *Take Me to Church* — Hozier (2014) / Demi Lovato (2015)
5. *Jolene* — Dolly Parton (1973) / Lil Nas X (2021)

**Wing II — Songs Reclaimed**

1. *Paris* — The Chainsmokers (2017) / TikTok in the wake of *Dobbs v. Jackson* (2022)
2. *True Colors* — Cyndi Lauper (1986) / AIDS Crisis & LGBTQ+ Anthem (2008–present)
3. *drivers license* — Olivia Rodrigo (2021) / Rick Astley (2024)

**Reading Room — Foundational Texts**

- **Curatorial Thesis** — what the museum is and how to read it.
- **Working Vocabulary** — Goffman's *frame*, Schechner & Turner's *strip of behavior*, Coyle's *antic of authenticity*.
- **Guiding Questions** — four questions to take with you through the museum.

