"""Dimension, leader and balloon primitives, drawn in sheet millimetres.

Everything here follows ISO 129-1 practice closely enough to read as a real
engineering drawing: extension lines that stop short of the feature and run a
little past the dimension line, arrowheads that flip outboard when the
dimension is too narrow to hold them, and dimension text placed above and
centred on its line, reading from the bottom or from the right.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import style
from .canvas import Canvas


def _fmt(value: float, places: int = 2) -> str:
    return f"{value:.{places}f}"


@dataclass(frozen=True)
class LinearDim:
    """Where :func:`linear` will put its line, its arrows and its value.

    Worked out apart from the drawing so that a caller which has to keep paper
    clear for the value can ask where the value goes instead of guessing.  The
    pin-field depth dimension writes its value beside its line rather than
    between its arrows, and the balloon placer, told only about the line, put
    a balloon through the last digit of a 3.23.
    """

    horizontal: bool
    #: The dimension line: its Y for a horizontal dimension, its X for a
    #: vertical one.
    line: float
    lo: float
    hi: float
    #: Whether the value fits between the arrows.  When it does not, the
    #: arrows point inwards and the value sits beyond one end.
    inside: bool
    label: str
    size: float
    tx: float
    ty: float
    anchor: str
    rotate: float

    @property
    def text_box(self) -> tuple[float, float, float, float]:
        """The value's bounding box in sheet millimetres, Y up.

        The same box ``tools/check_sheets.py`` recovers from the finished SVG,
        derived the same way: the anchor decides which end of the run the
        point is, and a rotated run stands the ascender and descender out to
        the sides instead of above and below.
        """
        w = style.text_width(self.label, self.size)
        asc, desc = style.text_height(self.size), style.descender(self.size)
        start = {"start": 0.0, "middle": -w / 2, "end": -w}[self.anchor]
        if self.rotate:
            y0 = self.ty + start
            return (self.tx - asc, y0, self.tx + desc, y0 + w)
        x0 = self.tx + start
        return (x0, self.ty - desc, x0 + w, self.ty + asc)


def linear_geometry(p1: tuple[float, float], p2: tuple[float, float],
                    offset: float, *, horizontal: bool | None = None,
                    text: str | None = None, places: int = 2,
                    value: float | None = None, size: float = style.T_DIM,
                    text_offset: float = 0.0,
                    text_side: str | None = None) -> LinearDim:
    """Where :func:`linear` would put everything, without drawing any of it.

    :func:`linear` places its own line, arrows and value from this and nothing
    else, so a caller that needs the value's paper reserved gets the answer
    the drawing will use rather than a second derivation of it.
    """
    (x1, y1), (x2, y2) = p1, p2
    if horizontal is None:
        horizontal = abs(x2 - x1) >= abs(y2 - y1)
    stub = style.ARROW_LEN * 2.2 + 1.4

    if horizontal:
        line = max(y1, y2) + offset if offset >= 0 else min(y1, y2) + offset
        lo, hi = min(x1, x2), max(x1, x2)
        span = abs(x2 - x1)
    else:
        line = max(x1, x2) + offset if offset >= 0 else min(x1, x2) + offset
        lo, hi = min(y1, y2), max(y1, y2)
        span = hi - lo
    label = text if text is not None else _fmt(span if value is None else value,
                                               places)
    inside = span > style.text_width(label, size) + 2 * style.ARROW_LEN + 2.0

    # Centred on its own span unless the value will not fit between the arrows
    # and the caller has said which side has room.  ISO 129-1 puts such a value
    # outside the extension lines, and only the caller knows which side is
    # free: in a stack of dimensions one side is the next dimension's.
    along, anchor = (lo + hi) / 2, "middle"
    if not inside and text_side:
        along, anchor = ((lo - stub, "end") if text_side == "low"
                         else (hi + stub, "start"))

    if horizontal:
        # Clear of the line by the gap, with the descender allowed for: the
        # baseline is not the bottom of the text.
        below = style.DIM_TEXT_GAP + style.descender(size)
        return LinearDim(True, line, lo, hi, inside, label, size,
                         along, line + below + text_offset, anchor, 0.0)
    # Turned on its side and centred, so half the character height sticks out
    # towards the dimension line and has to be cleared as well.
    aside = (style.DIM_TEXT_GAP + style.text_height(size) / 2
             + style.descender(size) / 2)
    return LinearDim(False, line, lo, hi, inside, label, size,
                     line - aside - text_offset, along, anchor, 90.0)


def linear(c: Canvas, p1: tuple[float, float], p2: tuple[float, float],
           offset: float, *, horizontal: bool | None = None,
           text: str | None = None, places: int = 2, value: float | None = None,
           colour: str = style.C_DIM, size: float = style.T_DIM,
           extension: bool = True,
           text_offset: float = 0.0, ext_start: float | None = None,
           text_side: str | None = None) -> LinearDim:
    """Dimension between two sheet points, offset perpendicular to their span.

    *offset* is signed: positive puts the dimension line above a horizontal
    dimension, or to the right of a vertical one.  *value* is the number to
    print, in model units; pass *text* to override it entirely.

    *ext_start* moves the start of the extension lines away from the feature.
    An overall dimension placed outside an ordinate chain would otherwise run
    its extension lines from the part all the way out, straight through the
    ordinate labels on the way.

    *text_side* is "low" or "high" and says which end a value too wide for its
    span is written beyond: "low" past the left or bottom end, "high" past the
    right or top.  See :func:`linear_geometry`, which decides all of that and
    is returned, so a caller can reserve the paper the value lands on.
    """
    g = linear_geometry(p1, p2, offset, horizontal=horizontal, text=text,
                        places=places, value=value, size=size,
                        text_offset=text_offset, text_side=text_side)
    (x1, y1), (x2, y2) = p1, p2
    over = style.EXT_OVER if g.inside else 0.0
    tail = style.ARROW_LEN * 2.2

    if g.horizontal:
        line_y = g.line
        if extension:
            for x, y in ((x1, y1), (x2, y2)):
                sign = 1 if line_y > y else -1
                start = y + style.EXT_GAP * sign if ext_start is None \
                    else ext_start
                # A value too wide for its span sits on the far side of the
                # dimension line, and the extension lines stop at the line
                # rather than overshooting into it.
                c.line(x, start, x, line_y + over * sign,
                       w=style.W_THIN, colour=colour)
        c.line(g.lo, line_y, g.hi, line_y, w=style.W_THIN, colour=colour)
        if g.inside:
            c.arrow(g.lo, line_y, 180, colour=colour)
            c.arrow(g.hi, line_y, 0, colour=colour)
        else:
            c.arrow(g.lo, line_y, 0, colour=colour)
            c.arrow(g.hi, line_y, 180, colour=colour)
            c.line(g.lo - tail, line_y, g.lo, line_y,
                   w=style.W_THIN, colour=colour)
            c.line(g.hi, line_y, g.hi + tail, line_y,
                   w=style.W_THIN, colour=colour)
        c.text(g.tx, g.ty, g.label, size=size, colour=colour, anchor=g.anchor)
    else:
        line_x = g.line
        if extension:
            for x, y in ((x1, y1), (x2, y2)):
                sign = 1 if line_x > x else -1
                start = x + style.EXT_GAP * sign if ext_start is None \
                    else ext_start
                c.line(start, y, line_x + over * sign, y,
                       w=style.W_THIN, colour=colour)
        c.line(line_x, g.lo, line_x, g.hi, w=style.W_THIN, colour=colour)
        if g.inside:
            c.arrow(line_x, g.lo, -90, colour=colour)
            c.arrow(line_x, g.hi, 90, colour=colour)
        else:
            c.arrow(line_x, g.lo, 90, colour=colour)
            c.arrow(line_x, g.hi, -90, colour=colour)
            c.line(line_x, g.lo - tail, line_x, g.lo,
                   w=style.W_THIN, colour=colour)
            c.line(line_x, g.hi, line_x, g.hi + tail,
                   w=style.W_THIN, colour=colour)
        # Vertical dimension text reads from the right, per ISO 129-1.
        c.text(g.tx, g.ty, g.label, size=size, colour=colour, anchor=g.anchor,
               rotate=90)
    return g



def centre_mark(c: Canvas, cx: float, cy: float, r: float, *,
                colour: str = style.C_LINE, over: float | None = None) -> None:
    """Cross centre mark, overshooting the circle as ISO 128 requires."""
    o = r + (style.CENTRE_OVER if over is None else over)
    c.line(cx - o, cy, cx + o, cy, w=style.W_CENTRE, colour=colour)
    c.line(cx, cy - o, cx, cy + o, w=style.W_CENTRE, colour=colour)


#: Length of a leader's horizontal tail, before its text.
LEADER_TAIL = 5.0


def leader(c: Canvas, tip: tuple[float, float], elbow: tuple[float, float],
           text: str, *, size: float = style.T_LABEL,
           colour: str = style.C_DIM, tail: float = LEADER_TAIL,
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
            colour: str = style.C_HIGHLIGHT, dash: str | None = None) -> None:
    """Numbered balloon: a circled label on a leader with a dot at the feature.

    *dash* draws the ring itself broken.  A sheet that superimposes several
    variants of one part cannot say which variant a balloon means by where
    its dot is -- the outlines lie on top of each other -- so the ring is
    drawn in the same line type as the outline it points at, which a
    monochrome print keeps and a colour alone would not.
    """
    tx, ty = tip
    bx, by = centre
    ang = math.atan2(by - ty, bx - tx)
    # A white core under the terminator: the dot is drawn in the same colour
    # as a filled feature, so on the LEDs, which are solid, it vanished and
    # the leader appeared to stop at nothing.
    c.circle(tx, ty, 1.05, fill="#ffffff", colour="#ffffff", w=0.05)
    c.circle(tx, ty, 0.65, fill=colour, colour=colour, w=0.05)
    c.line(tx, ty, bx - radius * math.cos(ang), by - radius * math.sin(ang),
           w=style.W_THIN, colour=colour)
    c.circle(bx, by, radius, fill="#ffffff", colour=colour, w=style.W_THIN,
             dash=dash)
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
    if label:
        c.text(x + label_dx, y + label_dy, label, size=style.T_TINY,
               colour=colour, anchor="middle")


def broken_line(c: Canvas, x1: float, y1: float, x2: float, y2: float,
                blockers, gap: float = 1.0, **kw) -> None:
    """Draw an axis-aligned line, leaving a gap where it crosses a blocker.

    An ordinate witness line runs from its feature to the chain, which on a
    board can be most of the width of the view.  Running it straight through
    every part on the way is what makes a generated ordinate chain look wrong;
    a real drawing breaks the line.
    """
    vertical = abs(x2 - x1) < 1e-9
    lo, hi = (min(y1, y2), max(y1, y2)) if vertical else (min(x1, x2), max(x1, x2))
    fixed = x1 if vertical else y1

    cuts = []
    for bx0, by0, bx1, by1 in blockers:
        across = (bx0 - gap, bx1 + gap) if vertical else (by0 - gap, by1 + gap)
        along = (by0 - gap, by1 + gap) if vertical else (bx0 - gap, bx1 + gap)
        if across[0] <= fixed <= across[1] and along[1] > lo and along[0] < hi:
            cuts.append((max(along[0], lo), min(along[1], hi)))
    cuts.sort()

    pos = lo
    for a, b in cuts:
        if a > pos:
            _seg(c, fixed, pos, a, vertical, **kw)
        pos = max(pos, b)
    if pos < hi:
        _seg(c, fixed, pos, hi, vertical, **kw)


def _seg(c: Canvas, fixed: float, a: float, b: float, vertical: bool, **kw):
    if b - a < 0.4:
        return
    if vertical:
        c.line(fixed, a, fixed, b, **kw)
    else:
        c.line(a, fixed, b, fixed, **kw)


def _outside_own(pos: float, from_pos: float, out: int, horizontal: bool,
                 blockers) -> float:
    """Where a witness line anchored at a feature should actually begin.

    Just outside whatever body contains the anchor, on the side the chain is
    on, so the line leaves the part rather than starting inside it.
    """
    px, py = (pos, from_pos) if horizontal else (from_pos, pos)
    edge = from_pos
    for bx0, by0, bx1, by1 in blockers:
        if not (bx0 <= px <= bx1 and by0 <= py <= by1):
            continue
        lo, hi = (by0, by1) if horizontal else (bx0, bx1)
        near = hi if out > 0 else lo
        if (near - edge) * out > 0:
            edge = near
    return edge + out * style.EXT_GAP


def ordinate_chain(c: Canvas, values, base: float, line_pos: float, *,
                   horizontal: bool, colour: str = style.C_DIM,
                   size: float = style.T_DIM, text_gap: float = 2.0,
                   stagger: float | None = None, zero_label: str = "0",
                   zero_pos: float | None = None,
                   zero_from: float | None = None,
                   blockers=()) -> float:
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

    # Two labels closer along the chain than a label is tall would overprint,
    # so the second goes to the next lane out.  A lane is a label's WIDTH
    # further out on either kind of chain: on a horizontal chain the labels
    # are turned on their side and run outward by their width; on a vertical
    # chain they read normally and again run outward by their width.  The
    # horizontal case used the height, which put ButterStick's 18.09 and
    # 18.50 on top of each other.
    labels = [v[1] for v in values] + [zero_label]
    widest = max((style.text_width(t, size) for t in labels), default=0.0)
    tall = style.text_height(size) + style.descender(size)
    if stagger is None:
        stagger = widest + text_gap + 1.6
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

    # Two passes: every label's box is known before any witness line is
    # drawn, so a line to an outer lane can break where it passes a label in
    # an inner one.  Two holes a millimetre apart on ButterStick put their
    # labels in different lanes, as they should be, and the outer one's line
    # then ran straight through the inner one's value.
    plan = []
    for pos, label, from_pos, lane in placed:
        end = line_pos + out * lane * stagger
        # Start clear of the feature, on the side the dimension line is on, as
        # ISO 129-1 asks of an extension line.  Subtracting here instead put
        # the start on the far side, so the line ran back through the feature
        # it was meant to stop short of.
        #
        # An anchor inside a body -- a Pmod host's pin field, say -- starts
        # from that body's own edge.  Starting at the anchor put the first
        # millimetres of the line inside the body, where the break logic then
        # removed them, and the witness line for the Pmod hosts on the
        # Raspberry Pi sheets ended in blank space six millimetres short of
        # the pin field it was pointing at.
        start = _outside_own(pos, from_pos, out, horizontal, blockers)
        if (end - start) * out <= 0:
            start = end - out * style.EXT_OVER
        width = style.text_width(label, size)
        if horizontal:
            # Rotated by 90 degrees and centred, so what has to clear the end
            # of the witness line is half the label's WIDTH, not its height.
            ty = end + out * (text_gap + width / 2)
            box = (pos - tall / 2, min(ty - width / 2, ty + width / 2),
                   pos + tall / 2, max(ty - width / 2, ty + width / 2))
            reach = ty + out * width / 2
        else:
            tx = end + (text_gap if out > 0 else -text_gap)
            box = (min(tx, tx + out * width), pos - tall / 2,
                   max(tx, tx + out * width), pos + tall / 2)
            reach = tx + out * width
        plan.append((pos, label, start, end, box, reach))

    extent = line_pos
    for pos, label, start, end, box, reach in plan:
        others = list(blockers) + [b for _, _, _, _, b, _ in plan if b is not box]
        if horizontal:
            broken_line(c, pos, start, pos, end, others,
                        w=style.W_THIN, colour=colour)
            c.text(pos, (box[1] + box[3]) / 2, label, size=size, colour=colour,
                   anchor="middle", rotate=90)
        else:
            broken_line(c, start, pos, end, pos, others,
                        w=style.W_THIN, colour=colour)
            c.text(end + (text_gap if out > 0 else -text_gap), pos, label,
                   size=size, colour=colour,
                   anchor="start" if out > 0 else "end", baseline="middle")
        extent = max(extent, reach) if out > 0 else min(extent, reach)
    return extent
