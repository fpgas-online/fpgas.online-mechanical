#!/usr/bin/env python3
"""Generate ``fpga/boards.py`` from each FPGA board's own published source.

Six boards, three kinds of source, one rule: the numbers are machine-read
and the identification is hand-curated.

===========  =============================================================
Arty A7      Digilent's mechanical drawing: a DXF for the outline, the
             through-hole pads and the connector slots, and the PDF plot
             beside it for the component bodies the DXF does not carry
ULX3S        the KiCad board file, at every tag Radiona sold boards from
PYNQ-Z2      TUL's STEP assembly, the only machine-readable source
ButterStick  the KiCad board file at the release that was sold
Icepi Zero   the KiCad board file at the mass-production tag, and again at
             a later, re-annotated commit of the same revision, which has to
             agree on every position drawn
Cynthion     the KiCad board file at the release Great Scott Gadgets call
             the initial production release
===========  =============================================================

The sources are expected under ``tmp/src``; ``tools/fetch_fpga.sh`` puts
them there.

Run: uv run --no-project --with ezdxf --with pdfplumber --with cadquery \\
         python fpga/extract.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import kicad_extract, kicad_pcb  # noqa: E402
from tools.dump_rpi_pdf import rectangles  # noqa: E402
from tools.kicad_extract import one  # noqa: E402

SRC = ROOT / "tmp" / "src"
WORK = ROOT / "tmp" / "pcb"

#: The number each feature carries on every sheet of the family.  Six boards
#: with six different sets of connectors share one schedule, so a reader
#: flipping between them finds the Ethernet jack at 3 whether the board has
#: one or not.  Pmod hosts are not features: they have their own table, as
#: on every other family.
#:
#: A number, once issued, keeps its meaning: it is printed on balloons and in
#: schedules on sheets that are already out, so a board that needs a slot the
#: family has not got gets a NEW number at the end rather than a renumbering.
#: Cynthion is the first board here with more than two USB ports -- four of
#: them -- and the first with a second row of LEDs that is not the user row,
#: so 9, 10 and 11 were added for those.  That is why the USB ports read
#: 1, 2, 9, 10 on its sheet and not 1 to 4.
FEATURE_ORDER = ["usb_prog", "usb_second", "ethernet", "leds", "rgb_leds",
                 "exp1", "exp2", "exp3", "usb_third", "usb_fourth",
                 "status_leds"]

FEATURE_NAMES = {
    "usb_prog": "USB programming / console port",
    "usb_second": "Second USB port",
    "ethernet": "Ethernet RJ45",
    "leds": "User LEDs, single colour",
    "rgb_leds": "User LEDs, tri-colour",
    "exp1": "Expansion connector, first",
    "exp2": "Expansion connector, second",
    "exp3": "Expansion connector, third",
    "usb_third": "Third USB port",
    "usb_fourth": "Fourth USB port",
    # Short, because this name is printed on the five sheets that do not
    # carry the row as well, and it sets the width of every FPGA schedule.
    "status_leds": "Status LEDs, debug controller",
}

#: Pin 1 of a 2x6 host, from the pin field's centre and the edge it faces.
#:
#: Looking into a host connector, pin 1 is at the top right: the PYNQ-Z2
#: manual draws it that way (figure 16.1), and the Tiny Tapeout board
#: files number their hosts the same way.  The top row of the socket is fed
#: by the row of through-holes FARTHER from the board edge, because those
#: are the contacts with the longer bend.  Turn the board so the host's edge
#: is at the bottom and pin 1 is the right-hand pin of the inner row; the
#: table gives that corner for each edge in the board's own frame.
PIN1_CORNER = {
    "bottom": (+1, +1),    # +x end, inner row is +y of centre
    "top": (-1, -1),
    "right": (-1, +1),     # inner row is -x of centre, +y end
    "left": (+1, -1),
}

PMOD_PITCH = 2.54
PMOD_COLUMNS = 6
PMOD_ROWS = 2


def pin1(cx: float, cy: float, edge: str) -> tuple[float, float]:
    sx, sy = PIN1_CORNER[edge]
    half_span = (PMOD_COLUMNS - 1) * PMOD_PITCH / 2
    half_rows = (PMOD_ROWS - 1) * PMOD_PITCH / 2
    if edge in ("bottom", "top"):
        return cx + sx * half_span, cy + sy * half_rows
    return cx + sx * half_rows, cy + sy * half_span


def pmod_from_pins(points, *, key: str, label: str, designator: str,
                   edge: str, body) -> dict:
    """A host from the twelve centres of its through-holes.

    The field has to be a 2x6 grid on 2.54 mm, or nearly so: the Arty A7's
    drawing puts its two rows 2.50 mm apart, which is a drawing on a metric
    grid rather than a different connector, and is let through with a note.
    The pin field's centre is what a plate registers against, so it is
    taken from the extreme pins rather than averaged.
    """
    if len(points) != PMOD_COLUMNS * PMOD_ROWS:
        raise SystemExit(f"{key}: {len(points)} pins, not 12")
    xs = sorted(p[0] for p in points)
    ys = sorted(p[1] for p in points)
    along, across = (xs, ys) if edge in ("bottom", "top") else (ys, xs)
    span = along[-1] - along[0]
    rows = across[-1] - across[0]
    if abs(span - (PMOD_COLUMNS - 1) * PMOD_PITCH) > 0.05 or abs(rows - PMOD_PITCH) > 0.05:
        raise SystemExit(f"{key}: pin field spans {span:.3f} x {rows:.3f} mm, "
                         "not a 2x6 on 2.54 mm")
    cx = (xs[0] + xs[-1]) / 2
    cy = (ys[0] + ys[-1]) / 2
    want = pin1(cx, cy, edge)
    # The pin 1 the rule gives has to be one of the holes actually read, and
    # that hole's own position is what gets reported, not the rule's ideal.
    p1 = min(points, key=lambda p: abs(p[0] - want[0]) + abs(p[1] - want[1]))
    if abs(p1[0] - want[0]) + abs(p1[1] - want[1]) > 0.05:
        raise SystemExit(f"{key}: no hole at the pin 1 position {want}")
    return dict(key=key, label=label, designator=designator, edge=edge,
                cx=round(cx, 3), cy=round(cy, 3),
                pin1_x=round(p1[0], 3), pin1_y=round(p1[1], 3),
                body_x0=round(body[0], 3), body_y0=round(body[1], 3),
                body_x1=round(body[2], 3), body_y1=round(body[3], 3))


def row_feature(boxes, *, key: str, label: str, kind: str, note: str = "",
                designator: str = "") -> dict:
    """One feature covering a row of small parts, LEDs mostly.

    A row of eight LEDs on 2.54 mm would take eight balloons and say nothing
    a plate designer needs; the row's extent and its pitch say it all.  The
    pitch is measured from the boxes rather than written into the label, so
    the label cannot claim a pitch the parts do not have.
    """
    boxes = sorted(boxes)
    cs = sorted(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in boxes)
    axis = 0 if (cs[-1][0] - cs[0][0]) >= (cs[-1][1] - cs[0][1]) else 1
    steps = [cs[i + 1][axis] - cs[i][axis] for i in range(len(cs) - 1)]
    pitch = sum(steps) / len(steps)
    if max(abs(s - pitch) for s in steps) > 0.05:
        raise SystemExit(f"{key}: LED pitch is not uniform: {steps}")
    return dict(key=key, kind=kind, designator=designator,
                label=f"{label}, {len(boxes)} on {pitch:.2f} mm pitch",
                x0=round(min(b[0] for b in boxes), 3),
                y0=round(min(b[1] for b in boxes), 3),
                x1=round(max(b[2] for b in boxes), 3),
                y1=round(max(b[3] for b in boxes), 3), note=note)


def number_features(key: str, features: list[dict]) -> None:
    unknown = [f["key"] for f in features if f["key"] not in FEATURE_ORDER]
    if unknown:
        raise SystemExit(f"{key}: {', '.join(unknown)} not in FEATURE_ORDER; "
                         "decide what number they carry across the family")
    features.sort(key=lambda f: FEATURE_ORDER.index(f["key"]))
    for f in features:
        f["number"] = FEATURE_ORDER.index(f["key"]) + 1


# ---------------------------------------------------------------------------
# KiCad boards: ULX3S and ButterStick
# ---------------------------------------------------------------------------

def kicad_file(repo: str, commit: str, path: str, name: str) -> Path:
    """Check the board file out of the upstream clone at a pinned commit."""
    return kicad_extract.pinned_board(SRC / repo, commit, path,
                                      WORK / f"{name}.kicad_pcb")


ULX3S_REPO = "https://github.com/emard/ulx3s"
#: Every revision the maker's own manual lists as "for sale", at its tag.
#: All four are read, and the drawn geometry has to agree before one sheet
#: is allowed to cover them; a revision that moved a hole would fail here.
ULX3S_REVISIONS = [
    ("v3.0.3", "300a361b"),
    ("v3.0.7", "v3.0.7"),
    ("v3.0.8", "9908a1f8"),
    ("v3.1.7", "cc1817d2"),
]
ULX3S_MANUAL = "https://github.com/emard/ulx3s/blob/master/doc/MANUAL.md"


def extract_ulx3s() -> dict:
    records = []
    for tag, commit in ULX3S_REVISIONS:
        path = kicad_file("ulx3s", commit, "ulx3s.kicad_pcb", f"ulx3s-{tag}")
        board = kicad_pcb.load(str(path))
        rec = _ulx3s_geometry(tag, board)
        # Resolve the tag to the commit it names, so the citation is exact.
        rec["commit"] = subprocess.run(
            ["git", "-C", str(SRC / "ulx3s"), "rev-parse", "--short=8", commit],
            capture_output=True, text=True, check=True).stdout.strip()
        rec["tag"] = tag
        records.append(rec)
    first = records[0]
    for other in records[1:]:
        for field in ("width", "height", "edges", "holes", "features"):
            if first[field] != other[field]:
                raise SystemExit(
                    f"ulx3s: {other['tag']} differs from {first['tag']} in "
                    f"{field}; the revisions need separate sheets")
    tags = [r["tag"] for r in records]
    return dict(
        key="ulx3s", title="ULX3S",
        subtitle=", ".join(tags[:-1]) + f" and {tags[-1]}",
        front_edge="top", thickness=first["thickness"],
        width=first["width"], height=first["height"], corner_radius=0.0,
        edges=first["edges"], holes=first["holes"], pmods=[],
        features=first["features"],
        sources=[
            ("KiCad board file",
             f"{ULX3S_REPO}  ulx3s.kicad_pcb @ {r['commit']} (tag {r['tag']})",
             "Radiona / emard") for r in records] + [
            ("Board versions", ULX3S_MANUAL,
             'section "Board Versions": v3.0.3, v3.0.7, v3.0.8 and v3.1.7 '
             'are the rows marked "for sale"; the four board files are read '
             "and agree on everything drawn here."),
            ("Board size", f"{ULX3S_REPO}/blob/master/README.md",
             'quoted: "This is a small (94x51 mm) standalone FPGA board"; '
             "the board file gives 93.98 x 50.80, which is 37 x 20 tenths "
             "of an inch."),
        ],
        notes=[
            "Hole IDs are the KiCad reference designators.",
            "No Pmod host. J1 and J2 are right-angle 2x20 sockets on 2.54 mm "
            "whose pinout is Pmod compatible, per the maker; pin 1 of each "
            "is given in the schedule note.",
            "No Ethernet jack.",
        ],
    )


def _ulx3s_geometry(tag: str, board) -> dict:
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints
    edges, radii = kicad_extract.outline(tag, board, to_xy, w, h)
    if radii:
        raise SystemExit(f"ulx3s {tag}: the outline has arcs now")
    holes = [kicad_extract.hole(tag, one(fps, ref), to_xy)
             for ref in ("H1", "H2", "H3", "H4")]
    features = []

    def header(ref, key, label):
        fp = one(fps, ref)
        b = kicad_extract.box(fp, to_box)
        p1 = to_xy(*next((p.x, p.y) for p in fp.pads if p.number == "1"))
        features.append(dict(
            key=key, kind="header", designator=ref, label=label,
            x0=b[0], y0=b[1], x1=b[2], y1=b[3],
            note=f"Right-angle 2x20 socket; pin 1 at ({p1[0]:.2f}, "
                 f"{p1[1]:.2f}). Body overhangs the board edge."))

    header("J1", "exp1", "GPIO header J1, 2x20")
    header("J2", "exp2", "GPIO header J2, 2x20")
    for ref, key, label in (("US1", "usb_prog", "micro-USB US1, FTDI programming and console"),
                            ("US2", "usb_second", "micro-USB US2, USB host / OTG")):
        b = kicad_extract.box(one(fps, ref), to_box)
        features.append(dict(key=key, kind="usb_power" if key == "usb_prog" else "connector",
                             designator=ref, label=label,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3], note=""))
    leds = [kicad_extract.box(one(fps, f"D{n}"), to_box) for n in range(8)]
    features.append(row_feature(
        leds, key="leds", label="LEDs D0-D7", kind="led",
        note="D0 at the right-hand end.", designator="D0-D7"))
    number_features(tag, features)
    return dict(width=round(w, 3), height=round(h, 3), edges=edges,
                thickness=board.thickness, holes=holes, features=features)


BUTTERSTICK_REPO = "https://github.com/butterstick-fpga/butterstick-hardware"
BUTTERSTICK_PATH = "hardware/ButterStick_r1.0/ButterStick.kicad_pcb"
#: The last commit to touch the r1.0 board file.  Its title block still says
#: r1.0a, the revision that was sold; the commit after the r1.0a tag is a
#: net fix and a KiCad 6 re-save, and no footprint moved.
BUTTERSTICK_COMMIT = "fac6a834"


def extract_butterstick() -> dict:
    path = kicad_file("butterstick", BUTTERSTICK_COMMIT, BUTTERSTICK_PATH,
                      "butterstick-r1.0")
    board = kicad_pcb.load(str(path))
    key = "butterstick"
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints
    edges, radii = kicad_extract.outline(key, board, to_xy, w, h)
    if len(radii) != 1:
        raise SystemExit(f"{key}: expected one corner radius, got {radii}")

    holes = [kicad_extract.hole(key, one(fps, ref), to_xy) for ref in ("H1", "H2")]
    # The SYZYGY carriers each bring two plated 3.2 mm standoff holes, and
    # the maker's own acrylic plate bolts through all eight holes on the
    # board, so a plate designer needs these six as much as the two M3s.
    for ref, port in (("J3", "A"), ("J4", "B"), ("J5", "C")):
        fp = one(fps, ref)
        pads = sorted((p for p in fp.pads if p.drill and p.drill >= 3.0),
                      key=lambda p: (to_xy(p.x, p.y)[1], to_xy(p.x, p.y)[0]))
        if len(pads) != 2:
            raise SystemExit(f"{key}: {ref} has {len(pads)} standoff holes, not 2")
        for n, p in enumerate(pads, 1):
            x, y = to_xy(p.x, p.y)
            holes.append(dict(x=round(x, 3), y=round(y, 3), dia=round(p.drill, 3),
                              label=f"S{port}{n}", kind="aux",
                              keepout_dia=round(max(p.size), 3)))

    features = []

    def part(ref, key_, label, kind, note="", source="courtyard"):
        b = kicad_extract.box(one(fps, ref), to_box, source)
        features.append(dict(key=key_, kind=kind, designator=ref, label=label,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3], note=note))

    part("J1", "usb_prog", "USB-C J1, programming and console", "usb_power",
         note="Courtyard, including the shell overhang past the board edge.")
    # The MagJack footprint has no courtyard, so its pads give its extent.
    # An RJ45 body overhangs its pads; the pads are what the source has.
    part("CON1", "ethernet", "Ethernet RJ45 CON1", "ethernet",
         note="Pad extent; the footprint carries no body outline.",
         source="pads")
    for ref, key_, port in (("J3", "exp1", "A"), ("J4", "exp2", "B"), ("J5", "exp3", "C")):
        part(ref, key_, f"SYZYGY port {port}, {ref}", "connector",
             note="Fab-layer body outline.", source="fab")
    leds = [kicad_extract.box(one(fps, f"D{n}"), to_box) for n in range(1, 8)]
    features.append(row_feature(
        leds, key="rgb_leds", label="RGB LEDs D1-D7", kind="led",
        note="D1 at the left-hand end; silkscreen numbers them 0 to 6.",
        designator="D1-D7"))
    number_features(key, features)
    return dict(
        key=key, title="ButterStick", subtitle="r1.0",
        front_edge="right", thickness=board.thickness,
        width=round(w, 3), height=round(h, 3), corner_radius=radii[0],
        edges=edges, holes=holes, pmods=[], features=features,
        sources=[
            ("KiCad board file",
             f"{BUTTERSTICK_REPO}  {BUTTERSTICK_PATH} @ {BUTTERSTICK_COMMIT}",
             f"title block: {board.title} rev {board.rev}, dated {board.date}; "
             "Greg Davill / GsD"),
            ("Board size", f"{BUTTERSTICK_REPO}/blob/main/README.md",
             'quoted: "Board dimensions: 80mm x 49mm"'),
            ("Thickness",
             f"{BUTTERSTICK_REPO}/blob/main/hardware/ButterStick_r1.0/"
             "Production/ButterStick-r1.0a-fab-notes.txt",
             'quoted: "Finished board thickness is 1.6 mm."'),
        ],
        notes=[
            "Hole IDs H1 and H2 are the KiCad reference designators; SA1 to "
            "SC2 are the SYZYGY standoff holes of ports A, B and C, plated, "
            "and the maker's acrylic plate bolts through all eight.",
            "No Pmod host: expansion is three SYZYGY ports.",
        ],
    )


CYNTHION_REPO = "https://github.com/greatscottgadgets/cynthion-hardware"
CYNTHION_PATH = "cynthion.kicad_pcb"
#: The tip of the repository, which is what the ``r1.4.0`` tag points at.  The
#: release notes for that tag read "Initial production release", so it is the
#: revision that ships, and nothing has been committed since.
CYNTHION_COMMIT = "13aa71c2"
CYNTHION_TAG = "r1.4.0"
CYNTHION_RELEASE = f"{CYNTHION_REPO}/releases/tag/{CYNTHION_TAG}"
CYNTHION_LICENCE = f"{CYNTHION_REPO}/blob/{CYNTHION_TAG}/LICENSE"
CYNTHION_OVERVIEW = ("https://cynthion.readthedocs.io/en/latest/hardware/"
                     "device_overview.html")

#: The four USB ports, in the order Great Scott Gadgets' own device overview
#: introduces them, which is also the order the top-level schematic lists the
#: port sheets in.  Ordering them is the whole of the numbering decision: the
#: family had one spare USB slot and this board wants four.
CYNTHION_USB = [
    ("J2", "usb_prog", "USB-C J2, CONTROL port", "usb_power"),
    ("J1", "usb_second", "USB-C J1, AUX port", "connector"),
    ("J4", "usb_third", "USB-C J4, TARGET C port", "connector"),
    ("J3", "usb_fourth", "USB-A J3, TARGET A port", "usb_a"),
]

#: The project text variables the sheet's citation quotes.  All three are
#: required: a missing one used to read as "None" in the title block line.
CYNTHION_TITLE_VARS = ("TITLE", "VERSION", "COPYRIGHT")

#: The three side-actuated buttons.  Not drawn -- the sheet marks ports,
#: hosts, LEDs, holes and the outline -- but they are what makes the board
#: wider than its outline, so a case designer needs their reach.
CYNTHION_BUTTONS = ("SW1", "SW2", "SW3")

#: J5's numbered contacts.  Checked rather than assumed, because the label
#: calls the part 30-way and nothing else the extractor reads says so; the
#: footprint carries two mechanical posts and two unnamed pads besides.
CYNTHION_MEZZANINE_WAYS = 30


def _cynthion_top_recess(edges: list[tuple], h: float) -> tuple:
    """The notch in the top edge: opening, flat, depth, ramp run.

    Measured off the resolved outline rather than typed into a note, so the
    note cannot describe a profile the drawing does not have.  The shape is
    checked as it is measured: two floor corners at one depth, each reached
    from the edge by its own ramp, or the board has grown a profile this note
    does not cover and the extractor stops.

    The 3.0 mm window is a coincidence worth knowing about: this board's
    corner radius is 3.0 too, so ``h - 3.0`` lands exactly on the tangent
    where each corner arc leaves its side edge, and the side edges' top
    endpoints sit precisely on the window's lower bound.  Only the strict
    ``h - 3.0 < y`` keeps them out of the floor set.  Widen the window and
    they come in, the floor is four corners rather than two, and the check
    rejects a board that is perfectly ordinary.
    """
    lines = [e for e in edges if e[0] == "line"]
    floor = sorted({(round(x, 3), round(y, 3)) for e in lines
                    for x, y in ((e[1], e[2]), (e[3], e[4]))
                    if h - 3.0 < y < h - 0.001})
    if len(floor) != 2 or floor[0][1] != floor[1][1]:
        raise SystemExit(f"cynthion: the top edge recess is not two corners "
                         f"at one depth: {floor}")
    opening = sorted({round(q[0], 3) for e in lines
                      for p, q in (((e[1], e[2]), (e[3], e[4])),
                                   ((e[3], e[4]), (e[1], e[2])))
                      if (round(p[0], 3), round(p[1], 3)) in floor
                      and abs(q[1] - h) < 0.001})
    if len(opening) != 2:
        raise SystemExit(f"cynthion: the recess does not meet the top edge "
                         f"at two points: {opening}")
    runs = {round(floor[0][0] - opening[0], 3), round(opening[1] - floor[1][0], 3)}
    if len(runs) != 1:
        raise SystemExit(f"cynthion: the recess ramps are not equal: {runs}")
    return opening[0], floor[0][0], floor[1][0], opening[1], \
        round(h - floor[0][1], 3), runs.pop()


def _cynthion_title_block() -> dict:
    """The title block the board file's ``${...}`` placeholders stand for.

    Cynthion's title block is templated: the board file says ``${TITLE}`` and
    ``${VERSION}`` and the strings live in the project file's text variables.
    Reading them at the same pinned commit is what lets the sheet quote a
    title block at all, and it is how the board file itself states its own
    revision rather than the citation taking it from the tag name.

    Every variable the citation uses has to be there.  ``dict.get`` would have
    put "None" on a sheet, in the one field a reader checks to find out which
    revision they are looking at, and nothing would have complained.
    """
    project = str(Path(CYNTHION_PATH).with_suffix(".kicad_pro"))
    blob = subprocess.run(
        ["git", "-C", str(SRC / "cynthion"), "show",
         f"{CYNTHION_COMMIT}:{project}"],
        capture_output=True, text=True, check=True).stdout
    variables = json.loads(blob).get("text_variables", {})
    missing = [k for k in CYNTHION_TITLE_VARS if not variables.get(k)]
    if missing:
        raise SystemExit(
            f"cynthion: {project} @ {CYNTHION_COMMIT} has no "
            f"{', '.join(missing)} in text_variables, so the board file's "
            "title block cannot be resolved. Do not guess it.")
    return variables


def extract_cynthion() -> dict:
    path = kicad_file("cynthion", CYNTHION_COMMIT, CYNTHION_PATH,
                      f"cynthion-{CYNTHION_TAG}")
    board = kicad_pcb.load(str(path))
    key = "cynthion"
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints
    edges, radii = kicad_extract.outline(key, board, to_xy, w, h)
    if len(radii) != 1:
        raise SystemExit(f"{key}: expected one corner radius, got {radii}")

    holes = [kicad_extract.hole(key, one(fps, ref), to_xy)
             for ref in ("H1", "H2", "H3", "H4")]

    pmods = []
    for ref, label in (("J7", "A"), ("J8", "B")):
        fp = one(fps, ref)
        # The fab outline, not the courtyard: these are right-angle sockets
        # whose housing hangs off the front edge, and what a case or plate has
        # to clear is the housing, not the housing plus assembly clearance.
        pm = pmod_from_pins([to_xy(p.x, p.y) for p in fp.pads],
                            key=f"pmod_{label.lower()}", label=f"Pmod {label}",
                            designator=ref, edge="bottom",
                            body=kicad_extract.box(fp, to_box, "fab"))
        # The Pmod convention says where pin 1 is; this board file numbers its
        # own pads, so the two can be checked against each other instead of
        # the convention being asserted.  They agree.
        p1 = to_xy(*next((p.x, p.y) for p in fp.pads if p.number == "1"))
        if abs(pm["pin1_x"] - p1[0]) > 0.01 or abs(pm["pin1_y"] - p1[1]) > 0.01:
            raise SystemExit(
                f"{key}: {ref} pad 1 is at {p1}, but the Pmod convention puts "
                f"pin 1 at ({pm['pin1_x']}, {pm['pin1_y']})")
        pmods.append(pm)

    features = []
    for ref, key_, label, kind in CYNTHION_USB:
        b = kicad_extract.box(one(fps, ref), to_box, "fab")
        features.append(dict(key=key_, kind=kind, designator=ref, label=label,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3],
                             note="Fab-layer body outline, shell included."))
    # J5 is populated -- not dnp, in the BOM, on the "Expansion Interfaces"
    # schematic sheet -- so the family's first expansion slot is its, and row
    # 6 cannot go on saying the board has no expansion connector.  It is not
    # an edge port, though, which is what the other boards put in that slot,
    # so the sheet says what it is in a note.
    mez = one(fps, "J5")
    ways = len([p for p in mez.pads if p.number.isdigit()])
    if ways != CYNTHION_MEZZANINE_WAYS:
        raise SystemExit(f"{key}: J5 has {ways} numbered contacts, not "
                         f"{CYNTHION_MEZZANINE_WAYS}; the label would be "
                         "wrong")
    b = kicad_extract.box(mez, to_box, "fab")
    features.append(dict(
        key="exp1", kind="connector", designator="J5",
        label=f"Mezzanine receptacle J5, {ways}-way",
        x0=b[0], y0=b[1], x1=b[2], y1=b[3],
        note="Fab-layer body outline. Board-to-board receptacle on the "
             f"component side, footprint {mez.library_id}."))
    features.append(row_feature(
        [kicad_extract.box(one(fps, f"D{n}"), to_box) for n in range(2, 8)],
        key="leds", label="User LEDs D2-D7", kind="led", designator="D2-D7",
        note="D2 at the left-hand end; the FPGA drives them."))
    features.append(row_feature(
        [kicad_extract.box(one(fps, f"D{n}"), to_box) for n in range(10, 15)],
        key="status_leds", label="Status LEDs D10-D14", kind="led",
        designator="D10-D14",
        note="D10 at the left-hand end; the debug controller drives them."))
    number_features(key, features)

    # The assembled envelope, worked out here rather than left to the sheet.
    # The sheet's figure is built from the features, and the Pmod hosts are
    # not features -- they have a table of their own -- so on this board it
    # would be 8.07 mm short in Y, which is most of what a case has to clear.
    # The buttons are not features either and are what makes the board wider
    # than its outline, so they are measured and given separately: one number
    # a reader cannot take apart is no use to someone cutting a front panel.
    buttons = [kicad_extract.box(one(fps, ref), to_box, "fab")
               for ref in CYNTHION_BUTTONS]
    parts = [(f["x0"], f["y0"], f["x1"], f["y1"]) for f in features]
    parts += [(p["body_x0"], p["body_y0"], p["body_x1"], p["body_y1"])
              for p in pmods]
    ex0 = min([0.0] + [p[0] for p in parts])
    ex1 = max([w] + [p[2] for p in parts])
    ey0 = min([0.0] + [p[1] for p in parts])
    ey1 = max([h] + [p[3] for p in parts])
    cx0 = min([ex0] + [b[0] for b in buttons])
    cx1 = max([ex1] + [b[2] for b in buttons])
    cy0 = min([ey0] + [b[1] for b in buttons])
    cy1 = max([ey1] + [b[3] for b in buttons])
    envelope = (
        "Assembled envelope, connector overhang and the Pmod housings "
        f"included: {ex1 - ex0:.2f} x {ey1 - ey0:.2f} mm. With the three "
        f"side buttons as well it is {cx1 - cx0:.2f} x {cy1 - cy0:.2f} mm, "
        "which is what a case has to clear.")
    left = -min(b[0] for b in buttons)
    right = max(b[2] for b in buttons) - w

    o0, f0, f1, o1, depth, run = _cynthion_top_recess(edges, h)
    profile_note = (
        f"The top edge carries a recess {depth:.2f} mm deep, flat from "
        f"x = {f0:.2f} to {f1:.2f}, each end ramping {run:.2f} back to the "
        f"edge at x = {o0:.2f} and {o1:.2f}. The board file gives no purpose "
        "for it.")

    tb = _cynthion_title_block()
    return dict(
        key=key, title="Cynthion", subtitle=CYNTHION_TAG,
        front_edge="bottom", thickness=board.thickness,
        width=round(w, 3), height=round(h, 3), corner_radius=radii[0],
        edges=edges, holes=holes, pmods=pmods, features=features,
        envelope_note=envelope, profile_note=profile_note,
        sources=[
            ("KiCad board file",
             f"{CYNTHION_REPO}  {CYNTHION_PATH} @ {CYNTHION_COMMIT} "
             f"(tag {CYNTHION_TAG})",
             f"title block: {tb['TITLE']} rev {tb['VERSION']}, "
             f"{tb['COPYRIGHT']}, resolved from the project file's text "
             "variables at the same commit; Great Scott Gadgets."),
            ("Revision sold", CYNTHION_RELEASE,
             f'the {CYNTHION_TAG} release notes read "Initial production '
             'release."; it is the newest release and the tip of the '
             "repository, and no commit since has touched the board file."),
            ("Licence", CYNTHION_LICENCE,
             "CERN Open Hardware Licence Version 2 - Permissive, "
             "Copyright (c) 2019-2024 Great Scott Gadgets."),
            ("Ports and indicators", CYNTHION_OVERVIEW,
             "names the four USB ports CONTROL, AUX, TARGET C and TARGET A, "
             "in that order; six user LEDs driven by the FPGA and five "
             "status LEDs driven by the debug microcontroller."),
        ],
        notes=[
            "Every dimension is read from the board file; Great Scott "
            "Gadgets publish no mechanical drawing. Hole IDs are the KiCad "
            "reference designators.",
            "Schedule numbers 9, 10 and 11 were added to the family for this "
            "board. 1 to 8 mean what they mean on the other FPGA sheets, so "
            "the four USB ports read 1, 2, 9, 10.",
            "No Ethernet jack.",
            "Feature 6, J5, is a surface-mount mezzanine receptacle on the "
            "component side: a board-to-board expansion socket well inside "
            "the outline, not an edge port like the expansion connectors on "
            "the other sheets.",
            "Pmod A and B are right-angle sockets: the pin field is on the "
            "board and the housing hangs off the front edge, so a peripheral "
            "plugs in level with the board rather than standing up from it. "
            f"The housings reach {-min(p['body_y0'] for p in pmods):.2f} mm "
            "past the edge.",
            "The board ships inside an enclosure. The outline drawn is the "
            "bare PCB's; the repository publishes no case dimensions.",
            "Buttons PROGRAM and USER on the left edge and RESET on the "
            "right are not drawn. They are side-actuated tactile switches "
            f"whose bodies reach {left:.2f} mm past the left edge and "
            f"{right:.2f} mm past the right.",
        ],
    )


# ---------------------------------------------------------------------------
# Icepi Zero: KiCad, read at two commits of one revision
# ---------------------------------------------------------------------------

ICEPI_REPO = "https://github.com/cheyao/icepi-zero"
ICEPI_PATH = "hardware/v1.3/icepi-zero.kicad_pcb"
#: The tag whose commit is "Final mass production files".  v1.3 is the
#: revision that was made in quantity and sold, and the only one the
#: repository tags: v1.0 to v1.2 are the prototypes the maker's JOURNAL.md
#: describes, and v1.4 is marked work in progress.  The tag is resolved at
#: extraction and required to be the commit below, so that a moved tag is an
#: error here rather than a sheet quietly citing a different board.
ICEPI_TAG = "v1.3"
ICEPI_COMMIT = "6e4aaba2"
#: The same v1.3 board later in its history: re-saved in KiCad 10 and
#: re-annotated, so two of the three USB-C receptacles swapped designators
#: and three of the five user LEDs were renumbered.  It is read only to require that nothing
#: moved, which is what lets this sheet keep the designators the boards were
#: fabbed with and say in a note that the later file disagrees.
ICEPI_RESPIN = "d67bb758"
ICEPI_README = f"{ICEPI_REPO}/blob/v1.3/README.md"
ICEPI_BOM = f"{ICEPI_REPO}/blob/v1.3/hardware/v1.3/production/bom.csv"
ICEPI_RELEASE = f"{ICEPI_REPO}/releases/tag/v1.3"

RPI_ZERO_DRAWING = ("https://datasheets.raspberrypi.com/rpizero/"
                    "raspberry-pi-zero-mechanical-drawing.pdf")
#: The Raspberry Pi Zero's own figures, read off drawing RPI-ZERO-V1_2: the
#: board, its corner radius, the M2.5 drill, and the hole pattern as both the
#: inset from each edge and the span between centres.  The board file is what
#: this sheet draws; these are here so the note claiming the Pi Zero pattern
#: is checked against the drawing it cites, rather than asserted from memory.
#: Both the inset and the span are kept although either implies the other on
#: a board of this size, because the note states both and a note states only
#: what has been checked.
RPI_ZERO = dict(width=65.0, height=30.0, radius=3.0, inset=3.5,
                span_x=58.0, span_y=23.0, drill=2.75, drill_tol=0.05)


def _icepi_net(pad) -> str:
    """The net name on a pad node.

    KiCad 9 writes ``(net 12 "/LED0")`` and KiCad 10 ``(net "/LED0")``, so the
    name is the last atom rather than a fixed index.  Both spellings turn up
    here: the two commits read are on either side of that change.
    """
    node = kicad_pcb.child(pad, "net")
    return node[-1] if node and isinstance(node[-1], str) else ""


def _icepi_nets(board) -> dict[str, dict[str, str]]:
    """Reference designator -> pad number -> net name."""
    out: dict[str, dict[str, str]] = {}
    for node in kicad_pcb.children(board.tree, "footprint"):
        ref = next((p[2] for p in kicad_pcb.children(node, "property")
                    if len(p) > 2 and p[1] == "Reference"), "")
        out[ref] = {str(pad[1]): _icepi_net(pad)
                    for pad in kicad_pcb.children(node, "pad")}
    return out


def _icepi_parts(key: str, board) -> dict:
    """Everything this sheet draws, found by what a part is rather than named.

    Nothing here is looked up by reference designator, because the Icepi's
    are not stable: between the two commits read, two of the three USB-C
    receptacles swapped designators and three of the five user LEDs were
    renumbered, the programming port among them.  So the
    programming port is the receptacle sharing the FTDI's data pair, a user
    LED is one a resistor drives from ``/LED0`` to ``/LED4``, and the rest
    are found by footprint.  The same function then reads both commits and
    the two are required to agree on every box.
    """
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints
    nets = _icepi_nets(board)
    edges, radii = kicad_extract.outline(key, board, to_xy, w, h)
    if radii != [3.5]:
        raise SystemExit(f"{key}: corner radii {radii}, not one R3.5")

    # Mounting holes: every drill of 2 mm or more, so a revision that gained
    # or lost one could not be drawn as though it had four.
    mounts = [fp for fp in fps
              if any(p.drill and p.drill >= 2.0 for p in fp.pads)]
    if len(mounts) != 4:
        raise SystemExit(f"{key}: {len(mounts)} drills of 2 mm or more, not 4")
    holes = sorted((kicad_extract.hole(key, fp, to_xy) for fp in mounts),
                   key=lambda hl: (hl["y"], hl["x"]))
    # One drill goes into the note, so all four have to be that drill.
    drills = {hl["dia"] for hl in holes}
    if len(drills) != 1:
        raise SystemExit(f"{key}: the four mounting holes are drilled "
                         f"{sorted(drills)}, and the note gives one figure")

    def only(what: str, hits: list):
        if len(hits) != 1:
            raise SystemExit(f"{key}: {len(hits)} {what}, not 1")
        return hits[0]

    def by_footprint(pattern: str) -> list:
        return [fp for fp in fps if pattern.lower() in fp.library_id.lower()]

    parts: dict[str, dict] = {}

    def part(role: str, fp) -> None:
        parts[role] = dict(ref=fp.reference, box=kicad_extract.box(fp, to_box))

    # The three USB-C receptacles, and which of them the FTDI hangs off: the
    # board's own README says the converter is on board, and the sheet has to
    # say which port to plug the cable into.
    usb = sorted(by_footprint("USB_C_Receptacle"),
                 key=lambda fp: fp.x)
    if len(usb) != 3:
        raise SystemExit(f"{key}: {len(usb)} USB-C receptacles, not 3")
    ftdi = only("FT231X", [fp for fp in fps if fp.fp_value == "FT231XQ"])
    ftdi_nets = {n for n in nets[ftdi.reference].values()
                 if n and n not in ("GND", "+5V")}
    wired = [fp for fp in usb
             if ftdi_nets & {n for n in nets[fp.reference].values() if n}]
    if len(wired) != 1:
        raise SystemExit(f"{key}: {len(wired)} receptacles share the FTDI's "
                         "data pair, not 1")
    part("usb_prog", wired[0])
    for n, fp in enumerate(fp for fp in usb if fp is not wired[0]):
        part(f"usb_fpga{n}", fp)

    part("gpdi", only("GPDI connector", by_footprint("A71-05H4")))
    part("microsd", only("microSD socket", by_footprint("microSD")))
    gpio = only("2x20 GPIO header", by_footprint("PinHeader_2x20_P2.54mm"))
    part("gpio", gpio)
    pin1 = to_xy(*next((p.x, p.y) for p in gpio.pads if p.number == "1"))
    parts["gpio"]["pin1"] = (round(pin1[0], 3), round(pin1[1], 3))
    # The position is only worth calling a Raspberry Pi header if its pins
    # are where a Pi puts them, so the note that says so is checked here
    # against the pins that fix the orientation: the two 5 V pins, the 3V3 at
    # pin 1, the first two GPIOs and every ground.
    pi_pins = {"1": "+3V3", "2": "+5V", "3": "/GPIO2", "4": "+5V",
               "5": "/GPIO3", **{str(n): "GND" for n in
                                 (6, 9, 14, 20, 25, 30, 34, 39)}}
    wrong = {n: nets[gpio.reference].get(n) for n, want in pi_pins.items()
             if nets[gpio.reference].get(n) != want}
    if wrong:
        raise SystemExit(f"{key}: the 2x20 header is not on the Raspberry Pi "
                         f"pinout the note claims: {wrong}")

    # The user LEDs: each is driven through a series resistor from a net the
    # maker's own constraints file calls led[0] to led[4].  Found this way
    # rather than by designator, the row comes out in LED order whichever
    # commit is being read, and the red FTDI activity LED beside the
    # programming port cannot be mistaken for one of them.
    for fp in fps:
        pads = nets.get(fp.reference, {})
        anodes = [n for n in pads.values() if n and n != "GND"]
        if fp.fp_value != "WHITE" or len(pads) != 2 or len(anodes) != 1:
            continue
        driven = [n for ref, other in nets.items() if ref != fp.reference
                  and anodes[0] in other.values()
                  for n in other.values() if n and n != anodes[0]]
        for n in driven:
            if n.startswith("/LED"):
                part(f"led{int(n[4:])}", fp)
    leds = [r for r in parts if r.startswith("led")]
    if sorted(leds) != [f"led{n}" for n in range(5)]:
        raise SystemExit(f"{key}: user LEDs found: {sorted(leds)}, not LED0-4")
    # "LED0 at the left-hand end" is on the sheet, so it is checked here: the
    # five have to run LED0 to LED4 in increasing x, not merely be five LEDs.
    xs = [(parts[f"led{n}"]["box"][0] + parts[f"led{n}"]["box"][2]) / 2
          for n in range(5)]
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise SystemExit(f"{key}: LED0 to LED4 are not left to right: {xs}")

    buttons = sorted(by_footprint("switch_button"),
                     key=lambda fp: -fp.y)
    if len(buttons) != 2:
        raise SystemExit(f"{key}: {len(buttons)} push buttons, not 2")
    for n, fp in enumerate(buttons):
        if fp.layer != "B.Cu":
            raise SystemExit(f"{key}: button {fp.reference} is on {fp.layer}; "
                             "the note says both are on the underside")
        part(f"button{n}", fp)

    return dict(width=round(w, 3), height=round(h, 3), edges=edges,
                radius=radii[0], thickness=board.thickness, holes=holes,
                parts=parts)


def extract_icepi_zero() -> dict:
    key = "icepi-zero"
    # The checkout first: it is where a missing clone is reported in words,
    # and a rev-parse on a clone that is not there is a traceback instead.
    path = kicad_file("icepi-zero", ICEPI_COMMIT, ICEPI_PATH, "icepi-zero-v1.3")
    # The tag is what the citation names and the commit is what is read, so
    # the two are required to be the same object.  ULX3S resolves its tags
    # the same way, for the same reason: a tag that moved would otherwise
    # change the sheet's provenance without changing the sheet.
    named = subprocess.run(
        ["git", "-C", str(SRC / "icepi-zero"), "rev-parse",
         f"--short={len(ICEPI_COMMIT)}", f"{ICEPI_TAG}^{{commit}}"],
        capture_output=True, text=True, check=True).stdout.strip()
    if named != ICEPI_COMMIT:
        raise SystemExit(f"{key}: tag {ICEPI_TAG} is {named}, not "
                         f"{ICEPI_COMMIT}; the pin and the citation disagree")
    board = kicad_pcb.load(str(path))
    if board.rev != ICEPI_TAG:
        raise SystemExit(f"{key}: the pinned file is rev {board.rev}, not "
                         f"{ICEPI_TAG}")
    got = _icepi_parts(key, board)

    # The same revision later in its history.  Everything drawn has to be in
    # the same place, or the sheet covers one spin of v1.3 and not the other
    # and has to say which.
    respin = _icepi_parts(key + " respin", kicad_pcb.load(str(kicad_file(
        "icepi-zero", ICEPI_RESPIN, ICEPI_PATH, "icepi-zero-v1.3-respin"))))
    for field in ("width", "height", "radius", "thickness"):
        if got[field] != respin[field]:
            raise SystemExit(f"{key}: the re-annotated v1.3 differs in {field}")
    # The outline as a set: KiCad 10 wrote the same eight edges out in a
    # different order, which is a re-save and not a change of shape.
    if sorted(got["edges"]) != sorted(respin["edges"]):
        raise SystemExit(f"{key}: the re-annotated v1.3 changed the outline")
    if [dict(h, label="") for h in got["holes"]] != \
            [dict(h, label="") for h in respin["holes"]]:
        raise SystemExit(f"{key}: the re-annotated v1.3 moved a mounting hole")
    for role, rec in got["parts"].items():
        if rec["box"] != respin["parts"][role]["box"]:
            raise SystemExit(f"{key}: the re-annotated v1.3 moved {role}")
    # Pin 1 of the GPIO position is a note, not a box, so it is compared
    # separately: a header rotated half a turn between the two files would
    # keep the same courtyard and put the note's corner at the far end.
    if got["parts"]["gpio"]["pin1"] != respin["parts"]["gpio"]["pin1"]:
        raise SystemExit(f"{key}: the re-annotated v1.3 moved pin 1 of the "
                         "GPIO position")

    p = got["parts"]
    w, h = got["width"], got["height"]
    features = []

    def part(role, key_, label, kind, note=""):
        rec = p[role]
        features.append(dict(key=key_, kind=kind, designator=rec["ref"],
                             label=label.format(ref=rec["ref"]),
                             x0=rec["box"][0], y0=rec["box"][1],
                             x1=rec["box"][2], y1=rec["box"][3], note=note))

    part("usb_prog", "usb_prog",
         "USB-C {ref}, JTAG and console", "usb_power",
         note="Courtyard, including the shell overhang past the board edge. "
              "The receptacle wired to the on-board FT231X.")
    pair = [p["usb_fpga0"], p["usb_fpga1"]]
    features.append(row_feature(
        [rec["box"] for rec in pair], key="usb_second", kind="connector",
        label="USB-C {} and {}, to the FPGA".format(*(r["ref"] for r in pair)),
        designator=", ".join(r["ref"] for r in pair),
        note="Courtyards, shell overhang included; two separate receptacles "
             "with 1.86 mm of board between them."))
    leds = [p[f"led{n}"] for n in range(5)]
    features.append(row_feature(
        [rec["box"] for rec in leds], key="leds", kind="led",
        label="User LEDs LED0-LED4", designator=", ".join(r["ref"] for r in leds),
        note="LED0 at the left-hand end. Courtyards of the 0603 bodies."))
    part("gpio", "exp1", "GPIO header {ref}, 2x20, not fitted", "header",
         note="Courtyard of the unfitted 2x20 position.")
    part("gpdi", "exp2", "GPDI video connector {ref}", "connector",
         note="Courtyard; the body overhangs the board edge.")
    part("microsd", "exp3", "microSD card socket {ref}", "connector",
         note="Courtyard. A card in the socket stands proud of the left edge; "
              "the source gives no figure for it.")
    number_features(key, features)

    hx = sorted({hl["x"] for hl in got["holes"]})
    hy = sorted({hl["y"] for hl in got["holes"]})
    drill = got["holes"][0]["dia"]
    # Everything the Pi Zero note states, checked: the board, all four insets
    # -- not just the two nearest the datum, which leaves the pattern free to
    # slide off the far edges -- and the span between centres on both axes.
    want = [RPI_ZERO["width"], RPI_ZERO["height"]] + [RPI_ZERO["inset"]] * 4 \
        + [RPI_ZERO["span_x"], RPI_ZERO["span_y"]]
    have = [w, h, hx[0], w - hx[-1], hy[0], h - hy[-1],
            hx[-1] - hx[0], hy[-1] - hy[0]]
    if [round(v, 3) for v in have] != want:
        raise SystemExit(f"{key}: the board is no longer the Pi Zero outline "
                         f"and hole pattern the note claims: {have} against "
                         f"{want}")
    gpio_pin1 = p["gpio"]["pin1"]
    buttons = [p["button0"], p["button1"]]
    return dict(
        key=key, title="Icepi Zero", subtitle="v1.3, Raspberry Pi Zero form factor",
        front_edge="bottom", thickness=got["thickness"],
        width=w, height=h, corner_radius=got["radius"],
        edges=got["edges"], holes=got["holes"], pmods=[], features=features,
        sources=[
            ("KiCad board file",
             f"{ICEPI_REPO}  {ICEPI_PATH} @ {ICEPI_COMMIT} (tag {ICEPI_TAG})",
             f"title block: {board.title} rev {board.rev}, dated {board.date}; "
             f"{board.company}. Solderpad Hardware Licence 2.1."),
            ("Board revision", ICEPI_RELEASE,
             f'the {ICEPI_TAG} tag, "Final mass production files": the '
             "revision made in quantity and sold. The same board file later "
             f"in its history, at {ICEPI_RESPIN}, is read too and agrees on "
             "every position drawn here."),
            ("Board size", ICEPI_README,
             'quoted at this tag: "Icepi Zero is an FPGA development board '
             'in the popular Raspberry Pi Zero form factor"; the board file '
             f"gives {w:.2f} x {h:.2f} mm."),
            ("Assembly", ICEPI_BOM,
             "the production bill of materials at the same tag lists no "
             "2x20 header: the GPIO position is not fitted."),
            ("Form factor compared", RPI_ZERO_DRAWING,
             "Raspberry Pi Zero, RPI-ZERO-V1_2 of 2015-09-23: 65 x 30 mm, "
             "corner radius 3.0, 4x M2.5 mounting holes drilled to 2.75 "
             "+/-0.05, 58 x 23 apart and 3.5 in from each edge."),
        ],
        notes=[
            "Hole IDs are the KiCad reference designators.",
            f"The mounting holes are the Raspberry Pi Zero pattern: "
            f"{hx[-1] - hx[0]:.2f} x {hy[-1] - hy[0]:.2f} mm, "
            f"{RPI_ZERO['inset']:.2f} mm in from each edge of a {w:.0f} x "
            f"{h:.0f} board. They are drilled {drill:.2f}, the bottom of "
            f"the Pi Zero drawing's {RPI_ZERO['drill']:.2f} +/-"
            f"{RPI_ZERO['drill_tol']:.2f} band; the corners are R"
            f"{got['radius']:.2f} where the Pi Zero's are "
            f"R{RPI_ZERO['radius']:.2f}.",
            "No Pmod host and no Ethernet jack.",
            "The unfitted GPIO position is a Raspberry Pi 40-pin header: "
            "1.00 mm holes on a 2.54 mm grid, with the Pi's 5 V, 3V3 and "
            f"first GPIO pins in the Pi's places and pin 1 at "
            f"({gpio_pin1[0]:.2f}, {gpio_pin1[1]:.2f}), in the row farther "
            "from the board edge.",
            "The two user buttons are on the underside, centred at "
            + " and ".join(f"({(r['box'][0] + r['box'][2]) / 2:.2f}, "
                           f"{(r['box'][1] + r['box'][3]) / 2:.2f})"
                           for r in buttons)
            + "; a plate under the board has to clear them.",
            "The board file has been re-annotated since the mass-production "
            f"release. Nothing drawn here moved, but at {ICEPI_RESPIN} the "
            f"programming port is {respin['parts']['usb_prog']['ref']} and "
            "the user LEDs run D1 to D5 left to right; the designators here "
            "are the ones the sold boards were fabbed with.",
        ],
    )


# ---------------------------------------------------------------------------
# PYNQ-Z2: STEP assembly
# ---------------------------------------------------------------------------

PYNQ_STEP = SRC / "pynq" / "PYNQ_Z2_20220218" / "PYNQ_Z2_20220218.STEP"
PYNQ_THREAD = "https://discuss.pynq.io/t/pynq-z2-pcb-3d-step-files/2645"
PYNQ_MANUAL = "https://dpoauwgwqsy2x.cloudfront.net/Download/PYNQ_Z2_User_Manual_v1.1.pdf"


def extract_pynq_z2() -> dict:
    from tools import step_model
    if not PYNQ_STEP.exists():
        raise SystemExit(f"missing {PYNQ_STEP}; run tools/fetch_fpga.sh")
    key = "pynq-z2"
    model = step_model.load(str(PYNQ_STEP))
    board = model.largest()
    z0, z1 = model.slab(board)
    _, (bx0, by0, bx1, by1) = model.top_face(board)
    w, h = bx1 - bx0, by1 - by0

    def to_xy(x, y):
        return x - bx0, y - by0

    def to_box(b):
        return (round(b[0] - bx0, 3), round(b[1] - by0, 3),
                round(b[2] - bx0, 3), round(b[3] - by0, 3))

    edges = []
    for x1_, y1_, x2_, y2_ in model.outline_edges(board):
        a, b = to_xy(x1_, y1_), to_xy(x2_, y2_)
        edges.append(("line", round(a[0], 3), round(a[1], 3),
                      round(b[0], 3), round(b[1], 3)))
    if len(edges) != 4:
        raise SystemExit(f"{key}: outline has {len(edges)} edges, not 4")

    holes = []
    for c in model.through_holes(board, 3.3, 3.5):
        x, y = to_xy(c.x, c.y)
        holes.append(dict(x=round(x, 3), y=round(y, 3), dia=round(c.dia, 3),
                          kind="mount", keepout_dia=None))
    if len(holes) != 4:
        raise SystemExit(f"{key}: {len(holes)} holes of 3.4 mm, not 4")
    holes.sort(key=lambda h_: (h_["y"], h_["x"]))
    for i, h_ in enumerate(holes, 1):
        h_["label"] = f"MT{i}"

    # The Pmod pin holes: 1.524 mm, in the right-hand strip of the board,
    # two columns 2.54 mm apart.  Other 1.524 mm holes sit in that strip too
    # (the Raspberry Pi header's neighbours), so the two columns are picked
    # by the exact x the twelve-hole groups share.
    pins = [(round(c.x, 3), round(c.y, 3))
            for c in model.through_holes(board, 1.5, 1.55)
            if c.x > bx1 - 15.0]
    columns = sorted({p[0] for p in pins})
    pairs = [(a, b) for a in columns for b in columns
             if abs((b - a) - PMOD_PITCH) < 0.01]
    fields = []
    for a, b in pairs:
        ys = sorted({p[1] for p in pins if p[0] in (a, b)})
        # Split the y values into runs on 2.54 mm.
        run = [ys[0]]
        for y in ys[1:]:
            if abs(y - run[-1] - PMOD_PITCH) < 0.01:
                run.append(y)
            else:
                if len(run) == PMOD_COLUMNS:
                    fields.append((a, b, run))
                run = [y]
        if len(run) == PMOD_COLUMNS:
            fields.append((a, b, run))
    if len(fields) != 2:
        raise SystemExit(f"{key}: found {len(fields)} Pmod pin fields, not 2")
    bodies = model.named("6x1 2.54 PinH-M_R")
    pmods = []
    # Pmod A is the upper of the two on the right edge, per the manual's
    # photograph (section 16); the model does not name them.
    for (a, b, ys), (label, designator) in zip(
            sorted(fields, key=lambda f: -f[2][0]), (("A", "JA"), ("B", "JB"))):
        points = [to_xy(x, y) for x in (a, b) for y in ys]
        mine = [s for s in bodies if s.y0 < ys[0] < s.y1 or s.y0 < ys[-1] < s.y1]
        if len(mine) != 2:
            raise SystemExit(f"{key}: Pmod {label} matched {len(mine)} body solids")
        body = to_box((min(s.x0 for s in mine), min(s.y0 for s in mine),
                       max(s.x1 for s in mine), max(s.y1 for s in mine)))
        pmods.append(pmod_from_pins(points, key=f"pmod_{label.lower()}",
                                    label=f"Pmod {label}", designator=designator,
                                    edge="right", body=body))

    def union(name):
        solids = model.named(name)
        if not solids:
            raise SystemExit(f"{key}: no solid named {name!r} in the model")
        return to_box((min(s.x0 for s in solids), min(s.y0 for s in solids),
                       max(s.x1 for s in solids), max(s.y1 for s in solids)))

    features = []
    for name, key_, label, kind in (
            ("Micro USB", "usb_prog", "micro-USB, programming and console", "usb_power"),
            ("USB-A-20", "usb_second", "USB type A host port", "usb_a"),
            ("RT7-174A-XXXX-10PIN", "ethernet", "Ethernet RJ45", "ethernet")):
        b = union(name)
        features.append(dict(key=key_, kind=kind, designator="", label=label,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3],
                             note=f'Model part "{name}", every solid of it.'))
    number_features(key, features)
    return dict(
        key=key, title="TUL PYNQ-Z2", subtitle="137 x 87 mm",
        front_edge="right", thickness=round(z1 - z0, 3),
        width=round(w, 3), height=round(h, 3), corner_radius=0.0,
        edges=edges, holes=holes, pmods=pmods, features=features,
        sources=[
            ("3D model", PYNQ_THREAD,
             "PYNQ_Z2_20220218.STEP, TUL's SolidWorks export of 2022-02-18 "
             "posted by Xilinx; the earlier model on the same thread has the "
             "Pmod spacing wrong and is not used."),
            ("User manual", PYNQ_MANUAL,
             "v1.1: Pmod A is the upper host (section 16); 4 LEDs and 2 "
             "tri-colour LEDs (section 14)."),
        ],
        notes=[
            "Every dimension is read from the STEP model; TUL publish no "
            "drawing. Hole IDs are assigned by this drawing.",
            "The user LEDs LD0-LD3 and the two tri-colour LEDs are not in "
            "the model, so schedule rows 4 and 5 are empty; the board has "
            "them, above the four push buttons near the lower edge.",
            "TUL's product sheet gives the board as 87 x 140 mm; the "
            "model's laminate is 137.0 wide and the Pmod hosts reach 1.2 "
            "beyond it.",
        ],
    )


# ---------------------------------------------------------------------------
# Arty A7: Digilent's DXF and its PDF plot
# ---------------------------------------------------------------------------

ARTY_DIR = SRC / "arty_a7" / "mechanical_drawing" / "Arty A7"
ARTY_DXF = ARTY_DIR / "Arty_A7_DXF.DXF"
ARTY_PDF = ARTY_DIR / "Mechanical_Arty_A7.pdf"
ARTY_ZIP = ("https://digilent.com/reference/_media/reference/"
            "programmable-logic/arty-a7/arty_a7.zip")
ARTY_CAD = ("https://digilent.com/reference/_media/reference/"
            "programmable-logic/arty/arty_revc_cad.zip")
ARTY_RM = "https://digilent.com/reference/programmable-logic/arty-a7/reference-manual"
ARTY_FORUM = "https://forum.digilent.com/topic/4523-410-319-mounting/"

#: Where the Rev C 3D model puts the eight user LEDs, as the rough position
#: the PDF's outlines are matched against.  The model is of the Avnet-era
#: Arty Rev C, whose outline differs from the A7 drawing by a fraction of a
#: millimetre, so it identifies the parts and the A7 plot supplies the
#: numbers.  The full-size 1.6 x 1.6 row nearest the edge is the tri-colour
#: LD0-LD3; the 0603 row behind it is LD4-LD7.
ARTY_LED_ROWS = {
    "rgb_leds": (3.988, (1.6, 1.6)),
    "leds": (10.16, (1.6, 0.8)),
}
ARTY_LED_X = [9.017 + n * 6.985 for n in range(4)]


def _arty_dxf():
    import ezdxf
    doc = ezdxf.readfile(str(ARTY_DXF))
    msp = doc.modelspace()
    keep = [(e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y)
            for e in msp if e.dxftype() == "LINE" and e.dxf.layer == "KeepOutLayer"]
    xs = [c for s in keep for c in (s[0], s[2])]
    ys = [c for s in keep for c in (s[1], s[3])]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    # Every keep-out line has to lie on the rectangle's boundary, or the
    # layer holds something other than the outline.  The file carries about
    # fifteen microns of unit-conversion noise on every coordinate.
    for ax, ay, bx, by in keep:
        on = all(abs(x - x0) < 1e-3 or abs(x - x1) < 1e-3
                 or abs(y - y0) < 1e-3 or abs(y - y1) < 1e-3
                 for x, y in ((ax, ay), (bx, by)))
        if not on:
            raise SystemExit("arty-a7: KeepOutLayer is not just the outline")
    circles = [(e.dxf.center.x - x0, e.dxf.center.y - y0, 2 * e.dxf.radius)
               for e in msp if e.dxftype() == "CIRCLE" and e.dxf.layer == "PadHoleLayer"]
    slots = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "PadHoleLayer":
            pts = [(p[0] - x0, p[1] - y0) for p in e.get_points("xy")]
            sx = [p[0] for p in pts]
            sy = [p[1] for p in pts]
            if max(sx) - min(sx) > 0.1 and max(sy) - min(sy) > 0.1:
                slots.append((min(sx), min(sy), max(sx), max(sy)))
    return (x1 - x0, y1 - y0), circles, slots


def _arty_pdf(width: float, height: float):
    """Component outlines from the PDF plot, in board millimetres.

    The plot's scale is taken from the board outline, per axis: the two
    longest horizontal and vertical lines on the page are the outline, and
    they measure the DXF's 109.0 x 87.0 to within a quarter of a percent.
    The axes are scaled separately because they disagree by that much, and
    the result is checked against the DXF where the two overlap.
    """
    import pdfplumber
    page = pdfplumber.open(str(ARTY_PDF)).pages[0]
    raw = []
    for obj in page.lines:
        pts = obj["pts"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            raw.append((ax, page.height - ay, bx, page.height - by))
    # Dimension extension lines run past the outline, so the outline is the
    # largest closed rectangle on the page with the board's own aspect ratio.
    boxes = [r for r in rectangles(raw)
             if abs((r[2] - r[0]) / (r[3] - r[1]) / (width / height) - 1) < 0.01]
    if not boxes:
        raise SystemExit("arty-a7: could not find the board outline in the PDF")
    x_lo, y_lo, x_hi, y_hi = max(boxes, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    sx = width / (x_hi - x_lo)
    sy = height / (y_hi - y_lo)
    if abs(sx / sy - 1.0) > 0.005:
        raise SystemExit(f"arty-a7: PDF axes disagree by {sx / sy:.4f}")
    segs = [((s[0] - x_lo) * sx, (s[1] - y_lo) * sy,
             (s[2] - x_lo) * sx, (s[3] - y_lo) * sy) for s in raw]
    return rectangles(segs), sx / sy


def _pick(rects, key, centre, size, tol_pos=0.6, tol_size=0.4):
    cx, cy = centre
    w, h = size
    hits = [r for r in rects
            if abs((r[0] + r[2]) / 2 - cx) < tol_pos
            and abs((r[1] + r[3]) / 2 - cy) < tol_pos
            and abs((r[2] - r[0]) - w) < tol_size
            and abs((r[3] - r[1]) - h) < tol_size]
    if not hits:
        raise SystemExit(f"arty-a7 {key}: no outline near {centre} sized {size}")
    # The largest of the near-identical readings: a body drawn with tabs or
    # a shell is bounded by its outermost lines.
    hits.sort(key=lambda r: -((r[2] - r[0]) * (r[3] - r[1])))
    return tuple(round(v, 3) for v in hits[0])


def extract_arty() -> dict:
    if not ARTY_DXF.exists():
        raise SystemExit(f"missing {ARTY_DXF}; run tools/fetch_fpga.sh")
    key = "arty-a7"
    (w, h), circles, slots = _arty_dxf()
    rects, aniso = _arty_pdf(w, h)

    # Pmod pin fields: the 1.067 mm pad holes within 15 mm of the top edge,
    # split into groups along x.
    pins = sorted((x, y) for x, y, d in circles if abs(d - 1.067) < 0.01 and y > h - 15)
    groups: list[list] = []
    for p in pins:
        if groups and p[0] - groups[-1][-1][0] < PMOD_PITCH + 0.1:
            groups[-1].append(p)
        else:
            groups.append([p])
    groups = [g for g in groups if len(g) == 12]
    if len(groups) != 4:
        raise SystemExit(f"{key}: found {len(groups)} Pmod pin fields, not 4")
    pmods = []
    row_gap = None
    for g, label in zip(groups, ("JA", "JB", "JC", "JD")):
        cx = (min(p[0] for p in g) + max(p[0] for p in g)) / 2
        ys = sorted({p[1] for p in g})
        row_gap = ys[-1] - ys[0]
        body = _pick(rects, f"pmod {label}", (cx, h - 6.8), (15.24, 13.56),
                     tol_pos=1.0)
        # The plot and the drawing have to agree on where the host is.
        if abs((body[0] + body[2]) / 2 - cx) > 0.1:
            raise SystemExit(f"{key}: PDF body of {label} is off its DXF pins")
        # Rows 2.50 apart, not 2.54: the field rule allows 0.05, so the
        # drawing's own figures go through and a note says so.
        pm = pmod_from_pins(g, key=f"pmod_{label.lower()}", label=label,
                            designator=label, edge="top", body=body)
        pmods.append(pm)

    # RJ45: pegs of 1.575 mm fix its centre line on the DXF; the body is
    # the PDF's.
    pegs = [(x, y) for x, y, d in circles if abs(d - 1.575) < 0.01]
    if len(pegs) != 2:
        raise SystemExit(f"{key}: {len(pegs)} RJ45 pegs, not 2")
    rj_cy = sum(p[1] for p in pegs) / 2
    rj = _pick(rects, "rj45", (13.0, rj_cy), (26.3, 18.8), tol_pos=1.0)
    if abs((rj[1] + rj[3]) / 2 - rj_cy) > 0.1:
        raise SystemExit(f"{key}: PDF RJ45 body is off the DXF pegs")
    # Micro-USB: the two shell slots in the DXF give its centre line.
    # The polylines' centre lines: 0.8 long and 0.45 apart, drawn with a
    # constant width that makes the finished slot 1.25 x 0.45.
    usb_slots = [s for s in slots if s[0] < 3.0 and abs((s[3] - s[1]) - 0.45) < 0.05]
    if len(usb_slots) != 2:
        raise SystemExit(f"{key}: {len(usb_slots)} USB shell slots, not 2")
    usb_cy = sum((s[1] + s[3]) / 2 for s in usb_slots) / 2
    usb = _pick(rects, "usb", (2.0, usb_cy), (5.2, 7.4), tol_pos=1.0)
    if abs((usb[1] + usb[3]) / 2 - usb_cy) > 0.1:
        raise SystemExit(f"{key}: PDF USB body is off the DXF slots")

    features = [
        dict(key="usb_prog", kind="usb_power", designator="J10",
             label="micro-USB J10, programming and console",
             x0=usb[0], y0=usb[1], x1=usb[2], y1=usb[3],
             note="Shell outline from the PDF plot; centre line from the "
                  "DXF's shell slots."),
        dict(key="ethernet", kind="ethernet", designator="J9",
             label="Ethernet RJ45 J9",
             x0=rj[0], y0=rj[1], x1=rj[2], y1=rj[3],
             note="Body outline from the PDF plot; centre line from the "
                  "DXF's locating pegs."),
    ]
    for key_, (row_y, size) in ARTY_LED_ROWS.items():
        boxes = [_pick(rects, f"{key_} {n}", (x, row_y), size, tol_pos=0.5,
                       tol_size=0.3) for n, x in enumerate(ARTY_LED_X)]
        label = "Tri-colour LEDs LD0-LD3" if key_ == "rgb_leds" else "LEDs LD4-LD7"
        features.append(row_feature(
            boxes, key=key_, label=label, kind="led",
            note="Bodies from the PDF plot; which row is which follows the "
                 "package size, see notes.",
            designator="LD0-LD3" if key_ == "rgb_leds" else "LD4-LD7"))
    number_features(key, features)
    return dict(
        key=key, title="Digilent Arty A7", subtitle="A7-35T and A7-100T",
        front_edge="top", thickness=None,
        width=round(w, 3), height=round(h, 3), corner_radius=0.0,
        edges=[("line", 0.0, 0.0, round(w, 3), 0.0),
               ("line", round(w, 3), 0.0, round(w, 3), round(h, 3)),
               ("line", round(w, 3), round(h, 3), 0.0, round(h, 3)),
               ("line", 0.0, round(h, 3), 0.0, 0.0)],
        holes=[], pmods=pmods, features=features,
        sources=[
            ("Mechanical drawing", ARTY_ZIP,
             "Digilent, Arty_A7_DXF.DXF and Mechanical_Arty_A7.pdf, dated "
             "2020-09-02. Outline, pin fields, slots and pegs from the DXF; "
             "component bodies from the PDF, whose plot scale is recovered "
             f"from the outline (axes agree to {abs(aniso - 1) * 100:.2f} %)."),
            ("3D model", ARTY_CAD,
             "Digilent, Arty Rev C: used only to identify which of the "
             "PDF's outlines are the eight user LEDs."),
            ("Reference manual", ARTY_RM,
             "Pmod JA, JB, JC, JD; four tri-colour and four single LEDs."),
            ("Mounting", ARTY_FORUM,
             'Digilent staff, 2017-07-19: "There are no thru holes or '
             'mounting provisions"; the board stands on rubber feet.'),
        ],
        notes=[
            "No mounting holes. The drawing shows four 10.0 mm rubber feet "
            "centred 5.0 mm from each corner; a plate has to carry the board "
            "on those or clamp its edges.",
            f"The Pmod pin rows are {row_gap:.2f} mm apart on the drawing, "
            "not 2.54, and the hosts are on a 22.80 mm pitch where the PDF's "
            "dimension reads 0.90 in; both within the general tolerance.",
            "JA is nearest the USB and Ethernet corner, per the reference "
            "manual's callout figure.",
            "The 1.6 x 1.6 mm LED row nearest the edge is taken as the "
            "tri-colour LD0-LD3 and the 0603 row behind it as LD4-LD7; no "
            "source names them.",
            "Bodies read from the PDF plot are good to about +/-0.3 mm; the "
            "DXF figures carry the general tolerance.",
        ],
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

HEADER = '''"""FPGA development board mechanical data.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber --with cadquery \\\\
        python fpga/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  Each board is drawn the way its
