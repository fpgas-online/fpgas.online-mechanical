"""Assembly drawings of the base plates: a Pi and an FPGA board joined by the direct Raspmod.

Three views, first angle, on an A2.  The elevation looks along -X, so the
plate's Y runs left to right with the Pi at the left and the FPGA board at
the right, and the plan sits under it at the same scale with its Y running
the same way, so a feature in one is straight above or below itself in the
other.  Both are 1:1: the plate is 192 mm long, and at 1:2 the plan had no
room for its own labels.  The heights are what the sheet is for, and a
1.4 mm board and a 3.8 mm socket are not legible at 1:1, so the joint --
from the Pi's far end to the host sockets -- is drawn again as a detail at
2:1, and that is where every level is dimensioned, as ordinates from the
plate's top face.

Everything standing on the plate is a box in ``base_plates/plates.py``, and
all three views are drawn from the same list, so the plan cannot put a part
where the elevation does not.  The plate itself and the cups are the made
parts and are drawn in full line; the boards, the connectors and the
standoffs are bought and in place, and are phantom.
"""

from __future__ import annotations

from base_plates.model import Box, Plate
from base_plates.plates import CUP_SCREW_HOLE
from tools.layout import drawing_name

from . import dims, style
from .board_sheet import Obstacles, draw_holes, draw_legend, note_blocks, outline_path
from .plate_sheet import place_label
from .sheet import Rect, Sheet, TitleBlock
from .view import scale_text

SHEET = "A2"
SCALE = 1.0
DETAIL_SCALE = 4.0
CUP_SCALE = 2.0
#: The notes column stops here when a cup detail goes under it.
CUP_DETAIL_TOP = 128.0
#: Left of the views: the plan's X ordinates and the Pi standoff's height.
LEFT = 44.0
CAPTION = 7.0
#: Between the elevation and the plan, and between the plan and the detail.
GAP = 12.0
#: Under the plan: its Y ordinates and the overall length.
PLAN_UNDER = 34.0
NO_BAND = 2.0
#: Below the plate's underside and above the tallest part, in model mm.
Z_BELOW = 5.0
Z_ABOVE = 3.0
#: How far the detail reaches either side of the joint, in model mm.
DETAIL_BEFORE = 12.0
DETAIL_AFTER = 4.0
#: Paper mm above and below the detail for the names of its parts.
NAME_LANE = 11.0
#: Right of the plan for its second X chain, then the notes.
RIGHT = 52.0

#: What the detail calls each part, and whether its name goes above the
#: part or below the plate.  A part not here is not named.
DETAIL_NAMES = {
    "Pmod host": ("HOST SOCKET", "up"),
    "Plug P1": ("PLUG", "up"),
    "ACC-": ("ADAPTER", "up"),
    "Pi 40-pin header": ("PI HEADER", "up"),
    "Demoboard": ("DEMOBOARD", "up"),
    "Digilent Arty A7": ("ARTY A7", "up"),
    "Adapter socket": ("SOCKET", "down"),
    "Raspberry Pi": ("RASPBERRY PI", "down"),
    "M2.5": ("STANDOFF", "down"),
    "M3 x": ("STANDOFF", "down"),
    "TT-MP-PLATE": ("TT-MP-PLATE", "down"),
    "Cup": ("CUP", "down"),
    "Rubber foot": ("FOOT", "down"),
}

MADE = dict(w=style.W_OUTLINE, colour=style.C_LINE)
ADJACENT = dict(w=style.W_PHANTOM, colour=style.C_PHANTOM, dash=style.D_PHANTOM)
HEADER = dict(w=style.W_PHANTOM, colour=style.C_PHANTOM)
ALT = dict(w=style.W_PHANTOM, colour=style.C_PHANTOM, dash=style.D_HIDDEN)
STANDOFF = dict(w=style.W_PHANTOM, colour=style.C_PHANTOM)
HOLE_LABEL = style.C_LINE

STYLES = {"adjacent": ADJACENT, "header": HEADER, "alt": ALT,
          "standoff": STANDOFF, "made": MADE}

HOLE_FOR = {"pi": "M2.5 clearance, c'sunk below, Raspberry Pi",
            "mp": "M4 tapped, TT plate", "cup": "M3 clearance, c'sunk below, cup"}

#: What the plan calls each board.
NAMED = {"Raspberry Pi": "RASPBERRY PI", "Digilent Arty A7": "ARTY A7",
         "TT-MP-PLATE": "TT-MP-PLATE", "Demoboard, every revision": "DEMOBOARD"}


class Side:
    """The elevation's mapping: plate Y to the right, Z up, at *s*."""

    def __init__(self, left: float, base: float, s: float):
        self.left, self.base, self.s = left, base, s

    def pt(self, y: float, z: float) -> tuple[float, float]:
        return (self.left + y * self.s, self.base + z * self.s)

    def x(self, y: float) -> float:
        return self.left + y * self.s

    def y(self, z: float) -> float:
        return self.base + z * self.s

    def d(self, v: float) -> float:
        return v * self.s


