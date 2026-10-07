#!/usr/bin/env python3
"""Pictures of the sheets for the documentation site, for light and dark.

The docs site (fpgas.online-docs, Sphinx with the Furo theme) shows a sheet
twice over: its views on the page about the board, and the whole sheet
behind a "full drawing" link.  Furo has a light and a dark theme and shows an
image classed ``only-light`` in one and ``only-dark`` in the other, so each
picture is written twice.  A sheet is drafted black on white, and a white A3
in the middle of a dark page is a defect, not a style.

For each sheet listed in ``DOCS_SHEETS`` this writes, into ``docs/`` beside
the sheet::

    <stem>-views-light.svg  .png    the views, for the board's page
    <stem>-views-dark.svg   .png
    <stem>-sheet-light.svg  .png    the whole sheet, for "full drawing"
    <stem>-sheet-dark.svg   .png

Both kinds have a transparent ground: no page rectangle, so the picture sits
on whatever the theme paints.  The light one is the drawing as drafted.  The
dark one is the same drawing with every colour swapped through ``PALETTE``
in ``tools/docs_palette.py``, which says what each becomes and why.  The
swap is strict: a colour not in the map, a colour written any other way
than ``#rrggbb``, an opacity, a style attribute or any element or attribute
the reader there does not know to be colourless stops the build rather than
passing through unswapped, because a colour that slips through is black on
a black page and nothing else would notice.

The views are not one crop.  A renderer that wants its sheet in the docs
sets ``Sheet.docs_panels``: rectangles of its own layout, each with what it
holds, and they are stacked top to bottom in that order.  Which panels is the
renderer's choice, for what the page about the board is for.  On the camera
position sheets it is the elevations, the plan, the notes beside the plan, the
heights table, then the legend; on the Tiny Tapeout mounting plate, for a
builder fitting a board and not whoever cuts it, the plan, the legend, the
table of which board revisions use each hole, then the notes a column to a
panel.  Each is a panel of its own so
that the picture is no wider than its widest panel, which sets how large its
text prints across a page.  An element is in a panel or out of it: one that a
panel's edge cuts through stops the build, so a layout change that moves
something under an edge is caught rather than shipped half drawn.  Panels may
overlap, as the plan's reaches out under the notes beside it to take in its
leader's text; an element wholly in several belongs to the last of them, and
one wholly in any panel is not cut by another.

What it is written from is the sheet's SVG on disk, the one `make diagrams`
has just written.  ``tools/check_docs_images.py`` holds the committed
pictures against a fresh run over the committed SVG, the way
``check_pdfs.py`` holds the PDFs, so the pictures carry the VERSION stamp of
the sheet they were made from and are committed with it.

A sheet in ``SHEET_PNG_ONLY`` has its whole-sheet pictures as PNG only, one
in ``VIEW_GROUPS`` has its views as more than one picture, and one in
``EXTRA_VIEWS`` has further pictures of some of its panels, chosen by label.

Some pictures are of no sheet: a drawing made for the docs alone, such as
where pin 1 is on a Pmod socket, which no A3 sheet has a view of.  A module
in ``PICTURE_MODULES`` draws them, each on a ``Canvas`` of its own size, and
they are written here as ``<stem>-light`` and ``<stem>-dark``, SVG and PNG,
through the same reader and palette as a whole sheet, with nothing cut out
of them.  Having no panels to take their measure from, they are held to two
rules a sheet's pictures get from ``check_sheets.py`` instead: no text under
2.5 mm when the picture is printed ``PRINT_WIDTH_MM`` wide, and no two
pieces of text overprinting.  ``tools/check_docs_images.py`` holds them to
what their module draws, byte for byte, as it does a sheet's.

To add a sheet: give its renderer ``sheet.docs_panels``, add its SVG to
``DOCS_SHEETS``, run `make diagrams`, look at all four PNGs on their grounds,
and if it uses a colour ``PALETTE`` has not met, add the colour with its
reason.

Run: uv run --no-project --with pillow --with pypdf python tools/docs_images.py
"""

from __future__ import annotations

