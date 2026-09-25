"""Assembly and fabrication drawing for the camera holder on the TT plate.

Three views, first angle, the way the camera position sheets lay theirs out:
the front elevation looking along +Y, the end elevation seen from the right
and drawn on the left, and the plan under the end elevation.  The holder is
four printed boxes-and-bores parts, so every view is drawn from the same
boxes ``holder.py`` gives the STEP and ``verify.py``: each part's outline is
the silhouette of its boxes' union, and what a nearer part hides is left out
rather than dashed, which on a frame this open would be most of the drawing.

The elevations also carry the 65 degree lens's field of view to frame A's
edges, as ``RPICAM-OVER-PLATE`` draws it, because the reason the holder is
the height it is is on those two lines.
"""

from __future__ import annotations


from raspberry_pi_camera import optics
from tinytapeout.camera_holder import holder as H
from tinytapeout.boards import BOARDS as TT
from tinytapeout.mounting_plate.plate import PLACEMENTS, STANDOFF_HEIGHT
from tools.layout import drawing_name

from . import dims, style
from .board_sheet import draw_legend, note_blocks
from .sheet import Rect, Sheet, TitleBlock
from .view import View, scale_text

#: The camera position sheet this holder is built to, by its own name.
POSITION_SHEET = drawing_name("raspberry-pi-camera", "over-tt-mounting-plate")

SCALE = 0.5
PLAN_SCALE = 0.4
LEFT = 16.0
GAP = 12.0
CAPTION = 7.0
UNDER = 28.0            # two lanes of dimensions under each elevation
RIGHT = 30.0            # the height dimensions right of the front elevation
PLAN_UNDER = 16.0
NO_BAND = 2.0

PART = dict(w=style.W_OUTLINE, colour=style.C_LINE)
BOUGHT = dict(w=style.W_COMPONENT, colour=style.C_HIGHLIGHT)
ADJACENT = dict(w=style.W_PHANTOM, colour=style.C_PHANTOM,
                dash=style.D_PHANTOM)
RAY = ("line", style.W_THIN, style.C_FRAME_A, None)

LEGEND = [
    ("outline", "Printed part"),
    (("line", style.W_COMPONENT, style.C_HIGHLIGHT, None),
     "Camera Module, bought"),
    ("phantom", "The plate and every revision's board, adjacent"),
    (RAY, "The 65 deg lens's field of view, to frame A's edges"),
    ("dimension", "Dimension, extension and leader"),
]


# ---------------------------------------------------------------------------
# silhouettes
# ---------------------------------------------------------------------------

def silhouette(rects):
    """The outline of a union of rectangles, as axis-aligned segments.

    Every rectangle edge is cut at every other rectangle's coordinates, and
    a piece of edge is outline where exactly one side of it is inside the
    union.  Collinear pieces are then joined, so a face two boxes share is
    one line and a face they meet across is none.
    """
    if not rects:
        return []
    xs = sorted({v for r in rects for v in (r[0], r[1])})
    ys = sorted({v for r in rects for v in (r[2], r[3])})

    def inside(x, y):
        return any(r[0] < x < r[1] and r[2] < y < r[3] for r in rects)

    segs = []
    for i in range(len(xs) - 1):
        xm = (xs[i] + xs[i + 1]) / 2
        for y in ys:
            if inside(xm, y - 1e-6) != inside(xm, y + 1e-6):
                segs.append(("h", y, xs[i], xs[i + 1]))
    for j in range(len(ys) - 1):
        ym = (ys[j] + ys[j + 1]) / 2
        for x in xs:
            if inside(x - 1e-6, ym) != inside(x + 1e-6, ym):
                segs.append(("v", x, ys[j], ys[j + 1]))
    return _join(segs)


def _join(segs):
    out = []
    for kind in ("h", "v"):
        lines: dict[float, list[tuple[float, float]]] = {}
        for k, at, a, b in segs:
            if k == kind:
                lines.setdefault(round(at, 6), []).append((a, b))
        for at, runs in lines.items():
            runs.sort()
            cur = list(runs[0])
            for a, b in runs[1:]:
                if a <= cur[1] + 1e-6:
                    cur[1] = max(cur[1], b)
                else:
                    out.append((kind, at, *cur))
                    cur = [a, b]
            out.append((kind, at, *cur))
    return out