class Plan:
    """The plan's mapping: plate Y to the right, X downwards, at *s*.

    A quarter turn of the usual X-right, Y-up plan, so that the plan's Y is
    the elevation's and the two line up; first angle puts the side nearest
    the elevation's viewer (large X) at the bottom.
    """

    def __init__(self, left: float, top: float, s: float):
        self.left, self.top, self.s = left, top, s

    def pt(self, x: float, y: float) -> tuple[float, float]:
        return (self.left + y * self.s, self.top - x * self.s)

    def d(self, v: float) -> float:
        return v * self.s


def _legend(p: Plate) -> list:
    entries = [
        ("outline", "The plate" + (", and a printed cup" if p.made else "")),
        ("phantom", "A board, standing in place, bought"),
        (("line", style.W_PHANTOM, style.C_PHANTOM, None),
         "A connector or a standoff, bought"),
    ]
    if any(b.kind == "alt" for b in p.boxes):
        entries.append((("line", style.W_PHANTOM, style.C_PHANTOM, style.D_HIDDEN),
                        "The Pi, its standoffs and the adapter at position B"))
    entries += [("dimension", "Dimension, extension and leader"),
                (style.C_LINE, "Hole, see the table")]
    return entries


def _hosts(p: Plate) -> list[Box]:
    return [b for b in p.boxes if b.label.startswith("Pmod host")]


def _pi(p: Plate) -> Box:
    return next(b for b in p.boxes if b.label == "Raspberry Pi" and b.position in ("", "A"))


def _z_range(p: Plate) -> tuple[float, float]:
    return (-p.spec.outline.thickness - Z_BELOW, max(b.z1 for b in p.boxes) + Z_ABOVE)


# ---------------------------------------------------------------------------
# the elevation and the detail, one drawer
# ---------------------------------------------------------------------------

def _draw_side(sheet: Sheet, p: Plate, v: Side, y0: float, y1: float) -> None:
    """The plate and everything on it, seen along -X, between plate y0 and y1.

    An end inside the plate is left open and closed with a break line.
    """
    c = sheet.canvas
    t = p.spec.outline.thickness
    L = p.spec.outline.height
    a, b = v.pt(y0, -t), v.pt(y1, 0.0)
    c.line(a[0], a[1], b[0], a[1], **MADE)
    c.line(a[0], b[1], b[0], b[1], **MADE)
    if y0 <= 0.0:
        c.line(a[0], a[1], a[0], b[1], **MADE)
    if y1 >= L:
        c.line(b[0], a[1], b[0], b[1], **MADE)
    # Every box, clipped to the range; the made parts last so they read
    # over what is behind them.
    for kind in ("standoff", "adjacent", "alt", "header", "made"):
        for box in p.boxes:
            if box.kind != kind:
                continue
            if box.kind == "alt" and box.position == "B":
                continue        # identical to A in this view
            by0, by1 = max(box.y0, y0), min(box.y1, y1)
            if by1 <= by0:
                continue
            kw = STYLES[kind]
            (x0, z0), (x1, z1) = v.pt(by0, box.z0), v.pt(by1, box.z1)
            # A cup's wall along the plate's Y is seen face on here, a
            # face and not a cut, so it is drawn thin; the wall across
            # it is seen end on and keeps the outline weight.
            weight = kw["w"]
            if box.label == "Cup wall" and box.y1 - box.y0 > box.x1 - box.x0:
                weight = style.W_THIN
            c.rect(x0, z0, x1 - x0, z1 - z0, weight=weight, colour=kw["colour"],
                   dash=kw.get("dash"))
            # A connector's pin rows, as centre lines across it.
            if "pins" not in box.label:
                for r in box.rows:
                    c.line(x0, v.y(r), x1, v.y(r), w=style.W_CENTRE,
                           colour=style.C_PHANTOM, dash=style.D_CENTRE)
    zlo, zhi = _z_range(p)
    for y, inside in ((y0, y0 > 0.0), (y1, y1 < L)):
        if inside:
            _break_line(c, v.x(y), v.y(zlo + Z_BELOW / 2), v.y(zhi - Z_ABOVE / 2))


def _break_line(c, x: float, y_from: float, y_to: float) -> None:
    """A zigzag from y_from up to y_to at x."""
    pts = [(x, y_from)]
    y, k = y_from, 0
    while y < y_to:
        k += 1
        y = min(y + 4.0, y_to)
        pts.append((x + (1.5 if k % 2 else -1.5), y))
    c.polyline(pts, w=style.W_THIN, colour=style.C_LINE)


def _detail_range(p: Plate) -> tuple[float, float]:
    """Plate y0, y1 the detail covers: the Pi's far end to past the hosts."""
    pi = _pi(p)
    far = max(h.y1 for h in _hosts(p))
    return (pi.y1 - DETAIL_BEFORE, far + DETAIL_AFTER)