import importlib
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_sheets import OVERLAP_TOL, boxes, overlap  # noqa: E402
from tools.docs_palette import (SVG_OPEN, Drawing, Element,  # noqa: E402
                                palette_problems, read, recolour)
from tools.drafting import style  # noqa: E402
from tools.drafting.sheet import Rect  # noqa: E402
from tools.layout import docs_dir_for, rel  # noqa: E402

#: The sheets pictured for the docs, by their SVG.  Each one's renderer must
#: set ``docs_panels``.
DOCS_SHEETS = (
    "raspberry_pi_camera/output/over-acorn-cle-215-plus.svg",
    "raspberry_pi_camera/output/over-tt-mounting-plate.svg",
    "tinytapeout/mounting_plate/output/tt-generic-mounting-plate.svg",
    "tinytapeout/mounting_plate/output/"
    "tt-generic-mounting-plate-fitting-guide.svg",
)

#: Sheets whose whole-sheet pictures are written as PNG only, with no SVG.
#: The plate's whole-sheet SVG is about 490 lines, the fitting guide's
#: about 550 and the camera over the plate's about 420, each over the
#: commit-size hook's 400 added lines, and a picture that cannot be
#: committed cannot be checked, so the docs link the sheet's own PDF for the
#: zoomable full drawing and the PNG here is its preview.  Question mech-01
#: to Tim is open; when it is answered this can go.  The views are SVG and
#: PNG as for any sheet.
SHEET_PNG_ONLY = frozenset({
    "raspberry_pi_camera/output/over-tt-mounting-plate.svg",
    "tinytapeout/mounting_plate/output/tt-generic-mounting-plate.svg",
    "tinytapeout/mounting_plate/output/"
    "tt-generic-mounting-plate-fitting-guide.svg",
})

#: The views are stacked with this much paper between panels and round the
#: outside, in sheet millimetres.
PANEL_GAP = 6.0
MARGIN = 1.0

#: The least width of every PNG, in pixels, and what that is for: legible on
#: a high-density screen at the docs' column width, and at least 300 dpi
#: when the picture is printed across an A4 page less 15 mm margins.  The dpi
#: is chosen per picture from its width so that the narrower views get more
#: of it than the whole sheet does.
MIN_PX = 2400
PRINT_WIDTH_MM = 180.0

#: Sheets whose views are more than one picture, by SVG stem: each group's
#: name and how many of the sheet's ``docs_panels`` it takes, in order, None
#: for all the rest.  A picture is committed as one file, and the commit-size
#: hook allows 400 added lines to a commit, so views that make an SVG of more
#: lines than that are two pictures, ``<stem>-views-a`` and ``-views-b``,
#: each its own run of panels, and the page shows them one after the other.
#: The fitting guide's: the board revisions on the plate and the legend, then
#: the tables and the notes.  The camera over the plate's: the elevations, the
#: plan, the first notes, the tables and the legend, then the notes that run
#: on and the sources; one picture of them is over two and a half A4 pages
#: printed across 180 mm.
VIEW_GROUPS = {
    "over-tt-mounting-plate": (("a", 5), ("b", None)),
    "tt-generic-mounting-plate-fitting-guide": (("a", 4), ("b", None)),
}


def view_groups(stem: str) -> list[tuple[str, slice]]:
    """The views pictures of the sheet with SVG stem *stem*, each
    with the slice of its ``docs_panels`` it is made from."""
    groups = VIEW_GROUPS.get(stem)
    if groups is None:
        return [("views", slice(None))]
    out, start = [], 0
    for name, count in groups:
        end = None if count is None else start + count
        out.append((f"views-{name}", slice(start, end)))
        start = end
    return out


#: Extra pictures drawn from some of a sheet's ``docs_panels``, by SVG stem:
#: each one's name and the labels of the panels it takes, stacked in the order
#: given.  A picture is ``<stem>-<name>-<theme>``.  Labels are the text each
#: panel is set with in the renderer, not positions, so a reordered layout
#: keeps the picture and a renamed or missing panel stops the build.  Each
#: label must match exactly one of the sheet's panels.  The fitting guide's
#: ``v3``: the two version 3 boards on the plate and the legend, for the step
#: of the fitting page that puts a version 3 demo board on the plate, where
#: ``-views-a`` is too much of the page.
EXTRA_VIEWS = {
    "tt-generic-mounting-plate-fitting-guide": (
        ("v3", ("DB ETR v3.2 and v3.3 on the plate", "the legend")),
    ),
}


