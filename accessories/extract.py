#!/usr/bin/env python3
"""Generate ``accessories/raspmod.py`` from the Raspmod's KiCad board file.

The Raspmod -- Pat Deegan's "TT Demoboard To Raspi", a frontplate that puts a
Tiny Tapeout demoboard's three Pmod ports on a Raspberry Pi ribbon cable --
is the one accessory with a machine-readable source: its KiCad board file is
published.  So its outline, its six 2x6 headers, its 40-way ribbon header and
its pin map are read from that file at a pinned commit, the way the Tiny
Tapeout and FPGA sheets are made.  The Digilent Pmod HAT Adapter and the PoE
splitters stay hand-curated in ``parts.py``, because nothing machine-readable
exists for them.

The pin map comes from the same file as the geometry: KiCad writes each pad's
net name into the board, so the table in ``raspmod-vs-pmod-hat.md`` and the
positions on the Raspmod sheet cannot disagree about which header is
which.

The source is expected under ``tmp/src``; ``make fetch`` clones it.

Run: uv run --no-project python accessories/extract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import kicad_extract, kicad_pcb  # noqa: E402
from tools.kicad_extract import one  # noqa: E402
from tools.kicad_pcb import child, children  # noqa: E402

SRC = ROOT / "tmp" / "src"
WORK = ROOT / "tmp" / "pcb"

REPO = "https://github.com/psychogenic/tinytapeout-demoboard-to-raspi"
BOARD_PATH = "TTDB_2_Raspi.kicad_pcb"
#: The commit the board file was imported in.  The one commit after it adds
#: the gerbers and does not touch the board.
COMMIT = "2c2e3db"
README = f"{REPO}/blob/main/README.md"

#: Which designator plays which role.  The three ports are named after
#: their nets -- P1, P2, P3 -- which is also the order the plugs meet the
#: demoboard's INPUT, BIDIR and OUTPUT hosts in.  Each port is a pair: the
#: socket on the component side that an external Pmod goes into, and the pin
#: header on the underside that goes into the demoboard.
PORTS = (("P1", "J5", "J2"), ("P2", "J6", "J3"), ("P3", "J7", "J4"))

FEATURES = (
    # key, ref, kind, label
    ("ribbon", "J1", "header", "40-way ribbon header J1 to the Raspberry Pi GPIO, 2x20 box"),
    ("clkrst_socket", "J8", "header", "Clock and reset socket J8, 1x2"),
    ("clkrst_pins", "J9", "header", "Clock and reset pins J9, 1x2, on the underside"),
    ("aux", "J10", "header", "Auxiliary socket J10, 1x4: GND, 3V3, USR_IO, USR_SW"),
    ("power_jumper", "J11", "header", "Power jumper J11: Pi 3V3 to the Pmod VCC rail"),
    ("user_switch", "SW1", "switch", "User push button SW1, USR_SW"),
)

HEADER = '''"""Raspmod mechanical data and pin map, from its KiCad board file.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python accessories/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, viewed from the component side, millimetres.  The
component side carries the three Pmod host sockets and the ribbon header; the
three plugs that go into the demoboard are on the underside, along the lower
edge, which is the edge that sits at the demoboard when the board stands in
front of it.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Outline, PmodHeader, Source

#: Raspberry Pi 40-pin header pin -> (the Pi's name for it, the Raspmod net
#: it lands on).  The Pi's names are the ``pinfunction`` KiCad's Raspberry Pi
#: symbol gives each pin; the nets are the board's own.  A pin with no net is
#: not connected on the Raspmod.
PI_HEADER: dict[int, tuple[str, str]] = __PI_HEADER__

