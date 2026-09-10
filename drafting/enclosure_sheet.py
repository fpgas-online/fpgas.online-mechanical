"""Three-view drawing for a packaged item such as a PoE splitter.

These parts are enclosures, not bare boards, so a single plan view says
nothing useful about how they mount.  The sheet carries a front elevation, a
plan below it and an end view to its left: first-angle projection, where each
view is placed on the side opposite the direction it is viewed from.
"""

from __future__ import annotations

from data.schema import BoardSpec

from . import dims, style
from .board_sheet import (_place_notes_and_sources, draw_legend,
                          legend_height, note_blocks,
                          notes_spill_needed)
from .sheet import Rect, Sheet, TitleBlock
from .view import STANDARD_SCALES, View, scale_text

GAP = 26.0          # space between views, for the dimensions that go there


def _material(spec) -> str:
    """The actual material, not the word "enclosure"."""
    return {"waveshare-poe-usbc": "aluminium extrusion",
            "generic-poe-microusb": "moulded plastic"}.get(
                spec.key, "enclosure")


def _tolerance(spec) -> str:
    """A tolerance the sheet's own notes do not contradict.

    The generic splitter's two independent sources disagree by 3 mm on width
    and 2 mm on height, and gigabit variants run 15 mm longer, so quoting a
    millimetre on that envelope would be false precision.
    """
    if spec.key == "generic-poe-microusb":
        # W and H are maxima; length is not.  Saying "envelope is a MAXIMUM"
        # without qualifying it contradicted the sheet's own note that gigabit
        # variants come in a case up to about 95 mm long.
        return "W +0/-3 MAX   H +0/-2 MAX   L +15/-0, see notes"
    return "envelope +/-1.0 unless noted"


def _pick_scale(length: float, depth: float, height: float,
                area: Rect) -> tuple[float, str]:
    need_w = length + GAP + depth
    need_h = height + GAP + depth
    # Reserve room for the dimensions that sit outside the view block: an
    # overall dimension plus its text on the left and below, and the height
    # dimension on the right.  Measured, not guessed: the plan's stack reaches
    # 36 mm below the view plus its text, and the caption sits 6 mm above the
    # elevation.  At 64 the generic splitter missed 1:1 by three millimetres
    # and was drawn at half the size of the Waveshare sheet beside it.
    for num, den in STANDARD_SCALES:
        s = num / den
        if need_w * s <= area.w - 52 and need_h * s <= area.h - 56:
            return s, scale_text(num, den)
    return 1.0, "1:1"


#: The kinds of feature this sheet projects into the end view and dimensions.
#: A feature of any other kind appears in the plan and in the feature table but
#: contributes no dimension, so its tolerance says nothing about the sheet.
DIMENSIONED_KINDS = ("ethernet",)


def ref_features(spec) -> tuple:
    """The features whose dimensions are drawn REF on this sheet.

    One definition, used both to decide which values get the REF suffix and to
    work out what the note should say they are good to.  Read off all of
    ``spec.features`` instead, the note on the Waveshare sheet quoted
    "+/-1.5 mm to +/-2.0 mm", where the 2.0 belonged to the captive output
    cable: a feature that carries a tolerance but is not dimensioned anywhere
    on the sheet.
    """
    return tuple(f for f in spec.features
                 if f.kind in DIMENSIONED_KINDS and f.tol)


def _ref_tol(spec) -> str:
    """How good the REF dimensions on this sheet are, read from the data.

    Written out rather than quoted from memory: the two splitters are scaled
    from different photographs and are not equally good.
    """
    tols = sorted({f.tol for f in ref_features(spec)})
    if not tols:
        return "the general tolerance"
    if tols[0] == tols[-1]:
        return f"+/-{tols[0]:.1f} mm"
    return f"+/-{tols[0]:.1f} mm to +/-{tols[-1]:.1f} mm"


