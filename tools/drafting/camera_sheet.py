"""Camera position sheets: where to put an OV5647 camera over a board.

Every other sheet in this repository draws a part.  These draw a part and a
place to stand, and the place to stand is a height first: the question the
sheet answers is how far above the board the camera goes and over which
point, so the ELEVATIONS are the primary views and the plan is the smaller
one.

Three views, first angle:

* the front elevation, looking along +Y, with the subject's X across it;
* the end elevation, seen from the right and so drawn on the left, with Y
  across it, at the front elevation's scale;
* the plan, at a smaller scale under the end elevation, with the footprints
  the picture covers, one per thing worth framing.  It is the view that
  says which way the picture lies over the subject and where the second
  frame is; the table carries every figure in it, and at the elevations'
  own scale it took the paper the notes need.

The two elevations are the two axes of the picture.  The 65 degree figure the
stock lens is sold under is its DIAGONAL; what reaches the edge of the
picture is the declared angle along each axis, 53.50 across the sensor's long
side and 41.41 along its short side, and which of the two lies along the
subject's X depends on which way the camera is turned.  Each elevation draws
the angle that lies in its own plane, from the lens to the edges of the frame,
and dimensions the height and the lateral position of the lens.  Only the
stock 65 degree lens is drawn: the 120 degree lens's declared pair
contradicts itself, so either of its two cones would be a drawing of one of
two figures that cannot both be right, and it has no published near limit
to check a height against.  Its heights are in the table.

One sheet per SUBJECT, both lenses in its tables, rather than one per lens:
the person reading it has one board in front of them.  The frame footprints
do not depend on the lens -- a frame is the sensor's own 4:3 round its target,
which is the shape of the file that comes out -- so a subject has exactly as
many rectangles as it has things worth framing, and the lens only decides how
high above them the camera goes.  See :mod:`raspberry_pi_camera.optics`.
"""

from __future__ import annotations

import math

from raspberry_pi_camera import optics
from raspberry_pi_camera.optics import (LENSES, Subject,  # noqa: E501
                                        blur, coincident_edges, place)

from . import dims, style
from .board_sheet import (draw_feature, draw_holes, draw_legend, draw_pmod,
                          note_blocks, outline_path)
from .plate_sheet import draw_slot
from .sheet import Rect, Sheet, TitleBlock
from .view import STANDARD_SCALES, View, scale_text

#: The lens every view draws.  The other is in the tables only.
DRAWN = "65"

#: The library's notes band, shrunk to nothing: these sheets put their notes
#: in the paper the views leave instead.  See ``_note_columns``.
NO_BAND = 2.0

#: Room left of the end elevation and the plan: the datum labels.
LEFT = 20.0
#: Room under the plan, for the leader that points at two frame edges too
#: close together to draw as two lines, where a sheet has one.
PLAN_BOTTOM = 12.0
PLAN_BOTTOM_BARE = 9.0


def _plan_bottom(subject: Subject) -> float:
    return PLAN_BOTTOM if any(coincident_edges(subject.frames())) \
        else PLAN_BOTTOM_BARE

#: Room round the elevations, in sheet millimetres.  Each carries its height
#: dimensions on its outer side and its lateral dimension underneath, and a
#: caption above.
ELEV_OUTER = 26.0       # the side the height dimensions stand on
ELEV_UNDER = 15.0       # the lateral dimension, under the lowest line drawn
CAPTION = 7.0           # above every view
GAP = 10.0              # between the two elevations

#: How far above the lens the elevations reach, in model millimetres: room
#: for the camera module drawn over it.
ABOVE_LENS = 12.0

#: Radius of the arc that marks the angle at the lens, in sheet millimetres.
ARC_R = 11.0

#: A frame's colour, its legend style and its letter, by its position in the
#: subject's list.  Two of each, because no subject has three things worth
#: framing; a third would have to earn a third colour that still reads when
#: photocopied, so it fails loudly here rather than raising an IndexError
#: halfway down a drawing or, worse, being skipped by the checker.
FRAME_COLOURS = (style.C_FRAME_A, style.C_FRAME_B)
FRAME_LEGEND = ("frame_a", "frame_b")
FRAME_LETTERS = "AB"
MAX_FRAMES = len(FRAME_COLOURS)

#: The rays from the lens to the edge of frame A: solid, thin, frame A's
#: colour.  Solid so they are not read as the chain-double-dot footprint in
#: the plan, which is the same colour.
RAY = ("line", style.W_THIN, style.C_FRAME_A, None)

#: Radius of the lettered marker that names a frame at its own corner.
MARKER_R = 3.2

#: How far the datum label is tried from the datum, and in which order: the
#: quadrants a drafter would reach for first.
DATUM_LABEL_R = 6.5
DATUM_DIRS = ((-1, -1), (1, -1), (-1, 1), (1, 1))


class DoesNotFit(Exception):
    """This scale leaves the notes nowhere to go; try the next one down."""


