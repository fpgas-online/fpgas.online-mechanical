#!/usr/bin/env python3
"""Rewrite the README's preview grid from the sheets that actually exist.

The grid names every sheet, its drawing number and its file paths.  Kept by
hand it drifts the moment a sheet is added, renamed or dropped -- which is
what happened when the Raspberry Pi 3 Model A+ was removed.  ``check_sheets``
catches that drift; this fixes it.

Everything between the two marker comments in README.md is replaced.  Run
with::

    uv run --no-project --with pillow python tools/update_readme.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import GENERIC_POE, PMOD_HAT, WAVESHARE_POE  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE                              # noqa: E402
from fpga.boards import BOARDS as FPGA                        # noqa: E402
from raspberry_pi.boards import BOARDS as RPI                 # noqa: E402
from tinytapeout.boards import BOARDS as TT                   # noqa: E402
from tools.generate_diagrams import FPGA_ORDER, RPI_ORDER, slug, tt_sheets  # noqa: E402
from tools.layout import FAMILY_DIRS, rel                               # noqa: E402

BEGIN = "<!-- sheets:begin -->"
END = "<!-- sheets:end -->"

#: Cells per row.  GitHub renders a three-column table at roughly 290 px a
#: cell, which is what the preview width is chosen against.  A family can
#: ask for fewer: the mounting plate's four sheets are two A3 landscape and
#: two A4 portrait, and at three across the two portrait templates split
#: over a row break with a lone cell under them.  Two across puts the pair
#: of A3 on one row and the pair of A4 side by side on the next.
COLUMNS = 3

#: Displayed width of a preview, in pixels.
CELL_WIDTH = 270


def groups() -> list[tuple[str, str, int, list[tuple[str, str, str, str]]]]:
    """Each family: its heading, layout key, cells per row, and its sheets."""
    return [
        ("Tiny Tapeout demo boards", "tinytapeout", COLUMNS,
         [(f"TT-DB-{n:02d}", f"tt-demo-board-{stem}", spec.title, spec.subtitle)
          for n, (stem, spec) in enumerate(tt_sheets(), 1)]),
        ("Raspberry Pi, with a Digilent Pmod HAT Adapter overlaid",
         "raspberry-pi", COLUMNS,
         [(f"RPI-{n:02d}", slug(k), RPI[k].title, RPI[k].subtitle)
          for n, k in enumerate(RPI_ORDER, 1)]),
        ("FPGA development boards", "fpga", COLUMNS,
         [(f"FPGA-{n:02d}", slug(k), FPGA[k].title, FPGA[k].subtitle)
          for n, k in enumerate(FPGA_ORDER, 1)]),
        ("Accessories", "accessories", COLUMNS,
         [("ACC-01", "digilent-pmod-hat-adapter",
           PMOD_HAT.title, PMOD_HAT.subtitle),
          ("ACC-02", WAVESHARE_POE.key,
           WAVESHARE_POE.title, WAVESHARE_POE.subtitle),
          ("ACC-03", GENERIC_POE.key,
           GENERIC_POE.title, GENERIC_POE.subtitle)]),
        ("Mounting plate", "mounting-plate", 2,
         [("TT-MP-01", "tt-generic-mounting-plate",
           PLATE.title, PLATE.subtitle),
          ("TT-MP-02", "tt-generic-mounting-plate-fitting-guide",
           "TT Mounting Plate Fitting Guide",
           "Which holes each demo board revision uses"),
          ("TT-MP-03", "tt-generic-mounting-plate-drill-template",
           "Drill Template: Mounting Plate",
           "A4 at 1:1 - print, tape down and drill through"),
          ("TT-MP-04", "tt-generic-mounting-plate-chassis-drill-template",
           "Drill Template: Chassis",
           "A4 at 1:1 - the six M4 fixings in the box the plate bolts to")]),
    ]


def table(rows, base: Path, columns: int = COLUMNS) -> list[str]:
    """One HTML table of previews, with every path relative to *base*.

    Not a Markdown table.  Markdown gives no way to set a column width, and
    the renderer sizes columns to their content, so the cell with the longest
    caption won the width and showed its preview at the full CELL_WIDTH while
    the others were squeezed narrower by the image's own max-width rule -- the
    first thumbnail came out visibly bigger than the two beside it.  A
    Markdown table also needs a header row, so a group of eight sheets became
    three separate tables with gaps between them rather than one grid.
    """
    out = ["<table>"]
    width = f"{100 // columns}%"
    for i in range(0, len(rows), columns):
        out.append("<tr>")
        for j in range(columns):
            if i + j >= len(rows):
                out.append(f'<td width="{width}"></td>')
                continue
            no, folder, stem, title, sub = rows[i + j]
            d = FAMILY_DIRS[folder]
            img = os.path.relpath(d / "previews" / f"{stem}.png", base)
            pdf = os.path.relpath(d / f"{stem}.pdf", base)
            out.append(f'<td width="{width}" valign="top" align="center">')
            out.append(f'<a href="{pdf}"><img src="{img}" '
                       f'width="{CELL_WIDTH}" alt="{no} {title}"></a><br>')
            out.append(f'<b>{no}</b> {title}<br>{sub}')
            out.append("</td>")
        out.append("</tr>")
    out += ["</table>", ""]
    return out


def full_grid(base: Path) -> str:
    """Every family, under its own heading: the root README's grid."""
    out = ["Each thumbnail links to the PDF. The same sheet is also there as "
           "SVG.", ""]
    for heading, folder, columns, rows in groups():
        out += [f"### {heading}", ""]
        out += table([(no, folder, stem, title, sub)
                      for no, stem, title, sub in rows], base, columns)
    return "\n".join(out).rstrip() + "\n"


def family_grid(folder: str, base: Path) -> str:
    """One family's sheets, for that family's own README."""
    rows = [(no, folder, stem, title, sub)
            for heading, key, columns, group in groups() if key == folder
            for no, stem, title, sub in group]
    columns = next(c for heading, key, c, group in groups() if key == folder)
    out = ["Each thumbnail links to the PDF. The same sheet is also there as "
           "SVG.", ""]
    out += table(rows, base, columns)
    return "\n".join(out).rstrip() + "\n"


#: Which README carries which family's grid.  The root carries them all.
FAMILY_READMES = {
    "tinytapeout": ROOT / "tinytapeout" / "README.md",
    "raspberry-pi": ROOT / "raspberry_pi" / "README.md",
    "fpga": ROOT / "fpga" / "README.md",
    "accessories": ROOT / "accessories" / "README.md",
    "mounting-plate": ROOT / "tinytapeout" / "mounting_plate" / "README.md",
}


def write_between(path: Path, body: str) -> bool:
    """Replace the marked region of *path* with *body*; True if it changed."""
    text = path.read_text()
    if BEGIN not in text or END not in text:
        raise SystemExit(
            f"{rel(path)} has no {BEGIN} / {END} markers to write between")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{BEGIN}\n\n{body}\n{END}{tail}"
    if new == text:
        return False
    path.write_text(new)
    return True


def main() -> int:
    changed = []
    readme = ROOT / "README.md"
    if write_between(readme, full_grid(readme.parent)):
        changed.append(rel(readme))
    for folder, path in FAMILY_READMES.items():
        if write_between(path, family_grid(folder, path.parent)):
            changed.append(rel(path))
    if not changed:
        print("preview grids already up to date")
        return 0
    print(f"rewrote the preview grids in: {', '.join(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
