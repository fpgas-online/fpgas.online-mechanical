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
autofocus module used here is not drawn: its angles are taken as the stock
lens's, and its cone would lie on the stock one.  A table gives, per variant
of the camera -- the v1.3 as sold and with its lens unscrewed, one focused
by hand, the motorised one -- the lowest height that both frames and focuses,
or says the module's close limit is not published.

One sheet per SUBJECT, both lenses on it, rather than one per lens: the
person reading it has one board in front of them, and wants to see the two
heights against each other.  The frame footprints
do not depend on the lens -- a frame is the sensor's own 4:3 round its target,
which is the shape of the file that comes out -- so a subject has exactly as
many rectangles as it has things worth framing, and the lens only decides how
high above them the camera goes.  See :mod:`raspberry_pi_camera.optics`.

A subject's sheet may be for ONE module, and give heights to its lens face
instead: a subject that carries ``face`` -- the Acorn's and the plate's --
draws the one lens at the height that both frames and focuses frame A,
dimensions that height above the plane, above what the stand is built on
and above the tallest thing under the camera, gives the same per frame in
its table, and says which terms of those are still to be measured.
Everything those sheets do differently is behind ``subject.face``, so the
other sheets are drawn exactly as before.
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

#: How far the docs' panels of the annotation column reach past the blocks
#: the table and the legend were given, in sheet millimetres: a block's
#: rules are drawn on its edge, and half of each stroke lies outside it.
#: Blocks in the column are four apart.
DOCS_PAD = 1.0

#: Where a leader's text starts past its tail, in sheet millimetres: the
#: gap ``dims.leader`` leaves.
LEADER_TEXT_GAP = 1.2

#: Room left of the end elevation and the plan: the datum labels.
LEFT = 20.0
#: Room under the plan, for the leader that points at two frame edges too
#: close together to draw as two lines, or names a target too small to see,
#: where a sheet has one.
PLAN_BOTTOM = 12.0
PLAN_BOTTOM_BARE = 9.0


def _plan_leader(subject: Subject) -> bool:
    """Whether the plan carries a leader out under it, into the paper beside."""
    return bool(subject.plan_callout
                or any(coincident_edges(subject.frames())))


def _plan_bottom(subject: Subject) -> float:
    return PLAN_BOTTOM if _plan_leader(subject) else PLAN_BOTTOM_BARE

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
#: The least the stock lens's arc may shrink to, to clear a lower camera:
#: room for its value's height and a millimetre over.
ARC_R_MIN = style.T_DIM + 1.5

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


#: How far from the plane a height nobody has measured is drawn, in SHEET
#: millimetres: the mounting plate's face under it and the assembly's highest
#: point over it, on a sheet that gives lens-face heights.  Not to scale, and
#: the legend says so; a measured height is drawn where it is.  Each is room
#: for its one-letter dimension between its arrows.
NTS_BASE = 11.0
NTS_HIGHEST = 11.0

#: The lines those two heights are drawn as: the plate's face as an outline,
#: the highest point thin and dashed, as hidden detail.
STACK_LINES = {
    "base": ("line", style.W_OUTLINE, style.C_LINE, None),
    "highest": ("line", style.W_THIN, style.C_PHANTOM, style.D_HIDDEN),
}


def _z(subject: Subject, lens) -> float:
    """The height *lens* is drawn at over frame A: its Z, or the lens face's
    height on a sheet that gives lens-face heights."""
    fr = subject.frames()[0]
    if subject.face:
        return subject.face.face(fr)
    return place(fr, lens).z


def _stack(subject: Subject, scale: float) -> dict[str, float]:
    """Where the stack's two lines are drawn, in model millimetres above the
    plane: at their measured heights, or not to scale where unmeasured."""
    face = subject.face
    return {
        "base": (-face.base.value if face.base.value is not None
                 else -NTS_BASE / scale),
        "highest": (face.highest.value if face.highest.value is not None
                    else NTS_HIGHEST / scale),
    }


def _base_drawn(subject: Subject) -> bool:
    """Whether what the stand is built on is drawn under the plane already.

    On the plate it is: the plate itself, to scale, with the boards on their
    standoffs over it, and its face is the stack's base.  A line across the
    view at the same height would only run on past the plate's ends.
    """
    base = subject.face.base.value
    return base is not None and any(
        what == "subject" and abs(top + base) < 1e-9
        for what, top, _ in _below_plane(subject))