def _standoff_dims(sheet: Sheet, p: Plate, v: Side) -> None:
    """The two heights a builder buys or prints, each at its own standoff.

    The Pi's, at its front standoff, dimensioned in the margin left of the
    plate's front end; the FPGA board's, at its rearmost standoff or cup,
    right of the plate's back end.  Every other level is in the detail.
    """
    c = sheet.canvas
    L = p.spec.outline.height
    pi_so = min((b for b in p.boxes if b.kind == "standoff" and b.z0 == 0.0
                 and b.position in ("", "A")), key=lambda b: b.cy)
    fx = v.x(pi_so.cy)
    # A 4 mm standoff is shorter than its own value: the value then goes
    # above the span, where nothing is, as ISO 129-1 has it.
    dims.linear(c, (fx, v.y(0.0)), (fx, v.y(pi_so.z1)), -(fx - v.x(0.0) + 6.0),
                horizontal=False, value=pi_so.z1, text_side="high")
    rear = max((b for b in p.boxes if b.kind in ("standoff", "made")
                and b.label != "Cup wall"), key=lambda b: b.cy)
    fx = v.x(rear.cy)
    dims.linear(c, (fx, v.y(rear.z0)), (fx, v.y(rear.z1)), v.x(L) - fx + 6.0,
                horizontal=False, value=rear.z1 - rear.z0, text_side="high")
    # The plate's thickness, at its front end.
    t = p.spec.outline.thickness
    dims.linear(c, v.pt(0.0, -t), v.pt(0.0, 0.0), -(6.0 + 2 * style.DIM_STEP),
                horizontal=False, value=t, text_side="low")


def _detail_names(sheet: Sheet, p: Plate, v: Side, y0: float, y1: float) -> None:
    """Name the parts in the detail: a row above, a row below the plate.

    Each name sits over (or under) the part it names, with a thin line down
    to the part's own edge; names that would overprint are pushed along the
    row.  One name per part: the first box of each kind in the detail.
    """
    c = sheet.canvas
    zlo, zhi = _z_range(p)
    rows = {"up": [], "down": []}
    named = set()
    for box in p.boxes:
        if box.kind == "alt" or "pins" in box.label or box.label == "Cup wall":
            continue
        by0, by1 = max(box.y0, y0), min(box.y1, y1)
        if by1 <= by0:
            continue
        key = next((k for k in DETAIL_NAMES if box.label.startswith(k)), None)
        if key is None or key in named:
            continue
        named.add(key)
        name, side = DETAIL_NAMES[key]
        # A part sitting on the plate is met half way up its band, or the
        # line's end would sit on the plate's own top face.
        tip_z = box.z1 if side == "up" else (box.z0 if box.z0 > 0.0 else (box.z0 + box.z1) / 2)
        rows[side].append((box, by0, by1, name, tip_z))
    taken: list[float] = []
    for side, items in rows.items():
        placed = []
        for box, by0, by1, name, tip_z in items:
            # Try along what is shown of the part: the spot whose line to
            # the row crosses the fewest other parts, then the one furthest
            # from the lines already placed.
            best = None
            for k in range(1, 20):
                y = by0 + (by1 - by0) * k / 20
                crossing = 0
                for b in p.boxes:
                    if b is box or b.kind == "alt" or "pins" in b.label:
                        continue
                    if not (b.y0 < y < b.y1):
                        continue
                    if side == "up" and b.z1 > tip_z + 0.01:
                        crossing += 1
                    if side == "down" and b.z0 < tip_z - 0.01:
                        crossing += 1
                apart = min((abs(v.x(y) - tx) for tx in taken), default=99.0)
                score = (crossing, -min(apart, 12.0), abs(k - 7))
                if best is None or score < best[0]:
                    best = (score, y)
            x = v.x(best[1])
            taken.append(x)
            placed.append((x, name, v.y(tip_z)))
        items = sorted(placed)
        row_y = v.y(zhi) + NAME_LANE - style.T_LABEL if side == "up" \
            else v.y(zlo) - NAME_LANE + 2.0
        end = -1e9
        for x, name, tip_y in items:
            w = style.text_width(name, style.T_TINY)
            tx = max(x, end + w / 2 + 4.0)
            c.text(tx, row_y, name, size=style.T_TINY, colour=style.C_DIM, anchor="middle")
            end = tx + w / 2
            ly = row_y - 1.0 if side == "up" else row_y + style.T_TINY + 1.0
            c.line(x, tip_y, tx, ly, w=style.W_THIN, colour=style.C_DIM)


