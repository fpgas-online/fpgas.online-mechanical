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

# Every feature in the schedule is drawn the same way.  Splitting them into
# emphasised and plain gave two unexplained line styles on one view, both
# carrying balloons and both in the same table, with nothing to say what the
# difference meant.  The one distinction kept is do-not-populate, which is
# drawn dashed and says so in its label.

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

#: Room reserved above and below a view.  Dimensions stack below and to the
#: left; only balloons need space above.
VIEW_MARGIN_SIDE = 46.0
VIEW_MARGIN_TOP = 22.0
VIEW_MARGIN_BOTTOM = 48.0

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
                # ("arc", x1, y1, x2, y2, radius, large_arc, counter_clockwise),
                # already resolved by the extractor.
                _, x1, y1, x2, y2, r, large, ccw = edge
                p1, p2 = view.pt(x1, y1), view.pt(x2, y2)
                c.arc(p1[0], p1[1], p2[0], p2[1], view.d(r), large=large,
                      sweep=ccw, w=w, colour=colour)
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


def draw_holes(c: Canvas, view: View, holes: tuple[Hole, ...]) -> None:
    for h in holes:
        px, py = view.pt(h.x, h.y)
        r = view.d(h.dia / 2)
        if h.keepout_dia:
            c.circle(px, py, view.d(h.keepout_dia / 2), w=style.W_PHANTOM,
                     colour=style.C_PHANTOM, dash=style.D_PHANTOM)
        c.circle(px, py, r, w=style.W_OUTLINE, fill=style.C_FILL_HOLE)
        dims.centre_mark(c, px, py, max(r, 0.8))


def draw_feature(c: Canvas, view: View, f: Feature) -> None:
    x0, y0 = view.pt(f.x0, f.y0)
    x1, y1 = view.pt(f.x1, f.y1)
    fitted = "not fitted" not in f.label.lower()
    colour = style.C_HIGHLIGHT if fitted else style.C_PHANTOM
    c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
           weight=style.W_COMPONENT, colour=colour,
           fill=style.C_FILL_LIGHT if fitted else "none",
           dash=None if fitted else style.D_HIDDEN)
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
               dash=style.D_PHANTOM)
    horizontal = p.edge in ("bottom", "top")
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

    def crossings(self, x1: float, y1: float, x2: float, y2: float) -> int:
        """How many recorded segments a proposed leader actually crosses.

        Sampling a leader against obstacles misses a clean crossing: two lines
        can intersect at a point that falls between samples.  A proper segment
        intersection test catches it, which is what stops two balloons swapping
        sides and crossing each other's leaders.
        """
        def side(ax, ay, bx, by, px, py):
            return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

        n = 0
        for ax, ay, bx, by in self.segments:
            d1 = side(x1, y1, x2, y2, ax, ay)
            d2 = side(x1, y1, x2, y2, bx, by)
            d3 = side(ax, ay, bx, by, x1, y1)
            d4 = side(ax, ay, bx, by, x2, y2)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                n += 1
        return n

    def leader_hits(self, x1: float, y1: float, x2: float, y2: float,
                    clearance: float = 1.0, samples: int = 14) -> int:
        """How much of a leader from (x1,y1) to (x2,y2) runs over something.

        Scoring only the balloon's own position lets its leader be routed
        straight through the feature next door, which is what put balloon 4 on
        the TT04 sheet across two neighbouring LEDs.
        """
        n = 0
        for i in range(1, samples):
            t = i / samples
            n += min(self.hits(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t,
                               clearance), 1)
        return n

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
_ANGLES = [i * 15 for i in range(24)]
_RADII = [9.0, 12.5, 16.5, 21.0, 27.0, 34.0]


