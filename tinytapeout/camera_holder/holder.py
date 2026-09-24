"""A camera holder built on the Tiny Tapeout generic mounting plate.

Hand-written, and derived rather than drawn: every figure below is worked
out at import from three other modules, so that the holder cannot drift away
from what it is built on.

* ``raspberry_pi_camera.optics`` says where the camera has to be: over the
  centre of the frame that holds every demo board revision, at the height
  the lens needs to take it all in -- the plate subject of
  ``RPICAM-OVER-PLATE``, frame A -- for each of the two lenses drawn there,
  the stock 65 degree one and the 120;
* ``tinytapeout.mounting_plate.plate`` says what the holder stands on: the
  plate's outline, its six M4 chassis fixings, and the standoff every board
  stands on;
* the camera module's own data says what the holder carries: its hole
  pattern, where its lens axis is, and how far the lens stands off the
  board.

The shape
---------
A portal: two side frames standing on the plate's left and right edges, and
a beam across the top of them that carries the camera, lens down, over the
frame's centre.  Front and back are open, because that is where every
revision's Pmod hosts and USB-C connectors are; each side frame is a window,
two posts and a rail over a foot, so that the side Pmod positions two
revisions carry on their left edge stay reachable too.  The feet sit over the
plate's own four side fixings and share their M4 screws: no hole is added to
the plate.

Four printed parts, all in this module as boxes -- a side frame (twice,
mirrored), the beam, and a camera carrier between the beam and the camera.
The carrier is its own part so that it can be turned: nobody publishes which
way the OV5647's pixel rows run on the module, and the camera's long image
axis has to lie along the plate's X.  The carrier bolts to the beam on a
square of four holes centred on the lens axis, so it goes on in any of four
quarter turns without moving the axis.

Two lenses, one design
----------------------
The 120 degree lens takes the same frame in from about half the height, so
it gets its own holder rather than a slot in one: :class:`Holder` builds the
design for a lens, and :data:`VARIANTS` holds one per lens.  Everything but
the side frames' posts is shared -- the beam and the carrier are the same two
parts, only lower -- and a fixed height is one a rule can check and nobody
can set wrong, where an adjustable carrier would have to reach across about
70 mm and be set by eye.

Coordinates
-----------
The plate's own: origin at its lower-left corner, X right, Y towards the
back, seen from above, and Z up from the plate's TOP face.  The side frames
are mirror images about the plate's centre line, X = PLATE_W / 2; each
``Part`` is a list of boxes and holes in these coordinates, which is all the
STEP export, the drawing and ``verify.py`` read.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from raspberry_pi_camera import optics
from tinytapeout.mounting_plate.plate import PLATE
from tools.schema import Source

# ---------------------------------------------------------------------------
# What the holder is built on, and what it has to achieve
# ---------------------------------------------------------------------------

PLATE_W = PLATE.outline.width
PLATE_H = PLATE.outline.height
PLATE_T = PLATE.outline.thickness
MIRROR_X = PLATE_W / 2

#: The plate subject of RPICAM-OVER-PLATE, and its frame A: every revision's
#: assembled envelope, plus the margin, made 4:3.
SUBJECT = optics.subjects()["tt-mounting-plate"]
FRAME = SUBJECT.frames()[0]

#: The plane Z is measured from on that sheet, above the plate face: the
#: standoff plus the THICKEST board, since a camera set from the higher
#: plane covers the lower one by more.
BOARD_PLANE = FRAME.target.plane_above_subject

#: Where the lens has to be, in plate coordinates: over frame A's centre,
#: which is the same point whichever lens is fitted.
AXIS_X = FRAME.cx
AXIS_Y = FRAME.cy

#: How much higher than the least the lens face is set.  A print comes out a
#: few tenths off in Z and the parts stack four deep between the plate and
#: the lens, so the face is set a millimetre above the minimum and then
#: rounded up to the whole millimetre: the height a reader can check with a
#: rule.
PRINT_ALLOWANCE = 1.0


# ---------------------------------------------------------------------------
# The camera module
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CameraBoard:
    """What the holder needs to know about the camera it carries.

    In the camera's own board frame (lens side up, per ``tools.schema``), so
    that it is read straight off the camera family's data module.  The
    holder turns it lens down and puts the lens axis over (AXIS_X, AXIS_Y).
    """

    name: str
    width: float
    height: float
    thickness: float
    #: (x, y, diameter) of each mounting hole.
    holes: tuple[tuple[float, float, float], ...]
    lens_axis: tuple[float, float]
    #: The lens stack on the lens side, from the board out: (height its step
    #: reaches above the lens-side face, size across).  The last step's
    #: height is the lens face's.
    lens_profile: tuple[tuple[float, float], ...]
    #: Parts on the LENS side that a screw head there has to miss: (label,
    #: x0, y0, x1, y1, height).
    front_parts: tuple[tuple[str, float, float, float, float, float], ...]
    #: Parts on the FAR face, which the carrier's bosses have to miss:
    #: (label, x0, y0, x1, y1, height below that face).
    back_parts: tuple[tuple[str, float, float, float, float, float], ...]
    #: Which board edge the FFC leaves by, in the board frame.
    ffc_edge: str
    #: How far below the far face the cable leaves the connector, and how
    #: wide it is.
    ffc_cable_z: float
    ffc_cable_width: float
    #: Where the cable crosses the board's edge, along that edge.
    ffc_cable: tuple[float, float]
    #: How far the holes may be from their nominal diameter.
    hole_dia_tol: float
    sources: tuple[Source, ...] = ()

    @property
    def lens_height(self) -> float:
        """Lens face to the board's lens-side face."""
        return self.lens_profile[-1][0]


