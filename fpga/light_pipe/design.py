#!/usr/bin/env python3
"""Derive the Arty A7 Ethernet light pipe adapter and write ``adapter.py``.

The Arty A7's Ethernet LEDs face forwards, out of two windows in the front
face of its RJ45.  Looking down at the board you cannot see them at all.  This
part clips over the front of that jack and carries two catalogue light pipes
from those windows up to a face you can see from above, leaving the cable
opening and the latch alone.

Three sources, machine-read, and one chain between them:

``tmp/src/arty_a7/arty_a7_sch.pdf``
    Digilent's schematic.  The Ethernet jack is J9 and its part number is
    printed beside it: Bel ``08B0-1X1T-36-F``.  Read here only to confirm that
    string is on the sheet, because everything below hangs off it.

``tmp/src/bel_magjack/dr-mag-08b0-1x1t-36-f.pdf``
    Bel's drawing of that jack.  Its front view is a vector drawing, so the
    LED windows, the plug aperture and the latch keyway can be measured off
    it once the plot scale is recovered -- per axis, from the two overall
    dimensions the drawing states, exactly as ``fpga/extract.py`` recovers the
    scale of Digilent's Arty plot.  Its side view gives 0.305 [7.75] from the
    front face back to the board-lock pegs, which is the link to the board.

``tmp/src/arty_a7/mechanical_drawing/Arty A7/Arty_A7_DXF.DXF``
    Digilent's drawing of the board.  The two 1.575 mm pads are the jack's
    board locks, and they put the jack's centre line and, through Bel's 7.75,
    its front face in board coordinates.  The DXF's peg spacing and Bel's
    0.635 [16.13] have to agree, or the two drawings are not of the same
    part; they agree to 0.03 mm.

``tmp/src/bivar/PLP2-XXX.pdf``
    Bivar's drawing of the light pipe the adapter carries.  Read for the
    pipe's diameters, its recommended mounting hole and the panel thickness
    the press fit is designed for, which is what the bore is built from.

Run: uv run --no-project --with ezdxf --with pdfplumber \\
         python fpga/light_pipe/design.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.dump_rpi_pdf import rectangles  # noqa: E402

SRC = ROOT / "tmp" / "src"
OUT = Path(__file__).resolve().parent / "adapter.py"

BEL_PDF = SRC / "bel_magjack" / "dr-mag-08b0-1x1t-36-f.pdf"
BIVAR_PDF = SRC / "bivar" / "PLP2-XXX.pdf"
ARTY_SCH = SRC / "arty_a7" / "arty_a7_sch.pdf"
ARTY_DXF = SRC / "arty_a7" / "mechanical_drawing" / "Arty A7" / "Arty_A7_DXF.DXF"

BEL_URL = ("https://www.belfuse.com/media/drawings/products/"
           "magjack%20ICMs/dr-mag-08b0-1x1t-36-f.pdf")
BIVAR_URL = "https://www.bivar.com/parts_content/Datasheets/PLP2-XXX.pdf"
ARTY_SCH_URL = ("https://digilent.com/reference/_media/reference/"
                "programmable-logic/arty-a7/arty_a7_sch.pdf")
ARTY_ZIP = ("https://digilent.com/reference/_media/reference/"
            "programmable-logic/arty-a7/arty_a7.zip")

#: The part number as Digilent's schematic prints it beside J9, and the same
#: number as Bel writes it.  Both are checked against the files.
JACK_PART = "08B0-1X1T-36-F"
JACK_DESIGNATOR = "J9"

# -- what Bel's drawing states in words --------------------------------------
#
# These are the numbers the drawing dimensions, in the [mm] reference figures
# it prints beside its inch dimensions.  Everything else about the jack is
# measured off the drawn geometry below.

SHIELD_W = 16.31            # 0.642, overall width of the shield
SHIELD_H = 13.49            # 0.531, overall height above the seating plane
BODY_D = 25.53              # 1.005, front face to the back of the body
SPRING_PROUD = 1.40         # 0.055 +/-0.020, EMI spring height above a face
SPRING_PROUD_TOL = 0.51
SPRING_FRONT = 0.64         # 0.025, how far the side springs wrap forward
SPRING_TOP_LEN = 6.35       # 0.250, how far back the top springs run
FACE_TO_PEG = 7.75          # 0.305, front face to the board-lock pegs
PEG_SPACING_BEL = 16.13     # 0.635, between the two Ø1.57 peg holes
PEG_DIA_BEL = 1.57          # Ø0.062, 2 places

#: Bel's title block: ``.XXX  +/-0.010`` inch on a three-decimal inch
#: dimension.  Every figure above is a three-decimal inch dimension, so this
#: is the tolerance on all of them.
BEL_TOL = round(0.010 * 25.4, 3)

# -- what Bivar's drawing states ---------------------------------------------

PIPE_SERIES = "PLP2"
PIPE_PART = "PLP2-4MM"
PIPE_LEN = 4.0              # "4mm (0.157\")", the body length X
PIPE_DIA = 2.8              # Ø0.112, the light pipe itself
PIPE_RIB_DIA = 3.1          # Ø0.122 REF, over the press-fit ribs
FLANGE_DIA = 3.3            # Ø0.130, the flange
FLANGE_T = 0.8              # 0.030
PIPE_HOLE = 2.92            # Ø0.115 +0.003/-0.002 recommended mounting hole
PIPE_HOLE_PLUS = 0.08
PIPE_HOLE_MINUS = 0.05
PANEL_MIN = 1.19            # 0.047 in
PANEL_MAX = 2.36            # 0.093 in
PIPE_MATERIAL = "polycarbonate, 94V-0, clear"

# -- design decisions, as clearances ------------------------------------------
#
# The geometry below is derived from the jack and the pipe; these are the only
# numbers chosen rather than read.  Each is a clearance or a wall, and
# verify.py checks the finished part against every one of them.

APERTURE_CLEAR = 0.45   # cheek underside above the jack's plug aperture
FACE_GAP = 0.30         # pipe tip in front of the jack's front face
WALL = 0.80             # material between a bore and the cheek's inner face
OUTER_WALL = 2.10       # and its outer face: the skirt's thickness lands here
SKIRT_CLEAR = 0.52      # skirt inner face outside the shield, at max material
SKIRT_T = 1.40          # skirt wall
ROOF_CLEAR = 0.86       # roof underside above the shield, at max material
ROOF_T = 1.90
SKIRT_DROP = 1.00       # skirt bottom below the side springs' lower end
DEPTH_BACK = 10.00      # how far the skirts and roof reach back over the jack
SLOT_CLEAR = 0.28       # around a top EMI spring in the roof's slot
POCKET_CLEAR = 0.05     # pocket walls outside the bore
POCKET_TOP = 0.15       # pocket ceiling above the LED window
PRESS_LEN = 2.00        # length of bore at the pipe's press-fit diameter
FACET_EDGE = 0.35       # flange rim to the nearest edge of its seat

#: Where the pipe sits in the bore: the bore is exactly the pipe's body long,
#: so the flange seats on the facet when the tip is on the entry plane.
BORE_ANGLE = 45.0


def _fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Digilent's schematic: which jack this is
# ---------------------------------------------------------------------------

def read_schematic() -> str:
    """Confirm the jack's part number is printed on the Ethernet sheet.

    The whole chain hangs off this one string, so it is read rather than
    remembered.  The schematic's text is searchable; the sheet that carries
    J9 is the one titled ETHERNET.
    """
    import pdfplumber

    with pdfplumber.open(str(ARTY_SCH)) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if "ETHERNET" not in text:
                continue
            flat = text.replace("\n", " ")
            if JACK_PART in flat and JACK_DESIGNATOR in flat:
                return (f"sheet {n} of {len(pdf.pages)}, ETHERNET: "
                        f"{JACK_DESIGNATOR} is {JACK_PART}")
    raise SystemExit(
        f"{ARTY_SCH}: no sheet carries both {JACK_DESIGNATOR} and "
        f"{JACK_PART}; the jack this adapter is built around is not the jack "
        "on this board")


# ---------------------------------------------------------------------------
# Bel's drawing: the jack's front face
# ---------------------------------------------------------------------------

#: Page of Bel's PDF carrying the mechanical specification.  The file's four
#: pages are numbered 2 to 5 in their own title blocks; this is the one headed
#: MECHANICAL SPECIFICATION.
BEL_MECH_PAGE = 1


def _segments(page) -> list[tuple[float, float, float, float]]:
    """Every straight segment on *page*, in points, Y up."""
    out = []
    for obj in page.lines:
        pts = obj["pts"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            out.append((ax, page.height - ay, bx, page.height - by))
    return out


def _runs(segs, horizontal: bool):
    """Total drawn length at each distinct line position, longest first."""
    totals: dict[float, float] = {}
    for x0, y0, x1, y1 in segs:
        if horizontal and abs(y1 - y0) < 0.05 and abs(x1 - x0) > 0.05:
            totals[round(y0, 2)] = totals.get(round(y0, 2), 0.0) + abs(x1 - x0)
        elif not horizontal and abs(x1 - x0) < 0.05 and abs(y1 - y0) > 0.05:
            totals[round(x0, 2)] = totals.get(round(x0, 2), 0.0) + abs(y1 - y0)
    return sorted(totals.items(), key=lambda kv: -kv[1])


class Face:
    """Bel's front view, in jack millimetres.

    Datum: the jack's centre plane for Y, the seating plane -- the bottom of
    the housing, which is the board's top surface -- for Z.
    """

    def __init__(self, page):
        segs = _segments(page)
        # The front view is the left-hand half of the sheet; the side view,
        # the top view and the notes are all to the right of it.
        view = [s for s in segs if max(s[0], s[2]) < 400 and
                min(s[1], s[3]) > 300]
        # The housing is the tallest pair of verticals and the longest pair of
        # horizontals in that view: nothing else on it is 16 mm long.
        vert = _runs(view, horizontal=False)
        horiz = _runs(view, horizontal=True)
        x_left, x_right = sorted(p for p, _ in vert[:2])
        y_top, y_bot = sorted((p for p, _ in horiz[:2]), reverse=True)
        self.sx = SHIELD_W / (x_right - x_left)
        self.sy = SHIELD_H / (y_top - y_bot)
        self.aniso = self.sx / self.sy
        if abs(self.aniso - 1.0) > 0.01:
            raise SystemExit(
                f"{BEL_PDF.name}: the front view's axes disagree by "
                f"{(self.aniso - 1) * 100:.2f} %, so it is not the housing "
                "that was found")
        self._cx = (x_left + x_right) / 2
        self._y0 = y_bot
        self.segs = view
        self.rects = rectangles(
            [(self.y(s[0]), self.z(s[1]), self.y(s[2]), self.z(s[3]))
             for s in view])
        # A drawn line is rarely one segment: the front view's longest line,
        # the one the LED windows sit on, comes in eight pieces.  Collect
        # each line's whole extent before asking how long it is, or a search
        # for the longest line finds the longest piece.
        self.hlines = self._collect(horizontal=True)
        self.vlines = self._collect(horizontal=False)
        # Dimension lines reach far above the housing and would otherwise be
        # the longest verticals on the view.
        self.vlines = {k: v for k, v in self.vlines.items()
                       if v[0] < SHIELD_H + 3.0}

    def _collect(self, horizontal: bool) -> dict:
        """Each drawn line, as position -> (from, to, drawn length) in mm.

        Both are needed and they are not the same thing.  The extent is what
        an edge of the housing spans; the drawn length is how much of it is
        ink.  A line that appears as two short pieces at either end of the
        view -- the drawing has several -- spans twelve millimetres and draws
        three, and a search for "the line at least twelve long" has to
        reject it.
        """
        spans: dict[float, list[tuple[float, float]]] = {}
        for x0, y0, x1, y1 in self.segs:
            if horizontal:
                if abs(y1 - y0) > 0.05 or abs(x1 - x0) < 0.05:
                    continue
                pos, a, b = self.z(y0), self.y(x0), self.y(x1)
            else:
                if abs(x1 - x0) > 0.05 or abs(y1 - y0) < 0.05:
                    continue
                pos, a, b = self.y(x0), self.z(y0), self.z(y1)
            # 0.02 mm is a twelfth of the thinnest line on the drawing: two
            # pieces of one line land in one bucket, two different lines do
            # not.
            key = round(pos / 0.02) * 0.02
            spans.setdefault(key, []).append(tuple(sorted((a, b))))
        out = {}
        for key, pieces in spans.items():
            pieces.sort()
            drawn = 0.0
            lo, hi = pieces[0]
            for a, b in pieces[1:]:
                if a > hi:
                    drawn += hi - lo
                    lo, hi = a, b
                else:
                    hi = max(hi, b)
            drawn += hi - lo
            out[key] = (pieces[0][0], max(p[1] for p in pieces), drawn)
        return out

    # -- transforms, page points to jack millimetres ------------------------

    def y(self, px: float) -> float:
        return (px - self._cx) * self.sx

    def z(self, py: float) -> float:
        return (py - self._y0) * self.sy

    # -- features -----------------------------------------------------------

    def pick(self, what: str, centre, size, tol_pos=0.6, tol_size=0.5):
        """The drawn rectangle near *centre* and about *size*, in mm.

        Identification by hand, measurement by machine: the same bargain
        ``fpga/extract.py`` strikes with Digilent's plot.  A hint that finds
        nothing is an error rather than a guess.
        """
        cy, cz = centre
        w, h = size
        hits = [r for r in self.rects
                if abs((r[0] + r[2]) / 2 - cy) < tol_pos
                and abs((r[1] + r[3]) / 2 - cz) < tol_pos
                and abs((r[2] - r[0]) - w) < tol_size
                and abs((r[3] - r[1]) - h) < tol_size]
        if not hits:
            raise SystemExit(
                f"{BEL_PDF.name}: no rectangle near {centre} sized {size} "
                f"for the {what}")
        hits.sort(key=lambda r: -((r[2] - r[0]) * (r[3] - r[1])))
        return tuple(round(v, 3) for v in hits[0])

    def line_y(self, what: str, lo: float, hi: float, min_len: float,
               z_above: float | None = None, z_below: float | None = None,
               ends_above: float | None = None) -> float:
        """The outermost vertical line in |y| in [lo, hi], as a distance.

        Outermost, because every line this is asked for bounds an opening the
        adapter has to stay out of, and the wider reading of an opening is
        the safe one.
        """
        best = None
        for pos, (z0, z1, drawn) in self.vlines.items():
            if drawn < min_len:
                continue
            if z_above is not None and z0 < z_above:
                continue
            if z_below is not None and z1 > z_below:
                continue
            if ends_above is not None and z1 < ends_above:
                continue
            a = abs(pos)
            if lo <= a <= hi and (best is None or a > best):
                best = a
        if best is None:
            raise SystemExit(f"{BEL_PDF.name}: no vertical line for the {what}")
        return round(best, 3)

    def line_z(self, what: str, lo: float, hi: float, min_len: float) -> float:
        """The longest horizontal line with z in [lo, hi]."""
        best, best_len = None, 0.0
        for pos, (y0, y1, drawn) in self.hlines.items():
            if not lo <= pos <= hi:
                continue
            if drawn >= min_len and drawn > best_len:
                best, best_len = pos, drawn
        if best is None:
            raise SystemExit(f"{BEL_PDF.name}: no horizontal line for the {what}")
        return round(best, 3)

    def spring_z(self) -> tuple[float, float]:
        """Top and bottom of the side EMI springs.

        Only the pieces on the spring's own line, and only those between the
        seating plane and the top of the housing: the shield's ground tabs
        reach as far out at the bottom of the view, and a dimension's
        extension line runs up the same X as the spring.
        """
        zs = []
        for x0, y0, x1, y1 in self.segs:
            if abs(x1 - x0) > 0.05 or abs(y1 - y0) < 0.05:
                continue
            if abs(abs(self.y(x0)) - self.spring_y) > 0.15:
                continue
            z0, z1 = sorted((self.z(y0), self.z(y1)))
            if z0 < -0.2 or z1 > SHIELD_H:
                continue
            zs += [z0, z1]
        if not zs:
            raise SystemExit(f"{BEL_PDF.name}: the side EMI springs are not drawn")
        return round(min(zs), 3), round(max(zs), 3)


def read_jack() -> dict:
    import pdfplumber

    if not BEL_PDF.exists():
        raise SystemExit(f"missing {BEL_PDF}; run tools/fetch_fpga.sh")
    with pdfplumber.open(str(BEL_PDF)) as pdf:
        face = Face(pdf.pages[BEL_MECH_PAGE])

    # The two LED windows: hatched squares in the top corners of the front
    # face.  Bel labels them on the drawing -- LED 2 bi-colour green/orange on
    # the left, LED 1 yellow on the right, looking into the jack.
    left = face.pick("left LED window", (-6.5, 11.9), (2.8, 2.6))
    right = face.pick("right LED window", (6.5, 11.9), (2.8, 2.6))
    if abs(abs(left[0]) - right[2]) > 0.2 or abs(abs(left[2]) - right[0]) > 0.2:
        raise SystemExit(
            f"the two LED windows are not symmetric about the jack's centre: "
            f"{left} against {right}")
    # One window, as distances from the centre plane: the mean of the pair.
    win_y0 = round((abs(left[2]) + right[0]) / 2, 3)
    win_y1 = round((abs(left[0]) + right[2]) / 2, 3)
    win_z0 = round((left[1] + right[1]) / 2, 3)
    win_z1 = round((left[3] + right[3]) / 2, 3)

    # The plug aperture.  Its top edge is the longest line on the front face
    # after the housing's own: the LED windows sit on it.
    ap_z1 = face.line_z("plug aperture top", 9.5, 11.5, 12.0)
    ap_z0 = face.line_z("plug aperture bottom", 2.0, 5.0, 10.0)
    ap_y = face.line_y("plug aperture side", 5.5, 7.5, 0.6 * (ap_z1 - ap_z0))

    # The latch keyway, the slot above the aperture that the plug's latch
    # enters: the outermost line that starts at the aperture's top edge and
    # stops short of the top of the shield, which is what tells it from the
    # LED window's frame beside it and from the narrower slot above it.
    key_y = face.line_y("latch keyway side", 2.5, 4.5, 1.0,
                        ends_above=ap_z1 + 1.0, z_below=SHIELD_H - 0.5)

    spring_y = face.line_y("side EMI spring", SHIELD_W / 2, SHIELD_W / 2 + 2.5,
                           0.5)
    face.spring_y = spring_y
    spring_z0, spring_z1 = face.spring_z()
    top_spring_y0 = face.line_y("inner edge of a top EMI spring", 2.0, 3.0,
                                0.03, z_above=SHIELD_H - 0.1)
    top_spring_y1 = face.line_y("outer edge of a top EMI spring", 3.5, 4.5,
                                0.03, z_above=SHIELD_H - 0.1)
    top_spring_z = max(
        z1 for pos, (z0, z1, _d) in face.vlines.items()
        if 3.0 < abs(pos) < 4.5
        and z1 < SHIELD_H + SPRING_PROUD + SPRING_PROUD_TOL)

    return dict(
        aniso=face.aniso,
        window=(win_y0, win_y1, win_z0, win_z1),
        aperture=(ap_y, ap_z0, ap_z1),
        keyway=(key_y, ap_z1, SHIELD_H),
        side_spring=(spring_y, spring_z0, spring_z1),
        top_spring=(top_spring_y0, top_spring_y1, round(top_spring_z, 3)),
    )


# ---------------------------------------------------------------------------
# Bivar's drawing: the light pipe
# ---------------------------------------------------------------------------

def read_pipe() -> str:
    """Confirm the pipe's figures are the ones on Bivar's drawing.

    The drawing's dimensions are outlined text, so the numbers cannot be read
    out of it; the ordering table and the notes are real text, and they are
    what says this length exists and what the pipe is made of.
    """
    import pdfplumber

    if not BIVAR_PDF.exists():
        raise SystemExit(f"missing {BIVAR_PDF}; run tools/fetch_fpga.sh")
    with pdfplumber.open(str(BIVAR_PDF)) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    flat = " ".join(text.split())
    for want in (PIPE_PART, "POLYCARBONATE", "Recommended Mounting Hole"):
        if want.lower() not in flat.lower():
            raise SystemExit(
                f"{BIVAR_PDF.name} does not carry {want!r}; the pipe this "
                "adapter is bored for is not the pipe on the drawing")
    return f"{PIPE_PART} is on the offering list; material {PIPE_MATERIAL}"


# ---------------------------------------------------------------------------
# Digilent's DXF: where the jack sits on the board
# ---------------------------------------------------------------------------

def read_board() -> dict:
    import ezdxf

    if not ARTY_DXF.exists():
        raise SystemExit(f"missing {ARTY_DXF}; run tools/fetch_fpga.sh")
    doc = ezdxf.readfile(str(ARTY_DXF))
    msp = doc.modelspace()
    keep = [(e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y)
            for e in msp if e.dxftype() == "LINE"
            and e.dxf.layer == "KeepOutLayer"]
    x0 = min(c for s in keep for c in (s[0], s[2]))
    y0 = min(c for s in keep for c in (s[1], s[3]))
    pegs = [(round(e.dxf.center.x - x0, 3), round(e.dxf.center.y - y0, 3))
            for e in msp if e.dxftype() == "CIRCLE"
            and e.dxf.layer == "PadHoleLayer"
            and abs(2 * e.dxf.radius - PEG_DIA_BEL) < 0.05]
    if len(pegs) != 2:
        raise SystemExit(
            f"{ARTY_DXF.name}: {len(pegs)} pads of Ø{PEG_DIA_BEL}, not 2; the "
            "jack's board locks are what fix its position")
    (px0, py0), (px1, py1) = sorted(pegs, key=lambda p: p[1])
    if abs(px0 - px1) > 0.05:
        raise SystemExit("the two board-lock pads are not on one line across "
                         "the board")
    spacing = round(py1 - py0, 3)
    if abs(spacing - PEG_SPACING_BEL) > 0.2:
        raise SystemExit(
            f"the board's board-lock pads are {spacing} mm apart and Bel's "
            f"drawing says {PEG_SPACING_BEL}; these are not the same jack")
    return dict(peg_x=px0, centre_y=round((py0 + py1) / 2, 3),
                spacing=spacing,
                face_x=round(px0 - FACE_TO_PEG, 3))


# ---------------------------------------------------------------------------
# The adapter
# ---------------------------------------------------------------------------

def design(jack: dict) -> dict:
    """Every dimension of the part, from the jack and the pipe.

    Jack frame: X back into the board from the jack's front face, Y across
    from the jack's centre plane, Z up from the board's top surface.  The
    part is symmetric about Y = 0, so one cheek, one bore, one pocket, one
    skirt and one roof slot are given and the other is their mirror.
    """
    win_y0, win_y1, win_z0, win_z1 = jack["window"]
    ap_y, ap_z0, ap_z1 = jack["aperture"]
    key_y = jack["keyway"][0]
    spring_y, spring_z0, spring_z1 = jack["side_spring"]
    top_y0, top_y1, top_z = jack["top_spring"]

    half = math.sqrt(0.5)
    shield_half_max = SHIELD_W / 2 + BEL_TOL / 2
    shield_top_max = SHIELD_H + BEL_TOL / 2

    # The bore is centred on the LED window, so the pipe's aperture -- a
    # circle seen from the window at 45 degrees, which projects to an
    # ellipse PIPE_DIA wide and PIPE_DIA / sqrt(2) high -- lands inside it.
    bore_y = round((win_y0 + win_y1) / 2, 3)
    # The tip's lowest point sits on the cheek's underside, which is the
    # clearance above the plug aperture: that is what decides the height.
    cheek_z0 = round(ap_z1 + APERTURE_CLEAR, 3)
    bore_z = round(cheek_z0 + PIPE_DIA / 2 * half, 3)
    # And its rearmost point is FACE_GAP in front of the jack's front face.
    bore_x = round(-(FACE_GAP + PIPE_DIA / 2 * half), 3)

    bore_dia = round(PIPE_RIB_DIA + 0.1, 2)
    # z - x is constant along the bore's axis, so the two planes across it --
    # where the pipe's tip sits and where its flange seats -- are two values
    # of it, PIPE_LEN apart along the axis.
    entry_k = round(bore_z - bore_x, 3)
    facet_k = round(entry_k + PIPE_LEN / half, 3)
    facet = (round(bore_x - PIPE_LEN * half, 3),
             round(bore_z + PIPE_LEN * half, 3))

    # The skirt is what fixes the part's width: it has to pass the shield at
    # maximum material and meet the side EMI spring inside that.  The cheek
    # ends on the same plane, so the two are one face and not a 0.02 mm step.
    # Rounded outwards, not to nearest: a clearance rounded down is a
    # clearance the part no longer has.
    skirt_y0 = math.ceil((shield_half_max + SKIRT_CLEAR) * 100) / 100
    skirt_y1 = round(skirt_y0 + SKIRT_T, 2)
    cheek_y0 = round(bore_y - bore_dia / 2 - WALL, 3)
    cheek_y1 = skirt_y1
    outer = cheek_y1 - (bore_y + bore_dia / 2)
    if outer < OUTER_WALL:
        raise SystemExit(
            f"only {outer:.2f} mm of material outboard of the bore, against "
            f"the {OUTER_WALL} mm the design asks for; the skirt has to move "
            "out or the bore in")
    cheek_z1 = round(shield_top_max + ROOF_CLEAR + ROOF_T, 3)
    # Far enough forward that the flange's seat is a full flange wide: the
    # facet crosses the cheek's front face FACET_EDGE clear of the flange's
    # rim.  Both coordinates of that crossing move together, so the distance
    # along the facet is the step in X over sqrt(1/2).
    cheek_x0 = math.floor(
        (facet[0] - (FLANGE_DIA / 2 + FACET_EDGE) * half) * 1000) / 1000

    # The pocket: the window's own size plus the bore's, so that the bore's
    # mouth is open to the window and nothing of the adapter lands on the
    # window itself.
    pocket_y0 = round(min(win_y0, bore_y - bore_dia / 2) - POCKET_CLEAR, 3)
    pocket_y1 = round(max(win_y1, bore_y + bore_dia / 2) + POCKET_CLEAR, 3)
    pocket_z1 = round(win_z1 + POCKET_TOP, 3)
    pocket_x0 = round(bore_x - bore_dia / 2 * half - POCKET_CLEAR, 3)

    roof_z0 = round(shield_top_max + ROOF_CLEAR, 3)

    return dict(
        bore=dict(y=bore_y, x=bore_x, z=bore_z, dia=bore_dia,
                  press_dia=PIPE_HOLE, press_len=PRESS_LEN,
                  entry_k=entry_k, facet_k=facet_k, facet=facet,
                  length=PIPE_LEN),
        cheek=dict(x0=cheek_x0, x1=0.0, y0=cheek_y0, y1=cheek_y1,
                   z0=cheek_z0, z1=cheek_z1),
        pocket=dict(x0=pocket_x0, x1=0.0, y0=pocket_y0, y1=pocket_y1,
                    z0=cheek_z0, z1=pocket_z1),
        roof=dict(x0=0.0, x1=DEPTH_BACK, y1=cheek_y1, z0=roof_z0,
                  z1=cheek_z1),
        slot=dict(x0=0.0, x1=round(SPRING_TOP_LEN + 0.95, 2),
                  y0=round(top_y0 - SLOT_CLEAR, 2),
                  y1=round(top_y1 + SLOT_CLEAR, 2)),
        skirt=dict(x0=0.0, x1=DEPTH_BACK, y0=skirt_y0, y1=skirt_y1,
                   z0=round(spring_z0 - SKIRT_DROP, 2), z1=cheek_z1),
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

HEADER = '''"""Arty A7 Ethernet LED light pipe adapter.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber \\\\
        python fpga/light_pipe/design.py