def _detail_ordinates(sheet: Sheet, p: Plate, v: Side, y0: float, y1: float) -> None:
    """Every level in the table, as an ordinate from the plate's top face.

    Each witness line starts at the face it measures, on the box that has
    that face, so the number can be traced to the part.  The plug rows are
    left out: they are the host rows to within the residual, and the table
    says by how much.
    """
    c = sheet.canvas
    values = []
    seen = set()
    for name, z in p.levels:
        if name == "Plug rows":
            continue
        for zz in (z if isinstance(z, tuple) else (z,)):
            if zz in seen:
                continue
            seen.add(zz)
            # The box with this face, nearest the chain (largest y).
            owners = [b for b in p.boxes if b.kind != "alt" and b.y1 > y0 and b.y0 < y1
                      and (abs(b.z0 - zz) < 0.011 or abs(b.z1 - zz) < 0.011
                           or any(abs(r - zz) < 0.011 for r in b.rows))]
            if not owners:
                continue
            owner = max(owners, key=lambda b: b.y1)
            values.append((v.y(zz), f"{zz:.2f}", v.x(min(owner.y1, y1))))
    blockers = []
    for b in p.boxes:
        if b.kind == "alt" or "pins" in b.label or b.y1 <= y0 or b.y0 >= y1:
            continue
        (bx0, bz0), (bx1, bz1) = v.pt(max(b.y0, y0), b.z0), v.pt(min(b.y1, y1), b.z1)
        blockers.append((bx0, bz0, bx1, bz1))
    base = v.x(y1)
    dims.ordinate_chain(c, values, base, base + 10.0, horizontal=False,
                        zero_pos=v.y(0.0), zero_from=v.x(y1), zero_label="Z 0",
                        blockers=blockers)


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------

def _draw_plan(sheet: Sheet, p: Plate, v: Plan) -> None:
    c = sheet.canvas
    outline_path(c, v, p.spec)
    for kind in ("adjacent", "alt", "header", "made"):
        for box in p.boxes:
            if box.kind != kind or box.label.endswith(" pins"):
                continue
            kw = STYLES[kind]
            (x0, y0), (x1, y1) = v.pt(box.x0, box.y0), v.pt(box.x1, box.y1)
            c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
                   weight=kw["w"], colour=kw["colour"], dash=kw.get("dash"))
    draw_holes(c, v, p.spec.holes)
    # Hole labels, placed clear of everything, the boards' names included.
    obstacles = Obstacles()
    for box in _plan_names(c, p, v):
        obstacles.add_rect(*box)
    for h in p.spec.holes:
        px, py = v.pt(h.x, h.y)
        obstacles.add_circle(px, py, v.d(h.dia / 2) + 0.6)
    for box in p.boxes:
        if box.label.endswith(" pins"):
            continue
        (x0, y0), (x1, y1) = v.pt(box.x0, box.y0), v.pt(box.x1, box.y1)
        x0, x1, y0, y1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
        if box.kind in ("made", "header"):
            obstacles.add_rect(x0, y0, x1, y1)
        else:
            # A board: a band along each edge, so a label neither crosses
            # nor touches the outline; and its area, lightly, so a label
            # goes outside the board when there is room there.
            m = 1.2
            for bx0, by0, bx1, by1 in ((x0 - m, y0 - m, x1 + m, y0 + m),
                                       (x1 - m, y0 - m, x1 + m, y1 + m),
                                       (x0 - m, y1 - m, x1 + m, y1 + m),
                                       (x0 - m, y0 - m, x0 + m, y1 + m)):
                obstacles.add_rect(bx0, by0, bx1, by1)
            obstacles.add_rect(x0, y0, x1, y1, weight=0.3)
    others = [v.pt(h.x, h.y) for h in p.spec.holes]
    o = p.spec.outline
    for hx, hy, side in _witness_paths(p):
        px, py = v.pt(hx, hy)
        if side == "left":
            obstacles.add_segment(v.left - 14.0, py, px, py)
        elif side == "right":
            obstacles.add_segment(px, py, v.left + v.d(o.height) + 14.0, py)
        else:
            obstacles.add_segment(px, py, px, v.top - v.d(o.width) - 14.0)
    bounds = Rect(v.left, v.top - v.d(o.width), v.d(o.height), v.d(o.width))
    for h in p.spec.holes:
        px, py = v.pt(h.x, h.y)
        box = place_label(c, obstacles, (px, py), v.d(h.dia / 2) + 0.6, h.label, HOLE_LABEL,
                          others=[q for q in others if q != (px, py)], bounds=bounds)
        obstacles.add_rect(*box)


