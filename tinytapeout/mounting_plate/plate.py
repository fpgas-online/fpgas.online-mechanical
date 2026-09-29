"""Tiny Tapeout generic mounting plate.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python tinytapeout/mounting_plate/design.py

One plate that accepts any Tiny Tapeout demo board revision on standoffs while
holding the Pmod host headers in a single fixed place.  See the module
docstring of the generating script for how the pattern is derived.

Plate coordinates: origin at the lower-left corner of the plate, X right, Y up,
viewed from the side the board mounts on.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Hole, Outline, Slot, Source

#: Pmod host pin-field centres, in plate coordinates.  These are the whole
#: point of the plate: they do not move when the board revision changes.
PMOD_SLOT_X = (38.75, 61.61, 84.47)
PMOD_ROW_Y = 9.0
PMOD_PITCH = 22.86

#: Plate face to board underside: what every board stands on.  A choice, not
#: a published figure; design.py says why it is at least what Tiny Tapeout's
#: own printed base gives the board.  UPSTREAM_BASE_STUD is that base's stud,
#: from the file UPSTREAM_BASE_REF, and verify.py reads the file back.
STANDOFF_HEIGHT = 8.0
UPSTREAM_BASE_STUD = 6.4
UPSTREAM_BASE_REF = 'https://github.com/TinyTapeout/tt-demo-pcb/blob/521108f4abad8e7a57e517b170d3d62ceb06667f/case/tt06_demo_base.scad'

#: The Pmod connector body relative to its pin-field centre, as
#: (dx0, dx1, dy0, dy1).  Identical on every revision; the generator checks it
#: rather than assuming it.  dy0 is negative because the body overhangs the
#: edge its host faces, and that overhang is what fixes the plate's front edge.
PMOD_BODY = (-8.15, 8.1, -11.78, 3.07)

#: Where each revision's USB-C connector lands, in plate coordinates, as
#: (x0, y0, x1, y1).  Marked on the plate because a chassis has to open for it
#: and it moves further between revisions than anything else on the board.
USB_C = {
    'DB mpw': (28.17, 3.285, 38.31, 11.185),
    'DB 4+': (32.935, 77.775, 45.675, 86.075),
    'DB 06+': (72.425, 74.955, 83.065, 84.375),
    'DB ETR v3.2': (90.29, 78.0, 100.93, 87.42),
    'DB ETR v3.3': (90.29, 83.0, 100.93, 92.42),
}

#: Offset from the design frame (origin at the leftmost Pmod pin-field centre)
#: to plate coordinates.
DATUM_X = 38.75
DATUM_Y = 9.0

#: How to place each board revision: add these to a board coordinate to get a
#: plate coordinate.
PLACEMENTS = {
    'DB mpw': dict(revision='tt123-v2.2.6', revisions=('tt123-v2.2.5', 'tt123-v2.2.6'),
        shuttles=('TT02', 'TT03'), dx=19.760, dy=4.535, first_pmod_position=2, pmod_count=2),
    'DB 4+': dict(revision='v1.2.2', revisions=('v1.2.1', 'v1.2.2', 'v1.2.3'),
        shuttles=('TT03p5', 'TT04', 'TT05'), dx=11.055, dy=4.725, first_pmod_position=1, pmod_count=3),
    'DB 06+': dict(revision='v2.0.1', revisions=('v2.0.1', 'v2.1.0', 'v2.1.2'),
        shuttles=('TT06', 'TT07', 'TT08'), dx=10.745, dy=5.225, first_pmod_position=1, pmod_count=3),
    'DB ETR v3.2': dict(revision='v3.2', revisions=('v3.2',),
        shuttles=('TT09', 'TTSKY25a', 'TTSKY25b', 'TTGF0p2'), dx=19.400, dy=5.770, first_pmod_position=1, pmod_count=3),
    'DB ETR v3.3': dict(revision='v3.3', revisions=('v3.3',),
        shuttles=(), dx=19.400, dy=5.770, first_pmod_position=1, pmod_count=3),
}

PLATE = BoardSpec(
    key="tt-generic-mounting-plate",
    title="TT Generic Mounting Plate",
    subtitle="Accepts every demo board revision, Pmod hosts fixed in place",
    family="mountingplate",
    outline=Outline(width=135.0, height=101.0, corner_radius=4.0, thickness=3.0),
    holes=(
        Hole(x=23.455, y=81.778, dia=3.40, label='DB mpw:MT3|DB ETR v3.2:MT1', kind="board", tol=None),  # Serves 2 revision positions spread 0.111 mm; drilled at their midpoint.
        Hole(x=23.510, y=8.285, dia=3.40, label='DB mpw:MT1', kind="board", tol=None),
        Hole(x=120.510, y=8.285, dia=3.40, label='DB mpw:MT2', kind="board", tol=None),
        Hole(x=120.510, y=81.785, dia=3.40, label='DB mpw:MT4', kind="board", tol=None),
        Hole(x=111.805, y=8.475, dia=3.40, label='DB 4+:MT2', kind="board", tol=None),
        Hole(x=111.805, y=81.975, dia=3.40, label='DB 4+:MT4', kind="board", tol=None),
        Hole(x=106.745, y=13.225, dia=3.40, label='DB 06+:MT2', kind="board", tol=None),
        Hole(x=106.745, y=79.725, dia=3.40, label='DB 06+:MT4', kind="board", tol=None),
        Hole(x=96.400, y=14.270, dia=3.40, label='DB ETR v3.2:MT2|DB ETR v3.3:MT2', kind="board", tol=None),
        Hole(x=23.400, y=86.770, dia=3.40, label='DB ETR v3.3:MT1', kind="board", tol=None),
        Hole(x=5.373, y=22.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=5.373, y=74.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=129.630, y=22.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=129.630, y=74.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=42.000, y=95.885, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=93.000, y=95.885, dia=4.30, label="PLATE", kind="plate"),
    ),
    slots=(
        Slot(x0=14.245, y0=8.725, x1=14.805, y1=8.475, width=3.40, label='DB 4+:MT1|DB 06+:MT1',
             note="Two revisions want a fastener 0.613 mm apart here, too close to drill as separate holes."),
        Slot(x0=14.245, y0=79.725, x1=14.805, y1=81.975, width=3.40, label='DB 4+:MT3|DB 06+:MT3',
             note="Two revisions want a fastener 2.319 mm apart here, too close to drill as separate holes."),
    ),
    sources=(
        Source(label="Derived from",
               ref="tinytapeout/boards.py",
               note="Board outlines, mounting holes and Pmod host positions "
                    "for every Tiny Tapeout demo board revision, extracted "
                    "from the upstream KiCad files."),
        Source(label="Standoff height",
               ref='https://github.com/TinyTapeout/tt-demo-pcb/blob/521108f4abad8e7a57e517b170d3d62ceb06667f/case/tt06_demo_base.scad',
               note="Tiny Tapeout's own printed base: Height = 8 with a 1.6 "
                    "mm PCB let into it, so its studs stand the board "
                    "6.4 mm up. The plate's 8 mm is not less."),
        Source(label="Pmod host pitch",
               ref="https://mith.ro/pmod-spec/",
               note="Digilent mandate .90 in (22.86 mm) between adjacent host "
                    "ports on a board edge, which is why one plate can serve "
                    "every revision."),
    ),
    notes=(
        "Board holes and slots are 3.4 mm, clearance for M3 standoffs. "
        "Plate fixings are 4.3 mm, clearance for M4. A slot serves two "
        "boards whose holes are too close together to drill separately.",
        "Pmod connector bodies overhang the front (lower) edge by 2.78 mm; "
        "keep it clear so a peripheral can plug in.",
        "Boards stand on M3 x 8 mm standoffs, plate face to "
        "board underside.",
        "Cut file: tt-generic-mounting-plate.dxf. Sizes are finished sizes.",
    ),
)
