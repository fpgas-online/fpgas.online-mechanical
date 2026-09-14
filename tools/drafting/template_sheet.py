"""Printable 1:1 drill templates for the generic mounting plate.

Two sheets, both A4 portrait at true size:

* the plate template drills the plate itself -- outline, every demo board
  fastener hole and slot, and the six plate fixings;
* the chassis template drills whatever the plate bolts onto -- the six M4
  fixings only, with the plate outline in phantom line to align it.

A drill template is not a drawing.  It is a gauge that happens to be made of
paper, so the only property that matters is that it leaves the printer at
exactly 1:1.  Nothing about a print dialog encourages that: the laser this was
written for advertises 4.32 mm hard margins and defaults to
``print-scaling=auto-fit``, which scales an A4 page by
min(201.36/210, 288.36/297) = 0.9588 and would move the far corner of this
hole pattern 5.6 mm.  So each sheet carries two printed scale bars, one per
axis, and tells the reader to measure them before touching a drill.  Two bars
rather than one because a laser fuser shrinks paper along the feed direction,
which scales the axes by different amounts and which a single bar cannot see.

Everything here is laid out from measured content heights rather than from
guessed constants, and the sheet refuses to render if the drawing no longer
fits.  A drill template that has quietly squeezed its own geometry is worse
than no drill template at all.
"""

from __future__ import annotations

import math

from tinytapeout.mounting_plate.plate import (PLACEMENTS, PMOD_BODY,
                                              PMOD_ROW_Y, PMOD_SLOT_X, PLATE)
from tools.schema import LABEL_SEP, Outline
from tinytapeout.boards import BOARDS as TT_BOARDS

from . import style
from .board_sheet import Obstacles
from .canvas import Canvas
from .plate_sheet import (BOARD_HOLE, PLATE_HOLE, REVISION_LETTER,
                          hole_ids, holes_by_version, place_label)
from .sheet import Rect, Sheet, TitleBlock
from .view import View

#: A4 the way it is actually fed: 210 wide, 297 tall.  ``style.SHEET_SIZES``
#: holds landscape sizes, which is right for every other sheet in the set and
#: wrong for a sheet that has to be held against a workpiece.
A4_PORTRAIT = (210.0, 297.0)

#: Page margin.  The printer's own unprintable border is 4.32 mm; ten leaves
#: room to tape the sheet down without covering a scale bar.
SAFE = 10.0

#: The scale bars, one per axis.  100 mm is long enough that a 1 % error is
#: a visible millimetre on a steel rule.
BAR_LEN = 100.0
BAR_THICK = 2.6

#: Each board revision's outline gets its own wash of colour so the five of
#: them can overlap and still be told apart.  Very pale on purpose: these are
#: not features, nothing is drilled to them, and they must never compete with
#: a hole centre.  They stay well clear of the hole and cut-line black so a
#: greyscale print loses the wash and keeps everything that gets drilled.
REVISION_TINT = {
    "DB mpw": "#f0cccc",
    "DB 4+": "#ccdcf0",
    "DB 06+": "#cfeacf",
    "DB ETR v3.2": "#f0e2c4",
    "DB ETR v3.3": "#e0cdf0",
}

#: The same hues at full strength, for legend text and swatch edges: a 2.5 mm
#: capital in the wash colour would fail the legibility floor.
REVISION_INK = {
    "DB mpw": "#993333",
    "DB 4+": "#33558c",
    "DB 06+": "#2f7a2f",
    "DB ETR v3.2": "#8a6a1f",
    "DB ETR v3.3": "#6a3d99",
}

#: Cross arm sticking out past the hole circle, for centre punching.
CROSS_OVER = 2.4


class TemplatePage(Sheet):
    """A bare page: no ISO frame, no zone markings, no title block.

    ``Sheet`` is inherited for its table and note machinery, which is pure
    canvas work, but none of its layout: its 165 mm annotation column and
    88 mm notes band would leave 45 mm of drawing area on a portrait A4.
    """

    def __init__(self) -> None:
        self.w, self.h = A4_PORTRAIT
        self.size_name = "A4P"
        self.canvas = Canvas(self.w, self.h)
        self.title = TitleBlock(title="")
        self.area = Rect(SAFE, SAFE, self.w - 2 * SAFE, self.h - 2 * SAFE)


