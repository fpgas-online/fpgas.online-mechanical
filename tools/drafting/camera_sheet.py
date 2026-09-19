"""Camera position sheets: where to put an OV5647 camera over a board.

Every other sheet in this repository draws a part.  These draw a part and a
place to stand: the plan view is the subject, and over it are the footprints
the picture covers, one per thing worth framing, with the camera's X, Y and
height beside them.

One sheet per SUBJECT, both lenses on it, rather than one sheet per lens.
The person reading it has one board in front of them and wants to know where
the camera goes; what changes between the two lenses is a number in a table,
while what changes between subjects is the whole drawing.  A per-lens sheet
would have had to put three different boards on one page, at three scales,
and would still have made anyone setting up a rig turn to a second page to
find out what the other lens does.

The frame footprints do not depend on the lens.  A frame is the sensor's own
4:3 aspect round its target -- that is the shape of the file that comes out,
whatever is in front of it -- so a subject has exactly as many rectangles as
it has things worth framing, and the lens only decides how high above them
the camera has to be.  See :mod:`raspberry_pi_camera.optics`.
"""

from __future__ import annotations

from raspberry_pi_camera import optics
from raspberry_pi_camera.optics import (LENSES, Subject,  # noqa: E501
                                        coincident_edges, place)

from . import dims, style
from .board_sheet import (_place_notes_and_sources, draw_feature, draw_holes,
                          draw_legend, draw_pmod, note_blocks,
                          notes_spill_needed, outline_path)
from .plate_sheet import draw_slot
from .sheet import Sheet, TitleBlock
from .view import View

#: Room round the plan view.  The left and the bottom carry one dimension per
#: frame, stacked, and the bottom also carries the coincident-edge leader;
#: nothing goes above or to the right but the frame markers.  The bottom
#: figure has to cover the outermost lane, which is 22 mm out plus its
#: arrowheads -- at 27 it reached two millimetres past the space it had
#: reserved, into the gap above the notes band.
MARGIN_LEFT = 34.0
MARGIN_BOTTOM = 30.0
MARGIN_TOP = 5.0
MARGIN_RIGHT = 12.0

#: A frame's colour, its legend style and its letter, by its position in the
#: subject's list.  Two of each, because no subject has three things worth
#: framing; a third would have to earn a third colour that still reads when
#: photocopied, so it fails loudly here rather than raising an IndexError
#: halfway down a drawing or, worse, being skipped by the checker.
FRAME_COLOURS = (style.C_FRAME_A, style.C_FRAME_B)
FRAME_LEGEND = ("frame_a", "frame_b")
FRAME_LETTERS = "AB"
MAX_FRAMES = len(FRAME_COLOURS)


#: Radius of the lettered marker that names a frame at its own corner.
MARKER_R = 3.2

#: How far the datum label is tried from the datum, and in which order: the
#: quadrants a drafter would reach for first.
DATUM_LABEL_R = 6.5
DATUM_DIRS = ((-1, -1), (1, -1), (-1, 1), (1, 1))

#: The annotation column stays at the library's own width.  Narrowing it
#: would widen every line of the notes band beside it, which these sheets
#: want -- their notes are mostly optics, a subject the drawing cannot show
#: at all -- but the title block is the column, and below about 157 mm the
#: VERSION cell can no longer hold a `git describe` string.  The notes were
#: cut to fit instead.


def _bbox(subject: Subject) -> tuple[float, float, float, float]:
    """Everything the view has to cover: the subject and every frame."""
    spec = subject.spec
    xs = [0.0, spec.outline.width]
    ys = [0.0, spec.outline.height]
    for f in spec.features:
        xs += [f.x0, f.x1]
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            xs += [p.body_x0, p.body_x1]
            ys += [p.body_y0, p.body_y1]
    for s in spec.slots:
        xs += [s.x0 - s.width, s.x1 + s.width]
        ys += [s.y0 - s.width, s.y1 + s.width]
    for fr in subject.frames():
        xs += [fr.x0, fr.x1]
        ys += [fr.y0, fr.y1]
    return min(xs), min(ys), max(xs), max(ys)


