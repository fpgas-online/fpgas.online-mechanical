#!/usr/bin/env python3
"""Rewrite the README's preview grid from the sheets that actually exist.

The grid names every sheet, its drawing name and its file paths.  Kept by
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
from accessories.raspmod import RASPMOD                       # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE                              # noqa: E402
from fpga.boards import BOARDS as FPGA                        # noqa: E402
from raspberry_pi.boards import BOARDS as RPI                 # noqa: E402
from tinytapeout.boards import BOARDS as TT                   # noqa: E402
from tools.generate_diagrams import FPGA_ORDER, RPI_ORDER, tt_sheets  # noqa: E402
from tools.layout import (DRILL_TEMPLATE_STEMS, FAMILY_DIRS,  # noqa: E402
                          FITTING_GUIDE_STEM, PLATE_STEM, PMOD_HAT_STEM,
                          drawing_name, rel, slug)

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


def named(family: str, rows) -> list[tuple[str, str, str, str]]:
    """Put each row's drawing name in front of it, derived from its stem.

    Derived here rather than written into the tables below, for the same
    reason the sheets themselves derive it: a name written out by hand is a
    name that can disagree with the one on the drawing.
    """
    return [(drawing_name(family, stem), stem, title, sub)
            for stem, title, sub in rows]


def groups() -> list[tuple[str, str, int, list[tuple[str, str, str, str]]]]:
    """Each family: its heading, layout key, cells per row, and its sheets."""
    return [
        ("Tiny Tapeout demo boards", "tinytapeout", COLUMNS,
         named("tinytapeout", [(stem, spec.title, spec.subtitle)
                               for stem, spec in tt_sheets()])),
        ("Raspberry Pi, with a Digilent Pmod HAT Adapter overlaid",
         "raspberry-pi", COLUMNS,
         named("raspberry-pi", [(slug(k), RPI[k].title, RPI[k].subtitle)
                                for k in RPI_ORDER])),
        ("FPGA development boards", "fpga", COLUMNS,
         named("fpga", [(slug(k), FPGA[k].title, FPGA[k].subtitle)
                        for k in FPGA_ORDER])),
        ("Accessories", "accessories", COLUMNS,
         named("accessories",
               [(PMOD_HAT_STEM, PMOD_HAT.title, PMOD_HAT.subtitle),
                (WAVESHARE_POE.key, WAVESHARE_POE.title,
                 WAVESHARE_POE.subtitle),
                (GENERIC_POE.key, GENERIC_POE.title, GENERIC_POE.subtitle),
                (RASPMOD.key, RASPMOD.title, RASPMOD.subtitle)])),
        ("Mounting plate", "mounting-plate", 2,
         named("mounting-plate",
               [(PLATE_STEM, PLATE.title, PLATE.subtitle),
                (FITTING_GUIDE_STEM, "TT Mounting Plate Fitting Guide",
                 "Which holes each demo board revision uses"),
                (DRILL_TEMPLATE_STEMS["plate"],
                 "Drill Template: Mounting Plate",
                 "A4 at 1:1 - print, tape down and drill through"),
                (DRILL_TEMPLATE_STEMS["chassis"], "Drill Template: Chassis",
                 "A4 at 1:1 - the six M4 fixings in the box the plate bolts "
                 "to")])),
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
            name, folder, stem, title, sub = rows[i + j]
            d = FAMILY_DIRS[folder]
            img = os.path.relpath(d / "previews" / f"{stem}.png", base)
            pdf = os.path.relpath(d / f"{stem}.pdf", base)
            out.append(f'<td width="{width}" valign="top" align="center">')
            out.append(f'<a href="{pdf}"><img src="{img}" '
                       f'width="{CELL_WIDTH}" alt="{name} {title}"></a><br>')
            out.append(f'<b>{name}</b> {title}<br>{sub}')
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
        out += table([(name, folder, stem, title, sub)
                      for name, stem, title, sub in rows], base, columns)
    return "\n".join(out).rstrip() + "\n"


def family_grid(folder: str, base: Path) -> str:
    """One family's sheets, for that family's own README."""
    rows = [(name, folder, stem, title, sub)
            for heading, key, columns, group in groups() if key == folder
            for name, stem, title, sub in group]
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
