"""Shared data types for the board mechanical database.

Everything in :mod:`data` is plain, frozen dataclasses so that a board
definition can be read, diffed and reviewed as ordinary Python.

Coordinate convention
---------------------
Every board uses a right-handed 2D frame, viewed from the **component side**
(top view):

* origin at the lower-left corner of the board's bounding box,
* X increases to the right,
* Y increases upwards,
* all lengths in millimetres.

For the Tiny Tapeout demo boards the Pmod headers are along the lower edge, so
"front of the board" is Y = 0.  For the Raspberry Pi boards the 40-pin GPIO
header is along the upper edge, matching how Raspberry Pi Ltd draw them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Source:
    """Where a set of numbers came from."""

    label: str
    ref: str                      # URL, or repo path plus commit
    note: str = ""


#: Separates the revisions in a feature's provenance label, as in
#: "DB mpw:MT3|DB ETR v3.2:MT1".  It was "+", until the board IDs became the
#: revision names and two of them -- "DB 4+" and "DB 06+" -- ended in the
#: separator, so a label split into pieces that named no revision at all.
#: A colon separates the revision from that board's own hole name, so neither
#: character may appear in a revision name.
LABEL_SEP = "|"


@dataclass(frozen=True)
class Hole:
    """A circular hole.

    ``dia`` is the finished hole diameter.  ``keepout_dia`` is the diameter of
    the surrounding area that must stay clear of anything but the fastener,
    where the source specifies one.
    """

    x: float
    y: float
    dia: float
    label: str = ""
    kind: str = "mount"           # "mount", "aux"
    keepout_dia: float | None = None
    tol: float | None = None


@dataclass(frozen=True)
class Slot:
    """An obround slot: a rectangle of width *width* with semicircular ends.

    Used where two board revisions want a fastener at positions too close
    together to drill as separate holes but too far apart to merge into one.
    """

    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    label: str = ""
    note: str = ""

    @property
    def length(self) -> float:
        return ((self.x1 - self.x0) ** 2 + (self.y1 - self.y0) ** 2) ** 0.5 + self.width


@dataclass(frozen=True)
class Feature:
    """A rectangular component footprint, given as a bounding box.

    ``kind`` drives how the drawing renders it and which features a given sheet
    chooses to dimension.  Known kinds:

    ``pmod``        a Pmod host header
    ``usb_power``   the connector normally used to power the board
    ``usb_a``       a USB type A host port
    ``ethernet``    an RJ45 jack
    ``display7``    a seven-segment display
    ``led``         an indicator LED
    ``switch``      a switch or DIP switch block
    ``header``      any other pin header
    ``connector``   any other connector
    ``lens``        a lens and sensor module; its centre is the optical axis
    ``outline``     an informational body outline, not dimensioned
    """

    key: str
    label: str
    kind: str
    x0: float
    y0: float
    x1: float
    y1: float
    note: str = ""
    tol: float | None = None
    designator: str = ""
    #: "top" for a part on the component side, "bottom" for one on the far
    #: side, which the drawing shows as hidden detail.  The Raspmod's
    #: clock/reset pins are on its underside, where the demoboard is.
    side: str = "top"
    #: The number this feature carries in the schedule and on its balloon.
    #: Fixed per family rather than counted off, so a given number means the
    #: same part on every sheet of that family; a revision that does not carry
    #: the part leaves its number unused.  None falls back to position.
    number: int | None = None
    #: Height above the seating plane, for a feature that also shows in an end
    #: view: the lower and upper edge of its aperture.  Only the enclosure
    #: sheets use these, and only for a feature in an end face.  Left None on a
    #: bare board, where the plan view says everything.
    z0: float | None = None
    z1: float | None = None
    #: Pin 1 of a header or connector whose orientation matters, where the
    #: drawing marks it with a dot.  None for a part drawn by its body alone.
    pin1: tuple[float, float] | None = None
    #: A pin header's field, (columns, rows) on ``pitch``, centred in the
    #: box, which the drawing then shows pin by pin as it shows a Pmod
    #: host's.  The columns run along the box's longer side.  None for a
    #: part that is its body alone.
    pins: tuple[int, int] | None = None
    pitch: float = 2.54

    def __post_init__(self) -> None:
        # A pin field is drawn centred in the box, so a box that is not
        # centred on the pins draws them in the wrong place; pin 1, given
        # from the part's own data, has to land on one of them.
        if self.pins is not None and self.pin1 is not None:
            near = min(math.dist(self.pin1, p) for p in self.pin_centres())
            if near > 0.05:
                raise ValueError(
                    f"{self.key}: pin 1 at {self.pin1} is {near:.2f} mm from the "
                    f"nearest pin of a {self.pins[0]}x{self.pins[1]} field centred "
                    f"in its box ({self.x0}, {self.y0})-({self.x1}, {self.y1})")

    def pin_centres(self) -> list[tuple[float, float]]:
        """Every pin of the field, or nothing for a part without one."""
        if self.pins is None:
            return []
        cols, rows = self.pins
        along_x = self.width >= self.height
        n_x, n_y = (cols, rows) if along_x else (rows, cols)
        x0 = self.cx - (n_x - 1) / 2 * self.pitch
        y0 = self.cy - (n_y - 1) / 2 * self.pitch
        return [(round(x0 + i * self.pitch, 3), round(y0 + j * self.pitch, 3))
                for j in range(n_y) for i in range(n_x)]

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


@dataclass(frozen=True)
class PmodHeader:
    """A 2x6 Pmod host header.

    Positions are given as the centre of the pin field, plus the position of
    pin 1, because a mounting plate cares about the pin field while a pinout
    cares about pin 1.  ``edge`` says which board edge the host faces, which
    fixes the axis the six columns run along.
    """

    key: str
    label: str
    designator: str
    cx: float
    cy: float
    pin1_x: float
    pin1_y: float
    pitch: float = 2.54
    columns: int = 6
    rows: int = 2
    #: Board edge the host faces: "bottom", "top", "left" or "right".  The six
    #: columns run parallel to that edge and the two rows perpendicular to it.
    #: A vertical header faces no edge; it takes the edge whose axis its
    #: columns run along, and the sheet says so.
    edge: str = "bottom"
    #: "host" for a socket a peripheral plugs into, which is every header on
    #: every board until the Raspmod; "plug" for a peripheral-side pin header
    #: that goes into someone else's host.  The Raspmod carries three of each,
    #: one row above the other, and a drawing that treated the plugs as hosts
    #: dimensioned a 0.05 mm spacing between the two rows and called the
    #: plugs hosts in the table.
    role: str = "host"
    body_x0: float = 0.0
    body_y0: float = 0.0
    body_x1: float = 0.0
    body_y1: float = 0.0

    @property
    def pin_span(self) -> float:
        return (self.columns - 1) * self.pitch

    @property
    def row_span(self) -> float:
        return (self.rows - 1) * self.pitch


@dataclass(frozen=True)
class Outline:
    """Board outline.

    ``width``, ``height`` and ``corner_radius`` describe the rounded rectangle
    that every board here is based on.  ``edges`` carries the exact profile
    when there is more than that -- the TT04/TT05 board, for instance, has a
    shallow recess in its upper edge for the USB-C shell, contributed by the
    connector footprint rather than by the board-level edge cuts.

    Each entry in ``edges`` is either::

        ("line", x1, y1, x2, y2)
        ("arc",  x1, y1, x2, y2, radius, large_arc, ccw)

    in the board frame.  An arc is resolved at extraction rather than carried
    as a mid point, because a renderer emitting an SVG arc needs the radius
    and the two flags and cannot recover them from three points without
    repeating the same arithmetic.  ``large_arc`` and ``ccw`` are 1 or 0 and
    are given in the board frame, ``ccw`` being 1 for a counter-clockwise
    sweep; the canvas inverts the sweep flag when it flips Y.  A renderer
    should prefer ``edges`` when present.
    """

    width: float
    height: float
    corner_radius: float = 0.0
    edges: tuple[tuple, ...] = ()
    thickness: float | None = None      # bare PCB thickness
    z_height: float | None = None       # overall height of a packaged item
    profile_note: str = ""
    #: True for a body of constant cross-section, such as an extrusion, whose
    #: corner radii belong to that section and so appear in the end view only.
    #: A moulded or clamshell case is rounded in plan as well, and its plan
    #: view has to show it.
    constant_section: bool = False

    def extent(self) -> tuple[float, float, float, float]:
        """x0, y0, x1, y1 of the profile: the exact edges' when there are any.

        Every outline without ``edges`` starts at the origin, so its extent is
        its width and height.  One with them may not: a part moved onto
        another board's frame (``moved``) carries its profile as edges
        wherever it has been put.
        """
        if not self.edges:
            return 0.0, 0.0, self.width, self.height
        xs = [v for e in self.edges for v in (e[1], e[3])]
        ys = [v for e in self.edges for v in (e[2], e[4])]
        return min(xs), min(ys), max(xs), max(ys)


def rounded_rect(x0: float, y0: float, w: float, h: float,
                 r: float) -> tuple[tuple, ...]:
    """A rounded rectangle as ``Outline.edges``, counter-clockwise."""
    x1, y1 = x0 + w, y0 + h
    if r <= 0:
        return (("line", x0, y0, x1, y0), ("line", x1, y0, x1, y1),
                ("line", x1, y1, x0, y1), ("line", x0, y1, x0, y0))
    return (("line", x0 + r, y0, x1 - r, y0),
            ("arc", x1 - r, y0, x1, y0 + r, r, 0, 1),
            ("line", x1, y0 + r, x1, y1 - r),
            ("arc", x1, y1 - r, x1 - r, y1, r, 0, 1),
            ("line", x1 - r, y1, x0 + r, y1),
            ("arc", x0 + r, y1, x0, y1 - r, r, 0, 1),
            ("line", x0, y1 - r, x0, y0 + r),
            ("arc", x0, y0 + r, x0 + r, y0, r, 0, 1))


@dataclass(frozen=True)
class BoardSpec:
    """One mechanical drawing's worth of data."""

    key: str
    title: str
    subtitle: str
    family: str
    outline: Outline
    holes: tuple[Hole, ...] = ()
    slots: tuple[Slot, ...] = ()
    features: tuple[Feature, ...] = ()
    pmods: tuple[PmodHeader, ...] = ()
    sources: tuple[Source, ...] = ()
    notes: tuple[str, ...] = ()
    used_by: tuple[str, ...] = ()
    #: The products this board ships inside, from the Kit table of Tiny
    #: Tapeout's board revision spreadsheet.  Not the same as ``used_by``,
    #: which names shuttles: one board can carry two kits for one shuttle
    #: (TT08's QFN and CoB editions), and one kit need not be a shuttle at all
    #: (the FPGA Dev Kit puts a FabricFox FPGA where the ASIC would go).
    kits: tuple[str, ...] = ()
    front_edge: str = "bottom"
    #: "pcb" for a bare board drawn in plan only, "enclosure" for a packaged
    #: item that also gets a side elevation.
    body: str = "pcb"
    #: Overrides the sheet's default general tolerance, for a part whose source
    #: does not support the usual figures.
    tolerance: str = ""
    #: Replaces the sheet's computed "assembled envelope" note.  That note is
    #: built from the features alone, and features do not include the Pmod
    #: hosts, which have a table of their own; on a board whose host bodies
    #: stand outside the outline the computed figure is therefore short by the
    #: overhang.  Widening the computation is the real fix and moves seven
    #: already-issued sheets, so a board that the figure gets badly wrong
    #: states its own, worked out by its extractor from the same data.
    envelope_note: str = ""
    #: What the feature schedule's extents are extents OF, when that is not
    #: the component body.  Every board drawn from a board file or a model
    #: gives a body, and a column headed "X EXTENT mm" over one is
    #: unambiguous.  The Ultra96-V2 is read from a plot that draws no bodies
    #: at all, so its figures are pad extents, and a table headed the same as
    #: everyone else's invites an aperture to be cut to a connector's pads.
    #: It goes in the table's own heading rather than in the column heads,
    #: which are too narrow to take another word: "X PAD EXTENT mm" and
    #: "Y PAD EXTENT mm" came out 0.08 mm apart and check_sheets read them as
    #: one word.
    extent_of: str = ""

    def of_kind(self, *kinds: str) -> tuple[Feature, ...]:
        return tuple(f for f in self.features if f.kind in kinds)


