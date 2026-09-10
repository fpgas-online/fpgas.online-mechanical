#!/usr/bin/env python3
"""Generate ``data/tinytapeout_boards.py`` from the upstream KiCad board files.

The numbers all come out of the ``.kicad_pcb`` files; the human judgement is the
``ROLES`` table below, which says which reference designator plays which
mechanical role on each revision.  Keeping those apart means a re-run can never
quietly invent a dimension, and a mis-identified part is a one-line fix.

The upstream repositories are expected to be cloned under ``tmp/src``::

    git clone https://github.com/TinyTapeout/tt-demo-pcb    tmp/src/tt-demo-pcb
    git clone https://github.com/TinyTapeout/tt123-demo-pcb tmp/src/tt123-demo-pcb

Run: uv run --no-project python scripts/extract_tinytapeout.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kicad_pcb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "tmp" / "pcb"

# Shuttle -> production revision comes from the upstream historic documentation,
# tt-demo-pcb/doc/historic/README.md, which names both the revision and the
# commit it was produced from.  That file stops at TT08; no Tiny Tapeout source
# states a board revision for any later shuttle, and per tinytapeout.com/chips
# no shuttle after TT08 has shipped, so v3.x is listed without a shuttle.
REVISIONS = [
    dict(
        key="tt123-v2.2.6",
        repo="tt123-demo-pcb", path="mpw-mb1.kicad_pcb", commit="3d721a6",
        title="Tiny Tapeout TT01/02/03 Demo Board",
        subtitle="mpw-mb1 rev 2.2.6",
        used_by=("TT01", "TT02", "TT03"),
        source_url="https://github.com/TinyTapeout/tt123-demo-pcb",
    ),
    dict(
        key="v1.2.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="cfdd80d7b",
        title="Tiny Tapeout 4+ Demo Board",
        subtitle="tinytapeout-demo rev 1.2.2",
        used_by=("TT04",),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v1.2.3",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="a88cbc08b",
        title="Tiny Tapeout 4+ Demo Board",
        subtitle="tinytapeout-demo rev 1.2.3",
        used_by=("TT05",),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.0.1",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="292760e1f",
        title="Tiny Tapeout 06+ Demo Board",
        subtitle="tinytapeout-demo rev 2.0.1",
        used_by=("TT06",),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.1.0",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="a799acb38",
        title="Tiny Tapeout 06+ Demo Board",
        subtitle="tinytapeout-demo rev 2.1.0",
        used_by=("TT07",),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v2.1.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="028a51b1e",
        title="Tiny Tapeout 06+ Demo Board",
        subtitle="tinytapeout-demo rev 2.1.2",
        used_by=("TT08",),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v3.2",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="d830790ca",
        title="Tiny Tapeout Demo Board v3 (ETR)",
        subtitle="tinytapeout-demo rev 3.2",
        used_by=(),
        source_url="https://github.com/TinyTapeout/tt-demo-pcb",
    ),
    dict(
        key="v3.3",
        repo="tt-demo-pcb", path="tinytapeout-demo.kicad_pcb", commit="ecb636ace",
        title="Tiny Tapeout Demo Board v3 (ETR)",
        subtitle="tinytapeout-demo rev 3.3",
        used_by=(),
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
    for g in arcs:
        a, m, b = to_xy(g.x1, g.y1), to_xy(g.xm, g.ym), to_xy(g.x2, g.y2)
        edges.append(("arc", round(a[0], 3), round(a[1], 3), round(m[0], 3),
                      round(m[1], 3), round(b[0], 3), round(b[1], 3)))
    radii = sorted({round(g.centre_radius()[2], 3) for g in arcs})
    corner_radius = radii[-1]
    profile_note = ""
    if len(radii) > 1:
        profile_note = (
            "Upper edge carries a shallow recess for the USB-C shell, "
            "contributed by the connector footprint's own edge cuts "
            f"(fillet radii {', '.join(f'{r} mm' for r in radii[:-1])}).")

    holes = []
    for ref in roles["holes"]:
        fp = one(fps, ref)
        x, y = to_xy(fp.x, fp.y)
        pads = fp.pads
        dia = min(p.drill for p in pads if p.drill) if any(p.drill for p in pads) else 3.2
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

    return dict(
        key=rev["key"], title=rev["title"], subtitle=rev["subtitle"],
        used_by=list(rev["used_by"]),
        commit=rev["commit"], repo=rev["repo"], path=rev["path"],
        source_url=rev["source_url"],
        kicad_title=board.title.strip(), kicad_rev=board.rev, kicad_date=board.date,
        width=round(w, 3), height=round(h, 3), corner_radius=corner_radius,
        thickness=board.thickness, edges=edges, profile_note=profile_note,
        holes=holes, pmods=pmods, features=features)


HEADER = '''"""Tiny Tapeout demo board mechanical data.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python scripts/extract_tinytapeout.py

Every dimension is read directly out of the upstream KiCad board file at the
commit named in each entry's ``source``; nothing here is transcribed by eye.
Coordinates follow :mod:`data.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  The three Pmod host headers are
along the lower (Y = 0) edge; the TT01/02/03 board has only two.
"""

from __future__ import annotations

from .schema import BoardSpec, Feature, Hole, Outline, PmodHeader, Source

BOARDS: dict[str, BoardSpec] = {}

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
            f"                note={f['note']!r})"
            for f in rec["features"])

    used = ", ".join(rec["used_by"]) or "no shipped shuttle yet"
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
               ref="https://github.com/TinyTapeout/tt-demo-pcb/blob/main/doc/historic/README.md",
               note="used by: {used}"),
    ),
    notes=(
        "Geometry is design nominal, read from the KiCad board file.",
        "Pmod host headers are on a 22.86 mm (0.9 in) pitch, per the Digilent "
        "Pmod Interface Specification 1.2.0.",
    ),
)
'''


def main() -> None:
    out = ROOT / "data" / "tinytapeout_boards.py"
    chunks = [HEADER]
    for rev in REVISIONS:
        rec = extract(rev)
        chunks.append(render(rec))
        print(f"{rec['key']:14s} {rec['width']:7.2f} x {rec['height']:6.2f} mm  "
              f"R{rec['corner_radius']}  {len(rec['holes'])} holes  "
              f"{len(rec['pmods'])} pmods  {len(rec['features'])} features")
    out.write_text("".join(chunks))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
