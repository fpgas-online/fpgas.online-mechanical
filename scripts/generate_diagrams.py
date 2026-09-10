#!/usr/bin/env python3
"""Generate every mechanical drawing from the data in ``data/``.

Writes SVG, PDF and PNG for each sheet under ``diagrams/``.

Run: uv run --no-project --with pillow python scripts/generate_diagrams.py
     add --no-raster to skip the PDF and PNG conversions while iterating.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data.accessories import (ACCESSORIES, GENERIC_POE, PMOD_HAT,  # noqa: E402
                              WAVESHARE_POE)
from data.raspberry_pi_boards import BOARDS as RPI_BOARDS  # noqa: E402
from data.tinytapeout_boards import BOARDS as TT_BOARDS  # noqa: E402
from drafting.board_sheet import render_board  # noqa: E402
from drafting.enclosure_sheet import render_enclosure  # noqa: E402
from drafting.plate_sheet import render_fitting_guide, render_plate  # noqa: E402

DATE = date.today().isoformat()
OUT = ROOT / "diagrams"

# Sheet numbering: family prefix, then the order the sheets are meant to be
# read in.  Numbers are stable so a reference to a drawing keeps working.
TT_ORDER = ["tt123-v2.2.6", "v1.2.2", "v1.2.3", "v2.0.1", "v2.1.0", "v2.1.2",
            "v3.2", "v3.3"]
RPI_ORDER = ["rpi3b", "rpi4b", "rpi5"]

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

    tt_dir = OUT / "tinytapeout"
    tt_dir.mkdir(parents=True, exist_ok=True)
    for n, (stem, spec) in enumerate(tt_sheets(), 1):
        sheet = render_board(spec, drawing_no=f"TT-DB-{n:02d}", date=DATE,
                             extra_notes=TT_NOTES)
        path = tt_dir / f"tt-demo-board-{stem}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

    rpi_dir = OUT / "raspberry-pi"
    rpi_dir.mkdir(parents=True, exist_ok=True)
    for n, key in enumerate(RPI_ORDER, 1):
        spec = RPI_BOARDS[key]
        sheet = render_board(spec, drawing_no=f"RPI-{n:02d}", date=DATE,
                             overlay=PMOD_HAT, extra_notes=RPI_NOTES)
        path = rpi_dir / f"{slug(key)}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

    acc_dir = OUT / "accessories"
    acc_dir.mkdir(parents=True, exist_ok=True)
    sheet = render_board(PMOD_HAT, drawing_no="ACC-01", date=DATE)
    path = acc_dir / "digilent-pmod-hat-adapter.svg"
    sheet.canvas.save(str(path))
    made.append(path)

    for n, spec in enumerate([WAVESHARE_POE, GENERIC_POE], 2):
        sheet = render_enclosure(spec, drawing_no=f"ACC-{n:02d}", date=DATE)
        path = acc_dir / f"{spec.key}.svg"
        sheet.canvas.save(str(path))
        made.append(path)

    plate_dir = OUT / "mounting-plate"
    plate_dir.mkdir(parents=True, exist_ok=True)
    sheet = render_plate(drawing_no="TT-MP-01", date=DATE)
    path = plate_dir / "tt-generic-mounting-plate.svg"
    sheet.canvas.save(str(path))
    made.append(path)

    sheet = render_fitting_guide(drawing_no="TT-MP-02", date=DATE)
    path = plate_dir / "tt-generic-mounting-plate-fitting-guide.svg"
    sheet.canvas.save(str(path))
    made.append(path)

    for path in made:
        print(f"  {path.relative_to(ROOT)}")
    print(f"{len(made)} sheets written")

    if not args.no_raster:
        from render_svg import to_pdf, to_png, to_preview
        previews = OUT / "previews"
        for path in made:
            to_pdf(path)
            to_png(path)
            to_preview(path, previews / f"{path.stem}.png")
        print(f"{len(made)} sheets converted to PDF and PNG, "
              f"with previews in {previews.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
