"""What a base plate is made of, for the generator, the sheet and the check.

A base plate carries a Raspberry Pi and an FPGA board joined by the direct
Raspmod, at the heights that put the adapter's plugs into the FPGA board's
Pmod hosts.  The plate itself is a ``BoardSpec``: an outline and a hole
table.  Everything that stands on it is a list of boxes in the plate's own
frame -- the boards, the connectors, the standoffs, the cups -- which is
all the plan, the elevation and ``verify.py`` need, and one list they
cannot disagree about.

Coordinates: origin at the plate's lower-left corner, X right, Y away from
the viewer, seen from above; Z up from the plate's top face, millimetres.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.schema import BoardSpec, Source


@dataclass(frozen=True)
class Box:
    """One thing standing on the plate, as the space it occupies.

    ``kind`` says how it is drawn and what it is to the check:

    * ``adjacent`` -- a bought board or part, in phantom;
    * ``header`` -- a connector body the stack is worked out through, in
      phantom, and its ``rows`` are the pin rows' heights above the plate;
    * ``standoff`` -- a bought spacer, in phantom;
    * ``made`` -- a part this sheet has made, in full line;
    * ``alt`` -- the same, at the plate's other position, dashed.
    """

    kind: str
    label: str
    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float
    #: The pin rows of a connector, as heights above the plate, or nothing.
    rows: tuple[float, ...] = ()
    #: Which of the plate's positions this belongs to, where a plate has two.
    position: str = ""

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass(frozen=True)
class Standoff:
    """A row of the fastener table: how many of what, holding which part."""

    qty: int
    what: str
    holds: str


@dataclass(frozen=True)
class Plate:
    key: str
    title: str
    subtitle: str
    #: The plate: outline, holes, notes and sources.
    spec: BoardSpec
    boxes: tuple[Box, ...]
    standoffs: tuple[Standoff, ...]
    #: Named heights above the plate's top face, in the order the table
    #: reads them, (name, Z).
    levels: tuple[tuple[str, float], ...]
    #: How far the plug rows sit above the host rows once everything is
    #: bought and stacked: positive is high.
    residual: float
    #: Which Raspberry Pi models fit, and which do not and why.
    fits: tuple[str, ...]
    excluded: tuple[tuple[str, str], ...]
    #: The Pi's positions on the plate, (label, x, y) of the Pi's own origin.
    pi_positions: tuple[tuple[str, float, float], ...] = ()
    #: Made parts: (name, qty, X x Y x Z, how).
    made: tuple[tuple[str, int, str, str], ...] = ()
    sources: tuple[Source, ...] = field(default_factory=tuple)

    def of_kind(self, *kinds: str) -> tuple[Box, ...]:
        return tuple(b for b in self.boxes if b.kind in kinds)