def _enclosure_text(spec) -> tuple[list[str], list[str]]:
    """The sheet's notes and sources, built before the sheet exists."""
    notes = [
        "All dimensions in millimetres. The datum symbol on the plan marks the "
        "origin: the lower-left corner of the body envelope, X along the "
        "length, Y across the width, Z up.",
        "First-angle projection. The plan is the view from above, placed below "
        "the front elevation; the end view is the view from the RJ45 end, "
        "placed to the left of it.",
        "The RJ45 aperture in the end view is a standard 8P8C jack envelope, "
        "placed centrally because the vendor does not dimension it. Every "
        "dimension marked REF is scaled from vendor photographs, is good to "
        "about " + _ref_tol(spec) + ", and is not for inspection. The body "
        "envelope is the dimension to trust.",
        ("The corner radius is nominal. It belongs to the body cross-section, "
         "so it appears in the end view only."
         if spec.outline.constant_section else
         "The corner radius is nominal. The case is not a constant section, "
         "so the radius runs round the plan as well and is drawn there."),
    ] + list(spec.notes)
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
           for s in spec.sources]
    return notes, src


def render_enclosure(spec: BoardSpec, *, drawing_no: str, date: str,
                     sheet_size: str = "A3") -> Sheet:
    o = spec.outline
    length, depth = o.width, o.height
    height = o.z_height or 10.0

    notes, src = _enclosure_text(spec)
    band_h, band_cols = Sheet.plan_notes_band(
        sheet_size, note_blocks(notes, src),
        max_height=style.SHEET_SIZES[sheet_size][1]
        # The 4 mm is the gap the sheet leaves between the notes band
        # and the drawing area.  Left out, the band could take the
        # last four millimetres the view needed and drop it a whole
        # scale step.
        - 2 * style.FRAME_MARGIN - (height + GAP + depth) - 56.0 - 4.0)
    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(), subtitle=spec.subtitle,
        drawing_no=drawing_no, rev="A", date=date, drawn_by="generated",
        material=_material(spec),
        tolerance=_tolerance(spec),
        projection="first angle"), notes_band_height=band_h)
    sheet.draw_frame()
    c = sheet.canvas
    area = sheet.area

    scale, label = _pick_scale(length, depth, height, area)
    sheet.title.scale = label

    # Lay the three views out as a block, then centre the block in the area.
    block_w = depth * scale + GAP + length * scale
    block_h = height * scale + GAP + depth * scale
    left = area.cx - block_w / 2 + 12.0
    top = area.cy + block_h / 2 + 6.0

    front = Rect(left + depth * scale + GAP, top - height * scale,
                 length * scale, height * scale)
    plan = Rect(front.x, front.y - GAP - depth * scale,
                length * scale, depth * scale)
    end = Rect(left, front.y, depth * scale, height * scale)

    def box(r: Rect, radius: float = 0.0) -> None:
        c.rect(r.x, r.y, r.w, r.h, weight=style.W_OUTLINE, radius=radius)

    # An extruded body has one cross-section, so its radii belong to the end
    # view and the plan and elevation are plain rectangles: drawing the radius
    # on the plan as well would say the part is rounded in two directions at
    # once.  A moulded or clamshell case is rounded in plan too, and saying
    # otherwise on its sheet was a note copied from the extrusion's.
    section_only = o.constant_section
    r = o.corner_radius * scale
    box(front, radius=0.0 if section_only else r)
    box(plan, radius=0.0 if section_only else r)
    box(end, radius=r)

    # Captions above each view, so the space below stays free for dimensions.
    for r, name in ((front, "FRONT ELEVATION"), (plan, "PLAN"),
                    (end, "END VIEW, RJ45 END")):
        c.text(r.cx, r.y1 + 4.0, name, size=style.T_LABEL, anchor="middle",
               bold=True)

    # Features are given in plan coordinates: X along the length, Y across the
    # depth.  Project each onto the plan, and onto the end view where it sits
    # in an end face.
    #
    # The plan's overall length sits at the bottom of its dimension stack, so
    # where a feature adds dimensions above it, it moves down to clear them.
    plan_stack = -14.0
    for f in spec.features:
        px = plan.x + f.x0 * scale
        py = plan.y + f.y0 * scale
        c.rect(px, py, (f.x1 - f.x0) * scale, (f.y1 - f.y0) * scale,
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT,
               fill=style.C_FILL_LIGHT)
        if f.kind in DIMENSIONED_KINDS:
            if f.z0 is None or f.z1 is None:
                raise SystemExit(
                    f"{spec.key}: feature {f.key} is drawn in the end view, "
                    "so it needs z0 and z1; the end view will not invent an "
                    "aperture height")
            # The RJ45 is in the end plate, so it also shows in the end view,
            # where its aperture is what a bracket has to clear.
            ex = end.x + f.y0 * scale
            ew = (f.y1 - f.y0) * scale
            ey = end.y + f.z0 * scale
            eh = (f.z1 - f.z0) * scale
            c.rect(ex, ey, ew, eh, weight=style.W_COMPONENT,
                   colour=style.C_HIGHLIGHT, fill=style.C_FILL_LIGHT)
            # Aperture size and position in the end face, both of which a
            # bracket has to clear.  Every one of these is scaled off a
            # photograph rather than measured, so it is marked REF: not for
            # inspection.  The figure it is good to is in a note, because
            # spelling the tolerance out on each dimension makes the text
            # wider than the feature it dimensions.
            ap = " REF" if f in ref_features(spec) else ""
            # One stack per axis, all measured off the same corner of the end
            # view and ordered shortest first, so a reader works outwards from
            # the aperture instead of picking between two baselines.
            # Size nearest the view, then location, then the overall: that is
            # the usual order and, here, the only one that works.  Every value
            # is wider than the span it belongs to, so each is written beyond
            # the extension lines rather than between them, and the size and
            # location values are sent to opposite ends so they do not meet in
            # the corner below the view.
            dims.linear(c, (ex, ey), (ex + ew, ey), (end.y - 14.0) - ey,
                        horizontal=True, text=f"{f.y1 - f.y0:.2f}{ap}",
                        text_side="high")
            dims.linear(c, (end.x, end.y), (ex, end.y), -25.0,
                        horizontal=True, text=f"{f.y0:.2f}{ap}",
                        text_side="low")
            dims.linear(c, (ex, ey), (ex, ey + eh), (end.x - 14.0) - ex,
                        horizontal=False, text=f"{f.z1 - f.z0:.2f}{ap}",
                        text_side="high")
            dims.linear(c, (end.x, end.y), (end.x, ey), -25.0,
                        horizontal=False, text=f"{f.z0:.2f}{ap}",
                        text_side="low")
            # Jack size and position along the body, in the plan.  All three
            # plan dimensions go below the view in one stack, shortest first,
            # so a reader reads outwards from the part.
            dims.linear(c, (plan.x + f.x0 * scale, plan.y),
                        (plan.x + f.x1 * scale, plan.y), -14.0,
                        horizontal=True, text=f"{f.x1 - f.x0:.2f}{ap}",
                        text_side="high")
            dims.linear(c, (plan.x, plan.y), (plan.x + f.x0 * scale, plan.y),
                        -25.0, horizontal=True, text=f"{f.x0:.2f}{ap}",
                        text_side="low")
            plan_stack = -36.0
        elif f.kind == "connector":
            # The captive output lead is what actually decides how close the
            # splitter can sit to the board it feeds, and it was drawn on the
            # plan without a dimension or a label to say what it was.
            #
            # Both dimensions are anchored on the exit's own inboard edge and
            # run out to the left, past the end the lead leaves.  Anchoring
            # them on plan.x1 instead put the value and its extension stubs at
            # the far end of the plan, hard against the RJ45 aperture, where
            # they read as dimensioning that aperture rather than a feature
            # eighty millimetres away with nothing joining the two.
            # Given on the leader rather than as dimension lines.  The exit is
            # three millimetres wide and each value is four times that, so a
            # dimension line for it is longer than the thing it dimensions and
            # has nowhere to sit: the left of the plan is the depth dimension
            # and the end view's stack, the right is the RJ45 aperture.  A
            # leader points at the feature and cannot be read as belonging to
            # anything else, which is the whole difficulty here.
            ap = f" +/-{f.tol:.1f} mm" if f.tol else " mm"
            y0 = plan.y + f.y0 * scale
            y1 = plan.y + f.y1 * scale
            exit_label = (f"{f.label}: {f.y1 - f.y0:.2f} wide, "
                          f"{f.y0:.2f} from the datum{ap}")
            # Above the plan, in the gap between it and the elevation: below
            # is the dimension stack and left is the depth dimension.
            # Held back so the text ends inside the drawing area, and never
            # so far back that it passes the point it labels and turns the
            # tail round.
            tip_x = plan.x + (f.x0 + f.x1) / 2 * scale
            elbow_x = max(tip_x + 3.0,
                          min(plan.x + 4.0,
                              area.x1 - 6.2 - style.text_width(exit_label,
                                                               style.T_LABEL)))
            dims.leader(c, (tip_x, (y0 + y1) / 2),
                        (elbow_x, plan.y1 + 9.0), exit_label, dot=True)

    dims.linear(c, (plan.x, plan.y), (plan.x1, plan.y), plan_stack,
                horizontal=True, value=length)
    dims.linear(c, (plan.x, plan.y), (plan.x, plan.y1), -14.0,
                horizontal=False, value=depth)
    dims.linear(c, (front.x1, front.y), (front.x1, front.y1), 14.0,
                horizontal=False, value=height)
    # Depth is dimensioned on the plan, next to the length it goes with, and
    # not again here: one dimension, one place.
    # Below the view, not above: the caption sits above and is wider than the
    # view itself, so an upward leader runs straight through it.
    dims.leader(c, (end.x1 - o.corner_radius * scale * 0.3,
                    end.y + o.corner_radius * scale * 0.3),
                (end.x1 + 9.0, end.y - 7.0),
                (f"R{o.corner_radius:.2f} nominal (4 places), body section"
                 if section_only else
                 f"R{o.corner_radius:.2f} nominal, all corners"))
    dims.datum_marker(c, plan.x, plan.y, label="")


    rows = [["Overall length", f"{length:.2f}"],
            ["Overall width", f"{depth:.2f}"],
            ["Overall height", f"{height:.2f}"]]
    block = sheet.column_block(sheet.table_height("ENVELOPE", len(rows)))
    sheet.table(block, "ENVELOPE", ["DIMENSION", "mm"], rows,
                ["start", "end"])

    if spec.features:
        rows = [[f.label, f"{f.x0:.2f} to {f.x1:.2f}",
                 f"{f.y0:.2f} to {f.y1:.2f}"] for f in spec.features]
        block = sheet.column_block(sheet.table_height("FEATURES (PLAN VIEW)", len(rows)))
        sheet.table(block, "FEATURES (PLAN VIEW)",
                    ["FEATURE", "X EXTENT mm", "Y EXTENT mm"], rows,
                    ["start", "end", "end"])

    # Legend under the tables, notes' tail at the foot of the column.
    legend = [
        ("outline", "Body envelope"),
        ("component", "Aperture or cable exit"),
        ("dimension", "Dimension, extension and leader"),
    ]
    spill = notes_spill_needed(sheet, notes, src, band_cols)
    want = legend_height(len(legend)) + (spill + 4.0 if spill else 0.0)
    if sheet.column_remaining < want:
        raise SystemExit(
            f"{spec.key}: the annotation column cannot hold both the legend "
            f"and the notes' tail ({want:.0f} mm wanted, "
            f"{sheet.column_remaining:.0f} mm left); shorten the notes")
    draw_legend(sheet, legend)
    _place_notes_and_sources(sheet, notes, src, columns=band_cols, spill=spill)

    sheet.draw_title_block()
    return sheet
