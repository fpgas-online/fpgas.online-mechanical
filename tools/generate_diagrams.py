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
from tools.drafting.board_sheet import render_board  # noqa: E402
from tools.drafting.enclosure_sheet import render_enclosure  # noqa: E402
from tools.drafting.plate_sheet import render_fitting_guide, render_plate  # noqa: E402
from tools.drafting.template_sheet import render_drill_template  # noqa: E402
from tools.layout import FAMILY_DIRS, preview_for, rel  # noqa: E402
from tools import reproducible  # noqa: E402

#: Stamped into every sheet's title block where a render date used to go.
#: See tools/reproducible.py: a date changed every sheet whenever anyone
#: rebuilt on a new day, and never said which data a drawing came from.
VERSION = reproducible.source_version()

# Sheet numbering: family prefix, then the order the sheets are meant to be
# read in.  Numbers are stable so a reference to a drawing keeps working.
TT_ORDER = ["tt123-v2.2.6", "v1.2.2", "v1.2.3", "v2.0.1", "v2.1.0", "v2.1.2",
            "v3.2", "v3.3"]
RPI_ORDER = ["rpi3b", "rpi4b", "rpi5"]

#: The drill templates, in sheet order, and the file stem each is written to.
DRILL_TEMPLATES = {
    "plate": "tt-generic-mounting-plate-drill-template",
    "chassis": "tt-generic-mounting-plate-chassis-drill-template",
}

TT_NOTES = (
    "The Pmod host headers along the lower edge are what a mounting plate "
    "registers against. Their 22.86 mm pitch is the same on every revision; "
    "their distance from the lower edge and their position along it are not.",
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
        # The shuttle mapping note names the shuttles this SHEET covers, not
        # the ones its first revision covers: merged, it carried "used by:
        # TT04" on a sheet that is also the TT05 board.
        for src in first.sources:
            if src.label == "KiCad board file":
                continue
            if src.label == "Shuttle mapping":
                src = replace(src, note="used by: " + ", ".join(shuttles))
            sources.append(src)
        covered = " and ".join(r.subtitle.split(" rev ")[-1] for r in revs)
        notes = tuple(n for n in first.notes
                      if not n.startswith("Geometrically identical"))
        notes += (
            f"This sheet covers revisions {covered}. They are the same board "
            "mechanically: the generator compares outline, holes, Pmod hosts "
            "and every feature before merging them. Only the electrical "
            "design and the shuttle differ.",)
        spec = replace(
            first,
            key="+".join(keys),
            subtitle=f"tinytapeout-demo rev {covered}",
            used_by=shuttles,
            sources=tuple(sources),
            notes=notes,
        )
        out.append(("-".join(slug(k) for k in keys), spec))
    return out


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

    tt_dir = FAMILY_DIRS["tinytapeout"]
    tt_dir.mkdir(parents=True, exist_ok=True)
    for n, (stem, spec) in enumerate(tt_sheets(), 1):
        sheet = render_board(spec, drawing_no=f"TT-DB-{n:02d}", version=VERSION,
                             extra_notes=TT_NOTES, family_numbers=TT_NUMBERS)
        path = tt_dir / f"tt-demo-board-{stem}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

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

    sheet = render_fitting_guide(drawing_no="TT-MP-02", version=VERSION)
    path = plate_dir / "tt-generic-mounting-plate-fitting-guide.svg"
    sheet.canvas.save(str(path))
    made.append(path)

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
        from tools.render_svg import to_pdf, to_png, to_preview
        for path in made:
            to_pdf(path)
            to_png(path)
            # Previews sit beside the sheet they preview rather than in one
            # pool, so a family stays self-contained.
            to_preview(path, preview_for(path))
        print(f"{len(made)} sheets converted to PDF and PNG, "
              "with a preview beside each")


if __name__ == "__main__":
    main()
