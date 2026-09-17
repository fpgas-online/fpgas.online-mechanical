"""The three Model B sized Raspberry Pis on the one outline they share.

The Raspberry Pi family's comparison sheet.  Where each model's own sheet
draws that model alone, this draws all three at once: the outline, the four
mounting holes and the 40-pin GPIO header once, because they are identical on
all three, and then each model's power input, Ethernet jack and USB type A
ports in that model's own line type.  Only the header is checked upstream --
the HAT specification fixes it and ``raspberry_pi/extract.py`` reads it out of
each drawing and requires the three to agree -- so ``require_shared`` below
checks all three things before this sheet draws any of them once.  What a
plate or chassis designer gets from it, and cannot get by laying three sheets
side by side, is the union envelope, the fact that a cut-out made for a Pi 4B
suits neither the Pi 3 nor the Pi 5, and the two extra holes the Pi 5 adds.

Continuous line means "the same on all three".  Everything a model does not
share with the other two is drawn broken, one type per model, and the legend
names them.  That is not one of the three ISO 128 broken types the rest of
this library uses -- none of those means "this model", and nothing here is
hidden, adjacent or an axis -- so the types are defined below, used on this
sheet alone, and each is in its legend.

``board_sheet.draw_feature`` is deliberately not reused: it takes the colour
and the line type from the feature's own kind, and here the line type is the
whole message.  Everything else that a board sheet and this one both do is
called rather than copied -- the outline path, the holes, the outline frame
of overall dimensions, datum and radius callout, the balloon placer and its
obstacle model, the legend and the notes -- because a second copy of the
reservation half of "reserve, then draw" is how that pair comes apart.
"""

from __future__ import annotations

from dataclasses import replace

from raspberry_pi.boards import BOARDS, FEATURE_NUMBERS
from tools.layout import PMOD_HAT_SHEET, drawing_name, slug

from . import board_sheet as bs
from . import dims, style
from .board_sheet import (HARD, VIEW_MARGIN_BOTTOM, VIEW_MARGIN_SIDE,
                          VIEW_MARGIN_TOP, Obstacles, _Ballooned,
                          draw_holes, draw_outline_frame, note_blocks,
                          outline_path, place_legend_and_notes,
                          reserve_overall_dimensions, reserve_radius_callout)
from .canvas import Canvas
from .sheet import Rect, Sheet, TitleBlock
from .view import View

#: The file this sheet is written to, its title and its subtitle, in one
#: place: the generator names the file, the README builder names the sheet,
#: and the title block is drawn from the same two strings.
STEM = "rpi-models-compared"
TITLE = "Raspberry Pi 3B/3B+, 4B and 5 compared"
SUBTITLE = "One 85 x 56 outline: what is shared and what moves"

#: The models, in the order they were made, which is also the order their
#: own sheets are bound in.
MODELS = ("rpi3b", "rpi4b", "rpi5")

#: The three models' own sheets, as the notes and the title block on this one
#: cite them.  Derived from the same stems the generator writes those sheets
#: to, never spelled out: a cross reference written by hand is a cross
#: reference that can disagree with the title block it points at.
MODEL_SHEETS = tuple(drawing_name("raspberry-pi", slug(k)) for k in MODELS)
MODEL_SHEET_LIST = ", ".join(MODEL_SHEETS[:-1]) + " and " + MODEL_SHEETS[-1]

#: What each is called on this sheet.  Short, because it is a table cell and
#: a legend entry; the full titles are on the models' own sheets.
MODEL_NAME = {"rpi3b": "Pi 3B/3B+", "rpi4b": "Pi 4B", "rpi5": "Pi 5"}

#: Colour and dash per model.  The dash is what survives a monochrome print
#: and is therefore what carries the distinction -- a long dash, a short dash
#: and a dot, which stay apart at 0.35 mm on A3 where two chain types would
#: not.  The colour is a convenience on screen, and every one of them is dark
#: enough to photocopy and distinct from the black of the shared geometry and
#: from the red the balloons are drawn in.
MODEL_LINE = {
    "rpi3b": ("#005c2e", "5.0,2.0"),
    "rpi4b": ("#7a4a00", "2.0,1.6"),
    "rpi5": ("#5b2d8e", "0.7,1.5"),
}

#: The keep-out the Raspberry Pi HAT specification asks for around a mounting
#: hole.  Drawn here rather than each model's own, which are 6.00, 5.80 and
#: not given: one circle that satisfies all three is what a plate is designed
#: to, and the three figures are in the hole schedule.
HAT_KEEPOUT = 6.2

