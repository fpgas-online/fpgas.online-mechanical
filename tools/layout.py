"""Where everything lives, and what every sheet is called.

This repository groups by subject: each family's directory owns its data,
its extractor and its rendered sheets (``FAMILY_DIRS`` below says where each
renders to) and the mounting plate is a Tiny Tapeout thing so it sits under
``tinytapeout``.  Machinery that belongs to no subject -- the drafting
library, the schema, the generator and the checks -- lives here in ``tools``.

The one thing that arrangement makes harder is answering "where are all the
sheets", which the generator, the README builder and the checks that
walk every sheet all need.  They ask here, so they cannot disagree about the
set: a family added in one place and forgotten in another is exactly the drift
these checks exist to catch.

"What is this sheet called" is the same question wearing a hat, so it is
answered here too.  See ``drawing_name``.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Each family of sheets, in reading order, and the directory it renders into.
#: The key is the family's slug, used in drawing names and README anchors.
FAMILY_DIRS = {
    "tinytapeout": ROOT / "tinytapeout" / "output",
    "raspberry-pi": ROOT / "raspberry_pi" / "output",
    "raspberry-pi-camera": ROOT / "raspberry_pi_camera" / "output",
    "fpga": ROOT / "fpga" / "output",
    "accessories": ROOT / "accessories" / "output",
    "mounting-plate": ROOT / "tinytapeout" / "mounting_plate" / "output",
    "camera-holder": ROOT / "tinytapeout" / "camera_holder" / "output",
}

#: Every demo board sheet's file stem is this and the revisions it covers,
#: assembled by ``tt_stem``.
TT_STEM_LEAD = "tt-demo-board"

#: Each accessory sheet's file stem, by the key of the part it is drawn from.
#: Here rather than in the generator because a stem is where a sheet lives,
#: and because ``ACC_NAMES`` below turns that same stem into the drawing name
#: the notes on other sheets cite, so the file and the name it is quoted by
#: are both derived from one string.
#:
#: A stem names the file, and the sheet's title block already says who makes
#: the part and what its part number is, so the stem is left to say what the
#: thing is.  What that drops differs by row, and only some of the keys
#: carry a vendor at all:
#:
#: * ``pmod-hat-adapter`` keeps its key and loses ``-adapter``, which the
#:   sheet's title says.  Its file used to be ``digilent-pmod-hat-adapter``:
#:   the vendor was not in the key, it was put in front of it by hand when the
#:   file name was written, and that is where ``ACC-DIGILENT-PMOD-HAT-ADAPTER``
#:   came from.
#: * ``waveshare-poe-usbc`` and ``generic-poe-microusb`` are keys that do name
#:   the vendor, because the data is a catalogue of parts somebody has to buy
#:   and that is what they buy.  The stem drops it.
#: * ``raspmod`` is already what the thing is called; nothing to drop.
ACC_STEMS = {
    "pmod-hat-adapter": "pmod-hat",
    "waveshare-poe-usbc": "poe-usbc",
    "generic-poe-microusb": "poe-microusb",
    "raspmod": "raspmod",
}

PMOD_HAT_STEM = ACC_STEMS["pmod-hat-adapter"]

#: What each accessory sheet is called, by the file stem it is written to.
#: ``acc_name`` reads it, and ``drawing_name`` puts ``ACC-`` in front.
#:
#: A table and not a rule, because these stems are words rather than codes and
#: no mechanical shortening of ``raspmod`` or ``poe-microusb`` leaves four
#: characters that still say which part it is.  Keyed by the stem rather than
#: by the part key so that the name can be worked out from a rendered file,
#: which is what ``drawing_name_for`` does and how ``check_sheets.py`` reads
#: the name it expects in a title block off the sheet's path alone.
#:
#: The first word is the kind and the second is which one of that kind, so two
#: names quoted in the same note show at a glance which two parts are
#: alternatives to each other.  HAT is Digilent's own word for the adapter
#: that sits on the Pi's 40-pin header; the Raspmod is filed under it as the
#: other way of getting Pmod ports onto a Pi, though it is not a HAT in the
#: Raspberry Pi specification's sense and reaches the Pi over a ribbon cable
#: instead -- which is what ``accessories/raspmod-vs-pmod-hat.md`` is about.
ACC_NAMES = {
    "pmod-hat": "hat-pmod",      # Digilent's Pmod HAT Adapter
    "raspmod": "hat-rmod",       # the Raspmod, the other Pi-to-Pmod board
    "poe-usbc": "poe-usbc",      # Waveshare's splitter, Type-C output
    "poe-microusb": "poe-musb",  # the generic splitter, micro-USB output
}

#: The mounting plate's four file stems.
PLATE_STEM = "tt-generic-mounting-plate"
FITTING_GUIDE_STEM = f"{PLATE_STEM}-fitting-guide"

#: The drill templates, in sheet order, and the file stem each is written to.
DRILL_TEMPLATE_STEMS = {
    "plate": f"{PLATE_STEM}-drill-template",
    "chassis": f"{PLATE_STEM}-chassis-drill-template",
}

#: What each mounting plate sheet is called, by the file stem it is written
#: to.  ``plate_name`` reads it, and ``drawing_name`` puts ``TT-MP-`` in front,
#: so these four stems give ``TT-MP-PLATE``, ``TT-MP-FIT``, ``TT-MP-DRILL`` and
#: ``TT-MP-CHASSIS``.
#:
#: A table and not a rule, for the reason ``ACC_NAMES`` is one: what is left
#: of these stems is words -- ``fitting-guide``, ``chassis-drill-template`` --
#: and no mechanical shortening of them leaves something a workshop would say
#: out loud.  Keyed by the whole stem rather than by the tail of it, so that a
#: row can be read against the stems it is built from; ``plate_name`` strips
#: the lead off the keys the same way ``drawing_name`` strips it off the stem
#: it is asked about.
#:
#: One word each, and the word is what the sheet is for rather than what it is
#: titled: the fitting guide is the sheet you FIT a board with, the two
#: templates are the DRILL and the CHASSIS. The full titles were the names
#: until the owner asked for them shortened -- ``TT-MP-CHASSIS-DRILL-TEMPLATE``
#: is a drawing number nobody reads out -- and the titles still say all of it
#: on the sheets themselves.
PLATE_NAMES = {
    PLATE_STEM: "plate",                        # the fabrication drawing
    FITTING_GUIDE_STEM: "fit",                  # which holes a revision uses
    DRILL_TEMPLATE_STEMS["plate"]: "drill",     # A4 template for the plate
    DRILL_TEMPLATE_STEMS["chassis"]: "chassis",  # A4 template for its box
}

#: Each family's drawing-name prefix, and the head of its file stems that the
#: prefix already says.  Adding a family is one row here beside its row above,
#: and a row in ``FAMILY_NAME_RULES`` as well if what is left of its stems is
#: longer than a drawing number should be.
#:
#: The lead is stripped so a name says each thing once: the demo board stems
#: all begin ``tt-demo-board``, which ``TT-DB`` is, and every mounting plate
#: stem begins ``tt-generic-mounting-plate``, which ``TT-MP`` is.  The whole of
#: it: the family is the plate and its three satellites, so PLATE on three of
#: the four names says nothing the prefix has not.  The sheet whose stem is
#: exactly the lead is left the lead's last word by ``drawing_name``, and
#: ``PLATE_NAMES`` keeps that word, so it is ``TT-MP-PLATE``.
FAMILY_PREFIXES = {
    "tinytapeout": ("TT-DB", TT_STEM_LEAD),
    "raspberry-pi": ("RPI", "rpi"),
    # The camera stems are the module numbers, cm2 for the Camera Module 2,
    # and the prefix already says what kind of module: RPICAM-2, exactly as
    # the Pi family's rpi5 is RPI-5.  The lead is "cm" and not "" so that a
    # name does not say camera twice.
    "raspberry-pi-camera": ("RPICAM", "cm"),
    "fpga": ("FPGA", ""),
    "accessories": ("ACC", ""),
    "mounting-plate": ("TT-MP", PLATE_STEM),
    # The camera holder is a made part built on the plate, and filed in a
    # directory of its own: its checks and its STEP solids do not belong
    # among the plate's generated data.  It takes the plate's prefix because
    # it is a sheet of the plate's set -- it bolts through the plate's own
    # fixings -- and HOLDER_NAMES says which in one word.  A prefix two
    # families share is safe because check_sheets.py tests every name
    # against every other across the whole set.
    "camera-holder": ("TT-MP", ""),
}


def slug(key: str) -> str:
    """A board key as it is written in a file name: ``v2.2.5`` -> ``v2p2p5``.

    A dot in a file name reads as an extension and a ``p`` for the decimal
    point is the convention the board files themselves use.
    """
    return key.replace(".", "p").replace("_", "-")


def strip_lead(lead: str, stem: str) -> str:
    """What is left of *stem* once its family's prefix has said *lead*.

    The slugged stem with *lead* taken off the front, which is what
    ``drawing_name`` names a sheet after and what it hands a family's rule in
    ``FAMILY_NAME_RULES``.  A sheet whose stem is exactly the lead would be
    left nothing, so it is left the lead's last word instead; see
    ``drawing_name`` for why that is a name and the bare prefix is not.

    Its own function because ``plate_name`` puts the keys of ``PLATE_NAMES``
    through it to meet the stem ``drawing_name`` is asking about.  Two copies
    of this stripping could disagree, and the sheet whose stem is the lead is
    exactly the one they would disagree about.
    """
    rest = slug(stem)
    if lead and rest.startswith(lead):
        rest = rest[len(lead):] or lead.rsplit("-", 1)[-1]
    return rest.strip("-")


def tt_stem(keys: list[str]) -> str:
    """The file stem of the demo board sheet covering *keys*, in board order.

    A sheet covers one geometry, which can be several revisions: the stem is
    the first revision and the last, and a board name the two share written
    once, so v2.2.5 and v2.2.6 of the tt123 board give
    ``tt-demo-board-tt123-v2p2p5-v2p2p6`` and the 4+ board's v1.2.1, v1.2.2 and
    v1.2.3 give ``tt-demo-board-v1p2p1-v1p2p3``.

    It listed every revision it covered, and every board name with it:
    ``tt-demo-board-tt123-v2p2p5-tt123-v2p2p6``, 39 characters that said
    tt123 twice.  A range says which revisions in the length of two, and the
    revisions are in order, so the end points are the range.  What the range
    cannot say -- that the middle revision is on this sheet too, and which
    shuttles and kits it went out in -- the title, the subtitle and the notes
    say in full, and they are what a reader of the drawing has in front of
    them.

    The range is kept for the file name's own sake, not for the drawing
    name's: the sheet is called ``TT-DB-TT123`` or ``TT-DB-V121``, by
    ``tt_name``, which takes the front of this and nothing else.  Somebody
    choosing between files in a directory listing is the reader this is for,
    and both end points are worth the characters to them.
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


