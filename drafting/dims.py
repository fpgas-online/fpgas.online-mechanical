"""Dimension, leader and balloon primitives, drawn in sheet millimetres.

Everything here follows ISO 129-1 practice closely enough to read as a real
engineering drawing: extension lines that stop short of the feature and run a
little past the dimension line, arrowheads that flip outboard when the
dimension is too narrow to hold them, and dimension text placed above and
centred on its line, reading from the bottom or from the right.
"""

from __future__ import annotations

import math

from . import style
from .canvas import Canvas


def _fmt(value: float, places: int = 2) -> str:
    return f"{value:.{places}f}"


def linear(c: Canvas, p1: tuple[float, float], p2: tuple[float, float],
           offset: float, *, horizontal: bool | None = None,
           text: str | None = None, places: int = 2, value: float | None = None,
           colour: str = style.C_DIM, size: float = style.T_DIM,
           extension: bool = True, flip_text: bool = False,
           text_offset: float = 0.0) -> None:
    """Dimension between two sheet points, offset perpendicular to their span.

    *offset* is signed: positive puts the dimension line above a horizontal
    dimension, or to the right of a vertical one.  *value* is the number to
    print, in model units; pass *text* to override it entirely.
    """
    (x1, y1), (x2, y2) = p1, p2
    if horizontal is None:
        horizontal = abs(x2 - x1) >= abs(y2 - y1)

    if horizontal:
        dy = offset
        line_y = max(y1, y2) + dy if dy >= 0 else min(y1, y2) + dy
        a, b = (min(x1, x2), line_y), (max(x1, x2), line_y)
        if extension:
            for x, y in ((x1, y1), (x2, y2)):
                gap = style.EXT_GAP * (1 if line_y > y else -1)
                over = style.EXT_OVER * (1 if line_y > y else -1)
                c.line(x, y + gap, x, line_y + over, w=style.W_THIN,
                       colour=colour)
        span = abs(x2 - x1)
        shown = span if value is None else value
        label = text if text is not None else _fmt(shown, places)
        tw = style.text_width(label, size)
        inside = span > tw + 2 * style.ARROW_LEN + 2.0
        c.line(a[0], line_y, b[0], line_y, w=style.W_THIN, colour=colour)
        if inside:
            c.arrow(a[0], line_y, 180, colour=colour)
            c.arrow(b[0], line_y, 0, colour=colour)
            tx = (a[0] + b[0]) / 2
        else:
            c.arrow(a[0], line_y, 0, colour=colour)
            c.arrow(b[0], line_y, 180, colour=colour)
            c.line(a[0] - style.ARROW_LEN * 2.2, line_y, a[0], line_y,
                   w=style.W_THIN, colour=colour)
            c.line(b[0], line_y, b[0] + style.ARROW_LEN * 2.2, line_y,
                   w=style.W_THIN, colour=colour)
            tx = b[0] + style.ARROW_LEN * 2.4 + tw / 2
        ty = line_y + style.DIM_TEXT_GAP + text_offset
        if flip_text:
            ty = line_y - style.DIM_TEXT_GAP - style.text_height(size) - text_offset
        c.text(tx, ty, label, size=size, colour=colour, anchor="middle")
    else:
        dx = offset
        line_x = max(x1, x2) + dx if dx >= 0 else min(x1, x2) + dx
        lo, hi = min(y1, y2), max(y1, y2)
        if extension:
            for x, y in ((x1, y1), (x2, y2)):
                gap = style.EXT_GAP * (1 if line_x > x else -1)
                over = style.EXT_OVER * (1 if line_x > x else -1)
                c.line(x + gap, y, line_x + over, y, w=style.W_THIN,
                       colour=colour)
        span = hi - lo
        shown = span if value is None else value
        label = text if text is not None else _fmt(shown, places)
        tw = style.text_width(label, size)
        inside = span > tw + 2 * style.ARROW_LEN + 2.0
        c.line(line_x, lo, line_x, hi, w=style.W_THIN, colour=colour)
        if inside:
            c.arrow(line_x, lo, -90, colour=colour)
            c.arrow(line_x, hi, 90, colour=colour)
            ty = (lo + hi) / 2
        else:
            c.arrow(line_x, lo, 90, colour=colour)
            c.arrow(line_x, hi, -90, colour=colour)
            c.line(line_x, lo - style.ARROW_LEN * 2.2, line_x, lo,
                   w=style.W_THIN, colour=colour)
            c.line(line_x, hi, line_x, hi + style.ARROW_LEN * 2.2,
                   w=style.W_THIN, colour=colour)
            ty = hi + style.ARROW_LEN * 2.4
        tx = line_x - style.DIM_TEXT_GAP - text_offset
        if flip_text:
            tx = line_x + style.DIM_TEXT_GAP + text_offset
        # Vertical dimension text reads from the right, per ISO 129-1.
        c.text(tx, ty, label, size=size, colour=colour, anchor="middle",
               rotate=90)


