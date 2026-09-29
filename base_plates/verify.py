#!/usr/bin/env python3
"""Check that each base plate does what its sheet claims.

Five claims, for each plate, and nothing else about it matters:

* the adapter's plug rows meet the host rows: summed back up the parts as
  bought -- standoff, PCB, header, socket, adapter, plug -- against the
  host board's own stack, they are within the connectors' tolerance;
* the adapter's plugs land on the hosts: each plug's pin field over a
  host's, along the edge, within the play of a pin in a socket;
* nothing on the Pi under the adapter is taller than the adapter's
  underside, on the models the sheet says fit, and something is on the
  ones it says do not;
* nothing overlaps in plan that should not: the Pi and the FPGA board, the
  cups and the Arty's sockets, the adapter and the cups;
* every hole is inside the plate, clear of the edge, and clear of every
  other hole, and every hole the Pi needs is there.

Proved from ``plates.py`` against the data it was built from, reaching
each figure the way ``design.py`` did not where there is another way.

Run: uv run --no-project python base_plates/verify.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.raspmod_direct import RASPMOD_DIRECT  # noqa: E402
from base_plates import plates as P  # noqa: E402
from base_plates.model import Plate  # noqa: E402
from fpga.boards import BOARDS as FPGA  # noqa: E402
from raspberry_pi.boards import BOARDS as RPI  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE, PMOD_SLOT_X  # noqa: E402

results: list[tuple[bool, str, str]] = []

#: The connectors' own tolerances, summed: socket legs and body +/-0.2 each,
#: plug body +/-0.2, socket height +/-0.3.  A residual inside this is one
#: the parts themselves could produce.
ROW_TOL = 0.4
#: A 0.64 mm pin in a 1.03 mm hole, less a little.
PIN_PLAY = 0.15
#: How far apart two holes have to be to be drilled as two.
HOLE_WEB = 1.5
EDGE = 3.0


def check(ok: bool, what: str, detail: str) -> None:
    results.append((bool(ok), what, detail))


def levels(p: Plate) -> dict:
    return {n: v for n, v in p.levels}


def check_rows(p: Plate) -> None:
    z = levels(p)
    # Summed up the bought parts, not read from the stack.
    pi_top = z["Pi top face"]
    adapter_top = pi_top + 2.54 + 3.8 + RASPMOD_DIRECT.outline.thickness
    plug = tuple(round(adapter_top + r, 2) for r in (1.27, 3.81))
    host = tuple(round(z[k] + r, 2) for k in z if k in ("Demoboard top face", "Arty top face")
                 for r in (3.3 + 2.5 - 1.27, 3.3 + 2.5 + 1.27))
    d = plug[0] - host[0]
    check(abs(d) <= ROW_TOL, f"{p.key}: the plug rows meet the host rows",
          f"plug {plug} host {host}: {d:+.2f}, within {ROW_TOL}")
    check(abs(d - p.residual) < 0.011, f"{p.key}: the sheet's residual is that figure",
          f"sheet {p.residual:+.2f}, summed {d:+.2f}")
    check(plug == tuple(z["Plug rows"]) and host == tuple(z["Host socket rows"]),
          f"{p.key}: the level table's rows are the summed rows",
          f"table {z['Plug rows']} / {z['Host socket rows']}")


def host_centres(p: Plate) -> list[tuple[str, float, float]]:
    """Every host's pin-field centre on this plate, from the FPGA data."""
    if p.key == "tt-pi":
        tt = next(b for b in p.boxes if b.label == "TT-MP-PLATE")
        return [(f"host {i + 1}", tt.x0 + x, tt.y0 + 9.0) for i, x in enumerate(PMOD_SLOT_X)]
    # The Arty lies a half turn round on its plate, hosts to the front, so
    # its own coordinates count back from the box's far corner.
    arty = next(b for b in p.boxes if b.label == "Digilent Arty A7")
    return [(h.label, arty.x1 - h.cx, arty.y1 - h.cy) for h in FPGA["arty-a7"].pmods]


def check_plugs(p: Plate) -> None:
    hosts = host_centres(p)
    for pos in sorted({b.position for b in p.boxes if b.label.startswith("Plug ")}):
        plugs = [b for b in p.boxes if b.label.startswith("Plug ") and "pins" not in b.label
                 and b.position == pos]
        if len(plugs) != 3:
            check(False, f"{p.key}{pos}: three plugs", f"{len(plugs)} found")
            continue
        for b in plugs:
            # The plug body is centred on its pin field along the edge.
            near = min(hosts, key=lambda h: abs(h[1] - b.cx))
            check(abs(near[1] - b.cx) <= PIN_PLAY,
                  f"{p.key}{pos}: {b.label} lands on {near[0]}",
                  f"{near[1] - b.cx:+.2f} along the edge, within {PIN_PLAY}")
            # And the plug's pins reach into that socket: the pins' box has
            # to overlap the host body's box across the edge.
            pins = next(q for q in p.boxes if q.label == f"{b.label} pins" and q.position == pos)
            body = next(q for q in p.boxes if q.kind == "header" and q.label.startswith("Pmod host")
                        and abs(q.cx - near[1]) < 0.5)
            reach = min(pins.y1, body.y1) - max(pins.y0, body.y0)
            check(reach >= 4.0, f"{p.key}{pos}: {b.label}'s pins reach into the socket",
                  f"{reach:.2f} mm of the {body.y1 - body.y0:.2f} mm body")