def _stack_bottom(subject: Subject, scale: float) -> float:
    """The lowest line an elevation draws on a lens-face sheet."""
    return min([_stack(subject, scale)["base"]]
               + [b for _, _, b in _below_plane(subject)])


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
    for lens in subject.lenses():
        p = place(fr, lens)
        cu, half = (p.x, p.covers_x / 2) if axis == "X" \
            else (p.y, p.covers_y / 2)
        if subject.face:
            # Higher than the height that frames: the picture is wider.
            angle = p.angle_x if axis == "X" else p.angle_y
            half = _z(subject, lens) * math.tan(math.radians(angle / 2))
        lo, hi = min(lo, cu - half), max(hi, cu + half)
    return lo, hi


def _elev_heights(subject: Subject, scale: float) -> tuple[float, float]:
    """The model range both elevations cover, up the page."""
    z = _z(subject, LENSES[DRAWN])
    below = [b for _, _, b in _below_plane(subject)]
    if subject.face:
        below.append(_stack(subject, scale)["base"])
    return (min(below + [0.0]) - 1.0, z + ABOVE_LENS)


def _deg(a: float) -> str:
    """An angle as its source gives it: 53.50, but 96 rather than 96.00."""
    return f"{a:.0f}" if abs(a - round(a)) < 1e-9 else f"{a:.2f}"


def _fmt_near(near: float | None) -> str:
    if near is None:
        return "not publ."
    return f"{near / 1000:g} m" if near >= 1000 else f"{near:g} mm"


#: How a close limit's basis is printed in the Z IN FOCUS table.
BASIS = {"DECLARED": "DECL", "REPORTED": "forum user"}


def _text(subject: Subject) -> tuple[list[str], list[str]]:
    """The notes and sources this sheet carries, built before it exists.

    Every figure in here is computed or quoted from
    :mod:`raspberry_pi_camera.optics`.  None is written out by hand: a second
    copy of a derived angle is a copy that goes stale the day the model
    changes, and the whole point of that module is that its numbers are
    checkable.
    """
    from raspberry_pi_camera import v1
    if subject.face:
        return _text_face(subject)
    frames = subject.frames()
    stock, wide = optics.LENS_65, optics.LENS_120
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
    notes.append(
        f'FOCUS. Both fixed lenses as sold are declared "{stock.near_quote}" '
        f'(Raspberry Pi) and "{wide.near_quote}" (Arducam), and every Z here '
        "is nearer: as sold, the subject is OUT OF FOCUS. At frame "
        f"{FRAME_LETTERS[0]}'s Z a point spreads to "
        f"{s_sensor / optics.PIXEL_PITCH:.0f} px, {s_subject:.1f} mm, at "
        f"{stock.short} and {w_sensor / optics.PIXEL_PITCH:.0f} px, "
        f"{w_subject:.1f} mm, at {wide.short} (DERIVED, thin lens ASSUMED "
        f"set at {stock.focus_at / 1000:g} m). Focused closer, Z is the "
        "higher of the close limit and Z + f (DERIVED, thin lens); the "
        "autofocus module used here publishes NO close limit.")
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

    return notes, _sources(subject)


def _sources(subject: Subject) -> list[str]:
    seen = []
    lens_src = Source(
        label="Lens figures and focus", ref=LENS_SHEET,
        note="Every lens figure on this sheet, declared and derived, with "
             "the vendor pages it is quoted from.")
    for s in list(subject.sources) + [lens_src]:
        entry = f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
        if entry not in seen:
            seen.append(entry)
    return seen


def _term(term) -> str:
    """A stack height as the notes and the table give it."""
    if term.value is None:
        return f"{term.symbol}: MEASURE"
    return f"{term.symbol} {term.value:.1f} +/-{term.tol:g}"


def _per_frame(subject: Subject, key: str) -> str:
    """One of a lens-face sheet's heights over every frame, for the notes:
    "frame A 152.4, frame B 113.3", or the formula's right-hand side."""
    return ", ".join(
        f"frame {letter} "
        + _face_text(subject, fr)[key].split(" ", 1)[1].removeprefix("= ")
        for letter, fr in zip(FRAME_LETTERS, subject.frames()))


