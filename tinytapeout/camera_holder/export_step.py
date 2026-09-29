#!/usr/bin/env python3
"""Write the camera holder as STEP solids, from ``holder.py``.

The holder's parts are printed, so what a maker needs is a solid model; it
is built from the same boxes the drawing and ``verify.py`` read, so the three
cannot drift apart.  Every number below is ``holder.py``'s.

For each lens's holder, the assembly, every part where it goes over the
plate -- the file to check a fit in, or to hand to somebody who wants to see
the rig -- and its side frames, the one part that differs between the two.
The beam and the carrier are the same two parts in both holders, which
``verify.py`` checks, so each is one file.  Every part file lies the way its
print note says, on the bed at Z = 0 and at the origin, so a slicer takes it
as it comes; the two side frames are mirror images, so each has its own.

Run: uv run --no-project --with cadquery python \\
         tinytapeout/camera_holder/export_step.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tinytapeout.camera_holder import holder  # noqa: E402
from tools import reproducible  # noqa: E402

OUT = Path(__file__).resolve().parent / "output"

#: The file stem every holder file starts with.
STEM = "tt-camera-holder"

#: The parts that differ between the holders, and so are written once per
#: lens; the others are written once.
PER_LENS = ("side", "side-right")

#: How far a cutting tool runs past the material it cuts, so no face is left
#: coincident with the face it cuts through.
OVER = 1.0

#: How each part lies to be printed: which face goes on the bed.  A rotation
#: about a plate axis, in degrees, and then it is set down at the origin.
PRINT_POSE = {
    "side": ("Y", -90.0),       # on its outer face: the foot stands up
    "side-right": ("Y", 90.0),  # the same, mirrored
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
        if h.hex:
            # A nut pocket: a hexagon *dia* across its flats, from its floor
            # up through the face it opens on.
            r = h.dia / math.sqrt(3)
            cutter = (cq.Workplane("XY", origin=(h.x, h.y, h.z0))
                      .polygon(6, 2 * r).extrude(h.z1 - h.z0 + OVER).val())
        else:
            cutter = cq.Solid.makeCylinder(
                h.dia / 2, h.z1 - h.z0 + 2 * OVER,
                cq.Vector(h.x, h.y, h.z0 - OVER))
        out = out.cut(cutter)
    return out.clean()


def bed_face_is_largest(shape) -> tuple[bool, float, float]:
    """Whether the part lies on its largest flat face, as its note says.

    The review caught the side frames posed the wrong way up: they lay on
    the 460 mm2 end of the foot, with the whole wall 8.7 mm over the bed.
    So the pose is checked, not trusted: the face at Z = 0 has to be the
    largest planar face the solid has.
    """
    faces = [f for f in shape.Faces() if f.geomType() == "PLANE"]
    largest = max(f.Area() for f in faces)
    on_bed = sum(f.Area() for f in faces
                 if abs(f.BoundingBox().zmax) < 1e-6
                 and abs(f.BoundingBox().zmin) < 1e-6)
    return on_bed >= largest - 1e-6, on_bed, largest


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


def part_path(h, part) -> Path:
    """Where *part* of holder *h* is written."""
    name = PRINT_NAME.get(part.key, part.key)
    if part.key in PER_LENS:
        return OUT / f"{STEM}-{h.KEY}-{name}.step"
    return OUT / f"{STEM}-{name}.step"


def main() -> None:
    import cadquery as cq

    OUT.mkdir(parents=True, exist_ok=True)
    written = set()
    for h in holder.VARIANTS.values():
        solids = {p.key: solid(p) for p in h.ASSEMBLY}
        assembly = OUT / f"{STEM}-{h.KEY}.step"
        write(cq.Compound.makeCompound(list(solids.values())), assembly)
        print(f"{assembly.relative_to(ROOT)}: the {h.LENS.short} deg lens's "
              "assembly, over the plate")
        for part in h.ASSEMBLY:
            path = part_path(h, part)
            if path in written:
                continue
            written.add(path)
            shape = posed(part, solids[part.key])
            ok, on_bed, largest = bed_face_is_largest(shape)
            if not ok:
                raise SystemExit(f"{part.name} lies on {on_bed:.0f} mm2 of "
                                 f"face where its largest is {largest:.0f}: "
                                 "turn it over in PRINT_POSE")
            write(shape, path)
            bb = shape.BoundingBox()
            vol = shape.Volume() / 1000
            print(f"{path.relative_to(ROOT)}: {part.name}, "
                  f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm as "
                  f"printed, {vol:.2f} cm3, {vol * 1.27:.1f} g in PETG at "
                  "1.27 g/cm3")


if __name__ == "__main__":
    main()
