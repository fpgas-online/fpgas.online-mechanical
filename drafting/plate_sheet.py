"""Drawing sheets for the Tiny Tapeout generic mounting plate.

Two sheets:

* a fabrication drawing of the plate itself, with every hole and slot;
* a fitting guide, one small view per board revision, showing which of those
  holes that revision actually uses and where its board and Pmod hosts land.

A many-hole pattern is dimensioned by table rather than by putting a dimension
on every hole, which is standard practice and the only way to keep a plate with
eighteen features readable.
"""

from __future__ import annotations

import math

from data.mounting_plate import PLACEMENTS, PMOD_ROW_Y, PMOD_SLOT_X, PLATE
from data.schema import BoardSpec, Hole, Slot
from data.tinytapeout_boards import BOARDS as TT_BOARDS

from . import dims, style
from .board_sheet import Obstacles, _place_notes_and_sources, outline_path
from .canvas import Canvas
from .sheet import Rect, Sheet, TitleBlock
from .view import View

BOARD_HOLE = "#a00000"
PLATE_HOLE = "#006060"


def draw_slot(c: Canvas, view: View, s: Slot, colour: str = BOARD_HOLE) -> None:
    """Obround: two semicircular ends joined by straight flanks.

    The path is emitted in SVG space, which is Y-down, so the arc sweep flag is
    the opposite of what it would be reasoning in the drawing's Y-up frame.
    Getting it wrong turns each end cap inside out and crosses the flanks.
    """
    r = view.d(s.width / 2)
    (x0, y0), (x1, y1) = view.pt(s.x0, s.y0), view.pt(s.x1, s.y1)
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * r, math.cos(ang) * r
    d = (f"M {x0 + nx:.4f} {c._y(y0 + ny):.4f} "
         f"L {x1 + nx:.4f} {c._y(y1 + ny):.4f} "
         f"A {r:.4f} {r:.4f} 0 0 1 {x1 - nx:.4f} {c._y(y1 - ny):.4f} "
         f"L {x0 - nx:.4f} {c._y(y0 - ny):.4f} "
         f"A {r:.4f} {r:.4f} 0 0 1 {x0 + nx:.4f} {c._y(y0 + ny):.4f} Z")
    c.path(d, w=style.W_OUTLINE, colour=colour, fill="#ffffff")

    # A short slot has no room for an axis line and two end centre marks: they
    # merge into a smudge.  Mark the midpoint instead.
    if math.dist((x0, y0), (x1, y1)) > 2.2 * r:
        c.line(x0, y0, x1, y1, w=style.W_CENTRE, colour=colour,
               dash="3,1.2,0.8,1.2")
        dims.centre_mark(c, x0, y0, r, colour=colour, over=1.0)
        dims.centre_mark(c, x1, y1, r, colour=colour, over=1.0)
    else:
        dims.centre_mark(c, (x0 + x1) / 2, (y0 + y1) / 2, r, colour=colour,
                         over=1.0)


#: Directions a hole label is tried in, nearest and clearest first.
_LABEL_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0),
               (0, 1), (0, -1)]


