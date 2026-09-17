#!/usr/bin/env python3
"""Write the light pipe adapter as a STEP solid, from ``adapter.py``.

The mounting plate is a flat part and its cut file is a DXF; this one is a
printed solid, so the file a maker needs is a solid model.  It is built from
the same data module the drawing is, so the two cannot drift apart: every
number below is a constant of ``adapter.py`` and none is written twice.

The part is six primitives and four cuts, which is the whole of it:

* two cheeks, the blocks in front of the jack that the bores run through,
  each cut off at a 45 degree facet that is the light pipe's flange seat;
* a roof over the jack joining them, slotted twice to clear the jack's top
  EMI springs;
* two skirts down the jack's sides, which its side EMI springs bear on;
* two bores at 45 degrees, each a clearance length and then a press fit;
* two pockets in the cheeks' back faces, open at the bottom, over the LED
  windows.

Run: uv run --no-project --with cadquery python fpga/light_pipe/export_step.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from fpga.light_pipe import adapter as A  # noqa: E402
from tools import reproducible  # noqa: E402

OUT = Path(__file__).resolve().parent / "output" / "arty-ethernet-light-pipe.step"

H = math.sqrt(0.5)

#: How far a cutting tool is run past the material it cuts, so that a face is
#: never left coincident with the face it is cutting through: a zero-thickness
#: sliver is what makes a boolean fail or leave a film of material behind.
OVER = 1.5


def build():
    import cadquery as cq

    def box(x0, x1, y0, y1, z0, z1):
        return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0,
                                cq.Vector(x0, y0, z0))

    def mirrored(make):
        """The part is symmetric about Y = 0: one of each, and its mirror."""
        return [make(+1), make(-1)]

    def span(y0, y1, side):
        return (min(side * y0, side * y1), max(side * y0, side * y1))

    solids = []
    for side in (+1, -1):
        y0, y1 = span(A.CHEEK_Y0, A.CHEEK_Y1, side)
        solids.append(box(A.CHEEK_X0, A.CHEEK_X1, y0, y1,
                          A.CHEEK_Z0, A.CHEEK_Z1))
        y0, y1 = span(A.SKIRT_Y0, A.SKIRT_Y1, side)
        solids.append(box(A.SKIRT_X0, A.SKIRT_X1, y0, y1,
                          A.SKIRT_Z0, A.SKIRT_Z1))
    solids.append(box(A.ROOF_X0, A.ROOF_X1, -A.ROOF_Y1, A.ROOF_Y1,
                      A.ROOF_Z0, A.ROOF_Z1))

    part = solids[0]
    for s in solids[1:]:
        part = part.fuse(s)

    # The facet: everything above the plane z - x = FACET_K comes off.  A box
    # whose own underside is that plane does it -- rotate it about Y until its
    # underside's normal is the plane's, then lift it to the plane.
    for side in (+1, -1):
        cutter = cq.Solid.makeBox(60, 60, 60, cq.Vector(-30, -30, 0))
        cutter = cutter.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -45)
        cutter = cutter.translate(cq.Vector(0, 0, A.FACET_K))
        part = part.cut(cutter)
        break       # one plane, and it crosses both cheeks

    cuts = []
    for side in (+1, -1):
        y0, y1 = span(A.POCKET_Y0, A.POCKET_Y1, side)
        cuts.append(box(A.POCKET_X0, A.POCKET_X1 + OVER, y0, y1,
                        A.POCKET_Z0 - OVER, A.POCKET_Z1))
        y0, y1 = span(A.SLOT_Y0, A.SLOT_Y1, side)
        cuts.append(box(A.SLOT_X0 - OVER, A.SLOT_X1, y0, y1,
                        A.ROOF_Z0 - OVER, A.ROOF_Z1 + OVER))

        axis = cq.Vector(-H, 0, H)
        tip = cq.Vector(A.BORE_X, side * A.BORE_Y, A.BORE_Z)
        clear_len = A.PIPE_LEN - A.PRESS_LEN
        cuts.append(cq.Solid.makeCylinder(
            A.BORE_DIA / 2, clear_len + OVER,
            tip - axis.multiply(OVER), axis))
        cuts.append(cq.Solid.makeCylinder(
            A.PRESS_DIA / 2, A.PRESS_LEN + OVER,
            tip + axis.multiply(clear_len), axis))

    for c in cuts:
        part = part.cut(c)
    return cq.Workplane("XY").newObject([part])


def main() -> None:
    import cadquery as cq

    part = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(part, str(OUT), "STEP")
    reproducible.normalise_step(OUT, name=OUT.stem)

    solid = part.val()
    volume = solid.Volume()
    bb = solid.BoundingBox()
    print(f"{OUT.relative_to(ROOT)}: "
          f"x {bb.xmin:.3f}..{bb.xmax:.3f}, y {bb.ymin:.3f}..{bb.ymax:.3f}, "
          f"z {bb.zmin:.3f}..{bb.zmax:.3f} mm")
    print(f"  {volume / 1000:.3f} cm3 of material, "
          f"{volume / 1000 * 1.27:.2f} g in PETG at 1.27 g/cm3")


if __name__ == "__main__":
    main()
