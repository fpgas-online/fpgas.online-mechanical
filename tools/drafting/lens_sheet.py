"""The OV5647's lens options: every field of view and focus figure, drawn.

One sheet for the lenses themselves, separate from the four camera position
sheets that compute with them: those carry the figures they use and send
the reader here for the rest -- every declared figure, what each one was
checked against, which one was rejected and why, and the depth of field.

Two views of the same thing: a camera 100 mm above a flat board, once with
each lens.  A section across the picture's long side, drawing both lenses'
rays from the lens to where the picture's edge meets the board; and the plan
of what each picture covers on the board, which is where a fisheye shows
itself.  The stock lens's picture is a
rectangle.  The 120 degree lens's is not: walked down onto the board from
the sensor's edge under the equidistant projection, each straight side of
the sensor lands as a curve bowing outwards, and the rectangle its angles
give -- which is what every height on the position sheets is worked from --
sits inside it, touching it at the middle of each side.

The height is a reference, not a recommendation: every figure on the views
scales with it.  The position sheets give the heights a subject needs.
"""

from __future__ import annotations

import math

from raspberry_pi_camera import optics

from . import dims, style
from .board_sheet import draw_legend, note_blocks
from .camera_sheet import RAYS, _deg, _draw_camera
from .sheet import Rect, Sheet, TitleBlock
from .view import STANDARD_SCALES, View, scale_text

#: The height of the lens above the board every view is drawn at.
Z_REF = 100.0

#: Room round the views, in sheet millimetres.
LEFT = 14.0
GAP = 10.0
CAPTION = 7.0
UNDER = 22.0            # two lanes of widths under each view
RIGHT = 24.0            # the height, or the plan's depths, on the right
NO_BAND = 2.0
ABOVE_LENS = 12.0       # room for the camera drawn over the lens

#: The equidistant outline is walked at this many points a side.
STEPS = 48

#: The rectangle the wide lens's angles give on the board, which the
#: heights are worked from: phantom, frame A's colour, as a frame is drawn.
USED_RECT = ("line", style.W_PHANTOM, style.C_FRAME_A, style.D_PHANTOM)


class DoesNotFit(Exception):
    """This scale leaves the views or the notes nowhere to go."""


def _cover(lens, axis: str) -> float:
    """Half the width of *lens*'s picture on the board, across *axis*."""
    a = lens.fov_h if axis == "H" else lens.fov_v
    return Z_REF * math.tan(math.radians(a / 2))


def _fisheye_outline(lens) -> list[tuple[float, float]]:
    """The wide lens's picture on the board, as a closed outline.

    The sensor's edge, point by point, turned back into a field angle by the
    lens's projection with its own focal length, and sent down to the board
    Z_REF below: theta = r / f, and a point theta off the axis lands
    Z tan(theta) out, in the direction of the image point.
    """
    w, h = optics.ARRAY_WIDTH / 2, optics.ARRAY_HEIGHT / 2
    corners = [(w, -h), (w, h), (-w, h), (-w, -h), (w, -h)]
    out = []
    for (u0, v0), (u1, v1) in zip(corners, corners[1:]):
        for i in range(STEPS):
            u = u0 + (u1 - u0) * i / STEPS
            v = v0 + (v1 - v0) * i / STEPS
            r = math.hypot(u, v)
            theta = r / lens.focal_length
            out.append((Z_REF * math.tan(theta) * u / r,
                        Z_REF * math.tan(theta) * v / r))
    out.append(out[0])
    return out


# ---------------------------------------------------------------------------
# the views
# ---------------------------------------------------------------------------

