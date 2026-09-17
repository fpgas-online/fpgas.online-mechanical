"""Fabrication drawing for the Arty A7 Ethernet light pipe adapter.

Three views of a part 20 mm across, so 5:1, first angle: the front elevation
at the top, the plan under it, and a section through one bore to its left.
The section is the view the part exists for -- it is the only one that shows
the 45 degree bore, the light pipe in it and the LED window it looks at, all
in true shape.

The jack the adapter clips onto is drawn in every view as an adjacent part,
because every dimension on the sheet is to a feature of that jack and a
reader has to be able to see which.
"""

from __future__ import annotations

import math

from fpga.light_pipe import adapter as A

from . import dims, style
from .board_sheet import (_place_notes_and_sources, draw_legend, legend_height,
                          note_blocks, notes_spill_needed)
from .canvas import Canvas
from .sheet import Rect, Sheet, TitleBlock
from .view import View

H = math.sqrt(0.5)

GAP = 16.0              # between views, for the dimensions that go there
#: Room above the view block for a caption and the overall width dimension,
#: and below it for the stack of dimensions under the plan.
TOP_ROOM = 24.0
BOTTOM_ROOM = 19.0
SCALE = 5.0

#: Room in front of the cheek for the light pipe's flange, which stands
#: proud of the facet and so reaches past the part itself.
SECT_NOSE = 1.4

#: How much of the jack each view draws.  The jack is 25.5 mm deep and the
#: adapter reaches 10 mm of it; drawing the rest would halve the scale to say
#: nothing, so the views stop at the back of the roof plus a little.
JACK_BACK = 10.6

#: The colour the jack is drawn in.  It is an adjacent part, not a feature of
#: this drawing, so it is phantom and grey wherever it appears.
JACK = style.C_PHANTOM
#: The two bought light pipes, which are not features of the printed part
#: either but are what it is for.
PIPE = "#7a4a00"

LEGEND = [
    ("outline", "The printed part"),
    ("hidden", "Hidden detail: bores and the pocket"),
    ("phantom", "The RJ45 J9 and its EMI springs, adjacent parts"),
    ("usbc", "The two Bivar light pipes, bought"),
]


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def bore_point(t: float, s: float) -> tuple[float, float]:
    """A point on the bore, ``t`` along its axis and ``s`` across it.

    t is measured from the plane the pipe's tip lies on, towards the flange;
    s from the axis, positive towards the part's top face.  The axis is at 45
    degrees in the X-Z plane, so both coordinates move together.
    """
    return (A.BORE_X - t * H + s * H, A.BORE_Z + t * H + s * H)


def ellipse(c: Canvas, cx: float, cy: float, rx: float, ry: float, **kw) -> None:
    """A circle seen at an angle.  Drawn as a polyline: the canvas emits
    paths and arcs, and an ellipse written as two arcs is four numbers that
    have to agree with each other, where this is one loop that cannot."""
    pts = [(cx + rx * math.cos(a * math.pi / 24),
            cy + ry * math.sin(a * math.pi / 24)) for a in range(48)]
    c.polyline(pts + [pts[0]], **kw)


def hatch(c: Canvas, polygon, spacing: float = 2.2, **kw) -> None:
    """Section hatching: parallel lines at 45 degrees, clipped to *polygon*.

    Lines run down to the right, against the bore, which runs up to the
    right: hatching parallel to the feature it is cutting through is the one
    direction ISO 128 rules out.
    """
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    lo = min(xs) + min(ys)
    hi = max(xs) + max(ys)
    k = lo
    while k <= hi:
        # The line x + y = k, clipped against every edge in turn.
        hits = []
        for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
            d0 = x0 + y0 - k
            d1 = x1 + y1 - k
            if d0 == 0 and d1 == 0:
                continue
            if (d0 <= 0 <= d1) or (d1 <= 0 <= d0):
                f = d0 / (d0 - d1) if d0 != d1 else 0.0
                hits.append((x0 + f * (x1 - x0), y0 + f * (y1 - y0)))
        hits.sort()
        for a, b in zip(hits[0::2], hits[1::2]):
            if math.dist(a, b) > 0.2:
                c.line(a[0], a[1], b[0], b[1], w=style.W_THIN, **kw)
        k += spacing * math.sqrt(2)


# ---------------------------------------------------------------------------
# the views
# ---------------------------------------------------------------------------