def camera_board() -> CameraBoard:
    """The Camera Module v1.3, from ``raspberry_pi_camera/v1.py``.

    The stock 65 degree lens is this board's.  Everything a holder needs is
    that module's own figures, with its own error bars: the hole centres to
    HOLE_TOL and their size to HOLE_DIA_TOL, the lens and so its axis to
    LENS_TOL, the connector's length and the cable's crossing to
    SCALED_TOL.
    """
    from raspberry_pi_camera import v1
    x0, y0, x1, y1 = v1.LENS
    side = x1 - x0
    profile = tuple((z, size) for z, size, _ in v1.LENS_PROFILE)
    if abs(profile[0][1] - side) > 1e-9:
        raise SystemExit("v1.LENS_PROFILE's first step is not v1.LENS")
    return CameraBoard(
        name="Raspberry Pi Camera Module v1.3",
        width=v1.BOARD_WIDTH, height=v1.BOARD_HEIGHT,
        thickness=v1.BOARD_THICKNESS,
        holes=tuple((x, y, v1.HOLE_DIA) for x, y in v1.HOLES.values()),
        lens_axis=v1.OPTICAL_AXIS,
        lens_profile=profile,
        front_parts=(("sensor flex and J2", *v1.TAIL, v1.TAIL_TOP_Z),),
        back_parts=(("FFC connector", *v1.FFC,
                     -v1.FFC_BOTTOM_Z - v1.BOARD_THICKNESS),),
        ffc_edge="top",
        ffc_cable_z=-v1.FFC_CABLE_Z - v1.BOARD_THICKNESS,
        ffc_cable_width=v1.FFC_CABLE_WIDTH,
        ffc_cable=v1.FFC_CABLE,
        hole_dia_tol=v1.HOLE_DIA_TOL,
        sources=v1.CM1.sources)


CAMERA = camera_board()


# ---------------------------------------------------------------------------
# Parts, as boxes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Box:
    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float
    what: str = ""

    def mirrored(self) -> "Box":
        return Box(2 * MIRROR_X - self.x1, 2 * MIRROR_X - self.x0,
                   self.y0, self.y1, self.z0, self.z1, self.what)


@dataclass(frozen=True)
class Hole:
    """A vertical hole through a part, and what goes in it.

    A *hex* hole is a nut pocket, *dia* across its flats.
    """

    x: float
    y: float
    dia: float
    z0: float
    z1: float
    what: str = ""
    hex: bool = False

    def mirrored(self) -> "Hole":
        return Hole(2 * MIRROR_X - self.x, self.y, self.dia, self.z0, self.z1,
                    self.what, self.hex)


@dataclass(frozen=True)
class Cyl:
    """A vertical round boss."""

    x: float
    y: float
    dia: float
    z0: float
    z1: float
    what: str = ""