def _section(sheet: Sheet, v: View, axis: str) -> None:
    """Both lenses from one point, across one axis of the picture."""
    c = sheet.canvas
    wide = optics.LENS_120
    reach = _cover(wide, axis)
    c.line(*v.pt(-reach - 4.0, 0.0), *v.pt(reach + 4.0, 0.0),
           w=style.W_OUTLINE)
    apex = v.pt(0.0, Z_REF)
    lane = 8.0
    for lens in optics.LENSES.values():
        half = _cover(lens, axis)
        _, w, colour, dash = RAYS[lens.key]
        for e in (-half, half):
            c.line(*apex, *v.pt(e, 0.0), w=w, colour=colour, dash=dash)
        a = lens.fov_h if axis == "H" else lens.fov_v
        # Both angles from one apex, so each value goes outside both cones:
        # the stock lens's on the left, past the wide lens's ray at that
        # height, and the wide lens's on the right of its own, larger arc.
        stock = lens.key == "65"
        r = 13.0 if stock else 24.0
        hr = math.radians(a / 2)
        left = (apex[0] - r * math.sin(hr), apex[1] - r * math.cos(hr))
        right = (apex[0] + r * math.sin(hr), apex[1] - r * math.cos(hr))
        c.arc(*left, *right, r, sweep=1, w=style.W_THIN, colour=style.C_DIM)
        label = f"{_deg(a)} deg, {axis}"
        wide_half = math.radians((wide.fov_h if axis == "H"
                                  else wide.fov_v) / 2)
        if stock:
            y = left[1] + 1.0
            x = apex[0] - (apex[1] - y) * math.tan(wide_half) - 1.5
            c.text(x, y, label, size=style.T_DIM, colour=style.C_DIM,
                   anchor="end")
        else:
            c.text(right[0] + 1.5, right[1] - 1.0, label, size=style.T_DIM,
                   colour=style.C_DIM, anchor="start")
        # What it covers, under the board line.
        dims.linear(c, v.pt(-half, 0.0), v.pt(half, 0.0), -lane,
                    horizontal=True, value=2 * half, places=1)
        lane += style.DIM_STEP
    # The optical axis.
    c.line(*v.pt(0.0, -2.0), *v.pt(0.0, Z_REF + ABOVE_LENS - 3.0),
           w=style.W_CENTRE, colour=style.C_LINE, dash=style.D_CENTRE)
    # The camera, lens down: its board's width across the long side.
    along, sign = ("u", -1) if axis == "H" else ("v", 1)
    _draw_camera(c, v, 0.0, Z_REF, along, sign)
    if axis == "H":
        dims.linear(c, v.pt(v.model_x1, 0.0), apex, 8.0, horizontal=False,
                    value=Z_REF, places=0)


def _plan(sheet: Sheet, v: View) -> None:
    """What each lens's picture covers on the board, seen from above."""
    c = sheet.canvas
    stock, wide = optics.LENS_65, optics.LENS_120
    # The stock lens: a rectangle, straight-sided, since it is rectilinear.
    hx, hy = _cover(stock, "H"), _cover(stock, "V")
    _, w, colour, dash = RAYS[stock.key]
    a, b = v.pt(-hx, -hy), v.pt(hx, hy)
    c.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], weight=w, colour=colour)
    # The wide lens: the outline its projection gives, and inside it the
    # rectangle its angles give.
    _, w, colour, dash = RAYS[wide.key]
    pts = [v.pt(x, y) for x, y in _fisheye_outline(wide)]
    c.polyline(pts, w=w, colour=colour, dash=dash)
    wx, wy = _cover(wide, "H"), _cover(wide, "V")
    a, b = v.pt(-wx, -wy), v.pt(wx, wy)
    c.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], weight=USED_RECT[1],
           colour=USED_RECT[2], dash=USED_RECT[3])
    ax, ay = v.pt(0.0, 0.0)
    dims.centre_mark(c, ax, ay, 1.6, colour=style.C_LINE, over=2.6)
    # Widths under, depths on the right, the stock lens's inside.
    lane = 8.0
    for lens, x, y in ((stock, hx, hy), (wide, wx, wy)):
        dims.linear(c, v.pt(-x, -wy), v.pt(x, -wy), -lane, horizontal=True,
                    value=2 * x, places=1)
        dims.linear(c, v.pt(wx, -y), v.pt(wx, y), lane, horizontal=False,
                    value=2 * y, places=1)
        lane += style.DIM_STEP


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------

def _rows_fov() -> list[list[str]]:
    """Every field of view figure for every lens, and what became of it.

    The pair a lens is computed with is marked USED on the row it is, rather
    than repeated: for the wide lens that is the catalogue's own 96 x 72 and
    the equidistant split of the diagonal, which are one pair.
    """
    rows = []
    for lens in optics.ALL_LENSES.values():
        first = True
        for fg in lens.figures:
            if fg.rejected:
                use = "REJECTED"
            elif (fg.h is not None and fg.v is not None
                  and abs(fg.h - lens.fov_h) < 0.005
                  and abs(fg.v - lens.fov_v) < 0.005):
                use = "USED"
            elif any(a.what == fg.what for a in lens.alternatives):
                use = "margin"
            else:
                use = ""
            rows.append([lens.short if first else "", fg.what, fg.kind[:4],
                         "--" if fg.h is None else _deg(round(fg.h, 2)),
                         "--" if fg.v is None else _deg(round(fg.v, 2)),
                         "--" if fg.d is None else _deg(round(fg.d, 2)),
                         use])
            first = False
    return rows