#: Feature numbers whose part sits in the same place on every model, so it is
#: drawn once in the shared style rather than three times in three.
SHARED_NUMBERS = (1,)

#: What a balloon is drawn in when the position it points at is one that more
#: than one model puts the part in.  Continuous and black, like everything
#: else on this sheet that more than one model shares.
SHARED_LINE = (style.C_LINE, None)


def _rect(c: Canvas, view: View, box, colour: str, dash: str | None,
          weight: float = style.W_COMPONENT) -> None:
    x0, y0 = view.pt(box[0], box[1])
    x1, y1 = view.pt(box[2], box[3])
    c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
           weight=weight, colour=colour, dash=dash)


def _features(number: int) -> list[tuple[str, object]]:
    """Every model's feature carrying *number*, in model order."""
    out = []
    for key in MODELS:
        for f in BOARDS[key].features:
            if f.number == number:
                out.append((key, f))
    return out


def _box(f) -> tuple[float, float, float, float]:
    return (f.x0, f.y0, f.x1, f.y1)


def _overlaps(a, b, slack: float = 0.0) -> bool:
    return (a[0] - slack < b[2] and b[0] - slack < a[2]
            and a[1] - slack < b[3] and b[1] - slack < a[3])


def require_shared() -> None:
    """Stop unless the three models agree on everything drawn once.

    The outline, the four mounting hole centres and the 40-pin GPIO header
    are each drawn a single time, in the continuous line that on this sheet
    means "identical on all three models", and the notes say so in words.
    Nothing upstream proves all of that: raspberry_pi/extract.py does read
    the header out of each model's own drawing and require the three to
    agree, but the outline size is declared per model in its own table, and
    only the Pi 4B's holes are read from its DXF -- the Pi 3B/3B+ and the
    Pi 5 take theirs from a hard-coded STANDARD_HOLES, and the two are never
    compared.  So the claim is checked here, where the drawing makes it.
    """
    first = MODELS[0]

    def outline(key):
        o = BOARDS[key].outline
        return (o.width, o.height, o.corner_radius, o.thickness, o.edges)

    def mounts(key):
        return sorted((h.label, h.x, h.y) for h in BOARDS[key].holes
                      if h.kind == "mount")

    def shared(key):
        return sorted((n, _box(f)) for n in SHARED_NUMBERS
                      for k, f in _features(n) if k == key)

    for what, get in (("outline", outline),
                      ("mounting hole centres", mounts),
                      ("shared feature positions", shared)):
        want = get(first)
        for key in MODELS[1:]:
            if get(key) != want:
                raise SystemExit(
                    f"{STEM}: the {what} of the {MODEL_NAME[key]} and of the "
                    f"{MODEL_NAME[first]} differ, {get(key)} against {want}, "
                    "so this sheet must not draw them once as shared; draw "
                    "them per model and take the claim out of the notes")


def _clusters(number: int) -> list[list[tuple[str, object]]]:
    """The positions *number* is found in, each with the models that use it.

    A number means the same part on every sheet of this family, so it is the
    balloon label here too.  On this sheet it can be in two places: the RJ45
    is in the lower right corner of a Pi 3 and a Pi 5 and in the upper right
    corner of a Pi 4B.  Models whose boxes overlap are one balloon; models
    whose boxes do not are separate ones, and the number is ballooned twice.

    One pass, and groups are never merged afterwards: a model that overlaps
    two existing groups joins the first of them rather than joining the two
    together.  Three models cannot produce that -- the third either overlaps
    a group or starts its own -- so it is not worth the union-find; a fourth
    Model B sized Pi would make it worth writing.
    """
    groups: list[list[tuple[str, object]]] = []
    for key, f in _features(number):
        for g in groups:
            if any(_overlaps(_box(f), _box(other)) for _, other in g):
                g.append((key, f))
                break
        else:
            groups.append([(key, f)])
    return groups


def _union(boxes) -> tuple[float, float, float, float]:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _area(box) -> float:
    return (box[2] - box[0]) * (box[3] - box[1])


#: How far inside its own outline a leader's dot sits, and how far outside a
#: foreign one it is worth trying to keep it.
DOT_CLEAR = 0.7