def _plan_names(c, p: Plate, v: Plan) -> list[tuple[float, float, float, float]]:
    """Name each board inside its outline; returns the paper each name took.

    The Pi at both positions is named at whichever end is its own; the
    adapter once, at A, its B outline being in the legend; the TT plate
    along the strip behind the demoboard, turned to fit it, and the
    adapter likewise in the strip between its socket and its plugs.
    """
    taken = []
    pis = [b for b in p.boxes if b.label == "Raspberry Pi"]
    for box in p.boxes:
        if box.label.startswith("ACC-"):
            if box.position == "B":
                continue
            text = box.label
        elif box.label in NAMED:
            text = NAMED[box.label]
        elif box.label.startswith("Pmod host J"):
            text = box.label.split()[-1]
        else:
            continue
        cx, cy = box.cx, box.cy
        rotate = 0.0
        if box.label == "Raspberry Pi" and box.position:
            text += f", {box.position}"
            other = next(b for b in pis if b is not box)
            cx = box.x0 + 12.0 if box.x0 < other.x0 else box.x1 - 12.0
        if box.label == "TT-MP-PLATE":
            inner = next(b for b in p.boxes if b.label.startswith("Demoboard"))
            cy = (inner.y1 + box.y1) / 2
            rotate = -90.0
        if box.label.startswith("ACC-"):
            socket = next(b for b in p.boxes if b.label.startswith("Adapter socket")
                          and b.position == box.position)
            plugs = [b for b in p.boxes if b.label.startswith("Plug P") and "pins" not in b.label
                     and b.position == box.position]
            cy = (socket.y1 + min(b.y0 for b in plugs)) / 2
            rotate = -90.0
            other = next((b for b in p.boxes if b.label == box.label and b.position == "B"), None)
            if other is not None:
                # Where the A outline is not also the B outline.
                cx = (other.x1 + box.x1) / 2 if other.x1 < box.x1 else (box.x0 + other.x0) / 2
        px, py = v.pt(cx, cy)
        w = style.text_width(text, style.T_LABEL)
        h = style.T_LABEL + style.descender(style.T_LABEL)
        if rotate:
            c.text(px + style.T_LABEL / 2, py, text, size=style.T_LABEL,
                   colour=style.C_PHANTOM, anchor="middle", rotate=rotate)
            taken.append((px - h - 1.0, py - w / 2 - 1.0, px + h + 1.0, py + w / 2 + 1.0))
        else:
            c.text(px, py - style.T_LABEL / 2, text, size=style.T_LABEL,
                   colour=style.C_PHANTOM, anchor="middle")
            taken.append((px - w / 2 - 1.0, py - h - 1.0, px + w / 2 + 1.0, py + 1.0))
    return taken


def _witness_paths(p: Plate) -> list[tuple[float, float, str]]:
    """Which hole each ordinate's witness line leaves, and which way it goes.

    One per distinct value: the Y chain along the bottom takes the hole
    nearest it (largest X); the X chains take the hole nearest their side,
    the front half's holes to the left and the back half's to the right.
    """
    o = p.spec.outline
    ys: dict[float, float] = {}
    front: dict[float, float] = {}
    back: dict[float, float] = {}
    for h in p.spec.holes:
        ys[h.y] = max(ys.get(h.y, -1e9), h.x)
        if h.y < o.height / 2:
            front[h.x] = min(front.get(h.x, 1e9), h.y)
        else:
            back[h.x] = max(back.get(h.x, -1e9), h.y)
    return ([(x, y, "down") for y, x in ys.items()]
            + [(x, y, "left") for x, y in front.items()]
            + [(x, y, "right") for x, y in back.items()])


def _plan_ordinates(sheet: Sheet, p: Plate, v: Plan) -> None:
    """Every hole's X and Y as ordinates, and the plate's overall size."""
    c = sheet.canvas
    o = p.spec.outline
    left, top = v.left, v.top
    right, bottom = v.pt(o.width, o.height)
    blockers = []
    for h in p.spec.holes:
        px, py = v.pt(h.x, h.y)
        r = v.d(h.dia / 2) + 1.0
        blockers.append((px - r, py - r, px + r, py + r))
    paths = _witness_paths(p)
    # Y along the bottom, one ordinate per distinct value; X down both
    # sides, from the top edge, which is where X = 0 is, so that no witness
    # line runs the length of the plate through everything on it.
    y_extent = dims.ordinate_chain(
        c, [(v.pt(0, y)[0], f"{y:.2f}", v.pt(x, y)[1]) for x, y, s in paths if s == "down"],
        bottom, bottom - 12.0, horizontal=True,
        zero_pos=left, zero_from=bottom, zero_label="Y 0", blockers=blockers)
    dims.ordinate_chain(
        c, [(v.pt(x, 0)[1], f"{x:.2f}", v.pt(x, y)[0]) for x, y, s in paths if s == "left"],
        left, left - 12.0, horizontal=False,
        zero_pos=top, zero_from=left, zero_label="X 0", blockers=blockers)
    x_extent = dims.ordinate_chain(
        c, [(v.pt(x, 0)[1], f"{x:.2f}", v.pt(x, y)[0]) for x, y, s in paths if s == "right"],
        right, right + 12.0, horizontal=False,
        zero_pos=top, zero_from=right, zero_label="X 0", blockers=blockers)
    dims.linear(c, (left, bottom), (right, bottom), y_extent - 7.0 - bottom,
                horizontal=True, value=o.height, ext_start=y_extent - 2.0)
    dims.linear(c, (right, bottom), (right, top), x_extent + 7.0 - right,
                horizontal=False, value=o.width, ext_start=x_extent + 2.0)
    dims.datum_marker(c, left, top, label="")