def place_balloons(items: list[_Ballooned], obstacles: Obstacles,
                   bounds: Rect, c: Canvas, passes: int = 4) -> None:
    """Put each balloon near its feature, clear of everything else.

    A single greedy sweep is very order-sensitive: whichever balloon is placed
    first takes the best spot and the last one is left with whatever remains,
    which is how two balloons ended up touching and a leader ended up clipping
    a third.  So the greedy pass is followed by relaxation sweeps that re-place
    each balloon in turn against the others' final positions.  It converges in
    a couple of passes on drawings this size.
    """
    placed: list[tuple[float, float] | None] = [None] * len(items)

    def scene(skip: int) -> Obstacles:
        o = Obstacles()
        o.rects = list(obstacles.rects)
        o.circles = list(obstacles.circles)
        o.segments = list(obstacles.segments)
        for k, pos in enumerate(placed):
            if pos is None or k == skip:
                continue
            o.add_circle(pos[0], pos[1], BALLOON_R + 2.0)
            o.add_segment(items[k].tip[0], items[k].tip[1], pos[0], pos[1])
        return o

    def best_spot(index: int) -> tuple[float, float]:
        tx, ty = items[index].tip
        world = scene(index)
        best, best_score = None, None
        for radius in _RADII:
            for ang in _ANGLES:
                a = math.radians(ang)
                cx = tx + radius * math.cos(a)
                cy = ty + radius * math.sin(a)
                if not (bounds.x + BALLOON_R < cx < bounds.x1 - BALLOON_R
                        and bounds.y + BALLOON_R < cy < bounds.y1 - BALLOON_R):
                    continue
                # Landing on something is worst; crossing a leader is next; a
                # long leader is a real cost too, or a balloon will travel
                # halfway across the view to dodge a crossing it could have
                # avoided by moving a few millimetres.
                score = (world.hits(cx, cy, BALLOON_R + 2.0) * 100
                         + world.crossings(tx, ty, cx, cy) * 60
                         + world.leader_hits(tx, ty, cx, cy) * 30
                         + radius * 2.0)
                if best_score is None or score < best_score:
                    best, best_score = (cx, cy), score
            if best_score is not None and best_score < radius * 2.0 + 1:
                break
        return best or (tx + 10.0, ty + 10.0)

    for i in range(len(items)):
        placed[i] = best_spot(i)
    for _ in range(passes):
        for i in range(len(items)):
            placed[i] = best_spot(i)

    for item, pos in zip(items, placed):
        dims.balloon(c, item.tip, pos, item.label, radius=BALLOON_R)


def _view_height_needed(spec: BoardSpec, overlay: BoardSpec | None) -> float:
    """Vertical room the view and its dimensions want, in sheet millimetres."""
    ys = [0.0, spec.outline.height]
    for f in spec.features:
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_y1 > p.body_y0:
            ys += [p.body_y0, p.body_y1]
    if overlay is not None:
        ys += [0.0, overlay.outline.height]
    return (max(ys) - min(ys)) + VIEW_MARGIN_TOP + VIEW_MARGIN_BOTTOM


def _sheet_text(spec: BoardSpec, overlay: BoardSpec | None,
                extra_notes: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """The notes and sources this sheet will carry."""
    o = spec.outline
    notes = [
        "All dimensions in millimetres. The datum symbol marks the origin: "
        "the lower-left corner of the board outline, X right, Y up, viewed "
        "from the component side.",
    ]
    if overlay is not None:
        notes.append(
            f"Phantom outline is the {overlay.title} fitted to the 40-pin GPIO "
            "header, drawn in this board's frame because its mounting holes "
            "coincide with this board's.")
    notes += list(spec.notes) + list(extra_notes)
    if overlay is not None:
        notes.append(
            "Those host positions are DERIVED, not published: Digilent issue "
            "no mechanical drawing for the adapter. Good to about +/-0.75 mm. "
            "JA and JB face out of the left edge, JC out of the lower edge, "
            "all right-angle hosts whose bodies overhang the edge. The Pmod "
            "HAT Adapter sheet has the derivation.")
    if o.profile_note:
        notes.append(o.profile_note)
    sources = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
               for s in spec.sources]
    return notes, sources


def note_blocks(notes: list[str], sources: list[str]):
    blocks = [("NOTES", notes, style.T_NOTE)]
    if sources:
        blocks.append(("SOURCES", sources, style.T_TINY))
    return blocks


def _place_notes_and_sources(sheet: Sheet, notes: list[str],
                             sources: list[str], columns: int = 2) -> None:
    """Draw the notes and sources in the band across the bottom of the sheet.

    Everything stays in the band.  Spilling the tail into the annotation column
    put a continuation above the block it continued, which reads badly: a
    reader scanning down the sheet meets note 10 before note 1.
    """
    sheet.notes_columns(sheet.band_columns(sheet.notes_band, count=columns),
                        note_blocks(notes, sources))


