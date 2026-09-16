"""Pmod interface constants, the Digilent Pmod HAT Adapter, and PoE splitters.

Unlike the Tiny Tapeout and Raspberry Pi data, none of this is generated: there
is no machine-readable source to generate it from.  Every number carries its
own provenance in the ``Source`` entries and, where a figure is derived rather
than published, an explicit uncertainty.
"""

from __future__ import annotations

from dataclasses import replace

from tools.schema import BoardSpec, Feature, Hole, Outline, PmodHeader, Source

# ---------------------------------------------------------------------------
# Digilent Pmod Interface Specification 1.2.0 (revised 5 October 2017)
# https://mith.ro/pmod-spec/, a short link to Digilent's
# pmod-interface-specification-1_2_0.pdf; the sheets print the citation.
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
    ref="https://mith.ro/pmod-spec/",
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
# top view by accessories/measure_pmod_hat.py, which sets scale and origin from the
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
                    "accessories/measure_pmod_hat.py. Digilent publish no "
                    "dimensioned drawing for this board."),
    ),
    notes=(
        # Which numbers to trust is the one thing this sheet has to say, and
        # it is said once: the HAT figures are specification, everything
        # else is read off a photograph.  The barrel jack is named too; a
        # note that said "only the hosts are derived" was wrong about it.
        "Outline, corner radii and mounting holes are the Raspberry Pi HAT "
        "specification's. Everything else is DERIVED from Digilent's "
        "top-view photo, as they publish no drawing: Pmod hosts good to "
        f"about +/-{PMOD_HAT_TOL} mm, the barrel jack to +/-1.5 mm.",
        # Not drawn: the connector bodies, which overhang the edge.  A plate
        # that ends at the board edge would foul them.
        "All three hosts are right-angle: the connector body overhangs the "
        "board edge by roughly 3 mm and a peripheral plugs in from outside "
        "that edge.",
        f"JA to JB is snapped to the {PMOD_HOST_SPACING} mm the Pmod "
        "Interface Specification mandates; it measured 23.18 mm, within the "
        "uncertainty.",
    ),
    # The general tolerance block otherwise claimed +/-0.20 on the edge and
    # +/-0.10 on hole position for a board whose host positions are known to
    # +/-0.75, which the sheet's own first note says.
    tolerance=f"HAT spec outline; hosts DERIVED +/-{PMOD_HAT_TOL}, see notes",
)

#: The adapter's pin map, from the "Pmod Pinout Table" of Digilent's
#: reference manual, which says it applies to Revision B of the board.  Each
#: port's Pmod pin -> (Raspberry Pi 40-pin header pin, the manual's name for
#: it).  Pins 5 and 11 of every port are ground and 6 and 12 the 3V3 rail,
#: which the manual states in prose under the table rather than in it.  Not
#: machine-read: Digilent publish no board file, and the page is behind a
#: bot check, so the table was transcribed by hand and is cited on the
#: comparison page it feeds.
PMOD_HAT_PINS: dict[str, dict[int, tuple[int, str]]] = {
    "JA": {1: (24, "SPI0_CE0/GPIO08"), 2: (19, "SPI0_MOSI/GPIO10"),
           3: (21, "SPI0_MISO/GPIO09"), 4: (23, "SPI0_CLK/GPIO11"),
           7: (35, "PCM_FS/GPIO19/PWM1"), 8: (40, "PCM_DOUT/GPIO21/GPCLK1"),
           9: (38, "PCM_DIN/GPIO20/GPCLK0"), 10: (12, "PCM_CLK/GPIO18/PWM0")},
    "JB": {1: (26, "SPI0_CE1/GPIO07"), 2: (19, "SPI0_MOSI/GPIO10"),
           3: (21, "SPI0_MISO/GPIO09"), 4: (23, "SPI0_CLK/GPIO11"),
           7: (37, "GPIO26"), 8: (33, "PWM1/GPIO13"),
           9: (5, "SCL1/GPIO03"), 10: (3, "SDA1/GPIO02")},
    "JC": {1: (36, "CTS0/GPIO16"), 2: (8, "TXD0/GPIO14"),
           3: (10, "RXD0/GPIO15"), 4: (11, "RTS0/GPIO17"),
           7: (7, "GPCLK0/GPIO04"), 8: (32, "PWM0/GPIO12"),
           9: (29, "GPCLK1/GPIO05"), 10: (31, "GPCLK2/GPIO06")},
}

#: The five GPIOs the manual says the adapter leaves free, quoted: "five
#: GPIO pins (GPIO22, GPIO23, GPIO24, GPIO25, and GPIO27) are unused by the
#: Pmod HAT Adapter."  Checked against the table above at import.
PMOD_HAT_UNUSED_GPIO = (22, 23, 24, 25, 27)