def _clip(v: View, u0: float, u1: float, w0: float, w1: float):
    """A box, trimmed to what the view covers.

    The jack is drawn in every view and reaches past all of them: 25.5 mm
    back, and below the board in its leads.  Trimming it here rather than
    choosing view frames big enough to hold it is what keeps the part at 5:1.
    """
    u0, u1 = max(min(u0, u1), v.model_x0), min(max(u0, u1), v.model_x1)
    w0, w1 = max(min(w0, w1), v.model_y0), min(max(w0, w1), v.model_y1)
    if u1 <= u0 or w1 <= w0:
        return None
    return u0, u1, w0, w1


def _box(c: Canvas, v: View, u0, u1, w0, w1, **kw) -> None:
    got = _clip(v, u0, u1, w0, w1)
    if got is None:
        return
    u0, u1, w0, w1 = got
    a, b = v.pt(u0, w0), v.pt(u1, w1)
    c.rect(min(a[0], b[0]), min(a[1], b[1]), abs(b[0] - a[0]),
           abs(b[1] - a[1]), **kw)


PHANTOM = dict(weight=style.W_PHANTOM, colour=JACK, dash=style.D_PHANTOM)
HIDDEN = dict(weight=style.W_HIDDEN, colour=style.C_HIGHLIGHT,
              dash=style.D_HIDDEN)


def draw_front(c: Canvas, v: View) -> None:
    """Looking at the face the cable comes to, jack included."""
    # The jack: shield, the opening a plug goes through, the keyway its latch
    # enters, and the EMI springs standing off three of its faces.
    _box(c, v, -A.SHIELD_W / 2, A.SHIELD_W / 2, 0.0, A.SHIELD_H, **PHANTOM)
    _box(c, v, -A.APERTURE_Y, A.APERTURE_Y, A.APERTURE_Z0, A.APERTURE_Z1,
         **PHANTOM)
    _box(c, v, -A.KEYWAY_Y, A.KEYWAY_Y, A.KEYWAY_Z0, A.KEYWAY_Z1, **PHANTOM)
    for side in (1, -1):
        _box(c, v, side * A.SHIELD_W / 2, side * A.SIDE_SPRING_Y,
             A.SIDE_SPRING_Z0, A.SIDE_SPRING_Z1, **PHANTOM)
        _box(c, v, side * A.TOP_SPRING_Y0, side * A.TOP_SPRING_Y1,
             A.SHIELD_H, A.TOP_SPRING_Z, **PHANTOM)
    # The board's top surface, which is where Z is measured from.
    c.line(*v.pt(v.model_x0, 0.0), *v.pt(v.model_x1, 0.0), w=style.W_PHANTOM,
           colour=JACK, dash=style.D_PHANTOM)

    # The part, filled so that it reads as being in front of the jack.
    _box(c, v, -A.ROOF_Y1, A.ROOF_Y1, A.ROOF_Z0, A.ROOF_Z1,
         weight=style.W_OUTLINE, fill="#ffffff")
    for side in (1, -1):
        _box(c, v, side * A.CHEEK_Y0, side * A.CHEEK_Y1, A.CHEEK_Z0,
             A.CHEEK_Z1, weight=style.W_OUTLINE, fill="#ffffff")
        # Where the facet crosses the cheek's front face.
        z = A.FACET_K + A.CHEEK_X0
        c.line(*v.pt(side * A.CHEEK_Y0, z), *v.pt(side * A.CHEEK_Y1, z),
               w=style.W_OUTLINE)
        # Behind that face: the bore, the pocket, and the LED window the
        # pocket is cut to clear.
        _box(c, v, side * (A.BORE_Y - A.BORE_DIA / 2),
             side * (A.BORE_Y + A.BORE_DIA / 2),
             A.BORE_Z - A.BORE_DIA / 2 * H, z, **HIDDEN)
        _box(c, v, side * A.POCKET_Y0, side * A.POCKET_Y1, A.POCKET_Z0,
             A.POCKET_Z1, **HIDDEN)
        _box(c, v, side * A.WINDOW_Y0, side * A.WINDOW_Y1, A.WINDOW_Z0,
             A.WINDOW_Z1, weight=style.W_COMPONENT,
             colour=style.C_HIGHLIGHT, dash=style.D_HIDDEN)
        # The flange seat, seen end on: a circle at 45 degrees.
        cx, cy = v.pt(side * A.BORE_Y, A.FACET_Z)
        ellipse(c, cx, cy, v.d(A.PRESS_DIA / 2), v.d(A.PRESS_DIA / 2 * H),
                w=style.W_OUTLINE)
        c.line(*v.pt(side * A.BORE_Y, A.CHEEK_Z0 - 1.0),
               *v.pt(side * A.BORE_Y, A.CHEEK_Z1 + 1.2),
               w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)
    # Short of the dimension stack below the view: a centre line run
    # the usual couple of millimetres past the part is ruled through
    # the first dimension's text.
    c.line(*v.pt(0, -0.2), *v.pt(0, A.CHEEK_Z1 + 1.2), w=style.W_CENTRE,
           colour=style.C_LINE, dash=style.D_CENTRE)


