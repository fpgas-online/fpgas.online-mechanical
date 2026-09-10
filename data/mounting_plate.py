"""Tiny Tapeout generic mounting plate.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python scripts/design_mounting_plate.py

One plate that accepts any Tiny Tapeout demo board revision on standoffs while
holding the Pmod host headers in a single fixed place.  See the module
docstring of the generating script for how the pattern is derived.

Plate coordinates: origin at the lower-left corner of the plate, X right, Y up,
viewed from the side the board mounts on.
"""

from __future__ import annotations

from .schema import BoardSpec, Hole, Outline, Slot, Source

#: Pmod host pin-field centres, in plate coordinates.  These are the whole
#: point of the plate: they do not move when the board revision changes.
PMOD_SLOT_X = (38.75, 61.61, 84.47)
PMOD_ROW_Y = 9.0
PMOD_PITCH = 22.86

#: Offset from the design frame (origin at the leftmost Pmod pin-field centre)
#: to plate coordinates.
DATUM_X = 38.75
DATUM_Y = 9.0

#: How to place each board revision: add these to a board coordinate to get a
#: plate coordinate.
PLACEMENTS = {
    'TT01-03': dict(revision='tt123-v2.2.6', revisions=('tt123-v2.2.6',),
        shuttles=('TT01', 'TT02', 'TT03'), dx=19.760, dy=4.535, first_pmod_position=2, pmod_count=2),
    'TT04-05': dict(revision='v1.2.2', revisions=('v1.2.2', 'v1.2.3'),
        shuttles=('TT04', 'TT05'), dx=11.055, dy=4.725, first_pmod_position=1, pmod_count=3),
    'TT06-08': dict(revision='v2.0.1', revisions=('v2.0.1', 'v2.1.0', 'v2.1.2'),
        shuttles=('TT06', 'TT07', 'TT08'), dx=10.745, dy=5.225, first_pmod_position=1, pmod_count=3),
    'v3.2': dict(revision='v3.2', revisions=('v3.2',),
        shuttles=(), dx=19.400, dy=5.770, first_pmod_position=1, pmod_count=3),
    'v3.3': dict(revision='v3.3', revisions=('v3.3',),
        shuttles=(), dx=19.400, dy=5.770, first_pmod_position=1, pmod_count=3),
}

PLATE = BoardSpec(
    key="tt-generic-mounting-plate",
    title="Tiny Tapeout Generic Mounting Plate",
    subtitle="Accepts every demo board revision, Pmod hosts fixed in place",
    family="mountingplate",
    outline=Outline(width=135.0, height=101.0, corner_radius=4.0, thickness=3.0),
    holes=(
        Hole(x=23.455, y=81.778, dia=3.40, label='TT01-03:MT3+v3.2:MT1', kind="board", tol=None),  # Serves 2 revision positions spread 0.111 mm; drilled at their midpoint.
        Hole(x=23.400, y=86.770, dia=3.40, label='v3.3:MT1', kind="board", tol=None),
        Hole(x=23.510, y=8.285, dia=3.40, label='TT01-03:MT1', kind="board", tol=None),
        Hole(x=96.400, y=14.270, dia=3.40, label='v3.2:MT2+v3.3:MT2', kind="board", tol=None),
        Hole(x=106.745, y=13.225, dia=3.40, label='TT06-08:MT2', kind="board", tol=None),
        Hole(x=106.745, y=79.725, dia=3.40, label='TT06-08:MT4', kind="board", tol=None),
        Hole(x=111.805, y=8.475, dia=3.40, label='TT04-05:MT2', kind="board", tol=None),
        Hole(x=111.805, y=81.975, dia=3.40, label='TT04-05:MT4', kind="board", tol=None),
        Hole(x=120.510, y=8.285, dia=3.40, label='TT01-03:MT2', kind="board", tol=None),
        Hole(x=120.510, y=81.785, dia=3.40, label='TT01-03:MT4', kind="board", tol=None),
        Hole(x=5.373, y=22.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=5.373, y=74.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=129.630, y=22.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=129.630, y=74.000, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=42.000, y=95.885, dia=4.30, label="PLATE", kind="plate"),
        Hole(x=93.000, y=95.885, dia=4.30, label="PLATE", kind="plate"),
    ),
    slots=(
        Slot(x0=14.245, y0=8.725, x1=14.805, y1=8.475, width=3.40, label='TT04-05:MT1+TT06-08:MT1',
             note="Two revisions want a fastener 0.613 mm apart here, too close to drill as separate holes."),
        Slot(x0=14.245, y0=79.725, x1=14.805, y1=81.975, width=3.40, label='TT04-05:MT3+TT06-08:MT3',
             note="Two revisions want a fastener 2.319 mm apart here, too close to drill as separate holes."),
    ),
    sources=(
        Source(label="Derived from",
               ref="data/tinytapeout_boards.py",
               note="Board outlines, mounting holes and Pmod host positions "
                    "for every Tiny Tapeout demo board revision, extracted "
                    "from the upstream KiCad files."),
        Source(label="Pmod host pitch",
               ref="https://digilent.com/reference/_media/reference/pmod/"
                   "pmod-interface-specification-1_2_0.pdf",
               note="Digilent mandate .90 in (22.86 mm) between adjacent host "
                    "ports on a board edge, which is why one plate can serve "
                    "every revision."),
    ),
    notes=(
        "Fit the board on standoffs. A board uses only the holes and slots "
        "its USED BY row names.",
        "Board holes and slots are 3.4 mm, a close clearance fit on M3. "
        "Plate fixings are 4.3 mm, a clearance fit on M4. A slot spans two "
        "revisions whose holes are too close together to drill separately.",
        "The Pmod host connector bodies overhang the plate's front edge by "
        "2.78 mm, so a peripheral module plugs into clear air.",
        "Cut file: tt-generic-mounting-plate.dxf, four layers. Sizes here are "
        "finished sizes; allow for your cutter's kerf.",
    ),
)