PMOD_HAT_PINOUT_SOURCE = Source(
    label="Pmod HAT Adapter Reference Manual",
    ref="https://digilent.com/reference/add-ons/pmod-hat/reference-manual",
    note='Digilent; "This reference manual applies to Revision B of the '
         'Pmod HAT Adapter." Appendix: Pinout Tables.',
)


def _check_hat_pins() -> None:
    """The transcribed table has to agree with the manual's own prose."""
    used = {int(name.rsplit("GPIO", 1)[1][:2]) for port in PMOD_HAT_PINS.values()
            for _, name in port.values()}
    free = {n for n in range(2, 28)} - used
    if free != set(PMOD_HAT_UNUSED_GPIO):
        raise SystemExit(f"PMOD_HAT_PINS leaves GPIO {sorted(free)} unused, "
                         f"but the manual says {PMOD_HAT_UNUSED_GPIO}")


_check_hat_pins()

# ---------------------------------------------------------------------------
# PoE splitters
# ---------------------------------------------------------------------------

WAVESHARE_POE = BoardSpec(
    key="waveshare-poe-usbc",
    title="Waveshare PoE Splitter 25 W, Type-C",
    subtitle="POE-SPLITTER-25W-TYPE-C, extruded aluminium body",
    family="accessory",
    body="enclosure",
    outline=Outline(width=102.5, height=29.6, z_height=24.8,
                    corner_radius=1.5, constant_section=True),
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
        "Output is a USB-C male plug on a captive lead from the cable exit, "
        "not a receptacle. Lead length is not published; allow for the plug "
        "and its bend radius.",
        "No mounting holes: a bracket has to clamp or strap the body. The "
        "end-plate corner screws are not published.",
        "Finned extrusion; the fins are not drawn and the outline is the "
        "overall envelope.",
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
        "NO SINGLE OFFICIAL SOURCE: these are clones from several factories. "
        "The envelope drawn is the larger of the two published figures, "
        "Adafruit's 80 x 30 x 24 mm over DSLRKIT's 80 x 27 x 22 mm, so a "
        "real part may be up to 3 mm narrower and 2 mm lower.",
        "Gigabit variants come in a longer case, up to about 95 mm, hence "
        "L +15/-0 in the title block. Allow for it or check the part.",
        "No mounting holes: the case is a glued clamshell, so a bracket has "
        "to clamp or strap the body.",
        "Output is a micro-USB male plug on a captive lead, quoted at 155 to "
        "205 mm, from the cable exit. The plug and its bend radius, not the "
        "body, set how close the splitter can sit to the board it feeds.",
    ),
)

# ---------------------------------------------------------------------------
# PCI Express M.2 Specification, Revision 1.0, 1 November 2013
# ---------------------------------------------------------------------------

M2_CARD_WIDTH = 22.00             # section 2.3.4.3, figure 13: 22 +/-0.15
M2_2280_LENGTH = 80.00            # section 2.3.4.3, figure 13: 80 +/-0.15
M2_NOTCH_DIA = 3.50               # figures 18 and 19: the half-moon cutout
M2_STANDOFF_DIA = 5.50            # section 2.5.4.2, figure 73, +/-0.10
M2_STANDOFF_THREAD = "M2 x 0.4"   # section 2.5.4.2, the shouldered stand-off

#: Distance from the connector datum to a module's retention screw, which is
#: that module's own length: the half-moon cutout is centred on the module's
#: far end edge, so the card ends where the screw is.
M2_LENGTHS = {"2230": 30.00, "2242": 42.00, "2260": 60.00, "2280": 80.00}

M2_SPEC_SOURCE = Source(
    label="PCI Express M.2 Specification",
    ref="PCI-SIG, Revision 1.0, 1 November 2013",
    note="Section 2.3.4.3 and figure 13: a Type 2280 module is 22 +/-0.15 by "
         "80 +/-0.15 mm with a half-moon cutout for the retention screw "
         "centred on its far end edge, 11 mm from either side. Section 2.5: "
         'a "5.5 mm diameter Keep-out zone at the end for attaching a screw", '
         "on an M2 x 0.4 shouldered stand-off, figure 73.",
)

