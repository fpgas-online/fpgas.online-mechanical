"""Three-view drawing for a packaged item such as a PoE splitter.

These parts are enclosures, not bare boards, so a single plan view says
nothing useful about how they mount.  The sheet carries a front elevation, a
plan below it and an end view to its left: first-angle projection, where each
view is placed on the side opposite the direction it is viewed from.
"""

from __future__ import annotations

from data.schema import BoardSpec

from . import dims, style
from .board_sheet import _place_notes_and_sources
from .sheet import Rect, Sheet, TitleBlock
from .view import STANDARD_SCALES, View, scale_text

GAP = 26.0          # space between views, for the dimensions that go there


def _pick_scale(length: float, depth: float, height: float,
                area: Rect) -> tuple[float, str]:
    need_w = length + GAP + depth
    need_h = height + GAP + depth
    # Reserve room for the dimensions that sit outside the view block: an
    # overall dimension plus its text on the left and below, and the height
    # dimension on the right.
    for num, den in STANDARD_SCALES:
        s = num / den
        if need_w * s <= area.w - 52 and need_h * s <= area.h - 64:
            return s, scale_text(num, den)
    return 1.0, "1:1"


def render_enclosure(spec: BoardSpec, *, drawing_no: str, date: str,
                     sheet_size: str = "A3") -> Sheet:
    o = spec.outline
    length, depth = o.width, o.height
    height = o.z_height or 10.0

    sheet = Sheet(sheet_size, TitleBlock(
        title=spec.title.upper(), subtitle=spec.subtitle,
        drawing_no=drawing_no, rev="A", date=date, drawn_by="generated",
        material="sealed enclosure",
        tolerance="envelope +/-1.0 unless noted",
        projection="first angle"))
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

    # The body is an extrusion, so its corner radii belong to the cross
    # section.  Only the end view shows them; the plan and the elevation are
    # plain rectangles.  Drawing the radius on the plan as well, as this sheet
    # used to, says the part is rounded in two directions at once.
    box(front)
    box(plan)
    box(end, radius=o.corner_radius * scale)

    # Captions above each view, so the space below stays free for dimensions.
    for r, name in ((front, "FRONT ELEVATION"), (plan, "PLAN"),
                    (end, "END VIEW, RJ45 END")):
        c.text(r.cx, r.y1 + 4.0, name, size=style.T_LABEL, anchor="middle",
               bold=True)

    # Features are given in plan coordinates: X along the length, Y across the
    # depth.  Project each onto the plan, and onto the end view where it sits
    # in an end face.
    for f in spec.features:
        px = plan.x + f.x0 * scale
        py = plan.y + f.y0 * scale
        c.rect(px, py, (f.x1 - f.x0) * scale, (f.y1 - f.y0) * scale,
               weight=style.W_COMPONENT, colour=style.C_HIGHLIGHT,
               fill=style.C_FILL_LIGHT)
        if f.kind == "ethernet":
            # The RJ45 is in the end plate, so it also shows in the end view,
            # where its aperture is what a bracket has to clear.
            ex = end.x + f.y0 * scale
            ew = (f.y1 - f.y0) * scale
            eh = 13.0 * scale
            ey = end.cy - eh / 2
            c.rect(ex, ey, ew, eh, weight=style.W_COMPONENT,
                   colour=style.C_HIGHLIGHT, fill=style.C_FILL_LIGHT)
            # Aperture size and position in the end face, both of which a
            # bracket has to clear.
            dims.linear(c, (ex, ey), (ex + ew, ey), -14.0, horizontal=True,
                        value=f.y1 - f.y0)
            dims.linear(c, (ex, ey), (ex, ey + eh), -14.0, horizontal=False,
                        value=eh / scale)
            dims.linear(c, (end.x, ey), (end.x, end.y), -26.0,
                        horizontal=False, value=(ey - end.y) / scale)
            # Jack size and position along the body, in the plan.
            dims.linear(c, (plan.x + f.x0 * scale, plan.y1),
                        (plan.x + f.x1 * scale, plan.y1), 9.0,
                        horizontal=True, value=f.x1 - f.x0)
            dims.linear(c, (plan.x, plan.y), (plan.x + f.x0 * scale, plan.y),
                        -25.0, horizontal=True, value=f.x0)

    dims.linear(c, (plan.x, plan.y), (plan.x1, plan.y), -14.0,
                horizontal=True, value=length)
    dims.linear(c, (plan.x, plan.y), (plan.x, plan.y1), -14.0,
                horizontal=False, value=depth)
    dims.linear(c, (front.x1, front.y), (front.x1, front.y1), 14.0,
                horizontal=False, value=height)
    dims.linear(c, (end.x, end.y), (end.x1, end.y), -14.0, horizontal=True,
                value=depth)
    # Below the view, not above: the caption sits above and is wider than the
    # view itself, so an upward leader runs straight through it.
    dims.leader(c, (end.x1 - o.corner_radius * scale * 0.3,
                    end.y + o.corner_radius * scale * 0.3),
                (end.x1 + 9.0, end.y - 7.0),
                f"R{o.corner_radius:.2f} nominal (4 places)")
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

    notes = [
        "All dimensions in millimetres. The datum symbol on the plan marks the "
        "origin: the lower-left corner of the body envelope, X along the "
        "length, Y across the width, Z up.",
        "First-angle projection. The plan is the view from above, placed below "
        "the front elevation; the end view is the view from the RJ45 end, "
        "placed to the left of it.",
        "The RJ45 aperture drawn in the end view is a standard 8P8C jack "
        "envelope, positioned centrally because the vendor does not dimension "
        "it. Its size and position are indicative to about +/-1.5 mm; the body "
        "envelope itself is the dimension to trust.",
        "The corner radius is nominal. It is a cross-section feature of the "
        "extrusion, so it appears in the end view only.",
    ] + list(spec.notes)
    src = [f"{s.label}: {s.ref}" + (f" - {s.note}" if s.note else "")
           for s in spec.sources]
    _place_notes_and_sources(sheet, notes, src)

    sheet.draw_title_block()
    return sheet
