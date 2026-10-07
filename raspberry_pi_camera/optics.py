"""OV5647 camera optics, and where a camera has to sit to frame a board.

Hand-written, unlike :mod:`raspberry_pi_camera.boards`, which is generated
from Raspberry Pi Ltd's mechanical drawings.  Nothing here comes off a
drawing: not one of the Raspberry Pi camera mechanical drawings carries a
field of view, a focal length or a focus range.  Those are curated from the
vendors' own prose, one value at a time, with the sentence each came from
recorded beside it -- which is what ``accessories/parts.py`` does for the
parts nobody publishes a drawing of, and for the same reason.

``tools/fetch_raspberry_pi_camera.sh`` caches every page quoted below into
``tmp/src/rpi-camera-optics/``, and ``raspberry_pi_camera/verify_optics.py``
reads those files back and fails if a quote here is not in them.

The model
---------
A camera looking straight down at the subject plane.  At a height *Z* above
that plane a lens whose full field angle across the picture is *A* covers
``2 * Z * tan(A / 2)``, and that is geometry, not a lens model: a ray *A/2*
off the axis meets the plane that far out whatever the lens did to bend it.
What does depend on the lens is what *A* is.  For the stock lens it is
checked rather than assumed: Raspberry Pi publish a focal length and a
sensor size as well as a field of view for the OV5647, and the three agree to
a hundredth of a degree on both axes only under a rectilinear lens, measured
to the edge of the active pixel array.  See :data:`FOV_CHECK`.  A 120 degree
lens is not rectilinear, and its angles are split from its diagonal under
the equidistant projection instead, with the rectilinear and equisolid
splits either side of it as the bound; see "Projection" below.

Focus is the other half.  Every lens carries the near end of its declared
focus range, or None where nobody publishes one, and the depth of field
figures are DERIVED from its focal length and F number at a circle of
confusion of two pixels, with every figure that is not published marked as
derived or assumed where it is set.

How close a camera focuses is the module's, not the lens's: the v1.3 as
sold and with its lens unscrewed by hand, an adjustable-lens module and a
motorised one each have their own close limit, each from the page that
publishes it, or marked unpublished; see :data:`FOCUS_VARIANTS`.

Each position sheet is for one module and gives heights to its lens
FACE, above the plane its target is in, above what the stand is built on
and above the tallest thing under the camera; see :class:`FaceHeights`.

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
#: because it is what the vendor prints, and because FOV_CHECK shows it is NOT
#: the rectangle the declared angles are measured to.  Its diagonal is 65.74;
#: the 65 the lens is sold under is nearer OmniVision's own image area, see
#: DATASHEET_IMAGE_AREA.
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
#: model these sheets use.  The same arithmetic on Raspberry Pi's image
#: area gives a 65.74 diagonal, against the array's 64.42 and OmniVision's
#: image area's 64.94.
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
#: under and which no vendor prints.  One per rectangle, because the
#: rectangles do not agree: Raspberry Pi's image area gives 65.74, OmniVision's
#: own (DIAGONAL_FROM_DATASHEET, below) 64.94, and the active array -- the one
#: that reproduces the declared H and V -- 64.42.
DIAGONAL_FROM_IMAGE_AREA = full_angle(math.hypot(*IMAGE_AREA))
DIAGONAL_FROM_ARRAY = full_angle(math.hypot(ARRAY_WIDTH, ARRAY_HEIGHT))

#: OmniVision's own "image area", from the OV5647 datasheet: the whole
#: 2624 x 1956 array at 1.4 um, border pixels included, round the 2592 x 1944
#: active array.  Raspberry Pi's 3.76 x 2.74 reads like this 3.67 x 2.74 with
#: two digits swapped -- that is a reading, not something either company
#: says -- and it is the rectangle whose diagonal is the 65 the stock lens is
#: sold under: 64.94 degrees at 3.60 mm.
DATASHEET_IMAGE_AREA = (3.6736, 2.7384)     # mm
DIAGONAL_FROM_DATASHEET = full_angle(math.hypot(*DATASHEET_IMAGE_AREA))

#: The active array's diagonal, which every diagonal angle here is measured
#: across.  DERIVED: sqrt(3.6288^2 + 2.7216^2) = 4.536 mm.
ARRAY_DIAGONAL = math.hypot(ARRAY_WIDTH, ARRAY_HEIGHT)

#: How far a vertical may sit from what the horizontal implies, under the
#: lens's own projection, before the pair is called inconsistent.  A tenth of
#: a degree: the stock pair comes in at 0.006, and every pair that fails
#: fails by more than half a degree.
CONSISTENCY_TOL = 0.1

# ---------------------------------------------------------------------------
# Projection: how a field angle lands on the sensor
# ---------------------------------------------------------------------------
#
# A lens maps a ray arriving at angle theta off its axis to a point r from
# the centre of the sensor.  A rectilinear lens has r = f tan(theta), which
# keeps straight lines straight, and is what the stock lens is: its declared
# angles come back out of its declared focal length under tan() to a
# hundredth of a degree (FOV_CHECK).  A wide lens cannot be: at 120 degrees
# diagonal tan() would need r to grow by tan(60) = 1.73 against the axis for
# a lens of the same f, and every real one bends the edges in instead --
# barrel distortion.  The simplest model of that is the equidistant, or
# f-theta, projection, r = f theta, and the other common fisheye mapping is
# the equisolid, r = 2 f sin(theta / 2).  Most wide lenses sit between the
# rectilinear and the equisolid, and not all: YXF's figures, relabelled,
# are more compressed than the equisolid on the long axis.  So the bound is
# not taken on trust; verify_optics.py checks the margin absorbs each pair.
#
# What this does and does not change.  Where the picture's edge lands on a
# flat board Z below the lens is a matter of the angle of the ray to that
# edge, not of how the lens got it there: a ray theta off the axis meets the
# plane Z tan(theta) out, whatever the projection.  So the COVERAGE of a
# plane is 2 Z tan(A / 2) for a lens whose full angle across the picture is
# A, for a fisheye as for any other, and place() is right for both.  What the
# projection decides is what A IS for a given focal length or a given
# diagonal -- which is where the tan() arithmetic goes wrong for a wide lens
# -- and how the frame's corners fare: under barrel distortion the
# picture's straight edges map to curves on the board that bow OUTWARDS, so
# a rectangle whose edges are set by A_h and A_v at the mid-points has its
# corners inside the picture, with room to spare.  verify_optics.py checks
# that by walking the picture's edge down onto the board.


def split_diagonal(d: float, projection: str) -> tuple[float, float]:
    """The full H and V angles a lens of diagonal *d* gives on this sensor.

    DERIVED: the image height at the array's corner is half its diagonal,
    and the image heights at the middle of its long and short edges are
    half its width and half its height; each projection turns a height back
    into an angle.
    """
    half = math.radians(d / 2)
    r_d = ARRAY_DIAGONAL / 2
    out = []
    for size in (ARRAY_WIDTH, ARRAY_HEIGHT):
        r = size / 2
        if projection == "rectilinear":
            t = math.atan(math.tan(half) * r / r_d)
        elif projection == "equidistant":
            t = half * r / r_d
        elif projection == "equisolid":
            t = 2 * math.asin(math.sin(half / 2) * r / r_d)
        else:
            raise ValueError(projection)
        out.append(2 * math.degrees(t))
    return out[0], out[1]


def focal_from_diagonal(d: float, projection: str) -> float:
    """The focal length that puts diagonal *d* on the array's corner."""
    half = math.radians(d / 2)
    r_d = ARRAY_DIAGONAL / 2
    if projection == "rectilinear":
        return r_d / math.tan(half)
    if projection == "equidistant":
        return r_d / half
    if projection == "equisolid":
        return r_d / (2 * math.sin(half / 2))
    raise ValueError(projection)


