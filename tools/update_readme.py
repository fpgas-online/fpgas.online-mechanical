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

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import GENERIC_POE, PMOD_HAT, WAVESHARE_POE  # noqa: E402
from tinytapeout.mounting_plate.plate import PLATE                              # noqa: E402
from raspberry_pi.boards import BOARDS as RPI                 # noqa: E402
from tinytapeout.boards import BOARDS as TT                   # noqa: E402
from tools.generate_diagrams import RPI_ORDER, slug, tt_sheets          # noqa: E402
from tools.layout import FAMILY_DIRS, rel                               # noqa: E402

BEGIN = "<!-- sheets:begin -->"
END = "<!-- sheets:end -->"

#: Cells per row.  GitHub renders a three-column table at roughly 290 px a
#: cell, which is what the preview width is chosen against.
COLUMNS = 3

#: Displayed width of a preview, in pixels.
CELL_WIDTH = 270


def groups() -> list[tuple[str, str, list[tuple[str, str, str, str]]]]:
    """Each family: its heading, its layout key, and its sheets in order."""
    return [
        ("Tiny Tapeout demo boards", "tinytapeout",
         [(f"TT-DB-{n:02d}", f"tt-demo-board-{stem}", spec.title, spec.subtitle)
          for n, (stem, spec) in enumerate(tt_sheets(), 1)]),
        ("Raspberry Pi, with a Digilent Pmod HAT Adapter overlaid",
         "raspberry-pi",
         [(f"RPI-{n:02d}", slug(k), RPI[k].title, RPI[k].subtitle)
          for n, k in enumerate(RPI_ORDER, 1)]),
        ("Accessories", "accessories",
         [("ACC-01", "digilent-pmod-hat-adapter",
           PMOD_HAT.title, PMOD_HAT.subtitle),
          ("ACC-02", WAVESHARE_POE.key,
           WAVESHARE_POE.title, WAVESHARE_POE.subtitle),
          ("ACC-03", GENERIC_POE.key,
           GENERIC_POE.title, GENERIC_POE.subtitle)]),
        ("Mounting plate", "mounting-plate",
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


def grid() -> str:
    """One HTML table per family, three equal columns.

    Not a Markdown table.  Markdown gives no way to set a column width, and
    the renderer sizes columns to their content, so the cell with the longest
    caption won the width and showed its preview at the full CELL_WIDTH while
    the others were squeezed narrower by the image's own max-width rule -- the
    first thumbnail came out visibly bigger than the two beside it.  A
    Markdown table also needs a header row, so a group of eight sheets became
    three separate tables with gaps between them rather than one grid.
    """
    out = ["Each thumbnail links to the PDF. The same sheet is also there as "
           "SVG and as", "a full-resolution PNG.", ""]
    width = f"{100 // COLUMNS}%"
    for heading, folder, rows in groups():
        out += [f"### {heading}", "", "<table>"]
        for i in range(0, len(rows), COLUMNS):
            out.append("<tr>")
            for j in range(COLUMNS):
                if i + j >= len(rows):
                    out.append(f'<td width="{width}"></td>')
                    continue
                no, stem, title, sub = rows[i + j]
                img = rel(FAMILY_DIRS[folder] / "previews" / f"{stem}.png")
                pdf = rel(FAMILY_DIRS[folder] / f"{stem}.pdf")
                out.append(f'<td width="{width}" valign="top" align="center">')
                out.append(f'<a href="{pdf}"><img src="{img}" '
                           f'width="{CELL_WIDTH}" alt="{no} {title}"></a><br>')
                out.append(f'<b>{no}</b> {title}<br>{sub}')
                out.append("</td>")
            out.append("</tr>")
        out += ["</table>", ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    readme = ROOT / "README.md"
    text = readme.read_text()
    if BEGIN not in text or END not in text:
        raise SystemExit(
            f"README.md has no {BEGIN} / {END} markers to write between")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{BEGIN}\n\n{grid()}\n{END}{tail}"
    if new == text:
        print("README preview grid already up to date")
        return 0
    readme.write_text(new)
    print(f"rewrote the README preview grid: "
          f"{sum(len(g[2]) for g in groups())} sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
