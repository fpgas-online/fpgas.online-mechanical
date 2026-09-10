"""Minimal reader for KiCad ``.kicad_pcb`` files.

KiCad board files are plain s-expressions, so nothing more than a tokeniser and
a recursive assembler is needed to get at the geometry.  This avoids depending
on a KiCad installation or on ``kicad-cli``.

Coordinates in a ``.kicad_pcb`` are millimetres with **Y pointing down**.  Every
function here returns raw KiCad coordinates; flipping to a Y-up drawing frame is
the caller's job.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# s-expression parsing
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+')


def parse_sexpr(text: str) -> list:
    """Parse s-expression *text* into nested lists of str."""
    stack: list[list] = [[]]
    for tok in _TOKEN.finditer(text):
        t = tok.group(0)
        if t == "(":
            new: list = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(t)
    return stack[0][0]


def children(node: list, name: str) -> Iterable[list]:
    """Yield direct child nodes of *node* whose head atom is *name*."""
    for item in node[1:]:
        if isinstance(item, list) and item and item[0] == name:
            yield item


def child(node: list, name: str) -> list | None:
    for item in children(node, name):
        return item
    return None


def value(node: list, name: str, index: int = 1, default: Any = None) -> Any:
    """Return positional argument *index* of the first ``(name ...)`` child."""
    found = child(node, name)
    if found is None or len(found) <= index:
        return default
    return found[index]


def fvalue(node: list, name: str, index: int = 1, default: Any = None) -> Any:
    raw = value(node, name, index)
    return default if raw is None else float(raw)


# ---------------------------------------------------------------------------
# geometry records
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    """A straight edge segment, in KiCad coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Arc:
    """A three-point arc (start / mid / end), in KiCad coordinates."""

    x1: float
    y1: float
    xm: float
    ym: float
    x2: float
    y2: float

    def centre_radius(self) -> tuple[float, float, float]:
        """Return ``(cx, cy, r)`` for the circle through the three points."""
        ax, ay, bx, by, cx_, cy_ = self.x1, self.y1, self.xm, self.ym, self.x2, self.y2
        d = 2 * (ax * (by - cy_) + bx * (cy_ - ay) + cx_ * (ay - by))
        if abs(d) < 1e-12:  # collinear
            return (ax + cx_) / 2, (ay + cy_) / 2, math.hypot(cx_ - ax, cy_ - ay) / 2
        ux = ((ax**2 + ay**2) * (by - cy_) + (bx**2 + by**2) * (cy_ - ay)
              + (cx_**2 + cy_**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx_ - bx) + (bx**2 + by**2) * (ax - cx_)
              + (cx_**2 + cy_**2) * (bx - ax)) / d
        return ux, uy, math.hypot(ax - ux, ay - uy)


@dataclass
class Circle:
    cx: float
    cy: float
    r: float


@dataclass
class Pad:
    number: str
    type: str          # "thru_hole", "smd", "np_thru_hole", ...
    shape: str
    x: float           # absolute, KiCad coordinates
    y: float
    rot: float
    size: tuple[float, float]
    drill: float | None
    drill_size: tuple[float, float] | None
    layers: list[str]


@dataclass
class Footprint:
    library_id: str
    reference: str
    fp_value: str
    x: float
    y: float
    rot: float
    layer: str
    attrs: list[str]
    pads: list[Pad] = field(default_factory=list)
    courtyard: list[Segment] = field(default_factory=list)
    fab: list[Segment] = field(default_factory=list)

    @property
    def dnp(self) -> bool:
        return "dnp" in self.attrs

    def bbox(self, source: str = "courtyard") -> tuple[float, float, float, float] | None:
        """Axis-aligned bounding box of the courtyard or fab outline."""
        segs = self.courtyard if source == "courtyard" else self.fab
        if not segs:
            return None
        xs = [c for s in segs for c in (s.x1, s.x2)]
        ys = [c for s in segs for c in (s.y1, s.y2)]
        return min(xs), min(ys), max(xs), max(ys)

    def pad_bbox(self) -> tuple[float, float, float, float] | None:
        if not self.pads:
            return None
        xs = [c for p in self.pads for c in (p.x - p.size[0] / 2, p.x + p.size[0] / 2)]
        ys = [c for p in self.pads for c in (p.y - p.size[1] / 2, p.y + p.size[1] / 2)]
        return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------------------
