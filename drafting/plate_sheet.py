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

from data.mounting_plate import (PLACEMENTS, PMOD_BODY, PMOD_ROW_Y,
                                 PMOD_SLOT_X, PLATE, USB_C)
from data.schema import BoardSpec, Hole, Slot
from data.tinytapeout_boards import BOARDS as TT_BOARDS

from . import dims, style
from .board_sheet import (Obstacles, _place_notes_and_sources,
                          draw_legend, legend_height, note_blocks,
                          notes_spill_needed, outline_path)
from .canvas import Canvas
from .sheet import Rect, Sheet, TitleBlock
from .view import View

#: Room above and below the plate view.  Nothing but hole labels goes above.
PLATE_MARGIN_TOP = 12.0
PLATE_MARGIN_BOTTOM = 40.0

BOARD_HOLE = "#a00000"
PLATE_HOLE = "#006060"
#: The USB-C outlines.  Distinct from both hole colours because it is neither
#: a hole nor a plate feature: it is an opening a chassis has to provide.
USB_MARK = "#7a4a00"


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
               dash=style.D_CENTRE)
        dims.centre_mark(c, x0, y0, r, colour=colour, over=1.0)
        dims.centre_mark(c, x1, y1, r, colour=colour, over=1.0)
    else:
        dims.centre_mark(c, (x0 + x1) / 2, (y0 + y1) / 2, r, colour=colour,
                         over=1.0)


#: Directions a hole label is tried in, nearest and clearest first.
_LABEL_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0),
               (0, 1), (0, -1)]


def place_label(c: Canvas, obstacles: Obstacles, anchor: tuple[float, float],
                clear: float, text: str, colour: str,
                others: list[tuple[float, float]] | None = None,
                bounds: Rect | None = None
                ) -> tuple[float, float, float, float]:
    """Put *text* near *anchor*, in the first spot free of *obstacles*.

    Draws a short leader when the label ends up far enough away that which
    feature it belongs to would otherwise be a guess.  Returns the box it
    occupied, so the caller can reserve it against the next label.

    *others* are the anchors of the neighbouring features.  A label that ends
    up nearer one of those than to its own feature reads as belonging to the
    wrong one: on the mounting plate, H3 and slot S1 sit nine millimetres
    apart and their labels swapped over each other's features.

    *bounds* keeps the label inside its own view.  The fitting guide draws
    five small views side by side, each with its own obstacle list, and two
    labels from neighbouring views drifted into the gap between them and
    landed on each other.
    """
    px, py = anchor
    tw = style.text_width(text, style.T_LABEL, bold=True)
    th = style.text_height(style.T_LABEL)
    best, best_score = None, None
    # Reaching further out is better than landing on a neighbour: on the
    # half-scale fitting guide views the near positions are all taken.
    for radius in (clear + 2.2, clear + 5.0, clear + 8.0, clear + 12.0,
                   clear + 16.0, clear + 21.0):
        for dx, dy in _LABEL_DIRS:
            cx = px + dx * (radius + tw / 2)
            cy = py + dy * (radius + th / 2)
            if bounds is not None and not (
                    bounds.x + tw / 2 <= cx <= bounds.x1 - tw / 2
                    and bounds.y + th / 2 <= cy <= bounds.y1 - th / 2):
                continue
            mine = math.dist((cx, cy), (px, py))
            stolen = any(math.dist((cx, cy), o) < mine for o in (others or ()))
            half_h = (th + style.descender(style.T_LABEL)) / 2
            score = (obstacles.rect_hits(cx - tw / 2, cy - half_h,
                                         cx + tw / 2, cy + half_h) * 100
                     + stolen * 70 + radius)
            if best_score is None or score < best_score:
                best, best_score = (cx, cy), score
        if best_score is not None and best_score < 70:
            break
    if best is None:
        raise SystemExit(
            f"no room anywhere for label {text!r} inside its view")
    cx, cy = best
    gap = math.dist((px, py), (cx, cy)) - clear - max(tw, th) / 2
    if gap > 1.5:
        ang = math.atan2(cy - py, cx - px)
        c.line(px + (clear + 1.0) * math.cos(ang),
               py + (clear + 1.0) * math.sin(ang),
               cx - (max(tw, th) / 2 + 0.8) * math.cos(ang),
               cy - (max(tw, th) / 2 + 0.8) * math.sin(ang),
               w=style.W_THIN, colour=colour)
    c.text(cx, cy, text, size=style.T_LABEL, colour=colour, bold=True,
           anchor="middle", baseline="middle")
    # The drawn box, descender included: reserving only the cap height let the
    # next label sit a fraction of a millimetre into this one.
    half_h = (th + style.descender(style.T_LABEL)) / 2
    return (cx - tw / 2, cy - half_h, cx + tw / 2, cy + half_h)