#: A stem word that is a board revision: ``v3p3``, ``v2p1p2``, ``v2`` if a
#: board is ever cut at a major revision, and ``v1p2p2c`` for a lettered one.
#: The ``p`` is ``slug``'s, standing in for the dot the revision is written
#: with everywhere else.
#:
#: The number and the letter are separate groups so that ``tt_name`` can take
#: the ``p``s out of the number without touching the letter, which matters for
#: the one revision whose letter would be a ``p``.
REVISION_RE = re.compile(r"(v\d+(?:p\d+)*)([a-z]?)")


def tt_name(rest: str) -> str:
    """What the demo board sheet whose stem ends in *rest* is called.

    *rest* is the stem with ``tt-demo-board`` taken off: hyphen-separated
    words, a board name first where the revisions carry one and then the
    revisions the sheet covers, so ``tt123-v2p2p5-v2p2p6``, ``v1p2p1-v1p2p3``
    or ``v3p3``.

    A board name is both shorter and more memorable than a revision, so it
    wins where there is one and ``tt123-v2p2p5-v2p2p6`` is ``TT123``.
    Otherwise the name is the first revision with the ``p`` separators taken
    out: ``v1p2p1-v1p2p3`` is ``V121``, ``v2p1p2`` is ``V212`` and ``v3p3`` is
    ``V33``.

    A revision may end in a letter, and the letter is kept: ``v1p2p2c`` is
    ``V122C``.  The data already has lettered revisions -- the sheet covering
    v1.2.1 to v1.2.3 is titled "DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c"
    -- so the day one of them is keyed that way and heads a sheet is a day
    this has to be right.  A pattern that did not match the letter would not
    fail: the word would be taken for a board name and passed through whole,
    and the sheet would quietly be called ``TT-DB-V1P2P2C``, which is the
    stem-shaped name this rule exists to stop.  The ``p`` separators come out
    of the number alone, so a revision lettered ``p`` keeps its letter.

    Naming a sheet after one of the revisions it covers is honest rather than
    approximate, because a sheet covers exactly one geometry and the first
    revision to carry that geometry is where it came from: v1.2.2 and v1.2.3
    are on the ``V121`` sheet because mechanically they are the v1.2.1 board.
    The stem keeps the range, so the file still says where the sheet stops as
    well as where it starts, and the sheet's title, subtitle and notes list
    every revision and every shuttle in full -- which is what a reader with
    the drawing in front of them actually has.
    """
    first = rest.split("-")[0]
    match = REVISION_RE.fullmatch(first)
    if not match:
        return first
    number, letter = match.groups()
    return number.replace("p", "") + letter


