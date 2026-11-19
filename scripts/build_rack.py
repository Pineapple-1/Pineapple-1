#!/usr/bin/env python3
"""Builds assets/rack.svg, the rack drawing at the top of the profile README.

Text is converted to outlines so the image renders the same everywhere
(GitHub serves SVGs without access to web fonts).

    pip install fonttools uharfbuzz
    python scripts/build_rack.py

Fonts (Barlow, SIL Open Font License) are downloaded to scripts/.fonts on
first run. To change what the panel says, edit NAME, ROLE, HOST and GROUPS.
"""
from pathlib import Path
from urllib.request import urlretrieve

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------- content
NAME = "Abdulrehman Ajmal"
ROLE = "React front, Python back, AI in the middle"
HOST = "slowserver.net"
HOST_SPEC = "12th-gen i5, 32 GB, Ubuntu Server"
GROUPS = [
    ("frontend", ["React", "TypeScript", "JavaScript", "MUI"]),
    ("backend", ["Python", "Django", "FastAPI", "Node.js"]),
    ("data", ["PostgreSQL", "MySQL", "MongoDB", "Redis"]),
    ("infrastructure", ["Docker", "Linux", "Traefik", "Dokploy"]),
]
# Ports whose amber activity light stays dark (1-based port numbers).
IDLE_PORTS = {4, 10, 15}

# ---------------------------------------------------------------- palette
CHASSIS = "#2E5A60"       # switch-chassis teal
CHASSIS_DARK = "#234A4F"  # ears, bezels
CHASSIS_DEEP = "#19383C"  # seams, vents
EDGE_LIGHT = "#4C858C"    # top edge catch-light
SILK = "#D3E6E4"          # silkscreen print
SILK_DIM = "#9DC0BE"
TAPE = "#F8F9F6"          # label tape
INK = "#141B1C"
CAVITY = "#0B1618"
GOLD = "#CDA64E"
GREEN = "#74E08F"
AMBER = "#FFB02E"
AMBER_OFF = "#5E4B20"
STEEL = "#B9C6C6"

W, H = 1000, 386
EAR = 46
U1_H = 156
SEAM = 4
U2_Y = U1_H + SEAM

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
def rect(x, y, w, h, fill, rx=0, extra=""):
    r = f' rx="{num(rx)}"' if rx else ""
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{r} fill="{fill}"{extra}/>'


def screw(cx, cy):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="9.5" fill="{CHASSIS_DEEP}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="7" fill="{STEEL}"/>'
        f'<path d="M{cx - 4} {cy - 2.5}L{cx + 4} {cy + 2.5}" stroke="#6F7F80" stroke-width="1.8" stroke-linecap="round"/>'
    )


def tape(x, y, w, h, angle, inner):
    cx, cy = x + w / 2, y + h / 2
    return (
        f'<g transform="rotate({angle} {num(cx)} {num(cy)})">'
        + rect(x + 1, y + 2, w, h, CHASSIS_DEEP, 2.5, ' opacity=".55"')
        + rect(x, y, w, h, TAPE, 2.5)
        + inner
        + "</g>"
    )


def port(x, y, number, blink_class):
    """An RJ45 jack, 54 wide and 42 tall, with link and activity lights."""
    w, h = 54, 42
    cav_x, cav_y, cav_w, cav_h = x + 6, y + 11, w - 12, 21
    tab_w = 16
    parts = [rect(x, y, w, h, CHASSIS_DARK, 3)]
    # cavity with the latch notch at the bottom
    parts.append(
        f'<path fill="{CAVITY}" d="M{cav_x} {cav_y}h{cav_w}v{cav_h}h-{(cav_w - tab_w) / 2}v6h-{tab_w}v-6h-{(cav_w - tab_w) / 2}z"/>'
    )
    # eight contacts
    step = (cav_w - 10) / 7
    pins = "".join(
        f"M{num(cav_x + 5 + i * step)} {cav_y}v7" for i in range(8)
    )
    parts.append(f'<path d="{pins}" stroke="{GOLD}" stroke-width="1.7"/>')
    # link (steady green) and activity (amber)
    parts.append(rect(x + 6, y + 4, 9, 4, GREEN, 1))
    parts.append(rect(x + w - 15, y + 4, 9, 4, AMBER_OFF, 1))
    if blink_class:
        parts.append(rect(x + w - 15, y + 4, 9, 4, AMBER, 1, f' class="act {blink_class}"'))
    parts.append(text("cond-500", str(number), 12.5, x - 7, y + h - 3, SILK_DIM, "end"))
    return "".join(parts)


