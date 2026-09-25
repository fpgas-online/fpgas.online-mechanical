"""OV5647 camera optics, and where a camera has to sit to frame a board.

Hand-written, unlike :mod:`raspberry_pi_camera.boards`, which is generated
from Raspberry Pi Ltd's mechanical drawings.  Nothing here comes off a
drawing: not one of the Raspberry Pi camera mechanical drawings carries a
field of view, a focal length or a focus range.  Those are curated from the
vendors' own prose, one value at a time, with the sentence each came from
recorded beside it -- which is what ``accessories/parts.py`` does for the
parts nobody publishes a drawing of, and for the same reason.

``tools/fetch_raspberry_pi_camera.sh`` caches every page quoted below into
``tmp/src/rpi-camera-optics/``, and ``raspberry_pi_camera/verify.py`` reads
those files back and fails if a quote here is not in them.

The model
---------
A rectilinear (pinhole) camera looking straight down at the subject plane.
At a height *Z* above that plane a lens of full field angle *A* covers
``2 * Z * tan(A / 2)``.  That model is not assumed: Raspberry Pi publish a
focal length and a sensor size as well as a field of view for the OV5647, and
the three agree to a hundredth of a degree on both axes only under this
model, measured to the edge of the active pixel array.  See
:data:`FOV_CHECK`.

Coordinates
-----------
Every subject uses its own sheet frame, per :mod:`tools.schema`: origin at
the lower-left corner of the part, X right, Y up, viewed from the component
side, millimetres.  A camera position is X and Y in that frame plus a height
Z above the subject plane, which is the top face of the board.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from tools.layout import PLATE_SHEET, drawing_name, slug
from tools.schema import BoardSpec, Feature, Source

# ---------------------------------------------------------------------------
# The sensor
# ---------------------------------------------------------------------------

#: Active pixel array.  Raspberry Pi: "2592 x 1944 pixels" on a pitch of
#: "1.4 um x 1.4 um".
SENSOR_COLUMNS = 2592
SENSOR_ROWS = 1944
PIXEL_PITCH = 0.0014            # mm

#: Raspberry Pi's own "Sensor image area", which is NOT the active array: it
#: is 0.13 mm wider and 0.02 mm taller, so the two give different angles.  Kept
#: because it is what the vendor prints, and because the diagonal of THIS
#: rectangle, not of the active array, is where the marketing figure "65
#: degrees" comes from.  See FOV_CHECK.
IMAGE_AREA = (3.76, 2.74)       # mm

#: Raspberry Pi: "3.60 mm +/- 0.01".
FOCAL_LENGTH = 3.60
FOCAL_LENGTH_TOL = 0.01

#: Raspberry Pi: "F2.9".
FOCAL_RATIO = "F2.9"
F_NUMBER = 2.9

#: Width and height of the active array, and its aspect ratio.  DERIVED:
#: 2592 x 0.0014 = 3.6288 and 1944 x 0.0014 = 2.7216, so 4:3 exactly.
ARRAY_WIDTH = SENSOR_COLUMNS * PIXEL_PITCH
ARRAY_HEIGHT = SENSOR_ROWS * PIXEL_PITCH
ASPECT = SENSOR_COLUMNS / SENSOR_ROWS


def full_angle(size: float, focal: float = FOCAL_LENGTH) -> float:
    """Full field angle, in degrees, subtended by *size* at *focal*."""
    return 2 * math.degrees(math.atan(size / 2 / focal))


#: What justifies the pinhole model, computed rather than asserted.  Each
#: entry is (what, derived degrees, what the vendor declares, or None).
#:
#: The active array reproduces Raspberry Pi's declared 53.50 and 41.41 to
#: better than 0.01 degrees.  Their own "image area" does not: it gives 55.15
#: horizontally, 1.65 degrees out.  So the declared field of view is measured
#: to the edge of the ACTIVE ARRAY, under a rectilinear model, and that is the
#: model these sheets use.  The same arithmetic on the image area is where
#: "65 degrees" comes from: 65.74 diagonal, against the array's 64.42.
FOV_CHECK = (
    ("Horizontal, from the active array", full_angle(ARRAY_WIDTH), 53.50),
    ("Vertical, from the active array", full_angle(ARRAY_HEIGHT), 41.41),
    ("Diagonal, from the active array",
     full_angle(math.hypot(ARRAY_WIDTH, ARRAY_HEIGHT)), None),
    ("Horizontal, from the image area", full_angle(IMAGE_AREA[0]), 53.50),
    ("Vertical, from the image area", full_angle(IMAGE_AREA[1]), 41.41),
    ("Diagonal, from the image area",
     full_angle(math.hypot(*IMAGE_AREA)), None),
)

#: How far the declared figures and the model may differ before the model is
#: the wrong one.  A hundredth of a degree is the precision the declared
#: figures are printed to.
FOV_CHECK_TOL = 0.01

#: The stock lens's diagonal field of view, which is the figure it is sold
#: under and which no vendor prints.  Two of them, because the two rectangles
#: Raspberry Pi publish do not agree: the image area gives the 65 the module
#: is named for, the active array -- the one that reproduces the declared H
#: and V -- gives a degree and a third less.
DIAGONAL_FROM_IMAGE_AREA = full_angle(math.hypot(*IMAGE_AREA))
DIAGONAL_FROM_ARRAY = full_angle(math.hypot(ARRAY_WIDTH, ARRAY_HEIGHT))

#: How far a declared vertical may sit from what the declared horizontal
#: implies on a 4:3 sensor before the pair is called inconsistent.  A tenth of
#: a degree: the stock lens comes in at 0.006 and the wide one at 14.82, so
#: nothing here is near the line.
CONSISTENCY_TOL = 0.1

RPI_DOC = Source(
    label="Raspberry Pi camera documentation",
    ref="https://web.archive.org/web/20241230011811/"
        "https://www.raspberrypi.com/documentation/accessories/camera.html",
    note='Camera Module 1 column: OV5647, 2592 x 1944 at 1.4 um, image '
         'area 3.76 x 2.74, 3.60 mm, 53.50 x 41.41 deg, "Approx 1 m to '
         'infinity"; the close limits of the other modules.',
)

ARDUCAM_DOC = Source(
    label="Arducam 5MP OV5647 documentation",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/"
        "5MP-OV5647/",
    note='Product catalogue: B0033 "Stock Lens 54 (H) x 41 (V) Fixed '
         'Focus", B006604 "120 (H) x 90 (V)", B0176 "54(H)x44 (V) Auto '
         'Focus".',
)

ARDUCAM_AF = Source(
    label="Arducam motorized focus camera",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Motorized-Focus-Camera/"
        "Motorized-Focus-Camera/",
    note='Quoted: "you can understand it the same as autofocus".',
)

# ---------------------------------------------------------------------------
# The two lenses the issue asks for
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Lens:
    """One lens variant of an OV5647 camera module.

    ``fov_h`` and ``fov_v`` are the full field angles the vendor declares, in
    degrees, for the long and the short axis of the image.  Neither vendor
    says how they are measured; :data:`FOV_CHECK` establishes that Raspberry
    Pi's pair is the rectilinear angle to the edge of the active array, and
    Arducam's is taken the same way for want of anything better.

    ``min_object_distance`` is the nearest the vendor says the module will
    focus, in millimetres, or None where none is published.  It is not a
    detail: the stock lens is fixed at "Approx 1 m to infinity", and every
    height on these sheets is a fraction of that.
    """

    key: str
    name: str
    subtitle: str
    fov_h: float
    fov_v: float
    focus: str
    min_object_distance: float | None
    mod_note: str
    sources: tuple[Source, ...]

    @property
    def consistent_v(self) -> float:
        """The vertical angle this lens's declared horizontal implies.

        DERIVED: on a 4:3 sensor a rectilinear lens has
        ``tan(V/2) = tan(H/2) * 3/4``.  A declared pair that disagrees with
        this is a pair that cannot both be right, and both of these sheets'
        lenses are checked against it.
        """
        return 2 * math.degrees(
            math.atan(math.tan(math.radians(self.fov_h / 2)) / ASPECT))

    @property
    def consistent(self) -> bool:
        """Whether the declared pair agrees with the sensor's own shape."""
        return abs(self.consistent_v - self.fov_v) <= CONSISTENCY_TOL