#: Each port's twelve Pmod pins -> the Raspmod net on that pin.  The host
#: socket and the underside plug of a port share every net, which is checked
#: at extraction.
PORT_PINS: dict[str, dict[int, str]] = __PORT_PINS__
'''


def nets(fp_node) -> dict[str, tuple[str, str]]:
    """Pad number -> (net, pinfunction) for one footprint node."""
    out = {}
    for pad in children(fp_node, "pad"):
        net = child(pad, "net")
        func = child(pad, "pinfunction")
        out[str(pad[1])] = (net[1] if net else "", func[1] if func else "")
    return out


def extract() -> dict:
    path = kicad_extract.pinned_board(SRC / "tinytapeout-demoboard-to-raspi",
                                      COMMIT, BOARD_PATH, WORK / "raspmod.kicad_pcb")
    board = kicad_pcb.load(str(path))
    key = "raspmod"
    to_xy, to_box, (w, h) = kicad_extract.frame(board)
    fps = board.footprints
    edges, radii = kicad_extract.outline(key, board, to_xy, w, h)
    if len(radii) != 1:
        raise SystemExit(f"{key}: expected one corner radius, got {radii}")

    # Mounting holes: there are none, and that is checked rather than
    # assumed, so a revision that gains some cannot be drawn without them.
    big = [p for fp in fps for p in fp.pads if p.drill and p.drill >= 2.0]
    if big:
        raise SystemExit(f"{key}: {len(big)} drills of 2 mm or more; the board "
                         "has mounting holes now, add them")

    # The nets, by designator, from the raw tree: the board reader keeps
    # geometry only.
    tree = board.tree
    by_ref = {}
    for node in children(tree, "footprint"):
        ref = next((p[2] for p in children(node, "property")
                    if p[1] == "Reference"), "")
        by_ref[ref] = nets(node)

    pmods = []
    port_pins: dict[str, dict[int, str]] = {}
    for label, host_ref, plug_ref in PORTS:
        host, plug = one(fps, host_ref), one(fps, plug_ref)
        for fp, role in ((host, "host"), (plug, "plug")):
            rec = kicad_extract.pmod(fp, to_xy, to_box, key=f"{label.lower()}_{role}",
                                     label=label, edge="bottom")
            rec["role"] = role
            pmods.append(rec)
        hn, pn = by_ref[host_ref], by_ref[plug_ref]
        if {k: v[0] for k, v in hn.items()} != {k: v[0] for k, v in pn.items()}:
            raise SystemExit(f"{key}: {host_ref} and {plug_ref} do not carry "
                             "the same nets pin for pin")
        port_pins[label] = {int(n): hn[n][0] for n in sorted(hn, key=int)}
    # The plugs sit on the demoboard's host pitch, or the board does not fit
    # the demoboard at all.
    plugs = sorted((p for p in pmods if p["role"] == "plug"), key=lambda p: p["cx"])
    for a, b in zip(plugs, plugs[1:]):
        if abs((b["cx"] - a["cx"]) - 22.86) > 0.01:
            raise SystemExit(f"{key}: plug pitch is {b['cx'] - a['cx']:.3f}, not 22.86")

    features = []
    for n, (fkey, ref, kind, label) in enumerate(FEATURES, 1):
        fp = one(fps, ref)
        b = kicad_extract.box(fp, to_box)
        note = ""
        if ref == "J1":
            p1 = to_xy(*next((p.x, p.y) for p in fp.pads if p.number == "1"))
            note = (f"Pin 1 at ({p1[0]:.2f}, {p1[1]:.2f}), the right-hand end of "
                    "the upper row. Courtyard of the 2x20 box header; the "
                    "ribbon plugs in from the front.")
        elif ref == "J9":
            note = ("Underside. Falls on pins 2 and 3 of the demoboard's "
                    "clock/reset SIL header; the maker's README says a 2-pin "
                    "header has to be added to the demoboard there.")
        features.append(dict(key=fkey, kind=kind, designator=ref, label=label,
                             x0=b[0], y0=b[1], x1=b[2], y1=b[3], note=note,
                             side="bottom" if fp.layer == "B.Cu" else "top",
                             number=n))

    j1 = by_ref["J1"]
    pi_header = {int(n): (j1[n][1], "" if j1[n][0].startswith("Net-") else j1[n][0])
                 for n in sorted(j1, key=int)}
    plug = plugs[0]
    host = next(p for p in pmods if p["role"] == "host" and p["label"] == plug["label"])
    dx, dy = host["cx"] - plug["cx"], host["cy"] - plug["cy"]
    return dict(
        key=key, title="Raspmod",
        subtitle=f"TT Demoboard To Raspi rev {board.rev}, silkscreen v1.1: "
                 "a frontplate for the demoboard's three Pmod hosts",
        thickness=board.thickness,
        width=round(w, 3), height=round(h, 3), corner_radius=radii[0],
        edges=edges, pmods=pmods, features=features,
        pi_header=pi_header, port_pins=port_pins,
        sources=[
            ("KiCad board file", f"{REPO}  {BOARD_PATH} @ {COMMIT}",
             f"title block: {board.title} rev {board.rev}, dated {board.date}, "
             f"{board.company}; the silkscreen reads v1.1"),
            ("Purpose", README,
             'quoted: "Connects all I/O from TT demoboard to RPi ribbon cable '
             'while still allowing the PMODs to be used with external modules."'),
            ("Clock and reset", README,
             'quoted: "the clock and reset are only available through the SIL '
             "(not one of the PMODs) so these must be connected by adding a "
             '2-pin header to the demoboard in the right spot."'),
        ],
        notes=[
            "Not a HAT. The board stands on edge in front of a Tiny Tapeout "
            "demoboard, its three underside plugs in the demoboard's Pmod "
            "hosts and its component side facing forward; the Raspberry Pi "
            "connects by ribbon cable only.",
            f"PLUG rows are the underside 2x6 pin headers. Their fields sit "
            f"{dy:.2f} mm below the HOST fields and {-dx:.2f} mm to the right, "
            "on the demoboard's 22.86 mm host pitch, so P1 goes into the "
            "INPUT host, P2 into BIDIR and P3 into OUTPUT.",
            "HOST rows J5 to J7 are vertical sockets facing out of the "
            "component side; EDGE gives the axis the columns run along, and "
            "pin 1 is the right-hand end of the upper row on both rows.",
            "No mounting holes: the plugs carry the board.",
            "The pin map, read from the same board file, is in "
            "accessories/raspmod-vs-pmod-hat.md.",
        ],
    )


def render(rec: dict) -> str:
    def pmods():
        return ",\n".join(
            f"        PmodHeader(key={p['key']!r}, label={p['label']!r}, "
            f"designator={p['designator']!r}, edge={p['edge']!r}, role={p['role']!r},\n"
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
            f"                note={f['note']!r}, side={f['side']!r}, number={f['number']})"
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
RASPMOD = BoardSpec(
    key={rec["key"]!r},
    title={rec["title"]!r},
    subtitle={rec["subtitle"]!r},
    family="accessory",
    front_edge="bottom",
    outline=Outline(width={rec["width"]}, height={rec["height"]},
                    corner_radius={rec["corner_radius"]}, thickness={rec["thickness"]},
                    edges=(
{edges()},
                    )),
    pmods=(
{pmods()},
    ),
    features=(
{feats()},
    ),
    sources=(
{sources()},
    ),
    notes=(
{notes()}    ),
)
'''


def _dict(d: dict, indent: int = 4) -> str:
    pad = " " * indent
    return "{\n" + "".join(f"{pad}{k!r}: {v!r},\n" for k, v in d.items()) + "}"


def main() -> None:
    rec = extract()
    pi = "{\n" + "".join(f"    {k}: {v!r},\n" for k, v in rec["pi_header"].items()) + "}"
    ports = "{\n" + "".join(
        f"    {port!r}: " + _dict(pins, 8).replace("\n}", "\n    }") + ",\n"
        for port, pins in rec["port_pins"].items()) + "}"
    text = HEADER.replace("__PI_HEADER__", pi).replace("__PORT_PINS__", ports)
    text += render(rec)
    out = ROOT / "accessories" / "raspmod.py"
    out.write_text(text)
    print(f"{rec['key']:12s} {rec['width']:7.2f} x {rec['height']:6.2f} mm  "
          f"{len(rec['pmods'])} pmods  {len(rec['features'])} features")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
