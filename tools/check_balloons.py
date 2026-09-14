#!/usr/bin/env python3
"""Report balloon leaders that run across something they should not.

``check_sheets.py`` reads the finished SVG and catches text collisions.  This
looks one level down instead, at the obstacle model the balloon placer works
from, and reports every leader whose final route crosses a *hard* obstacle: a
phantom Pmod host, another balloon, another leader, or an ordinate witness
line.  Those are the things a reader cannot afford to have a line ruled over.

Two crossings are unavoidable and are listed in ACCEPTED below: on the
Raspberry Pi 4B and Pi 5 the micro-HDMI connectors sit directly beneath the
Pmod HAT Adapter's host JC, so a leader from those connectors has to cross the
host whichever way it leaves.  That physical overlap is the subject of a note
on both sheets.  Anything else fails, so a regression cannot pass unremarked
just because the total happens to look familiar.

Run with::

    uv run --no-project --with pillow python tools/check_balloons.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.drafting import board_sheet as bs           # noqa: E402
from tools.drafting import dims                        # noqa: E402

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

from accessories.parts import ACCESSORIES, PMOD_HAT        # noqa: E402
from fpga.boards import BOARDS as FPGA               # noqa: E402
from raspberry_pi.boards import BOARDS as RPI        # noqa: E402
from tinytapeout.boards import BOARDS as TT          # noqa: E402


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


#: Crossings that no placement can avoid, as {sheet: {balloon labels}}.
#: Listed per balloon rather than as a count, so a new crossing somewhere else
#: on the same sheet is still caught.
#:
#: Empty at present.  The two entries that used to be here were the micro-HDMI
#: connectors on the Pi 4B and Pi 5, which sit underneath the Pmod HAT
#: Adapter's host JC; those connectors are no longer drawn, so the crossing
#: they forced is gone with them.
ACCEPTED: dict[str, set[str]] = {}


def _on_a_feature(items, placed, obstacles) -> set[str]:
    """Balloons whose circle overlaps a drawn feature outline.

    A balloon covers whatever it sits on, so one sitting on a feature hides
    the geometry the reader followed its leader to see.  The placer prices
    that, but pricing is not proof: on the Raspberry Pi 3A+ a balloon covered
    a neighbouring connector because every other position cost more still.
    """
    out = set()
    for label, tip, centre in placed:
        for x0, y0, x1, y1, _ in obstacles.rects:
            nx = max(x0, min(centre[0], x1))
            ny = max(y0, min(centre[1], y1))
            if math.hypot(centre[0] - nx, centre[1] - ny) < bs.BALLOON_R:
                out.add(label)
                break
    del items
    return out


def check(name: str, spec, overlay=None) -> tuple[set[str], set[str]]:
    """Draw one sheet and report which balloons cross a hard obstacle.

    Returns the crossings that were not expected and the expected ones that no
    longer happen; both mean the sheet and ACCEPTED have drifted apart.
    """
    bs.render_board(spec, drawing_no="-", version="-", overlay=overlay)
    obstacles = _state["obstacles"]
    accepted = ACCEPTED.get(name, set())
    crossing = set()
    for label, tip, centre in _state["leaders"]:
        hit = _crossed(tip, centre, obstacles)
        if hit:
            crossing.add(label)
            mark = "accepted" if label in accepted else "UNEXPECTED"
            print(f"  balloon {label} ({mark}): leader crosses "
                  + "; ".join(hit))
    on_feature = _on_a_feature(None, _state["leaders"], obstacles)
    for label in sorted(on_feature):
        print(f"  balloon {label} (UNEXPECTED): sits on a feature outline")
    print(f"{name}: {len(crossing)} leader(s) crossing a hard obstacle "
          f"of {len(_state['leaders'])}")
    return (crossing - accepted) | on_feature, accepted - crossing


def main() -> int:
    sheets = [(f"tinytapeout/{k}", v, None) for k, v in TT.items()]
    sheets += [(f"raspberry-pi/{k}", v, PMOD_HAT) for k, v in RPI.items()]
    sheets += [(f"fpga/{k}", v, None) for k, v in FPGA.items()]
    sheets.append(("accessories/pmod-hat", PMOD_HAT, None))
    sheets += [(f"accessories/{k}", v, None) for k, v in ACCESSORIES.items()
               if v is not PMOD_HAT]

    unexpected: dict[str, set[str]] = {}
    stale: dict[str, set[str]] = {}
    for name, spec, overlay in sheets:
        new, gone = check(name, spec, overlay)
        if new:
            unexpected[name] = new
        if gone:
            stale[name] = gone

    print()
    for name, labels in stale.items():
        print(f"{name}: balloon(s) {', '.join(sorted(labels))} no longer "
              "cross anything; trim them from ACCEPTED")
    if not unexpected:
        print(f"pass: {sum(len(v) for v in ACCEPTED.values())} accepted "
              f"crossing(s), none unexpected, across {len(sheets)} sheets")
        return 0
    for name, labels in unexpected.items():
        print(f"FAIL {name}: balloon(s) {', '.join(sorted(labels))} cross a "
              "hard obstacle, or sit on a feature, and are not in ACCEPTED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