def draw_plan(c: Canvas, v: View) -> None:
    """Looking down.  The front of the part is at the top of the view, which
    is where first angle projection puts it under the elevation."""
    def box(x0, x1, y0, y1, **kw):
        _box(c, v, y0, y1, -x1, -x0, **kw)

    def pt(x, y):
        return v.pt(y, -x)

    box(0.0, A.BODY_D, -A.SHIELD_W / 2, A.SHIELD_W / 2, **PHANTOM)
    for side in (1, -1):
        box(0.0, A.SPRING_TOP_LEN, side * A.TOP_SPRING_Y0,
            side * A.TOP_SPRING_Y1, **PHANTOM)
        box(0.0, A.SPRING_TOP_LEN, side * A.SHIELD_W / 2,
            side * A.SIDE_SPRING_Y, **PHANTOM)

    box(A.ROOF_X0, A.ROOF_X1, -A.ROOF_Y1, A.ROOF_Y1, weight=style.W_OUTLINE,
        fill="#ffffff")
    for side in (1, -1):
        box(A.SLOT_X0, A.SLOT_X1, side * A.SLOT_Y0, side * A.SLOT_Y1,
            weight=style.W_OUTLINE)
        box(A.SKIRT_X0, A.SKIRT_X1, side * A.SKIRT_Y0, side * A.SKIRT_Y1,
            **HIDDEN)
        box(A.CHEEK_X0, A.CHEEK_X1, side * A.CHEEK_Y0, side * A.CHEEK_Y1,
            weight=style.W_OUTLINE, fill="#ffffff")
        box(A.POCKET_X0, A.POCKET_X1, side * A.POCKET_Y0, side * A.POCKET_Y1,
            **HIDDEN)
        # The facet runs from here to the cheek's front face.
        edge = A.CHEEK_Z1 - A.FACET_K
        c.line(*pt(edge, side * A.CHEEK_Y0), *pt(edge, side * A.CHEEK_Y1),
               w=style.W_OUTLINE)
        cx, cy = pt(A.FACET_X, side * A.BORE_Y)
        ellipse(c, cx, cy, v.d(A.PRESS_DIA / 2 * H), v.d(A.PRESS_DIA / 2),
                w=style.W_OUTLINE)
        dims.centre_mark(c, cx, cy, v.d(A.PRESS_DIA / 2), over=1.2)
    # Barely past the part at the front, where the PLAN caption is.
    c.line(*pt(A.CHEEK_X0 - 0.4, 0), *pt(JACK_BACK, 0),
           w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)


def section_outline() -> list[tuple[float, float]]:
    """The material the section plane cuts, as one closed polygon.

    The plane is on a bore's axis, so it cuts that cheek and the roof; the
    skirt is outboard of it and the roof's slots inboard, and it misses both.
    """
    return [
        (A.CHEEK_X0, A.CHEEK_Z0),
        (A.POCKET_X0, A.CHEEK_Z0),
        (A.POCKET_X0, A.POCKET_Z1),
        (A.POCKET_X1, A.POCKET_Z1),
        (A.POCKET_X1, A.ROOF_Z0),
        (A.ROOF_X1, A.ROOF_Z0),
        (A.ROOF_X1, A.ROOF_Z1),
        (A.CHEEK_Z1 - A.FACET_K, A.CHEEK_Z1),
        (A.CHEEK_X0, A.FACET_K + A.CHEEK_X0),
    ]