def draw_overlay(c: Canvas, view: View, spec: BoardSpec) -> None:
    """Draw an adjacent part in phantom line, ISO 128 style.

    Used to show where a Digilent Pmod HAT Adapter's host connectors land once
    it is plugged onto a Raspberry Pi.  Phantom line is the convention for a
    part that is not the subject of the drawing but constrains it.
    """
    outline_path(c, view, spec, colour=style.C_PHANTOM, w=style.W_PHANTOM,
                 dash=style.D_PHANTOM)
    for p in spec.pmods:
        horizontal = p.edge in ("bottom", "top")
        half_span, half_rows = p.pin_span / 2, p.row_span / 2
        xs, ys = [], []
        for col in range(p.columns):
            for row in range(p.rows):
                if horizontal:
                    x = p.cx - half_span + col * p.pitch
                    y = p.cy - half_rows + row * p.pitch
                else:
                    x = p.cx - half_rows + row * p.pitch
                    y = p.cy - half_span + col * p.pitch
                xs.append(x)
                ys.append(y)
                px, py = view.pt(x, y)
                c.circle(px, py, view.d(0.5), w=style.W_PHANTOM,
                         colour=style.C_PHANTOM, fill="#ffffff")
        x0, y0 = view.pt(min(xs) - 1.3, min(ys) - 1.3)
        x1, y1 = view.pt(max(xs) + 1.3, max(ys) + 1.3)
        c.rect(x0, y0, x1 - x0, y1 - y0, weight=style.W_COMPONENT,
               colour=style.C_PHANTOM)
        # Label goes inboard of the pin field, away from the edge the host
        # faces, so it never sits on top of the pins.
        pad = 2.0
        if p.edge == "left":
            lx, ly, anchor = x1 + pad, (y0 + y1) / 2, "start"
        elif p.edge == "right":
            lx, ly, anchor = x0 - pad, (y0 + y1) / 2, "end"
        elif p.edge == "bottom":
            lx, ly, anchor = (x0 + x1) / 2, y1 + pad, "middle"
        else:
            lx, ly, anchor = (x0 + x1) / 2, y0 - pad - style.T_LABEL, "middle"
        c.text(lx, ly, p.label, size=style.T_LABEL, colour=style.C_PHANTOM,
               anchor=anchor, baseline="middle" if p.edge in ("left", "right")
               else "alphabetic", bold=True)


