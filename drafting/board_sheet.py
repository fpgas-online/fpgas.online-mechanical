"""Render a :class:`data.schema.BoardSpec` as a 2D orthographic drawing sheet.

Layout rules that keep these sheets readable:

* Dimensions live below and to the left of the view; balloons live above and to
  the right.  Keeping the two annotation families on opposite sides is the
  single biggest thing that stops them colliding.
* Hole and feature positions are dimensioned by ordinate chains from one datum
  at the board's lower-left corner, rather than by chained linear dimensions.
  Ordinates never overlap each other and never accumulate tolerance.
* Anything that would clutter the view goes in a table in the right-hand
  column: the full hole schedule, and every feature's bounding box.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from data.schema import BoardSpec, Feature, Hole

from . import dims, style
from .canvas import Canvas
from .sheet import Rect, Sheet, TitleBlock
from .view import View

# Which feature kinds this drawing is *about*, and so draws emphasised.
HIGHLIGHT_KINDS = {"pmod", "usb_power", "usb_a", "ethernet", "display7", "led"}

KIND_LABEL = {
    "pmod": "Pmod host header, 2x6, 2.54 mm pitch",
    "usb_power": "USB power / control connector",
    "usb_a": "USB type A port",
    "ethernet": "Ethernet RJ45 jack",
    "display7": "Seven-segment display",
    "led": "Indicator LED",
    "switch": "Switch",
    "header": "Pin header",
    "connector": "Connector",
}

BALLOON_R = 3.2
BALLOON_STEP = 8.4
BALLOON_OFFSET = 13.0


@dataclass
class _Ballooned:
    label: str
    tip: tuple[float, float]


def outline_path(c: Canvas, view: View, spec: BoardSpec, *,
                 colour: str = style.C_LINE, w: float = style.W_OUTLINE,
                 dash: str | None = None) -> None:
    """Draw the board profile, using the exact edge list when there is one."""
    o = spec.outline
    if o.edges:
        for edge in o.edges:
            if edge[0] == "line":
                _, x1, y1, x2, y2 = edge
                c.line(*view.pt(x1, y1), *view.pt(x2, y2), w=w, colour=colour,
                       dash=dash)
            else:
                _, x1, y1, xm, ym, x2, y2 = edge
                r = _arc_radius(x1, y1, xm, ym, x2, y2)
                p1, p2 = view.pt(x1, y1), view.pt(x2, y2)
                large = 0
                sweep = 1 if _cross(x1, y1, xm, ym, x2, y2) < 0 else 0
                c.arc(p1[0], p1[1], p2[0], p2[1], view.d(r), large=large,
                      sweep=sweep, w=w, colour=colour)
        return
    r = o.corner_radius
    x0, y0 = 0.0, 0.0
    x1, y1 = o.width, o.height
    pts = [(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r),
           (x1 - r, y1), (x0 + r, y1), (x0, y1 - r), (x0, y0 + r)]
    sp = [view.pt(*p) for p in pts]
    rr = view.d(r)
    d = f"M {sp[0][0]:.4f} {c._y(sp[0][1]):.4f} L {sp[1][0]:.4f} {c._y(sp[1][1]):.4f} "
    for i in (1, 3, 5, 7):
        nxt = sp[(i + 1) % 8]
        d += f"A {rr:.4f} {rr:.4f} 0 0 0 {nxt[0]:.4f} {c._y(nxt[1]):.4f} "
        after = sp[(i + 2) % 8]
        d += f"L {after[0]:.4f} {c._y(after[1]):.4f} "
    d += "Z"
    c.path(d, w=w, colour=colour, dash=dash)


def _cross(x1, y1, xm, ym, x2, y2) -> float:
    return (xm - x1) * (y2 - y1) - (ym - y1) * (x2 - x1)


def _arc_radius(x1, y1, xm, ym, x2, y2) -> float:
    d = 2 * (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym))
    if abs(d) < 1e-9:
        return math.hypot(x2 - x1, y2 - y1) / 2
    ux = ((x1**2 + y1**2) * (ym - y2) + (xm**2 + ym**2) * (y2 - y1)
          + (x2**2 + y2**2) * (y1 - ym)) / d
    uy = ((x1**2 + y1**2) * (x2 - xm) + (xm**2 + ym**2) * (x1 - x2)
          + (x2**2 + y2**2) * (xm - x1)) / d
    return math.hypot(x1 - ux, y1 - uy)


def draw_holes(c: Canvas, view: View, holes: tuple[Hole, ...]) -> None:
    for h in holes:
        px, py = view.pt(h.x, h.y)
        r = view.d(h.dia / 2)
        if h.keepout_dia:
            c.circle(px, py, view.d(h.keepout_dia / 2), w=style.W_PHANTOM,
                     colour=style.C_PHANTOM, dash="2.4,1.2,0.6,1.2")
        c.circle(px, py, r, w=style.W_OUTLINE, fill=style.C_FILL_HOLE)
        dims.centre_mark(c, px, py, max(r, 0.8))


def draw_feature(c: Canvas, view: View, f: Feature) -> None:
    x0, y0 = view.pt(f.x0, f.y0)
    x1, y1 = view.pt(f.x1, f.y1)
    hot = f.kind in HIGHLIGHT_KINDS
    colour = style.C_HIGHLIGHT if hot else style.C_COMPONENT
    dash = "2.2,1.4" if "not fitted" in f.label.lower() else None
    c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
           weight=style.W_COMPONENT if hot else style.W_PHANTOM,
           colour=colour, fill=style.C_FILL_LIGHT if hot else "none", dash=dash)
    if f.kind == "led":
        c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
               weight=0.05, colour=colour, fill=colour)


def draw_pmod(c: Canvas, view: View, p, spec: BoardSpec) -> None:
    """Pmod host: body outline plus the 2x6 pin field on its true grid."""
    if p.body_x1 > p.body_x0:
        bx0, by0 = view.pt(p.body_x0, p.body_y0)
        bx1, by1 = view.pt(p.body_x1, p.body_y1)
        c.rect(min(bx0, bx1), min(by0, by1), abs(bx1 - bx0), abs(by1 - by0),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash="3,1.5,0.8,1.5")
    horizontal = spec.front_edge in ("bottom", "top")
    half_span = p.pin_span / 2
    half_rows = p.row_span / 2
    for col in range(p.columns):
        for row in range(p.rows):
            if horizontal:
                x = p.cx - half_span + col * p.pitch
                y = p.cy - half_rows + row * p.pitch
            else:
                x = p.cx - half_rows + row * p.pitch
                y = p.cy - half_span + col * p.pitch
            px, py = view.pt(x, y)
            r = view.d(0.5)
            c.circle(px, py, r, w=style.W_COMPONENT, colour=style.C_HIGHLIGHT,
                     fill="#ffffff")
    cx, cy = view.pt(p.cx, p.cy)
    span = view.d(p.pin_span)
    rows = view.d(p.row_span)
    if horizontal:
        c.rect(cx - span / 2 - view.d(1.3), cy - rows / 2 - view.d(1.3),
               span + view.d(2.6), rows + view.d(2.6),
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT)
    else:
        c.rect(cx - rows / 2 - view.d(1.3), cy - span / 2 - view.d(1.3),
               rows + view.d(2.6), span + view.d(2.6),
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT)


class Obstacles:
    """Everything a balloon must not land on."""

    def __init__(self) -> None:
        self.rects: list[tuple[float, float, float, float]] = []
        self.circles: list[tuple[float, float, float]] = []
        self.segments: list[tuple[float, float, float, float]] = []

    def add_rect(self, x0, y0, x1, y1, pad: float = 0.0) -> None:
        self.rects.append((min(x0, x1) - pad, min(y0, y1) - pad,
                           max(x0, x1) + pad, max(y0, y1) + pad))

    def add_circle(self, cx, cy, r) -> None:
        self.circles.append((cx, cy, r))

    def add_segment(self, x1, y1, x2, y2) -> None:
        self.segments.append((x1, y1, x2, y2))

    def hits(self, cx: float, cy: float, r: float) -> int:
        n = 0
        for x0, y0, x1, y1 in self.rects:
            if cx + r > x0 and cx - r < x1 and cy + r > y0 and cy - r < y1:
                n += 1
        for ox, oy, orr in self.circles:
            if math.hypot(cx - ox, cy - oy) < r + orr:
                n += 1
        for x1, y1, x2, y2 in self.segments:
            if _point_segment_distance(cx, cy, x1, y1, x2, y2) < r:
                n += 1
        return n


def _point_segment_distance(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


#: Candidate balloon offsets, tried in order: close and to the side first,
#: then further out.  Angles start at "up and right" and go round.
_ANGLES = [i * 30 for i in range(12)]
_RADII = [9.0, 12.5, 16.5, 21.0, 27.0, 34.0]


def place_balloons(items: list[_Ballooned], obstacles: Obstacles,
                   bounds: Rect, c: Canvas) -> None:
    """Put each balloon near its feature, in the first free spot found.

    Balloons sit inside the drawing area rather than in a ring outside the
    part, because a ring forces long leaders that cross the view.  Placement is
    greedy: each balloon becomes an obstacle for the ones after it, so they
    never stack up.
    """
    for item in items:
        tx, ty = item.tip
        best = None
        best_score = None
        for radius in _RADII:
            for ang in _ANGLES:
                a = math.radians(ang)
                cx = tx + radius * math.cos(a)
                cy = ty + radius * math.sin(a)
                if not (bounds.x + BALLOON_R < cx < bounds.x1 - BALLOON_R
                        and bounds.y + BALLOON_R < cy < bounds.y1 - BALLOON_R):
                    continue
                score = obstacles.hits(cx, cy, BALLOON_R + 1.6) * 100 + radius
                if best_score is None or score < best_score:
                    best, best_score = (cx, cy), score
            if best_score is not None and best_score < 100:
                break
        if best is None:
            best = (tx + 10.0, ty + 10.0)
        dims.balloon(c, item.tip, best, item.label, radius=BALLOON_R)
        obstacles.add_circle(best[0], best[1], BALLOON_R + 1.2)
        obstacles.add_segment(item.tip[0], item.tip[1], best[0], best[1])


def _dim_places(value: float) -> int:
    return 2


def render_board(spec: BoardSpec, *, drawing_no: str, date: str,
                 sheet_size: str = "A3", extra_notes: tuple[str, ...] = (),
                 force_scale: float | None = None) -> Sheet:
    """Build a complete drawing sheet for *spec* and return it."""
    o = spec.outline
    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(),
        subtitle=spec.subtitle,
        drawing_no=drawing_no,
        rev="A",
        date=date,
        drawn_by="generated",
        units="mm",
    ))
    sheet.draw_frame()
    c = sheet.canvas

    # The view has to cover anything that hangs off the board edge: USB shells,
    # right-angle Pmod bodies, and so on.
    xs = [0.0, o.width]
    ys = [0.0, o.height]
    for f in spec.features:
        xs += [f.x0, f.x1]
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            xs += [p.body_x0, p.body_x1]
            ys += [p.body_y0, p.body_y1]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    view = View.fit(sheet.area, bbox, margin=48.0, force_scale=force_scale)
    sheet.title.scale = view.scale_label

    board = Rect(view.x(0), view.y(0), view.d(o.width), view.d(o.height))

    # --- geometry -----------------------------------------------------------
    for f in spec.features:
        draw_feature(c, view, f)
    for p in spec.pmods:
        draw_pmod(c, view, p, spec)
    outline_path(c, view, spec)
    draw_holes(c, view, spec.holes)

    # --- balloons -----------------------------------------------------------
    obstacles = Obstacles()
    for f in spec.features:
        obstacles.add_rect(*view.pt(f.x0, f.y0), *view.pt(f.x1, f.y1), pad=0.8)
    for h in spec.holes:
        obstacles.add_circle(*view.pt(h.x, h.y),
                             view.d(max(h.dia, h.keepout_dia or 0) / 2) + 1.0)
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            obstacles.add_rect(*view.pt(p.body_x0, p.body_y0),
                               *view.pt(p.body_x1, p.body_y1), pad=0.8)
    # The board edge itself: a balloon straddling it reads badly.
    for edge in ((0, 0, o.width, 0), (o.width, 0, o.width, o.height),
                 (o.width, o.height, 0, o.height), (0, o.height, 0, 0)):
        obstacles.add_segment(*view.pt(edge[0], edge[1]),
                              *view.pt(edge[2], edge[3]))

    items: list[_Ballooned] = []
    schedule: list[list[str]] = []
    # Largest features first: they have the least freedom, and placing them
    # early stops a small feature's balloon taking the only good spot.
    order = sorted(range(len(spec.features)),
                   key=lambda i: -(spec.features[i].width * spec.features[i].height))
    for n, f in enumerate(spec.features, 1):
        schedule.append([str(n), f.label,
                         f"{f.x0:.2f} to {f.x1:.2f}",
                         f"{f.y0:.2f} to {f.y1:.2f}"])
    for i in order:
        f = spec.features[i]
        items.append(_Ballooned(str(i + 1), view.pt(f.cx, f.cy)))
    place_balloons(items, obstacles, sheet.area, c)

    # --- dimensions ---------------------------------------------------------
    lowest = min([board.y] + [view.y(p.body_y0) for p in spec.pmods
                              if p.body_y1 > p.body_y0]
                 + [view.y(f.y0) for f in spec.features])
    leftmost = min([board.x] + [view.x(f.x0) for f in spec.features])

    if spec.pmods and spec.front_edge == "bottom" and len(spec.pmods) > 1:
        p0, p1 = spec.pmods[0], spec.pmods[1]
        dims.linear(c, view.pt(p0.cx, p0.cy), view.pt(p1.cx, p1.cy),
                    lowest - 6.0 - view.y(p0.cy), horizontal=True,
                    text=f"{p1.cx - p0.cx:.2f} TYP")
        lowest -= 6.0 + style.T_DIM + 2.0

    xvals = sorted({round(h.x, 3) for h in spec.holes}
                   | {round(p.cx, 3) for p in spec.pmods
                      if spec.front_edge in ("bottom", "top")})
    yvals = sorted({round(h.y, 3) for h in spec.holes}
                   | {round(p.cy, 3) for p in spec.pmods
                      if spec.front_edge in ("bottom", "top")})
    x_extent = dims.ordinate_chain(
        c, [(view.x(v), f"{v:.2f}") for v in xvals], board.y, lowest - 9.0,
        horizontal=True)
    y_extent = dims.ordinate_chain(
        c, [(view.y(v), f"{v:.2f}") for v in yvals], board.x, leftmost - 9.0,
        horizontal=False)

    dims.linear(c, (board.x, board.y), (board.x1, board.y),
                x_extent - 6.0 - board.y, horizontal=True, value=o.width)
    dims.linear(c, (board.x, board.y), (board.x, board.y1),
                y_extent - 6.0 - board.x, horizontal=False, value=o.height)
    # The datum sits in the busiest corner of the sheet, so its label goes out
    # on a leader into the empty wedge below and left of the ordinate chains
    # rather than next to the marker.
    dims.datum_marker(c, board.x, board.y, label="")
    dims.leader(c, (board.x, board.y),
                (min(y_extent, board.x - 34.0), board.y - 16.0),
                "DATUM  X0 Y0", tail=2.0, anchor="start", dot=True)

    if o.corner_radius:
        r = o.corner_radius
        tip = view.pt(o.width - r * 0.3, o.height - r * 0.3)
        dims.leader(c, tip, (board.x1 + 8.0, board.y1 + 5.0),
                    f"R{r:.2f} (4 places)")

    # --- annotation column --------------------------------------------------
    if spec.holes:
        rows = [[h.label or f"H{i}", f"{h.x:.2f}", f"{h.y:.2f}",
                 f"{h.dia:.2f}",
                 f"{h.keepout_dia:.2f}" if h.keepout_dia else "-"]
                for i, h in enumerate(spec.holes, 1)]
        block = sheet.column_block(len(rows) * style.T_TABLE * 1.75 + 14.0)
        sheet.table(block, "HOLE SCHEDULE",
                    ["ID", "X", "Y", "DIA", "KEEPOUT"], rows,
                    ["start", "end", "end", "end", "end"])

    if spec.pmods:
        rows = [[p.label, p.designator, f"{p.cx:.2f}", f"{p.cy:.2f}",
                 f"{p.pin1_x:.2f}", f"{p.pin1_y:.2f}"] for p in spec.pmods]
        block = sheet.column_block(len(rows) * style.T_TABLE * 1.75 + 14.0)
        sheet.table(block, "PMOD HOST HEADERS",
                    ["PORT", "REF", "CX", "CY", "PIN1 X", "PIN1 Y"], rows,
                    ["start", "start", "end", "end", "end", "end"])

    if schedule:
        block = sheet.column_block(len(schedule) * style.T_TABLE * 1.75 + 14.0)
        sheet.table(block, "FEATURE SCHEDULE",
                    ["#", "FEATURE", "X EXTENT", "Y EXTENT"], schedule,
                    ["middle", "start", "end", "end"])

    notes = [
        "All dimensions in millimetres. Datum is the lower-left corner of the "
        "board outline; X to the right, Y up, viewed from the component side.",
        "Hole and Pmod positions are ordinate dimensions from that single "
        "datum, so they do not accumulate tolerance.",
    ]
    notes += list(spec.notes) + list(extra_notes)
    notes.append(
        f"Fabrication tolerance is not called out per dimension. Assume "
        f"+/-{0.20:.2f} on the routed board edge, +/-{0.10:.2f} on drilled "
        f"hole position and +/-{0.08:.2f} on plated hole diameter unless the "
        f"board house states otherwise.")
    if o.profile_note:
        notes.append(o.profile_note)
    block = sheet.column_block(min(sheet.column_remaining * 0.62, 96.0))
    sheet.notes(block, "NOTES", notes)

    src_lines = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
                 for s in spec.sources]
    block = sheet.column_block(max(sheet.column_remaining - 2.0, 20.0))
    sheet.notes(block, "SOURCES", src_lines, size=style.T_TINY)

    sheet.draw_title_block()
    return sheet
