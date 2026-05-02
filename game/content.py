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
class Citation:
    """Footnoted source. ``number`` is the in-text superscript marker
    used by the body copy (e.g. 1, 2, 3 …)."""

    number: int
    url: str
    label: str = ""  # short title; falls back to the URL if blank


@dataclass(frozen=True)
class EssaySection:
    """A formatted section of an exhibit's analysis. Bodies may contain
    paragraph breaks ("\\n\\n") and inline footnote markers ("[1]", "[2]"…)
    that map to the exhibit's ``citations`` tuple. ``image`` is an optional
    illustration filename (relative to ``assets/art/``) for the section's
    Frame image."""

    heading: str
    body: str
    image: Optional[str] = None
    image_caption: Optional[str] = None


@dataclass(frozen=True)
class Exhibit:
    song: str
    art_key: str  # e.g. 'hurt' — used to look up assets/art/exhibits/<key>.png
    original: Performance
    reperformances: Tuple[Performance, ...]
    curator_note: str
    essay: Tuple[EssaySection, ...] = ()
    citations: Tuple[Citation, ...] = ()


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
DANCING_ON_MY_OWN_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Robyn (2010)",
        body=(
            "Released in April 2010 as the first single from Swedish artist Robyn\u2019s Body Talk "
            "trilogy. The track is a contemporary electro-pop ballad in which Robyn explicitly "
            "modeled it on what she called \u201csad, gay disco anthems\u201d such as Ultravox\u2019s "
            "\u201cDancing With Tears In My Eyes\u201d and songs by Sylvester and Donna Summer.\u201d[1] "
            "To Robyn, there is something inherently sacred about the dance floor, comparing the "
            "club to \u201ca new church\u2026where people go to experience something bigger than "
            "themselves.\u201d In terms of instrumentation, many other dance-pop and electro-pop "
            "music were being released around the same time against the broader 2010 dance-pop "
            "landscape such as \u201cLike a G6\u201d by Far East Movement or \u201cClub Can\u2019t Handle Me\u201d "
            "by Flo Rida[2]. However, many of these songs were trying to maintain a very positive "
            "and fun atmosphere both in instrumentation and lyrics, while Robyn and her "
            "songwriter wanted to maintain the raw and ugly emotions of heartbreak, rather than "
            "fake some heroic protagonist who wishes to be calm and mature. Robyn\u2019s song and "
            "music video made it clear that the dancefloor is a place to fully feel and embrace "
            "all of that rawness, rather than a place to numb it. The defiant yet cathartic act of "
            "expressing unfiltered emotional pain through dancing and singing."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The accompanying music video[3] reinforces the song\u2019s emotional logic visually. "
            "Robyn is seen dancing alone in a sparse industrial space with a microphone stand, "
            "exposed cables, and stage lights\u2014\u2014the bare image of a club where all of the "
            "equipment makes a dance floor possible but no one else is around to fill it up. "
            "Furthermore, her outfit seems like clubwear, but no one else is around to see it. "
            "The result is a frame that holds two feelings simultaneously: the ache of being "
            "abandoned on a dancefloor, but also the strange freedom of having that dancefloor "
            "entirely to oneself without the need to perform for others. (1:37)"
        ),
        image="exhibits/frames/dancing_robyn.png",
        image_caption="Robyn \u2014 \u201cDancing on My Own\u201d (2010), 1:37",
    ),
    EssaySection(
        heading="II. Reperformance: Calum Scott",
        body=(
            "Calum Scott performed a cover of \u201cDancing on My Own\u201d in April 2015\u2014\u2014almost "
            "exactly five years after Robyn\u2019s original release\u2014\u2014for his Britain\u2019s Got Talent "
            "audition, where Simon Cowell pressed the Golden Buzzer[4]. Since then, the audition "
            "clip has garnered over 400 million views on Youtube. The following April, Scott "
            "released a studio version of his cover where it reached No. 2 on the UK official "
            "charts\u2014\u2014higher than Robyn\u2019s original song ever charted in the UK[5]. Scott\u2019s "
            "version strips the song of its signature synths and club beats, replacing them with "
            "a solo piano and slower tempo, and the vocals feel very exposed. The arrangement now "
            "signals not chaos nor rebellion against the sadness of heartbreak, but a more deep "
            "and intimate wallowing and witnessing of the pain. Crucially, while Robyn drew on "
            "the inspiration of gay disco anthems without herself identifying as a queer artist, "
            "Scott reroutes the song\u2019s queerness through a form of autobiography. He alters one "
            "small but consequential line: when Robyn sings the lyrics \u201cBut I\u2019m not the girl "
            "you\u2019re taking home,\u201d Scott sings \u201cBut I\u2019m not the guy you\u2019re taking home,\u201d while "
            "preserving the original pronouns describing the unrequited love subject that is "
            "kissing a woman\u2014\u2014 \u201cwatching you kiss her.\u201d The result is a song narrated "
            "explicitly from a gay man\u2019s perspective of a man watching the man he wishes to be "
            "with, kissing a woman. Scott, who has publicly discussed the difficulty of coming to "
            "terms with his sexuality growing up[6] and has mentioned that this reframing was "
            "deliberate, and has continued to make his coming-out experience as an integral part "
            "of his artist identity[7]."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The accompanying music video[8] has many scenes where Calum Scott stands among a "
            "sea of figures uniformly dressed in white clothing, all gazing forward in the same "
            "direction under a cool-toned blue color grade. Scott is surrounded by people, yet "
            "none of them turn toward him or acknowledge his presence. While Robyn\u2019s music "
            "video reflects every element of a dancefloor except the crowd, Scott\u2019s video "
            "contains an audience but without the equipment and strips them of individuality and "
            "feeling. The scene inverts Robyn\u2019s loneliness as her portrayal was of being alone "
            "in a space built for crowds, while Scott\u2019s is the feeling of being alone within a "
            "crowd. The ache of unrequited longing is amplified here is the invisibility of "
            "standing in a room full of people. (2:08)"
        ),
        image="exhibits/frames/dancing_calum.png",
        image_caption="Calum Scott \u2014 \u201cDancing on My Own\u201d (2016), 2:08",
    ),
    EssaySection(
        heading="III. Synthesis and Comparison",
        body=(
            "Robyn\u2019s song was constructed out of a queer disco lineage and built to honor the "
            "dancefloor (which Robyn referred to as her \u201cnew church\u201d) as the place where pain "
            "can be felt in its rawest form, processed through a defiance and electro-pop "
            "production. Scott\u2019s version is constructed in an entirely different context: the "
            "talent-show stage, where his voice is meant to be the main focus of the performance "
            "and production is stripped back to make room for it. His cover honors the song\u2019s "
            "emotional story (portrayal of unrequited love) through the genre of a ballad, but "
            "in doing so, it abandons the original versions defining intentions of making "
            "\u201cDancing on My Own\u201d a song for the dancefloor. Furthermore, while Robyn\u2019s version "
            "was structurally influenced by queer culture, Scott\u2019s version is autobiographical, "
            "shown through a single word change in lyrics. What survives is the expression of "
            "unrequited love, but with a completely different context."
        ),
    ),
)


