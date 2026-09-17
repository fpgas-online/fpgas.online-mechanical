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

#: Every demo board sheet's file stem is this and the revisions it covers,
#: assembled by ``tt_stem``.
TT_STEM_LEAD = "tt-demo-board"

#: Each accessory sheet's file stem, by the key of the part it is drawn from.
#: Here rather than in the generator because a stem is where a sheet lives,
#: and because the notes on other sheets cite these by name and must derive
#: that name from the same string the file is written to.
#:
#: A part key names the thing, vendor and all, because the data is a catalogue
#: of parts somebody has to buy.  A stem names the sheet, and the sheet's title
#: block already says who makes it, so the stem says what it is: ``poe-usbc``,
#: not ``waveshare-poe-usbc``.  The names that came out of the vendor-bearing
#: stems -- ``ACC-DIGILENT-PMOD-HAT-ADAPTER``, ``ACC-WAVESHARE-POE-USBC`` --
#: were long enough to be read as a sentence rather than as a label.
ACC_STEMS = {
    "pmod-hat-adapter": "pmod-hat",
    "waveshare-poe-usbc": "poe-usbc",
    "generic-poe-microusb": "poe-microusb",
    "raspmod": "raspmod",
}

PMOD_HAT_STEM = ACC_STEMS["pmod-hat-adapter"]

#: The mounting plate's four file stems.
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
#: stem begins ``tt-generic-mounting-plate``, which ``TT-MP`` is.  The whole of
#: it: the family is the plate and its three satellites, so PLATE on three of
#: the four names says nothing the prefix has not.  The sheet whose stem is
#: exactly the lead keeps it, by the rule in ``drawing_name``, and is
#: ``TT-MP-PLATE``.
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


def tt_stem(keys: list[str]) -> str:
    """The file stem of the demo board sheet covering *keys*, in board order.

    A sheet covers one geometry, which can be several revisions: the stem is
    the first revision and the last, and a board name the two share written
    once, so v2.2.5 and v2.2.6 of the tt123 board give
    ``tt-demo-board-tt123-v2p2p5-v2p2p6`` and the 4+ board's v1.2.1, v1.2.2 and
    v1.2.3 give ``tt-demo-board-v1p2p1-v1p2p3``.

    It listed every revision it covered, and every board name with it:
    ``tt-demo-board-tt123-v2p2p5-tt123-v2p2p6``, whose drawing name ran to
    31 characters and said tt123 twice.  A range says which revisions in the
    length of two, and the revisions are in order, so the end points are the
    range.  What the range cannot say -- that the middle revision is on this
    sheet too, and which shuttles and kits it went out in -- the title, the
    subtitle and the notes say in full, and they are what a reader of the
    drawing has in front of them.
    """
    first, last = slug(keys[0]), slug(keys[-1])
    if first == last:
        return f"{TT_STEM_LEAD}-{first}"
    board, _, rev = first.rpartition("-")
    board_last, _, rev_last = last.rpartition("-")
    if board and board == board_last:
        return f"{TT_STEM_LEAD}-{board}-{rev}-{rev_last}"
    return f"{TT_STEM_LEAD}-{first}-{last}"


def acc_stem(key: str) -> str:
    """The file stem of the accessory sheet drawn from the part *key*."""
    try:
        return ACC_STEMS[key]
    except KeyError:
        raise SystemExit(
            f"no sheet file stem for the accessory {key!r}; add one to "
            "ACC_STEMS in tools/layout.py, saying what the part is without "
            "the vendor the title block already names")


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
    is created, and nothing else in the set can take it away.

    Two sheets in one family collide only if their stems differ by something
    ``slug`` and ``upper`` throw away -- ``rpi5``, ``rpi-5`` and ``rpi_5`` all
    give ``RPI-5`` -- so uniqueness is very nearly the file system's, but not
    quite, and ``tools/check_sheets.py`` checks it rather than assuming it.

    A family whose lead is one of its own stems has one sheet the stripping
    leaves nothing of: the mounting plate's fabrication drawing is written to
    ``tt-generic-mounting-plate``, which is the lead entire.  That sheet takes
    the last word of the lead, so it is ``TT-MP-PLATE`` -- named for what it
    is, which is the plate, rather than for the family it heads.  Handing back
    the bare prefix instead would be worse than terse: ``TT-MP`` is a substring
    of ``TT-MP-FITTING-GUIDE``, so the check that each sheet carries its own
    name was satisfied by the plate's *note* citing the fitting guide, and
    deleting the title block from the plate SVG did not fail it.  A name that
    is a prefix of its siblings' cannot be told from them by any test that
    reads a sheet, so the rule is not to produce one.

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
        rest = rest[len(lead):] or lead.rsplit("-", 1)[-1]
    rest = rest.strip("-").upper()
    if not rest:
        raise SystemExit(
            f"the sheet {stem!r} has no file stem to be named after, so "
            f"{family!r} would name it {prefix!r}, which is the family and "
            "not a sheet of it.")
    return f"{prefix}-{rest}"


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
