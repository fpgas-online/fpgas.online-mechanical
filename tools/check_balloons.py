#!/usr/bin/env python3
"""Report balloon leaders that run across something they should not.

``check_sheets.py`` reads the finished SVG and catches text collisions.  This
looks one level down instead, at what the drafting library was asked to draw,
and holds every leader on every sheet against four things:

* another leader.  Two leaders that cross make a reader trace both to find
  out which balloon points where, which is the one question a balloon exists
  to answer.  Every leader counts: a balloon's, and a callout's such as the
  corner radius.  Tested as an exact segment intersection, because two lines
  meeting at a steep angle share less than a millimetre of paper and a
  sampled test steps straight over them.
* a *hard* obstacle in the balloon placer's model: a phantom Pmod host,
  another balloon, an ordinate witness line.
* the body of a feature it does not point at, which is what makes a leader
  look as though it belongs to the wrong part.  A body that also contains
  the leader's own dot is exempt: where outlines overlap, as the three
  Raspberry Pi models' connectors do on RPI-ALL, the dot has to sit inside
  more than one of them.
* a dimension line or an extension line drawn by ``dims.linear``.

It also reports a balloon that sits on a feature outline, which hides what
its own leader was followed to see.

Every sheet the generator writes is walked, drawn by the generator itself
through ``generate_diagrams.draw_sheets``, so what is judged here is what is
on the page: the same view frames, notes bands and family numbers.  A sheet
with no leaders is listed as such, so a sheet cannot drop out of the check
without it showing.

Anything found fails unless it is listed in ACCEPTED below, per sheet and per
balloon, so a new crossing on a sheet that already has an accepted one is
still caught.

Run with::

    uv run --no-project --with pillow --with pypdf python tools/check_balloons.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.drafting import board_sheet as bs           # noqa: E402
from tools.drafting import dims                        # noqa: E402

#: What the current sheet drew.  ``placed`` is one entry per balloon the
#: placer put down: its label, its leader as drawn, and the index of its own
#: feature's rectangle in the placer's obstacle model.  ``leaders`` is every
#: leader segment on the sheet, balloons' and callouts' alike, and
#: ``dimensions`` every dimension and extension line.
_state: dict = {}
_place, _balloon, _leader, _linear, _ring = (
    bs.place_balloons, dims.balloon, dims.leader, dims.linear,
    dims.balloon_ring)


def _reset() -> None:
    _state.update(obstacles=[], placed=[], leaders=[], dimensions=[],
                  rings=[], pending=None, ids=0, current=None, placing=None)


def _next_id() -> int:
    """A leader's identity: two balloons can carry the same number."""
    _state["ids"] += 1
    return _state["ids"]


def _spy_place(items, obstacles, bounds, c, passes=12, position_only=None):
    _state["pending"] = []
    _state["placing"] = obstacles
    out = _place(items, obstacles, bounds, c, passes, position_only)
    # place_balloons draws its balloons in the order of *items*, so the n-th
    # balloon drawn during this call is items[n].
    for item, (label, tip, end, centre) in zip(items, _state["pending"]):
        _state["placed"].append((obstacles, label, tip, end, centre,
                                 item.own))
    _state["obstacles"].append(obstacles)
    _state["pending"] = None
    return out


def _spy_balloon(c, tip, centre, label, **kw):
    r = kw.get("radius", 3.2)
    ang = math.atan2(centre[1] - tip[1], centre[0] - tip[0])
    end = (centre[0] - r * math.cos(ang), centre[1] - r * math.sin(ang))
    n = _next_id()
    _state["leaders"].append((n, f"balloon {label}", tip, end))
    if _state["pending"] is not None:
        _state["pending"].append((label, tip, end, centre))
    # dims.balloon draws its own ring through dims.balloon_ring, which is
    # watched too; this tells that ring whose leader it is on.
    _state["current"] = n
    try:
        return _balloon(c, tip, centre, label, **kw)
    finally:
        _state["current"] = None


