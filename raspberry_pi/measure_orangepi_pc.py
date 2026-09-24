#!/usr/bin/env python3
"""Measure the Xunlong Orange Pi PC from photographs of it.

Xunlong publish one mechanical figure for this board, its overall size, and
no drawing: SCRATCH.md records the search.  So the geometry is recovered from
square-on photographs of the real board, the way accessories/measure_pmod_hat.py
recovers the Pmod HAT Adapter's, from two independent pairs:

    sunxi-v1p3-*   linux-sunxi's top and bottom views of a v1.3 board, a
                   Fujifilm X-E2 at 35 mm, 15 November 2016
    xunlong-*      Xunlong's own product page views of a v1.2 board

``tools/fetch_orangepi_pc.sh`` fetches them, with the URL of each.  A third
pair, linux-sunxi's views of another v1.2, was measured and is not used: it is
shot obliquely with the far half of the board out of focus, and its frame fit
misses the board's left edge by a millimetre.

The fit, per photograph:

* The four board edges are found where the edge is not hidden behind a
  connector, a line is fitted to each and the corners are their
  intersections.  A homography takes the corners onto an 85.00 x 56.00 mm
  rectangle, the size Xunlong's product page dimensions.  (Their manual says
  85 x 55; the photographs' own aspect is printed as a check.)
* Everything else is then measured in that frame, in millimetres, from the
  lower-left corner of the board seen from the component side, the same
  frame as the Raspberry Pi sheets.  A bottom view is mirrored into it.

What is measured where:

* mounting holes: in all four views, as circles fitted to the copper ring;
* the 40-pin header: in the two bottom views, from the 40 solder joints,
  which lie in the board plane where the pins in a top view stand 8 mm off it;
* the connectors: their top faces, read off both rectified top views and
  corrected for parallax, and where a part overhangs the board edge, what
  both bottom views see of it past the edge.  ``orangepi_pc.py`` takes the
  mean of every reading.  A top face is nearer the lens than the board is,
  so it is drawn larger, about the point under the lens, by D / (D - z).
  That point and D come from the header itself: its pin tips in the top view
  against its solder joints in the bottom view of the same board.  The tip
  height and each part's height enter only through the size of that
  correction.

Checks not used in the fit are printed for each: the header must be 48.26 mm
from pin 1 to pin 39 on a 2.54 mm pitch with its rows 2.54 mm apart, the four
views must agree on every hole, and the board's aspect in each photograph
must say 56 rather than 55.  raspberry_pi/verify_orangepi_pc.py holds the
adopted figures against the same checks and against third-party models.

The connector edges are read by eye off a 1 mm grid drawn on the rectified
photograph, at 40 pixels to the millimetre; ``--grids DIR`` writes those
images so any reading below can be checked.

Run: uv run --no-project --with numpy --with opencv-python-headless python \\
         raspberry_pi/measure_orangepi_pc.py [--grids tmp/orangepi_pc]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.photo_frame import (Frame, blob, fit_board, grid_image,  # noqa: E402
                               photographed_height, ring)

SRC = ROOT / "tmp" / "src" / "orangepi_pc" / "photos"

#: The rectangle every photograph is fitted to, from Xunlong's product page.
FRAME = Frame(85.0, 56.0)
#: The height Xunlong's manual gives instead, checked against the photographs.
MANUAL_HEIGHT = 55.0

#: Each photograph: file, how a bottom view is mirrored into the top view
#: (see tools.photo_frame.Frame.corners), and roughly where the board's
#: corners are in it, in image pixels, top-left first and clockwise.
PHOTOS = {
    "sunxi-v1p3-top": ("sunxi-v1p3-top.jpg", None,
                       [(143, 154), (2249, 154), (2249, 1540), (143, 1540)]),
    "sunxi-v1p3-bottom": ("sunxi-v1p3-bottom.jpg", "x",
                          [(228, 100), (2423, 100), (2423, 1536), (228, 1536)]),
    "xunlong-top": ("xunlong-top.png", None,
                    [(267, 208), (953, 206), (951, 667), (267, 668)]),
    "xunlong-bottom": ("xunlong-bottom.png", "y",
                       [(303, 176), (1006, 175), (1007, 637), (301, 638)]),
}
#: Which view of the same board each top view's parallax is measured against.
PAIRS = {"sunxi-v1p3-top": "sunxi-v1p3-bottom", "xunlong-top": "xunlong-bottom"}

#: Where each board edge cannot be seen for a connector in front of it, board
#: frame, millimetres.  Only a choice of where to look for the edge.
HIDDEN = {"bottom": [(7, 19), (30, 46), (59, 70)], "top": [(60, 70)],
          "left": [(6, 14), (14.5, 29.5), (34, 44)],
          "right": [(6, 21.3), (23.3, 41.3), (41.7, 49.5)]}
CORNER = 3.5            # the rounded corners are not edge

#: Header pin tip height above the board, for the parallax fit only: a
#: 2.54 mm header's 2.5 mm insulator and 6 mm of pin.
TIP_HEIGHT = 8.5

#: Each part's height above the board, for the parallax correction only; a
#: 2 mm error here moves a corrected edge by at most 0.4 mm on these views.
Z = {"usb_a_1": 13.5, "ethernet": 13.5, "usb_a_2": 15.5, "hdmi": 6.5,
     "power": 6.5, "audio": 6.0, "usb_otg": 3.0, "button": 3.5,
     "ir": 7.0, "camera": 2.5, "uart": 2.5}

#: Top-face edges read off the rectified top views: x0, y0, x1, y1, mm.
READ_TOP = {
    "sunxi-v1p3-top": {
        "usb_a_1": (70.0, 45.4, 90.4, 51.3), "ethernet": (68.9, 25.4, 90.7, 42.3),
        "usb_a_2": (73.0, 7.4, 91.0, 21.1), "hdmi": (29.3, -1.8, 44.6, 9.9),
        "power": (6.3, -1.9, 14.6, 10.9), "audio": (61.3, -2.0, 67.0, 11.8),
        "usb_otg": (-1.6, 35.8, 4.4, 43.2), "button": (-1.8, 7.9, 3.9, 12.6),
        "ir": (63.3, 50.9, 68.9, 57.6), "camera": (0.3, 15.6, 5.9, 32.4),
        "uart": (17.3, 0.9, 25.6, 3.4)},
    "xunlong-top": {
        "usb_a_1": (71.0, 43.9, 91.8, 49.4), "ethernet": (69.0, 24.1, 91.8, 40.3),
        "usb_a_2": (74.9, 5.0, 92.0, 17.9), "hdmi": (29.7, -2.7, 44.9, 9.8),
        "power": (7.0, -2.8, 15.1, 10.1), "audio": (62.0, -2.8, 67.2, 11.9),
        "usb_otg": (-1.4, 35.7, 4.4, 43.4), "button": (-1.2, 7.6, 4.1, 12.6),
        "ir": (63.4, 51.9, 68.8, 56.9), "camera": (0.4, 15.6, 6.1, 32.1),
        "uart": (17.3, 0.9, 25.8, 3.6)},
}
#: What the bottom views see past the board edge, which is the part's
#: underside, practically in the board plane: the extent along the edge, and
#: how far out it reaches.  (lo, hi, reach), mm.
READ_OVERHANG = {
    "sunxi-v1p3-bottom": {"power": (7.9, 16.2, -1.7), "hdmi": (30.7, 45.0, -1.9),
                          "audio": (62.3, 67.3, -1.9), "usb_a_1": (43.1, 49.5, 89.0),
                          "ethernet": (24.5, 40.7, 88.8), "usb_a_2": (6.9, 20.8, 88.9),
                          "usb_otg": (36.1, 42.1, -0.7)},
    "xunlong-bottom": {"power": (7.8, 16.4, -1.6), "hdmi": (30.8, 45.3, -1.4),
                       "audio": (62.4, 67.4, -1.8), "usb_a_1": (43.1, 49.4, 89.3),
                       "ethernet": (25.0, 40.6, 88.9), "usb_a_2": (7.2, 20.6, 89.0),
                       "usb_otg": (35.9, 42.2, -0.7)},
}
#: The microSD socket is on the underside, so a bottom view sees it square on.
READ_SD = {"sunxi-v1p3-bottom": (-0.6, 16.8, 13.9, 31.2),
           "xunlong-bottom": (-0.8, 16.5, 13.9, 31.0)}

HOLES = {"MT1": (2.9, 2.9), "MT2": (82.1, 2.9), "MT3": (2.9, 53.1), "MT4": (82.1, 53.1)}



def solder_joints(rect) -> dict:
    """The header's 40 solder joints in a bottom view, by (row, pin index).

    Row 0 is the row nearer the board centre, the one pin 1 is in; index 0 is
    the end with the square pad.  Each joint is whatever differs most from
    the board's own colour near where the 2.54 mm grid says it is.
    """
    x0, y0 = FRAME.to_px(20, 30)
    x1, y1 = FRAME.to_px(40, 20)
    board = np.median(rect[int(y0):int(y1), int(x0):int(x1)].reshape(-1, 3), 0)
    weight = np.linalg.norm(rect.astype(float) - board, axis=2)
    return {(row, i): blob(rect, FRAME, 9.7 + i * 2.54, 50.9 + row * 2.54,
                           1.1, weight)
            for row in (0, 1) for i in range(20)}


def pin_tips(rect) -> dict:
    """The header's 40 pin tips in a top view: the brightest tenth near each."""
    grey = cv2.cvtColor(rect, cv2.COLOR_BGR2GRAY).astype(float)
    out = {}
    for row in (0, 1):
        for i in range(20):
            x, y = 9.7 + i * 2.54, 51.1 + row * 2.54
            for _ in range(3):
                cx, cy = FRAME.to_px(x, y)
                r = 0.9 * FRAME.px_per_mm
                w = grey[int(cy - r):int(cy + r), int(cx - r):int(cx + r)]
                yy, xx = np.nonzero(w >= np.percentile(w, 90))
                x, y = FRAME.to_mm(int(cx - r) + xx.mean(), int(cy - r) + yy.mean())
            out[(row, i)] = (x, y)
    return out