# board
# ---------------------------------------------------------------------------


def _rotate(x: float, y: float, deg: float) -> tuple[float, float]:
    """Rotate a footprint-local offset into board coordinates.

    KiCad stores footprint rotation counter-clockwise in a Y-down frame, which
    works out to this sign convention for the local-to-board transform.
    """
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return x * ca - y * sa, x * sa + y * ca


class Board:
    def __init__(self, text: str) -> None:
        self.tree = parse_sexpr(text)
        tb = child(self.tree, "title_block") or []
        self.title = value(tb, "title", default="") if tb else ""
        self.rev = value(tb, "rev", default="") if tb else ""
        self.date = value(tb, "date", default="") if tb else ""
        self.company = value(tb, "company", default="") if tb else ""
        self.thickness = fvalue(child(self.tree, "general") or ["general"],
                                "thickness", default=None)
        self.footprints = [self._footprint(fp) for fp in children(self.tree, "footprint")]

    # -- board outline ------------------------------------------------------

    def edge_cuts(self) -> tuple[list[Segment], list[Arc], list[Circle]]:
        """Return the Edge.Cuts geometry as segments, arcs and circles."""
        segs: list[Segment] = []
        arcs: list[Arc] = []
        circles: list[Circle] = []
        for kind in ("gr_line", "gr_arc", "gr_rect", "gr_circle", "gr_poly"):
            for node in children(self.tree, kind):
                if value(node, "layer") != "Edge.Cuts":
                    continue
                start = child(node, "start")
                end = child(node, "end")
                if kind == "gr_line" and start and end:
                    segs.append(Segment(float(start[1]), float(start[2]),
                                        float(end[1]), float(end[2])))
                elif kind == "gr_rect" and start and end:
                    x1, y1, x2, y2 = (float(start[1]), float(start[2]),
                                      float(end[1]), float(end[2]))
                    segs += [Segment(x1, y1, x2, y1), Segment(x2, y1, x2, y2),
                             Segment(x2, y2, x1, y2), Segment(x1, y2, x1, y1)]
                elif kind == "gr_arc":
                    mid = child(node, "mid")
                    if start and mid and end:
                        arcs.append(Arc(float(start[1]), float(start[2]),
                                        float(mid[1]), float(mid[2]),
                                        float(end[1]), float(end[2])))
                elif kind == "gr_circle":
                    centre = child(node, "center")
                    if centre and end:
                        r = math.hypot(float(end[1]) - float(centre[1]),
                                       float(end[2]) - float(centre[2]))
                        circles.append(Circle(float(centre[1]), float(centre[2]), r))
                elif kind == "gr_poly":
                    pts = child(node, "pts")
                    if pts:
                        xy = [(float(p[1]), float(p[2])) for p in children(pts, "xy")]
                        for i in range(len(xy)):
                            (ax, ay), (bx, by) = xy[i], xy[(i + 1) % len(xy)]
                            segs.append(Segment(ax, ay, bx, by))
        return segs, arcs, circles

    def outline_bbox(self) -> tuple[float, float, float, float]:
        """Bounding box of the board outline, accounting for arc bulge."""
        segs, arcs, circles = self.edge_cuts()
        xs = [c for s in segs for c in (s.x1, s.x2)]
        ys = [c for s in segs for c in (s.y1, s.y2)]
        for a in arcs:
            xs += [a.x1, a.xm, a.x2]
            ys += [a.y1, a.ym, a.y2]
        for c in circles:
            xs += [c.cx - c.r, c.cx + c.r]
            ys += [c.cy - c.r, c.cy + c.r]
        return min(xs), min(ys), max(xs), max(ys)

    # -- footprints ---------------------------------------------------------

    def _footprint(self, node: list) -> Footprint:
        at = child(node, "at") or ["at", "0", "0"]
        fx, fy = float(at[1]), float(at[2])
        frot = float(at[3]) if len(at) > 3 else 0.0

        # KiCad 8/9 store the designator as (property "Reference" "J3"); KiCad
        # 6/7 store it as (fp_text reference "J3" ...).  Handle both so that
        # older board revisions parse.
        reference = fp_value = ""
        for prop in children(node, "property"):
            if len(prop) >= 3:
                if prop[1] == "Reference":
                    reference = prop[2]
                elif prop[1] == "Value":
                    fp_value = prop[2]
        for txt in children(node, "fp_text"):
            if len(txt) >= 3:
                if txt[1] == "reference" and not reference:
                    reference = txt[2]
                elif txt[1] == "value" and not fp_value:
                    fp_value = txt[2]

        attr = child(node, "attr")
        attrs = [a for a in (attr[1:] if attr else []) if isinstance(a, str)]

        fp = Footprint(
            library_id=node[1] if len(node) > 1 and isinstance(node[1], str) else "",
            reference=reference,
            fp_value=fp_value,
            x=fx, y=fy, rot=frot,
            layer=value(node, "layer", default="F.Cu"),
            attrs=attrs,
        )

        for pad in children(node, "pad"):
            pat = child(pad, "at") or ["at", "0", "0"]
            lx, ly = float(pat[1]), float(pat[2])
            prot = float(pat[3]) if len(pat) > 3 else 0.0
            dx, dy = _rotate(lx, ly, frot)
            size = child(pad, "size")
            drill = child(pad, "drill")
            drill_d = drill_size = None
            if drill:
                nums = [d for d in drill[1:] if isinstance(d, str)
                        and re.fullmatch(r"-?\d+(\.\d+)?", d)]
                if drill[1] == "oval" and len(nums) >= 2:
                    drill_size = (float(nums[0]), float(nums[1]))
                elif nums:
                    drill_d = float(nums[0])
            layers = child(pad, "layers")
            fp.pads.append(Pad(
                number=str(pad[1]), type=str(pad[2]), shape=str(pad[3]),
                x=fx + dx, y=fy + dy, rot=frot + prot,
                size=(float(size[1]), float(size[2])) if size else (0.0, 0.0),
                drill=drill_d, drill_size=drill_size,
                layers=[l for l in (layers[1:] if layers else []) if isinstance(l, str)],
            ))

        for kind, sink in (("fp_line", None), ("fp_rect", None)):
            for gnode in children(node, kind):
                layer = value(gnode, "layer")
                if layer not in ("F.CrtYd", "B.CrtYd", "F.Fab", "B.Fab"):
                    continue
                start, end = child(gnode, "start"), child(gnode, "end")
                if not (start and end):
                    continue
                x1, y1 = float(start[1]), float(start[2])
                x2, y2 = float(end[1]), float(end[2])
                pairs = [(x1, y1, x2, y2)]
                if kind == "fp_rect":
                    pairs = [(x1, y1, x2, y1), (x2, y1, x2, y2),
                             (x2, y2, x1, y2), (x1, y2, x1, y1)]
                for ax, ay, bx, by in pairs:
                    rax, ray = _rotate(ax, ay, frot)
                    rbx, rby = _rotate(bx, by, frot)
                    seg = Segment(fx + rax, fy + ray, fx + rbx, fy + rby)
                    (fp.courtyard if "CrtYd" in layer else fp.fab).append(seg)
        return fp

    def by_library(self, pattern: str) -> list[Footprint]:
        rx = re.compile(pattern, re.I)
        return [f for f in self.footprints if rx.search(f.library_id)]

    def by_reference(self, pattern: str) -> list[Footprint]:
        rx = re.compile(pattern, re.I)
        return [f for f in self.footprints if rx.fullmatch(f.reference)]


def load(path: str) -> Board:
    with open(path, encoding="utf-8") as handle:
        return Board(handle.read())
