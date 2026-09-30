#!/usr/bin/env python3
"""Measure the Waveshare PoE M.2 HAT+ (B) from Waveshare's dimension drawing.

Waveshare publish a dimension drawing for this HAT -- a straight-on top view of
the real board with six figures printed on it and "Unit: mm" in the corner:

    https://www.waveshare.com/wiki/PoE_M.2_HAT%2B_(B)
    https://www.waveshare.com/w/upload/d/d9/PoE-M.2-HAT-Plus-B-details-size.jpg

What it dimensions is the outline and the four HAT mounting holes -- 85.00 x
56.00, holes on a 58.00 x 49.00 rectangle 3.50 in from one end -- and one
overhang: the 2280 standoff projects 3.00 mm past the opposite board edge.  It
does not dimension the M.2 connector or any of the four M.2 standoffs, and
Waveshare publish no drawing, DXF, STEP or board file that does.  Those have to
be recovered from the same image, the way the Digilent Pmod HAT Adapter's host
positions are recovered in ``accessories/measure_pmod_hat.py``.

Scale and origin come from the four HAT mounting holes, whose 58.00 x 49.00
pitch the drawing states.  The fit is then *checked* against things not used to
derive it:

* the board's own edges, which must come out 85.00 x 56.00 and whose
  lower-left corner must land on the origin -- that second half is also what
  proves the image is being read the right way round, see below;
* the three M.2 standoffs that sit clear of the board edge, each of which
  gives the M.2 connector datum independently: the PCI Express M.2
  Specification fixes a module's retention screw at 30, 42 or 60 mm from the
  connector for a 2230, 2242 or 2260, so the three readings must agree;
* the 2280 standoff, which is then *predicted* at 80 mm from that datum and
  whose boss must therefore reach the 85.00 + 3.00 mm Waveshare dimension.

The residuals on those checks are the honest error bar for everything measured
here.  The 2280 standoff is deliberately not measured: the drawing rules a
dimension line down its overhang and it is the one boss whose outline the paper
behind the board runs into, so it is predicted and then checked instead.

Output is in the **Raspberry Pi's** frame, not the image's.  Waveshare draw the
HAT with its 40-pin header along the lower edge, which is the assembly seen
from above and turned through 180 degrees from the way Raspberry Pi Ltd draw a
Pi, so X runs right to left across the image and Y down it.

That turn is proved, not assumed.  Naming the four rings by which half of the
image each falls in cannot prove it: a picture the other way up has a ring in
each quadrant too, and the hole pitch is symmetric, so the fit comes out with
the same scale either way.  What is not symmetric is where the holes sit in
the board: 3.50 mm in from one end of an 85 mm board and 23.50 in from the
other.  So the check is the first one below -- with the origin put on the
holes, the board's own lower-left corner has to come back at (0, 0), and a
view read the wrong way round puts it twenty millimetres out.

Run: uv run --no-project --with pillow --with numpy python \\
         accessories/measure_poe_m2_hat.py \\
         tmp/src/waveshare-poe-m2-hat/poe-m2-hat-b-size.jpg
"""

from __future__ import annotations

import sys

import numpy as np
from PIL import Image

#: What Waveshare print on the drawing, verbatim, in millimetres.
DECLARED_WIDTH = 85.00
DECLARED_HEIGHT = 56.00
DECLARED_HOLE_PITCH_X = 58.00
DECLARED_HOLE_PITCH_Y = 49.00
DECLARED_HOLE_EDGE = 3.50
DECLARED_STANDOFF_OVERHANG = 3.00

#: How far the board's lower-left corner may land from the origin before the
#: view is being read the wrong way round.  Generous on purpose: the failure
#: it exists to catch is 20 mm wide, because the mounting holes are 3.50 in
#: from one end of the board and 23.50 in from the other, while the residuals
#: of a fit that is the right way round run to about a tenth of a millimetre.
ORIGIN_TOL = 1.0

