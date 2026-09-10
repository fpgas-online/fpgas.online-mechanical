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
    cares about pin 1.  ``row_edge_offset`` is the distance from the board edge
    the header faces to the nearer pin row.
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
        ("arc",  x1, y1, xm, ym, x2, y2)      # start, mid, end

    in the board frame.  A renderer should prefer ``edges`` when present.
    """

    width: float
    height: float
    corner_radius: float = 0.0
    edges: tuple[tuple, ...] = ()
    thickness: float | None = None      # bare PCB thickness
    z_height: float | None = None       # overall height of a packaged item
    profile_note: str = ""


@dataclass(frozen=True)
class BoardSpec:
    """One mechanical drawing's worth of data."""

    key: str
    title: str
    subtitle: str
    family: str
    outline: Outline
    holes: tuple[Hole, ...] = ()
    features: tuple[Feature, ...] = ()
    pmods: tuple[PmodHeader, ...] = ()
    sources: tuple[Source, ...] = ()
    notes: tuple[str, ...] = ()
    used_by: tuple[str, ...] = ()
    front_edge: str = "bottom"
    #: "pcb" for a bare board drawn in plan only, "enclosure" for a packaged
    #: item that also gets a side elevation.
    body: str = "pcb"

    def of_kind(self, *kinds: str) -> tuple[Feature, ...]:
        return tuple(f for f in self.features if f.kind in kinds)


# Fabrication tolerances quoted on the drawings.  These are the usual PCB house
# figures, not a per-board measurement, and are stated as such on every sheet.
PCB_OUTLINE_TOL = 0.20      # mm, routed board edge
PCB_HOLE_POS_TOL = 0.10     # mm, drilled hole position
PCB_HOLE_DIA_TOL = 0.08     # mm, plated hole diameter