def _text_face(subject: Subject) -> tuple[list[str], list[str]]:
    """The notes of a sheet that gives lens-face heights for one module.

    Computed or quoted from :mod:`raspberry_pi_camera.optics` and
    ``accessories/parts.py``, like every other sheet's.  With one frame,
    as on the Acorn's, each height is that frame's; with two, as on the
    plate's, the notes give each height for both, and the elevations draw
    frame A's.
    """
    from raspberry_pi_camera import v1
    face = subject.face
    frames = subject.frames()
    one = len(frames) == 1
    fr = frames[0]
    lens = face.variant.lens
    f = face.face(fr)
    framing = optics.framed_in_focus(fr, lens)
    words = _face_text(subject)
    s, t = face.base, face.highest
    on_sensor, _ = lens.blur(f)
    near = face.variant.near
    term = {k: "MEASURE, not published" if h.value is None
            else f"{h.value:.1f} +/-{h.tol:g}, {h.source}" for k, h in
            (("S", s), ("T", t))}
    # The pupil's worst case is at the lowest face: the nearest frame.
    lowest = min(face.face(x) for x in frames)
    forum = (f'"{face.variant.quote}" (a Raspberry Pi forum user, 2013; '
             f"{face.variant.basis}).")
    if one:
        f_note = (
            f"{words['F']} is the higher of two heights: the one that just "
            f"frames frame {FRAME_LETTERS[0]} with the lens focused there, "
            f"{place(fr, lens).z:.1f} + f {lens.focal_length:.2f} = "
            f"{framing:.1f} (DERIVED, thin lens), and the lens's close limit "
            f"unscrewed, {near:g} mm: {forum}")
    else:
        f_note = (
            "F is, per frame, the higher of two heights: the one that just "
            "frames it with the lens focused there, "
            + ", ".join(
                f"frame {letter} {place(x, lens).z:.1f} + f "
                f"{lens.focal_length:.2f} = "
                f"{optics.framed_in_focus(x, lens):.1f}"
                for letter, x in zip(FRAME_LETTERS, frames))
            + f" (DERIVED, thin lens), and the lens's close limit unscrewed, "
            f"{near:g} mm: {forum}")
    if any(optics.framed_in_focus(x, lens) < near for x in frames):
        # Only where the close limit is what sets F does it matter where
        # the forum measured it from.
        f_note += (" The forum does not say whether its \"about 6 cm\" is "
                   "from the lens face; it is taken as from the face, note "
                   "2's convention.")
    else:
        f_note += " The framing governs every frame."
    if one:
        h1 = f"{words['H1']}, where"
        h2 = f"{words['H2']}, the clearance, where"
    else:
        h1 = (f"H1 = {s.symbol} + F, {_per_frame(subject, 'H1')}, where")
        h2 = (f"H2 = F - {t.symbol}, the clearance, "
              f"{_per_frame(subject, 'H2')}, where")
    others = "".join(f", {face.face(x):.1f} for frame {letter}"
                     for letter, x in zip(FRAME_LETTERS[1:], frames[1:]))
    notes = [
        "First angle; the end elevation is seen from the right. One camera: "
        f"a {lens.product}, stock {lens.short} deg lens, looking straight "
        "down, reading the whole sensor.",
        "Heights are to the lens FACE. The entrance pupil the optics are "
        "worked to is ASSUMED behind it by at most the lens's "
        f"{v1.LENS_TOP_Z:.2f} mm, so the picture is up to "
        f"{100 * v1.LENS_TOP_Z / (lowest - lens.focal_length):.1f}% larger, "
        f"never smaller, and {face.target} no nearer than the close limit.",
        f_note,
        f"{h1} {s.symbol} is {s.what}: {term['S']}.",
        f"{h2} {t.symbol} is {t.what}: {term['T']}.",
    ]
    for label, box in subject.standing:
        notes.append(
            f"HEADROOM: {label[0].lower()}{label[1:]} stays in frame "
            f"{FRAME_LETTERS[0]}'s picture, the lens refocused to F, up to "
            f"{face.headroom(fr, box):.1f} mm above {face.plane_short} "
            f"(DERIVED). If {t.symbol} is more, raise the camera.")
    notes += [
        f"REFOCUS THE LENS TO F, {f:.1f} mm from the lens face to "
        f"{face.target}"
        + ("" if one else f" for frame {FRAME_LETTERS[0]}{others}")
        + ". As sold it is set far -- "
        f'"{lens.near_quote}" (Raspberry Pi; infinity is their sign), '
        '"from about 0.5m to infinity" (raspi.tv) -- and at '
        + ("F" if one else f"frame {FRAME_LETTERS[0]}'s F")
        + " a point spreads to "
        f"{on_sensor / optics.PIXEL_PITCH:.0f} px (DERIVED). raspi.tv adds "
        'a +2D lens in front, "focus at about 25cm", too far for F; a '
        'reader\'s comment there: "You CAN change the focus of the stock '
        'lens on the pi camera. It is tricky but can be done." Unscrew it '
        f"until {face.target} are sharp.",
    ]
    if one:
        notes.append(
            f"Frame {FRAME_LETTERS[0]} is the sensor's own 4:3 round "
            f"{fr.target.label} plus {optics.FRAME_MARGIN:.2f} mm all round. "
            f"{fr.target.note} At F the picture is larger; the table gives "
            "the crop.")
    else:
        notes.append(
            "A frame is the sensor's own 4:3 round its target plus "
            f"{optics.FRAME_MARGIN:.2f} mm all round, turned whichever way "
            "needs the lower camera; the table gives which, and where the "
            "lens axis goes over each.")
        for letter, x in zip(FRAME_LETTERS, frames):
            if x.target.note:
                notes.append(f"Frame {letter}, {x.target.label}: "
                             f"{x.target.note}")
    for ob in subject.observations:
        ox, oy = optics.picture(ob.lens, ob.distance)
        factor, per_mm = optics.crop(fr, ob.lens, ob.distance)
        column = max(fr.target.width, fr.target.height)
        notes.append(
            f"OBSERVED, reported by {ob.by}, {ob.on}, of the deployed "
            f"hardware: {ob.text}. DERIVED, the 10 cm approximate, the "
            "module's angles ASSUMED the stock lens's: at "
            f"{ob.distance:.0f} mm the picture covers {oy:.1f} x {ox:.1f} "
            f"mm, frame {FRAME_LETTERS[0]} is a crop of x {factor:.2f}, the "
            f"{column:.2f} mm LED column {column * per_mm:.0f} px.")
    notes += list(subject.notes)
    return notes, _sources(subject)


