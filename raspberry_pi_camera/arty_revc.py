#!/usr/bin/env python3
"""Read back the Arty heights RPICAM-OVER-ARTY quotes, from Digilent's files.

The Arty A7 has no mounting holes and stands on four rubber feet, so a camera
stand over it needs two heights: S, what it stands on to its top face, and T,
its top face to its tallest part.  Digilent's A7 drawing is a plan and gives
neither.  Their 3D model does give heights, but it is of the Arty Rev C, not
the A7, and states no tolerance, so ``optics.py`` quotes its figures on the
sheet and sets nothing from them: S and T are to measure.  This reads every
figure quoted there back out of the two files, and fails if one has moved:

* the model's board slab, its two largest horizontal faces apart;
* its "Ruber_Feet": how tall, how far across, and where;
* its tallest part over the slab's top face, which has to be the Ethernet
  jack's shield, standing where the A7 drawing puts J9;
* its outline, against the A7 drawing's DXF and its own inch dimensions;
* the foot circles the A7 drawing's PDF plot draws, scaled by the plot's
  outline to the DXF's size as ``fpga/extract.py`` does.

``tools/fetch_fpga.sh`` fetches both files into ``tmp/src/arty_a7``.  Loading
the model takes a minute, and it needs OpenCascade, so this is run by hand
or by ``make data``, not by ``make check``::

    uv run --no-project --with cadquery --with pdfplumber \\
        python raspberry_pi_camera/arty_revc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fpga.boards import BOARDS  # noqa: E402
from raspberry_pi_camera import optics  # noqa: E402
from tools import step_model  # noqa: E402

SRC = ROOT / "tmp" / "src" / "arty_a7"
STEP = SRC / "revc_cad" / "ARTY For Web" / "Arty Rev C.stp"
PLOT = SRC / "mechanical_drawing" / "Arty A7" / "Mechanical_Arty_A7.pdf"

#: How close a figure read back has to be to the one quoted: the quoted
#: figures are to the hundredth, and the model's own faces carry about a
#: hundredth of export noise.
CLOSE = 0.01

#: The A7 drawing's own inch dimensions, as lettered on the PDF: "4.3in" and
#: "3.4in".
DRAWN_INCHES = (4.3, 3.4)


def check(what: str, got: float, want: float, tol: float = CLOSE) -> int:
    ok = abs(got - want) <= tol
    print(f"   {'ok  ' if ok else 'FAIL'} {what}: {got:.3f}, quoted {want:.2f}")
    return not ok


def main() -> None:
    for path in (STEP, PLOT):
        if not path.exists():
            raise SystemExit(f"missing {path}; run tools/fetch_fpga.sh")
    bad = 0
    spec = BOARDS["arty-a7"]
    model = step_model.load(str(STEP))
    board = model.largest()
    lo, hi = model.slab(board)
    print(f"Digilent's Arty Rev C model, {STEP.name}: {len(model.solids)} "
          f"solids, the board {board.name!r}")
    bad += check("board slab", hi - lo, optics.ARTY_REVC_BOARD)

    feet = model.named("Ruber_Feet")
    if len(feet) != 4:
        raise SystemExit(f"{len(feet)} Ruber_Feet in the model, not 4")
    for n, foot in enumerate(feet):
        bad += check(f"foot {n + 1} under the slab", lo - foot.z0,
                     optics.ARTY_REVC_FOOT)
        bad += check(f"foot {n + 1} across", foot.x1 - foot.x0,
                     optics.ARTY_REVC_FOOT_ACROSS)
        # Centred 5.0 in from each corner, as the A7 drawing draws them.
        cx = (foot.x0 + foot.x1) / 2 - board.x0
        cy = (foot.y0 + foot.y1) / 2 - board.y0
        near_x = min(cx, board.x1 - board.x0 - cx)
        near_y = min(cy, board.y1 - board.y0 - cy)
        bad += check(f"foot {n + 1} in from the nearer edges",
                     max(abs(near_x - 5.0), abs(near_y - 5.0)), 0.0)
    # Nothing reaches lower than the feet, or the board would not stand
    # on them.
    lowest = min(s.z0 for s in model.solids)
    ok = all(abs(f.z0 - lowest) < 1e-6 for f in feet)
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} the feet are the lowest solids")

    tallest = max(model.solids, key=lambda s: s.z1)
    bad += check(f"tallest, {tallest.name!r}, over the slab's top face",
                 tallest.z1 - hi, optics.ARTY_REVC_TALLEST)
    # The A7's J9, from fpga/boards.py, against the shield in board
    # coordinates: the same jack in the same place, on the drawing's
    # locating-peg centre line.
    j9 = next(f for f in spec.features if f.designator == "J9")
    cy = (tallest.y0 + tallest.y1) / 2 - board.y0
    ok = (tallest.name == "shielding"
          and abs(cy - (j9.y0 + j9.y1) / 2) < 0.1
          and tallest.x0 - board.x0 < 1.0)
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} it is the Ethernet jack's shield, "
          f"centred {cy:.2f} up the board's edge; the A7 drawing's J9 "
          f"{(j9.y0 + j9.y1) / 2:.2f}")

    w, h = board.x1 - board.x0, board.y1 - board.y0
    print(f"   --   outline {w:.2f} x {h:.2f}: the A7 DXF's "
          f"{spec.outline.width:.2f} x {spec.outline.height:.2f}, the A7 "
          f"drawing's {DRAWN_INCHES[0]} x {DRAWN_INCHES[1]} in")
    bad += check("outline against the drawing's inches, X", w,
                 DRAWN_INCHES[0] * 25.4)
    bad += check("outline against the drawing's inches, Y", h,
                 DRAWN_INCHES[1] * 25.4)

    # The foot circles on the A7 drawing's plot: the four curves 59 points
    # across in the corners, scaled by the outline as fpga/extract.py
    # scales the plot.  Nothing else on the page is a curve that size.
    import pdfplumber
    from tools.dump_rpi_pdf import rectangles
    page = pdfplumber.open(str(PLOT)).pages[0]
    raw = []
    for ln in page.lines:
        pts = ln["pts"]
        raw += [(ax, ay, bx, by) for (ax, ay), (bx, by) in zip(pts, pts[1:])]
    aspect = spec.outline.width / spec.outline.height
    x0, _, x1, _ = max(
        (r for r in rectangles(raw)
         if abs((r[2] - r[0]) / (r[3] - r[1]) / aspect - 1) < 0.01),
        key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    scale = spec.outline.width / (x1 - x0)
    circles = []
    for c in page.curves:
        xs = [p[0] for p in c["pts"]]
        if max(xs) - min(xs) > 20:
            circles.append((max(xs) - min(xs)) * scale)
    if len(circles) != 4:
        raise SystemExit(f"{len(circles)} foot circles on the plot, not 4")
    for n, d in enumerate(circles):
        bad += check(f"the A7 drawing's foot {n + 1} across", d,
                     optics.ARTY_FOOT_DRAWN, tol=0.05)

    print()
    if bad:
        raise SystemExit(f"FAIL: {bad} figure(s) quoted in optics.py are not "
                         "what the files give")
    print("PASS: every Arty figure optics.py quotes is what the files give")


if __name__ == "__main__":
    main()
