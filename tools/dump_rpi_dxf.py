#!/usr/bin/env python3
"""Dump the mechanical features of a Raspberry Pi DXF drawing.

Raspberry Pi Ltd publish layered DXF mechanical drawings for some models.  The
layers of interest are:

``BOARD_OUTLINE``  a single closed polyline, with bulge values on the corner
                   vertices for the corner radii
``0``              the mounting holes and their keep-out circles
``PARTS_TOP``      component body outlines
``SILK_TOP``       silkscreen, including the reference designators and the
                   connector legends ("ETHERNET", "USB3", "POWER IN", ...)

This script prints everything an operator needs in order to hand-identify which
outline is which connector.  The *numbers* come from the file; deciding what a
given rectangle *is* stays a human judgement, recorded in
``raspberry_pi/extract.py``.

Usage: dump_rpi_dxf.py <file.dxf> [min_area]
"""

import sys

import ezdxf


def outline(msp):
    for e in msp.query('LWPOLYLINE[layer=="BOARD_OUTLINE"]'):
        return [(p[0], p[1], p[4]) for p in e.get_points()], bool(e.closed)
    for e in msp.query('POLYLINE[layer=="BOARD_OUTLINE"]'):
        pts = [(v.dxf.location.x, v.dxf.location.y, getattr(v.dxf, "bulge", 0.0))
               for v in e.vertices]
        return pts, bool(e.is_closed)
    return [], False


def poly_points(e):
    if e.dxftype() == "LWPOLYLINE":
        return [(p[0], p[1]) for p in e.get_points("xy")]
    return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]


def main() -> None:
    path = sys.argv[1]
    min_area = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    print(f"### {path}")
    pts, closed = outline(msp)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    print(f"\n[BOARD_OUTLINE] closed={closed} vertices={len(pts)} "
          f"extent={max(xs) - min(xs):.3f} x {max(ys) - min(ys):.3f} mm "
          f"origin=({min(xs):.3f},{min(ys):.3f})")
    for x, y, bulge in pts:
        print(f"    {x:9.4f} {y:9.4f}  bulge={bulge:+.4f}")

    print("\n[HOLES] circles on layer 0")
    for e in sorted(msp.query('CIRCLE[layer=="0"]'),
                    key=lambda c: (c.dxf.center.x, c.dxf.center.y, c.dxf.radius)):
        c = e.dxf.center
        print(f"    centre=({c.x:8.4f},{c.y:8.4f})  dia={2 * e.dxf.radius:7.4f}")

    for layer in ("PARTS_TOP", "PARTS_BOTTOM"):
        rows = []
        for e in list(msp.query(f'LWPOLYLINE[layer=="{layer}"]')) + \
                 list(msp.query(f'POLYLINE[layer=="{layer}"]')):
            p = poly_points(e)
            if len(p) < 3:
                continue
            xs = [q[0] for q in p]
            ys = [q[1] for q in p]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if w * h >= min_area:
                rows.append((w * h, min(xs), min(ys), max(xs), max(ys), w, h, len(p)))
        rows.sort(reverse=True)
        print(f"\n[{layer}] outlines with bbox area >= {min_area} mm^2")
        print(f"    {'area':>9} {'x0':>9} {'y0':>9} {'x1':>9} {'y1':>9} "
              f"{'w':>8} {'h':>8}  pts")
        for r in rows:
            print(f"    {r[0]:9.2f} {r[1]:9.3f} {r[2]:9.3f} {r[3]:9.3f} {r[4]:9.3f} "
                  f"{r[5]:8.3f} {r[6]:8.3f}  {r[7]}")

    for layer in ("SILK_TOP", "SILK_BOTTOM"):
        texts = list(msp.query(f'TEXT[layer=="{layer}"]'))
        if not texts:
            continue
        print(f"\n[{layer}] text")
        for e in sorted(texts, key=lambda t: (-t.dxf.insert.y, t.dxf.insert.x)):
            print(f"    ({e.dxf.insert.x:8.3f},{e.dxf.insert.y:8.3f}) "
                  f"h={e.dxf.height:4.2f} rot={getattr(e.dxf, 'rotation', 0):6.1f}  "
                  f"{e.dxf.text!r}")


if __name__ == "__main__":
    main()
