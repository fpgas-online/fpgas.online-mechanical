"""Pmod interface constants, the Digilent Pmod HAT Adapter, and PoE splitters.

Unlike the Tiny Tapeout and Raspberry Pi data, none of this is generated: there
is no machine-readable source to generate it from.  Every number carries its
own provenance in the ``Source`` entries and, where a figure is derived rather
than published, an explicit uncertainty.
"""

from __future__ import annotations

from .schema import BoardSpec, Feature, Hole, Outline, PmodHeader, Source

# ---------------------------------------------------------------------------
# Digilent Pmod Interface Specification 1.2.0 (revised 5 October 2017)
# https://digilent.com/reference/_media/reference/pmod/pmod-interface-specification-1_2_0.pdf
# ---------------------------------------------------------------------------

PMOD_PITCH = 2.54                 # .10 in, both axes, figures 1-5
PMOD_ROW_SPACING = 2.54           # .10 in between the two rows of a 2x6
PMOD_COLUMNS = 6
PMOD_ROWS = 2
PMOD_PIN_SPAN = 12.70             # 5 x 2.54, pin 1 to pin 6 centres
PMOD_HOST_SPACING = 22.86         # .90 in, mandated centre-to-centre spacing
                                  # of adjacent host ports on a board edge
PMOD_KEEPOUT_ACROSS = 10.16       # .40 in, host keep-out box, figure 5
PMOD_KEEPOUT_MARGIN = 3.81        # .15 in, pin envelope to keep-out boundary
PMOD_MODULE_MAX_WIDTH = 20.32     # .80 in, peripheral module width limit

PMOD_SPEC_SOURCE = Source(
    label="Pmod Interface Specification 1.2.0",
    ref="https://digilent.com/reference/_media/reference/pmod/"
        "pmod-interface-specification-1_2_0.pdf",
    note="Digilent, revised 5 October 2017. Host ports on a common board edge "
         "are spaced .90 in (22.86 mm) centre to centre; pins are on a .10 in "
         "(2.54 mm) grid in both axes.",
)

# ---------------------------------------------------------------------------
# Raspberry Pi HAT mechanical specification
# https://github.com/raspberrypi/hats  ->  hat-board-mechanical.pdf
# ---------------------------------------------------------------------------

HAT_WIDTH = 65.0
HAT_HEIGHT_SMT = 56.5             # SMT 40-way header; 56.0 for through-hole
HAT_CORNER_RADIUS = 3.0
HAT_HOLE_DIA = 2.75               # M2.5 clearance, drilled 2.75 +/- 0.05
HAT_HOLES = ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5))

HAT_SPEC_SOURCE = Source(
    label="Raspberry Pi HAT mechanical specification",
    ref="https://github.com/raspberrypi/hats  hat-board-mechanical.pdf",
    note="65 x 56.0 or 65 x 56.5 mm (56.5 for an SMT 40-way header), 3 mm "
         "corner radii, four 2.75 mm holes 3.5 mm in from the edges on a "
         "58 x 49 mm rectangle.",
)

# ---------------------------------------------------------------------------
# Digilent Pmod HAT Adapter, 410-366
# ---------------------------------------------------------------------------
#
# Digilent publish no dimensioned drawing, DXF, STEP or board file for this
# product; its reference manual and schematic carry no mechanical data, and
# there is no board-file repository under github.com/Digilent.  The three Pmod
# host positions below were therefore measured off Digilent's own straight-on
# top view by scripts/measure_pmod_hat.py, which sets scale and origin from the
# four HAT mounting screws.
#
# Raw measurement (see the script's output):
#     JA  pin field centre y = 39.45 mm, 6 pins, pitch 2.548 mm
#     JB  pin field centre y = 16.27 mm, 6 pins, pitch 2.582 mm
#     JC  pin field centre x = 27.57 mm, 6 pins, pitch 2.568 mm
#     JA to JB spacing 23.18 mm against the specified 22.86 mm
#
# The recovered pin pitch sits about 1 % off the true 2.54 mm, which puts the
# uncertainty at roughly +/-0.75 mm across the board.  JA and JB are therefore
# snapped to the 22.86 mm spacing the Pmod specification mandates, keeping
# their measured midpoint; JC is the measured value rounded to 0.1 mm.

_JA_JB_MID = (39.45 + 16.27) / 2
PMOD_HAT_JA_Y = round(_JA_JB_MID + PMOD_HOST_SPACING / 2, 2)
PMOD_HAT_JB_Y = round(_JA_JB_MID - PMOD_HOST_SPACING / 2, 2)
PMOD_HAT_JC_X = 27.6

# Depth of the through-hole field in from the edge the host faces.  The visible
# pin runs in the photo span roughly 6.1 to 10.9 mm in from the edge, which puts
# the two hole rows at about 8.2 and 10.7 mm, so the field centre is 9.4 mm.
PMOD_HAT_FIELD_DEPTH = 9.4
PMOD_HAT_TOL = 0.75