def extra_views(stem: str) -> dict[str, tuple[str, ...]]:
    """The extra pictures of the sheet with SVG stem *stem*, by name, each
    with the labels of the panels it is made from."""
    return dict(EXTRA_VIEWS.get(stem, ()))


def extra_panels(stem: str, name: str,
                 panels: list[tuple[Rect, str]]) -> list[tuple[Rect, str]]:
    """The panels of *panels* that extra picture *name* of *stem* takes, in
    the order of its labels; a label not matching exactly one panel stops the
    build."""
    out = []
    for label in extra_views(stem)[name]:
        hits = [p for p in panels if p[1] == label]
        if len(hits) != 1:
            raise SystemExit(f"{stem}: extra picture {name!r} takes the "
                             f"panel {label!r}, and {len(hits)} of the "
                             "sheet's docs_panels have that label")
        out.append(hits[0])
    return out


THEMES = ("light", "dark")

#: The modules that draw pictures of no sheet.  Each has ``PICTURES``: where
#: each picture is written, repository-relative and less its ``-light`` or
#: ``-dark``, and the function that draws it, returning a ``Canvas``.
PICTURE_MODULES = ("tinytapeout.pmod_pin1.draw",)


# ---------------------------------------------------------------------------
# which panel an element is in
# ---------------------------------------------------------------------------

#: An element's ink, in SVG coordinates (Y down): ("box", x0, y0, x1, y1) for
#: an area, ("seg", x0, y0, x1, y1) for a stroke.  A shape with no fill is
#: its sides, so a frame round a panel is not "in" it.
def ink(el: Element) -> list[tuple]:
    a = {k: v for k, v in el.attrs.items()}
    half = float(a.get("stroke-width", 0)) / 2
    filled = a.get("fill", "none") != "none"

    def fl(k):
        return float(a[k])

    def sides(pts, closed):
        segs = list(zip(pts, pts[1:] + (pts[:1] if closed else [])))
        return [("seg", *p, *q, half) for p, q in segs]

    def box(xs, ys, pad):
        return [("box", min(xs) - pad, min(ys) - pad, max(xs) + pad,
                 max(ys) + pad, 0.0)]

    if el.tag == "line":
        return [("seg", fl("x1"), fl("y1"), fl("x2"), fl("y2"), half)]
    if el.tag == "rect":
        x, y, w, h = fl("x"), fl("y"), fl("width"), fl("height")
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        return (box([x, x + w], [y, y + h], half) if filled
                else sides(pts, True))
    if el.tag == "circle":
        r = fl("r") + half
        return box([fl("cx")], [fl("cy")], r)
    if el.tag in ("polygon", "polyline"):
        pts = [tuple(float(v) for v in p.split(","))
               for p in a["points"].split()]
        if filled:
            return box([p[0] for p in pts], [p[1] for p in pts], half)
        return sides(pts, el.tag == "polygon")
    if el.tag == "path":
        # M, L and A only, as the canvas writes them; an arc bulges at most
        # its radius off its chord, so its end points padded by that.
        toks = re.findall(r"[MLAZ]|[-\d.]+", a["d"])
        xs, ys, pad, i = [], [], half, 0
        while i < len(toks):
            t = toks[i]
            if t in ("M", "L"):
                xs.append(float(toks[i + 1]))
                ys.append(float(toks[i + 2]))
                i += 3
            elif t == "A":
                pad = max(pad, float(toks[i + 1]) + half)
                xs.append(float(toks[i + 6]))
                ys.append(float(toks[i + 7]))
                i += 8
            elif t == "Z":
                i += 1
            else:
                raise SystemExit(f"path {a['d']!r}: {t!r} is not M, L, A "
                                 "or Z")
        return box(xs, ys, pad)
    if el.tag == "text":
        got = boxes(el.line)
        if not got:
            return []
        x0, y0, x1, y1 = got[0][:4]
        return [("box", x0, y0, x1, y1, 0.0)]
    raise AssertionError(el.tag)


