#!/usr/bin/env python3
"""Write the camera holder as STEP solids, from ``holder.py``.

The holder's parts are printed, so what a maker needs is a solid model; it
is built from the same boxes the drawing and ``verify.py`` read, so the three
cannot drift apart.  Every number below is ``holder.py``'s.

The assembly, every part where it goes over the plate -- the file to check
a fit in, or to hand to somebody who wants to see the rig.  And one file per
part to print, each lying the way its print note says, on the bed at Z = 0
and at the origin, so a slicer takes it as it comes; the two side frames are
mirror images, so each has its own.

Run: uv run --no-project --with cadquery python \\
         tinytapeout/camera_holder/export_step.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tinytapeout.camera_holder import holder as H  # noqa: E402
from tools import reproducible  # noqa: E402

OUT = Path(__file__).resolve().parent / "output"
ASSEMBLY = OUT / "tt-camera-holder.step"

#: How far a cutting tool runs past the material it cuts, so no face is left
#: coincident with the face it cuts through.
OVER = 1.0

#: How each part lies to be printed: which face goes on the bed.  A rotation
#: about a plate axis, in degrees, and then it is set down at the origin.
PRINT_POSE = {
    "side": ("Y", 90.0),        # on its outer face: the foot stands up
    "side-right": ("Y", -90.0),  # the same, mirrored
    "beam": ("X", 180.0),       # on its top face
    "carrier": ("X", 180.0),    # on its top face, bosses up
}


#: What each part's print file is called, where not its key.
PRINT_NAME = {"side": "side-left"}


def solid(part):
    import cadquery as cq
    shapes = [cq.Solid.makeBox(b.x1 - b.x0, b.y1 - b.y0, b.z1 - b.z0,
                               cq.Vector(b.x0, b.y0, b.z0))
              for b in part.boxes]
    shapes += [cq.Solid.makeCylinder(c.dia / 2, c.z1 - c.z0,
                                     cq.Vector(c.x, c.y, c.z0))
               for c in part.bosses]
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    for h in part.holes:
        out = out.cut(cq.Solid.makeCylinder(
            h.dia / 2, h.z1 - h.z0 + 2 * OVER,
            cq.Vector(h.x, h.y, h.z0 - OVER)))
    return out.clean()


def posed(part, shape):
    """*shape* turned onto the face it is printed on, at the origin."""
    import cadquery as cq
    axis, angle = PRINT_POSE[part.key]
    vec = {"X": cq.Vector(1, 0, 0), "Y": cq.Vector(0, 1, 0)}[axis]
    shape = shape.rotate(cq.Vector(0, 0, 0), vec, angle)
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))


def write(shape, path: Path) -> None:
    import cadquery as cq
    cq.exporters.export(cq.Workplane("XY").newObject([shape]), str(path),
                        "STEP")
    reproducible.normalise_step(path, name=path.stem)


def main() -> None:
    import cadquery as cq

    OUT.mkdir(parents=True, exist_ok=True)
    solids = {p.key: solid(p) for p in H.ASSEMBLY}
    write(cq.Compound.makeCompound(list(solids.values())), ASSEMBLY)
    print(f"{ASSEMBLY.relative_to(ROOT)}: the assembly, over the plate")
    for part in H.ASSEMBLY:
        path = OUT / f"tt-camera-holder-{PRINT_NAME.get(part.key, part.key)}.step"
        shape = posed(part, solids[part.key])
        write(shape, path)
        bb = shape.BoundingBox()
        vol = shape.Volume() / 1000
        print(f"{path.relative_to(ROOT)}: {part.name}, "
              f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm as printed,"
              f" {vol:.2f} cm3, {vol * 1.27:.1f} g in PETG at 1.27 g/cm3")


if __name__ == "__main__":
    main()