def angles_from_focal(f: float, projection: str) -> tuple[float, float, float]:
    """H, V and D, in degrees, for a lens of focal length *f* on the array."""
    out = []
    for size in (ARRAY_WIDTH, ARRAY_HEIGHT, ARRAY_DIAGONAL):
        r = size / 2
        if projection == "rectilinear":
            t = math.atan(r / f)
        elif projection == "equidistant":
            t = r / f
        else:
            raise ValueError(projection)
        out.append(2 * math.degrees(t))
    return out[0], out[1], out[2]


def implied_v(h: float, projection: str) -> float:
    """The vertical angle a horizontal *h* implies on the 4:3 array."""
    if projection == "rectilinear":
        return 2 * math.degrees(
            math.atan(math.tan(math.radians(h / 2)) / ASPECT))
    if projection == "equidistant":
        return h / ASPECT
    raise ValueError(projection)


# ---------------------------------------------------------------------------
# Focus and depth of field
# ---------------------------------------------------------------------------

#: The circle of confusion the depth of field figures are worked to: two
#: pixels, 2.8 um.  ASSUMED, and not arbitrary: Raspberry Pi's own "Approx 1
#: m to infinity" for the stock lens is what a lens focused at its
#: hyperfocal distance gives with a circle of 2.24 um, 1.6 pixels (see
#: IMPLIED_COC), so two pixels is that figure rounded to the sensor.  One
#: pixel doubles every hyperfocal distance; the sheets say which they use.
COC_PIXELS = 2
COC = COC_PIXELS * PIXEL_PITCH          # mm


def hyperfocal(f: float, n: float, c: float = COC) -> float:
    """Hyperfocal distance, in mm: focused there, all from half of it to
    infinity is within *c*.  DERIVED, thin lens: f^2 / (N c) + f."""
    return f * f / (n * c) + f


def dof(s: float, f: float, n: float,
        c: float = COC) -> tuple[float, float]:
    """Near and far limits of the depth of field focused at *s*, in mm.

    DERIVED, thin lens: near = s (H - f) / (H + s - 2 f), far = s (H - f) /
    (H - s), infinity at or beyond the hyperfocal distance H.
    """
    h = hyperfocal(f, n, c)
    near = s * (h - f) / (h + s - 2 * f)
    far = math.inf if s >= h else s * (h - f) / (h - s)
    return near, far


def blur(z: float, focus: float, f: float,
         n: float) -> tuple[float, float]:
    """How big a point on a subject *z* away comes out, focused at *focus*.

    DERIVED, thin lens: the subject images at ``v = f z / (z - f)`` behind
    the lens and the sensor sits where *focus* images, so a point spreads to
    a disc of the aperture ``f / N`` scaled by how far short of its own image
    the sensor is.  Returned as (diameter on the sensor, the same disc
    projected back onto the subject), both in millimetres.
    """
    v_subject = f * z / (z - f)
    v_sensor = f * focus / (focus - f)
    on_sensor = (f / n) * abs(v_subject - v_sensor) / v_subject
    return on_sensor, on_sensor * z / v_subject


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

RPI_DOC = Source(
    label="Raspberry Pi camera documentation",
    ref="https://web.archive.org/web/20241230011811/"
        "https://www.raspberrypi.com/documentation/accessories/camera.html",
    note='Camera Module 1 column: OV5647, 2592 x 1944 at 1.4 um, image '
         'area 3.76 x 2.74, 3.60 mm, F2.9, 53.50 x 41.41 deg, "Approx 1 m '
         'to infinity"; the close limits of the other modules.',
)

OV5647_DATASHEET = Source(
    label="OmniVision OV5647 datasheet",
    ref="https://web.archive.org/web/20260723044623/"
        "https://cdn.sparkfun.com/datasheets/Dev/RaspberryPi/ov5647_full.pdf",
    note='"active array size: 2592 x 1944", "image area: 3673.6 um x '
         '2738.4 um".',
)

ARDUCAM_DOC = Source(
    label="Arducam 5MP OV5647 documentation",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/"
        "5MP-OV5647/",
    note='Product catalogue: B0033 "54 (H) x 41 (V)", B0176 "54(H)x44 (V) '
         'Auto Focus", B006604 "120(H) x 90(V)", and B006604N, the same '
         'without its IR filter, "96(H) x 72(V)".',
)

ARDUCAM_B006604 = Source(
    label="Arducam B006604 product page",
    ref="https://web.archive.org/web/20250530094438/https://www.arducam.com/"
        "b006604-arducam-for-raspberry-pi-zero-camera-module-wide-angle-120-"
        "1-4-inch-5mp-ov5647-spy-camera-with-flex-cable-for-pi-zero-and-pi-"
        "compute-module.html",
    note='"angle of view: 120 diagonal", "Focus Distance 1 m to infinity", '
         '"Focus Type Fixed".',
)

ARDUCAM_B0121 = Source(
    label="Arducam B0121 product page, the B0176's predecessor",
    ref="https://web.archive.org/web/20241103134041/https://www.arducam.com/"
        "product/5mp-ov5647-motorized-focus-camera-sensor-raspberry-pi/",
    note='"Angle of View: 54 x 41 degrees", "Full-frame SLR lens '
         'equivalent: 35 mm", "Focus distance: 4 cm to infinity".',
)

UCTRONICS_B0176 = Source(
    label="Arducam B0176 on UCTRONICS, Arducam's own store",
    ref="https://web.archive.org/web/20251209063424/https://www.uctronics."
        "com/arducam-auto-focus-camera-module-5mp-for-raspberry-pi.html",
    note='"Focus Distance 80mm to infinity", "Field of View(FOV) 54(H), '
         '44(V)", "Full-frame SLR lens equivalent 35mm".',
)

ARDUCAM_AF = Source(
    label="Arducam motorized focus camera",
    ref="https://docs.arducam.com/Raspberry-Pi-Camera/Motorized-Focus-Camera/"
        "Motorized-Focus-Camera/",
    note='Quoted: "you can understand it the same as autofocus".',
)

ALIEXPRESS_AF65 = Source(
    label="AliExpress listing of the autofocus module used here",
    ref="https://www.aliexpress.com/item/1005007810082171.html",
    note='"Camera Module OV5647 for Raspberry Pi 3 Model B+ 3B 4B HD 5MP '
         '1080P AF 65 120 Degrees Auto Focus Webcam Video", variant "AF-65 '
         'Degrees", read 3 October 2026.  No focus distance, focal length, '
         'F number or driver chip; the 65 is the only optical figure.',
)

RPI_FORUM_FOCUS = Source(
    label='Raspberry Pi forums, "setting lens focus", June 2013',
    ref="https://web.archive.org/web/20241118184419/https://www."
        "raspberrypi.org/forums/viewtopic.php?t=46637",
    note='jbeale, a forum user, the v1.3 lens unscrewed by hand: "170 '
         'degrees: focus at 7 cm"; towolf: "closer than about 4cm. EDIT: '
         'actually, make that 3cm", where the lens starts to fall out.',
)

RPI_FORUM_MACRO = Source(
    label='Raspberry Pi forums, "Camera with Macro focus", November 2013',
    ref="https://web.archive.org/web/20230427204222/https://forums."
        "raspberrypi.com/viewtopic.php?t=60828",
    note='jbeale, unscrewing the v1.3 lens: "About the closest you can get '
         'this way is about 6 cm."',
)

ARDUCAM_B0031 = Source(
    label="Arducam B0031, OV5647 with an M12 lens focused by hand",
    ref="https://www.arducam.com/blog/?p=4561",
    note='"From less than an inch to infinity".',
)

RASPI_TV = Source(
    label='RasPi.TV, "Adapt your Raspberry Pi Camera for close-up use", '
          "25 May 2013",
    ref="https://web.archive.org/web/20260212013652/https://raspi.tv/2013/"
        "adapt-your-raspberry-pi-camera-for-close-up-use",
    note='Alex Eames: "anything from about 0.5m to infinity is acceptably '
         'sharp"; "Adding a +2D lens allows you to focus at about 25cm". The '
         "article adds a lens in front and does not unscrew the stock one; a "
         'reader\'s comment under it, of 23 July 2014: "You CAN change the '
         'focus of the stock lens on the pi camera. It is tricky but can be '
         'done." No closest distance for that.',
)