def _tables_face(sheet: Sheet, subject: Subject) -> Rect:
    """The tables of a sheet that gives lens-face heights for one module.

    The heights first, because they are what the sheet is for, a column per
    frame where there is more than one.  Then, with one frame, the frame
    and what the picture is at each height anyone has given; with more,
    the frames and where the lens axis goes over each, since the
    elevations dimension frame A's alone.  No lens table: the one lens's
    angles are in the legend, and the lens sheet has the rest.

    Returns the heights table's block.
    """
    face = subject.face
    frames = subject.frames()
    fr = frames[0]
    lens = face.variant.lens
    f = face.face(fr)
    per = [_face_text(subject, x) for x in frames]

    def rhs(key: str) -> list[str]:
        return [w[key].split(" ", 1)[1].removeprefix("= ") for w in per]

    rows = [
        ["H1", "the mounting plate's face, the standoffs' base"]
        + rhs("H1") + [_term(face.base)],
        ["H2", f"{face.highest_what}, as clearance"] + rhs("H2")
        + [_term(face.highest)],
        ["F", face.plane] + rhs("F") + ["DERIVED"],
    ]
    title = f"LENS FACE HEIGHTS, mm: {face.heading}"
    heights = sheet.column_block(sheet.table_height(title, len(rows)))
    cols = (["HEIGHT"] if len(frames) == 1
            else [f"FRAME {FRAME_LETTERS[i]}" for i in range(len(frames))])
    sheet.table(heights, title, ["", "THE LENS FACE ABOVE"] + cols + ["TERM"],
                rows, ["middle", "start"] + ["end"] * len(frames) + ["start"])

    if len(frames) > 1:
        rows = [[FRAME_LETTERS[i], x.target.label,
                 f"{x.width:.2f} x {x.height:.2f}", x.long_axis,
                 f"{x.cx:.2f}", f"{x.cy:.2f}"]
                for i, x in enumerate(frames)]
        title = "FRAMES, AND WHERE THE LENS AXIS GOES, mm"
        block = sheet.column_block(sheet.table_height(title, len(rows)))
        sheet.table(block, title,
                    ["", "FRAME", "RECTANGLE", "LONG", "AXIS X", "AXIS Y"],
                    rows, ["middle", "start", "end", "middle", "end", "end"])
        return heights

    column = max(fr.target.width, fr.target.height)

    def view(z: float, ln) -> list[str]:
        long_side, short_side = optics.picture(ln, z)
        x, y = ((long_side, short_side) if fr.long_axis == "X"
                else (short_side, long_side))
        factor, per_mm = optics.crop(fr, ln, z)
        return [f"{x:.1f} x {y:.1f}", f"x {factor:.2f}",
                f"{column * per_mm:.0f} px"]

    # One table for the frame and the pictures it is cropped from: the
    # frame's axis is dimensioned on the elevations, so its row is its
    # rectangle and which way its long side lies.
    letter = FRAME_LETTERS[0]
    rows = [["--", f"frame {letter}, long side along {fr.long_axis}",
             f"{fr.width:.2f} x {fr.height:.2f}", "x 1.00", "--"],
            [f"F {f:.1f}", "the v1.3's picture, refocused"] + view(f, lens)]
    for ob in subject.observations:
        rows.append([f"about {ob.distance:.0f}",
                     f"the {ob.lens.short}-65, as reported; angles ASSUMED"]
                    + view(ob.distance, ob.lens))
    title = f"FRAME {letter} AND THE PICTURE AT THE CARD, mm, DERIVED"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["LENS TO LEDs", "WHAT", "COVERS X x Y", f"CROP TO {letter}",
                 "LED COLUMN"], rows,
                ["start", "start", "end", "end", "end"])
    return heights


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
            # Named in the legend, not on the view.  What a reader looks
            # for on the card is its LEDs, at its far end, which the plan
            # names with a leader; a second name on the view, on a strip
            # the plan draws at a reduced scale, would only be one more
            # thing to tell them from.
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