# ---------------------------------------------------------------------------
# Waveshare PoE M.2 HAT+ (B), on a Raspberry Pi 5
# ---------------------------------------------------------------------------
#
# Waveshare sell three PoE-plus-M.2 HATs for the Pi 5 and only this one takes
# a 2280 card: the plain PoE M.2 HAT+ and the (C) are "Compatible with M.2
# hard drives of 2230 / 2242 sizes", the (B) with "2230 / 2242 / 2260 / 2280".
# The (B) is also the only one the size of a Pi: 85.00 x 56.00 against the
# plain one's 70.00 x 56.50 and the (C)'s 65.00 x 56.50, both of which their
# own dimension drawings state.
#
# Everything below in the RASPBERRY PI's frame: origin at the Pi's lower-left
# corner, X right, Y up, viewed from the component side.  Waveshare draw this
# HAT with its 40-pin header along the lower edge, which is the assembly seen
# from above and turned through 180 degrees; accessories/measure_poe_m2_hat.py
# undoes the rotation and checks it by requiring the four mounting holes to
# land on the Pi's own 3.5 / 61.5 by 3.5 / 52.5.
#
# DECLARED, printed on Waveshare's dimension drawing with "Unit: mm":
#     85.00 and 56.00    the outline
#     58.00 and 49.00    the mounting hole rectangle
#     3.50               hole centre to the board edge at the M.2 socket end
#     3.00               how far the 2280 standoff projects past the far edge
#
# DERIVED, by accessories/measure_poe_m2_hat.py from the same drawing, because
# Waveshare dimension no part of the M.2 system but that 3.00: scale and
# origin from the mounting holes, then the three standoffs that sit clear of
# the board edge.  Each gives the connector datum independently, through the
# M.2 specification's 30 / 42 / 60 mm module lengths, and the three agree to
# 0.04 mm.  The board's own edges then come out 84.88 x 55.88 against the
# declared 85.00 x 56.00, and the 2280 standoff -- predicted at 80 mm from
# that datum and never measured -- reaches exactly the 88.00 mm the declared
# 3.00 puts it at.  The worst of those three residuals is 0.12 mm.

POE_M2_HAT_WIDTH = 85.00
POE_M2_HAT_HEIGHT = 56.00
POE_M2_HAT_HOLE_PITCH = (58.00, 49.00)
POE_M2_HAT_HOLE_EDGE = 3.50
POE_M2_STANDOFF_OVERHANG = 3.00

#: Where a seated card's mating edge sits, and the axis it sits on.
POE_M2_DATUM_X = 5.07
POE_M2_AXIS_Y = 18.26

#: Outside diameter of the standoff bosses, measured: all four read the same,
#: and 0.37 mm over the M.2 specification's Ø5.50 guideline figure.  It is the
#: boss, not the screw, that decides how far the assembly reaches past the
#: Pi's edge, so it is the boss that is drawn.
POE_M2_BOSS_DIA = 5.87

#: Everything derived from the drawing, to the worst residual on a check that
#: was not used to make the fit.
POE_M2_HAT_TOL = 0.2

#: The M.2 socket's own footprint, from the same drawing but read off the
#: moulding rather than off a circle, so an order of magnitude looser.  Its
#: length is taken from the end the search window did not clip and mirrored
#: about the axis the standoffs define, which is the axis a socket for a
#: 22 mm module is symmetric about.
POE_M2_SOCKET_TOL = 1.0

_STANDOFF_Y = POE_M2_AXIS_Y

POE_M2_HAT = BoardSpec(
    key="waveshare-poe-m2-hat-b",
    title="Waveshare PoE M.2 HAT+ (B)",
    # BoardSpec requires a subtitle and no title block ever carries this
    # one: the part is never a sheet's subject.  It is here for a reader of
    # this module, and because the field has no default.
    subtitle="PoE M.2 HAT+ (B), fitted on a Raspberry Pi 5 40-pin header",
    family="accessory",
    front_edge="top",
    outline=Outline(width=POE_M2_HAT_WIDTH, height=POE_M2_HAT_HEIGHT,
                    corner_radius=HAT_CORNER_RADIUS),
    # The four HAT mounting holes are the Pi's own -- the drawing's 58.00 x
    # 49.00 and 3.50 are the Pi's 3.5 / 61.5 by 3.5 / 52.5 -- so they are not
    # repeated here: the sheet draws the Pi, and a second circle a fortieth of
    # a millimetre outside the first is a smudge, not information.  What is
    # here is the M.2 system, which is this board's own.
    holes=tuple(
        Hole(x=POE_M2_DATUM_X + M2_LENGTHS[n], y=_STANDOFF_Y,
             dia=2.0, label=n, kind="aux", keepout_dia=POE_M2_BOSS_DIA,
             tol=POE_M2_HAT_TOL)
        for n in ("2230", "2242", "2260", "2280")
    ),
    features=(
        Feature(key="m2_socket", label="M.2 M-key socket", kind="connector",
                x0=1.02, y0=POE_M2_AXIS_Y - 11.07,
                x1=10.20, y1=POE_M2_AXIS_Y + 11.07,
                note="Moulding, end posts and solder tails together. Read off "
                     "Waveshare's drawing, +/-1 mm; they dimension none of it.",
                tol=POE_M2_SOCKET_TOL),
    ),
    sources=(
        Source(label="Dimension drawing",
               ref="https://www.waveshare.com/w/upload/d/d9/"
                   "PoE-M.2-HAT-Plus-B-details-size.jpg",
               note='Annotated 85.00, 56.00, 58.00, 49.00, 3.50 and 3.00, '
                    '"Unit: mm". The 3.00 is the 2280 standoff\'s projection '
                    "past the board edge; nothing else of the M.2 system is "
                    "dimensioned."),
        Source(label="Product wiki",
               ref="https://www.waveshare.com/wiki/PoE_M.2_HAT%2B_(B)",
               note='"Compatible with M.2 hard drives of 2230 / 2242 / 2260 / '
                    '2280 sizes", IEEE 802.3af/at, Pi 5 only. Its '
                    '"Product size: 56.5mm x 70.0mm" is the plain PoE M.2 '
                    "HAT+'s size and contradicts this board's own drawing."),
        HAT_SPEC_SOURCE,
        M2_SPEC_SOURCE,
    ),
    # No notes.  A sheet's notes are its SUBJECT's: tools/drafting/
    # board_sheet.py's _sheet_text reads spec.notes and never the overlay's,
    # so anything written here would be a provenance note no drawing prints.
    # What this part's figures are and how good they are is said on the sheet
    # that draws it, by ACC_M2_HAT_NOTES in tools/generate_diagrams.py.
    tolerance=f"Waveshare outline; M.2 system DERIVED +/-{POE_M2_HAT_TOL}",
)

