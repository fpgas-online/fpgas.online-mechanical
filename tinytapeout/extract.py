#!/usr/bin/env python3
"""Generate ``tinytapeout/boards.py`` from the upstream KiCad board files.

The numbers all come out of the ``.kicad_pcb`` files; the human judgement is the
``ROLES`` table below, which says which reference designator plays which
mechanical role on each revision.  Keeping those apart means a re-run can never
quietly invent a dimension, and a mis-identified part is a one-line fix.

The upstream repositories are expected to be cloned under ``tmp/src``::

    git clone https://github.com/TinyTapeout/tt-demo-pcb    tmp/src/tt-demo-pcb
    git clone https://github.com/TinyTapeout/tt123-demo-pcb tmp/src/tt123-demo-pcb

Run: uv run --no-project python tinytapeout/extract.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import kicad_extract, kicad_pcb  # noqa: E402
from tools.kicad_extract import one  # noqa: E402
WORK = ROOT / "tmp" / "pcb"

# Which shuttles used a board comes from the "Used by" column of Tiny Tapeout's
# own board revision spreadsheet, which is authoritative for this and is the
# only source that covers every revision.  The upstream historic README,
# tt-demo-pcb/doc/historic/README.md, is still cited for the revision-to-commit
# mapping it gives, but it stops at v2.1.2 and it is not a shuttle record.
#
# The spreadsheet's ID column is the canonical name of a board, and is what
# each sheet is titled with: "DB 06+ v2.1.2", not a description of it.  One of
# its IDs has no drawing here -- DB 4+ v1.2.1 (TT03p5) -- because the upstream
# repository has no tagged commit for it.  Every other board the spreadsheet
# lists is drawn.
#: Where the shuttle-to-board-revision mapping comes from.
HISTORIC_README = ("https://github.com/TinyTapeout/tt-demo-pcb/blob/main/"
                   "doc/historic/README.md")
# A short link, because this URL is printed in the SOURCES block of every
# demo board sheet and the plate sheet.  It resolves to the sheet's
# Demoboards tab, spreadsheet 1xD_uemuQcpUnXRY4twOrfFzF0urJLVWMdqAnrOJLetM
# at gid 1250963370; the redirect lives in github.com/mithro/mithro.github.io
# under redirects/tt-demoboards.md.
SHUTTLE_SHEET = "https://mith.ro/tt-demoboards/"

#: The number each feature carries in the schedule and on its balloon, fixed
#: across the whole demo board family so that a number means the same part on
#: every sheet.  A revision that does not carry a part leaves its number
#: unused: the boards with a fourth LED have no DIP switch and the boards with
#: a DIP switch have no fourth LED, so numbering them off each sheet's own
#: list made 6 mean one thing on half the set and another on the rest.
FEATURE_ORDER = ["usb_power", "display7", "led1", "led2", "led3", "led4",
                 "dipsw", "dipsw2", "side_pmod1", "side_pmod2", "side_pmod3"]

#: What each number means, in words a reader can match against, for the rows a
#: board has to carry for parts it does not have.  Generic, because the same
#: number is "LED D1" on one revision and "LED D3" on another: the number
#: identifies the position in the family's schedule, not the designator.
FEATURE_NAMES = {
    "usb_power": "USB-C power / control",
    "display7": "7-segment display",
    "led1": "First indicator LED",
    "led2": "Second indicator LED",
    "led3": "Third indicator LED",
    "led4": "Fourth indicator LED",
    "dipsw": "Input DIP switch",
    "dipsw2": "Second DIP switch",
    "side_pmod1": "Side Pmod, first position",
    "side_pmod2": "Side Pmod, second position",
    "side_pmod3": "Side Pmod, third position",
}

REVISIONS = [
    dict(
        key="tt123-v2.2.5",
        repo="tt123-demo-pcb", path="mpw-mb1.kicad_pcb", commit="303509a",
        title="DB mpw v2.2.5",
        subtitle="mpw-mb1 rev 2.2.5",
        used_by=("TT02",),
        kits=("TT02 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB mpw v2.2.5", Used by: {used}.',
        source_url="https://github.com/TinyTapeout/tt123-demo-pcb",
    ),
    dict(
        key="tt123-v2.2.6",
        repo="tt123-demo-pcb", path="mpw-mb1.kicad_pcb", commit="3d721a6",
        title="DB mpw v2.2.6",
        subtitle="mpw-mb1 rev 2.2.6",
        used_by=("TT03",),
        kits=("TT03 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB mpw v2.2.6", Used by: {used}.',
        extra_notes=(
            "Named \"TinyTapeout 1,2,3 Demo Board\" in KiCad, but no PCB "
            "served TT01, which was a bare-die trial run.",
        ),
        source_url="https://github.com/TinyTapeout/tt123-demo-pcb",
    ),
    dict(
        key="v1.2.1",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="8aad3f8",
        title="DB 4+ v1.2.1",
        subtitle="tinytapeout-demo rev 1.2.1",
        used_by=("TT03p5",),
        kits=("TT03p5 ASIC IC kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 4+ v1.2.1", Used by: {used}.',
        extra_notes=(
            "TT03p5's board is recorded as rev 1.2.1 but unconfirmed: the "
            "TT03p5 render is labelled v1.1.2.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v1.2.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="cfdd80d7b",
        title="DB 4+ v1.2.2",
        subtitle="tinytapeout-demo rev 1.2.2",
        used_by=("TT04",),
        kits=("TT04 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 4+ v1.2.2", Used by: {used}.',
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v1.2.3",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="a88cbc08b",
        title="DB 4+ v1.2.2c",
        subtitle="tinytapeout-demo rev 1.2.3",
        used_by=("TT05",),
        kits=("TT05 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 4+ v1.2.2c", Used by: {used}.',
        extra_notes=(
            "v1.2.2c is Tiny Tapeout's name for rev 1.2.3, an assembly "
            "variant of 1.2.2.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.0.1",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="292760e1f",
        title="DB 06+ v2.0.1",
        subtitle="tinytapeout-demo rev 2.0.1",
        used_by=("TT06",),
        kits=("TT06 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 06+ v2.0.1", Used by: {used}.',
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.1.0",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="a799acb38",
        title="DB 06+ v2.1.0",
        subtitle="tinytapeout-demo rev 2.1.0",
        used_by=("TT07",),
        kits=("TT07 Dev Kit",),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 06+ v2.1.0", Used by: {used}.',
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.1.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="028a51b1e",
        title="DB 06+ v2.1.2",
        subtitle="tinytapeout-demo rev 2.1.2",
        used_by=("TT08",),
        kits=("TT08 Dev Kit", "TT08 Dev Kit - CoB edition"),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 06+ v2.1.2", Used by: {used}.',
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v3.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="d830790ca",
        title="DB ETR v3.2",
        subtitle="tinytapeout-demo rev 3.2",
        used_by=("TT09", "TTSKY25a", "TTSKY25b", "TTGF0p2"),
        kits=("TT09 Dev Kit", "TTSKY25a Dev Kit", "TTSKY25b Dev Kit",
               "TTGF0p2 Dev Kit - P2 edition", "FPGA Dev Kit"),
        # The historic README does not carry this revision; Tiny Tapeout's own
        # board revision spreadsheet does, and it is where "ETR" comes from.
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB ETR v3.2", Used by: {used}.',
        extra_notes=(
            "\"DB ETR\" is the board's ID in Tiny Tapeout's board revision "
            "spreadsheet; the KiCad title block does not carry it.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v3.3",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="ecb636ace",
        title="DB ETR v3.3",
        subtitle="tinytapeout-demo rev 3.3",
        used_by=(),
        kits=(),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note="no row: this revision is not in the board revision "
                     "spreadsheet, so no shuttle is recorded for it.",
        extra_notes=(
            "Not in Tiny Tapeout's board revision spreadsheet, so no shuttle "
            "or kit is known to have shipped on it; the name follows the "
            "v3.2 ID.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
]

# Which designator plays which mechanical role, per revision.  Pmod designators
# are listed left to right as seen in the top view.
ROLES = {
    "tt123-v2.2.6": dict(
        pmods=["J3", "J9"], pmod_labels=["PMOD A", "PMOD B"],
        usb_power="J6", display7="U5",
        leds=["D1", "D2", "D3", "D4"], switch="SW4", switch2="SW2",
        holes=["MT1", "MT2", "MT3", "MT4"],
    ),
    "v1.2.2": dict(
        pmods=["J3", "J5", "J6"], pmod_labels=["INPUT", "BIDIR", "OUTPUT"],
        usb_power="J15", display7="U1",
        leds=["D1", "D2", "D3", "D4"], switch="SW4",
        holes=["MT1", "MT2", "MT3", "MT4"],
        side_pmods=["J12", "J13", "J14"],
    ),
    "v2.0.1": dict(
        pmods=["J3", "J5", "J6"], pmod_labels=["INPUT", "BIDIR", "OUTPUT"],
        usb_power="J20", display7="U1",
        leds=["D1", "D2", "D3"], switch="SW4",
        holes=["MT1", "MT2", "MT3", "MT4"],
        side_pmods=["J12", "J13", "J14"],
    ),
    "v3.2": dict(
        pmods=["J11", "J12", "J13"], pmod_labels=["INPUT", "BIDIR", "OUTPUT"],
        usb_power="J1", display7="U2",
        leds=["D3", "D4", "D5"], switch="SW1",
        holes=["MT1", "MT2"],
    ),
}
ROLES["tt123-v2.2.5"] = ROLES["tt123-v2.2.6"]
ROLES["v1.2.1"] = ROLES["v1.2.2"]
ROLES["v1.2.3"] = ROLES["v1.2.2"]
ROLES["v2.1.0"] = ROLES["v2.0.1"]
ROLES["v2.1.2"] = ROLES["v2.0.1"]
# The v3.3 file predates the schematic re-annotation on tt-demo-pcb main, so it
# still uses the v3.2 designators.
ROLES["v3.3"] = ROLES["v3.2"]

PMOD_HUMAN = {
    "usb_power": "USB power / control connector",
    "display7": "Seven-segment display",
}


def fetch(rev: dict) -> Path:
    """Check the board file out of the upstream clone at the pinned commit."""
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{rev['key']}.kicad_pcb"
    if out.exists():
        return out
    repo = ROOT / "tmp" / "src" / rev["repo"]
    blob = subprocess.run(
        ["git", "-C", str(repo), "show", f"{rev['commit']}:{rev['path']}"],
        capture_output=True, text=True, check=True).stdout
    out.write_text(blob)
    return out


def extract(rev: dict) -> dict:
    board = kicad_pcb.load(str(fetch(rev)))
    roles = ROLES[rev["key"]]
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints

    edges, radii = kicad_extract.outline(rev["key"], board, to_xy, w, h)
    corner_radius = radii[-1]
    profile_note = ""
    if len(radii) > 1:
        # The recess is a real feature of the outline and belongs on the
        # drawing.  Its fillet radii do not: four numbers to three decimals,
        # contributed by a connector footprint, that nobody cuts to.
        # Half a millimetre deep at 1:1, it reads as a drawing fault unless
        # the sheet says it is real.  Which footprint contributed it is a
        # KiCad detail nobody cuts to.
        profile_note = "The notch in the upper edge is a recess for the " \
            "USB-C shell."

    holes = [kicad_extract.hole(rev["key"], one(fps, ref), to_xy)
             for ref in roles["holes"]]

    pmods = [kicad_extract.pmod(one(fps, ref), to_xy, to_box,
                                key=f"pmod{i + 1}", label=roles["pmod_labels"][i])
             for i, ref in enumerate(roles["pmods"])]

    features = []

    def add(ref, key, label, kind, note="", box="courtyard"):
        b = kicad_extract.box(one(fps, ref), to_box, box)
        features.append(dict(key=key, label=label, kind=kind, designator=ref,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3], note=note))

    add(roles["usb_power"], "usb_power", "USB-C power / control", "usb_power",
        note="Body outline including the shell overhang past the board edge.")
    add(roles["display7"], "display7", "7-segment display", "display7")
    for n, ref in enumerate(roles["leds"], 1):
        add(ref, f"led{n}", f"LED {ref}", "led")
    # Every revision carries an 8-way input DIP switch, and the mpw board a
    # second, 9-way one beside it.  The way count is halved out of the pad
    # count rather than written in: a label that asserts "8-way" is a label
    # that will one day sit under a 9-way part, which is exactly what happened.
    if roles.get("switch"):
        ways = len(one(fps, roles["switch"]).pads) // 2
        add(roles["switch"], "dipsw", f"{ways}-way input DIP switch", "switch")
    if roles.get("switch2"):
        ways = len(one(fps, roles["switch2"]).pads) // 2
        add(roles["switch2"], "dipsw2",
            f"{ways}-way DIP switch {roles['switch2']}", "switch")
    for n, ref in enumerate(roles.get("side_pmods", []), 1):
        add(ref, f"side_pmod{n}", f"Side Pmod {ref} (not fitted)", "header",
            note="Footprint present but marked do-not-populate.")

    # Fixed numbers, not positions.  An unknown key stops the extraction
    # rather than sorting to the front, so adding a part is a decision about
    # where it belongs in the family's numbering.
    unknown = [f["key"] for f in features if f["key"] not in FEATURE_ORDER]
    if unknown:
        raise SystemExit(
            f"{rev['key']}: {', '.join(unknown)} not in FEATURE_ORDER; "
            "decide what number they carry across the family")
    features.sort(key=lambda f: FEATURE_ORDER.index(f["key"]))
    for f in features:
        f["number"] = FEATURE_ORDER.index(f["key"]) + 1

    return dict(
        key=rev["key"], title=rev["title"], subtitle=rev["subtitle"],
        used_by=list(rev["used_by"]),
        kits=list(rev.get("kits", ())),
        # Carried through so the emitted sheet can cite where its shuttle
        # mapping came from, which is not the same document for every
        # revision.
        shuttle_source=rev.get("shuttle_source", HISTORIC_README),
        shuttle_note=rev.get("shuttle_note", "used by: {used}"),
        extra_notes=rev.get("extra_notes", ()),
        commit=rev["commit"], repo=rev["repo"], path=rev["path"],
        source_url=rev["source_url"],
        kicad_title=board.title.strip(), kicad_rev=board.rev, kicad_date=board.date,
        width=round(w, 3), height=round(h, 3), corner_radius=corner_radius,
        thickness=board.thickness, edges=edges, profile_note=profile_note,
        holes=holes, pmods=pmods, features=features)


HEADER = '''"""Tiny Tapeout demo board mechanical data.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python tinytapeout/extract.py

