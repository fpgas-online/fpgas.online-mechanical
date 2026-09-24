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

import math
from dataclasses import replace

from raspberry_pi.boards import BOARDS, FEATURE_NUMBERS
from tools.layout import PMOD_HAT_SHEET, drawing_name, slug

from . import board_sheet as bs
from . import dims, style
from .board_sheet import (BALLOON_R, HARD, OVERALL_GAP, VIEW_MARGIN_BOTTOM,
                          VIEW_MARGIN_SIDE, VIEW_MARGIN_TOP, Obstacles,
                          _Ballooned, draw_holes, draw_outline_frame,
                          note_blocks,
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
#: enough to photocopy, and distinct from the black of the shared geometry
#: and from the blue of the dimensions.
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

#: What the header's balloon is drawn in, and every leader: the header is
#: the same part on all three models, and a leader goes to a place all three
#: put a part in.  Continuous and black, like everything else on this sheet
#: that the models share.
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


def _places() -> list[list[tuple[str, object]]]:
    """Where the models put their unshared parts, and what each puts there.

    A place is a set of feature outlines that overlap one another, taken
    across every model and every number not drawn once as shared, and
    joined transitively.  On these boards that is the power corner and the
    bays down the right-hand edge, and each holds one part from each model
    -- not always the same part, because the Pi 4B swapped its Ethernet jack
    and its USB ports round.  So a place is what gets a leader, and each
    model's part in it gets a balloon on that leader; see _balloon_groups.

    The members come back in model order, and a place holding anything but
    exactly one part from each model stops the render: the balloons on its
    leader are read by position, left to right in model order, and a place
    with a model missing or doubled would put a number in the wrong column
    without anything on the sheet showing it.
    """
    groups: list[list[tuple[str, object]]] = []
    for number in sorted(FEATURE_NUMBERS):
        if number in SHARED_NUMBERS:
            continue
        for key, f in _features(number):
            touching = [g for g in groups
                        if any(_overlaps(_box(f), _box(o)) for _, o in g)]
            groups = [g for g in groups if all(g is not t for t in touching)]
            groups.append([(key, f)] + [m for g in touching for m in g])
    for g in groups:
        g.sort(key=lambda m: MODELS.index(m[0]))
        keys = tuple(k for k, _ in g)
        if keys != MODELS:
            raise SystemExit(
                f"{STEM}: the parts at {_union([_box(f) for _, f in g])} "
                f"belong to {', '.join(MODEL_NAME[k] for k in keys)}, not "
                "to one each of " + ", ".join(MODEL_NAME[k] for k in MODELS)
                + "; a leader there cannot carry one balloon per model in "
                "model order, so this sheet has to balloon them another way")
    return groups


def _union(boxes) -> tuple[float, float, float, float]:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _common(boxes) -> tuple[float, float, float, float]:
    """Where every one of *boxes* overlaps: the part of a place a dot owns."""
    return (max(b[0] for b in boxes), max(b[1] for b in boxes),
            min(b[2] for b in boxes), min(b[3] for b in boxes))


#: How far inside every outline of its place a leader's dot must sit.  A dot
#: on or beside an edge of one of three superimposed outlines reads as
#: pointing at that one outline.
DOT_CLEAR = 0.7

#: How far a leader leans off the horizontal (or, below the board, off the
#: vertical).  ISO 128-22 wants a leader at an angle to the lines it meets
#: rather than parallel to them; square to the connector edges, a leader
#: would run parallel to the outlines above and below it.  Fifteen degrees
#: says it is deliberate and keeps the top row's ring clear of the corner
#: radius callout above it.
LEADER_LEAN = math.tan(math.radians(15.0))

#: Clear paper between the furthest connector outline on a side and the
#: first ring there: enough leader outside the connector to see which way
#: it goes, and no more.
LEADER_OUT = 7.0


def _dot(view: View, boxes, lean: float = 0.0) -> tuple[float, float]:
    """A leader's dot for a place, in sheet millimetres.

    The centre of the region every outline in the place covers, moved *lean*
    sheet millimetres down, so that a leaning leader can straddle the middle
    of its place: dot half the rise below it, ring half the rise above.
    Stops the render if that point is not DOT_CLEAR inside every outline.
    """
    x0, y0, x1, y1 = _common(boxes)
    cx, cy = view.pt((x0 + x1) / 2, (y0 + y1) / 2)
    cy -= lean
    mx, my = (cx - view.x(0)) / view.scale, (cy - view.y(0)) / view.scale
    if not (x0 + DOT_CLEAR <= mx <= x1 - DOT_CLEAR
            and y0 + DOT_CLEAR <= my <= y1 - DOT_CLEAR):
        raise SystemExit(
            f"{STEM}: the outlines at {_union(boxes)} have no point "
            f"{DOT_CLEAR} mm inside all of them where the leader's dot "
            "should go, so one dot cannot stand for the whole place")
    return cx, cy


def _balloon_groups(view: View, board: Rect, places, shared
                    ) -> list[tuple[list, _Ballooned]]:
    """The balloons, one leader to each place, and the boxes each points at.

    A place holds one part from each model, so its leader carries a balloon
    for each: ISO 6433's part references grouped on one leader, ring against
    ring, left to right in model order, each drawn in its model's line type.
    Where two models put the same part in a place the number repeats; where
    the Pi 4B puts a different part there, its column says so.  That is the
    whole comparison in one row, and nothing about it depends on which
    outline a dot lands in, which on this sheet nothing could tell apart.

    The places on the right-hand edge have their rows in one column outside
    the board, each straddling the middle of its place with its leader, so
    the leaders are short and parallel and cannot cross.  A place on the bottom edge has its
    row below the board, and the header, which is one part on all three,
    has a single plain balloon in the lane between the board and the overall
    width above it, leaning away from the width's value.  *shared* is that
    part's number and box.
    """
    out: list[tuple[list, _Ballooned]] = []
    width = BOARDS[MODELS[0]].outline.width
    right = [g for g in places if max(f.x1 for _, f in g) >= width]
    below = [g for g in places if all(g is not r for r in right)
             and min(f.y0 for _, f in g) <= 0.0]
    stray = [g for g in places if all(g is not o for o in right + below)]
    if stray:
        raise SystemExit(
            f"{STEM}: the parts at {_union([_box(f) for _, f in stray[0]])} "
            "reach neither the right-hand edge nor the bottom one, and those "
            "are the only two sides this sheet has a column of balloons on")

    def group(g, dot, ring):
        labels = [(str(f.number), *MODEL_LINE[k]) for k, f in g]
        first, rest = labels[0], tuple(labels[1:])
        return ([_box(f) for _, f in g],
                _Ballooned(first[0], dot, (dot,), colour=first[1],
                           dash=first[2], at=ring, also=rest,
                           leader_colour=SHARED_LINE[0]))

    if right:
        ring_x = (view.x(max(f.x1 for g in right for _, f in g))
                  + LEADER_OUT + BALLOON_R)
        for g in right:
            boxes = [_box(f) for _, f in g]
            c0 = _common(boxes)
            mid_x = view.x((c0[0] + c0[2]) / 2)
            mid_y = view.y((c0[1] + c0[3]) / 2)
            rise = LEADER_LEAN * (ring_x - mid_x)
            dot = _dot(view, boxes, lean=rise / 2)
            out.append(group(g, dot, (ring_x, mid_y + rise / 2)))
    if below:
        ring_y = (view.y(min(f.y0 for g in below for _, f in g))
                  - LEADER_OUT - BALLOON_R)
        for g in below:
            boxes = [_box(f) for _, f in g]
            dot = _dot(view, boxes)
            out.append(group(g, dot, (dot[0] - LEADER_LEAN
                                      * (dot[1] - ring_y), ring_y)))

    number, box = shared
    dot = view.pt((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    # Halfway up the lane between the outline and the band that
    # reserve_overall_dimensions holds under the width's dimension line,
    # which reaches 1.0 mm below the line and is padded 1.2 mm more.  Half
    # the gap was 0.4 mm into that band, and the placer refused it.
    ring_y = board.y1 + (OVERALL_GAP - 1.0 - 1.2) / 2
    away = -1.0 if dot[0] < (board.x + board.x1) / 2 else 1.0
    colour, dash = SHARED_LINE
    out.append(([box], _Ballooned(
        str(number), dot, (dot,), colour=colour, dash=dash,
        at=(dot[0] + away * LEADER_LEAN * (ring_y - dot[1]), ring_y))))
    return out


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
        "A balloon number means the same part on every Raspberry Pi sheet. "
        "Each leader goes to one place and carries a balloon for each model, "
        f"left to right {', '.join(MODEL_NAME[k] for k in MODELS)}, the ring "
        "in that model's own line type and colour, so a row reads which part "
        "each model puts there. The 40-pin header, the same part on all "
        "three, has one plain balloon.",
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
    # A row of balloons on one leader is a key of its own: ISO 6433 groups
    # references on one leader for parts fitted together, and here they are
    # the alternatives, one per model, which a reader should not have to
    # find a note to learn.  The rings are drawn in the model line types
    # above, in the order they stand in on the view.
    entries.append((("balloons", style.W_THIN,
                     tuple(MODEL_LINE[k][0] for k in MODELS),
                     tuple(MODEL_LINE[k][1] for k in MODELS)),
                    "Balloons on one leader: one per model, "
                    + ", ".join(MODEL_NAME[k] for k in MODELS)
                    + ", left to right"))
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
    places = _places()
    for g in places:
        for key, f in g:
            colour, dash = MODEL_LINE[key]
            _rect(c, view, _box(f), colour, dash)

    # SHARED_NUMBERS is the header alone, and one balloon is drawn for it.
    (shared_number,) = SHARED_NUMBERS
    # require_shared has already proved the three are the same box, so the
    # first model's is drawn rather than a union of them, which would have
    # quietly widened to cover a disagreement.
    shared_box = _box(_features(shared_number)[0][1])
    _rect(c, view, shared_box, style.C_LINE, None)

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

    groups = _balloon_groups(view, board, places,
                             (shared_number, shared_box))
    items: list[_Ballooned] = []
    for boxes, item in groups:
        u = _union(boxes)
        obstacles.add_rect(*view.pt(u[0], u[1]), *view.pt(u[2], u[3]),
                           pad=0.8)
        item.own = len(obstacles.rects) - 1
        items.append(item)
    for h in list(base.holes) + list(aux):
        obstacles.add_circle(*view.pt(h.x, h.y),
                             view.d(max(h.dia, HAT_KEEPOUT) / 2) + 1.0)

    # The corner radius callout, the board outline and the two overall
    # dimensions are all drawn after the balloons, so the library's own
    # reservations for them go in here, at the same point in the obstacle
    # list a board sheet puts them.
    reserve_radius_callout(sheet, view, base, board, obstacles)
    # The three model sheets keep their X chain on the bottom edge (every
    # Pi votes for it under _x_chain_edge), so this sheet says so rather
    # than take the default, and lines up with them by construction.
    # The overall height goes up the left, not the right as on a board
    # sheet: the left is where a board sheet's ordinate chain is, and this
    # sheet has none, while the right is where the balloon rows are.
    reserve_overall_dimensions(sheet, view, base, board, obstacles, edge_only,
                               chain_edge="bottom", height_edge="left")

    bounds = sheet.area.inset(4.0)
    # Every balloon here has its place already, from _balloon_groups, so the
    # placer moves none of them; it draws them, and it is called at all so
    # that tools/check_balloons.py, which watches it, sees this sheet's
    # leaders against the same obstacles as every other sheet's.  Through the
    # module, not through a name bound at import, or the check could not.
    bs.place_balloons(items, obstacles, bounds, c, position_only=edge_only)

    # --- dimensions ---------------------------------------------------------
    # Only what the three individual sheets cannot say between them: that the
    # outline they are all drawn on is one and the same.  Hole and connector
    # positions are dimensioned there and tabulated here, so this sheet
    # carries the library's outline frame and nothing else.
    draw_outline_frame(sheet, view, base, board, chain_edge="bottom",
                       height_edge="left")

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