# ---------------------------------------------------------------------------
# the cup
# ---------------------------------------------------------------------------

def _cup_detail(sheet: Sheet, p: Plate, x: float, top: float) -> None:
    """One corner cup, plan and section at CUP_SCALE, with its own dimensions.

    The cup is a printed part and gets what a printed part needs: its plan
    with the walls shaded, and a section through the screw hole showing
    the ledge, the wall and the foot standing on the ledge.
    """
    c = sheet.canvas
    s = CUP_SCALE
    cup = next(b for b in p.boxes if b.label == "Cup")
    walls = [b for b in p.boxes if b.label == "Cup wall"
             and b.x0 < cup.x1 and b.x1 > cup.x0 and b.y0 < cup.y1 and b.y1 > cup.y0]
    foot = next(b for b in p.boxes if b.label == "Rubber foot"
                and cup.x0 < b.cx < cup.x1 and cup.y0 < b.cy < cup.y1)
    hole = next(h for h in p.spec.holes if cup.x0 < h.x < cup.x1 and cup.y0 < h.y < cup.y1)
    board = next(b for b in p.boxes if b.label == "Digilent Arty A7")
    c.text(x, top + 3.0, f"DETAIL B, ONE CORNER CUP, {scale_text(s, 1)}", size=style.T_LABEL,
           bold=True)

    # The plan, the same way up as the main plan.
    v = Plan(x + 4.0 - cup.y0 * s, top - 12.0 + cup.x0 * s, s)
    (px0, py0), (px1, py1) = v.pt(cup.x0, cup.y0), v.pt(cup.x1, cup.y1)
    px0, px1, py0, py1 = min(px0, px1), max(px0, px1), min(py0, py1), max(py0, py1)
    for w in walls:
        (wx0, wy0), (wx1, wy1) = v.pt(w.x0, w.y0), v.pt(w.x1, w.y1)
        c.rect(min(wx0, wx1), min(wy0, wy1), abs(wx1 - wx0), abs(wy1 - wy0),
               weight=style.W_THIN, colour=style.C_LINE, fill=style.C_FILL_LIGHT)
    c.rect(px0, py0, px1 - px0, py1 - py0, weight=style.W_OUTLINE, colour=style.C_LINE)
    fx, fy = v.pt(foot.cx, foot.cy)
    c.circle(fx, fy, v.d((foot.x1 - foot.x0) / 2), w=style.W_PHANTOM, colour=style.C_PHANTOM,
             dash=style.D_PHANTOM)
    c.circle(fx, fy, v.d(CUP_SCREW_HOLE / 2), w=style.W_OUTLINE, fill=style.C_FILL_HOLE)
    dims.centre_mark(c, fx, fy, v.d(CUP_SCREW_HOLE / 2))
    # The cut for the section: through the hole, along the plate's Y.
    c.line(px0 - 16.0, fy, px0 - 12.0, fy, w=style.W_THIN, colour=style.C_DIM, dash=style.D_CENTRE)
    c.line(px1 + 1.0, fy, px1 + 5.0, fy, w=style.W_THIN,
           colour=style.C_DIM, dash=style.D_CENTRE)
    c.text(px0 - 19.0, fy - 1.0, "B", size=style.T_LABEL, colour=style.C_DIM, bold=True,
           anchor="middle")
    c.text(px1 + 7.5, fy - 1.0, "B", size=style.T_LABEL,
           colour=style.C_DIM, bold=True, anchor="middle")
    # Its size, and the hole from the two outer faces, which is how a print
    # is checked: the walls are on those faces.
    dims.linear(c, (px0, py0), (px1, py0), -6.0 - style.DIM_STEP, horizontal=True,
                value=cup.y1 - cup.y0)
    dims.linear(c, (px1, py0), (px1, py1), 6.0 + 1.5 * style.DIM_STEP, horizontal=False,
                value=cup.x1 - cup.x0, text_side="high")
    ywall = next(w for w in walls if w.y1 - w.y0 < w.x1 - w.x0)      # runs along x
    xwall = next(w for w in walls if w.x1 - w.x0 < w.y1 - w.y0)      # runs along y
    y_face = ywall.y0 if ywall.y0 <= cup.y0 + 0.01 else ywall.y1
    x_face = xwall.x0 if xwall.x0 <= cup.x0 + 0.01 else xwall.x1
    dims.linear(c, (v.pt(0, y_face)[0], py0), (fx, py0), -6.0,
                horizontal=True, value=abs(hole.y - y_face))
    dims.linear(c, (px0, v.pt(x_face, 0)[1]), (px0, fy), -6.0,
                horizontal=False, value=abs(hole.x - x_face), text_side="high")
    (_, xw0), (_, xw1) = v.pt(xwall.x0, 0), v.pt(xwall.x1, 0)
    dims.linear(c, (px0, xw0), (px0, xw1), -6.0, horizontal=False,
                value=xwall.x1 - xwall.x0, text_side="low")
    hw = ywall.y1 - ywall.y0
    (hx0, _), (hx1, _) = v.pt(0, ywall.y0), v.pt(0, ywall.y1)
    dims.linear(c, (hx0, py1), (hx1, py1), 5.0, horizontal=True, value=hw, text_side="high")

    # The section B-B, under the plan: the plate's Y across, Z up.
    t_ = p.spec.outline.thickness
    zlo, zhi = -t_ - 2.0, max(w.z1 for w in walls) + 1.0
    stop = py0 - 6.0 - 2 * style.DIM_STEP - 6.0
    sv = Side(x + 4.0 - cup.y0 * s, stop - zhi * s, s)
    c.text(x, stop + 3.0, f"SECTION B-B, {scale_text(s, 1)}", size=style.T_LABEL, bold=True)
    a, b = sv.pt(cup.y0 - 3.0, -t_), sv.pt(cup.y1 + 3.0, 0.0)
    c.line(a[0], a[1], b[0], a[1], **MADE)
    c.line(a[0], b[1], b[0], b[1], **MADE)
    # The wall beyond the cut, seen face on; then the cut parts, shaded.
    (bx0, bz0), (bx1, bz1) = sv.pt(cup.y0, xwall.z0), sv.pt(cup.y1, xwall.z1)
    c.rect(bx0, bz0, bx1 - bx0, bz1 - bz0, weight=style.W_THIN, colour=style.C_LINE)
    (lx0, lz0), (lx1, lz1) = sv.pt(cup.y0, cup.z0), sv.pt(cup.y1, cup.z1)
    c.rect(lx0, lz0, lx1 - lx0, lz1 - lz0, weight=style.W_OUTLINE, colour=style.C_LINE,
           fill=style.C_FILL_LIGHT)
    (wx0, wz0), (wx1, wz1) = sv.pt(ywall.y0, ywall.z0), sv.pt(ywall.y1, ywall.z1)
    c.rect(wx0, wz0, wx1 - wx0, wz1 - wz0, weight=style.W_OUTLINE, colour=style.C_LINE,
           fill=style.C_FILL_LIGHT)
    # The screw hole through the ledge and the plate's clearance hole, hidden.
    for r, z0, z1 in ((CUP_SCREW_HOLE / 2, cup.z0, cup.z1), (hole.dia / 2, -t_, 0.0)):
        for side in (-1, 1):
            hx = sv.x(hole.y + side * r)
            c.line(hx, sv.y(z0), hx, sv.y(z1), w=style.W_HIDDEN, colour=style.C_LINE,
                   dash=style.D_HIDDEN)
    # The foot on the ledge and the board on the foot, in place.
    (fx0, fz0), (fx1, fz1) = sv.pt(foot.y0, foot.z0), sv.pt(foot.y1, foot.z1)
    c.rect(fx0, fz0, fx1 - fx0, fz1 - fz0, weight=ADJACENT["w"], colour=ADJACENT["colour"],
           dash=ADJACENT["dash"])
    inner = ywall.y1 if y_face == ywall.y0 else ywall.y0
    by0, by1 = (inner, cup.y1 + 3.0) if y_face == ywall.y0 else (cup.y0 - 3.0, inner)
    (ax0, az0), (ax1, az1) = sv.pt(by0, board.z0), sv.pt(by1, board.z1)
    c.rect(ax0, az0, ax1 - ax0, az1 - az0, weight=ADJACENT["w"], colour=ADJACENT["colour"],
           dash=ADJACENT["dash"])
    # The heights: ledge and wall, from the plate's top face.
    ex = sv.x(cup.y1 + 3.0)
    dims.ordinate_chain(c, [(sv.y(cup.z1), f"{cup.z1:.2f}", sv.x(cup.y1)),
                            (sv.y(ywall.z1), f"{ywall.z1:.2f}", sv.x(cup.y1))],
                        ex, ex + 6.0, horizontal=False, zero_pos=sv.y(0.0), zero_from=ex,
                        zero_label="Z 0")