LENS_65 = Lens(
    key="65",
    name="65 deg (stock lens)",
    subtitle="Camera Module OV5647, stock fixed-focus lens",
    fov_h=53.50,
    fov_v=41.41,
    focus="Fixed",
    min_object_distance=1000.0,
    mod_note='Raspberry Pi give the depth of field as "Approx 1 m to '
             'infinity", so 1000 mm is the nearest this lens focuses.',
    sources=(RPI_DOC, ARDUCAM_DOC),
)

LENS_120 = Lens(
    key="120",
    name="120 deg (wide lens)",
    subtitle="Camera Module OV5647, wide fixed-focus lens",
    fov_h=120.0,
    fov_v=90.0,
    focus="Fixed",
    min_object_distance=None,
    mod_note="Arducam publish no focus distance for this lens, so no height "
             "on this sheet can be checked against one.",
    sources=(ARDUCAM_DOC,),
)

LENSES = {LENS_65.key: LENS_65, LENS_120.key: LENS_120}

#: The autofocus variant, which is a statement rather than a lens to compute
#: with: Arducam declare a field of view for it and nothing else, so no
#: height on these sheets is worked out from it.
AUTOFOCUS = Lens(
    key="af",
    name="Autofocus",
    subtitle="Arducam B0176, OV5647 with a motorised lens",
    fov_h=54.0,
    fov_v=44.0,
    focus="Auto",
    min_object_distance=None,
    mod_note="Arducam publish no near limit and no lens height for it.",
    sources=(ARDUCAM_DOC, ARDUCAM_AF),
)

