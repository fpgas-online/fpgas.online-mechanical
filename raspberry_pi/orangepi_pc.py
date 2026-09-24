"""The Xunlong Orange Pi PC, measured from photographs.

Not generated, unlike ``boards.py``: Xunlong publish no drawing to generate it
from -- SCRATCH.md has the search -- so every figure here is either theirs,
and says so, or was measured off a photograph by ``measure_orangepi_pc.py``
and is recorded below as it was printed, photograph by photograph.  The
figures the sheet draws are worked out from those records here, in the open:
a mean of every reading, put on the 40-pin header's scale across the board.
So is the tolerance the sheet quotes, the furthest any reading, or any check
the fit did not use, lies from what is drawn.  ``verify_orangepi_pc.py``
recomputes both.

Photographs, fetched by tools/fetch_orangepi_pc.sh:

    v13t, v13b   linux-sunxi, top and bottom of a v1.3 board
    xt, xb       Xunlong's product page, top and bottom of a v1.2 board

Frame as for every Raspberry Pi sheet: lower-left corner of the board, top
view, X right, Y up, millimetres, with the 40-pin header along the top.
"""

from __future__ import annotations

from statistics import mean

from tools.schema import BoardSpec, Feature, Hole, Outline, Source

# ---------------------------------------------------------------------------
# What Xunlong publish
# ---------------------------------------------------------------------------

#: The product page's dimensioned photograph of the underside, "85mm" by
#: "56mm".  The same page's specification table says "85 mm × 55mm", and so
#: does the user manual's; the photographs settle it, below.
WIDTH, HEIGHT = 85.0, 56.0
MANUAL_HEIGHT = 55.0

# ---------------------------------------------------------------------------
# What the photographs say, as measure_orangepi_pc.py printed it
# ---------------------------------------------------------------------------

#: The board's height if its width is 85, read from each photograph's own
#: proportions.  xt is Xunlong's marketing top view, which is out by a
#: millimetre on this and on nothing else, and is taken to be shot tilted.
PHOTO_HEIGHT = {"v13t": 55.99, "v13b": 55.88, "xt": 57.09, "xb": 55.72}

#: Mounting hole centres, from the copper ring round each.
HOLES_SEEN = {
    "MT1": {"v13t": (2.67, 3.05), "v13b": (2.73, 3.03), "xt": (2.84, 2.99), "xb": (2.82, 2.95)},
    "MT2": {"v13t": (82.18, 3.05), "v13b": (82.18, 3.02), "xt": (82.27, 2.99), "xb": (82.24, 2.96)},
    "MT3": {"v13t": (2.75, 53.18), "v13b": (2.86, 53.12), "xt": (2.91, 53.19), "xb": (2.87, 53.09)},
    "MT4": {"v13t": (82.09, 53.30), "v13b": (82.18, 53.12), "xt": (82.26, 53.13), "xb": (82.28, 53.11)},
}
#: The drilled hole, the inner edge of the ring: sixteen readings, four holes
#: in four photographs, from 2.93 to 3.13.
HOLE_DIA_SEEN = (3.10, 3.04, 3.04, 2.93, 3.13, 3.01, 3.01, 3.01,
                 3.03, 3.08, 3.08, 2.97, 3.09, 3.10, 3.11, 3.09)
#: The copper ring's outside diameter, likewise.
RING_DIA_SEEN = (5.01, 4.98, 5.14, 5.08, 5.01, 4.98, 5.13, 5.11,
                 4.99, 4.98, 5.03, 5.03, 4.97, 4.97, 5.03, 5.04)

#: The 40-pin header, from its solder joints in the two bottom views: pin 1
#: (the square pad), the pitch along the rows, pin 1 to pin 39, and the
#: spacing between the rows.
HEADER_SEEN = {"v13b": dict(pin1=(9.58, 51.23), pitch=2.557, span=48.58, rows=2.50),
               "xb": dict(pin1=(9.83, 50.92), pitch=2.551, span=48.48, rows=2.60)}

