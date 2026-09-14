"""What every KiCad-sourced extractor does the same way.

An extractor's job is to turn one ``.kicad_pcb`` into the numbers a
:class:`tools.schema.BoardSpec` carries: the outline in a Y-up frame with its
arcs resolved and checked, the mounting holes with their drill sizes, the Pmod
hosts as pin fields, and every other part as a bounding box.  The judgement --
which designator plays which role -- stays in each family's own script.  The
arithmetic, and the checks that catch an arc resolved the wrong way round, live
here so a second family cannot get a different answer from the same file.

Everything returned is in the drawing frame of :mod:`tools.schema`: origin at
the lower-left corner of the board's bounding box, X right, Y up, millimetres,
rounded to three decimals.
"""

from __future__ import annotations

import math


def frame(board):
    """Return mappers from KiCad coordinates to the drawing frame.

    ``to_xy`` maps a point; ``to_box`` maps a ``(x0, y0, x1, y1)`` box, which
    needs its own function because flipping Y swaps which edge is the top.
    """
    x0, y0, x1, y1 = board.outline_bbox()

    def to_xy(x, y):
        return x - x0, y1 - y

    def to_box(bb):
        return (bb[0] - x0, y1 - bb[3], bb[2] - x0, y1 - bb[1])

    return to_xy, to_box, (x1 - x0, y1 - y0)


def one(fps, ref):
    """The single footprint with reference *ref*, or stop."""
    hits = [f for f in fps if f.reference == ref]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one {ref}, found {len(hits)}")
    return hits[0]


def _check_arc_passes_through(key: str, edge, point, tol: float = 0.02) -> None:
    best = min(math.dist(point, p) for p in sample_arc(*edge[1:], steps=180))
    if best > tol:
        raise SystemExit(
            f"{key}: a resolved outline arc misses the point KiCad puts on it "
            f"by {best:.3f} mm. It is curving the wrong way.")


def _check_outline_extent(key: str, edges, width: float, height: float) -> None:
    """The resolved outline must fill its own bounding box, and no more.

    An arc resolved with the wrong direction or the wrong large-arc flag bulges
    the opposite way, which shows up here immediately.  It is exactly the
    mistake that turns rounded corners into scallops bitten out of the board,
    and it looks plausible enough at screen size to survive a visual check.

    Each arc is sampled rather than reasoned about: recovering a circle centre
    from SVG-style parameters has its own sign trap, and sampling has none.
    """
    xs: list[float] = []
    ys: list[float] = []
    for e in edges:
        if e[0] == "line":
            xs += [e[1], e[3]]
            ys += [e[2], e[4]]
        else:
            for px, py in sample_arc(*e[1:]):
                xs.append(px)
                ys.append(py)
    got_w, got_h = max(xs) - min(xs), max(ys) - min(ys)
    if abs(got_w - width) > 0.02 or abs(got_h - height) > 0.02:
        raise SystemExit(
            f"{key}: the resolved outline spans {got_w:.3f} x {got_h:.3f} mm "
            f"but the board is {width:.3f} x {height:.3f}. An arc is bulging "
            f"the wrong way.")


