#!/usr/bin/env python3
"""Read the Orange Pi PC's geometry out of other people's models of it.

Nothing here is used to draw the sheet.  These are the independent figures
the photogrammetry in ``measure_orangepi_pc.py`` is held against, every one
put into the sheet's frame -- lower-left corner of the board, component side
up, millimetres -- and printed for ``orangepi_pc.py`` to record and
``verify_orangepi_pc.py`` to compare:

* **Xunlong's Orange Pi PC Plus assembly drawing**, two AutoCAD 2000 DWGs in
  mils.  A different board -- the PC with eMMC and Wi-Fi added -- which a
  forum answer says is the same size, so a sibling and not a source: what it
  shows is what Xunlong drew for the connectors the two boards share.  Each
  part is found by its reference designator, as the box its body outline
  draws round the label.
* **Roman Gachin's Orange Pi PC model**, a 3MF of the board and its parts,
  sectioned through the board and above it.
* **landroo's Orange Pi PC case**, whose walls have one cut-out per
  connector; the STL is sectioned through each wall.
* **Seven more cases**, of which only the standoffs are read: the hole
  pattern is the one thing every case has to get right.

tools/fetch_orangepi_pc.sh fetches them.

Run: uv run --no-project --with numpy --with trimesh --with scipy \\
         --with networkx --with shapely --with ezdxf --with ezdwg \\
         --with libarchive-c python raspberry_pi/crosscheck_orangepi_pc.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "tmp" / "src" / "orangepi_pc" / "models"

MIL = 0.0254

#: The PC Plus parts the PC also has, by designator, under this repository's
#: feature keys.  CON1 is left out: its outline is the connector's latch
#: alone.
PC_PLUS_PARTS = {"header": "CON3", "ethernet": "CN3", "usb_a_1": "P1",
                 "usb_a_2": "USB1", "hdmi": "CON2", "power": "J1",
                 "audio": "J4", "usb_otg": "CN1", "button": "SW4", "ir": "U22",
                 "uart": "J3"}

#: Roughly where each part sits, board frame: the Gachin model's parts are
#: named by nothing, so a part is the section outline containing this point.
GACHIN_PARTS = {"ethernet": (80, 32), "usb_a_1": (80, 46), "usb_a_2": (80, 14),
                "hdmi": (38, 4), "power": (13, 4), "audio": (65, 5),
                "usb_otg": (2, 39), "button": (2, 10), "ir": (65, 54),
                "camera": (4, 24), "uart": (23, 2.9), "microsd": (6, 24)}


def pc_plus() -> dict:
    """Outline, holes, header and part outlines off the PC Plus drawing."""
    import ezdxf
    import ezdwg
    import libarchive

    out = {}
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
        cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp)
            libarchive.extract_file(str(MODELS / "xunlong-pc-plus-v1p1-drawing.rar"))
        finally:
            os.chdir(cwd)
        for side in ("TOP", "BOT"):
            dwg = next(Path(tmp).rglob(f"ASM{side}.dwg"))
            ezdwg.to_dxf(str(dwg), f"{tmp}/{side}.dxf")
            msp = ezdxf.readfile(f"{tmp}/{side}.dxf").modelspace()
            segs, texts, circles, outlines, polys = [], {}, [], [], []
            for e in msp.query("LWPOLYLINE"):
                pts = [(p[0] * MIL, p[1] * MIL) for p in e.get_points()]
                segs += list(zip(pts, pts[1:]))
                polys.append(pts)
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if abs(max(xs) - min(xs) - 85) < 0.1 and abs(max(ys) - min(ys) - 56) < 0.1:
                    outlines.append((min(ys), min(xs), max(xs) - min(xs), max(ys) - min(ys)))
            for e in msp.query("TEXT"):
                texts[e.dxf.text] = (e.dxf.insert[0] * MIL, e.dxf.insert[1] * MIL)
            for e in msp.query("CIRCLE"):
                circles.append((e.dxf.center.x * MIL, e.dxf.center.y * MIL,
                                2 * e.dxf.radius * MIL))
            if side == "TOP":
                # The drawing is of a two-up panel; the board is the lower of
                # the two 85 x 56 outlines, and its lower-left corner is the
                # origin.
                oy, ox, bw, bh = min(outlines)
                out["board"] = (round(bw, 3), round(bh, 3))
                out["holes"] = sorted((round(x - ox, 3), round(y - oy, 3), round(d, 3))
                                      for x, y, d in circles if abs(d - 5.0) < 0.01
                                      and 0 < x - ox < 85 and 0 < y - oy < 56)
            # A part is the largest outline drawn round its designator; the
            # network jack's is four loose lines, so failing an outline it is
            # the nearest line on each side, the board's own edges excepted.
            shift = [[(x - ox, y - oy) for x, y in pts] for pts in polys]
            lines = [(a, b) for pts in shift for a, b in zip(pts, pts[1:])
                     if not on_board_edge(a, b)]
            for key, ref in PC_PLUS_PARTS.items():
                if side == "TOP" and ref in texts:
                    out[key] = part_box(shift, lines, texts[ref][0] - ox,
                                        texts[ref][1] - oy)
            if side == "BOT":
                # The microSD socket carries no designator on this layer.  It
                # is drawn as its card lip and two long sides, which between
                # them give its extent.
                near = [p for pts in shift
                        if all(-1 < q[0] < 14 and 16 < q[1] < 32 for q in pts)
                        for p in pts]
                out["microsd"] = tuple(round(v, 2) for v in (
                    min(p[0] for p in near), min(p[1] for p in near),
                    max(p[0] for p in near), max(p[1] for p in near)))
    return out


def on_board_edge(a, b) -> bool:
    """Whether the segment a-b lies along the edge of the 85 x 56 board."""
    return any(abs(a[i] - v) < 0.01 and abs(b[i] - v) < 0.01
               for i, v in ((0, 0.0), (0, 85.0), (1, 0.0), (1, 56.0)))


def part_box(polys, lines, x: float, y: float):
    """The largest outline round (x, y) under 30 mm, else the lines round it."""
    boxes = []
    for pts in polys:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if len(pts) >= 4 and min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys) \
                and max(xs) - min(xs) < 30 and max(ys) - min(ys) < 30:
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
    if boxes:
        return tuple(round(v, 2) for v in max(
            boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])))
    return enclosing_box(lines, x, y)


def enclosing_box(segs, x: float, y: float):
    """The nearest drawn line on each side of (x, y) that spans it."""
    left, right, below, above = -1e9, 1e9, -1e9, 1e9
    for (ax, ay), (bx, by) in segs:
        if abs(ax - bx) < 1e-6 and min(ay, by) <= y <= max(ay, by):
            if ax < x:
                left = max(left, ax)
            else:
                right = min(right, ax)
        if abs(ay - by) < 1e-6 and min(ax, bx) <= x <= max(ax, bx):
            if ay < y:
                below = max(below, ay)
            else:
                above = min(above, ay)
    return tuple(round(v, 2) for v in (left, below, right, above))


def gachin() -> dict:
    """Holes, header and part boxes off Roman Gachin's 3MF.

    The model is centred on the origin with Y up out of the component side;
    the board is 85 mm along Z and 56 mm along X.  Turned so the header is
    along the top and the network jack on the right, board X = 42.5 - z and
    Y = 28 - x.  That is a rotation, not a mirror, which the DC jack being
    bottom left confirms.
    """
    import zipfile
    with zipfile.ZipFile(MODELS / "gachin-pipc.3mf") as z:
        text = z.read("3D/3dmodel.model").decode()
    V = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', text), float)
    T = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', text), int)
    mesh = trimesh.Trimesh(V, T, process=False)

    def boxes(height):
        sec = mesh.section(plane_origin=[0, height, 0], plane_normal=[0, 1, 0])
        for e in sec.entities:
            P = sec.vertices[e.points]
            yield (42.5 - P[:, 2].max(), 28 - P[:, 0].max(),
                   42.5 - P[:, 2].min(), 28 - P[:, 0].min())
    out = {}
    board = list(boxes(0.8))
    b = max(board, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    out["board"] = (b[2] - b[0], b[3] - b[1])
    out["holes"] = sorted((round((r[0] + r[2]) / 2 - b[0], 3),
                           round((r[1] + r[3]) / 2 - b[1], 3), round(r[2] - r[0], 3))
                          for r in board if r is not b)
    top, under = list(boxes(3.0)), list(boxes(-1.0))
    for key, (x, y) in GACHIN_PARTS.items():
        hits = [r for r in (under if key == "microsd" else top)
                if r[0] <= x <= r[2] and r[1] <= y <= r[3]]
        if hits:
            out[key] = tuple(round(v, 2) for v in min(
                hits, key=lambda r: (r[2] - r[0]) * (r[3] - r[1])))
    pins = sorted({round((r[0] + r[2]) / 2, 2) for r in boxes(5.0)
                   if r[2] - r[0] < 1 and r[1] > 45})
    rows = sorted({round((r[1] + r[3]) / 2, 2) for r in boxes(5.0)
                   if r[2] - r[0] < 1 and r[1] > 45})
    out["header"] = (pins[0], rows[0], (pins[-1] - pins[0]) / (len(pins) - 1),
                     rows[-1] - rows[0])
    return out


def load(name: str) -> trimesh.Trimesh:
    mesh = trimesh.load(MODELS / name, force="mesh")
    if mesh.extents.max() < 1:          # one of them is in metres
        mesh.apply_scale(1000)
    return mesh


def standoffs(name: str):
    """The pitch of the case's four standoff bores, long side first.

    Read at every height that sections four small circles of one size, which
    is where the bores are and the bosses round them are not.
    """
    mesh = load(name)
    lo, hi = mesh.bounds[:, 2]
    found = set()
    for z in np.linspace(lo, hi, 40)[1:-1]:
        sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        rings = []
        for e in sec.entities:
            P = sec.vertices[e.points][:, :2]
            d = np.ptp(P, 0)
            if 2.2 < d.mean() < 3.4 and abs(d[0] - d[1]) < 0.2:
                rings.append(P.mean(0))
        # Four bores, or eight where a lid's screws are the same size as the
        # board's: then the inner four and the outer four.
        c = np.array(rings)
        order = np.argsort(np.hypot(*(c - c.mean(0)).T)) if len(c) else []
        for group in ([order] if len(c) == 4 else
                      [order[:4], order[4:]] if len(c) == 8 else []):
            c4 = c[group]
            found.add(tuple(sorted((round(float(np.ptp(c4[:, 0])), 2),
                                    round(float(np.ptp(c4[:, 1])), 2)), reverse=True)))
    # A case with lid screws as well has two such patterns; the board's
    # standoffs are the inner one.
    return min(found) if found else None


def landroo() -> dict:
    """The landroo case's cut-outs, and its standoffs.

    Its SCAD models the board as an 86 x 57 box at the origin with the
    standoffs on an 80 x 50 rectangle 3 mm in from its corner; the cut-outs
    are put in the sheet's frame by moving that rectangle's centre onto the
    centre of the board's measured holes, which ``orangepi_pc.py`` does.
    """
    mesh = load("landroo-opipc.stl")
    walls = {"bottom": ([0, -2, 0], 0), "top": ([0, 59, 0], 0),
             "left": ([-2, 0, 0], 1), "right": ([90, 0, 0], 1)}
    out = {}
    for wall, (origin, axis) in walls.items():
        normal = [0, 1, 0] if axis == 0 else [1, 0, 0]
        sec = mesh.section(plane_origin=origin, plane_normal=normal)
        cuts = []
        for e in sec.entities:
            P = sec.vertices[e.points]
            span = (P[:, axis].min(), P[:, axis].max())
            zs = (P[:, 2].min(), P[:, 2].max())
            # Not the wall itself, and not the vent slots, which are 2 mm
            # wide and 10 mm tall.
            if span[1] - span[0] < 50 and not (abs(span[1] - span[0] - 2) < 0.1
                                              and zs[1] - zs[0] > 9):
                cuts.append(tuple(round(v, 2) for v in span))
        out[wall] = sorted(cuts)
    return out


def main() -> None:
    print("--- Xunlong, Orange Pi PC Plus assembly drawing ---")
    for k, v in pc_plus().items():
        print(f"  {k:9s} {v}")
    print("\n--- Roman Gachin, Orange Pi PC 3MF ---")
    for k, v in gachin().items():
        print(f"  {k:9s} {v}")
    print("\n--- landroo case, cut-outs by wall, in its own frame ---")
    for k, v in landroo().items():
        print(f"  {k:9s} {v}")
    print("\n--- standoff pattern of each case, X by Y ---")
    for f in sorted(MODELS.glob("*.stl")):
        s = standoffs(f.name)
        print(f"  {f.name:32s} " + (f"{s[0]:6.2f} x {s[1]:6.2f}" if s else "not found"))


if __name__ == "__main__":
    main()
