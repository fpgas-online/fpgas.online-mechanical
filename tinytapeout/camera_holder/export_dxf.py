#!/usr/bin/env python3
"""Write the camera holder's beam as a DXF cut file.

The beam is the holder's one flat part: a profile of constant thickness
with every hole through it square to its faces, so it can be cut from sheet
as well as printed -- from 6 mm acrylic on the laser that cuts the plate,
say.  The side frames and the carrier are not flat (a foot, bosses) and
stay printed.

Geometry only, as the plate's cut file is: the outline and the holes, each
on its own layer, in the plate's coordinates seen from above, so the file
lies over the plate's own DXF where the beam goes.  Every figure is
``holder.py``'s.

Run: uv run --no-project --with ezdxf python \\
         tinytapeout/camera_holder/export_dxf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tinytapeout.camera_holder import holder as H  # noqa: E402
from tools import reproducible  # noqa: E402

OUT = Path(__file__).resolve().parent / "output" / "tt-camera-holder-beam.dxf"

LAYERS = {
    "BEAM_OUTLINE": 5,
    "BEAM_FIXINGS": 1,
    "CARRIER_FIXINGS": 3,
}


def outline() -> list[tuple[float, float]]:
    """The beam's profile: a bar along X with the square pad across it.

    Built from the two boxes rather than drawn: the pad has to stand past
    the bar on both sides and sit inside its length, which is checked here
    rather than assumed, since that is what makes it this one polygon.
    """
    bar = next(b for b in H.BEAM.boxes if b.what == "beam")
    pad = next(b for b in H.BEAM.boxes if b.what == "pad")
    if not (pad.y0 < bar.y0 and pad.y1 > bar.y1
            and bar.x0 < pad.x0 and pad.x1 < bar.x1):
        raise SystemExit("the beam's pad no longer stands across its bar; "
                         "its outline is not the polygon this writes")
    return [(bar.x0, bar.y0), (pad.x0, bar.y0), (pad.x0, pad.y0),
            (pad.x1, pad.y0), (pad.x1, bar.y0), (bar.x1, bar.y0),
            (bar.x1, bar.y1), (pad.x1, bar.y1), (pad.x1, pad.y1),
            (pad.x0, pad.y1), (pad.x0, bar.y1), (bar.x0, bar.y1)]


def main() -> None:
    reproducible.configure_dxf()
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4        # millimetres
    msp = doc.modelspace()
    for name, colour in LAYERS.items():
        doc.layers.add(name, color=colour)
    msp.add_lwpolyline(outline(), close=True,
                       dxfattribs={"layer": "BEAM_OUTLINE"})
    for h in H.BEAM.holes:
        layer = ("CARRIER_FIXINGS" if "carrier" in h.what
                 else "BEAM_FIXINGS")
        msp.add_circle((h.x, h.y), h.dia / 2, dxfattribs={"layer": layer})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    reproducible.normalise_dxf(doc)
    doc.saveas(str(OUT))
    bar = next(b for b in H.BEAM.boxes if b.what == "beam")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {bar.x1 - bar.x0:.1f} long, {H.BEAM_T:g} thick, "
          f"{len(H.BEAM.holes)} holes")


if __name__ == "__main__":
    main()