#: Each part's top face in the two top views, corrected for parallax:
#: x0, y0, x1, y1.
TOP_SEEN = {
    "v13t": {"usb_a_1": (69.91, 44.02, 89.88, 49.80), "ethernet": (68.83, 24.44, 90.17, 40.99),
             "usb_a_2": (72.82, 6.73, 90.39, 20.10), "hdmi": (29.66, -1.99, 44.81, 9.59),
             "power": (6.89, -2.09, 15.11, 10.58), "audio": (61.34, -2.17, 66.99, 11.50),
             "usb_otg": (-1.29, 35.54, 4.68, 42.90), "button": (-1.44, 7.75, 4.23, 12.42),
             "ir": (63.32, 50.13, 68.86, 56.75), "camera": (0.55, 15.46, 6.13, 32.19),
             "uart": (17.49, 0.82, 25.75, 3.31)},
    "xt": {"usb_a_1": (69.45, 43.83, 89.25, 49.07), "ethernet": (67.54, 24.98, 89.25, 40.40),
           "usb_a_2": (72.90, 7.05, 89.07, 19.25), "hdmi": (29.90, -1.66, 44.75, 10.55),
           "power": (7.72, -1.76, 15.63, 10.84), "audio": (61.50, -1.84, 66.59, 12.55),
           "usb_otg": (-0.98, 35.77, 4.76, 43.39), "button": (-0.71, 8.03, 4.52, 12.97),
           "ir": (62.78, 51.67, 68.05, 56.54), "camera": (0.74, 15.84, 6.39, 32.19),
           "uart": (17.49, 1.27, 25.91, 3.94)},
}
#: What the bottom views see of each part past the board edge: its extent
#: along the edge, and how far out it reaches.
OVERHANG_SEEN = {
    "v13b": {"power": (7.9, 16.2, -1.7), "hdmi": (30.7, 45.0, -1.9), "audio": (62.3, 67.3, -1.9),
             "usb_a_1": (43.1, 49.5, 89.0), "ethernet": (24.5, 40.7, 88.8),
             "usb_a_2": (6.9, 20.8, 88.9), "usb_otg": (36.1, 42.1, -0.7)},
    "xb": {"power": (7.8, 16.4, -1.6), "hdmi": (30.8, 45.3, -1.4), "audio": (62.4, 67.4, -1.8),
           "usb_a_1": (43.1, 49.4, 89.3), "ethernet": (25.0, 40.6, 88.9),
           "usb_a_2": (7.2, 20.6, 89.0), "usb_otg": (35.9, 42.2, -0.7)},
}
#: The microSD socket, on the underside and seen square on from below.
MICROSD_SEEN = {"v13b": (-0.6, 16.8, 13.9, 31.2), "xb": (-0.8, 16.5, 13.9, 31.0)}

#: The board's corner radius, fitted where the edge finder sees each corner:
#: lower left, lower right, upper left, upper right.  None where it cannot,
#: which is behind the single USB port in Xunlong's top view.
CORNER_SEEN = {"v13t": (2.27, 2.36, 2.14, 1.96), "v13b": (1.74, 2.10, 2.01, 2.30),
               "xt": (2.28, 2.31, 2.39, None), "xb": (2.32, 2.30, 2.24, 1.96)}

#: Which edge each part overhangs, so which of its sides the bottom views see.
EDGE = {"power": "bottom", "hdmi": "bottom", "audio": "bottom",
        "usb_a_1": "right", "ethernet": "right", "usb_a_2": "right",
        "usb_otg": "left"}

# ---------------------------------------------------------------------------
# The adopted figures, and the tolerance, worked out from the records
# ---------------------------------------------------------------------------


#: The scale across the board.  Fitted to the board's edges alone, the
#: header comes out long in both bottom views, pin 1 to pin 39 48.58 and
#: 48.48 mm where it is 19 x 2.54 = 48.26, and so does everything else
#: measured across the board: the holes came out 79.40 apart, where the
#: cases and Xunlong's PC Plus drawing put them 78.96 to 79.15.  The likeliest
#: cause is the edge finder landing a little inside the routed edge.  So
#: every X is scaled about the board's centre line by the header's own pitch,
#: the most exactly known length on the board; Y, where the header's two rows
#: are too short a ruler, is left as the edges give it.
HEADER_SPAN = mean(h["span"] for h in HEADER_SEEN.values())
X_SCALE = 19 * 2.54 / HEADER_SPAN


def fix_x(x: float) -> float:
    """An X read in the edges' frame, put on the header's scale."""
    return WIDTH / 2 + (x - WIDTH / 2) * X_SCALE


def side_readings(part: str) -> list[list[float]]:
    """Every independent reading of each side of *part*: x0, y0, x1, y1.

    X readings on the header's scale, see X_SCALE.
    """
    sides = [[seen[part][i] for seen in TOP_SEEN.values()] for i in range(4)]
    # Which side each of an overhang's three readings is: its two ends along
    # the edge, and how far it reaches past it.
    lo_hi_reach = {"bottom": (0, 2, 1), "right": (1, 3, 2), "left": (1, 3, 0)}
    if part in EDGE:
        for seen in OVERHANG_SEEN.values():
            for side, value in zip(lo_hi_reach[EDGE[part]], seen[part]):
                sides[side].append(value)
    return [[fix_x(v) for v in vs] if i in (0, 2) else vs
            for i, vs in enumerate(sides)]


def adopted(part: str) -> tuple[float, float, float, float]:
    """A part's box: the mean of every reading of each side."""
    return tuple(round(mean(s), 2) for s in side_readings(part))


