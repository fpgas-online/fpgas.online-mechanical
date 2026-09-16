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

from dataclasses import dataclass, field


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
