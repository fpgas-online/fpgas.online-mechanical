"""The direct Raspmod on a Raspberry Pi: what is under it, and where a fourth plug would go.

The adapter's own sheet draws the adapter.  This one draws it where it
lives: on a Raspberry Pi's 40-pin header, pin 1 on pin 1, with every Model
B sized Pi under it at once -- the outline, holes and header they share,
and the parts some model puts inside the adapter's footprint, each named
with its height.  Beside P3, in phantom, a fourth plug one host pitch on
and the edge a board four plugs wide would have.  It is the sheet a board
reshaped to fit every model, with a plug for each of the Arty's hosts, is
drawn against.

Its own sheet rather than an overlay on the adapter's, because the Pi is
85 mm long: with it in the view the adapter's sheet fell from 2:1 to 1:1,
and its annotation, laid out for 2:1, ran into everything.  Here the view
has the width of the sheet and keeps 2:1.
"""

from __future__ import annotations

from accessories.pi_under import (CLASH_PARTS, adapter_on_pi, grown_edge,
                                  host_pitch, pi_pin1, pi_under_direct)
from accessories.raspmod_direct import PI_PIN1, RASPMOD_DIRECT
from base_plates.plates import ADAPTER_UNDER
from tools.layout import acc_stem, drawing_name

from . import dims, style
from .board_sheet import (draw_feature, draw_overlay, draw_pmod, note_blocks,
                          outline_path, place_legend_and_notes)
from .sheet import Sheet, TitleBlock
from .view import View

TITLE = "Raspmod, direct, on a Raspberry Pi"
SUBTITLE = ("Every Model B sized Pi under the adapter, pin 1 on pin 1, and where "
            "a fourth plug would go")

#: Room round the view.  The sides are as thin as the sheet allows: the
#: view is 104 mm wide and the drawing area 217, and 2:1 is what makes the
#: pin fields legible, so nothing is dimensioned at the sides.
SIDE = 3.5
TOP = 12.0
BOTTOM = 22.0


def _models(part) -> str:
    return part.label.split(", ", 1)[1] if ", " in part.label else ""


def _text() -> tuple[list[str], list[str]]:
    adapter = drawing_name("accessories", acc_stem(RASPMOD_DIRECT.key))
    p1 = pi_pin1()
    x0, y0, x1, y1 = adapter_on_pi()
    notes = [
        "Viewed from the component side; the Pi is seen through the adapter.",
        "Phantom outline is the Raspberry Pi -- the 85 x 56 outline, four holes and "
        "40-pin header every Model B sized model shares, and the Pi 5's two extra "
        f"holes -- turned a half turn to the adapter: the adapter's pin 1, at "
        f"({PI_PIN1[0]}, {PI_PIN1[1]}), sits on the Pi's pin 1, at ({p1[0]}, {p1[1]}) "
        "on the Pi.",
        f"The adapter's underside is {ADAPTER_UNDER} above the Pi's top face (its header "
        "body 2.54, the socket 3.8), and it covers the Pi from X "
        f"{x0:.2f} to {x1:.2f} and Y {y0:.2f} out past the header edge. A part of the "
        "Pi in that strip and taller than that stops it seating; the boxes are those "
        "parts, with their heights. Every model's USB and Ethernet stack stands beyond "
        "the adapter's far end and is not drawn.",
    ]
    for p in CLASH_PARTS:
        verdict = (f"CLASH, {p.z - ADAPTER_UNDER:.2f} too tall" if p.clashes
                   else f"clears by {ADAPTER_UNDER - p.z:.2f}")
        notes.append(f"{p.label}: Z {p.z:g}, {verdict}. {p.source}.")
    notes += [
        "FITS a Pi 3 Model B or a Pi 5; NOT a 3 Model B+ or a 4 Model B, whose PoE "
        "header is under it.",
        f"P4? is a fourth plug one host pitch, {host_pitch():.2f}, beyond P3, and the "
        f"phantom edge is a board four plugs wide, {grown_edge().x1:.2f}. The Pi has "
        "nothing under the board there; grown the other way it meets the Pi's USB and "
        "Ethernet stack.",
        f"The adapter is {adapter}, which governs it, and whose pin mapping is not yet "
        "right: its plugs mate in mirror image as drawn.",
    ]
    src = [
        f"Adapter: accessories/raspmod_direct.py, {adapter} - outline, plugs, socket pin 1",
        "Raspberry Pi: raspberry_pi/boards.py - outline, holes and header, from Raspberry "
        "Pi Ltd's drawings; the parts under the adapter from the Pi 4 and Pi 5 drawings, "
        "accessories/pi_under.py",
    ]
    return notes, src