def _rows_focus() -> list[list[str]]:
    rows = []
    for lens in optics.ALL_LENSES.values():
        h2 = lens.hyperfocal
        h1 = optics.hyperfocal(lens.focal_length, lens.f_number,
                               optics.PIXEL_PITCH)
        rows.append([
            lens.short,
            f"{lens.focal_length:.2f} {lens.focal_basis[0]}",
            f"F{lens.f_number:g} {lens.f_basis[0]}", lens.focus,
            f"{lens.near:.0f} to inf",
            f"{h2 / 1000:.2f} / {h1 / 1000:.2f}",
            f"{h2 / 2000:.2f} / {h1 / 2000:.2f}"])
    rows.append(["WS G", "3.15", "F2.35", "Adjustable", "100 to inf", "--",
                 "--"])
    return rows


def _rows_af() -> list[list[str]]:
    af = optics.AUTOFOCUS
    rows = []
    for z in (af.near, 100.0, 150.0):
        near, far = optics.dof(z, af.focal_length, af.f_number)
        rows.append([f"{z:.0f}", f"{near:.1f}", f"{far:.1f}",
                     f"{far - near:.1f}"])
    return rows


def _text() -> tuple[list[str], list[str]]:
    stock, af, wide = optics.LENS_65, optics.AUTOFOCUS, optics.LENS_120
    rect = optics.split_diagonal(120.0, "rectilinear")
    solid = optics.split_diagonal(120.0, "equisolid")
    on_sensor, on_subject = stock.blur(Z_REF)
    w_sensor, w_subject = wide.blur(Z_REF)
    ws = optics.WAVESHARE_G_FIGURES[-1]
    corner = max(_fisheye_outline(wide), key=lambda p: p[0] + p[1])
    notes = [
        f"65: rectilinear; its {_deg(stock.fov_h)} x {_deg(stock.fov_v)} "
        f"come back out of {stock.focal_length:.2f} mm on the 3.6288 x "
        "2.7216 mm active array to 0.01 deg. The 65 it is sold as is the "
        f"diagonal, {optics.DIAGONAL_FROM_ARRAY:.2f} on the array and "
        f"{optics.DIAGONAL_FROM_DATASHEET:.2f} on OmniVision's image area.",
        f"AF: 54 across implies "
        f"{optics.implied_v(54.0, 'rectilinear'):.2f} down, so neither "
        f"declared V is exact; the lower, {_deg(af.fov_v)}, is used. f from "
        "the 35 mm equivalent over the 43.27 mm full-frame diagonal.",
        f"120: the page's {wide.fov_d:.0f} is the DIAGONAL, so the "
        "catalogue's 120 x 90 is REJECTED: no lens sees as far across as to "
        "the corner. Its 96 x 72 for the same camera without IR filter is "
        "that diagonal split equidistantly, r = f theta, as Commonlands find"
        " for a real fisheye; rectilinear is the widest a lens can be. Every"
        " position sheet's margin is checked to absorb those marked margin.",
        f"DISTORTION: a ray A/2 off the axis meets a board Z below at "
        "Z tan(A/2) whatever the lens did to it. The dashed outline is the "
        "sensor's edge walked onto the board equidistantly: its sides bow "
        "outwards, so the rectangle "
        "the angles give, which every height is worked from, is inside the "
        f"picture: its corner reaches {corner[0]:.1f}, {corner[1]:.1f} "
        f"against the rectangle's {_cover(wide, 'H'):.1f}, "
        f"{_cover(wide, 'V'):.1f}. At the long side's edge a pixel covers "
        f"{1 / math.cos(math.radians(wide.fov_h / 2)) ** 2:.2f} x the board "
        "it does on the axis.",
        f"DEPTH OF FIELD, DERIVED, thin lens, circle of confusion "
        f"{optics.COC_PIXELS} px, {optics.COC * 1000:.1f} um: hyperfocal "
        "f^2 / (N c) + f, sharp from half of it to infinity focused there. "
        "Raspberry Pi's \"Approx 1 m to infinity\" is a "
        f"{optics.IMPLIED_COC / optics.PIXEL_PITCH:.1f} px circle.",
        f"FIXED FOCUS, ASSUMED at {stock.focus_at / 1000:g} m, twice the "
        f"declared 1 m. At {Z_REF:.0f} mm a point spreads to "
        f"{on_sensor / optics.PIXEL_PITCH:.0f} px, {on_subject:.1f} mm on "
        f"the board, at {stock.short}, {w_sensor / optics.PIXEL_PITCH:.0f} "
        f"px, {w_subject:.1f} mm, at {wide.short}: out of focus.",
        "AF: \"80mm to infinity\", the B0121 \"4 cm\"; the 80 is used. "
        "No 120 deg motorised OV5647 is sold.",
        f"WS G, Waveshare's RPi Camera (G), is sold as 160 deg diagonal and"
        f" 120 across; its 3.15 mm gives {ws.d:.1f} diagonal equidistantly,"
        " so its figures do not hold together and it is not drawn.",
    ]
    # The pages by name, and where their addresses are: pinned Internet
    # Archive captures a hundred and more characters long each, which wrapped
    # to half this sheet's paper.  raspberry_pi_camera/optics.py gives every
    # one beside the figures it supports, the fetch script caches them, and
    # verify_optics.py checks every quote on this sheet against the cached
    # page.
    pages = [s.label for s in (
        optics.RPI_DOC, optics.OV5647_DATASHEET, optics.ARDUCAM_DOC,
        optics.ARDUCAM_B006604, optics.ARDUCAM_B0121, optics.UCTRONICS_B0176,
        optics.ARDUCAM_AF, optics.COMMONLANDS, optics.YXF_M6,
        optics.WAVESHARE_G)]
    src = [
        "; ".join(pages) + ". Addresses, pinned Internet Archive captures "
        "where one exists, in raspberry_pi_camera/optics.py; every quote "
        "checked against the cached page by "
        "raspberry_pi_camera/verify_optics.py, "
        "in ASCII here: x, um, deg and infinity for the pages' signs.",
    ]
    return notes, src