def acc_name(stem: str) -> str:
    """What the accessory sheet written to *stem* is called: see ACC_NAMES."""
    try:
        return ACC_NAMES[stem]
    except KeyError:
        raise SystemExit(
            f"no drawing name for the accessory sheet {stem!r}; add one to "
            "ACC_NAMES in tools/layout.py, as the kind of part it is -- HAT "
            "for a board on the Pi's header, POE for a splitter -- and four "
            "or five characters saying which one")


def plate_name(stem_tail: str) -> str:
    """What the mounting plate sheet ending in *stem_tail* is called.

    *stem_tail* is what ``strip_lead`` leaves of the sheet's file stem once
    ``tt-generic-mounting-plate`` has been taken off -- ``fitting-guide``,
    ``drill-template``, ``chassis-drill-template``, and for the plate's own
    sheet, whose stem is the lead entire, the lead's last word, ``plate``.
    ``PLATE_NAMES`` is keyed by the whole stem, so its keys go through the
    same stripping to be looked up in those terms.
    """
    names = {strip_lead(PLATE_STEM, stem): name
             for stem, name in PLATE_NAMES.items()}
    try:
        return names[stem_tail]
    except KeyError:
        raise SystemExit(
            f"no drawing name for the mounting plate sheet whose stem ends "
            f"{stem_tail!r}; add one to PLATE_NAMES in tools/layout.py, keyed "
            "by that sheet's whole file stem, as the one word saying which of "
            "the family's sheets it is -- not the sheet's title, which the "
            "sheet itself already carries in full")


