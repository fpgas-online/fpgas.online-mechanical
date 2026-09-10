#!/usr/bin/env python3
"""Report balloon leaders that run across something they should not.

``check_sheets.py`` reads the finished SVG and catches text collisions.  This
looks one level down instead, at the obstacle model the balloon placer works
from, and reports every leader whose final route crosses a *hard* obstacle: a
phantom Pmod host, another balloon, another leader, or an ordinate witness
line.  Those are the things a reader cannot afford to have a line ruled over.

It is a report, not a gate.  One case is unavoidable and is expected in the
output: on the Raspberry Pi 5 the micro-HDMI connectors sit directly beneath
the Pmod HAT Adapter's host JC, so a leader from those connectors has to cross
the host whichever way it leaves.  That physical overlap is the subject of a
note on the sheet.

Run with::

    uv run --no-project --with pillow --with pyyaml python scripts/check_balloons.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drafting import board_sheet as bs           # noqa: E402
from drafting import dims                        # noqa: E402

# What the placer was given, and where every leader ended up.
_state: dict = {"obstacles": None, "leaders": []}
_place, _balloon = bs.place_balloons, dims.balloon


def _spy_place(items, obstacles, bounds, c, passes=12, position_only=None):
    _state["obstacles"] = obstacles
    _state["leaders"] = []
    return _place(items, obstacles, bounds, c, passes, position_only)


def _spy_balloon(c, tip, centre, label, **kw):
    _state["leaders"].append((label, tip, centre))
    return _balloon(c, tip, centre, label, **kw)


bs.place_balloons = _spy_place
dims.balloon = _spy_balloon

from data.accessories import ACCESSORIES, PMOD_HAT        # noqa: E402
from data.raspberry_pi_boards import BOARDS as RPI        # noqa: E402
from data.tinytapeout_boards import BOARDS as TT          # noqa: E402


#: A leader that only grazes an obstacle's clearance band is not worth
#: reporting.  Every obstacle rectangle is padded by a millimetre or two so
#: that balloons keep clear of it, so a crossing shorter than this is a clip
#: of the padding rather than of anything drawn.
MIN_RUN_MM = 2.0


def _crossed(tip, centre, obstacles, samples: int = 200) -> list[str]:
    """Hard obstacles the segment tip->centre runs through, and by how much.

    Sampled finely and reported as a length: this is a report on a handful of
    sheets, so there is no reason to be as coarse as the placer's own scoring
    loop, and the length is what separates a leader ruled along a pin field
    from one that clips the corner of its clearance band.
    """
    hard_rects = [r for r in obstacles.rects if r[4] > bs.SOFT]
    hard_circles = [o for o in obstacles.circles if o[3] > bs.SOFT]
    hard_segs = [s for s in obstacles.segments if s[4] > bs.SOFT]
    length = ((centre[0] - tip[0]) ** 2 + (centre[1] - tip[1]) ** 2) ** 0.5
    step = length / samples
    runs: dict[str, float] = {}

    def note(key):
        runs[key] = runs.get(key, 0.0) + step

    for i in range(1, samples):
        t = i / samples
        px = tip[0] + (centre[0] - tip[0]) * t
        py = tip[1] + (centre[1] - tip[1]) * t
        for x0, y0, x1, y1, _ in hard_rects:
            if x0 < px < x1 and y0 < py < y1:
                note(f"rect ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f})")
        for cx, cy, r, _ in hard_circles:
            if (px - cx) ** 2 + (py - cy) ** 2 < r * r:
                note(f"circle ({cx:.1f},{cy:.1f}) r{r:.1f}")
        for x1_, y1_, x2_, y2_, _ in hard_segs:
            if bs._point_segment_distance(px, py, x1_, y1_, x2_, y2_) < 0.6:
                note(f"line ({x1_:.1f},{y1_:.1f})-({x2_:.1f},{y2_:.1f})")
    return [f"{k} for {v:.1f} mm" for k, v in sorted(runs.items())
            if v >= MIN_RUN_MM]


def check(name: str, spec, overlay=None) -> int:
    bs.render_board(spec, drawing_no="-", date="0000-00-00", overlay=overlay)
    obstacles = _state["obstacles"]
    bad = 0
    for label, tip, centre in _state["leaders"]:
        hit = _crossed(tip, centre, obstacles)
        if hit:
            bad += 1
            print(f"  balloon {label}: leader crosses " + "; ".join(hit))
    print(f"{name}: {bad} leader(s) crossing a hard obstacle "
          f"of {len(_state['leaders'])}")
    return bad


def main() -> int:
    total = 0
    for key, spec in TT.items():
        total += check(f"tinytapeout/{key}", spec)
    for key, spec in RPI.items():
        total += check(f"raspberry-pi/{key}", spec, overlay=PMOD_HAT)
    total += check("accessories/pmod-hat", PMOD_HAT)
    for key, spec in ACCESSORIES.items():
        if spec is PMOD_HAT:
            continue
        total += check(f"accessories/{key}", spec)
    print(f"\n{total} leader(s) crossing a hard obstacle in total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
