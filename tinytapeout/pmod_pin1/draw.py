"""The pin 1 pictures: where pin 1 is on the demo board's Pmod sockets, and
on the Pmod HAT Adapter's ports.

Two drawings for the docs site, not sheets: each is drawn here on a
``Canvas`` and written by ``tools/docs_images.py``, light and dark, SVG and
PNG, through the same palette and reader as the sheets' pictures, which
``tools/check_docs_images.py`` then holds them to.  ``PICTURES`` says which.

Stylised: only what tells one pin from another is drawn.  The demo board's
pads, nets, silkscreen and socket bodies are ``pmods_v3p2.py``'s, read out of
the board file, and drawn where the file puts them; only the lettering is
sized for reading rather than to the board's own.  The HAT's are ``hat.py``'s.

Each is drawn to its own scale and no wider than ``tools.docs_images``
prints a picture, so that no text in them prints smaller than its 2.5 mm.
"""

from __future__ import annotations

import math

from tinytapeout.pmod_pin1 import hat
from tinytapeout.pmod_pin1.pmods_v3p2 import (FRONT_EDGE_X, FRONT_EDGE_Y,
                                              SOCKETS, SOURCE)
from tools.drafting import style
from tools.drafting.canvas import Canvas
from tools.kicad_pcb import Arc

#: Paper millimetres to a board millimetre, on the HAT.
HAT_SCALE = 2.6
#: The least text, in capitals, and the larger sizes the pictures use.
T = 2.6
T_CALLOUT = 3.5
T_CAPTION = 3.5
#: Paper round the drawing.
MARGIN = 1.0

INK = style.C_LINE              # the drawing, and the board's own printing
PAD = style.C_COMPONENT         # pad outlines
PIN1 = style.C_HIGHLIGHT        # pin 1
WARN = style.C_FRAME_B          # the corner mark that is not pin 1
POWER = style.C_DIM             # what the pictures add: GND and 3V3
QUIET = "#666666"               # the source line
BODY = style.C_PHANTOM          # a socket body, over the board edge
FILL = style.C_FILL_TABLE_HEAD  # a block the board prints solid
MASK = style.C_FILL_HOLE        # inside a pad: the ground


def _pad(c: Canvas, x: float, y: float, d: float, number: str,
         square: bool) -> None:
    """A pad *d* across at (*x*, *y*) on the paper, its number inside."""
    if square:
        c.rect(x - d / 2, y - d / 2, d, d, weight=0.6, colour=PIN1,
               fill=MASK)
    else:
        c.circle(x, y, d / 2, w=style.W_COMPONENT, colour=PAD, fill=MASK)
    c.text(x, y, number, size=T, colour=PIN1 if square else INK,
           anchor="middle", baseline="middle", bold=square)


def _leader(c: Canvas, x0, y0, x1, y1, colour) -> None:
    """A leader from (*x1*, *y1*) to an arrowhead at (*x0*, *y0*)."""
    c.line(x1, y1, x0, y0, w=style.W_THIN, colour=colour)
    c.arrow(x0, y0, math.degrees(math.atan2(y0 - y1, x0 - x1)),
            colour=colour)


# ---------------------------------------------------------------------------
# the demo board
# ---------------------------------------------------------------------------

#: Paper millimetres to a board millimetre, on the demo board.
TT_SCALE = 2.7
#: How far past pad 1 the pin 1 leader ends, in board millimetres: clear
#: of the socket body's corner, which is 1.27 past the pad's centre.
_PIN1_RUN = 3.6

#: The board window drawn, in KiCad millimetres: from just left of the
#: first socket's corner mark, where its warning starts, to the end of the
#: last socket's pin 1 leader.  Above the boxes, the warnings and the
#: caption; below the bodies, the pin 1 callouts and the source line.
_LEFT = min(s["corner"][0] for s in SOCKETS) - 1.8
_RIGHT = max(s["pads"][0][2] for s in SOCKETS) + _PIN1_RUN + 0.3
_TOP = min(min(seg[1] for seg in s["lines"]) for s in SOCKETS) - 6.6
_BODY_END = max(max(seg[1], seg[3]) for s in SOCKETS for seg in s["body"])
_BOTTOM = _BODY_END + 5.4