COMMONLANDS = Source(
    label="Commonlands, OV5647 lens table",
    ref="https://web.archive.org/web/20260817210431/https://commonlands.com/"
        "pages/image-sensors/ov5647",
    note='Worked from each lens\'s "real distortion": CIL282, "2.2 mm M12 '
         'f/1.8 96 72 122" on the active area.',
)

YXF_M6 = Source(
    label="YXF YXF4Y001A1 M6 lens for OV5647 modules",
    ref="https://www.yxfcamera.com/products/Lenses/"
        "m6-lens-5mp-ov5647-raspberry-pi-camera-lens.html",
    note='"1.79mm", "F.no 2.4", 119.9, 92.4 and 73.9 deg with the labels '
         'shuffled, "-11.5%" distortion.',
)

WAVESHARE_G = Source(
    label="Waveshare RPi Camera (G)",
    ref="https://web.archive.org/web/20191211152844/"
        "https://www.waveshare.com/RPi-Camera-G.htm",
    note='"Aperture (F) : 2.35", "Focal Length : 3.15mm", "Angle of View '
         '(diagonal) : 160 degree"; its wiki, "Approximately 10cm to '
         'infinity"; The Pi Hut, "Horizontal angle: 120 degree".',
)

# ---------------------------------------------------------------------------
# The lenses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Figure:
    """One set of field angles for a lens, and where it came from.

    ``kind`` is DECLARED for a vendor's own figure, DERIVED for one worked
    out here, and RELABELLED for a vendor's figures put under the labels
    they must have -- YXF print their lens's diagonal as its vertical and
    its horizontal as its diagonal.  ``d`` is None where the source gives no
    diagonal.
    ``rejected`` says why a figure is not used, where it cannot be right
    whatever else is true; verify_optics.py checks the reason.
    """

    what: str
    kind: str
    h: float | None
    v: float | None
    d: float | None = None
    rejected: str = ""


@dataclass(frozen=True)
class Lens:
    """One lens option for an OV5647 camera module.

    ``fov_h`` and ``fov_v`` are the pair the sheets compute with: the full
    field angles across the picture's long and short axes, in degrees.  They
    are declared figures wherever a vendor's own pair survives the checks,
    and ``basis`` says why these and not the others in ``figures``.

    ``projection`` is how the lens maps angle to image height, which is what
    "consistent" means for its pair: a rectilinear pair obeys
    tan(V/2) = tan(H/2) x 3/4 on a 4:3 sensor, an equidistant one V = H x 3/4.

    ``alternatives`` are the other pairs the evidence would allow, and
    verify_optics.py requires the TARGET to stay in the picture at the
    sheet's height under every one of them: the frame's margin is what has
    to absorb the uncertainty in the lens, and it is checked that it does.

    ``focal_length`` and ``f_number`` carry their own basis, DECLARED,
    DERIVED or ASSUMED; ``near`` is the near end of the focus range the
    vendor declares, in millimetres, or None where none is published,
    and ``near_quote`` the words.
    ``focus_at`` is where a fixed lens is focused, which nobody publishes,
    and is ASSUMED at twice the declared near limit, as a lens focused at
    its hyperfocal distance would be; None for a lens that focuses itself.
    """

    key: str
    name: str
    short: str
    product: str
    fov_h: float
    fov_v: float
    projection: str
    basis: str
    figures: tuple[Figure, ...]
    alternatives: tuple[Figure, ...]
    focal_length: float
    focal_basis: str
    f_number: float
    f_basis: str
    focus: str
    near: float | None
    near_quote: str
    focus_at: float | None
    sources: tuple[Source, ...]

    @property
    def fov_d(self) -> float:
        """The diagonal the pair used implies, under the lens's projection.

        DERIVED.  For the stock lens, 64.42 against the array; for the wide
        lens, its declared 120 exactly, since the pair is split from it.
        """
        if self.projection == "equidistant":
            return math.hypot(self.fov_h, self.fov_v)
        th = math.tan(math.radians(self.fov_h / 2))
        tv = math.tan(math.radians(self.fov_v / 2))
        return 2 * math.degrees(math.atan(math.hypot(th, tv)))

    @property
    def fov_d_basis(self) -> str:
        """DECLARED if a vendor declares the diagonal used, else DERIVED."""
        return ("DECLARED" if any(f.kind == "DECLARED" and f.d is not None
                                  and abs(f.d - self.fov_d) < 0.01
                                  and f.h is None for f in self.figures)
                else "DERIVED")

    @property
    def consistent_v(self) -> float:
        """The vertical the pair's horizontal implies, under its projection."""
        return implied_v(self.fov_h, self.projection)

    @property
    def consistent(self) -> bool:
        """Whether the pair used agrees with the sensor's own shape."""
        return abs(self.consistent_v - self.fov_v) <= CONSISTENCY_TOL

    @property
    def hyperfocal(self) -> float:
        """DERIVED at COC, from the focal length and F number carried."""
        return hyperfocal(self.focal_length, self.f_number)

    @property
    def min_object_distance(self) -> float | None:
        """The declared near end of the focus range, in millimetres, or
        None where nobody publishes one."""
        return self.near

    def blur(self, z: float) -> tuple[float, float]:
        """How soft a fixed lens is at *z*: see :func:`blur`."""
        if self.focus_at is None:
            raise ValueError(f"{self.name} focuses itself")
        return blur(z, self.focus_at, self.focal_length, self.f_number)


#: The stock lens: Raspberry Pi's Camera Module v1.3, which Arducam's B0033
#: copies.  Every figure but the diagonal is Raspberry Pi's own.
LENS_65 = Lens(
    key="65",
    name="65 deg, stock",
    short="65",
    product="Raspberry Pi Camera Module v1.3",
    fov_h=53.50,
    fov_v=41.41,
    projection="rectilinear",
    basis="Raspberry Pi's own pair, which comes back out of their own 3.60 "
          "mm and the active array to 0.01 deg under tan().",
    figures=(
        Figure("Raspberry Pi", "DECLARED", 53.50, 41.41),
        Figure("Arducam B0033", "DECLARED", 54.0, 41.0),
        Figure("3.60 mm on the active array", "DERIVED",
               *angles_from_focal(3.60, "rectilinear")),
    ),
    alternatives=(Figure("Arducam B0033", "DECLARED", 54.0, 41.0),),
    focal_length=3.60,
    focal_basis="DECLARED",
    f_number=2.9,
    f_basis="DECLARED",
    focus="Fixed",
    near=1000.0,
    near_quote="Approx 1 m to infinity",
    focus_at=2000.0,
    sources=(RPI_DOC, OV5647_DATASHEET, ARDUCAM_DOC),
)

#: The autofocus module used here: the one on the Acorn's host and the one
#: its twin is to get, bought as the "AF-65 Degrees" variant of an AliExpress
#: listing.  A clone of the Camera Module v1.3's board -- silkscreened
#: "Raspberry pi Camera Rev 1.3", the same four holes -- carrying an OV5647
#: in a square voice-coil can, its flex marked P5V04A2.  Not an Arducam
#: module.  The listing gives no focus distance, focal length, F number or
#: driver chip; the only optical figure is the 65 in the variant's name,
#: which is what the stock lens is sold under, its diagonal.  So its angles
#: are the stock lens's, ASSUMED, and so are its 3.60 mm and F2.9, used only
#: for the depth of field once it has focused.  Its close limit is None:
#: nothing published, and nothing is worked from a guess.
AUTOFOCUS = Lens(
    key="af",
    name="65 deg, autofocus",
    short="AF",
    product="OV5647 AF-65, AliExpress, motorised",
    fov_h=LENS_65.fov_h,
    fov_v=LENS_65.fov_v,
    projection="rectilinear",
    basis="The listing's only figure is its 65, the stock lens's diagonal; "
          "the stock lens's pair is ASSUMED.",
    figures=(
        Figure("AliExpress, AF-65", "DECLARED", None, None, 65.0),
        Figure("the stock lens's pair", "ASSUMED", LENS_65.fov_h,
               LENS_65.fov_v),
    ),
    alternatives=LENS_65.alternatives,
    focal_length=LENS_65.focal_length,
    focal_basis="ASSUMED",
    f_number=LENS_65.f_number,
    f_basis="ASSUMED",
    focus="Motorized",
    near=None,
    near_quote="not published",
    focus_at=None,
    sources=(ALIEXPRESS_AF65,),
)

