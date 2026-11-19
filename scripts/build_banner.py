#!/usr/bin/env python3
"""Builds assets/banner.svg, the banner at the top of the profile README.

Text is converted to outlines so the image renders the same everywhere
(GitHub serves SVGs without access to web fonts). Everything is drawn large
enough to stay readable when the banner is scaled down to a phone screen.

    pip install fonttools uharfbuzz
    python scripts/build_banner.py

Fonts (Barlow, SIL Open Font License) are downloaded to scripts/.fonts on
first run. To change what the banner says, edit NAME and ROLE.
"""
from pathlib import Path
from urllib.request import urlretrieve

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------- content
NAME = "Abdulrehman Ajmal"
ROLE = "Ships products, runs a homelab, reads about rockets"

# ---------------------------------------------------------------- palette
SKY_TOP = "#0B1620"
SKY_LOW = "#17343B"
WHITE = "#F4F7F5"
MINT = "#9AD8CB"
AMBER = "#FFB02E"
LINK = "#5FA79E"
STAR = "#C9DBD8"

W, H = 1000, 340
PAD = 56

# ---------------------------------------------------------------- fonts
FONT_DIR = Path(__file__).parent / ".fonts"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/{dir}/{file}"
FONT_FILES = {
    "semi-600": ("barlowsemicondensed", "BarlowSemiCondensed-SemiBold.ttf"),
    "semi-500": ("barlowsemicondensed", "BarlowSemiCondensed-Medium.ttf"),
    "cond-600": ("barlowcondensed", "BarlowCondensed-SemiBold.ttf"),
    "cond-500": ("barlowcondensed", "BarlowCondensed-Medium.ttf"),
}
_fonts = {}


def font(key):
    if key not in _fonts:
        folder, name = FONT_FILES[key]
        path = FONT_DIR / name
        if not path.exists():
            FONT_DIR.mkdir(exist_ok=True)
            urlretrieve(FONT_URL.format(dir=folder, file=name), path)
        tt = TTFont(path)
        hbfont = hb.Font(hb.Face(path.read_bytes()))
        _fonts[key] = (tt, tt.getGlyphSet(), hbfont, tt["head"].unitsPerEm)
    return _fonts[key]


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def shape(key, text, size, tracking=0.0):
    """Returns [(glyph_name, x_offset)], total width — in px at `size`."""
    tt, _, hbfont, upm = font(key)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True, "liga": False})
    scale = size / upm
    x, out = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((tt.getGlyphName(info.codepoint), x + pos.x_offset * scale))
        x += pos.x_advance * scale + tracking
    return out, x - tracking


def text_width(key, text, size, tracking=0.0):
    return shape(key, text, size, tracking)[1]


def text(key, s, size, x, y, fill, anchor="start", tracking=0.0):
    """Outlined text with its baseline at (x, y)."""
    _, glyphset, _, upm = font(key)
    glyphs, width = shape(key, s, size, tracking)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    scale = size / upm
    pen = SVGPathPen(glyphset, ntos=num)
    for name, gx in glyphs:
        glyphset[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + gx, y)))
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


# ---------------------------------------------------------------- parts


def build():
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        f'<title id="t">{NAME}: {ROLE}</title>',
        '<desc id="d">A night sky with a rocket climbing along a dashed arc above a small mesh of linked radio nodes.</desc>',
        "<style>"
        ".n{animation:p 3.2s ease-in-out infinite}.n2{animation-delay:-1.1s}.n3{animation-delay:-2.2s}"
        "@keyframes p{0%,100%{opacity:1}50%{opacity:.35}}"
        "@media (prefers-reduced-motion:reduce){.n{animation:none}}"
        "</style>",
        f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SKY_TOP}"/><stop offset="1" stop-color="{SKY_LOW}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#sky)"/>',
    ]
    # stars
    for x, y, r in [(90, 52, 2), (236, 30, 1.5), (402, 62, 2), (548, 34, 1.5), (668, 78, 2),
                    (742, 40, 1.5), (120, 300, 1.5), (512, 306, 2), (640, 286, 1.5), (968, 300, 1.5)]:
        o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{STAR}" opacity=".55"/>')

    # the words: sized to fill the left two thirds, so they survive a phone
    name_size = 86
    while text_width("semi-600", NAME, name_size) > 640:
        name_size -= 1
    o.append(text("semi-600", NAME, name_size, PAD, 172, WHITE))
    role_size = 33
    while text_width("semi-500", ROLE, role_size) > 640:
        role_size -= 0.5
    o.append(text("semi-500", ROLE, role_size, PAD, 228, MINT))
    o.append(f'<rect x="{PAD}" y="252" width="84" height="5" rx="2.5" fill="{AMBER}"/>')

    # a rocket on its way up
    o.append(f'<path d="M726 318Q790 96 938 62" fill="none" stroke="{STAR}" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 13" opacity=".8"/>')
    o.append(
        '<g transform="translate(946 60) rotate(77)">'
        f'<path d="M0-30C11-18 12-2 10 14H-10C-12-2-11-18 0-30z" fill="{WHITE}"/>'
        f'<path d="M-10 4-20 20-10 16zM10 4 20 20 10 16z" fill="{MINT}"/>'
        f'<circle cy="-8" r="4.5" fill="{SKY_TOP}"/>'
        f'<path d="M-6 16h12L0 34z" fill="{AMBER}"/>'
        "</g>"
    )

    # a small mesh network on the ground
    nodes = [(800, 262), (872, 206), (944, 258), (878, 304)]
    links = [(0, 1), (1, 2), (2, 3), (3, 0), (1, 3)]
    for a, b in links:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        o.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{LINK}" stroke-width="3" stroke-linecap="round"/>')
    for i, (x, y) in enumerate(nodes):
        o.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{AMBER}" opacity=".18"/>')
        o.append(f'<circle class="n n{i % 3 + 1}" cx="{x}" cy="{y}" r="8" fill="{AMBER}"/>')

    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build() + "\n")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