Every dimension is read directly out of the upstream KiCad board file at the
commit named in each entry's ``source``; nothing here is transcribed by eye.
Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  The three Pmod host headers are
along the lower (Y = 0) edge; the TT01/02/03 board has only two.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, PmodHeader, Source

BOARDS: dict[str, BoardSpec] = {}

#: Feature numbers are fixed across the family: a number means the same part on
#: every sheet.  A revision that does not carry the part still gets a row, so a
#: gap in a schedule reads as "not on this board" rather than as an omission.
FEATURE_NUMBERS = __NUMBERS__

'''


def render(rec: dict) -> str:
    def holes():
        return ",\n".join(
            f"        Hole(x={h['x']}, y={h['y']}, dia={h['dia']}, "
            f"label={h['label']!r}, kind={h['kind']!r}, keepout_dia={h['keepout_dia']})"
            for h in rec["holes"])

    def pmods():
        return ",\n".join(
            f"        PmodHeader(key={p['key']!r}, label={p['label']!r}, "
            f"designator={p['designator']!r}, cx={p['cx']}, cy={p['cy']}, "
            f"pin1_x={p['pin1_x']}, pin1_y={p['pin1_y']},\n"
            f"                   body_x0={p['body_x0']}, body_y0={p['body_y0']}, "
            f"body_x1={p['body_x1']}, body_y1={p['body_y1']})"
            for p in rec["pmods"])

    def edges():
        return ",\n".join("                        " + repr(e) for e in rec["edges"])

    def feats():
        return ",\n".join(
            f"        Feature(key={f['key']!r}, label={f['label']!r}, kind={f['kind']!r},\n"
            f"                designator={f['designator']!r}, x0={f['x0']}, y0={f['y0']}, "
            f"x1={f['x1']}, y1={f['y1']},\n"
            f"                note={f['note']!r}, number={f['number']})"
            for f in rec["features"])

    used = ", ".join(rec["used_by"]) or "no shipped shuttle yet"
    twins = ", ".join(rec["identical_to"])
    def extra_notes() -> str:
        return "".join(f"        {n!r},\n"
                       for n in rec.get("extra_notes", ()))

    # A database fact, kept on the record even though the drawing set merges
    # twins onto one sheet and says it there once.  A revision with no twin
    # gets no note: a sheet for one board need not say it is for one board.
    identical_note = (
        f"        {'Geometrically identical to revision ' + twins + '.'!r},\n"
        if twins else "")
    return f'''