#: The figure the stock lens is sold under, which is its DIAGONAL and which no
#: vendor prints: see DIAGONAL_FROM_IMAGE_AREA.  Kept as a number only so the
#: sheets can show what goes wrong if it is used as if it were the angle
#: across the picture, which is the mistake the name invites.
NOMINAL_DIAGONAL = 65.0

#: ASSUMED: where the stock fixed-focus lens is focused.  Raspberry Pi give
#: its depth of field as "Approx 1 m to infinity".  A depth of field whose far
#: end is infinity is what a lens focused at its hyperfocal distance H gives,
#: and its near end is then H / 2; so H is taken as twice the published near
#: limit.  Nobody publishes the figure itself.  It is used for one thing, an
#: estimate of how soft a board at the heights on these sheets comes out, and
#: that estimate is labelled as resting on it.
FIXED_FOCUS_DISTANCE = 2 * LENS_65.min_object_distance


def blur(z: float, focus: float = FIXED_FOCUS_DISTANCE) -> tuple[float, float]:
    """How big a point on a subject Z away comes out, on a lens focused at *focus*.

    DERIVED, thin lens: the subject images at ``v = f z / (z - f)`` behind
    the lens and the sensor sits where *focus* images, so a point spreads to
    a disc of the aperture ``f / N`` scaled by how far short of its own image
    the sensor is.  Returned as (diameter on the sensor, the same disc
    projected back onto the subject), both in millimetres.
    """
    f = FOCAL_LENGTH
    v_subject = f * z / (z - f)
    v_sensor = f * focus / (focus - f)
    on_sensor = (f / F_NUMBER) * abs(v_subject - v_sensor) / v_subject
    return on_sensor, on_sensor * z / v_subject


#: The near limits Raspberry Pi publish for their own focusable modules.
#: Different sensors -- IMX219 and IMX708, not OV5647 -- so they cannot be
#: read as an OV5647 figure. They are here because they are the only published
#: close limits for any Raspberry Pi camera, and because they say what order
#: of distance a focusable module reaches: a tenth of the stock lens's metre.
RPI_NEAR_LIMITS = (
    ("Camera Module 2, IMX219, adjustable", "Approx 10 cm to infinity"),
    ("Camera Module 3, IMX708, motorized", "Approx 10 cm to infinity"),
    ("Camera Module 3 Wide, IMX708, motorized", "Approx 5 cm to infinity"),
)


