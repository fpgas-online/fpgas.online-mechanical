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
    ("Diagonal, from the image area",
     full_angle(math.hypot(*IMAGE_AREA)), None),
)

#: How far the declared figures and the model may differ before the model is
#: the wrong one.  A hundredth of a degree is the precision the declared
#: figures are printed to.
FOV_CHECK_TOL = 0.01

RPI_DOC = Source(
    label="Raspberry Pi camera documentation",
    ref="https://web.archive.org/web/20241230011811/"
        "https://www.raspberrypi.com/documentation/accessories/camera.html",
    note='Camera Module 1 column, quoted: sensor "OmniVision OV5647", '
         '"2592 x 1944 pixels", image area "3.76 x 2.74 mm", pixels '
         '"1.4 um x 1.4 um", focal length "3.60 mm +/- 0.01", horizontal '
         'field of view "53.50 +/- 0.13 degrees", vertical "41.41 +/- 0.11 '
         'degrees", aperture "F2.9", focus "Fixed", depth of field '
         '"Approx 1 m to infinity". Fetched from the Internet Archive at a '
         "pinned snapshot; raspberrypi.com answers a plain request 403.",
)

ARDUCAM_DOC = Source(
    label="Arducam 5MP OV5647 documentation",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/"
        "5MP-OV5647/",
    note='Product catalogue, column headed "Field of View(H x V) Focus '
         'Type", quoted: B0033 "Stock Lens 54 (H) x 41 (V) Fixed Focus"; '
         'B006604 "120 (H) x 90 (V)" on an "M6 Lens", fixed focus; B0176 '
         '"Mini Size 54(H)x44 (V) Auto Focus". Degree signs dropped here; '
         "the cached page carries them.",
)

ARDUCAM_AF = Source(
    label="Arducam motorized focus camera",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Motorized-Focus-Camera/"
        "Motorized-Focus-Camera/",
    note='Quoted: "The focusing process done with the help of motors is '
         'called motorized focus. Generally, you can understand it the same '
         'as autofocus." The OV5647 quick start adds the device tree line '
         '"dtoverlay = ov5647 , vcm" and a close-focus setting, '
         '"autofocus - range macro".',
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
    notes: tuple[str, ...] = ()

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
    notes=(
        'The "65 degrees" this lens is sold under is its DIAGONAL, and it is '
        "not a figure either vendor prints. DERIVED from Raspberry Pi's own "
        "image area and focal length: 2 x atan(sqrt(3.76^2 + 2.74^2) / 2 / "
        "3.60) = 65.74 deg. From the active pixel array instead it is 64.42 "
        "deg. What both vendors do print is the pair used here, 53.50 x "
        "41.41 deg (Arducam, independently, 54 x 41).",
    ),
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
    notes=(
        "Raspberry Pi never made a wide OV5647, so the declared figures are "
        "Arducam's, for the M6 lens on their B006604: 120 x 90 deg.",
        "Those two cannot both be right. DERIVED: 120 deg across a 4:3 "
        "sensor implies 104.82 deg down it, not 90. The height is taken as "
        "the greater of the two the pair asks for, which is the vertical, so "
        "the real frame is wider across than the rectangle drawn.",
    ),
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
    """A rectangle on the subject that has to end up inside the picture."""

    key: str
    label: str
    x0: float
    y0: float
    x1: float
    y1: float
    note: str = ""

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
    sources: tuple[Source, ...] = ()
    notes: tuple[str, ...] = ()

    def frames(self) -> tuple[Frame, ...]:
        return tuple(frame_for(t) for t in self.targets)


def _union(boxes) -> tuple[float, float, float, float]:
    xs = [v for b in boxes for v in (b[0], b[2])]
    ys = [v for b in boxes for v in (b[1], b[3])]
    return min(xs), min(ys), max(xs), max(ys)


def _plate_subject() -> Subject:
    """The Tiny Tapeout generic mounting plate, with every revision's LEDs.

    The plate is the subject rather than any one demo board, because the plate
    is what the camera rig is built against and the board under it changes.
    What is drawn in red is therefore not one board's indicators but every
    place an indicator lands on any revision, in plate coordinates -- which is
    the honest target for a rig that has to work whatever is bolted on.
    """
    from tinytapeout.boards import BOARDS as TT
    from tinytapeout.mounting_plate.plate import PLACEMENTS, PLATE

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
    o = PLATE.outline
    return Subject(
        key="tt-mounting-plate",
        title="Camera over the TT Mounting Plate",
        subtitle="Camera Module OV5647, 65 and 120 degree lenses",
        spec=replace(PLATE, features=features),
        targets=(
            Target("plate", "The whole plate", 0.0, 0.0, o.width, o.height,
                   note=f"The plate outline, {PLATE_SHEET}. Every demo "
                        "board revision sits inside it."),
            Target("leds", "Every revision's LEDs and 7-segment", lx0, ly0,
                   lx1, ly1,
                   note="The union over all five revision families, in plate "
                        "coordinates: no one revision needs all of it, but a "
                        "fixed rig does."),
        ),
        sources=(
            Source(label="Plate geometry",
                   ref="tinytapeout/mounting_plate/plate.py",
                   note="Outline 135.0 x 101.0 and the board placements, "
                        "generated by tinytapeout/mounting_plate/design.py."),
            Source(label="Indicator positions", ref="tinytapeout/boards.py",
                   note="Every revision's LED and 7-segment footprints, "
                        "extracted from the upstream KiCad files, moved into "
                        "plate coordinates by the placement offsets."),
        ),
        notes=(
            "The indicators are not clustered. Across the five revision "
            f"families they span {lx1 - lx0:.2f} x {ly1 - ly0:.2f} mm of a "
            f"{o.width:.0f} x {o.height:.0f} mm plate, so framing the "
            "indicators alone buys little over framing the plate.",
        ),
    )


def _arty_targets(spec: BoardSpec) -> dict[str, Target]:
    leds = [f for f in spec.features if f.kind == "led"]
    bx = [(0.0, 0.0, spec.outline.width, spec.outline.height)]
    bx += [(f.x0, f.y0, f.x1, f.y1) for f in spec.features]
    bx += [(p.body_x0, p.body_y0, p.body_x1, p.body_y1) for p in spec.pmods]
    wx0, wy0, wx1, wy1 = _union(bx)
    lx0, ly0, lx1, ly1 = _union([(f.x0, f.y0, f.x1, f.y1) for f in leds])
    return {
        "board": Target(
            "board", "The whole board", wx0, wy0, wx1, wy1,
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
                  note="Outline, Pmod hosts, connectors and LED rows from "
                       f"Digilent's own DXF and PDF plot; see {arty_sheet}, "
                       "which carries the derivation and its tolerances."),)
    return Subject(
        key="arty-a7",
        title="Camera over the Arty A7",
        subtitle="Camera Module OV5647, 65 and 120 degree lenses",
        spec=spec, targets=(t["board"], t["leds"]), sources=src,
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
