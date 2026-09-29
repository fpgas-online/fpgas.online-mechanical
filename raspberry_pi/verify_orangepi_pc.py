#!/usr/bin/env python3
"""Check the Orange Pi PC's measured geometry against what it was not fitted to.

``orangepi_pc.py`` records every reading ``measure_orangepi_pc.py`` took off
the photographs, adopts a figure from them and quotes a tolerance.  This
holds the result to checks the measurement did not use, and fails if any
check lands outside the tolerance the sheet prints -- twice it, where two
positions are compared by the distance between them:

1. **The tolerance covers the readings.**  It must be at least the furthest
   any photograph's reading lies from the figure drawn, and for holes and
   header, the furthest any check on them lies.
2. **The 40-pin header.**  Fitted to the board's edges, it came out long:
   48.58 and 48.48 mm from pin 1 to pin 39 where it is 48.26.  That check
   found the fit 0.5 to 0.7 % wide across the board, and ``orangepi_pc.py``
   now takes its scale across the board from the header, so this prints
   what the check found and then holds to the tolerance what is left: the
   two photographs' headers against each other, the rows' 2.54 mm spacing,
   which the correction does not touch, and the board's own edges on the
   header's scale.
3. **The board** is 56 mm tall in the photographs' own proportions, not the
   55 of Xunlong's manual.
4. **Standard parts** are the size the same part is on Raspberry Pi Ltd's
   drawings, or failing one there, on Xunlong's PC Plus drawing.
5. **Third-party models**, from ``crosscheck_orangepi_pc.py``: the hole
   pattern of every case, and the holes, header and part positions of
   Xunlong's PC Plus drawing and of Roman Gachin's model, and where
   landroo's case cuts its walls.  A part is compared by its centre along
   the edge it sits on, which is what a cut-out has to match and what every
   source draws the same way; each source draws a part's extent differently
   -- a body, a courtyard, a clearance.  A third-party figure outside the
   tolerance is accepted only if it is outside it against Xunlong's own
   drawing as well: then it is that model that is wrong, not this one.

Needs nothing but the repository: every third-party figure is recorded here
as ``crosscheck_orangepi_pc.py`` printed it, so this runs where the models
have not been fetched.

Run: uv run --no-project python raspberry_pi/verify_orangepi_pc.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from raspberry_pi import orangepi_pc as opi  # noqa: E402
from raspberry_pi.boards import BOARDS as PIS  # noqa: E402

# ---------------------------------------------------------------------------
# Third-party figures, as crosscheck_orangepi_pc.py printed them
# ---------------------------------------------------------------------------

#: Xunlong's Orange Pi PC Plus assembly drawing, ASMTOP.dwg and ASMBOT.dwg:
#: part outlines found by designator, x0, y0, x1, y1.
PC_PLUS = {
    "ethernet": (67.66, 24.84, 89.25, 40.33), "usb_a_1": (69.65, 42.48, 89.25, 50.19),
    "usb_a_2": (71.90, 6.42, 89.25, 20.82), "hdmi": (29.74, -1.78, 44.75, 6.98),
    "power": (7.50, -1.78, 15.50, 11.52), "audio": (61.57, -2.08, 67.77, 11.92),
    "usb_otg": (-0.91, 35.60, 5.09, 43.20), "button": (1.29, 7.92, 4.29, 12.72),
    "ir": (62.28, 50.67, 69.08, 55.87), "uart": (18.31, 1.30, 25.93, 3.84),
    "microsd": (-0.17, 16.38, 13.03, 31.18),
}
PC_PLUS_HOLES = {"MT1": (2.944, 2.944), "MT2": (82.056, 2.944),
                 "MT3": (2.944, 53.056), "MT4": (82.056, 53.056)}
#: The header's body outline is 8.57..59.37 by 49.50..54.58: pin 1 is
#: 1.27 in from its lower-left corner.
PC_PLUS_PIN1 = (9.84, 50.77)

#: Roman Gachin's 3MF, sectioned; holes 2.925 in from every edge.
GACHIN = {
    "ethernet": (68.65, 24.30, 89.95, 40.30), "usb_a_1": (69.95, 42.70, 89.95, 48.50),
    "usb_a_2": (72.45, 7.05, 89.95, 20.30), "hdmi": (30.73, -2.10, 45.47, 9.15),
    "power": (8.95, -2.00, 17.25, 10.70), "audio": (62.05, -2.20, 68.55, 11.90),
    "usb_otg": (-0.95, 35.40, 4.55, 42.95), "button": (-0.55, 7.85, 4.25, 12.45),
    "ir": (62.25, 51.08, 68.15, 56.53), "camera": (1.45, 15.40, 6.35, 31.85),
    "uart": (19.80, 1.60, 26.80, 4.18), "microsd": (-3.20, 16.45, 14.75, 31.75),
}
GACHIN_HOLES = {"MT1": (2.925, 2.925), "MT2": (82.075, 2.925),
                "MT3": (2.925, 53.075), "MT4": (82.075, 53.075)}
#: Gachin's pin 1.  His rows are 3.19 mm apart where a header's are 2.54, so
#: only the X of his pin 1, and his 2.54 pitch along the rows, are compared.
GACHIN_PIN1_X = 9.82

#: landroo's case: the wall cut-outs, along the wall, in the case's own
#: frame, whose standoffs are centred on (43, 28).
LANDROO_CUTS = {"power": (8.00, 16.50), "hdmi": (29.98, 46.02), "audio": (62.54, 68.50),
                "ir": (64.00, 68.00), "button": (7.51, 11.49), "microsd": (16.00, 28.00),
                "usb_otg": (33.51, 44.49), "usb_a_2": (7.00, 22.50),
                "ethernet": (25.00, 41.50), "usb_a_1": (43.50, 50.50)}
LANDROO_CENTRE = (43.0, 28.0)

#: Every case's standoff pattern, long side first.
CASE_PITCH = {"aristotelov": (79.15, 50.00), "jargov": (78.96, 50.01),
              "landroo": (80.00, 50.00), "lowich": (78.99, 50.00),
              "maghirang": (78.96, 50.00), "mexus": (78.97, 50.01),
              "n7cat": (79.53, 49.98), "stanley": (78.99, 50.00)}

#: The axis each part's position along its edge is on.
ALONG = {"power": 0, "hdmi": 0, "audio": 0, "ir": 0, "uart": 0,
         "button": 1, "microsd": 1, "usb_otg": 1, "usb_a_2": 1,
         "ethernet": 1, "usb_a_1": 1, "camera": 1}

#: Which Raspberry Pi feature, on which model, is the same kind of part, and
#: the axis along the edge it sits on there: the Pi 3B's micro-USB is on its
#: lower edge, this board's on its left.
PI_SAME = {"ethernet": [(m, "ethernet", 1) for m in ("rpi3b", "rpi4b", "rpi5")],
           "usb_a_2": [(m, k, 1) for m in ("rpi3b", "rpi4b", "rpi5")
                       for k in ("usb_a_1", "usb_a_2")],
           "usb_otg": [("rpi3b", "usb_power", 0)]}
#: Parts with no counterpart on a Pi drawing, held to Xunlong's PC Plus
#: instead.  The upright USB is in neither: the PC Plus outline takes in its
#: mounting tabs, and no Pi has one.
PC_PLUS_SAME = ("hdmi", "power", "audio")


def box(part: str):
    return opi.MICROSD if part == "microsd" else opi.adopted(part)


def centre(b, axis: int) -> float:
    return (b[axis] + b[axis + 2]) / 2


def width(b, axis: int) -> float:
    return b[axis + 2] - b[axis]


def main() -> int:
    failures: list[str] = []

    def check(ok: bool, line: str) -> None:
        print(("  ok    " if ok else "  FAIL  ") + line)
        if not ok:
            failures.append(line)

    print("1. the tolerance covers the readings")
    worst_board = max(opi.board_residuals().items(), key=lambda kv: kv[1])
    worst_part = max(opi.part_residuals().items(), key=lambda kv: kv[1])
    check(opi.BOARD_TOL >= worst_board[1],
          f"holes and header +/-{opi.BOARD_TOL}: worst {worst_board[1]:.2f}, "
          f"{worst_board[0]}")
    check(opi.PARTS_TOL >= worst_part[1],
          f"parts +/-{opi.PARTS_TOL}: worst {worst_part[1]:.2f}, {worst_part[0]}")

    print("2. the 40-pin header")
    for name, h in opi.HEADER_SEEN.items():
        print(f"  found {name}: pin 1 to pin 39 {h['span']:.2f} on the edges' "
              f"scale, against 48.26 ({(h['span'] / 48.26 - 1) * 100:+.2f} %)")
        scaled = h["span"] * opi.X_SCALE
        check(abs(scaled - 48.26) <= opi.BOARD_TOL,
              f"{name}: pin 1 to pin 39 {scaled:.2f} on the header's scale "
              f"({scaled - 48.26:+.2f})")
        check(abs(h["rows"] - 2.54) <= opi.BOARD_TOL,
              f"{name}: rows {h['rows']:.2f} apart against 2.54")
        edge = abs(opi.WIDTH - opi.WIDTH * 48.26 / h["span"]) / 2
        check(edge <= opi.BOARD_TOL,
              f"{name}: board {opi.WIDTH * 48.26 / h['span']:.2f} wide on the "
              f"header's scale, each edge {edge:.2f} from where it is drawn")

    print("3. the board's height, as the photographs have it")
    h = median(opi.PHOTO_HEIGHT.values())
    check(abs(h - opi.HEIGHT) <= opi.BOARD_TOL < abs(h - opi.MANUAL_HEIGHT),
          f"median {h:.2f} of " + ", ".join(f"{v:.2f}" for v in opi.PHOTO_HEIGHT.values())
          + f": {h - opi.HEIGHT:+.2f} from {opi.HEIGHT:.0f}, "
          f"{h - opi.MANUAL_HEIGHT:+.2f} from the manual's {opi.MANUAL_HEIGHT:.0f}")

    print("4. standard parts, across the edge they sit on")
    for part, same in PI_SAME.items():
        w = width(box(part), ALONG[part])
        refs = [width((f.x0, f.y0, f.x1, f.y1), axis)
                for m, k, axis in same for f in PIS[m].features if f.key == k]
        off = 0.0 if min(refs) <= w <= max(refs) else min(abs(w - r) for r in refs)
        check(off <= opi.PARTS_TOL,
              f"{part} {w:.2f} wide; on the Pi drawings {min(refs):.2f} to "
              f"{max(refs):.2f}, off by {off:.2f}")
    for part in PC_PLUS_SAME:
        w, r = width(box(part), ALONG[part]), width(PC_PLUS[part], ALONG[part])
        check(abs(w - r) <= opi.PARTS_TOL,
              f"{part} {w:.2f} wide; on the PC Plus drawing {r:.2f} ({w - r:+.2f})")

    print("5. third-party models")
    x0, y0 = opi.HOLES_AT["MT1"]
    x1, y1 = opi.HOLES_AT["MT4"]
    xun = (PC_PLUS_HOLES["MT4"][0] - PC_PLUS_HOLES["MT1"][0],
           PC_PLUS_HOLES["MT4"][1] - PC_PLUS_HOLES["MT1"][1])
    for case, (px, py) in CASE_PITCH.items():
        off = max(abs(x1 - x0 - px), abs(y1 - y0 - py))
        ok = off <= 2 * opi.BOARD_TOL
        why = ""
        if not ok and max(abs(xun[0] - px), abs(xun[1] - py)) > 2 * opi.BOARD_TOL:
            ok, why = True, f"; {px - xun[0]:+.2f} from the PC Plus as well"
        check(ok, f"{case} case standoffs {px:.2f} x {py:.2f} against "
                  f"{x1 - x0:.2f} x {y1 - y0:.2f} "
                  f"({x1 - x0 - px:+.2f}, {y1 - y0 - py:+.2f}){why}")
    for label, (hx, hy) in opi.HOLES_AT.items():
        for src, holes in (("PC Plus", PC_PLUS_HOLES), ("Gachin", GACHIN_HOLES)):
            ox, oy = holes[label]
            check(max(abs(hx - ox), abs(hy - oy)) <= opi.BOARD_TOL,
                  f"{label} {src} ({ox:.2f}, {oy:.2f}), residual "
                  f"({hx - ox:+.2f}, {hy - oy:+.2f})")
    check(max(abs(a - b) for a, b in zip(opi.PIN1, PC_PLUS_PIN1)) <= opi.BOARD_TOL,
          f"header pin 1 PC Plus {PC_PLUS_PIN1}, residual "
          f"({opi.PIN1[0] - PC_PLUS_PIN1[0]:+.2f}, {opi.PIN1[1] - PC_PLUS_PIN1[1]:+.2f})")
    check(abs(opi.PIN1[0] - GACHIN_PIN1_X) <= opi.BOARD_TOL,
          f"header pin 1 X Gachin {GACHIN_PIN1_X}, residual "
          f"{opi.PIN1[0] - GACHIN_PIN1_X:+.2f}")

    shift = ((x0 + x1) / 2 - LANDROO_CENTRE[0], (y0 + y1) / 2 - LANDROO_CENTRE[1])
    print(f"   parts, by centre along the edge (landroo moved by "
          f"{shift[0]:+.2f}, {shift[1]:+.2f} onto the holes)")
    for part, axis in ALONG.items():
        here = centre(box(part), axis)
        xun = centre(PC_PLUS[part], axis) if part in PC_PLUS else None
        others = []
        if part in GACHIN:
            others.append(("Gachin", centre(GACHIN[part], axis)))
        if part in LANDROO_CUTS:
            lo, hi = LANDROO_CUTS[part]
            others.append(("landroo", (lo + hi) / 2 + shift[axis]))
        if xun is not None:
            check(abs(xun - here) <= opi.PARTS_TOL,
                  f"{part:9s} at {here:6.2f}: PC Plus {xun - here:+.2f}")
        for src, c in others:
            ok = abs(c - here) <= opi.PARTS_TOL
            why = ""
            if not ok and xun is not None and abs(c - xun) > opi.PARTS_TOL:
                ok, why = True, f"; {c - xun:+.2f} from the PC Plus as well"
            check(ok, f"{part:9s} at {here:6.2f}: {src} {c - here:+.2f}{why}")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) outside the sheet's tolerance")
        return 1
    print("\npass: every check within the tolerance the sheet quotes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