def _spy_ring(c, centre, label, **kw):
    """Every ring a placed balloon is drawn with, the first on its leader
    and the others beside it on a row that shares the leader.  A ring drawn
    outside the placer -- a legend's sample -- is not a balloon."""
    if _state["pending"] is not None:
        n = _state["current"] or _next_id()
        _state["rings"].append((n, f"balloon {label}", centre,
                                kw.get("radius", 3.2), _state["placing"]))
    return _ring(c, centre, label, **kw)


def _spy_leader(c, tip, elbow, text, **kw):
    end = _leader(c, tip, elbow, text, **kw)
    what, n = f'callout "{text}"', _next_id()
    _state["leaders"].append((n, what, tip, elbow))
    _state["leaders"].append((n, what, elbow, end))
    return end


def _spy_linear(c, p1, p2, offset, **kw):
    g = _linear(c, p1, p2, offset, **kw)
    what = f"dimension {g.label}"
    if g.horizontal:
        _state["dimensions"].append((what, (g.lo, g.line), (g.hi, g.line)))
        if kw.get("extension", True):
            for x, y in (p1, p2):
                start = y if kw.get("ext_start") is None else kw["ext_start"]
                _state["dimensions"].append((f"{what} extension", (x, start),
                                             (x, g.line)))
    else:
        _state["dimensions"].append((what, (g.line, g.lo), (g.line, g.hi)))
        if kw.get("extension", True):
            for x, y in (p1, p2):
                start = x if kw.get("ext_start") is None else kw["ext_start"]
                _state["dimensions"].append((f"{what} extension", (start, y),
                                             (g.line, y)))
    return g


bs.place_balloons = _spy_place
dims.balloon = _spy_balloon
dims.leader = _spy_leader
dims.linear = _spy_linear
dims.balloon_ring = _spy_ring

from tools.generate_diagrams import draw_sheets      # noqa: E402


#: A leader that only grazes an obstacle's clearance band is not worth
#: reporting.  Every obstacle rectangle is padded by a millimetre or two so
#: that balloons keep clear of it, so a crossing shorter than this is a clip
#: of the padding rather than of anything drawn.
MIN_RUN_MM = 2.0


def _run_lengths(tip, end, rects, samples: int = 200) -> dict[tuple, float]:
    """How far the segment tip->end runs inside each of *rects*."""
    length = math.hypot(end[0] - tip[0], end[1] - tip[1])
    step = length / samples
    runs: dict[tuple, float] = {}
    for i in range(1, samples):
        t = i / samples
        px = tip[0] + (end[0] - tip[0]) * t
        py = tip[1] + (end[1] - tip[1]) * t
        for r in rects:
            if r[0] < px < r[2] and r[1] < py < r[3]:
                runs[r] = runs.get(r, 0.0) + step
    return runs


def _crossed(tip, centre, obstacles, samples: int = 200) -> list[str]:
    """Hard obstacles the segment tip->centre runs through, and by how much.

    Sampled finely and reported as a length: the length is what separates a
    leader ruled along a pin field from one that clips the corner of its
    clearance band.
    """
    hard_rects = [r for r in obstacles.rects if r[4] > bs.SOFT]
    hard_circles = [o for o in obstacles.circles if o[3] > bs.SOFT]
    hard_segs = [s for s in obstacles.segments if s[4] > bs.SOFT]
    length = math.hypot(centre[0] - tip[0], centre[1] - tip[1])
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


def _cross(a0, a1, b0, b1) -> bool:
    """Whether two segments cross at a point inside both.

    Proper crossings only.  Segments that merely meet end to end -- the two
    legs of one callout at its elbow, a witness line stopping on a leader's
    dot -- are not a crossing a reader has to untangle.
    """
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    d1, d2 = side(a0, a1, b0), side(a0, a1, b1)
    d3, d4 = side(b0, b1, a0), side(b0, b1, a1)
    eps = 1e-9
    return (((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps))
            and ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)))