def centre_mark(c: Canvas, cx: float, cy: float, r: float, *,
                colour: str = style.C_LINE, over: float | None = None) -> None:
    """Cross centre mark, overshooting the circle as ISO 128 requires."""
    o = r + (style.CENTRE_OVER if over is None else over)
    c.line(cx - o, cy, cx + o, cy, w=style.W_CENTRE, colour=colour)
    c.line(cx, cy - o, cx, cy + o, w=style.W_CENTRE, colour=colour)


def leader(c: Canvas, tip: tuple[float, float], elbow: tuple[float, float],
           text: str, *, size: float = style.T_LABEL,
           colour: str = style.C_DIM, tail: float = 5.0,
           anchor: str | None = None, dot: bool = False) -> tuple[float, float]:
    """Leader with an arrow at *tip*, a bend at *elbow* and a horizontal tail.

    Returns the end of the tail, so a caller can line several up.
    """
    tx, ty = tip
    ex, ey = elbow
    to_right = ex >= tx
    end_x = ex + (tail if to_right else -tail)
    if dot:
        c.circle(tx, ty, 0.7, fill=colour, colour=colour, w=0.05)
    else:
        c.arrow(tx, ty, math.degrees(math.atan2(ty - ey, tx - ex)), colour=colour)
    c.line(tx, ty, ex, ey, w=style.W_THIN, colour=colour)
    c.line(ex, ey, end_x, ey, w=style.W_THIN, colour=colour)
    use = anchor or ("start" if to_right else "end")
    pad = 1.2 if use == "start" else -1.2
    c.text(end_x + pad, ey + 0.9, text, size=size, colour=colour, anchor=use)
    return end_x, ey


def balloon(c: Canvas, tip: tuple[float, float], centre: tuple[float, float],
            label: str, *, radius: float = 3.2, size: float = style.T_LABEL,
            colour: str = style.C_HIGHLIGHT) -> None:
    """Numbered balloon: a circled label on a leader with a dot at the feature."""
    tx, ty = tip
    bx, by = centre
    ang = math.atan2(by - ty, bx - tx)
    c.circle(tx, ty, 0.65, fill=colour, colour=colour, w=0.05)
    c.line(tx, ty, bx - radius * math.cos(ang), by - radius * math.sin(ang),
           w=style.W_THIN, colour=colour)
    c.circle(bx, by, radius, fill="#ffffff", colour=colour, w=style.W_THIN)
    c.text(bx, by, label, size=size, colour=colour, anchor="middle",
           baseline="middle", bold=True)


