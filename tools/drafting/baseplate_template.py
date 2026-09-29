"""Printable 1:1 drill templates for the base plates.

One A4 sheet per plate, at true size, in the mounting plate's manner
(``template_sheet.py``): scale bars on both axes, every hole at its drill
size with a punch cross, the plate's edge as a cut line, and the boards it
carries in phantom so the sheet is held the right way round.

Landscape, where the mounting plate's templates are portrait.  That plate
is 135 x 101 and stands on a portrait page with room for a schedule under
it; a base plate is 135 x 192, and on a portrait page the plate alone took
the height a header, two bars and the notes need.  Across the page it fits
with a column beside it, and the plate lies the way the assembly sheet's
plan lies, Y to the right and X down, so the two agree about which end is
the front.
"""

from __future__ import annotations

from base_plates.model import Plate
from base_plates.plates import PLATES
from tools.layout import bp_template_stem, drawing_name

from . import style
from .baseplate_sheet import Plan, _plan_names
from .board_sheet import Obstacles, outline_path
from .canvas import Canvas
from .plate_sheet import place_label
from .sheet import Rect, TitleBlock
from .template_sheet import (BAR_LEN, BAR_THICK, CROSS_OVER, PRINT_CMD, SAFE,
                             WARNING, TemplatePage, _fit_beside, drill_mark,
                             fit_size, scale_bar)

#: A4 across: 297 wide, 210 tall.
A4_LANDSCAPE = (297.0, 210.0)

#: Top and bottom margins.  The sides keep the mounting plate's SAFE, which
#: leaves room to tape the sheet down; top and bottom carry nothing to tape
#: over and the height is what this page is short of.  The printer's own
#: border is 4.32.
EDGE = 6.0

#: Between the plate and the column beside it.
GAP = 8.0

#: What the table calls each kind of hole.
DRILL_FOR = {"mp": "tap M4", "pi": "M2.5 clearance", "cup": "M3 clearance"}

TITLE = "DRILL TEMPLATE - {title}"


class LandscapePage(TemplatePage):
    """The mounting plate's bare page, turned on its side."""

    def __init__(self) -> None:
        self.w, self.h = A4_LANDSCAPE
        self.size_name = "A4L"
        self.canvas = Canvas(self.w, self.h)
        self.title = TitleBlock(title="")
        self.area = Rect(SAFE, EDGE, self.w - 2 * SAFE, self.h - 2 * EDGE)


def _stamp(drawing_no: str) -> str:
    return f"{drawing_no}    A4 LANDSCAPE    SCALE 1:1"


def _title(p: Plate) -> str:
    return TITLE.format(title=p.title.upper())


def _header_sizes(version: str) -> tuple[float, float]:
    """One pair of sizes for both templates, so they read as a pair."""
    area = LandscapePage().area
    tsizes, ssizes = [], []
    for key, p in PLATES.items():
        stamp = _stamp(drawing_name("base-plates", bp_template_stem(key)))
        avail = area.w - style.text_width(stamp, style.T_TINY) - 6.0
        tsizes.append(_fit_beside(key, _title(p), avail, stamp, face="sans", bold=True))
        avail = area.w - style.text_width(version, style.T_TINY) - 6.0
        ssizes.append(_fit_beside(key, p.subtitle, avail, version))
    # The subtitle is what the sheet was drawn from, not what it is: it
    # stays at the caption size however much room the line has.
    return min(tsizes), min(min(ssizes), style.T_TINY)


def _groups(p: Plate) -> list[tuple[str, list]]:
    """The holes by ID prefix, in data order: MP1-6, PI1-4; CUP, PIA, PIB."""
    out: list[tuple[str, list]] = []
    for h in p.spec.holes:
        prefix = h.label.rstrip("0123456789")
        if not out or out[-1][0] != prefix:
            out.append((prefix, []))
        out[-1][1].append(h)
    return out


def _table_rows(p: Plate) -> list[list[str]]:
    rows = []
    for prefix, holes in _groups(p):
        dias = {h.dia for h in holes}
        kinds = {h.kind for h in holes}
        if len(dias) != 1 or len(kinds) != 1:
            raise SystemExit(f"{p.key}: the {prefix} holes are not all one drill")
        rows.append([f"{holes[0].label}-{holes[-1].label}", f"{holes[0].dia:.2f}",
                     DRILL_FOR[holes[0].kind]])
    return rows