def near_limits() -> list[tuple[str, float]]:
    """Each distinct published close limit, and its near end in millimetres.

    Read out of the quote rather than typed beside it, so the figure a
    height is compared against is the one the vendor's words give.
    """
    import re
    out = []
    for quote in dict.fromkeys(q for _, q in RPI_NEAR_LIMITS):
        cm = re.fullmatch(r"Approx (\d+) cm to infinity", quote)
        if not cm:
            raise SystemExit(f"cannot read a near limit out of {quote!r}")
        out.append((quote, float(cm.group(1)) * 10))
    return out

# ---------------------------------------------------------------------------
# Framing
# ---------------------------------------------------------------------------

#: Clear paper the frame keeps round the thing it is framing, on every side.
#:
#: Five millimetres, flat, and not a percentage.  A camera on a stand over a
#: board is aimed by hand: what has to be absorbed is where the stand actually
#: ends up, which is a few millimetres whatever is being framed, and not a
#: proportion of it.  A ten per cent margin round the Arty's LED block would
#: be 0.36 mm on the short axis, which is less than the board data's own
#: tolerance.
FRAME_MARGIN = 5.0


@dataclass(frozen=True)
class Target:
    """A rectangle on the subject that has to end up inside the picture.

    The rectangle is in the subject's own plan frame, but it need not lie in
    the subject's own top face, and on the mounting plate's sheet it does
    not: the demo boards' indicators are on a board standing on standoffs
    above the plate.  A camera height measured to the wrong plane covers
    less at the right one -- the picture at ``h`` above the frame plane is
    ``(Z - h) / Z`` of what is drawn -- so ``Z`` on these sheets is always
    quoted above the TARGET's plane, and ``plane_name`` says which plane that
    is.

    ``plane_above_subject`` is how far that plane sits above the subject's own
    top face, where anyone publishes it, and None where nobody does.  It is
    never used to compute Z; it is there so the sheet can say what has to be
    added to get from the subject's face to the plane the stand is set from,
    or say that the figure does not exist.
    """

    key: str
    label: str
    x0: float
    y0: float
    x1: float
    y1: float
    note: str = ""
    plane_name: str = "the subject's own top face"
    plane_above_subject: float | None = 0.0
    plane_note: str = ""

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class Frame:
    """The footprint the picture covers on the subject plane.

    Always the sensor's own 4:3, because that is the shape of the file that
    comes out; the only choice is which way round the camera is turned, and
    ``long_axis`` records it.  ``x0..y1`` is in the subject's frame.
    """

    target: Target
    long_axis: str              # "X" or "Y"
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


def frame_for(target: Target, margin: float = FRAME_MARGIN) -> Frame:
    """The smallest 4:3 frame, either way up, holding *target* plus *margin*.

    Either way up matters.  A target taller than it is wide, framed
    landscape, puts the camera higher than the same target turned through
    ninety degrees.
    """
    x0, y0 = target.x0 - margin, target.y0 - margin
    x1, y1 = target.x1 + margin, target.y1 + margin
    need_w, need_h = x1 - x0, y1 - y0
    best = None
    for long_axis, ratio in (("X", ASPECT), ("Y", 1 / ASPECT)):
        w = max(need_w, need_h * ratio)
        h = max(need_h, w / ratio)
        if best is None or w * h < best[0]:
            best = (w * h, long_axis, w, h)
    _, long_axis, w, h = best
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return Frame(target, long_axis, cx - w / 2, cy - h / 2,
                 cx + w / 2, cy + h / 2)


#: Two frame edges closer together than this cannot be drawn as two lines:
#: at A3 two 0.25 mm chain-double-dot lines that close read as one.  Where it
#: happens the sheet points at them and says so, rather than leaving a reader
#: to wonder which rectangle they are looking at.  On
#: RPICAM-OVER-ARTY the two lower edges are 0.43 mm apart.
COINCIDENT = 1.5


def _frame_edges(frames) -> list[tuple[str, int, float, float, float]]:
    """Every frame edge, as (axis, frame index, position, span lo, span hi).

    ``axis`` is the axis the edge is PERPENDICULAR to, so two edges with the
    same axis and a close position are two lines lying nearly on top of each
    other.
    """
    out = []
    for i, f in enumerate(frames):
        out.append(("Y", i, f.y0, f.x0, f.x1))
        out.append(("Y", i, f.y1, f.x0, f.x1))
        out.append(("X", i, f.x0, f.y0, f.y1))
        out.append(("X", i, f.x1, f.y0, f.y1))
    return out