def _plan_bbox(subject: Subject) -> tuple[float, float, float, float]:
    """Everything the plan has to cover: the subject and every frame."""
    spec = subject.spec
    xs = [0.0, spec.outline.width]
    ys = [0.0, spec.outline.height]
    for f in spec.features:
        xs += [f.x0, f.x1]
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            xs += [p.body_x0, p.body_x1]
            ys += [p.body_y0, p.body_y1]
    for s in spec.slots:
        xs += [s.x0 - s.width, s.x1 + s.width]
        ys += [s.y0 - s.width, s.y1 + s.width]
    for fr in subject.frames():
        xs += [fr.x0, fr.x1]
        ys += [fr.y0, fr.y1]
    return min(xs), min(ys), max(xs), max(ys)


def _below_plane(subject: Subject) -> list[tuple[str, float, float]]:
    """What the elevations draw under the plane Z is measured from.

    Each is (what, top, bottom), in millimetres above that plane, and only
    what is known: a slab whose height nobody publishes is not drawn at all,
    because an elevation is a scale drawing and a guessed slab would be
    measured off it.  The plate is drawn under the demo boards because its
    standoff is the plate's own figure; the Arty's thickness is not in its
    data, so that sheet draws the plane and the target on it and nothing
    below.
    """
    plane = subject.frames()[0].target.plane_above_subject
    spec = subject.spec
    t = spec.outline.thickness
    out = []
    if subject.key == "tt-mounting-plate":
        lo, hi = optics.plate_board_plane()
        out.append(("board", 0.0, -(hi - optics.plate_standoff())))
        out.append(("subject", -hi, -hi - t))
    elif plane == 0.0 and t:
        out.append(("subject", 0.0, -t))
    return out


def _elev_extent(subject: Subject, axis: str) -> tuple[float, float]:
    """The model range an elevation along *axis* covers, across the page."""
    fr = subject.frames()[0]
    lo, hi = (fr.x0, fr.x1) if axis == "X" else (fr.y0, fr.y1)
    o = subject.spec.outline
    if _below_plane(subject):
        lo, hi = min(lo, 0.0), max(hi, o.width if axis == "X" else o.height)
    return lo, hi


def _elev_heights(subject: Subject) -> tuple[float, float]:
    """The model range both elevations cover, up the page."""
    p = place(subject.frames()[0], LENSES[DRAWN])
    below = _below_plane(subject)
    return (min([b for _, _, b in below] + [0.0]) - 1.0, p.z + ABOVE_LENS)


def _fmt_mod(lens) -> str:
    if lens.min_object_distance is None:
        return "not published"
    return f"{lens.min_object_distance:.0f}"


def _focus_verdict(p) -> str:
    """What the height means against the lens's published near limit."""
    if p.too_close is None:
        return "UNKNOWN"
    return "TOO CLOSE" if p.too_close else "ok"