def _fmt_mod(lens) -> str:
    if lens.min_object_distance is None:
        return "not published"
    return f"{lens.min_object_distance:.0f}"


def _focus_verdict(p) -> str:
    """What the height means against the lens's published near limit."""
    if p.too_close is None:
        return "UNKNOWN"
    return "TOO CLOSE" if p.too_close else "ok"


def _text(subject: Subject) -> tuple[list[str], list[str]]:
    """The notes and sources this sheet carries, built before it exists.

    Every figure in here is computed or quoted from
    :mod:`raspberry_pi_camera.optics`.  None is written out by hand: a second
    copy of a derived angle is a copy that goes stale the day the model
    changes, and the whole point of that module is that its numbers are
    checkable.
    """
    frames = subject.frames()
    stock = LENSES["65"]
    notes = [
        "The camera looks straight down. X and Y locate the optical axis in "
        "the subject's plan frame; Z is the lens height above the plane its "
        "target lies in. ASSUMED: Z is to the entrance pupil, which no "
        "vendor locates; set it from the lens face.",
        f"A frame is the smallest rectangle of the sensor's own 4:3 holding "
        f"its target plus {optics.FRAME_MARGIN:.2f} mm all round; LONG says "
        "which way the camera is turned. It is the shape of the picture, not "
        "of the optics, so both lenses share it and differ only in Z.",
    ]

    # Which plane each frame's height is set from.  One note, because a
    # reader who sets the stand from the wrong face gets a picture that is
    # smaller at the thing they are photographing, and nothing on the drawing
    # would tell them.
    # Grouped by plane, not listed per frame: on the Acorn sheet both frames
    # are set from the card's face, and naming it twice printed its whole
    # explanation twice.
    by_plane: dict[tuple[str, str], list[str]] = {}
    for letter, fr in zip(FRAME_LETTERS, frames):
        t = fr.target
        by_plane.setdefault((t.plane_name, t.plane_note), []).append(letter)
    planes = []
    for (name, plane_note), letters in by_plane.items():
        line = f"{'/'.join(letters)} from {name}"
        if plane_note:
            line += f" -- {plane_note}"
        planes.append(line)
    notes.append(
        "PLANE, which Z is measured from: " + "; ".join(planes)
        + ". A stand set h mm too low covers only (Z - h) / Z of what is "
        "drawn, so the error always loses the edges.")

    # What stands above the plane the first frame's height was set from, and
    # how high it may stand before it leaves the picture.
    for label, box in subject.standing:
        reach = ", ".join(
            f"{place(frames[0], ln).headroom(box):.1f} mm at {ln.key} deg"
            for ln in LENSES.values())
        notes.append(
            f"HEADROOM: {label} lies inside frame {FRAME_LETTERS[0]} in plan "
            "but stands above the plane its height is set from, and stays in "
            f"the picture only up to {reach}. Above that, raise the camera.")

    # The one thing a reader has to be told before building anything, so it
    # goes above the derivations.
    verdicts = {_focus_verdict(place(fr, ln))
                for fr in frames for ln in LENSES.values()}
    if "TOO CLOSE" in verdicts:
        notes.append(
            f"FOCUS: {stock.mod_note} Every height here is nearer than "
            "that, so a stock OV5647 cannot focus on any of these boards. "
            "Use one whose lens focuses closer.")

    af = optics.AUTOFOCUS
    notes.append(
        "AUTOFOCUS: an autofocus OV5647 is a different part -- Arducam's "
        f"B0176, declared {af.fov_h:.0f} x {af.fov_v:.0f} deg against the "
        f"stock lens's {stock.fov_h:.2f} x {stock.fov_v:.2f}, with a "
        f"motorised lens and a close focus setting. {af.mod_note} Raspberry "
        "Pi's focusable modules, other sensors, are given as "
        + " and ".join(f'"{q}"' for q in
                       dict.fromkeys(q for _, q in optics.RPI_NEAR_LIMITS))
        + ".")

    # The wide lens's declared pair does not agree with the sensor's shape,
    # so the picture runs over the rectangle drawn -- on the axis the height
    # was NOT set from, which depends on how the camera is turned.  Both are
    # read off the model rather than worded by hand: on the Arty's Ethernet
    # sheet the camera is turned through ninety degrees and the overrun is in
    # Y, where the note used to say it was across.
    for lens in LENSES.values():
        if lens.consistent:
            continue
        runs = []
        for letter, fr in zip(FRAME_LETTERS, frames):
            p = place(fr, lens)
            dx, dy = p.excess
            axis, over = ("X", dx) if dx >= dy else ("Y", dy)
            runs.append(f"{letter} by {over:.2f} mm in {axis}")
        notes.append(
            f"The {lens.key} deg lens's declared pair is not self-consistent: "
            f"{lens.fov_h:.0f} across a 4:3 sensor implies "
            f"{lens.consistent_v:.2f} down it, not {lens.fov_v:.0f}. Z is the "
            "greater of what the two ask for, so the picture runs OVER the "
            "rectangle -- " + ", ".join(runs) + " -- which is still covered.")

    notes.append(
        f'The "{stock.key} deg" name is the stock lens\'s diagonal, which no '
        "vendor prints. DERIVED: 2 x atan(sqrt("
        f"{optics.IMAGE_AREA[0]:.2f}^2 + {optics.IMAGE_AREA[1]:.2f}^2) / 2 / "
        f"{optics.FOCAL_LENGTH:.2f}) = {optics.DIAGONAL_FROM_IMAGE_AREA:.2f} "
        f"deg from the image area, {optics.DIAGONAL_FROM_ARRAY:.2f} from the "
        "pixel array.")

    # The sheets are lettered in ASCII, and the pages they quote are not.
    # Nothing here is a character-for-character quote, so say so once rather
    # than let a reader take "1.4 um x 1.4 um" for what the page prints.
    notes.append(
        "Quotes here are transliterated to ASCII: x for the multiplication "
        "sign, um for micro, infinity for its symbol. The cached pages carry "
        "them as printed.")

    for letter, fr in zip(FRAME_LETTERS, frames):
        if fr.target.note:
            notes.append(f"Frame {letter}, {fr.target.label}: "
                         f"{fr.target.note}")
    notes += list(subject.notes)

    # Every source the sheet makes a claim from, the autofocus variant's
    # included: the AUTOFOCUS note above says the B0176 carries a motorised
    # lens and a close focus setting, and that comes from Arducam's motorized
    # focus page, not from the catalogue row.  It was cited nowhere.
    seen = []
    for s in list(subject.sources) + [s for ln in LENSES.values()
                                      for s in ln.sources] + list(af.sources):
        entry = f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
        if entry not in seen:
            seen.append(entry)
    return notes, seen


