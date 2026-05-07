"""Centralized audio.

There is no other audio state in the app. Do not call pygame.mixer
elsewhere!
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import urllib.request
from typing import Dict, Optional, Tuple

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
# Song preview clips
#
# Plays 30-second MP3 previews fetched from the Deezer API. We only ever
# store the stable Deezer track ID; the preview URL is signed and short-
# lived, so we resolve it at click-time. The fetch + download runs on a
# worker thread; ``poll()`` (called from the main loop) is what actually
# starts pygame playback once the bytes have arrived. This keeps the UI
# fully responsive even on slow connections.
# ---------------------------------------------------------------------------
_preview_sound: Optional[pygame.mixer.Sound] = None
# Preview state machine. All mutations happen under _preview_lock.
_preview_lock = threading.Lock()
_preview_state: str = "idle"          # 'idle' | 'loading' | 'ready' | 'playing' | 'error'
_preview_track_id: Optional[int] = None
# Unique identifier for the currently active preview (whether loading,
# ready, or playing). For Deezer previews this is f"deezer:{track_id}";
# for local files it's f"local:{path}". UI uses this to tell apart
# which Play/Stop button is the active one across exhibits.
_preview_id: Optional[str] = None
_preview_token: int = 0               # incremented to invalidate in-flight workers
_preview_pending_path: Optional[str] = None  # MP3 file the worker dropped here
_preview_pending_volume: float = 0.7
_preview_started_at: float = 0.0       # monotonic time playback began
_preview_length: float = 30.0          # seconds, refined once Sound is loaded
_preview_error_message: str = ""
_preview_pre_duck_volume: float = 0.0


def play_preview_track(track_id: int, volume: float = 0.7) -> None:
    """Begin (or restart) playback for the given Deezer track ID.

    Returns immediately. Use :func:`preview_state` and :func:`poll` to
    drive UI updates. Calling this while a different track is loading
    or playing cancels that one cleanly.
    """
    if not _mixer_ok or not isinstance(track_id, int):
        return
    global _preview_state, _preview_track_id, _preview_id, _preview_token, _preview_error_message
    with _preview_lock:
        _preview_token += 1
        token = _preview_token
        _preview_state = "loading"
        _preview_track_id = track_id
        _preview_id = f"deezer:{track_id}"
        _preview_error_message = ""
    # Stop any current playback synchronously.
    _stop_playback_internal()
    # Hand off to a worker so the UI thread never blocks on the network.
    t = threading.Thread(
        target=_preview_worker,
        args=(track_id, token, volume),
        daemon=True,
    )
    t.start()


def play_local_preview(path: str, volume: float = 0.7) -> None:
    """Play a local MP3 file as a preview, capped at 30 seconds.

    Drops straight to 'playing' state — no network worker needed.
    The 30s cutoff is enforced in ``poll()``.
    """
    if not _mixer_ok:
        return
    global _preview_state, _preview_track_id, _preview_id, _preview_token, _preview_error_message
    global _preview_sound, _preview_started_at, _preview_length, _preview_pending_path
    with _preview_lock:
        _preview_token += 1
        _preview_state = "loading"
        _preview_track_id = None
        _preview_id = f"local:{path}"
        _preview_error_message = ""
    _stop_playback_internal()
    try:
        snd = pygame.mixer.Sound(path)
    except pygame.error as exc:
        with _preview_lock:
            _preview_state = "error"
            _preview_error_message = str(exc)
        return
    _preview_sound = snd
    _preview_length = min(snd.get_length(), 30.0)
    ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
    ch.stop()
    ch.set_volume(volume)
    ch.play(snd)
    _duck_music()
    _preview_started_at = time.monotonic()
    _preview_pending_path = None
    with _preview_lock:
        _preview_state = "playing"


def _preview_worker(track_id: int, token: int, volume: float) -> None:
    """Resolve a fresh preview URL via the Deezer track endpoint, then
    download the MP3 to a temp file and hand off to the main thread."""
    global _preview_state, _preview_pending_path, _preview_pending_volume, _preview_error_message
    try:
        meta_url = f"https://api.deezer.com/track/{track_id}"
        req = urllib.request.Request(
            meta_url,
            headers={"User-Agent": "MuseumOfReperformance/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            track = json.loads(resp.read().decode("utf-8"))
        url = track.get("preview")
        if not url:
            raise RuntimeError("track has no preview")
        # Short-circuit if user already cancelled.
        with _preview_lock:
            if token != _preview_token:
                return
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read()
        fd, path = tempfile.mkstemp(suffix=".mp3", prefix="preview_")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
    except Exception as exc:
        with _preview_lock:
            if token != _preview_token:
                return
            _preview_state = "error"
            _preview_error_message = str(exc)
        return

    with _preview_lock:
        if token != _preview_token:
            # User changed their mind; throw away the file.
            try:
                os.unlink(path)
            except OSError:
                pass
            return
        _preview_pending_path = path
        _preview_pending_volume = volume
        _preview_state = "ready"


def poll() -> None:
    """Called every frame from the main loop. Promotes a downloaded
    preview to actual playback (must happen on the main thread because
    pygame.mixer is not thread-safe for some platforms) and detects
    natural end-of-clip so the UI flips back to idle."""
    if not _mixer_ok:
        return
    global _preview_state, _preview_pending_path, _preview_sound, _preview_started_at, _preview_length
    with _preview_lock:
        state = _preview_state
        pending = _preview_pending_path
        volume = _preview_pending_volume
        # We'll consume the pending entry below.
        if state == "ready":
            _preview_pending_path = None
    if state == "ready" and pending:
        try:
            snd = pygame.mixer.Sound(pending)
        except pygame.error as exc:
            with _preview_lock:
                _preview_state = "error"
            try:
                os.unlink(pending)
            except OSError:
                pass
            return
        _preview_sound = snd
        _preview_length = max(1.0, snd.get_length())
        ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
        ch.stop()
        ch.set_volume(volume)
        ch.play(snd)
        _duck_music()
        _preview_started_at = time.monotonic()
        # Schedule cleanup of the temp file: it has to outlive the Sound
        # while it's playing, so we delete it on the next stop instead.
        _preview_pending_path = pending  # repurposed as "current temp"
        with _preview_lock:
            _preview_state = "playing"
            _preview_pending_path = pending
        return

    if state == "playing":
        ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
        elapsed = time.monotonic() - _preview_started_at
        if not ch.get_busy() or elapsed >= 30.0:
            stop_preview()


def stop_preview() -> None:
    """Stop any playing or pending preview and un-duck music."""
    if not _mixer_ok:
        return
    global _preview_state, _preview_track_id, _preview_id, _preview_token, _preview_error_message
    _stop_playback_internal()
    with _preview_lock:
        _preview_token += 1
        _preview_state = "idle"
        _preview_track_id = None
        _preview_id = None
        _preview_error_message = ""


def _stop_playback_internal() -> None:
    """Stop the channel and clean up any temp MP3 we wrote."""
    global _preview_sound, _preview_pending_path
    try:
        ch = pygame.mixer.Channel(CHANNEL_SONG_PREVIEW)
        ch.stop()
    except pygame.error:
        pass
    _preview_sound = None
    _unduck_music()
    with _preview_lock:
        path = _preview_pending_path
        _preview_pending_path = None
    if path:
        try:
            os.unlink(path)
        except OSError:
            pass


def _duck_music() -> None:
    """Drop ambient music to a quieter background level while a preview
    plays. Using 0.30 keeps it perceptibly present without competing."""
    global _preview_pre_duck_volume
    _preview_pre_duck_volume = _music_volume
    try:
        pygame.mixer.music.set_volume(max(0.05, _music_volume * 0.30))
    except pygame.error:
        pass


def _unduck_music() -> None:
    """Restore ambient music to whatever it was before ducking."""
    if _preview_pre_duck_volume <= 0:
        return
    try:
        pygame.mixer.music.set_volume(_preview_pre_duck_volume)
    except pygame.error:
        pass


def preview_state() -> str:
    """One of 'idle' | 'loading' | 'playing' | 'error'.

    'ready' is a transient internal state that flips to 'playing' on the
    next ``poll()``; we collapse it to 'loading' for UI purposes since
    the user shouldn't see a frame of "ready but silent"."""
    with _preview_lock:
        s = _preview_state
    return "loading" if s == "ready" else s


def preview_track_id() -> Optional[int]:
    with _preview_lock:
        return _preview_track_id


def preview_id() -> Optional[str]:
    """Stable identifier for whatever preview is currently active.

    Returns ``"deezer:<id>"`` for Deezer previews, ``"local:<path>"``
    for local files, or ``None`` when nothing is active. UI uses this
    to pick which Play/Stop button is the active one.
    """
    with _preview_lock:
        return _preview_id


def preview_progress() -> Tuple[float, float]:
    """``(elapsed_seconds, total_seconds)`` for whatever's currently
    playing. Returns ``(0.0, 0.0)`` if not playing."""
    if preview_state() != "playing":
        return (0.0, 0.0)
    elapsed = max(0.0, time.monotonic() - _preview_started_at)
    return (min(elapsed, _preview_length), _preview_length)


def preview_error_message() -> str:
    with _preview_lock:
        return _preview_error_message


def preview_is_playing() -> bool:
    return preview_state() == "playing"


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