def _text(subject: Subject) -> tuple[list[str], list[str]]:
    """The notes and sources this sheet carries, built before it exists.

    Every figure in here is computed or quoted from
    :mod:`raspberry_pi_camera.optics`.  None is written out by hand: a second
    copy of a derived angle is a copy that goes stale the day the model
    changes, and the whole point of that module is that its numbers are
    checkable.
    """
    from raspberry_pi_camera import v1
    frames = subject.frames()
    stock = LENSES["65"]
    a = place(frames[0], stock)
    notes = [
        "First angle; the end elevation is seen from the right. The camera, "
        "a Camera Module v1.3 from its own data, looks straight down, in a "
        "mode reading the whole sensor. Z is to its entrance pupil, which "
        "nobody locates; ASSUMED behind the lens face by at most the lens's "
        f"{v1.LENS_TOP_Z:.2f} mm, so set the FACE at Z and the picture is up "
        f"to {100 * v1.LENS_TOP_Z / a.z:.1f}% larger, never smaller.",
        "A frame is the smallest rectangle of the sensor's own 4:3 holding "
        f"its target plus {optics.FRAME_MARGIN:.2f} mm all round, turned "
        "whichever way needs the lower camera; LONG says which. The margin "
        "is what absorbs where the stand ends up: "
        f"{optics.FRAME_MARGIN:.2f} mm of lateral error, or a lean of "
        f"{a.aim_tilt:.1f} deg at frame {FRAME_LETTERS[0]}'s Z, not both.",
    ]

    # Which plane each frame's height is set from.  One note, because a
    # reader who sets the stand from the wrong face gets a picture that is
    # smaller at the thing they are photographing, and nothing on the drawing
    # would tell them.
    # Grouped by plane, not listed per frame: where two frames are set from
    # one face, naming it for each would print its whole explanation twice.
    by_plane: dict[tuple[str, str], list[str]] = {}
    for letter, fr in zip(FRAME_LETTERS, frames):
        t = fr.target
        by_plane.setdefault((t.plane_name, t.plane_note), []).append(letter)
    planes = []
    for (name, plane_note), letters in by_plane.items():
        line = f"{'/'.join(letters)} from {name}"
        if plane_note:
            line += f" -- {plane_note}"
        planes.append(line)
    notes.append(
        "PLANE, which Z is measured from: " + "; ".join(planes)
        + ". A stand set h mm too low covers only (Z - h) / Z of what is "
        "drawn, so the error always loses the edges.")

    # What stands above the plane the first frame's height was set from, and
    # how high it may stand before it leaves the picture.
    for label, box in subject.standing:
        reach = ", ".join(
            f"{place(frames[0], ln).headroom(box):.1f} mm at {ln.key} deg"
            for ln in LENSES.values())
        notes.append(
            f"HEADROOM: {label[0].lower()}{label[1:]} stays in frame "
            f"{FRAME_LETTERS[0]}'s picture up to {reach} above the plane Z is "
            "set from. Higher, raise the camera.")

    # The one thing a reader has to be told before building anything, so it
    # goes above the derivations.
    verdicts = {_focus_verdict(place(fr, ln))
                for fr in frames for ln in LENSES.values()}
    if "TOO CLOSE" in verdicts:
        on_sensor, on_subject = blur(a.z)
        # Against the only close limits anyone publishes for a Raspberry Pi
        # camera, which are other sensors': the question a reader has once
        # the stock lens is ruled out is whether a focusable module would do.
        reach = []
        for quote, mm in optics.near_limits():
            ins = [FRAME_LETTERS[i] for i, fr in enumerate(frames)
                   if place(fr, stock).z >= mm]
            said = ("every Z here inside it" if len(ins) == len(frames)
                    else "no Z here inside it" if not ins
                    else "/".join(ins) + " inside it")
            reach.append(f'"{quote}", {said}')
        af = optics.AUTOFOCUS
        notes.append(
            f"FOCUS: {stock.mod_note} Every Z here is nearer, so on a stock "
            "OV5647 the board is OUT OF FOCUS: at frame "
            f"{FRAME_LETTERS[0]}'s Z a point spreads to "
            f"{on_sensor / optics.PIXEL_PITCH:.0f} pixels, about "
            f"{on_subject:.1f} mm on the board (DERIVED, thin lens ASSUMED "
            f"set at the {optics.FIXED_FOCUS_DISTANCE / 1000:.0f} m that "
            "implies). "
            "Raspberry Pi's focusable modules, other sensors: "
            + "; ".join(reach) + f". The OV5647 that focuses is Arducam's "
            f"B0176, {af.fov_h:.0f} x {af.fov_v:.0f} deg. {af.mod_note}")

    # The wide lens's declared pair does not agree with the sensor's shape,
    # so the picture runs over the rectangle drawn -- on the axis the height
    # was NOT set from, which depends on how the camera is turned.  Both are
    # read off the model rather than worded by hand, because a camera turned
    # through ninety degrees runs over in Y rather than across.
    for lens in LENSES.values():
        if lens.consistent:
            continue
        runs = []
        for letter, fr in zip(FRAME_LETTERS, frames):
            p = place(fr, lens)
            dx, dy = p.excess
            axis, over = ("X", dx) if dx >= dy else ("Y", dy)
            runs.append(f"{letter} by {over:.2f} mm in {axis}")
        notes.append(
            f"The {lens.key} deg lens's declared pair is not self-consistent: "
            f"{lens.fov_h:.0f} across a 4:3 sensor implies "
            f"{lens.consistent_v:.2f} down it, not {lens.fov_v:.0f}. Z is the "
            "greater of what the two ask for, so the picture runs OVER the "
            "rectangle -- " + ", ".join(runs) + " -- which is still covered.")

    notes.append(
        f'The "{stock.key} deg" name is the stock lens\'s DIAGONAL, which '
        "no vendor prints: 2 x atan(sqrt("
        f"{optics.IMAGE_AREA[0]:.2f}^2 + {optics.IMAGE_AREA[1]:.2f}^2) / 2 / "
        f"{optics.FOCAL_LENGTH:.2f}) = {optics.DIAGONAL_FROM_IMAGE_AREA:.2f} "
        f"deg from the image area, {optics.DIAGONAL_FROM_ARRAY:.2f} from the "
        "pixel array. Every Z here is from the declared angle along each "
        f"axis instead. {optics.NOMINAL_DIAGONAL:.0f} deg across frame "
        f"{FRAME_LETTERS[0]}'s long side would give Z {a.naive_z:.1f} and "
        f"lose {a.naive_shortfall:.1f} mm off each end of it.")

    # The sheets are lettered in ASCII, and the pages they quote are not.
    # Nothing here is a character-for-character quote, so say so once rather
    # than let a reader take "1.4 um x 1.4 um" for what the page prints.
    notes.append(
        "Quotes are transliterated to ASCII: x, um and infinity for the "
        "signs the cached pages print.")

    for letter, fr in zip(FRAME_LETTERS, frames):
        if fr.target.note:
            notes.append(f"Frame {letter}, {fr.target.label}: "
                         f"{fr.target.note}")
    notes += list(subject.notes)

    # Every source the sheet makes a claim from, the autofocus variant's
    # included: the AUTOFOCUS note above says the B0176 carries a motorised
    # lens and a close focus setting, and that comes from Arducam's motorized
    # focus page, not from the catalogue row.  It was cited nowhere.
    seen = []
    for s in list(subject.sources) + [s for ln in LENSES.values()
                                      for s in ln.sources] + list(af.sources):
        entry = f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
        if entry not in seen:
            seen.append(entry)
    return notes, seen


