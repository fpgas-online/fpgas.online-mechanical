#!/usr/bin/env python3
"""Report every balloon leader ruled through a dimension arrowhead.

A leader crossing a dimension LINE is ordinary and the balloon placer allows
it: the line is thin, the two are different colours, and pricing the whole
dimension band against leaders boxes the balloons into the board's interior.
An arrowhead is not ordinary.  It is a solid filled triangle, and a leader
through one stops it reading as an arrowhead at all.

Reads the finished SVGs back rather than the model that drew them, so it
measures what a reader will see, and tests segment against triangle properly
instead of sampling: a leader can pass through a three millimetre arrowhead
between any two samples you care to take.

What counts as a leader is read off the sheet: a balloon is a ring of the
balloon radius, and its leader is a line in that ring's colour with an end on
that ring.  Both halves of that matter.  One fixed colour --
``style.C_HIGHLIGHT``, which is what every single-board sheet uses -- finds no
leaders at all on RPI-ALL, whose balloons take the colour of the
model they point at, so its eight leaders go unexamined and the sheet passes
for having nothing on it to check.  Colour alone finds too much as well: the
Pmod pin-row centre line is drawn in the balloon colour, and it runs along the
lane the pin-field depth dimension is drawn in, so on four sheets it reads as
a leader through the arrowhead of the very dimension that measures to it.

It passes on every sheet in the set, and runs in ``make check`` with the
others.

Run: uv run --no-project --with pillow python tools/check_leader_arrows.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.drafting.board_sheet import BALLOON_R  # noqa: E402
from tools.layout import rel, sheets  # noqa: E402

LINE = re.compile(r'<line x1="([-\d.]+)" y1="([-\d.]+)" '
                  r'x2="([-\d.]+)" y2="([-\d.]+)"[^/]*?stroke="([^"]+)"')
POLYGON = re.compile(r'<polygon points="([^"]+)"[^/]*?fill="([^"]+)"')
CIRCLE = re.compile(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)" '
                    r'fill="[^"]*" stroke="([^"]+)"')


def balloons(text: str) -> list:
    """Every balloon on this sheet: its centre and the colour it is drawn in.

    A balloon is a ring of the balloon radius, so the rings say what a
    balloon looks like on this sheet without anything having to be told.

    Asked instead for one fixed colour -- ``style.C_HIGHLIGHT``, which is
    what every single-board sheet uses -- this found no leaders at all on
    RPI-ALL, whose balloons take the colour of the model they
    point at so that a monochrome print can still tell them apart.  Eight
    leaders went unexamined and the sheet passed for having nothing to
    check, which is the failure mode a checker must not have.
    """
    return [(float(cx), float(cy), stroke)
            for cx, cy, radius, stroke in CIRCLE.findall(text)
            if abs(float(radius) - BALLOON_R) < 1e-9]


def leaders_of(text: str, rings: list) -> list:
    """The balloon leaders on this sheet, as segments.

    A leader is drawn in its balloon's colour and stops on the ring, so it
    is a line of that colour with an end the balloon radius from that
    balloon's centre.  Colour alone is not enough: the comparison sheet
    draws each model's outline in the same colour as that model's balloons,
    and six-and-forty of its lines are outline rather than leader.
    """
    out = []
    for a, b, c, d, colour in LINE.findall(text):
        p, q = (float(a), float(b)), (float(c), float(d))
        for cx, cy, stroke in rings:
            if stroke != colour:
                continue
            if any(abs(math.hypot(x - cx, y - cy) - BALLOON_R) < 0.01
                   for x, y in (p, q)):
                out.append((p, q))
                break
    return out


def _cross(o, a, b) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _straddles(p, q, a, b) -> bool:
    """True when segment pq and segment ab cross each other properly."""
    return ((_cross(p, q, a) > 0) != (_cross(p, q, b) > 0)
            and (_cross(a, b, p) > 0) != (_cross(a, b, q) > 0))


def _inside(point, tri) -> bool:
    turns = [_cross(tri[i], tri[(i + 1) % 3], point) for i in range(3)]
    return all(t >= 0 for t in turns) or all(t <= 0 for t in turns)


def through(segment, tri) -> bool:
    p, q = segment
    if _inside(p, tri) or _inside(q, tri):
        return True
    return any(_straddles(p, q, tri[i], tri[(i + 1) % 3]) for i in range(3))


def main() -> None:
    problems = 0
    examined = 0
    for svg in sheets():
        text = svg.read_text()
        rings = balloons(text)
        colours = {stroke for _, _, stroke in rings}
        leaders = leaders_of(text, rings)
        arrows = []
        for points, fill in POLYGON.findall(text):
            corners = [tuple(float(v) for v in pt.split(","))
                       for pt in points.split()]
            # Three points and not a balloon colour: a dimension arrowhead.
            # The datum marker's quadrants are paths, not polygons.
            if len(corners) == 3 and fill not in colours:
                arrows.append(corners)
        hits = [(s, t) for s in leaders for t in arrows if through(s, t)]
        problems += len(hits)
        examined += len(leaders)
        print(f"{rel(svg)}: {len(leaders)} leader(s), {len(arrows)} "
              f"arrowhead(s), {len(hits)} through one")
        for (p, q), tri in hits:
            print(f"    leader {p} to {q} through arrowhead {tri}")
    # Shaped like the other checks' last line, so one glance down a build log
    # reads the same for all of them.  It counts the leaders it examined as
    # well as the problems it found, because that is the number that went
    # wrong here once: a rule that matched none of a sheet's leaders reported
    # that sheet clean, and nothing printed said it had looked at nothing.
    print(f"\n{problems} problem(s) across {examined} leader(s) on "
          f"{len(sheets())} sheets")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