DANCING_ON_MY_OWN_CITATIONS: Tuple[Citation, ...] = (
    Citation(1,
        "https://www.popmatters.com/126189-robyn-is-here-the-swedish-singer-premieres-her-new-video-for--2496187792.html",
        "PopMatters \u2014 Robyn premieres \u201cDancing on My Own\u201d"),
    Citation(2,
        "https://www.grammy.com/news/robyn-dancing-on-my-own-impact-legacy",
        "Grammy.com \u2014 \u201cDancing on My Own\u201d impact and legacy"),
    Citation(3,
        "https://www.youtube.com/watch?v=CcNo07Xp8aQ",
        "Robyn \u2014 \u201cDancing on My Own\u201d official music video (YouTube)"),
    Citation(4,
        "https://www.youtube.com/watch?v=WSinMOs5eGw",
        "Calum Scott \u2014 Britain\u2019s Got Talent audition (YouTube)"),
    Citation(5,
        "https://genius.com/Calum-scott-dancing-on-my-own-lyrics",
        "Genius \u2014 Calum Scott lyrics (compared to Robyn\u2019s)"),
    Citation(6,
        "https://www.gaytimes.co.uk/culture/calum-scott-interview/",
        "Gay Times \u2014 Calum Scott interview"),
    Citation(7,
        "https://www.billboard.com/music/music-news/calum-scott-response-coming-out-no-mattter-what-don-diablo-interview-8487696/",
        "Billboard \u2014 Calum Scott on coming out"),
    Citation(8,
        "https://www.youtube.com/watch?v=q31tGyBJhRY",
        "Calum Scott \u2014 \u201cDancing on My Own\u201d official music video (YouTube)"),
)