def _draw_plan(sheet: Sheet, subject: Subject, view: View) -> None:
    c = sheet.canvas
    spec = subject.spec
    outline_path(c, view, spec)
    draw_holes(c, view, spec.holes)
    for s in spec.slots:
        draw_slot(c, view, s, colour=style.C_HIGHLIGHT)
    for f in spec.features:
        draw_feature(c, view, f)
    for p in spec.pmods:
        draw_pmod(c, view, p, spec)


def _obstacle_segments(subject: Subject, view: View):
    """The ruled lines near the datum, in sheet millimetres.

    Segments, not infinite lines: a frame's left edge is no obstacle to a
    label placed above the datum if that edge is nowhere near it, and treating
    every edge as an infinite line was why the first version of this found no
    clear quadrant at all and put the label across two frame edges.
    """
    out = []
    spec = subject.spec
    boxes = [(f.x0, f.y0, f.x1, f.y1) for f in subject.frames()]
    boxes += [(f.x0, f.y0, f.x1, f.y1) for f in spec.features]
    # Holes and slots too.  They are circles rather than rectangles, so their
    # bounding box is what the label has to clear -- and leaving them out put
    # the mounting plate's datum label on top of a slot, which is the one
    # thing near that corner.
    for h in spec.holes:
        r = max(h.dia, h.keepout_dia or 0.0) / 2 + style.CENTRE_OVER
        boxes.append((h.x - r, h.y - r, h.x + r, h.y + r))
    for sl in spec.slots:
        r = sl.width / 2 + style.CENTRE_OVER
        boxes.append((min(sl.x0, sl.x1) - r, min(sl.y0, sl.y1) - r,
                      max(sl.x0, sl.x1) + r, max(sl.y0, sl.y1) + r))
    for x0, y0, x1, y1 in boxes:
        sx0, sy0 = view.pt(x0, y0)
        sx1, sy1 = view.pt(x1, y1)
        out += [(sx0, sy0, sx1, sy0), (sx0, sy1, sx1, sy1),
                (sx0, sy0, sx0, sy1), (sx1, sy0, sx1, sy1)]
    return out


def _box_clearance(box, segments) -> float:
    """Clear paper between an axis-aligned *box* and the nearest segment."""
    bx0, by0, bx1, by1 = box
    best = 99.0
    for ax, ay, bx, by in segments:
        # Every segment here is axis-aligned, so the gap is a 1D problem on
        # the axis the segment is perpendicular to, and zero if the segment
        # runs past the box on the other one.
        if abs(ay - by) < 1e-9:                      # horizontal
            if bx1 < min(ax, bx) or bx0 > max(ax, bx):
                continue
            gap = by0 - ay if ay < by0 else (ay - by1 if ay > by1 else -1.0)
        else:                                        # vertical
            if by1 < min(ay, by) or by0 > max(ay, by):
                continue
            gap = bx0 - ax if ax < bx0 else (ax - bx1 if ax > bx1 else -1.0)
        best = min(best, gap)
    return best


def _datum_label_offset(subject: Subject, view: View) -> tuple[float, float]:
    """Which way to throw the datum label so it lands on nothing.

    The datum sits at the subject's own lower-left corner, and a frame edge
    can pass within a few millimetres of it: on
    RPICAM-OVER-ARTY both frames' lower edges run five millimetres below
    it, and the label was printed across them.  Reserve, then draw: the four
    diagonals are tried against the lines that will actually be there, and
    the roomiest wins.
    """
    half_w = style.text_width("X0 Y0", style.T_TINY) / 2 + 1.0
    half_h = style.T_TINY / 2 + 1.0
    segments = _obstacle_segments(subject, view)
    ox, oy = view.pt(0.0, 0.0)
    best = None
    for sx, sy in DATUM_DIRS:
        cx = ox + sx * (DATUM_LABEL_R + half_w)
        cy = oy + sy * DATUM_LABEL_R
        clear = _box_clearance((cx - half_w, cy - half_h,
                                cx + half_w, cy + half_h), segments)
        if best is None or clear > best[0]:
            best = (clear, cx - ox, cy - oy)
        if clear >= 1.5:
            break
    return best[1], best[2]