def check_fits(p: Plate) -> None:
    x0, y0, x1, y1 = P.ADAPTER_OVER_PI
    for key, pi in RPI.items():
        tall = []
        for f in pi.features:
            z = {"usb_a": 16.0, "ethernet": 13.5}.get(f.kind)
            if z and f.x0 < x1 and f.x1 > x0 and f.y0 < y1 and f.y1 > y0:
                tall.append(f.label)
        if key == "rpi4b":
            tall.append("PoE header")
        title = pi.title.replace(" and B+", "")
        claimed_fit = title in p.fits
        check(claimed_fit == (not tall), f"{p.key}: {title} {'fits' if claimed_fit else 'is excluded'}",
              f"under the adapter: {', '.join(tall) or 'nothing over 6.34'}")


def overlap(a, b) -> float:
    return min(a.x1, b.x1) - max(a.x0, b.x0), min(a.y1, b.y1) - max(a.y0, b.y0)


def check_plan(p: Plate) -> None:
    boards = [b for b in p.boxes if b.label in ("Raspberry Pi", "Digilent Arty A7", "TT-MP-PLATE")]
    for i, a in enumerate(boards):
        for b in boards[i + 1:]:
            if a.label == b.label:
                continue
            ox, oy = overlap(a, b)
            check(ox <= 0 or oy <= 0, f"{p.key}: {a.label}{a.position} clear of {b.label}",
                  f"gap {max(-ox, -oy):.2f}")
    for cup in [b for b in p.boxes if b.label == "Cup"]:
        for other in [b for b in p.boxes if b.kind in ("header", "alt", "adjacent")
                      and b.label not in ("Rubber foot", "Digilent Arty A7")]:
            ox, oy = overlap(cup, other)
            if other.z0 < cup.z1 + 7.2:      # the walls stand this high above the ledge
                check(ox <= 0 or oy <= 0, f"{p.key}: a cup at ({cup.x0:g},{cup.y0:g}) clear of {other.label}{other.position}",
                      f"gap {max(-ox, -oy):.2f}")


def check_holes(p: Plate) -> None:
    o = p.spec.outline
    holes = p.spec.holes
    for h in holes:
        check(EDGE <= h.x <= o.width - EDGE and EDGE <= h.y <= o.height - EDGE,
              f"{p.key}: {h.label} is {EDGE} mm inside the plate", f"({h.x}, {h.y}) on {o.width} x {o.height}")
    for i, a in enumerate(holes):
        for b in holes[i + 1:]:
            d = math.dist((a.x, a.y), (b.x, b.y))
            check(d >= (a.dia + b.dia) / 2 + HOLE_WEB, f"{p.key}: {a.label} and {b.label} drill separately",
                  f"{d:.2f} apart")
    # The Pi's four holes at every position, 58 x 49 apart as the Pi has them.
    for label, x, y in p.pi_positions:
        pos = label.split(":")[0] if ":" in label else ""
        mine = sorted(((h.x, h.y) for h in holes if h.label.startswith("PI" + pos)
                       and (pos or h.label[2].isdigit())))
        want = sorted((x + h.x, y + h.y) for h in RPI["rpi5"].holes if h.kind == "mount")
        # Matched as a pair of spacings, so the check holds whichever way
        # round the Pi lies on a plate.
        spans = lambda pts: (round(max(a for a, _ in pts) - min(a for a, _ in pts), 2),  # noqa: E731
                             round(max(b for _, b in pts) - min(b for _, b in pts), 2))
        check(len(mine) == 4 and spans(mine) == (58.0, 49.0),
              f"{p.key}{pos}: the Pi's four holes are there", f"{spans(mine) if mine else 'none'}")
    if p.key == "tt-pi":
        tt = next(b for b in p.boxes if b.label == "TT-MP-PLATE")
        mine = sorted((h.x, h.y) for h in holes if h.kind == "mp")
        want = sorted((round(tt.x0 + h.x, 2), round(tt.y0 + h.y, 2)) for h in PLATE.holes if h.kind == "plate")
        check(mine == want, "tt-pi: the TT plate's six fixings are its own",
              f"{len(mine)} holes")


def main() -> int:
    for p in P.PLATES.values():
        check_rows(p)
        check_plugs(p)
        check_fits(p)
        check_plan(p)
        check_holes(p)
    bad = [r for r in results if not r[0]]
    for ok, what, detail in results:
        if not ok:
            print(f"FAIL  {what}: {detail}")
    passed = len(results) - len(bad)
    print(f"{passed} of {len(results)} checks passed")
    if bad:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