def coincident_edges(frames, tol: float = COINCIDENT):
    """Pairs of frame edges too close together to be drawn as two lines.

    Two frames on one sheet are not nested and need not be: on
    RPICAM-OVER-ARTY frame B's lower edge is 0.43 mm below frame A's.
    Where two edges land within a chain line's own width of each other,
    the drawing cannot show two, so the sheet says which they are instead of
    leaving the reader to guess.

    Yields ``(axis, i, j, position, overlap lo, overlap hi, gap)``.
    """
    edges = _frame_edges(frames)
    for a in range(len(edges)):
        axis_a, ia, pa, lo_a, hi_a = edges[a]
        for b in range(a + 1, len(edges)):
            axis_b, ib, pb, lo_b, hi_b = edges[b]
            if axis_a != axis_b or ia == ib or abs(pa - pb) > tol:
                continue
            lo, hi = max(lo_a, lo_b), min(hi_a, hi_b)
            if hi - lo <= 0:
                continue
            yield (axis_a, ia, ib, (pa + pb) / 2, lo, hi, abs(pa - pb))


@dataclass(frozen=True)
class Placement:
    """Where the camera goes for one frame and one lens."""

    frame: Frame
    lens: Lens
    x: float
    y: float
    z: float
    z_from_h: float
    z_from_v: float
    covers_x: float
    covers_y: float

    @property
    def too_close(self) -> bool | None:
        """True if below the lens's published near limit, None if none is."""
        if self.lens.min_object_distance is None:
            return None
        return self.z < self.lens.min_object_distance

    @property
    def governed_by(self) -> str:
        """Which declared angle set the height: "H" or "V"."""
        return "H" if self.z_from_h >= self.z_from_v else "V"

    @property
    def excess(self) -> tuple[float, float]:
        """How much wider than the rectangle drawn the picture really is.

        Zero on the axis that governed the height and positive on the other.
        A lens whose declared pair agrees with the sensor gives zero on both;
        the wide lens's does not, and the sheet has to say on WHICH axis the
        picture runs over, which depends on how the camera is turned.
        """
        return (self.covers_x - self.frame.width,
                self.covers_y - self.frame.height)

    @property
    def angle_x(self) -> float:
        """The declared full angle that lies along the subject's X axis.

        H if the frame's long side is along X, V if the camera is turned.
        The front elevation shows this one and the end elevation the other.
        """
        return self.lens.fov_h if self.frame.long_axis == "X" \
            else self.lens.fov_v

    @property
    def angle_y(self) -> float:
        """The declared full angle that lies along the subject's Y axis."""
        return self.lens.fov_v if self.frame.long_axis == "X" \
            else self.lens.fov_h

    @property
    def naive_z(self) -> float:
        """The height the lens's DIAGONAL figure gives across the long side.

        What a reader who takes "65 degrees" for the angle across the picture
        would set.  It is wrong, and :attr:`naive_shortfall` is by how much.
        """
        long_side = max(self.frame.width, self.frame.height)
        return long_side / 2 / math.tan(math.radians(NOMINAL_DIAGONAL / 2))

    @property
    def naive_shortfall(self) -> float:
        """What a stand at :attr:`naive_z` loses off EACH end of the long side."""
        long_side = max(self.frame.width, self.frame.height)
        covers = 2 * self.naive_z * math.tan(math.radians(self.lens.fov_h / 2))
        return (long_side - covers) / 2

    @property
    def aim_tilt(self) -> float:
        """How far off vertical the camera may lean, in degrees, and still
        hold the target: the margin, seen from Z.

        A lateral error of the whole margin, or a tilt of this much, uses it
        up; the two together use it up sooner.
        """
        return math.degrees(math.atan(FRAME_MARGIN / self.z))

    def headroom(self, box: tuple[float, float, float, float]) -> float:
        """How far above the frame plane *box* may rise and stay in shot.

        For a thing that is inside the frame in plan but stands above the
        plane the height was set from: a demo board on standoffs over the
        mounting plate is inside the plate's own frame, and still leaves the
        picture if it stands high enough.
        """
        x0, y0, x1, y1 = box
        need_x = 2 * max(abs(x0 - self.x), abs(x1 - self.x))
        need_y = 2 * max(abs(y0 - self.y), abs(y1 - self.y))
        return min(self.z * (1 - need_x / self.covers_x),
                   self.z * (1 - need_y / self.covers_y))