#: The holes are drawn on a rectangle, the mean of each pair of readings
#: that should agree: MT1 and MT3 share an X, MT1 and MT2 a Y.  Read one by
#: one they are off square by at most 0.09 mm, which is inside what two
#: photographs of one hole disagree by, and every other model of the board,
#: Xunlong's included, puts them on a rectangle.
_SHARE = {"MT1": ("MT3", "MT2"), "MT2": ("MT4", "MT1"),
          "MT3": ("MT1", "MT4"), "MT4": ("MT2", "MT3")}
HOLES_AT = {k: (round(fix_x(mean(p[0] for h in (k, sx) for p in HOLES_SEEN[h].values())), 2),
                round(mean(p[1] for h in (k, sy) for p in HOLES_SEEN[h].values()), 2))
            for k, (sx, sy) in _SHARE.items()}
HOLE_DIA = round(mean(HOLE_DIA_SEEN), 2)
RING_DIA = round(mean(RING_DIA_SEEN), 2)
PIN1 = (round(fix_x(mean(h["pin1"][0] for h in HEADER_SEEN.values())), 2),
        round(mean(h["pin1"][1] for h in HEADER_SEEN.values()), 2))
MICROSD = tuple(round((fix_x if i % 2 == 0 else float)(
    mean(b[i] for b in MICROSD_SEEN.values())), 2) for i in range(4))