DO_I_WANNA_KNOW_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Arctic Monkeys (2013)",
        body=(
            "Released in June 2013 as the lead single from Arctic Monkeys\u2019 fifth studio album "
            "AM, \u201cDo I Wanna Know\u201d[1] marked a shift from the band\u2019s usual direct indie rock "
            "style by incorporating in R&B influences into its composition, pulling the band "
            "toward a heavier and slower register. By frontman Alex Turner\u2019s account, the "
            "album\u2019s underlying approach was an attempt to translate the methods of an R&B "
            "producer into the format of a rock band\u2014\u2014experienting with their instruments to "
            "mimic the layered, loop samples a producer such as as Timbaland might assemble in a "
            "studio[2]. The framing matters because the textures of the song and distinctive "
            "groove resemble the looped elements an R&B producer would chop and stack, but they "
            "are structurally created using the instrumentation of a traditional rock band. The "
            "result is a sultry, heavy song that sonically resembles a desperate, possibly, "
            "obsessive lover wondering whether his love is being reciprocated. Co-producer James "
            "Ford has spoken about deliberately building and sustaining the song\u2019s heavy mood, "
            "treating that heaviness as something they established early on and wanting to build "
            "and carry[3]."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame attached captures the Arctic Monkeys performing \u201cDo I Wanna Know\u201d live "
            "at the Red Bull Sound Space in 2013[4], which will serve as a comparison point "
            "against Hozier\u2019s later studio cover. This performance stages the song as a "
            "rock-club performance, with the backdrop filled with a wall of stacked vintage "
            "speaker cabinets. The density of the gear is doing a lot of visual work, where "
            "before the music even starts, the staging suggests that this will be a loud, "
            "amplified, guitar-driven performance, with the equipment backdrop complementing the "
            "genre. The \u201c0114\u201d on the drum set reflects Sheffield\u2019s dialing code, which is "
            "the hometown of the members of the Arctic Monkeys[5], a tribute to their humble "
            "roots of growth from hometown band to worldwide fame. Turner stands center with a "
            "rock-frontman aesthetic: his white shirt, unbuttoned halfway to expose the chest, "
            "implying rebellion and theatrical masculinity resembling the style of 1970s rock "
            "band frontmen such as Mick Jagger or Robert Plant. There is an outwardness in his "
            "body language where his feet are planted apart, the guitar is being displayed as "
            "much as it is being played, and every element of the physical staging is oriented "
            "toward an audience, as expected by the context of the performance. The frame "
            "ultimately shows that \u201cDo I Wanna Know\u201d is a song performed more through "
            "seduction than longing. The lyrics ask a vulnerable question of whether the "
            "narrator\u2019s love interest feels the same way about him, but the visual staging "
            "overlays that vulnerability with a sort of swagger that matches the R&B influences "
            "and mood of the song, even though we cannot explicitly hear anything from the static "
            "frame."
        ),
        image="exhibits/frames/diwk_arctic.png",
        image_caption="Arctic Monkeys \u2014 Red Bull Sound Space, 2013",
    ),
    EssaySection(
        heading="II. Reperformance: Hozier (2016)",
        body=(
            "Hozier covered \u201cDo I Wanna Know\u201d in October 2016 for BBC Radio 1\u2019s Live "
            "Lounge\u2014\u2014a long-running segment in which artists perform one of their own songs "
            "alongside a cover, with the cover often reinterpreted in a genre outside the "
            "artist\u2019s usual style[6]. In this performance, the Arctic Monkeys\u2019 rock "
            "instrumentals with R&B influence are replaced completely with a guitar that is "
            "played in a softer, blues-folk pattern, joined by a cello, bass, women\u2026"
        ),
        image="exhibits/frames/diwk_hozier.png",
        image_caption="Hozier \u2014 BBC Radio 1 Live Lounge, 2016",
    ),
)


DO_I_WANNA_KNOW_CITATIONS: Tuple[Citation, ...] = (
    Citation(1, "https://www.youtube.com/watch?v=bpOSxM0rNPM",
             "Arctic Monkeys \u2014 \u201cDo I Wanna Know?\u201d official music video"),
    Citation(2,
        "https://www.ultimate-guitar.com/articles/features/the_story_behind_do_i_wanna_know_by_arctic_monkeys-69117",
        "Ultimate Guitar \u2014 The story behind \u201cDo I Wanna Know?\u201d"),
    Citation(3,
        "https://faroutmagazine.co.uk/alex-turner-isolated-vocals-arctic-monkeys-do-i-wanna-know/",
        "Far Out Magazine \u2014 Alex Turner on the song\u2019s mood"),
    Citation(4, "https://youtu.be/1tWFk8ojF4M",
             "Arctic Monkeys \u2014 Live at Red Bull Sound Space (KROQ)"),
    Citation(5, "https://faroutmagazine.co.uk/matt-helders-drum-kit-0114/",
             "Far Out Magazine \u2014 The \u201c0114\u201d on Helders\u2019 drum kit"),
    Citation(6, "https://en.wikipedia.org/wiki/Live_Lounge",
             "Wikipedia \u2014 BBC Radio 1\u2019s Live Lounge"),
)


