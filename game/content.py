"""Museum content, structured so new exhibits can be plugged in without
touching any scene code. Each wing has a title, subtitle, thesis, accent
color, and a list of exhibits; each exhibit has two or more performances
(an original and one or more reperformances) and a curator's note.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .constants import COL_WING_I, COL_WING_II, COL_WING_III


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
def youtube_search(query: str) -> str:
    """Build a stable YouTube search URL. This is intentionally a search
    link rather than a direct video ID because:
      1. Direct video IDs rot (deletions, takedowns, private switches).
      2. Search results for 'Artist Title Year' reliably surface the
         intended recording on official channels.
    The user clicks once and lands on exactly the version we're discussing.
    """
    q = urllib.parse.quote_plus(query)
    return f"https://www.youtube.com/results?search_query={q}"


@dataclass(frozen=True)
class MediaLink:
    label: str
    url: str
    kind: str = "video"  # 'video' | 'article' | 'audio'


@dataclass(frozen=True)
class Performance:
    """One recorded instance of the song — the original, or a reperformance.
    ``setting`` captures the context (year, venue, audience, register)."""

    performer: str
    year: str
    setting: str
    register: str
    media: Tuple[MediaLink, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Exhibit:
    song: str
    art_key: str  # e.g. 'hurt' — used to look up assets/art/exhibits/<key>.png
    original: Performance
    reperformances: Tuple[Performance, ...]
    curator_note: str


@dataclass(frozen=True)
class Wing:
    key: str
    title: str
    subtitle: str
    thesis: str
    accent: Tuple[int, int, int]
    exhibits: Tuple[Exhibit, ...]


# ---------------------------------------------------------------------------
# Wing I — Same Lyrics, Opposite Emotional Register
# ---------------------------------------------------------------------------
WING_I = Wing(
    key="wing_i",
    title="Wing I",
    subtitle="Same Lyrics, Opposite Register",
    thesis=(
        "The words do not move, but the weather around them does. "
        "In this wing, a single lyric is tracked through performances "
        "whose emotional temperatures run in opposite directions — "
        "from swagger to longing, from rage to penitence, from the "
        "bedroom to the cathedral."
    ),
    accent=COL_WING_I,
    exhibits=(
        Exhibit(
            song="Hurt",
            art_key="hurt",
            original=Performance(
                performer="Nine Inch Nails",
                year="1994",
                setting="Studio, from The Downward Spiral. Industrial rock, late in the album, close to collapse.",
                register="Self-lacerating. Youth inside its own ruin.",
                media=(
                    MediaLink(
                        "Nine Inch Nails — Hurt (1994)",
                        youtube_search("Nine Inch Nails Hurt 1994 official"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Johnny Cash",
                    year="2002",
                    setting="American IV: The Man Comes Around. Filmed at his Tennessee home months before his death.",
                    register="Valedictory. A life looking back at itself at the end.",
                    media=(
                        MediaLink(
                            "Johnny Cash — Hurt (2002)",
                            youtube_search("Johnny Cash Hurt 2002 official music video"),
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Trent Reznor wrote Hurt from inside addiction at twenty-eight; "
                "Cash sang it at seventy, months before his death. "
                "The same line — 'What have I become?' — lands differently when "
                "the person asking has a past long enough to answer. "
                "Reznor later said, watching the Cash video, the song 'isn't mine anymore.'"
            ),
        ),
        Exhibit(
            song="Hallelujah",
            art_key="hallelujah",
            original=Performance(
                performer="Leonard Cohen",
                year="1984",
                setting="Various Positions, a studio album Columbia records initially declined to release in the United States.",
                register="Sacred and profane held together. Ironic, adult, bruised.",
                media=(
                    MediaLink(
                        "Leonard Cohen — Hallelujah (1984)",
                        youtube_search("Leonard Cohen Hallelujah 1984 official"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Jeff Buckley",
                    year="1994",
                    setting="Grace. Recorded after John Cale's 1991 arrangement stripped Cohen's verses down.",
                    register="Tender, erotic, almost whispered — romance as devotion.",
                    media=(
                        MediaLink(
                            "Jeff Buckley — Hallelujah (1994)",
                            youtube_search("Jeff Buckley Hallelujah official 1994"),
                        ),
                    ),
                ),
                Performance(
                    performer="Pop choirs & film soundtracks",
                    year="2001 onward",
                    setting="Shrek, talent shows, benefit concerts, funerals.",
                    register="Inspirational. Sanded smooth into a hymn of uplift.",
                    media=(
                        MediaLink(
                            "Rufus Wainwright — Hallelujah (Shrek OST, 2001)",
                            youtube_search("Rufus Wainwright Hallelujah Shrek"),
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Cohen wrote some eighty verses over seven years and called the song "
                "'a desire to affirm my faith in life, not in some formal religious way.' "
                "Buckley narrowed the verses to four and romanticized it; pop covers "
                "reduced it further to a secular hymn of uplift. "
                "The word 'Hallelujah' stays constant. What it refers to does not."
            ),
        ),
        Exhibit(
            song="Do I Wanna Know?",
            art_key="do_i_wanna_know",
            original=Performance(
                performer="Arctic Monkeys",
                year="2013",
                setting="AM. Stadium-era rock, Sheffield swagger, slow burn.",
                register="Leering, swaggering, masculine-coded yearning.",
                media=(
                    MediaLink(
                        "Arctic Monkeys — Do I Wanna Know? (2013)",
                        youtube_search("Arctic Monkeys Do I Wanna Know official"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Hozier",
                    year="2014",
                    setting="BBC Radio 1 Live Lounge. Solo with acoustic guitar.",
                    register="Hoarse, hymn-like. A private ache instead of a strut.",
                    media=(
                        MediaLink(
                            "Hozier — Do I Wanna Know? (BBC Live Lounge)",
                            youtube_search("Hozier Do I Wanna Know Live Lounge"),
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The original frames desire as a question asked across a bar. "
                "Hozier relocates it to a pew: the same line, 'I dreamt about "
                "you nearly every night this week,' becomes confession rather "
                "than come-on. The lyric never claims a gender; performance decides."
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Wing II — Songs Reclaimed, Repurposed, or Taken Back
# Per the Museum of Reperformance proposal, this wing explicitly collects
# songs sung by (or circulated through) audiences the writer did not intend,
# including viral / TikTok reperformance.
# ---------------------------------------------------------------------------
WING_II = Wing(
    key="wing_ii",
    title="Wing II",
    subtitle="Songs Reclaimed",
    thesis=(
        "A song leaves its author. Sometimes an audience takes it and "
        "turns it toward a purpose the writer never sat down to serve. "
        "Sometimes the taking is radical; sometimes it sands the song "
        "smooth. The feed counts too: on TikTok, a song is a caption, "
        "and a millionth listener arrives without the first context. "
        "This wing collects songs whose second life runs against — or "
        "beyond — the grain of the first."
    ),
    accent=COL_WING_II,
    exhibits=(
        Exhibit(
            song="I Will Survive",
            art_key="i_will_survive",
            original=Performance(
                performer="Gloria Gaynor",
                year="1978",
                setting="Recorded in a back brace, months after a fall on stage that left her with a broken spine.",
                register="Personal recovery anthem. A private declaration.",
                media=(
                    MediaLink(
                        "Gloria Gaynor — I Will Survive (1978)",
                        youtube_search("Gloria Gaynor I Will Survive 1978 official"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="LGBTQ+ communities during the AIDS crisis",
                    year="1980s–1990s",
                    setting="Clubs, Pride parades, vigils, funerals.",
                    register="Collective survival. A vow sung in chorus.",
                    media=(
                        MediaLink(
                            "Gaynor on the song's reclaiming (NPR)",
                            youtube_search("Gloria Gaynor I Will Survive LGBTQ AIDS anthem interview"),
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Written for a woman picking herself up after a breakup, sung back "
                "by a community picking itself up after mass death. Gaynor has "
                "spoken about the reclaiming with gratitude: the song grew in a "
                "direction she did not plan, and she considers that growth part of the work."
            ),
        ),
        Exhibit(
            song="Born in the U.S.A.",
            art_key="born_in_the_usa",
            original=Performance(
                performer="Bruce Springsteen",
                year="1984",
                setting="An E Street Band arena anthem with a stadium-shaped hook.",
                register="A bitter lament about a Vietnam veteran abandoned at home.",
                media=(
                    MediaLink(
                        "Bruce Springsteen — Born in the U.S.A. (1984)",
                        youtube_search("Bruce Springsteen Born in the USA official 1984"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="U.S. political rallies & ad campaigns",
                    year="1984 onward",
                    setting="Campaign stops, fireworks, stadium jumbotrons — the chorus heard without the verses.",
                    register="Unalloyed patriotism.",
                    media=(
                        MediaLink(
                            "The song's political misuse (overview)",
                            youtube_search("Born in the USA misinterpreted patriotic song explained"),
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The verses describe a man sent 'off to a foreign land / to go and "
                "kill the yellow man,' and the empty homecoming that follows. The "
                "chorus is four words. Reperformance at a rally keeps only the "
                "chorus and flips the song into its opposite — a textbook case of "
                "context overwriting text."
            ),
        ),
        Exhibit(
            song="Dreams",
            art_key="dreams",
            original=Performance(
                performer="Fleetwood Mac",
                year="1977",
                setting="Rumours. Stevie Nicks writes it in a studio lounge during the band's internal collapse.",
                register="A bruised, knowing ballad about leaving.",
                media=(
                    MediaLink(
                        "Fleetwood Mac — Dreams (1977)",
                        youtube_search("Fleetwood Mac Dreams official 1977"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Nathan Apodaca ('Doggface208')",
                    year="2020",
                    setting="TikTok. A man longboards to work sipping Ocean Spray. The clip hits hundreds of millions of views.",
                    register="Blissful. Pandemic-era serenity, no heartbreak in sight.",
                    media=(
                        MediaLink(
                            "Doggface's original TikTok (Sep 2020)",
                            youtube_search("Doggface208 Dreams Ocean Spray TikTok original"),
                        ),
                        MediaLink(
                            "The song re-charts 43 years later (coverage)",
                            youtube_search("Fleetwood Mac Dreams charts TikTok 2020"),
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The song charted again, four decades later, because of a skateboard "
                "and a juice bottle. The 1977 recording is unchanged; what changed is "
                "the reader looking at it. For many new listeners, Dreams is a vibe "
                "first and a breakup song second — if ever. A song written about the "
                "end of a marriage reperformed as the feeling of everything being fine."
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Wing III — Viral Reperformance (reserved, disabled).
# Wing III ("Viral Reperformance") extends the argument into the algorithmic
# era: a song that didn't change at all, but whose surrounding context did.
# ---------------------------------------------------------------------------
WING_III = Wing(
    key="wing_iii",
    title="Wing III",
    subtitle="Viral Reperformance",
    thesis=(
        "On TikTok, a song is a caption. On streaming, a catalog cut can "
        "be revived by a single scene. Here a recording does not change, "
        "but its neighbors do."
    ),
    accent=COL_WING_III,
    exhibits=(
        Exhibit(
            song="Running Up That Hill",
            art_key="running_up_that_hill",
            original=Performance(
                performer="Kate Bush",
                year="1985",
                setting="Hounds of Love. A synth-driven prayer for empathy between partners.",
                register="Fervent, art-pop, mystical.",
                media=(
                    MediaLink(
                        "Kate Bush — Running Up That Hill (1985)",
                        youtube_search("Kate Bush Running Up That Hill 1985 official"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Stranger Things, Season 4",
                    year="2022",
                    setting="A Netflix sequence in which the song pulls a character back from the underworld.",
                    register="Rescue anthem. For a new audience, the song's primary context.",
                    media=(
                        MediaLink(
                            "Kate Bush back in the charts (coverage)",
                            youtube_search("Kate Bush Running Up That Hill Stranger Things chart"),
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The song reached number one thirty-seven years after release. For "
                "many Gen Z listeners, it now cites Stranger Things before it cites "
                "1985. The soundtrack cue became the 'original' context."
            ),
        ),
    ),
)


WINGS: Tuple[Wing, ...] = (WING_I, WING_II, WING_III)


def wing_by_key(key: str) -> Wing:
    for w in WINGS:
        if w.key == key:
            return w
    raise KeyError(key)


MUSEUM_THESIS = (
    "Welcome. This museum is about a single simple fact: a song can be "
    "sung again, by someone else, in a different year, to a different "
    "room — and when it is, it often means something different, "
    "sometimes the opposite of what it once did. The exhibits gathered "
    "here are not about originality. They are about reperformance: the "
    "second life of a lyric, and the third, and the fourth."
)