maker draws it: the Arty A7 and ULX3S with their Pmod or GPIO edge and USB
along the top, the PYNQ-Z2 with its Pmod hosts on the right, ButterStick with
its USB-C and Ethernet on the right, the Icepi Zero the way Raspberry Pi
draw a Zero, its GPIO header along the top and its connector edge at the
bottom, and Cynthion with its two Pmod hosts along the bottom.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, PmodHeader, Source

BOARDS: dict[str, BoardSpec] = {}

#: Feature numbers are fixed across the family: a number means the same part on
#: every sheet.  A board that does not carry the part still gets a row, so a
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
            f"designator={p['designator']!r}, edge={p['edge']!r},\n"
            f"                   cx={p['cx']}, cy={p['cy']}, "
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

    def sources():
        return ",\n".join(
            f"        Source(label={label!r},\n"
            f"               ref={ref!r},\n"
            f"               note={note!r})"
            for label, ref, note in rec["sources"])

    def notes():
        return "".join(f"        {n!r},\n" for n in rec["notes"])

    return f'''
BOARDS[{rec["key"]!r}] = BoardSpec(
    key={rec["key"]!r},
    title={rec["title"]!r},
    subtitle={rec["subtitle"]!r},
    family="fpga",
    front_edge={rec["front_edge"]!r},
    outline=Outline(width={rec["width"]}, height={rec["height"]},
                    corner_radius={rec["corner_radius"]}, thickness={rec["thickness"]},
                    profile_note={rec.get("profile_note", "")!r},
                    edges=(
{edges()},
                    )),
    holes=(
{holes()}{"," if rec["holes"] else ""}
    ),
    pmods=(
{pmods()}{"," if rec["pmods"] else ""}
    ),
    features=(
{feats()},
    ),
    sources=(
{sources()},
    ),
    notes=(
{notes()}    ),
    envelope_note={rec.get("envelope_note", "")!r},
)
'''


def main() -> None:
    records = [extract_arty(), extract_ulx3s(), extract_pynq_z2(),
               extract_butterstick(), extract_icepi_zero(),
               extract_cynthion()]
    numbers = "{\n" + "".join(
        f"    {i}: {FEATURE_NAMES[key]!r},\n"
        for i, key in enumerate(FEATURE_ORDER, 1)) + "}"
    chunks = [HEADER.replace("__NUMBERS__", numbers)]
    for rec in records:
        chunks.append(render(rec))
        print(f"{rec['key']:12s} {rec['width']:7.2f} x {rec['height']:6.2f} mm  "
              f"{len(rec['holes'])} holes  {len(rec['pmods'])} pmods  "
              f"{len(rec['features'])} features")
    out = ROOT / "fpga" / "boards.py"
    out.write_text("".join(chunks))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