WAKE_ME_UP_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="IV. Original Context: Aloe Blacc, Mike Einziger (2013)",
        body=(
            "The original completed version of Wake Me Up is acoustic. The song was written in "
            "an evening at Mike Einziger's home studio in Malibu: Einziger on acoustic guitar, "
            "Aloe Blacc arriving with fragments of lyrics, and the two lines that would become "
            "the emotional core of the song coming together almost accidentally. Blacc sang "
            "\u201cWake me up when it's all over,\u201d then introduced the line \u201cAll this time I was "
            "finding myself, I didn't know I was lost,\u201d and was concerned that these two lines "
            "wouldn't make any sense in the same song. They are, in retrospect, the most honest "
            "lines in the song. One is about wanting to skip past experience. The other is about "
            "not recognizing your own condition from inside it. Together they describe something "
            "that sounds less like a coming-of-age anthem and more like dissociation: the "
            "experience of living a life that doesn't feel real."
        ),
    ),
    EssaySection(
        heading="V. Reperformance: Avicii (2013)",
        body=(
            "Avicii remixed Wake Me Up into a dance and electronic song, the version that most "
            "people know now."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "(Analysis in progress.)"
        ),
    ),
)


WING_I = Wing(
    key="wing_i",
    title="Wing I",
    subtitle="Same Lyrics, Opposite Register",
    thesis=(
        "The words do not move, but the weather around them does. "
        "In this wing, a single lyric is tracked through performances "
        "whose emotional temperatures run in opposite directions \u2014 "
        "from swagger to longing, from rage to penitence, from the "
        "bedroom to the cathedral."
    ),
    accent=COL_WING_I,
    exhibits=(
        Exhibit(
            song="Dancing on My Own",
            art_key="dancing_on_my_own",
            original=Performance(
                performer="Robyn",
                year="2010",
                setting="Body Talk Pt. 1. Electro-pop ballad written for the dance floor as \u201ca new church.\u201d",
                register="Defiant catharsis. Heartbreak felt in its rawest form, on the floor.",
                media=(
                    MediaLink(
                        "Robyn \u2014 Dancing on My Own (2010, music video)",
                        "https://www.youtube.com/watch?v=CcNo07Xp8aQ",
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Calum Scott",
                    year="2016",
                    setting="Britain\u2019s Got Talent audition (2015) and a 2016 studio single. Solo piano, slower tempo.",
                    register="Wallowing, witnessing. A ballad of unrequited love, autobiographical and out.",
                    media=(
                        MediaLink(
                            "Calum Scott \u2014 Dancing on My Own (2016, music video)",
                            "https://www.youtube.com/watch?v=q31tGyBJhRY",
                        ),
                        MediaLink(
                            "Calum Scott \u2014 BGT audition (2015)",
                            "https://www.youtube.com/watch?v=WSinMOs5eGw",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Robyn made \u201cDancing on My Own\u201d a song for the dancefloor; Scott made it a "
                "song for the talent-show stage. The lyrics survive almost intact, save for one "
                "pronoun \u2014 \u201cthe girl\u201d to \u201cthe guy\u201d \u2014 and the song\u2019s queerness moves "
                "from structural inheritance to autobiography."
            ),
            essay=DANCING_ON_MY_OWN_ESSAY,
            citations=DANCING_ON_MY_OWN_CITATIONS,
        ),
        # Hurt and Hallelujah are reserved; analysis not yet written.
        # Exhibit(
        #     song="Hurt",
        #     art_key="hurt",
        #     original=Performance(
        #         performer="Nine Inch Nails",
        #         year="1994",
        #         setting="Studio, from The Downward Spiral. Industrial rock, late in the album, close to collapse.",
        #         register="Self-lacerating. Youth inside its own ruin.",
        #         media=(
        #             MediaLink(
        #                 "Nine Inch Nails \u2014 Hurt (1994)",
        #                 youtube_search("Nine Inch Nails Hurt 1994 official"),
        #             ),
        #         ),
        #     ),
        #     reperformances=(
        #         Performance(
        #             performer="Johnny Cash",
        #             year="2002",
        #             setting="American IV: The Man Comes Around. Filmed at his Tennessee home months before his death.",
        #             register="Valedictory. A life looking back at itself at the end.",
        #             media=(
        #                 MediaLink(
        #                     "Johnny Cash \u2014 Hurt (2002)",
        #                     youtube_search("Johnny Cash Hurt 2002 official music video"),
        #                 ),
        #             ),
        #         ),
        #     ),
        #     curator_note=(
        #         "Trent Reznor wrote Hurt from inside addiction at twenty-eight; "
        #         "Cash sang it at seventy, months before his death. "
        #     ),
        # ),
        # Exhibit(
        #     song="Hallelujah",
        #     art_key="hallelujah",
        #     original=Performance(
        #         performer="Leonard Cohen",
        #         year="1984",
        #         setting="Various Positions, a studio album Columbia records initially declined to release in the United States.",
        #         register="Sacred and profane held together. Ironic, adult, bruised.",
        #         media=(
        #             MediaLink(
        #                 "Leonard Cohen \u2014 Hallelujah (1984)",
        #                 youtube_search("Leonard Cohen Hallelujah 1984 official"),
        #             ),
        #         ),
        #     ),
        #     reperformances=(
        #         Performance(
        #             performer="Jeff Buckley",
        #             year="1994",
        #             setting="Grace. Recorded after John Cale\u2019s 1991 arrangement stripped Cohen\u2019s verses down.",
        #             register="Tender, erotic, almost whispered \u2014 romance as devotion.",
        #             media=(
        #                 MediaLink(
        #                     "Jeff Buckley \u2014 Hallelujah (1994)",
        #                     youtube_search("Jeff Buckley Hallelujah official 1994"),
        #                 ),
        #             ),
        #         ),
        #     ),
        #     curator_note=(
        #         "Cohen wrote some eighty verses over seven years; Buckley narrowed them to four."
        #     ),
        # ),
        Exhibit(
            song="Do I Wanna Know?",
            art_key="do_i_wanna_know",
            original=Performance(
                performer="Arctic Monkeys",
                year="2013",
                setting="AM. R&B-inflected indie rock written to translate Timbaland\u2019s loop methods into a band format.",
                register="Sultry, heavy, swaggering. Vulnerability staged as seduction.",
                media=(
                    MediaLink(
                        "Arctic Monkeys \u2014 Do I Wanna Know? (2013)",
                        "https://www.youtube.com/watch?v=bpOSxM0rNPM",
                    ),
                    MediaLink(
                        "Arctic Monkeys \u2014 Live at Red Bull Sound Space (2013)",
                        "https://youtu.be/1tWFk8ojF4M",
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Hozier",
                    year="2016",
                    setting="BBC Radio 1\u2019s Live Lounge. Acoustic guitar, cello, backing vocalists.",
                    register="Softer, blues-folk. Vulnerability without the swagger.",
                    media=(
                        MediaLink(
                            "Hozier \u2014 Do I Wanna Know? (BBC Live Lounge, 2016)",
                            youtube_search("Hozier Do I Wanna Know Live Lounge 2016"),
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The original frames desire as a question asked across a bar. "
                "Hozier relocates it to a pew: the same line, \u2018I dreamt about "
                "you nearly every night this week,\u2019 becomes confession rather "
                "than come-on. The lyric never claims a gender; performance decides."
            ),
            essay=DO_I_WANNA_KNOW_ESSAY,
            citations=DO_I_WANNA_KNOW_CITATIONS,
        ),
        Exhibit(
            song="Wake Me Up",
            art_key="wake_me_up",
            original=Performance(
                performer="Aloe Blacc & Mike Einziger",
                year="2013",
                setting="Mike Einziger\u2019s home studio in Malibu. Acoustic guitar; lyric fragments from Aloe Blacc.",
                register="Quiet, dissociative. Two honest lines about not recognizing your own life.",
                media=(
                    MediaLink(
                        "Aloe Blacc \u2014 Wake Me Up (acoustic)",
                        youtube_search("Aloe Blacc Wake Me Up acoustic"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Avicii",
                    year="2013",
                    setting="Studio remix as an electronic dance single from True (2013).",
                    register="Festival anthem. Soaring drop where the verses\u2019 ache used to sit.",
                    media=(
                        MediaLink(
                            "Avicii \u2014 Wake Me Up (2013)",
                            youtube_search("Avicii Wake Me Up 2013 official"),
                        ),
                    ),
                ),
            ),
            curator_note=(
                "An acoustic song about dissociation \u2014 \u2018I didn\u2019t know I was lost\u2019 \u2014 "
                "becomes a dance anthem about being awake. The lyric doesn\u2019t change; the "
                "tempo, the kick drum, and the room around it do."
            ),
            essay=WAKE_ME_UP_ESSAY,
            citations=(),
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


WINGS: Tuple[Wing, ...] = (WING_I, WING_II)


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