def draw_section(c: Canvas, v: View) -> None:
    """Through one bore: the part cut, the pipe in it, the jack beside it."""
    # The jack, cut by the same plane.  At this Y the plane passes through an
    # LED window, which is the whole reason the bore is where it is.
    _box(c, v, 0.0, A.BODY_D, 0.0, A.SHIELD_H, **PHANTOM)
    c.line(*v.pt(v.model_x0, 0.0), *v.pt(v.model_x1, 0.0),
           w=style.W_PHANTOM, colour=JACK, dash=style.D_PHANTOM)
    c.line(*v.pt(0.0, A.APERTURE_Z1), *v.pt(v.model_x1, A.APERTURE_Z1),
           w=style.W_PHANTOM, colour=JACK, dash=style.D_PHANTOM)
    c.line(*v.pt(0.0, A.WINDOW_Z0), *v.pt(0.0, A.WINDOW_Z1),
           w=style.W_COMPONENT, colour=style.C_HIGHLIGHT)
    for z in (A.WINDOW_Z0, A.WINDOW_Z1):
        c.line(*v.pt(0.0, z), *v.pt(1.2, z), w=style.W_COMPONENT,
               colour=style.C_HIGHLIGHT)

    poly = [v.pt(x, z) for x, z in section_outline()]
    hatch(c, poly, colour=style.C_THIN)
    c.polyline(poly + [poly[0]], w=style.W_OUTLINE)

    # The bore, painted over the hatching: a clearance length, then the press
    # fit, both about the axis.
    r, p = A.BORE_DIA / 2, A.PRESS_DIA / 2
    clear = A.PIPE_LEN - A.PRESS_LEN
    void = [bore_point(0.0, r), bore_point(clear, r), bore_point(clear, p),
            bore_point(A.PIPE_LEN, p), bore_point(A.PIPE_LEN, -p),
            bore_point(clear, -p), bore_point(clear, -r), bore_point(0.0, -r)]
    pts = [v.pt(*q) for q in void]
    c.polyline(pts + [pts[0]], w=style.W_OUTLINE, fill="#ffffff")

    # The pipe in it, flange standing on the facet.
    pr, fr = A.PIPE_DIA / 2, A.FLANGE_DIA / 2
    pipe = [bore_point(0.0, pr), bore_point(A.PIPE_LEN, pr),
            bore_point(A.PIPE_LEN, fr),
            bore_point(A.PIPE_LEN + A.FLANGE_T, fr),
            bore_point(A.PIPE_LEN + A.FLANGE_T, -fr),
            bore_point(A.PIPE_LEN, -fr), bore_point(A.PIPE_LEN, -pr),
            bore_point(0.0, -pr)]
    pts = [v.pt(*q) for q in pipe]
    c.polyline(pts + [pts[0]], w=style.W_PHANTOM, colour=PIPE,
               dash=style.D_PHANTOM)

    a = v.pt(*bore_point(-1.6, 0.0))
    b = v.pt(*bore_point(A.PIPE_LEN + 2.4, 0.0))
    c.line(*a, *b, w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)


def _text() -> tuple[list[str], list[str]]:
    notes = [
        "First angle; SECTION A-A is on the right-hand bore's axis. Origin "
        "on the jack's centre plane, in its front face, at the board's top "
        "surface: X back, Y across, Z up. The part is symmetric about "
        "Y = 0.",
        f"Two light pipes, Bivar {A.PIPE_PART} in {A.PIPE_MATERIAL}, pressed "
        "in from the facet until the flange seats.",
    ]
    notes += list(A.ADAPTER.notes)
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
           for s in A.ADAPTER.sources]
    return notes, src


def _bore_rows() -> list[list[str]]:
    rows = []
    for name, side in (("B1", +1), ("B2", -1)):
        rows.append([
            name,
            f"{side * A.BORE_Y:+.2f}",
            f"{A.BORE_X:.2f} / {A.BORE_Z:.2f}",
            f"{A.BORE_DIA:.2f}",
            f"{A.PRESS_DIA:.2f}",
            f"{A.PRESS_LEN:.2f}",
            f"{A.BORE_ANGLE:g}",
        ])
    return rows