def draw_plate_holes(c: Canvas, view: View, spec: BoardSpec,
                     labels: dict[int, str] | None = None,
                     highlight: set[int] | None = None,
                     extra: Obstacles | None = None) -> None:
    """Draw the holes, and place their labels so they do not collide.

    Several holes on this plate sit five millimetres apart, so a fixed label
    offset puts one label straight through the next hole.  Labels are placed
    greedily against an obstacle list that already holds every hole and slot.
    """
    obstacles = Obstacles()
    if extra is not None:
        obstacles.rects += extra.rects
        obstacles.circles += extra.circles
        obstacles.segments += extra.segments
    for h in spec.holes:
        obstacles.add_circle(*view.pt(h.x, h.y), view.d(h.dia / 2) + 1.4)
    for sl in spec.slots:
        # A short slot is a small segment, which a label can sit almost on top
        # of without registering a hit, so use its envelope instead.
        pad = view.d(sl.width / 2) + 1.4
        obstacles.add_rect(min(view.x(sl.x0), view.x(sl.x1)),
                           min(view.y(sl.y0), view.y(sl.y1)),
                           max(view.x(sl.x0), view.x(sl.x1)),
                           max(view.y(sl.y0), view.y(sl.y1)), pad=pad)

    for i, h in enumerate(spec.holes):
        colour = PLATE_HOLE if h.kind == "plate" else BOARD_HOLE
        faint = highlight is not None and i not in highlight
        if faint:
            colour = style.C_PHANTOM
        px, py = view.pt(h.x, h.y)
        r = view.d(h.dia / 2)
        c.circle(px, py, r, w=style.W_OUTLINE if not faint else style.W_PHANTOM,
                 colour=colour, fill="#ffffff")
        dims.centre_mark(c, px, py, r, colour=colour, over=1.2)
        if not (labels and i in labels) or faint:
            continue
        text = labels[i]
        tw = style.text_width(text, style.T_LABEL, bold=True)
        th = style.text_height(style.T_LABEL)
        best, best_score = None, None
        for radius in (r + 2.2, r + 5.0, r + 8.0):
            for dx, dy in _LABEL_DIRS:
                cx = px + dx * (radius + tw / 2)
                cy = py + dy * (radius + th / 2)
                score = obstacles.hits(cx, cy, max(tw, th) / 2) * 100 + radius
                if best_score is None or score < best_score:
                    best, best_score = (cx, cy), score
            if best_score is not None and best_score < 100:
                break
        cx, cy = best
        # A label pushed away from its hole needs a leader, or in a cluster of
        # holes a few millimetres apart the reader cannot tell which hole it
        # belongs to.
        gap = math.dist((px, py), (cx, cy)) - r - max(tw, th) / 2
        if gap > 1.5:
            ang = math.atan2(cy - py, cx - px)
            c.line(px + (r + 1.0) * math.cos(ang),
                   py + (r + 1.0) * math.sin(ang),
                   cx - (max(tw, th) / 2 + 0.8) * math.cos(ang),
                   cy - (max(tw, th) / 2 + 0.8) * math.sin(ang),
                   w=style.W_THIN, colour=colour)
        c.text(cx, cy, text, size=style.T_LABEL, colour=colour, bold=True,
               anchor="middle", baseline="middle")
        obstacles.add_rect(cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2,
                           pad=0.8)