#: The wide lens: Arducam's B006604, the OV5647 sold as 120 degrees, a spy
#: camera on a 60 x 11.5 mm flex for the Pi Zero.  Its product page gives the
#: 120 as a DIAGONAL; the catalogue table gives the same camera "120(H) x
#: 90(V)", which cannot be right under any projection -- the horizontal is
#: shorter than the diagonal on the sensor, so no lens can see as far across
#: as it does to the corner.  The catalogue gives the same camera without its
#: IR filter, the B006604N -- its page's address calls it the 120 degree spy
#: camera, noir -- "96(H) x 72(V)".
#:
#: That pair is not a measurement.  Every row of that block of the catalogue
#: is its diagonal times 0.8 and 0.6, the 3:4:5 of the sides: B006603 72.4 x
#: 54.3 from 90.5, B006605 128 x 96 from 160, B006604N 96 x 72 from 120.  So
#: 96 x 72 is Arducam's own arithmetic, the diagonal split equidistantly,
#: r = f theta, by construction.  It is used because it is the vendor's, and
#: because the equidistant model is the usual first model of a fisheye; the
#: one independent figure, Commonlands' CIL282, worked from a real 2.2 mm
#: fisheye's distortion data on this sensor's active area, is 96 x 72 for a
#: 122 degree diagonal, which scaled to 120 is 94.4 x 70.8 -- close to the
#: equisolid split.
#:
#: The bound on that.  For a fixed diagonal, the rectilinear split is the
#: widest, 108.36 x 92.20, and puts the picture further out than drawn: the
#: safe side.  The equisolid split, 94.31 x 69.83, Commonlands' lens scaled
#: to 120, and YXF's M6 lens for OV5647 modules, 92.4 x 73.9 as relabelled,
#: are narrower than 96 x 72 on at least one axis, and are the alternatives
#: the frame margin is checked to absorb.
#:
#: Neither the focal length nor the F number is published for the B006604.
#: The focal length is DERIVED, 2.17 mm, from the 120 diagonal under the
#: equidistant projection -- a fisheye's paraxial focal length is its f in
#: r = f theta -- beside YXF's 1.79 and Commonlands' 2.2 for lenses of the
#: same angle.  The F number is ASSUMED, F2.4, YXF's for their 120 degree M6
#: lens made for these modules; it only enters the depth of field.
#:
#: Its focus is declared "1 m to infinity" too, but with this focal length
#: and F number the hyperfocal distance at two pixels is 0.70 m, so that is
#: not what a lens focused at its hyperfocal distance gives: 1 m to infinity
#: focused at 2 m would need a circle of 0.7 pixels, and the page's
#: specification table reads like the stock lens's.  The 2 m is ASSUMED all
#: the same, as for the stock lens; set at infinity instead, the blur at
#: these heights is the same to a pixel, so no verdict hangs on it.
#: Commonlands' 96 x 72 x 122 lens, scaled to a 120 diagonal in proportion,
#: as a fisheye's angles scale with its diagonal.  DERIVED.
COMMONLANDS_AT_120 = tuple(a * 120.0 / 122.0 for a in (96.0, 72.0))
LENS_120 = Lens(
    key="120",
    name="120 deg, wide",
    short="120",
    product="Arducam B006604, OV5647 with a wide M6 lens",
    fov_h=96.0,
    fov_v=72.0,
    projection="equidistant",
    basis="Arducam's own 96 x 72, which is their declared 120 diagonal "
          "split equidistantly; the margin absorbs the narrower pairs.",
    figures=(
        Figure("Arducam B006604 page", "DECLARED", None, None, 120.0),
        Figure("Arducam catalogue, B006604", "DECLARED", 120.0, 90.0,
               rejected="its H is the page's own diagonal"),
        Figure("Arducam catalogue, B006604N", "DECLARED", 96.0, 72.0),
        Figure("120 diagonal, equidistant", "DERIVED",
               *split_diagonal(120.0, "equidistant"), 120.0),
        Figure("120 diagonal, rectilinear", "DERIVED",
               *split_diagonal(120.0, "rectilinear"), 120.0),
        Figure("120 diagonal, equisolid", "DERIVED",
               *split_diagonal(120.0, "equisolid"), 120.0),
        Figure("Commonlands CIL282, 2.2 mm", "DECLARED", 96.0, 72.0, 122.0),
        Figure("Commonlands CIL282, scaled to 120", "DERIVED",
               *COMMONLANDS_AT_120, 120.0),
        Figure("YXF4Y001A1, 1.79 mm", "RELABELLED", 92.4, 73.9, 119.9),
    ),
    alternatives=(
        Figure("120 diagonal, rectilinear", "DERIVED",
               *split_diagonal(120.0, "rectilinear")),
        Figure("120 diagonal, equisolid", "DERIVED",
               *split_diagonal(120.0, "equisolid")),
        Figure("Commonlands CIL282, scaled to 120", "DERIVED",
               *COMMONLANDS_AT_120),
        Figure("YXF4Y001A1, 1.79 mm", "RELABELLED", 92.4, 73.9),
    ),
    focal_length=focal_from_diagonal(120.0, "equidistant"),
    focal_basis="DERIVED",
    f_number=2.4,
    f_basis="ASSUMED",
    focus="Fixed",
    near=1000.0,
    near_quote="Focus Distance 1 m to infinity",
    focus_at=2000.0,
    sources=(ARDUCAM_B006604, ARDUCAM_DOC, COMMONLANDS, YXF_M6),
)

#: The two lenses every sheet draws, by key.
LENSES = {LENS_65.key: LENS_65, LENS_120.key: LENS_120}

#: Every lens a height is worked out for: the two drawn, and the autofocus
#: module used here, whose angles are taken as the stock lens's.
ALL_LENSES = {LENS_65.key: LENS_65, AUTOFOCUS.key: AUTOFOCUS,
              LENS_120.key: LENS_120}


#: Waveshare's RPi Camera (G): the Camera Module v1 sized OV5647 with a
#: fisheye, and the other thing sold as "120 degrees" -- horizontally, on The
#: Pi Hut's listing of it, and 160 diagonally on Waveshare's own page.  Not
#: drawn, and here for the record: its declared "3.15mm" cannot put 160
#: degrees on this sensor under any projection a lens has -- equidistant, it
#: gives 82.5 -- so its figures do not hold together, and nothing is worked
#: from them.  Its focus is adjustable, "Approximately 10cm to infinity".
WAVESHARE_G_FIGURES = (
    Figure("Waveshare, diagonal", "DECLARED", None, None, 160.0),
    Figure("The Pi Hut, horizontal", "DECLARED", 120.0, None, 160.0),
    Figure("3.15 mm, equidistant", "DERIVED",
           *angles_from_focal(3.15, "equidistant")),
)

#: The figure the stock lens is sold under, which is its DIAGONAL and which no
#: vendor prints.  Kept as a number only so the sheets can show what goes
#: wrong if it is used as if it were the angle across the picture, which is
#: the mistake the name invites.
NOMINAL_DIAGONAL = 65.0

#: The circle of confusion Raspberry Pi's "Approx 1 m to infinity" implies,
#: if the stock lens is focused at its hyperfocal distance and the metre is
#: half of it: DERIVED, f^2 / (N (2000 - f)).
IMPLIED_COC = (LENS_65.focal_length ** 2
               / (LENS_65.f_number
                  * (LENS_65.focus_at - LENS_65.focal_length)))

