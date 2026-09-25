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
and dimensions the height and the lateral position of the lens.

Both lenses are drawn on both elevations, each with its own camera at its
own height and its own rays, told apart by line type -- solid for the stock
65 degree lens, long dashes for the 120 -- and keyed in the legend.  The
autofocus version of the stock camera is not drawn: its angles are the stock
lens's to within a degree and its cone would lie on top of the stock one.
Its height is in the table beside theirs, with whether each height is in
focus.

One sheet per SUBJECT, both lenses on it, rather than one per lens: the
person reading it has one board in front of them, and wants to see the two
heights against each other.  The frame footprints
do not depend on the lens -- a frame is the sensor's own 4:3 round its target,
which is the shape of the file that comes out -- so a subject has exactly as
many rectangles as it has things worth framing, and the lens only decides how
high above them the camera goes.  See :mod:`raspberry_pi_camera.optics`.
"""

from __future__ import annotations

import math

from raspberry_pi_camera import optics
from raspberry_pi_camera.optics import (LENSES, Subject,  # noqa: E501
                                        coincident_edges, place)
from tools.schema import Source

from . import dims, style
from .board_sheet import (draw_feature, draw_holes, draw_legend, draw_pmod,
                          note_blocks, outline_path)
from .plate_sheet import draw_slot
from .sheet import Rect, Sheet, TitleBlock
from .view import STANDARD_SCALES, View, scale_text
from tools.layout import LENS_STEM, drawing_name

#: The lens whose height sets the elevations' extent, and whose camera sits
#: highest: the stock one.
DRAWN = "65"

#: The sheet that carries every lens figure, declared and derived, and
#: where each came from.  These sheets carry the figures they compute with
#: and send the reader there for the rest.
LENS_SHEET = drawing_name("raspberry-pi-camera", LENS_STEM)

#: The rays from each drawn lens to the edge of its picture, by lens key:
#: solid for the stock lens, long dashes for the wide one, both thin and in
#: frame A's colour.  Solid so the stock lens's are not read as the
#: chain-double-dot footprint in the plan, which is the same colour; dashed
#: long enough that the wide lens's are not read as hidden detail.
RAYS = {
    "65": ("line", style.W_THIN, style.C_FRAME_A, None),
    "120": ("line", style.W_THIN, style.C_FRAME_A, "5.0,1.5"),
}

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
GAP = 8.0               # between the two elevations

#: How far above the lens the elevations reach, in model millimetres: room
#: for the camera module drawn over it.
ABOVE_LENS = 12.0

#: Radius of the arc that marks the angle at the lens, in sheet millimetres.
ARC_R = 11.0
#: The wide lens's arc, smaller: its label goes under it, inside its own
#: cone, where the stock lens's rays cannot reach it.
ARC_R_WIDE = 10.0

#: A frame's colour, its legend style and its letter, by its position in the
#: subject's list.  Two of each, because no subject has three things worth
#: framing; a third would have to earn a third colour that still reads when
#: photocopied, so it fails loudly here rather than raising an IndexError
#: halfway down a drawing or, worse, being skipped by the checker.
FRAME_COLOURS = (style.C_FRAME_A, style.C_FRAME_B)
FRAME_LEGEND = ("frame_a", "frame_b")
FRAME_LETTERS = "AB"
MAX_FRAMES = len(FRAME_COLOURS)

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
    data, and nothing publishes how far the Acorn's card stands above its
    Pi, so those sheets draw the plane and the target on it and nothing
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
    """The model range an elevation along *axis* covers, across the page.

    Frame A, the subject where something is drawn under the plane, and
    wherever a lens's picture reaches past the frame: the wide lens's does,
    on the axis its height was not set by, and its rays are drawn to where
    they meet the plane rather than cut off at the frame.
    """
    fr = subject.frames()[0]
    lo, hi = (fr.x0, fr.x1) if axis == "X" else (fr.y0, fr.y1)
    o = subject.spec.outline
    if _below_plane(subject):
        lo, hi = min(lo, 0.0), max(hi, o.width if axis == "X" else o.height)
    for lens in LENSES.values():
        p = place(fr, lens)
        cu, half = (p.x, p.covers_x / 2) if axis == "X" \
            else (p.y, p.covers_y / 2)
        lo, hi = min(lo, cu - half), max(hi, cu + half)
    return lo, hi


def _elev_heights(subject: Subject) -> tuple[float, float]:
    """The model range both elevations cover, up the page."""
    p = place(subject.frames()[0], LENSES[DRAWN])
    below = _below_plane(subject)
    return (min([b for _, _, b in below] + [0.0]) - 1.0, p.z + ABOVE_LENS)


def _deg(a: float) -> str:
    """An angle as its source gives it: 53.50, but 96 rather than 96.00."""
    return f"{a:.0f}" if abs(a - round(a)) < 1e-9 else f"{a:.2f}"


def _fmt_near(lens) -> str:
    return f"{lens.near / 1000:g} m" if lens.near >= 1000 \
        else f"{lens.near:.0f} mm"


def _in_focus(p) -> str:
    """Whether the height is inside the lens's declared focus range."""
    return "no" if p.too_close else "yes"


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
    stock, wide, af = (optics.LENS_65, optics.LENS_120, optics.AUTOFOCUS)
    a = place(frames[0], stock)
    w = place(frames[0], wide)
    notes = [
        "First angle; the end elevation is seen from the right. The camera, "
        "a Camera Module v1.3 from its own data, drawn per lens and "
        "fitted one at a time, looks straight down, in a "
        "mode reading the whole sensor. Z is to its entrance pupil, which "
        "nobody locates; ASSUMED behind the lens face by at most the lens's "
        f"{v1.LENS_TOP_Z:.2f} mm, so set the FACE at Z and the picture is up "
        f"to {100 * v1.LENS_TOP_Z / w.z:.1f}% larger, never smaller.",
        "A frame is the smallest rectangle of the sensor's own 4:3 holding "
        f"its target plus {optics.FRAME_MARGIN:.2f} mm all round, turned "
        "whichever way needs the lower camera; LONG says which. One margin "
        "absorbs both where the stand ends up -- "
        f"{optics.FRAME_MARGIN:.2f} mm of lateral error, or a lean of "
        f"{a.aim_tilt:.1f} deg at frame {FRAME_LETTERS[0]}'s {stock.short} Z "
        f"or {w.aim_tilt:.1f} at its {wide.short}, measured at the picture's "
        "edge -- and what is not known about the lens, below: what one uses "
        "the other cannot.",
    ]

    # Which plane each frame's height is set from.  One note, because a
    # reader who sets the stand from the wrong face gets a picture that is
    # smaller at the thing they are photographing, and nothing on the drawing
    # would tell them.  Grouped by plane, not listed per frame.
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

    for label, box in subject.standing:
        reach = ", ".join(
            f"{place(frames[0], ln).headroom(box):.1f} mm at {ln.short}"
            for ln in LENSES.values())
        notes.append(
            f"HEADROOM: {label[0].lower()}{label[1:]} stays in frame "
            f"{FRAME_LETTERS[0]}'s picture up to {reach} above the plane Z is "
            "set from. Higher, raise the camera.")

    # Focus, before the derivations: the one thing a reader has to be told
    # before building anything.
    s_sensor, s_subject = stock.blur(a.z)
    w_sensor, w_subject = wide.blur(w.z)
    af_z = place(frames[0], af)
    near, far = optics.dof(af_z.z, af.focal_length, af.f_number)
    if af_z.too_close:
        af_there = (f"frame {FRAME_LETTERS[0]}'s {af_z.z:.1f} is nearer, and "
                    "it cannot focus there")
    else:
        af_there = (f"at frame {FRAME_LETTERS[0]}'s its depth of field is "
                    f"{near:.1f} to {far:.1f} (DERIVED, F{af.f_number:g} "
                    "ASSUMED)")
    notes.append(
        f'FOCUS. Both fixed lenses are declared "{stock.near_quote}" (Raspberry'
        f' Pi) and "{wide.near_quote}" (Arducam), and every Z here is nearer:'
        " on either the board is OUT OF FOCUS. At frame "
        f"{FRAME_LETTERS[0]}'s Z a point spreads to "
        f"{s_sensor / optics.PIXEL_PITCH:.0f} px, {s_subject:.1f} mm on the "
        f"board, at {stock.short}, and {w_sensor / optics.PIXEL_PITCH:.0f} px,"
        f" {w_subject:.1f} mm, at {wide.short} (DERIVED, thin lens ASSUMED set"
        f" at {stock.focus_at / 1000:g} m). The autofocus {af.short}, "
        f'Arducam\'s B0176, is declared "{af.near_quote}": every Z of '
        f"{af.near:.0f} or more is in focus once it has focused; {af_there}. "
        "Arducam's catalogue lists no 120 deg OV5647 with a motorised lens.")
    # The wide lens: where its figures come from and what they are good to.
    alts = []
    for alt in wide.alternatives:
        if alt.h > wide.fov_h and alt.v > wide.fov_v:
            continue
        spare = min(_spare(fr, wide, alt) for fr in frames)
        alts.append(f"{alt.what}, {alt.h:.1f} x {alt.v:.1f}, leaving "
                    f"{spare:.1f} mm")
    notes.append(
        f"The {wide.short} deg lens is a fisheye, {wide.fov_d:.0f} deg on the "
        f"diagonal: {wide.fov_h:.0f} x {wide.fov_v:.0f} is Arducam's split "
        "of that diagonal, equidistant, not a measurement. Its barrel "
        "distortion bows the picture's edges "
        "outwards on the board, so the frame's corners are inside it; the "
        "margin absorbs the narrower lenses the evidence allows, "
        + "; ".join(alts) + f". See {LENS_SHEET}.")

    notes.append(
        f'The "{stock.key} deg" name is the stock lens\'s DIAGONAL, which '
        "no vendor prints: 2 x atan(sqrt("
        f"{optics.DATASHEET_IMAGE_AREA[0]:.4f}^2 + "
        f"{optics.DATASHEET_IMAGE_AREA[1]:.4f}^2) / 2 / "
        f"{optics.FOCAL_LENGTH:.2f}) = {optics.DIAGONAL_FROM_DATASHEET:.2f} deg "
        "on OmniVision's image area, "
        f"{optics.DIAGONAL_FROM_ARRAY:.2f} on the pixel array. Every Z here is "
        f"from the angle along each axis. {optics.NOMINAL_DIAGONAL:.0f} deg "
        f"across frame {FRAME_LETTERS[0]}'s long side would give Z "
        f"{a.naive_z:.1f} and lose {a.naive_shortfall:.1f} mm off each end.")

    notes.append(
        "Quotes are transliterated to ASCII: x, um and infinity for the "
        "signs the cached pages print.")

    for letter, fr in zip(FRAME_LETTERS, frames):
        if fr.target.note:
            notes.append(f"Frame {letter}, {fr.target.label}: "
                         f"{fr.target.note}")
    notes += list(subject.notes)

    seen = []
    lens_src = Source(
        label="Lens figures and focus", ref=LENS_SHEET,
        note="Every lens figure on this sheet, declared and derived, with "
             "the vendor pages it is quoted from.")
    for s in list(subject.sources) + [lens_src]:
        entry = f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
        if entry not in seen:
            seen.append(entry)
    return notes, seen