def place(frame: Frame, lens: Lens) -> Placement:
    """Camera position for *frame* with *lens*: over the centre, at height Z.

    Z is the lower of nothing: it is the height at which BOTH declared angles
    reach, which is the greater of what each asks for on its own.  For a lens
    whose declared pair is consistent with the sensor the two are the same
    number; for one whose pair is not, the sheet says which reached further.
    """
    along_h = frame.width if frame.long_axis == "X" else frame.height
    along_v = frame.height if frame.long_axis == "X" else frame.width
    z_h = along_h / 2 / math.tan(math.radians(lens.fov_h / 2))
    z_v = along_v / 2 / math.tan(math.radians(lens.fov_v / 2))
    z = max(z_h, z_v)
    cover_h = 2 * z * math.tan(math.radians(lens.fov_h / 2))
    cover_v = 2 * z * math.tan(math.radians(lens.fov_v / 2))
    cx, cy = ((cover_h, cover_v) if frame.long_axis == "X"
              else (cover_v, cover_h))
    return Placement(frame, lens, frame.cx, frame.cy, z, z_h, z_v, cx, cy)


# ---------------------------------------------------------------------------
# The subjects: what a camera is being pointed at
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Subject:
    """One thing a camera gets pointed at, and the frames it is framed in.

    ``spec`` is what the plan view draws, and it is another family's data
    module wherever there is one: the plate's own, the Arty's own.  Nothing
    here restates a geometry that is already extracted somewhere in this
    repository, because a second copy is a copy that drifts.
    """

    key: str
    title: str
    subtitle: str
    spec: BoardSpec
    targets: tuple[Target, ...]
    #: A thing that lies inside the first frame in plan but stands above the
    #: plane that frame's height is set from, as (label, box).
    #: The sheet turns it into a headroom note: how high it may stand before
    #: it leaves the picture.  Only the mounting plate has one.
    standing: tuple[tuple[str, tuple[float, float, float, float]], ...] = ()
    sources: tuple[Source, ...] = ()
    notes: tuple[str, ...] = ()
    #: What the title block's SUBJECT field says.  Short: it is a title block
    #: cell, not a caption, and the sheet's own title carries the long form.
    subject_field: str = ""
    #: What the title block should say the subject's own figures are good to.
    #: Comma-separated, because SVG collapses the runs of spaces the other
    #: sheets separate their tolerance fields with, and "plot bodies +/-0.30
    #: Z DERIVED" then reads as one clause about nothing in particular.
    #: Not the drafting library's PCB default: nothing on these sheets is a
    #: hole in a board, and each subject's geometry came from a different
    #: source with a different claim.
    tolerance: str = ""

    def frames(self) -> tuple[Frame, ...]:
        return tuple(frame_for(t) for t in self.targets)


def _union(boxes) -> tuple[float, float, float, float]:
    xs = [v for b in boxes for v in (b[0], b[2])]
    ys = [v for b in boxes for v in (b[1], b[3])]
    return min(xs), min(ys), max(xs), max(ys)


def _envelope(spec: BoardSpec, dx: float = 0.0, dy: float = 0.0):
    """A board's assembled plan envelope, moved by (dx, dy).

    The outline together with every connector and Pmod body that overhangs
    it: what "the whole board" means to a camera, which sees the Pmod bodies
    hanging off the front edge as much as it sees the board.
    """
    bx = [(0.0, 0.0, spec.outline.width, spec.outline.height)]
    bx += [(f.x0, f.y0, f.x1, f.y1) for f in spec.features]
    bx += [(p.body_x0, p.body_y0, p.body_x1, p.body_y1) for p in spec.pmods
           if p.body_x1 > p.body_x0]
    x0, y0, x1, y1 = _union(bx)
    return x0 + dx, y0 + dy, x1 + dx, y1 + dy