def tt_demoboard() -> Canvas:
    S = TT_SCALE
    w = (_RIGHT - _LEFT) * S + 2 * MARGIN
    h = (_BOTTOM - _TOP) * S + 2 * MARGIN
    c = Canvas(w, h)

    def X(x: float) -> float:
        return MARGIN + (x - _LEFT) * S

    def Y(y: float) -> float:          # KiCad's Y is down, the canvas's up
        return MARGIN + (_BOTTOM - y) * S

    c.text(X(_LEFT), h - MARGIN - T_CAPTION,
           "Tiny Tapeout demo board v3.2: the Pmod sockets from above",
           size=T_CAPTION, bold=True)

    # The board's front edge, the line every socket hangs over, named in
    # the gap between the first socket's pin 1 leader and the next body.
    ex0, ex1 = max(FRONT_EDGE_X[0], _LEFT), min(FRONT_EDGE_X[1], _RIGHT)
    c.line(X(ex0), Y(FRONT_EDGE_Y), X(ex1), Y(FRONT_EDGE_Y),
           w=style.W_OUTLINE, colour=INK)
    gap = (SOCKETS[0]["pads"][0][2] + _PIN1_RUN
           + min(seg[0] for seg in SOCKETS[1]["body"])) / 2
    c.text(X(gap), Y(FRONT_EDGE_Y) - 1.4 - T, "board", size=T,
           anchor="middle")
    c.text(X(gap), Y(FRONT_EDGE_Y) - 2.8 - 2 * T, "edge",
           size=T, anchor="middle")

    for s in SOCKETS:
        for x1, y1, x2, y2 in s["body"]:
            c.line(X(x1), Y(y1), X(x2), Y(y2), w=style.W_PHANTOM,
                   colour=BODY, dash=style.D_PHANTOM)
        for x1, y1, x2, y2 in s["blocks"]:
            c.rect(X(min(x1, x2)), Y(max(y1, y2)), abs(x2 - x1) * S,
                   abs(y2 - y1) * S, weight=style.W_THIN, colour=INK,
                   fill=FILL)
        for x1, y1, x2, y2 in s["lines"]:
            c.line(X(x1), Y(y1), X(x2), Y(y2), w=style.W_COMPONENT,
                   colour=INK)
        for a in s["arcs"]:
            _cx, _cy, rad = Arc(*a).centre_radius()
            # Which way round: the side of the chord its mid point is on.
            cross = ((a[2] - a[0]) * (a[5] - a[1])
                     - (a[3] - a[1]) * (a[4] - a[0]))
            c.arc(X(a[0]), Y(a[1]), X(a[4]), Y(a[5]), rad * S,
                  sweep=0 if cross > 0 else 1, w=style.W_COMPONENT,
                  colour=INK)
        for text, x, y, height, justify, bold in s["texts"]:
            anchor = ("end" if "right" in justify else
                      "start" if "left" in justify else "middle")
            # Seven tenths of the board's own height, at this scale: the
            # board's narrow monospace, set in the drawing's face, would
            # otherwise reach into the line below.
            c.text(X(x), Y(y), text, size=max(T, 0.7 * height * S),
                   anchor=anchor, bold=bold)
        for n, shape, x, y, size, _net in s["pads"]:
            _pad(c, X(x), Y(y), size * S, n, shape == "rect")

        pads = {p[0]: p for p in s["pads"]}
        # GND and 3V3 down their column, in the socket body: the nets of
        # pads 5 and 11, and of 6 and 12.
        mid = Y((FRONT_EDGE_Y + _BODY_END) / 2)
        for n, what in (("5", "GND"), ("6", "3V3")):
            net = {"GND": "GND", "3V3": "+3V3"}[what]
            if {pads[n][5], pads[str(int(n) + 6)][5]} != {net}:
                raise SystemExit(f"{s['ref']}: pads {n} and {int(n) + 6} "
                                 f"are not both on {what}")
            c.text(X(pads[n][2]) + T / 2, mid, what, size=T, colour=POWER,
                   anchor="middle", bold=True, rotate=90)

        # Pin 1: a leader from the square pad's corner down past the body,
        # and what it is under the body, beside the leader.
        _n, _shape, px, py, size, _net = pads["1"]
        half = size / 2 * S
        tx, ty = X(px + _PIN1_RUN), Y(_BODY_END) - 0.8
        _leader(c, X(px) + half, Y(py) - half, tx, ty, PIN1)
        c.text(tx, ty - 0.8 - T_CALLOUT, "PIN 1", size=T_CALLOUT,
               colour=PIN1, bold=True, anchor="end")
        c.text(tx, ty - 2.2 - T_CALLOUT - T, "square pad", size=T,
               colour=PIN1, anchor="end")

        # The corner mark, and what it is not.
        for x1, y1, x2, y2 in s["mark"]:
            c.line(X(x1), Y(y1), X(x2), Y(y2), w=0.7, colour=WARN)
        cx, cy = s["corner"]
        top = Y(min(seg[1] for seg in s["lines"]))
        wx, wy = X(cx) - 1.2 * S, top + 2.0
        _leader(c, X(cx) - 0.4, Y(cy) + 0.4, wx, wy, WARN)
        c.text(wx - 0.4, wy + 1.0, "this corner mark is pin 6, 3.3 V",
               size=T, colour=WARN)
        c.text(wx - 0.4, wy + 2.4 + T, "NOT PIN 1", size=T_CALLOUT,
               colour=WARN, bold=True)

    c.text(X(_LEFT), MARGIN + 0.2,
           f"Pads, nets, silkscreen and socket bodies from Tiny Tapeout's "
           f"tt-demo-pcb at {SOURCE['commit']}, the rev 3.2 board file",
           size=T, colour=QUIET)
    return c