def draw_plate_holes(c: Canvas, view: View, spec: BoardSpec,
                     labels: dict[int, str] | None = None,
                     highlight: set[int] | None = None,
                     extra: Obstacles | None = None,
                     slot_labels: dict[int, str] | None = None,
                     bounds: Rect | None = None) -> Obstacles:
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

    # Every *labelled* feature's anchor, so a label can be kept nearer its own
    # feature than to any other.  Features drawn faint carry no label, so they
    # cannot steal one and must not push labels around.
    anchors = [view.pt(h.x, h.y) for i, h in enumerate(spec.holes)
               if labels and i in labels
               and not (highlight is not None and i not in highlight)]
    anchors += [view.pt((sl.x0 + sl.x1) / 2, (sl.y0 + sl.y1) / 2)
                for i, sl in enumerate(spec.slots)
                if slot_labels and i in slot_labels]

    def others(mine: tuple[float, float]) -> list[tuple[float, float]]:
        return [a for a in anchors if a != mine]

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
        box = place_label(c, obstacles, (px, py), r, labels[i], colour,
                          others((px, py)), bounds)
        # Reserve it: nothing stopped the next label landing on this one.
        obstacles.add_rect(*box, pad=1.5)

    # Slot labels go through the same placer, so they cannot land on the datum
    # marker or the ordinate chain the way a fixed offset did.
    for i, sl in enumerate(spec.slots):
        if not (slot_labels and i in slot_labels):
            continue
        mx, my = view.pt((sl.x0 + sl.x1) / 2, (sl.y0 + sl.y1) / 2)
        half = view.d(max(abs(sl.x1 - sl.x0), abs(sl.y1 - sl.y0)) / 2
                      + sl.width / 2)
        box = place_label(c, obstacles, (mx, my), half, slot_labels[i],
                          BOARD_HOLE, others((mx, my)), bounds)
        obstacles.add_rect(*box, pad=1.5)
    # Returned so a caller labelling anything else on the same view carries on
    # from here: the USB-C marks were placed against a set that did not know
    # where the hole labels had gone, and landed on three of them.
    return obstacles


def _group_key() -> str:
    """Spell out the mixed shuttle-range / board-revision group names.

    The USED BY column mixes two naming schemes because the boards do: three
    early revisions each covered a run of shuttles and are known by that run,
    while v3.2 and v3.3 have shipped on none and can only be named by revision.
    Rather than assert that mapping in prose it is read back out of the data,
    so the key cannot drift from the labels it explains.
    """
    parts = []
    bare = []
    for name, pl in PLACEMENTS.items():
        if pl["shuttles"]:
            parts.append(f"{name} = " + ", ".join(pl["revisions"]))
        else:
            bare.append(name)
    if bare:
        parts.append(_and(bare) + " = themselves, no shuttle yet")
    return "; ".join(parts)