#: The near limits Raspberry Pi publish for their own focusable modules.
#: Different sensors -- IMX219 and IMX708, not OV5647 -- so they cannot be
#: read as an OV5647 figure. They are here because they say what order of
#: distance a focusable Raspberry Pi module reaches.
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
# Focus, per variant of the camera
# ---------------------------------------------------------------------------
#
# A Lens above is a field of view.  How close a camera focuses is the
# module's, and the OV5647 is sold three ways that matter here: the Camera
# Module v1.3, fixed and set far, whose glued lens can be broken free and
# unscrewed by hand; modules with a lens focused by hand by design; and
# modules with a motorised lens, a voice coil and its driver on the I2C bus,
# focused by software.  Each figure below belongs to the module named beside
# it, not to its class, and where nobody publishes one it says so.


@dataclass(frozen=True)
class FocusVariant:
    """One way an OV5647 module is sold, and how close it can focus.

    ``module`` is the product the figure belongs to, ``near`` its close
    limit in millimetres, or None where none is published, and ``quote`` the
    words it is read from.  ``basis`` is DECLARED for a vendor's figure,
    REPORTED for a forum user's measurement, and NONE where nothing is
    published.  ``lens`` is whose field of view frames the subject, and
    ``lens_basis`` says whether that is the module's own or ASSUMED.
    ``used`` is True for the modules on the rig, False for one listed only
    for comparison.
    """

    key: str
    variant: str
    module: str
    near: float | None
    quote: str
    basis: str
    lens: Lens
    lens_basis: str
    source: Source
    used: bool = True


#: Every variant an in-focus height is given for, in the order the sheets
#: list them.
#:
#: The v1.3 unscrewed: no figure from Raspberry Pi, whose own post on doing
#: it gives no distance.  Two forum users measured it in 2013, neither
#: Raspberry Pi staff: jbeale, "about 6 cm" as the closest, after "170
#: degrees: focus at 7 cm"; towolf, 3 cm, at the point the lens starts to
#: fall out of its thread.  The 6 cm is used, the closest anyone reports
#: with the lens still held.  raspi.tv's article on the v1.3 close up gives
#: no figure for it either: it adds a +2D lens in front, "focus at about
#: 25cm", and only a reader's comment under it says the stock lens's focus
#: can be changed, with no distance.  So the forum's 6 cm stands alone.
#:
#: Focused by hand: Arducam's B0031, an OV5647 on an M12 lens, "From less
#: than an inch to infinity" -- so 25.4 mm is an upper bound on its close
#: limit, and the height worked from it is no lower than it needs.  Its
#: angles are taken as the stock lens's, ASSUMED: where the field of view
#: sets the height the lens is a 3.6 mm one like the stock lens, and where
#: the close limit sets it the angle does not enter.
#:
#: Motorised: the module used here publishes no close limit, so no height
#: in focus is given for it.  Arducam's B0176, a different module, publishes
#: "80mm to infinity", and is listed for comparison, marked as not the one
#: used.
FOCUS_VARIANTS = (
    FocusVariant("v13", "v1.3 as sold", "Raspberry Pi Camera Module v1.3",
                 LENS_65.near, LENS_65.near_quote, "DECLARED", LENS_65,
                 "own", RPI_DOC),
    FocusVariant("v13-unscrewed", "v1.3, lens unscrewed by hand",
                 "Raspberry Pi Camera Module v1.3", 60.0,
                 "About the closest you can get this way is about 6 cm.",
                 "REPORTED", LENS_65, "own", RPI_FORUM_MACRO),
    FocusVariant("manual", "lens focused by hand", "Arducam B0031", 25.4,
                 "From less than an inch to infinity", "DECLARED", LENS_65,
                 "ASSUMED", ARDUCAM_B0031),
    FocusVariant("af", "motorised, the one used here", AUTOFOCUS.product,
                 None, AUTOFOCUS.near_quote, "NONE", AUTOFOCUS, "ASSUMED",
                 ALIEXPRESS_AF65),
    FocusVariant("b0176", "motorised, NOT the one used here",
                 "Arducam B0176", 80.0, "80mm to infinity", "DECLARED",
                 LENS_65, "ASSUMED", UCTRONICS_B0176, used=False),
    FocusVariant("wide", "120 deg as sold", "Arducam B006604", LENS_120.near,
                 LENS_120.near_quote, "DECLARED", LENS_120, "own",
                 ARDUCAM_B006604),
)


def framed_in_focus(frame: Frame, lens: Lens) -> float:
    """The lowest Z that frames *frame* with *lens* focused at that Z.

    A lens focused at a distance s stands v = f s / (s - f) from the sensor,
    further than f, so it covers less than the pinhole at f says:
    s (sensor / v) = (s - f) (sensor / f), the pinhole's cover at s - f.  The
    height that frames the subject in focus is therefore the field-of-view
    height plus f.  DERIVED, thin lens, the declared angles taken to be the
    lens's focused at infinity.
    """
    return place(frame, lens).z + lens.focal_length


def in_focus_z(frame: Frame, v: FocusVariant) -> float | None:
    """The lowest Z at which variant *v* both frames *frame* and is in focus.

    The higher of the field-of-view height, focused there, and the module's
    close limit: raising the camera only grows the picture, so above the
    framing height the close limit is all that can push it up.  None where
    the module's close limit is not published.  Z is to the entrance pupil
    as on every position sheet; no vendor or forum post says whether its
    close limit is from the lens face, the pupil or the sensor, which are
    within a few millimetres of each other on these modules.
    """
    if v.near is None:
        return None
    return max(framed_in_focus(frame, v.lens), v.near)



def picture(lens: Lens, z: float) -> tuple[float, float]:
    """What *lens* covers on a plane *z* away, focused there: (long, short).

    DERIVED, thin lens, as :func:`framed_in_focus`: focused at z the lens
    covers what the pinhole at f covers at z - f, so 2 (z - f) tan(A / 2)
    along each axis of the sensor.
    """
    return tuple(2 * (z - lens.focal_length) * math.tan(math.radians(a / 2))
                 for a in (lens.fov_h, lens.fov_v))


def crop(frame: Frame, lens: Lens, z: float) -> tuple[float, float]:
    """How much of the picture at *z* *frame* is, and the picture's scale.

    Returned as (the crop factor, pixels per millimetre): the picture's long
    side over the frame's, which is the digital zoom that fills the picture
    with the frame, and the sensor's columns over the picture's long side.
    The pixels are square, so a length on the subject spans the same number
    of them whichever way the camera is turned.  DERIVED.
    """
    long_side, _ = picture(lens, z)
    return (long_side / max(frame.width, frame.height),
            SENSOR_COLUMNS / long_side)


