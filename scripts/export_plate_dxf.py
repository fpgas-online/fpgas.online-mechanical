#!/usr/bin/env python3
"""Export the mounting plate as a DXF cut file.

Geometry only: the outline, the board mounting holes, the slots and the plate
fixings, each on its own layer so a laser or router job can pick what it wants.
No dimensions, no text, nothing that a CAM package would have to strip out.

Run: uv run --no-project --with ezdxf python scripts/export_plate_dxf.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.mounting_plate import PLATE  # noqa: E402

LAYERS = {
    "PLATE_OUTLINE": 5,
    "BOARD_HOLES": 1,
    "BOARD_SLOTS": 1,
    "PLATE_FIXINGS": 3,
}

#: A quarter-circle's bulge value: tan(90 degrees / 4).
QUARTER_BULGE = math.tan(math.pi / 8)


def rounded_rect(width: float, height: float, r: float):
    """Vertices of a rounded rectangle as (x, y, bulge) for an LWPOLYLINE."""
    return [
        (r, 0.0, 0.0), (width - r, 0.0, QUARTER_BULGE),
        (width, r, 0.0), (width, height - r, QUARTER_BULGE),
        (width - r, height, 0.0), (r, height, QUARTER_BULGE),
        (0.0, height - r, 0.0), (0.0, r, QUARTER_BULGE),
    ]


def slot_outline(x0, y0, x1, y1, width):
    """Obround as an LWPOLYLINE: two straight flanks and two semicircular ends."""
    r = width / 2
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * r, math.cos(ang) * r
    # A semicircle is a bulge of magnitude 1 (tan of a quarter of 180 degrees).
    # The sign is negative because walking this vertex order, up the left flank
    # and back down the right, goes clockwise, and a positive bulge is
    # counter-clockwise.  Getting it wrong ties the outline into a bowtie.
    return [(x0 + nx, y0 + ny, 0.0), (x1 + nx, y1 + ny, -1.0),
            (x1 - nx, y1 - ny, 0.0), (x0 - nx, y0 - ny, -1.0)]


def main() -> None:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4        # millimetres
    msp = doc.modelspace()
    for name, colour in LAYERS.items():
        doc.layers.add(name, color=colour)

    o = PLATE.outline
    msp.add_lwpolyline(rounded_rect(o.width, o.height, o.corner_radius),
                       format="xyb", close=True,
                       dxfattribs={"layer": "PLATE_OUTLINE"})

    for h in PLATE.holes:
        layer = "PLATE_FIXINGS" if h.kind == "plate" else "BOARD_HOLES"
        msp.add_circle((h.x, h.y), h.dia / 2, dxfattribs={"layer": layer})

    for s in PLATE.slots:
        msp.add_lwpolyline(slot_outline(s.x0, s.y0, s.x1, s.y1, s.width),
                           format="xyb", close=True,
                           dxfattribs={"layer": "BOARD_SLOTS"})

    out = ROOT / "diagrams" / "mounting-plate" / "tt-generic-mounting-plate.dxf"
    doc.saveas(str(out))
    board = sum(1 for h in PLATE.holes if h.kind != "plate")
    fixings = len(PLATE.holes) - board
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  outline {o.width} x {o.height} mm, corner radius {o.corner_radius}")
    print(f"  {board} board holes, {len(PLATE.slots)} slots, {fixings} plate fixings")


if __name__ == "__main__":
    main()