def _and(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _plate_text(spec) -> tuple[list[str], list[str]]:
    """The plate sheet's notes and sources, built before the sheet exists."""
    web_a, web_b, web = tightest_web(spec)
    notes = [
        "All dimensions in millimetres. The datum symbol marks the origin: "
        "the plate's lower-left corner, X right, Y up, seen from the side "
        "the board mounts on.",
        "Hole positions are tabulated, not dimensioned on the view: there are "
        "too many to dimension and keep it readable. A slot row gives its two "
        "end centres; DIA/WIDTH is the slot width, LENGTH is overall.",
        "USED BY reads <group>:<hole>; MT1 to MT4 are the board's own hole "
        "IDs. Groups, by board revision: " + _group_key() + ".",
        "The three PMOD envelopes are not machined features. They mark where "
        "the Pmod host pin fields end up, the same place for every board "
        "revision. That is the point of the plate.",
    ] + list(spec.notes) + [
        "Fit the plate to its chassis before the board: the fixings sit in the "
        f"border, which a board overhangs. Least material between features is "
        f"{web:.2f} mm, between {web_a} and {web_b}.",
        "Drawing TT-MP-02 shows which holes each revision uses.",
    ]
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
           for s in spec.sources]
    return notes, src


#: The plate sheets' key.  A board fastener and a plate fixing differ only in
#: the colour of their circle, which a monochrome print loses, so both are
#: named here as well as being tabulated separately.
PLATE_LEGEND = [
    ("outline", "Plate edge"),
    (BOARD_HOLE, "Hole or slot for a demo board fastener"),
    (PLATE_HOLE, "Plate fixing, into the chassis"),
    ("centre", "Slot axis"),
    ("component", "Pmod host pin field, where a board's hosts land"),
    ("phantom", "Pmod connector body, overhanging the front edge"),
    ("usbc", "USB-C connector, one position per board version"),
    ("dimension", "Dimension, extension and leader"),
]

GUIDE_LEGEND = [
    ("outline", "Plate edge"),
    (BOARD_HOLE, "Hole or slot this revision uses"),
    ("phantom", "Holes it does not use, and its board outline"),
]


def holes_by_version(spec) -> list[tuple[str, list[str]]]:
    """Which plate holes and slots each board version uses, in version order.

    The hole table is indexed by hole and says which versions use it, which
    answers "what is this hole for".  A user of the plate has the opposite
    question -- "I have this board, which holes do I use" -- so it is also
    given the other way round.
    """
    labels, _, _ = hole_ids(spec)
    used: dict[str, list[str]] = {name: [] for name in PLACEMENTS}
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            continue
        for part in h.label.split("+"):
            group = part.split(":")[0]
            if group in used:
                used[group].append(labels[i])
    for n, sl in enumerate(spec.slots, 1):
        for part in sl.label.split("+"):
            group = part.split(":")[0]
            if group in used:
                used[group].append(f"S{n}")
    for name, ids in used.items():
        want = len(TT_BOARDS[PLACEMENTS[name]["revision"]].holes)
        if len(ids) != want:
            raise SystemExit(
                f"{name} uses {len(ids)} plate positions "
                f"({', '.join(ids)}) but its board has {want} mounting "
                "holes; the plate must serve every one of them")
    return [(name, sorted(ids, key=_id_sort)) for name, ids in used.items()]


def _id_sort(label: str) -> tuple[int, int]:
    return (0 if label.startswith("H") else 1, int(label[1:]))


def hole_ids(spec) -> tuple[dict[int, str], list[int], list[int]]:
    """Assign H1.. to the board holes and P1.. to the plate fixings.

    One definition, so the view, the tables and the notes cannot disagree
    about which hole is which.
    """
    labels: dict[int, str] = {}
    board_ids: list[int] = []
    plate_ids: list[int] = []
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            plate_ids.append(i)
            labels[i] = f"P{len(plate_ids)}"
        else:
            board_ids.append(i)
            labels[i] = f"H{len(board_ids)}"
    return labels, board_ids, plate_ids