def _draw_plan(sheet: Sheet, subject: Subject, view: View) -> None:
    c = sheet.canvas
    spec = subject.spec
    outline_path(c, view, spec)
    draw_holes(c, view, spec.holes)
    for s in spec.slots:
        draw_slot(c, view, s, colour=style.C_HIGHLIGHT)
    for f in spec.features:
        if f.kind == "outline":
            # An informational body, not a part of the subject: the Acorn
            # card lying in its HAT is the only one here.  Drawn in the
            # component red it read as something soldered to the Pi under it.
            x0, y0 = view.pt(f.x0, f.y0)
            x1, y1 = view.pt(f.x1, f.y1)
            c.rect(x0, y0, x1 - x0, y1 - y0, weight=style.W_PHANTOM,
                   colour=style.C_PHANTOM, dash=style.D_PHANTOM)
            # Low in the body, clear of the witness lines that run out to
            # the dimension stacks from the camera axes above it.
            c.text(x0 + 2.0, y0 + 2.0, f.designator or f.label,
                   size=style.T_LABEL, colour=style.C_PHANTOM, bold=True)
            continue
        draw_feature(c, view, f)
    for p in spec.pmods:
        draw_pmod(c, view, p, spec)


def _obstacle_segments(subject: Subject, view: View):
    """The ruled lines near the datum, in sheet millimetres.

    Segments, not infinite lines: a frame's left edge is no obstacle to a
    label placed above the datum if that edge is nowhere near it, and treating
    every edge as an infinite line was why the first version of this found no
    clear quadrant at all and put the label across two frame edges.
    """
    out = []
    spec = subject.spec
    boxes = [(f.x0, f.y0, f.x1, f.y1) for f in subject.frames()]
    boxes += [(f.x0, f.y0, f.x1, f.y1) for f in spec.features]
    # Holes and slots too.  They are circles rather than rectangles, so their
    # bounding box is what the label has to clear -- and leaving them out put
    # the mounting plate's datum label on top of a slot, which is the one
    # thing near that corner.
    for h in spec.holes:
        r = max(h.dia, h.keepout_dia or 0.0) / 2 + style.CENTRE_OVER
        boxes.append((h.x - r, h.y - r, h.x + r, h.y + r))
    for sl in spec.slots:
        r = sl.width / 2 + style.CENTRE_OVER
        boxes.append((min(sl.x0, sl.x1) - r, min(sl.y0, sl.y1) - r,
                      max(sl.x0, sl.x1) + r, max(sl.y0, sl.y1) + r))
    for x0, y0, x1, y1 in boxes:
        sx0, sy0 = view.pt(x0, y0)
        sx1, sy1 = view.pt(x1, y1)
        out += [(sx0, sy0, sx1, sy0), (sx0, sy1, sx1, sy1),
                (sx0, sy0, sx0, sy1), (sx1, sy0, sx1, sy1)]
    return out