def render_board(spec: BoardSpec, *, drawing_no: str, date: str,
                 sheet_size: str = "A3", extra_notes: tuple[str, ...] = (),
                 force_scale: float | None = None,
                 overlay: BoardSpec | None = None) -> Sheet:
    """Build a complete drawing sheet for *spec* and return it."""
    o = spec.outline

    # The notes are known before anything is drawn, and their height decides
    # how much of the sheet is left for the view, so they are built first and
    # the band is sized to them.
    notes, src_lines = _sheet_text(spec, overlay, extra_notes)
    view_needs = _view_height_needed(spec, overlay)
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src_lines),
        max_height=style.SHEET_SIZES[sheet_size][1] - 2 * (style.SHEET_MARGIN + 5)
        - view_needs - 6.0)

    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(),
        subtitle=spec.subtitle,
        drawing_no=drawing_no,
        rev="A",
        date=date,
        drawn_by="generated",
        units="mm",
        # Board thickness matters: standoff and screw length depend on it.
        material=(f"PCB, {o.thickness:.2f} thick" if o.thickness
                  else "PCB, thickness not stated"),
        **({"tolerance": spec.tolerance} if spec.tolerance else {}),
    ), notes_band_height=band_h)
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
    if overlay is not None:
        xs += [0.0, overlay.outline.width]
        ys += [0.0, overlay.outline.height]
        for p in overlay.pmods:
            xs += [p.cx - p.pin_span / 2 - 2, p.cx + p.pin_span / 2 + 2]
            ys += [p.cy - p.pin_span / 2 - 2, p.cy + p.pin_span / 2 + 2]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    # Dimensions stack below and left; only balloons need room above.
    view = View.fit(sheet.area, bbox, margin=VIEW_MARGIN_SIDE,
                    margin_top=VIEW_MARGIN_TOP,
                    margin_bottom=VIEW_MARGIN_BOTTOM, force_scale=force_scale)
    sheet.title.scale = view.scale_label

    board = Rect(view.x(0), view.y(0), view.d(o.width), view.d(o.height))

    # --- geometry -----------------------------------------------------------
    if overlay is not None:
        draw_overlay(c, view, overlay)
    for f in spec.features:
        draw_feature(c, view, f)
    for p in spec.pmods:
        draw_pmod(c, view, p, spec)
    outline_path(c, view, spec)
    draw_holes(c, view, spec.holes)

    # --- balloons -----------------------------------------------------------
    # Where the dimension bands will go, computed before the balloons so they
    # can be kept out of it.  A balloon sitting on an ordinate witness line
    # reads as though it belongs to the dimension.
    dim_bottom = min([board.y] + [view.y(p.body_y0) for p in spec.pmods
                                  if p.body_y1 > p.body_y0]
                     + [view.y(f.y0) for f in spec.features])
    dim_left = min([board.x] + [view.x(f.x0) for f in spec.features])
    balloon_bounds = Rect(dim_left, dim_bottom,
                          sheet.area.x1 - dim_left, sheet.area.y1 - dim_bottom)

    obstacles = Obstacles()
    for f in spec.features:
        obstacles.add_rect(*view.pt(f.x0, f.y0), *view.pt(f.x1, f.y1), pad=0.8)
    # The radius callout is drawn after the balloons but occupies its space
    # regardless, so reserve it now.
    if o.corner_radius:
        rlabel = f"R{o.corner_radius:.2f} (4 places), board outline" \
            if overlay is not None else f"R{o.corner_radius:.2f} (4 places)"
        rw = style.text_width(rlabel, style.T_LABEL)
        obstacles.add_rect(board.x1 + 8.0, board.y1 + 3.0,
                           board.x1 + 8.0 + rw + 8.0, board.y1 + 8.0, pad=1.0)
        obstacles.add_segment(*view.pt(o.width - o.corner_radius * 0.3,
                                       o.height - o.corner_radius * 0.3),
                              board.x1 + 8.0, board.y1 + 5.0)

    if overlay is not None:
        # The phantom part is drawn on this view, so a balloon must keep off it
        # too.  Its Pmod hosts, and the labels beside them, are what gets in
        # the way.
        for p in overlay.pmods:
            half_a, half_b = p.pin_span / 2 + 1.6, p.row_span / 2 + 1.6
            if p.edge in ("bottom", "top"):
                half_x, half_y = half_a, half_b
            else:
                half_x, half_y = half_b, half_a
            obstacles.add_rect(*view.pt(p.cx - half_x, p.cy - half_y),
                               *view.pt(p.cx + half_x, p.cy + half_y), pad=1.0)
            lw = style.text_width(p.label, style.T_LABEL, bold=True)
            lx0, ly0 = view.pt(p.cx - half_x, p.cy - half_y)
            lx1, ly1 = view.pt(p.cx + half_x, p.cy + half_y)
            if p.edge == "left":
                obstacles.add_rect(lx1, ly0, lx1 + lw + 3.0, ly1, pad=1.0)
            elif p.edge == "right":
                obstacles.add_rect(lx0 - lw - 3.0, ly0, lx0, ly1, pad=1.0)
            else:
                mid = (lx0 + lx1) / 2
                obstacles.add_rect(mid - lw / 2, ly1, mid + lw / 2,
                                   ly1 + style.T_LABEL + 3.0, pad=1.0)
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
    place_balloons(items, obstacles, balloon_bounds, c)

    # --- dimensions ---------------------------------------------------------
    lowest, leftmost = dim_bottom, dim_left

    # Pmod host spacing is dimensioned per board edge, between the first two
    # hosts on that edge.  Taking the first two hosts overall instead gives a
    # meaningless 0.00 on a board like the Pmod HAT Adapter, whose JA and JB
    # sit one above the other on the same edge.
    by_edge: dict[str, list] = {}
    for p in spec.pmods:
        by_edge.setdefault(p.edge, []).append(p)
    for edge, group in by_edge.items():
        if len(group) < 2:
            continue
        along = "cx" if edge in ("bottom", "top") else "cy"
        group = sorted(group, key=lambda p: getattr(p, along))
        p0, p1 = group[0], group[1]
        spacing = getattr(p1, along) - getattr(p0, along)
        if spacing < 0.01:
            continue
        label = f"{spacing:.2f} TYP" if len(group) > 2 else f"{spacing:.2f}"
        if along == "cx":
            dims.linear(c, view.pt(p0.cx, p0.cy), view.pt(p1.cx, p1.cy),
                        lowest - 6.0 - view.y(p0.cy), horizontal=True,
                        text=label)
            lowest -= 6.0 + style.T_DIM + 2.0
        else:
            dims.linear(c, view.pt(p0.cx, p0.cy), view.pt(p1.cx, p1.cy),
                        leftmost - 6.0 - view.x(p0.cx), horizontal=False,
                        text=label)
            leftmost -= 6.0 + style.T_DIM + 2.0

    # Each ordinate entry carries the feature's other-axis coordinate too, so
    # its witness line can start at the feature rather than at a board edge.
    xvals: dict[float, float] = {}
    yvals: dict[float, float] = {}

    def note_x(x, y):
        xvals[round(x, 3)] = max(xvals.get(round(x, 3), y), y) \
            if spec.front_edge == "top" else min(xvals.get(round(x, 3), y), y)

    def note_y(y, x):
        yvals[round(y, 3)] = min(yvals.get(round(y, 3), x), x)

    for h in spec.holes:
        note_x(h.x, h.y)
        note_y(h.y, h.x)
    # A host on a horizontal edge is located along that edge by its X, one on a
    # vertical edge by its Y: that is the coordinate a mating peripheral cares
    # about.  The board's own hosts also get their depth in from the edge
    # dimensioned, since that is what a plate has to clear.
    # A Pmod host goes into the chain that locates it along its edge, and only
    # that one.  Putting its depth into the other chain landed a value within
    # a third of a millimetre of a mounting hole's, so the two witness lines
    # printed as one and neither label could be tied to a line.  The depth gets
    # its own dimension instead.
    for p in spec.pmods:
        if p.edge in ("bottom", "top"):
            note_x(p.cx, p.cy)
        else:
            note_y(p.cy, p.cx)
    for p in (overlay.pmods if overlay else ()):
        if p.edge in ("bottom", "top"):
            note_x(p.cx, p.cy)
        else:
            note_y(p.cy, p.cx)

    # The Pmod pin-field depth, dimensioned once per edge rather than folded
    # into an ordinate chain.
    for edge, group in by_edge.items():
        outer = max(group, key=lambda p: p.cx if edge in ("bottom", "top")
                    else p.cy)
        if edge == "bottom":
            x = view.x(outer.cx + outer.pin_span / 2 + 5.0)
            dims.linear(c, (x, board.y), (x, view.y(outer.cy)), 0.0,
                        horizontal=False, value=outer.cy)
        elif edge == "top":
            x = view.x(outer.cx + outer.pin_span / 2 + 5.0)
            dims.linear(c, (x, view.y(outer.cy)), (x, board.y1), 0.0,
                        horizontal=False, value=o.height - outer.cy)
        elif edge == "left":
            y = view.y(outer.cy + outer.pin_span / 2 + 5.0)
            dims.linear(c, (board.x, y), (view.x(outer.cx), y), 0.0,
                        horizontal=True, value=outer.cx)
        else:
            y = view.y(outer.cy + outer.pin_span / 2 + 5.0)
            dims.linear(c, (view.x(outer.cx), y), (board.x1, y), 0.0,
                        horizontal=True, value=o.width - outer.cx)

    # Witness lines break where they cross a drawn part, rather than running
    # through it.
    blockers = [(*view.pt(f.x0, f.y0), *view.pt(f.x1, f.y1))
                for f in spec.features]
    blockers += [(*view.pt(h.x - h.dia / 2 - 0.6, h.y - h.dia / 2 - 0.6),
                  *view.pt(h.x + h.dia / 2 + 0.6, h.y + h.dia / 2 + 0.6))
                 for h in spec.holes]
    for p in spec.pmods:
        half_a, half_b = p.pin_span / 2 + 1.4, p.row_span / 2 + 1.4
        hx, hy = ((half_a, half_b) if p.edge in ("bottom", "top")
                  else (half_b, half_a))
        blockers.append((*view.pt(p.cx - hx, p.cy - hy),
                         *view.pt(p.cx + hx, p.cy + hy)))
    blockers = [(min(b[0], b[2]), min(b[1], b[3]),
                 max(b[0], b[2]), max(b[1], b[3])) for b in blockers]

    x_extent = dims.ordinate_chain(
        c, [(view.x(v), f"{v:.2f}", view.y(f)) for v, f in xvals.items()],
        board.y, lowest - 9.0, horizontal=True,
        zero_pos=board.x, zero_from=board.y, blockers=blockers)
    y_extent = dims.ordinate_chain(
        c, [(view.y(v), f"{v:.2f}", view.x(f)) for v, f in yvals.items()],
        board.x, leftmost - 9.0, horizontal=False,
        zero_pos=board.y, zero_from=board.x, blockers=blockers)

    # Extension lines start outside the ordinate labels, not at the board, so
    # they do not run through them on the way out.
    dims.linear(c, (board.x, board.y), (board.x1, board.y),
                x_extent - 6.0 - board.y, horizontal=True, value=o.width,
                ext_start=x_extent - 2.0)
    dims.linear(c, (board.x, board.y), (board.x, board.y1),
                y_extent - 6.0 - board.x, horizontal=False, value=o.height,
                ext_start=y_extent - 2.0)
    # The datum sits in the busiest corner of the sheet, so its label goes out
    # on a leader into the empty wedge below and left of the ordinate chains
    # rather than next to the marker.
    dims.datum_marker(c, board.x, board.y, label="")

    if o.corner_radius:
        r = o.corner_radius
        tip = view.pt(o.width - r * 0.3, o.height - r * 0.3)
        # Says which outline it applies to, because on the Pi 3A+ the phantom
        # Pmod HAT Adapter outline runs within half a millimetre of the board's
        # own and the callout would otherwise be ambiguous.
        label = f"R{r:.2f} (4 places), board outline" if overlay is not None \
            else f"R{r:.2f} (4 places)"
        dims.leader(c, tip, (board.x1 + 8.0, board.y1 + 5.0), label)

    # --- annotation column --------------------------------------------------
    if spec.holes:
        rows = [[h.label or f"H{i}", f"{h.x:.2f}", f"{h.y:.2f}",
                 f"{h.dia:.2f}" + (f" +/-{h.tol:.2f}" if h.tol else ""),
                 f"{h.keepout_dia:.2f}" if h.keepout_dia else "not given"]
                for i, h in enumerate(spec.holes, 1)]
        block = sheet.column_block(sheet.table_height("HOLE SCHEDULE", len(rows)))
        sheet.table(block, "HOLE SCHEDULE",
                    ["ID", "X mm", "Y mm", "DIA mm", "KEEPOUT mm"], rows,
                    ["start", "end", "end", "end", "end"])

    if spec.pmods:
        # Drop the designator column when it just repeats the port name, as it
        # does on the Pmod HAT Adapter where both read JA, JB, JC.
        show_ref = any(p.designator and p.designator != p.label
                       for p in spec.pmods)
        head = ["PORT"] + (["REF"] if show_ref else []) + \
            ["EDGE", "CX mm", "CY mm", "PIN1 X mm", "PIN1 Y mm"]
        align = ["start"] + (["start"] if show_ref else []) + \
            ["start", "end", "end", "end", "end"]
        # Three decimals here on purpose: at two, 27.695 and 50.555 print as
        # 27.70 and 50.55, whose difference is 22.85, contradicting the 22.86
        # pitch dimensioned on the view.
        rows = [[p.label] + ([p.designator] if show_ref else [])
                + [p.edge, f"{p.cx:.3f}", f"{p.cy:.3f}",
                   f"{p.pin1_x:.3f}", f"{p.pin1_y:.3f}"] for p in spec.pmods]
        block = sheet.column_block(sheet.table_height("PMOD HOST HEADERS", len(rows)))
        sheet.table(block, "PMOD HOST HEADERS", head, rows, align)

    if schedule:
        block = sheet.column_block(sheet.table_height("FEATURE SCHEDULE", len(schedule)))
        sheet.table(block, "FEATURE SCHEDULE",
                    ["#", "FEATURE", "X EXTENT mm", "Y EXTENT mm"], schedule,
                    ["middle", "start", "end", "end"])

    if overlay is not None and overlay.pmods:
        # Pin 1 is included here as well: it is what a plate has to register
        # a mating peripheral against.
        rows = [[p.label, f"{p.edge} edge", f"{p.cx:.2f}", f"{p.cy:.2f}",
                 f"{p.pin1_x:.2f}", f"{p.pin1_y:.2f}"] for p in overlay.pmods]
        block = sheet.column_block(sheet.table_height("PMOD HAT ADAPTER HOSTS", len(rows)))
        sheet.table(block, "PMOD HAT ADAPTER HOSTS",
                    ["PORT", "EDGE", "CX mm", "CY mm", "PIN1 X mm",
                     "PIN1 Y mm"], rows,
                    ["start", "start", "end", "end", "end", "end"])

    # Notes carry facts about this board, not an explanation of how to read a
    # drawing.  The column is finite, and losing a provenance note to make room
    # for a description of ordinate dimensioning is a bad trade.
    _place_notes_and_sources(sheet, notes, src_lines, columns=band_cols)

    sheet.draw_title_block()
    return sheet