def render_plate(*, drawing_no: str, date: str, sheet_size: str = "A3") -> Sheet:
    spec = PLATE
    o = spec.outline
    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(), subtitle=spec.subtitle, drawing_no=drawing_no,
        rev="A", date=date, drawn_by="generated", material="3 mm sheet"))
    sheet.draw_frame()
    c = sheet.canvas

    view = View.fit(sheet.area, (0, 0, o.width, o.height), margin=40.0,
                    margin_top=20.0, margin_bottom=48.0)
    sheet.title.scale = view.scale_label
    plate = Rect(view.x(0), view.y(0), view.d(o.width), view.d(o.height))

    outline_path(c, view, spec)

    labels = {}
    board_ids, plate_ids = [], []
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            plate_ids.append(i)
            labels[i] = f"P{len(plate_ids)}"
        else:
            board_ids.append(i)
            labels[i] = f"H{len(board_ids)}"
    # Labels must also keep off the plate outline itself: the fixings near the
    # right-hand edge would otherwise put their label straight on it.
    edge = Obstacles()
    o = spec.outline
    for a, b in (((0, 0), (o.width, 0)), ((o.width, 0), (o.width, o.height)),
                 ((o.width, o.height), (0, o.height)), ((0, o.height), (0, 0))):
        edge.add_segment(*view.pt(*a), *view.pt(*b))
    draw_plate_holes(c, view, spec, labels, extra=edge)
    for n, sl in enumerate(spec.slots, 1):
        draw_slot(c, view, sl)
        mx, my = view.pt((sl.x0 + sl.x1) / 2, (sl.y0 + sl.y1) / 2)
        dims.leader(c, (mx, my), (mx - 13.0, my - 9.0), f"S{n}",
                    colour=BOARD_HOLE, tail=1.5, anchor="end", dot=True)

    # The Pmod host grid is the reason the plate exists, so it is drawn and
    # dimensioned even though it is not a machined feature.
    for i, px in enumerate(PMOD_SLOT_X):
        sx, sy = view.pt(px, PMOD_ROW_Y)
        half = view.d(6.35)
        c.rect(sx - half, sy - view.d(2.9), half * 2, view.d(5.8),
               weight=style.W_PHANTOM, colour=style.C_HIGHLIGHT,
               dash="3,1.5,0.8,1.5")
        c.text(sx, sy + view.d(3.4), f"PMOD {i + 1}", size=style.T_LABEL,
               colour=style.C_HIGHLIGHT, anchor="middle")

    dims.linear(c, view.pt(PMOD_SLOT_X[0], PMOD_ROW_Y),
                view.pt(PMOD_SLOT_X[1], PMOD_ROW_Y),
                plate.y - 8.0 - view.y(PMOD_ROW_Y), horizontal=True,
                text=f"{PMOD_SLOT_X[1] - PMOD_SLOT_X[0]:.2f} TYP")

    x_extent = dims.ordinate_chain(
        c, [(view.x(v), f"{v:.2f}", view.y(PMOD_ROW_Y)) for v in PMOD_SLOT_X],
        plate.y, plate.y - 17.0, horizontal=True,
        zero_pos=plate.x, zero_from=plate.y)
    y_extent = dims.ordinate_chain(
        c, [(view.y(PMOD_ROW_Y), f"{PMOD_ROW_Y:.2f}", view.x(PMOD_SLOT_X[0]))],
        plate.x, plate.x - 12.0, horizontal=False,
        zero_pos=plate.y, zero_from=plate.x)

    dims.linear(c, (plate.x, plate.y), (plate.x1, plate.y),
                x_extent - 7.0 - plate.y, horizontal=True, value=o.width)
    dims.linear(c, (plate.x, plate.y), (plate.x, plate.y1),
                y_extent - 7.0 - plate.x, horizontal=False, value=o.height)
    dims.datum_marker(c, plate.x, plate.y, label="")
    dims.leader(c, (plate.x, plate.y),
                (min(y_extent, plate.x - 30.0), plate.y - 15.0),
                "DATUM  X0 Y0", tail=2.0, anchor="start", dot=True)
    dims.leader(c, view.pt(o.width - o.corner_radius * 0.3,
                           o.height - o.corner_radius * 0.3),
                (plate.x1 + 8.0, plate.y1 + 5.0),
                f"R{o.corner_radius:.2f} (4 places)")

    rows = []
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            continue
        rows.append([labels[i], f"{h.x:.2f}", f"{h.y:.2f}", f"{h.dia:.2f}",
                     h.label.replace("+", ", ")])
    for n, s in enumerate(spec.slots, 1):
        # Two values because a slot has two end centres; the note below says so.
        rows.append([f"S{n}", f"{s.x0:.2f} / {s.x1:.2f}",
                     f"{s.y0:.2f} / {s.y1:.2f}",
                     f"{s.width:.2f} wide slot", s.label.replace("+", ", ")])
    block = sheet.column_block(sheet.table_height("BOARD MOUNTING HOLES", len(rows)))
    sheet.table(block, "BOARD MOUNTING HOLES",
                ["ID", "X mm", "Y mm", "SIZE mm", "USED BY"], rows,
                ["start", "end", "end", "end", "start"])

    rows = [[labels[i], f"{spec.holes[i].x:.2f}", f"{spec.holes[i].y:.2f}",
             f"{spec.holes[i].dia:.2f}"] for i in plate_ids]
    block = sheet.column_block(sheet.table_height("PLATE FIXING HOLES", len(rows)))
    sheet.table(block, "PLATE FIXING HOLES",
                ["ID", "X mm", "Y mm", "DIA mm"], rows,
                ["start", "end", "end", "end"])

    notes = [
        "All dimensions in millimetres. Datum is the lower-left corner of the "
        "plate; X right, Y up, viewed from the side the demo board mounts on.",
        "Hole positions are tabulated rather than dimensioned individually: "
        "there are too many to put on the view without it becoming unreadable.",
        "The three PMOD envelopes are not machined features. They mark where "
        "the Pmod host pin fields end up, which is the same place for every "
        "board revision. That is the point of the plate.",
        "A slot row gives two X and two Y values: the centres of its two ends. "
        "Its length is those centres apart plus the slot width.",
    ] + list(spec.notes) + [
        "Fit the plate to its chassis before fitting a demo board: the plate "
        "fixings sit in the border, but the board overhangs part of it.",
        "Suggested material 3 mm acrylic or 1.6 mm FR4. Least material between "
        "any two features is about 1.6 mm, between H2 and H3.",
    ]
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
           for s in spec.sources]
    _place_notes_and_sources(sheet, notes, src)

    sheet.draw_title_block()
    return sheet


