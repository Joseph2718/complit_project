"""Museum content, structured so new exhibits can be plugged in without
touching any scene code. Each wing has a title, subtitle, thesis, accent
color, and a list of exhibits; each exhibit has two or more performances
(an original and one or more reperformances) and a curator's note.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .constants import COL_WING_I, COL_WING_II


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
    """Footnoted source for Chicago *Notes* style (CMOS 17).

    ``number`` matches the in-text note reference (superscript ``¹``, ``²``, …
    in the exhibit; data is still written as ``[1]``, ``[2]``). Each entry becomes
    one numbered note with prose line plus URL — a light web adaptation of full
    Chicago note form.
    """

    number: int
    url: str
    label: str = ""  # short title; falls back to the URL if blank


@dataclass(frozen=True)
class EssaySection:
    """A formatted section of an exhibit's analysis. Bodies may contain
    paragraph breaks (``\\n\\n``) and Chicago-style source markers written in
    the data as ``[1]``, ``[2]`` … which render as raised superscript numerals
    (modest type size) and map to the exhibit's ``citations`` tuple. ``image`` is an optional illustration
    filename (relative to ``assets/art/``) for the section's frame image.
    ``image_caption`` may retain video timestamps (e.g. ``1:37``); running
    prose in ``body`` has parenthetical timestamps like ``(1:37)`` stripped
    at display time so captions carry the timing.
    """

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
            "entirely to oneself without the need to perform for others."
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
            "standing in a room full of people."
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
            "obsessive lover wondering whether his love is being reciprocated. The line "
            "\u201ccrawling back to you\u201d is accompanied with an intensified increase swell in the "
            "guitar, where the riff thickens, pushing forward an image of a physical, passionate "
            "surrender to one\u2019s lover\u2014\u2014dragging the listener into the same gravitational pull "
            "that narrator is admitting to. Co-producer James Ford has spoken about deliberately "
            "building and sustaining the song\u2019s heavy mood, treating that heaviness as something "
            "they established early on and wanting to build and carry[3]."
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
            "and mood of the song, even though we cannot explicitly hear anything from the "
            "static frame."
        ),
        image="exhibits/frames/diwk_arctic.png",
        image_caption="Arctic Monkeys \u2014 Red Bull Sound Space, 2013 (3:45)",
    ),
    EssaySection(
        heading="II. Reperformance: Hozier (2016)",
        body=(
            "Hozier covered \u201cDo I Wanna Know\u201d in October 2014[6] for BBC Radio 1\u2019s Live "
            "Lounge\u2014\u2014a long-running segment in which artists perform one of their own songs "
            "alongside a cover, with the cover often reinterpreted in a genre outside the "
            "artist\u2019s usual style[7]. In this performance, the Arctic Monkeys\u2019 rock "
            "instrumentals with R&B influence are replaced completely with a guitar that is "
            "played in a softer, blues-folk pattern, joined by a cello, bass, and backing female "
            "vocalists. The swagger of the original song is now replaced for looser texture of "
            "warmth and softer tone where the overwhelming instrumentals of drums are replaced "
            "with softer string harmonization of the cello and Hozier\u2019s guitar. Most "
            "consequentially, where the question \u201cDo I wanna know?\u201d was sung in a seductive, "
            "obsessive tone by Turner, Hozier sings the question in a tone closer to yearning, "
            "pulling the lyrics closer toward the kind of confessional folk-soul genre his own "
            "catalog normally sits in. The line \u201ccrawling back to you\u201d can now be read as "
            "earnest resignation. Without the thickening guitar sound that follows \u201ccrawling "
            "back to you,\u201d there is a slower and gentler delivery of the song, where the lyrics "
            "are left bare with soft picking of the instruments beneath it. The song is now "
            "holding space around the vulnerable admission. Hozier\u2019s cover has resonated deeply "
            "with listeners, gaining popularity in recent years. In January 2025, the song "
            "became viral on tiktok, accumulating over one million posts under the official "
            "sound (as of May 2026), surpassing the Arctic Monkeys\u2019 original, which currently "
            "sits at 945.1K posts."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame is taken from the same BBC Radio 1 Live Lounge performance where the "
            "studio is small with neon lights glowing softly in the background. The lighting is "
            "soft and ambient with cool pinks and blues bleeding into one another. The frame "
            "embraces the studio for what it is: a working room made to create and record music "
            "for the audience to listen to at home, rather than a song that is meant to be "
            "performed in front of a large crowd. Similar to the Arctic Monkeys, you can see "
            "all of the working parts of the song at play such as the cellist or the backing "
            "vocalists. Hozier\u2019s outfit contrasts Alex Turner\u2019s theatrical frontman aesthetic "
            "where he is wearing a denim jacket layered over a flannel shirt\u2014\u2014an outfit closer "
            "to everyday wear than a costume. His posture is also more inward, where his "
            "shoulders are relaxed and it seems as though he is receiving and taking in all of "
            "the parts of the song rather than projecting it. Though barely visible in this "
            "angle, a long curly strand of hair falls down the far side of his face, unstyled. "
            "This is in stark contrast to Turner\u2019s sleek gelled-back hair, adding another "
            "layer of pure intimacy and vulnerability to the staging and music. Even without "
            "hearing the music, the frame suggests the song being performed is one of "
            "gentleness and vulnerability in an intimate setting, rather than a performed "
            "seduction."
        ),
        image="exhibits/frames/diwk_hozier.png",
        image_caption="Hozier \u2014 BBC Radio 1 Live Lounge, 2016 (1:45)",
    ),
    EssaySection(
        heading="III. Synthesis and Comparison",
        body=(
            "The Arctic Monkeys built \u201cDo I Wanna Know\u201d as an attempt to translate R&B "
            "production methods into the format of a rock band, resulting in a song whose "
            "heavy, looped groove creates a hybrid, sultry, and gravitational sound rather "
            "than directly indie rock. Hozier\u2019s cover is constructed in a different context "
            "at BBC Radio 1\u2019s Live Lounge, a studio segment whose entire premise is "
            "genre-translation. The segment asks artists to remake an existing song in their "
            "own usual style\u2014\u2014in Hozier\u2019s case, blues-folk. What this means is that \u201cDo I "
            "Wanna Know\u201d was already produced as a translation (R&B \u2192 Indie Rock), and when "
            "it gets to Hozier, his cover would then be the third genre to have touched the "
            "song, not the second. The R&B influences the Arctic Monkeys had filtered through "
            "rock instrumentation are now filtered again through acoustic guitar, cello, and "
            "beautiful vocal harmonies. The song that is ultimately created by Hozier\u2019s cover "
            "is a result of genre translations stacked on top of one another, each one keeping "
            "the lyrics intact while rewriting the overall composition of the song."
        ),
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
    Citation(6, "https://xpn.org/2018/10/04/hozier-/",
             "WXPN \u2014 Hozier covers Arctic Monkeys at BBC Live Lounge"),
    Citation(7, "https://en.wikipedia.org/wiki/Live_Lounge",
             "Wikipedia \u2014 BBC Radio 1\u2019s Live Lounge"),
)


WAKE_ME_UP_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Aloe Blacc, Mike Einziger (2013)",
        body=(
            "The original completed version of \u201cWake Me Up\u201d is acoustic. The initial "
            "inspiration for the song came to Aloe Blacc during a flight home from Geneva when "
            "he was reflecting on how much his life has changed since the success of \u201cI Need "
            "a Dollar\u201d and how it feels like a dream that he never wants to end[1]. He wrote "
            "the lyrics on his phone. The song was written in an evening at Mike Einziger\u2019s "
            "home studio in Malibu: Einziger on acoustic guitar, Aloe Blacc arriving with "
            "fragments of lyrics, and the two lines that would become the emotional core of the "
            "song coming together almost accidentally. Blacc sang \u201cWake me up when it\u2019s all "
            "over,\u201d then introduced the line, \u201cAll this time I was finding myself, I didn\u2019t "
            "know I was lost,\u201d and was concerned that these two lines wouldn\u2019t make any "
            "sense in the same song[2]. One is about wanting to skip past experience. The other "
            "is about not recognizing your own condition from inside it. They describe "
            "something that sounds less like a coming-of-age anthem and more like dissociation: "
            "the experience of living a life that doesn\u2019t feel real. Aloe Blacc describes the "
            "song as a folk-inspired dance song."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "As the song[3] is about fear and dealing with difficult situations, the video uses "
            "actual people that have been negatively affected by immigration laws in the U.S. "
            "and highlights the struggle of Mexican immigrants with various aspects of "
            "immigration in the United States. It was inspired by the true stories of "
            "undocumented immigrants who struggle to reunite with their families. It represents "
            "waking up when immigrants are able to live freely."
        ),
        image="exhibits/frames/wake_me_up_aloe.png",
        image_caption="Aloe Blacc \u2014 \u201cWake Me Up\u201d (acoustic, 2013)",
    ),
    EssaySection(
        heading="II. Reperformance: Avicii (2013)",
        body=(
            "Avicii remixed \u201cWake Me Up\u201d into a dance and electronic song, the version that "
            "most people know now. Avicii invited Aloe Blacc and Mike Einziger to join him in "
            "a music session, and Aloe Blacc came prepared with the lyrics for \u201cWake Me Up\u201d "
            "while Mike Einzinger had created the guitar part. With the recording of a guitar "
            "and vocal acoustic demo, Avicii was able to remix and arrange the music by "
            "increasing the tempo and adding drums and synths."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "Avicii\u2019s video has an entirely different meaning from Aloe Blacc\u2019s version, "
            "featuring a Russian fashion model and her younger sister and depicts how they are "
            "outsiders and different from the rest of the people in their small town[4]. Both "
            "are unhappy and have matching tattoos that set them apart. One morning, the model "
            "gets up early and rides off on a horse to a nearby city. She notices a woman with "
            "the Avicii logo birthmark like the one on her lower arm. They meet others and then "
            "jump into a truck and are then shown to be attending an Avicii concert. The next "
            "morning, she rides back on the horse to Laneya. The video ends with them walking "
            "down the highway and shots from the concert and the staring villagers from the "
            "beginning. It serves as a metaphor about identity, belonging, and self-discovery, "
            "and represents two sisters who are trying to find a place where they belong so "
            "the lyrics mean wake me up when there are people like them. This version shows a "
            "different meaning of finding a way home."
        ),
        image="exhibits/frames/wake_me_up_avicii.png",
        image_caption="Avicii \u2014 \u201cWake Me Up\u201d (2013)",
    ),
)


WAKE_ME_UP_CITATIONS: Tuple[Citation, ...] = (
    Citation(1,
        "https://www.today.com/popculture/aloe-blacc-says-he-wrote-wake-me-about-his-own-1d80008710",
        "Today \u2014 Aloe Blacc on writing \u201cWake Me Up\u201d"),
    Citation(2, "https://www.songfacts.com/facts/avicii/wake-me-up",
             "Songfacts \u2014 Avicii, \u201cWake Me Up\u201d"),
    Citation(3, "https://www.youtube.com/watch?v=M_o6axAseak",
             "Aloe Blacc \u2014 \u201cWake Me Up\u201d official music video"),
    Citation(4, "https://www.youtube.com/watch?v=IcrbM1l_BoI",
             "Avicii \u2014 \u201cWake Me Up\u201d official music video"),
)


# ---------------------------------------------------------------------------
# Take Me to Church --- Hozier (2014) / Demi Lovato (2015)
# ---------------------------------------------------------------------------
TAKE_ME_TO_CHURCH_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Hozier (2014)",
        body=(
            "Hozier wrote the song explicitly as a critique of the Catholic Church\u2019s "
            "homophobia, using a relationship as a religious metaphor. When Hozier recorded "
            "\u201cTake Me to Church\u201d in his attic in County Wicklow at two in the morning in "
            "2013[1], he was not simply writing a love song. Growing up in Ireland, he always "
            "saw the hypocrisy of the Catholic Church: \u201cThe history speaks for itself, and I "
            "grew incredibly frustrated and angry. I essentially just put that into my "
            "words.\u201d[2] The song uses the language of religious devotion as a weapon turned "
            "back on the institution itself. To hear \u201cTake Me to Church\u201d in 2013 was to hear "
            "a protest song, a powerful critique of organized religion within a love ballad, "
            "arguing that loving another person is the only true form of worship and asserting "
            "yourself and reclaiming your humanity through an act of love. He metaphorically "
            "compares his relationship to a religious experience through using similes, \u201cMy "
            "church offers no absolutes. She tells me, \u2018Worship in the bedroom\u2019 The only "
            "heaven I\u2019ll be sent to is when I\u2019m alone with you.\u201d The church in the title is "
            "an institution to burn down. \u201cTake Me to Church\u201d has a slow tempo and a heavy "
            "subject matter that can seem controversial to some, combining the dramatic "
            "quality found in traditional Irish songs and ballads with the metaphorical "
            "density and attention to rhythm often associated with American blues."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The music video, shot in black and white grayscale in Cork, Ireland, follows a "
            "same-sex relationship between two young men in Russia and the violently "
            "homophobic backlash that ensues when the community learns of one of the men\u2019s "
            "sexuality. One of them spends much of the video trying to hide a steel case "
            "wrapped in chains, but his efforts are unsuccessful and the masked people capture "
            "his lover and torture him. The homosexual man gets brutally beaten by a gang of "
            "thugs while his lover looks on helplessly. The pace of the editing and "
            "transitions is consistent throughout. This may be interpreted as representing how "
            "nothing seems to change regarding society accepting freedom of choice and "
            "homosexuality. Viewers of the video are prompted to identify violence and "
            "discrimination based on differences in gender and sexuality. Overall, the video serves "
            "as commentary on human rights and institutional homophobia in certain "
            "countries.[3]"
        ),
        image="exhibits/frames/ttc_hozier.png",
        image_caption="Hozier \u2014 \u201cTake Me to Church\u201d (2014, music video)",
    ),
    EssaySection(
        heading="II. Reperformance: Demi Lovato (2015)",
        body=(
            "When women cover \u201cTake Me to Church\u201d with acoustic or pop arrangements, the "
            "religious critique tends to dissolve and it reads simply as an intense love song. "
            "Demi Lovato sang the song with the exact same lyrics at the BBC Radio 1 Live "
            "Lounge two years after its release[4]. She performed with a band and two backup "
            "singers. She told the Live Lounge host before the performance, \u201cThe first time I "
            "heard it, it was on the radio. And I was like, \u2018Wow, this is on pop radio.\u2019 And "
            "it\u2019s not your typical pop song. In fact, it doesn\u2019t sound like a pop song.\u201d "
            "Notably, she did not change the pronouns in the original version, a choice that "
            "preserved the song\u2019s queer legibility and signaled her alignment with its "
            "politics. Lovato had been a vocal strong supporter of LGBTQ+ rights, and the "
            "cover may be seen as an act of solidarity. She had entered treatment at 18, "
            "relapsed publicly, nearly died from an overdose in 2018, and had spoken openly "
            "about her complicated, ongoing relationship with God, \u201cI believe in gay marriage, "
            "I believe in equality. I think there\u2019s a lot of hypocrisy with religion. But I "
            "just found that you can have your own relationship with God, and I still have a "
            "lot of faith.\u201d[5]"
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame shows Demi Lovato singing \u201cTake Me to Church\u201d at BBC Radio 1\u2019s Live "
            "Lounge in a dimly-lit, intimate setting. Her rich powerful voice combined with the "
            "harmonization from the voices of the backup singers and the live instruments of "
            "the band helps bring another dimension to the song. She sings the song strongly "
            "as if she is living the pain of the song, and puts emphasis on the \u201cAmen\u201d with "
            "rifts and deep emotion."
        ),
        image="exhibits/frames/ttc_demi.png",
        image_caption="Demi Lovato \u2014 BBC Radio 1 Live Lounge, 2015",
    ),
    EssaySection(
        heading="III. Comparison",
        body=(
            "Both Hozier and Demi Lovato arrive at the meaning of this song from entirely "
            "different directions and the emotional register shifts completely. Hozier\u2019s rage "
            "is outward. The church he addresses is an institution, a political structure, a "
            "system of organized cruelty toward those it condemns. When he sings, \u201cI\u2019ll tell "
            "you my sins so you can sharpen your knife,\u201d the anger is directed at the "
            "external authority doing the judging. Demi Lovato\u2019s version, sung by a woman "
            "who has almost literally lived that line, who has confessed her struggles "
            "publicly and watched them be weaponized, turns the same words inward. Her "
            "delivery is raw in a different way: not of political outrage but of someone who "
            "has actually been on her knees, not as metaphor. The \u201cshrine of your lie\u201d "
            "sounds like something she has kneeled before, not something she has only "
            "observed from outside."
        ),
    ),
)


TAKE_ME_TO_CHURCH_CITATIONS: Tuple[Citation, ...] = (
    Citation(1,
        "https://www.lyriclab.net/blog/hozier-take-me-to-church-meaning-and-songwriting-analysis/",
        "Lyriclab \u2014 \u201cTake Me to Church\u201d meaning and songwriting analysis"),
    Citation(2,
        "https://www.rollingstone.com/music/music-news/behind-hoziers-unlikely-rise-60949/2/",
        "Rolling Stone \u2014 Behind Hozier\u2019s unlikely rise"),
    Citation(3,
        "https://journals.openedition.org/etudesirlandaises/13453?lang=en",
        "\u00c9tudes irlandaises \u2014 reading the music video"),
    Citation(4,
        "https://www.youtube.com/watch?v=ysv84KEZXWw",
        "Demi Lovato \u2014 \u201cTake Me to Church\u201d (BBC Radio 1 Live Lounge, 2015)"),
    Citation(5,
        "https://www.motherjones.com/politics/2014/07/demi-lovato-gay-rights-video-marriage-equality-human-rights-campaign/",
        "Mother Jones \u2014 Demi Lovato on gay marriage and equality"),
)


# ---------------------------------------------------------------------------
# Jolene --- Dolly Parton (1973) / Lil Nas X (2021)
# ---------------------------------------------------------------------------
JOLENE_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Dolly Parton (1973)",
        body=(
            "Dolly Parton wrote \u201cJolene\u201d in 1973 about a bank teller who flirted with her "
            "husband, Carl Thomas Dean, shortly after they were married.[1] The repetition of "
            "\u201cJolene\u201d in the chorus acts as a desperate, almost hypnotic mantra, with each "
            "utterance sounding more pleading than the last. What makes Parton\u2019s original "
            "version so effective is its tempo. The song moves fast, almost urgently, as if "
            "she is chasing someone, as if there is still time. The tempo mirrors the "
            "singer\u2019s racing heart and anxious state of mind. Every word of the plea, \u201cI\u2019m "
            "begging of you, please don\u2019t take my man,\u201d comes from someone who still believes "
            "the outcome is undecided, who believes Jolene might actually listen, who still "
            "has something left to lose that hasn\u2019t been lost yet.\n\n"
            "That urgency is the engine of the original. The willingness to beg another woman, "
            "directly and openly, is what gives the song its vulnerability. The entire song is "
            "an exercise in emotional honesty, portraying vulnerability rather than anger. The "
            "singer is not angry at Jolene, but rather, she is afraid of her. She acknowledges "
            "Jolene\u2019s beauty with something close to admiration, \u201cyour beauty is beyond "
            "compare\u201d and that admiration is what drives the fear. The message of the song "
            "may be interpreted as you cannot be angry at someone you see as simply better "
            "than you."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame captures Dolly Parton singing \u201cJolene\u201d with her band in 1988 on her "
            "TV variety show at the Grand Ole Opry[2]. She sings donning her signature "
            "towering blonde hair, wearing a rhinestone-studded costume, and right before "
            "singing about insecurity and inadequacy, uses self-deprecating humor. The Grand "
            "Ole Opry is not simply just a concert hall, but it is a temple of country music\u2019s "
            "institutional history, and Dolly Parton has been a member since 1969, so "
            "performing \u201cJolene\u201d on that stage is very meaningful."
        ),
        image="exhibits/frames/jolene_dolly.png",
        image_caption="Dolly Parton \u2014 Grand Ole Opry, 1988",
    ),
    EssaySection(
        heading="II. Reperformance: Lil Nas X (2021)",
        body=(
            "Lil Nas X covered the song at BBC Radio 1\u2019s Live Lounge in September 2021, just "
            "after the release of his debut album Montero[3]. He sings in a deep baritone over "
            "a sparse rock arrangement, delivering an impactful gender-flipping rendition of "
            "Dolly Parton\u2019s song. The pronouns stay unchanged as he sings every word in the "
            "lyrics of the original version, but his version describes a love triangle between "
            "himself, a male partner, and a straight woman, and lyrics like \u201cI can easily "
            "understand how you could easily take my man\u201d become laced with themes of queer "
            "yearning and the harmful impact of heterosexual normativity. A straight woman "
            "pleading with another straight woman not to steal her man is a story about "
            "romantic competition. A gay Black man pleading with a straight woman not to steal "
            "his man is a story about the way heterosexuality is treated as a default, an "
            "inevitability that queer love has to fight against just to exist."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame shows Lil Nas X singing \u201cJolene\u201d at BBC Radio 1\u2019s Live Lounge "
            "decorated with floral arrangements. His warm low register voice combined with the voices of the backup singers and the "
            "live instruments of the band helps change the meaning of the song and give the "
            "song a new narrative. The sound of the instruments are very soft, and his vocal "
            "delivery gives \u201cJolene\u201d a sinister feeling that serves as a twist to the song."
        ),
        image="exhibits/frames/jolene_lilnasx.png",
        image_caption="Lil Nas X \u2014 BBC Radio 1 Live Lounge, 2021",
    ),
    EssaySection(
        heading="III. Synthesis and Comparison",
        body=(
            "Dolly Parton\u2019s version sounds like someone trying to prevent something. Lil Nas "
            "X\u2019s version sounds like someone recounting something that has already happened, "
            "or will happen, and cannot be stopped. The desperation becomes grief. He is not "
            "asking Jolene to spare him and the listener is left wondering what he will do to "
            "Jolene if she took his man. The line \u201cplease don\u2019t take him just because you "
            "can\u201d carries a different weight when the line is about the structural advantage "
            "of being the woman a man was always \u201csupposed\u201d to end up with in a "
            "heteronormative society that works in their favor. Jolene doesn\u2019t have to try. "
            "Dolly Parton sings against a rival. Lil Nas X sings against a world that was "
            "never built for him to win."
        ),
    ),
)


JOLENE_CITATIONS: Tuple[Citation, ...] = (
    Citation(1,
        "https://www.biography.com/musicians/a60266702/jolene-dolly-parton-inspiration-meaning",
        "Biography.com \u2014 the inspiration for \u201cJolene\u201d"),
    Citation(2,
        "https://www.youtube.com/watch?v=L0eeSoU35wM",
        "Dolly Parton \u2014 \u201cJolene\u201d at the Grand Ole Opry (1988)"),
    Citation(3,
        "https://www.youtube.com/watch?v=RWjnC8HSRdU",
        "Lil Nas X \u2014 \u201cJolene\u201d (BBC Radio 1 Live Lounge, 2021)"),
)


# ---------------------------------------------------------------------------
# Wing II essays --- Paris, True Colors, Drivers License
# ---------------------------------------------------------------------------
PARIS_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: The Chainsmokers (2017)",
        body=(
            "Released in January 2017, \u201cParis\u201d came out as the lead single from The "
            "Chainsmokers\u2019 debut studio album Memories\u2026Do Not Open[1]. According to the "
            "duo[2], the song was written late one night in Stockholm, just days after a visit "
            "to Paris, beginning with the opening line \u201cwe were staying in Paris\u201d and just "
            "building on to the song from there. Although the lyrics can be read as a vague "
            "romantic vignette, the duo has explained the song is inspired by something more "
            "personal, specifically by Drew Taggart\u2019s (a member of the Chainsmokers) "
            "childhood friend who had been battling a drug addiction for several years at that "
            "point. Taggart had only learned about the addiction secondhand, through their "
            "families\u2019 closeness, while the friend would avoid the subject all together when "
            "they would catch up through Facebook messages. The duo prescribed the song as a "
            "metaphor for the gap between how someone presents themselves and the difficulty "
            "of what they are actually living through, projecting an image of being somewhere "
            "idealized and untroubled, while sensing the worry of those watching from the "
            "outside. In this context, the song is about escaping from reality into a fantasy "
            "of being elsewhere with someone else. Thus the chorus\u2019s iconic lines\u2014\u2014\u201cIf we "
            "go down, then we go down together\u201d\u2014\u2014is meant to evoke a private, almost doomed "
            "romanticism between two people. The \u201cWe\u201d in the song is of two people, "
            "descending together into a shared fantasy, which is why most people think the "
            "song is so often read as a portrait of the fragility of young romance."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The accompanying music video[3] reinforces the song\u2019s core metaphor of escape. "
            "In this frame in particular, a young woman with long blonde hair leans out of an "
            "open window of her home, eyes closed, head tilted back, hair caught mid-motion in "
            "the wind, and moth hands spread out. Behind her stretches a vast, hazy image of "
            "the city under a soft pale blue sky. She is positioned above the city leaning out "
            "into the open air with no visible hesitation\u2014\u2014a posture that reads as "
            "fearlessness but also objectively the posture on the edge of a fall. The lighting "
            "is warm and overexposed, almost dreamlike. Her closed eyes and parted lips "
            "suggests her agenda is not to look at the city, but more so absorbed in a "
            "boundary of the interior (within the house) and exterior (outside the house). "
            "The frame encompasses what it means to be in a space where the line between "
            "reality and fantasy becomes blurred, and one\u2019s boundaries are no longer fully "
            "visible. There is a danger involved here as the girl is suspended above the city, "
            "but the chorus\u2019s central line of \u201cIf we go down, then we go down together\u201d is "
            "visible in this staging where she is no longer afraid to fall."
        ),
        image="exhibits/frames/paris_chainsmokers.png",
        image_caption="The Chainsmokers \u2014 \u201cParis\u201d (2017, music video, 1:56)",
    ),
    EssaySection(
        heading="II. Reperformance: TikTok and the Overturning of Roe v. Wade (2022)",
        body=(
            "In June 2022, the United States Supreme Court issued its decision in Dobbs v. "
            "Jackson Women\u2019s Health Organization, overturning Roe v. Wade and removing the "
            "federal interpretation of women\u2019s constitutional right to abortion[4]. Within "
            "days, Tiktok users\u2014\u2014hoping to invoke feelings of solidarity\u2014\u2014began posting "
            "videos lip-syncing one specific line from \u201cParis\u201d: \u201cIf we go down, then we go "
            "down together\u201d. The song had already been a hit years earlier when it was "
            "released, but now it has become a coordinated piece of political infrastructure. "
            "Tiktokers used the sound offer rides across state lines, guest bedrooms in one\u2019s "
            "house, and informal travel networks for women seeking abortion access[5]. The "
            "hashtag #ifwegodownthenwegodowntogether accumulated over 33 million views within "
            "four days of the ruling[6]. The main chorus, originally interpreted as a private "
            "escape between two people, was being repurposed in real time as a public "
            "political pledge of mutual aid."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame shown here is one of the most-circulated examples of this repurposing "
            "with 4.3 million views total on this one Tiktok duet posted by The "
            "Chainsmokers[7]. On the right side of this duet is a young woman crying openly "
            "into the camera, and her caption reads: \u201cDo you think The Chainsmokers knew "
            "their little pop song about Paris would be used to fight for reproductive rights? "
            "Truly, fuck the Supreme Court.\u201d On the left side of the duet is Drew Taggart of "
            "The Chainsmokers duo, staring back, and although no caption is on the video, the "
            "caption under the video reads: \u201cwe did not see that coming but are glad that "
            "something we wrote is being used to support a cause we believe in \U0001f90d.\u201d Through "
            "this split-screen format, the original artist and a stranger appear side-by-side "
            "in the same frame, experiencing the same song but now in a different context "
            "than what the original artist had created the song for. The TikToker is grieving "
            "a Supreme Court ruling, and Taggart is responding to that grief in "
            "solidarity\u2014\u2014giving space and acknowledging a meaning of the lyrics that he did "
            "not intend to write."
        ),
        image="exhibits/frames/paris_tiktok.png",
        image_caption="@thechainsmokers TikTok duet \u2014 \u201cParis\u201d (2022)",
    ),
    EssaySection(
        heading="III. Synthesis and Comparison",
        body=(
            "This is a reperformance without a second performer. No one is re-recording "
            "\u201cParis,\u201d and The Chainsmoker\u2019s original studio track is the only recording "
            "used in circulation under the hashtag; what changed then is not the audio but "
            "the use of the audio. The performers in this case are millions of TikTok users. "
            "The key transformation is happening at the level of the pronoun \u201cwe.\u201d In the "
            "original, \u201cwe\u201d refers to two people inside a private (romantic) fantasy, a "
            "couple disappearing into an idealized Paris together. In this reperformance, "
            "\u201cwe\u201d refers to a movement: a network of strangers across state lines extending "
            "material help and support to other strangers facing political and medical "
            "precarity. The lyrics: \u201cif we go down, then we go down together\u201d undergoes a "
            "corresponding shift. In the original, \u201cgoing down\u201d can be interpreted as "
            "romantic fatalism, whereas in this reperformance it means political solidarity; "
            "the people falling together are being pushed by a Supreme Court ruling, and "
            "\u201ctogether\u201d reaffirms a vow of mutual aid rather than romantic loyalty. The "
            "lyrics did not change at all, but because of the context, the referents of the "
            "lyrics have changed completely. Another aspect worth noting is Tiktok\u2019s unique "
            "setup as a lip-syncing platform. Its format allows millions of individuals to "
            "\u201cperform\u201d or \u201crepurpose\u201d a song, all for the context they wish to use the "
            "song in, along with their own captions they wish to add on. This piece shows how "
            "a song\u2019s reperformance(s) can be distributed, political, participatory, and "
            "ongoing."
        ),
    ),
)


PARIS_CITATIONS: Tuple[Citation, ...] = (
    Citation(1, "https://genius.com/The-chainsmokers-paris-lyrics",
             "Genius \u2014 \u201cParis\u201d lyrics, from Memories\u2026Do Not Open"),
    Citation(2, "https://www.facebook.com/thechainsmokers/posts/1462049853827400",
             "The Chainsmokers \u2014 Facebook post on writing \u201cParis\u201d"),
    Citation(3, "https://youtu.be/fRNkQH4DVg8",
             "The Chainsmokers \u2014 \u201cParis\u201d official music video"),
    Citation(4, "https://www.supremecourt.gov/opinions/21pdf/19-1392_6j37.pdf",
             "U.S. Supreme Court \u2014 Dobbs v. Jackson Women\u2019s Health Organization (2022)"),
    Citation(5,
        "https://www.washingtonpost.com/nation/2022/06/30/tiktok-the-chainsmokers-abortion-roe/",
        "Washington Post \u2014 TikTok turns The Chainsmokers into a Roe-protest anthem"),
    Citation(6,
        "https://corq.studio/insights/influencers-and-social-media-react-to-the-roe-v-wade-ruling/",
        "Corq Studio \u2014 Influencers and social media react to the Roe v. Wade ruling"),
    Citation(7,
        "https://www.tiktok.com/@thechainsmokers/video/7113999336089865515",
        "@thechainsmokers \u2014 TikTok duet (2022)"),
)


TRUE_COLORS_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Cyndi Lauper (1986)",
        body=(
            "Released in August 1986, the song was originally written in the same year by "
            "Billy Steinberg and Tom Kelly\u2014\u2014songwriters who have made other songs such as "
            "Madonna\u2019s \u201cLike a Virgin,\u201d Heart\u2019s \u201cAlone,\u201d and \u201cEternal Flame.\u201d[1] The "
            "motivation for this song, according to Steinberg is the song was inspired by his "
            "own mother, and the demo he and Kelly produced were rooted in gospel-ballad "
            "traditions that were piano-driven, churchy, and emotionally direct[2]. The song "
            "was then given to Cyndi Lauper, and what Lauper did with the demo was unexpected: "
            "rather than copy the gospel-balled arrangement, she had changed it completely. "
            "Steinberg later recalled that Lauper had \u201ccompletely dismantled that sort of "
            "traditional arrangement and came up with something that was breathtaking and "
            "stark\u201d\u2014\u2014creating a sparse, almost ambient production built around her whispery "
            "vocals[3]. Lauper later talks about her artistic choices for recording the song, "
            "which in a way is a reperformance on her part by changing the song from the "
            "original. She was carrying private grief into the recording booth as shortly "
            "before she had heard the demo, her close friend Gregory Natal had died of "
            "AIDs[4]. When she sang the song\u2019s quietest sections, she had been thinking of "
            "him. In a later interview with 60 Minutes: \u201cI realized it had to be a voice that "
            "whispers to you. A voice that\u2019s almost childlike so it will speak to the "
            "softest, most gentle part of a human being\u2026 It\u2019s a voice whispering to you, "
            "telling you it\u2019s going to be OK.\u201d[5] To many, the song touches them because the "
            "lyrics and Lauper\u2019s sincere vocals emphasize the message of a friend reassuring "
            "another friend that they are seen and loved as they are, even if one did not "
            "know of the specific grief Lauper was carrying."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "In this frame of the accompanying music video[6] reinforces the song\u2019s themes of "
            "being seen for who one truly is. Lauper stands in a surreal, dreamlike landscape "
            "of pale stone, candles, and what appears to be a beach or desert at dusk. She "
            "wears an elaborate beaded headdress that rises above her like a chandelier, with "
            "extravagant strings of pearls and gold draped across her bare shoulder, holding a "
            "large seashell in her hands. Her clothing appears to be gold-beaded that falls "
            "loosely across her chest, paired with a sequined gold skirt. Much of her skin is "
            "left bare, which can be read as a sign of vulnerability: the openness of a friend "
            "you want you trust enough to be seen by. Yet the towering headdress and "
            "extravagant style balance that vulnerability with a self-assuredness that comes "
            "off confident and authoritative."
        ),
        image="exhibits/frames/true_colors_lauper.png",
        image_caption="Cyndi Lauper \u2014 \u201cTrue Colors\u201d (1986, music video, 1:43)",
    ),
    EssaySection(
        heading="II. Reperformance: AIDS Crisis & LGBTQ+ Anthem (2008 - Present)",
        body=(
            "The original song already contained two layers of authorship: Steinberg and "
            "Kelly wrote it, and then Lauper transformed it through her grief over Natal. The "
            "third layer happened in the years after the release of the original song. The "
            "LGBTQ+ community\u2014devastated by the AIDS crisis and confronted daily with social, "
            "medical, and political abandonment\u2014took up \u201cTrue Colors\u201d as an anthem. The "
            "song\u2019s lyrics and original message made this transition from original context to "
            "reperformance almost seamless: a song about being seen past the surface, about "
            "being loved for who you truly are, in an era where there was a lot of stigma and "
            "misinformation about the LGBTQ+ community. In this context, the \u201ccolors\u201d of the "
            "title became associated with the colors of the rainbow pride flag, even though "
            "Steinberg and Kelly had not written the song with that meaning in mind. What "
            "makes this reperformance unique is that Lauper had personal ties to this "
            "reinterpretation and usage of her song, and thus although when she released it "
            "she had not expected it to become an LGBTQ+ anthem, she not only accepted it but "
            "also actively participated in the reperformance process. In 2008, she founded "
            "the True Colors Fund (now True Colors United), an organization advocating for "
            "LGBTQ+ youth, particularly the disproportionately high number of LGBTQ+ youth "
            "suffering from homelessness in the United States[7]."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "This frame, taken from Lauper\u2019s performance of \u201cTrue Colors\u201d at the 2025 Rock "
            "& Roll Hall of Fame Induction Ceremony,[8] stages the song nearly forty years "
            "after its release in a setup that aligns itself with the LGBTQ+ community it has "
            "come to advocate for. Lauper here is shown in profile, her short, voluminous, "
            "and tousled hair backlit and her face partially hidden in shadow against a wash "
            "of stage light. Behind her is a vast arena audience, and the stage itself is "
            "bathed in the colors of the rainbow to symbolize the pride flag. The lightly "
            "design is not just a pure aesthetic choice, it visually completes the song\u2019s "
            "reclamation, as this frame stages her inside the community that resonated the "
            "most with the song in the past decades. Rather than performing the song for an "
            "audience, Lauper has made it clear this song is now one with the audience as she "
            "has dedicated the stage design to honor the LGBTQ+ community, alongside her "
            "other works of advocacy. The bareness and fragility of the 1986 video is gone, "
            "and instead there is pure strength and optimism in this frame\u2014\u2014the image of "
            "singer in profile against a rainbow, metaphorically surrounded by the community "
            "her song has made a mark on."
        ),
        image="exhibits/frames/true_colors_rrhof.png",
        image_caption="Cyndi Lauper \u2014 Rock & Roll Hall of Fame Induction, 2025 (0:01)",
    ),
    EssaySection(
        heading="III. Synthesis and Comparison",
        body=(
            "The repurposing of this song can almost parallel a similar famous case of Gloria "
            "Gaynor\u2019s \u201cI Will Survive,\u201d in which Gaynor\u2019s song has also been repurposed "
            "for an LGBTQ+ narrative.[9] However, there is a large difference in how the "
            "artists themselves have participated in the reinterpretation. For the most part, "
            "Gaynor has decided to stray away from LGBTQ+ activism, and has rarely spoken "
            "about the LGBTQ+ community, choosing a stance of neutrality and claiming that "
            "she is \u201cnot a political person.\u201d[10] Lauper on the other hand, had already "
            "connected emotions of the song to AIDs during the recording, and her later "
            "activism and support of the LGBTQ+ community further cements her active role in "
            "the reinterpretation of the song. Her activism as the original singer of the "
            "song has inherently institutionalized the reclamation. While Gaynor may have "
            "been neutral about the reclamation of her song where it simply evolved into an "
            "LGBTQ+ anthem because the song itself resonated with the community, Lauper has "
            "been a continuous participant of this repurposing, constantly giving back to "
            "the community and acknowledging the importance of this song for them."
        ),
    ),
)


TRUE_COLORS_CITATIONS: Tuple[Citation, ...] = (
    Citation(1,
        "https://www.smoothradio.com/features/the-story-of/true-colours-cyndi-lauper-lyrics-meaning/",
        "Smooth Radio \u2014 The story of \u201cTrue Colors\u201d"),
    Citation(2,
        "https://www.songfacts.com/facts/cyndi-lauper/true-colors",
        "Songfacts \u2014 Cyndi Lauper, \u201cTrue Colors\u201d"),
    Citation(3,
        "https://www.smoothradio.com/features/the-story-of/true-colours-cyndi-lauper-lyrics-meaning/",
        "Smooth Radio \u2014 Steinberg on Lauper\u2019s reworking"),
    Citation(4,
        "https://www.smoothradio.com/features/the-story-of/true-colours-cyndi-lauper-lyrics-meaning/",
        "Smooth Radio \u2014 Lauper, Gregory Natal, and the recording"),
    Citation(5,
        "https://stereogum.com/2112347/the-number-ones-cyndi-laupers-true-colors/columns/the-number-ones",
        "Stereogum, \u201cThe Number Ones\u201d \u2014 Cyndi Lauper, \u201cTrue Colors\u201d"),
    Citation(6,
        youtube_search("Cyndi Lauper True Colors official music video 1986"),
        "Cyndi Lauper \u2014 \u201cTrue Colors\u201d official music video (YouTube search)"),
    Citation(7, "https://truecolorsunited.org/",
             "True Colors United \u2014 about the organization"),
    Citation(8,
        "https://www.youtube.com/watch?v=hUkL-EwEPBA",
        "Cyndi Lauper \u2014 \u201cTrue Colors\u201d, Rock & Roll Hall of Fame Induction (2025)"),
    Citation(9,
        "https://www.npr.org/2019/09/24/763518201/gloria-gaynor-i-will-survive-american-anthem",
        "NPR \u2014 Gloria Gaynor on \u201cI Will Survive\u201d"),
    Citation(10,
        "https://www.primetimer.com/news/gloria-gaynor-kennedy-center-honor-draws-controversy",
        "Primetimer \u2014 Gloria Gaynor Kennedy Center Honor controversy"),
)


DRIVERS_LICENSE_ESSAY: Tuple[EssaySection, ...] = (
    EssaySection(
        heading="I. Original Context: Olivia Rodrigo (2021)",
        body=(
            "Olivia Rodrigo released \u201cdrivers license\u201d on January 8, 2021[1] and the song "
            "became a cultural phenomenon almost immediately as a heartbreak ballad, "
            "capturing the heartbreak experienced by the generation of teenagers. The song "
            "is built from a sense of minimalism and piano, and the lyrics capture details of "
            "teenage grief. The impact of the song largely comes from the artist being 17 "
            "years old and her debut single, writing about the person she wasn\u2019t over yet "
            "and the pain she feels for the first time. The sound of a car\u2019s ignition and "
            "door chime at the beginning of the song immediately places the listener inside "
            "the intimate setting of the car with Olivia Rodrigo."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The video[2] starts with viewers seeing a road at night, seen through a "
            "windshield, headlights barely illuminating the road ahead. Later, a scene "
            "involves memories of old photos and videos being projected onto Olivia "
            "Rodrigo\u2019s back, representing something she carries on her body. The video "
            "utilizes a vignette aesthetic and depicts her healing from heartbreak. She "
            "receives her driver\u2019s license in the video, but instead of going to her old "
            "lover\u2019s house like she used to dream of, she finds herself aimlessly cruising "
            "suburban side streets. The driver\u2019s license is supposed to represent a newfound "
            "freedom and a new chapter. It was a moment the girl was supposed to share with "
            "her partner, and achieving it alone highlights her heartbreak. She has the "
            "freedom to go anywhere, and she drives in circles through an empty suburb at "
            "night, past a street she can name but not stop on. The color palette features "
            "purple, blue and black tint that symbolize her emotions. During the song\u2019s "
            "bridge, the color temperature shifts to become warmer. Toward the end, she "
            "stands on a dark street alone, with only a street light to keep her company, "
            "and the video ends in the dark as it began."
        ),
        image="exhibits/frames/dl_olivia.png",
        image_caption="Olivia Rodrigo \u2014 \u201cdrivers license\u201d (2021, music video)",
    ),
    EssaySection(
        heading="II. Reperformance: Rick Astley (2024)",
        body=(
            "Rick Astley sings \u201cdrivers license\u201d three years after its release as a "
            "57-year-old British pop star best known for his 1987 dance hit. He sings in BBC "
            "Radio 2\u2019s Piano Room[3] with the original lyrics, and stands before a full "
            "concert orchestra. He performs in baritone with the BBC Concert Orchestra and a "
            "pair of back-up singers. Rick singing a breakup song catered for the GenZ "
            "audience makes the feeling experienced by teenage heartbreak more universalized. "
            "His version utilizes a full orchestral arrangement and dramatic swells, and Rick "
            "Astley\u2019s voice is deep and controlled, a contrast to Olivia Rodrigo\u2019s voice "
            "who sounds overwhelmed by feeling for the first time. The song stops being about "
            "the chaos of first heartbreak and starts being about long-term grief, so it ages "
            "a song meant for adolescence. The lyrics about driving alone past someone\u2019s "
            "house lands differently in an older, more experienced voice because they feel "
            "to be from a different time when he is looking back."
        ),
    ),
    EssaySection(
        heading="Frame",
        body=(
            "The frame shows Rick Astley singing \u201cdrivers license\u201d in BBC Radio 2\u2019s Piano "
            "Room. His low register voice combined with the live instruments of the full "
            "orchestra helps change the meaning of the song. The sound of the instruments "
            "are dramatic, and his voice is low and deep, providing a contrast to the "
            "original version."
        ),
        image="exhibits/frames/dl_rick.png",
        image_caption="Rick Astley \u2014 BBC Radio 2 Piano Room, 2024",
    ),
)


DRIVERS_LICENSE_CITATIONS: Tuple[Citation, ...] = (
    Citation(1, "https://genius.com/Olivia-rodrigo-drivers-license-lyrics",
             "Genius \u2014 Olivia Rodrigo, \u201cdrivers license\u201d lyrics"),
    Citation(2, "https://youtu.be/ZmDBbnmKpqQ",
             "Olivia Rodrigo \u2014 \u201cdrivers license\u201d official music video"),
    Citation(3, "https://www.youtube.com/watch?v=6V8luIR9zFo",
             "Rick Astley \u2014 \u201cdrivers license\u201d (BBC Radio 2 Piano Room)"),
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
            citations=WAKE_ME_UP_CITATIONS,
        ),
        Exhibit(
            song="Take Me to Church",
            art_key="take_me_to_church",
            original=Performance(
                performer="Hozier",
                year="2014",
                setting=(
                    "Recorded in his attic in County Wicklow at 2 a.m. in 2013. "
                    "Critique of the Catholic Church\u2019s homophobia, dressed as a love song."
                ),
                register="Outward rage. Devotion as a weapon turned back on the institution.",
                media=(
                    MediaLink(
                        "Hozier \u2014 Take Me to Church (2014, music video)",
                        youtube_search("Hozier Take Me to Church official music video"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Demi Lovato",
                    year="2015",
                    setting=(
                        "BBC Radio 1\u2019s Live Lounge. Same lyrics, including the original "
                        "pronouns; band and two backing singers."
                    ),
                    register=(
                        "Inward rawness. A love song with the political critique softened "
                        "into solidarity and confession."
                    ),
                    media=(
                        MediaLink(
                            "Demi Lovato \u2014 Take Me to Church (BBC Live Lounge, 2015)",
                            "https://www.youtube.com/watch?v=ysv84KEZXWw",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Hozier wrote \u201cTake Me to Church\u201d as a protest against an institution; "
                "Lovato sang it back as a personal confession. The lyrics did not change \u2014 "
                "even the pronouns held \u2014 but the rage moved from outside to inside."
            ),
            essay=TAKE_ME_TO_CHURCH_ESSAY,
            citations=TAKE_ME_TO_CHURCH_CITATIONS,
        ),
        Exhibit(
            song="Jolene",
            art_key="jolene",
            original=Performance(
                performer="Dolly Parton",
                year="1973",
                setting=(
                    "Country single inspired by a bank teller flirting with Parton\u2019s "
                    "husband. Fast tempo, hypnotic chorus."
                ),
                register=(
                    "Vulnerable, urgent. The plea of a woman who still believes the outcome "
                    "is undecided."
                ),
                media=(
                    MediaLink(
                        "Dolly Parton \u2014 Jolene at the Grand Ole Opry (1988)",
                        "https://www.youtube.com/watch?v=L0eeSoU35wM",
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Lil Nas X",
                    year="2021",
                    setting=(
                        "BBC Radio 1\u2019s Live Lounge. Sparse rock arrangement; gender-flipping "
                        "rendition with the pronouns left intact."
                    ),
                    register=(
                        "Sinister, resigned. A queer Black man pleading with a straight woman "
                        "in a heteronormative world."
                    ),
                    media=(
                        MediaLink(
                            "Lil Nas X \u2014 Jolene (BBC Live Lounge, 2021)",
                            "https://www.youtube.com/watch?v=RWjnC8HSRdU",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Parton sings against a rival; Lil Nas X sings against a world that was "
                "never built for him to win. The plea is the same; the structural fight "
                "behind it is not."
            ),
            essay=JOLENE_ESSAY,
            citations=JOLENE_CITATIONS,
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
            song="Paris",
            art_key="paris",
            original=Performance(
                performer="The Chainsmokers",
                year="2017",
                setting=(
                    "Lead single from Memories\u2026Do Not Open. Written in Stockholm "
                    "after a trip to Paris; addiction-tinged escapist romance."
                ),
                register="Private, almost doomed romanticism between two people.",
                media=(
                    MediaLink(
                        "The Chainsmokers \u2014 Paris (2017, music video)",
                        "https://youtu.be/fRNkQH4DVg8",
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="TikTok / overturning of Roe v. Wade",
                    year="2022",
                    setting=(
                        "After Dobbs v. Jackson, TikTok users lip-sync \u201cif we go down, "
                        "then we go down together\u201d to coordinate cross-state abortion "
                        "support. Same audio, no second performer."
                    ),
                    register=(
                        "Public, political. A pledge of mutual aid sung in millions of "
                        "duets."
                    ),
                    media=(
                        MediaLink(
                            "@thechainsmokers TikTok duet (2022)",
                            "https://www.tiktok.com/@thechainsmokers/video/7113999336089865515",
                        ),
                        MediaLink(
                            "Washington Post coverage of the TikTok repurposing",
                            "https://www.washingtonpost.com/nation/2022/06/30/tiktok-the-chainsmokers-abortion-roe/",
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "The audio file did not change at all. What changed is the pronoun "
                "\u201cwe\u201d \u2014 from a couple sliding into a fantasy of Paris to a network "
                "of strangers extending help across state lines. Same recording; "
                "completely different referents."
            ),
            essay=PARIS_ESSAY,
            citations=PARIS_CITATIONS,
        ),
        Exhibit(
            song="True Colors",
            art_key="true_colors",
            original=Performance(
                performer="Cyndi Lauper",
                year="1986",
                setting=(
                    "Steinberg & Kelly demo \u2014 a piano gospel ballad \u2014 reworked by Lauper "
                    "into a sparse, whispered production while she grieved the AIDS-related "
                    "death of her friend Gregory Natal."
                ),
                register=(
                    "Tender, almost childlike. A friend telling another friend: I see you."
                ),
                media=(
                    MediaLink(
                        "Cyndi Lauper \u2014 True Colors (1986, music video)",
                        youtube_search("Cyndi Lauper True Colors official music video 1986"),
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="LGBTQ+ communities & Lauper's later activism",
                    year="2008\u2013present",
                    setting=(
                        "Adopted as an LGBTQ+ anthem during and after the AIDS crisis. "
                        "Lauper founds the True Colors Fund (now True Colors United) in "
                        "2008; performs the song under rainbow lighting at the 2025 Rock & "
                        "Roll Hall of Fame Induction."
                    ),
                    register=(
                        "Communal, declarative. Recognition turned into mutual care and "
                        "advocacy."
                    ),
                    media=(
                        MediaLink(
                            "Cyndi Lauper \u2014 True Colors, RnRHOF Induction (2025)",
                            "https://www.youtube.com/watch?v=hUkL-EwEPBA",
                        ),
                        MediaLink(
                            "True Colors United (organization)",
                            "https://truecolorsunited.org/",
                            kind="article",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Steinberg and Kelly wrote it; Lauper transformed it through private grief; "
                "the LGBTQ+ community took it back as a public anthem; Lauper, unlike many "
                "original artists, walked into the reclamation and stayed there."
            ),
            essay=TRUE_COLORS_ESSAY,
            citations=TRUE_COLORS_CITATIONS,
        ),
        Exhibit(
            song="drivers license",
            art_key="drivers_license",
            original=Performance(
                performer="Olivia Rodrigo",
                year="2021",
                setting=(
                    "Debut single. Piano-led teen heartbreak ballad opening on the chime "
                    "and ignition of a car. Rodrigo is 17."
                ),
                register=(
                    "First-time grief. Overwhelmed, intimate, present-tense."
                ),
                media=(
                    MediaLink(
                        "Olivia Rodrigo \u2014 drivers license (2021, music video)",
                        "https://youtu.be/ZmDBbnmKpqQ",
                    ),
                ),
            ),
            reperformances=(
                Performance(
                    performer="Rick Astley",
                    year="2024",
                    setting=(
                        "BBC Radio 2 Piano Room. A 57-year-old British pop star sings a "
                        "GenZ heartbreak ballad with the BBC Concert Orchestra and two "
                        "backing singers."
                    ),
                    register=(
                        "Long-term grief. Deep baritone, looking back."
                    ),
                    media=(
                        MediaLink(
                            "Rick Astley \u2014 drivers license (BBC Radio 2 Piano Room, 2024)",
                            "https://www.youtube.com/watch?v=6V8luIR9zFo",
                        ),
                    ),
                ),
            ),
            curator_note=(
                "Rodrigo sings as if the heartbreak is happening; Astley sings as if it "
                "happened a long time ago. The lyrics do not move; the lifespan that "
                "delivers them does."
            ),
            essay=DRIVERS_LICENSE_ESSAY,
            citations=DRIVERS_LICENSE_CITATIONS,
        ),
        # Wing II's prior exhibits (I Will Survive, Born in the U.S.A.,
        # Dreams) were retired when the final analyses landed; the new
        # set above (Paris, True Colors, drivers license) replaces them.
    ),
)


WINGS: Tuple[Wing, ...] = (WING_I, WING_II)


def wing_by_key(key: str) -> Wing:
    for w in WINGS:
        if w.key == key:
            return w
    raise KeyError(key)


# ---------------------------------------------------------------------------
# Reading Room — the foundational texts the museum is built on.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReadingEntry:
    """One inspectable item in the Reading Room.

    ``key`` is a stable id used by the lobby/scene to address the entry.
    ``sections`` is a tuple of (subheading, body) pairs. Bodies may use
    Chicago-style ``[1]`` markers that resolve against ``citations``.
    """
    key: str
    title: str
    intro: str
    sections: Tuple[Tuple[str, str], ...] = ()
    citations: Tuple[Citation, ...] = ()


READING_ROOM_REFERENCES: Tuple[Citation, ...] = (
    Citation(
        1,
        "https://archive.org/details/frameanalysisess0000goff",
        "Goffman, Erving. 1974. \u201cFrame Analysis: An Essay on the Organization "
        "of Experience.\u201d Harper & Row.",
    ),
    Citation(
        2,
        "https://doi.org/10.9783/9780812200928",
        "Schechner, Richard, and Victor W. Turner. 1985. \u201cBetween Theater & "
        "Anthropology.\u201d 1st ed. University of Pennsylvania Press.",
    ),
    Citation(
        3,
        "https://doi.org/10.1515/9780822383376-005",
        "Coyle, Michael. 2020. \u201cHijacked Hits and Antic Authenticity: Cover "
        "Songs, Race, and Postwar Marketing.\u201d In Rock Over the Edge, edited by "
        "Denise Fulbrook, Ben Saunders, and Roger Beebe. Duke University Press.",
    ),
)


READING_THESIS = ReadingEntry(
    key="thesis",
    title="Curatorial Thesis",
    intro=(
        "A song is never a fixed object, even when it has been recorded, "
        "published, and distributed among streaming platforms, DVDs, or "
        "records. The lyrics may be identical from one performance to the "
        "next and yet the song does something different each time it is sung "
        "and played simply because even if the song is replayed, the context "
        "that follows and precedes it can never be reconstructed. This museum "
        "takes the different meanings as its subject."
    ),
    sections=(
        (
            "What we treat as the score",
            "We treat the lyrics as essentially a musical score: a recorded "
            "pattern that is documented to be produced, but each time it is "
            "set down somewhere new, it picks up new meaning from its "
            "surroundings and context. What changes between an \u201coriginal\u201d "
            "and a \u201creperformance\u201d is rarely the words, instead it is the "
            "audience the words are sung to, the singer\u2019s body, aesthetic, "
            "instrumentation, political context, the platform, the year, "
            "everything else. Meaning exists in lived context, beyond just "
            "what words on the page may convey.",
        ),
        (
            "Two ways meaning shifts",
            "Across two wings, the museum traces two ways this happens. Wing I "
            "gathers the cases where the same lyrics, sung by a different voice "
            "in a different setting, changes the meaning of the song\u2014\u2014even "
            "when the same lyrics are being performed. Wing II gathers cases "
            "where a song is claimed, repurposed, or sung by someone it wasn\u2019t "
            "originally intended for. Together, the museum is evidence that a "
            "song\u2019s lyrics, once recorded, are stripped from the conditions "
            "that originally gave them meaning and are constantly reabsorbed "
            "into new conditions that give them a different meaning. Each "
            "exhibit is an instance of that movement\u2014\u2014 of lyrics leaving one "
            "frame and arriving in another, where the words are carried through "
            "these frames but not necessarily the meaning.",
        ),
    ),
)


READING_VOCAB = ReadingEntry(
    key="vocab",
    title="Working Vocabulary",
    intro=(
        "The concepts gathered below are not explicitly citations that the "
        "exhibits pull from, instead they are recurring patterns the exhibits "
        "reveal. The information under each song analysis tries to be "
        "extremely specific to the songs and frame being analyzed; however, "
        "we ask visitors to read this section first, then walk through the "
        "museum and watch for moments where a song, a singer, or a context "
        "performs one of these foundational ideas of music covers and "
        "performance. The exhibits are evidence of these concepts and "
        "frameworks, while this vocabulary page defines them."
    ),
    sections=(
        (
            "The Frame  (Erving Goffman, 1974)[1]",
            "Sociologist Erving Goffman uses the word frame to describe the "
            "interpretive schema a listener or viewer brings to an event\u2014\u2014the "
            "set of assumptions that tells them what kind of activity they\u2019re "
            "witnessing and how to interpret it. A frame cannot be equal to "
            "the event or experience itself, however, it provides the viewer "
            "the lens through which they view and experience the event.\n\n"
            "Thus, the same occurrence of anything will be consumed differently "
            "inside and outside of the frame. One example Goffman provides is "
            "the scenario of a loud door being shut, but in the dream, it is "
            "reframed as a gunshot. The source sound did not change, but the "
            "framing did.\n\n"
            "Reperformance works this way, especially in some of the contexts "
            "of Wing II, where the source material sound does not change, but "
            "the context the song is being interpreted has. Furthermore, our "
            "museum relies heavily on taking one snapshot of an entire "
            "performance\u2014\u2014the frame\u2014and identifying cues that instruct "
            "the audience how to hear and interpret the song before it plays. "
            "However, your interpretation of the frame may be very different "
            "from our interpretation, and thus, the meaning of songs and "
            "lyrics will always be determined by interpretations of the "
            "viewer/listener, even when external outside contexts are identical.",
        ),
        (
            "The Strip  (Schechner & Turner, 1985)[2]",
            "Schechner and Turner build on Goffman\u2019s original statement of "
            "\u201cstrip of activity\u201d in Frame Analysis, and argue that no "
            "behavior is ever truly repeated in its original form. To even be "
            "repeated in the first place, a behavior has to be removed from "
            "the situation that first gave it meaning and turn it into a "
            "reproducible pattern or object\u2014\u2014what they refer to as a strip "
            "of behavior.\n\n"
            "Their metaphor is a film: a strip of film records an action, but "
            "once recorded, the strip can be cut, spliced, and projected "
            "anywhere in any order, with no true obligation to the \u201coriginal\u201d "
            "moment that was captured. We argue song lyrics are like this "
            "strip. Once recorded, words can be re-sung in a context that has "
            "nothing to do with what originally inspired or produced them. "
            "Schechner and Turner argue that this is the only way "
            "reperformance is at all possible.\n\n"
            "Thus the museum anchors on their quote: \u201cThe original \u2018truth\u2019 "
            "or \u2018source\u2019 of the behavior may be lost, ignored, or "
            "contradicted\u2014even while this truth or source is apparently being "
            "honored and observed. How the strip of behavior was made, found, "
            "or developed may be unknown or concealed; elaborated; distorted "
            "by myth and tradition.\u201d",
        ),
        (
            "Authenticity as a Performance  (Michael Coyle, 2020)[3]",
            "Coyle argues that one of the things a cover does (especially "
            "across racial or cultural lines) is perform an identity. A cover "
            "stages a claim about the artist in relation to what the original "
            "was. He grounds this in Elvis\u2019s rise to fame in the 1950s, "
            "pointing out that many of Elvis\u2019s recordings were recordings of "
            "older Black material such as Arthur Crudup\u2019s \u201cThat\u2019s All "
            "Right,\u201d Wynonie Harris\u2019s \u201cGood Rockin\u2019 Tonight,\u201d and Junior "
            "Parker\u2019s \u201cMystery Train.\u201d\n\n"
            "Many of these records had faded from the charts, and thus, it can "
            "be argued that rather than trying to compete with these songs, "
            "his covers were meant to revive them. In reviving them, Elvis "
            "positions himself in relation to the original source material. "
            "Coyle notes that Elvis gained fame from Black material not "
            "because he was mistaken for a Black artist, nor did he claim "
            "authenticity, but because audiences could clearly see him for "
            "what he was: a white Southern singer performing music that is "
            "sourced from Black material.\n\n"
            "Thus, Coyle\u2019s more general argument is that \u201cauthenticity\u201d is "
            "a construct of relativism rather than a fact about the singer. "
            "Coyle argues that authenticity through covers is not produced by "
            "the artist singing it (it is not the artist that possesses "
            "authenticity), instead it is a trait generated by performance. "
            "The cover is what provides the credentials of authenticity, and "
            "so he labels the term as the \u201cantic of authenticity,\u201d "
            "reframing authenticity as a stage trick where it is performed "
            "rather than a prior stated fact about the artist.\n\n"
            "This concept is one of the more complex concepts within this "
            "museum so it may help to ground it in a specific case. A good "
            "example of using the cover as a vehicle for identity is Calum "
            "Scott\u2019s 2016 cover of \u201cDancing on My Own\u201d in which he alters "
            "the pronouns to reflect his own sexuality. Coupled with Scott\u2019s "
            "public coming-out narrative, which he has spoken about in "
            "interviews and made central to his artist identity, the cover "
            "becomes the vehicle through which he claims a credential as a "
            "queer artist with a confessional song to sing. No one doubts "
            "Scott\u2019s struggles with his identity and sexuality, but it is "
            "through cover where his identity is able to be publicly attached "
            "to a song. Without the original reference point (Robyn\u2019s "
            "version), the single-word change would not have registered as a "
            "bigger deal.",
        ),
    ),
    citations=READING_ROOM_REFERENCES,
)


READING_QUESTIONS = ReadingEntry(
    key="questions",
    title="Guiding Questions",
    intro=(
        "Now that you have seen the working vocabulary highlight some of the "
        "patterns that will show up across these covers and performances, "
        "what is left while you walk through the museum is your interpretation "
        "for it. As you explore the wings, we want to leave you with some "
        "guiding questions to ask yourself."
    ),
    sections=(
        (
            "On the frame",
            "What does the frame of this performance tell you to expect? "
            "Did it match what you hear in the audio preview?",
        ),
        (
            "On unchanged lyrics",
            "If the lyrics didn\u2019t change a single word here, what features "
            "cause the song to mean something else here?",
        ),
        (
            "On the original artist",
            "What would the original artist make of the new version? Does it "
            "matter what they think? Or has the reproduction / reconstruction "
            "of the song moved beyond their reach?",
        ),
        (
            "On ownership after a reperformance",
            "Whose song is this, after the reperformance? When does a cover "
            "still get associated with the original artist, and when does it "
            "become a stand-alone piece?",
        ),
    ),
)


READING_ENTRIES: Tuple[ReadingEntry, ...] = (
    READING_THESIS, READING_VOCAB, READING_QUESTIONS,
)


def reading_entry_by_key(key: str) -> ReadingEntry:
    for e in READING_ENTRIES:
        if e.key == key:
            return e
    raise KeyError(key)


MUSEUM_THESIS = (
    "You are about to explore the Museum of Reperformance! Before "
    "stepping into the exhibits, head into the Reading Room, and the "
    "information desk there will guide you through the museum\u2019s "
    "thesis, its working vocabulary of the patterns the exhibits return "
    "to, and a set of questions to bring with you as you walk."
)