def _draw_frames(sheet: Sheet, subject: Subject, view: View, bbox) -> None:
    """The frame footprints, their letters and the camera axis in each."""
    c = sheet.canvas
    frames = subject.frames()
    if len(frames) > MAX_FRAMES:
        raise SystemExit(
            f"{subject.key}: {len(frames)} frames, and this sheet has "
            f"{MAX_FRAMES} colours, {MAX_FRAMES} legend entries and "
            f"{MAX_FRAMES} letters. Add a third of each, or split the sheet.")
    x0m, y0m, x1m, y1m = bbox
    bottom = view.y(y0m) - 2.0
    placed: list[tuple[float, float]] = []
    for i, fr in enumerate(frames):
        colour = FRAME_COLOURS[i]
        p0 = view.pt(fr.x0, fr.y0)
        p1 = view.pt(fr.x1, fr.y1)
        c.rect(p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1],
               weight=style.W_PHANTOM, colour=colour, dash=style.D_PHANTOM)
        # The optical axis: a centre mark in the frame's own colour, which is
        # the point of the whole sheet and the thing a stand is set over.
        ax, ay = view.pt(fr.cx, fr.cy)
        c.circle(ax, ay, 1.6, w=style.W_CENTRE, colour=colour, fill="#ffffff")
        dims.centre_mark(c, ax, ay, 1.6, colour=colour, over=2.6)
        # The letter at one of the frame's own corners: the top right, unless
        # a letter already placed is there.  At 1:1 those corners were well
        # apart; at the plan's smaller scale the plate's are three
        # millimetres apart, and two rings that close read as one.
        corners = [(p1[0], p1[1]), (p0[0], p1[1]), (p1[0], p0[1]),
                   (p0[0], p0[1])]
        mx, my = next(
            (q for q in corners
             if all(math.dist(q, m) >= 2 * MARKER_R + 1.5 for m in placed)),
            corners[0])
        placed.append((mx, my))
        c.circle(mx, my, MARKER_R, fill="#ffffff", colour=colour,
                 w=style.W_THIN)
        c.text(mx, my, FRAME_LETTERS[i], size=style.T_LABEL,
               colour=colour, anchor="middle", baseline="middle", bold=True)
        # No dimensions: frame A's axis is dimensioned on the elevations
        # and every frame's is in the table, and at the plan's scale a
        # second set would be a second copy of each figure, smaller.

    # Where two frame edges are too close to draw as two lines, point at them
    # and say so.  One leader, into the clear band between the drawing and
    # the first dimension lane.
    for axis, ia, ib, pos, lo, hi, gap in coincident_edges(frames):
        mid = (lo + hi) / 2
        tip = view.pt(mid, pos) if axis == "Y" else view.pt(pos, mid)
        text = (f"FRAMES {FRAME_LETTERS[ia]} AND {FRAME_LETTERS[ib]}: "
                f"edges {gap:.2f} apart, drawn as one line")
        elbow_x = min(tip[0] + 8.0,
                      sheet.area.x1 - 6.0 - style.text_width(text,
                                                             style.T_LABEL))
        dims.leader(c, tip, (max(elbow_x, tip[0] + 4.0), bottom - 6.0),
                    text, dot=True, colour=style.C_PHANTOM)

    dx, dy = _datum_label_offset(subject, view)
    dims.datum_marker(c, *view.pt(0.0, 0.0), label="X0 Y0",
                      label_dx=dx, label_dy=dy)


def _tables(sheet: Sheet, subject: Subject) -> None:
    """Two tables: one row per frame, and one row per lens.

    The frames and the heights were two tables, keyed to each other by the
    frame letter, and a reader answering "where do I put the camera for the
    LEDs" had to find B in one and then both of B's rows in the other.  One
    row per frame with a height column per lens says the same thing in a
    quarter of the column, which the mounting plate sheet needs: its view is
    the tallest in the set, so its notes band is the shortest, and what the
    band cannot hold comes out of this column.

    No per-row focus verdict.  It was the same word on every row of every
    sheet, and what it means is in the FOCUS note and in the LENSES table's
    own near-limit column, which is where a reader compares lenses anyway.
    """
    frames = subject.frames()
    lenses = list(LENSES.values())

    rows = []
    for i, fr in enumerate(frames):
        row = [FRAME_LETTERS[i], fr.target.label,
               f"{fr.width:.2f} x {fr.height:.2f}", fr.long_axis,
               f"{fr.cx:.2f}", f"{fr.cy:.2f}"]
        row += [f"{place(fr, ln).z:.1f}" for ln in lenses]
        rows.append(row)
    headers = ["", "FRAME", "RECTANGLE mm", "LONG", "AXIS X", "AXIS Y"]
    headers += [f"Z {ln.key}" for ln in lenses]
    aligns = ["middle", "start", "end", "middle", "end", "end"] \
        + ["end"] * len(lenses)
    title = "FRAMES, AND Z ABOVE THE FRAME PLANE, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, headers, rows, aligns)

    rows = [[ln.name, f"{ln.fov_h:.2f}", f"{ln.fov_v:.2f}", ln.focus,
             _fmt_mod(ln)]
            for ln in lenses + [optics.AUTOFOCUS]]
    block = sheet.column_block(sheet.table_height("LENSES", len(rows)))
    sheet.table(block, "LENSES",
                ["LENS", "H deg", "V deg", "FOCUS", "NEAR mm"], rows,
                ["start", "end", "end", "start", "end"])


def _note_columns(sheet: Sheet, subject: Subject, end: View, front: View,
                  plan: View) -> list[Rect]:
    """The paper the notes can have: what the three views leave.

    Not a band across the foot.  The elevations take the top of the drawing
    area and the small plan sits under the end elevation, so the notes run
    first down the paper beside the plan, then across the full width under
    it in two columns, and then -- as on every other sheet -- into the foot
    of the annotation column.
    """
    f = sheet.frame
    base = f.y + 3.0
    x0, x1 = f.x + 4.0, sheet.area.x1 - 2.0
    elev_bottom = min(end.rect.y, front.rect.y) - ELEV_UNDER
    plan_bottom = plan.rect.y - _plan_bottom(subject)
    cols = []
    beside = plan.rect.x1 + 10.0
    if elev_bottom - plan_bottom >= 20.0:
        cols.append(Rect(beside, plan_bottom, x1 - beside,
                         elev_bottom - plan_bottom))
    gutter = 8.0
    w = (x1 - x0 - gutter) / 2
    cols += [Rect(x0 + i * (w + gutter), base, w, plan_bottom - base)
             for i in range(2)]
    return cols