def _at(a0, a1, b0, b1) -> tuple[float, float]:
    """Where two crossing segments meet."""
    dx1, dy1 = a1[0] - a0[0], a1[1] - a0[1]
    dx2, dy2 = b1[0] - b0[0], b1[1] - b0[1]
    t = ((b0[0] - a0[0]) * dy2 - (b0[1] - a0[1]) * dx2) / (dx1 * dy2
                                                             - dy1 * dx2)
    return a0[0] + t * dx1, a0[1] + t * dy1


def _leader_crossings() -> list[tuple[str, str]]:
    """Every pair of leaders that cross, and every leader through a balloon.

    A leader ruled across another balloon's ring reads as ending there, which
    is as bad as crossing that balloon's leader, and the placer's own model
    cannot report it: the placed balloons are added to a scene built per
    balloon and thrown away, so the obstacles it is handed never hold them.
    """
    out = []
    leaders = _state["leaders"]
    for na, wa, a0, a1 in leaders:
        for nb, wb, (cx, cy), r, _ in _state["rings"]:
            if na != nb and bs._point_segment_distance(
                    cx, cy, a0[0], a0[1], a1[0], a1[1]) < r:
                out.append((wa, f"runs through the ring of {wb} at "
                                f"({cx:.1f},{cy:.1f})"))
    for i, (na, wa, a0, a1) in enumerate(leaders):
        for nb, wb, b0, b1 in leaders[i + 1:]:
            if na == nb:
                continue
            if _cross(a0, a1, b0, b1):
                x, y = _at(a0, a1, b0, b1)
                out.append((wa, f"crosses the leader of {wb} at "
                                f"({x:.1f},{y:.1f})"))
                out.append((wb, f"crosses the leader of {wa} at "
                                f"({x:.1f},{y:.1f})"))
    return out


def _dimension_crossings() -> list[tuple[str, str]]:
    out = []
    for _, wa, a0, a1 in _state["leaders"]:
        for wb, b0, b1 in _state["dimensions"]:
            if _cross(a0, a1, b0, b1):
                x, y = _at(a0, a1, b0, b1)
                out.append((wa, f"crosses {wb} line at ({x:.1f},{y:.1f})"))
    return out


def _body_crossings() -> list[tuple[str, str]]:
    """Balloon leaders run through a feature body they do not point at.

    A feature body is a *soft* rectangle in the placer's model: that is how
    ``render_board`` and the comparison sheet enter a connector or a Pmod
    body, and the only thing either enters soft.  The leader's own feature
    is exempt, and so is any body its dot sits in.
    """
    out = []
    for obstacles, label, tip, end, _centre, own in _state["placed"]:
        bodies = [r for i, r in enumerate(obstacles.rects)
                  if r[4] <= bs.SOFT and i != own
                  and not (r[0] <= tip[0] <= r[2] and r[1] <= tip[1] <= r[3])]
        for r, run in sorted(_run_lengths(tip, end, bodies).items()):
            if run >= MIN_RUN_MM:
                out.append((f"balloon {label}",
                            f"runs {run:.1f} mm through the feature at "
                            f"({r[0]:.1f},{r[1]:.1f})-({r[2]:.1f},{r[3]:.1f})"))
    return out


def _hard_crossings() -> list[tuple[str, str]]:
    out = []
    for obstacles, label, tip, _end, centre, _own in _state["placed"]:
        hit = _crossed(tip, centre, obstacles)
        if hit:
            out.append((f"balloon {label}", "leader crosses a hard obstacle: "
                        + "; ".join(hit)))
    return out


def _on_a_feature() -> list[tuple[str, str]]:
    """Balloons whose circle overlaps a drawn feature outline.

    A balloon covers whatever it sits on, so one sitting on a feature hides
    the geometry the reader followed its leader to see.  The placer prices
    that, but pricing is not proof: on the Raspberry Pi 3A+ a balloon covered
    a neighbouring connector because every other position cost more still.
    """
    out = []
    for _, what, centre, r, obstacles in _state["rings"]:
        for x0, y0, x1, y1, _ in obstacles.rects:
            nx = max(x0, min(centre[0], x1))
            ny = max(y0, min(centre[1], y1))
            if math.hypot(centre[0] - nx, centre[1] - ny) < r:
                out.append((what, "sits on a feature outline"))
                break
    return out