# ---------------------------------------------------------------------------
# the column
# ---------------------------------------------------------------------------

def _tables(sheet: Sheet, p: Plate) -> None:
    rows = [[h.label, f"{h.x:.2f}", f"{h.y:.2f}", f"{h.dia:.2f}", HOLE_FOR[h.kind]]
            for h in p.spec.holes]
    block = sheet.column_block(sheet.table_height("HOLES", len(rows)))
    sheet.table(block, "HOLES", ["HOLE", "X", "Y", "DIA", "FOR"], rows,
                ["start", "end", "end", "end", "start"])

    rows = []
    for name, z in p.levels:
        rows.append([name, " / ".join(f"{v:.2f}" for v in z) if isinstance(z, tuple) else f"{z:.2f}"])
    title = "HEIGHTS ABOVE THE PLATE'S TOP FACE, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["", "Z"], rows, ["start", "end"])

    rows = [[str(s.qty), s.what, s.holds] for s in p.standoffs]
    block = sheet.column_block(sheet.table_height("FASTENERS AND SPACERS", len(rows)))
    sheet.table(block, "FASTENERS AND SPACERS", ["QTY", "WHAT", "HOLDS"], rows,
                ["end", "start", "start"])

    if p.made:
        rows = [[name, str(qty), size] for name, qty, size, how in p.made]
        block = sheet.column_block(sheet.table_height("PARTS, PRINTED", len(rows)))
        sheet.table(block, "PARTS, PRINTED", ["PART", "QTY", "X x Y x Z mm"], rows,
                    ["start", "end", "end"])


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------