def render_fitting_guide(*, drawing_no: str, date: str,
                         sheet_size: str = "A3") -> Sheet:
    spec = PLATE
    o = spec.outline
    sheet = Sheet(sheet_size, TitleBlock(
        title="TT MOUNTING PLATE - BOARD FITTING GUIDE",
        subtitle="Which holes each demo board revision uses",
        drawing_no=drawing_no, rev="A", date=date, drawn_by="generated"))
    sheet.draw_frame()
    c = sheet.canvas
    area = sheet.area

    scale = 0.5
    sheet.title.scale = "1:2"
    # Three across, two down: at 1:2 a plate view is 67.5 x 50.5 mm, so three
    # fit the drawing width and two rows leave room for the captions without
    # running into the notes band.
    cols, rows = 3, 2
    cell_w = area.w / cols
    cell_h = area.h / rows

    for n, (name, pl) in enumerate(PLACEMENTS.items()):
        col, row = n % cols, n // cols
        cell = Rect(area.x + col * cell_w, area.y1 - (row + 1) * cell_h,
                    cell_w, cell_h)
        _guide_view(c, cell, scale, name, pl)

    rows_t = []
    for name, pl in PLACEMENTS.items():
        used = ", ".join(pl["shuttles"]) or "not yet shipped"
        rows_t.append([name, used, f"{pl['dx']:.2f}", f"{pl['dy']:.2f}",
                       str(pl["pmod_count"]), str(pl["first_pmod_slot"])])
    # In the annotation column, not in a half-width cell: at a true 2.5 mm cap
    # height this table does not fit in half the drawing area.
    block = sheet.column_block(sheet.table_height("BOARD PLACEMENT ON THE PLATE",
                                                  len(rows_t)))
    sheet.table(block, "BOARD PLACEMENT ON THE PLATE",
                ["REVISION", "SHUTTLES", "dX mm", "dY mm", "PMODS",
                 "FIRST SLOT"],
                rows_t, ["start", "start", "end", "end", "middle", "middle"])

    notes = [
        "Each view shows one demo board revision sitting on the plate, with "
        "the holes that revision uses drawn solid and the rest greyed back.",
        "dX and dY place the board: add them to a coordinate in that board's "
        "own frame to get a plate coordinate.",
        "The TT01/02/03 board has only two Pmod hosts. They go on plate Pmod "
        "positions 2 and 3, which makes the plate 5.15 mm narrower than "
        "putting them on 1 and 2 would.",
        "All five revisions put their Pmod host pin fields on the same three "
        "positions, at the same height above the plate's front edge.",
    ]
    _place_notes_and_sources(sheet, notes, [])
    sheet.draw_title_block()
    return sheet


def _guide_view(c: Canvas, cell: Rect, scale: float, name: str,
                pl: dict) -> None:
    spec = PLATE
    o = spec.outline
    view = View(cell, 0, 0, o.width, o.height, scale, "1:2",
                cell.cx - o.width * scale / 2,
                cell.cy - o.height * scale / 2 - 2.0)

    board = TT_BOARDS[pl["revision"]]
    used = {i for i, h in enumerate(spec.holes)
            if h.kind != "plate" and name in h.label}
    used_slots = {i for i, s in enumerate(spec.slots) if name in s.label}

    outline_path(c, view, spec, colour=style.C_LINE, w=style.W_THIN)

    # The board, in phantom line, shifted onto the plate.
    dx, dy = pl["dx"], pl["dy"]
    bo = board.outline
    for edge in bo.edges or ():
        if edge[0] == "line":
            _, x1, y1, x2, y2 = edge
            c.line(*view.pt(x1 + dx, y1 + dy), *view.pt(x2 + dx, y2 + dy),
                   w=style.W_PHANTOM, colour=style.C_PHANTOM,
                   dash="5,1.4,1,1.4")
    if not bo.edges:
        c.rect(*view.pt(dx, dy), view.d(bo.width), view.d(bo.height),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash="5,1.4,1,1.4")

    for p in board.pmods:
        px, py = view.pt(p.cx + dx, p.cy + dy)
        c.rect(px - view.d(p.pin_span / 2 + 1.3),
               py - view.d(p.row_span / 2 + 1.3),
               view.d(p.pin_span + 2.6), view.d(p.row_span + 2.6),
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT,
               fill="#ffffff")

    draw_plate_holes(c, view, spec, highlight=used)
    for i, s in enumerate(spec.slots):
        draw_slot(c, view, s,
                  colour=BOARD_HOLE if i in used_slots else style.C_PHANTOM)

    shuttles = ", ".join(pl["shuttles"]) or "no shipped shuttle yet"
    c.text(cell.cx, view.y(0) - 7.0, f"{name}  ({shuttles})",
           size=style.T_LABEL, anchor="middle", bold=True, face="sans")
    c.text(cell.cx, view.y(0) - 12.0, f"board rev {pl['revision']}",
           size=style.T_LABEL, anchor="middle", colour="#444444")
    c.text(cell.cx, view.y(0) - 17.0,
           f"offset X {dx:.2f}  Y {dy:.2f} mm",
           size=style.T_LABEL, anchor="middle", colour="#444444")