#: Raspberry Pi HAT mounting hole centres, in the Pi's own frame.  The HAT
#: bolts through the Pi's own holes, so these are known before anything is
#: measured, and the drawing's 58.00 x 49.00 and 3.50 agree with them.
SCREWS_MM = {"bl": (3.5, 3.5), "br": (61.5, 3.5),
             "tl": (3.5, 52.5), "tr": (61.5, 52.5)}

#: Distance from the M.2 connector datum to the retention screw for a module
#: of each length, which is the module's own length: PCI Express M.2
#: Specification Revision 1.0, section 2.3.4, where the half-moon cutout that
#: takes the screw is centred on the module's far end edge.
STANDOFF_MM = {"2230": 30.0, "2242": 42.0, "2260": 60.0, "2280": 80.0}


def blobs(mask: np.ndarray, min_px: int):
    """Label connected True regions.

    Returns (cx, cy, area, x0, x1, y0, y1) in pixel coordinates.  The bounding
    box matters as much as the centroid here: every feature this script looks
    for is a circle, and the centre of a circle's box survives a bite taken
    out of one side of it where its centroid does not.
    """
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]
        seen[sy, sx] = True
        pts = []
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(pts) >= min_px:
            a = np.array(pts)
            out.append((a[:, 1].mean(), a[:, 0].mean(), len(pts),
                        int(a[:, 1].min()), int(a[:, 1].max()),
                        int(a[:, 0].min()), int(a[:, 0].max())))
    return out


def board_edges(lum: np.ndarray, run: int = 15, ink: float = 215.0):
    """The board's own outline in pixels, found by run length rather than area.

    The drawing's extension and dimension lines are a pixel or two wide and
    cross the paper all round the board, so any plain "not white" test finds
    one of those first.  A pixel counts as board only where *run* pixels in a
    row are all darker than *ink*, which no dimension line is.
    """
    h, w = lum.shape
    dark = lum < ink
    left, right, top, bottom = [], [], [], []
    for y in range(int(h * 0.30), int(h * 0.75)):
        hit = [x for x in range(w - run) if dark[y, x:x + run].all()]
        if hit:
            left.append(hit[0])
            right.append(hit[-1] + run - 1)
    for x in range(int(w * 0.30), int(w * 0.70)):
        hit = [y for y in range(h - run) if dark[y:y + run, x].all()]
        if hit:
            top.append(hit[0])
            bottom.append(hit[-1] + run - 1)
    return (float(np.median(left)), float(np.median(right)),
            float(np.median(top)), float(np.median(bottom)))