def _place_text(sheet: Sheet, subject: Subject, notes: list[str],
                src: list[str], cols: list[Rect]) -> None:
    """Notes and sources in what the views leave, then the column's foot.

    A sheet whose text will not go anywhere at this scale says so by raising
    :class:`DoesNotFit`, and the caller tries the next scale down.
    """
    blocks = note_blocks(notes, src)
    if not cols:
        raise DoesNotFit("the views leave no paper for the notes")
    if not sheet.notes_columns(cols, blocks, dry=True):
        spare = sheet.column_remaining - 4.0
        h = 20.0
        while True:
            if h > spare:
                raise DoesNotFit(
                    f"{subject.key}: neither the paper beside the views nor "
                    f"the annotation column can hold this sheet's text "
                    f"({spare:.0f} mm of column left)")
            probe = Rect(sheet.column.x, sheet.column.y,
                         sheet.column.w - sheet.COLUMN_GUTTER, h)
            if sheet.notes_columns(cols + [probe], blocks, dry=True):
                break
            h += 2.0
        cols = cols + [sheet.column_block_bottom(h)]
    sheet.notes_columns(cols, blocks)


# ---------------------------------------------------------------------------
# the elevations
# ---------------------------------------------------------------------------

def _along(subject: Subject, axis: str):
    """Frame A, its target, the lens and the subject, along one axis.

    Returns (frame lo, frame hi, target lo, target hi, lens position, the
    declared angle in this plane and which one it is, the subject's size).
    """
    fr = subject.frames()[0]
    t = fr.target
    lens = LENSES[DRAWN]
    p = place(fr, lens)
    o = subject.spec.outline
    if axis == "X":
        angle = p.angle_x
        return (fr.x0, fr.x1, t.x0, t.x1, p.x, angle,
                "H" if fr.long_axis == "X" else "V", o.width)
    angle = p.angle_y
    return (fr.y0, fr.y1, t.y0, t.y1, p.y, angle,
            "V" if fr.long_axis == "X" else "H", o.height)


def _draw_elevation(sheet: Sheet, subject: Subject, v: View,
                    axis: str) -> float:
    """One elevation: the subject edge on, the lens over it, and its rays.

    Returns the sheet position of the lens axis, which the caller
    dimensions from the datum.
    """
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, axis)
    p = place(subject.frames()[0], LENSES[DRAWN])
    z = p.z

    # Under the plane: only what has a published or specified height.
    for what, top, bottom in _below_plane(subject):
        if what == "board":
            x0, y0, x1, y1 = optics.plate_boards_union()
            lo, hi = (x0, x1) if axis == "X" else (y0, y1)
            kw = dict(weight=style.W_PHANTOM, colour=style.C_PHANTOM,
                      dash=style.D_PHANTOM)
        else:
            lo, hi = 0.0, size
            kw = dict(weight=style.W_OUTLINE)
        a, b = v.pt(lo, bottom), v.pt(hi, top)
        c.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], **kw)

    # The plane Z is measured from, a little past everything on it, and the
    # target lying in it.
    # Clipped to the view: a frame over part of a board leaves the rest of
    # the board to run on across the other elevation.
    span_lo = max(min(f_lo, 0.0) - 3.0, v.model_x0)
    span_hi = min(max(f_hi, size) + 3.0, v.model_x1)
    c.line(*v.pt(span_lo, 0.0), *v.pt(span_hi, 0.0), w=style.W_THIN,
           colour=style.C_PHANTOM, dash=style.D_CENTRE)
    c.line(*v.pt(t_lo, 0.0), *v.pt(t_hi, 0.0), w=style.W_OUTLINE + 0.2,
           colour=style.C_HIGHLIGHT)

    # The rays, from the lens to the edges of the frame.
    apex = v.pt(cu, z)
    for edge in (f_lo, f_hi):
        c.line(*apex, *v.pt(edge, 0.0), w=RAY[1], colour=RAY[2])
    # The optical axis.
    c.line(*v.pt(cu, -1.5), *v.pt(cu, z + ABOVE_LENS - 3.0),
           w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)
    long_x = subject.frames()[0].long_axis == "X"
    # ASSUMED, as on the holder: the long image axis along the board's
    # width.  Lens down, the board's width runs against X; a quarter turn
    # puts its height against X and its width against Y.
    if long_x:
        along, sign = ("u", -1) if axis == "X" else ("v", 1)
    else:
        along, sign = ("v", -1) if axis == "X" else ("u", -1)
    _draw_camera(c, v, cu, z, along, sign)

    # The angle, at the lens, and its value outside the cone on the left,
    # where neither elevation has anything else: the heights are dimensioned
    # on the front elevation's right.
    half = math.radians(angle / 2)
    left = (apex[0] - ARC_R * math.sin(half), apex[1] - ARC_R * math.cos(half))
    right = (apex[0] + ARC_R * math.sin(half), apex[1] - ARC_R * math.cos(half))
    c.arc(*left, *right, ARC_R, sweep=1, w=style.W_THIN, colour=style.C_DIM)
    c.text(left[0] - 1.5, left[1] + 1.0, f"{angle:.2f} deg, {which}",
           size=style.T_DIM, colour=style.C_DIM, anchor="end")
    return apex[0]