def _anchors(view: View, mine, foreign, steps: int = 61
             ) -> tuple[tuple[float, float], ...]:
    """Where a leader may touch this group of outlines, best first.

    The connectors on the right of this drawing lie across one another.  The
    Pi 4B's lower USB pair is the worst of them: the widest strip of it that
    is not also inside the Pi 3's or the Pi 5's Ethernet jack is 0.562 mm
    tall, along its bottom edge, and a dot with DOT_CLEAR either side of it
    wants 1.4 mm.  So the outlines a dot avoids are scored rather than forbidden
    -- the fewer it lands in, the better -- and where nothing can be avoided
    the ring's own line type is what says which model the number belongs to.
    """
    ux0, uy0, ux1, uy1 = _union(mine)
    cx, cy = (ux0 + ux1) / 2, (uy0 + uy1) / 2
    out = []
    for i in range(steps):
        px = ux0 + (ux1 - ux0) * (i + 0.5) / steps
        for j in range(steps):
            py = uy0 + (uy1 - uy0) * (j + 0.5) / steps
            if not any(b[0] + DOT_CLEAR <= px <= b[2] - DOT_CLEAR
                       and b[1] + DOT_CLEAR <= py <= b[3] - DOT_CLEAR
                       for b in mine):
                continue
            hits = sum(1 for b in foreign
                       if _overlaps((px, py, px, py), b, DOT_CLEAR))
            out.append((hits, (px - cx) ** 2 + (py - cy) ** 2, px, py))
    if not out:
        return (view.pt(cx, cy),)
    out.sort()
    return tuple(view.pt(px, py) for _, _, px, py in out[:12])


def _join(names) -> str:
    names = list(names)
    if len(names) == len(MODELS):
        return "all three"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _feature_rows() -> list[list[str]]:
    """One row per position a numbered part is found in, in number order.

    Models that put the part in the same place with the same description
    share a row: the 40-pin header is one row reading "all three", which is
    the sheet's first claim and belongs in the schedule as well as in a note.
    """
    rows = []
    for number in sorted(FEATURE_NUMBERS):
        groups: list[tuple[tuple, list[str], object]] = []
        for key, f in _features(number):
            sig = (f.label, f.x0, f.y0, f.x1, f.y1)
            for other in groups:
                if other[0] == sig:
                    other[1].append(MODEL_NAME[key])
                    break
            else:
                groups.append((sig, [MODEL_NAME[key]], f))
        for _, names, f in groups:
            rows.append([str(number), _join(names), f.label,
                         f"{f.x0:.2f} to {f.x1:.2f}",
                         f"{f.y0:.2f} to {f.y1:.2f}"])
    return rows


def _hole_rows() -> list[list[str]]:
    """The holes, by ID, with each model's diameter and keep-out beside it.

    Every model's MT1 to MT4 are at the same centres -- that is the whole
    reason one plate can take any of them -- so the position is given once and
    the three figures that do differ are given as a triple in model order,
    which the note beneath the table spells out.
    """
    rows = []
    seen: dict[str, dict[str, object]] = {}
    for key in MODELS:
        for h in BOARDS[key].holes:
            seen.setdefault(h.label, {})[key] = h
    for label, by_model in seen.items():
        ref = next(iter(by_model.values()))
        dia = " / ".join(
            (f"{by_model[k].dia:.2f}"
             + (f" +/-{by_model[k].tol:.2f}" if by_model[k].tol else ""))
            if k in by_model else "-" for k in MODELS)
        keep = " / ".join(
            (f"{by_model[k].keepout_dia:.2f}" if by_model[k].keepout_dia
             else "not given") if k in by_model else "-" for k in MODELS)
        rows.append([label, f"{ref.x:.2f}", f"{ref.y:.2f}",
                     _join([MODEL_NAME[k] for k in MODELS if k in by_model]),
                     dia, keep])
    return rows


def _sources() -> list[str]:
    """The Raspberry Pi Ltd drawings the three models' data cites.

    One line per drawing, and the drawing only.  Most models cite their own
    file twice, once for the outline and once for the holes, and the second
    entry carries a paragraph saying which circle on which layer was read:
    across the three models that is five URLs in seven entries with three
    such derivations, which on this sheet would be a third of the notes
    band.  A derivation belongs to the model it was made for and is on that
    model's own sheet, where the note below sends the reader.
    """
    out: dict[tuple[str, str], list[str]] = {}
    for key in MODELS:
        for s in BOARDS[key].sources:
            labels = out.setdefault((MODEL_NAME[key], s.ref), [])
            if s.label not in labels:
                labels.append(s.label)
    return [f"{name}, {_join_labels(labels)}: {ref}"
            for (name, ref), labels in out.items()]