def _box_clearance(box, segments) -> float:
    """Clear paper between an axis-aligned *box* and the nearest segment."""
    bx0, by0, bx1, by1 = box
    best = 99.0
    for ax, ay, bx, by in segments:
        # Every segment here is axis-aligned, so the gap is a 1D problem on
        # the axis the segment is perpendicular to, and zero if the segment
        # runs past the box on the other one.
        if abs(ay - by) < 1e-9:                      # horizontal
            if bx1 < min(ax, bx) or bx0 > max(ax, bx):
                continue
            gap = by0 - ay if ay < by0 else (ay - by1 if ay > by1 else -1.0)
        else:                                        # vertical
            if by1 < min(ay, by) or by0 > max(ay, by):
                continue
            gap = bx0 - ax if ax < bx0 else (ax - bx1 if ax > bx1 else -1.0)
        best = min(best, gap)
    return best


def _datum_label_offset(subject: Subject, view: View) -> tuple[float, float]:
    """Which way to throw the datum label so it lands on nothing.

    The datum sits at the subject's own lower-left corner, and on three of
    these four sheets a frame edge passes within a few millimetres of it: on
    RPICAM-OVER-ARTY both frames' lower edges run five millimetres below
    it, and the label was printed across them.  Reserve, then draw: the four
    diagonals are tried against the lines that will actually be there, and
    the roomiest wins.
    """
    half_w = style.text_width("X0 Y0", style.T_TINY) / 2 + 1.0
    half_h = style.T_TINY / 2 + 1.0
    segments = _obstacle_segments(subject, view)
    ox, oy = view.pt(0.0, 0.0)
    best = None
    for sx, sy in DATUM_DIRS:
        cx = ox + sx * (DATUM_LABEL_R + half_w)
        cy = oy + sy * DATUM_LABEL_R
        clear = _box_clearance((cx - half_w, cy - half_h,
                                cx + half_w, cy + half_h), segments)
        if best is None or clear > best[0]:
            best = (clear, cx - ox, cy - oy)
        if clear >= 1.5:
            break
    return best[1], best[2]


