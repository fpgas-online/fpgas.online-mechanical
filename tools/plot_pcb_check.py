#!/usr/bin/env python3
"""Throwaway sanity plot of an extracted .kicad_pcb.

Draws the board outline, every footprint courtyard and every pad, labelled with
its reference designator, so the extraction can be eyeballed against the
official board render.  This exists to catch transform mistakes -- in particular
the sign convention for footprint rotation, which silently mirrors parts.

Usage: plot_pcb_check.py <file.kicad_pcb> <out.svg>
"""

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import kicad_pcb  # noqa: E402

SCALE = 6  # px per mm
PAD = 12


def main() -> None:
    board = kicad_pcb.load(sys.argv[1])
    out = sys.argv[2]
    x0, y0, x1, y1 = board.outline_bbox()
    w, h = x1 - x0, y1 - y0

    def tx(x, y):
        # KiCad Y points down and SVG Y points down too, so no flip is needed:
        # the plot comes out the same way up as the official board renders.
        return (x - x0) * SCALE + PAD, (y - y0) * SCALE + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * SCALE + 2 * PAD}" '
             f'height="{h * SCALE + 2 * PAD}">',
             '<rect width="100%" height="100%" fill="white"/>']

    segs, arcs, circles = board.edge_cuts()
    for s in segs:
        a, b = tx(s.x1, s.y1), tx(s.x2, s.y2)
        parts.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" '
                     f'y2="{b[1]:.2f}" stroke="black" stroke-width="2"/>')
    for a in arcs:
        p1, pm, p2 = tx(a.x1, a.y1), tx(a.xm, a.ym), tx(a.x2, a.y2)
        _, _, r = a.centre_radius()
        parts.append(f'<path d="M {p1[0]:.2f} {p1[1]:.2f} A {r * SCALE:.2f} '
                     f'{r * SCALE:.2f} 0 0 0 {p2[0]:.2f} {p2[1]:.2f}" fill="none" '
                     f'stroke="black" stroke-width="2"/>')
        parts.append(f'<circle cx="{pm[0]:.2f}" cy="{pm[1]:.2f}" r="1" fill="red"/>')

    for fp in board.footprints:
        for s in fp.courtyard:
            a, b = tx(s.x1, s.y1), tx(s.x2, s.y2)
            parts.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" '
                         f'y2="{b[1]:.2f}" stroke="#c060c0" stroke-width="0.6"/>')
        for p in fp.pads:
            c = tx(p.x, p.y)
            colour = "#d08000" if p.type != "smd" else "#0080d0"
            parts.append(f'<rect x="{c[0] - p.size[0] * SCALE / 2:.2f}" '
                         f'y="{c[1] - p.size[1] * SCALE / 2:.2f}" '
                         f'width="{p.size[0] * SCALE:.2f}" height="{p.size[1] * SCALE:.2f}" '
                         f'fill="{colour}" opacity="0.55"/>')
        if fp.reference and fp.pads:
            c = tx(fp.x, fp.y)
            parts.append(f'<text x="{c[0]:.2f}" y="{c[1]:.2f}" font-size="7" '
                         f'fill="#008000">{fp.reference}</text>')
            parts.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="1.6" fill="#008000"/>')

    parts.append("</svg>")
    open(out, "w").write("\n".join(parts))
    print(f"wrote {out}  ({w:.2f} x {h:.2f} mm)")


if __name__ == "__main__":
    main()
