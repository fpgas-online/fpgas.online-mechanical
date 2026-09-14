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
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import (ACCESSORIES, GENERIC_POE,  # noqa: E402
                               PMOD_HAT, WAVESHARE_POE)
from raspberry_pi.boards import BOARDS as RPI_BOARDS  # noqa: E402
from raspberry_pi.boards import FEATURE_NUMBERS as RPI_NUMBERS  # noqa: E402
from tinytapeout.boards import BOARDS as TT_BOARDS  # noqa: E402
from tinytapeout.boards import FEATURE_NUMBERS as TT_NUMBERS  # noqa: E402
from tools.drafting.board_sheet import (planned_band_height,  # noqa: E402
                                        render_board)
from tools.drafting.enclosure_sheet import render_enclosure  # noqa: E402
from tools.drafting.plate_sheet import render_fitting_guide, render_plate  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE  # noqa: E402
from tools.drafting.template_sheet import render_drill_template  # noqa: E402
from tools.layout import FAMILY_DIRS, preview_for, rel  # noqa: E402
from tools.render_svg import combine_pdfs  # noqa: E402
from tools import reproducible  # noqa: E402

#: Stamped into every sheet's title block where a render date used to go.
#: See tools/reproducible.py: a date changed every sheet whenever anyone
#: rebuilt on a new day, and never said which data a drawing came from.
VERSION = reproducible.source_version()

#: Every demo board sheet bound into one document, beside the sheets it is
#: made of.  Not an SVG and not rendered from one, so it is the only file in
#: an output directory with no drawing of its own.
#: Every A3 Tiny Tapeout sheet bound into one document: the six demo boards
#: and the two mounting plate drawings.  Not the drill templates -- those are
#: A4 portrait, and a document that mixes page sizes is one where "print all"
#: silently scales the pages that have to be 1:1.  They stay separate files,
#: which is also how anyone uses them: you print the template, not the set.
TT_BUNDLE = "tinytapeout-sheets.pdf"

# Sheet numbering: family prefix, then the order the sheets are meant to be
# read in.  Numbers are stable so a reference to a drawing keeps working.
TT_ORDER = ["tt123-v2.2.5", "tt123-v2.2.6", "v1.2.1", "v1.2.2", "v1.2.3",
            "v2.0.1", "v2.1.0", "v2.1.2", "v3.2", "v3.3"]
RPI_ORDER = ["rpi3b", "rpi4b", "rpi5"]

#: The drill templates, in sheet order, and the file stem each is written to.
DRILL_TEMPLATES = {
    "plate": "tt-generic-mounting-plate-drill-template",
    "chassis": "tt-generic-mounting-plate-chassis-drill-template",
}

#: One note, carrying the pitch and its citation.  There were two, this one and
#: a per-board "Pmod host headers are on a 22.86 mm (0.9 in) pitch, per the
#: Digilent Pmod Interface Specification 1.2.0", and both appeared on every
#: Tiny Tapeout sheet saying the same number.  The duplicate was what pushed
#: the merged 4+ sheet past its notes budget, but it had been a wasted line on
#: all of them.
TT_NOTES = (
    "The Pmod host headers along the lower edge are what a mounting plate "
    "registers against. Their 22.86 mm (0.9 in) pitch, per the Digilent Pmod "
    "Interface Specification 1.2.0, is the same on every revision; their "
    "distance from the lower edge and their position along it are not.",
)

RPI_NOTES = (
    "Pmod host JC on the Pmod HAT Adapter overhangs the lower board edge, "
    "where these boards carry their HDMI and power connectors. Digilent's "
    "manual warns to fit the two standoffs opposite the 40-pin connector so "
    "JC's pins cannot touch the HDMI shell. The HDMI connectors are not "
    "drawn here.",
)


def slug(key: str) -> str:
    return key.replace(".", "p").replace("_", "-")


