#!/usr/bin/env python3
"""Builds assets/banner.svg: my name drawn as a LoRa packet on a waterfall plot.

LoRa radios talk in chirps, tones that sweep up through the band. A symbol's
value is the frequency its chirp starts at; the sweep wraps round at the top
of the band and carries on from the bottom. In each row time runs left to
right and frequency runs bottom to top, the way an SDR waterfall shows it
turned on its side.

The first row is the start of a packet: a preamble of plain upchirps, then
two and a quarter downchirps of sync. Each row after it spells one word of
NAME, one chirp per letter, starting at that letter's place in the alphabet
(A at the bottom of the band, Z near the top). After the last letter the
radio goes quiet. A real radio would also whiten and error-code the payload;
this one is a drawing.

    python scripts/build_banner.py        # standard library only
"""
import random
from pathlib import Path

NAME = "Abdulrehman Ajmal"
PREAMBLE = 8
LEVELS = 32  # 2 ** spreading factor; room for the alphabet

W = 1200
SIDE, EDGE = 30, 36
BAND, GAP = 108, 26               # height of one row's band, space between rows
PER_ROW = 11                      # symbols across

GROUND = "#07070C"
# frequency to colour, low to high, in the manner of a waterfall display
HEAT = [(0, "#3B1C8C"), (0.3, "#8E2C9B"), (0.55, "#E0456B"), (0.8, "#FB9A3C"), (1, "#FCE9A0")]


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def chirp(x, bottom, w, start, up=True, length=1.0):
    """Line segments for one chirp starting at band position `start` (0..1)."""
    def y(level):
        return bottom - level * BAND

    if not up:
        return [(x, y(1), x + length * w, y(1 - length))]
    first = min(1 - start, length)              # time until the wrap
    segs = [(x, y(start), x + first * w, y(start + first))]
    if length > first:
        segs.append((x + first * w, y(0), x + length * w, y(length - first)))
    return segs


def build():
    words = NAME.split()
    rows = 1 + len(words)
    H = 2 * EDGE + rows * BAND + (rows - 1) * GAP
    w = (W - 2 * SIDE) / PER_ROW
    bottoms = [EDGE + BAND + r * (BAND + GAP) for r in range(rows)]

    segs = []
    x = SIDE
    for _ in range(PREAMBLE):
        segs += chirp(x, bottoms[0], w, 0)
        x += w
    for length in (1, 1, 0.25):
        segs += chirp(x, bottoms[0], w, 0, up=False, length=length)
        x += w * length
    for word, bottom in zip(words, bottoms[1:]):
        x = SIDE
        for ch in word.upper():
            segs += chirp(x, bottom, w, (ord(ch) - ord("A")) / LEVELS)
            x += w

    d = "".join(f"M{n(a)} {n(b)}L{n(c)} {n(e)}" for a, b, c, e in segs)
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in HEAT)
    # one gradient per row so colour always means height within that row's band
    grads = "".join(
        f'<linearGradient id="h{i}" gradientUnits="userSpaceOnUse" x1="0" y1="{b}" x2="0" y2="{b - BAND}">{stops}</linearGradient>'
        for i, b in enumerate(bottoms)
    )

    def row_paths(width, extra=""):
        out = []
        for i, b in enumerate(bottoms):
            rd = "".join(
                f"M{n(a)} {n(y1)}L{n(c)} {n(y2)}" for a, y1, c, y2 in segs if b - BAND - 1 <= min(y1, y2) and max(y1, y2) <= b + 1
            )
            out.append(f'<path d="{rd}" fill="none" stroke="url(#h{i})" stroke-width="{width}" stroke-linecap="round"{extra}/>')
        return "".join(out)

    rng = random.Random(7)
    noise = "".join(
        f'<circle cx="{n(rng.uniform(0, W))}" cy="{n(rng.uniform(0, H))}" r="{n(rng.uniform(.5, 1.6))}" '
        f'opacity="{n(rng.uniform(.1, .55))}"/>'
        for _ in range(520)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">'
        f'<title id="t">Self-portrait as a LoRa packet</title>'
        f'<desc id="d">Glowing diagonal strokes on a black ground, like a radio waterfall plot. The top row is a run of identical '
        f"rising chirps followed by two falling ones. Each row below spells a word of the name {NAME}, one rising chirp per letter, "
        "starting higher the later the letter comes in the alphabet.</desc>"
        "<defs>"
        f"{grads}"
        '<filter id="glow" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="8"/></filter>'
        f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
        "</defs>"
        '<g clip-path="url(#frame)">'
        f'<rect width="{W}" height="{H}" fill="{GROUND}"/>'
        f'<g fill="#7A5CC0">{noise}</g>'
        f'<g opacity=".6" filter="url(#glow)">{row_paths(17)}</g>'
        f"{row_paths(7)}"
        f'<path d="{d}" fill="none" stroke="#FFF7DC" stroke-width="1.6" stroke-linecap="round" opacity=".55"/>'
        "</g></svg>"
    )


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build() + "\n")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