#: The camera holders' sheets, one per lens, by file stem: the stem says
#: what it is, what it is on and for which lens, where the prefix has already
#: said the plate.  CAM and the lens's own angle: CAMERA with a lens after
#: it would have made the holder for one lens a prefix of the other's.
HOLDER_STEM = "tt-camera-holder"


def holder_stem(lens_key: str) -> str:
    """The file stem of the holder sheet for the lens keyed *lens_key*."""
    return f"{HOLDER_STEM}-{lens_key}"


HOLDER_NAMES = {
    holder_stem("65"): "cam65",     # the holder for the stock 65 deg lens
    holder_stem("120"): "cam120",   # the holder for the 120 deg lens
}


def holder_name(stem: str) -> str:
    """What the camera holder sheet written to *stem* is called."""
    try:
        return HOLDER_NAMES[stem]
    except KeyError:
        raise SystemExit(
            f"no drawing name for the camera holder sheet {stem!r}; add one "
            "to HOLDER_NAMES in tools/layout.py, one word saying what it is "
            "on the plate for")


#: The OV5647's lens sheet: every lens option's field of view and focus,
#: declared and derived, which the position sheets compute with and cite.
#: Its stem says what it is of; its name, RPICAM-LENS, says which sheet.
LENS_STEM = "ov5647-lenses"