PMOD_HAT = BoardSpec(
    key="pmod-hat-adapter",
    title="Digilent Pmod HAT Adapter",
    subtitle="410-366, fitted to a Raspberry Pi 40-pin GPIO header",
    family="accessory",
    front_edge="bottom",
    outline=Outline(width=HAT_WIDTH, height=HAT_HEIGHT_SMT,
                    corner_radius=HAT_CORNER_RADIUS),
    holes=tuple(
        Hole(x=x, y=y, dia=HAT_HOLE_DIA, keepout_dia=6.2, label=f"MT{i + 1}")
        for i, (x, y) in enumerate(sorted(HAT_HOLES, key=lambda p: (p[1], p[0])))
    ),
    pmods=(
        PmodHeader(key="ja", label="JA", designator="JA", edge="left",
                   cx=PMOD_HAT_FIELD_DEPTH, cy=PMOD_HAT_JA_Y,
                   pin1_x=PMOD_HAT_FIELD_DEPTH - PMOD_ROW_SPACING / 2,
                   pin1_y=PMOD_HAT_JA_Y + PMOD_PIN_SPAN / 2,
                   columns=PMOD_COLUMNS, rows=PMOD_ROWS),
        PmodHeader(key="jb", label="JB", designator="JB", edge="left",
                   cx=PMOD_HAT_FIELD_DEPTH, cy=PMOD_HAT_JB_Y,
                   pin1_x=PMOD_HAT_FIELD_DEPTH - PMOD_ROW_SPACING / 2,
                   pin1_y=PMOD_HAT_JB_Y + PMOD_PIN_SPAN / 2,
                   columns=PMOD_COLUMNS, rows=PMOD_ROWS),
        PmodHeader(key="jc", label="JC", designator="JC", edge="bottom",
                   cx=PMOD_HAT_JC_X, cy=PMOD_HAT_FIELD_DEPTH,
                   pin1_x=PMOD_HAT_JC_X - PMOD_PIN_SPAN / 2,
                   pin1_y=PMOD_HAT_FIELD_DEPTH - PMOD_ROW_SPACING / 2,
                   columns=PMOD_COLUMNS, rows=PMOD_ROWS),
    ),
    features=(
        Feature(key="gpio40", label="40-pin GPIO socket (mates with the Pi)",
                kind="header", x0=7.1, y0=50.5, x1=57.9, y1=55.5,
                note="Position follows the HAT specification, which fixes the "
                     "40-way connector so the HAT mates with the Pi."),
        Feature(key="barrel", label="5 V barrel jack J2", kind="connector",
                x0=45.0, y0=1.0, x1=57.5, y1=13.5,
                note="Approximate; measured from the product photo, +/-1.5 mm.",
                tol=1.5),
    ),
    sources=(
        HAT_SPEC_SOURCE,
        PMOD_SPEC_SOURCE,
        Source(label="Board outline",
               ref="https://digilent.com/reference/add-ons/pmod-hat/start",
               note="Digilent state width 65 mm, length 56.5 mm."),
        Source(label="Pmod host positions",
               ref="https://digilent.com/reference/_media/reference/add-ons/"
                   "pmod-hat/pmod-hat-adapter-top-1000.png",
               note="Measured from Digilent's official top view by "
                    "scripts/measure_pmod_hat.py. Digilent publish no "
                    "dimensioned drawing for this board."),
    ),
    notes=(
        "DERIVED DIMENSIONS. Digilent publish no mechanical drawing, DXF, STEP "
        "or board file for this product. Pmod host positions were measured "
        f"photogrammetrically and are good to about +/-{PMOD_HAT_TOL} mm.",
        "JA and JB face out of the left edge, JC out of the lower edge. All "
        "three are right-angle hosts: the connector body overhangs the board "
        "edge by roughly 3 mm and the through-hole field sits about 9.4 mm in "
        "from it, so a mating Pmod peripheral plugs in from outside that edge.",
        f"JA and JB are snapped to the {PMOD_HOST_SPACING} mm host spacing "
        "the Pmod Interface Specification mandates; they measured 23.18 mm "
        "apart, inside the measurement uncertainty.",
        "The board outline, corner radii and mounting holes are the "
        "Raspberry Pi HAT specification's, which this board conforms to, and "
        "carry that specification's figures. Only the Pmod host positions are "
        "derived.",
    ),
    # The general tolerance block otherwise claimed +/-0.20 on the edge and
    # +/-0.10 on hole position for a board whose host positions are known to
    # +/-0.75, which the sheet's own first note says.
    tolerance=f"HAT spec outline; hosts DERIVED +/-{PMOD_HAT_TOL}, see notes",
)

# ---------------------------------------------------------------------------
# PoE splitters
# ---------------------------------------------------------------------------