def _notes(p: Plate, sheet_name: str) -> list[str]:
    notes = [
        "Print at 100 % on A4 with scaling off. Never Fit to page:  " + PRINT_CMD,
        f"Measure both scale bars; if either is not {BAR_LEN:.1f} mm, reprint.",
        "Black is drilled: a circle is the hole at true size, its cross the punch "
        "centre, the heavy line the plate's edge. Grey dashed boxes are the boards, "
        "to hold the sheet the right way round; nothing is drilled to them.",
        "Tape it down printed side up, FRONT EDGE at the Pi's end, and punch every "
        "cross.",
    ]
    groups = _groups(p)
    tapped = [g for g, hs in groups if hs[0].kind == "mp"]
    clearance = [g for g, hs in groups if hs[0].kind != "mp"]
    if tapped:
        notes.append(f"{', '.join(tapped)}: drill and tap M4 through.")
    if clearance:
        notes.append(f"{', '.join(clearance)}: drill through, then countersink from "
                     "the other face; the screws come up from below.")
    if len(p.pi_positions) > 1:
        names = [label.split(':')[0] for label, _, _ in p.pi_positions]
        notes.append(f"PI{' and PI'.join(names)} are the two positions for the Pi, "
                     f"see {sheet_name}: drill one set, not both.")
    notes.append(f"With a mill or a DRO, work from the coordinates on {sheet_name} "
                 "instead.")
    return notes


def render_baseplate_template(p: Plate, *, drawing_no: str, version: str) -> LandscapePage:
    page = LandscapePage()
    c, area = page.canvas, page.area
    o = p.spec.outline
    L, W = o.height, o.width
    sheet_name = drawing_name("base-plates", p.key)

    # -- header, as the mounting plate's templates have it ------------------
    stamp = _stamp(drawing_no)
    tsize, ssize = _header_sizes(version)
    y = area.y1
    c.text(area.x, y - tsize, _title(p), size=tsize, face="sans", bold=True)
    c.text(area.x1, y - tsize, stamp, size=style.T_TINY, anchor="end")
    y -= tsize + 2.4
    c.text(area.x, y - ssize, p.subtitle, size=ssize)
    c.text(area.x1, y - ssize, version, size=style.T_TINY, anchor="end")
    y -= ssize + 3.0
    box_h = 9.0
    c.rect(area.x, y - box_h, area.w, box_h, weight=style.W_FRAME)
    # Capped at the size the portrait templates set it at: the wider page
    # would fit a rung larger, and the warning is not the sheet's subject.
    c.text(area.cx, y - box_h / 2, WARNING, size=min(fit_size(WARNING, area.w - 8.0), 7.0),
           anchor="middle", baseline="middle", face="sans", bold=True)
    y -= box_h + 3.0

    # -- the plate, at true size, Y across the page and X down -------------
    # The vertical bar and its caption take the left margin; the front-edge
    # callout stands between them and the plate.
    left = area.x + 16.0
    top = y - 2.0
    bottom = top - W
    v = Plan(left, top, 1.0)
    below = bottom - 5.0 - BAR_THICK - 1.2 - style.T_TINY - style.descender(style.T_TINY)
    if below < area.y:
        raise SystemExit(
            f"{drawing_no}: the plate and the bar under it need {area.y - below:.1f} mm "
            "more than the page has")
    _draw_template(c, page, p, v, Rect(left, bottom, L, W))
    page.view = v

    scale_bar(c, area.x + 4.0, bottom, vertical=True)
    c.text(area.x + 1.2, bottom + BAR_LEN / 2, f"measure: {BAR_LEN:.1f} mm",
           size=style.T_TINY, anchor="middle", rotate=90.0)
    bar_y = bottom - 5.0 - BAR_THICK
    scale_bar(c, left + (L - BAR_LEN) / 2, bar_y)
    c.text(left + L / 2, bar_y - 1.2 - style.T_TINY,
           f"measure: this bar is {BAR_LEN:.1f} mm overall", size=style.T_TINY,
           anchor="middle")

    # -- the column beside it: what to drill, then what to do ---------------
    col = Rect(left + L + GAP, area.y, area.x1 - (left + L + GAP), top - area.y)
    rows = _table_rows(p)
    notes = _notes(p, sheet_name)
    table_h = page.table_height("", len(rows))
    notes_h = page.notes_height(col.w, "BEFORE YOU DRILL", notes)
    need = page.HEADING_HEIGHT + table_h + 4.5 + notes_h
    if need > col.h:
        raise SystemExit(
            f"{drawing_no}: the column beside the plate holds {col.h:.1f} mm and the "
            f"table and notes need {need:.1f}. The page is fixed and the plate is "
            "1:1, so take it out of the notes.")
    cursor = page.heading(Rect(col.x, col.y1 - page.HEADING_HEIGHT, col.w,
                               page.HEADING_HEIGHT), "DRILL")
    page.table(Rect(col.x, cursor - table_h, col.w, table_h), "",
               ["HOLES", "DRILL", "FOR"], rows, ["start", "end", "start"])
    cursor -= table_h + 4.5
    page.notes(Rect(col.x, cursor - notes_h, col.w, notes_h), "BEFORE YOU DRILL", notes)
    return page


