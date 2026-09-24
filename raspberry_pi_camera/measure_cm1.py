#!/usr/bin/env python3
"""Measure the Camera Module v1.3 off Gert van Loo's 2013 drawing.

Raspberry Pi never published a mechanical drawing for the OV5647 camera.  The
nearest thing is a one-page sheet Gert van Loo drew on 21 May 2013 and posted
the same day in the Raspberry Pi forum's camera board thread "Mechanical
data": "As with the raspberry-Pi mechanical data it is hand
measured, accuracy about 0.05 mm no guarantees."  It is on Scribd, and
``tools/fetch_raspberry_pi_camera.sh`` caches the page image and its text
layer in ``tmp/rpi/cm1``.

The sheet prints most of what a mount needs, and ``v1.py`` takes those figures
as printed.  A few things it draws and does not dimension: how long the FFC
connector is along the board edge, where the sensor's flex tail runs, how
tall that tail stands, and the steps of the lens stack.  Those are *scaled* off the
drawing here, the way ``accessories/measure_pmod_hat.py`` scales the Pmod HAT
Adapter off a photograph.

The drawing says "scale 5:1", but that is not taken on trust any more than a
PDF's plot scale is.  The scale is recovered from the two overall dimensions,
25 and 23.9, one on each axis, and then *checked* against every other figure
the sheet prints, none of which was used to derive it.  The worst of those
residuals is the error bar on everything scaled.

Frame: the drawing's own.  The plan view puts the FFC connector on the left
edge and looks at the lens side; ``u`` is millimetres in from that edge,
across the 23.9, and ``v`` millimetres up from the lower edge, across the 25.
``v1.py`` turns the drawing a quarter turn clockwise into the family's frame,
connector edge at the top.

Run: uv run --no-project --with pillow --with numpy python \\
         raspberry_pi_camera/measure_cm1.py
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMAGE = ROOT / "tmp" / "rpi" / "cm1" / "scribd-page1-original.jpg"

#: The one image the search windows below were fitted to.  Any other image,
#: even of the same page, is a different set of pixels, and the windows have
#: to be looked at again rather than trusted.
IMAGE_SHA256 = "777292c4b75b445d4277f8d8bad232de77002924d087ce43b1b54b79d4320aca"

#: Ink, on an 8-bit grey scale.  The sheet is black line work on white, JPEG
#: compressed, so anything darker than mid grey is a line.
INK = 128

#: The figures the sheet prints for the board's overall size.  These two set
#: the scale and nothing else does.
PRINTED_ACROSS = 23.9       # u, connector edge to far edge
PRINTED_UP = 25.0           # v, lower edge to upper edge


@dataclass(frozen=True)
class Check:
    """A figure the sheet prints, beside the same distance scaled off it."""

    printed: float
    drawn: float
    what: str

    @property
    def residual(self) -> float:
        return self.drawn - self.printed


def _ink(path: Path) -> np.ndarray:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != IMAGE_SHA256:
        raise SystemExit(
            f"{path} is not the page image this script was fitted to "
            f"(sha256 {digest}, expected {IMAGE_SHA256}).  Every search "
            "window below is in that image's pixels; look at the new one and "
            "refit them before trusting a number from it.")
    grey = np.asarray(Image.open(path).convert("L")).astype(int)
    return grey < INK


def _runs(line: np.ndarray, offset: int) -> list[tuple[int, int]]:
    """Inclusive (first, last) index of each run of ink along *line*."""
    idx = np.nonzero(line)[0]
    if not len(idx):
        return []
    runs, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i != prev + 1:
            runs.append((start + offset, prev + offset))
            start = i
        prev = i
    runs.append((start + offset, prev + offset))
    return runs


def _line_at(profile: np.ndarray, lo: int, hi: int, min_ink: int) -> float:
    """Centre of the one long line whose ink count in *profile* passes
    *min_ink* between indices *lo* and *hi*.  A drawn line is one or two
    pixels wide, so its centre is the mean of the indices that pass."""
    hits = [i for i in range(lo, hi) if profile[i] >= min_ink]
    if not hits or max(hits) - min(hits) > 3:
        raise SystemExit(f"expected one line between {lo} and {hi}, found "
                         f"ink at {hits}")
    return float(np.mean(hits))


def _circle(ink: np.ndarray, cx: int, cy: int, r_in: float, r_out: float,
            box: int = 30, off_axis: bool = False
            ) -> tuple[float, float, float]:
    """Least-squares circle through the ink in an annulus round (cx, cy).

    The annulus keeps out the centre lines that cross every hole; where a
    centre line is long enough to cross the annulus too, *off_axis* keeps
    only ink more than 10 degrees off both axes."""
    ys, xs = np.nonzero(ink[cy - box:cy + box, cx - box:cx + box])
    xs, ys = xs + cx - box, ys + cy - box
    d = np.hypot(xs - cx, ys - cy)
    keep = (d > r_in) & (d < r_out)
    if off_axis:
        ang = np.degrees(np.arctan2(np.abs(ys - cy), np.abs(xs - cx)))
        keep &= (ang > 10) & (ang < 80)
    xs, ys = xs[keep], ys[keep]
    a = np.c_[2 * xs, 2 * ys, np.ones(len(xs))]
    (x0, y0, c), *_ = np.linalg.lstsq(a, xs ** 2 + ys ** 2, rcond=None)
    return float(x0), float(y0), float(np.sqrt(c + x0 ** 2 + y0 ** 2))


def measure(path: Path = IMAGE) -> dict:
    """Everything this script reads off the sheet, in millimetres.

    Returns the scale, the checks against printed figures, and the scaled
    figures ``v1.py`` uses, all in the drawing's (u, v) frame."""
    ink = _ink(path)

    # --- the plan view's board outline --------------------------------
    # Long vertical lines in the band the plan view occupies, then long
    # horizontal ones.  The left edge is drawn heavy where the connector's
    # face sits on it, so it is taken as the thin outline line's column.
    plan = ink[280:760, :]
    cols = plan.sum(axis=0)
    rows = ink[:, 150:700].sum(axis=1)
    left = _line_at(cols, 176, 184, 440)
    right = _line_at(cols, 612, 624, 440)
    top = _line_at(rows, 286, 296, 420)
    bottom = _line_at(rows, 744, 754, 420)

    px_u = (right - left) / PRINTED_ACROSS
    px_v = (bottom - top) / PRINTED_UP

    def u(x: float) -> float:
        return (x - left) / px_u

    def v(y: float) -> float:
        return (bottom - y) / px_v

    # --- the four holes ------------------------------------------------
    holes = [_circle(ink, cx, cy, 12, 24)
             for cx, cy in ((354, 327), (580, 327), (354, 712), (580, 712))]
    near_u = np.mean([h[0] for h in holes if h[0] < 470])
    far_u = np.mean([h[0] for h in holes if h[0] > 470])
    low_v = np.mean([h[1] for h in holes if h[1] > 520])
    high_v = np.mean([h[1] for h in holes if h[1] < 520])
    hole_dia = np.mean([2 * h[2] for h in holes]) / ((px_u + px_v) / 2)

    # --- the lens and sensor module, and its flex tail ----------------
    # The module is the square box; the tail is the outline that runs on
    # from its far side to the sensor's own connector, J2.
    # The box's two long sides across, found as lines; its two sides up,
    # as the first and last ink on a column through the box that misses
    # the centre lines.
    lens_u0 = _line_at(cols, 270, 280, 140)
    lens_u1 = _line_at(cols, 417, 426, 140)
    lens_vruns = _runs(ink[430:610, 300], 430)
    lens_top = (lens_vruns[0][0] + lens_vruns[0][1]) / 2
    lens_bot = (lens_vruns[-1][0] + lens_vruns[-1][1]) / 2
    # The larger of the two concentric circles drawn inside the module, the
    # lens barrel.  Fitted rather than read off one line, since both centre
    # lines run through it.
    lens_cx, lens_cy = (lens_u0 + lens_u1) / 2, (lens_top + lens_bot) / 2
    barrel = _circle(ink, round(lens_cx), round(lens_cy), 61, 71, box=75,
                     off_axis=True)
    barrel_outer = 2 * barrel[2] / ((px_u + px_v) / 2)
    # The tail's far end: the last ink in the module's band short of the
    # board edge, which is the rounded end of the tail over J2.
    tail_end = max(x for x in range(424, 612) if ink[440:600, x].any())

    # --- the underside connector, dashed in the plan view -------------
    dashed = ink[300:740, 190:283].sum(axis=1)
    dash_rows = [i + 300 for i in range(len(dashed)) if dashed[i] >= 40]
    conn_top = np.mean([y for y in dash_rows if y < 400])
    conn_bot = np.mean([y for y in dash_rows if y > 650])
    conn_back = _line_at(ink[330:710, :].sum(axis=0), 280, 290, 150)

    # --- the FFC cable, off the left edge -----------------------------
    cable = [y for y in range(330, 720) if ink[y, 60:178].sum() > 60]
    cable_top = np.mean([y for y in cable if y < 500])
    cable_bot = np.mean([y for y in cable if y > 500])

    # --- the elevation below it ---------------------------------------
    side_rows = ink[:, 180:620].sum(axis=1)
    board_top = _line_at(side_rows, 934, 942, 400)
    board_bot = _line_at(side_rows, 952, 958, 400)
    # The lens stack in elevation is three boxes one on another -- the
    # module body, a round holder, a thin ring at the tip -- and each is
    # topped by a horizontal line at least 90 pixels long.  Each line's
    # height and length is one step of the profile.
    steps = []
    for y in range(835, 936):
        long_runs = [r for r in _runs(ink[y, 260:430], 260)
                     if r[1] - r[0] >= 90]
        if long_runs:
            r = max(long_runs, key=lambda r: r[1] - r[0])
            if steps and y - steps[-1][0][-1] <= 2:
                steps[-1][0].append(y)
                steps[-1][1].append(r[1] - r[0] + 1)
            else:
                steps.append(([y], [r[1] - r[0] + 1]))
    if len(steps) != 3:
        raise SystemExit(f"expected the lens stack in three steps, found "
                         f"{len(steps)}")
    profile = [(float(np.mean(ys)), max(ws)) for ys, ws in steps]
    lens_tip = profile[0][0]
    conn_foot = _line_at(ink[:, 190:280].sum(axis=1), 1000, 1012, 60)
    # J2 and the flex over it: the highest ink over the board beyond the
    # lens module, which is where the flex arches over the connector.
    j2_top = min(y for y in range(890, 938)
                 if ink[y, 430:615].sum() > 0)
    px_z = (px_u + px_v) / 2

    checks = [
        Check(21.85, u(far_u), "connector edge to far hole centres"),
        Check(9.35, u(near_u), "connector edge to near hole centres"),
        Check(23.0, v(high_v), "lower edge to upper hole centres"),
        Check(2.0, v(low_v), "lower edge to lower hole centres"),
        Check(2.0, hole_dia, "hole diameter"),
        Check(5.1, u(lens_u0), "connector edge to lens module"),
        Check(8.0, (lens_bot - lens_top) / px_v, "lens module, plan, up"),
        Check(8.0, (lens_u1 - lens_u0) / px_u, "lens module, plan, across"),
        Check(5.6, u(conn_back), "connector depth, plan"),
        Check(16.2, (cable_bot - cable_top) / px_v, "FFC cable width"),
        Check(0.95, (board_bot - board_top) / px_z, "board thickness"),
        Check(5.2, (board_top - lens_tip) / px_z, "lens tip above board"),
        Check(2.8, (conn_foot - board_bot) / px_z, "connector below board"),
    ]

    return dict(
        px_per_mm=(px_u, px_v),
        checks=checks,
        worst=max(abs(c.residual) for c in checks),
        # Scaled, not printed: what v1.py takes from this script.
        connector_v=(v(conn_bot), v(conn_top)),
        lens_v=(v(lens_bot), v(lens_top)),
        barrel_dia=barrel_outer,
        tail_u=(u(lens_u1), u(tail_end)),
        tail_height=(board_top - j2_top) / px_z,
        # Top of each step above the board, and its width, from the tip down.
        lens_profile=[((board_top - y) / px_z, w / px_z) for y, w in profile],
    )


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else IMAGE
    m = measure(path)
    px_u, px_v = m["px_per_mm"]
    print(f"scale: {px_u:.3f} px/mm across, {px_v:.3f} px/mm up "
          f"({abs(px_u - px_v) / px_v * 100:.2f} % apart)")
    print("\nprinted figures, not used for the scale, against the drawing:")
    for c in m["checks"]:
        print(f"  {c.what:38s} printed {c.printed:6.2f}  drawn "
              f"{c.drawn:6.2f}  residual {c.residual:+.2f}")
    print(f"  worst residual {m['worst']:.2f} mm")
    print("\nscaled, not printed:")
    v0, v1 = m["connector_v"]
    print(f"  FFC connector, along the edge  v {v0:.2f} to {v1:.2f}, "
          f"{v1 - v0:.2f} long")
    l0, l1 = m["lens_v"]
    print(f"  lens module, across            v {l0:.2f} to {l1:.2f}")
    print(f"  lens barrel, outer circle      dia {m['barrel_dia']:.2f}")
    t0, t1 = m["tail_u"]
    print(f"  flex tail, from the module     u {t0:.2f} to {t1:.2f}")
    print(f"  flex tail and J2, above board  {m['tail_height']:.2f}")
    for z, w in m["lens_profile"]:
        print(f"  lens stack step, top at        {z:.2f} above board, "
              f"{w:.2f} across")


if __name__ == "__main__":
    main()
