#!/usr/bin/env python3
"""Check that the mounting plate really does accept every demo board revision.

The plate's whole claim is that any Tiny Tapeout demo board bolts to it while
its Pmod hosts land in one fixed place.  This proves it, from the two data
modules rather than from the drawing:

* every mounting hole on every revision falls inside a plate hole or slot, with
  enough clearance for an M3 fastener;
* every Pmod host pin field lands on one of the three plate positions;
* no board overhangs the plate;
* the Pmod connector bodies clear the plate's front edge;
* the standoff the plate specifies stands a board no lower than Tiny
  Tapeout's own printed base does, read back from that base's source.

Run: uv run --no-project python tinytapeout/mounting_plate/verify.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import re  # noqa: E402

from tinytapeout.mounting_plate.plate import (  # noqa: E402
    PLACEMENTS, PLATE, PMOD_ROW_Y, PMOD_SLOT_X, STANDOFF_HEIGHT,
    UPSTREAM_BASE_REF, UPSTREAM_BASE_STUD)
from tinytapeout.boards import BOARDS  # noqa: E402

M3_DIA = 3.0
POS_TOL = 0.05          # how far a Pmod may sit from its plate position
PMOD_BODY_OVERHANG = 11.78


def point_segment_distance(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def fastener_clearance(x: float, y: float) -> tuple[float, str]:
    """Best clearance an M3 shank has at (x, y), and what provides it."""
    best, why = -math.inf, "nothing"
    for h in PLATE.holes:
        if h.kind == "plate":
            continue
        c = (h.dia - M3_DIA) / 2 - math.dist((x, y), (h.x, h.y))
        if c > best:
            best, why = c, f"hole at ({h.x:.2f},{h.y:.2f}) dia {h.dia}"
    for s in PLATE.slots:
        d = point_segment_distance((x, y), (s.x0, s.y0), (s.x1, s.y1))
        c = (s.width - M3_DIA) / 2 - d
        if c > best:
            best, why = c, f"slot {s.label}"
    return best, why


#: Where ``make fetch`` leaves Tiny Tapeout's printed base.
UPSTREAM_BASE = ROOT / "tmp" / "src" / "tt-demo-pcb" / "case" / \
    "tt06_demo_base.scad"


def check_standoff() -> int:
    """The standoff against the stud of Tiny Tapeout's own base.

    ``plate.py`` records that stud as 6.4 mm; this reads the base's own
    source for the two numbers it comes from -- ``Height = 8`` and the PCB
    thickness it lets into the top, ``pcb_base(99.5, 78, 1.6, ...)`` -- so
    the figure the standoff is chosen against is not taken on trust.
    """
    if not UPSTREAM_BASE.exists():
        print(f"standoff: {UPSTREAM_BASE.relative_to(ROOT)} is not there; "
              "run `make fetch` to check it against the base\n")
        return 0
    text = UPSTREAM_BASE.read_text()
    height = float(re.search(r"^Height\s*=\s*([\d.]+)", text, re.M).group(1))
    pcb = float(re.search(r"pcb_base\([\d.]+,\s*[\d.]+,\s*([\d.]+)",
                          text).group(1))
    stud = height - pcb
    bad = 0
    ok = abs(stud - UPSTREAM_BASE_STUD) < 1e-9
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} upstream base stud {height:g} - "
          f"{pcb:g} = {stud:.2f} mm, plate.py records {UPSTREAM_BASE_STUD}")
    ok = STANDOFF_HEIGHT >= stud
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} the plate's {STANDOFF_HEIGHT:g} mm standoff "
          f"stands the board {STANDOFF_HEIGHT - stud:+.2f} mm against it "
          f"({UPSTREAM_BASE_REF.rsplit('/', 1)[-1]})\n")
    return bad


def main() -> None:
    o = PLATE.outline
    problems = 0
    print(f"Plate {o.width} x {o.height} mm, "
          f"{sum(1 for h in PLATE.holes if h.kind != 'plate')} board holes, "
          f"{len(PLATE.slots)} slot(s)\n")

    for name, pl in PLACEMENTS.items():
        board = BOARDS[pl["revision"]]
        dx, dy = pl["dx"], pl["dy"]
        print(f"{name}  (board rev {pl['revision']}, offset "
              f"{dx:.3f}, {dy:.3f})")

        for h in board.holes:
            x, y = h.x + dx, h.y + dy
            clear, why = fastener_clearance(x, y)
            ok = clear >= 0
            problems += not ok
            print(f"   {'ok  ' if ok else 'FAIL'} {h.label:<4} at "
                  f"({x:7.3f},{y:7.3f})  M3 clearance {clear:+.3f} mm  via {why}")

        for p in board.pmods:
            px, py = p.cx + dx, p.cy + dy
            nearest = min(PMOD_SLOT_X, key=lambda s: abs(s - px))
            dxe, dye = abs(px - nearest), abs(py - PMOD_ROW_Y)
            ok = dxe <= POS_TOL and dye <= POS_TOL
            problems += not ok
            print(f"   {'ok  ' if ok else 'FAIL'} {p.label:<6} pin field at "
                  f"({px:7.3f},{py:7.3f})  off plate position by "
                  f"({dxe:.3f},{dye:.3f}) mm")

        bo = board.outline
        inside = (dx >= 0 and dy >= 0 and dx + bo.width <= o.width
                  and dy + bo.height <= o.height)
        problems += not inside
        print(f"   {'ok  ' if inside else 'FAIL'} board occupies "
              f"x {dx:.3f}..{dx + bo.width:.3f}, y {dy:.3f}..{dy + bo.height:.3f} "
              f"of {o.width} x {o.height}")

        front = min(p.cy + dy - PMOD_BODY_OVERHANG for p in board.pmods)
        clears = front < 0
        problems += not clears
        print(f"   {'ok  ' if clears else 'FAIL'} Pmod connector faces reach "
              f"y = {front:+.3f}, {abs(front):.3f} mm "
              f"{'beyond' if clears else 'short of'} the plate front edge\n")

    problems += check_standoff()
    print("PASS: the plate accepts every revision" if not problems
          else f"FAIL: {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