def datum_marker(c: Canvas, x: float, y: float, *, size: float = 4.0,
                 label: str = "X0 Y0", colour: str = style.C_DIM,
                 label_dx: float = 0.0, label_dy: float = 0.0) -> None:
    """Mark the drawing datum with a filled quadrant target and a label."""
    c.circle(x, y, size / 2, w=style.W_THIN, colour=colour)
    c.path(f"M {x} {c._y(y)} L {x + size / 2} {c._y(y)} "
           f"A {size / 2} {size / 2} 0 0 1 {x} {c._y(y + size / 2)} Z",
           fill=colour, colour=colour, w=0.05)
    c.path(f"M {x} {c._y(y)} L {x - size / 2} {c._y(y)} "
           f"A {size / 2} {size / 2} 0 0 1 {x} {c._y(y - size / 2)} Z",
           fill=colour, colour=colour, w=0.05)
    c.text(x + label_dx, y + label_dy, label, size=style.T_TINY, colour=colour,
           anchor="middle")


def ordinate_chain(c: Canvas, values, base: float, line_pos: float, *,
                   horizontal: bool, colour: str = style.C_DIM,
                   size: float = style.T_DIM, text_gap: float = 2.0,
                   stagger: float | None = None, zero_label: str = "0",
                   zero_pos: float | None = None,
                   zero_from: float | None = None) -> float:
    """Ordinate dimensions: every value measured from one datum, no chains.

    *values* are ``(pos, label, from_pos)`` triples: where the feature sits
    along the chain's axis, what to print, and where it sits on the other axis
    so the witness line can start **at the feature**.  A witness line that
    starts at the board edge instead tells the reader nothing about which
    feature the number belongs to, which is the usual failing of a generated
    ordinate chain.

    Labels that would land on top of each other are pushed out to a further
    lane, with the witness line extended to match.  A zero ordinate is drawn at
    the datum so the origin of the chain is explicit.

    Returns the outermost extent used, so the caller can place the overall
    dimensions clear of it.
    """
    out = 1 if line_pos > base else -1

    # A label in the next lane out must clear the one before it.  For a
    # horizontal chain the labels are turned on their side, so what has to
    # clear is their height; for a vertical chain it is their width.
    labels = [v[1] for v in values] + [zero_label]
    widest = max((style.text_width(t, size) for t in labels), default=0.0)
    tall = style.text_height(size) + style.descender(size)
    if stagger is None:
        stagger = (tall + text_gap + 1.6) if horizontal \
            else (widest + text_gap + 1.6)
    need = tall + 1.6

    # The zero ordinate marks the datum on the chain's own axis.  Using the
    # chain's *base*, which is the perpendicular coordinate, drops it somewhere
    # arbitrary along the chain.
    entries = list(values)
    if zero_pos is not None:
        entries = [(zero_pos, zero_label,
                    base if zero_from is None else zero_from)] + entries

    lanes: list[float] = []
    placed = []
    for pos, label, from_pos in sorted(entries, key=lambda e: e[0]):
        lane = 0
        while lane < len(lanes) and pos - lanes[lane] < need:
            lane += 1
        if lane == len(lanes):
            lanes.append(pos)
        else:
            lanes[lane] = pos
        placed.append((pos, label, from_pos, lane))

    extent = line_pos
    for pos, label, from_pos, lane in placed:
        end = line_pos + out * lane * stagger
        # Start clear of the feature, on the side the dimension line is on, as
        # ISO 129-1 asks of an extension line.  Subtracting here instead put
        # the start on the far side, so the line ran back through the feature
        # it was meant to stop short of.
        start = from_pos + out * style.EXT_GAP
        if (end - start) * out <= 0:
            start = end - out * style.EXT_OVER
        if horizontal:
            c.line(pos, start, pos, end, w=style.W_THIN, colour=colour)
            ty = end + (text_gap if out > 0 else
                        -text_gap - style.text_height(size))
            c.text(pos, ty, label, size=size, colour=colour, anchor="middle",
                   rotate=90)
            reach = ty + out * style.text_width(label, size)
        else:
            c.line(start, pos, end, pos, w=style.W_THIN, colour=colour)
            tx = end + (text_gap if out > 0 else -text_gap)
            c.text(tx, pos, label, size=size, colour=colour,
                   anchor="start" if out > 0 else "end", baseline="middle")
            reach = tx + out * style.text_width(label, size)
        extent = max(extent, reach) if out > 0 else min(extent, reach)
    return extent