def _tables(sheet: Sheet) -> None:
    rows = [[p.label.split(",")[0], _models(p), f"{(p.x0 + p.x1) / 2:.2f}",
             f"{(p.y0 + p.y1) / 2:.2f}", f"{p.z:g}", "CLASH" if p.clashes else "clears"]
            for p in CLASH_PARTS]
    title = "UNDER THE ADAPTER, on the Pi"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["PART", "MODELS", "CX mm", "CY mm", "Z mm", ""], rows,
                ["start", "start", "end", "end", "end", "start"])
    x0, y0, x1, y1 = adapter_on_pi()
    p1 = pi_pin1()
    rows = [["Adapter pin 1 on the Pi", f"{p1[0]:.2f}", f"{p1[1]:.2f}"],
            ["Adapter, near corner", f"{x0:.2f}", f"{y0:.2f}"],
            ["Adapter, far corner", f"{x1:.2f}", f"{y1:.2f}"]]
    title = "THE ADAPTER ON THE PI, in the Pi's frame"
    block = sheet.column_block(sheet.table_height(title, len(rows)))
    sheet.table(block, title, ["", "X mm", "Y mm"], rows, ["start", "end", "end"])


def render_fit(*, drawing_no: str, version: str, sheet_size: str = "A3") -> Sheet:
    adapter = RASPMOD_DIRECT
    pi = pi_under_direct()
    notes, src = _text()
    band_h, band_cols = Sheet.plan_notes_band(sheet_size, note_blocks(notes, src),
                                              max_height=44.0)
    sheet = Sheet(sheet_size, TitleBlock(
        title=TITLE.upper(), subtitle=SUBTITLE, drawing_no=drawing_no, rev="A",
        version=version, drawn_by="generated", material="-  not a made part",
        tolerance="reference only - the boards' own sheets govern them"),
        notes_band_height=band_h)
    sheet.draw_frame()
    c = sheet.canvas

    xs, ys = [], []
    for e in (pi.outline.extent(), adapter.outline.extent()):
        xs += [e[0], e[2]]
        ys += [e[1], e[3]]
    for f in pi.features:
        xs += [f.x0, f.x1]
        ys += [f.y0, f.y1]
    for p in adapter.pmods:
        if p.body_x1 > p.body_x0:
            xs += [p.body_x0, p.body_x1]
            ys += [p.body_y0, p.body_y1]
    view = View.fit(sheet.area, (min(xs), min(ys), max(xs), max(ys)), margin=SIDE,
                    margin_top=TOP, margin_bottom=BOTTOM, margin_right=SIDE)
    sheet.title.scale = view.scale_label

    # The parts' names go up into the Pi's empty half above the adapter:
    # the view is the width of the sheet, so there is no room beside it.
    draw_overlay(c, view, pi, parts=True, names="up")
    for f in adapter.features:
        draw_feature(c, view, f)
    for p in adapter.pmods:
        draw_pmod(c, view, p, adapter)
    outline_path(c, view, adapter)

    # The widths, under the plugs' pins; the Pi's reach past the socket
    # end, over it.  What else a reader wants is in the tables.
    o = adapter.outline
    below = view.y(min(ys)) - view.y(0.0) - 7.0
    dims.linear(c, view.pt(0.0, 0.0), view.pt(o.width, 0.0), below, horizontal=True,
                value=o.width)
    dims.linear(c, view.pt(0.0, 0.0), view.pt(grown_edge().x1, 0.0),
                below - style.DIM_STEP, horizontal=True, value=grown_edge().x1)
    px0, _, _, py1 = pi.outline.extent()
    dims.linear(c, view.pt(px0, py1), view.pt(0.0, py1), 6.0, horizontal=True,
                value=-px0)
    dims.datum_marker(c, view.x(0.0), view.y(0.0), label="")

    _tables(sheet)
    legend = [("outline", "The adapter, its outline"),
              ("component", "Component body, scheduled on the adapter's sheet"),
              ("hidden", "On the adapter's underside, seen through it"),
              ("phantom", "The Raspberry Pi under it, and what is on it; P4? and the edge "
                          "of a board four plugs wide"),
              ("dimension", "Dimension, extension and leader")]
    place_legend_and_notes(sheet, legend, notes, src, columns=band_cols, name=drawing_no)
    sheet.draw_title_block()
    return sheet