def _seg_hits(x0, y0, x1, y1, r) -> bool:
    """Does the segment touch rectangle *r* (left, top, right, bottom)?"""
    t0, t1 = 0.0, 1.0
    dx, dy = x1 - x0, y1 - y0
    for p, q in ((-dx, x0 - r[0]), (dx, r[2] - x0),
                 (-dy, y0 - r[1]), (dy, r[3] - y0)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


#: Slack on "inside" and "clear of", in millimetres: for floating point, so
#: that text whose box touches a panel's edge is on the side it was laid out
#: on.
EPS = 0.005


def where(el: Element, panel: tuple[float, float, float, float]) -> str:
    """"in", "out" or "cut": where *el*'s ink lies against *panel*."""
    inside = outside = True
    for kind, x0, y0, x1, y1, pad in ink(el):
        if kind == "box":
            within = (x0 >= panel[0] - EPS and y0 >= panel[1] - EPS
                      and x1 <= panel[2] + EPS and y1 <= panel[3] + EPS)
            clear = (x1 <= panel[0] + EPS or x0 >= panel[2] - EPS
                     or y1 <= panel[1] + EPS or y0 >= panel[3] - EPS)
        else:
            grown = (panel[0] - pad + EPS, panel[1] - pad + EPS,
                     panel[2] + pad - EPS, panel[3] + pad - EPS)
            shrunk = (panel[0] + pad - EPS, panel[1] + pad - EPS,
                      panel[2] - pad + EPS, panel[3] - pad + EPS)
            within = all(shrunk[0] <= x <= shrunk[2]
                         and shrunk[1] <= y <= shrunk[3]
                         for x, y in ((x0, y0), (x1, y1)))
            clear = not _seg_hits(x0, y0, x1, y1, grown)
        inside &= within
        outside &= clear
    if inside:
        return "in"
    return "out" if outside else "cut"


# ---------------------------------------------------------------------------
# writing the pictures
# ---------------------------------------------------------------------------

def _fmt(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _svg(head: str, w: float, h: float, body: list[str]) -> str:
    return (f"{head}\n"
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'width="{_fmt(w)}mm" height="{_fmt(h)}mm" '
            f'viewBox="0 0 {_fmt(w)} {_fmt(h)}">\n'
            + "".join(line + "\n" for line in body) + "</svg>\n")


def sheet_svg(d: Drawing, theme: str) -> str:
    """The whole sheet, less its page, in *theme*'s colours."""
    return _svg(d.head, d.width, d.height,
                [recolour(e.line, theme) for e in d.elements])


def views_svg(d: Drawing, panels: list[tuple[Rect, str]],
              furniture: list[str], theme: str,
              name: str) -> tuple[str, list[float]]:
    """The panels stacked top to bottom; and the cap heights of their text.

    Each panel's elements are those wholly inside it, moved to where the
    panel lands; an element a panel's edge cuts through is refused.  The
    sheet's *furniture* is in none of them.
    """
    furniture = set(furniture)
    missing = furniture - {e.line for e in d.elements}
    if missing:
        raise SystemExit(f"{name}: the frame the generator draws now is not "
                         "the one in this SVG, so it is not the drawing the "
                         "panels were laid out on; run make diagrams")
    body, caps, cuts = [], [], []
    spans = [(d.height - r.y1, d.height - r.y) for r, _ in panels]
    # Panels may overlap, as the plan's reaches under the notes beside it:
    # an element wholly in several belongs to the last of them.
    owner: dict[int, int] = {}
    cutting: dict[int, str] = {}
    for i, e in enumerate(d.elements):
        if e.line in furniture:
            continue
        for j, (rect, what) in enumerate(panels):
            got = where(e, (rect.x, spans[j][0], rect.x1, spans[j][1]))
            if got == "in":
                owner[i] = j
            elif got == "cut":
                cutting[i] = what
    cuts = [f"{what}: {d.elements[i].line[:110]}"
            for i, what in cutting.items() if i not in owner]
    y = MARGIN
    width = 0.0
    for j, (rect, what) in enumerate(panels):
        # Sheet millimetres are Y up, the SVG's are Y down.
        box = (rect.x, spans[j][0], rect.x1, spans[j][1])
        body.append(f'<g transform="translate({_fmt(MARGIN - box[0])} '
                    f'{_fmt(y - box[1])})">')
        for i, e in enumerate(d.elements):
            if owner.get(i) == j:
                body.append(recolour(e.line, theme))
                if e.tag == "text":
                    caps.extend(b[5] for b in boxes(e.line))
        body.append("</g>")
        y += rect.h + PANEL_GAP
        width = max(width, rect.w)
    if cuts:
        raise SystemExit(f"{name}: a docs panel's edge cuts through what is "
                         "drawn; move the panel in the renderer's "
                         "docs_panels, or the drawing:\n  "
                         + "\n  ".join(cuts))
    return (_svg(d.head, width + 2 * MARGIN, y - PANEL_GAP + MARGIN, body),
            caps)


def dpi_for(width_mm: float) -> int:
    """The least whole dpi that makes a picture *width_mm* wide MIN_PX."""
    return math.ceil(MIN_PX * 25.4 / width_mm)


def to_png(svg: Path, dpi: int) -> Path:
    """Render *svg* with nothing behind it: the ground is the theme's."""
    out = svg.with_suffix(".png")
    subprocess.run(["inkscape", "--export-type=png", f"--export-dpi={dpi}",
                    "--export-background-opacity=0",
                    f"--export-filename={out}", str(svg)],
                   check=True, capture_output=True)
    return out


def outputs(svg: Path, out_dir: Path) -> dict[tuple[str, str], Path]:
    """Where each picture of *svg* goes: by (kind, theme), the SVG's path."""
    kinds = ([k for k, _ in view_groups(svg.stem)]
             + list(extra_views(svg.stem)) + ["sheet"])
    return {(k, t): out_dir / f"{svg.stem}-{k}-{t}.svg"
            for k in kinds for t in THEMES}


def kept(svg: Path, out_dir: Path, png_only: bool) -> list[Path]:
    """The files of *svg*'s pictures that are kept: every SVG and PNG, less
    the whole-sheet SVGs when *png_only*."""
    files = []
    for (kind, _), path in outputs(svg, out_dir).items():
        if not (png_only and kind == "sheet"):
            files.append(path)
        files.append(path.with_suffix(".png"))
    return files


def write(svg_text: str, svg: Path, panels: list[tuple[Rect, str]],
          furniture: list[str], out_dir: Path,
          png_only: bool = False) -> list[str]:
    """Every picture of one sheet into *out_dir*; returns what it says."""
    name = rel(svg) if svg.is_relative_to(ROOT) else str(svg)
    bad = palette_problems()
    if bad:
        raise SystemExit("PALETTE breaks its own rules:\n  "
                         + "\n  ".join(bad))
    if not panels:
        raise SystemExit(f"{name}: its renderer sets no docs_panels, so "
                         "there is nothing to say which part is the views")
    d = read(svg_text, name)
    out_dir.mkdir(parents=True, exist_ok=True)
    said = []
    for (kind, theme), path in outputs(svg, out_dir).items():
        if kind == "sheet":
            text, w = sheet_svg(d, theme), d.width
        else:
            if kind in extra_views(svg.stem):
                panels_here = extra_panels(svg.stem, kind, panels)
            else:
                panels_here = panels[dict(view_groups(svg.stem))[kind]]
            text, caps = views_svg(d, panels_here, furniture, theme, name)
            w = float(SVG_OPEN.search(text).group(1))
        path.write_text(text, encoding="utf-8")
        dpi = dpi_for(w)
        to_png(path, dpi)
        if png_only and kind == "sheet":
            path.unlink()
        if theme == "light":
            line = (f"{kind}: {w:.1f} mm wide at {dpi} dpi, "
                    f"{round(w / 25.4 * dpi)} px")
            if kind != "sheet":
                low = min(caps)
                line += ("; panels " + ", ".join(f"{r.w:.0f}"
                                                 for r, _ in panels_here)
                         + " mm wide")
                line += (f"; smallest text {low:.2f} mm capitals, "
                         f"{low * PRINT_WIDTH_MM / w:.2f} mm printed "
                         f"{PRINT_WIDTH_MM:.0f} mm wide")
            said.append(line)
    return said


def pictures() -> dict[str, object]:
    """Every picture of no sheet: its stem, and what draws it."""
    out: dict[str, object] = {}
    for module in PICTURE_MODULES:
        for stem, draw in importlib.import_module(module).PICTURES.items():
            if stem in out:
                raise SystemExit(f"{stem}: drawn by two modules")
            out[stem] = draw
    return out


def picture_files(stem: str, out_dir: Path) -> list[Path]:
    """The files the picture *stem* is written as, in *out_dir*."""
    name = Path(stem).name
    return [out_dir / f"{name}-{theme}.{kind}"
            for theme in THEMES for kind in ("svg", "png")]


def write_picture(svg_text: str, stem: str, out_dir: Path) -> str:
    """One picture of no sheet, both themes, into *out_dir*; returns what
    it says."""
    bad = palette_problems()
    if bad:
        raise SystemExit("PALETTE breaks its own rules:\n  "
                         + "\n  ".join(bad))
    d = read(svg_text, stem)
    text = boxes(svg_text)
    if not text:
        raise SystemExit(f"{stem}: the picture has no text; a picture of no "
                         "sheet without a label is a mistake")
    low = min(b[5] for b in text)
    printed = low * PRINT_WIDTH_MM / d.width
    problems = []
    if printed < style.T_MIN - 0.005:
        problems.append(f"its smallest text, {low:.2f} mm capitals, prints "
                        f"{printed:.2f} mm at {PRINT_WIDTH_MM:.0f} mm wide, "
                        f"under {style.T_MIN}")
    for i, a in enumerate(text):
        for b in text[i + 1:]:
            if overlap(a, b) > OVERLAP_TOL:
                problems.append(f"{a[4]!r} and {b[4]!r} overprint")
    if problems:
        raise SystemExit(f"{stem}: " + "; ".join(problems))
    out_dir.mkdir(parents=True, exist_ok=True)
    dpi = dpi_for(d.width)
    for theme in THEMES:
        path = out_dir / f"{Path(stem).name}-{theme}.svg"
        path.write_text(sheet_svg(d, theme), encoding="utf-8")
        to_png(path, dpi)
    return (f"{d.width:.1f} mm wide at {dpi} dpi, "
            f"{round(d.width / 25.4 * dpi)} px; smallest text {low:.2f} mm "
            f"capitals, {printed:.2f} mm printed {PRINT_WIDTH_MM:.0f} mm "
            "wide")


def panels_by_sheet() -> dict[str, tuple[list[tuple[Rect, str]],
                                         list[str]]]:
    """``docs_panels`` and ``furniture`` of each sheet in ``DOCS_SHEETS``,
    as the generator draws it."""
    from tools.generate_diagrams import draw_sheets

    want = {(ROOT / p).resolve(): p for p in DOCS_SHEETS}
    got = {}
    for sheet, path, _what in draw_sheets():
        key = want.get(Path(path).resolve())
        if key is not None:
            got[key] = (list(sheet.docs_panels), list(sheet.furniture))
    missing = sorted(set(DOCS_SHEETS) - set(got))
    if missing:
        raise SystemExit("DOCS_SHEETS names a sheet the generator does not "
                         "draw: " + ", ".join(missing))
    return got


def main() -> None:
    for path, (panels, furniture) in panels_by_sheet().items():
        svg = ROOT / path
        for line in write(svg.read_text(encoding="utf-8"), svg, panels,
                          furniture, docs_dir_for(svg),
                          path in SHEET_PNG_ONLY):
            print(f"  {path} {line}")
    for stem, draw in pictures().items():
        line = write_picture(draw().to_svg(), stem,
                             (ROOT / stem).parent)
        print(f"  {stem} {line}")


if __name__ == "__main__":
    main()