def sample_arc(x1, y1, x2, y2, r, large, ccw, steps: int = 33):
    """Points along an SVG-style arc, including both ends."""
    dx, dy = x2 - x1, y2 - y1
    half = math.hypot(dx, dy) / 2
    off = math.sqrt(max(r * r - half * half, 0.0))
    # Of the two candidate centres, the one that gives the requested sweep.
    nx, ny = -dy / (2 * half), dx / (2 * half)
    for sign in (1, -1):
        cx = (x1 + x2) / 2 + sign * off * nx
        cy = (y1 + y2) / 2 + sign * off * ny
        a0 = math.atan2(y1 - cy, x1 - cx)
        a2 = math.atan2(y2 - cy, x2 - cx)
        span = (a2 - a0) % (2 * math.pi) if ccw else (a0 - a2) % (2 * math.pi)
        if (span > math.pi) == bool(large):
            break
    out = []
    for i in range(steps + 1):
        a = a0 + (span if ccw else -span) * i / steps
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def outline(key: str, board, to_xy, w: float, h: float
            ) -> tuple[list[tuple], list[float]]:
    """The Edge.Cuts geometry as drawing-frame edges, plus its arc radii.

    Arcs are resolved here, where the source geometry is, rather than in the
    renderer.  Storing the end points, radius, whether the arc is the major one
    and which way it turns means the drawing side never has to re-derive a
    circle from three points, and cannot get the large-arc flag wrong.  Every
    arc is checked to pass through the point KiCad puts on it, and the whole
    outline to fill its bounding box exactly.

    The radii come back sorted and deduplicated, so a caller can tell a plain
    rounded rectangle (one radius) from a profile with a recess (several), and
    a board with square corners (none).
    """
    segs, arcs, circles = board.edge_cuts()
    edges: list[tuple] = []
    for g in segs:
        a, b = to_xy(g.x1, g.y1), to_xy(g.x2, g.y2)
        edges.append(("line", round(a[0], 3), round(a[1], 3),
                      round(b[0], 3), round(b[1], 3)))
    for g in arcs:
        cx, cy, r = g.centre_radius()
        a, m, b = to_xy(g.x1, g.y1), to_xy(g.xm, g.ym), to_xy(g.x2, g.y2)
        centre = to_xy(cx, cy)
        a0 = math.atan2(a[1] - centre[1], a[0] - centre[0])
        a1 = math.atan2(m[1] - centre[1], m[0] - centre[0])
        a2 = math.atan2(b[1] - centre[1], b[0] - centre[0])
        ccw = ((a1 - a0) % (2 * math.pi)) < ((a2 - a0) % (2 * math.pi))
        swept = ((a2 - a0) % (2 * math.pi)) if ccw \
            else ((a0 - a2) % (2 * math.pi))
        edge = ("arc", round(a[0], 3), round(a[1], 3),
                round(b[0], 3), round(b[1], 3), round(r, 4),
                1 if swept > math.pi else 0, 1 if ccw else 0)
        # KiCad gives an explicit point on the arc.  Requiring the resolved arc
        # to pass through it is the only check that catches a corner fillet
        # resolved the wrong way round: such an arc curves into the corner
        # rather than out of it, so it stays inside the board's bounding box
        # and a bounding box check sees nothing wrong.
        _check_arc_passes_through(key, edge, m)
        edges.append(edge)
    _check_outline_extent(key, edges, w, h)
    radii = sorted({round(g.centre_radius()[2], 3) for g in arcs})
    return edges, radii


def hole(key: str, fp, to_xy) -> dict:
    """A mounting hole from its footprint: position, drill, and pad size."""
    x, y = to_xy(fp.x, fp.y)
    pads = fp.pads
    drills = [p.drill for p in pads if p.drill]
    if not drills:
        raise SystemExit(
            f"{key}: mounting hole {fp.reference} has no drill size. Do not "
            f"guess one; fix the role table or the source.")
    # The largest drill, not the only one: ButterStick's M3 footprint rings
    # its 3.2 mm hole with four 0.5 mm vias, and those are pads too.
    dia = max(drills)
    pad_dia = max(max(p.size) for p in pads)
    return dict(x=round(x, 3), y=round(y, 3), dia=round(dia, 3),
                label=fp.reference, kind="mount", keepout_dia=round(pad_dia, 3))


def pmod(fp, to_xy, to_box, *, key: str, label: str, edge: str = "bottom"
         ) -> dict:
    """A 2x6 Pmod host from its footprint: pin-field centre, pin 1, body."""
    pads = {p.number: p for p in fp.pads}
    xs = [to_xy(p.x, p.y)[0] for p in fp.pads]
    ys = [to_xy(p.x, p.y)[1] for p in fp.pads]
    p1x, p1y = to_xy(pads["1"].x, pads["1"].y)
    body = to_box(fp.bbox("courtyard"))
    return dict(
        key=key, label=label, designator=fp.reference, edge=edge,
        cx=round((min(xs) + max(xs)) / 2, 3), cy=round((min(ys) + max(ys)) / 2, 3),
        pin1_x=round(p1x, 3), pin1_y=round(p1y, 3),
        body_x0=round(body[0], 3), body_y0=round(body[1], 3),
        body_x1=round(body[2], 3), body_y1=round(body[3], 3))


def box(fp, to_box, source: str = "courtyard") -> tuple[float, float, float, float]:
    """A footprint's bounding box in the drawing frame, rounded.

    The courtyard by default, which is what a neighbouring part has to clear;
    the pads when a footprint has no courtyard, which is the least a part can
    be said to occupy.
    """
    bb = fp.bbox(source) or fp.pad_bbox()
    b = to_box(bb)
    return (round(b[0], 3), round(b[1], 3), round(b[2], 3), round(b[3], 3))