def _draw_camera(c, v: View, cu: float, z: float, along: str,
                 sign: int) -> None:
    """The Camera Module v1.3, lens face down at Z, from its own data.

    *along* is which of the board's two axes lies across this elevation: its
    25 mm width ("u") or its 23.9 mm height ("v"); *sign* is +1 where that
    axis runs the elevation's way and -1 where turning the board lens down
    reverses it.  Both follow the camera holder's ``camera_to_plate``, so
    the module is drawn the way the holder hangs it.  The lens axis is
    ``v1.OPTICAL_AXIS``, so the board is drawn off centre along its height,
    with the FFC connector on its far face at the edge the axis is nearer.
    """
    from raspberry_pi_camera import v1
    au, av = v1.OPTICAL_AXIS
    a, size, f0, f1 = ((au, v1.BOARD_WIDTH, v1.FFC[0], v1.FFC[2])
                       if along == "u" else
                       (av, v1.BOARD_HEIGHT, v1.FFC[1], v1.FFC[3]))

    def at(w):
        return cu + sign * (w - a)

    lo, hi = sorted((at(0.0), at(size)))
    flo, fhi = sorted((at(f0), at(f1)))
    front = z + v1.LENS_TOP_Z
    back = front + v1.BOARD_THICKNESS
    kw = dict(weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT)

    def box(u0, u1, z0, z1):
        a, b = v.pt(u0, z0), v.pt(u1, z1)
        c.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], fill="#ffffff", **kw)

    box(lo, hi, front, back)
    below = 0.0
    for top, size, _ in v1.LENS_PROFILE:
        box(cu - size / 2, cu + size / 2, front - top, front - below)
        below = top
    box(flo, fhi, back, back - v1.FFC_BOTTOM_Z - v1.BOARD_THICKNESS)


def _dimension_front(sheet: Sheet, subject: Subject, v: View,
                     lens_x: float) -> None:
    """Z, up the right-hand side, and X, under the view.

    Z is dimensioned here and not again on the end elevation: it is one
    height, seen twice.  On the mounting plate the plate face gets a second
    figure, because the plate is what a stand is built on and the plane Z
    is measured from is a board standing on it.
    """
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, "X")
    p = place(subject.frames()[0], LENSES[DRAWN])
    right = v.pt(v.model_x1, 0.0)
    dims.linear(c, right, v.pt(cu, p.z), 8.0, horizontal=False,
                value=p.z, places=1)
    below = _below_plane(subject)
    if subject.key == "tt-mounting-plate":
        plate_top = below[-1][1]
        dims.linear(c, v.pt(size, plate_top), v.pt(cu, p.z),
                    8.0 + style.DIM_STEP + (v.x(v.model_x1) - v.x(size)),
                    horizontal=False, value=p.z - plate_top, places=1)
    # X of the lens, from the datum, under the lowest thing drawn.
    bottom = min([b for _, _, b in below] + [0.0])
    dims.linear(c, v.pt(0.0, bottom), (lens_x, v.y(0.0)),
                -(8.0 + (v.y(0.0) - v.y(bottom))), horizontal=True, value=cu)


def _dimension_end(sheet: Sheet, subject: Subject, v: View,
                   lens_y: float) -> None:
    """Y of the lens, from the datum, under the view."""
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, "Y")
    below = _below_plane(subject)
    bottom = min([b for _, _, b in below] + [0.0])
    dims.linear(c, v.pt(0.0, bottom), (lens_y, v.y(0.0)),
                -(8.0 + (v.y(0.0) - v.y(bottom))), horizontal=True, value=cu)


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------

def plan_scales(scale: float) -> list[float]:
    """The scales the plan may take under elevations at *scale*, best first.

    The plan is the smaller view: it says which way the picture lies over
    the subject and where the second frame is, and the table gives every
    figure in it.  So it is always at a smaller standard scale than the
    elevations, the next one down if the notes still fit and the one after
    that if not -- the elevations keep their scale before the plan does.
    """
    return [num / den for num, den in STANDARD_SCALES
            if num / den < scale - 1e-9][:2]


def _label(scale: float) -> str:
    return scale_text(1, 1 / scale) if scale < 1 else scale_text(scale, 1)