def _draw_frames(sheet: Sheet, subject: Subject, view: View, bbox) -> None:
    """The frame footprints, their letters and the camera axis in each."""
    c = sheet.canvas
    frames = subject.frames()
    if len(frames) > MAX_FRAMES:
        raise SystemExit(
            f"{subject.key}: {len(frames)} frames, and this sheet has "
            f"{MAX_FRAMES} colours, {MAX_FRAMES} legend entries and "
            f"{MAX_FRAMES} letters. Add a third of each, or split the sheet.")
    x0m, y0m, x1m, y1m = bbox
    left = view.x(x0m) - MARGIN_LEFT + 20.0
    bottom = view.y(y0m) - MARGIN_BOTTOM + 20.0
    for i, fr in enumerate(frames):
        colour = FRAME_COLOURS[i]
        p0 = view.pt(fr.x0, fr.y0)
        p1 = view.pt(fr.x1, fr.y1)
        c.rect(p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1],
               weight=style.W_PHANTOM, colour=colour, dash=style.D_PHANTOM)
        # The optical axis: a centre mark in the frame's own colour, which is
        # the point of the whole sheet and the thing a stand is set over.
        ax, ay = view.pt(fr.cx, fr.cy)
        c.circle(ax, ay, 1.6, w=style.W_CENTRE, colour=colour, fill="#ffffff")
        dims.centre_mark(c, ax, ay, 1.6, colour=colour, over=2.6)
        # The letter at the frame's own top-right corner.  Those corners are
        # far apart on every sheet in this set -- the closest pair is 12 mm
        # -- but that is a property of these four subjects and not a
        # guarantee, so check_sheets reports the collision if one ever lands
        # on another.
        c.circle(p1[0], p1[1], MARKER_R, fill="#ffffff", colour=colour,
                 w=style.W_THIN)
        c.text(p1[0], p1[1], FRAME_LETTERS[i], size=style.T_LABEL,
               colour=colour, anchor="middle", baseline="middle", bold=True)
        # X and Y from the subject datum to that axis, one lane per frame.
        d0 = view.pt(0.0, 0.0)
        lane = 14.0 + i * style.DIM_STEP
        dims.linear(c, d0, (ax, ay), (bottom - lane) - min(d0[1], ay),
                    horizontal=True, value=fr.cx, colour=colour)
        dims.linear(c, d0, (ax, ay), (left - lane) - min(d0[0], ax),
                    horizontal=False, value=fr.cy, colour=colour)

    # Where two frame edges are too close to draw as two lines, point at them
    # and say so.  One leader, into the clear band between the drawing and
    # the first dimension lane.
    for axis, ia, ib, pos, lo, hi, gap in coincident_edges(frames):
        mid = (lo + hi) / 2
        tip = view.pt(mid, pos) if axis == "Y" else view.pt(pos, mid)
        text = (f"FRAMES {FRAME_LETTERS[ia]} AND {FRAME_LETTERS[ib]}: "
                f"edges {gap:.2f} apart, drawn as one line")
        elbow_x = min(tip[0] + 8.0,
                      sheet.area.x1 - 6.0 - style.text_width(text,
                                                             style.T_LABEL))
        dims.leader(c, tip, (max(elbow_x, tip[0] + 4.0), bottom - 7.0), text,
                    dot=True, colour=style.C_PHANTOM)

    dx, dy = _datum_label_offset(subject, view)
    dims.datum_marker(c, *view.pt(0.0, 0.0), label="X0 Y0",
                      label_dx=dx, label_dy=dy)


def _tables(sheet: Sheet, subject: Subject) -> None:
    """Two tables: one row per frame, and one row per lens.

    The frames and the heights were two tables, keyed to each other by the
    frame letter, and a reader answering "where do I put the camera for the
    LEDs" had to find B in one and then both of B's rows in the other.  One
    row per frame with a height column per lens says the same thing in a
    quarter of the column, which the mounting plate sheet needs: its view is
    the tallest in the set, so its notes band is the shortest, and what the
    band cannot hold comes out of this column.

    No per-row focus verdict.  It was the same word on every row of every
    sheet, and what it means is in the FOCUS note and in the LENSES table's
    own near-limit column, which is where a reader compares lenses anyway.
    """
    frames = subject.frames()
    lenses = list(LENSES.values())

    rows = []
    for i, fr in enumerate(frames):
        row = [FRAME_LETTERS[i], fr.target.label,
               f"{fr.width:.2f} x {fr.height:.2f}", fr.long_axis,
               f"{fr.cx:.2f}", f"{fr.cy:.2f}"]
        row += [f"{place(fr, ln).z:.1f}" for ln in lenses]
        rows.append(row)
    headers = ["", "FRAME", "RECTANGLE mm", "LONG", "AXIS X", "AXIS Y"]
    headers += [f"Z {ln.key}" for ln in lenses]
    aligns = ["middle", "start", "end", "middle", "end", "end"] \
        + ["end"] * len(lenses)
    title = "FRAMES, AND Z ABOVE THE FRAME PLANE, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, headers, rows, aligns)

    rows = [[ln.name, f"{ln.fov_h:.2f}", f"{ln.fov_v:.2f}", ln.focus,
             _fmt_mod(ln)]
            for ln in lenses + [optics.AUTOFOCUS]]
    block = sheet.column_block(sheet.table_height("LENSES", len(rows)))
    sheet.table(block, "LENSES",
                ["LENS", "H deg", "V deg", "FOCUS", "NEAR mm"], rows,
                ["start", "end", "end", "start", "end"])