# -- primitives -------------------------------------------------------------

def scale_bar(c: Canvas, x: float, y: float, *, vertical: bool = False) -> None:
    """A map-style bar of alternating 10 mm blocks, BAR_LEN long overall.

    A bar rather than a ruled scale because a ruler begs the question of
    whether to measure from the tick centre or its edge, and half a
    millimetre of doubt is half the error being looked for.  The block run
    has one unambiguous overall length.
    """
    for i in range(int(BAR_LEN // 10)):
        fill = "#000000" if i % 2 == 0 else "#ffffff"
        if vertical:
            c.rect(x, y + i * 10, BAR_THICK, 10.0,
                   weight=style.W_THIN, fill=fill)
        else:
            c.rect(x + i * 10, y, 10.0, BAR_THICK,
                   weight=style.W_THIN, fill=fill)
    for at in (0.0, 50.0, BAR_LEN):
        text = f"{at:g}"
        if vertical:
            c.text(x + BAR_THICK + 1.4, y + at, text, size=style.T_TINY,
                   anchor="start", baseline="middle")
        else:
            c.text(x + at, y + BAR_THICK + 1.6, text, size=style.T_TINY,
                   anchor="middle")


def drill_mark(c: Canvas, view: View, x: float, y: float, dia: float,
               colour: str) -> float:
    """A hole at true size with a punch cross through it; returns its radius."""
    px, py = view.pt(x, y)
    r = view.d(dia / 2)
    c.circle(px, py, r, w=style.W_OUTLINE, colour=colour, fill="#ffffff")
    arm = r + CROSS_OVER
    c.line(px - arm, py, px + arm, py, w=style.W_CENTRE, colour=colour)
    c.line(px, py - arm, px, py + arm, w=style.W_CENTRE, colour=colour)
    return r


def slot_mark(c: Canvas, view: View, sl, colour: str) -> None:
    """A slot at true size, with a punch cross at each end centre.

    Both ends are marked because a slot this short is made by drilling its
    two ends and taking out the web, not by plunging a cutter.
    """
    r = sl.width / 2
    dx, dy = sl.x1 - sl.x0, sl.y1 - sl.y0
    span = (dx * dx + dy * dy) ** 0.5
    ux, uy = (dx / span, dy / span) if span else (1.0, 0.0)
    nx, ny = -uy * r, ux * r
    a = view.pt(sl.x0 + nx, sl.y0 + ny)
    b = view.pt(sl.x1 + nx, sl.y1 + ny)
    d = view.pt(sl.x1 - nx, sl.y1 - ny)
    e = view.pt(sl.x0 - nx, sl.y0 - ny)
    rr = view.d(r)
    c.line(*a, *b, w=style.W_OUTLINE, colour=colour)
    c.line(*d, *e, w=style.W_OUTLINE, colour=colour)
    for (sx, sy), (ex, ey) in ((b, d), (e, a)):
        c.arc(sx, sy, ex, ey, rr, large=0, sweep=0,
              w=style.W_OUTLINE, colour=colour)
    for cx, cy in ((sl.x0, sl.y0), (sl.x1, sl.y1)):
        px, py = view.pt(cx, cy)
        arm = rr + CROSS_OVER
        c.line(px - arm, py, px + arm, py, w=style.W_CENTRE, colour=colour)
        c.line(px, py - arm, px, py + arm, w=style.W_CENTRE, colour=colour)


def offset_outline(c: Canvas, view: View, o: Outline, dx: float, dy: float,
                   colour: str, w: float) -> None:
    """A board profile shifted onto the plate, exact edge list when there is one."""
    if o.edges:
        for edge in o.edges:
            if edge[0] == "line":
                _, x1, y1, x2, y2 = edge
                c.line(*view.pt(x1 + dx, y1 + dy), *view.pt(x2 + dx, y2 + dy),
                       w=w, colour=colour)
            else:
                _, x1, y1, x2, y2, r, large, ccw = edge
                p1, p2 = view.pt(x1 + dx, y1 + dy), view.pt(x2 + dx, y2 + dy)
                c.arc(p1[0], p1[1], p2[0], p2[1], view.d(r), large=large,
                      sweep=ccw, w=w, colour=colour)
        return
    c.rect(*view.pt(dx, dy), view.d(o.width), view.d(o.height),
           weight=w, colour=colour, radius=view.d(o.corner_radius))


# -- content ----------------------------------------------------------------

def used_by(label: str) -> str:
    """Which board revisions a plate feature serves, from its own label."""
    if label == "PLATE":
        return "chassis fixing"
    groups: list[str] = []
    for part in label.split(LABEL_SEP):
        group = part.split(":")[0]
        if group not in groups:
            groups.append(group)
    return ", ".join(groups)


def schedule_rows(kind: str) -> list[list[str]]:
    """Every feature to be made, with the coordinates to make it from.

    The table is not decoration.  Paper is the least trustworthy gauge in any
    workshop, so the sheet carries the numbers that produced it: anyone with a
    mill, a DRO or a doubt about the print works from these instead.
    """
    labels, _, _ = hole_ids(PLATE)
    rows = []
    for i, h in enumerate(PLATE.holes):
        if kind == "chassis" and h.kind != "plate":
            continue
        rows.append([labels[i], f"{h.dia:.2f}", f"{h.x:.3f}", f"{h.y:.3f}",
                     used_by(h.label)])
    if kind == "plate":
        for n, sl in enumerate(PLATE.slots, 1):
            rows.append([f"S{n}", f"{sl.width:.2f}",
                         f"{sl.x0:.3f} / {sl.x1:.3f}",
                         f"{sl.y0:.3f} / {sl.y1:.3f}",
                         used_by(sl.label)])
    return rows


#: Blocks are laid out across the page, one revision each.  Five columns
#: because six blocks at four columns needs 51.0 mm of band and the sheet has
#: 50.6 mm; the sixth block shares a column with the fifth instead.
BLOCK_COLUMNS = 5
BLOCK_GUTTER = 6.0
BLOCK_GAP = 2.5

#: Marks a feature that more than one revision uses.
SHARED_MARK = "*"


def _feature_index() -> tuple[dict[str, str], set[str]]:
    """Every feature's drill size by ID, and which IDs two revisions share.

    Shared is read off the provenance labels rather than declared: a hole
    whose label names two revisions is one hole serving both, and the only
    way to get that wrong is to drill it twice.
    """
    labels, _, _ = hole_ids(PLATE)
    dia: dict[str, str] = {}
    shared: set[str] = set()
    for i, h in enumerate(PLATE.holes):
        dia[labels[i]] = f"{h.dia:.2f}"
        if h.kind != "plate" and "," in used_by(h.label):
            shared.add(labels[i])
    for n, sl in enumerate(PLATE.slots, 1):
        dia[f"S{n}"] = f"{sl.width:.2f}"
        if "," in used_by(sl.label):
            shared.add(f"S{n}")
    return dia, shared


def schedule_blocks() -> list[tuple[str, list[list[str]]]]:
    """The plate's features, grouped by the board revision that needs them.

    Indexed the way someone at a drill press asks the question.  The flat
    table this replaced was indexed by hole and answered "what is this hole
    for", which is the fabricator's question and is already on TT-MP-01; a
    person holding a v3.3 board wants to be told H9 and H10 and nothing else.

    Grouping cannot partition the features, because H1, H9, S1 and S2 each
    serve two revisions.  Those repeat, marked, so every block is a complete
    drill list on its own and no one has to read two blocks to fit one board.
    """
    dia, shared = _feature_index()

    def rows(ids: list[str]) -> list[list[str]]:
        return [[i + (SHARED_MARK if i in shared else ""), dia[i]]
                for i in ids]

    blocks = [(name, rows(ids)) for name, ids in holes_by_version(PLATE)]
    labels, _, plate_ids = hole_ids(PLATE)
    blocks.append(("CHASSIS", rows([labels[i] for i in plate_ids])))
    return blocks


def pack_blocks(blocks: list[tuple[str, list[list[str]]]],
                ncol: int) -> list[list[tuple[str, list[list[str]]]]]:
    """Blocks into columns, filled left to right and balanced by line count.

    A block is never split across columns: half a revision's drill list at the
    foot of one column is exactly the way to drill four holes and miss two.
    """
    lines = [len(body) + 1 for _, body in blocks]   # + its header row
    target = math.ceil(sum(lines) / ncol)
    cols: list[list[tuple[str, list[list[str]]]]] = []
    cur: list[tuple[str, list[list[str]]]] = []
    used = 0
    for block, n in zip(blocks, lines):
        if cur and used + n > target and len(cols) < ncol - 1:
            cols.append(cur)
            cur, used = [], 0
        cur.append(block)
        used += n
    cols.append(cur)
    return cols


def blocks_height(page: Sheet, cols) -> float:
    """How tall the tallest column of blocks is."""
    return max(sum(page.table_height("", len(body)) for _, body in col)
               + BLOCK_GAP * (len(col) - 1) for col in cols)


HEADERS = ["ID", "DRILL", "X", "Y", "USED BY"]
ALIGNS = ["start", "end", "end", "end", "start"]

#: The print command for a CUPS queue.  Spelled out because the default on the
#: queue this was written against is ``auto-fit``, and a reader who accepts
#: that default gets a 95.88 % template and no warning from anything.
PRINT_CMD = "lp -d <queue> -o media=A4 -o print-scaling=none <file>.pdf"

#: The legend strip already says the washes are board outlines and are not
#: drilled, and each scale bar is captioned with its length, so the notes
#: carry only the actions: how to print, what to measure, what the black
#: means, what the grey means, how to tape it down.
COMMON_NOTES = [
    "Print at 100 % on A4 with scaling off. Never Fit to page:  " + PRINT_CMD,
    f"Measure both scale bars; if either is not {BAR_LEN:.1f} mm, reprint.",
    "Black is drilled: a circle is the hole at true size, its cross the punch "
    "centre, a heavy line an edge.",
    "Grey dashed boxes are Pmod connector bodies: clearance only, not "
    "drilled.",
]

TAIL_NOTES = [
    "Tape it down printed side up, FRONT EDGE along the edge the Pmod bodies "
    "will overhang, and punch every cross.",
    "With a mill or a DRO, work from the coordinates on TT-MP-01 instead.",
]

def _fixing_span() -> str:
    """"P1 to P6", counted rather than asserted."""
    _, _, plate_ids = hole_ids(PLATE)
    return f"P1 to P{len(plate_ids)}"


#: The schedule heading explains the shared mark and the legend strip the
#: letters, and the DRILL column gives every size, so the plate notes say
#: only what neither can: that the blocks are a menu, and that a slot is
#: two drillings and a cut.
PLATE_NOTES = COMMON_NOTES + [
    "Drill every block for a plate that takes any board, or only the blocks "
    "for the boards you need.",
    "Drill both ends of each slot, then cut out the web between them.",
] + TAIL_NOTES

CHASSIS_NOTES = COMMON_NOTES + [
    f"Only {_fixing_span()} are drilled; the plate edge and board outlines "
    "only place the pattern.",
] + TAIL_NOTES


def legend_strip(c: Canvas, rect: Rect) -> float:
    """One row of revision swatches; returns the y below it."""
    y = rect.y1
    c.text(rect.x, y - style.T_TINY,
           "BOARD OUTLINES, drawn for clearance and not drilled. "
           "The letter is its hole ID prefix:",
           size=style.T_TINY, face="sans", bold=True)
    y -= style.T_TINY + 2.6
    sw, gap = 6.0, 2.0
    x = rect.x
    for name in PLACEMENTS:
        c.rect(x, y - style.T_TINY, sw, style.T_TINY,
               weight=style.W_THIN, colour=REVISION_INK[name],
               fill=REVISION_TINT[name])
        text = f"{REVISION_LETTER[name]}  {name}"
        c.text(x + sw + 1.6, y - style.T_TINY, text, size=style.T_TINY,
               colour=REVISION_INK[name])
        x += sw + 1.6 + style.text_width(text, style.T_TINY) + gap + 5.0
    return y - style.T_TINY - 1.0


LEGEND_HEIGHT = 2 * style.T_TINY + 3.6


def fit_size(text: str, width: float, face: str = "sans",
             bold: bool = True) -> float:
    """Largest ISO 3098 lettering height at which *text* fits *width*."""
    for size in style.TEXT_LADDER:
        if style.text_width(text, size, face=face, bold=bold) <= width:
            return size
    return style.T_MIN


TITLES = {
    "plate": ("DRILL TEMPLATE - MOUNTING PLATE",
              "Tiny Tapeout generic mounting plate: outline, board fastener "
              "holes, slots and plate fixings"),
    "chassis": ("DRILL TEMPLATE - CHASSIS",
                "Six M4 fixings for the generic mounting plate; plate and "
                "board outlines shown for clearance"),
}

WARNING = "PRINT AT 100 %   -   DO NOT FIT TO PAGE"


def render_drill_template(kind: str, *, drawing_no: str,
                          version: str) -> TemplatePage:
    if kind not in TITLES:
        raise SystemExit(f"unknown drill template {kind!r}")
    page = TemplatePage()
    c, area = page.canvas, page.area
    o = PLATE.outline
    rows = schedule_rows(kind)
    notes = PLATE_NOTES if kind == "plate" else CHASSIS_NOTES

    # -- header ------------------------------------------------------------
    title, subtitle = TITLES[kind]
    y = area.y1
    stamp = f"{drawing_no}    {version}    A4 PORTRAIT    SCALE 1:1"
    # The stamp is fixed-width and the title is not, so the title is the one
    # that gives way; setting both at their natural sizes ran one through the
    # other.
    avail = area.w - style.text_width(stamp, style.T_TINY) - 6.0
    tsize = fit_size(title, avail)
    c.text(area.x, y - tsize, title, size=tsize, face="sans", bold=True)
    c.text(area.x1, y - tsize, stamp, size=style.T_TINY, anchor="end")
    y -= tsize + 2.8
    ssize = fit_size(subtitle, area.w, face="condensed", bold=False)
    c.text(area.x, y - ssize, subtitle, size=ssize)
    y -= ssize + 3.6

    box_h = 11.0
    c.rect(area.x, y - box_h, area.w, box_h, weight=style.W_FRAME)
    c.text(area.cx, y - box_h / 2, WARNING,
           size=fit_size(WARNING, area.w - 8.0), anchor="middle",
           baseline="middle", face="sans", bold=True)
    y -= box_h + 4.5

    # -- horizontal scale bar ----------------------------------------------
    bar_y = y - style.T_TINY - 1.6 - BAR_THICK
    scale_bar(c, (page.w - BAR_LEN) / 2, bar_y)
    caption = f"measure: this bar is {BAR_LEN:.1f} mm overall"
    c.text(page.w / 2, bar_y - 1.2 - style.T_TINY, caption, size=style.T_TINY,
           anchor="middle")
    y = bar_y - 1.2 - style.T_TINY - style.descender(style.T_TINY) - 3.0

    # -- how tall the bottom band has to be --------------------------------
    # Measured, never guessed: the drawing gets whatever is left, and if that
    # is not enough the sheet refuses to render rather than shrink the one
    # thing on it that has to be true size.
    cols = pack_blocks(schedule_blocks(), BLOCK_COLUMNS) if kind == "plate" \
        else []
    notes_h = page.notes_height(area.w, "BEFORE YOU DRILL", notes)
    table_h = (blocks_height(page, cols) if kind == "plate"
               else page.table_height("", len(rows)))
    band_h = (LEGEND_HEIGHT + 3.0 + page.HEADING_HEIGHT + table_h + 4.5
              + notes_h)
    band_top = area.y + band_h

    view_bottom = band_top + 4.0
    # Room under the plate for the front-edge callout.  It has to clear the
    # Pmod bodies, which is the whole point of the callout and is why the
    # first version of it printed straight through them.
    below = below_plate()
    need = o.height + below + 2.0
    have = y - view_bottom
    if have < need:
        raise SystemExit(
            f"{kind} drill template: {have:.1f} mm left for a view that needs "
            f"{need:.1f} mm. The page is fixed and the plate is 1:1, so take "
            "it out of the notes or the schedule.")

    # -- the template itself, at true size ---------------------------------
    view = View(Rect(area.x, view_bottom, area.w, have), 0, 0,
                o.width, o.height, 1.0, "1:1",
                offset_x=(page.w - o.width) / 2,
                offset_y=view_bottom + below)
    _draw_template(c, page, view, kind)
    # Kept on the page so check_drill_template can turn a plate coordinate
    # into a page coordinate and go looking for the hole there, rather than
    # re-deriving this layout and checking its own arithmetic.
    page.view = view

    # -- vertical scale bar, against the plate -----------------------------
    scale_bar(c, area.x + 4.0, view.y(0), vertical=True)
    c.text(area.x + 1.2, view.y(0) + BAR_LEN / 2,
           f"measure: {BAR_LEN:.1f} mm", size=style.T_TINY, anchor="middle",
           rotate=90.0)

    # -- legend, schedule, notes -------------------------------------------
    cursor = band_top
    cursor = legend_strip(c, Rect(area.x, cursor - LEGEND_HEIGHT, area.w,
                                  LEGEND_HEIGHT)) - 3.0
    # Kept short deliberately: page.heading does not fit-size its text, and
    # the frame is 190 mm.  The full sense of the mark is in the notes.
    head = "SCHEDULE" if kind == "chassis" else (
        f"SCHEDULE   -   what each revision needs   "
        f"({SHARED_MARK} shared: drill once)")
    cursor = page.heading(Rect(area.x, cursor - page.HEADING_HEIGHT, area.w,
                               page.HEADING_HEIGHT), head)
    _draw_schedule(page, Rect(area.x, cursor - table_h, area.w, table_h),
                   kind, rows, cols)
    cursor -= table_h + 4.5
    page.notes(Rect(area.x, cursor - notes_h, area.w, notes_h),
               "BEFORE YOU DRILL", notes)
    return page


def _draw_schedule(page: Sheet, rect: Rect, kind: str, rows: list[list[str]],
                   cols) -> None:
    """The schedule: one block per revision on the plate sheet, one table on
    the chassis sheet.

    The two sheets are shaped differently because the same column does not
    carry information on both.  The chassis sheet has six features, all of
    them chassis fixings, so grouping them by revision would be five empty
    headings and the coordinates are worth the space instead.  The plate sheet
    has twelve features across five revisions, and the question a reader
    actually arrives with is which of them their board needs.

    Each block's header row doubles as its heading: the ID column is headed
    with the revision name rather than the word ID, which buys back the six
    heading rows that grouping would otherwise cost.
    """
    if kind == "chassis":
        headers = ["ID", "DRILL", "X", "Y"]
        aligns = ["start", "end", "end", "end"]
        body = [[r[0], r[1], r[2], r[3]] for r in rows]
        page.table(rect, "", headers, body, aligns)
        return
    colw = (rect.w - (BLOCK_COLUMNS - 1) * BLOCK_GUTTER) / BLOCK_COLUMNS
    for n, column in enumerate(cols):
        x = rect.x + n * (colw + BLOCK_GUTTER)
        y = rect.y1
        for name, body in column:
            h = page.table_height("", len(body))
            page.table(Rect(x, y - h, colw, h), "", [name, "DRILL"], body,
                       ["start", "end"])
            y -= h + BLOCK_GAP


def below_plate() -> float:
    """Space needed under the plate edge for the front-edge callout.

    Reserved and drawn from one function, because the version that reserved
    7 mm and then drew 2 mm under the edge put the callout through the Pmod
    bodies it was there to talk about.
    """
    return (-(PMOD_ROW_Y + PMOD_BODY[2]) + 2.2 + style.T_LABEL
            + style.descender(style.T_LABEL))


def _draw_template(c: Canvas, page: Sheet, view: View, kind: str) -> None:
    """The 1:1 pattern: washes first, then clearances, then what is drilled."""
    o = PLATE.outline
    labels, _, _ = hole_ids(PLATE)
    obstacles = Obstacles()
    area = page.area

    # The scale bar and its caption own the left margin of this band.
    obstacles.add_rect(area.x, view.y(0) - 4.0, area.x + 14.0,
                       view.y(0) + BAR_LEN + 5.0)

    # Board outlines, one wash each.  Deliberately not obstacles: they cover
    # most of the plate between them, so treating them as things to avoid
    # would leave nowhere for a label, and a black ID over a pale wash is
    # perfectly readable.
    for name, pl in PLACEMENTS.items():
        board = TT_BOARDS[pl["revision"]]
        offset_outline(c, view, board.outline, pl["dx"], pl["dy"],
                       REVISION_TINT[name], style.W_COMPONENT)

    # Pmod connector bodies: the reason the front edge is where it is.
    for sx in PMOD_SLOT_X:
        x0, x1 = sx + PMOD_BODY[0], sx + PMOD_BODY[1]
        y0, y1 = PMOD_ROW_Y + PMOD_BODY[2], PMOD_ROW_Y + PMOD_BODY[3]
        c.rect(*view.pt(x0, y0), view.d(x1 - x0), view.d(y1 - y0),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash=style.D_PHANTOM)
        obstacles.add_rect(*view.pt(x0, y0), *view.pt(x1, y1))

    # The plate edge: a cut line on its own template, a locating line on the
    # chassis one, where it is not a feature of the workpiece at all.
    if kind == "plate":
        c.rect(*view.pt(0, 0), view.d(o.width), view.d(o.height),
               weight=style.W_OUTLINE, radius=view.d(o.corner_radius))
    else:
        c.rect(*view.pt(0, 0), view.d(o.width), view.d(o.height),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash=style.D_PHANTOM, radius=view.d(o.corner_radius))
    for a, b in (((0, 0), (o.width, 0)), ((o.width, 0), (o.width, o.height)),
                 ((o.width, o.height), (0, o.height)), ((0, o.height), (0, 0))):
        obstacles.add_segment(*view.pt(*a), *view.pt(*b))

    # Everything drilled is black, and only black.  A colour laser registers
    # its planes to a few tenths of a millimetre, so a cyan circle can sit off
    # its own black cross by more than the tolerance being worked to; one
    # plane cannot misregister against itself.
    anchors: list[tuple[float, float]] = []
    marks: list[tuple[float, float, float, str]] = []
    for i, h in enumerate(PLATE.holes):
        if kind == "chassis" and h.kind != "plate":
            continue
        r = drill_mark(c, view, h.x, h.y, h.dia, style.C_LINE)
        px, py = view.pt(h.x, h.y)
        obstacles.add_circle(px, py, r + CROSS_OVER)
        anchors.append((px, py))
        marks.append((px, py, r + CROSS_OVER, labels[i]))
    if kind == "plate":
        for n, sl in enumerate(PLATE.slots, 1):
            slot_mark(c, view, sl, style.C_LINE)
            mx, my = view.pt((sl.x0 + sl.x1) / 2, (sl.y0 + sl.y1) / 2)
            half = (abs(sl.x1 - sl.x0) + abs(sl.y1 - sl.y0)) / 2 + sl.width / 2
            obstacles.add_rect(mx - view.d(half), my - view.d(half),
                               mx + view.d(half), my + view.d(half))
            anchors.append((mx, my))
            marks.append((mx, my, view.d(half) + CROSS_OVER, f"S{n}"))

    overhang = -(PMOD_ROW_Y + PMOD_BODY[2])
    front = (f"FRONT EDGE   -   Pmod connector bodies overhang it by "
             f"{overhang:.2f} mm")
    fy = view.y(0) - below_plate() + style.descender(style.T_LABEL)
    fw = style.text_width(front, style.T_LABEL, face="sans", bold=True)
    c.text(page.w / 2, fy, front, size=style.T_LABEL, face="sans", bold=True,
           anchor="middle")
    obstacles.add_rect(page.w / 2 - fw / 2, fy - style.descender(style.T_LABEL),
                       page.w / 2 + fw / 2, fy + style.T_LABEL, pad=1.0)

    for px, py, clear, text in marks:
        others = [a for a in anchors if a != (px, py)]
        box = place_label(c, obstacles, (px, py), clear, text, style.C_LINE,
                          others=others, bounds=view.rect)
        obstacles.add_rect(*box, pad=0.6)