def _draw_frames(sheet: Sheet, subject: Subject, view: View, bbox) -> float:
    """The frame footprints, their letters and the camera axis in each.

    Returns how far right the plan's leader's text runs, or the plan's own
    right edge where it has none.
    """
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
        # Filled white, so the lines under it do not run through the mark --
        # unless an indicator is under it, which the mark must not hide: the
        # axis over the Acorn's LED column lands on A4.
        r = 1.6 / view.scale
        under = any(f.kind in ("led", "display7")
                    and f.x0 < fr.cx + r and f.x1 > fr.cx - r
                    and f.y0 < fr.cy + r and f.y1 > fr.cy - r
                    for f in subject.spec.features)
        c.circle(ax, ay, 1.6, w=style.W_CENTRE, colour=colour,
                 fill="none" if under else "#ffffff")
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

    reach = view.rect.x1
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
        end_x, _ = dims.leader(c, tip,
                               (max(elbow_x, tip[0] + 4.0), bottom - 6.0),
                               text, dot=True, colour=style.C_PHANTOM)
        reach = max(reach, end_x + LEADER_TEXT_GAP
                    + style.text_width(text, style.T_LABEL))

    # A target too small to tell from what is round it at this scale, named
    # by a leader from its lower edge into the same band, arrowed rather
    # than dotted: a dot the size of the LED it lands on would hide it.  The
    # Acorn's LEDs are the one: a column the plan draws a millimetre wide,
    # lying over the Pi's own Ethernet and USB bodies.
    if subject.plan_callout:
        # Both leaders would share one elbow in the one band
        # _plan_bottom reserves.  No subject has both, so refuse rather
        # than overlap.
        if any(coincident_edges(frames)):
            raise ValueError(
                f"{subject.key}: a plan callout and coincident frame "
                "edges would put two leaders on one elbow")
        t = frames[0].target
        tip = view.pt((t.x0 + t.x1) / 2, t.y0)
        text = subject.plan_callout
        elbow_x = min(tip[0] + 8.0,
                      sheet.area.x1 - 6.0 - style.text_width(text,
                                                             style.T_LABEL))
        end_x, _ = dims.leader(c, tip,
                               (max(elbow_x, tip[0] + 4.0), bottom - 6.0),
                               text, colour=style.C_HIGHLIGHT)
        reach = max(reach, end_x + LEADER_TEXT_GAP
                    + style.text_width(text, style.T_LABEL))

    dx, dy = _datum_label_offset(subject, view)
    dims.datum_marker(c, *view.pt(0.0, 0.0), label="X0 Y0",
                      label_dx=dx, label_dy=dy)
    return reach


def _tables(sheet: Sheet, subject: Subject) -> Rect:
    """Three tables: the frames, the heights in focus, and the lenses.

    The frames, where their axes are and the height each drawn lens frames
    them from; then a row for each module that focuses closer, its close
    limit and the lowest height at which it both frames and focuses each
    frame; then the lenses themselves, declared figures against the ones
    used, each value's basis flagged.

    Returns the first table's block: the heights, which is what the sheet
    is for.
    """
    if subject.face:
        return _tables_face(sheet, subject)
    frames = subject.frames()
    stock, wide, af = (optics.LENS_65, optics.LENS_120, optics.AUTOFOCUS)

    rows = [[FRAME_LETTERS[i], fr.target.label,
             f"{fr.width:.2f} x {fr.height:.2f}", fr.long_axis,
             f"{fr.cx:.2f}", f"{fr.cy:.2f}",
             f"{place(fr, stock).z:.1f}", f"{place(fr, wide).z:.1f}"]
            for i, fr in enumerate(frames)]
    title = "FRAMES, AND Z TO FRAME THEM, mm"
    heights = block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "FRAME", "RECTANGLE", "LONG", "AXIS X", "AXIS Y",
                 f"Z {stock.short}", f"Z {wide.short}"], rows,
                ["middle", "start", "end", "middle", "end", "end", "end",
                 "end"])

    # Each module that focuses closer, at the lowest height that both
    # frames and focuses.  The fixed lenses as sold focus at none of the
    # heights above, and the focus note says so.
    rows = []
    for v in optics.FOCUS_VARIANTS:
        if v.lens.focus_at is not None and v.near == v.lens.near:
            continue    # as sold: out of focus at every height here
        if not v.used:
            continue    # a comparison only, on RPICAM-LENS
        zs = [optics.in_focus_z(fr, v) for fr in frames]
        rows.append([v.variant, v.module.replace(
                         "Raspberry Pi Camera Module", "RPi Camera").replace(
                         ", AliExpress, motorised", ""),
                     "not published" if v.near is None
                     else f"{_fmt_near(v.near)}, {BASIS[v.basis]}"]
                    + ["--" if z is None else f"{z:.1f}" for z in zs])
    title = "Z IN FOCUS, mm: THE LOWEST THAT FRAMES AND FOCUSES"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "MODULE", "CLOSE LIMIT"]
                + [f"Z {FRAME_LETTERS[i]}" for i in range(len(frames))],
                rows, ["start", "start", "start"] + ["end"] * len(frames))

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
            f"{lens.focus[:5]}, {_fmt_near(lens.near)}"])
    title = f"LENSES, deg, AS USED: SEE {LENS_SHEET}"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "MODULE", "H", "V", "DIAG", "f mm", "F", "FOCUS FROM"],
                rows,
                ["start", "start", "end", "end", "end", "end", "end",
                 "start"])
    return heights