# ---------------------------------------------------------------------------
# the Pmod HAT Adapter
# ---------------------------------------------------------------------------

#: Paper round the board: a caption above it and a source line below.
_HAT_ABOVE = 9.0
_HAT_BELOW = 14.0
_HAT_SIDE = 4.0
#: The pads are drawn this size, which Digilent do not publish.
_HAT_PAD = 2.0


def pmod_hat() -> Canvas:
    S = HAT_SCALE
    w = hat.WIDTH * S + 2 * _HAT_SIDE
    h = hat.HEIGHT * S + _HAT_ABOVE + _HAT_BELOW
    c = Canvas(w, h)

    def X(x: float) -> float:
        return _HAT_SIDE + x * S

    def Y(y: float) -> float:
        return _HAT_BELOW + y * S

    c.text(X(0), h - 1.0 - T_CAPTION,
           "Digilent Pmod HAT Adapter Rev. B, from above",
           size=T_CAPTION, bold=True)

    c.rect(X(0), Y(0), hat.WIDTH * S, hat.HEIGHT * S,
           weight=style.W_OUTLINE, colour=INK,
           radius=hat.CORNER_RADIUS * S)
    for x, y in hat.HOLES:
        c.circle(X(x), Y(y), hat.HOLE_DIA / 2 * S, w=style.W_THIN,
                 colour=INK)
    f = hat.HEADER
    c.rect(X(f.x0), Y(f.y0), (f.x1 - f.x0) * S, (f.y1 - f.y0) * S,
           weight=style.W_COMPONENT, colour=PAD, fill=FILL)
    c.text(X((f.x0 + f.x1) / 2), Y((f.y0 + f.y1) / 2),
           "40-pin header, onto the Raspberry Pi", size=T, anchor="middle",
           baseline="middle")
    b = hat.BARREL
    c.rect(X(b.x0), Y(b.y0), (b.x1 - b.x0) * S, (b.y1 - b.y0) * S,
           weight=style.W_PHANTOM, colour=BODY, dash=style.D_PHANTOM)
    c.text(X((b.x0 + b.x1) / 2), Y((b.y0 + b.y1) / 2) + 0.8,
           "5 V jack", size=T, anchor="middle")
    c.text(X((b.x0 + b.x1) / 2), Y((b.y0 + b.y1) / 2) - 0.8 - T,
           "J2", size=T, anchor="middle")

    d = _HAT_PAD * S
    for name, port in hat.PORTS.items():
        pins, left = port["pins"], port["edge"] == "left"
        xs = [p[0] for p in pins.values()]
        ys = [p[1] for p in pins.values()]
        pad = _HAT_PAD / 2 + 0.6
        c.rect(X(min(xs) - pad), Y(min(ys) - pad),
               (max(xs) - min(xs) + 2 * pad) * S,
               (max(ys) - min(ys) + 2 * pad) * S,
               weight=style.W_COMPONENT, colour=INK)
        for n, (x, y) in pins.items():
            _pad(c, X(x), Y(y), d, str(n), n == 1)
        (x1, y1), (x5, y5), (x6, y6) = pins[1], pins[5], pins[6]
        out = pad + 0.5
        if left:
            # As printed: 3V3 and GND to the right of pins 6 and 5, the 1
            # under pin 1 and the port's name under pin 7.
            for (x, y), what in (((x6, y6), "3V3"), ((x5, y5), "GND")):
                c.text(X(x + out), Y(y), what, size=T, baseline="middle",
                       bold=True)
            c.text(X(x1), Y(y1 - out) - T, "1", size=T, anchor="middle",
                   bold=True)
            c.text(X(pins[7][0]), Y(y1 - out) - T, name, size=T,
                   anchor="middle", bold=True)
            # Pin 1: a leader from below the square pad, down and right.
            tx, ty = X(x1) + 7.5, Y(y1) - 13.0
            _leader(c, X(x1) + d / 2, Y(y1) - d / 2, tx, ty + T_CALLOUT
                    + 1.0, PIN1)
            c.text(tx, ty, "PIN 1", size=T_CALLOUT, colour=PIN1, bold=True)
        else:
            # Turned a quarter, reading up: 3V3 and GND above pins 6 and 5,
            # the 1 beside pin 1 and the port's name beside pin 7.
            for (x, y), what in (((x6, y6), "3V3"), ((x5, y5), "GND")):
                c.text(X(x) + T / 2, Y(y + out), what, size=T, bold=True,
                       rotate=90)
            c.text(X(x1 + out) + T, Y(y1), "1", size=T, bold=True,
                   rotate=90, anchor="middle")
            c.text(X(x1 + out) + T, Y(pins[7][1]), name, size=T,
                   bold=True, rotate=90, anchor="middle")
            tx, ty = X(x1) + 9.0, Y(y1) + 11.0
            _leader(c, X(x1) + d / 2, Y(y1) + d / 2, tx - 0.4, ty - 0.6,
                    PIN1)
            c.text(tx, ty, "PIN 1", size=T_CALLOUT, colour=PIN1, bold=True)

    c.text(X(0), 2.4 + 2 * T,
           f"Ports where accessories/parts.py measured them, "
           f"+/-{hat.TOLERANCE} mm; pads not to size.", size=T, colour=QUIET)
    c.text(X(0), 1.0 + T,
           "Pin 1 and the printing as in Digilent's photographs of the "
           "board.", size=T, colour=QUIET)
    return c


#: The pictures, by where each is written less its ``-light``/``-dark``.
PICTURES = {
    "tinytapeout/pmod_pin1/output/docs/tt-demoboard-v3.2-pmods": tt_demoboard,
    "tinytapeout/pmod_pin1/output/docs/digilent-pmod-hat-ports": pmod_hat,
}