@dataclass(frozen=True)
class FaceHeights:
    """Where one module's LENS FACE goes: the headline of a one-module sheet.

    A sheet that carries this gives heights to the lens face, not Z to the
    entrance pupil, and for one module only: ``variant``, whose close limit
    is used.  Three figures follow.

    ``face`` is the lens face above the plane the frame's target lies in:
    the higher of the height that frames it, focused there, and the
    module's close limit, which :func:`in_focus_z` works out to the pupil.
    The face is then SET there.  That is the conservative convention: the
    pupil is behind the face, by at most the lens's own height, so it is
    that much further from the subject than worked -- the picture is larger,
    never smaller, and the subject no nearer than the close limit.

    ``above_base`` adds ``base``, how far that plane stands above whatever
    the stand is built on, and ``clearance`` takes off ``highest``, how far
    the tallest thing under the camera stands above the plane.  Each is None
    while its term is unmeasured, and the sheet prints the formula.

    ``base`` and ``highest`` are ``accessories.parts.StackHeight``s: this
    module restates neither.

    The rest is what the sheet calls things, which is the subject's:
    ``plane`` is the plane F is measured from, as the heights table names
    it, and ``plane_short`` the same in a few words, for the legend;
    ``base_what`` what H1 is measured from, as the heights table names it,
    and ``base_short`` the same for the legend: the mounting plate's face,
    or, under a board with no mounting holes, what its feet stand on;
    ``highest_what`` the highest point; ``target`` what has to be sharp; and
    ``heading`` what the heights table's title says they put in view.
    """

    variant: FocusVariant
    base: object
    highest: object
    plane: str
    plane_short: str
    base_what: str
    base_short: str
    highest_what: str
    target: str
    heading: str

    def face(self, frame: Frame) -> float:
        z = in_focus_z(frame, self.variant)
        if z is None:
            raise ValueError(f"{self.variant.module} publishes no close "
                             "limit, so no height in focus can be given")
        return z

    def above_base(self, frame: Frame) -> float | None:
        if self.base.value is None:
            return None
        return self.base.value + self.face(frame)

    def clearance(self, frame: Frame) -> float | None:
        if self.highest.value is None:
            return None
        return self.face(frame) - self.highest.value

    def headroom(self, frame: Frame,
                 box: tuple[float, float, float, float]) -> float:
        """How far above the plane *box* may rise and stay in the picture,
        with the lens face at :meth:`face` over *frame* and focused there.

        :meth:`Placement.headroom` with the lens refocused: the picture on
        the plane is then :func:`picture` at the face's height, and the cone
        that carries it has its apex at the face -- the pupil is behind it,
        which only widens the cone -- so a thing h above the plane is inside
        it while its half-width is under (F - h) / F of the picture's.
        """
        f = self.face(frame)
        long_side, short_side = picture(self.variant.lens, f)
        cover_x, cover_y = ((long_side, short_side) if frame.long_axis == "X"
                            else (short_side, long_side))
        x0, y0, x1, y1 = box
        need_x = 2 * max(abs(x0 - frame.cx), abs(x1 - frame.cx))
        need_y = 2 * max(abs(y0 - frame.cy), abs(y1 - frame.cy))
        return min(f * (1 - need_x / cover_x), f * (1 - need_y / cover_y))


@dataclass(frozen=True)
class Observation:
    """What somebody saw on the deployed hardware, and who and when.

    Not a measurement and not a vendor's figure: ``distance`` is by eye, in
    millimetres from the lens to the target, and ``lens`` is whose angles
    anything DERIVED from it is worked with.
    """

    by: str
    on: str
    lens: Lens
    distance: float
    text: str


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
    the subject's own top face, and on some of these sheets it does not: the
    demo boards' indicators are on a board standing on standoffs above the
    mounting plate, and the Acorn is a card seated in a HAT above a Pi.  A
    camera height measured to the wrong plane covers less at the right one --
    the picture at ``h`` above the frame plane is ``(Z - h) / Z`` of what is
    drawn -- so ``Z`` on these sheets is always quoted above the TARGET's
    plane, and ``plane_name`` says which plane that is.

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
        hold the target, with the whole margin spent on the lean.

        Measured at the picture's edge on the axis that set the height, not
        on the lens axis: that edge is theta = A/2 out, and a lean t pulls it
        in to Z tan(theta - t), so the margin m is used up when
        tan(theta) - tan(theta - t) = m / Z.  At the edge a degree of lean
        moves the picture sec^2(theta) times as far as it does on the axis,
        which on the wide lens is more than twice.

        A lateral error of the whole margin, or a lean of this much, uses it
        up; the two together use it up sooner, and so does anything the lens
        is not known to within -- it all comes out of the same margin.
        """
        a = self.lens.fov_h if self.governed_by == "H" else self.lens.fov_v
        theta = math.radians(a / 2)
        return math.degrees(
            theta - math.atan(math.tan(theta) - FRAME_MARGIN / self.z))

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
    #: it leaves the picture.  The plate's and the Arty's have one.
    standing: tuple[tuple[str, tuple[float, float, float, float]], ...] = ()
    #: Where a known part stands inside the first of those, as (what, box):
    #: the headroom note gives each its own figure beside the worst case, at
    #: the envelope's corner, so that a measured T is held against the
    #: figure for where its part stands.  Only the Arty's J9 has one.
    standing_at: tuple[tuple[str, tuple[float, float, float, float]], ...] = ()
    #: What the plan names frame A's target with a leader, where the target
    #: is too small at the plan's scale to be told from what is round it.
    #: Only the Acorn's LEDs need one: a column 2.3 mm wide, lying in plan
    #: over the Pi's own Ethernet and USB bodies, which are under the HAT.
    plan_callout: str = ""
    #: The lenses this sheet draws, by key, where it is not both of LENSES.
    #: Every position sheet sets it: each is for one module.
    lens_keys: tuple[str, ...] | None = None
    #: Where the lens FACE goes, on a sheet that gives lens-face heights for
    #: one module instead of Z per lens: every position sheet's.
    face: FaceHeights | None = None
    #: What has been seen on the deployed hardware, for the sheet to record
    #: beside what it derives.
    observations: tuple[Observation, ...] = ()
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
    #: Whether the docs pictures take in all the notes, the columns the text
    #: runs on into under the plan and in the annotation column, and not just
    #: the first two beside the plan, and leave out the empty paper left of
    #: the elevations.  The Acorn's are the two notes and the whole width; the
    #: plate's and the Arty's lens-face notes are further on, and with the
    #: dimension chain the elevations are wider than the tables without the
    #: trim.
    docs_all_notes: bool = False

    def frames(self) -> tuple[Frame, ...]:
        return tuple(frame_for(t) for t in self.targets)

    def lenses(self) -> tuple[Lens, ...]:
        """The lenses this subject's sheet draws: both, unless it says."""
        if self.lens_keys is None:
            return tuple(LENSES.values())
        return tuple(LENSES[k] for k in self.lens_keys)


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


# --- The plate's stack -------------------------------------------------------
#
# The two heights the plate's lens face is given from, as the Acorn's are.
# S, the plate's face to the demo board's top face, is a figure: the plate's
# own standoff and each revision's own board thickness, both already in this
# repository, so it is worked from them rather than typed in.  T, the board's
# top face to the tallest part standing on it, is not: no board file gives a
# part a height, and nobody publishes one for every revision, so it is to
# measure, like the Acorn's.


def plate_stack_s():
    """S on the plate: its face, the standoffs' base, to the board's top face.

    ``plate_board_plane``'s higher figure, which F is set from, with the
    spread down to the thinnest board as its tolerance, rounded up to the
    hundredth.  The standoff is the plate's choice and the boards' thickness
    their KiCad files' stackup; neither states a fabrication tolerance, and
    the source says so.
    """
    from accessories.parts import StackHeight
    lo, hi = plate_board_plane()
    st = plate_standoff()
    return StackHeight(
        "S", "the mounting plate's face, the standoffs' base, to the demo "
             "board's top face",
        value=hi, tol=math.ceil(round((hi - lo) * 100, 6)) / 100,
        source=f"M3 x {st:g} mm standoffs ({PLATE_SHEET}) and a "
               f"{lo - st:.2f} to {hi - st:.2f} mm board (each revision's "
               f"KiCad file): {lo:.2f} to {hi:.2f}, F set from the higher. "
               "Neither states a fabrication tolerance")