def _join_labels(labels) -> str:
    first = labels[0]
    rest = [t[0].lower() + t[1:] for t in labels[1:]]
    return " and ".join([first] + rest)


def _closest_power_edge() -> float:
    """The smallest gap between two models' power connector faces.

    Measured rather than written down, because it is the figure the note
    beside it quotes and a data change would otherwise leave that note
    stating something the drawing no longer shows.
    """
    boxes = [_box(f) for _, f in _features(2)]
    return min(abs(a[i] - b[i]) for i in range(4)
               for n, a in enumerate(boxes) for b in boxes[n + 1:])


def _notes() -> list[str]:
    shared = BOARDS[MODELS[0]].outline
    envelope = _union([_box(f) for key in MODELS for f in BOARDS[key].features]
                      + [(0.0, 0.0, shared.width, shared.height)])
    aux = [h for h in BOARDS["rpi5"].holes if h.kind == "aux"]
    return [
        "Viewed from the component side.",
        f"All three models share this outline exactly: {shared.width:.2f} x "
        f"{shared.height:.2f} mm, R{shared.corner_radius:.2f} corners and the "
        "same four mounting hole centres. Only the hole diameter and the "
        "keep-out differ.",
        "The 40-pin GPIO header is in the same place on all three because "
        "the Raspberry Pi HAT specification fixes it; the three drawings were "
        "read separately and required to agree.",
        "The Ethernet jack and the USB type A ports swap places between the "
        "Pi 3 and the Pi 4. On the Pi 3B/3B+ and on the Pi 5 the RJ45 sits in "
        "the lower right corner with the USB ports above it; on the Pi 4B the "
        "RJ45 is in the upper right corner with the USB ports below. A "
        "chassis cut for one will not take the other.",
        f"The Pi 5 adds AUX1 and AUX2, two {aux[0].dia:.2f} mm holes on the "
        "mounting hole axes. Power input is micro-USB on the Pi 3B/3B+ and "
        "USB-C on the Pi 4B and the Pi 5.",
        "The three power inputs very nearly coincide: their nearest faces "
        f"are {_closest_power_edge():.3f} mm apart, so at 1:1 the three "
        "outlines print as one line and that corner cannot be read as "
        "three. The feature schedule gives each model's extents.",
        "Assembled envelope, every model taken together and connector "
        f"overhang included: {envelope[2] - envelope[0]:.2f} x "
        f"{envelope[3] - envelope[1]:.2f} mm. Each model's own is on its own "
        "sheet.",
        "A balloon number means the same part on every Raspberry Pi sheet, "
        "and appears twice here where the part is in two places depending on "
        "the model. Ring, number and leader are drawn in that model's own "
        "line type and colour; a plain black balloon is a position more than "
        "one model shares.",
        f"Design keep-outs to {HAT_KEEPOUT} mm diameter around every mounting "
        "hole, per the Raspberry Pi HAT specification. The phantom circles "
        "are that figure; KEEPOUT gives what each model's own drawing shows.",
        "The Digilent Pmod HAT Adapter is not drawn. It is the same on all "
        "three, and its phantom pin fields would lie across the lower edge "
        "and the right-hand connectors, which are what this sheet exists to "
        f"show; {', '.join(MODEL_SHEETS)} and {PMOD_HAT_SHEET} carry it.",
        "HDMI, micro-HDMI and the 3.5 mm audio jack are deliberately not "
        "drawn on any sheet of this family.",
        "SOURCES lists the drawings only; what was read from each, and the "
        "drawing notes quoted from it, are on that model's own sheet.",
    ]


def _legend() -> list[tuple[object, str]]:
    entries: list[tuple[object, str]] = [
        ("outline", "Outline, mounting holes and 40-pin GPIO header: "
                    "identical on all three models"),
        ("phantom", f"Mounting hole keep-out, {HAT_KEEPOUT} dia, per the "
                    "HAT specification"),
    ]
    for key in MODELS:
        colour, dash = MODEL_LINE[key]
        what = ("power, Ethernet, USB and its two extra holes"
                if key == "rpi5" else "power input, Ethernet and USB")
        entries.append((("line", style.W_COMPONENT, colour, dash),
                        f"{MODEL_NAME[key]}: {what}"))
    # Balloons are not in this entry: they are drawn in the line type and
    # colour of the model they point at, which the entries above already
    # show, and a blue sample would say they were dimension-coloured.
    entries.append(("dimension", "Dimension, extension and callout leader"))
    return entries