def _jack_rows() -> list[list[str]]:
    """What the adapter is built to, and where each figure comes from."""
    return [
        ["LED window", f"{A.WINDOW_Y0:.2f}..{A.WINDOW_Y1:.2f}",
         f"{A.WINDOW_Z0:.2f}..{A.WINDOW_Z1:.2f}", "MEASURED"],
        ["Plug aperture", f"+/-{A.APERTURE_Y:.2f}",
         f"{A.APERTURE_Z0:.2f}..{A.APERTURE_Z1:.2f}", "MEASURED"],
        ["Latch keyway", f"+/-{A.KEYWAY_Y:.2f}",
         f"{A.KEYWAY_Z0:.2f}..{A.KEYWAY_Z1:.2f}", "MEASURED"],
        ["Shield", f"+/-{A.SHIELD_W / 2:.2f}", f"0..{A.SHIELD_H:.2f}",
         "STATED"],
        ["EMI spring, side", f"+/-{A.SIDE_SPRING_Y:.2f}",
         f"{A.SIDE_SPRING_Z0:.2f}..{A.SIDE_SPRING_Z1:.2f}", "MEASURED"],
        ["EMI spring, top",
         f"+/-{A.TOP_SPRING_Y0:.2f}..{A.TOP_SPRING_Y1:.2f}",
         f"{A.SHIELD_H:.2f}..{A.TOP_SPRING_Z:.2f}", "MEASURED"],
    ]


def render_light_pipe(*, drawing_no: str, version: str,
                      sheet_size: str = "A3") -> Sheet:
    spec = A.ADAPTER
    notes, src = _text()

    # The block of three views, in sheet millimetres, worked out before the
    # sheet exists: the notes band gets what is left under it.  Both
    # elevations run down to the board's top surface, because that is where Z
    # is measured from and a datum a view does not reach is a datum a reader
    # cannot check.
    front_w = A.WIDTH * SCALE
    view_h = A.CHEEK_Z1 * SCALE
    plan_h = (JACK_BACK - A.CHEEK_X0) * SCALE
    sect_w = (JACK_BACK - A.CHEEK_X0 + SECT_NOSE) * SCALE
    block_w = sect_w + GAP + front_w
    block_h = view_h + GAP + plan_h

    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src),
        max_height=style.SHEET_SIZES[sheet_size][1]
        - 2 * style.FRAME_MARGIN - block_h - TOP_ROOM - BOTTOM_ROOM)
    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(), subtitle=spec.subtitle,
        drawing_no=drawing_no, rev="A", version=version, drawn_by="generated",
        material="3D printed, opaque",
        tolerance=spec.tolerance, projection="first angle", scale="5:1"),
        notes_band_height=band_h)
    sheet.draw_frame()
    c = sheet.canvas
    area = sheet.area

    # Left-aligned, not centred: the dimensions that cannot go anywhere but
    # beside the front elevation go in the gutter this leaves on the right,
    # and the section's callouts go in the paper it leaves under the section.
    left = area.x + 2.0
    top = area.y1 - TOP_ROOM

    front = Rect(left + sect_w + GAP, top - view_h, front_w, view_h)
    plan = Rect(front.x, front.y - GAP - plan_h, front_w, plan_h)
    sect = Rect(left, front.y, sect_w, view_h)

    front_v = View(front, -A.WIDTH / 2, 0.0, A.WIDTH / 2, A.CHEEK_Z1,
                   SCALE, "5:1", front.cx, front.y)
    plan_v = View(plan, -A.WIDTH / 2, -JACK_BACK, A.WIDTH / 2, -A.CHEEK_X0,
                  SCALE, "5:1", plan.cx, plan.y + JACK_BACK * SCALE)
    sect_v = View(sect, A.CHEEK_X0 - SECT_NOSE, 0.0, JACK_BACK, A.CHEEK_Z1,
                  SCALE, "5:1", sect.x - (A.CHEEK_X0 - SECT_NOSE) * SCALE,
                  sect.y)

    draw_section(c, sect_v)
    draw_front(c, front_v)
    draw_plan(c, plan_v)

    for r, name in ((front, "FRONT ELEVATION"), (plan, "PLAN"),
                    (sect, "SECTION A-A")):
        c.text(r.cx, r.y1 + 3.4, name, size=style.T_LABEL, anchor="middle",
               bold=True)

    _dimension_front(c, front_v, front)
    _dimension_plan(c, plan_v, plan)
    _dimension_section(c, sect_v, sect)
    _section_marks(c, front_v, plan_v)

    rows = _bore_rows()
    block = sheet.column_block(sheet.table_height("BORE SCHEDULE", len(rows)))
    sheet.table(block, "BORE SCHEDULE",
                ["ID", "Y mm", "TIP X / Z mm", "DIA mm", "PRESS mm",
                 "PRESS LEN", "DEG"],
                rows, ["start", "end", "end", "end", "end", "end", "end"])

    rows = _jack_rows()
    title = f"THE JACK, {A.JACK_DESIGNATOR} {A.JACK_PART}"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["FEATURE", "Y mm", "Z mm", "READ FROM"], rows,
                ["start", "end", "end", "start"])

    spill = notes_spill_needed(sheet, notes, src, band_cols)
    want = legend_height(len(LEGEND)) + (spill + 4.0 if spill else 0.0)
    if sheet.column_remaining < want:
        raise SystemExit(
            f"the light pipe sheet's column cannot hold the legend and the "
            f"notes' tail ({want:.0f} mm wanted, {sheet.column_remaining:.0f} "
            "mm left); shorten the notes")
    draw_legend(sheet, LEGEND)
    _place_notes_and_sources(sheet, notes, src, columns=band_cols, spill=spill)

    sheet.draw_title_block()
    return sheet


