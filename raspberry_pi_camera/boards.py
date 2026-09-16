"""Raspberry Pi camera module mechanical data, from Raspberry Pi Ltd drawings.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with pdfplumber python \\
        raspberry_pi_camera/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  Top view means the lens side,
which is how Raspberry Pi draw the Camera Module 3 plan; the Camera Module 2
drawing is the same view turned a quarter turn on the page, and the extractor
turns it back.

The board is 25 mm across and 23.862 mm up.  The camera FFC connector is on
the underside, against the upper edge; the lens is near that same edge, at
14.4 mm up; the four mounting holes are 21 mm apart across and 12.5 mm apart
up, the lower pair 2 mm in from the lower and side edges.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, Source

BOARDS: dict[str, BoardSpec] = {}

#: Feature numbers are fixed across the family: a number means the same part
#: on every sheet.
FEATURE_NUMBERS = {
    1: 'Lens and sensor module',
    2: 'Camera FFC connector, on the underside',
}


BOARDS['cm2'] = BoardSpec(
    key='cm2',
    title='Raspberry Pi Camera Module 2',
    subtitle='25 x 23.862 mm, Sony IMX219',
    family="raspberrypicamera",
    front_edge="top",
    outline=Outline(width=25.0, height=23.862,
                    corner_radius=2.0),
    holes=(
        Hole(x=2.0, y=2.003, dia=2.2, label='MT1', kind='mount', keepout_dia=None),
        Hole(x=22.977, y=2.003, dia=2.2, label='MT2', kind='mount', keepout_dia=None),
        Hole(x=2.0, y=14.516, dia=2.2, label='MT3', kind='mount', keepout_dia=None),
        Hole(x=22.977, y=14.516, dia=2.2, label='MT4', kind='mount', keepout_dia=None),
    ),
    features=(
        Feature(key='lens', label='Lens and sensor module', kind='lens',
                x0=8.264, y0=10.157, x1=16.713, y1=18.649,
                side='top', number=1),
        Feature(key='ffc', label='Camera FFC connector, 15-way', kind='connector',
                x0=2.046, y0=18.333, x1=22.93, y1=23.851,
                side='bottom', number=2),
    ),
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/camera/camera-module-2-mechanical-drawing.pdf',
               note='Raspberry Pi Ltd, RPI-CAM-V2_1, 12/11/2015'),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/camera/camera-module-2-mechanical-drawing.pdf',
               note='Drawing note, quoted: 4x 2.2mm diameter holes. No land or keep-out is shown.'),
    ),
    notes=(
        "Hole IDs are this drawing's, the same hole on every camera sheet here.",
        'Optical axis at X 12.49, Y 14.40 from the datum, the centre of feature 1. Feature 1 is dimensioned 8.5 square on the drawing. Its lower body, stepped, reaches to 2.76 from the lower edge across 6.72 to 16.14.',
        'The source drawing is a plan view only and gives no height.',
        'Source read as a 1.5055:1 plot: scale from the 21.0 x 12.5 hole rectangle, overall dimensions then back within 0.031.',
        'Every figure printed on the source is an outlined path, not text: its geometry is machine-read, its printed dimensions are transcribed by eye.',
    ),
)

BOARDS['cm3'] = BoardSpec(
    key='cm3',
    title='Raspberry Pi Camera Module 3',
    subtitle='25 x 23.862 mm, standard and wide, Sony IMX708',
    family="raspberrypicamera",
    front_edge="top",
    outline=Outline(width=25.0, height=23.862,
                    corner_radius=2.0, thickness=1.12),
    holes=(
        Hole(x=2.002, y=2.004, dia=2.2, label='MT1', kind='mount', keepout_dia=4.75),
        Hole(x=23.002, y=2.004, dia=2.2, label='MT2', kind='mount', keepout_dia=4.75),
        Hole(x=2.002, y=14.504, dia=2.2, label='MT3', kind='mount', keepout_dia=4.75),
        Hole(x=23.002, y=14.504, dia=2.2, label='MT4', kind='mount', keepout_dia=4.75),
    ),
    features=(
        Feature(key='lens', label='Lens and sensor module', kind='lens',
                x0=7.102, y0=9.004, x1=17.902, y1=19.804,
                side='top', number=1),
        Feature(key='ffc', label='Camera FFC connector, 15-way', kind='connector',
                x0=2.688, y0=18.153, x1=22.297, y1=23.863,
                side='bottom', number=2),
    ),
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf',
               note='Raspberry Pi Ltd, RP-008153-DS-1'),
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/camera/camera-module-3-wide-mechanical-drawing.pdf',
               note='Raspberry Pi Ltd, RP-008155-DS-1'),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf',
               note='o2.2, with an o4.75 land round each one.'),
    ),
    notes=(
        "Hole IDs are this drawing's, the same hole on every camera sheet here.",
        "Optical axis at X 12.50, Y 14.40 from the datum, the centre of feature 1. Clear aperture o5.75 standard, o6.95 wide. Feature 1's lower body, 8.9 across, reaches to 1.70 from the lower edge.",
        "Overall thickness printed 11.3 standard, 12 wide, lens tip to connector back; lens assembly 6.98 and 8.3 above the board. The source's elevations scale 1.2 short of those, so no height is drawn here.",
        'Source read as a true 1:1 plot: scale from the 21.0 x 12.5 hole rectangle, overall dimensions then back within 0.004.',
        'The standard and Camera Module 3 Wide drawings agree on the outline, holes and lens module within 0.05, so one sheet covers both.',
    ),
)
