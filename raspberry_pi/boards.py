"""Raspberry Pi mechanical data, from Raspberry Pi Ltd drawings.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber python \\
        raspberry_pi/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  This is the same way up as
Raspberry Pi Ltd draw their own plan views, with the 40-pin GPIO header along
the upper edge.

Note the Ethernet jack and the USB type A ports swap places between the Pi 3
and the Pi 4: on the Pi 3B/3B+ and on the Pi 5 the RJ45 sits in the lower right
corner with the USB ports above it, while on the Pi 4B the RJ45 is in the upper
right corner with the USB ports below.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, Source

BOARDS: dict[str, BoardSpec] = {}

#: Feature numbers are fixed across the family: a number means the same part on
#: every sheet.  A model that does not carry the part still gets a row, so a
#: gap in a schedule reads as "not on this board" rather than as an omission.
FEATURE_NUMBERS = {
    1: '40-pin GPIO header',
    2: 'Power input connector',
    3: 'Ethernet RJ45',
    4: 'USB type A, upper pair',
    5: 'USB type A, lower pair',
}


BOARDS['rpi3b'] = BoardSpec(
    key='rpi3b',
    title='Raspberry Pi 3 Model B and B+',
    subtitle='85 x 56 mm, both models',
    family="raspberrypi",
    front_edge="top",
    outline=Outline(width=85.0, height=56.0,
                    corner_radius=3.0),
    holes=(
        Hole(x=3.5, y=3.5, dia=2.75, label='MT1', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=61.5, y=3.5, dia=2.75, label='MT2', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=3.5, y=52.5, dia=2.75, label='MT3', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=61.5, y=52.5, dia=2.75, label='MT4', kind='mount', keepout_dia=None, tol=0.05),
    ),
    features=(
        Feature(key='gpio40', label='40-pin GPIO header', kind='header',
                x0=7.1, y0=50.0, x1=57.9, y1=55.0,
                number=1),
        Feature(key='usb_power', label='micro-USB power input', kind='usb_power',
                x0=6.85, y0=-0.6, x1=14.35, y1=4.71,
                number=2),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=65.65, y0=2.495, x1=87.0, y1=18.005,
                number=3),
        Feature(key='usb_a_1', label='USB 2.0 type A (upper pair)', kind='usb_a',
                x0=69.3, y0=39.65, x1=87.0, y1=53.57,
                number=4),
        Feature(key='usb_a_2', label='USB 2.0 type A (lower pair)', kind='usb_a',
                x0=69.3, y0=21.65, x1=87.0, y1=35.57,
                number=5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-mechanical-drawing.dxf',
               note="Raspberry Pi Ltd"),
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-plus-mechanical-drawing.dxf',
               note='Raspberry Pi Ltd, Raspberry Pi 3 Model B+'),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-mechanical-drawing.pdf',
               note='Drawing note on the Model B drawing, quoted: 4x M2.5 MOUNTING HOLES DRILLED TO 2.75 +/- 0.05mm. The B+ drawing gives no hole size, but its geometry is identical.'),
    ),
    notes=(
        'Hole IDs are assigned by this drawing and mean the same hole on every Raspberry Pi sheet.',
        'The Raspberry Pi 3 Model B and Raspberry Pi 3 Model B+ drawings agree on every hole and connector position, so one sheet covers both.',
        'The 40-pin GPIO header position is fixed by the Raspberry Pi HAT specification, so it is the same on every Raspberry Pi sheet.',
        "Design keep-outs to 6.2 mm diameter around every mounting hole, per the Raspberry Pi HAT specification; KEEPOUT gives what this model's own drawing shows.",
    ),
)

BOARDS['rpi4b'] = BoardSpec(
    key='rpi4b',
    title='Raspberry Pi 4 Model B',
    subtitle='85 x 56 mm',
    family="raspberrypi",
    front_edge="top",
    outline=Outline(width=85.0, height=56.0,
                    corner_radius=3.0),
    holes=(
        Hole(x=3.5, y=3.5, dia=2.7, label='MT1', kind='mount', keepout_dia=6.0, tol=None),
        Hole(x=61.5, y=3.5, dia=2.7, label='MT2', kind='mount', keepout_dia=6.0, tol=None),
        Hole(x=3.5, y=52.5, dia=2.7, label='MT3', kind='mount', keepout_dia=6.0, tol=None),
        Hole(x=61.5, y=52.5, dia=2.7, label='MT4', kind='mount', keepout_dia=6.0, tol=None),
    ),
    features=(
        Feature(key='gpio40', label='40-pin GPIO header', kind='header',
                x0=7.1, y0=50.0, x1=57.9, y1=55.0,
                number=1),
        Feature(key='usb_power', label='USB-C power input', kind='usb_power',
                x0=6.875, y0=-1.25, x1=15.525, y1=6.15,
                number=2),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=66.65, y0=37.995, x1=88.0, y1=53.505,
                number=3),
        Feature(key='usb_a_1', label='USB 3.0 type A (upper pair)', kind='usb_a',
                x0=70.5, y0=20.43, x1=88.0, y1=34.25,
                number=4),
        Feature(key='usb_a_2', label='USB 2.0 type A (lower pair)', kind='usb_a',
                x0=70.3, y0=1.65, x1=88.0, y1=15.57,
                number=5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.dxf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.dxf',
               note='Read from the DXF: hole and keep-out circles on layer 0.'),
    ),
    notes=(
        'Hole IDs are assigned by this drawing and mean the same hole on every Raspberry Pi sheet.',
        'The 40-pin GPIO header position is fixed by the Raspberry Pi HAT specification, so it is the same on every Raspberry Pi sheet.',
        "Design keep-outs to 6.2 mm diameter around every mounting hole, per the Raspberry Pi HAT specification; KEEPOUT gives what this model's own drawing shows.",
    ),
)

BOARDS['rpi5'] = BoardSpec(
    key='rpi5',
    title='Raspberry Pi 5',
    subtitle='85 x 56 mm',
    family="raspberrypi",
    front_edge="top",
    outline=Outline(width=85.0, height=56.0,
                    corner_radius=3.0),
    holes=(
        Hole(x=3.5, y=3.5, dia=2.7, label='MT1', kind='mount', keepout_dia=5.8, tol=None),
        Hole(x=61.5, y=3.5, dia=2.7, label='MT2', kind='mount', keepout_dia=5.8, tol=None),
        Hole(x=3.5, y=52.5, dia=2.7, label='MT3', kind='mount', keepout_dia=5.8, tol=None),
        Hole(x=61.5, y=52.5, dia=2.7, label='MT4', kind='mount', keepout_dia=5.8, tol=None),
        Hole(x=3.5, y=9.497, dia=3.0, label='AUX1', kind='aux', keepout_dia=None, tol=None),
        Hole(x=61.5, y=46.504, dia=3.0, label='AUX2', kind='aux', keepout_dia=None, tol=None),
    ),
    features=(
        Feature(key='gpio40', label='40-pin GPIO header', kind='header',
                x0=7.1, y0=50.0, x1=57.9, y1=55.0,
                number=1),
        Feature(key='usb_power', label='USB-C power input', kind='usb_power',
                x0=7.8, y0=-1.316, x1=14.52, y1=5.987,
                number=2),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=66.72, y0=2.212, x1=87.96, y1=18.193,
                number=3),
        Feature(key='usb_a_1', label='USB 3.0 type A (upper pair)', kind='usb_a',
                x0=70.92, y0=40.842, x1=87.24, y1=53.154,
                number=4),
        Feature(key='usb_a_2', label='USB 3.0 type A (lower pair)', kind='usb_a',
                x0=70.92, y0=22.92, x1=87.24, y1=35.16,
                number=5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf',
               note='Hole diameter dimensioned on the drawing as ø2.7 mm; the keep-out circle is drawn and measures 5.80 mm.'),
    ),
    notes=(
        'Hole IDs are assigned by this drawing and mean the same hole on every Raspberry Pi sheet.',
        'The 40-pin GPIO header position is fixed by the Raspberry Pi HAT specification, so it is the same on every Raspberry Pi sheet.',
        "Design keep-outs to 6.2 mm diameter around every mounting hole, per the Raspberry Pi HAT specification; KEEPOUT gives what this model's own drawing shows.",
    ),
)