def plate_board_plane() -> tuple[float, float]:
    """How far above the plate face a demo board's top face is: (low, high).

    The standoff the plate specifies plus the board's own thickness, which
    each revision's board file gives and which is not the same on all of
    them.  Z is set from the HIGHER, because a camera set from the higher
    plane covers the lower one by more than its frame.
    """
    from tinytapeout.boards import BOARDS as TT
    from tinytapeout.mounting_plate.plate import PLACEMENTS, STANDOFF_HEIGHT
    thicks = [TT[rev].outline.thickness for pl in PLACEMENTS.values()
              for rev in pl["revisions"]]
    if any(t is None for t in thicks):
        raise SystemExit("a demo board revision has no thickness in "
                         "tinytapeout/boards.py, so the plane its top face "
                         "is in cannot be placed above the plate")
    return STANDOFF_HEIGHT + min(thicks), STANDOFF_HEIGHT + max(thicks)


def plate_standoff() -> float:
    """What a demo board stands on above the plate: the plate's own figure."""
    from tinytapeout.mounting_plate.plate import STANDOFF_HEIGHT
    return STANDOFF_HEIGHT


def plate_boards_union() -> tuple[float, float, float, float]:
    """Every revision's board OUTLINE on the plate, as one box.

    Not the envelope, which adds the connectors that hang off the outline:
    this is the board itself, which the elevations draw as a slab.
    """
    from tinytapeout.boards import BOARDS as TT
    from tinytapeout.mounting_plate.plate import PLACEMENTS
    return _union([(pl["dx"], pl["dy"],
                    pl["dx"] + TT[rev].outline.width,
                    pl["dy"] + TT[rev].outline.height)
                   for pl in PLACEMENTS.values() for rev in pl["revisions"]])


def _plate_subject() -> Subject:
    """The Tiny Tapeout generic mounting plate, with every revision on it.

    The plate is the subject rather than any one demo board, because the plate
    is what the camera rig is built against and the board under it changes.
    So the first frame is not one board but every board: the union of every
    revision's assembled envelope, in plate coordinates, which is the honest
    target for a camera fixed over a plate that any of them may be bolted
    to.  What is drawn in red is likewise every place an indicator lands on
    any revision.
    """
    from tinytapeout.boards import BOARDS as TT
    from tinytapeout.mounting_plate.plate import (PLACEMENTS, PLATE,
                                                  STANDOFF_HEIGHT)

    seen: dict[tuple, str] = {}
    boxes = []
    for name, pl in PLACEMENTS.items():
        dx, dy = pl["dx"], pl["dy"]
        for rev in pl["revisions"]:
            for f in TT[rev].features:
                if f.kind not in ("led", "display7"):
                    continue
                box = (round(f.x0 + dx, 3), round(f.y0 + dy, 3),
                       round(f.x1 + dx, 3), round(f.y1 + dy, 3))
                key = box + (f.kind,)
                if key in seen:
                    continue
                seen[key] = name
                boxes.append((name, f, box))
    features = tuple(
        Feature(key=f"{name}-{f.key}".lower().replace(" ", "-")
                .replace("+", "p").replace(".", "p"),
                label=f"{name} {f.designator or f.label}", kind=f.kind,
                x0=box[0], y0=box[1], x1=box[2], y1=box[3],
                designator=f.designator)
        for name, f, box in boxes)
    lx0, ly0, lx1, ly1 = _union([(f.x0, f.y0, f.x1, f.y1) for f in features])
    # Every revision's envelope in plate coordinates, and their union.
    ex0, ey0, ex1, ey1 = _union([_envelope(TT[rev], pl["dx"], pl["dy"])
                                 for pl in PLACEMENTS.values()
                                 for rev in pl["revisions"]])
    lo, hi = plate_board_plane()
    plane = "the DEMO BOARD's top face, not the plate's"
    plane_note = (f"{STANDOFF_HEIGHT:g} mm standoffs and a {lo - STANDOFF_HEIGHT:.2f}"
                  f" to {hi - STANDOFF_HEIGHT:.2f} mm board put it {lo:.2f} to "
                  f"{hi:.2f} above the plate face; Z is from the higher")
    o = PLATE.outline
    return Subject(
        key="tt-mounting-plate",
        title="Camera over the TT Mounting Plate",
        subtitle="Camera Module OV5647, 65 and 120 degree lenses",
        spec=replace(PLATE, features=features),
        subject_field="TT Mounting Plate",
        targets=(
            Target("boards", "Every board, any revision", ex0, ey0, ex1, ey1,
                   note="Every revision's assembled envelope -- outline, "
                        "connectors, Pmod bodies -- in plate coordinates, "
                        "in one: a camera fixed over the plate serves them "
                        "all.",
                   plane_name=plane, plane_above_subject=hi,
                   plane_note=plane_note),
            Target("leds", "Every LED and 7-seg", lx0, ly0, lx1, ly1,
                   plane_name=plane, plane_above_subject=hi,
                   plane_note=plane_note),
        ),
        standing=(("A part standing on a board, anywhere in its envelope",
                   (ex0, ey0, ex1, ey1)),),
        sources=(
            Source(label="Plate geometry",
                   ref="tinytapeout/mounting_plate/plate.py",
                   note=f"Outline, placements and standoff; see "
                        f"{PLATE_SHEET}."),
            Source(label="Board and indicator positions",
                   ref="tinytapeout/boards.py",
                   note="Outlines, connectors, Pmod bodies, LEDs and "
                        "7-segment displays, in plate coordinates."),
        ),
        tolerance="plate +/-0.20, LEDs +/-0.10, Z DERIVED",
        notes=(
            "Frame B is the union of every LED and 7-segment over all five "
            "revision families. They are not clustered -- "
            f"{lx1 - lx0:.2f} x {ly1 - ly0:.2f} of a "
            f"{o.width:.0f} x {o.height:.0f} plate -- so frame B buys little "
            "over frame A.",
        ),
    )