def build():
    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">'
    )
    groups_desc = "; ".join(f"{g}: {', '.join(p)}" for g, p in GROUPS)
    o.append(f'<title id="t">{NAME}: {ROLE}</title>')
    o.append(
        f'<desc id="d">A teal rack unit labelled {NAME}, above a patch panel whose ports are labelled with the tools he works with. {groups_desc}.</desc>'
    )
    o.append(
        "<style>"
        ".act{animation:1s steps(1,end) infinite}"
        ".b1{animation-name:k1;animation-duration:2.3s}"
        ".b2{animation-name:k2;animation-duration:3.1s}"
        ".b3{animation-name:k3;animation-duration:1.7s}"
        ".b4{animation-name:k2;animation-duration:4.3s;animation-delay:-1.9s}"
        ".b5{animation-name:k1;animation-duration:3.7s;animation-delay:-.8s}"
        "@keyframes k1{0%{opacity:1}7%{opacity:0}13%{opacity:1}19%{opacity:0}26%{opacity:1}58%{opacity:0}64%{opacity:1}}"
        "@keyframes k2{0%{opacity:0}22%{opacity:1}27%{opacity:0}33%{opacity:1}38%{opacity:0}44%{opacity:1}81%{opacity:0}86%{opacity:1}92%{opacity:0}}"
        "@keyframes k3{0%{opacity:1}11%{opacity:0}23%{opacity:1}35%{opacity:0}47%{opacity:1}70%{opacity:0}88%{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.act{animation:none}}"
        "</style>"
    )

    # ---- chassis
    o.append(rect(0, 0, W, H, CHASSIS, 7))
    o.append(rect(0, U1_H, W, SEAM, CHASSIS_DEEP))
    for y0 in (0, U2_Y):
        o.append(rect(8, y0 + 1.5, W - 16, 1.5, EDGE_LIGHT, 0, ' opacity=".7"'))
    # ears
    o.append(f'<path fill="{CHASSIS_DARK}" d="M7 0h{EAR - 7}v{H}h-{EAR - 7}a7 7 0 0 1-7-7v-{H - 14}a7 7 0 0 1 7-7z"/>')
    o.append(f'<path fill="{CHASSIS_DARK}" d="M{W - EAR} 0h{EAR - 7}a7 7 0 0 1 7 7v{H - 14}a7 7 0 0 1-7 7h-{EAR - 7}z"/>')
    o.append(rect(0, U1_H, W, SEAM, CHASSIS_DEEP))
    for cx in (EAR / 2, W - EAR / 2):
        for cy in (34, U1_H - 34, U2_Y + 40, H - 40):
            o.append(screw(cx, cy))

    # ---- unit 1: the server, labelled by its owner
    left = EAR + 34
    name_size = 52
    name_w = text_width("semi-600", NAME, name_size)
    o.append(
        tape(
            left, 28, name_w + 44, 70, -0.8,
            text("semi-600", NAME, name_size, left + 22, 28 + 53, INK),
        )
    )
    role_size = 19.5
    role_w = text_width("semi-500", ROLE, role_size)
    o.append(
        tape(
            left + 6, 108, role_w + 28, 31, 0.5,
            text("semi-500", ROLE, role_size, left + 20, 108 + 21.5, INK),
        )
    )

    right = W - EAR - 34
    o.append(text("cond-600", HOST, 30, right, 62, SILK, "end", 0.4))
    o.append(text("cond-500", HOST_SPEC, 15.5, right, 85, SILK_DIM, "end", 0.3))
    # light legend, right-aligned
    lx = right
    for label, colour in (("activity", AMBER), ("link", GREEN)):
        lw = text_width("cond-500", label, 15.5, 0.3)
        o.append(text("cond-500", label, 15.5, lx, 126, SILK, "end", 0.3))
        lx -= lw + 8
        o.append(rect(lx - 11, 116, 11, 5, colour, 1.2))
        lx -= 11 + 22

    # vent slots between the labels and the host name
    vent_x0 = left + name_w + 44 + 52
    vent_x1 = right - text_width("cond-600", HOST, 30, 0.4) - 52
    slot_w, slot_gap = 34, 10
    count = int((vent_x1 - vent_x0 + slot_gap) // (slot_w + slot_gap))
    if count > 0:
        span = count * slot_w + (count - 1) * slot_gap
        start = vent_x0 + (vent_x1 - vent_x0 - span) / 2
        for row in range(6):
            for i in range(count):
                o.append(rect(start + i * (slot_w + slot_gap), 40 + row * 14, slot_w, 6, CHASSIS_DEEP, 3))

    # ---- unit 2: the patch panel
    inner_x, inner_w = EAR + 34, W - 2 * (EAR + 34)
    gap = 36
    block_w = (inner_w - gap * (len(GROUPS) - 1)) / len(GROUPS)
    col = block_w / 2
    blinks = ["b1", "b2", "b3", "b4", "b5"]
    n = 0
    for gi, (group, labels) in enumerate(GROUPS):
        bx = inner_x + gi * (block_w + gap)
        ty = U2_Y + 34
        gw = text_width("cond-600", group, 16.5, 0.6)
        o.append(text("cond-600", group, 16.5, bx, ty, SILK, tracking=0.6))
        o.append(rect(bx + gw + 10, ty - 6, block_w - gw - 10, 1.5, SILK_DIM, 0, ' opacity=".55"'))
        for li, label in enumerate(labels):
            n += 1
            cx = bx + col * (li % 2) + col / 2
            ry = U2_Y + 50 + (li // 2) * 84
            strip_w = col - 10
            size = 17
            while text_width("cond-500", label, size) > strip_w - 12:
                size -= 0.5
            o.append(rect(cx - strip_w / 2, ry, strip_w, 24, TAPE, 1.5))
            o.append(text("cond-500", label, size, cx, ry + 17.5, INK, "middle"))
            blink = None if n in IDLE_PORTS else blinks[(n * 3 + gi) % len(blinks)]
            o.append(port(cx - 27, ry + 29, n, blink))

    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "rack.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build() + "\n")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