def _spare(frame, lens, alt) -> float:
    """What of the margin is left round *frame*'s target at *lens*'s Z, if
    the lens's angles are really *alt*'s."""
    p = place(frame, lens)
    t = frame.target
    ax = alt.h if frame.long_axis == "X" else alt.v
    ay = alt.v if frame.long_axis == "X" else alt.h
    hx = p.z * math.tan(math.radians(ax / 2))
    hy = p.z * math.tan(math.radians(ay / 2))
    return min(t.x0 - (p.x - hx), (p.x + hx) - t.x1,
               t.y0 - (p.y - hy), (p.y + hy) - t.y1)


def _draw_plan(sheet: Sheet, subject: Subject, view: View) -> None:
    c = sheet.canvas
    spec = subject.spec
    outline_path(c, view, spec)
    draw_holes(c, view, spec.holes)
    for s in spec.slots:
        draw_slot(c, view, s, colour=style.C_HIGHLIGHT)
    for f in spec.features:
        if f.kind == "outline":
            # An informational body, not a part of the subject: the Acorn
            # card lying in its HAT is the only one here.  Drawn in the
            # component red it read as something soldered to the Pi under it.
            x0, y0 = view.pt(f.x0, f.y0)
            x1, y1 = view.pt(f.x1, f.y1)
            c.rect(x0, y0, x1 - x0, y1 - y0, weight=style.W_PHANTOM,
                   colour=style.C_PHANTOM, dash=style.D_PHANTOM)
            # Low in the body, clear of the witness lines that run out to
            # the dimension stacks from the camera axes above it.
            c.text(x0 + 2.0, y0 + 2.0, f.designator or f.label,
                   size=style.T_LABEL, colour=style.C_PHANTOM, bold=True)
            continue
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
    """Three tables: the frames, the heights and focus, and the lenses.

    The frames and where their axes are; then one row per frame giving the
    height for each lens and whether that height is inside the lens's
    declared focus range -- the stock lens fixed and motorised, and the
    wide one, for which nobody sells a motorised version; then the lenses
    themselves, declared figures against the ones used, each value's basis
    flagged.
    """
    frames = subject.frames()
    stock, wide, af = (optics.LENS_65, optics.LENS_120, optics.AUTOFOCUS)

    rows = [[FRAME_LETTERS[i], fr.target.label,
             f"{fr.width:.2f} x {fr.height:.2f}", fr.long_axis,
             f"{fr.cx:.2f}", f"{fr.cy:.2f}"] for i, fr in enumerate(frames)]
    title = "FRAMES, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "FRAME", "RECTANGLE", "LONG", "AXIS X", "AXIS Y"], rows,
                ["middle", "start", "end", "middle", "end", "end"])

    rows = []
    for i, fr in enumerate(frames):
        a, m, w = place(fr, stock), place(fr, af), place(fr, wide)
        rows.append([FRAME_LETTERS[i], f"{a.z:.1f}", _in_focus(a),
                     f"{m.z:.1f}", _in_focus(m), f"{w.z:.1f}", _in_focus(w),
                     "none listed"])
    title = "Z ABOVE THE FRAME PLANE, mm, AND IN FOCUS THERE?"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", f"Z {stock.short}", "FIXED", f"Z {af.short}", "MOTOR",
                 f"Z {wide.short}", "FIXED", "MOTOR"], rows,
                ["middle", "end", "middle", "end", "middle", "end", "middle",
                 "middle"])

    def flag(basis: str) -> str:
        return basis[:4]

    rows = []
    for lens in (stock, af, wide):
        rows.append([
            lens.short,
            lens.product.split(",")[0].replace("Raspberry Pi Camera Module",
                                               "RPi Camera"),
            _deg(lens.fov_h), _deg(lens.fov_v),
            f"{lens.fov_d:.1f} {flag(lens.fov_d_basis)}",
            f"{lens.focal_length:.2f} {flag(lens.focal_basis)}",
            f"F{lens.f_number:g} {flag(lens.f_basis)}",
            f"{lens.focus[:5]}, {_fmt_near(lens)}"])
    title = f"LENSES, deg, AS USED: SEE {LENS_SHEET}"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "MODULE", "H", "V", "DIAG", "f mm", "F", "FOCUS FROM"],
                rows,
                ["start", "start", "end", "end", "end", "end", "end",
                 "start"])


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
    # Where the plan carries a leader to two coincident frame edges, its
    # text runs out to the right under the plan, into the paper beside it:
    # the column beside the plan stops above it.
    beside_bottom = (plan.rect.y - 3.0 if any(coincident_edges(
        subject.frames())) else plan_bottom)
    if elev_bottom - beside_bottom >= 20.0:
        cols.append(Rect(beside, beside_bottom, x1 - beside,
                         elev_bottom - beside_bottom))
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

