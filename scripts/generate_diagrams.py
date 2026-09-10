#!/usr/bin/env python3
"""Generate every mechanical drawing from the data in ``data/``.

Writes SVG, PDF and PNG for each sheet under ``diagrams/``.

Run: uv run --no-project --with pillow python scripts/generate_diagrams.py
     add --no-raster to skip the PDF and PNG conversions while iterating.
"""

from __future__ import annotations

import argparse
import sys
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
RPI_ORDER = ["rpi3aplus", "rpi3b", "rpi3bplus", "rpi4b", "rpi5"]

TT_NOTES = (
    "The Pmod host headers along the lower edge are what a mounting plate has "
    "to register against. Their 22.86 mm pitch is identical on every Tiny "
    "Tapeout demo board revision, but their distance from the lower board edge "
    "and their absolute position along it are not.",
)

RPI_NOTES = (
    "Pmod host JC on the Pmod HAT Adapter overhangs the lower board edge in "
    "the same region as this board's HDMI and power connectors. Digilent's "
    "own reference manual warns to fit the two standoffs opposite the 40-pin "
    "connector so that JC's pins cannot touch the HDMI shell.",
)


def slug(key: str) -> str:
    return key.replace(".", "p").replace("_", "-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    args = ap.parse_args()

    made: list[Path] = []

    tt_dir = OUT / "tinytapeout"
    tt_dir.mkdir(parents=True, exist_ok=True)
    for n, key in enumerate(TT_ORDER, 1):
        spec = TT_BOARDS[key]
        sheet = render_board(spec, drawing_no=f"TT-DB-{n:02d}", date=DATE,
                             extra_notes=TT_NOTES)
        path = tt_dir / f"tt-demo-board-{slug(key)}.svg"
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
        from render_svg import to_pdf, to_png
        for path in made:
            to_pdf(path)
            to_png(path)
        print(f"{len(made)} sheets converted to PDF and PNG")


if __name__ == "__main__":
    main()