def render_rpi_comparison(*, drawing_no: str, version: str,
                          sheet_size: str = "A3",
                          view_bbox=None,
                          band_height: float | None = None) -> Sheet:
    """Build the comparison sheet and return it.

    *view_bbox* and *band_height* are the ones the rest of the family is
    drawn with, so that the outline lands on the same point of this page as
    it does on the models' own sheets and the bound copy can be flipped
    through.
    """
    require_shared()
    base = BOARDS[MODELS[0]]
    o = base.outline
    notes, src_lines = _notes(), _sources()
    bbox = view_bbox or (0.0, min(f.y0 for key in MODELS
                                  for f in BOARDS[key].features),
                         max(f.x1 for key in MODELS
                             for f in BOARDS[key].features), o.height)
    view_needs = (bbox[3] - bbox[1]) + VIEW_MARGIN_TOP + VIEW_MARGIN_BOTTOM
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src_lines),
        max_height=style.SHEET_SIZES[sheet_size][1] - 2 * style.FRAME_MARGIN
        - view_needs - 6.0)
    if band_height is not None:
        band_h = max(band_h, band_height)

    sheet = Sheet(sheet_size, TitleBlock(
        title=TITLE.upper(),
        subtitle=SUBTITLE,
        drawing_no=drawing_no,
        rev="A",
        version=version,
        drawn_by="generated",
        units="mm",
        material="-  not a made part",
        # Nothing here is a manufactured feature and every figure is read off
        # another drawing, so this sheet must not assert a tolerance of its
        # own: the three it compares each carry their own, and two of them
        # disagree about the mounting hole diameter.
        tolerance=f"reference only - governed by {MODEL_SHEET_LIST}",
    ), notes_band_height=band_h)
    sheet.draw_frame()
    c = sheet.canvas

    view = View.fit(sheet.area, bbox, margin=VIEW_MARGIN_SIDE,
                    margin_top=VIEW_MARGIN_TOP,
                    margin_bottom=VIEW_MARGIN_BOTTOM)
    sheet.title.scale = view.scale_label
    board = Rect(view.x(0), view.y(0), view.d(o.width), view.d(o.height))

    # --- geometry -----------------------------------------------------------
    # The per-model connectors first, then the shared geometry over them: the
    # outline is the one line a reader traces first and it must not be broken
    # by a connector that happens to cross it.
    clusters: list[tuple[int, list, tuple]] = []
    for number in sorted(FEATURE_NUMBERS):
        if number in SHARED_NUMBERS:
            continue
        for group in _clusters(number):
            for key, f in group:
                colour, dash = MODEL_LINE[key]
                _rect(c, view, _box(f), colour, dash)
            clusters.append((number, [_box(f) for _, f in group],
                             tuple(k for k, _ in group)))

    for number in SHARED_NUMBERS:
        # require_shared has already proved the three are the same box, so
        # the first model's is drawn rather than a union of them, which
        # would have quietly widened to cover a disagreement.
        shared_box = _box(_features(number)[0][1])
        _rect(c, view, shared_box, style.C_LINE, None)
        clusters.append((number, [shared_box], MODELS))

    aux = [h for h in BOARDS["rpi5"].holes if h.kind == "aux"]
    aux_colour, aux_dash = MODEL_LINE["rpi5"]
    for h in aux:
        px, py = view.pt(h.x, h.y)
        c.circle(px, py, view.d(h.dia / 2), w=style.W_COMPONENT,
                 colour=aux_colour, dash=aux_dash, fill="#ffffff")
        dims.centre_mark(c, px, py, view.d(h.dia / 2), colour=aux_colour)

    outline_path(c, view, base)
    # Every model's MT1 to MT4 are at the same centres; the diameters differ
    # by five hundredths and are tabulated, so the circle drawn is the first
    # model's and the keep-out is the specification's, not any one drawing's.
    draw_holes(c, view, tuple(replace(h, keepout_dia=HAT_KEEPOUT)
                              for h in base.holes if h.kind == "mount"))

    # --- annotation on the view ---------------------------------------------
    obstacles = Obstacles()
    edge_only = Obstacles()

    # The two Pi 5 holes are named on the view rather than left to the
    # schedule: they are the one feature a reader of the other three sheets
    # has never seen, and a dotted circle among four solid ones does not say
    # what it is.  Placed by hand because there are two of them and the space
    # beside each is known: AUX1 has open board to its right, AUX2 has the
    # gap between the GPIO header and the USB ports to its left.
    for h, side in zip(sorted(aux, key=lambda h: h.y), ("start", "end")):
        px, py = view.pt(h.x, h.y)
        dx = view.d(h.dia / 2) + 1.6
        tx = px + dx if side == "start" else px - dx
        c.text(tx, py, h.label, size=style.T_LABEL, colour=aux_colour,
               anchor=side, baseline="middle", bold=True)
        w = style.text_width(h.label, style.T_LABEL, bold=True)
        lo = tx if side == "start" else tx - w
        obstacles.add_rect(lo, py - style.T_LABEL, lo + w,
                           py + style.T_LABEL, pad=1.0, weight=HARD)

    cluster_rect: dict[int, int] = {}
    for n, (_, boxes, _) in enumerate(clusters):
        u = _union(boxes)
        obstacles.add_rect(*view.pt(u[0], u[1]), *view.pt(u[2], u[3]),
                           pad=0.8)
        cluster_rect[n] = len(obstacles.rects) - 1
    for h in list(base.holes) + list(aux):
        obstacles.add_circle(*view.pt(h.x, h.y),
                             view.d(max(h.dia, HAT_KEEPOUT) / 2) + 1.0)

    # The corner radius callout, the board outline and the two overall
    # dimensions are all drawn after the balloons, so the library's own
    # reservations for them go in here, at the same point in the obstacle
    # list a board sheet puts them.
    reserve_radius_callout(sheet, view, base, board, obstacles)
    reserve_overall_dimensions(sheet, view, base, board, obstacles, edge_only)

    items: list[_Ballooned] = []
    # Largest first, as on a board sheet: the big boxes have the least
    # freedom and placing them early stops a small one taking the only spot.
    order = sorted(range(len(clusters)),
                   key=lambda n: -_area(_union(clusters[n][1])))
    for n in order:
        number, boxes, keys = clusters[n]
        foreign = [b for m, other in enumerate(clusters) if m != n
                   for b in other[1]]
        tips = _anchors(view, boxes, foreign)
        colour, dash = (MODEL_LINE[keys[0]] if len(keys) == 1
                        else SHARED_LINE)
        items.append(_Ballooned(str(number), tips[0], tips, cluster_rect[n],
                                colour=colour, dash=dash))
    bounds = sheet.area.inset(4.0)
    # Through the module, not through a name bound at import:
    # tools/check_balloons.py replaces board_sheet.place_balloons to watch
    # where every leader ends up, and a direct import would leave this sheet
    # the only one it could not see.
    bs.place_balloons(items, obstacles, bounds, c, position_only=edge_only)

    # --- dimensions ---------------------------------------------------------
    # Only what the three individual sheets cannot say between them: that the
    # outline they are all drawn on is one and the same.  Hole and connector
    # positions are dimensioned there and tabulated here, so this sheet
    # carries the library's outline frame and nothing else.
    draw_outline_frame(sheet, view, base, board)

    # --- annotation column --------------------------------------------------
    rows = _feature_rows()
    block = sheet.column_block(sheet.table_height("FEATURE SCHEDULE",
                                                  len(rows)))
    sheet.table(block, "FEATURE SCHEDULE",
                ["#", "ON", "FEATURE", "X EXTENT mm", "Y EXTENT mm"], rows,
                ["middle", "start", "start", "end", "end"])

    rows = _hole_rows()
    block = sheet.column_block(sheet.table_height("HOLE SCHEDULE", len(rows)))
    # The two columns that differ between models carry the model order in
    # their heading rather than in a note under the table: a note that says
    # "three values are 3B, 4B, 5 in that order" is a note the reader has to
    # find before the table means anything.
    sheet.table(block, "HOLE SCHEDULE",
                ["ID", "X mm", "Y mm", "ON", "DIA mm  3B / 4B / 5",
                 "KEEPOUT mm  3B / 4B / 5"], rows,
                ["start", "end", "end", "start", "end", "end"])

    place_legend_and_notes(sheet, _legend(), notes, src_lines, band_cols,
                           STEM)

    sheet.draw_title_block()
    return sheet
