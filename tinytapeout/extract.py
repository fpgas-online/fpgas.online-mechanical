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

import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import kicad_pcb  # noqa: E402
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
SHUTTLE_SHEET = ("https://docs.google.com/spreadsheets/d/"
                 "1xD_uemuQcpUnXRY4twOrfFzF0urJLVWMdqAnrOJLetM/"
                 "edit?gid=1250963370")

#: The number each feature carries in the schedule and on its balloon, fixed
#: across the whole demo board family so that a number means the same part on
#: every sheet.  A revision that does not carry a part leaves its number
#: unused: the boards with a fourth LED have no DIP switch and the boards with
#: a DIP switch have no fourth LED, so numbering them off each sheet's own
#: list made 6 mean one thing on half the set and another on the rest.
FEATURE_ORDER = ["usb_power", "display7", "led1", "led2", "led3", "led4",
                 "dipsw", "side_pmod1", "side_pmod2", "side_pmod3"]

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
    "dipsw": "8-way input DIP switch",
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
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB mpw v2.2.6", Used by: {used}.',
        extra_notes=(
            "The title block reads \"TinyTapeout 1,2,3 Demo Board\", but no "
            "PCB served TT01: that was a bare-die trial run.",
        ),
        source_url="https://github.com/TinyTapeout/tt123-demo-pcb",
    ),
    dict(
        key="v1.2.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="cfdd80d7b",
        title="DB 4+ v1.2.2",
        subtitle="tinytapeout-demo rev 1.2.2",
        used_by=("TT04",),
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
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB 4+ v1.2.2c", Used by: {used}.',
        extra_notes=(
            "v1.2.2c is an assembly variant, not a layout change: no X1, a "
            "0R at R51. Its KiCad title block reads rev 1.2.3.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.0.1",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="292760e1f",
        title="DB 06+ v2.0.1",
        subtitle="tinytapeout-demo rev 2.0.1",
        used_by=("TT06",),
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
        # The historic README does not carry this revision; Tiny Tapeout's own
        # board revision spreadsheet does, and it is where "ETR" comes from.
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note='row "DB ETR v3.2", Used by: {used}.',
        extra_notes=(
            "ETR is Tiny Tapeout's own designation for this board. The KiCad "
            "title block reads \"Tiny Tapeout Demoboard v3\" and does not "
            "carry it; the name here is the board's ID in Tiny Tapeout's "
            "board revision spreadsheet. Nothing mechanical depends on it.",
        ),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v3.3",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="ecb636ace",
        title="DB ETR v3.3",
        subtitle="tinytapeout-demo rev 3.3",
        used_by=(),
        shuttle_source=SHUTTLE_SHEET,
        shuttle_note="no row: this revision is not in the board revision "
                     "spreadsheet, so no shuttle is recorded for it.",
        extra_notes=(
            "This revision has no row in Tiny Tapeout's board revision "
            "spreadsheet, which lists DB ETR v3.2 as the current demoboard. "
            "The name used here follows that ID; no shuttle is known to have "
            "shipped on it.",
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
        leds=["D1", "D2", "D3", "D4"],
        holes=["MT1", "MT2", "MT3", "MT4"],
    ),
    "v1.2.2": dict(
        pmods=["J3", "J5", "J6"], pmod_labels=["INPUT", "BIDIR", "OUTPUT"],
        usb_power="J15", display7="U1",
        leds=["D1", "D2", "D3", "D4"],
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


def frame(board):
    """Return a mapper from KiCad coordinates to the drawing frame."""
    x0, y0, x1, y1 = board.outline_bbox()

    def to_xy(x, y):
        return x - x0, y1 - y

    def to_box(bb):
        return (bb[0] - x0, y1 - bb[3], bb[2] - x0, y1 - bb[1])

    return to_xy, to_box, (x1 - x0, y1 - y0)


def _check_arc_passes_through(key: str, edge, point, tol: float = 0.02) -> None:
    best = min(math.dist(point, p) for p in _sample_arc(*edge[1:], steps=180))
    if best > tol:
        raise SystemExit(
            f"{key}: a resolved outline arc misses the point KiCad puts on it "
            f"by {best:.3f} mm. It is curving the wrong way.")


def _check_outline_extent(key: str, edges, width: float, height: float) -> None:
    """The resolved outline must fill its own bounding box, and no more.

    An arc resolved with the wrong direction or the wrong large-arc flag bulges
    the opposite way, which shows up here immediately.  It is exactly the
    mistake that turns rounded corners into scallops bitten out of the board,
    and it looks plausible enough at screen size to survive a visual check.

    Each arc is sampled rather than reasoned about: recovering a circle centre
    from SVG-style parameters has its own sign trap, and sampling has none.
    """
    xs: list[float] = []
    ys: list[float] = []
    for e in edges:
        if e[0] == "line":
            xs += [e[1], e[3]]
            ys += [e[2], e[4]]
        else:
            for px, py in _sample_arc(*e[1:]):
                xs.append(px)
                ys.append(py)
    got_w, got_h = max(xs) - min(xs), max(ys) - min(ys)
    if abs(got_w - width) > 0.02 or abs(got_h - height) > 0.02:
        raise SystemExit(
            f"{key}: the resolved outline spans {got_w:.3f} x {got_h:.3f} mm "
            f"but the board is {width:.3f} x {height:.3f}. An arc is bulging "
            f"the wrong way.")


def _sample_arc(x1, y1, x2, y2, r, large, ccw, steps: int = 33):
    """Points along an SVG-style arc, including both ends."""
    dx, dy = x2 - x1, y2 - y1
    half = math.hypot(dx, dy) / 2
    off = math.sqrt(max(r * r - half * half, 0.0))
    # Of the two candidate centres, the one that gives the requested sweep.
    nx, ny = -dy / (2 * half), dx / (2 * half)
    for sign in (1, -1):
        cx = (x1 + x2) / 2 + sign * off * nx
        cy = (y1 + y2) / 2 + sign * off * ny
        a0 = math.atan2(y1 - cy, x1 - cx)
        a2 = math.atan2(y2 - cy, x2 - cx)
        span = (a2 - a0) % (2 * math.pi) if ccw else (a0 - a2) % (2 * math.pi)
        if (span > math.pi) == bool(large):
            break
    out = []
    for i in range(steps + 1):
        a = a0 + (span if ccw else -span) * i / steps
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def one(fps, ref):
    hits = [f for f in fps if f.reference == ref]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one {ref}, found {len(hits)}")
    return hits[0]


def extract(rev: dict) -> dict:
    board = kicad_pcb.load(str(fetch(rev)))
    roles = ROLES[rev["key"]]
    to_xy, to_box, (w, h) = frame(board)
    fps = board.footprints

    segs, arcs, circles = board.edge_cuts()
    edges = []
    for g in segs:
        a, b = to_xy(g.x1, g.y1), to_xy(g.x2, g.y2)
        edges.append(("line", round(a[0], 3), round(a[1], 3),
                      round(b[0], 3), round(b[1], 3)))
    # Arcs are resolved here, where the source geometry is, rather than in the
    # renderer.  Storing centre, radius, whether the arc is the major one and
    # which way it turns means the drawing side never has to re-derive a circle
    # from three points, and cannot get the large-arc flag wrong.
    for g in arcs:
        cx, cy, r = g.centre_radius()
        a, m, b = to_xy(g.x1, g.y1), to_xy(g.xm, g.ym), to_xy(g.x2, g.y2)
        centre = to_xy(cx, cy)
        a0 = math.atan2(a[1] - centre[1], a[0] - centre[0])
        a1 = math.atan2(m[1] - centre[1], m[0] - centre[0])
        a2 = math.atan2(b[1] - centre[1], b[0] - centre[0])
        ccw = ((a1 - a0) % (2 * math.pi)) < ((a2 - a0) % (2 * math.pi))
        swept = ((a2 - a0) % (2 * math.pi)) if ccw \
            else ((a0 - a2) % (2 * math.pi))
        edge = ("arc", round(a[0], 3), round(a[1], 3),
                round(b[0], 3), round(b[1], 3), round(r, 4),
                1 if swept > math.pi else 0, 1 if ccw else 0)
        # KiCad gives an explicit point on the arc.  Requiring the resolved arc
        # to pass through it is the only check that catches a corner fillet
        # resolved the wrong way round: such an arc curves into the corner
        # rather than out of it, so it stays inside the board's bounding box
        # and a bounding box check sees nothing wrong.
        _check_arc_passes_through(rev["key"], edge, m)
        edges.append(edge)
    # An arc resolved with the wrong direction or the wrong large-arc flag
    # bulges the opposite way, which shows up as the outline no longer filling
    # its own bounding box.  Cheap to check, and it is exactly the mistake that
    # turns rounded corners into scallops bitten out of the board.
    _check_outline_extent(rev["key"], edges, w, h)

    radii = sorted({round(g.centre_radius()[2], 3) for g in arcs})
    corner_radius = radii[-1]
    profile_note = ""
    if len(radii) > 1:
        profile_note = (
            "Upper edge carries a shallow recess for the USB-C shell, "
            "contributed by the connector footprint's own edge cuts "
            # Three decimals throughout: printed at their natural precision
            # the list read "0.136 mm, 0.303 mm, 0.364 mm, 0.4 mm", where the
            # last looks like a coarser measurement than the others.
            f"(fillet radii {', '.join(f'{r:.3f} mm' for r in radii[:-1])}).")

    holes = []
    for ref in roles["holes"]:
        fp = one(fps, ref)
        x, y = to_xy(fp.x, fp.y)
        pads = fp.pads
        drills = [p.drill for p in pads if p.drill]
        if not drills:
            raise SystemExit(
                f"{rev['key']}: mounting hole {ref} has no drill size. Do not "
                f"guess one; fix the role table or the source.")
        dia = min(drills)
        pad_dia = max(max(p.size) for p in pads)
        holes.append(dict(x=round(x, 3), y=round(y, 3), dia=round(dia, 3),
                          label=ref, kind="mount", keepout_dia=round(pad_dia, 3)))

    pmods = []
    for i, ref in enumerate(roles["pmods"]):
        fp = one(fps, ref)
        pads = {p.number: p for p in fp.pads}
        xs = [to_xy(p.x, p.y)[0] for p in fp.pads]
        ys = [to_xy(p.x, p.y)[1] for p in fp.pads]
        p1x, p1y = to_xy(pads["1"].x, pads["1"].y)
        body = to_box(fp.bbox("courtyard"))
        pmods.append(dict(
            key=f"pmod{i + 1}", label=roles["pmod_labels"][i], designator=ref,
            cx=round((min(xs) + max(xs)) / 2, 3), cy=round((min(ys) + max(ys)) / 2, 3),
            pin1_x=round(p1x, 3), pin1_y=round(p1y, 3),
            body_x0=round(body[0], 3), body_y0=round(body[1], 3),
            body_x1=round(body[2], 3), body_y1=round(body[3], 3)))

    features = []

    def add(ref, key, label, kind, note="", box="courtyard"):
        fp = one(fps, ref)
        bb = fp.bbox(box) or fp.pad_bbox()
        b = to_box(bb)
        features.append(dict(key=key, label=label, kind=kind, designator=ref,
                             x0=round(b[0], 3), y0=round(b[1], 3),
                             x1=round(b[2], 3), y1=round(b[3], 3), note=note))

    add(roles["usb_power"], "usb_power", "USB-C power / control", "usb_power",
        note="Body outline including the shell overhang past the board edge.")
    add(roles["display7"], "display7", "7-segment display", "display7")
    for n, ref in enumerate(roles["leds"], 1):
        add(ref, f"led{n}", f"LED {ref}", "led")
    if roles.get("switch"):
        add(roles["switch"], "dipsw", "8-way input DIP switch", "switch")
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

    identical_note = (
        f"Geometrically identical to revision {twins}: the outline, mounting "
        f"holes, Pmod hosts and every feature on this sheet are in the same "
        f"place. Only the electrical design and the shuttle differ."
        if twins else
        "No other demo board revision shares this geometry.")
    return f'''
BOARDS[{rec["key"]!r}] = BoardSpec(
    key={rec["key"]!r},
    title={rec["title"]!r},
    subtitle={rec["subtitle"]!r},
    family="tinytapeout",
    used_by={tuple(rec["used_by"])!r},
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
        "Geometry is design nominal, read from the KiCad board file.",
        "Hole IDs are the board's own reference designators from the KiCad "
        "file, not assigned by this drawing, and are in no positional order.",
        {identical_note!r},
{extra_notes()}    ),
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