def _arty_targets(spec: BoardSpec) -> dict[str, Target]:
    leds = [f for f in spec.features if f.kind == "led"]
    wx0, wy0, wx1, wy1 = _envelope(spec)
    lx0, ly0, lx1, ly1 = _union([(f.x0, f.y0, f.x1, f.y1) for f in leds])
    return {
        "board": Target(
            "board", "Whole board", wx0, wy0, wx1, wy1,
            note="The assembled envelope: the outline together with the "
                 "connectors and Pmod bodies that overhang it."),
        "leds": Target(
            "leds", "LD0-LD7", lx0, ly0, lx1, ly1,
            note="The four tri-colour LEDs LD0-LD3 and the four single "
                 "LD4-LD7, in two rows on a 7.00 mm pitch."),
    }


def _arty_subject() -> Subject:
    from fpga.boards import BOARDS as FPGA
    spec = FPGA["arty-a7"]
    # The Arty's own sheet, derived from the stem fpga/ writes it to rather
    # than spelled out here: a cross reference written by hand is one that
    # goes stale the day the other family renames its file.
    arty_sheet = drawing_name("fpga", slug(spec.key))
    t = _arty_targets(spec)
    src = (Source(label="Board geometry", ref="fpga/boards.py",
                  note="Outline, Pmod hosts, connectors and LED rows; see "
                       f"{arty_sheet}."),)
    return Subject(
        key="arty-a7",
        title="Camera over the Arty A7",
        subtitle="Camera Module OV5647, 65 and 120 degree lenses",
        spec=spec, targets=(t["board"], t["leds"]), sources=src,
        subject_field="Digilent Arty A7",
        tolerance="DXF +/-0.20, plot bodies +/-0.30, Z DERIVED",
        notes=(
            "Which LED row is which is not named by any Digilent source; "
            f"{arty_sheet} takes the row nearest the edge as the tri-colour "
            "LD0-LD3 by package size. Either way both rows are inside the "
            "frame, so the framing does not turn on it.",
        ),
    )


def subjects() -> dict[str, Subject]:
    """Every camera position sheet's subject, in reading order."""
    out = (_plate_subject(), _arty_subject())
    return {s.key: s for s in out}