def header_fit(joints: dict) -> dict:
    """Pin 1, the pitch along the rows and the spacing between them."""
    keys = np.array(list(joints), float)
    xy = np.array(list(joints.values()))
    A = np.c_[np.ones(len(keys)), keys[:, 1], keys[:, 0]]
    sx = np.linalg.lstsq(A, xy[:, 0], rcond=None)[0]
    sy = np.linalg.lstsq(A, xy[:, 1], rcond=None)[0]
    r = np.hypot(xy[:, 0] - A @ sx, xy[:, 1] - A @ sy)
    return dict(pin1_x=sx[0], pin1_y=sy[0], pitch=sx[1], span=19 * sx[1],
                rows=sy[2], rms=float(np.sqrt((r ** 2).mean())))


def parallax(tips: dict, joints: dict) -> tuple[float, float, float]:
    """Where the lens is over the board, and how far away, from the header.

    A tip at height h is drawn at c + k (p - c), p being its joint in the
    board plane and k = D / (D - h).  Solved for k and c by least squares
    over all 40 pins; returns (cx, cy, D).
    """
    keys = sorted(set(tips) & set(joints))
    p = np.array([joints[k] for k in keys])
    t = np.array([tips[k] for k in keys])
    A = np.zeros((2 * len(keys), 3))
    A[0::2, 0], A[0::2, 1] = p[:, 0], 1
    A[1::2, 0], A[1::2, 2] = p[:, 1], 1
    k, ax, ay = np.linalg.lstsq(A, t.reshape(-1), rcond=None)[0]
    return ax / (1 - k), ay / (1 - k), TIP_HEIGHT * k / (k - 1)