#: Findings that are known and deliberately left, as {drawing name: {(what,
#: kind)}}, where *what* is the leader as the report names it and *kind* is
#: the name its test has in KINDS.  Listed per leader rather than as a
#: count, so a new finding somewhere else on the same sheet is still caught,
#: and an entry that stops happening is reported so it can be trimmed.
#:
#: All of them are a leader across an overall dimension, and none is the
#: placer's to fix.  The corner radius callout leaves its corner up and to
#: the right, across the extension line that the overall dimension on that
#: corner runs out from; ``_radius_callout`` draws it there on every board
#: sheet, and where the extension line and the callout miss each other it
#: is because the width dimension is on the other edge.  The three balloons
#: are ruled across an overall dimension or its extension line because
#: ``reserve_overall_dimensions`` holds those lines against where a balloon
#: sits and not against where a leader runs: reserving them against leaders
#: as well boxed the balloons into the board's interior.
#:
#: The micro-HDMI connectors on the Pi 4B and Pi 5, which sat underneath the
#: Pmod HAT Adapter's host JC, used to be here too; they are no longer drawn.
ACCEPTED: dict[str, set[tuple[str, str]]] = {
    name: {(f'callout "R{r} (4 places), board outline"', "dimension")}
    for name, r in (("TT-DB-V121", "3.00"), ("TT-DB-V201", "3.00"),
                    ("TT-DB-V212", "3.00"), ("TT-DB-V32", "3.20"),
                    ("TT-DB-V33", "3.20"), ("RPI-3B", "3.00"),
                    ("RPI-4B", "3.00"), ("RPI-5", "3.00"),
                    ("FPGA-BUTTERSTICK", "3.00"), ("FPGA-CYNTHION", "3.00"))
}
ACCEPTED["RPI-4B"].add(("balloon 5", "dimension"))
ACCEPTED["FPGA-BUTTERSTICK"].add(("balloon 1", "dimension"))
ACCEPTED["FPGA-CYNTHION"].add(("balloon 9", "dimension"))

KINDS = (("leader", _leader_crossings),
         ("hard", _hard_crossings),
         ("body", _body_crossings),
         ("dimension", _dimension_crossings),
         ("sits", _on_a_feature))


def check(name: str) -> tuple[set, set]:
    """Report one sheet's findings; return the unexpected and the stale."""
    accepted = ACCEPTED.get(name, set())
    found, lines = set(), []
    for kind, test in KINDS:
        for what, why in test():
            found.add((what, kind))
            mark = "accepted" if (what, kind) in accepted else "UNEXPECTED"
            lines.append(f"  {what} ({mark}, {kind}): {why}")
    leaders = len({n for n, *_ in _state['leaders']})
    print(f"{name}: {leaders} leader(s), "
          f"{len({w for w, _ in found})} with a finding")
    for line in lines:
        print(line)
    return found - accepted, accepted - found


def main() -> int:
    unexpected: dict[str, set] = {}
    stale: dict[str, set] = {}
    names = []
    _reset()
    for _sheet, _path, what in draw_sheets():
        name = what.split()[0]
        names.append(name)
        new, gone = check(name)
        if new:
            unexpected[name] = new
        if gone:
            stale[name] = gone
        _reset()

    print()
    for name, entries in stale.items():
        for what, kind in sorted(entries):
            print(f"{name}: {what} no longer has a '{kind}' finding; trim it "
                  "from ACCEPTED")
    if not unexpected and not stale:
        print(f"pass: {sum(len(v) for v in ACCEPTED.values())} accepted "
              f"finding(s), none unexpected, on every sheet the generator "
              f"writes ({', '.join(names)})")
        return 0
    for name, entries in unexpected.items():
        print(f"FAIL {name}: "
              + "; ".join(f"{what} ({kind})" for what, kind in sorted(entries))
              + " not in ACCEPTED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
