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
from raspberry_pi_camera.optics import LENSES, Subject, place

from . import dims, style
from .board_sheet import (_place_notes_and_sources, draw_feature, draw_holes,
                          draw_legend, draw_pmod, legend_height, note_blocks,
                          notes_spill_needed, outline_path)
from .plate_sheet import draw_slot
from .sheet import Rect, Sheet, TitleBlock
from .view import View

#: Room round the plan view.  The left and the bottom carry one dimension per
#: frame, stacked; nothing goes above or to the right but the frame markers.
MARGIN_LEFT = 34.0
MARGIN_BOTTOM = 27.0
MARGIN_TOP = 5.0
MARGIN_RIGHT = 12.0

#: A frame's colour, by its position in the subject's list.
FRAME_COLOURS = (style.C_FRAME_A, style.C_FRAME_B)
FRAME_LEGEND = ("frame_a", "frame_b")
FRAME_LETTERS = "AB"

#: Radius of the lettered marker that names a frame at its own corner.
MARKER_R = 3.2

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
    """The notes and sources this sheet carries, built before it exists."""
    frames = subject.frames()
    stock = LENSES["65"]
    notes = [
        "The camera looks straight down at the subject plane, the top face "
        "of the board. X and Y locate the optical axis in the subject's own "
        "frame; Z is the lens height above it. ASSUMED: Z is to the entrance "
        "pupil, which neither vendor locates; set it from the lens face.",
        f"A frame is the smallest rectangle of the sensor's own 4:3 "
        f"proportions holding its target plus {optics.FRAME_MARGIN:.2f} mm "
        "all round; LONG says which way the camera is turned. A frame is the "
        "shape of the picture, not of the optics, so both lenses share the "
        "rectangles drawn and differ only in Z.",
    ]
    # The one thing a reader of this sheet has to be told before they build
    # anything, so it goes above the derivations.
    verdicts = {_focus_verdict(place(fr, ln))
                for fr in frames for ln in LENSES.values()}
    if "TOO CLOSE" in verdicts:
        notes.append(
            "FOCUS: every height here is nearer than the stock lens's near "
            f"limit of {stock.min_object_distance:.0f} mm -- Raspberry Pi "
            'give its focus as "Fixed", "Approx 1 m to infinity". A stock '
            "OV5647 cannot focus on any of these boards; use one whose lens "
            "focuses closer.")
    notes.append(
        "AUTOFOCUS: an autofocus OV5647 exists and is a different part -- "
        "Arducam's B0176, declared 54 x 44 deg against the stock lens's 54 x "
        "41, with a motorised lens, its own device tree line and a close "
        "focus setting. No lens height and no near limit are published for "
        "it, so no Z here comes from it. Raspberry Pi's own focusable "
        'modules, on other sensors, reach "Approx 10 cm" and "Approx 5 cm".')
    notes.append(
        "The 120 deg lens's declared pair is not self-consistent: 120 across "
        "a 4:3 sensor implies 104.82 down it, not 90. Z is the greater of "
        "what the two ask for, the vertical, so the picture is WIDER than "
        "the rectangle drawn and the frame is still covered.")
    notes.append(
        'The name "65 degrees" is the stock lens\'s diagonal, which no '
        "vendor prints. DERIVED: 2 x atan(sqrt(3.76^2 + 2.74^2) / 2 / 3.60) "
        "= 65.74 deg from the image area, 64.42 from the pixel array. The "
        "table gives the figures they do print.")
    for fr in frames:
        if fr.target.note:
            letter = FRAME_LETTERS[frames.index(fr)]
            notes.append(f"Frame {letter}, {fr.target.label}: "
                         f"{fr.target.note}")
    notes += list(subject.notes)

    seen = []
    for s in list(subject.sources) + [s for ln in LENSES.values()
                                      for s in ln.sources]:
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


def _draw_frames(sheet: Sheet, subject: Subject, view: View,
                 bbox) -> None:
    """The frame footprints, their letters and the camera axis in each."""
    c = sheet.canvas
    x0m, y0m, x1m, y1m = bbox
    left = view.x(x0m) - MARGIN_LEFT + 20.0
    bottom = view.y(y0m) - MARGIN_BOTTOM + 20.0
    for i, fr in enumerate(subject.frames()):
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
        # The letter at the frame's own top-right corner, where the two
        # frames on a sheet are always further apart than the marker is wide:
        # one frame contains the other, so their corners cannot coincide.
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
    dims.datum_marker(c, *view.pt(0.0, 0.0), label="X0 Y0",
                      label_dy=-7.0)


def _tables(sheet: Sheet, subject: Subject) -> None:
    frames = subject.frames()

    rows = [[FRAME_LETTERS[i], fr.target.label,
             f"{fr.width:.2f} x {fr.height:.2f}", fr.long_axis,
             f"{fr.cx:.2f}", f"{fr.cy:.2f}"]
            for i, fr in enumerate(frames)]
    block = sheet.column_block(sheet.table_height("FRAMES", len(rows)))
    sheet.table(block, "FRAMES",
                ["", "FRAME", "COVERS mm", "LONG", "AXIS X", "AXIS Y"], rows,
                ["middle", "start", "end", "middle", "end", "end"])

    rows = []
    for i, fr in enumerate(frames):
        for lens in LENSES.values():
            p = place(fr, lens)
            rows.append([FRAME_LETTERS[i], lens.name.split(" ")[0] + " deg",
                         f"{p.z:.1f}", _focus_verdict(p)])
    block = sheet.column_block(
        sheet.table_height("CAMERA HEIGHT Z ABOVE THE SUBJECT", len(rows)))
    sheet.table(block, "CAMERA HEIGHT Z ABOVE THE SUBJECT",
                ["", "LENS", "Z mm", "FOCUS"], rows,
                ["middle", "start", "end", "start"])

    rows = [[ln.name, f"{ln.fov_h:.2f}", f"{ln.fov_v:.2f}", ln.focus,
             _fmt_mod(ln)]
            for ln in list(LENSES.values()) + [optics.AUTOFOCUS]]
    block = sheet.column_block(sheet.table_height("LENSES", len(rows)))
    sheet.table(block, "LENSES",
                ["LENS", "H deg", "V deg", "FOCUS", "NEAR mm"], rows,
                ["start", "end", "end", "start", "end"])


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
                       f"Frame {FRAME_LETTERS[i]}, what the picture covers"))
    legend.append(("dimension", "Dimension, extension and leader"))

    spill = notes_spill_needed(sheet, notes, src, band_cols)
    want = legend_height(len(legend)) + (spill + 4.0 if spill else 0.0)
    if sheet.column_remaining < want:
        raise SystemExit(
            f"{subject.key}: the annotation column cannot hold both the "
            f"legend and the notes' tail ({want:.0f} mm wanted, "
            f"{sheet.column_remaining:.0f} mm left); shorten the notes")
    draw_legend(sheet, legend)
    _place_notes_and_sources(sheet, notes, src, columns=band_cols,
                             spill=spill)

    sheet.draw_title_block()
    return sheet