def render_baseplate(p: Plate, *, drawing_no: str, version: str,
                     sheet_size: str = SHEET) -> Sheet:
    sheet = Sheet(sheet_size, TitleBlock(
        title=p.title.upper(), subtitle=p.subtitle, drawing_no=drawing_no,
        rev="A", version=version, drawn_by="generated",
        scale=" / ".join([scale_text(1, 1 / SCALE), scale_text(DETAIL_SCALE, 1)]
                         + ([scale_text(CUP_SCALE, 1)] if p.made else [])),
        projection="first angle",
        material=f"{p.spec.outline.thickness:g} mm acrylic or alu",
        tolerance="edge +/-0.20   hole pos +/-0.10   Z summed +/-0.20"),
        notes_band_height=NO_BAND)
    sheet.draw_frame()
    c = sheet.canvas
    area = sheet.area
    o = p.spec.outline
    L, W = o.height, o.width
    s = SCALE
    zlo, zhi = _z_range(p)

    # The elevation, along the top; the plan under it, lined up.
    left = area.x + LEFT
    top = area.y1 - CAPTION
    elev = Side(left, top - zhi * s, s)
    _draw_side(sheet, p, elev, 0.0, L)
    _standoff_dims(sheet, p, elev)
    both = any(b.kind == "alt" for b in p.boxes)
    c.text(left, top + 3.0, f"ELEVATION FROM +X, {scale_text(1, 1 / s)}"
           + (" - POSITIONS A AND B COINCIDE" if both else ""),
           size=style.T_LABEL, bold=True)

    ptop = elev.y(zlo) - GAP - CAPTION
    plan = Plan(left, ptop, s)
    _draw_plan(sheet, p, plan)
    _plan_ordinates(sheet, p, plan)
    c.text(left + 8.0, ptop + 3.0, f"PLAN, {scale_text(1, 1 / s)}", size=style.T_LABEL,
           bold=True)

    # The detail of the joint, at the foot, marked out on the elevation.
    dy0, dy1 = _detail_range(p)
    dtop = ptop - W * s - PLAN_UNDER - CAPTION
    ds = DETAIL_SCALE
    detail = Side(left - dy0 * ds, dtop - NAME_LANE - zhi * ds, ds)
    _draw_side(sheet, p, detail, dy0, dy1)
    _detail_names(sheet, p, detail, dy0, dy1)
    _detail_ordinates(sheet, p, detail, dy0, dy1)
    c.text(left, dtop + 3.0, f"DETAIL A, THE JOINT, {scale_text(ds, 1)} - "
           "EVERYTHING IN THE BAND, NOTHING HIDDEN", size=style.T_LABEL, bold=True)
    (ax0, az0), (ax1, az1) = elev.pt(dy0, zlo + 1.0), elev.pt(dy1, zhi - 1.0)
    c.rect(ax0, az0, ax1 - ax0, az1 - az0, weight=style.W_THIN, colour=style.C_DIM,
           dash=style.D_HIDDEN)
    c.text(ax1 + 1.5, az1 - style.T_LABEL, "A", size=style.T_LABEL, colour=style.C_DIM,
           bold=True)

    _tables(sheet, p)
    draw_legend(sheet, _legend(p))

    # Notes: one column to the right of the views, the sheet's height.
    notes_x = elev.x(L) + RIGHT
    x1 = area.x1 - 2.0
    base = sheet.frame.y + 3.0
    if p.made:
        _cup_detail(sheet, p, area.x1 - 64.0, CUP_DETAIL_TOP - 8.0)
        base = CUP_DETAIL_TOP
    cols = [Rect(notes_x, base, x1 - notes_x, area.y1 - base)]
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "") for s in p.spec.sources]
    blocks = note_blocks(list(p.spec.notes), src)
    if not sheet.notes_columns(cols, blocks, dry=True):
        raise SystemExit(f"{drawing_no}: the notes do not fit beside the views")
    sheet.notes_columns(cols, blocks)
    sheet.draw_title_block()
    return sheet


def baseplate_name(p: Plate) -> str:
    return drawing_name("base-plates", p.key)
