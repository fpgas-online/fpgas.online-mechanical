#!/usr/bin/env python3
"""Measure the drill template PDFs and prove they are true size.

Every other sheet in this set is read by a human who can see a scale label.
A drill template is used as a gauge: it is laid on the work and drilled
through, so an error of a percent does not look wrong, it just puts the holes
a couple of millimetres out.  Nothing about rendering an SVG guarantees that
the PDF beside it is 1:1 -- a different exporter, a viewBox change, a page
size in points rather than millimetres would all pass every other check here
and quietly ruin a workpiece.

So this reads the PDF back, finds each hole as a circle on the page, and
compares where it landed against the plate data that produced it.  It also
checks the printed scale bars really are 100 mm, and that nothing strays into
the 4.32 mm border the laser physically cannot print.

Run: uv run --no-project --with pdfplumber --with pillow \\
         python tools/check_drill_template.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from base_plates.plates import PLATES                                  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE                      # noqa: E402
from tools.layout import (DRILL_TEMPLATE_STEMS, FAMILY_DIRS,  # noqa: E402
                          bp_template_stem, drawing_name, rel)
from tools.drafting.baseplate_template import (  # noqa: E402
    render_baseplate_template)
from tools.drafting.template_sheet import (BAR_LEN, BAR_THICK,  # noqa: E402
                                           render_drill_template)

PT = 25.4 / 72.0

#: How far a hole centre on the page may sit from where the data puts it.
#: Inkscape writes coordinates to six figures, so this is slack for rounding
#: and for pdfplumber's bezier bounding box, not a real tolerance.
POS_TOL = 0.05

#: Overall length of a printed scale bar, and how exact it has to be.
BAR_TOL = 0.02

#: The largest unprintable border among the queues this is meant for.  Brother
#: reports media-*-margin-supported = 432 hundredths of a millimetre on every
#: A4 tray, and a template is worthless if a hole falls in that strip.
PRINTER_MARGIN = 4.32

#: Every drill template: what to call it, its PDF, how to render it again
#: (with the real drawing name, so a name that will not fit its header line
#: is a failure this check sees), and the holes it must print.  Taken from
#: the generator's own tables rather than written out again, so a renamed
#: sheet cannot leave this checking a file that no longer exists.
SHEETS = []
for _kind, _stem in DRILL_TEMPLATE_STEMS.items():
    _name = drawing_name("mounting-plate", _stem)
    SHEETS.append((
        _kind, FAMILY_DIRS["mounting-plate"] / f"{_stem}.pdf",
        lambda kind=_kind, name=_name: render_drill_template(kind, drawing_no=name,
                                                              version="-"),
        [h for h in PLATE.holes if _kind == "plate" or h.kind == "plate"]))
for _key, _plate in PLATES.items():
    _stem = bp_template_stem(_key)
    _name = drawing_name("base-plates", _stem)
    SHEETS.append((
        f"base plate {_key}", FAMILY_DIRS["base-plates"] / f"{_stem}.pdf",
        lambda plate=_plate, name=_name: render_baseplate_template(
            plate, drawing_no=name, version="-"),
        list(_plate.spec.holes)))


def circles(page, dia: float) -> list[tuple[float, float]]:
    """Centres, in page millimetres, of every circle of diameter *dia*.

    A circle survives the SVG-to-PDF trip as four beziers, whose bounding box
    is the circle: square, and exactly the diameter across.  Matching on that
    picks the holes out without picking up an O from the lettering, which at
    a 2.5 mm cap height is nothing like 3.4 mm wide.
    """
    out = []
    for cu in page.curves:
        w = (cu["x1"] - cu["x0"]) * PT
        h = (cu["y1"] - cu["y0"]) * PT
        if abs(w - dia) < 0.02 and abs(h - dia) < 0.02:
            out.append(((cu["x0"] + cu["x1"]) / 2 * PT,
                        (cu["y0"] + cu["y1"]) / 2 * PT))
    return out


def bar_runs(page, long_axis: str) -> list[float]:
    """Overall lengths of the alternating-block scale bars on the page."""
    blocks = []
    for r in page.rects:
        w = (r["x1"] - r["x0"]) * PT
        h = (r["y1"] - r["y0"]) * PT
        want = (10.0, BAR_THICK) if long_axis == "x" else (BAR_THICK, 10.0)
        if abs(w - want[0]) < 0.02 and abs(h - want[1]) < 0.02:
            blocks.append((r["x0"] * PT, r["x1"] * PT,
                           r["y0"] * PT, r["y1"] * PT))
    if not blocks:
        return []
    if long_axis == "x":
        return [max(b[1] for b in blocks) - min(b[0] for b in blocks)]
    return [max(b[3] for b in blocks) - min(b[2] for b in blocks)]


def check(kind: str, path: Path, render, wanted) -> list[str]:
    bad: list[str] = []
    page_obj = render()
    view = page_obj.view
    size = (page_obj.w, page_obj.h)

    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 1:
            return [f"{len(pdf.pages)} pages; a template is one sheet"]
        page = pdf.pages[0]
        w, h = page.width * PT, page.height * PT
        if abs(w - size[0]) > 0.01 or abs(h - size[1]) > 0.01:
            bad.append(f"page is {w:.3f} x {h:.3f} mm, not the "
                       f"{size[0]} x {size[1]} it was drawn as")

        for dia in sorted({h.dia for h in wanted}):
            expect = [h for h in wanted if h.dia == dia]
            found = circles(page, dia)
            if len(found) != len(expect):
                bad.append(f"{len(found)} circles of {dia} mm on the page, "
                           f"{len(expect)} in the data")
                continue
            for hole in expect:
                want = view.pt(hole.x, hole.y)
                near = min(found, key=lambda p: (p[0] - want[0]) ** 2
                           + (p[1] - want[1]) ** 2)
                off = max(abs(near[0] - want[0]), abs(near[1] - want[1]))
                if off > POS_TOL:
                    bad.append(
                        f"hole at plate ({hole.x}, {hole.y}) should print at "
                        f"({want[0]:.3f}, {want[1]:.3f}) mm but is at "
                        f"({near[0]:.3f}, {near[1]:.3f}), out by {off:.3f} mm")

        for axis, name in (("x", "horizontal"), ("y", "vertical")):
            runs = bar_runs(page, axis)
            if len(runs) != 1:
                bad.append(f"{len(runs)} {name} scale bars, expected 1")
                continue
            if abs(runs[0] - BAR_LEN) > BAR_TOL:
                bad.append(f"the {name} scale bar prints {runs[0]:.3f} mm, "
                           f"and it tells the reader it is {BAR_LEN}")

        for obj in page.objects.get("char", []) + page.curves + page.rects \
                + page.lines:
            # Every canvas lays a white rectangle over the whole page first,
            # which is not ink and is meant to reach the edges.
            if ((obj["x1"] - obj["x0"]) * PT >= size[0] - 0.01
                    and (obj["y1"] - obj["y0"]) * PT >= size[1] - 0.01):
                continue
            if (obj["x0"] * PT < PRINTER_MARGIN
                    or obj["x1"] * PT > size[0] - PRINTER_MARGIN
                    or obj["y0"] * PT < PRINTER_MARGIN
                    or obj["y1"] * PT > size[1] - PRINTER_MARGIN):
                bad.append(f"something reaches ({obj['x0'] * PT:.2f}, "
                           f"{obj['y0'] * PT:.2f}) mm, inside the "
                           f"{PRINTER_MARGIN} mm the printer cannot reach")
                break
    return bad


def main() -> int:
    total = 0
    for kind, path, render, wanted in SHEETS:
        if not path.exists():
            print(f"{kind}: {rel(path)} missing; run tools/generate_diagrams.py")
            total += 1
            continue
        problems = check(kind, path, render, wanted)
        total += len(problems)
        if problems:
            print(f"{kind}: {len(problems)} problem(s)")
            for line in problems[:10]:
                print(f"    {line}")
        else:
            print(f"{kind}: true size, bars measure {BAR_LEN} mm, "
                  "nothing in the unprintable border")
    print(f"\n{total} problem(s) across {len(SHEETS)} drill templates")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