@dataclass(frozen=True)
class Part:
    key: str
    name: str
    boxes: tuple[Box, ...]
    holes: tuple[Hole, ...] = ()
    bosses: tuple[Cyl, ...] = ()
    count: int = 1
    print_note: str = ""

    @property
    def bbox(self) -> Box:
        xs = [b.x0 for b in self.boxes] + [b.x1 for b in self.boxes]
        ys = [b.y0 for b in self.boxes] + [b.y1 for b in self.boxes]
        zs = [b.z0 for b in self.boxes] + [b.z1 for b in self.boxes]
        for c in self.bosses:
            xs += [c.x - c.dia / 2, c.x + c.dia / 2]
            ys += [c.y - c.dia / 2, c.y + c.dia / 2]
            zs += [c.z0, c.z1]
        return Box(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


# --- Fasteners -------------------------------------------------------------

#: ISO 7380 M4 button head: the head is low, which is what lets it sit under
#: a side Pmod body standing on a board that overhangs it.
M4_HEAD_DIA = 7.6
M4_HEAD_H = 2.2
M4_CLEAR = 4.5                  # printed: a drill's 4.3 closes up in a print
M3_CLEAR = 3.4
M3_HEAD_DIA = 5.5               # ISO 4762
M3_NUT_AF = 5.5                 # ISO 4032
M2_CLEAR = 2.4
M2_HEAD_DIA = 3.8               # ISO 4762
M2_NUT_AF = 4.0

# --- The side frame --------------------------------------------------------

#: Where the plate's own fixings along its left edge are, which the left
#: foot sits over: the plate fixings nearest that edge.  The right foot's are
#: their mirror images, which verify.py checks the plate really has.
_PLATE_FIXINGS = [(h.x, h.y) for h in PLATE.holes if h.kind == "plate"]
FIXINGS = tuple(sorted(
    (x, y) for x, y in _PLATE_FIXINGS
    if abs(x - min(px for px, _ in _PLATE_FIXINGS)) < 1e-9))

#: Thickness of every member of a side frame across the plate: a post, the
#: rail and the wall they stand in, 10 mm; a post is POST_LEN, 8 mm, front to
#: back, which about halves its stiffness that way.  An estimate, not a
#: check: a 10 mm square PETG post, E about 2 GPa, is about 1.5 N/mm stiff as
#: a 150 mm cantilever,
#: so the four together about 6 N/mm before the feet give -- a finger's push
#: moves the camera by a millimetre or so, and a camera weighing a few grams
#: does not move it at all.  The weak point is the foot at the plate's edge,
#: which the posts' bending goes through across the print layers.
MEMBER = 10.0

#: The inner face of the side frame's wall, from the plate's own edge.
#: Two revisions carry three side Pmod positions on their left edge, not
#: fitted, whose connector bodies stand 2.50 mm in from the plate's edge on
#: the board; a peripheral in one of them would come out through the wall.
#: 1.0 mm clear of that.  verify.py checks it against the board data.
WALL_INNER = 1.5
WALL_OUTER = WALL_INNER - MEMBER

#: The foot: a flange along the plate's edge, as thick as it can be and
#: still pass under a side Pmod body with a button head on it.
FOOT_T = 5.0
#: How far in the foot reaches: the M4 head's own radius past the fixing,
#: and a millimetre.
FOOT_INNER = max(x for x, _ in FIXINGS) + M4_HEAD_DIA / 2 + 1.0

#: The frame's length along the plate edge, and its two posts, one at each
#: end.  Between them is the window the side Pmods reach through.
FRAME_Y0 = 1.0
FRAME_Y1 = 93.0
POST_LEN = 8.0

# --- The camera stack, lens face up to the beam ----------------------------

#: The carrier's bosses stand the camera off the carrier far enough to clear
#: the tallest part on the camera's far face, and the FFC leaves under the
#: carrier in that same gap.
BOSS_DIA = 5.0
BOSS_CLEAR = 1.0
BOSS_H = max(h for *_, h in CAMERA.back_parts) + BOSS_CLEAR
CARRIER_T = 6.0
#: The camera's M2 nuts sit in hex pockets in the carrier's top face, deep
#: enough for the nut and the screw's end below the face the beam's pad
#: bears on.
M2_POCKET_AF = 4.3
M2_POCKET_DEPTH = 3.5
#: The carrier and the pad under the beam are this square, centred on the
#: lens axis, with a fixing near each corner.  The corners have to be
#: outside the camera board however it is turned, which is its lens axis's
#: furthest distance from any of its edges; the fixings are half a nut
#: across corners and a millimetre past that.
_REACH = max(CAMERA.lens_axis[0], CAMERA.width - CAMERA.lens_axis[0],
             CAMERA.lens_axis[1], CAMERA.height - CAMERA.lens_axis[1])
CARRIER_FIX = math.ceil(2 * (_REACH + M3_NUT_AF / math.sqrt(3) + 1.0)) / 2
CARRIER_HALF = CARRIER_FIX + 4.0
BEAM_T = 6.0
BEAM_W = 16.0

#: The beam's M3 fixings into each rail: two, across the beam.
BEAM_FIX_DY = BEAM_W / 4

#: Which way the camera is turned on the carrier, in quarter turns from its
#: board X along the plate's X.  ASSUMED 0: that the OV5647's long image axis
#: lies along the board's 25 mm width, with the connector edge at the back.
#: Nobody publishes it; the carrier is square so that it can be changed.
QUARTER_TURNS = 0


def camera_to_plate(u: float, v: float, turns: int = QUARTER_TURNS):
    """A point of the camera board, lens side up, to plate X and Y.

    The board is turned lens DOWN to hang under the carrier, which mirrors
    it: seen from above, a point at board (u, v) is at (-du, dv) from the
    lens axis.  Then the carrier's quarter turns.
    """
    du = u - CAMERA.lens_axis[0]
    dv = v - CAMERA.lens_axis[1]
    x, y = -du, dv
    for _ in range(turns % 4):
        x, y = -y, x
    return AXIS_X + x, AXIS_Y + y


#: Nut heights, ISO 4032, and the M4 washer, ISO 7089.
NUT_H = {"M2": 1.6, "M3": 2.4, "M4": 3.2}
#: Coarse pitches, ISO 261: a screw is long enough when two of them stand
#: past its nut.
PITCH = {"M2": 0.4, "M3": 0.5, "M4": 0.7}
M4_WASHER_T = 0.8

#: Screw lengths that are made, ISO 4762 and ISO 7380 alike, to 30 mm.
LENGTHS = (4, 5, 6, 8, 10, 12, 16, 20, 25, 30)


def screw_length(grip: float, nut: float, pitch: float) -> int:
    """The shortest length made that passes *grip*, a whole nut and two
    threads past it."""
    return next(n for n in LENGTHS if n >= grip + nut + 2 * pitch)


#: What each screw passes through, as (thread, grip, washer).
GRIPS = {
    "plate": ("M4", FOOT_T + PLATE_T, M4_WASHER_T),
    "beam": ("M3", BEAM_T + MEMBER, 0.0),
    "carrier": ("M3", BEAM_T + CARRIER_T, 0.0),
    "camera": ("M2", CAMERA.thickness + BOSS_H + CARRIER_T - M2_POCKET_DEPTH,
               0.0),
}


def _screw(key: str) -> int:
    thread, grip, washer = GRIPS[key]
    return screw_length(grip + washer, NUT_H[thread], PITCH[thread])


def _carrier_fixings(z0: float, z1: float) -> tuple[Hole, ...]:
    return tuple(Hole(AXIS_X + sx * CARRIER_FIX, AXIS_Y + sy * CARRIER_FIX,
                      M3_CLEAR, z0, z1, "M3 carrier fixing")
                 for sx in (-1, 1) for sy in (-1, 1))


def camera_holes(turns: int = QUARTER_TURNS):
    """The camera's mounting holes in plate X and Y, and their diameters."""
    return tuple((*camera_to_plate(u, v, turns), d)
                 for u, v, d in CAMERA.holes)


def _plate_box(u0, v0, u1, v1, z0, z1, what) -> Box:
    """A rectangle of the camera board, as a box in plate coordinates."""
    xs, ys = zip(*(camera_to_plate(u, v) for u, v in
                   ((u0, v0), (u1, v0), (u0, v1), (u1, v1))))
    return Box(min(xs), max(xs), min(ys), max(ys), z0, z1, what)


def _mirror(part: Part) -> Part:
    return Part(part.key + "-right", part.name + ", right",
                tuple(b.mirrored() for b in part.boxes),
                tuple(h.mirrored() for h in part.holes), part.bosses,
                count=1, print_note=part.print_note)


#: What the holder is bolted together with.
FASTENERS = (
    (f"M4 x {_screw('plate')} button head, ISO 7380, washer and nut", 4,
     "Foot to plate, through the plate's own side fixings; where the plate "
     f"is on a chassis, {FOOT_T:g} mm longer than the plate's own screws."),
    (f"M3 x {_screw('beam')} socket head, ISO 4762, and nut", 4,
     "Beam to the side frames' rails."),
    (f"M3 x {_screw('carrier')} socket head, ISO 4762, and nut", 4,
     "Carrier to the beam's pad."),
    (f"M2 x {_screw('camera')} socket head, ISO 4762, and nut", 4,
     "Camera to the carrier, head on the lens side."),
)


def _sources(lens) -> tuple[Source, ...]:
    """What the holder for *lens* is built from."""
    return (
        Source(label="Where the camera goes",
               ref="raspberry_pi_camera/optics.py",
               note=f"The plate subject's frame A and the {lens.short} deg "
                    "lens: RPICAM-OVER-PLATE."),
        Source(label="What it stands on",
               ref="tinytapeout/mounting_plate/plate.py",
               note="Outline, side fixings, standoff; TT-MP-PLATE."),
        Source(label="What it carries",
               ref="raspberry_pi_camera/v1.py",
               note="The Camera Module v1.3: Gert van Loo's hand-measured "
                    "sheet of 21 May 2013, checked against Raspberry Pi "
                    "Spy's calipers."),
    )


# ---------------------------------------------------------------------------
# The holder, for one lens
# ---------------------------------------------------------------------------


class Holder:
    """The holder built for one lens: everything that depends on its height.

    Two lenses, two heights, one design.  The lens face goes at the height
    ``RPICAM-OVER-PLATE`` gives for the lens over frame A, and the stack
    above it -- camera, bosses, carrier, beam -- is the same for both, so
    the beam and the carrier are the same two parts in both holders, only
    higher or lower; the side frames are the one part that changes, and
    only in how long their posts are.

    Every other attribute is the module's own: a holder answers for the
    fasteners, the camera and the plate as the module does, so code that
    reads a holder reads it as it would read the module.
    """

    def __init__(self, lens_key: str):
        self.KEY = lens_key
        self.LENS = optics.LENSES[lens_key]
        self.REQUIRED = optics.place(FRAME, self.LENS)
        self.LENS_FACE_MIN = BOARD_PLANE + self.REQUIRED.z
        self.LENS_FACE_Z = math.ceil(self.LENS_FACE_MIN + PRINT_ALLOWANCE)
        self.LENS_FACE = self.LENS_FACE_Z
        self.PCB_FRONT = self.LENS_FACE + CAMERA.lens_height
        self.PCB_BACK = self.PCB_FRONT + CAMERA.thickness
        self.CARRIER_Z0 = self.PCB_BACK + BOSS_H
        self.CARRIER_Z1 = self.CARRIER_Z0 + CARRIER_T
        self.RAIL_Z1 = self.CARRIER_Z1        # the beam sits on the rails
        self.RAIL_Z0 = self.RAIL_Z1 - MEMBER
        self.BEAM_Z0, self.BEAM_Z1 = self.RAIL_Z1, self.RAIL_Z1 + BEAM_T
        self.SIDE_LEFT = self._side_frame()
        self.SIDE_RIGHT = _mirror(self.SIDE_LEFT)
        self.BEAM = self._beam()
        self.CARRIER = self._carrier()
        # The printed parts, as they are assembled.  The side frame is one
        # part printed twice; the right-hand one is its mirror image, so the
        # STEP gives the assembly both and the parts list counts it once,
        # twice over.
        self.ASSEMBLY = (self.SIDE_LEFT, self.SIDE_RIGHT, self.BEAM,
                         self.CARRIER)
        self.PARTS = (self.SIDE_LEFT, self.BEAM, self.CARRIER)
        self.SOURCES = _sources(self.LENS)

    def __getattr__(self, name):
        try:
            return globals()[name]
        except KeyError:
            raise AttributeError(name) from None

    def turned_wrong(self) -> float:
        """What the picture misses off each end of frame A's long side if the
        camera is a quarter turn out: its short side lies along it instead."""
        long_side = max(FRAME.width, FRAME.height)
        covers = 2 * (self.LENS_FACE - BOARD_PLANE) * math.tan(
            math.radians(self.LENS.fov_v / 2))
        return (long_side - covers) / 2

    def _side_frame(self) -> Part:
        boxes = (
            Box(WALL_OUTER, FOOT_INNER, FRAME_Y0, FRAME_Y1, 0.0, FOOT_T,
                "foot"),
            Box(WALL_OUTER, WALL_INNER, FRAME_Y0, FRAME_Y0 + POST_LEN, FOOT_T,
                self.RAIL_Z0, "front post"),
            Box(WALL_OUTER, WALL_INNER, FRAME_Y1 - POST_LEN, FRAME_Y1, FOOT_T,
                self.RAIL_Z0, "back post"),
            Box(WALL_OUTER, WALL_INNER, FRAME_Y0, FRAME_Y1, self.RAIL_Z0,
                self.RAIL_Z1, "rail"),
        )
        xr = (WALL_OUTER + WALL_INNER) / 2
        holes = tuple(Hole(x, y, M4_CLEAR, 0.0, FOOT_T, "M4 plate fixing")
                      for x, y in FIXINGS)
        holes += tuple(Hole(xr, AXIS_Y + s * BEAM_FIX_DY, M3_CLEAR,
                            self.RAIL_Z0, self.RAIL_Z1, "M3 beam fixing")
                       for s in (-1, 1))
        return Part("side", "Side frame", boxes, holes, count=2,
                    print_note="Print on its outer face: the foot stands "
                               "up from the bed, and nothing overhangs. Its "
                               "holes print lying down, so ream them to "
                               "size.")

    def _beam(self) -> Part:
        x0 = WALL_OUTER
        x1 = 2 * MIRROR_X - WALL_OUTER
        boxes = (
            Box(x0, x1, AXIS_Y - BEAM_W / 2, AXIS_Y + BEAM_W / 2,
                self.BEAM_Z0, self.BEAM_Z1, "beam"),
            Box(AXIS_X - CARRIER_HALF, AXIS_X + CARRIER_HALF,
                AXIS_Y - CARRIER_HALF, AXIS_Y + CARRIER_HALF, self.BEAM_Z0,
                self.BEAM_Z1, "pad"),
        )
        xr = (WALL_OUTER + WALL_INNER) / 2
        holes = tuple(Hole(x, AXIS_Y + s * BEAM_FIX_DY, M3_CLEAR, self.BEAM_Z0,
                           self.BEAM_Z1, "M3 beam fixing")
                      for x in (xr, 2 * MIRROR_X - xr) for s in (-1, 1))
        holes += _carrier_fixings(self.BEAM_Z0, self.BEAM_Z1)
        return Part("beam", "Beam", boxes, holes,
                    print_note="Print flat, on its top face.")

    def camera_boxes(self) -> tuple[Box, ...]:
        """The camera module itself, as it hangs: board, lens, far face parts.

        Not printed, and not in the STEP: a bought part, drawn on the sheet
        from its own data so that the lens face the heights are set from is
        the lens face the camera actually has.
        """
        out = [_plate_box(0.0, 0.0, CAMERA.width, CAMERA.height,
                          self.PCB_FRONT, self.PCB_BACK, "camera board")]
        below = 0.0
        u, v = CAMERA.lens_axis
        for z, size in CAMERA.lens_profile:
            out.append(_plate_box(u - size / 2, v - size / 2, u + size / 2,
                                  v + size / 2, self.PCB_FRONT - z,
                                  self.PCB_FRONT - below, "lens"))
            below = z
        out += [_plate_box(x0, y0, x1, y1, self.PCB_FRONT - h,
                           self.PCB_FRONT, label)
                for label, x0, y0, x1, y1, h in CAMERA.front_parts]
        out += [_plate_box(x0, y0, x1, y1, self.PCB_BACK,
                           self.PCB_BACK + h, label)
                for label, x0, y0, x1, y1, h in CAMERA.back_parts]
        return tuple(out)

    def _carrier(self) -> Part:
        boxes = (Box(AXIS_X - CARRIER_HALF, AXIS_X + CARRIER_HALF,
                     AXIS_Y - CARRIER_HALF, AXIS_Y + CARRIER_HALF,
                     self.CARRIER_Z0, self.CARRIER_Z1, "carrier"),)
        bosses = tuple(Cyl(x, y, BOSS_DIA, self.PCB_BACK, self.CARRIER_Z0,
                           "boss") for x, y, _ in camera_holes())
        holes = tuple(Hole(x, y, M2_CLEAR, self.PCB_BACK, self.CARRIER_Z1,
                           "M2 camera fixing") for x, y, _ in camera_holes())
        holes += tuple(Hole(x, y, M2_POCKET_AF,
                            self.CARRIER_Z1 - M2_POCKET_DEPTH,
                            self.CARRIER_Z1, "M2 nut pocket", hex=True)
                       for x, y, _ in camera_holes())
        holes += _carrier_fixings(self.CARRIER_Z0, self.CARRIER_Z1)
        return Part("carrier", "Camera carrier", boxes, holes, bosses,
                    print_note="Print on its top face, bosses up; the nut "
                               "pockets open onto the bed.")


#: One holder per drawn lens, by lens key.  Both carry the same camera over
#: the same point; they differ in height.
VARIANTS = {key: Holder(key) for key in optics.LENSES}
