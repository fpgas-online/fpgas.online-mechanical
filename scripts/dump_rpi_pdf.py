#!/usr/bin/env python3
"""Dump mechanical features from a 1:1 vector Raspberry Pi drawing PDF.

Raspberry Pi Ltd publish DXF drawings for some models but only PDF for others
(Pi 5, Pi 3A+).  Those PDFs are 1:1 scale vector drawings, so they are usable as
CAD data: one PDF point is 1/72 inch and the drawing is true size on the sheet.

The board origin is recovered from the four mounting-hole circles, whose centres
are known to sit 3.5 mm in from the left, bottom and top edges with 58 x 49 mm
spacing on every Model B sized Raspberry Pi.  Everything is then reported in
board coordinates: X right from the left edge, Y up from the bottom edge.

Component bodies are drawn as four separate straight segments, so axis-aligned
rectangles are recovered by matching up horizontal and vertical segment pairs.

Usage: dump_rpi_pdf.py <file.pdf> [board_width_mm] [board_height_mm]
"""

import sys
from collections import defaultdict

import pdfplumber

MM = 72 / 25.4          # PDF points per millimetre
TOL = 0.12              # mm, tolerance for treating coordinates as coincident


def points_mm(page, obj):
    """Path points in page millimetres, Y measured up from the page bottom.

    pdfplumber reports path points as ``(x, top)``, i.e. Y increasing downwards
    from the top of the sheet, so it has to be flipped to get a conventional
    drawing frame.  Getting this wrong silently mirrors the whole board, which
    is easy to miss because the mounting hole pattern is symmetric.
    """
    return [(x / MM, (page.height - y) / MM) for (x, y) in (obj.get("pts") or [])]


def circles(page):
    """Return (cx, cy, dia) in page millimetres for closed round paths."""
    found = []
    for obj in page.curves:
        pts = points_mm(page, obj)
        if len(pts) < 5:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if w < 0.5 or abs(w - h) > 0.25:
            continue
        found.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (w + h) / 2))
    return found


def find_origin(page):
    """Locate the board origin and drawing scale from the mounting holes.

    Every Raspberry Pi from the Model B onwards places four mounting holes on a
    58 x 49 mm rectangle whose lower-left corner sits 3.5 mm in from the left
    and bottom edges.  Finding that rectangle pins down both where the board is
    on the sheet and what scale the drawing was plotted at -- the Pi 5 sheet is
    a true 1:1 plot, but the Pi 3A+ sheet is a fit-to-page reduction.

    Returns ``(ox, oy, scale)`` where ``scale`` multiplies sheet millimetres to
    give real millimetres.
    """
    cands = circles(page)
    best = None
    for cx, cy, _ in cands:
        for ox2, oy2, _ in cands:
            dx, dy = ox2 - cx, oy2 - cy
            if dx < 40 or dy < 35:
                continue
            sx, sy = 58.0 / dx, 49.0 / dy
            if abs(sx - sy) > 0.02 or not 0.5 < sx < 2.0:
                continue

            def near(x, y, tol=0.4):
                return any(abs(c[0] - x) < tol and abs(c[1] - y) < tol for c in cands)

            if near(cx + dx, cy) and near(cx, cy + dy):
                err = abs(sx - sy)
                if best is None or err < best[0]:
                    best = (err, cx, cy, (sx + sy) / 2)
    if best is None:
        raise SystemExit("could not find the 58 x 49 mm mounting hole pattern")
    _, cx, cy, scale = best
    return cx - 3.5 / scale, cy - 3.5 / scale, scale


def rectangles(segments):
    """Recover axis-aligned rectangles from a soup of straight segments."""
    horiz, vert = [], []
    for x0, y0, x1, y1 in segments:
        if abs(y1 - y0) < TOL and abs(x1 - x0) > TOL:
            horiz.append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
        elif abs(x1 - x0) < TOL and abs(y1 - y0) > TOL:
            vert.append((min(y0, y1), max(y0, y1), (x0 + x1) / 2))

    by_span = defaultdict(list)
    for xa, xb, y in horiz:
        by_span[(round(xa / TOL), round(xb / TOL))].append(y)

    rects = []
    for (ka, kb), ys in by_span.items():
        if len(ys) < 2:
            continue
        xa, xb = ka * TOL, kb * TOL
        ys = sorted(ys)
        for i, ylo in enumerate(ys):
            for yhi in ys[i + 1:]:
                if yhi - ylo < TOL:
                    continue
                # A side counts if a vertical segment at either end spans the
                # gap -- it may run past it, because connector shells are drawn
                # with mounting tabs that overshoot the body outline.
                sides = sum(
                    1 for (va, vb, vx) in vert
                    if va <= ylo + TOL and vb >= yhi - TOL
                    and (abs(vx - xa) < TOL or abs(vx - xb) < TOL)
                )
                if sides >= 1:
                    rects.append((xa, ylo, xb, yhi))
    return rects


def main() -> None:
    path = sys.argv[1]
    bw = float(sys.argv[2]) if len(sys.argv) > 2 else 85.0
    bh = float(sys.argv[3]) if len(sys.argv) > 3 else 56.0

    page = pdfplumber.open(path).pages[0]
    ox, oy, scale = find_origin(page)
    print(f"### {path}")
    print(f"board origin on sheet: ({ox:.3f}, {oy:.3f}) mm from page bottom-left")
    print(f"drawing scale: {scale:.5f} (sheet mm -> real mm); "
          f"{'1:1 plot' if abs(scale - 1) < 0.002 else 'REDUCED PLOT, precision is lower'}")
    print(f"assumed board size: {bw} x {bh} mm\n")

    print("[CIRCLES] in board coordinates")
    seen = set()
    for cx, cy, dia in sorted(circles(page), key=lambda c: -c[2]):
        bx, by, bd = (cx - ox) * scale, (cy - oy) * scale, dia * scale
        if not (-8 < bx < bw + 8 and -8 < by < bh + 8):
            continue
        key = (round(bx, 2), round(by, 2), round(bd, 2))
        if key in seen:
            continue
        seen.add(key)
        print(f"    centre=({bx:8.3f},{by:8.3f})  dia={bd:7.3f}")

    segments = []
    for obj in page.lines + page.curves:
        pts = points_mm(page, obj)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            p0 = ((ax - ox) * scale, (ay - oy) * scale)
            p1 = ((bx - ox) * scale, (by - oy) * scale)
            if all(-10 < p[0] < bw + 10 and -10 < p[1] < bh + 10 for p in (p0, p1)):
                segments.append((p0[0], p0[1], p1[0], p1[1]))

    rects = rectangles(segments)
    rects.sort(key=lambda r: -((r[2] - r[0]) * (r[3] - r[1])))
    print(f"\n[RECTANGLES] {len(rects)} found, largest first")
    print(f"    {'area':>9} {'x0':>9} {'y0':>9} {'x1':>9} {'y1':>9} {'w':>8} {'h':>8}")
    for x0, y0, x1, y1 in rects:
        area = (x1 - x0) * (y1 - y0)
        if area < 8:
            continue
        print(f"    {area:9.2f} {x0:9.3f} {y0:9.3f} {x1:9.3f} {y1:9.3f} "
              f"{x1 - x0:8.3f} {y1 - y0:8.3f}")

    words = page.extract_words() if page.chars else []
    if words:
        print("\n[TEXT] in board coordinates")
        for w in words:
            bx = (w["x0"] / MM - ox) * scale
            by = ((page.height - w["bottom"]) / MM - oy) * scale
            print(f"    ({bx:9.3f},{by:9.3f})  {w['text']!r}")


if __name__ == "__main__":
    main()