def _draw_template(c: Canvas, page, p: Plate, v: Plan, plate: Rect) -> None:
    """The 1:1 pattern: the boards in phantom, the edge, then what is drilled."""
    obstacles = Obstacles()
    # The boards, and the adapter, as the assembly sheet's plan draws them;
    # their names keep the hole IDs off them.
    for box in p.boxes:
        if box.kind not in ("adjacent", "alt") or box.label == "Rubber foot":
            continue
        if box.kind == "alt" and not (box.label == "Raspberry Pi"
                                      or box.label.startswith("ACC-")):
            continue
        (x0, y0), (x1, y1) = v.pt(box.x0, box.y0), v.pt(box.x1, box.y1)
        x0, x1, y0, y1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
        c.rect(x0, y0, x1 - x0, y1 - y0, weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash=style.D_HIDDEN if box.kind == "alt" else style.D_PHANTOM)
        m = 1.2
        for bx0, by0, bx1, by1 in ((x0 - m, y0 - m, x1 + m, y0 + m),
                                   (x1 - m, y0 - m, x1 + m, y1 + m),
                                   (x0 - m, y1 - m, x1 + m, y1 + m),
                                   (x0 - m, y0 - m, x0 + m, y1 + m)):
            obstacles.add_rect(bx0, by0, bx1, by1)
    for box in _plan_names(c, p, v):
        obstacles.add_rect(*box)

    # The plate's edge: the cut line.
    outline_path(c, v, p.spec, w=style.W_OUTLINE)
    # Just inside the edge, in the strip before the Pi's outline: outside it
    # the vertical bar's figures are, and this is the edge it names.
    front = "FRONT EDGE  -  the Pi's end"
    c.text(plate.x + 3.6, plate.y + plate.h / 2, front, size=style.T_LABEL, face="sans",
           bold=True, anchor="middle", rotate=90.0)
    fw = style.text_width(front, style.T_LABEL, face="sans", bold=True)
    obstacles.add_rect(plate.x + 0.6, plate.y + plate.h / 2 - fw / 2, plate.x + 4.2,
                       plate.y + plate.h / 2 + fw / 2, pad=1.0)

    # Everything drilled is black, and only black: one plane cannot
    # misregister against itself.
    anchors = [v.pt(h.x, h.y) for h in p.spec.holes]
    marks = []
    for h in p.spec.holes:
        r = drill_mark(c, v, h.x, h.y, h.dia, style.C_LINE)
        px, py = v.pt(h.x, h.y)
        obstacles.add_circle(px, py, r + CROSS_OVER)
        marks.append((px, py, r + CROSS_OVER, h.label))
    for px, py, clear, text in marks:
        others = [a for a in anchors if a != (px, py)]
        box = place_label(c, obstacles, (px, py), clear, text, style.C_LINE,
                          others=others, bounds=plate)
        obstacles.add_rect(*box, pad=0.6)