def _tables(sheet: Sheet) -> None:
    rows = _rows_fov()
    title = "FIELD OF VIEW, deg, EVERY FIGURE"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["", "FIGURE", "", "H", "V", "DIAG", ""], rows,
                ["start", "start", "start", "end", "end", "end", "start"])
    rows = _rows_focus()
    title = f"FOCUS; HYPERFOCAL AND NEAR AT {optics.COC_PIXELS} / 1 px"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title,
                ["", "f mm", "F", "FOCUS", "RANGE, mm", "HYPER m",
                 "NEAR m"], rows,
                ["start", "end", "start", "start", "end", "end", "end"])
    rows = _rows_af()
    title = f"{optics.AUTOFOCUS.short}, FOCUSED AT Z: SHARP FROM, TO, mm"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["Z", "NEAR", "FAR", "DEPTH"], rows,
                ["end", "end", "end", "end"])


def _legend() -> list:
    out = []
    for lens in optics.LENSES.values():
        out.append((RAYS[lens.key],
                    f"The {lens.short} deg lens: rays, and its picture on "
                    "the board"))
    out.append((USED_RECT, f"The rectangle the {optics.LENS_120.short} deg "
                           "lens's angles give"))
    out.append((("line", style.W_COMPONENT, style.C_HIGHLIGHT, None),
                "Camera Module v1.3"))
    out.append(("dimension", "Dimension, extension and leader"))
    return out


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------