# ---------------------------------------------------------------------------
# SQRL Acorn CLE-215+ in that HAT
# ---------------------------------------------------------------------------
#
# SQRL published no mechanical drawing and the company's site is gone; what
# they did publish, and what the Internet Archive still has, is the sentence
# below.  So the card is drawn as the M.2 specification's 2280 outline with
# SQRL's own one millimetre added to the width, and the sheet says that the
# heatsink the CLE-215+ carries is not published and is not drawn.

ACORN_WIDTH = M2_CARD_WIDTH + 1.00
ACORN_LENGTH = M2_2280_LENGTH

ACORN_SOURCE = Source(
    label="SQRL Acorn CLE-215+ product page",
    ref="https://web.archive.org/web/2020/"
        "http://www.squirrelsresearch.com/acorn-cle-215-plus/",
    note='Squirrels Research Labs, captured 2020; the site is gone. "An M.2 '
         "2280 M-Key (PCIe) slot is required to use Acorn. Acorn should fit "
         "comfortably in most M.2 slots, but it is one millimeter wider than "
         'the official specifications. Ensure you have clearance."',
)

ACORN_CARD = Feature(
    key="acorn",
    label="SQRL Acorn CLE-215+, M.2 2280 M-key",
    # What goes on the view, where the clear paper inside the card's own
    # outline runs from the socket to the mounting hole column's witness
    # line and the full name does not fit between them.
    designator="Acorn CLE-215+",
    kind="outline",
    x0=POE_M2_DATUM_X, y0=POE_M2_AXIS_Y - ACORN_WIDTH / 2,
    x1=POE_M2_DATUM_X + ACORN_LENGTH, y1=POE_M2_AXIS_Y + ACORN_WIDTH / 2,
    note="Seated: the mating edge is at the connector datum and the far end "
         "edge passes through the 2280 retention screw. 23 mm wide, which is "
         "SQRL's one millimetre over the specification's 22. The heatsink is "
         "not published and is not drawn.",
    tol=POE_M2_HAT_TOL,
)

#: The overlay the assembly sheet draws: the HAT with a card in it.  One
#: phantom part rather than two, because the card's position is the HAT's
#: geometry -- the socket and the standoff put it where it is -- and a nested
#: overlay would have to carry that relationship somewhere else.
POE_M2_HAT_WITH_ACORN = replace(
    POE_M2_HAT,
    key="waveshare-poe-m2-hat-b-acorn",
    # Unread, like the one it replaces, and required for the same reason.
    subtitle="PoE M.2 HAT+ (B) with an Acorn CLE-215+, on a Raspberry Pi 5",
    features=POE_M2_HAT.features + (ACORN_CARD,),
    sources=POE_M2_HAT.sources + (ACORN_SOURCE,),
)

ACCESSORIES: dict[str, BoardSpec] = {
    PMOD_HAT.key: PMOD_HAT,
    WAVESHARE_POE.key: WAVESHARE_POE,
    GENERIC_POE.key: GENERIC_POE,
    POE_M2_HAT.key: POE_M2_HAT,
}
