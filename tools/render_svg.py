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

# This module is both imported and run directly; when it is run, the
# repository root is not on the path and ``tools`` is not importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import reproducible  # noqa: E402

PNG_DPI = 150
CROP_PX_PER_MM = 8.0

#: Width of a README preview, in pixels.  Twice the width GitHub shows a cell
#: of a three-column table at, so the thumbnails stay sharp on a high-density
#: display without carrying a full-resolution sheet into every page load: the
#: real PNGs are close to a megabyte each.
PREVIEW_WIDTH = 640


def to_pdf(svg: Path) -> Path:
    """Render *svg* to a PDF beside it, with text converted to paths.

    Paths rather than embedded fonts so that a print shop with no DejaVu
    installed still gets the right lettering at the right width, which on a
    1:1 drawing is the difference between a dimension and a lie.
    """
    out = svg.with_suffix(".pdf")
    subprocess.run(["inkscape", "--export-type=pdf", "--export-text-to-path",
                    f"--export-filename={out}", str(svg)],
                   check=True, capture_output=True)
    # Cairo stamps the wall clock into every PDF it writes, so two renders of
    # one drawing differ.  Pin it here, once, rather than at each caller.
    return reproducible.normalise_pdf(out)


def combine_pdfs(pages: list[tuple[Path, str]], out: Path,
                 title: str) -> Path:
    """Bind already-rendered sheets into one document, bookmarked per sheet.

    The individual sheets stay the deliverable: a drawing is printed and laid
    on a board, and that is one sheet at a time.  The bound copy is for the
    other way people use a drawing set -- reading it, mailing it, handing a
    whole family to a machine shop -- where six attachments is six chances to
    send five.

    Each sheet becomes an outline entry, because a six-page PDF with no
    bookmarks is a scroll bar, and the drawing numbers are the only thing that
    distinguishes the pages at thumbnail size.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    for pdf, label in pages:
        first = len(writer.pages)
        writer.append(str(pdf))
        writer.add_outline_item(label, first)
    writer.add_metadata({"/Title": title})
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as handle:
        writer.write(handle)
    # pypdf stamps its own clock, exactly as cairo does one layer down; the
    # tool strings are pinned as pypdf's, not the sheets', because this file
    # is pypdf's work.
    return reproducible.normalise_pdf(out, bound=True)


def to_png(svg: Path, dpi: float = PNG_DPI, out: Path | None = None) -> Path:
    out = out or svg.with_suffix(".png")
    subprocess.run(["inkscape", "--export-type=png", f"--export-dpi={dpi}",
                    f"--export-filename={out}", str(svg)],
                   check=True, capture_output=True)
    return out


def to_preview(svg: Path, out: Path, width: int = PREVIEW_WIDTH) -> Path:
    """Render *svg* small, for the README's preview grid."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["inkscape", "--export-type=png",
                    f"--export-width={width}",
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