# Fabrication tolerances quoted on the drawings.  These are the usual PCB house
# figures, not a per-board measurement, and are stated as such on every sheet.
PCB_OUTLINE_TOL = 0.20      # mm, routed board edge
PCB_HOLE_POS_TOL = 0.10     # mm, drilled hole position
PCB_HOLE_DIA_TOL = 0.08     # mm, plated hole diameter


def turned(spec: BoardSpec, cx: float, cy: float) -> BoardSpec:
    """*spec* turned a half turn about (cx, cy): every (x, y) to (2cx-x, 2cy-y).

    For a board drawn under another that sits on it the other way round:
    an adapter on a Raspberry Pi's header, pin 1 on pin 1, lies a half turn
    to the Pi, so the Pi in the adapter's frame is the Pi turned about the
    midpoint of the two pins 1.  A half turn keeps an arc's sweep, so the
    outline's edges only move; a mirror would not, and there is none here.
    The edges a Pmod faces swap, bottom with top and left with right.
    """
    o = spec.outline
    x0, y0, x1, y1 = o.extent()
    edges = o.edges or rounded_rect(x0, y0, x1 - x0, y1 - y0, o.corner_radius)

    def t(x, y):
        return (round(2 * cx - x, 3), round(2 * cy - y, 3))

    def turn_edge(e):
        (ax, ay), (bx, by) = t(e[1], e[2]), t(e[3], e[4])
        return (e[0], ax, ay, bx, by) + tuple(e[5:])

    def box(bx0, by0, bx1, by1):
        (ax, ay), (bx_, by_) = t(bx0, by0), t(bx1, by1)
        return min(ax, bx_), min(ay, by_), max(ax, bx_), max(ay, by_)

    across = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
    features = []
    for f in spec.features:
        fx0, fy0, fx1, fy1 = box(f.x0, f.y0, f.x1, f.y1)
        features.append(replace(f, x0=fx0, y0=fy0, x1=fx1, y1=fy1,
                                pin1=t(*f.pin1) if f.pin1 else None))
    pmods = []
    for p in spec.pmods:
        fields = dict(zip(("cx", "cy"), t(p.cx, p.cy)))
        fields.update(zip(("pin1_x", "pin1_y"), t(p.pin1_x, p.pin1_y)))
        fields["edge"] = across[p.edge]
        if p.body_x1 > p.body_x0:
            fields.update(zip(("body_x0", "body_y0", "body_x1", "body_y1"),
                              box(p.body_x0, p.body_y0, p.body_x1, p.body_y1)))
        pmods.append(replace(p, **fields))
    return replace(
        spec,
        outline=replace(o, edges=tuple(turn_edge(e) for e in edges)),
        holes=tuple(replace(h, **dict(zip(("x", "y"), t(h.x, h.y)))) for h in spec.holes),
        slots=tuple(replace(s, **dict(zip(("x0", "y0", "x1", "y1"), box(s.x0, s.y0, s.x1, s.y1))))
                    for s in spec.slots),
        features=tuple(features),
        pmods=tuple(pmods),
    )