def _beside_column(sheet: Sheet, subject: Subject, end: View, front: View,
                   plan: View) -> Rect | None:
    """The paper right of the plan, under the elevations, if there is room
    for notes in it.

    Where the plan carries a leader -- to two coincident frame edges, or
    naming a small target -- its text runs out to the right under the plan,
    into the paper beside it: the column stops above it.
    """
    x0 = plan.rect.x1 + 10.0
    elev_bottom = min(end.rect.y, front.rect.y) - ELEV_UNDER
    beside_bottom = (plan.rect.y - 3.0 if _plan_leader(subject)
                     else plan.rect.y - _plan_bottom(subject))
    if elev_bottom - beside_bottom >= 20.0:
        return Rect(x0, beside_bottom, sheet.area.x1 - 2.0 - x0,
                    elev_bottom - beside_bottom)
    return None


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
    plan_bottom = plan.rect.y - _plan_bottom(subject)
    beside = _beside_column(sheet, subject, end, front, plan)
    cols = [beside] if beside else []
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

    # The stack's two heights, on a sheet that gives lens-face heights: the
    # mounting plate's face under the plane and the assembly's highest point
    # over it, each a line across the view.
    if subject.face:
        for key, h in _stack(subject, v.scale).items():
            if key == "base" and _base_drawn(subject):
                continue    # the plate's own face, drawn above
            _, wgt, colour, dash = STACK_LINES[key]
            c.line(*v.pt(span_lo, h), *v.pt(span_hi, h), w=wgt,
                   colour=colour, dash=dash)

    apexes = {}
    wide_label = None
    for lens in subject.lenses():
        *_, angle, which, _ = _along(subject, axis, lens)
        z = _z(subject, lens)
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
        if lens.key == DRAWN:
            r = _arc_clear_of_cameras(subject, v, cu, z, apex, r)
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
    top = v.pt(cu, _z(subject, LENSES[DRAWN]) + ABOVE_LENS - 3.0)
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
    if subject.face:
        _dimension_face(c, subject, v, lens_x, cu)
        return
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
    _lateral(c, v, lens_x, bottom, cu, "X")


def _face_text(subject: Subject, fr=None) -> dict[str, str]:
    """What each of a lens-face sheet's heights is printed as, over *fr*.

    F is a figure.  H1 and H2 are figures once their term is measured, and
    until then the formula, so the drawing never shows a height that
    nobody has.  The dimensions and the table both print these.  *fr* is
    frame A unless given: the elevations draw frame A's.
    """
    face = subject.face
    fr = fr or subject.frames()[0]
    f = face.face(fr)
    s, t = face.base, face.highest
    h1, h2 = face.above_base(fr), face.clearance(fr)
    return {
        "F": f"F {f:.1f}",
        "S": s.symbol if s.value is None else f"{s.symbol} {s.value:.1f}",
        "T": t.symbol if t.value is None else f"{t.symbol} {t.value:.1f}",
        "H1": (f"H1 = {s.symbol} + {f:.1f}" if h1 is None
               else f"H1 {h1:.1f}"),
        "H2": (f"H2 = {f:.1f} - {t.symbol}" if h2 is None
               else f"H2 {h2:.1f}"),
    }


