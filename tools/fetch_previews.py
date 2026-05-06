"""Resolve a 30-second MP3 preview URL for every Performance defined in
``game/content.py`` and write the result to ``assets/previews.json``.

We use the public Deezer API (https://developers.deezer.com) because:
* It returns *MP3* preview clips (pygame's SDL_mixer plays MP3 natively;
  it cannot play AAC / M4A which is what iTunes Search returns).
* No authentication is required for the search + preview endpoints.
* Spotify deprecated ``preview_url`` for new applications in Nov 2024,
  so it is no longer a viable source.

Run once whenever the content list changes:

    python tools/fetch_previews.py

The script does not embed audio — only URLs — so distributing the repo
does not redistribute Deezer's audio (per their developer guidelines,
the 30-second preview is freely linkable for any user, logged in or
not).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

# Make the parent package importable when running this file directly.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from game.content import WINGS  # noqa: E402


OUT_PATH = os.path.join(ROOT, "assets", "previews.json")
DEEZER_SEARCH = "https://api.deezer.com/search"


def _http_get_json(url: str, timeout: float = 8.0) -> Optional[Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MuseumOfReperformance/1.0 (academic project)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover  (network)
        print(f"  [warn] {url}: {exc}")
        return None


def _norm(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum())


def _query(song: str, performer: str) -> Optional[Dict[str, Any]]:
    """Search Deezer for a track. Tries strict ``track:"x" artist:"y"``
    syntax first, falls back to a plain bag-of-words query."""
    queries = [
        f'track:"{song}" artist:"{performer}"',
        f"{song} {performer}",
    ]
    for q in queries:
        url = f"{DEEZER_SEARCH}?q={urllib.parse.quote(q)}&limit=15"
        data = _http_get_json(url)
        if not data or not data.get("data"):
            continue
        # Score: title contains song & artist contains performer (loose).
        target_song = _norm(song)
        target_perf = _norm(performer)
        scored = []
        for item in data["data"]:
            title = _norm(item.get("title_short") or item.get("title", ""))
            artist = _norm((item.get("artist") or {}).get("name", ""))
            score = 0
            if target_song and target_song in title:
                score += 2
            if target_perf and target_perf in artist:
                score += 3
            # Penalty for weird remixes/karaoke when a cleaner version exists.
            full = (item.get("title", "") + " " + (item.get("artist") or {}).get("name", "")).lower()
            if any(bad in full for bad in ("karaoke", "tribute", "made famous by", "instrumental")):
                score -= 4
            if item.get("preview"):
                score += 1
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] >= 4 and scored[0][1].get("preview"):
            return scored[0][1]
        time.sleep(0.2)  # be polite between fallback queries
    return None


def main() -> None:
    print(f"resolving Deezer previews → {OUT_PATH}\n")
    out: Dict[str, Dict[str, Any]] = {}
    for wing in WINGS:
        print(f"=== {wing.title}: {wing.subtitle}")
        for ex in wing.exhibits:
            performances = (ex.original,) + ex.reperformances
            for perf in performances:
                key = f"{ex.song}::{perf.performer}"
                # Skip entries that aren't actually recordings (e.g.
                # "LGBTQ+ communities during the AIDS crisis", "U.S.
                # political rallies & ad campaigns") — these are
                # cultural reperformances, not tracks.
                if any(stopword in perf.performer.lower() for stopword in (
                    "rally", "rallies", "campaign", "communities", "season ",
                    "doggface", "apodaca", "nathan",
                )):
                    out[key] = {"source": None, "skipped": True}
                    print(f"  -- {key:60s}  (skipped: cultural reperformance)")
                    continue

                hit = _query(ex.song, perf.performer)
                if hit and hit.get("preview"):
                    # Deezer's signed preview URLs expire within hours, so
                    # we only persist the stable track ID + display metadata.
                    # The runtime fetches a fresh URL from
                    # https://api.deezer.com/track/{id} on demand.
                    out[key] = {
                        "source": "deezer",
                        "deezer_track_id": hit.get("id"),
                        "matched_title": hit.get("title"),
                        "matched_artist": (hit.get("artist") or {}).get("name"),
                    }
                    print(
                        f"  ok {key:60s}  → {hit.get('title')!r} by "
                        f"{(hit.get('artist') or {}).get('name')!r}"
                    )
                else:
                    out[key] = {"source": None}
                    print(f"  ?? {key:60s}  (no match)")
                time.sleep(0.25)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    found = sum(1 for v in out.values() if v.get("deezer_track_id"))
    print(f"\nwrote {OUT_PATH}: {found}/{len(out)} resolved")


if __name__ == "__main__":
    main()
