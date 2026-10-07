#!/usr/bin/env python3
"""The docs pictures' colours, and the reader that will not miss one.

What every colour on a sheet becomes on the docs site's dark ground, and a
reader of a sheet's SVG that refuses anything it cannot account for: see
``tools/docs_images.py``, which this is the half of that knows about colour.
Imported, not run.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

#: Furo's ``--color-background-primary`` in each theme, Furo 2024.8.6 being
#: the version fpgas.online-docs pins in docs/requirements.txt; read from its
#: built furo.css, not remembered.
GROUND = {"light": "#ffffff", "dark": "#131416"}

#: WCAG 2 contrast a colour must keep against the ground.  The docs site's
#: standard (fo-docs, 7 October 2026) for what it draws in the dark theme is
#: 7:1 for anything that letters text against the page ground, 4.5:1 for that
#: text against the table fills it sits on, and 3:1 for a colour only lines
#: and arrowheads are drawn in.  The light drawing is as drafted and is held
#: to 4.5:1 only; ``light_text_below_7`` reports the colours of text it has
#: that are short of the 7:1 the dark one is held to.  A fill is not held to
#: either -- it is a tint under text -- and a mask has to BE the ground.
#: A colour that is used for both text and lines is a text colour.
TEXT, LINE, FILL, MASK = "text", "line", "fill", "mask"
MIN_CONTRAST = {TEXT: 4.5, LINE: 3.0}
MIN_TEXT_DARK_GROUND = 7.0
MIN_TEXT_ON_FILL = 4.5


@dataclass(frozen=True)
class Swap:
    dark: str
    role: str
    why: str


#: Every colour a pictured sheet may use, and what it becomes on the dark
#: ground.  The greys keep the contrast against the dark ground that they had
#: against white -- the nearest grey to it, so the ranking a drafter set by
#: greyness survives inverted -- except black, which cannot have 21:1 on a
#: ground that is not black and takes the 15.5:1 that is the most this ground
#: allows short of a glare-white.  The hues are each lightened to the same
#: hue, enough to clear 4.5:1 with room, and kept apart: blue, teal and red
#: stay three colours.  A colour new to a sheet goes here, with its reason.
PALETTE = {
    "#000000": Swap("#ebebeb", TEXT,
                    "outlines, notes, tables: the drawing itself. 15.5:1"),
    "#333333": Swap("#d6d6d6", TEXT,
                    "style.C_COMPONENT: 12.6:1, as it had on white"),
    "#666666": Swap("#a6a6a6", TEXT,
                    "zone and title block labels: 7.6:1, 6.1:1 on the "
                    "darkest fill, and still two steps under the #d6d6d6 "
                    "and #ebebeb of the drawing's own text"),
    "#7a7a7a": Swap("#7a7a7a", LINE,
                    "style.C_PHANTOM: unchanged, it is 4.3:1 on both"),
    "#888888": Swap("#6d6d6d", LINE,
                    "trim line and zone ticks, the sheet's quietest line: "
                    "3.5:1, as on white"),
    "#004c99": Swap("#5aa9ff", TEXT,
                    "style.C_DIM, dimensions and their values: the same "
                    "blue lightened, 7.5:1"),
    "#a00000": Swap("#ff8080", TEXT,
                    "style.C_HIGHLIGHT, what the sheet is about: the same "
                    "red lightened, 7.6:1, and still a red beside the "
                    "amber, the teals and the blue"),
    "#005f5f": Swap("#45c8bd", TEXT,
                    "style.C_FRAME_A, frame A and the rays: the same teal "
                    "lightened, 9.0:1, and greener than the blue"),
    "#006060": Swap("#45c8bd", TEXT,
                    "the mounting plate's PLATE_HOLE, the plate fixings into "
                    "the chassis: the teal of frame A, #005f5f, one unit of "
                    "green and of blue off it, lightened to the same 9.0:1"),
    "#7a4a00": Swap("#d9983a", TEXT,
                    "style.C_FRAME_B, here the USB-C outlines: the same "
                    "brown lightened to amber, 7.5:1 as on white, and apart "
                    "from the red and the teal"),
    "#e6e6e6": Swap("#282828", FILL,
                    "style.C_FILL_TABLE_HEAD: a tint 1.25:1 off the ground, "
                    "as on white"),
    "#f0f0f0": Swap("#212121", FILL,
                    "style.C_FILL_LIGHT: a tint 1.14:1 off the ground, as on "
                    "white"),
    "#ffffff": Swap(GROUND["dark"], MASK,
                    "the white behind a label or inside a balloon, which "
                    "hides what runs under it: it must be the ground, since "
                    "a transparent mask masks nothing"),
}

#: The page rectangle ``Canvas.to_svg`` writes first, and the docs leave out.
PAGE_RECT = '<rect width="100%" height="100%" fill="#ffffff"/>'

#: What may be drawn, and the attributes each may carry.  Anything else is
#: refused: an attribute this does not know might carry a colour or an
#: opacity, and an element might hold children whose colours it never reads.
ELEMENTS = {"line", "rect", "circle", "path", "polygon", "polyline", "text"}
COLOURLESS = {"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
              "width", "height", "points", "d", "stroke-width",
              "stroke-dasharray", "stroke-dashoffset", "stroke-linecap",
              "stroke-linejoin", "font-family", "font-size", "font-weight",
              "text-anchor", "transform"}
COLOURED = {"fill", "stroke"}
HEX = re.compile(r"#[0-9a-f]{6}")
ROTATE = re.compile(r"rotate\([-\d. ]+\)")


# ---------------------------------------------------------------------------
# colour
# ---------------------------------------------------------------------------

def _luminance(colour: str) -> float:
    def lin(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    """WCAG 2 contrast ratio of two #rrggbb colours."""
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def palette_problems() -> list[str]:
    """Every way ``PALETTE`` fails its own rules, in either theme."""
    bad = []
    for light, swap in PALETTE.items():
        for theme, colour in (("light", light), ("dark", swap.dark)):
            if not HEX.fullmatch(colour):
                bad.append(f"{light}: {colour!r} is not #rrggbb")
                continue
            need = MIN_CONTRAST.get(swap.role)
            if swap.role == TEXT and theme == "dark":
                need = MIN_TEXT_DARK_GROUND
            got = contrast(colour, GROUND[theme])
            if need and got < need:
                bad.append(f"{light} ({swap.role}) is {got:.2f}:1 on the "
                           f"{theme} ground {GROUND[theme]}, under {need}:1")
            if swap.role == TEXT:
                for fill, other in PALETTE.items():
                    if other.role != FILL:
                        continue
                    under = fill if theme == "light" else other.dark
                    got = contrast(colour, under)
                    if got < MIN_TEXT_ON_FILL:
                        bad.append(f"{light} ({theme}: {colour}) is "
                                   f"{got:.2f}:1 on the fill {under}")
        if swap.role == MASK and (light != GROUND["light"]
                                  or swap.dark != GROUND["dark"]):
            bad.append(f"{light} is a mask and must be the ground in both "
                       "themes")
    return bad