def _dimension_face(c, subject: Subject, v: View, lens_x: float,
                    cu: float) -> None:
    """The lens face's three heights, chained up the right-hand side.

    Nearest the view, S and then F: the plate's face to the card, the card
    to the lens face.  Outside them T and then H2: the card to the highest
    point, the highest point to the lens face.  Outside those H1, the plate's
    face to the lens face, which is the first two added.  X of the lens
    under the view, as on every position sheet.
    """
    stack = _stack(subject, v.scale)
    f = _z(subject, LENSES[DRAWN])
    words = _face_text(subject)
    rx = v.x(v.model_x1)
    plane, face = (rx, v.y(0.0)), v.pt(cu, f)
    base, highest = (rx, v.y(stack["base"])), (rx, v.y(stack["highest"]))
    lane = 8.0
    # S below its span where it is too short for its value, as the plate's
    # 9.6 is at 1:2: under the base nothing else stands in this lane.
    dims.linear(c, base, plane, lane, horizontal=False, text=words["S"],
                extension=False, text_side="low")
    dims.linear(c, plane, face, lane, horizontal=False, text=words["F"])
    lane += style.DIM_STEP
    dims.linear(c, plane, highest, lane, horizontal=False, text=words["T"],
                extension=False)
    dims.linear(c, highest, (rx, face[1]), lane, horizontal=False,
                text=words["H2"], extension=False)
    # The highest point's own extension line, which neither chain above
    # draws: out to its lane and no further.
    c.line(rx + style.EXT_GAP, highest[1], rx + lane + style.EXT_OVER,
           highest[1], w=style.W_THIN, colour=style.C_DIM)
    lane += style.DIM_STEP
    dims.linear(c, base, face, lane, horizontal=False, text=words["H1"])
    _lateral(c, v, lens_x, _stack_bottom(subject, v.scale), cu, "X",
             face=True)


def _dimension_end(sheet: Sheet, subject: Subject, v: View,
                   lens_y: float) -> None:
    """Y of the lens, from the datum, under the view."""
    c = sheet.canvas
    f_lo, f_hi, t_lo, t_hi, cu, angle, which, size = _along(subject, "Y")
    below = _below_plane(subject)
    bottom = min([b for _, _, b in below] + [0.0])
    if subject.face:
        bottom = _stack_bottom(subject, v.scale)
    _lateral(c, v, lens_y, bottom, cu, "Y", face=bool(subject.face))


def _lateral(c, v: View, lens_u: float, bottom: float, cu: float,
             axis: str, face: bool = False) -> None:
    """Where the lens is across an elevation, under the lowest thing drawn.

    A dimension from the datum, where the datum is in the view.  Where it
    is not -- a frame on the far side of the subject from its datum, as the
    Acorn's LEDs are, at the far end of the Pi from it -- a dimension line
    back to it would run out of the view and across the next one.  So the
    lens's coordinate is given instead, ordinate fashion: the axis's own
    extension line carried down, and the coordinate at its end.  The plan
    shows the datum it is measured from.

    *face* is a sheet that gives lens-face heights, whose lowest line is
    well under the plane: its dimension goes the usual 8 mm under that line
    and not as far again as the line is under the plane.
    """
    if v.model_x0 <= 0.0 <= v.model_x1:
        dims.linear(c, v.pt(0.0, bottom), (lens_u, v.y(0.0)),
                    -8.0 if face else -(8.0 + (v.y(0.0) - v.y(bottom))),
                    horizontal=True, value=cu)
        return
    top = v.y(bottom) - style.EXT_GAP
    end = v.y(bottom) - 8.0 - style.EXT_OVER
    c.line(lens_u, top, lens_u, end, w=style.W_THIN, colour=style.C_DIM)
    c.text(lens_u, end - 1.0 - style.T_DIM, f"{axis} {cu:.2f}",
           size=style.T_DIM, colour=style.C_DIM, anchor="middle")


