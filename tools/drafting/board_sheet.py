"""Render a :class:`tools.schema.BoardSpec` as a 2D orthographic drawing sheet.

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

from tools.schema import BoardSpec, Feature, Hole

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
# Room the view wants around the part.  The bottom carries the Pmod spacing
# dimension, the ordinate chain and the overall dimension; the top carries
# balloons only.  Both were set generously and then measured: on the fullest
# sheet the deepest dimension still cleared the notes band by ten millimetres,
# which is space the notes need more than the view does.
VIEW_MARGIN_SIDE = 46.0
VIEW_MARGIN_TOP = 20.0
VIEW_MARGIN_BOTTOM = 30.0

#: How far the overall width and height dimensions sit off the board edge.
#: They are the only things on the top and right edges, so they can be close.
OVERALL_GAP = 9.0

BALLOON_R = 3.2
BALLOON_STEP = 8.4
BALLOON_OFFSET = 13.0


@dataclass
class _Ballooned:
    """A feature to balloon, and where its leader may touch it.

    ``tips`` holds the candidate anchor points in order of preference, the
    feature centre first.  A leader dot may sit anywhere on the feature it
    points at, and on a crowded board that freedom is what stops a leader
    having to cross a neighbour: on the Raspberry Pi 3 sheets the micro-USB
    power connector sits directly under the phantom Pmod host JC, so every
    leader anchored at its centre crossed the host's pin field.
    """

    label: str
    tip: tuple[float, float]
    tips: tuple[tuple[float, float], ...] = ()
    #: Index into ``Obstacles.rects`` of the rectangle this balloon's own
    #: feature contributes, if any.  A leader has to start on its feature, so
    #: scoring it against that feature charges every leader for something it
    #: cannot avoid, and the balloon ends up wedged into whatever gap is
    #: nearest.  Held as an index, not as the rectangle itself: two features
    #: with the same bounding box would otherwise both be exempted.
    own: int | None = None

    def anchors(self) -> tuple[tuple[float, float], ...]:
        return self.tips or (self.tip,)


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


def is_fitted(f: Feature) -> bool:
    """Whether this position carries a part on this board revision.

    One definition.  The envelope note counted the unfitted side Pmod
    positions and overstated the demo boards' assembled envelope by the eight
    millimetres those connectors would have stuck out had they been there.
    """
    return "not fitted" not in f.label.lower()


def draw_feature(c: Canvas, view: View, f: Feature) -> None:
    x0, y0 = view.pt(f.x0, f.y0)
    x1, y1 = view.pt(f.x1, f.y1)
    fitted = is_fitted(f)
    colour = style.C_HIGHLIGHT if fitted else style.C_PHANTOM
    c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
           weight=style.W_COMPONENT, colour=colour,
           fill=style.C_FILL_LIGHT if fitted else "none",
           # Type K, not the dashed hidden-detail type: these positions are
           # not hidden behind material, they are alternative positions that
           # this revision does not populate.
           dash=None if fitted else style.D_PHANTOM)
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


#: How much worse it is to touch one kind of obstacle than another.  A
#: component outline is a soft obstacle: a leader crossing one is untidy but a
#: reader still follows it.  Another balloon, its text or its leader is a hard
#: one: two of those on top of each other cannot be read at all.
SOFT = 1.0
HARD = 6.0


class Obstacles:
    """Everything a balloon must not land on, each with a weight."""

    def __init__(self) -> None:
        self.rects: list[tuple[float, float, float, float, float]] = []
        self.circles: list[tuple[float, float, float, float]] = []
        self.segments: list[tuple[float, float, float, float, float]] = []

    def add_rect(self, x0, y0, x1, y1, pad: float = 0.0,
                 weight: float = SOFT) -> None:
        self.rects.append((min(x0, x1) - pad, min(y0, y1) - pad,
                           max(x0, x1) + pad, max(y0, y1) + pad, weight))

    def add_circle(self, cx, cy, r, weight: float = SOFT) -> None:
        self.circles.append((cx, cy, r, weight))

    def add_segment(self, x1, y1, x2, y2, weight: float = SOFT) -> None:
        self.segments.append((x1, y1, x2, y2, weight))

    def crossings(self, x1: float, y1: float, x2: float, y2: float) -> int:
        """How many recorded segments a proposed leader actually crosses.

        Sampling a leader against obstacles misses a clean crossing: two lines
        can intersect at a point that falls between samples.  A proper segment
        intersection test catches it, which is what stops two balloons swapping
        sides and crossing each other's leaders.
        """
        def side(ax, ay, bx, by, px, py):
            return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

        n = 0.0
        for ax, ay, bx, by, w in self.segments:
            d1 = side(x1, y1, x2, y2, ax, ay)
            d2 = side(x1, y1, x2, y2, bx, by)
            d3 = side(ax, ay, bx, by, x1, y1)
            d4 = side(ax, ay, bx, by, x2, y2)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                n += w
        return n

    def leader_hits(self, x1: float, y1: float, x2: float, y2: float,
                    clearance: float = 1.0, samples: int = 14) -> float:
        """How much of a leader from (x1,y1) to (x2,y2) runs over something.

        Scoring only the balloon's own position lets its leader be routed
        straight through the feature next door, which is what put balloon 4 on
        the TT04 sheet across two neighbouring LEDs.  Each sample counts the
        heaviest thing under it, so a leader crossing a balloon costs more than
        one crossing a connector outline.
        """
        n = 0.0
        for i in range(1, samples):
            t = i / samples
            n += self.hits(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t,
                           clearance, worst=True)
        return n

    def rect_hits(self, x0: float, y0: float, x1: float, y1: float) -> float:
        """Weight of the obstacles a rectangle overlaps.

        A label is a wide, short box, and testing it as a disc of half its
        width either misses a neighbour above it or invents one beside it.
        The mounting plate's USB-C marks were placed by the disc test and
        still landed on a hole label and on the corner radius callout.
        """
        n = 0.0
        for ax0, ay0, ax1, ay1, w in self.rects:
            if x1 > ax0 and x0 < ax1 and y1 > ay0 and y0 < ay1:
                n += w
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rr = math.hypot(x1 - x0, y1 - y0) / 2
        for ox, oy, orr, w in self.circles:
            if math.hypot(cx - ox, cy - oy) < rr + orr:
                n += w
        for ax0, ay0, ax1, ay1, w in self.segments:
            if _segment_hits_rect(ax0, ay0, ax1, ay1, x0, y0, x1, y1):
                n += w
        return n

    def hits(self, cx: float, cy: float, r: float,
             worst: bool = False) -> float:
        """Weight of the obstacles a disc of radius *r* at (cx,cy) touches.

        With *worst*, the heaviest single obstacle rather than their sum, which
        is what a point sample along a leader wants: overlapping outlines are
        one obstruction, not three.
        """
        n = 0.0
        for x0, y0, x1, y1, w in self.rects:
            if cx + r > x0 and cx - r < x1 and cy + r > y0 and cy - r < y1:
                n = max(n, w) if worst else n + w
        for ox, oy, orr, w in self.circles:
            if math.hypot(cx - ox, cy - oy) < r + orr:
                n = max(n, w) if worst else n + w
        for x1, y1, x2, y2, w in self.segments:
            if _point_segment_distance(cx, cy, x1, y1, x2, y2) < r:
                n = max(n, w) if worst else n + w
        return n


def _segment_hits_rect(ax, ay, bx, by, x0, y0, x1, y1) -> bool:
    """Whether a segment touches an axis-aligned rectangle."""
    if max(ax, bx) < x0 or min(ax, bx) > x1:
        return False
    if max(ay, by) < y0 or min(ay, by) > y1:
        return False
    if x0 <= ax <= x1 and y0 <= ay <= y1:
        return True
    if x0 <= bx <= x1 and y0 <= by <= y1:
        return True
    # Both ends outside: the segment crosses if the corners fall on both sides.
    def side(px, py):
        return (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    signs = [side(x, y) > 0
             for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return any(signs) and not all(signs)


def _point_segment_distance(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


#: Candidate balloon offsets, tried in order: close and to the side first,
#: then further out.  Angles start at "up and right" and go round.
_ANGLES = [i * 15 for i in range(24)]
# A small board with several connectors and a phantom HAT over it has no room
# left inside its own outline: on the Raspberry Pi 3A+ every position within
# 34 mm of a feature landed on something.  The longer radii let a balloon step
# off the view into the clear margin, which is where a drawing would put it
# anyway.  The search stops at the first radius that yields a clean spot, so
# the extra reach costs nothing on an uncrowded sheet.
_RADII = [9.0, 12.5, 16.5, 21.0, 27.0, 34.0, 42.0, 52.0, 64.0]

#: A leader that clears everything scores only its own length, so anything
#: above the longest clean leader means it is running over something.
CLEAN_SCORE = _RADII[-1] * 2.0 + 1.0

#: What an off-centre leader dot has to save before it is worth taking.
TIP_PENALTY = 45.0


def _ordinate_values(spec: BoardSpec, overlay: BoardSpec | None
                     ) -> tuple[dict[float, float], dict[float, float]]:
    """The X and Y ordinate values, each with the feature it comes from.

    Each entry carries the feature's other-axis coordinate too, so its witness
    line can start at the feature rather than at a board edge.  This is worked
    out before anything is drawn, because the witness lines are obstacles the
    balloons have to keep off and the balloons go on the sheet first.

    A host on a horizontal edge is located along that edge by its X, one on a
    vertical edge by its Y: that is the coordinate a mating peripheral cares
    about, and a host goes into that chain only.  Putting its depth into the
    other chain landed a value within a third of a millimetre of a mounting
    hole's, so the two witness lines printed as one and neither label could be
    tied to a line.  The depth gets its own dimension instead.
    """
    xvals: dict[float, float] = {}
    yvals: dict[float, float] = {}

    def note_x(x, y):
        key = round(x, 3)
        xvals[key] = (max(xvals.get(key, y), y) if spec.front_edge == "top"
                      else min(xvals.get(key, y), y))

    def note_y(y, x):
        key = round(y, 3)
        yvals[key] = min(yvals.get(key, x), x)

    for h in spec.holes:
        note_x(h.x, h.y)
        note_y(h.y, h.x)
    for p in list(spec.pmods) + list(overlay.pmods if overlay else ()):
        if p.edge in ("bottom", "top"):
            note_x(p.cx, p.cy)
        else:
            note_y(p.cy, p.cx)
    return xvals, yvals


def _feature_anchors(view: View, f) -> tuple[tuple[float, float], ...]:
    """Where a leader may touch feature *f*, best first.

    The centre first, then the four edge midpoints, then the four quadrant
    centres, all a quarter of the feature's width and height from the centre.
    Everything stays well inside the outline, so the dot always reads as
    belonging to this feature and not to whatever is next to it.
    """
    qx, qy = f.width / 4.0, f.height / 4.0
    return tuple(view.pt(f.cx + dx, f.cy + dy) for dx, dy in
                 ((0.0, 0.0), (-qx, 0.0), (qx, 0.0), (0.0, -qy), (0.0, qy),
                  (-qx, -qy), (qx, -qy), (-qx, qy), (qx, qy)))


def place_balloons(items: list[_Ballooned], obstacles: Obstacles,
                   bounds: Rect, c: Canvas, passes: int = 12,
                   position_only: Obstacles | None = None) -> None:
    """Put each balloon near its feature, clear of everything else.

    A single greedy sweep is very order-sensitive: whichever balloon is placed
    first takes the best spot and the last one is left with whatever remains,
    which is how two balloons ended up touching and a leader ended up clipping
    a third.  So the greedy pass is followed by relaxation sweeps that re-place
    each balloon in turn against the others' final positions.  It converges in
    a couple of passes on drawings this size.
    """
    placed: list[tuple[float, float] | None] = [None] * len(items)
    anchor: list[tuple[float, float]] = [it.tip for it in items]

    def scene(skip: int, route: bool = False) -> Obstacles:
        """The obstacle set for one balloon.

        With *route*, the set a leader is scored against rather than the one
        the balloon itself is scored against.  The two differ in what a line
        may cross but a disc may not sit on: the board outline, which a leader
        crosses as a matter of course, and the balloon's own feature, where
        every leader has to start.
        """
        o = Obstacles()
        own = items[skip].own
        o.rects = []
        for i, r in enumerate(obstacles.rects):
            if i != own:
                o.rects.append(r)
            elif not route:
                # Hard for the balloon, absent for its leader.  A balloon on
                # top of the very feature it labels hides what the reader
                # followed the leader to see, which is worse than landing on a
                # neighbour, and it happened on the Pi 3A+ where the board is
                # small and every other position was taken.
                o.rects.append(r[:4] + (HARD,))
        o.circles = list(obstacles.circles)
        o.segments = list(obstacles.segments)
        if not route and position_only is not None:
            o.rects += position_only.rects
            o.circles += position_only.circles
            o.segments += position_only.segments
        for k, pos in enumerate(placed):
            if pos is None or k == skip:
                continue
            o.add_circle(pos[0], pos[1], BALLOON_R + 2.0, weight=HARD)
            o.add_segment(anchor[k][0], anchor[k][1], pos[0], pos[1],
                          weight=HARD)
        return o

    def best_for_tip(world: Obstacles, route: Obstacles,
                     tip: tuple[float, float]):
        """Cheapest balloon position for a leader anchored at *tip*.

        *world* scores where the balloon may sit and *route* what its leader
        may cross.  They differ by one rectangle: the balloon's own feature.
        The balloon must still keep off it, or it hides what it labels, but
        the leader has to start there, so charging the leader for it prices in
        something no placement can avoid.
        """
        tx, ty = tip
        best, best_score = None, None
        for radius in _RADII:
            for ang in _ANGLES:
                a = math.radians(ang)
                cx = tx + radius * math.cos(a)
                cy = ty + radius * math.sin(a)
                if not (bounds.x + BALLOON_R < cx < bounds.x1 - BALLOON_R
                        and bounds.y + BALLOON_R < cy < bounds.y1 - BALLOON_R):
                    continue
                # Landing on something is worst by a wide margin: a balloon
                # covers what it is meant to point at, while a leader merely
                # runs across it.  Priced any closer together, a balloon parks
                # on its own connector rather than stepping out to the clear
                # margin, which is where a drawing would put it.  Leader
                # length is a real cost too, or a balloon travels halfway
                # across the view to dodge a crossing it could have avoided by
                # moving a few millimetres.
                score = (world.hits(cx, cy, BALLOON_R + 2.0) * 200
                         + route.crossings(tx, ty, cx, cy) * 60
                         + route.leader_hits(tx, ty, cx, cy) * 30
                         + radius * 2.0)
                if best_score is None or score < best_score:
                    best, best_score = (cx, cy), score
            if best_score is not None and best_score < radius * 2.0 + 1:
                break
        return best, best_score

    def best_spot(index: int) -> tuple[tuple[float, float], tuple[float, float]]:
        item = items[index]
        world = scene(index)
        route = scene(index, route=True)
        tips = item.anchors()
        pos, score = best_for_tip(world, route, tips[0])
        tip = tips[0]
        # Moving the dot off the centre of a feature is legitimate but it is
        # not free: an off-centre dot is slightly harder to associate with its
        # feature, so it has to buy a real improvement, and the whole search is
        # skipped when the centre already gives a clean leader.
        if score is not None and score > CLEAN_SCORE:
            for alt in tips[1:]:
                apos, ascore = best_for_tip(world, route, alt)
                if apos is None:
                    continue
                if score is None or ascore + TIP_PENALTY < score:
                    pos, score, tip = apos, ascore + TIP_PENALTY, alt
        return tip, pos or (tip[0] + 10.0, tip[1] + 10.0)

    for i in range(len(items)):
        anchor[i], placed[i] = best_spot(i)
    # Coordinate descent: each sweep re-places every balloon against the
    # others' current positions.  The sweep direction alternates, because a
    # one-way sweep always lets the last balloon win and can leave the first
    # one's leader lying under a balloon that moved after it was placed.  It
    # stops as soon as a sweep changes nothing, which is the fixed point.
    order = list(range(len(items)))
    for n in range(passes):
        moved = False
        for i in (order if n % 2 == 0 else order[::-1]):
            was = (anchor[i], placed[i])
            anchor[i], placed[i] = best_spot(i)
            if (anchor[i], placed[i]) != was:
                moved = True
        if not moved:
            break

    for item, tip, pos in zip(items, anchor, placed):
        dims.balloon(c, tip, pos, item.label, radius=BALLOON_R)


def _radius_callout(o, board: Rect, sheet: Sheet, view: View
                    ) -> tuple[str, float, float, float]:
    """The corner radius callout: its text, its elbow, and the text's span.

    One definition, because the balloon placer reserves the callout's space
    before it is drawn and the two have to agree.  Reserving one span and
    drawing another put a balloon straight on the callout: the elbow is held
    back so the text ends inside the drawing area, and on the widest boards
    that pulls it left of the corner it points at, which makes the leader tail
    -- and the text with it -- run the other way.  That is fine, the space
    above the board is empty; guessing the direction was not.
    """
    label = f"R{o.corner_radius:.2f} (4 places), board outline"
    tw = style.text_width(label, style.T_LABEL)
    tip_x = view.x(o.width - o.corner_radius * 0.3)
    elbow = min(board.x1 + 8.0, sheet.area.x1 - 6.2 - tw)
    # Mirrors dims.leader: the tail runs away from the tip, and the text runs
    # on from the end of the tail.
    if elbow >= tip_x:
        end = elbow + dims.LEADER_TAIL
        return label, elbow, end + 1.2, end + 1.2 + tw
    end = elbow - dims.LEADER_TAIL
    return label, elbow, end - 1.2 - tw, end - 1.2


def _view_height_needed(spec: BoardSpec, overlay: BoardSpec | None,
                        view_bbox=None) -> float:
    """Vertical room the view and its dimensions want, in sheet millimetres."""
    if view_bbox is not None:
        return view_bbox[3] - view_bbox[1] + VIEW_MARGIN_TOP + VIEW_MARGIN_BOTTOM
    ys = [0.0, spec.outline.height]
    for f in spec.features:
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_y1 > p.body_y0:
            ys += [p.body_y0, p.body_y1]
    if overlay is not None:
        ys += [0.0, overlay.outline.height]
    return (max(ys) - min(ys)) + VIEW_MARGIN_TOP + VIEW_MARGIN_BOTTOM


def planned_band_height(spec: BoardSpec, *, sheet_size: str = "A3",
                        extra_notes: tuple[str, ...] = (),
                        overlay: BoardSpec | None = None,
                        view_bbox=None) -> float:
    """The notes band height render_board would choose for *spec*.

    Exposed so a caller drawing a family can give every sheet the same band.
    The band's height decides how much of the sheet is left for the view, so
    sheets with different bands centre their views at different heights --
    which defeats a shared view frame, whose whole purpose is that a feature
    lands in the same place on every page.
    """
    notes, src_lines = _sheet_text(spec, overlay, extra_notes)
    return Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src_lines),
        max_height=style.SHEET_SIZES[sheet_size][1] - 2 * style.FRAME_MARGIN
        - _view_height_needed(spec, overlay, view_bbox) - 6.0)[0]


#: Finished PCB thicknesses a fabricator actually offers.  A KiCad board file
#: does not carry a specified thickness; what it carries is the sum of the
#: stackup, which lands a few hundredths off the nominal once copper, prepreg
#: and solder mask are counted.
STANDARD_PCB_THICKNESS = (0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.4)


#: How far a stackup sum may sit from a standard thickness and still be taken
#: as that thickness.  The demo boards are all within 0.04 mm of 1.6.
NOMINAL_THICKNESS_TOL = 0.05


def _nominal_thickness(o) -> float | None:
    """The finished thickness a board's stackup sum corresponds to, if any.

    One definition, because the MATERIAL field and the note that explains it
    both need the answer and must not disagree about it.
    """
    if not o.thickness:
        return None
    nominal = min(STANDARD_PCB_THICKNESS, key=lambda t: abs(t - o.thickness))
    return nominal if abs(nominal - o.thickness) <= NOMINAL_THICKNESS_TOL \
        else None


def _pcb_material(o) -> str:
    """The MATERIAL field for a bare board.

    Printing the stackup sum to two decimals made 1.56252 and 1.561 both read
    as "1.56 thick", and made the one board whose file happens to say 1.6 look
    like a thicker board than the rest.  They are all nominal 1.6 mm.
    """
    if not o.thickness:
        return "PCB, thickness not stated"
    nominal = _nominal_thickness(o)
    if nominal is not None:
        return f"PCB, {nominal:.1f} nominal"
    return f"PCB, {o.thickness:.3f} stackup sum"


#: How tall one legend row is, and how long its line sample is.
# 4.8 for 2.5 mm capitals: 2.3 mm of leading, which is comfortable for a
# list of one-line entries and gives the notes back a few millimetres of
# column on the fullest sheets.
LEGEND_ROW = 4.6
# Long enough to show a full period of the longest dash pattern: at 14 mm the
# chain-dot and the chain-double-dot samples were indistinguishable, which
# defeats the point of a legend.
LEGEND_SWATCH = 20.0

#: Every line style these sheets use, keyed by the name a legend entry gives.
#: Drawn from the same constants the views are drawn from, so a legend cannot
#: describe a style the sheet no longer uses.
#: shape, weight, colour, dash.  "hole" entries exist because on the mounting
#: plate sheets the only thing separating a board fastener from a plate fixing
#: is the colour of its circle, and these sheets are meant to be printed.
LEGEND_STYLES = {
    "outline": ("line", style.W_OUTLINE, style.C_LINE, None),
    "component": ("line", style.W_COMPONENT, style.C_HIGHLIGHT, None),
    "dnp": ("line", style.W_COMPONENT, style.C_PHANTOM, style.D_PHANTOM),
    "phantom": ("line", style.W_PHANTOM, style.C_PHANTOM, style.D_PHANTOM),
    "centre": ("line", style.W_CENTRE, style.C_LINE, style.D_CENTRE),
    "dimension": ("arrow", style.W_THIN, style.C_DIM, None),
    "usbc": ("line", style.W_PHANTOM, "#7a4a00", style.D_PHANTOM),
}


def legend_height(rows: int) -> float:
    return Sheet.HEADING_HEIGHT + rows * LEGEND_ROW + 0.5


def draw_legend(sheet: Sheet, entries: list[tuple[str, str]]) -> None:
    """A key to the line styles, in the annotation column.

    Without one, the only thing telling a reader that a grey chain-double-dot
    rectangle is an adjacent part and a red one is a component is the colour,
    and these sheets are meant to be printed.
    """
    if not entries:
        return
    rect = sheet.column_block(legend_height(len(entries)))
    c = sheet.canvas
    y = sheet.heading(rect, "LEGEND")
    for kind, label in entries:
        if kind.startswith("#"):
            shape, w, colour, dash = "hole", style.W_OUTLINE, kind, None
        else:
            shape, w, colour, dash = LEGEND_STYLES[kind]
        cy = y - LEGEND_ROW / 2
        if shape == "hole":
            mid = rect.x + LEGEND_SWATCH / 2
            c.circle(mid, cy, 1.7, w=w, colour=colour, fill="#ffffff")
            dims.centre_mark(c, mid, cy, 1.7, colour=colour, over=1.2)
        else:
            c.line(rect.x, cy, rect.x + LEGEND_SWATCH, cy, w=w, colour=colour,
                   dash=dash)
            if shape == "arrow":
                c.arrow(rect.x + LEGEND_SWATCH, cy, 0, colour=colour)
        c.text(rect.x + LEGEND_SWATCH + 3.0, cy - style.T_NOTE / 2, label,
               size=style.T_NOTE)
        y -= LEGEND_ROW


def _legend_entries(spec: BoardSpec, overlay: BoardSpec | None
                    ) -> list[tuple[str, str]]:
    """Only the styles this particular sheet actually uses."""
    entries = [("outline", "Board outline")]
    if spec.features:
        entries.append(("component", "Component body, scheduled"))
    if any(not is_fitted(f) for f in spec.features):
        entries.append(("dnp", "Position not fitted on this revision"))
    phantom = ["Pmod connector body" if spec.pmods else ""]
    if overlay is not None:
        phantom.append("adjacent part")
    if any(h.keepout_dia for h in spec.holes):
        phantom.append("hole keep-out")
    phantom = [t for t in phantom if t]
    if phantom:
        entries.append(("phantom", ", ".join(phantom).capitalize()))
    entries.append(("dimension", "Dimension, extension and leader"))
    return entries


def _sheet_text(spec: BoardSpec, overlay: BoardSpec | None,
                extra_notes: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """The notes and sources this sheet will carry."""
    o = spec.outline
    notes = [
        "All dimensions in millimetres. The datum symbol marks the origin: "
        "the board's lower-left corner, X right, Y up, seen from the "
        "component side.",
    ]
    if overlay is not None:
        notes.append(
            f"Phantom outline is the {overlay.title} on the 40-pin GPIO "
            "header, drawn in this board's frame: its mounting holes coincide "
            "with this board's.")
    notes += list(spec.notes) + list(extra_notes)
    if overlay is not None:
        notes.append(
            "Those host positions are DERIVED, not published: Digilent issue "
            "no mechanical drawing for the adapter. Good to about +/-0.75 mm. "
            "JA and JB face out of the left edge, JC out of the lower edge. "
            "The Pmod HAT Adapter sheet has the derivation.")
    if spec.pmods:
        notes.append(
            "The chain-double-dot rectangle at each Pmod host is the "
            "connector body where it overhangs the edge: what a peripheral "
            "and a bracket must clear.")
    if spec.pmods or (overlay is not None and overlay.pmods):
        notes.append(
            "Pmod host coordinates are given to three decimals, unlike the "
            "rest of this sheet. Rounded to two, adjacent hosts print 22.85 "
            "apart and contradict the 22.86 pitch dimensioned here.")
        notes.append(
            "Port names differ by family: JA, JB, JC on the adapter and "
            "Raspberry Pi sheets, by signal direction on the demo boards, "
            "PMOD 1 to 3 on the plate sheets. TT-MP-02 maps them.")
    if o.thickness:
        nominal = _nominal_thickness(o)
        if nominal is not None:
            notes.append(
                f"Board thickness is {nominal:.1f} mm nominal. The KiCad "
                f"file's {o.thickness:.5f} mm is its stackup sum, not a "
                "specified finished thickness.")
        else:
            # The title block prints the raw stackup figure in this case, so
            # the note has to say what that figure is, or the sheet asserts an
            # unexplained number.
            notes.append(
                f"MATERIAL gives {o.thickness:.3f} mm, the sum of the KiCad "
                "stackup layers. It is not a specified finished thickness, "
                "and it is not within a twentieth of a millimetre of any "
                "standard one, so no nominal is claimed for it.")
    fitted = [f for f in spec.features if is_fitted(f)]
    if fitted:
        # What a chassis actually has to clear, which is not the board
        # outline: on the Pi 4B the connectors reach 88 mm across an 85 mm
        # board, and the demo boards' USB-C shells overhang too.  Positions
        # that are not fitted are left out, or the figure describes a board
        # that was never built.
        x0 = min([0.0] + [f.x0 for f in fitted])
        x1 = max([o.width] + [f.x1 for f in fitted])
        y0 = min([0.0] + [f.y0 for f in fitted])
        y1 = max([o.height] + [f.y1 for f in fitted])
        if (x0, y0, x1, y1) != (0.0, 0.0, o.width, o.height):
            notes.append(
                f"Assembled envelope, connector overhang included, is "
                f"{x1 - x0:.2f} x {y1 - y0:.2f} mm against a "
                f"{o.width:.2f} x {o.height:.2f} mm board outline. The "
                "FEATURE SCHEDULE gives the extents.")
    if o.profile_note:
        notes.append(o.profile_note)
    if any(f.number for f in spec.features):
        notes.append(
            "Feature numbers are fixed across this family, so a number "
            "means the same part on every sheet. A part this board does not "
            "carry still has a row, marked as such.")
    if not spec.tolerance:
        # Say where the general tolerance comes from.  It is a board house's
        # usual figures, not something any source here states, and on sheets
        # whose whole discipline is that every number is traceable an
        # untraceable one in the title block is the odd thing out.
        schedule = " A tolerance quoted in the hole schedule is from the " \
            "source drawing and governs." if any(h.tol for h in spec.holes) \
            else ""
        notes.append(
            "GENERAL TOLERANCE in the title block is a normal board-house "
            "figure, not one any source here states." + schedule)
    # Says what DRAWN "generated" means and that nobody countersigned it.
    # ISO 7200 expects an approver; there isn't one, and a sheet that leaves
    # the field off without saying so implies there was.
    notes.append(
        "Generated from the listed sources and not checked by a second "
        "party: there is no CHECKED field because nobody has signed it.")
    sources = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
               for s in spec.sources]
    return notes, sources


def note_blocks(notes: list[str], sources: list[str]):
    blocks = [("NOTES", notes, style.T_NOTE)]
    if sources:
        blocks.append(("SOURCES", sources, style.T_TINY))
    return blocks


def notes_spill_needed(sheet: Sheet, notes: list[str], sources: list[str],
                       columns: int = 2) -> float:
    """How much of the annotation column the notes' tail needs, or 0.

    Worked out before anything is placed in the column, so the legend can be
    given the top of it and the notes the bottom.
    """
    blocks = note_blocks(notes, sources)
    cols = sheet.band_columns(sheet.notes_band, count=columns)
    if sheet.notes_columns(cols, blocks, dry=True):
        return 0.0
    spare = sheet.column_remaining
    h = 20.0
    # Two millimetre steps, not four: the search returns the first height that
    # works, so the step size is wasted space, and on the Pi 3B sheet that
    # waste was the difference between fitting and not.
    while h <= spare:
        probe = Rect(sheet.column.x, sheet.column.y,
                     sheet.column.w - sheet.COLUMN_GUTTER, h)
        if sheet.notes_columns(cols + [probe], blocks, dry=True):
            return h
        h += 2.0
    return spare


def _place_notes_and_sources(sheet: Sheet, notes: list[str],
                             sources: list[str], columns: int = 2,
                             spill: float | None = None) -> None:
    """Draw the notes and sources in the band across the bottom of the sheet.

    The band comes first and is used in full.  Only when it cannot hold
    everything does the tail spill into the annotation column, and then into
    the BOTTOM of it, level with the lower half of the band, so the sheet
    reads left to right along its foot.  Higher up, between the tables and the
    legend, "SOURCES (continued)" printed ninety millimetres above the
    "SOURCES" heading it continued.
    """
    blocks = note_blocks(notes, sources)
    cols = sheet.band_columns(sheet.notes_band, count=columns)
    if spill is None:
        spill = notes_spill_needed(sheet, notes, sources, columns)
    if spill > 0:
        cols = cols + [sheet.column_block_bottom(spill)]
    sheet.notes_columns(cols, blocks)


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


def _pin_row_centre_line(c: Canvas, view: View, group, edge: str,
                         lane: float) -> None:
    """Centre line through a row of Pmod pin fields, on the row's own axis.

    Extended past the outermost host far enough to reach *lane*, which is
    where the setback dimension's extension line meets it, plus the usual
    centre-line overshoot.
    """
    along_edge = edge in ("bottom", "top")
    axis = view.y(group[0].cy) if along_edge else view.x(group[0].cx)
    ends = []
    for p in group:
        half = p.pin_span / 2 + 1.3
        centre = p.cx if along_edge else p.cy
        ends += [centre - half, centre + half]
    lo = view.x(min(ends)) if along_edge else view.y(min(ends))
    hi = view.x(max(ends)) if along_edge else view.y(max(ends))
    lo, hi = min(lo, hi), max(lo, hi)
    lo, hi = min(lo, lane) - 4.0, max(hi, lane) + 4.0
    if along_edge:
        c.line(lo, axis, hi, axis, w=style.W_CENTRE, colour=style.C_HIGHLIGHT,
               dash=style.D_CENTRE)
    else:
        c.line(axis, lo, axis, hi, w=style.W_CENTRE, colour=style.C_HIGHLIGHT,
               dash=style.D_CENTRE)


def _clear_lane(view: View, host, edge: str, board: Rect,
                blockers: list[tuple[float, float, float, float]]) -> float:
    """Where to run the pin-field depth dimension for *host*, in sheet mm.

    A lane parallel to the host's own edge, alongside the host, on which
    nothing is drawn.  Candidates step outwards from the end of the pin field
    in both directions, nearest first, so the dimension normally lands just
    beyond the host and only moves further when something is in the way.
    Falls back to the nearest candidate if every lane is blocked, which is
    better than silently dropping the dimension.
    """
    along_edge = edge in ("bottom", "top")
    centre = host.cx if along_edge else host.cy
    half = host.pin_span / 2

    def blocked(pos: float) -> bool:
        lo, hi = (board.y, board.y1) if along_edge else (board.x, board.x1)
        for x0, y0, x1, y1 in blockers:
            a, b = (x0, x1) if along_edge else (y0, y1)
            other0, other1 = (y0, y1) if along_edge else (x0, x1)
            if a - 2.6 < pos < b + 2.6 and other1 > lo and other0 < hi:
                return True
        return False

    first = None
    for step in range(0, 16):
        for direction in (1, -1):
            model = centre + direction * (half + 4.0 + step * 1.5)
            pos = view.x(model) if along_edge else view.y(model)
            inside = (board.x + 2.0 < pos < board.x1 - 2.0 if along_edge
                      else board.y + 2.0 < pos < board.y1 - 2.0)
            if not inside:
                continue
            if first is None:
                first = pos
            if not blocked(pos):
                return pos
    return first if first is not None else (
        view.x(centre + half + 4.0) if along_edge else
        view.y(centre + half + 4.0))


def render_board(spec: BoardSpec, *, drawing_no: str, version: str,
                 sheet_size: str = "A3", extra_notes: tuple[str, ...] = (),
                 force_scale: float | None = None,
                 overlay: BoardSpec | None = None,
                 view_bbox: tuple[float, float, float, float] | None = None,
                 band_height: float | None = None,
                 family_numbers: dict[int, str] | None = None) -> Sheet:
    """Build a complete drawing sheet for *spec* and return it.

    *view_bbox* overrides the area the view is fitted to, in this board's own
    coordinates.  A caller drawing a family of boards passes each one the same
    region of a shared frame, so a chosen feature lands in the same place on
    every sheet and the set can be flipped through without it moving.
    """
    o = spec.outline

    # The notes are known before anything is drawn, and their height decides
    # how much of the sheet is left for the view, so they are built first and
    # the band is sized to them.
    notes, src_lines = _sheet_text(spec, overlay, extra_notes)
    view_needs = _view_height_needed(spec, overlay, view_bbox)
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src_lines),
        max_height=style.SHEET_SIZES[sheet_size][1] - 2 * style.FRAME_MARGIN
        - view_needs - 6.0)
    if band_height is not None:
        # A caller giving the whole family one band so their views line up.
        # Only ever taller than this sheet needs: a shorter one would reflow
        # the notes into a space that has already been proven too small.
        band_h = max(band_h, band_height)

    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(),
        subtitle=spec.subtitle,
        drawing_no=drawing_no,
        rev="A",
        version=version,
        drawn_by="generated",
        units="mm",
        # Board thickness matters: standoff and screw length depend on it.
        material=_pcb_material(o),
        # A sheet whose hole schedule quotes the source's own diameter
        # tolerance must not also assert a different one here: the Pi 3B's
        # schedule says +/-0.05 and the block said +/-0.08, with nothing but a
        # note to say which wins.
        **({"tolerance": spec.tolerance} if spec.tolerance
           else {"tolerance": "edge +/-0.20   hole pos +/-0.10   "
                              "hole dia per schedule"}
           if any(h.tol for h in spec.holes) else {}),
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
    if view_bbox is not None:
        # The caller's frame has to cover this board as well, or the board
        # would be drawn outside its own view: a caller that gets the union
        # wrong should be told, not quietly cropped.
        if (view_bbox[0] > bbox[0] or view_bbox[1] > bbox[1]
                or view_bbox[2] < bbox[2] or view_bbox[3] < bbox[3]):
            raise SystemExit(
                f"{spec.key}: the common view frame "
                f"({view_bbox[0]:.2f}, {view_bbox[1]:.2f}) to "
                f"({view_bbox[2]:.2f}, {view_bbox[3]:.2f}) does not cover the "
                f"board's own ({bbox[0]:.2f}, {bbox[1]:.2f}) to "
                f"({bbox[2]:.2f}, {bbox[3]:.2f})")
        bbox = view_bbox

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

    # How far the dimensions will reach below and to the left, worked out
    # before anything is placed.  A Pmod spacing dimension goes in first, then
    # the ordinate chain nine millimetres below that.
    horiz_edges = len({p.edge for p in spec.pmods if p.edge in ("bottom", "top")
                       and len([q for q in spec.pmods if q.edge == p.edge]) > 1})
    vert_edges = len({p.edge for p in spec.pmods if p.edge in ("left", "right")
                      and len([q for q in spec.pmods if q.edge == p.edge]) > 1})
    step = 6.0 + style.T_DIM + 2.0
    chain_y = dim_bottom - horiz_edges * step - 9.0
    chain_x = dim_left - vert_edges * step - 9.0

    # Balloons may use the strip between the view and the ordinate chain.
    # The witness lines crossing it are already reserved as obstacles, and on
    # a board like the Raspberry Pi 5, whose micro-HDMI connectors sit under
    # the Pmod HAT's host JC, that strip is the only clear space a leader from
    # those connectors can reach without being ruled across the host.
    balloon_bounds = Rect(chain_x + 4.0, chain_y + 4.0,
                          sheet.area.x1 - chain_x - 4.0,
                          sheet.area.y1 - chain_y - 4.0)

    obstacles = Obstacles()
    feature_rect: dict[int, int] = {}
    for i, f in enumerate(spec.features):
        obstacles.add_rect(*view.pt(f.x0, f.y0), *view.pt(f.x1, f.y1), pad=0.8)
        feature_rect[i] = len(obstacles.rects) - 1
    # The radius callout is drawn after the balloons but occupies its space
    # regardless, so reserve it now, at exactly the place it will be drawn.
    if o.corner_radius:
        _, relbow, rx0, rx1 = _radius_callout(o, board, sheet, view)
        # Hard: a balloon on the callout hides a dimension, and there is
        # always somewhere else for a balloon to go.
        obstacles.add_rect(min(relbow, rx0), board.y1 + 2.0,
                           max(relbow, rx1), board.y1 + 9.0,
                           pad=1.2, weight=HARD)
        obstacles.add_segment(*view.pt(o.width - o.corner_radius * 0.3,
                                       o.height - o.corner_radius * 0.3),
                              relbow, board.y1 + 5.0, weight=HARD)

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
            # Hard: the phantom host is the whole reason this overlay is on
            # the sheet, and a leader ruled across its pin field hides the one
            # thing the reader came for.
            obstacles.add_rect(*view.pt(p.cx - half_x, p.cy - half_y),
                               *view.pt(p.cx + half_x, p.cy + half_y), pad=1.0,
                               weight=HARD)
            # The label's own box, sized to the text.  Reserving the pin
            # field's full height for a two-letter label walled off the
            # diagonal every leader from the lower-left corner wanted to take,
            # and pushed those leaders across the pin fields instead.
            lw = style.text_width(p.label, style.T_LABEL, bold=True)
            lh = style.T_LABEL
            lx0, ly0 = view.pt(p.cx - half_x, p.cy - half_y)
            lx1, ly1 = view.pt(p.cx + half_x, p.cy + half_y)
            mx, my = (lx0 + lx1) / 2, (ly0 + ly1) / 2
            if p.edge == "left":
                obstacles.add_rect(lx1, my - lh / 2, lx1 + lw + 3.0,
                                   my + lh / 2, pad=1.0, weight=HARD)
            elif p.edge == "right":
                obstacles.add_rect(lx0 - lw - 3.0, my - lh / 2, lx0,
                                   my + lh / 2, pad=1.0, weight=HARD)
            else:
                obstacles.add_rect(mx - lw / 2, ly1, mx + lw / 2,
                                   ly1 + lh + 3.0, pad=1.0, weight=HARD)
    for h in spec.holes:
        obstacles.add_circle(*view.pt(h.x, h.y),
                             view.d(max(h.dia, h.keepout_dia or 0) / 2) + 1.0)
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            obstacles.add_rect(*view.pt(p.body_x0, p.body_y0),
                               *view.pt(p.body_x1, p.body_y1), pad=0.8)
    # The board outline.  A balloon straddling it breaks the one line on the
    # sheet a reader traces first, so it is hard; but a leader crossing it is
    # how a balloon in the margin points at a part on the board, so it is not
    # charged for at all.
    edge_only = Obstacles()
    for edge in ((0, 0, o.width, 0), (o.width, 0, o.width, o.height),
                 (o.width, o.height, 0, o.height), (0, o.height, 0, 0)):
        edge_only.add_segment(*view.pt(edge[0], edge[1]),
                              *view.pt(edge[2], edge[3]), weight=HARD)

    # The overall dimensions are drawn after the balloons, along the top and
    # right edges, so they are reserved now.  The value is hard -- a leader
    # ruled through "56.00" is as unreadable as a balloon parked on it -- but
    # the line either side of it is position only.  Reserving the whole band
    # against leaders as well boxed the balloons into the board's interior,
    # because a leader from a part near the top or right had to cross a band
    # to reach any space at all.
    band = style.T_DIM + style.descender(style.T_DIM) + style.DIM_TEXT_GAP
    for value, horizontal in ((o.width, True), (o.height, False)):
        half = style.text_width(f"{value:.2f}", style.T_DIM) / 2
        if horizontal:
            mid = (board.x + board.x1) / 2
            lo, hi = board.y1 + OVERALL_GAP - 1.0, board.y1 + OVERALL_GAP + band
            edge_only.add_rect(board.x, lo, board.x1, hi, pad=1.2, weight=HARD)
            obstacles.add_rect(mid - half, lo, mid + half, hi,
                               pad=1.2, weight=HARD)
        else:
            mid = (board.y + board.y1) / 2
            lo, hi = board.x1 + OVERALL_GAP - band, board.x1 + OVERALL_GAP + 1.0
            edge_only.add_rect(lo, board.y, hi, board.y1, pad=1.2, weight=HARD)
            obstacles.add_rect(lo, mid - half, hi, mid + half,
                               pad=1.2, weight=HARD)

    # The ordinate witness lines are drawn after the balloons but stand in
    # their way all the same: a balloon sitting on one reads as though it
    # belonged to the dimension, so they are reserved now.  They run from the
    # feature they locate out to the dimension band.
    # Position only, like the board outline: a balloon parked on a witness
    # line reads as belonging to the dimension, but a leader crossing one is
    # ordinary.  Charged to the leader as well, they cost more to cross than a
    # feature costs to sit on, and on the Pi 3A+ a balloon chose to cover a
    # neighbouring connector rather than cross the witness line beside it.
    xvals, yvals = _ordinate_values(spec, overlay)
    for v, f in xvals.items():
        edge_only.add_segment(view.x(v), view.y(f), view.x(v),
                              balloon_bounds.y, weight=HARD)
    for v, f in yvals.items():
        edge_only.add_segment(view.x(f), view.y(v), balloon_bounds.x,
                              view.y(v), weight=HARD)

    items: list[_Ballooned] = []
    schedule: list[list[str]] = []
    # Largest features first: they have the least freedom, and placing them
    # early stops a small feature's balloon taking the only good spot.
    order = sorted(range(len(spec.features)),
                   key=lambda i: -(spec.features[i].width * spec.features[i].height))
    # The number a feature carries is its own, not its position in the list,
    # so it means the same part on every sheet of the family.  Every number
    # the family uses gets a row, including the ones this board does not
    # carry: a schedule that jumps from 6 to 8 reads as a mistake, and the
    # reader has no way to find out what 7 would have been.
    present = {f.number or n: f for n, f in enumerate(spec.features, 1)}
    for number in sorted(set(present) | set(family_numbers or {})):
        f = present.get(number)
        if f is None:
            schedule.append([str(number),
                             f"{family_numbers[number]} - not on this board",
                             "-", "-"])
        else:
            schedule.append([str(number), f.label,
                             f"{f.x0:.2f} to {f.x1:.2f}",
                             f"{f.y0:.2f} to {f.y1:.2f}"])
    for i in order:
        f = spec.features[i]
        items.append(_Ballooned(str(f.number or i + 1), view.pt(f.cx, f.cy),
                                _feature_anchors(view, f), feature_rect[i]))
    place_balloons(items, obstacles, balloon_bounds, c,
                   position_only=edge_only)

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

    # The Pmod pin-field depth, dimensioned once per edge rather than folded
    # into an ordinate chain.  It runs on a lane alongside the outermost host
    # of that edge, chosen clear of every drawn part: fixed five millimetres
    # out, it ran through mounting hole MT2 on the v3 boards and through MT3
    # on the Pmod HAT Adapter.  The span is three or four millimetres and the
    # value three times that, so the value cannot sit between the arrows; it
    # is written along the lane on the inboard side, where the lane is clear
    # by construction.  Outboard is where the host spacing dimension and the
    # ordinate chain already are.
    for edge, group in by_edge.items():
        along = "cx" if edge in ("bottom", "top") else "cy"
        outer = max(group, key=lambda p: getattr(p, along))
        lane = _clear_lane(view, outer, edge, board, blockers)
        # A centre line along the row of pin fields, so the dimension's
        # extension line ends on something.  Without it the lane -- chosen
        # clear of every drawn part, which is what put it in a gap between
        # hosts or just beyond the last one -- gave a 1.2 mm stub floating in
        # open board, pointing at nothing.  It is a row of centres, so a
        # centre line is what belongs there.
        _pin_row_centre_line(c, view, group, edge, lane)
        if edge == "bottom":
            dims.linear(c, (lane, board.y), (lane, view.y(outer.cy)), 0.0,
                        horizontal=False, value=outer.cy, text_side="high")
        elif edge == "top":
            dims.linear(c, (lane, view.y(outer.cy)), (lane, board.y1), 0.0,
                        horizontal=False, value=o.height - outer.cy,
                        text_side="low")
        elif edge == "left":
            dims.linear(c, (board.x, lane), (view.x(outer.cx), lane), 0.0,
                        horizontal=True, value=outer.cx, text_side="high")
        else:
            dims.linear(c, (view.x(outer.cx), lane), (board.x1, lane), 0.0,
                        horizontal=True, value=o.width - outer.cx,
                        text_side="low")

    x_extent = dims.ordinate_chain(
        c, [(view.x(v), f"{v:.2f}", view.y(f)) for v, f in xvals.items()],
        board.y, lowest - 9.0, horizontal=True,
        zero_pos=board.x, zero_from=board.y, blockers=blockers)
    y_extent = dims.ordinate_chain(
        c, [(view.y(v), f"{v:.2f}", view.x(f)) for v, f in yvals.items()],
        board.x, leftmost - 9.0, horizontal=False,
        zero_pos=board.y, zero_from=board.x, blockers=blockers)

    # The overall dimensions go on the edges the ordinate chains do not use:
    # width across the top, height up the right.  Stacked outside the chains
    # below and left, they had to clear the chain, its labels and the Pmod
    # spacing dimension, which put the overall size of the board thirty
    # millimetres away from the board.  On these edges they sit close in, with
    # short extension lines, which is where a reader looks for them.
    del x_extent, y_extent
    dims.linear(c, (board.x, board.y1), (board.x1, board.y1), OVERALL_GAP,
                horizontal=True, value=o.width)
    dims.linear(c, (board.x1, board.y), (board.x1, board.y1), OVERALL_GAP,
                horizontal=False, value=o.height)
    # The datum sits in the busiest corner of the sheet, so its label goes out
    # on a leader into the empty wedge below and left of the ordinate chains
    # rather than next to the marker.
    dims.datum_marker(c, board.x, board.y, label="")

    if o.corner_radius:
        r = o.corner_radius
        tip = view.pt(o.width - r * 0.3, o.height - r * 0.3)
        # Always names its subject.  On the Pi 3A+ the phantom Pmod HAT
        # Adapter outline runs within half a millimetre of the board's own, so
        # the callout has to say which it means; naming it only there left the
        # same callout worded two ways across the package.
        label, elbow_x, _, _ = _radius_callout(o, board, sheet, view)
        dims.leader(c, tip, (elbow_x, board.y1 + 5.0), label)

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
        # pitch dimensioned on the view.  A note on the sheet says so, because
        # a third decimal otherwise reads as a claim to micrometre accuracy
        # that neither the source nor the general tolerance supports.
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
        # Same numbers as the adapter's own sheet, so the same precision.
        rows = [[p.label, f"{p.edge} edge", f"{p.cx:.3f}", f"{p.cy:.3f}",
                 f"{p.pin1_x:.3f}", f"{p.pin1_y:.3f}"] for p in overlay.pmods]
        block = sheet.column_block(sheet.table_height("PMOD HAT ADAPTER HOSTS", len(rows)))
        sheet.table(block, "PMOD HAT ADAPTER HOSTS",
                    ["PORT", "EDGE", "CX mm", "CY mm", "PIN1 X mm",
                     "PIN1 Y mm"], rows,
                    ["start", "start", "end", "end", "end", "end"])

    # The legend goes directly under the tables and the notes' tail below it,
    # at the foot of the column.  Both are measured first so that neither can
    # take space the other needs.
    #
    # Notes carry facts about this board, not an explanation of how to read a
    # drawing.  The column is finite, and losing a provenance note to make room
    # for a description of ordinate dimensioning is a bad trade.
    entries = _legend_entries(spec, overlay)
    spill = notes_spill_needed(sheet, notes, src_lines, band_cols)
    want = legend_height(len(entries)) + (spill + 4.0 if spill else 0.0)
    if sheet.column_remaining < want:
        raise SystemExit(
            f"{spec.key}: the annotation column cannot hold both the legend "
            f"and the notes' tail ({want:.0f} mm wanted, "
            f"{sheet.column_remaining:.0f} mm left); shorten the notes")
    draw_legend(sheet, entries)
    _place_notes_and_sources(sheet, notes, src_lines, columns=band_cols,
                             spill=spill)

    sheet.draw_title_block()
    return sheet
