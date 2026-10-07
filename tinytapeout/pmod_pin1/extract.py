#!/usr/bin/env python3
"""Generate ``tinytapeout/pmod_pin1/pmods_v3p2.py`` from the v3.2 board file.

What the pin 1 picture of the demo board draws, read out of Tiny Tapeout's
KiCad board file: each Pmod socket's pads with their numbers, shapes and
nets, the corner mark its footprint prints in silkscreen, the socket body
its footprint draws on the fabrication layer, and the silkscreen the board
prints round it -- the box, the block over pins 5 and 11, and the words.

The file is ``tinytapeout-demo.kicad_pcb`` at commit 0277545 of
github.com/TinyTapeout/tt-demo-pcb, the last commit at rev 3.2.  Its blob
there is the one d830790 ("v3.2 as prototyped") has, which the ``TT-DB-V32``
sheet is drawn from; that is checked, not assumed, so the picture and the
sheet are of one board file.

Which designator is which socket is ``tinytapeout/extract.py``'s ``ROLES``,
imported rather than restated.  Every claim the picture makes about the
board is checked here, and the run stops if the file says otherwise: pad 1
is the only square pad, pins 5 and 11 are on GND and 6 and 12 on +3V3, the
label printed over pad 1 ends in 0, and the footprint's corner mark is at
the pin 6 end of the socket, not the pin 1 end.

Run (after tools/fetch_pmod_pin1.sh):
    uv run --no-project python tinytapeout/pmod_pin1/extract.py
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tinytapeout.extract import ROLES  # noqa: E402
from tools import kicad_pcb  # noqa: E402

REPO = ROOT / "tmp" / "src" / "tt-demo-pcb"
URL = "https://github.com/TinyTapeout/tt-demo-pcb"
PATH = "tinytapeout-demo.kicad_pcb"
COMMIT = "0277545"
#: The commit the TT-DB-V32 sheet reads, whose board file this must be.
SHEET_COMMIT = "d830790"
OUT = Path(__file__).resolve().parent / "pmods_v3p2.py"

#: The window round a socket that its own printing is taken from, in
#: millimetres from its pads: across, past pad 6 and pad 1; and up, away
#: from the board edge, from the row of pads 1 to 6.  It holds the socket's
#: box, its block and its words and none of the next socket's, nor the side
#: headers' labels, which sit level with the pads rather than above them --
#: the run prints what it took, so that can be seen.
ACROSS = 1.5
UP = 7.0


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True,
                          capture_output=True, text=True).stdout


def r(v: float) -> float:
    return round(v, 4)


def socket(board: kicad_pcb.Board, art: kicad_pcb.Graphics, ref: str,
           name: str) -> dict:
    fp, = board.by_reference(ref)
    pads = {p.number: p for p in fp.pads}
    if sorted(pads, key=int) != [str(n) for n in range(1, 13)]:
        raise SystemExit(f"{ref}: pads {sorted(pads)}, not 1 to 12")
    square = [n for n, p in pads.items() if p.shape == "rect"]
    if square != ["1"]:
        raise SystemExit(f"{ref}: square pads {square}, not pad 1 alone")
    nets = {n: p.net for n, p in pads.items()}
    for n, want in (("5", "GND"), ("11", "GND"), ("6", "+3V3"),
                    ("12", "+3V3")):
        if nets[n] != want:
            raise SystemExit(f"{ref}: pad {n} is on {nets[n]!r}, not {want}")
    p1, p6 = pads["1"], pads["6"]
    if abs(p1.y - p6.y) > 1e-6:
        raise SystemExit(f"{ref}: pads 1 and 6 are not in one row")
    row = p1.y
    x0, x1 = sorted((p1.x, p6.x))
    x0, x1 = x0 - ACROSS, x1 + ACROSS

    def mine(pts) -> bool:
        return all(x0 <= x <= x1 and row - UP <= y <= row for x, y in pts)

    # The footprint's own printing on the board side of pads 1 to 6: its
    # corner mark.  The rest of its silkscreen is ticks between the pads and
    # the socket body's outline over the edge, which is not on the board.
    mark = [s for s in fp.silk if s.y1 <= row and s.y2 <= row]
    ends = [(s.x1, s.y1) for s in mark] + [(s.x2, s.y2) for s in mark]
    if len(mark) != 2:
        raise SystemExit(f"{ref}: {len(mark)} silk lines beside pads 1-6, "
                         "not the two of a corner mark")
    corner = [p for p in ends if ends.count(p) == 2]
    if len(corner) != 2:
        raise SystemExit(f"{ref}: the silk lines beside pads 1-6 do not meet")
    cx, cy = corner[0]
    to6, to1 = math.dist((cx, cy), (p6.x, p6.y)), math.dist((cx, cy),
                                                            (p1.x, p1.y))
    if not to6 < to1:
        raise SystemExit(f"{ref}: the corner mark is nearer pad 1 than pad 6")

    # The body: the footprint's fabrication outline past the board edge.
    edge = board.outline_bbox()[3]
    body = [s for s in fp.fab if s.y1 >= edge - 0.5 and s.y2 >= edge - 0.5]

    texts = [t for t in art.texts if mine([(t.x, t.y)])]
    # The labels over the pads stand in the line just above them, each
    # within half a pitch of its pad; the bus name stands higher.
    over1 = [t for t in texts
             if abs(t.x - p1.x) < 1.27 and row - t.y < 1.5]
    if len(over1) != 1 or not over1[0].text.endswith("0"):
        raise SystemExit(f"{ref}: the label over pad 1 is "
                         f"{[t.text for t in over1]}, not one ending in 0")
    if name not in [t.text for t in texts]:
        raise SystemExit(f"{ref}: {name!r} is not printed over it")
    return dict(
        ref=ref, name=name,
        pads=tuple((n, pads[n].shape, r(pads[n].x), r(pads[n].y),
                    r(pads[n].size[0]), nets[n])
                   for n in sorted(pads, key=int)),
        mark=tuple((r(s.x1), r(s.y1), r(s.x2), r(s.y2)) for s in mark),
        corner=(r(cx), r(cy)),
        body=tuple((r(s.x1), r(s.y1), r(s.x2), r(s.y2)) for s in body),
        lines=tuple((r(s.x1), r(s.y1), r(s.x2), r(s.y2))
                    for s in art.segments
                    if mine([(s.x1, s.y1), (s.x2, s.y2)])),
        arcs=tuple((r(a.x1), r(a.y1), r(a.xm), r(a.ym), r(a.x2), r(a.y2))
                   for a in art.arcs
                   if mine([(a.x1, a.y1), (a.x2, a.y2)])),
        blocks=tuple((r(b.x1), r(b.y1), r(b.x2), r(b.y2)) for b in art.rects
                     if b.filled and mine([(b.x1, b.y1)])),
        texts=tuple((t.text, r(t.x), r(t.y), t.height, " ".join(t.justify),
                     t.bold) for t in sorted(texts, key=lambda t: (t.y, t.x))),
    )


HEADER = '''"""The Tiny Tapeout demo board v3.2's Pmod sockets, for the pin 1 picture.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python tinytapeout/pmod_pin1/extract.py