WAVESHARE_POE = BoardSpec(
    key="waveshare-poe-usbc",
    title="Waveshare PoE Splitter (25 W), Type-C",
    subtitle="POE-SPLITTER-25W-TYPE-C, extruded aluminium body",
    family="accessory",
    body="enclosure",
    outline=Outline(width=102.5, height=29.6, z_height=24.8, corner_radius=1.5),
    features=(
        Feature(key="rj45_in", label="RJ45 PoE input, in the end plate",
                kind="ethernet", x0=86.5, y0=6.3, x1=102.5, y1=23.3,
                z0=5.9, z1=18.9,
                note="Centred in the 29.6 x 24.8 mm end plate; the opening "
                     "size and position are scaled from the vendor photo, "
                     "+/-1.5 mm. The 13.0 mm aperture height is the same "
                     "measurement taken in Z, so 5.9 mm of end plate remains "
                     "above and below it.", tol=1.5),
        Feature(key="cable_exit", label="Output cable exit",
                kind="connector", x0=0.0, y0=11.8, x1=3.0, y1=17.8,
                note="Captive lead ending in an RJ45 male plug and a USB-C "
                     "male plug. Lead length is not published.", tol=2.0),
    ),
    sources=(
        Source(label="Product page",
               ref="https://www.waveshare.com/poe-splitter-25w-type-c.htm",
               note='Specification table: "DIMENSIONS 102.5 x 29.6 x 24.8mm '
                    '(L x W x H)"; "POE INPUT VOLTAGE 37V ~ 57V"; '
                    '"POWER OUTPUT 5V 5A (MAX)"; IEEE 802.3af/at.'),
        Source(label="Dimension drawing",
               ref="https://www.waveshare.com/img/devkit/accBoard/"
                   "POE-SPLITTER-25W-TYPE-C/POE-SPLITTER-25W-TYPE-C-details-size.jpg",
               note="Annotated 102.50 / 29.60 / 24.80, unit mm, matching the "
                    "specification table."),
    ),
    notes=(
        "Output is 5 V at up to 5 A (25 W) on a USB-C male plug on a captive "
        "lead, not a panel-mounted receptacle.",
        "No panel mounting holes. Each end plate is retained by four corner "
        "screws, whose size and position the vendor does not publish, so any "
        "bracket has to clamp or strap the body.",
        "Body is a finned aluminium extrusion; the fin profile is not "
        "dimensioned here and the outline is the overall envelope.",
    ),
)

GENERIC_POE = BoardSpec(
    key="generic-poe-microusb",
    title="Generic PoE splitter to micro-USB",
    subtitle="IEEE 802.3af, 5 V output, sealed plastic body",
    family="accessory",
    body="enclosure",
    outline=Outline(width=80.0, height=30.0, z_height=24.0, corner_radius=2.0),
    features=(
        Feature(key="rj45_in", label="RJ45 PoE input, moulded into the body",
                kind="ethernet", x0=64.0, y0=6.5, x1=80.0, y1=23.5,
                z0=5.5, z1=18.5,
                note="Position and size derived from vendor photographs, "
                     "+/-2 mm. The 13.0 mm aperture height is the same "
                     "measurement taken in Z, centred in the 24.0 mm end "
                     "face.", tol=2.0),
        Feature(key="cable_exit", label="Output cable exit",
                kind="connector", x0=0.0, y0=12.0, x1=3.0, y1=18.0,
                note="Captive lead ending in an RJ45 male plug and a micro-USB "
                     "male plug; quoted lead length 155 to 205 mm.", tol=2.0),
    ),
    sources=(
        Source(label="DSLRKIT active PoE splitter",
               ref="https://www.amazon.com/DSLRKIT-Active-Splitter-Ethernet-"
                   "Raspberry/dp/B01H37XQP8",
               note='Vendor text: "Body size: 80 x 27 x 22 mm", weight 55 g, '
                    "DC cable 165 mm, RJ45 plug cable 155 mm."),
        Source(label="Adafruit 3785, equivalent unit",
               ref="https://www.adafruit.com/product/3785",
               note='"Body dimensions: 80mm x 30mm x 24mm", weight 54.1 g, '
                    "each lead 205 mm."),
        Source(label="AliExpress listings",
               ref="AliExpress items 1005006389914897, 1005005523161215, "
                   "1005009263116567",
               note="Most listings quote packaging rather than body size. The "
                    "one plausible body figure seen was 95 x 28 x 24 mm, for a "
                    "gigabit variant in a longer case."),
    ),
    notes=(
        "NO SINGLE OFFICIAL SOURCE. These are near-identical clones from "
        "several factories. Two independent sources agree on an 80 mm long "
        "body: DSLRKIT quote 80 x 27 x 22 mm and Adafruit measure "
        "80 x 30 x 24 mm.",
        "The envelope drawn here is the LARGER of those two, 80 x 30 x 24 mm, "
        "and the title block quotes it as a maximum rather than a nominal: a "
        "real part may be up to 3 mm narrower and 2 mm shorter in height.",
        "Length is the one dimension that is not bounded by 80 mm, which is "
        "why the title block gives it +15/-0 while width and height are "
        "maxima: gigabit variants come in a longer case, up to about 95 mm. "
        "Design a cradle that can take that, or check the part before "
        "committing.",
        "No mounting holes: the case is a glued plastic clamshell, so a "
        "bracket has to clamp or strap the body.",
    ),
)

ACCESSORIES: dict[str, BoardSpec] = {
    PMOD_HAT.key: PMOD_HAT,
    WAVESHARE_POE.key: WAVESHARE_POE,
    GENERIC_POE.key: GENERIC_POE,
}