def plate_stack_t():
    """T on the plate: the board's top face to its tallest part.  MEASURE.

    A function, as ``plate_stack_s`` is, so that asking this module about a
    lens does not import the accessories.  A measured figure goes in here,
    with its tolerance and who measured it, and the sheet then prints H2.
    """
    from accessories.parts import StackHeight
    return StackHeight(
        "T", "the demo board's top face to the tallest part on it, on "
             "whichever revision is fitted")


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
                  f"{hi:.2f} above the plate face; F is from the higher")
    o = PLATE.outline
    # One module, as on the Acorn's sheet: the v1.3 with its stock lens,
    # unscrewed to focus, and the heights of its lens face.  The 120 degree
    # lens is off this sheet; TT-MP-CAM120 is still built over frame A from
    # LENS_120, and prints its own height.
    variant = next(v for v in FOCUS_VARIANTS if v.key == ACORN_VARIANT)
    face = FaceHeights(variant, plate_stack_s(), plate_stack_t(),
                       plane="the demo board's top face, any revision",
                       plane_short="the board's top face",
                       base_what="the mounting plate's face, the "
                                 "standoffs' base",
                       base_short="The mounting plate's face",
                       highest_what="the highest point on the board",
                       target="the boards",
                       heading="BOARDS IN VIEW AND IN FOCUS")
    return Subject(
        key="tt-mounting-plate",
        title="Camera over the TT Mounting Plate",
        subtitle="Camera Module v1.3, stock 65 degree lens: lens face "
                 "heights",
        spec=replace(PLATE, features=features),
        subject_field="TT Mounting Plate",
        lens_keys=(LENS_65.key,),
        face=face,
        docs_all_notes=True,
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
                        "7-segment displays, in plate coordinates, and "
                        "each board's thickness."),
            # Cited for where the lens is focused as sold, as on the
            # Acorn's sheet; the forum's close limit is on the lens sheet.
            replace(RASPI_TV, label="raspi.tv, 25 May 2013", note=""),
        ),
        tolerance="plate +/-0.20, LEDs +/-0.10, heights DERIVED",
        notes=(
            "Frame B is the union of every LED and 7-segment over all five "
            "revision families. They are not clustered -- "
            f"{lx1 - lx0:.2f} x {ly1 - ly0:.2f} of a "
            f"{o.width:.0f} x {o.height:.0f} plate -- so frame B buys little "
            "over frame A.",
            "T: no board file gives a part a height, and nobody publishes "
            "one for every revision. Measure it on the boards in use, from "
            "the board's top face to the top of its tallest part.",
        ),
    )


# --- The Arty's stack --------------------------------------------------------
#
# The two heights the Arty's lens face is given from, as the plate's and the
# Acorn's are.  The Arty has no mounting holes and stands on four rubber feet,
# so S is from what it stands on, under the feet, to its top face -- a foot
# and the board -- and T from its top face to the top of its tallest part.
#
# Neither is a figure.  Digilent's A7 drawing is a plan and nothing else: it
# draws the feet, as circles 10.0 mm across centred 5.0 from each corner, and
# gives no height, for them, the board or any part.  Digilent's 3D model does
# give heights, but it is of the Arty Rev C, not the A7, and states no
# tolerance; and its feet are not the ones the A7 drawing draws.  So its
# figures are quoted on the sheet, as the Rev C's, and both terms are to
# MEASURE on an A7.

#: What Digilent's 3D model of the Arty Rev C, ``Arty Rev C.stp`` in
#: ``arty_revc_cad.zip``, gives, in millimetres: the REV C's, not the A7's.
#: ``raspberry_pi_camera/arty_revc.py`` reads each back out of the model, and
#: the foot the A7 drawing draws out of its plot, and fails if one has moved.
#: The model's outline is 109.22 x 86.36, the A7 drawing's 4.3 x 3.4 in;
#: the drawing's DXF, which ``fpga/boards.py`` is drawn from, is 109.00 x
#: 87.00.
ARTY_REVC_BOARD = 1.50          # the board slab: its two largest faces apart
ARTY_REVC_FOOT = 3.70           # "Ruber_Feet", under the slab, domed
ARTY_REVC_FOOT_ACROSS = 8.70    # the same feet in plan
ARTY_REVC_TALLEST = 14.80       # J9's "shielding", over the slab's top face
ARTY_FOOT_DRAWN = 10.0          # the A7 drawing's foot circles, across

ARTY_REVC_SOURCE = Source(
    label="3D model, Arty Rev C",
    ref="https://digilent.com/reference/_media/reference/programmable-logic/"
        "arty/arty_revc_cad.zip",
    note="Digilent, Arty Rev C.stp, 20 June 2016: not the A7. Its heights "
         "are quoted in the notes; no height on this sheet is set from it.")


def arty_stack_s():
    """S on the Arty: what it stands on, under its feet, to its top face.

    MEASURE.  A function, as ``plate_stack_s`` is, so that asking this
    module about a lens does not import the accessories.  A measured figure
    goes in here, with its tolerance and who measured it, and the sheet then
    prints H1.
    """
    from accessories.parts import StackHeight
    return StackHeight(
        "S", "what the Arty stands on, under its rubber feet, to its top "
             "face: a foot and the board")


def arty_stack_t():
    """T on the Arty: its top face to the top of its tallest part.  MEASURE.

    A measured figure goes in here, as in ``arty_stack_s``, and the sheet
    then prints H2.
    """
    from accessories.parts import StackHeight
    return StackHeight(
        "T", "the Arty's top face to the top of its tallest part")


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
    """The Digilent Arty A7, standing on its rubber feet.

    One module, as on the plate's and the Acorn's sheets: the v1.3 with its
    stock lens, unscrewed to focus, and the heights of its lens face.  Frame
    A is the whole board, which F is set from -- the whole board in view and
    in focus -- and frame B its LEDs, as the plate keeps its LEDs.
    """
    from fpga.boards import BOARDS as FPGA
    spec = FPGA["arty-a7"]
    # The Arty's own sheet, derived from the stem fpga/ writes it to rather
    # than spelled out here: a cross reference written by hand is one that
    # goes stale the day the other family renames its file.
    arty_sheet = drawing_name("fpga", slug(spec.key))
    t = _arty_targets(spec)
    board = t["board"]
    variant = next(v for v in FOCUS_VARIANTS if v.key == ACORN_VARIANT)
    face = FaceHeights(variant, arty_stack_s(), arty_stack_t(),
                       plane="the Arty's top face",
                       plane_short="the board's top face",
                       base_what="what the Arty stands on, under its feet",
                       base_short="What the Arty stands on",
                       highest_what="the highest point on the board",
                       target="the board and its LEDs",
                       heading="BOARD IN VIEW AND IN FOCUS")
    # Where J9 stands, which is not the envelope's corner: how tall it may
    # be and stay in frame A's picture, against the Rev C's figure.
    j9 = next(f for f in spec.features if f.designator == "J9")
    j9_box = (j9.x0, j9.y0, j9.x1, j9.y1)
    whole = (board.x0, board.y0, board.x1, board.y1)
    worst = face.headroom(frame_for(board), whole)
    j9_room = face.headroom(frame_for(board), j9_box)
    src = (
        Source(label="Board geometry", ref="fpga/boards.py",
               note="Outline, Pmod hosts, connectors and LED rows; see "
                    f"{arty_sheet}."),
        ARTY_REVC_SOURCE,
        # Cited for where the lens is focused as sold, as on the Acorn's
        # and the plate's sheets; the forum's close limit is on the lens
        # sheet.
        replace(RASPI_TV, label="raspi.tv, 25 May 2013", note=""),
    )
    return Subject(
        key="arty-a7",
        title="Camera over the Arty A7",
        subtitle="Camera Module v1.3, stock 65 degree lens: lens face "
                 "heights",
        spec=spec, targets=(board, t["leds"]), sources=src,
        subject_field="Digilent Arty A7",
        lens_keys=(LENS_65.key,),
        face=face,
        docs_all_notes=True,
        standing=(("A part standing on the board, anywhere in its envelope",
                   whole),),
        standing_at=(("J9", j9_box),),
        tolerance="DXF +/-0.20, plot bodies +/-0.30, heights DERIVED",
        notes=(
            "Which LED row is which is not named by any Digilent source; "
            f"{arty_sheet} takes the row nearest the edge as the tri-colour "
            "LD0-LD3 by package size. Either way both rows are inside the "
            "frame, so the framing does not turn on it.",
            "S: the A7 drawing has four corner circles, "
            f"{ARTY_FOOT_DRAWN:.1f} mm across scaled from its plot, taken "
            "as the rubber feet, and no height for them or the board. "
            "Digilent's 3D model of the Arty Rev C, not the A7, has a "
            f"{ARTY_REVC_BOARD:.2f} board on feet {ARTY_REVC_FOOT:.2f} "
            f"tall, {ARTY_REVC_BOARD + ARTY_REVC_FOOT:.2f} in all, but its "
            f"feet are {ARTY_REVC_FOOT_ACROSS:.2f} across and it states no "
            "tolerance. Measure S on the A7, from what it stands on to its "
            "top face.",
            "T: the A7 drawing gives no part a height. The Rev C model's "
            "tallest part is the Ethernet jack J9's shield, "
            f"{ARTY_REVC_TALLEST:.2f} above the board's top face, and the "
            f"A7 drawing puts J9 in the same place: more than the "
            f"{worst:.1f} mm headroom at the envelope's corner, less than "
            f"the {j9_room:.1f} where J9 stands. Measure T on the A7, from "
            "its top face to the top of its tallest part, and which part.",
        ),
    )