def moved(spec: BoardSpec, dx: float, dy: float) -> BoardSpec:
    """*spec* with every coordinate in it moved by (dx, dy).

    For a part drawn over another board whose frame is not its own: the Pmod
    HAT Adapter is specified in a Raspberry Pi's frame, and fitted to a board
    whose 40-pin header is somewhere else it has to go with the header.  A
    rounded-rectangle outline becomes explicit edges, since an outline
    without them is always drawn from the origin.
    """
    o = spec.outline
    x0, y0, x1, y1 = o.extent()
    edges = o.edges or rounded_rect(x0, y0, x1 - x0, y1 - y0, o.corner_radius)

    def shift(e):
        return (e[0], e[1] + dx, e[2] + dy, e[3] + dx, e[4] + dy) + tuple(e[5:])
    return replace(
        spec,
        outline=replace(o, edges=tuple(shift(e) for e in edges)),
        holes=tuple(replace(h, x=h.x + dx, y=h.y + dy) for h in spec.holes),
        slots=tuple(replace(s, x0=s.x0 + dx, y0=s.y0 + dy, x1=s.x1 + dx,
                            y1=s.y1 + dy) for s in spec.slots),
        features=tuple(replace(f, x0=f.x0 + dx, y0=f.y0 + dy, x1=f.x1 + dx,
                               y1=f.y1 + dy,
                               pin1=((round(f.pin1[0] + dx, 3), round(f.pin1[1] + dy, 3))
                                     if f.pin1 else None))
                       for f in spec.features),
        pmods=tuple(replace(p, cx=p.cx + dx, cy=p.cy + dy, pin1_x=p.pin1_x + dx,
                            pin1_y=p.pin1_y + dy,
                            **({"body_x0": p.body_x0 + dx, "body_y0": p.body_y0 + dy,
                                "body_x1": p.body_x1 + dx, "body_y1": p.body_y1 + dy}
                               if p.body_x1 > p.body_x0 else {}))
                    for p in spec.pmods),
    )