def _place_text(sheet: Sheet, subject: Subject, notes: list[str],
                src: list[str], band_cols: int) -> None:
    """Notes and sources along the foot, spilling into the annotation column.

    The same flow the rest of the set uses.  It is called out here only to
    carry a message that says which sheet ran out of room: these carry more
    prose than any other in the repository -- optics is a subject the drawing
    cannot show at all -- and the mounting plate's band is the shortest in
    the set, because its view is the tallest.
    """
    spill = notes_spill_needed(sheet, notes, src, band_cols)
    if spill and spill + 4.0 > sheet.column_remaining:
        raise SystemExit(
            f"{subject.key}: neither the notes band nor the annotation "
            f"column can hold this sheet's text ({spill + 4.0:.0f} mm of "
            f"tail wanted, {sheet.column_remaining:.0f} mm left); shorten "
            "the notes")
    _place_notes_and_sources(sheet, notes, src, columns=band_cols,
                             spill=spill)


def render_camera_position(subject: Subject, *, drawing_no: str, version: str,
                           sheet_size: str = "A3") -> Sheet:
    bbox = _bbox(subject)
    view_h = (bbox[3] - bbox[1]) + MARGIN_TOP + MARGIN_BOTTOM
    notes, src = _text(subject)
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src),
        max_height=style.SHEET_SIZES[sheet_size][1]
        - 2 * style.FRAME_MARGIN - view_h - 4.0)

    sheet = Sheet(sheet_size, TitleBlock(
        title=subject.title.upper(), subtitle=subject.subtitle,
        drawing_no=drawing_no, rev="A", version=version,
        drawn_by="generated",
        material=subject.subject_field or subject.spec.title,
        material_label="SUBJECT",
        tolerance=subject.tolerance), notes_band_height=band_h)
    sheet.draw_frame()

    view = View.fit(sheet.area, bbox, margin=MARGIN_LEFT,
                    margin_top=MARGIN_TOP, margin_bottom=MARGIN_BOTTOM,
                    margin_right=MARGIN_RIGHT)
    sheet.title.scale = view.scale_label

    _draw_plan(sheet, subject, view)
    _draw_frames(sheet, subject, view, bbox)
    _tables(sheet, subject)

    # Only the styles this particular sheet uses: an entry for a line the
    # reader cannot find on the drawing is worse than no legend at all.
    spec = subject.spec
    legend = [("outline", "Subject outline")]
    if any(f.kind != "outline" for f in spec.features) or spec.slots:
        legend.append(("component", "LED, display or connector"))
    if (any(f.kind == "outline" for f in spec.features)
            or any(p.body_x1 > p.body_x0 for p in spec.pmods)
            or any(h.keepout_dia for h in spec.holes)):
        legend.append(("phantom", "Adjacent part or connector body"))
    for i in range(len(subject.targets)):
        legend.append((FRAME_LEGEND[i],
                       f"Frame {FRAME_LETTERS[i]}, the rectangle the picture "
                       "must cover"))
    legend.append(("dimension", "Dimension, extension and leader"))

    draw_legend(sheet, legend)
    _place_text(sheet, subject, notes, src, band_cols)

    sheet.draw_title_block()
    return sheet