def main() -> None:
    path = (sys.argv[1] if len(sys.argv) > 1
            else "tmp/src/waveshare-poe-m2-hat/poe-m2-hat-b-size.jpg")
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    h, w, _ = a.shape
    lum = a.sum(axis=2) / 3
    print(f"image {w} x {h}: {path}")

    # --- the four HAT mounting holes ---------------------------------------
    #
    # Each is a white silkscreen ring on a black board, a clear 6 mm across
    # with nothing else white near it.
    ring = [c for c in blobs(lum > 200, 900)
            if 45 <= c[4] - c[3] <= 60 and 45 <= c[6] - c[5] <= 60]
    named: dict[str, tuple[float, float]] = {}
    for _, _, _, x0, x1, y0, y1 in ring:
        box = ((x0 + x1) / 2, (y0 + y1) / 2)
        # Named in the PI's frame on the assumption this is Waveshare's view,
        # the Pi turned through 180 degrees, so that the image's right is the
        # Pi's left and its bottom the Pi's top.  Naming proves nothing on its
        # own -- a picture the other way up also has one ring per quadrant --
        # and the assumption is tested by the board-origin check below.
        key = ("t" if box[1] > h / 2 else "b") + ("l" if box[0] > w / 2 else "r")
        if key in named:
            raise SystemExit(f"two candidate rings in quadrant {key}")
        named[key] = box
    if set(named) != set(SCREWS_MM):
        raise SystemExit(f"found rings {sorted(named)}, wanted {sorted(SCREWS_MM)}")
    for key in sorted(named):
        print(f"  hole {key}: pixel ({named[key][0]:7.2f},{named[key][1]:7.2f})")

    # --- fit pixel -> millimetre, in the Pi's frame ------------------------
    left_px = (named["tl"][0] + named["bl"][0]) / 2     # Pi x = 3.5
    right_px = (named["tr"][0] + named["br"][0]) / 2    # Pi x = 61.5
    low_px = (named["bl"][1] + named["br"][1]) / 2      # Pi y = 3.5
    high_px = (named["tl"][1] + named["tr"][1]) / 2     # Pi y = 52.5
    sx = (left_px - right_px) / DECLARED_HOLE_PITCH_X
    sy = (high_px - low_px) / DECLARED_HOLE_PITCH_Y
    print(f"  scale: {sx:.4f} px/mm across, {sy:.4f} px/mm down "
          f"(anisotropy {abs(sx - sy) / sx * 100:.2f} %)")
    ox = left_px + SCREWS_MM["bl"][0] * sx
    oy = low_px - SCREWS_MM["bl"][1] * sy

    def to_mm(px: float, py: float) -> tuple[float, float]:
        return (ox - px) / sx, (py - oy) / sy

    # --- check 1: the board's own outline, and which way up it is ----------
    x_lo, x_hi, y_lo, y_hi = board_edges(lum)
    x_max, y_min = to_mm(x_lo, y_lo)
    x_min, y_max = to_mm(x_hi, y_hi)
    print(f"\n--- check: board outline (declared {DECLARED_WIDTH:.2f} x "
          f"{DECLARED_HEIGHT:.2f}) ---")
    print(f"  X {x_min:6.2f} .. {x_max:6.2f}  width  {x_max - x_min:6.2f} mm "
          f"({x_max - x_min - DECLARED_WIDTH:+.2f})")
    print(f"  Y {y_min:6.2f} .. {y_max:6.2f}  height {y_max - y_min:6.2f} mm "
          f"({y_max - y_min - DECLARED_HEIGHT:+.2f})")
    print(f"  lower-left corner at ({x_min:.2f}, {y_min:.2f}), "
          f"origin tolerance {ORIGIN_TOL:.2f}")
    if abs(x_min) > ORIGIN_TOL or abs(y_min) > ORIGIN_TOL:
        raise SystemExit(
            f"the board's lower-left corner lands at ({x_min:.2f}, "
            f"{y_min:.2f}), not the origin. The mounting holes are "
            f"{DECLARED_HOLE_EDGE:.2f} in from one end of the board and "
            f"{DECLARED_WIDTH - DECLARED_HOLE_EDGE - DECLARED_HOLE_PITCH_X:.2f}"
            " in from the other, so this is what an image turned the wrong "
            "way round looks like once the fit has been made on them")
    resid = [abs(x_max - x_min - DECLARED_WIDTH),
             abs(y_max - y_min - DECLARED_HEIGHT),
             abs(x_min), abs(y_min)]

    # --- the three inboard M.2 standoffs -----------------------------------
    #
    # Metal bosses in one row across the board, each a bright disc close to
    # 6 mm across with black board all round it.  The 2280 boss is the fourth
    # and is left out here: it sits on the board edge with white paper beyond
    # it and the drawing's own extension line down its side, so no threshold
    # separates it from either.  It is predicted below instead.
    band = np.zeros_like(lum, dtype=bool)
    lo, hi = int(h * 0.36), int(h * 0.50)
    band[lo:hi, int(x_lo) + 4:int(x_hi) - 4] = \
        lum[lo:hi, int(x_lo) + 4:int(x_hi) - 4] > 140
    discs = [c for c in blobs(band, 1300)
             if 40 <= c[4] - c[3] <= 56 and 40 <= c[6] - c[5] <= 56
             and abs((c[4] - c[3]) - (c[6] - c[5])) <= 8]
    discs.sort(key=lambda c: -c[0])          # image right = Pi left = 2230 end
    if len(discs) != 3:
        raise SystemExit(f"found {len(discs)} inboard standoff candidates, "
                         "wanted 2230, 2242 and 2260")
    print("\n--- M.2 standoffs, Pi frame in mm ---")
    pos, dias, datums = {}, [], {}
    for name, c in zip(("2230", "2242", "2260"), discs):
        x, y = to_mm((c[3] + c[4]) / 2, (c[5] + c[6]) / 2)
        dia = (c[4] - c[3] + 1) / sx
        pos[name] = (x, y)
        dias.append(dia)
        datums[name] = x - STANDOFF_MM[name]
        print(f"  {name}: x {x:6.2f}  y {y:5.2f}  boss dia {dia:4.2f} mm  "
              f"-> connector datum x = {datums[name]:5.2f}")

    # --- check 2: the three datums have to be the same point ---------------
    datum = sum(datums.values()) / len(datums)
    spread = max(datums.values()) - min(datums.values())
    print(f"\n--- check: one connector datum from three standoffs ---")
    print(f"  mean x = {datum:.2f} mm, spread {spread:.2f} mm")
    resid.append(spread)

    # --- check 3: the 2280 standoff, predicted then checked ----------------
    dia = sum(dias) / len(dias)
    x2280 = datum + STANDOFF_MM["2280"]
    outer = x2280 + dia / 2
    print(f"\n--- check: 2280 standoff (Waveshare dimension "
          f"{DECLARED_WIDTH:.2f} + {DECLARED_STANDOFF_OVERHANG:.2f}) ---")
    print(f"  screw x  {x2280:6.2f} mm, boss dia {dia:.2f} mm, "
          f"outer extremity {outer:6.2f} mm "
          f"({outer - DECLARED_WIDTH - DECLARED_STANDOFF_OVERHANG:+.2f})")
    resid.append(abs(outer - DECLARED_WIDTH - DECLARED_STANDOFF_OVERHANG))

    # --- the M.2 connector's footprint -------------------------------------
    #
    # The socket is a black moulding on a black board, but it is not as black:
    # bare board reads about 55 here and the moulding, its solder tails and
    # its end posts about 70 to 125.  So it separates at a threshold well
    # below anything the other measurements use, inside a window around the
    # M.2 axis beyond the connector datum.  The window is 11.5 mm each side
    # of the axis, which a socket for a 22 mm module cannot reach past, and
    # which is what keeps the mounting hole ring 3.5 mm from the board's
    # corner out of it.
    axis = sum(p[1] for p in pos.values()) / len(pos)
    win = np.zeros_like(lum, dtype=bool)
    xs0, xs1 = int(ox - (datum + 9.0) * sx), int(ox - (datum - 6.0) * sx)
    ys0, ys1 = int(oy + (axis - 11.5) * sy), int(oy + (axis + 11.5) * sy)
    win[ys0:ys1, xs0:xs1] = lum[ys0:ys1, xs0:xs1] > 66
    body = max(blobs(win, 2000), key=lambda c: c[2], default=None)
    if body is not None:
        x1, y0 = to_mm(body[3], body[5])
        x0, y1 = to_mm(body[4], body[6])
        print("\n--- M.2 M-key socket footprint ---")
        print(f"  X {x0:6.2f} .. {x1:6.2f} ({x1 - x0:5.2f} deep)   "
              f"Y {y0:5.2f} .. {y1:5.2f} ({y1 - y0:5.2f} long), "
              f"centre y {(y0 + y1) / 2:5.2f}")

    # --- what all that means for a card ------------------------------------
    print("\n--- derived: where a 2280 card lands, Pi frame in mm ---")
    print(f"  mating edge, seated   x = {datum:6.2f}")
    print(f"  far end and its screw x = {x2280:6.2f} "
          f"({x2280 - DECLARED_WIDTH:+.2f} past the board edge)")
    print(f"  centreline            y = {axis:6.2f}")

    worst = max(resid)
    print(f"\n  Worst residual on a check not used in the fit: {worst:.2f} mm.")
    print(f"  Treat every position above as +/-{max(0.2, round(worst, 1)):.1f} mm.")


if __name__ == "__main__":
    main()
