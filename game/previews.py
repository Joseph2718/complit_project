"""Preview-track lookup.

Deezer track IDs live in ``assets/previews.json``. For BBC covers not
on Deezer, drop an MP3 in ``music/`` and add an entry to
``_LOCAL_FILES`` below — the exhibit will play it (capped at 30 s)
instead of hitting Deezer.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JSON_PATH = os.path.join(ROOT, "assets", "previews.json")
MUSIC_DIR = os.path.join(ROOT, "music")

# Map (song, performer) -> filename inside music/ for local MP3 previews.
# Add entries here once the files are downloaded.
_LOCAL_FILES: Dict[Tuple[str, str], str] = {
    ("Take Me to Church", "Demi Lovato"): "demi_lovato_take_me_to_church_bbc.mp3",
    ("Jolene",            "Lil Nas X"):   "lil_nas_x_jolene_bbc.mp3",
    ("drivers license",   "Rick Astley"): "rick_astley_drivers_license_bbc.mp3",
}

_table: Dict[Tuple[str, str], int] = {}
_substitute: Dict[Tuple[str, str], str] = {}


def _load() -> None:
    if not os.path.isfile(JSON_PATH):
        return
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    for key, entry in raw.items():
        if "::" not in key:
            continue
        song, performer = key.split("::", 1)
        tid = entry.get("deezer_track_id")
        if isinstance(tid, int):
            _table[(song, performer)] = tid
            sub = entry.get("substitute")
            if isinstance(sub, str):
                _substitute[(song, performer)] = sub


_load()


def track_id_for(song: str, performer: str) -> Optional[int]:
    return _table.get((song, performer))


def has_preview(song: str, performer: str) -> bool:
    return (song, performer) in _table or local_path_for(song, performer) is not None


def substitute_kind(song: str, performer: str) -> Optional[str]:
    """Returns ``"original"`` / ``"same_audio"`` / ``None``."""
    return _substitute.get((song, performer))


def local_path_for(song: str, performer: str) -> Optional[str]:
    """Return absolute path to a local MP3 preview, or None."""
    fname = _LOCAL_FILES.get((song, performer))
    if fname is None:
        return None
    path = os.path.join(MUSIC_DIR, fname)
    return path if os.path.isfile(path) else None