#: The camera family's other sheets, by file stem.  A camera module's own
#: sheet needs no row: ``cm3`` leaves ``3`` behind the lead and the name is
#: RPICAM-3.  A position sheet's stem is ``over-`` and its subject's key,
#: which says the subject in full -- ``over-tt-mounting-plate`` -- where
#: the drawing number wants OVER and one word for which subject.
RPICAM_NAMES = {
    LENS_STEM: "lens",                         # the OV5647's lens options
    "over-tt-mounting-plate": "over-plate",    # the TT mounting plate
    "over-arty-a7": "over-arty",               # the Arty A7
    "over-arty-ethernet": "over-eth",          # the Arty's Ethernet corner
}

#: What a camera module sheet's stem leaves behind the lead: the module
#: number, ``1``, ``2`` or ``3``.
RPICAM_MODULE_RE = re.compile(r"\d+")


def rpicam_name(rest: str) -> str:
    """What the camera sheet whose stem ends in *rest* is called.

    A module's own sheet keeps the module number; anything else is looked up
    in ``RPICAM_NAMES``, and a stem that is neither stops the render rather
    than passing a stem-shaped name through.
    """
    if RPICAM_MODULE_RE.fullmatch(rest):
        return rest
    try:
        return RPICAM_NAMES[rest]
    except KeyError:
        raise SystemExit(
            f"no drawing name for the camera sheet whose stem ends {rest!r}; "
            "a module sheet is named for its module, and a position sheet "
            "wants a row in RPICAM_NAMES in tools/layout.py, OVER and four "
            "or five characters saying which subject")


#: How a family cuts what is left of a stem down to a drawing name, for the
#: families that need it.  A separate table rather than a third column
#: of FAMILY_PREFIXES: several branches are open at once each adding a row to
#: that table, and changing its shape would conflict with every one of them,
#: where a new table beside it conflicts with nothing.
#:
#: A family with no rule here is named for its stem, which is the ordinary
#: case and wants no table: RPI-3B and FPGA-ARTY-A7 are already as short as
#: their sheets can honestly be said to be.  The families here are the
#: ones where the stem is not:
#:
#: * a demo board's stem carries every revision the sheet covers
#: * an accessory's says in words what the part is
#: * a mounting plate sheet's says its title -- ``chassis-drill-template``
#: * a camera position sheet's says its subject in full
#: * a camera holder's says what it is and what it is on
#:
#: Each is right for a file name and too long for a drawing number.
FAMILY_NAME_RULES = {
    "tinytapeout": tt_name,
    "accessories": acc_name,
    "mounting-plate": plate_name,
    "raspberry-pi-camera": rpicam_name,
    "camera-holder": holder_name,
}