def _layout(scale: float, area: Rect):
    """Where the two views go at *scale*, or None if they do not fit.

    The section across the long side at the top left, the plan under it.
    No section along the short side: the plan dimensions both lenses'
    pictures that way, the table gives the angle, and the paper it would
    take is the notes'.
    """
    wide = optics.LENS_120
    hx = _cover(wide, "H") + 4.0
    outline = _fisheye_outline(wide)
    px = max(abs(x) for x, _ in outline) + 2.0
    py = max(abs(y) for _, y in outline) + 2.0
    s = scale
    z0, z1 = -2.0, Z_REF + ABOVE_LENS
    sec_h = (z1 - z0) * s
    h_w = 2 * hx * s
    plan_w, plan_h = 2 * px * s, 2 * py * s
    height = (CAPTION + sec_h + UNDER + CAPTION + plan_h + UNDER)
    width = LEFT + max(h_w, plan_w) + RIGHT
    if width > area.w or height > area.h:
        return None
    top = area.y1 - CAPTION
    left = area.x + LEFT
    hsec = View(Rect(left, top - sec_h, h_w, sec_h), -hx, z0, hx, z1, s,
                _label(s), left + hx * s, top - z1 * s)
    ptop = top - sec_h - UNDER - CAPTION
    plan = View(Rect(left, ptop - plan_h, plan_w, plan_h), -px, -py, px, py,
                s, _label(s), left + px * s, ptop - py * s)
    return hsec, plan


def _label(scale: float) -> str:
    return scale_text(1, 1 / scale) if scale < 1 else scale_text(scale, 1)


def render_lenses(*, title: str, subtitle: str, drawing_no: str,
                  version: str, sheet_size: str = "A3") -> Sheet:
    """The largest standard scale at which the views and the text fit."""
    why = []
    for num, den in STANDARD_SCALES:
        try:
            return _render(num / den, title=title, subtitle=subtitle,
                           drawing_no=drawing_no, version=version,
                           sheet_size=sheet_size)
        except DoesNotFit as e:
            why.append(f"{_label(num / den)}: {e}")
    raise SystemExit("the lens sheet fits at no scale:\n  " + "\n  ".join(why))


def _render(scale: float, *, title: str, subtitle: str, drawing_no: str,
            version: str, sheet_size: str) -> Sheet:
    notes, src = _text()
    sheet = Sheet(sheet_size, TitleBlock(
        title=title.upper(), subtitle=subtitle, drawing_no=drawing_no,
        rev="A", version=version, drawn_by="generated",
        scale=_label(scale), projection="first angle",
        material="OV5647 lenses", material_label="SUBJECT",
        tolerance="angles as declared, D and A as flagged"),
        notes_band_height=NO_BAND)
    got = _layout(scale, sheet.area)
    if got is None:
        raise DoesNotFit("the views do not fit the drawing area")
    hsec, plan = got
    sheet.draw_frame()
    c = sheet.canvas
    _section(sheet, hsec, "H")
    _plan(sheet, plan)
    for v, name in ((hsec, "SECTION ACROSS THE LONG SIDE"),
                    (plan, f"PLAN: THE PICTURE ON A BOARD {Z_REF:.0f} "
                           "BELOW")):
        c.text(v.rect.cx, v.rect.y1 + 3.0, name, size=style.T_LABEL,
               anchor="middle", bold=True)
    _tables(sheet)
    draw_legend(sheet, _legend())

    # Notes: beside the section, beside the plan, across the foot, then the
    # column's foot.
    f = sheet.frame
    base = f.y + 3.0
    x0, x1 = f.x + 4.0, sheet.area.x1 - 2.0
    top = sheet.area.y1
    sec_bottom = hsec.rect.y - UNDER
    plan_bottom = plan.rect.y - UNDER
    cols = []
    for view, lo, hi, room in ((hsec, sec_bottom - CAPTION, top, 16.0),
                               (plan, plan_bottom, sec_bottom - CAPTION,
                                RIGHT)):
        beside = view.rect.x1 + room + 4.0
        if x1 - beside >= 50.0 and hi - lo >= 20.0:
            cols.append(Rect(beside, lo, x1 - beside, hi - lo))
    w = (x1 - x0 - 8.0) / 2
    if plan_bottom - base > 20.0:
        cols += [Rect(x0 + i * (w + 8.0), base, w, plan_bottom - base)
                 for i in range(2)]
    blocks = note_blocks(notes, src)
    if not sheet.notes_columns(cols, blocks, dry=True):
        h = 20.0
        while True:
            if h > sheet.column_remaining - 4.0:
                raise DoesNotFit("the notes do not fit")
            probe = Rect(sheet.column.x, sheet.column.y,
                         sheet.column.w - sheet.COLUMN_GUTTER, h)
            if sheet.notes_columns(cols + [probe], blocks, dry=True):
                break
            h += 2.0
        cols.append(sheet.column_block_bottom(h))
    sheet.notes_columns(cols, blocks)
    sheet.draw_title_block()
    return sheet