Jack frame, used by every dimension here: origin on the jack's centre plane,
in its front face, at the board's top surface.  X runs back into the board,
Y across it and Z up.  ``JACK_FACE_X`` and ``JACK_CENTRE_Y`` put that frame on
the Arty A7 of ``fpga/boards.py``.

The part is symmetric about Y = 0.  One cheek, bore, pocket, roof slot and
skirt are given; the other of each is its mirror image.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Outline, Source
'''


def emit(jack, board, adapter, provenance) -> str:
    b = adapter["bore"]
    ch = adapter["cheek"]
    po = adapter["pocket"]
    rf = adapter["roof"]
    sl = adapter["slot"]
    sk = adapter["skirt"]
    win_y0, win_y1, win_z0, win_z1 = jack["window"]
    ap_y, ap_z0, ap_z1 = jack["aperture"]
    key_y, key_z0, key_z1 = jack["keyway"]
    sp_y, sp_z0, sp_z1 = jack["side_spring"]
    ts_y0, ts_y1, ts_z = jack["top_spring"]

    width = 2 * ch["y1"]
    depth = rf["x1"] - ch["x0"]
    height = ch["z1"] - sk["z0"]

    out = [HEADER, ""]
    out += [
        "#: The jack the adapter clips onto, and where it is.",
        f"JACK_PART = {JACK_PART!r}",
        f"JACK_DESIGNATOR = {JACK_DESIGNATOR!r}",
        f"JACK_ON_SHEET = {provenance['schematic']!r}",
        f"SHIELD_W = {SHIELD_W}",
        f"SHIELD_H = {SHIELD_H}",
        f"BODY_D = {BODY_D}",
        f"SPRING_PROUD = {SPRING_PROUD}",
        f"SPRING_PROUD_TOL = {SPRING_PROUD_TOL}",
        f"SPRING_FRONT = {SPRING_FRONT}",
        f"SPRING_TOP_LEN = {SPRING_TOP_LEN}",
        f"FACE_TO_PEG = {FACE_TO_PEG}",
        "#: Bel's title block, on a three-decimal inch dimension.",
        f"BEL_TOL = {BEL_TOL}",
        "",
        "#: Measured off Bel's front view, whose plot scale is recovered per",
        "#: axis from the two overall dimensions it states.  The axes agree",
        f"#: to {abs(provenance['aniso'] - 1) * 100:.2f} %; figures from this",
        "#: view are good to about +/-0.20 mm.",
        f"READ_TOL = 0.20",
        f"PLOT_ANISO = {provenance['aniso']:.5f}",
        "",
        "#: One LED window, as distances from the jack's centre plane and the",
        "#: board's top surface.  The other is its mirror.",
        f"WINDOW_Y0, WINDOW_Y1 = {win_y0}, {win_y1}",
        f"WINDOW_Z0, WINDOW_Z1 = {win_z0}, {win_z1}",
        "",
        "#: The opening a plug goes through, and the keyway its latch enters.",
        f"APERTURE_Y, APERTURE_Z0, APERTURE_Z1 = {ap_y}, {ap_z0}, {ap_z1}",
        f"KEYWAY_Y, KEYWAY_Z0, KEYWAY_Z1 = {key_y}, {key_z0}, {key_z1}",
        "",
        "#: The EMI springs: the side pair is what grips the skirts, the top",
        "#: pair is what the roof's slots clear.",
        f"SIDE_SPRING_Y, SIDE_SPRING_Z0, SIDE_SPRING_Z1 = {sp_y}, {sp_z0}, {sp_z1}",
        f"TOP_SPRING_Y0, TOP_SPRING_Y1, TOP_SPRING_Z = {ts_y0}, {ts_y1}, {ts_z}",
        "",
        "#: The jack on the Arty A7, from Digilent's DXF: the centre line and",
        "#: front face of the frame above, in board coordinates.",
        f"BOARD_KEY = 'arty-a7'",
        f"JACK_CENTRE_Y = {board['centre_y']}",
        f"JACK_FACE_X = {board['face_x']}",
        f"PEG_X = {board['peg_x']}",
        f"PEG_SPACING_DXF = {board['spacing']}",
        f"PEG_SPACING_BEL = {PEG_SPACING_BEL}",
        "",
        "#: The light pipe, from Bivar's drawing.",
        f"PIPE_PART = {PIPE_PART!r}",
        f"PIPE_SERIES = {PIPE_SERIES!r}",
        f"PIPE_LEN = {PIPE_LEN}",
        f"PIPE_DIA = {PIPE_DIA}",
        f"PIPE_RIB_DIA = {PIPE_RIB_DIA}",
        f"FLANGE_DIA = {FLANGE_DIA}",
        f"FLANGE_T = {FLANGE_T}",
        f"PIPE_HOLE = {PIPE_HOLE}",
        f"PIPE_HOLE_PLUS, PIPE_HOLE_MINUS = {PIPE_HOLE_PLUS}, {PIPE_HOLE_MINUS}",
        f"PANEL_MIN, PANEL_MAX = {PANEL_MIN}, {PANEL_MAX}",
        f"PIPE_MATERIAL = {PIPE_MATERIAL!r}",
        f"PIPE_ON_SHEET = {provenance['pipe']!r}",
        "",
        "#: The bore: a cylinder at 45 degrees in the X-Z plane, rising",
        "#: forwards.  Along its axis z - x does not change, so the plane the",
        "#: pipe's tip lies on and the plane its flange seats on are two",
        "#: values of z - x.  (BORE_X, BORE_Z) is the tip's centre.",
        f"BORE_ANGLE = {BORE_ANGLE}",
        f"BORE_Y = {b['y']}",
        f"BORE_X, BORE_Z = {b['x']}, {b['z']}",
        f"BORE_DIA = {b['dia']}",
        f"PRESS_DIA, PRESS_LEN = {b['press_dia']}, {b['press_len']}",
        f"ENTRY_K = {b['entry_k']}",
        f"FACET_K = {b['facet_k']}",
        f"FACET_X, FACET_Z = {b['facet'][0]}, {b['facet'][1]}",
        "",
        "#: The cheek: the block the bore runs through, cut off at the facet.",
        f"CHEEK_X0, CHEEK_X1 = {ch['x0']}, {ch['x1']}",
        f"CHEEK_Y0, CHEEK_Y1 = {ch['y0']}, {ch['y1']}",
        f"CHEEK_Z0, CHEEK_Z1 = {ch['z0']}, {ch['z1']}",
        "",
        "#: The light pocket in the cheek's back face, open at the bottom: it",
        "#: keeps the adapter off the LED window and lets the window see the",
        "#: end of the pipe.",
        f"POCKET_X0, POCKET_X1 = {po['x0']}, {po['x1']}",
        f"POCKET_Y0, POCKET_Y1 = {po['y0']}, {po['y1']}",
        f"POCKET_Z0, POCKET_Z1 = {po['z0']}, {po['z1']}",
        "",
        "#: The roof over the jack, which joins the two cheeks and the two",
        "#: skirts, and the slot in it that clears a top EMI spring.",
        f"ROOF_X0, ROOF_X1 = {rf['x0']}, {rf['x1']}",
        f"ROOF_Y1 = {rf['y1']}",
        f"ROOF_Z0, ROOF_Z1 = {rf['z0']}, {rf['z1']}",
        f"SLOT_X0, SLOT_X1 = {sl['x0']}, {sl['x1']}",
        f"SLOT_Y0, SLOT_Y1 = {sl['y0']}, {sl['y1']}",
        "",
        "#: The skirt down the side of the jack: the jack's own side EMI",
        "#: spring bears on it, and that is what holds the adapter on.",
        f"SKIRT_X0, SKIRT_X1 = {sk['x0']}, {sk['x1']}",
        f"SKIRT_Y0, SKIRT_Y1 = {sk['y0']}, {sk['y1']}",
        f"SKIRT_Z0, SKIRT_Z1 = {sk['z0']}, {sk['z1']}",
        "",
        "#: The envelope, for the sheet's views and for anything designing a",
        "#: box around the board.",
        f"WIDTH, DEPTH, HEIGHT = {round(width, 3)}, {round(depth, 3)}, {round(height, 3)}",
        "",
        "#: The clearances the design was built to, which verify.py checks the",
        "#: finished geometry against.",
        "CLEARANCES = {",
        f"    'plug aperture': {APERTURE_CLEAR},",
        f"    'pipe tip to jack face': {FACE_GAP},",
        f"    'bore to cheek inner face': {WALL},",
        f"    'skirt to shield': {SKIRT_CLEAR},",
        f"    'roof to shield': {ROOF_CLEAR},",
        f"    'roof slot to top EMI spring': {SLOT_CLEAR},",
        f"    'flange rim to the edge of its seat': {FACET_EDGE},",
        "}",
        "",
    ]
    out.append(SPEC_TEMPLATE.format(
        width=round(depth, 3), height=round(width, 3),
        z_height=round(height, 3),
        bel_url=BEL_URL, bivar_url=BIVAR_URL,
        arty_sch_url=ARTY_SCH_URL, arty_zip=ARTY_ZIP,
        schematic=provenance["schematic"], pipe=provenance["pipe"],
        aniso=f"{abs(provenance['aniso'] - 1) * 100:.2f}",
        spacing=board["spacing"], face_x=board["face_x"],
        centre_y=board["centre_y"], peg_x=board["peg_x"],
    ))
    return "\n".join(out)


#: The sheet reads its title, its sources and its notes off this, exactly as
#: every other sheet in the repository does.  ``outline`` is the plan
#: envelope: X back into the board along the sheet's width, Y across it.
SPEC_TEMPLATE = '''
ADAPTER = BoardSpec(
    key="arty-ethernet-light-pipe",
    title="Arty A7 Ethernet Light Pipe",
    subtitle="Clips over J9 and carries its two LEDs to a face you can see from above",
    family="lightpipe",
    body="enclosure",
    front_edge="left",
    outline=Outline(width={width}, height={height}, z_height={z_height}),
    tolerance="printed +/-0.20   bore dia +0.05/-0   see notes",
    sources=(
        Source(label="Board schematic",
               ref="{arty_sch_url}",
               note="Digilent, Arty A7 rev E.0, 2018-01-09: {schematic}."),
        Source(label="Jack drawing",
               ref="{bel_url}",
               note="Bel MagJack 08B0-1X1T-36-F, drawing 08B01X1T36-F rev E, 2018-03-18. Stated dimensions are its own; the LED windows, the plug aperture, the latch keyway and the EMI springs are measured off its front view, whose plot scale is recovered per axis from the 0.642 [16.31] and 0.531 [13.49] it dimensions (the axes agree to {aniso} %)."),
        Source(label="Board drawing",
               ref="{arty_zip}",
               note="Digilent, Arty_A7_DXF.DXF: the two Ø1.575 mm board-lock pads at x = {peg_x} put the jack's centre line at y = {centre_y}. They are {spacing} mm apart, against Bel's 0.635 [16.13], so the two drawings are of the same jack; Bel's 0.305 [7.75] from the pegs to the front face puts that face at x = {face_x}."),
        Source(label="Light pipe drawing",
               ref="{bivar_url}",
               note="Bivar PLP2-XXX rev Y, 2018-07-06, press-fit panel mount front mount light pipe: {pipe}. The bore is built from its Ø0.115 +0.003/-0.002 recommended mounting hole and its 0.047-0.093 in panel thickness."),
    ),
    notes=(
        "The adapter slides onto the front of J9 and stops against its front face. Nothing fixes it but the jack's own side EMI springs, which stand 1.40 +/-0.51 mm proud of the shield and bear on the skirts: over that whole band the springs are deflected and the shield itself never touches.",
        "Print it upside down, on the top face. Every other face then rises from the plate, the two 45 degree facets and the two bores are the only overhangs, and neither needs support.",
        "Bore diameters are for a printed hole. A printer that comes out undersize will not take the pipe: ream the press-fit length to Bivar's Ø2.92 +0.08/-0.05 and test the fit on a scrap before printing the part.",
        "The pipe's tip is 0.30 mm in front of the jack's front face and its light crosses that gap in air. Nothing of the adapter touches the LED windows: the pocket clears both of them.",
        "A plug and a plain boot pass under the cheeks. A snagless boot whose hood stands above the plug's own top face within 6 mm of the jack will foul them; the note on the cheek gives the height that is clear.",
        "MEASURED figures come off Bel's front view and are good to about +/-0.20 mm. Figures Bel dimensions carry its own +/-0.254 mm (.XXX +/-0.010 in). Both are wider than the printed part's tolerance, and the clearances are sized for them.",
    ),
)
'''


def main() -> None:
    provenance = dict(schematic=read_schematic(), pipe=read_pipe())
    jack = read_jack()
    provenance["aniso"] = jack["aniso"]
    board = read_board()
    adapter = design(jack)
    OUT.write_text(emit(jack, board, adapter, provenance))

    print(f"schematic : {provenance['schematic']}")
    print(f"pipe      : {provenance['pipe']}")
    print(f"jack      : LED window y {jack['window'][0]}..{jack['window'][1]}, "
          f"z {jack['window'][2]}..{jack['window'][3]} mm; aperture "
          f"|y| <= {jack['aperture'][0]}, z <= {jack['aperture'][2]}; keyway "
          f"|y| <= {jack['keyway'][0]}")
    print(f"board     : pegs {board['spacing']} mm apart (Bel "
          f"{PEG_SPACING_BEL}), centre line y = {board['centre_y']}, front "
          f"face x = {board['face_x']}")
    print(f"adapter   : bore at y = {adapter['bore']['y']}, tip at "
          f"({adapter['bore']['x']}, {adapter['bore']['z']}), "
          f"Ø{adapter['bore']['dia']} at {BORE_ANGLE:g} degrees")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
