"""Centralized audio.

There is no other audio state in the app. Do not call pygame.mixer
elsewhere!
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import pygame


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_DIR = os.path.join(ROOT, "music")

# Any Sound longer than this is rejected as an SFX (sanity check).
MAX_SFX_SECONDS = 8.0

# Dedicated SFX channels. Having a channel per sfx lets each sfx enforce
# "stop before restart" without affecting other SFX.
CHANNEL_CLICK = 1
CHANNEL_OPEN = 2
CHANNEL_FOOTSTEP = 3
CHANNEL_SONG_PREVIEW = 4   # optional in-game audio preview (see play_preview)

_mixer_ok: bool = False
_sfx_cache: Dict[str, Optional[pygame.mixer.Sound]] = {}
_current_music: Optional[str] = None
_music_volume: float = 1.0


def init() -> bool:
    """Initialize the mixer. Safe to call multiple times."""
    global _mixer_ok
    if _mixer_ok:
        return True
    try:
        # 44.1kHz stereo, 512-sample buffer for low-latency SFX.
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        # Reserve channels 0..4 for our named usages so the auto-allocator
        # doesn't hand them out.
        pygame.mixer.set_reserved(5)
        _mixer_ok = True
    except pygame.error:
        _mixer_ok = False
    return _mixer_ok


def _path(relpath: str) -> Optional[str]:
    full = os.path.join(MUSIC_DIR, relpath)
    return full if os.path.isfile(full) else None


# ---------------------------------------------------------------------------
# Music (one track at a time, looping, crossfaded on change)
# ---------------------------------------------------------------------------
def play_music(relpath: str, volume: float = 0.4, fade_ms: int = 600) -> None:
    """Loop ``relpath`` as the single ambient track.

    No-op if the same track is already playing — just adjusts the volume.
    If a different track is playing, it is faded out and replaced.
    Missing files are ignored silently so the game runs without audio assets.
    """
    global _current_music, _music_volume
    if not _mixer_ok:
        return
    p = _path(relpath)
    if not p:
        return

    if _current_music == relpath and pygame.mixer.music.get_busy():
        if abs(_music_volume - volume) > 0.01:
            pygame.mixer.music.set_volume(volume)
            _music_volume = volume
        return

    try:
        pygame.mixer.music.fadeout(fade_ms)
    except pygame.error:
        pass
    try:
        pygame.mixer.music.load(p)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=-1, fade_ms=fade_ms)
        _current_music = relpath
        _music_volume = volume
    except pygame.error:
        _current_music = None


def stop_music(fade_ms: int = 400) -> None:
    global _current_music
    if not _mixer_ok:
        return
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except pygame.error:
        pass
    _current_music = None


def set_music_volume(volume: float) -> None:
    global _music_volume
    if not _mixer_ok:
        return
    _music_volume = max(0.0, min(1.0, volume))
    try:
        pygame.mixer.music.set_volume(_music_volume)
    except pygame.error:
        pass


# ---------------------------------------------------------------------------
# SFX — cached, length-checked, routed through a fixed channel so
# rapid re-triggering always stops the prior voice.
# ---------------------------------------------------------------------------
def _load_sfx(relpath: str) -> Optional[pygame.mixer.Sound]:
    if relpath in _sfx_cache:
        return _sfx_cache[relpath]
    if not _mixer_ok:
        _sfx_cache[relpath] = None
        return None
    p = _path(relpath)
    if not p:
        _sfx_cache[relpath] = None
        return None
    try:
        snd = pygame.mixer.Sound(p)
    except pygame.error:
        _sfx_cache[relpath] = None
        return None
    if snd.get_length() > MAX_SFX_SECONDS:
        print(
            f"[audio] rejecting {relpath!r} as sfx: {snd.get_length():.1f}s exceeds {MAX_SFX_SECONDS}s limit"
        )
        _sfx_cache[relpath] = None
        return None
    _sfx_cache[relpath] = snd
    return snd


def _play_on_channel(channel_id: int, snd: pygame.mixer.Sound, volume: float) -> None:
    ch = pygame.mixer.Channel(channel_id)
    # Stop whatever was on this channel first, so we never stack voices.
    ch.stop()
    ch.set_volume(volume)
    ch.play(snd)


def play_click(volume: float = 0.55) -> None:
    if not _mixer_ok:
        return
    snd = _load_sfx("ui_click.mp3")
    if snd:
        _play_on_channel(CHANNEL_CLICK, snd, volume)


def play_open(volume: float = 0.6) -> None:
    if not _mixer_ok:
        return
    snd = _load_sfx("exhibit_open.mp3")
    if snd:
        _play_on_channel(CHANNEL_OPEN, snd, volume)


def play_footstep(volume: float = 0.25) -> None:
    if not _mixer_ok:
        return
    snd = _load_sfx("footstep.mp3")
    if snd:
        _play_on_channel(CHANNEL_FOOTSTEP, snd, volume)


# ---------------------------------------------------------------------------
# Song preview clips (optional, opt-in, strictly 1 at a time).
# ---------------------------------------------------------------------------
_preview_sound: Optional[pygame.mixer.Sound] = None


def play_preview(relpath: str, volume: float = 0.7) -> bool:
    """Play a short audio clip (e.g. a licensed excerpt, CC0 cover, or
    public-domain recording) on the dedicated preview channel. Any prior
    preview is stopped first. Returns True on success."""
    global _preview_sound
    if not _mixer_ok:
        return False
    full = _path(relpath)
    if not full:
        return False
    try:
        snd = pygame.mixer.Sound(full)
    except pygame.error:
        return False
    stop_preview()
    _preview_sound = snd
    ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
    ch.stop()
    ch.set_volume(volume)
    ch.play(snd)
    # Duck music while preview plays.
    set_music_volume(max(0.06, _music_volume * 0.25))
    return True


def stop_preview() -> None:
    """Stop any playing preview and un-duck the music."""
    global _preview_sound
    if not _mixer_ok:
        return
    ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
    ch.stop()
    _preview_sound = None
    # Restore music volume to whatever scene last set it to.
    try:
        pygame.mixer.music.set_volume(_music_volume)
    except pygame.error:
        pass


def preview_is_playing() -> bool:
    if not _mixer_ok:
        return False
    return pygame.mixer.Channel(CHANNEL_SONG_PREVIEW).get_busy()


def shutdown() -> None:
    global _mixer_ok, _current_music
    if not _mixer_ok:
        return
    try:
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        pygame.mixer.quit()
    except pygame.error:
        pass
    _mixer_ok = False
    _current_music = None