def tt_sheets() -> list[tuple[str, "BoardSpec"]]:
    """One sheet per distinct board geometry, not one per revision.

    Several revisions differ only electrically: v1.2.2 and v1.2.3 are the same
    board mechanically, as are v2.0.1 and v2.1.0.  Issuing a separate sheet for
    each meant two drawings a reader had to compare to discover they were
    identical, which the sheets themselves then said in a note.  They are
    merged instead, and the sheet names every revision and shuttle it covers.

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
            out.append((slug(keys[0]), first))
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
        # the whole sheet rather than once per revision on it.
        notes += (
            f"Covers revisions {covered}, the same board mechanically, "
            "compared feature by feature before merging; only the electrical "
            "design and the shuttle differ.",)
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
        out.append(("-".join(slug(k) for k in keys), spec))
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


def _drawn_bbox(spec) -> tuple[float, float, float, float]:
    """Everything the view has to cover: the board and whatever hangs off it.

    The same rule render_board applies, so that the frame built from these
    cannot be smaller than the one it checks against.
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
    return min(xs), min(ys), max(xs), max(ys)


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    args = ap.parse_args()

    made: list[Path] = []
    #: The A3 Tiny Tapeout sheets, in drawing-number order, for the bound copy.
    tt_set: list[tuple[Path, str]] = []

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
    for n, (stem, spec) in enumerate(sheets, 1):
        sheet = render_board(spec, drawing_no=f"TT-DB-{n:02d}", version=VERSION,
                             extra_notes=TT_NOTES, family_numbers=TT_NUMBERS,
                             view_bbox=frames[stem], band_height=band)
        path = tt_dir / f"tt-demo-board-{stem}.svg"
        sheet.canvas.save(str(path))
        made.append(path)
        tt_set.append((path.with_suffix(".pdf"),
                       f"TT-DB-{n:02d}  {spec.title}  -  {spec.subtitle}"))

    rpi_dir = FAMILY_DIRS["raspberry-pi"]
    rpi_dir.mkdir(parents=True, exist_ok=True)
    for n, key in enumerate(RPI_ORDER, 1):
        spec = RPI_BOARDS[key]
        sheet = render_board(spec, drawing_no=f"RPI-{n:02d}", version=VERSION,
                             overlay=PMOD_HAT, extra_notes=RPI_NOTES,
                             family_numbers=RPI_NUMBERS)
        path = rpi_dir / f"{slug(key)}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

    acc_dir = FAMILY_DIRS["accessories"]
    acc_dir.mkdir(parents=True, exist_ok=True)
    sheet = render_board(PMOD_HAT, drawing_no="ACC-01", version=VERSION)
    path = acc_dir / "digilent-pmod-hat-adapter.svg"
    sheet.canvas.save(str(path))
    made.append(path)

    for n, spec in enumerate([WAVESHARE_POE, GENERIC_POE], 2):
        sheet = render_enclosure(spec, drawing_no=f"ACC-{n:02d}", version=VERSION)
        path = acc_dir / f"{spec.key}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

    plate_dir = FAMILY_DIRS["mounting-plate"]
    plate_dir.mkdir(parents=True, exist_ok=True)
    sheet = render_plate(drawing_no="TT-MP-01", version=VERSION)
    path = plate_dir / "tt-generic-mounting-plate.svg"
    sheet.canvas.save(str(path))
    made.append(path)
    tt_set.append((path.with_suffix(".pdf"),
                   f"TT-MP-01  {PLATE.title}  -  {PLATE.subtitle}"))

    sheet = render_fitting_guide(drawing_no="TT-MP-02", version=VERSION)
    path = plate_dir / "tt-generic-mounting-plate-fitting-guide.svg"
    sheet.canvas.save(str(path))
    made.append(path)
    tt_set.append((path.with_suffix(".pdf"),
                   "TT-MP-02  TT Mounting Plate Fitting Guide  -  "
                   "Which holes each demo board revision uses"))

    # The drill templates are A4 portrait and 1:1 rather than A3 drawings,
    # but they are still sheets of the mounting plate and live with it: a
    # directory of their own split the plate's four sheets across two places.
    for n, (kind, stem) in enumerate(DRILL_TEMPLATES.items(), 3):
        sheet = render_drill_template(kind, drawing_no=f"TT-MP-{n:02d}",
                                      version=VERSION)
        path = plate_dir / f"{stem}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

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
        bundle = combine_pdfs(tt_set, tt_dir / TT_BUNDLE,
                              "Tiny Tapeout - mechanical drawings")
        print(f"  {rel(bundle)}: {len(tt_set)} sheets bound into one PDF")


if __name__ == "__main__":
    main()