def unparallax(box, z: float, cx: float, cy: float, d: float):
    """A top face read at height *z*, put back where it stands on the board."""
    k = d / (d - z)
    x0, y0, x1, y1 = box
    return (cx + (x0 - cx) / k, cy + (y0 - cy) / k,
            cx + (x1 - cx) / k, cy + (y1 - cy) / k)


def fmt(v) -> str:
    return " ".join(f"{a:7.2f}" for a in v)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids", type=Path,
                    help="write the gridded rectified views the readings are "
                         "taken from into this directory")
    args = ap.parse_args()

    rect = {}
    print(f"frame: {FRAME.width:.2f} x {FRAME.height:.2f} mm\n")
    print("--- board edges, and the height the photograph itself gives ---")
    for name, (file, flip, approx) in PHOTOS.items():
        img = cv2.imread(str(SRC / file))
        if img is None:
            raise SystemExit(f"{SRC / file} missing: run tools/fetch_orangepi_pc.sh")
        corners, fits, rect[name] = fit_board(img, FRAME, approx, flip,
                                              HIDDEN, CORNER)
        h = photographed_height(corners, FRAME.width)
        print(f"  {name:18s} edge rms px " + " ".join(f"{r:4.2f}" for r, _ in fits)
              + f"   height {h:6.2f} (vs {FRAME.height:.0f}: {h - FRAME.height:+.2f},"
              f" vs {MANUAL_HEIGHT:.0f}: {h - MANUAL_HEIGHT:+.2f})")

    print("\n--- mounting holes: ring centre, drilled hole and ring diameters ---")
    holes = {}
    for label, (x, y) in HOLES.items():
        for name in PHOTOS:
            r = ring(rect[name], FRAME, x, y)
            o, i = r["outer"], r.get("inner")
            holes.setdefault(label, []).append((o["x"], o["y"]))
            print(f"  {label} {name:18s} ({o['x']:6.2f}, {o['y']:6.2f})  hole "
                  + (f"{i['dia']:4.2f}" if i else "  - ") + f"  ring {o['dia']:4.2f}")
        pts = np.array(holes[label])
        m, spread = pts.mean(0), np.ptp(pts, 0)
        print(f"  {label} mean ({m[0]:6.2f}, {m[1]:6.2f})  spread "
              f"{spread[0]:.2f} x {spread[1]:.2f}\n")

    print("--- 40-pin header, from the solder joints ---")
    joints = {}
    for name in PAIRS.values():
        joints[name] = solder_joints(rect[name])
        f = header_fit(joints[name])
        print(f"  {name:18s} pin 1 ({f['pin1_x']:6.2f}, {f['pin1_y']:6.2f})  "
              f"pitch {f['pitch']:.3f}  pin 1-39 {f['span']:6.2f} "
              f"({f['span'] - 48.26:+.2f})  rows {f['rows']:.2f} "
              f"({f['rows'] - 2.54:+.2f})  rms {f['rms']:.2f}")

    print("\n--- connectors, top face read and corrected for parallax ---")
    for top, bottom in PAIRS.items():
        cx, cy, d = parallax(pin_tips(rect[top]), joints[bottom])
        print(f"  {top}: lens over ({cx:.1f}, {cy:.1f}), {d:.0f} mm off the board")
        for part, box in READ_TOP[top].items():
            print(f"    {part:9s} read {fmt(box)}   corrected "
                  f"{fmt(unparallax(box, Z[part], cx, cy, d))}")
    print("\n--- overhangs seen from below: along the edge, and reach ---")
    for name, parts in READ_OVERHANG.items():
        print(f"  {name}: " + "  ".join(f"{p} {fmt(v)}" for p, v in parts.items()))
    print("\n--- microSD socket, underside ---")
    for name, box in READ_SD.items():
        print(f"  {name:18s} {fmt(box)}")

    if args.grids:
        args.grids.mkdir(parents=True, exist_ok=True)
        for name, r in rect.items():
            cv2.imwrite(str(args.grids / f"{name}.png"),
                        grid_image(r, FRAME, (-4, -5, 94, 60)))
        print(f"\ngridded views written to {args.grids}")


if __name__ == "__main__":
    main()
