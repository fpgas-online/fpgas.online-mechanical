#!/usr/bin/env python3
"""Rewrite the README's preview grid from the sheets that actually exist.

The grid names every sheet, its drawing number and its file paths.  Kept by
hand it drifts the moment a sheet is added, renamed or dropped -- which is
what happened when the Raspberry Pi 3 Model A+ was removed.  ``check_sheets``
catches that drift; this fixes it.

Everything between the two marker comments in README.md is replaced.  Run
with::

    uv run --no-project --with pillow --with pyyaml python scripts/update_readme.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data.accessories import GENERIC_POE, PMOD_HAT, WAVESHARE_POE  # noqa: E402
from data.mounting_plate import PLATE                              # noqa: E402
from data.raspberry_pi_boards import BOARDS as RPI                 # noqa: E402
from data.tinytapeout_boards import BOARDS as TT                   # noqa: E402
from generate_diagrams import RPI_ORDER, TT_ORDER, slug            # noqa: E402

BEGIN = "<!-- sheets:begin -->"
END = "<!-- sheets:end -->"

#: Cells per row.  GitHub renders a three-column table at roughly 290 px a
#: cell, which is what the preview width is chosen against.
COLUMNS = 3

#: Displayed width of a preview, in pixels.
CELL_WIDTH = 270


def groups() -> list[tuple[str, str, list[tuple[str, str, str, str]]]]:
    """Each family: its heading, its directory, and its sheets in order."""
    return [
        ("Tiny Tapeout demo boards", "tinytapeout",
         [(f"TT-DB-{n:02d}", f"tt-demo-board-{slug(k)}",
           TT[k].title, TT[k].subtitle)
          for n, k in enumerate(TT_ORDER, 1)]),
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
           "Which holes each demo board revision uses")]),
    ]


def grid() -> str:
    out = ["Each thumbnail links to the PDF. The same sheet is also there as "
           "SVG and as", "a full-resolution PNG.", ""]
    for heading, folder, rows in groups():
        out += [f"### {heading}", ""]
        for i in range(0, len(rows), COLUMNS):
            chunk = rows[i:i + COLUMNS]
            cells, caps = [], []
            for no, stem, title, sub in chunk:
                img = f"diagrams/previews/{stem}.png"
                pdf = f"diagrams/{folder}/{stem}.pdf"
                cells.append(f'<a href="{pdf}"><img src="{img}" '
                             f'width="{CELL_WIDTH}" alt="{no} {title}"></a>')
                caps.append(f"**{no}** {title}<br>{sub}")
            pad = [""] * (COLUMNS - len(chunk))
            out.append("| " + " | ".join(cells + pad) + " |")
            out.append("|" + "---|" * COLUMNS)
            out.append("| " + " | ".join(caps + pad) + " |")
            out.append("")
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