def tightest_web(spec) -> tuple[str, str, float]:
    """The two features with the least material between them, and how much.

    Worked out from the hole table rather than written into the note by hand.
    The note used to say H2/H3; those two are 78 mm apart, and the 1.6 mm web
    is between H1 and H2.  A note that names generated IDs has to be generated
    from the same data or it drifts the first time a hole moves.
    """
    labels, _, _ = hole_ids(spec)
    items = [(labels[i], h.x, h.y, h.dia / 2) for i, h in enumerate(spec.holes)]
    for n, sl in enumerate(spec.slots, 1):
        # A slot's two end centres, each with the slot's own end radius.
        items.append((f"S{n}", sl.x0, sl.y0, sl.width / 2))
        items.append((f"S{n}", sl.x1, sl.y1, sl.width / 2))
    best = None
    for i, (na, ax, ay, ar) in enumerate(items):
        for nb, bx, by, br in items[i + 1:]:
            if na == nb:
                continue
            web = math.dist((ax, ay), (bx, by)) - ar - br
            if best is None or web < best[2]:
                best = (na, nb, web)
    return best


def render_plate(*, drawing_no: str, date: str, sheet_size: str = "A3") -> Sheet:
    spec = PLATE
    o = spec.outline
    notes, src = _plate_text(spec)
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src),
        max_height=style.SHEET_SIZES[sheet_size][1]
        - 2 * style.FRAME_MARGIN - o.height
        - PLATE_MARGIN_TOP - PLATE_MARGIN_BOTTOM - 6.0)
    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(), subtitle=spec.subtitle, drawing_no=drawing_no,
        rev="A", date=date, drawn_by="generated",
        # The plate is a two-sheet set: this one and the fitting guide, which
        # each cross-reference the other.  Both said "1 OF 1".
        sheet="1 OF 2",
        material="3 mm acrylic or 1.6 mm FR4",
        # Self-contained: "see kerf note" was a cross-reference to a note
        # whose number is generated, so it could not be given.
        tolerance="edge +/-0.20   hole pos +/-0.10   allow for cutter kerf"),
        notes_band_height=band_h)
    sheet.draw_frame()
    c = sheet.canvas

    view = View.fit(sheet.area, (0, 0, o.width, o.height), margin=40.0,
                    margin_top=PLATE_MARGIN_TOP,
                    margin_bottom=PLATE_MARGIN_BOTTOM)
    sheet.title.scale = view.scale_label
    plate = Rect(view.x(0), view.y(0), view.d(o.width), view.d(o.height))

    outline_path(c, view, spec)

    labels, _, plate_ids = hole_ids(spec)
    # Labels must also keep off the plate outline itself: the fixings near the
    # right-hand edge would otherwise put their label straight on it.
    edge = Obstacles()
    o = spec.outline
    for a, b in (((0, 0), (o.width, 0)), ((o.width, 0), (o.width, o.height)),
                 ((o.width, o.height), (0, o.height)), ((0, o.height), (0, 0))):
        edge.add_segment(*view.pt(*a), *view.pt(*b))

    # The corner radius callout is drawn further down, after the labels are
    # placed, so its span is worked out here and reserved.  Computing it twice
    # is what let a balloon land on the same callout on the board sheets.
    radius_label = f"R{o.corner_radius:.2f} (4 places), plate edge"
    radius_w = style.text_width(radius_label, style.T_LABEL)
    radius_elbow = min(plate.x1 + 8.0, sheet.area.x1 - 6.2 - radius_w)
    edge.add_rect(min(radius_elbow, radius_elbow + radius_w + 8.0),
                  plate.y1 + 2.0,
                  max(radius_elbow, radius_elbow + radius_w + 8.0),
                  plate.y1 + 9.0, pad=1.2)
    edge.add_segment(*view.pt(o.width - o.corner_radius * 0.3,
                              o.height - o.corner_radius * 0.3),
                     radius_elbow, plate.y1 + 5.0)
    # The Pmod host grid is the reason the plate exists, so it is drawn and
    # dimensioned even though it is not a machined feature.  Its envelopes and
    # captions are worked out before the hole labels are placed and handed to
    # the placer: drawn afterwards without being reserved, caption "PMOD 1"
    # and hole label "H3" ended up 0.48 mm apart and printed as one word.
    bx0, bx1, by0, by1 = PMOD_BODY
    envelopes = []
    for i, px in enumerate(PMOD_SLOT_X):
        sx, sy = view.pt(px, PMOD_ROW_Y)
        half = view.d(6.35)
        cap = f"PMOD {i + 1}"
        cap_y = sy + view.d(2.9) + 2.2
        cap_w = style.text_width(cap, style.T_LABEL)
        body = (view.x(px + bx0), view.y(PMOD_ROW_Y + by0),
                view.x(px + bx1), view.y(PMOD_ROW_Y + by1))
        envelopes.append((sx, sy, half, cap, cap_y, cap_w, body))
        edge.add_rect(min(body[0], body[2]), min(body[1], body[3]),
                      max(body[0], body[2]), max(body[1], body[3]), pad=0.8)
        edge.add_rect(sx - cap_w / 2, cap_y - style.descender(style.T_LABEL),
                      sx + cap_w / 2, cap_y + style.T_LABEL, pad=1.2)

    # Where each revision's USB-C lands.  A chassis has to open for it, and it
    # is in a different place on every revision: TT01-03 puts it on the front
    # edge beside the Pmod hosts, every later revision at the back.
    for name, (ux0, uy0, ux1, uy1) in USB_C.items():
        r = (view.x(ux0), view.y(uy0), view.x(ux1), view.y(uy1))
        edge.add_rect(min(r[0], r[2]), min(r[1], r[3]),
                      max(r[0], r[2]), max(r[1], r[3]), pad=0.8)

    for sl in spec.slots:
        draw_slot(c, view, sl)
    usb_obstacles = draw_plate_holes(
        c, view, spec, labels, extra=edge,
        slot_labels={i: f"S{i + 1}" for i in range(len(spec.slots))})
    for name, (ux0, uy0, ux1, uy1) in USB_C.items():
        x0, y0 = view.pt(ux0, uy0)
        x1, y1 = view.pt(ux1, uy1)
        c.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0),
               weight=style.W_PHANTOM, colour=USB_MARK, dash=style.D_PHANTOM)
        box = place_label(c, usb_obstacles, ((x0 + x1) / 2, (y0 + y1) / 2),
                          max(abs(x1 - x0), abs(y1 - y0)) / 2, name, USB_MARK)
        usb_obstacles.add_rect(*box, pad=1.5)

    for sx, sy, half, cap, cap_y, _, body in envelopes:
        # The connector body, phantom, overhanging the plate's front edge --
        # which is the 2.78 mm the notes call the point of the design and
        # which nothing on this view used to show.  Drawn exactly as the board
        # sheets draw it, because it is the same connector: the pin field as
        # pins, the body as a type K rectangle.  Only the pin-field box was
        # here before, in the same line type as a board sheet's connector
        # body, so one line type meant two different pieces of geometry.
        c.rect(min(body[0], body[2]), min(body[1], body[3]),
               abs(body[2] - body[0]), abs(body[3] - body[1]),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash=style.D_PHANTOM)
        for col in range(6):
            for row in range(2):
                c.circle(sx + view.d((col - 2.5) * 2.54),
                         sy + view.d((row - 0.5) * 2.54),
                         view.d(0.5), w=style.W_PHANTOM,
                         colour=style.C_PHANTOM, fill="#ffffff")
        c.rect(sx - half - view.d(1.3), sy - view.d(2.54 / 2 + 1.3),
               (half + view.d(1.3)) * 2, view.d(2.54 + 2.6),
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT)
        c.text(sx, cap_y, cap, size=style.T_LABEL,
               colour=style.C_HIGHLIGHT, anchor="middle")

    dims.linear(c, view.pt(PMOD_SLOT_X[0], PMOD_ROW_Y),
                view.pt(PMOD_SLOT_X[1], PMOD_ROW_Y),
                plate.y - 8.0 - view.y(PMOD_ROW_Y), horizontal=True,
                text=f"{PMOD_SLOT_X[1] - PMOD_SLOT_X[0]:.2f} TYP")

    # Witness lines break where they cross a machined feature rather than
    # running through it.  The 9.00 ordinate runs the width of the plate to
    # reach its chain, and passed straight through hole H3 and slot S1 on the
    # way; a dimension line through a feature is exactly what ISO 128 forbids.
    dim_blockers = [
        (view.x(h.x) - view.d(h.dia / 2) - 1.0,
         view.y(h.y) - view.d(h.dia / 2) - 1.0,
         view.x(h.x) + view.d(h.dia / 2) + 1.0,
         view.y(h.y) + view.d(h.dia / 2) + 1.0)
        for h in spec.holes]
    for sl in spec.slots:
        pad = view.d(sl.width / 2) + 1.0
        dim_blockers.append(
            (min(view.x(sl.x0), view.x(sl.x1)) - pad,
             min(view.y(sl.y0), view.y(sl.y1)) - pad,
             max(view.x(sl.x0), view.x(sl.x1)) + pad,
             max(view.y(sl.y0), view.y(sl.y1)) + pad))

    x_extent = dims.ordinate_chain(
        c, [(view.x(v), f"{v:.2f}", view.y(PMOD_ROW_Y)) for v in PMOD_SLOT_X],
        plate.y, plate.y - 17.0, horizontal=True,
        zero_pos=plate.x, zero_from=plate.y, blockers=dim_blockers)
    y_extent = dims.ordinate_chain(
        c, [(view.y(PMOD_ROW_Y), f"{PMOD_ROW_Y:.2f}", view.x(PMOD_SLOT_X[0]))],
        plate.x, plate.x - 12.0, horizontal=False,
        zero_pos=plate.y, zero_from=plate.x, blockers=dim_blockers)

    dims.linear(c, (plate.x, plate.y), (plate.x1, plate.y),
                x_extent - 7.0 - plate.y, horizontal=True, value=o.width,
                ext_start=x_extent - 2.0)
    dims.linear(c, (plate.x, plate.y), (plate.x, plate.y1),
                y_extent - 7.0 - plate.x, horizontal=False, value=o.height,
                ext_start=y_extent - 2.0)
    dims.datum_marker(c, plate.x, plate.y, label="")
    dims.leader(c, view.pt(o.width - o.corner_radius * 0.3,
                           o.height - o.corner_radius * 0.3),
                (radius_elbow, plate.y1 + 5.0), radius_label)

    rows = []
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            continue
        # A round hole has no length to give, so the column is struck through
        # rather than left blank: a blank cell reads as a missing value.
        rows.append([labels[i], f"{h.x:.2f}", f"{h.y:.2f}", f"{h.dia:.2f}",
                     "-", h.label.replace("+", ", ")])
    for n, s in enumerate(spec.slots, 1):
        # Two values because a slot has two end centres; the note below says so.
        # LENGTH is the overall length, end to end, which is what a cutter or a
        # slot mill is set to.
        rows.append([f"S{n}", f"{s.x0:.2f} / {s.x1:.2f}",
                     f"{s.y0:.2f} / {s.y1:.2f}",
                     f"{s.width:.2f}", f"{s.length:.2f}",
                     s.label.replace("+", ", ")])
    block = sheet.column_block(sheet.table_height("BOARD MOUNTING HOLES", len(rows)))
    sheet.table(block, "BOARD MOUNTING HOLES",
                ["ID", "X mm", "Y mm", "DIA/WIDTH mm", "LENGTH mm", "USED BY"], rows,
                ["start", "end", "end", "end", "end", "start"])

    rows = [[labels[i], f"{spec.holes[i].x:.2f}", f"{spec.holes[i].y:.2f}",
             f"{spec.holes[i].dia:.2f}"] for i in plate_ids]
    block = sheet.column_block(sheet.table_height("PLATE FIXING HOLES", len(rows)))
    sheet.table(block, "PLATE FIXING HOLES",
                ["ID", "X mm", "Y mm", "DIA mm"], rows,
                ["start", "end", "end", "end"])

    spill = notes_spill_needed(sheet, notes, src, band_cols)
    want = legend_height(len(PLATE_LEGEND)) + (spill + 4.0 if spill else 0.0)
    if sheet.column_remaining < want:
        raise SystemExit(
            f"the plate sheet's annotation column cannot hold both the legend "
            f"and the notes' tail ({want:.0f} mm wanted, "
            f"{sheet.column_remaining:.0f} mm left); shorten the notes")
    draw_legend(sheet, PLATE_LEGEND)
    _place_notes_and_sources(sheet, notes, src, columns=band_cols, spill=spill)

    sheet.draw_title_block()
    return sheet