def _arc_clear_of_cameras(subject: Subject, v: View, cu: float, z: float,
                          apex, r: float) -> float:
    """The stock lens's arc radius, shrunk to clear a lower camera's body.

    Its value is written at the arc's left end, and on a sheet where the
    wide lens's camera stands close under the stock lens's, as it does on
    the Acorn's, the wide lens's camera, drawn after it and filled white,
    would cover both.  So the arc comes up into the gap between that
    camera's top and this lens, a millimetre clear of the top, if the gap
    is room enough for it; otherwise it is left as it was.
    """
    from raspberry_pi_camera import v1
    height = (v1.LENS_TOP_Z + v1.BOARD_THICKNESS
              + max(0.0, -v1.FFC_BOTTOM_Z - v1.BOARD_THICKNESS))
    fr = subject.frames()[0]
    tops = [v.y(place(fr, ln).z + height) for ln in subject.lenses()
            if place(fr, ln).z < z]
    if not tops:
        return r
    room = apex[1] - max(tops) - 1.0
    if room >= r or room < ARC_R_MIN:
        return r
    return room


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
    w_lo, w_hi = _elev_heights(subject, scale)
    px0, py0, px1, py1 = _plan_bbox(subject)
    s = scale
    end_w = (ey_hi - ey_lo) * s
    front_w = (ex_hi - ex_lo) * s
    elev_h = (w_hi - w_lo) * s
    plan_w, plan_h = (px1 - px0) * sp, (py1 - py0) * sp
    lanes = len(LENSES) * (2 if subject.key == "tt-mounting-plate" else 1)
    if subject.face:
        lanes = 3       # S and F, T and H2, H1
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
        bodies = [f.designator or f.label for f in spec.features
                  if f.kind == "outline"]
        legend.append(("phantom", "Adjacent part or connector body"
                       + "".join(f", and the {b}" for b in bodies)))
    legend.append((("line", style.W_OUTLINE + 0.2, style.C_HIGHLIGHT, None),
                   f"Frame {FRAME_LETTERS[0]}'s target, on the plane "
                   + ("F is measured from" if subject.face
                      else "Z is measured from")))
    for lens in subject.lenses():
        legend.append((RAYS[lens.key],
                       f"The {lens.short} deg lens's field of view, "
                       f"{_deg(lens.fov_h)} x {_deg(lens.fov_v)}, to its "
                       "picture's edge"))
    for i in range(len(subject.targets)):
        legend.append((FRAME_LEGEND[i],
                       f"Frame {FRAME_LETTERS[i]}, the rectangle the picture "
                       "must cover"))
    if subject.face:
        face = subject.face
        for key, term, what in (
                ("base", face.base,
                 "The mounting plate's face, {} below " + face.plane_short),
                ("highest", face.highest,
                 face.highest_what[0].upper() + face.highest_what[1:]
                 + ", {} above " + face.plane_short)):
            legend.append((STACK_LINES[key], what.format(term.symbol)
                           + ("" if term.value is not None
                              else ": NOT TO SCALE, to measure")))
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
    plan_reach = _draw_frames(sheet, subject, plan, _plan_bbox(subject))

    for v, name in ((end, "END ELEVATION"), (front, "FRONT ELEVATION"),
                    (plan, f"PLAN, {plan.scale_label}")):
        c.text(v.rect.cx, v.rect.y1 + 3.0, name, size=style.T_LABEL,
               anchor="middle", bold=True)

    heights = _tables(sheet, subject)
    legend = draw_legend(sheet, _legend(subject))
    _place_text(sheet, subject, notes, src,
                _note_columns(sheet, subject, end, front, plan))
    sheet.draw_title_block()

    # What the docs show: how the camera sits over the subject and how high,
    # with the figures and the key that make the views readable on their
    # own.  From the layout just drawn, so it moves when the views do; see
    # tools/docs_images.py, which also refuses a panel edge that cuts
    # through anything drawn.
    # The elevations from the frame down to where the paper beside the plan
    # begins, the plan under them, and the notes in the paper beside the
    # plan, each its own panel so that none is wider than it need be: the
    # picture is as wide as its widest panel, and that sets how large its
    # text prints.  The plan's panel reaches right under the notes, as far
    # as its leader's text runs, and the notes' panel is listed after it, so
    # that what lies wholly in the notes' paper is theirs.  The frame itself
    # is furniture and left out.
    f = sheet.frame
    elev_bottom = min(end.rect.y, front.rect.y) - ELEV_UNDER
    views_bottom = plan.rect.y - _plan_bottom(subject)
    beside = _beside_column(sheet, subject, end, front, plan)
    elev_right = front.rect.x1 + ELEV_OUTER + DOCS_PAD
    sheet.docs_panels = [
        (Rect(f.x, elev_bottom, elev_right - f.x, f.y1 - elev_bottom),
         "the two elevations with their height and lateral dimensions"),
        (Rect(f.x, views_bottom, plan_reach + DOCS_PAD - f.x,
              elev_bottom - views_bottom),
         "the plan with its callout"),
    ]
    if beside:
        sheet.docs_panels.append(
            (beside.inset(-DOCS_PAD), "notes 1 and 2, in the paper beside "
             "the plan"))
    sheet.docs_panels += [
        (heights.inset(-DOCS_PAD),
         "the heights table, the sheet's headline figures"),
        (legend.inset(-DOCS_PAD),
         "the legend, which says what each line in the views is"),
    ]
    return sheet