def _along(subject: Subject, axis: str, lens=None):
    """Frame A, its target, a lens and the subject, along one axis.

    Returns (frame lo, frame hi, target lo, target hi, lens position, the
    lens's declared angle in this plane and which one it is, the subject's
    size).
    """
    fr = subject.frames()[0]
    t = fr.target
    lens = lens or LENSES[DRAWN]
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
                    axis: str) -> dict[str, float]:
    """One elevation: the subject edge on, and each lens and its rays.

    Returns the sheet position of each lens's apex by lens key; the lens
    axis is the same for both, over frame A's centre, and the caller
    dimensions it from the datum.
    """
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, axis)

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
    # target lying in it.  Clipped to the view: a frame over part of a board
    # leaves the rest of the board to run on across the other elevation.
    span_lo = max(min(f_lo, 0.0) - 3.0, v.model_x0)
    span_hi = min(max(f_hi, size) + 3.0, v.model_x1)
    c.line(*v.pt(span_lo, 0.0), *v.pt(span_hi, 0.0), w=style.W_THIN,
           colour=style.C_PHANTOM, dash=style.D_CENTRE)
    c.line(*v.pt(t_lo, 0.0), *v.pt(t_hi, 0.0), w=style.W_OUTLINE + 0.2,
           colour=style.C_HIGHLIGHT)

    long_x = subject.frames()[0].long_axis == "X"
    # ASSUMED, as on the holder: the long image axis along the board's
    # width.  Lens down, the board's width runs against X; a quarter turn
    # puts its height against X and its width against Y.
    if long_x:
        along, sign = ("u", -1) if axis == "X" else ("v", 1)
    else:
        along, sign = ("v", -1) if axis == "X" else ("u", -1)

    apexes = {}
    wide_label = None
    for lens in LENSES.values():
        *_, angle, which, _ = _along(subject, axis, lens)
        z = place(subject.frames()[0], lens).z
        apex = v.pt(cu, z)
        apexes[lens.key] = apex[0]
        # The rays, from the lens to where the picture's edge meets the
        # plane: the frame's edge on the axis that set the height, past it
        # on the other.
        half = math.radians(angle / 2)
        reach = z * math.tan(half)
        shape, wgt, colour, dash = RAYS[lens.key]
        for edge in (cu - reach, cu + reach):
            c.line(*apex, *v.pt(edge, 0.0), w=wgt, colour=colour, dash=dash)
        _draw_camera(c, v, cu, z, along, sign)
        # The angle, at the lens.  The stock lens's value goes outside its
        # cone on the left, where nothing else is; the wide lens sits inside
        # the stock lens's cone, so its value goes under its own arc, inside
        # its own cone, which the stock lens's rays cannot cross.
        r = ARC_R if lens.key == DRAWN else ARC_R_WIDE
        left = (apex[0] - r * math.sin(half), apex[1] - r * math.cos(half))
        right = (apex[0] + r * math.sin(half), apex[1] - r * math.cos(half))
        c.arc(*left, *right, r, sweep=1, w=style.W_THIN, colour=style.C_DIM)
        if lens.key == DRAWN:
            c.text(left[0] - 1.5, left[1] + 1.0,
                   f"{angle:.2f} deg, {which}", size=style.T_DIM,
                   colour=style.C_DIM, anchor="end")
        else:
            wide_label = (apex[0], apex[1] - r - 1.5 - style.T_DIM,
                          f"{angle:.0f} deg, {which}")
            c.text(*wide_label, size=style.T_DIM, colour=style.C_DIM,
                   anchor="middle")

    # The optical axis, one line for both lenses, broken where the wide
    # lens's value sits across it.
    top = v.pt(cu, place(subject.frames()[0], LENSES[DRAWN]).z
               + ABOVE_LENS - 3.0)
    bottom = v.pt(cu, -1.5)
    if wide_label:
        gap_hi = wide_label[1] + style.T_DIM + 0.8
        gap_lo = wide_label[1] - 1.2
        c.line(bottom[0], bottom[1], bottom[0], gap_lo, w=style.W_CENTRE,
               colour=style.C_LINE, dash=style.D_CENTRE)
        c.line(top[0], gap_hi, top[0], top[1], w=style.W_CENTRE,
               colour=style.C_LINE, dash=style.D_CENTRE)
    else:
        c.line(*bottom, *top, w=style.W_CENTRE, colour=style.C_LINE,
               dash=style.D_CENTRE)
    return apexes


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
    """Z for each lens, up the right-hand side, and X, under the view.

    Z is dimensioned here and not again on the end elevation: it is one
    height, seen twice.  The wide lens's, which is lower, is on the inner
    lane.  On the mounting plate the plate face gets a second figure for
    each, outside those, because the plate is what a stand is built on and
    the plane Z is measured from is a board standing on it.
    """
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, "X")
    right = v.pt(v.model_x1, 0.0)
    order = sorted(LENSES.values(),
                   key=lambda ln: place(subject.frames()[0], ln).z)
    below = _below_plane(subject)
    plate = subject.key == "tt-mounting-plate"
    # Lens by lens, lowest first, each lens's figures side by side: an
    # extension line from the higher lens then runs out past the lower
    # lens's lanes, whose values sit at half the lower height, clear of it.
    lane = 8.0
    for lens in order:
        z = place(subject.frames()[0], lens).z
        dims.linear(c, right, v.pt(cu, z), lane, horizontal=False,
                    text=f"Z {lens.short}: {z:.1f}")
        lane += style.DIM_STEP
        if plate:
            plate_top = below[-1][1]
            dims.linear(c, v.pt(size, plate_top), v.pt(cu, z),
                        lane + (v.x(v.model_x1) - v.x(size)),
                        horizontal=False,
                        text=f"{lens.short}, PLATE: {z - plate_top:.1f}")
            lane += style.DIM_STEP
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
    lanes = len(LENSES) * (2 if subject.key == "tt-mounting-plate" else 1)
    width = LEFT + max(end_w, plan_w) + GAP + front_w + ELEV_OUTER \
        + (lanes - 1) * style.DIM_STEP
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
    if any(f.kind != "outline" for f in spec.features) or spec.slots:
        legend.append(("component", "LED, display or connector"))
    if (any(f.kind == "outline" for f in spec.features)
            or any(p.body_x1 > p.body_x0 for p in spec.pmods)
            or any(h.keepout_dia for h in spec.holes)
            or any(w == "board" for w, _, _ in _below_plane(subject))):
        legend.append(("phantom", "Adjacent part or connector body"))
    legend.append((("line", style.W_OUTLINE + 0.2, style.C_HIGHLIGHT, None),
                   f"Frame {FRAME_LETTERS[0]}'s target, on the plane Z is "
                   "measured from"))
    for lens in LENSES.values():
        legend.append((RAYS[lens.key],
                       f"The {lens.short} deg lens's field of view, "
                       f"{_deg(lens.fov_h)} x {_deg(lens.fov_v)}, to its "
                       "picture's edge"))
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

    lens_x = _draw_elevation(sheet, subject, front, "X")[DRAWN]
    lens_y = _draw_elevation(sheet, subject, end, "Y")[DRAWN]
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
