"""Where everything lives.

This repository groups by subject: ``tinytapeout``, ``raspberry_pi`` and
``accessories`` each own their data, their extractor and their rendered
sheets, and the mounting plate is a Tiny Tapeout thing so it sits under
``tinytapeout``.  Machinery that belongs to no subject -- the drafting
library, the schema, the generator and the checks -- lives here in ``tools``.

The one thing that arrangement makes harder is answering "where are all the
sheets", which the generator, the README builder and the three checks that
walk every sheet all need.  They ask here, so they cannot disagree about the
set: a family added in one place and forgotten in another is exactly the drift
these checks exist to catch.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Each family of sheets, in reading order, and the directory it renders into.
#: The key is the family's slug, used in drawing numbers and README anchors.
FAMILY_DIRS = {
    "tinytapeout": ROOT / "tinytapeout" / "output",
    "raspberry-pi": ROOT / "raspberry_pi" / "output",
    "fpga": ROOT / "fpga" / "output",
    "accessories": ROOT / "accessories" / "output",
    "mounting-plate": ROOT / "tinytapeout" / "mounting_plate" / "output",
}


def sheets() -> list[Path]:
    """Every rendered sheet, as an SVG path, in family order."""
    out: list[Path] = []
    for directory in FAMILY_DIRS.values():
        out.extend(sorted(directory.glob("*.svg")))
    return out


def preview_for(svg: Path) -> Path:
    """Where a sheet's small render belongs: beside it, not in a common pool."""
    return svg.parent / "previews" / f"{svg.stem}.png"


def rel(path: Path | str) -> str:
    """A repository-relative path, for printing and for README references."""
    return str(Path(path).relative_to(ROOT))