# --- The Acorn ------------------------------------------------------------
#
# Nothing restated.  The card, where it is seated, where its LEDs are and the
# two heights of its stack are accessories/parts.py's, which is what the
# assembly sheet is drawn from too: the card on this sheet and the card on
# that one are one rectangle in one place, so they cannot drift apart.
#
# The one thing framed is the LEDs, because they are the only part of the
# Acorn anyone needs to see: A1 to A4 and PWR, at the card's far end.  Not the
# card and not the whole assembly, which this sheet framed first and which put
# the camera nearly four times as high, the LEDs that much smaller in the
# picture.  The camera's axis is over the LEDs, as it is over any frame's
# target, and here that matters: the heatsink's blower stands beside them,
# as Enjoy-Digital's photographs show and nobody dimensions: its height is
# part of T, unmeasured.  The camera is put over the LEDs so that rays to
# them rise clear of it, ASSUMED, to be confirmed when T is measured.
#
# One module: the Raspberry Pi Camera Module v1.3 with its stock lens, and
# heights to its lens FACE, see FaceHeights, as on every position sheet:
# where the face of the one camera goes, above what the stand is built on
# and above the tallest thing under it.  Both of those need a height of
# the stack nobody has published or measured, so each is a formula with one
# term to MEASURE.

#: The plane the Acorn's frame is set from, and why it is the card's and not
#: the Pi's: the LEDs are on the card's top face, which stands above the Pi,
#: and a height set at the Pi's face covers less at the card's.
CARD_PLANE = "the ACORN CARD's top face, not the Pi's"
CARD_PLANE_NOTE = (
    "the LEDs are on it. How far it stands above the mounting plate is S, "
    "which nobody publishes: measure it"
)

#: The module the Acorn's sheet is for, by its key in FOCUS_VARIANTS: the
#: v1.3 with its lens unscrewed, which is the only way it focuses this close.
ACORN_VARIANT = "v13-unscrewed"


def _hat_sheet() -> str:
    """What the sheet that draws the assembly the Acorn sits in is called.

    Derived from the stem accessories/ writes it to, like every other cross
    reference here.

    A function rather than a module constant, and the import inside it,
    because every other family's data module is imported inside the subject
    that wants it: importing this module to ask about a lens should not pull
    in the accessories.
    """
    from accessories.parts import POE_M2_HAT_WITH_ACORN
    from tools.layout import acc_stem
    return drawing_name("accessories", acc_stem(POE_M2_HAT_WITH_ACORN.key))


def _acorn_subject() -> Subject:
    from accessories.parts import (ACORN_CARD, ACORN_LED_TOL, ACORN_LEDS,
                                   ACORN_STACK_S, ACORN_STACK_T,
                                   HAT_PLUS_SPEC_SOURCE, HAT_PLUS_SPACER_QUOTE,
                                   M2_CARD_THICKNESS, M2_CARD_THICKNESS_TOL)
    from raspberry_pi.boards import BOARDS as RPI
    from raspberry_pi_camera import v1
    hat_sheet = _hat_sheet()
    pi = RPI["rpi5"]
    spec = replace(pi, features=pi.features + (ACORN_CARD,) + ACORN_LEDS)
    lx0, ly0, lx1, ly1 = _union([(f.x0, f.y0, f.x1, f.y1) for f in ACORN_LEDS])
    names = [f.designator for f in ACORN_LEDS]
    target = Target(
        "leds", f"{names[0]}-{names[-2]} and {names[-1]}", lx0, ly0, lx1, ly1,
        note=f"{names[0]} to {names[-2]} are in a column on the +Y side "
             f"of the retention screw, {names[-1]} on the -Y side; measured "
             f"off SQRL's own photograph to +/-{ACORN_LED_TOL:.1f} mm.",
        plane_name=CARD_PLANE, plane_above_subject=None,
        plane_note=CARD_PLANE_NOTE)
    variant = next(v for v in FOCUS_VARIANTS if v.key == ACORN_VARIANT)
    face = FaceHeights(variant, ACORN_STACK_S, ACORN_STACK_T,
                       plane="the card's top face, where the LEDs are",
                       plane_short="the card",
                       base_what="the mounting plate's face, the "
                                 "standoffs' base",
                       base_short="The mounting plate's face",
                       highest_what="the assembly's highest point",
                       target="the LEDs",
                       heading="THE LEDs IN VIEW AND IN FOCUS")
    return Subject(
        key="acorn-cle-215-plus",
        title="Camera over the Acorn CLE-215+",
        subtitle="Camera Module v1.3, stock 65 degree lens: lens face "
                 "heights",
        spec=spec,
        subject_field="Acorn CLE-215+, Pi 5",
        targets=(target,),
        plan_callout=f"LEDs {target.label}",
        lens_keys=(LENS_65.key,),
        face=face,
        observations=(
            Observation(
                by="Tim Ansell", on="3 Oct 2026", lens=AUTOFOCUS,
                distance=100.0,
                text='the autofocus camera on the reference Acorn, the '
                     '"AF-65" OV5647 module, is about 10 cm above the '
                     "Acorn's LEDs, the picture looks in focus, and it needs "
                     "a digital zoom or crop onto the Acorn's end"),
        ),
        sources=(
            Source(label="Board geometry", ref="raspberry_pi/boards.py",
                   note="Pi 5 outline and connectors; see "
                        f"{drawing_name('raspberry-pi', slug(pi.key))}."),
            # One line for the card, its LEDs and the HAT, as the Arty's
            # sheet cites fpga/boards.py and not Digilent: the M.2
            # specification, SQRL's page and photograph and Waveshare's
            # drawing are the part's own sources.
            Source(label="Card, LEDs, HAT and stack",
                   ref="accessories/parts.py",
                   note="The card, its seat, its LEDs, S and T; see "
                        f"{hat_sheet}."),
            # The quotes' own pages, without the notes the lens sheet and
            # the data modules carry beside them: the sheet's notes quote
            # them.  Raspberry Pi's documentation and the forum thread are
            # on the lens sheet, which the last source here names.
            replace(HAT_PLUS_SPEC_SOURCE, note=""),
            replace(RASPI_TV, label="raspi.tv, 25 May 2013", note=""),
        ),
        tolerance=(f"Pi 5 +/-0.20, LEDs +/-{ACORN_LED_TOL:.1f}, "
                   "heights DERIVED"),
        notes=(
            f"{ACORN_STACK_S.symbol} is six terms -- standoffs under the "
            "Pi, Pi 5 board, Pi-to-HAT spacers, HAT board, M.2 socket seat, "
            f"card -- and only the card's {M2_CARD_THICKNESS:.2f} "
            f"+/-{M2_CARD_THICKNESS_TOL:.2f} is published (M.2 "
            "specification); the HAT+ specification only recommends "
            f'"{HAT_PLUS_SPACER_QUOTE}". Measure {ACORN_STACK_S.symbol} as '
            "one figure.",
            "The camera is over the LEDs, not the card, so that rays to "
            "them rise clear of the heatsink's blower beside them: ASSUMED "
            "from Enjoy-Digital's photographs, which show the blower there "
            f"and no height for it ({ACORN_STACK_T.symbol} includes it, "
            "unmeasured); confirm when it is measured. The camera board "
            f"overhangs it, its underside {v1.LENS_TOP_Z:.2f} above the "
            "lens face.",
        ),
    )


def subjects() -> dict[str, Subject]:
    """Every camera position sheet's subject, in reading order."""
    out = (_plate_subject(), _arty_subject(), _acorn_subject())
    return {s.key: s for s in out}