def _clip(seg, covers):
    """What is left of an axis-aligned segment once *covers* are taken out."""
    kind, at, a, b = seg
    pieces = [(a, b)]
    for r in covers:
        if kind == "h":
            if not (r[2] < at < r[3]):
                continue
            lo, hi = r[0], r[1]
        else:
            if not (r[0] < at < r[1]):
                continue
            lo, hi = r[2], r[3]
        nxt = []
        for p, q in pieces:
            if hi <= p or lo >= q:
                nxt.append((p, q))
                continue
            if p < lo:
                nxt.append((p, lo))
            if hi < q:
                nxt.append((hi, q))
        pieces = nxt
    return [(kind, at, p, q) for p, q in pieces if q - p > 1e-6]


def _project(box, view: str):
    """A box's rectangle in a view, and how near it is to the viewer."""
    if view == "front":            # looking along +Y: X across, Z up
        return (box.x0, box.x1, box.z0, box.z1), -box.y0, -box.y1
    if view == "end":              # from the right, looking along -X
        return (box.y0, box.y1, box.z0, box.z1), box.x1, box.x0
    return (box.x0, box.x1, box.y0, box.y1), box.z1, box.z0     # plan


def _all_boxes():
    """Every holder box, and the camera's, with the part each belongs to."""
    out = []
    for p in H.ASSEMBLY:
        for b in p.boxes:
            out.append((p.key, b, PART))
        for c in p.bosses:
            r = c.dia / 2
            out.append((p.key, H.Box(c.x - r, c.x + r, c.y - r, c.y + r,
                                     c.z0, c.z1, c.what), PART))
    for b in H.camera_boxes():
        out.append(("camera", b, BOUGHT))
    return out


def draw_parts(c, v: View, view: str) -> None:
    """Every part's silhouette in *view*, less what a nearer part hides."""
    items = _all_boxes()
    by_part: dict[str, list] = {}
    for key, b, kw in items:
        by_part.setdefault(key, []).append((b, kw))
    for key, members in by_part.items():
        rects = [_project(b, view)[0] for b, _ in members]
        near = max(_project(b, view)[1] for b, _ in members)
        # A box of another part hides this part's lines only where it is
        # wholly in front of all of this part.
        covers = [_project(b, view)[0] for k, b, _ in items
                  if k != key and _project(b, view)[2] >= near - 1e-9]
        kw = members[0][1]
        for seg in silhouette(rects):
            for kind, at, a, b in _clip(seg, covers):
                if kind == "h":
                    c.line(*v.pt(a, at), *v.pt(b, at), **kw)
                else:
                    c.line(*v.pt(at, a), *v.pt(at, b), **kw)


def draw_adjacent(c, v: View, view: str) -> None:
    """The plate, and every revision's board on its standoffs, in phantom."""
    lo, hi = optics.plate_board_plane()
    w, h = H.PLATE_W, H.PLATE_H
    if view == "plan":
        c.rect(*v.pt(0, 0), v.d(w), v.d(h), weight=ADJACENT["w"],
               colour=ADJACENT["colour"], dash=ADJACENT["dash"])
        seen = set()
        for pl in PLACEMENTS.values():
            o = TT[pl["revision"]].outline
            key = (pl["dx"], pl["dy"], o.width, o.height)
            if key in seen:
                continue
            seen.add(key)
            c.rect(*v.pt(pl["dx"], pl["dy"]), v.d(o.width), v.d(o.height),
                   weight=ADJACENT["w"], colour=ADJACENT["colour"],
                   dash=ADJACENT["dash"])
        return
    size = w if view == "front" else h
    c.rect(*v.pt(0, -H.PLATE_T), v.d(size), v.d(H.PLATE_T),
           weight=ADJACENT["w"], colour=ADJACENT["colour"],
           dash=ADJACENT["dash"])
    x0, y0, x1, y1 = optics.plate_boards_union()
    a, b = (x0, x1) if view == "front" else (y0, y1)
    c.rect(*v.pt(a, STANDOFF_HEIGHT), v.d(b - a), v.d(hi - STANDOFF_HEIGHT),
           weight=ADJACENT["w"], colour=ADJACENT["colour"],
           dash=ADJACENT["dash"])