BOARDS[{rec["key"]!r}] = BoardSpec(
    key={rec["key"]!r},
    title={rec["title"]!r},
    subtitle={rec["subtitle"]!r},
    family="tinytapeout",
    used_by={tuple(rec["used_by"])!r},
    kits={tuple(rec["kits"])!r},
    outline=Outline(width={rec["width"]}, height={rec["height"]},
                    corner_radius={rec["corner_radius"]}, thickness={rec["thickness"]},
                    profile_note={rec["profile_note"]!r},
                    edges=(
{edges()},
                    )),
    holes=(
{holes()},
    ),
    pmods=(
{pmods()},
    ),
    features=(
{feats()},
    ),
    sources=(
        Source(label="KiCad board file",
               ref="{rec["source_url"]}  {rec["path"]} @ {rec["commit"]}",
               note="title block: {rec["kicad_title"]} rev {rec["kicad_rev"]}, "
                    "dated {rec["kicad_date"]}"),
        Source(label="Shuttle mapping",
               ref={rec["shuttle_source"]!r},
               note={rec["shuttle_note"].format(used=used)!r}),
    ),
    notes=(
        "Hole IDs are the KiCad reference designators.",
{identical_note}{extra_notes()}    ),
)
'''


def geometry_signature(rec: dict):
    """What makes two revisions the same board, mechanically.

    The outline edges are part of it, not just the bounding box: two revisions
    could share a width, height and corner radius while differing in a profile
    feature such as the USB-C shell recess in the TT04/TT05 upper edge.
    """
    return (rec["width"], rec["height"], rec["corner_radius"],
            tuple(rec["edges"]),
            tuple(sorted((h["x"], h["y"], h["dia"]) for h in rec["holes"])),
            tuple(sorted((p["cx"], p["cy"]) for p in rec["pmods"])),
            tuple(sorted((f["key"], f["x0"], f["y0"], f["x1"], f["y1"])
                         for f in rec["features"])))


def main() -> None:
    out = ROOT / "tinytapeout" / "boards.py"
    records = [extract(rev) for rev in REVISIONS]
    # Several revisions are byte-identical mechanically; say so on the sheet,
    # so a reader can tell an identical board from a stale drawing.
    by_sig: dict = {}
    for rec in records:
        by_sig.setdefault(geometry_signature(rec), []).append(rec["key"])
    for rec in records:
        twins = by_sig[geometry_signature(rec)]
        rec["identical_to"] = [k for k in twins if k != rec["key"]]

    numbers = "{\n" + "".join(
        f"    {i}: {FEATURE_NAMES[key]!r},\n"
        for i, key in enumerate(FEATURE_ORDER, 1)) + "}"
    chunks = [HEADER.replace('__NUMBERS__', numbers)]
    for rec in records:
        chunks.append(render(rec))
        print(f"{rec['key']:14s} {rec['width']:7.2f} x {rec['height']:6.2f} mm  "
              f"R{rec['corner_radius']}  {len(rec['holes'])} holes  "
              f"{len(rec['pmods'])} pmods  {len(rec['features'])} features"
              + (f"  == {', '.join(rec['identical_to'])}"
                 if rec["identical_to"] else ""))
    out.write_text("".join(chunks))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