Read out of {url}
{path} at commit {commit}, whose board file is the one {sheet} has
(blob {blob}).  KiCad coordinates: millimetres, Y down, top
view, so the board's front edge, the one the sockets face, is at the
largest Y.  Each socket's ``pads`` are (number, shape, x, y, size, net);
``mark`` the lines of its footprint's silkscreen corner mark and ``corner``
where they meet; ``body`` its fabrication outline past the board edge;
``lines``, ``arcs``, ``blocks`` and ``texts`` (text, x, y, height, justify,
bold) the board's own front silkscreen round it.
"""

SOURCE = {{
    "url": {url!r},
    "path": {path!r},
    "commit": {commit!r},
    "same_as": {sheet!r},
    "blob": {blob!r},
}}

#: The board's front edge, the Edge.Cuts line the sockets face, and how far
#: it runs.
FRONT_EDGE_Y = {edge_y!r}
FRONT_EDGE_X = {edge_x!r}

SOCKETS = (
'''


def main() -> None:
    blob = git("rev-parse", f"{COMMIT}:{PATH}").strip()
    sheet = git("rev-parse", f"{SHEET_COMMIT}:{PATH}").strip()
    if blob != sheet:
        raise SystemExit(f"{PATH} at {COMMIT} is not the one at "
                         f"{SHEET_COMMIT}, which TT-DB-V32 is drawn from")
    board = kicad_pcb.Board(git("show", f"{COMMIT}:{PATH}"))
    art = board.graphics("F.SilkS")
    roles = ROLES["v3.2"]
    sockets = [socket(board, art, ref, name)
               for ref, name in zip(roles["pmods"], roles["pmod_labels"])]

    segs, _arcs, _circles = board.edge_cuts()
    edge_y = board.outline_bbox()[3]
    front = [s for s in segs if s.y1 == edge_y and s.y2 == edge_y]
    if len(front) != 1:
        raise SystemExit(f"{len(front)} Edge.Cuts lines along the front edge")
    edge_x = tuple(sorted((front[0].x1, front[0].x2)))

    out = [HEADER.format(url=URL, path=PATH, commit=COMMIT,
                         sheet=SHEET_COMMIT, blob=blob[:12], edge_y=edge_y,
                         edge_x=edge_x)]
    for s in sockets:
        out.append("    {\n")
        for k, v in s.items():
            if isinstance(v, tuple) and v and isinstance(v[0], tuple):
                out.append(f"        {k!r}: (\n")
                out.extend(f"            {item!r},\n" for item in v)
                out.append("        ),\n")
            else:
                out.append(f"        {k!r}: {v!r},\n")
        out.append("    },\n")
        print(f"{s['ref']} {s['name']:6s} pad 1 at {s['pads'][0][2:4]}, "
              f"corner mark at {s['corner']}; {len(s['lines'])} lines, "
              f"{len(s['arcs'])} arcs, {len(s['blocks'])} blocks; "
              + " ".join(t[0] for t in s["texts"]))
    out.append(")\n")
    OUT.write_text("".join(out))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