def draw_rays(c, v: View, view: str) -> None:
    """The stock lens's field of view, from the lens face to frame A."""
    f = H.FRAME
    plane = H.BOARD_PLANE
    u = H.AXIS_X if view == "front" else H.AXIS_Y
    lo, hi = (f.x0, f.x1) if view == "front" else (f.y0, f.y1)
    apex = v.pt(u, H.LENS_FACE)
    for e in (lo, hi):
        c.line(*apex, *v.pt(e, plane), w=RAY[1], colour=RAY[2])
    c.line(*v.pt(u, plane - 3.0), *v.pt(u, H.BEAM_Z1 + 4.0),
           w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------

def _text():
    lens = H.LENS
    lo, hi = optics.plate_board_plane()
    on_sensor, on_subject = optics.blur(H.LENS_FACE - hi)
    spare = H.LENS_FACE - hi - H.REQUIRED.z
    notes = [
        "First angle, in TT-MP-PLATE's coordinates, Z up from the plate's "
        "TOP face. The right side frame is the left one mirrored.",
        f"FOR: the lens over {POSITION_SHEET}'s frame A, at "
        f"({H.AXIS_X:.2f}, {H.AXIS_Y:.2f}), high enough for the stock "
        f"{lens.key} deg lens to take in every revision's whole board: "
        f"{H.REQUIRED.z:.2f} over the highest board face, {hi:.2f} up, so "
        f"{H.LENS_FACE_MIN:.2f}. Set at {H.LENS_FACE:.2f}, {spare:.2f} over "
        "for the print. For a camera mode reading the whole sensor.",
        "TURN THE CAMERA RIGHT: ASSUMED that the picture's long side runs "
        "along the camera board's 25 mm width, which nobody publishes; it "
        "has to run along X, and a quarter turn out the picture is "
        f"{H.turned_wrong():.1f} mm short at each end. If the first picture "
        "is the wrong way, turn the carrier a quarter: its fixings are "
        "square about the lens.",
        f"FOCUS: stock lens \"Approx 1 m to infinity\"; at "
        f"{H.LENS_FACE - hi:.1f} the boards are OUT OF FOCUS, a point about "
        f"{on_sensor / optics.PIXEL_PITCH:.0f} pixels, {on_subject:.1f} mm "
        f"on the board ({POSITION_SHEET}).",
        "MAKE the parts from tt-camera-holder-*.step; this sheet is the "
        f"assembly. Holes: M4 {H.M4_CLEAR:.1f}, M3 {H.M3_CLEAR:.1f}, M2 "
        f"{H.M2_CLEAR:.1f}, M2 nut pockets {H.M2_POCKET_AF:.1f} AF. Ream "
        "the side frames' holes, which print lying down. Opaque PETG, four "
        "perimeters, matte black if it can be: the side frames show in the "
        "picture's margin. The camera's holes are 2.0 +/-"
        f"{H.CAMERA.hole_dia_tol:.1f}: open a tight one with a 2.0 drill.",
        "ACCESS: front and back are open over every Pmod host and USB-C; "
        "the side frames are windows over the unfitted side Pmods J12-J14. "
        "Buttons are not in the board data and not checked; they are "
        f"pressed from above, under a beam {H.BEAM_Z0:.0f} mm up.",
        "FIXING: the feet share the plate's own M4 side fixings, so no new "
        f"hole; on a chassis the M4s are {H.FOOT_T:g} mm longer than the "
        "plate's own. Plug the FFC in first -- its latch is out of reach "
        "under the carrier -- and take it up and back over the beam.",
    ]
    src = [f"{s.label}: {s.ref} - {s.note}" for s in H.SOURCES]
    return notes, src


def _tables(sheet: Sheet) -> None:
    rows = []
    for p in H.PARTS:
        b = p.bbox
        rows.append([p.name, str(p.count),
                     f"{b.x1 - b.x0:.1f} x {b.y1 - b.y0:.1f} x "
                     f"{b.z1 - b.z0:.1f}",
                     p.print_note.split(":")[0].split(";")[0].rstrip(".")])
    block = sheet.column_block(sheet.table_height("PARTS, PRINTED", len(rows)))
    sheet.table(block, "PARTS, PRINTED",
                ["PART", "QTY", "X x Y x Z mm", "PRINT"], rows,
                ["start", "end", "end", "start"])

    rows = []
    for what, n, where in H.FASTENERS:
        screw, standard, extra = what.split(", ")
        rows.append([str(n), f"{screw}, {standard}", extra,
                     where.split(";")[0].split(".")[0].split(",")[0]])
    block = sheet.column_block(sheet.table_height("FASTENERS", len(rows)))
    sheet.table(block, "FASTENERS", ["QTY", "SCREW", "WITH", "JOINS"], rows,
                ["end", "start", "start", "start"])

    lo, hi = optics.plate_board_plane()
    rows = [
        ["Board faces", f"{lo:.2f} to {hi:.2f}"],
        ["Lens face, least", f"{H.LENS_FACE_MIN:.2f}"],
        ["Lens face, as built", f"{H.LENS_FACE:.2f}"],
        ["Camera board", f"{H.PCB_FRONT:.2f} to {H.PCB_BACK:.2f}"],
        ["Carrier", f"{H.CARRIER_Z0:.2f} to {H.CARRIER_Z1:.2f}"],
        ["Beam", f"{H.BEAM_Z0:.2f} to {H.BEAM_Z1:.2f}"],
    ]
    title = "HEIGHTS ABOVE THE PLATE FACE, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["", "Z"], rows, ["start", "end"])


def _dimension(sheet: Sheet, front: View, end: View, plan: View) -> None:
    c = sheet.canvas
    right = front.pt(front.model_x1, 0.0)
    dims.linear(c, right, front.pt(H.AXIS_X, H.LENS_FACE), 8.0,
                horizontal=False, value=H.LENS_FACE)
    dims.linear(c, right, front.pt(H.WALL_OUTER, H.BEAM_Z1),
                8.0 + style.DIM_STEP, horizontal=False, value=H.BEAM_Z1)
    base = front.y(-H.PLATE_T)
    dims.linear(c, front.pt(0.0, -H.PLATE_T), front.pt(H.AXIS_X, 0.0),
                -(8.0 + front.y(0.0) - base), horizontal=True,
                value=H.AXIS_X)
    # The overall width, a lane under the lens's X.
    x1 = 2 * H.MIRROR_X - H.WALL_OUTER
    dims.linear(c, front.pt(H.WALL_OUTER, -H.PLATE_T),
                front.pt(x1, -H.PLATE_T),
                -(8.0 + style.DIM_STEP), horizontal=True,
                value=x1 - H.WALL_OUTER)
    base = end.y(-H.PLATE_T)
    dims.linear(c, end.pt(0.0, -H.PLATE_T), end.pt(H.AXIS_Y, 0.0),
                -(8.0 + end.y(0.0) - base), horizontal=True, value=H.AXIS_Y)
    dims.linear(c, end.pt(H.FRAME_Y0, -H.PLATE_T),
                end.pt(H.FRAME_Y1, -H.PLATE_T),
                -(8.0 + style.DIM_STEP), horizontal=True,
                value=H.FRAME_Y1 - H.FRAME_Y0)
    # The carrier's square of fixings, on the plan.
    f = H.CARRIER_FIX
    dims.linear(c, plan.pt(H.AXIS_X - f, H.AXIS_Y + f),
                plan.pt(H.AXIS_X + f, H.AXIS_Y + f),
                plan.y(H.AXIS_Y + H.CARRIER_HALF) - plan.y(H.AXIS_Y + f)
                + 5.0, horizontal=True, value=2 * f)


def _plan_holes(c, v: View) -> None:
    """The holes a builder drives a screw into, seen from above."""
    for p in H.ASSEMBLY:
        for h in p.holes:
            if "camera fixing" in h.what:
                continue            # under the pad
            x, y = v.pt(h.x, h.y)
            c.circle(x, y, v.d(h.dia / 2), w=style.W_OUTLINE, fill="#ffffff")
            dims.centre_mark(c, x, y, v.d(h.dia / 2), over=1.0)


def render_holder(*, title: str, subtitle: str, drawing_no: str,
                  version: str, sheet_size: str = "A3") -> Sheet:
    notes, src = _text()
    sheet = Sheet(sheet_size, TitleBlock(
        title=title.upper(), subtitle=subtitle,
        drawing_no=drawing_no, rev="A", version=version,
        drawn_by="generated", scale=f"{scale_text(1, 1 / SCALE)}, PLAN "
        f"{scale_text(1, 1 / PLAN_SCALE)}", projection="first angle",
        material="PETG, printed, opaque",
        tolerance="print +/-0.2, Z DERIVED"), notes_band_height=NO_BAND)
    sheet.draw_frame()
    c = sheet.canvas
    area = sheet.area

    # Model extents.
    fx0, fx1 = H.WALL_OUTER - 2.0, 2 * H.MIRROR_X - H.WALL_OUTER + 2.0
    ey0 = min(0.0, H.FRAME.y0) - 2.0
    ey1 = max(H.PLATE_H, H.FRAME.y1) + 2.0
    fx0 = min(fx0, H.FRAME.x0 - 2.0)
    fx1 = max(fx1, H.FRAME.x1 + 2.0)
    z0, z1 = -H.PLATE_T - 1.0, H.BEAM_Z1 + 5.0
    s, sp = SCALE, PLAN_SCALE
    elev_h = (z1 - z0) * s
    top = area.y1 - CAPTION
    left = area.x + LEFT
    end_w = (ey1 - ey0) * s
    end = View(Rect(left, top - elev_h, end_w, elev_h), ey0, z0, ey1, z1, s,
               scale_text(1, 1 / s), left - ey0 * s, top - z1 * s)
    fleft = left + end_w + GAP
    front = View(Rect(fleft, top - elev_h, (fx1 - fx0) * s, elev_h), fx0, z0,
                 fx1, z1, s, scale_text(1, 1 / s), fleft - fx0 * s,
                 top - z1 * s)
    px0, px1 = fx0, fx1
    py0, py1 = ey0, ey1
    ptop = top - elev_h - UNDER - CAPTION
    plan_h = (py1 - py0) * sp
    plan = View(Rect(left, ptop - plan_h, (px1 - px0) * sp, plan_h), px0,
                py0, px1, py1, sp, scale_text(1, 1 / sp), left - px0 * sp,
                ptop - py1 * sp)

    for v, view in ((front, "front"), (end, "end")):
        draw_adjacent(c, v, view)
        draw_rays(c, v, view)
        draw_parts(c, v, view)
    draw_adjacent(c, plan, "plan")
    draw_parts(c, plan, "plan")
    _plan_holes(c, plan)
    # Frame A's footprint on the plan, and the lens axis.
    f = H.FRAME
    a, b = plan.pt(f.x0, f.y0), plan.pt(f.x1, f.y1)
    c.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], weight=style.W_PHANTOM,
           colour=style.C_FRAME_A, dash=style.D_PHANTOM)
    ax, ay = plan.pt(H.AXIS_X, H.AXIS_Y)
    dims.centre_mark(c, ax, ay, 1.6, colour=style.C_FRAME_A, over=2.6)
    _dimension(sheet, front, end, plan)

    for v, name in ((end, "END ELEVATION"), (front, "FRONT ELEVATION"),
                    (plan, f"PLAN, {plan.scale_label}, NOT IN PROJECTION")):
        c.text(v.rect.cx, v.rect.y1 + 3.0, name, size=style.T_LABEL,
               anchor="middle", bold=True)

    _tables(sheet)
    draw_legend(sheet, LEGEND + [("frame_a", "Frame A of "
                                  f"{POSITION_SHEET}, on the board plane")])

    # Notes: beside the plan, then across under it, then the column's foot.
    base = sheet.frame.y + 3.0
    x0, x1 = sheet.frame.x + 4.0, area.x1 - 2.0
    elev_bottom = front.rect.y - UNDER
    plan_bottom = plan.rect.y - PLAN_UNDER
    beside = plan.rect.x1 + 10.0
    cols = [Rect(beside, plan_bottom, x1 - beside, elev_bottom - plan_bottom)]
    w = (x1 - x0 - 8.0) / 2
    cols += [Rect(x0 + i * (w + 8.0), base, w, plan_bottom - base)
             for i in range(2)]
    blocks = note_blocks(notes, src)
    if not sheet.notes_columns(cols, blocks, dry=True):
        h = 20.0
        while h <= sheet.column_remaining - 4.0:
            probe = Rect(sheet.column.x, sheet.column.y,
                         sheet.column.w - sheet.COLUMN_GUTTER, h)
            if sheet.notes_columns(cols + [probe], blocks, dry=True):
                break
            h += 2.0
        else:
            raise SystemExit("the camera holder sheet's notes do not fit")
        cols.append(sheet.column_block_bottom(h))
    sheet.notes_columns(cols, blocks)
    sheet.draw_title_block()
    return sheet