# ---------------------------------------------------------------------------
# dimensions
# ---------------------------------------------------------------------------

def _dimension_front(c: Canvas, v: View, r: Rect) -> None:
    """Widths above and below, the one height on the right.

    The gutter beside this view is nine millimetres wide -- the three views
    take all but thirty-four of the drawing area between them -- so only the
    overall height goes there, and the heights measured from the board's
    surface are dimensioned on the section, where the surface is a line
    rather than an edge seen end on.
    """
    dims.linear(c, v.pt(-A.ROOF_Y1, A.CHEEK_Z1), v.pt(A.ROOF_Y1, A.CHEEK_Z1),
                7.0, horizontal=True, value=2 * A.ROOF_Y1)
    # All three widths above the view.  Below it there is room for the
    # plan's caption and nothing else: the two views are sixteen millimetres
    # apart and a dimension line put there crosses that caption.
    dims.linear(c, v.pt(-A.SKIRT_Y0, A.CHEEK_Z1), v.pt(A.SKIRT_Y0, A.CHEEK_Z1),
                13.0, horizontal=True, value=2 * A.SKIRT_Y0,
                ext_start=r.y1 + 2.0)
    dims.linear(c, v.pt(-A.CHEEK_Y0, A.CHEEK_Z1), v.pt(A.CHEEK_Y0, A.CHEEK_Z1),
                19.0, horizontal=True, value=2 * A.CHEEK_Y0,
                ext_start=r.y1 + 2.0)
    dims.linear(c, v.pt(A.ROOF_Y1, A.SKIRT_Z0), v.pt(A.ROOF_Y1, A.CHEEK_Z1),
                7.0, horizontal=False, value=A.CHEEK_Z1 - A.SKIRT_Z0)
    dims.datum_marker(c, *v.pt(0, 0.0), label="Y0 Z0", label_dy=-5.2)


def _dimension_plan(c: Canvas, v: View, r: Rect) -> None:
    """Depths in the gutter on the right, the bore across the bottom.

    The slot is called out rather than dimensioned twice: there are two of
    them, they are identical, and a third row of dimensions under this view
    would take the notes band's last ten millimetres.
    """
    def pt(x, y):
        return v.pt(y, -x)

    # One dimension each side: the gutter on the right is nine millimetres
    # to the annotation column, and the paper on the left is the section's
    # callouts.
    dims.linear(c, pt(A.CHEEK_X0, -A.ROOF_Y1), pt(A.ROOF_X1, -A.ROOF_Y1),
                -10.0, horizontal=False, value=A.ROOF_X1 - A.CHEEK_X0)
    dims.linear(c, pt(A.CHEEK_X0, A.ROOF_Y1), pt(0.0, A.ROOF_Y1), 7.0,
                horizontal=False, value=-A.CHEEK_X0)
    dims.linear(c, pt(A.SLOT_X1, 0.0), pt(A.SLOT_X1, A.BORE_Y),
                r.y - 9.0 - v.y(-A.SLOT_X1), horizontal=True,
                value=A.BORE_Y, ext_start=r.y - 2.0)
    dims.leader(c, pt(A.SLOT_X1 * 0.75, -(A.SLOT_Y0 + A.SLOT_Y1) / 2),
                (r.x - 6.0, v.y(-A.SLOT_X1) - 6.0),
                f"2 slots {A.SLOT_Y1 - A.SLOT_Y0:.2f} x {A.SLOT_X1:.2f}, "
                "clear of the top EMI springs")
    # Beside the marker, as in the elevation: directly under it is
    # the view's own centre line.
    dims.datum_marker(c, *pt(0.0, 0.0), label="X0 Y0", label_dx=-6.0,
                      label_dy=-5.2)


