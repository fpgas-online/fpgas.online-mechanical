#!/usr/bin/env python3
"""Rewrite the tables in ``raspmod-vs-pmod-hat.md`` from the data modules.

The page compares the two ways of putting Pmod ports on a Raspberry Pi: the
Digilent Pmod HAT Adapter (ACC-01, hand-curated in ``parts.py``) and Pat
Deegan's Raspmod (ACC-04, generated from its board file into ``raspmod.py``).
Its prose is written by hand; its tables are not, because a pin map copied
into a document by hand is a pin map that drifts from the data the drawings
are made from.  Everything between a pair of ``<!-- name:begin -->`` and
``<!-- name:end -->`` markers is replaced, the way ``tools/update_readme.py``
rewrites the preview grids.

One figure on the page is measured rather than carried in a data module:
where the Raspmod's clock/reset pins land on the demoboard's SIL header.
The demoboard's SIL header is not part of the demoboard sheets, so it is
re-measured here from the checked-out board files whenever they are present,
and the page says which residual it was last written with.

Run: uv run --no-project python accessories/compare.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from accessories.parts import PMOD_HAT, PMOD_HAT_PINS  # noqa: E402
from accessories.raspmod import PI_HEADER, PORT_PINS, RASPMOD  # noqa: E402
from tinytapeout.boards import BOARDS as TT  # noqa: E402

PAGE = ROOT / "accessories" / "raspmod-vs-pmod-hat.md"

#: What each Raspmod port carries on the demoboard, and therefore what each
#: of its Pmod pins is: port P<n> is the demoboard's n-th host, and Pmod pin
#: 1-4 / 7-10 are that host's I/O 0-3 / 4-7.  Read off the demoboard board
#: file, tinytapeout-demo.kicad_pcb rev 2.1.2: host J3 pads 1-4 and 7-10 are
#: nets ui_in0-3 and ui_in4-7, J5 uio0-7, J6 uo_out0-7, and the Raspmod's
#: plugs J2-J4 carry P1_1-8, P2_1-8, P3_1-8 on the same pads.
TT_SIGNAL = {"P1": "ui_in", "P2": "uio", "P3": "uo_out"}
TT_HOST = {"P1": "INPUT", "P2": "BIDIR", "P3": "OUTPUT"}

#: The Raspmod's remaining nets, which are not port pins.
RASPMOD_OTHER = {
    "/CLK": "CLK, the demoboard's project clock, via J8/J9",
    "/~{RST}": "nRST, the demoboard's project reset, via J8/J9",
    "/USR_SW": "USR_SW, push button SW1, also on J10",
    "/USR_IO": "USR_IO, spare, on J10",
    "VDD": "3V3 from the Pi; J11 jumpers it to the Pmod VCC rail",
    "GND": "GND",
}


def pi_name(func: str) -> str:
    """The Pi's own name for a header pin, from KiCad's Raspberry Pi symbol.

    The symbol writes an active-low signal as ``~{CE0}``; the page writes it
    as ``nCE0``, which survives a Markdown table.
    """
    return re.sub(r"~\{([^}]*)\}", r"n\1", func)


def raspmod_signal(net: str) -> str:
    m = re.fullmatch(r"/P([123])_([1-8])", net)
    if m:
        port, io = m.group(1), int(m.group(2))
        pin = io if io <= 4 else io + 2
        return f"P{port} pin {pin}, {TT_SIGNAL['P' + port]}[{io - 1}]"
    return RASPMOD_OTHER.get(net, net or "not connected")


def hat_by_pi_pin() -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for port, pins in PMOD_HAT_PINS.items():
        for pmod_pin, (pi_pin, _) in pins.items():
            out.setdefault(pi_pin, []).append(f"{port}{pmod_pin}")
    return out


def table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out + [""]


def pi_header_table() -> list[str]:
    hat = hat_by_pi_pin()
    rows = []
    for pin in range(1, 41):
        func, net = PI_HEADER[pin]
        name = pi_name(func)
        if name in ("GND",):
            h = "GND"
        elif name == "3V3":
            h = "3V3 rail"
        elif name == "5V":
            h = "5 V in or out"
        elif pin in (27, 28):
            h = "ID EEPROM"
        else:
            h = ", ".join(hat.get(pin, [])) or "free"
        rows.append([str(pin), name, h, raspmod_signal(net)])
    return table(["Pi pin", "Pi name", "Pmod HAT Adapter", "Raspmod"], rows)


def port_tables() -> list[str]:
    out = ["**Digilent Pmod HAT Adapter**", ""]
    rows = []
    for pmod_pin in range(1, 13):
        row = [str(pmod_pin)]
        for port in ("JA", "JB", "JC"):
            if pmod_pin in (5, 11):
                row.append("GND")
            elif pmod_pin in (6, 12):
                row.append("3V3")
            else:
                pi_pin, name = PMOD_HAT_PINS[port][pmod_pin]
                row.append(f"{name} (pin {pi_pin})")
        rows.append(row)
    out += table(["Pmod pin", "JA", "JB", "JC"], rows)
    out += ["**Raspmod**", ""]
    by_net = {net: pin for pin, (_, net) in PI_HEADER.items() if net}
    rows = []
    for pmod_pin in range(1, 13):
        row = [str(pmod_pin)]
        for port in ("P1", "P2", "P3"):
            net = PORT_PINS[port][pmod_pin]
            if net == "GND":
                row.append("GND")
            elif net == "+3V3":
                row.append("3V3 (Pmod VCC rail)")
            else:
                pin = by_net[net]
                io = int(net.rsplit("_", 1)[1])
                row.append(f"{pi_name(PI_HEADER[pin][0])} (pin {pin}), "
                           f"{TT_SIGNAL[port]}[{io - 1}]")
        rows.append(row)
    out += table(["Pmod pin", "P1 = INPUT host", "P2 = BIDIR host",
                  "P3 = OUTPUT host"], rows)
    return out


def mechanics_table() -> list[str]:
    hat, rm = PMOD_HAT, RASPMOD
    hosts = [p for p in rm.pmods if p.role == "host"]
    plugs = [p for p in rm.pmods if p.role == "plug"]

    def hostpos(ps):
        return "; ".join(f"{p.label} ({p.cx:.2f}, {p.cy:.2f})" for p in ps)

    rows = [
        ["Drawing", "ACC-01", "ACC-04"],
        ["Outline", f"{hat.outline.width:.1f} x {hat.outline.height:.1f} mm, "
                    f"R{hat.outline.corner_radius:.0f} corners",
         f"{rm.outline.width:.1f} x {rm.outline.height:.1f} mm, "
         f"R{rm.outline.corner_radius:.0f} corners"],
        ["Thickness", "not stated", f"{rm.outline.thickness:.1f} mm"],
        ["Mounting holes",
         f"{len(hat.holes)} x {hat.holes[0].dia:.2f} mm, the HAT pattern",
         "none"],
        ["Pmod hosts", f"{len(hat.pmods)}, right-angle, on two edges",
         f"{len(hosts)}, vertical, on the front face"],
        ["Host pin-field centres (x, y)", hostpos(hat.pmods), hostpos(hosts)],
        ["Host pitch",
         f"JA to JB {hat.pmods[0].cy - hat.pmods[1].cy:.2f} mm",
         f"{hosts[1].cx - hosts[0].cx:.2f} mm, both gaps"],
        ["Plugs into", "the Pi's 40-pin header, from above",
         f"the demoboard's 3 hosts: {len(plugs)} underside plugs at "
         f"({plugs[0].cx:.2f}, {plugs[0].cy:.2f}), ({plugs[1].cx:.2f}, "
         f"{plugs[1].cy:.2f}), ({plugs[2].cx:.2f}, {plugs[2].cy:.2f})"],
        ["Pi connection", "direct, as a HAT", "2x20 box header J1, ribbon cable"],
        ["Position on the assembly", "flat on top of the Pi, on M2.5 standoffs",
         "on edge in front of the demoboard, component side forward"],
    ]
    return table(["", "Digilent Pmod HAT Adapter", "Raspmod"], rows)


def demoboard_table() -> list[str]:
    """Where the Raspmod sits on each demoboard revision, along the front edge.

    Only X can be worked out from plan views: the Raspmod stands on edge,
    so its Y is the assembly's height and does not meet the demoboard's Y.
    """
    plug = next(p for p in RASPMOD.pmods if p.role == "plug" and p.label == "P1")
    # One row per distinct answer, naming every revision that gives it, the
    # way the sheet set merges mechanically identical revisions.
    groups: dict[tuple, list[str]] = {}
    for b in TT.values():
        hosts = sorted(b.pmods, key=lambda p: p.cx)
        if len(hosts) != 3:
            continue
        x0 = hosts[0].cx - plug.cx
        groups.setdefault((round(x0, 3), b.outline.width), []).append(b.title)
    rows = []
    for (x0, width), titles in groups.items():
        x1 = x0 + RASPMOD.outline.width
        rows.append([", ".join(titles), f"{width:.1f}", f"{x0:.2f}", f"{x1:.2f}",
                     "yes" if 0 <= x0 and x1 <= width else "no"])
    return table(["Demoboard", "Board width mm", "Raspmod left edge at x",
                  "Raspmod right edge at x", "Within the board's width"], rows)


def clkrst_residual() -> str | None:
    """Re-measure J9 against the demoboard SIL header, if the files are here."""
    try:
        from tools import kicad_extract, kicad_pcb
        from tools.kicad_extract import one
    except ImportError:
        return None
    files = {"v2.1.2": ("J3", "J17"), "v3.3": ("J11", "J9")}
    board = kicad_pcb.load(str(ROOT / "tmp" / "pcb" / "raspmod.kicad_pcb"))
    to_xy, _, _ = kicad_extract.frame(board)
    plug = one(board.footprints, "J2")
    j9 = one(board.footprints, "J9")
    pc = [to_xy(p.x, p.y) for p in plug.pads]
    centre = (sum(p[0] for p in pc) / 12, sum(p[1] for p in pc) / 12)
    j9_pins = {p.number: to_xy(p.x, p.y) for p in j9.pads}
    worst = 0.0
    for rev, (host_ref, sil_ref) in files.items():
        path = ROOT / "tmp" / "pcb" / f"{rev}.kicad_pcb"
        if not path.exists():
            return None
        db = kicad_pcb.load(str(path))
        dxy, _, _ = kicad_extract.frame(db)
        hp = [dxy(p.x, p.y) for p in one(db.footprints, host_ref).pads]
        hc = (sum(p[0] for p in hp) / 12, sum(p[1] for p in hp) / 12)
        sil = {p.number: dxy(p.x, p.y) for p in one(db.footprints, sil_ref).pads}
        # J9 pin 1 is nRST and pin 2 CLK; on the SIL, pad 2 is the reset and
        # pad 3 the clock.
        for j9_pin, sil_pad in (("1", "2"), ("2", "3")):
            dx = (j9_pins[j9_pin][0] - centre[0]) - (sil[sil_pad][0] - hc[0])
            dy = (j9_pins[j9_pin][1] - centre[1]) - (sil[sil_pad][1] - hc[1])
            worst = max(worst, abs(dx), abs(dy))
    return f"{worst:.2f}"


def replace_block(text: str, name: str, lines: list[str]) -> str:
    begin, end = f"<!-- {name}:begin -->", f"<!-- {name}:end -->"
    i, j = text.index(begin) + len(begin), text.index(end)
    return text[:i] + "\n\n" + "\n".join(lines) + text[j:]


def main() -> None:
    text = PAGE.read_text()
    text = replace_block(text, "mechanics", mechanics_table())
    text = replace_block(text, "demoboards", demoboard_table())
    text = replace_block(text, "pi-header", pi_header_table())
    text = replace_block(text, "ports", port_tables())
    residual = clkrst_residual()
    if residual is not None:
        text = re.sub(r"within \d+\.\d+ mm on both", f"within {residual} mm on both",
                      text)
        print(f"clock/reset pins re-measured: worst residual {residual} mm")
    else:
        print("demoboard files not in tmp/pcb; clock/reset residual left as written")
    PAGE.write_text(text)
    print(f"wrote {PAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
