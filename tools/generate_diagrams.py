#!/usr/bin/env python3
"""Generate every mechanical drawing from each family's own data module.

Writes SVG, PDF and PNG for each sheet into its family's ``output/``
directory, as named by ``tools.layout``.

Run: uv run --no-project --with pillow python tools/generate_diagrams.py
     add --no-raster to skip the PDF and PNG conversions while iterating.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import (ACCESSORIES, ACORN_WIDTH,  # noqa: E402
                               GENERIC_POE,
                               M2_CARD_WIDTH, M2_LENGTHS,
                               M2_STANDOFF_THREAD,
                               POE_M2_BOSS_DIA, POE_M2_DATUM_X,
                               POE_M2_HAT_TOL, POE_M2_HAT_WIDTH,
                               POE_M2_HAT_WITH_ACORN, POE_M2_SOCKET_TOL,
                               POE_M2_STANDOFF_OVERHANG,
                               PMOD_HAT, PMOD_HAT_TOL, WAVESHARE_POE)
from accessories.raspmod import RASPMOD  # noqa: E402
from fpga.boards import BOARDS as FPGA_BOARDS  # noqa: E402
from fpga.boards import FEATURE_NUMBERS as FPGA_NUMBERS  # noqa: E402
from fpga.light_pipe.adapter import ADAPTER as LIGHT_PIPE  # noqa: E402
from raspberry_pi.boards import BOARDS as RPI_BOARDS  # noqa: E402
from raspberry_pi.boards import FEATURE_NUMBERS as RPI_NUMBERS  # noqa: E402
from raspberry_pi_camera.boards import (  # noqa: E402
    BOARDS as RPICAM_BOARDS, FEATURE_NUMBERS as RPICAM_NUMBERS)
from raspberry_pi_camera.optics import subjects as rpicam_subjects  # noqa: E402
from tinytapeout.boards import BOARDS as TT_BOARDS  # noqa: E402
from tinytapeout.boards import FEATURE_NUMBERS as TT_NUMBERS  # noqa: E402
from tools.drafting.board_sheet import (planned_band_height,  # noqa: E402
                                        render_board)
from tools.drafting.camera_sheet import render_camera_position  # noqa: E402
from tools.drafting.enclosure_sheet import render_enclosure  # noqa: E402
from tools.drafting.lightpipe_sheet import render_light_pipe  # noqa: E402
from tools.drafting.plate_sheet import render_fitting_guide, render_plate  # noqa: E402
from tools.drafting import rpi_compare_sheet  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE  # noqa: E402
from tools.drafting.template_sheet import render_drill_template  # noqa: E402
from tools.layout import (DRILL_TEMPLATE_STEMS, FAMILY_DIRS,  # noqa: E402
                          FITTING_GUIDE_SHEET, FITTING_GUIDE_STEM,
                          PLATE_SHEET, PLATE_STEM, PMOD_HAT_SHEET,
                          PMOD_HAT_STEM, acc_stem, drawing_name,
                          preview_for, rel, slug, tt_stem)
from tools.render_svg import combine_pdfs  # noqa: E402
from tools import reproducible  # noqa: E402

#: Stamped into every sheet's title block where a render date used to go.
#: See tools/reproducible.py: a date changed every sheet whenever anyone
#: rebuilt on a new day, and never said which data a drawing came from.
VERSION = reproducible.source_version()

#: Every A3 Tiny Tapeout sheet bound into one document, beside the sheets it
#: is made of: the two mounting plate drawings first, then the six demo
#: boards.  The plate is what a reader of the set is designing against, and
#: the fitting guide is the index to the board sheets that follow it.  Not
#: the drill templates -- those are A4 portrait, and a document that mixes
#: page sizes is one where "print all" silently scales the pages that have
#: to be 1:1.  They stay separate files, which is also how anyone uses them:
#: you print the template, not the set.  Not an SVG and not rendered from
#: one, so it is the only file in an output directory with no drawing of its
#: own.
TT_BUNDLE = "tinytapeout-sheets.pdf"

#: The Raspberry Pi sheets bound the same way, for the same reasons: the
#: three models, then the comparison sheet, which draws them on top of one
#: another.
RPI_BUNDLE = "raspberry-pi-sheets.pdf"

#: And the camera family: the two board sheets, which are a pair -- the same
#: board twice, with the lens module the only thing that moves between them --
#: and then the four that say where to put the camera once it is mounted.
RPICAM_BUNDLE = "raspberry-pi-camera-sheets.pdf"

#: And the FPGA development boards, with the light pipe adapter after them:
#: it is a part for one of those boards, so a reader of the set meets the
#: board first and the thing that clips onto it second.
FPGA_BUNDLE = "fpga-sheets.pdf"

# Reading order: what a bound copy pages through and what the README grid
# runs across.  It numbers nothing -- a sheet's drawing name is derived from
# the sheet itself, see tools.layout.drawing_name -- so adding a board here
# cannot renumber the sheets already drawn.
TT_ORDER = ["tt123-v2.2.5", "tt123-v2.2.6", "v1.2.1", "v1.2.2", "v1.2.3",
            "v2.0.1", "v2.1.0", "v2.1.2", "v3.2", "v3.3"]
RPI_ORDER = ["rpi3b", "rpi4b", "rpi5"]
#: Oldest first, as the Pi sheets are.  Both camera boards are the same
#: 25 x 23.862 mm outline on the same hole pattern, so the two sheets share
#: one view frame and one notes band and the board holds still between them:
#: what moves is the lens module, which is the whole point of the pair.
RPICAM_ORDER = ["cm2", "cm3"]
#: The camera POSITION sheets, which follow the two board sheets in the same
#: family: they are about the same two modules, and a reader who has just
#: found out where the optical axis sits on the board is the reader who wants
#: to know where to put the board.  The plate first, because it is the thing
#: this repository is mostly about, then the Arty and its extra sheet, then
#: the Acorn.  Each entry is the key of a subject in
#: ``raspberry_pi_camera.optics``, which is the thing the camera is pointed
#: at; ``position_stem`` says what the sheet drawn for it is called.
RPICAM_POSITION_ORDER = ["tt-mounting-plate", "arty-a7", "arty-ethernet",
                         "acorn-cle-215-plus"]
#: In the order they were asked for.  No shared frame: unlike the demo
#: boards, which register on their Pmod hosts, and the Pis, which share an
#: outline, these have nothing in common to hold still, so each sheet is
#: fitted to its own board.
FPGA_ORDER = ["arty-a7", "ulx3s", "pynq-z2", "butterstick", "icepi-zero",
              "cynthion", "zybo-z7", "ultra96-v2"]

#: The pitch is dimensioned on the view; what the view cannot say is where
#: the number comes from and that every revision shares it, which is what
#: lets one mounting plate serve them all.  The sheets are registered on the
#: hosts, so that the hosts hold still and the board moves between revisions
#: is visible by flipping through the set and needs no note.
TT_NOTES = (
    "Pmod host pitch, 22.86 mm (0.9 in), is the Digilent Pmod Interface "
    "Specification 1.2.0 figure and is the same on every revision; the "
    f"mounting plate, {PLATE_SHEET}, registers against it.",
)

RPI_NOTES = (
    "Pmod host JC overhangs the lower edge, over the HDMI and power "
    "connectors. Fit the two standoffs opposite the 40-pin header, as "
    "Digilent's manual warns, so JC's pins cannot touch the HDMI shell. "
    "HDMI connectors are not drawn.",
    # The adapter's own sheet carries the derivation; here only the figure a
    # plate designer needs.  Stated with the adapter's constant rather than
    # a copied "0.75", so the two sheets cannot drift apart.
    "Pmod HAT Adapter host positions are DERIVED, good to about "
    f"+/-{PMOD_HAT_TOL} mm; drawing {PMOD_HAT_SHEET} has the derivation.",
)

#: Both camera sheets say which face is being looked at.  The generic note is
#: "Viewed from the component side", which on a board with its lens on one
#: face and its connector on the other leaves the reader to work out which
#: side that is, and it is the side the light goes in.
RPICAM_NOTES = (
    "The component side is the lens side; the connector is on the far face.",
)

#: The M.2 HAT assembly sheet's own title and subtitle.  Named here rather
#: than written into the render call because the README grid has to print the
#: same words, and a sheet whose caption and title block disagree is exactly
#: the drift tools/update_readme.py exists to stop.
ACC_M2_HAT_TITLE = "Acorn CLE-215+ in a PoE M.2 HAT+ on a Pi 5"
ACC_M2_HAT_SUBTITLE = ("Plan envelope of the assembly; the Raspberry Pi 5 is "
                       "the board drawn")

#: Where the card's far end lands, which is where its retention screw is:
#: the M.2 specification puts the half-moon cutout on the module's far edge.
_ACORN_END = POE_M2_DATUM_X + M2_LENGTHS["2280"]

#: What this sheet has to say that neither the Pi's own data nor the HAT's
#: says on its own: it is the assembly, not either part, that projects past
#: the Pi and that has to be given room.
#:
#: Every figure here is interpolated from accessories/parts.py rather than
#: typed again, for the reason RPI_NOTES gives above: a note and the data it
#: describes that are two copies of one number drift apart silently, and the
#: note is the copy nobody rebuilds.
ACC_M2_HAT_NOTES = (
    f"The card's far end and its retention screw land at X {_ACORN_END:.2f}, "
    f"just past the Pi's Ethernet-end edge, and the standoff's "
    f"{POE_M2_BOSS_DIA:.2f} mm boss reaches "
    f"{_ACORN_END + POE_M2_BOSS_DIA / 2:.2f}: allow "
    f"{POE_M2_STANDOFF_OVERHANG:.2f} mm past the {POE_M2_HAT_WIDTH:.0f} mm "
    "board, on the edge the RJ45 and USB already overhang.",
    f"The Acorn is {ACORN_WIDTH:.0f} mm wide, a millimetre over the M.2 "
    f"specification's {M2_CARD_WIDTH:.0f} +/-0.15; SQRL say to make sure of "
    "the clearance.",
    "PLAN ONLY, no Z anywhere: neither Waveshare nor SQRL publish a height "
    "for the HAT, its standoffs, the card, or the heatsink the CLE-215+ "
    "carries, which is therefore not drawn.",
    # Which figures are NOT derived is as much a provenance question as which
    # are, and the phantom schedule's four 2.75s are the only ones on the
    # sheet that come from neither Raspberry Pi Ltd's drawing nor Waveshare's.
    "Waveshare dimension nothing of the M.2 system but the standoff's "
    f"{POE_M2_STANDOFF_OVERHANG:.2f} mm overhang, so the socket, the "
    "standoffs and the card are DERIVED from their drawing by "
    f"accessories/measure_poe_m2_hat.py, to +/-{POE_M2_HAT_TOL} mm and the "
    f"socket to +/-{POE_M2_SOCKET_TOL:.0f} mm; the standoffs' DIA is the "
    f"{M2_STANDOFF_THREAD} tapped thread, not a clearance hole, and BOSS is "
    "what they occupy. MT1 to MT4 are not derived at all: their 2.75 mm is "
    "the Raspberry Pi HAT specification's DECLARED M2.5 clearance, which "
    "Waveshare do not dimension.",
)


def position_stem(key: str) -> str:
    """The file stem of the camera position sheet for subject *key*.

    The subject's own key behind ``over-``, so the sheet that draws the
    camera over the Arty A7 is written to ``over-arty-a7.svg``.  Its name
    comes from ``tools.layout.RPICAM_NAMES``, keyed by that stem:
    ``RPICAM-OVER-ARTY``, the family prefix, the word the title shares with
    the other three, and one word for the subject, as ``RPICAM-2`` does not
    say camera twice either.  The widest of the four, ``RPICAM-OVER-ACORN``,
    is 37.70 mm of lettering at the ISO 3098 floor in the 79.30 mm the
    DRAWING NO cell has.

    The Arty's two subjects are ``arty-a7`` and ``arty-ethernet``, which is
    what ``fpga/light_pipe/`` calls that end of the board; their names are
    OVER-ARTY and OVER-ETH, and neither is a prefix of the other -- a name
    that is a prefix of a sibling's cannot be told from it by any test that
    reads a sheet, which ``tools.layout.drawing_name`` makes a rule and
    ``tools/check_sheets.py`` enforces.

    Here rather than in ``tools/layout.py``, which holds the stems that notes
    on OTHER sheets cite: nothing cites these, and the camera board sheets
    take their stems from the generator too.
    """
    return f"over-{key}"


def tt_sheets() -> list[tuple[str, "BoardSpec"]]:
    """One sheet per distinct board geometry, not one per revision.

    Several revisions differ only electrically: v1.2.2 and v1.2.3 are the same
    board mechanically, as are v2.0.1 and v2.1.0.  Issuing a separate sheet for
    each meant two drawings a reader had to compare to discover they were
    identical, which the sheets themselves then said in a note.  They are
    merged instead, and the sheet names every revision and shuttle it covers.
    Each returns with the file stem it is written to, which is also what its
    drawing name is worked out from: ``layout.tt_stem`` assembles the stem
    from the first revision and the last, ``layout.tt_name`` takes the name
    from the front of it, and the title and notes here carry the rest.

    The data keeps every revision: it is a database of what was built, and the
    plate is designed against individual revisions.  Only the drawing set is
    merged.
    """
    # A board in the data and not in TT_ORDER is a board nobody draws, and
    # nothing said so: v2.2.5 was extracted, written to boards.py and silently
    # left off the sheet set, because this list is maintained by hand and the
    # build had no opinion about what it left out.
    missing = [k for k in TT_BOARDS if k not in TT_ORDER]
    if missing:
        raise SystemExit(
            f"tinytapeout/boards.py holds {', '.join(sorted(missing))}, which "
            "TT_ORDER does not list, so no sheet would be drawn for it. Add "
            "it to TT_ORDER, in the order the sheets should be read.")

    groups: list[list[str]] = []
    seen: dict = {}
    for key in TT_ORDER:
        sig = _geometry(TT_BOARDS[key])
        if sig in seen:
            groups[seen[sig]].append(key)
        else:
            seen[sig] = len(groups)
            groups.append([key])

    out = []
    for keys in groups:
        first = TT_BOARDS[keys[0]]
        if len(keys) == 1:
            out.append((tt_stem(keys), first))
            continue
        revs = [TT_BOARDS[k] for k in keys]
        # Every revision's own board file is cited, each at its own commit,
        # and the shuttle mapping is merged into one entry.
        sources = [s for r in revs for s in r.sources
                   if s.label == "KiCad board file"]
        shuttles = tuple(sh for r in revs for sh in r.used_by)
        # Kits merge the same way the shuttles do, and for the same reason: a
        # merged sheet carries both revisions, so it ships in both revisions'
        # kits.  Taking them from the first revision alone put "TT02 Dev Kit"
        # on a sheet that is also the TT03 board.
        kits = tuple(dict.fromkeys(k for r in revs for k in r.kits))
        # The shuttle mapping note names the shuttles this SHEET covers, not
        # the ones its first revision covers: merged, it carried "used by:
        # TT04" on a sheet that is also the TT05 board.
        for src in first.sources:
            if src.label == "KiCad board file":
                continue
            if src.label == "Shuttle mapping":
                src = replace(src, note="used by: " + ", ".join(shuttles))
            sources.append(src)
        revnos = [r.subtitle.split(" rev ")[-1] for r in revs]
        covered = (revnos[0] if len(revnos) == 1
                   else ", ".join(revnos[:-1]) + " and " + revnos[-1])
        # The board file's own name, taken from the first revision rather than
        # written in.  It was hardcoded "tinytapeout-demo", which was true of
        # every merged sheet until the mpw board -- whose file is mpw-mb1 --
        # gained a second revision and would have been captioned with the name
        # of a file it is not in.
        board_file = first.subtitle.split(" rev ")[0]
        # Every ID the sheet covers, not just the first.  The spreadsheet's ID
        # is the board's name, and a merged sheet is genuinely two of them.
        ids = " / ".join(r.title for r in revs)
        # Notes from every revision the sheet covers, in order, deduplicated
        # -- not just the first's.  The note explaining that TT01 never had a
        # PCB belongs to v2.2.6, and when v2.2.5 joined the sheet in front of
        # it that note silently left the drawing.
        notes = ()
        for r in revs:
            for n in r.notes:
                if n.startswith("Geometrically identical") or n in notes:
                    continue
                notes += (n,)
        # The per-revision "Geometrically identical to ..." notes are dropped
        # above and replaced by this one, which says the same thing once for
        # the whole sheet rather than once per revision on it.  The subtitle
        # already lists the revisions; the note adds only what the title
        # cannot, that they are one board mechanically.
        notes += (
            "The revisions covered are mechanically identical; only the "
            "electrical design differs.",)
        spec = replace(
            first,
            key="+".join(keys),
            title=ids,
            subtitle=f"{board_file} rev {covered}",
            used_by=shuttles,
            kits=kits,
            sources=tuple(sources),
            notes=notes,
        )
        out.append((tt_stem(keys), spec))
    return out


#: The Pmod host pitch, from the Digilent specification.  Imported rather than
#: restated: the plate is built on the same number.
def _pmod_frame(spec) -> tuple[float, float]:
    """Offset from this board's own coordinates to the Pmod-referenced frame.

    The frame the mounting plate uses: the first Pmod host pin field sits at
    the origin, or at the second grid position for a board with only two hosts,
    whose pair lines up with the later boards' second and third.
    """
    from tinytapeout.mounting_plate.plate import PMOD_PITCH
    pmods = sorted(spec.pmods, key=lambda p: p.cx)
    slot = 1 if len(pmods) == 2 else 0
    return slot * PMOD_PITCH - pmods[0].cx, -pmods[0].cy


def _drawn_bbox(spec, overlay=None) -> tuple[float, float, float, float]:
    """Everything the view has to cover: the board and whatever hangs off it.

    The same rule render_board applies, so that the frame built from these
    cannot be smaller than the one it checks against.  An *overlay* is an
    adjacent part drawn in phantom on the same view, and its outline and pin
    fields count too.
    """
    xs = [0.0, spec.outline.width]
    ys = [0.0, spec.outline.height]
    for f in spec.features:
        xs += [f.x0, f.x1]
        ys += [f.y0, f.y1]
    for p in spec.pmods:
        if p.body_x1 > p.body_x0:
            xs += [p.body_x0, p.body_x1]
            ys += [p.body_y0, p.body_y1]
    if overlay is not None:
        xs += [0.0, overlay.outline.width]
        ys += [0.0, overlay.outline.height]
        for p in overlay.pmods:
            xs += [p.cx - p.pin_span / 2 - 2, p.cx + p.pin_span / 2 + 2]
            ys += [p.cy - p.pin_span / 2 - 2, p.cy + p.pin_span / 2 + 2]
    return min(xs), min(ys), max(xs), max(ys)


def shared_view_frame(specs, overlay) -> tuple[float, float, float, float]:
    """One view frame for a family whose boards share a coordinate system.

    What ``tt_view_frames`` does for the Pmod hosts, this does for the board
    itself.  Where every member of a family is the same outline on the same
    hole pattern the sheets already share a frame and need no offsets, so
    the union of what they all draw -- overlay included -- is enough to hold
    the board on the same point of every page.

    Two families use it.  Every Model B sized Pi is 85 x 56 with the same
    hole pattern and the 40-pin header in the same place; each sheet used to
    be fitted to its own connectors, and the Pi 5's USB ports reach further
    than the Pi 3B's, so the board itself moved between pages.  Both camera
    boards are 25 x 23.862 on one hole pattern, and holding that still is the
    point of drawing them as a pair: what moves between the two sheets is
    the lens module.

    It was ``rpi_view_frame`` while the Pi sheets were the only caller;
    nothing in it was ever particular to a Raspberry Pi.
    """
    boxes = [_drawn_bbox(spec, overlay) for spec in specs]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def tt_view_frames(sheets) -> dict[str, tuple[float, float, float, float]]:
    """One view frame per sheet, so the Pmod hosts land in the same place.

    Every demo board revision puts its Pmod hosts on the same 22.86 mm pitch
    -- that invariant is what makes one mounting plate serve all of them -- but
    each sheet used to be fitted to its own board, so the hosts moved from page
    to page and flipping through the set showed six boards jumping around.
    Registered on the hosts instead, the connectors hold still and what moves
    is what actually changed between revisions: the outline, the mounting holes
    and the USB-C.

    Both axes.  The frame is the union of every board in that shared frame --
    121.75 x 95.20 mm -- expressed back in each board's own coordinates, so all
    six views cover the same region and the hosts land on the same point of
    every page.

    This only fits because the notes were cut back first.  The frame makes
    every sheet reserve the tallest board's height (v3.3 at 85 mm) on top of
    the 11.78 mm Pmod body overhang, and an A3 sheet holds that at 1:1 only
    with a notes band of 120 mm or less.  The 4+ sheet wanted 128 mm while it
    was still carrying four notes that explained the drawing rather than the
    board.  Without those it fits, at 1:1, with its remaining notes intact.
    """
    offsets = {key: _pmod_frame(spec) for key, spec in sheets}
    x0 = min(_drawn_bbox(s)[0] + offsets[k][0] for k, s in sheets)
    y0 = min(_drawn_bbox(s)[1] + offsets[k][1] for k, s in sheets)
    x1 = max(_drawn_bbox(s)[2] + offsets[k][0] for k, s in sheets)
    y1 = max(_drawn_bbox(s)[3] + offsets[k][1] for k, s in sheets)
    return {k: (x0 - dx, y0 - dy, x1 - dx, y1 - dy)
            for k, (dx, dy) in offsets.items()}


def _geometry(b) -> tuple:
    """What makes two revisions the same board, mechanically."""
    o = b.outline
    return (o.width, o.height, o.corner_radius, o.thickness, o.edges,
            tuple((h.x, h.y, h.dia, h.label) for h in b.holes),
            tuple((p.cx, p.cy, p.pin1_x, p.pin1_y, p.label) for p in b.pmods),
            tuple(sorted((f.key, f.x0, f.y0, f.x1, f.y1) for f in b.features)))


@dataclass(frozen=True)
class Bundle:
    """One bound copy: where it is written, its title, and its pages in order.

    A bound copy is the one output with no drawing of its own, so nothing
    about it can be checked by re-rendering an SVG: it is a pypdf assembly of
    files that were already finished.  What it is *supposed* to hold --
    which sheets, in what order, under what bookmarks -- lived only inside
    ``main()``, as lists built while the sheets were being rendered, so the
    only way to find out was to render the whole set again.  Stated here it
    can be read by a check that binds nothing, and the generator and
    ``tools/check_pdfs.py`` cannot disagree about the page list because there
    is only one.
    """

    path: Path
    title: str
    #: (sheet PDF, bookmark label), in binding order: exactly the argument
    #: ``tools.render_svg.combine_pdfs`` takes.
    pages: tuple[tuple[Path, str], ...]


def _label(name: str, spec) -> str:
    """A sheet's outline entry: its name, what it draws, and the subtitle.

    The drawing name leads because at thumbnail size it is the only thing
    that tells two pages of one family apart.
    """
    return f"{name}  {spec.title}  -  {spec.subtitle}"


def tt_board_sheets() -> list[tuple[str, str, Path, "BoardSpec"]]:
    """The demo board sheets: drawing name, file stem, path, spec.

    The stem is both the file ``tt_sheets`` says the sheet is written to and
    the key ``tt_view_frames`` returns its frame under, and it is what the
    drawing name is derived from.
    """
    tt_dir = FAMILY_DIRS["tinytapeout"]
    return [(drawing_name("tinytapeout", stem), stem,
             tt_dir / f"{stem}.svg", spec) for stem, spec in tt_sheets()]


def rpi_sheets() -> list[tuple[str, Path, "BoardSpec"]]:
    """The Raspberry Pi sheets: drawing name, path, spec."""
    rpi_dir = FAMILY_DIRS["raspberry-pi"]
    return [(drawing_name("raspberry-pi", slug(key)),
             rpi_dir / f"{slug(key)}.svg", RPI_BOARDS[key])
            for key in RPI_ORDER]


def rpi_compare() -> tuple[str, Path, str]:
    """The comparison sheet: drawing name, path, outline entry.

    Beside ``rpi_sheets`` rather than in it, and carrying a written label the
    way ``plate_sheets`` does.  The three model sheets are one board each,
    rendered by ``render_board`` from that board's spec; this one draws all
    three and is rendered by a module of its own, so there is no single spec
    for ``_label`` to take a title and a subtitle from.

    Its name is derived like every other sheet's, from the file stem it is
    written to.  It is the one Raspberry Pi sheet with no board key behind it
    -- the others are named from a key in ``RPI_ORDER`` by way of ``slug`` --
    and ``drawing_name`` does not need one, which is the point of naming a
    sheet after itself.
    """
    stem = rpi_compare_sheet.STEM
    name = drawing_name("raspberry-pi", stem)
    return (name, FAMILY_DIRS["raspberry-pi"] / f"{stem}.svg",
            f"{name}  {rpi_compare_sheet.TITLE}  -  "
            f"{rpi_compare_sheet.SUBTITLE}")


def rpicam_sheets() -> list[tuple[str, Path, "BoardSpec"]]:
    """The Raspberry Pi camera sheets: drawing name, path, spec.

    A family of its own rather than two more Pi sheets: a 25 x 23.862 mm
    camera shares nothing with an 85 x 56 mm Pi but the company that made it,
    and the Pi sheets are drawn with the Pmod HAT Adapter overlaid on a frame
    a 25 mm board would be lost in.
    """
    cam_dir = FAMILY_DIRS["raspberry-pi-camera"]
    return [(drawing_name("raspberry-pi-camera", slug(key)),
             cam_dir / f"{slug(key)}.svg", RPICAM_BOARDS[key])
            for key in RPICAM_ORDER]


def rpicam_position_sheets() -> list[tuple[str, Path, "Subject"]]:
    """The camera position sheets: drawing name, path, subject.

    Beside ``rpicam_sheets`` and read after it, the way ``rpi_compare`` sits
    beside ``rpi_sheets``: those are one board each, rendered by
    ``render_board`` from a ``BoardSpec``; these draw no part at all and are
    rendered by a module of their own from a subject in
    ``raspberry_pi_camera.optics``.  They bind into the same family's copy
    because they are about the same two modules -- a reader who has just
    found out where the optical axis sits on the board is the reader who
    wants to know where to put the board.
    """
    cam_dir = FAMILY_DIRS["raspberry-pi-camera"]
    subjects = rpicam_subjects()
    # A subject in the data and not in the reading order is a sheet nobody
    # draws, the way a demo board missing from TT_ORDER was.
    missing = [k for k in subjects if k not in RPICAM_POSITION_ORDER]
    if missing:
        raise SystemExit(
            f"raspberry_pi_camera/optics.py defines {', '.join(missing)}, "
            "which RPICAM_POSITION_ORDER does not list, so no sheet would be "
            "drawn for it. Add it to RPICAM_POSITION_ORDER, in the order the "
            "sheets should be read.")
    return [(drawing_name("raspberry-pi-camera", position_stem(key)),
             cam_dir / f"{position_stem(key)}.svg", subjects[key])
            for key in RPICAM_POSITION_ORDER]


def fpga_sheets() -> list[tuple[str, Path, "BoardSpec"]]:
    """The FPGA development board sheets: drawing name, path, spec."""
    fpga_dir = FAMILY_DIRS["fpga"]
    return [(drawing_name("fpga", slug(key)),
             fpga_dir / f"{slug(key)}.svg", FPGA_BOARDS[key])
            for key in FPGA_ORDER]


def light_pipe_sheet() -> tuple[str, Path, str]:
    """The light pipe adapter's sheet: drawing name, path, outline entry.

    A made part rather than a board, so it has a directory and a family row
    of its own -- its design script, its checks and its STEP solid do not
    belong among the extracted board data -- but its prefix begins with the
    boards', ``FPGA-LP``, and it binds with them, because that is where it
    is read.  See ``tools.layout.FAMILY_PREFIXES``.

    Beside ``fpga_sheets`` rather than in it, the way ``rpi_compare`` sits
    beside ``rpi_sheets``: those are a board each, rendered by
    ``render_board`` from a ``BoardSpec``; this one is a part, rendered by a
    module of its own.  Its title and subtitle do come from its data module,
    so ``_label`` reads them the way it does for a board.
    """
    name = drawing_name("light-pipe", LIGHT_PIPE.key)
    return (name, FAMILY_DIRS["light-pipe"] / f"{LIGHT_PIPE.key}.svg",
            _label(name, LIGHT_PIPE))


def plate_sheets() -> list[tuple[str, Path, str]]:
    """The two A3 mounting plate sheets: drawing name, path, outline label.

    Their labels are written here rather than taken from a spec because
    neither sheet draws a board: the plate's own drawing takes its title and
    subtitle from the plate data, and the fitting guide is drawn from the
    whole demo board set and has no subject of its own to name it.  The names
    themselves are derived like every other, in tools.layout.

    Not the two drill templates.  They are sheets of the same plate and live
    in the same directory, but they are A4 portrait and are not bound; see
    TT_BUNDLE for why.
    """
    plate_dir = FAMILY_DIRS["mounting-plate"]
    return [
        (PLATE_SHEET, plate_dir / f"{PLATE_STEM}.svg",
         f"{PLATE_SHEET}  {PLATE.title}  -  {PLATE.subtitle}"),
        (FITTING_GUIDE_SHEET, plate_dir / f"{FITTING_GUIDE_STEM}.svg",
         f"{FITTING_GUIDE_SHEET}  TT Mounting Plate Fitting Guide  -  "
         "Which holes each demo board revision uses"),
    ]


def bundles() -> list[Bundle]:
    """Every bound copy the generator writes, without rendering anything.

    Data only: reading the board modules and naming files.  Nothing here
    calls Inkscape, pypdf or the drafting library, so a check can import this
    and ask what belongs in a bound copy at the cost of an import.
    """
    tt_pages = [(path.with_suffix(".pdf"), label)
                for _, path, label in plate_sheets()]
    tt_pages += [(path.with_suffix(".pdf"), _label(name, spec))
                 for name, _, path, spec in tt_board_sheets()]
    # The three models in the order they were made, then the sheet that draws
    # all three at once, which is the order they are read in.
    rpi_pages = [(path.with_suffix(".pdf"), _label(name, spec))
                 for name, path, spec in rpi_sheets()]
    _, compare_path, compare_label = rpi_compare()
    rpi_pages.append((compare_path.with_suffix(".pdf"), compare_label))
    # The two board sheets, then the four that say where to put the camera
    # once it is on something: the order RPICAM_POSITION_ORDER explains.
    cam_pages = [(path.with_suffix(".pdf"), _label(name, spec))
                 for name, path, spec in rpicam_sheets()]
    cam_pages += [(path.with_suffix(".pdf"), _label(name, subject))
                  for name, path, subject in rpicam_position_sheets()]
    # The boards, then the light pipe: it is a part for one of them, so a
    # reader meets the board first and the thing that clips onto it second.
    fpga_pages = [(path.with_suffix(".pdf"), _label(name, spec))
                  for name, path, spec in fpga_sheets()]
    _, lp_path, lp_label = light_pipe_sheet()
    fpga_pages.append((lp_path.with_suffix(".pdf"), lp_label))
    return [
        Bundle(FAMILY_DIRS["tinytapeout"] / TT_BUNDLE,
               "Tiny Tapeout - mechanical drawings", tuple(tt_pages)),
        Bundle(FAMILY_DIRS["raspberry-pi"] / RPI_BUNDLE,
               "Raspberry Pi - mechanical drawings", tuple(rpi_pages)),
        Bundle(FAMILY_DIRS["raspberry-pi-camera"] / RPICAM_BUNDLE,
               "Raspberry Pi camera modules - mechanical drawings",
               tuple(cam_pages)),
        Bundle(FAMILY_DIRS["fpga"] / FPGA_BUNDLE,
               "FPGA development boards - mechanical drawings",
               tuple(fpga_pages)),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    args = ap.parse_args()

    made: list[Path] = []
    drawn: dict[Path, str] = {}

    def save(sheet, path: Path, what: str) -> Path:
        """Write one sheet, refusing to write two sheets to one file.

        Stems are unique by construction and ``check_drawing_names`` proves
        the names derived from them are, but that check walks the output
        directory: two sheets writing to one path leave one file, and it is
        the surviving one the check reads.  The collision would show up as a
        sheet quietly missing from a set nobody counts.

        It is reachable.  ``tt_stem`` is not injective -- revisions ``a-b``
        and ``a-c`` on one sheet give ``tt-demo-board-a-b-c``, and so does a
        single revision named ``a-b-c`` -- so the guard is here rather than
        in an argument that it cannot happen.

        *what* says which sheet, for the message.  The drawing name alone
        would not: it is derived from the stem, so two sheets that collide on
        a stem have the same name as well, and a message naming both would
        print one string twice.  What tells them apart is what they are of,
        so a board sheet passes its title too.
        """
        if path in drawn:
            raise SystemExit(
                f"{rel(path)} would be written twice, first for {drawn[path]} "
                f"and then for {what}. Two sheets have been given the same "
                "file stem; see tools/layout.py.")
        drawn[path] = what
        sheet.canvas.save(str(path))
        made.append(path)
        return path

    tt_dir = FAMILY_DIRS["tinytapeout"]
    tt_dir.mkdir(parents=True, exist_ok=True)
    sheets = tt_sheets()
    frames = tt_view_frames(sheets)
    # One band for the whole family, so every view gets the same rectangle and
    # therefore the same scale and the same centring.  The shared frame alone
    # is not enough: a sheet with a taller notes band has a shorter view area
    # and drops to the next standard scale, which moves the hosts it was meant
    # to hold still.
    band = max(planned_band_height(spec, extra_notes=TT_NOTES,
                                   view_bbox=frames[stem])
               for stem, spec in sheets)
    for name, stem, path, spec in tt_board_sheets():
        sheet = render_board(spec, drawing_no=name, version=VERSION,
                             extra_notes=TT_NOTES, family_numbers=TT_NUMBERS,
                             view_bbox=frames[stem], band_height=band)
        save(sheet, path, f"{name} ({spec.title})")

    rpi_dir = FAMILY_DIRS["raspberry-pi"]
    rpi_dir.mkdir(parents=True, exist_ok=True)
    rpi_frame = shared_view_frame(
        [RPI_BOARDS[k] for k in RPI_ORDER], PMOD_HAT)
    # One band for the family, as for the Tiny Tapeout set: a taller notes
    # band on one sheet would shrink its view and drop its scale.
    rpi_band = max(planned_band_height(RPI_BOARDS[k], extra_notes=RPI_NOTES,
                                       overlay=PMOD_HAT, view_bbox=rpi_frame)
                   for k in RPI_ORDER)
    for name, path, spec in rpi_sheets():
        sheet = render_board(spec, drawing_no=name, version=VERSION,
                             overlay=PMOD_HAT, extra_notes=RPI_NOTES,
                             family_numbers=RPI_NUMBERS, view_bbox=rpi_frame,
                             band_height=rpi_band)
        save(sheet, path, f"{name} ({spec.title})")

    # The comparison sheet: the three models on the one outline they share.
    # Given the same frame and the same notes band as the three sheets before
    # it, so the board lands on the same point of the page and the bound copy
    # can be flipped through; its own band is not folded into rpi_band above,
    # because a taller one there would move the three sheets it is meant to
    # line up with.
    compare_name, compare_path, _ = rpi_compare()
    sheet = rpi_compare_sheet.render_rpi_comparison(
        drawing_no=compare_name, version=VERSION,
        view_bbox=rpi_frame, band_height=rpi_band)
    save(sheet, compare_path, f"{compare_name} ({rpi_compare_sheet.TITLE})")

    cam_dir = FAMILY_DIRS["raspberry-pi-camera"]
    cam_dir.mkdir(parents=True, exist_ok=True)
    cam_specs = [RPICAM_BOARDS[k] for k in RPICAM_ORDER]
    # One frame and one band for the two, for the reason RPICAM_ORDER gives:
    # the two boards are the same outline on the same hole pattern, so the
    # board holds still between the pages and what moves is the lens module.
    cam_frame = shared_view_frame(cam_specs, None)
    cam_band = max(planned_band_height(spec, extra_notes=RPICAM_NOTES,
                                       view_bbox=cam_frame)
                   for spec in cam_specs)
    for name, path, spec in rpicam_sheets():
        sheet = render_board(spec, drawing_no=name, version=VERSION,
                             extra_notes=RPICAM_NOTES,
                             family_numbers=RPICAM_NUMBERS,
                             view_bbox=cam_frame, band_height=cam_band)
        save(sheet, path, f"{name} ({spec.title})")

    # The camera position sheets, drawn from the same family's optics module
    # rather than from a BoardSpec: they are not drawings of a part.  No
    # shared frame and no shared band with the two board sheets above --
    # nothing about a 25 mm camera module holds still against a 135 mm plate
    # -- so each is fitted to its own subject.
    for name, path, subject in rpicam_position_sheets():
        sheet = render_camera_position(subject, drawing_no=name,
                                       version=VERSION)
        save(sheet, path, f"{name} ({subject.title})")

    fpga_dir = FAMILY_DIRS["fpga"]
    fpga_dir.mkdir(parents=True, exist_ok=True)
    for name, path, spec in fpga_sheets():
        sheet = render_board(spec, drawing_no=name, version=VERSION,
                             family_numbers=FPGA_NUMBERS)
        save(sheet, path, f"{name} ({spec.title})")

    # The light pipe adapter: a made part for the Arty A7's Ethernet jack, so
    # it sits under fpga/ the way the mounting plate sits under tinytapeout/,
    # and binds into the FPGA set after the boards.  Its own directory, but
    # the boards' prefix, so the name says which board it clips onto.
    lp_dir = FAMILY_DIRS["light-pipe"]
    lp_dir.mkdir(parents=True, exist_ok=True)
    lp_name, lp_path, _ = light_pipe_sheet()
    sheet = render_light_pipe(drawing_no=lp_name, version=VERSION)
    save(sheet, lp_path, f"{lp_name} ({LIGHT_PIPE.title})")

    acc_dir = FAMILY_DIRS["accessories"]
    acc_dir.mkdir(parents=True, exist_ok=True)
    sheet = render_board(PMOD_HAT, drawing_no=PMOD_HAT_SHEET, version=VERSION)
    save(sheet, acc_dir / f"{PMOD_HAT_STEM}.svg", PMOD_HAT_SHEET)

    for spec in [WAVESHARE_POE, GENERIC_POE]:
        stem = acc_stem(spec.key)
        name = drawing_name("accessories", stem)
        sheet = render_enclosure(spec, drawing_no=name, version=VERSION)
        save(sheet, acc_dir / f"{stem}.svg", name)

    # The Raspmod: the other way of putting Pmods on a Raspberry Pi, drawn
    # beside the Digilent adapter it is compared with.
    raspmod_stem = acc_stem(RASPMOD.key)
    raspmod_name = drawing_name("accessories", raspmod_stem)
    sheet = render_board(RASPMOD, version=VERSION, drawing_no=raspmod_name)
    save(sheet, acc_dir / f"{raspmod_stem}.svg", raspmod_name)

    # An assembly rather than a part.  The board drawn is the Pi 5, whose
    # geometry is Raspberry Pi Ltd's and is already on that model's own
    # sheet; what is new is the phantom part on top of it, and that is an
    # accessory, curated by hand from a dimensioned vendor image the way
    # everything else in accessories/parts.py is.  So the sheet is named and
    # filed with the accessories even though the outline on it belongs to a
    # Raspberry Pi.
    m2_stem = acc_stem(POE_M2_HAT_WITH_ACORN.key)
    m2_name = drawing_name("accessories", m2_stem)
    sheet = render_board(
        replace(RPI_BOARDS["rpi5"],
                key=POE_M2_HAT_WITH_ACORN.key,
                title=ACC_M2_HAT_TITLE,
                subtitle=ACC_M2_HAT_SUBTITLE,
                # Not the Pi 5 sheet's notes: those are about where that
                # family's numbers come from and about the Pmod HAT Adapter,
                # and the Pi 5's own sheet is where a reader goes for
                # them.  This sheet says what the assembly does, which is all
                # it is for.
                notes=ACC_M2_HAT_NOTES,
                # The Pi's own drawing, then the HAT's and the card's, all
                # of them: a figure on this sheet that no line under SOURCES
                # accounts for is the one thing these drawings are for.
                sources=RPI_BOARDS["rpi5"].sources[:1]
                + POE_M2_HAT_WITH_ACORN.sources),
        drawing_no=m2_name, version=VERSION,
        overlay=POE_M2_HAT_WITH_ACORN, overlay_detail=True,
        family_numbers=RPI_NUMBERS)
    save(sheet, acc_dir / f"{m2_stem}.svg", m2_name)

    plate_dir = FAMILY_DIRS["mounting-plate"]
    plate_dir.mkdir(parents=True, exist_ok=True)
    # The two A3 plate sheets are drawn by a function each rather than by one
    # renderer over a list, so they are rendered one at a time; where each
    # lands and what it is called still comes from plate_sheets().
    plate = plate_sheets()
    if len(plate) != 2:
        raise SystemExit(
            f"plate_sheets() lists {len(plate)} A3 mounting plate sheets, and "
            "this renders exactly two: the plate's own drawing by "
            "render_plate and the fitting guide by render_fitting_guide. "
            "Each plate sheet is drawn by a function of its own, so a third "
            "needs its call added here, in the order the sheets are bound.")
    (mp_name, mp_path, _), (fg_name, fg_path, _) = plate
    sheet = render_plate(drawing_no=mp_name, version=VERSION)
    save(sheet, mp_path, mp_name)

    sheet = render_fitting_guide(drawing_no=fg_name, version=VERSION)
    save(sheet, fg_path, fg_name)

    # The drill templates are A4 portrait and 1:1 rather than A3 drawings,
    # but they are still sheets of the mounting plate and live with it: a
    # directory of their own split the plate's four sheets across two places.
    for kind, stem in DRILL_TEMPLATE_STEMS.items():
        name = drawing_name("mounting-plate", stem)
        sheet = render_drill_template(kind, drawing_no=name, version=VERSION)
        save(sheet, plate_dir / f"{stem}.svg", name)

    for path in made:
        print(f"  {rel(path)}")
    print(f"{len(made)} sheets written")

    if not args.no_raster:
        from tools.render_svg import to_pdf, to_preview
        for path in made:
            to_pdf(path)
            # No full-resolution PNG.  Each sheet used to get one at 150 dpi,
            # about 700 kB, 11.7 MB across the set, and nothing ever read them:
            # the READMEs link the preview and the PDF, and no check opens one.
            # They were a committed build product with no consumer, and they
            # were most of what made this repository large to clone.
            #
            # Previews sit beside the sheet they preview rather than in one
            # pool, so a family stays self-contained.
            to_preview(path, preview_for(path))
        print(f"{len(made)} sheets converted to PDF, with a preview beside "
              "each")

        # Bound after the individual PDFs exist, from those same files: a
        # second render would be a second chance for the set and the bound
        # copy to disagree about what a sheet says.
        for bundle in bundles():
            out = combine_pdfs(list(bundle.pages), bundle.path, bundle.title)
            print(f"  {rel(out)}: {len(bundle.pages)} sheets bound into "
                  "one PDF")


if __name__ == "__main__":
    main()