def render_fitting_guide(*, drawing_no: str, date: str,
                         sheet_size: str = "A3") -> Sheet:
    spec = PLATE
    o = spec.outline
    sheet = Sheet(sheet_size, TitleBlock(
        title="TT MOUNTING PLATE FITTING GUIDE",
        subtitle="Which holes each demo board revision uses",
        drawing_no=drawing_no, rev="A", date=date, drawn_by="generated",
        sheet="2 OF 2",
        material="-  not a made part",
        # Nothing on this sheet is a manufactured feature, so it must not
        # assert a manufacturing tolerance; the previous default claimed an
        # edge, hole position and hole diameter tolerance of its own, which
        # differed from the ones on the sheet the plate is actually made from.
        tolerance="reference only - TT-MP-01 governs every dimension"))
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

    by_version = dict(holes_by_version(spec))
    rows_t = []
    for name, pl in PLACEMENTS.items():
        used = ", ".join(pl["shuttles"]) or "not yet shipped"
        # The plate positions this board's hosts land on, spelled out.  "3
        # Pmods starting at position 1" said the same thing and made the
        # reader do the arithmetic to see that TT01-03's two hosts share
        # positions 2 and 3 with the later boards' second and third.
        first = pl["first_pmod_position"]
        slots = ", ".join(str(first + i) for i in range(pl["pmod_count"]))
        rows_t.append([name, ", ".join(pl["revisions"]), used,
                       f"{pl['dx']:.2f}", f"{pl['dy']:.2f}", slots,
                       ", ".join(by_version[name])])
    # In the annotation column, not in a half-width cell: at a true 2.5 mm cap
    # height this table does not fit in half the drawing area.
    block = sheet.column_block(sheet.table_height("BOARD PLACEMENT ON THE PLATE",
                                                  len(rows_t)))
    sheet.table(block, "BOARD PLACEMENT ON THE PLATE",
                ["GROUP", "BOARD REVISIONS", "SHUTTLES", "dX mm", "dY mm",
                 "PLATE PMODS", "HOLES USED"],
                rows_t,
                ["start", "start", "start", "end", "end", "middle", "start"])

    rows_u = [[name, f"{USB_C[name][0]:.2f} to {USB_C[name][2]:.2f}",
               f"{USB_C[name][1]:.2f} to {USB_C[name][3]:.2f}"]
              for name in PLACEMENTS]
    block = sheet.column_block(
        sheet.table_height("USB-C CONNECTOR POSITION ON THE PLATE", len(rows_u)))
    sheet.table(block, "USB-C CONNECTOR POSITION ON THE PLATE",
                ["BOARD", "X EXTENT mm", "Y EXTENT mm"], rows_u,
                ["start", "end", "end"])

    notes = [
        "Each view shows one group of demo board revisions on the plate, with "
        "the holes and slots that group uses drawn solid and labelled, and "
        "the rest greyed back. Hole IDs match drawing TT-MP-01.",
        "The revisions in a group share their mounting holes and Pmod host "
        "positions exactly, which is all the plate registers against. They "
        "may differ elsewhere: v2.1.2 moved its USB-C connector 0.9 mm "
        "relative to v2.0.1 and v2.1.0, for instance.",
        "dX and dY place the board: add them to a coordinate in that board's "
        "own frame to get a plate coordinate.",
        "The TT01/02/03 board has only two Pmod hosts. They go on plate Pmod "
        "positions 2 and 3, which makes the plate 5.15 mm narrower than "
        "putting them on 1 and 2 would.",
        "Every revision puts its Pmod host pin fields on the same three "
        "positions, at the same height above the plate's front edge. See "
        "drawing TT-MP-01 for the plate itself.",
    ]
    spill = notes_spill_needed(sheet, notes, [])
    draw_legend(sheet, GUIDE_LEGEND)
    _place_notes_and_sources(sheet, notes, [], spill=spill)
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
                   dash=style.D_PHANTOM)
    if not bo.edges:
        c.rect(*view.pt(dx, dy), view.d(bo.width), view.d(bo.height),
               weight=style.W_PHANTOM, colour=style.C_PHANTOM,
               dash=style.D_PHANTOM)

    for p in board.pmods:
        px, py = view.pt(p.cx + dx, p.cy + dy)
        c.rect(px - view.d(p.pin_span / 2 + 1.3),
               py - view.d(p.row_span / 2 + 1.3),
               view.d(p.pin_span + 2.6), view.d(p.row_span + 2.6),
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT,
               fill="#ffffff")

    for i, sl in enumerate(spec.slots):
        draw_slot(c, view, sl,
                  colour=BOARD_HOLE if i in used_slots else style.C_PHANTOM)
    board_n = 0
    labels = {}
    for i, h in enumerate(spec.holes):
        if h.kind == "plate":
            continue
        board_n += 1
        if i in used:
            labels[i] = f"H{board_n}"
    # The plate edge and the phantom board outline are both obstacles for the
    # hole labels here, as they are on the fabrication drawing.
    edge = Obstacles()
    for a, b in (((0, 0), (o.width, 0)), ((o.width, 0), (o.width, o.height)),
                 ((o.width, o.height), (0, o.height)), ((0, o.height), (0, 0))):
        edge.add_segment(*view.pt(*a), *view.pt(*b))
    edge.add_rect(*view.pt(dx, dy),
                  *view.pt(dx + bo.width, dy + bo.height), pad=0.0)

    # The three caption lines sit right under the view, close enough that a
    # hole label on the plate's lower edge lands on the first of them.
    shuttles = ", ".join(pl["shuttles"]) or "no shipped shuttle yet"
    captions = [
        (f"{name}  ({shuttles})", 7.0, True, style.C_NOTE),
        ("board rev " + ", ".join(pl["revisions"]), 12.0, False, "#444444"),
        (f"offset X {dx:.2f}  Y {dy:.2f} mm", 17.0, False, "#444444"),
    ]
    for text, drop, bold, _ in captions:
        w = style.text_width(text, style.T_LABEL, bold=bold)
        y = view.y(0) - drop
        edge.add_rect(cell.cx - w / 2, y - style.descender(style.T_LABEL),
                      cell.cx + w / 2, y + style.T_LABEL, pad=1.0)

    draw_plate_holes(c, view, spec, labels, highlight=used, extra=edge,
                     slot_labels={i: f"S{i + 1}" for i in used_slots},
                     bounds=cell)

    for text, drop, bold, colour in captions:
        c.text(cell.cx, view.y(0) - drop, text, size=style.T_LABEL,
               anchor="middle", bold=bold, colour=colour,
               face="sans" if bold else "condensed")
