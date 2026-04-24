"""Generate CC0 SFX for the museum: ui click, page flip (exhibit open), soft
footstep. Writes .wav files into ../music/ next to the ambient tracks.

The sounds are synthesized mathematically — no third-party samples, no
licensing ambiguity. Run once; the resulting .wav files are committed.
"""

from __future__ import annotations

import math
import os
import struct
import wave
from typing import Iterable

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "music"))
SAMPLE_RATE = 44100


def _write_wav(path: str, samples: Iterable[float]) -> None:
    samples = list(samples)
    peak = max(1e-9, max(abs(s) for s in samples))
    norm = [max(-1.0, min(1.0, s / peak * 0.85)) for s in samples]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in norm))


def make_click() -> None:
    """A short, soft 'tick' — band-limited noise shaped with a fast
    exponential decay. Feels like a real wooden museum button."""
    duration = 0.055
    n = int(SAMPLE_RATE * duration)
    import random
    random.seed(1)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t / 0.012) * (1 - math.exp(-t / 0.0008))
        noise = random.uniform(-1.0, 1.0)
        tone = 0.3 * math.sin(2 * math.pi * 2200 * t)
        samples.append((0.7 * noise + tone) * env)
    _write_wav(os.path.join(OUT, "ui_click.wav"), samples)


def make_open() -> None:
    """A two-tone chime — 'a small card flipped over.' Rising major third."""
    duration = 0.55
    n = int(SAMPLE_RATE * duration)
    samples = []
    freqs = [(523.25, 0.0), (659.25, 0.08)]  # C5 then E5
    for i in range(n):
        t = i / SAMPLE_RATE
        v = 0.0
        for f, start in freqs:
            if t >= start:
                local = t - start
                env = math.exp(-local / 0.18) * (1 - math.exp(-local / 0.004))
                v += 0.5 * math.sin(2 * math.pi * f * local) * env
        # subtle 2nd-harmonic shimmer
        v += 0.05 * math.sin(2 * math.pi * 1318.51 * t) * math.exp(-t / 0.15)
        samples.append(v)
    _write_wav(os.path.join(OUT, "exhibit_open.wav"), samples)


def make_footstep() -> None:
    """A low-frequency thump shaped like a footfall on stone — filtered
    noise with a quick attack/decay. Used sparsely to imply a quiet room."""
    duration = 0.14
    n = int(SAMPLE_RATE * duration)
    import random
    random.seed(2)
    # Simple one-pole low-pass
    samples = []
    y = 0.0
    alpha = 0.08
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = random.uniform(-1.0, 1.0)
        y = y + alpha * (noise - y)
        env = math.exp(-t / 0.06) * (1 - math.exp(-t / 0.003))
        thump = 0.35 * math.sin(2 * math.pi * 110 * t) * math.exp(-t / 0.045)
        samples.append((0.6 * y + thump) * env)
    _write_wav(os.path.join(OUT, "footstep.wav"), samples)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_click()
    make_open()
    make_footstep()
    print(f"wrote sfx to {OUT}")
