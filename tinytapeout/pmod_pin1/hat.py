"""The Digilent Pmod HAT Adapter's three ports, for the pin 1 picture.

Hand-written, derived.  Digilent publish no board file for the HAT, so
nothing here can be machine-read the way the demo board's sockets are.
Where each port is comes from ``accessories/parts.py``, which measured it off
Digilent's own top view of the board to about +/-0.75 mm and is imported,
not restated.  Which end and which row of each port is pin 1 is read off
that same photograph and off the one in Digilent's reference manual, which
says it applies to Rev. B: pin 1 is the square pad, and Digilent print a 1
beside it.

- JA and JB face the left edge, JC the bottom edge, as the HAT is seen with
  its 40-pin header at the top -- the way Digilent photograph it.
- Pins 1 to 6 are the row further from the edge, the one with the square
  pad; pins 7 to 12 are the row nearer the edge, 7 beside 1, as the Pmod
  Interface Specification numbers a 2x6 host.
- Pin 1 is at the end of JA and JB nearer the bottom of the board and at
  the end of JC nearer the barrel jack; pin 6, beside which Digilent print
  3V3, and pin 5, beside which they print GND, are at the other end.

``accessories/parts.py`` gives each port a ``pin1_x`` and ``pin1_y`` at the
row nearer the edge and the opposite end of the port, which is pin 12's
place by the above, not pin 1's.  That is recorded in TODO.md; this module
does not use those two figures.

Coordinates as in ``tools.schema``: origin at the board's lower-left
corner, X right, Y up, top view, millimetres.
"""

from __future__ import annotations

from accessories import parts

WIDTH = parts.HAT_WIDTH
HEIGHT = parts.HAT_HEIGHT_SMT
CORNER_RADIUS = parts.HAT_CORNER_RADIUS
HOLES = parts.HAT_HOLES
HOLE_DIA = parts.HAT_HOLE_DIA
TOLERANCE = parts.PMOD_HAT_TOL
PITCH = parts.PMOD_PITCH

_features = {f.key: f for f in parts.PMOD_HAT.features}
#: The 40-pin header and the barrel jack, for finding one's way round the
#: board; the jack is good to +/-1.5 mm, ``parts.py`` says.
HEADER = _features["gpio40"]
BARREL = _features["barrel"]

#: Each port: the edge it faces, and the end of its length pin 1 is at,
#: as -1 for the lower X or Y and +1 for the higher.
_PORTS = {"JA": ("left", -1), "JB": ("left", -1), "JC": ("bottom", +1)}


def pins(name: str) -> dict[int, tuple[float, float]]:
    """Where each of port *name*'s twelve pins is."""
    edge, end = _PORTS[name]
    hosts = {p.label: p for p in parts.PMOD_HAT.pmods}
    host = hosts[name]
    if host.edge != edge:
        raise SystemExit(f"{name} faces {host.edge} in parts.py, not {edge}")
    inner = parts.PMOD_HAT_FIELD_DEPTH + parts.PMOD_ROW_SPACING / 2
    outer = parts.PMOD_HAT_FIELD_DEPTH - parts.PMOD_ROW_SPACING / 2
    along = host.cy if edge == "left" else host.cx
    out = {}
    for i in range(6):
        a = along + end * (parts.PMOD_PIN_SPAN / 2 - i * PITCH)
        for n, depth in ((i + 1, inner), (i + 7, outer)):
            out[n] = (depth, a) if edge == "left" else (a, depth)
    return out


PORTS = {name: dict(edge=edge, pins=pins(name))
         for name, (edge, _end) in _PORTS.items()}

SOURCES = (
    ("Port positions", "accessories/parts.py, measured off Digilent's top "
     "view of the board, +/-0.75 mm"),
    ("Pin 1 and the printing", "Digilent's top view on the Pmod HAT Adapter "
     "Reference Manual page, and the photograph in the manual for Rev. B"),
)