def drawing_name(family: str, stem: str) -> str:
    """What the DRAWING NO cell of *stem*'s title block says.

    The name is the sheet's own file stem in capitals, behind its family's
    prefix, with the part of the stem the prefix already says taken off:
    ``fpga/output/arty-a7.svg`` is ``FPGA-ARTY-A7`` and
    ``raspberry_pi/output/rpi5.svg`` is ``RPI-5``.

    A family may shorten what is left of its stem instead, by having a rule
    in ``FAMILY_NAME_RULES``: the demo boards, the accessories and the
    mounting plate do, so
    ``tinytapeout/output/tt-demo-board-v1p2p1-v1p2p3.svg`` is ``TT-DB-V121``,
    ``accessories/output/pmod-hat.svg`` is ``ACC-HAT-PMOD`` and the plate's
    ``tt-generic-mounting-plate-chassis-drill-template.svg`` is
    ``TT-MP-CHASSIS``.  The rule is a function of the stem and nothing
    else, because ``drawing_name_for`` has to answer from a rendered sheet's
    path alone.

    The two are named for different readers, which is why they are allowed to
    differ.  A drawing number is read off a title block, quoted in a note on
    another sheet, written on a purchase order and said out loud across a
    workshop, so it has to be short enough to take in at a glance and to copy
    without a slip; the owner's figure is at most four or five characters
    behind the family's prefix.  A file name is read once from a directory
    listing by somebody who is choosing between files, and can afford to say
    more -- which is exactly what the demo board stems and the accessory
    stems do say.  So the stems are left alone, every link and preview that
    cites them keeps working, and only the name is cut.

    It used to be a sequence position -- ``enumerate()`` over a reading-order
    list -- which meant a sheet's identity depended on what else was in the
    set.  Four pull requests open at once each added an FPGA sheet and each
    called it ``FPGA-05``; whichever landed second had to renumber, re-render,
    rebind, and go back over every cross reference written against the old
    number.  A name derived from the sheet alone is fixed the moment the sheet
    is created, and nothing else in the set can take it away.

    Two sheets in a family with no rule collide only if their stems differ by
    something ``slug`` and ``upper`` throw away -- ``rpi5``, ``rpi-5`` and
    ``rpi_5`` all give ``RPI-5`` -- so uniqueness is very nearly the file
    system's, but not quite.  A rule throws away more than that by design: two
    demo board sheets starting at one revision would both take its name, and
    two rows of ``ACC_NAMES`` or of ``PLATE_NAMES`` could be given the same
    value.  Neither is reachable today, and neither is argued about here,
    because
    ``tools/check_sheets.py`` checks the whole set rather than assuming it.

    A family whose lead is one of its own stems has one sheet the stripping
    leaves nothing of: the mounting plate's fabrication drawing is written to
    ``tt-generic-mounting-plate``, which is the lead entire.  ``strip_lead``
    leaves that sheet the last word of the lead, ``plate``, which is the word
    ``PLATE_NAMES`` keeps for it, so it is ``TT-MP-PLATE`` -- named for what
    it is, which is the plate, rather than for the family it heads.  Handing
    back the bare prefix instead would be worse than terse: ``TT-MP`` is a
    prefix of ``TT-MP-FIT`` and of every other name in the family, so the
    check that each sheet carries its own name was satisfied by the plate's
    *note* citing the fitting guide, and deleting the title block from the
    plate SVG did not fail it.  A name that is a prefix of its siblings'
    cannot be told from them by any test that reads a sheet, so the rule is
    not to produce one -- which is why the family's four names are four
    different words and not ``TT-MP``, ``TT-MP-F``, ``TT-MP-D``.

    "The last word of the lead" is the whole lead where the lead is one word,
    which would give ``RPI-RPI`` for a Raspberry Pi sheet whose file is
    ``rpi.svg``.  No family has such a sheet -- every Pi stem says which Pi --
    and the name it would produce is at least honest about being the family's
    one sheet rather than the family.  Recorded because it is the case a
    reader will think of, not because anything needs doing about it.

    The reading-order lists stay.  The bound copies and the README grid still
    need an order; they just no longer number anything.
    """
    try:
        prefix, lead = FAMILY_PREFIXES[family]
    except KeyError:
        raise SystemExit(
            f"no drawing-name prefix for the family {family!r}; add one to "
            "FAMILY_PREFIXES in tools/layout.py, beside its output directory")
    rest = strip_lead(lead, stem)
    rule = FAMILY_NAME_RULES.get(family)
    if rule is not None and rest:
        rest = rule(rest)
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
    """Every bound copy on disk: a PDF in an output directory with no SVG.

    Found rather than listed, and findable because of what a bundle is: it is
    bound from finished sheets and is not rendered from a drawing of its own,
    so it is the only kind of file in an output directory with no SVG next to
    it.

    What each bundle *holds* is the generator's answer, not this one --
    ``generate_diagrams.bundles()`` names the pages and the bookmarks, and the
    check reads a bound copy against that.  This is the other half of the
    question, and the only one a file system can answer: which bound copies
    are actually there.  A bundle nobody binds any more would be committed
    and unread without it.
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
