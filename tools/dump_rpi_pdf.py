#!/usr/bin/env python3
"""Dump mechanical features from a 1:1 vector Raspberry Pi drawing PDF.

Raspberry Pi Ltd publish DXF drawings for some models but only PDF for others,
the Pi 5 among them.  Such a PDF is a vector drawing, so it is usable as CAD
data -- one PDF point is 1/72 inch -- provided its plot scale is recovered
rather than assumed, because some of these sheets are fit-to-page reductions.

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
    on the sheet and what scale the drawing was plotted at.  The Pi 5 sheet
    measures 1.00002 and is a true 1:1 plot; others published by the same
    company are fit-to-page reductions, so it is measured, never assumed.

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
    """Recover axis-aligned rectangles from a soup of straight segments.

    Two passes, because a connector outline may be closed in either direction:
    some are drawn as a pair of full-width horizontals with the vertical sides
    broken up by shell detail, others as a pair of full-height verticals with
    the horizontals broken up.  The Pi 5's micro-HDMI connectors are the second
    kind, and a horizontal-only pass misses them entirely.
    """
    horiz, vert = [], []
    for x0, y0, x1, y1 in segments:
        if abs(y1 - y0) < TOL and abs(x1 - x0) > TOL:
            horiz.append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
        elif abs(x1 - x0) < TOL and abs(y1 - y0) > TOL:
            vert.append((min(y0, y1), max(y0, y1), (x0 + x1) / 2))
    # Keep the raw segments as well as the merged ones.  Merging is what lets a
    # connector drawn as many short pieces close a rectangle at all, but it can
    # also swallow a genuine edge into a longer collinear run belonging to
    # something else, so both sets are offered to the matcher.
    horiz += _merge_collinear(horiz)
    vert += _merge_collinear(vert)

    rects = set()
    rects |= _pairs(horiz, vert, flip=False)
    rects |= {(a, b, c, d) for (b, a, d, c) in _pairs(vert, horiz, flip=True)}
    return sorted(rects)


def _merge_collinear(lines):
    """Join segments that lie on the same line and touch or overlap.

    A connector outline is often drawn as many short pieces, so the full-width
    edge only exists once they are joined.  Without this, the Pi 5's micro-HDMI
    connectors have no edge long enough to close a rectangle.
    """
    by_pos = defaultdict(list)
    for lo, hi, pos in lines:
        by_pos[round(pos / TOL)].append((lo, hi))
    out = []
    for key, spans in by_pos.items():
        pos = key * TOL
        spans.sort()
        cur_lo, cur_hi = spans[0]
        for lo, hi in spans[1:]:
            if lo <= cur_hi + TOL:
                cur_hi = max(cur_hi, hi)
            else:
                out.append((cur_lo, cur_hi, pos))
                cur_lo, cur_hi = lo, hi
        out.append((cur_lo, cur_hi, pos))
    return out


def _pairs(along, across, flip: bool):
    """Find rectangles from two parallel *along* lines closed by *across* ones.

    A side counts if a crossing segment spans the gap; it may run past it,
    because connector shells are drawn with tabs that overshoot the body.
    """
    by_span = defaultdict(list)
    for lo, hi, pos in along:
        by_span[(round(lo / TOL), round(hi / TOL))].append(pos)

    found = set()
    for (klo, khi), positions in by_span.items():
        if len(positions) < 2:
            continue
        lo, hi = klo * TOL, khi * TOL
        positions = sorted(positions)
        for i, p0 in enumerate(positions):
            for p1 in positions[i + 1:]:
                if p1 - p0 < TOL:
                    continue
                sides = sum(
                    1 for (va, vb, vx) in across
                    if va <= p0 + TOL and vb >= p1 - TOL
                    and (abs(vx - lo) < TOL or abs(vx - hi) < TOL))
                if sides >= 1:
                    found.add((lo, p0, hi, p1) if not flip else (p0, lo, p1, hi))
    return found


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