def _layout(subject: Subject, scale: float, sp: float, area: Rect):
    """Where the three views go at *scale*, or None if they do not fit.

    The two elevations side by side across the top, the end elevation on
    the left as first angle puts a view from the right; the plan, at its
    own smaller scale, under the end elevation.  Returns (end, front, plan).
    """
    ex_lo, ex_hi = _elev_extent(subject, "X")
    ey_lo, ey_hi = _elev_extent(subject, "Y")
    w_lo, w_hi = _elev_heights(subject)
    px0, py0, px1, py1 = _plan_bbox(subject)
    s = scale
    end_w = (ey_hi - ey_lo) * s
    front_w = (ex_hi - ex_lo) * s
    elev_h = (w_hi - w_lo) * s
    plan_w, plan_h = (px1 - px0) * sp, (py1 - py0) * sp
    width = LEFT + max(end_w, plan_w) + GAP + front_w + ELEV_OUTER \
        + (style.DIM_STEP if subject.key == "tt-mounting-plate" else 0.0)
    height = (CAPTION + elev_h + ELEV_UNDER + CAPTION + plan_h
              + _plan_bottom(subject))
    if width > area.w or height > area.h:
        return None
    left = area.x + LEFT
    top = area.y1 - CAPTION
    end = View(Rect(left, top - elev_h, end_w, elev_h), ey_lo, w_lo, ey_hi,
               w_hi, s, _label(s), left - ey_lo * s, top - w_hi * s)
    fx = left + max(end_w, plan_w) + GAP
    front = View(Rect(fx, top - elev_h, front_w, elev_h), ex_lo, w_lo,
                 ex_hi, w_hi, s, _label(s), fx - ex_lo * s, top - w_hi * s)
    ptop = top - elev_h - ELEV_UNDER - CAPTION
    plan = View(Rect(left, ptop - plan_h, plan_w, plan_h), px0, py0, px1,
                py1, sp, _label(sp), left - px0 * sp, ptop - py1 * sp)
    return end, front, plan


def _legend(subject: Subject) -> list:
    spec = subject.spec
    legend = [("outline", "Subject outline")]
    if spec.features or spec.slots:
        legend.append(("component", "LED, display or connector"))
    if (any(p.body_x1 > p.body_x0 for p in spec.pmods)
            or any(h.keepout_dia for h in spec.holes)
            or any(w == "board" for w, _, _ in _below_plane(subject))):
        legend.append(("phantom", "Adjacent part or connector body"))
    legend.append((("line", style.W_OUTLINE + 0.2, style.C_HIGHLIGHT, None),
                   f"Frame {FRAME_LETTERS[0]}'s target, on the plane Z is "
                   "measured from"))
    legend.append((RAY, f"The {DRAWN} deg lens's field of view, to frame "
                        f"{FRAME_LETTERS[0]}'s edges"))
    for i in range(len(subject.targets)):
        legend.append((FRAME_LEGEND[i],
                       f"Frame {FRAME_LETTERS[i]}, the rectangle the picture "
                       "must cover"))
    legend.append(("dimension", "Dimension, extension and leader"))
    return legend


def render_camera_position(subject: Subject, *, drawing_no: str, version: str,
                           sheet_size: str = "A3") -> Sheet:
    """The largest standard scale at which the views and the text both fit."""
    why = []
    for num, den in STANDARD_SCALES:
        scale = num / den
        for sp in plan_scales(scale):
            try:
                return _render(subject, scale, sp, drawing_no=drawing_no,
                               version=version, sheet_size=sheet_size)
            except DoesNotFit as e:
                why.append(f"{_label(scale)}, plan {_label(sp)}: {e}")
    raise SystemExit(f"{subject.key}: no scale fits.\n  " + "\n  ".join(why))


def _render(subject: Subject, scale: float, sp: float, *, drawing_no: str,
            version: str, sheet_size: str) -> Sheet:
    frames = subject.frames()
    if len(frames) > MAX_FRAMES:
        raise SystemExit(
            f"{subject.key}: {len(frames)} frames, and this sheet has "
            f"{MAX_FRAMES} colours, {MAX_FRAMES} legend entries and "
            f"{MAX_FRAMES} letters. Add a third of each, or split the sheet.")
    notes, src = _text(subject)
    label = f"{_label(scale)}, PLAN {_label(sp)}"
    # No notes band of the library's kind: the notes go where the views
    # leave paper, which _note_columns works out once the views are placed.
    sheet = Sheet(sheet_size, TitleBlock(
        title=subject.title.upper(), subtitle=subject.subtitle,
        drawing_no=drawing_no, rev="A", version=version,
        drawn_by="generated", scale=label, projection="first angle",
        material=subject.subject_field or subject.spec.title,
        material_label="SUBJECT",
        tolerance=subject.tolerance), notes_band_height=NO_BAND)
    got = _layout(subject, scale, sp, sheet.area)
    if got is None:
        raise DoesNotFit("the views do not fit the drawing area")
    end, front, plan = got
    sheet.draw_frame()
    c = sheet.canvas

    lens_x = _draw_elevation(sheet, subject, front, "X")
    lens_y = _draw_elevation(sheet, subject, end, "Y")
    _dimension_front(sheet, subject, front, lens_x)
    _dimension_end(sheet, subject, end, lens_y)

    _draw_plan(sheet, subject, plan)
    _draw_frames(sheet, subject, plan, _plan_bbox(subject))

    for v, name in ((end, "END ELEVATION"), (front, "FRONT ELEVATION"),
                    (plan, f"PLAN, {plan.scale_label}")):
        c.text(v.rect.cx, v.rect.y1 + 3.0, name, size=style.T_LABEL,
               anchor="middle", bold=True)

    _tables(sheet, subject)
    draw_legend(sheet, _legend(subject))
    _place_text(sheet, subject, notes, src,
                _note_columns(sheet, subject, end, front, plan))
    sheet.draw_title_block()
    return sheet
