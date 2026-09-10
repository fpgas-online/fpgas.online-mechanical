#!/usr/bin/env python3
"""Convert drawing SVGs to PDF and PNG, and optionally crop a detail view.

Inkscape's --export-area takes CSS pixel units rather than the document's
millimetres, which makes cropping through it error prone.  Rendering the whole
page and cropping with Pillow avoids that entirely.

Usage:
    render_svg.py <file.svg> [more.svg ...]            # PDF + PNG beside them
    render_svg.py --crop X0 Y0 X1 Y1 <file.svg>        # crop in sheet mm
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

PNG_DPI = 150
CROP_PX_PER_MM = 8.0


def to_pdf(svg: Path) -> Path:
    out = svg.with_suffix(".pdf")
    subprocess.run(["inkscape", "--export-type=pdf", "--export-text-to-path",
                    f"--export-filename={out}", str(svg)],
                   check=True, capture_output=True)
    return out


def to_png(svg: Path, dpi: float = PNG_DPI, out: Path | None = None) -> Path:
    out = out or svg.with_suffix(".png")
    subprocess.run(["inkscape", "--export-type=png", f"--export-dpi={dpi}",
                    f"--export-filename={out}", str(svg)],
                   check=True, capture_output=True)
    return out


def crop(svg: Path, box_mm: tuple[float, float, float, float],
         out: Path, px_per_mm: float = CROP_PX_PER_MM) -> Path:
    """Crop *box_mm* (x0, y0, x1, y1, sheet mm, Y up) out of a rendered page."""
    dpi = px_per_mm * 25.4
    full = to_png(svg, dpi=dpi, out=out.with_name(out.stem + "-full.png"))
    img = Image.open(full)
    sheet_h_mm = img.height / px_per_mm
    x0, y0, x1, y1 = box_mm
    img.crop((int(x0 * px_per_mm), int((sheet_h_mm - y1) * px_per_mm),
              int(x1 * px_per_mm), int((sheet_h_mm - y0) * px_per_mm))).save(out)
    full.unlink()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("svgs", nargs="+", type=Path)
    ap.add_argument("--crop", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--dpi", type=float, default=PNG_DPI)
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()

    for svg in args.svgs:
        if args.crop:
            out = args.out or svg.with_name(svg.stem + "-detail.png")
            print(crop(svg, tuple(args.crop), out))
            continue
        png = to_png(svg, dpi=args.dpi)
        line = f"{png}"
        if not args.no_pdf:
            line += f"  {to_pdf(svg)}"
        print(line)


if __name__ == "__main__":
    main()
