"""Where everything lives, and what every sheet is called.

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

"What is this sheet called" is the same question wearing a hat, so it is
answered here too.  See ``drawing_name``.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Each family of sheets, in reading order, and the directory it renders into.
#: The key is the family's slug, used in drawing names and README anchors.
FAMILY_DIRS = {
    "tinytapeout": ROOT / "tinytapeout" / "output",
    "raspberry-pi": ROOT / "raspberry_pi" / "output",
    "fpga": ROOT / "fpga" / "output",
    "accessories": ROOT / "accessories" / "output",
    "mounting-plate": ROOT / "tinytapeout" / "mounting_plate" / "output",
}

#: Every demo board sheet's file stem is this and the revisions it covers.
TT_STEM_LEAD = "tt-demo-board"

#: The file stems of the sheets that are not named after a board key: the
#: accessories' adapter sheet, whose part key is shorter than the file it
#: renders to, and the mounting plate's four.  Here rather than in the
#: generator because a stem is where a sheet lives, and because the notes on
#: other sheets cite these by name and must derive that name from the same
#: string the file is written to.
PMOD_HAT_STEM = "digilent-pmod-hat-adapter"
PLATE_STEM = "tt-generic-mounting-plate"
FITTING_GUIDE_STEM = f"{PLATE_STEM}-fitting-guide"

#: The drill templates, in sheet order, and the file stem each is written to.
DRILL_TEMPLATE_STEMS = {
    "plate": f"{PLATE_STEM}-drill-template",
    "chassis": f"{PLATE_STEM}-chassis-drill-template",
}

#: Each family's drawing-name prefix, and the head of its file stems that the
#: prefix already says.  Adding a family is one row here beside its row above.
#:
#: The lead is stripped so a name says each thing once: the demo board stems
#: all begin ``tt-demo-board``, which ``TT-DB`` is, and every mounting plate
#: stem begins with the plate's own name, which ``TT-MP`` is.  Strip it and
#: the plate's own fabrication drawing has nothing left, so it is called
#: ``TT-MP`` flat: the family's principal sheet, with the detail sheets
#: hanging off it.
FAMILY_PREFIXES = {
    "tinytapeout": ("TT-DB", TT_STEM_LEAD),
    "raspberry-pi": ("RPI", "rpi"),
    "fpga": ("FPGA", ""),
    "accessories": ("ACC", ""),
    "mounting-plate": ("TT-MP", PLATE_STEM),
}


def slug(key: str) -> str:
    """A board key as it is written in a file name: ``v2.2.5`` -> ``v2p2p5``.

    A dot in a file name reads as an extension and a ``p`` for the decimal
    point is the convention the board files themselves use.
    """
    return key.replace(".", "p").replace("_", "-")


def drawing_name(family: str, stem: str) -> str:
    """What the DRAWING NO cell of *stem*'s title block says.

    The name is the sheet's own file stem in capitals, behind its family's
    prefix, with the part of the stem the prefix already says taken off:
    ``fpga/output/arty-a7.svg`` is ``FPGA-ARTY-A7`` and
    ``tinytapeout/output/tt-demo-board-v3p3.svg`` is ``TT-DB-V3P3``.

    It used to be a sequence position -- ``enumerate()`` over a reading-order
    list -- which meant a sheet's identity depended on what else was in the
    set.  Four pull requests open at once each added an FPGA sheet and each
    called it ``FPGA-05``; whichever landed second had to renumber, re-render,
    rebind, and go back over every cross reference written against the old
    number.  A name derived from the sheet alone is fixed the moment the sheet
    is created and no other sheet can take it, because no two sheets can share
    a file.  That last point is the whole argument: uniqueness is not a rule
    anyone has to remember, it is the file system's.

    The reading-order lists stay.  The bound copies and the README grid still
    need an order; they just no longer number anything.
    """
    try:
        prefix, lead = FAMILY_PREFIXES[family]
    except KeyError:
        raise SystemExit(
            f"no drawing-name prefix for the family {family!r}; add one to "
            "FAMILY_PREFIXES in tools/layout.py, beside its output directory")
    rest = slug(stem)
    if lead and rest.startswith(lead):
        rest = rest[len(lead):]
    rest = rest.strip("-").upper()
    return "-".join(part for part in (prefix, rest) if part)


def family_of(svg: Path) -> str:
    """Which family a rendered sheet belongs to, by where it was written."""
    for family, directory in FAMILY_DIRS.items():
        if svg.parent == directory:
            return family
    raise SystemExit(f"{svg} is not in any family's output directory")


def drawing_name_for(svg: Path) -> str:
    """The drawing name of an already-rendered sheet."""
    return drawing_name(family_of(svg), svg.stem)


#: The sheets that other sheets cite in their notes.  A note that names a
#: drawing has to spell the name out, and spelling it out by hand is how a
#: cross reference goes stale.
PMOD_HAT_SHEET = drawing_name("accessories", PMOD_HAT_STEM)
PLATE_SHEET = drawing_name("mounting-plate", PLATE_STEM)
FITTING_GUIDE_SHEET = drawing_name("mounting-plate", FITTING_GUIDE_STEM)


def sheets() -> list[Path]:
    """Every rendered sheet, as an SVG path, in family order."""
    out: list[Path] = []
    for directory in FAMILY_DIRS.values():
        out.extend(sorted(directory.glob("*.svg")))
    return out


def bundles() -> list[Path]:
    """Every bound copy: a PDF in an output directory with no SVG beside it.

    Found rather than listed, and findable because of what a bundle is: it is
    bound from finished sheets and is not rendered from a drawing of its own,
    so it is the only kind of file in an output directory with no SVG next to
    it.  A list here would be a second place to forget a new family.
    """
    out: list[Path] = []
    for directory in FAMILY_DIRS.values():
        out.extend(sorted(p for p in directory.glob("*.pdf")
                          if not p.with_suffix(".svg").exists()))
    return out


def preview_for(svg: Path) -> Path:
    """Where a sheet's small render belongs: beside it, not in a common pool."""
    return svg.parent / "previews" / f"{svg.stem}.png"


def rel(path: Path | str) -> str:
    """A repository-relative path, for printing and for README references."""
    return str(Path(path).relative_to(ROOT))