#: The median of every corner the edge finder could see.
CORNERS = sorted(r for rs in CORNER_SEEN.values() for r in rs if r is not None)
CORNER_RADIUS = round(CORNERS[len(CORNERS) // 2], 1)


def board_residuals() -> dict[str, float]:
    """How far the hole and header figures are from each check on them."""
    out = {}
    for label, seen in HOLES_SEEN.items():
        ax, ay = HOLES_AT[label]
        out[f"{label}, photo to photo"] = max(max(abs(fix_x(x) - ax), abs(y - ay))
                                              for x, y in seen.values())
    for name, h in HEADER_SEEN.items():
        out[f"header pin 1 to pin 39 on the header's scale, {name}"] = abs(
            h["span"] * X_SCALE - 19 * 2.54)
        out[f"header rows, {name}"] = abs(h["rows"] - 2.54)
        out[f"header pin 1, {name}"] = max(abs(fix_x(h["pin1"][0]) - PIN1[0]),
                                          abs(h["pin1"][1] - PIN1[1]))
        # Where the edges are, against the header's scale.  The board is
        # drawn 85 wide; a photograph whose board is narrower than that on
        # the header's scale has each edge half the difference from where
        # the drawing puts it, relative to everything inside the board.
        out[f"board edge on the header's scale, {name}"] = abs(
            WIDTH - WIDTH * 19 * 2.54 / h["span"]) / 2
    return out


def part_residuals() -> dict[str, float]:
    """How far each connector's readings are from the box adopted for it."""
    out = {}
    for part in TOP_SEEN["v13t"]:
        box = adopted(part)
        out[part] = max(abs(v - box[i]) for i, side in enumerate(side_readings(part))
                        for v in side)
    return out


#: The tolerances the sheet quotes.  The parts' is their worst residual,
#: 1.04, rounded up.  The holes' and header's worst is 0.28, the v1.3 board's
#: edges on the header's scale; it is quoted as 0.4 rather than 0.3 because
#: Xunlong's PC Plus drawing puts pin 1 0.31 from here, and a sibling board's
#: drawing is the nearest thing to the board's own.  verify_orangepi_pc.py
#: fails if either is less than the worst residual, and holds every
#: third-party model to them as well.
BOARD_TOL = 0.4
PARTS_TOL = 1.1
#: The drilled hole's spread over the sixteen readings, rounded up.
HOLE_DIA_TOL = 0.15

#: Header body, from pin 1: a 2 x 20 header on the 2.54 mm grid is 50.80 by
#: 5.08 round its pins.
HEADER_BOX = (round(PIN1[0] - 1.27, 2), round(PIN1[1] - 1.27, 2),
              round(PIN1[0] + 19 * 2.54 + 1.27, 2), round(PIN1[1] + 2.54 + 1.27, 2))

#: Balloon numbers.  One to five mean what they mean on every Raspberry Pi
#: sheet; the rest are this board's own, for the parts a Pi sheet does not
#: draw and a case round this board has to clear.  Two parts are measured and
#: checked like the rest but not drawn, because both are well inside the
#: outline and on the sheet their balloons had nowhere to go but across one
#: of the adapter's hosts: the debug UART header J3, across JC, and the camera
#: connector CON1, which left the microSD socket's and the power button's
#: balloons only JB to cross.
FEATURE_NUMBERS = {
    6: "HDMI", 7: "3.5 mm audio and video jack", 8: "Micro-USB OTG",
    9: "MicroSD socket", 10: "Power button", 11: "IR receiver",
}

_PARTS = (
    # key, number, label, kind, designator
    ("power", 2, "DC 5 V input, barrel jack", "connector", "J1"),
    ("ethernet", 3, "Ethernet RJ45", "ethernet", "CN3"),
    ("usb_a_1", 4, "USB 2.0 type A, single, upright", "usb_a", "P1"),
    ("usb_a_2", 5, "USB 2.0 type A pair", "usb_a", "USB1"),
    ("hdmi", 6, "HDMI", "connector", "CON2"),
    ("audio", 7, "3.5 mm audio and video jack", "connector", "J4"),
    ("usb_otg", 8, "Micro-USB OTG", "connector", "CN1"),
    ("button", 10, "Power button", "switch", "SW4"),
    ("ir", 11, "IR receiver", "connector", "U22"),
)

ORANGEPI_PC = BoardSpec(
    key="orangepi_pc",
    title="Xunlong Orange Pi PC",
    subtitle="Allwinner H3, v1.2 and v1.3, 85 x 56 mm",
    family="raspberrypi",
    front_edge="top",
    outline=Outline(
        width=WIDTH, height=HEIGHT, corner_radius=CORNER_RADIUS,
        profile_note=f"Corner radius measured {CORNERS[0]:.1f} to "
                     f"{CORNERS[-1]:.1f} mm, drawn at the median."),
    holes=tuple(Hole(x=x, y=y, dia=HOLE_DIA, label=label, kind="mount",
                     keepout_dia=RING_DIA, tol=HOLE_DIA_TOL)
                for label, (x, y) in HOLES_AT.items()),
    features=(
        (Feature(key="gpio40", label="40-pin GPIO header", kind="header",
                 x0=HEADER_BOX[0], y0=HEADER_BOX[1], x1=HEADER_BOX[2],
                 y1=HEADER_BOX[3], number=1, designator="CON3", pin1=PIN1),)
        + tuple(Feature(key=key, label=label, kind=kind, designator=ref,
                        number=number, x0=b[0], y0=b[1], x1=b[2], y1=b[3])
                for key, number, label, kind, ref in _PARTS
                for b in (adopted(key),))
        + (Feature(key="microsd", label="MicroSD socket, underside",
                   kind="connector", designator="J2", number=9, side="bottom",
                   x0=MICROSD[0], y0=MICROSD[1], x1=MICROSD[2], y1=MICROSD[3]),)
    ),
    tolerance=f"MEASURED: holes, header +/-{BOARD_TOL}   parts +/-{PARTS_TOL}",
    sources=(
        Source(label="Board size",
               ref="orangepi.org/html/hardWare/computerAndMicrocontrollers/"
                   "details/Orange-Pi-PC.html",
               note="Xunlong's product page: its dimensioned photograph says 85 "
                    "by 56 mm, its specification table 85 x 55. No other "
                    "mechanical figure is published."),
        Source(label="Photographs, v1.3",
               ref="linux-sunxi.org/Xunlong_Orange_Pi_PC, "
                   "Orange_Pi_PC_v1.3_front.jpg and _back.jpg",
               note="Fetched from the Wayback Machine's January 2026 capture."),
        Source(label="Photographs, v1.2",
               ref="orangepi.org/img/computersAndMmicrocontrollers/PC40.png "
                   "and PC/Rectangle 641.png",
               note="Xunlong's product page."),
        Source(label="Measurement",
               ref="raspberry_pi/measure_orangepi_pc.py",
               note="Held against other models of the board by "
                    "raspberry_pi/verify_orangepi_pc.py."),
    ),
    notes=(
        "Xunlong publish no drawing of this board. Everything but its size is "
        "MEASURED from the photographs listed, good to "
        f"+/-{BOARD_TOL} mm for holes and header and +/-{PARTS_TOL} mm for the "
        "parts: no photograph's reading, and no check on the holes and "
        "header, is further than that from what is drawn.",
        "Across the board the scale is the 40-pin header's 2.54 mm pitch. "
        "Fitted to the board's edges alone, the photographs came out "
        f"{(HEADER_SPAN / (19 * 2.54) - 1) * 100:.1f} % wide.",
        "Xunlong's manual and specification table give 85 x 55 mm. The "
        "photographs measure 55.7 to 57.1 mm, and Xunlong's own dimensioned "
        "photograph and drawing of the PC Plus say 56.",
        "Each part is the mean of every photograph that shows it, top face "
        "from above and overhang from below; raspberry_pi/orangepi_pc.py "
        "records every reading.",
        "The dot is pin 1 of the 40-pin header. KEEPOUT is the copper ring "
        "round each hole.",
        "Plan only: no height is measured, nor how far a microSD card "
        "stands out of its socket.",
    ),
)
