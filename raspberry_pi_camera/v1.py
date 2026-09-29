"""The original Raspberry Pi Camera Module, the OV5647 board lettered Rev 1.3.

Lettered "Raspberry Pi Camera Rev 1.3" on its lens side, and known as the
v1.3.

Hand-curated, with per-value provenance, because there is nothing to
generate it from.  Raspberry Pi never published a mechanical drawing for this
camera (see ``README.md`` in this directory), so where ``boards.py`` is read
out of Raspberry Pi Ltd's own vector drawings, this module is written by hand
from the best of what does exist, in the manner of ``accessories/parts.py``.

Sources, all cached by ``tools/fetch_raspberry_pi_camera.sh``:

``GVL``   Gert van Loo, "Raspberry-Pi Camera module", one page, Rev 1.0,
          21 May 2013: "Measurements from Raspberry-Pi Camera module / Best
          effort, manually measured, no guarantees!"  Posted in the Raspberry
          Pi forum's camera board thread "Mechanical data" the same day: "As
          with the raspberry-Pi mechanical data it is hand measured, accuracy
          about 0.05 mm no guarantees."  A plan view and a side elevation, to
          scale.  **The primary source.**  Every figure below marked GVL is
          one that sheet prints; ``verify.py`` finds each in its text layer.
``GVL-scaled``  Drawn on that sheet but not dimensioned, so scaled off it by
          ``measure_cm1.py``.  The scale comes from the sheet's two overall
          dimensions and is checked against every other figure it prints;
          the worst of those residuals is 0.09 mm, which with Gert's
          own 0.05 is where ``SCALED_TOL`` comes from.
``SPY``   Raspberry Pi Spy, "Raspberry Pi Camera Module Mechanical
          Dimensions", 17 May 2013: a board lettered "Raspberry Pi Camera
          Rev 1.3" measured "using a set of plastic calipers".  A second,
          independent hand measurement, every figure on it a whole or half
          millimetre.
``RPI``   Raspberry Pi's camera documentation, product table: Camera Module
          1, "Around 25 × 24 × 9 mm".
``CM2``   Raspberry Pi Ltd's Camera Module 2 drawing, ``RPI-CAM-V2_1``, as
          ``extract.py`` reads it into ``boards.py``.  Not this board, but the
          board that replaced it; used only to check the hole pattern.
``B0033`` Arducam's drawing of their B0033, an OV5647 board sold as "fully
          compatible with official one".  A clone, not the Raspberry Pi
          board, and not the source of any figure here; it corroborates the
          hole pattern and hole size, and disagrees about the lens.

``verify.py`` checks that each quoted figure is on its source.  It cannot
check what the figure dimensions; that is read off the drawing, by eye, and
said beside each figure here.

Frame
-----
The family's, :mod:`tools.schema`: origin at the lower-left corner, X across
the 25 mm, Y up the 23.9 mm, millimetres, looking at the lens side, with the
FFC connector on the underside against the **upper** edge.  Gert's sheet has
the connector on its left edge; it is turned a quarter turn clockwise to get
here, so his "from the connector edge" is ``BOARD_HEIGHT - y`` and his "from
the lower edge" is ``x``.

Heights are along Z, **zero on the lens-side face of the board**, positive
toward the lens.  The underside is at ``-BOARD_THICKNESS`` and everything on
it is below that.

What a camera holder needs is at module level: ``BOARD_WIDTH``,
``BOARD_HEIGHT``, ``BOARD_THICKNESS``, ``CORNER_RADIUS``, ``HOLES`` and
``HOLE_DIA``, ``OPTICAL_AXIS``, ``LENS``, ``LENS_PROFILE``, ``TAIL``,
``FFC`` and ``FFC_BODY``, ``FFC_CABLE`` and ``FFC_CABLE_WIDTH``, the
``*_Z`` heights with ``OVERALL_HEIGHT``, and the ``*_TOL`` error bars.  ``CM1`` is the same data as a
:class:`tools.schema.BoardSpec` for the drawing.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, Source

# ---------------------------------------------------------------------------
# Error bars.  Each figure below says which one it carries.
# ---------------------------------------------------------------------------

#: Outline and hole positions.  GVL prints them to 0.05 and claims about
#: 0.05; the hole centres it prints agree with Raspberry Pi's own Camera
#: Module 2 drawing to 0.03 (``verify.py`` holds it to that), and SPY and
#: B0033 both give the same 21 x 12.5 rectangle 2 mm in from the edges.
HOLE_TOL = 0.1

#: Hole diameter.  Every source says 2, and none says it finer: GVL prints
#: "ø 2" with no decimal, SPY "~2mm", the clone "R=1.00mm".  The Camera
#: Module 2's are 2.2 on the same centres, and nothing here rules that out
#: for this board, so the diameter carries enough to include it.
HOLE_DIA_TOL = 0.2

#: The lens and sensor module.  GVL puts its near side 5.1 from the connector
#: edge, SPY 5.5, and SPY reads to the half millimetre, so its 5.5 is
#: anything from 5.25 to 5.75: the two could be as much as 0.65 apart.  The
#: module is stuck to the board with adhesive rather than located by
#: anything (GVL's thread, towolf, 11 June 2013: "the camera housing itself
#: is stuck to the board with a patch of adhesive and comes off fairly
#: easily"), so neither is wrong for the board it measured, and no board is
#: known better than the whole of that spread.
LENS_TOL = 0.65

#: Anything ``measure_cm1.py`` scales off GVL rather than reads from it: the
#: worst residual of its checks, 0.09, plus GVL's own 0.05, rounded up.
SCALED_TOL = 0.15

# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------

#: GVL, "25".  SPY "25mm", B0033 "25.00 mm", RPI "Around 25".
BOARD_WIDTH = 25.0
#: GVL, "23.9".  SPY and B0033 both say 24, RPI "around 24"; CM2's board,
#: which kept the hole pattern, is 23.862.  GVL's is the only measurement of
#: this board finer than the nearest half millimetre, and it is 0.04 from
#: CM2's.
BOARD_HEIGHT = 23.9
#: GVL, "0.95".  SPY: "approximately 1mm thick".
BOARD_THICKNESS = 0.95
#: Square.  GVL, SPY and B0033 all draw square corners and SPY's photograph
#: of the board shows them.  CM2's corners are R2.0.
CORNER_RADIUS = 0.0

# ---------------------------------------------------------------------------
# Mounting holes
# ---------------------------------------------------------------------------

#: GVL, "ø 2".  SPY "~2mm hole", B0033 "R=1.00mm".  SPY also says "The
#: mounting holes will accept a 2mm machine screw according to various posts
#: and photos I have seen", which is hearsay, and true of a 2.2 hole as well.
#: Both measurements of this board say 2, where CM2's drawing says 2.2 on the
#: same centres; see HOLE_DIA_TOL.
HOLE_DIA = 2.0

#: GVL: 9.35 and 21.85 from the connector edge, 2 and 23 up from the lower
#: edge.  In this frame the connector edge is the upper one, so
#: y = 23.9 - 21.85 and 23.9 - 9.35.  Named as the Camera Module 2 and 3
#: sheets name them, MT1 lower left to MT4 upper right.
HOLES = {
    "MT1": (2.0, round(BOARD_HEIGHT - 21.85, 2)),
    "MT2": (23.0, round(BOARD_HEIGHT - 21.85, 2)),
    "MT3": (2.0, round(BOARD_HEIGHT - 9.35, 2)),
    "MT4": (23.0, round(BOARD_HEIGHT - 9.35, 2)),
}

# ---------------------------------------------------------------------------
# Lens and sensor module, on the lens side
# ---------------------------------------------------------------------------

#: The module's square body, (x0, y0, x1, y1).  Across: SPY, "8.5mm" in from
#: each side of an "8mm" module -- GVL draws it, undimensioned, at 8.53 to
#: 16.52, which is the same place, and B0033 puts its centre "12.50 mm" from
#: the side.  Up: GVL, "5.1" from the connector edge to a module "8.0" deep
#: in elevation, so y1 = 23.9 - 5.1.  SPY gives 5.5 for the same distance;
#: see LENS_TOL.
LENS = (8.5, round(BOARD_HEIGHT - 5.1 - 8.0, 2), 16.5,
        round(BOARD_HEIGHT - 5.1, 2))

#: The optical axis: the centre of LENS, which GVL draws the lens barrel
#: circles on.  It is 0.25 off the line of the upper holes, toward the
#: connector.  A reader of GVL's sheet in the same thread said as much --
#: RaspISteve, 11 June 2013: "from the drawing it would appear that the lens
#: axis is just off line from the adjacent mounting holes" -- which is a
#: reading of the same sheet, not a second measurement.  SPY puts the axis
#: on that line and CM2 its own 0.12 the other side, both within LENS_TOL;
#: B0033, the clone, puts it 1.15 away, which is not.
OPTICAL_AXIS = ((LENS[0] + LENS[2]) / 2, (LENS[1] + LENS[3]) / 2)

#: GVL, "5.2": the top of the lens above the board.  SPY: "The distance
#: between the reverse side of the PCB and the face of the camera is 6mm",
#: which GVL makes 5.2 + 0.95 = 6.15.
LENS_TOP_Z = 5.2

#: The lens stack in elevation, from the board up, every step centred on
#: OPTICAL_AXIS: (top of the step above the board, the step's size across,
#: its shape in plan).  GVL-scaled: the sheet draws three steps and
#: dimensions only the tip.  The square module body, 8.0 across (GVL,
#: "8.0"); a round holder, which the plan view draws as the larger of two
#: circles, 7.48 there and 7.44 in elevation; a thin ring at the tip, 5.52.
#: The top step is LENS_TOP_Z, as printed, rather than its scaled 5.11.
LENS_PROFILE = (
    (3.15, 8.0, "square"),
    (4.81, 7.5, "round"),
    (LENS_TOP_Z, 5.5, "round"),
)

#: The sensor's flex tail, which runs from the module's far side to the
#: sensor's own connector, J2, under a gold stiffener marked "P5V04A SUNNY"
#: in SPY's photograph.  GVL-scaled: drawn in both views, dimensioned in
#: neither.  (x0, y0, x1, y1): the module's width, from 0.85 above the lower
#: edge to the module.  Not a scheduled feature on the sheet, for the reason
#: the Camera Module 2 and 3 sheets give for their modules' lower bodies: a
#: bounding box of a shape that narrows would be a precise-looking figure
#: wrong at the corners.
TAIL = (LENS[0], round(BOARD_HEIGHT - 23.05, 2), LENS[2], LENS[1])
#: GVL-scaled: the flex where it arches over J2, the highest point beside
#: the lens.
TAIL_TOP_Z = 1.18

# ---------------------------------------------------------------------------
# FFC connector, on the underside
# ---------------------------------------------------------------------------

#: The connector as a holder has to clear it, (x0, y0, x1, y1): the envelope
#: of its body and the face it presents at the board edge.  Depth in from
#: the edge: GVL, "5.6" -- lettered under the elevation, below where the
#: cached page image is cropped, so which distance it dimensions is read
#: from where the text layer puts it, and the dashed body in plan measures
#: 5.63; CM2 draws its connector 5.52 and Camera Module 3's 5.71.  Along the
#: edge: GVL-scaled, never dimensioned.  GVL draws the body dashed, and the
#: face on the edge as a heavy line that runs past it at each end, 2.19 to
#: 22.92, 20.73 long -- the latch ears, which CM2's drawing also draws, and
#: whose envelope with the body is the 20.88 its sheet schedules.
FFC = (2.19, round(BOARD_HEIGHT - 5.6, 2), 22.92, BOARD_HEIGHT)

#: The body alone, GVL-scaled: 2.79 to 22.24, 19.45 long.  The Camera Module
#: 2 and 3 connector bodies are both 19.61 on Raspberry Pi's drawings.
FFC_BODY = (2.79, round(BOARD_HEIGHT - 5.6, 2), 22.24, BOARD_HEIGHT)

#: GVL, "2.8": the connector's foot below the underside.  CM3 prints 2.75
#: for its own.
FFC_BOTTOM_Z = round(-BOARD_THICKNESS - 2.8, 2)

#: GVL, "1.27": from the underside to the upper face of the cable where it
#: leaves the connector, running off the upper edge.
FFC_CABLE_Z = round(-BOARD_THICKNESS - 1.27, 2)

#: GVL, "16.2": the 15-way cable's width.  SPY: "16mm".
FFC_CABLE_WIDTH = 16.2

#: Where the cable crosses the upper edge, (x0, x1).  GVL-scaled: 4.43 to
#: 20.68, which is the printed 16.2 to within the scaling, and centred on the
#: board to 0.06.
FFC_CABLE = (4.43, 20.68)

#: The highest and lowest points of the board as assembled, and the whole.
#: 5.2 + 0.95 + 2.8 = 8.95, against RPI's "Around 25 × 24 × 9 mm".
TOP_Z = LENS_TOP_Z
BOTTOM_Z = FFC_BOTTOM_Z
OVERALL_HEIGHT = round(TOP_Z - BOTTOM_Z, 2)

# ---------------------------------------------------------------------------
# Not known
# ---------------------------------------------------------------------------
#
# No source dimensions or draws these, and nothing here guesses them.  Each
# is something a board in hand settles with calipers; TODO.md says how.
#
# * The small parts on the lens side besides the module and J2: LED D1 and
#   resistor R9 in the corner by MT1 in SPY's photograph, and others.  GVL's
#   elevation draws none of them.  Every one looks lower than J2, which is
#   not a measurement.
# * Anything on the underside but the connector.  GVL's elevation draws
#   nothing else there, and SPY does not say.
# * The lens's clear aperture and field stop.  GVL's circles are the holder
#   and its tip ring, not the glass.

# ---------------------------------------------------------------------------
# The drawing
# ---------------------------------------------------------------------------

GVL_SHEET = "https://www.scribd.com/doc/142718448/Raspberry-Pi-Camera-Mechanical-Data"
GVL_THREAD = "https://forums.raspberrypi.com/viewtopic.php?t=44466"
SPY_PAGE = ("https://www.raspberrypi-spy.co.uk/2013/05/"
            "pi-camera-module-mechanical-dimensions/")
RPI_DOCS = "https://www.raspberrypi.com/documentation/accessories/camera.html"


def _fmt(v: float) -> str:
    return f"{v:.2f}"


CM1 = BoardSpec(
    key="cm1",
    title="Raspberry Pi Camera Module 1 (v1.3)",
    subtitle="25 x 23.9 mm, OmniVision OV5647, hand measured",
    family="raspberrypicamera",
    front_edge="top",
    outline=Outline(width=BOARD_WIDTH, height=BOARD_HEIGHT,
                    corner_radius=CORNER_RADIUS, thickness=BOARD_THICKNESS),
    holes=tuple(Hole(x=x, y=y, dia=HOLE_DIA, label=label, kind="mount",
                     keepout_dia=None, tol=HOLE_DIA_TOL)
                for label, (x, y) in HOLES.items()),
    features=(
        Feature(key="lens", label="Lens and sensor module", kind="lens",
                x0=LENS[0], y0=LENS[1], x1=LENS[2], y1=LENS[3],
                side="top", number=1, tol=LENS_TOL),
        Feature(key="ffc", label="Camera FFC connector, 15-way",
                kind="connector",
                x0=FFC[0], y0=FFC[1], x1=FFC[2], y1=FFC[3],
                side="bottom", number=2, tol=SCALED_TOL),
    ),
    sources=(
        Source(label="Hand-measured drawing", ref=GVL_SHEET,
               note="Gert van Loo, 21 May 2013, posted in the forum's "
                    "'Mechanical data' thread: hand measured, 'accuracy "
                    "about 0.05 mm no guarantees'."),
        Source(label="Second measurement", ref=SPY_PAGE,
               note="Raspberry Pi Spy, 17 May 2013, a Rev 1.3 board, "
                    "calipers."),
        Source(label="Size", ref=RPI_DOCS,
               note="Camera Module 1: 'Around 25 x 24 x 9 mm'."),
    ),
    notes=(
        "Raspberry Pi publish no drawing for this board. Figures are the "
        "hand-measured source's as printed, but feature 1's X extent, the "
        "second measurement's; the connector's length and the flex are "
        f"scaled off the first, +/-{SCALED_TOL:.2f}.",
        "Hole centres, from the connector edge, agree with Raspberry Pi's "
        "Camera Module 2 drawing to 0.03; the second measurement gives the "
        "same 21 x 12.5. Both measure the holes o2, not finer; the Camera "
        "Module 2's are o2.2.",
        f"Optical axis at X {_fmt(OPTICAL_AXIS[0])}, Y "
        f"{_fmt(OPTICAL_AXIS[1])}, the centre of feature 1, "
        f"+/-{LENS_TOL:.2f}: the two measurements are that far apart at most, "
        "and the module is glued on.",
        f"Heights: lens {LENS_TOP_Z:.2f} above the board, board "
        f"{BOARD_THICKNESS:.2f}, connector {-FFC_BOTTOM_Z - BOARD_THICKNESS:.2f} "
        f"below; {OVERALL_HEIGHT:.2f} overall.",
        "The sensor's flex and its connector J2, about "
        f"{TAIL_TOP_Z:.1f} high, run from feature 1 to "
        f"{_fmt(TAIL[1])} from the lower edge. Other small parts are not "
        "measured.",
    ),
    # Hole positions and the edge, then the diameter, which the schedule
    # also prints beside each hole: "hole dia per schedule" did not fit.
    tolerance=f"edge, holes +/-{HOLE_TOL:.1f}  dia +/-{HOLE_DIA_TOL:.1f}  "
              f"lens +/-{LENS_TOL:.2f}  FFC +/-{SCALED_TOL:.2f}",
)