def light_text_below_7() -> dict[str, float]:
    """The text colours the light drawing uses that are under 7:1 on white,
    with their contrast: reported, not changed, since the light picture is the
    drawing as drafted."""
    return {light: round(contrast(light, GROUND["light"]), 2)
            for light, swap in PALETTE.items()
            if swap.role == TEXT
            and contrast(light, GROUND["light"]) < MIN_TEXT_DARK_GROUND}


# ---------------------------------------------------------------------------
# reading a sheet
# ---------------------------------------------------------------------------

@dataclass
class Element:
    line: str           # the element as the canvas wrote it, one line
    tag: str
    attrs: dict[str, str]


@dataclass
class Drawing:
    head: str           # the <?xml?> line
    width: float        # millimetres
    height: float
    elements: list[Element]


SVG_OPEN = re.compile(r'<svg xmlns="http://www.w3.org/2000/svg" '
                      r'version="1.1" width="([\d.]+)mm" height="([\d.]+)mm" '
                      r'viewBox="0 0 ([\d.]+) ([\d.]+)">')


def read(svg: str, name: str) -> Drawing:
    """A sheet as ``Canvas.to_svg`` writes it, every element checked.

    Read line by line, because the canvas writes one element to a line, and
    refused outright if it is not shaped that way: this is not an SVG
    reader, and a file it only half understood is one whose colours it
    might only half swap.
    """
    lines = svg.split("\n")
    problems = []
    if lines[0] != '<?xml version="1.0" encoding="UTF-8"?>':
        problems.append("line 1 is not the XML declaration")
    m = SVG_OPEN.fullmatch(lines[1]) if len(lines) > 1 else None
    if not m or m.group(1) != m.group(3) or m.group(2) != m.group(4):
        raise SystemExit(f"{name}: line 2 is not the canvas's <svg> element "
                         "with a viewBox in millimetres")
    if lines[2] != PAGE_RECT:
        problems.append(f"line 3 is not the page rectangle {PAGE_RECT}")
    if lines[3] != "":
        problems.append("line 4 holds <defs>, which nothing here reads: a "
                        "pattern or a gradient could carry a colour")
    if lines[-2:] != ["</svg>", ""]:
        problems.append("the file does not end with </svg>")
    elements = []
    for n, line in enumerate(lines[4:-2], start=5):
        try:
            el = ET.fromstring(line)
        except ET.ParseError as e:
            problems.append(f"line {n} is not one whole element: {e}")
            continue
        tag = el.tag
        if tag not in ELEMENTS:
            problems.append(f"line {n}: <{tag}> is not an element this "
                            "reads")
        if len(el):
            problems.append(f"line {n}: <{tag}> has children")
        for key, value in el.attrib.items():
            if key in COLOURED:
                if value != "none" and value not in PALETTE:
                    problems.append(
                        f"line {n}: {key}={value!r} is not in PALETTE"
                        + ("" if HEX.fullmatch(value)
                           else ", nor written as #rrggbb"))
            elif key not in COLOURLESS:
                problems.append(f"line {n}: <{tag}> carries {key}="
                                f"{value!r}, which this does not know to be "
                                "colourless")
            elif key == "transform" and not ROTATE.fullmatch(value):
                problems.append(f"line {n}: transform {value!r} is not a "
                                "rotation")
        if tag == "text" and (el.attrib.get("fill") not in PALETTE
                              or PALETTE[el.attrib["fill"]].role != TEXT):
            problems.append(f"line {n}: text is filled "
                            f"{el.attrib.get('fill')!r}, which PALETTE does "
                            "not hold to the text contrast")
        elements.append(Element(line, tag, dict(el.attrib)))
    if problems:
        raise SystemExit(f"{name}: cannot picture this sheet for the docs:\n  "
                         + "\n  ".join(problems))
    return Drawing(lines[0], float(m.group(1)), float(m.group(2)), elements)


def recolour(line: str, theme: str) -> str:
    """One element line as it is drawn on *theme*'s ground."""
    if theme == "light":
        return line
    return re.sub(r'\b(fill|stroke)="(#[0-9a-f]{6})"',
                  lambda m: f'{m.group(1)}="{PALETTE[m.group(2)].dark}"', line)