#: Where the section's callouts stack.  Far enough right of the bore that a
#: leader's text, which is written on the far side of its elbow, runs into
#: the empty paper under the section rather than off the frame.
CALLOUT_X = 44.0
CALLOUT_STEP = 7.0


def _dimension_section(c: Canvas, v: View, r: Rect) -> None:
    """The bore, the pocket and the clearances, all in true shape here."""
    # The two heights from the board's top surface, in the gutter this view
    # shares with the plan below it.
    dims.linear(c, v.pt(JACK_BACK, 0.0), v.pt(JACK_BACK, A.CHEEK_Z0), 5.0,
                horizontal=False, value=A.CHEEK_Z0)
    dims.linear(c, v.pt(JACK_BACK, 0.0), v.pt(JACK_BACK, A.ROOF_Z0), 13.0,
                horizontal=False, value=A.ROOF_Z0, ext_start=r.x1 + 2.0)

    below = r.y - 20.0
    seat = v.pt(*bore_point(A.PIPE_LEN, A.PRESS_DIA / 2))
    dims.leader(c, seat, (r.x + CALLOUT_X, below),
                f"Ø{A.PRESS_DIA:.2f} x {A.PRESS_LEN:.2f} press fit")
    mid = v.pt(*bore_point((A.PIPE_LEN - A.PRESS_LEN) / 2, A.BORE_DIA / 2))
    dims.leader(c, mid, (r.x + CALLOUT_X, below - CALLOUT_STEP),
                f"Ø{A.BORE_DIA:.2f} bore, {A.BORE_ANGLE:g} deg")
    dims.leader(c, v.pt(A.POCKET_X0, (A.POCKET_Z0 + A.POCKET_Z1) / 2),
                (r.x + CALLOUT_X, below - 2 * CALLOUT_STEP),
                f"pocket {-A.POCKET_X0:.2f} deep")
    nearest = A.BORE_X + A.PIPE_DIA / 2 * H
    dims.leader(c, v.pt(nearest / 2, A.BORE_Z),
                (r.x + CALLOUT_X, below - 3 * CALLOUT_STEP),
                f"{-nearest:.2f} air gap to J9")
    dims.leader(c, v.pt(0.0, A.APERTURE_Z1),
                (r.x + CALLOUT_X, below - 4 * CALLOUT_STEP),
                f"{A.CHEEK_Z0 - A.APERTURE_Z1:.2f} clear of the plug")
    dims.leader(c, v.pt(0.5, A.SHIELD_H),
                (r.x + CALLOUT_X, below - 5 * CALLOUT_STEP),
                f"{A.ROOF_Z0 - A.SHIELD_H:.2f} clear of the shield")
    dims.leader(c, v.pt(0.3, (A.WINDOW_Z0 + A.WINDOW_Z1) / 2),
                (r.x + CALLOUT_X, below - 6 * CALLOUT_STEP),
                f"LED window, {A.WINDOW_Z1 - A.WINDOW_Z0:.2f} high",
                colour=style.C_HIGHLIGHT)
    dims.datum_marker(c, *v.pt(0.0, 0.0), label="X0 Z0", label_dx=-7.5,
                      label_dy=-5.2)


def _section_marks(c: Canvas, front: View, plan: View) -> None:
    """The A-A cutting plane, marked on the two views it is taken from."""
    for v, a, b in ((front, front.pt(A.BORE_Y, 0.0),
                     front.pt(A.BORE_Y, A.CHEEK_Z1)),
                    (plan, plan.pt(A.BORE_Y, -JACK_BACK),
                     plan.pt(A.BORE_Y, -A.CHEEK_X0))):
        c.line(a[0], a[1] - 4.0, b[0], b[1] + 4.0, w=style.W_CENTRE,
               colour=style.C_DIM, dash=style.D_CENTRE)
        c.arrow(a[0], a[1] - 4.0, 90, colour=style.C_DIM)
        c.arrow(b[0], b[1] + 4.0, -90, colour=style.C_DIM)
        c.text(a[0] + 2.2, a[1] - 5.6, "A", size=style.T_LABEL,
               colour=style.C_DIM, bold=True)
        c.text(b[0] + 2.2, b[1] + 4.6, "A", size=style.T_LABEL,
               colour=style.C_DIM, bold=True)
