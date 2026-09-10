"""Raspberry Pi mechanical data, from Raspberry Pi Ltd drawings.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber python \\
        scripts/extract_raspberry_pi.py

Coordinates follow :mod:`data.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  This is the same way up as
Raspberry Pi Ltd draw their own plan views, with the 40-pin GPIO header along
the upper edge.

Note the Ethernet jack and the USB type A ports swap places between the Pi 3
and the Pi 4: on the Pi 3B/3B+ and on the Pi 5 the RJ45 sits in the lower right
corner with the USB ports above it, while on the Pi 4B the RJ45 is in the upper
right corner with the USB ports below.
"""

from __future__ import annotations

from .schema import BoardSpec, Feature, Hole, Outline, Source

BOARDS: dict[str, BoardSpec] = {}


BOARDS['rpi3b'] = BoardSpec(
    key='rpi3b',
    title='Raspberry Pi 3 Model B',
    subtitle='85 x 56 mm',
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
                x0=7.1, y0=50.0, x1=57.9, y1=55.0),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=65.65, y0=2.495, x1=87.0, y1=18.005),
        Feature(key='usb_a_1', label='USB 2.0 type A (upper pair)', kind='usb_a',
                x0=69.3, y0=39.65, x1=87.0, y1=53.57),
        Feature(key='usb_a_2', label='USB 2.0 type A (lower pair)', kind='usb_a',
                x0=69.3, y0=21.65, x1=87.0, y1=35.57),
        Feature(key='usb_power', label='micro-USB power input', kind='usb_power',
                x0=6.85, y0=-0.6, x1=14.35, y1=4.71),
        Feature(key='hdmi', label='HDMI type A', kind='connector',
                x0=24.75, y0=-1.5, x1=39.25, y1=10.65),
        Feature(key='av', label='3.5 mm A/V jack', kind='connector',
                x0=50.0, y0=0.0, x1=57.0, y1=12.5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-mechanical-drawing.dxf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-mechanical-drawing.pdf',
               note='Drawing note, quoted: 4x M2.5 MOUNTING HOLES DRILLED TO 2.75 +/- 0.05mm.'),
    ),
    notes=(
        "Connector outlines are the component body as drawn by Raspberry Pi Ltd, overhang past the board edge included.",
        'Mounting hole diameter: Drawing note, quoted: 4x M2.5 MOUNTING HOLES DRILLED TO 2.75 +/- 0.05mm.',
        'Hole IDs are assigned by this drawing, bottom row first then left to right, and mean the same thing on every Raspberry Pi sheet here.',
        "Design mounting hole keep-outs to 6.2 mm diameter on every model. That is what the Raspberry Pi HAT mechanical specification (github.com/raspberrypi/hats) requires around each hole, and it is the largest of the figures the individual models publish. The KEEPOUT column gives what this model's own drawing shows, which is not always anything.",
        "Hole positions are the 3.5 mm inset and 58 x 49 mm rectangle dimensioned on this model's drawing.",
    ),
)

BOARDS['rpi3bplus'] = BoardSpec(
    key='rpi3bplus',
    title='Raspberry Pi 3 Model B+',
    subtitle='85 x 56 mm',
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
                x0=7.1, y0=50.0, x1=57.9, y1=55.0),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=65.65, y0=2.495, x1=87.0, y1=18.005),
        Feature(key='usb_a_1', label='USB 2.0 type A (upper pair)', kind='usb_a',
                x0=69.3, y0=39.65, x1=87.0, y1=53.57),
        Feature(key='usb_a_2', label='USB 2.0 type A (lower pair)', kind='usb_a',
                x0=69.3, y0=21.65, x1=87.0, y1=35.57),
        Feature(key='usb_power', label='micro-USB power input', kind='usb_power',
                x0=6.85, y0=-0.6, x1=14.35, y1=4.71),
        Feature(key='hdmi', label='HDMI type A', kind='connector',
                x0=24.75, y0=-1.5, x1=39.25, y1=10.65),
        Feature(key='av', label='3.5 mm A/V jack', kind='connector',
                x0=50.0, y0=0.0, x1=57.0, y1=12.5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-plus-mechanical-drawing.dxf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-plus-mechanical-drawing.pdf',
               note='Carried over from the Pi 3 Model B drawing, which states 4x M2.5 holes drilled to 2.75 +/-0.05 mm. The 3B+ drawing gives no hole size; the two boards share an identical outline, hole pattern and DXF geometry.'),
    ),
    notes=(
        "Connector outlines are the component body as drawn by Raspberry Pi Ltd, overhang past the board edge included.",
        'Mounting hole diameter: Carried over from the Pi 3 Model B drawing, which states 4x M2.5 holes drilled to 2.75 +/-0.05 mm. The 3B+ drawing gives no hole size; the two boards share an identical outline, hole pattern and DXF geometry.',
        'Hole IDs are assigned by this drawing, bottom row first then left to right, and mean the same thing on every Raspberry Pi sheet here.',
        "Design mounting hole keep-outs to 6.2 mm diameter on every model. That is what the Raspberry Pi HAT mechanical specification (github.com/raspberrypi/hats) requires around each hole, and it is the largest of the figures the individual models publish. The KEEPOUT column gives what this model's own drawing shows, which is not always anything.",
        "Hole positions are the 3.5 mm inset and 58 x 49 mm rectangle dimensioned on this model's drawing.",
    ),
)

BOARDS['rpi3aplus'] = BoardSpec(
    key='rpi3aplus',
    title='Raspberry Pi 3 Model A+',
    subtitle='65 x 56 mm',
    family="raspberrypi",
    front_edge="top",
    outline=Outline(width=65.0, height=56.0,
                    corner_radius=3.0),
    holes=(
        Hole(x=3.5, y=3.5, dia=2.75, label='MT1', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=61.5, y=3.5, dia=2.75, label='MT2', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=3.5, y=52.5, dia=2.75, label='MT3', kind='mount', keepout_dia=None, tol=0.05),
        Hole(x=61.5, y=52.5, dia=2.75, label='MT4', kind='mount', keepout_dia=None, tol=0.05),
    ),
    features=(
        Feature(key='gpio40', label='40-pin GPIO header', kind='header',
                x0=7.08, y0=50.04, x1=57.96, y1=54.96),
        Feature(key='usb_a_1', label='USB 2.0 type A (single)', kind='usb_a',
                x0=53.28, y0=24.96, x1=67.56, y1=38.04),
        Feature(key='usb_power', label='micro-USB power input', kind='usb_power',
                x0=6.84, y0=-0.605, x1=14.4, y1=4.68),
        Feature(key='hdmi', label='HDMI type A', kind='connector',
                x0=24.72, y0=-1.51, x1=39.24, y1=10.635),
        Feature(key='av', label='3.5 mm A/V jack', kind='connector',
                x0=50.04, y0=-0.017, x1=57.0, y1=12.48),
    ),
    tolerance='reduced-source plot, see note: +/-0.5 typical',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-a-plus-mechanical-drawing.pdf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-a-plus-mechanical-drawing.pdf',
               note='Carried over from the Pi 3 Model B drawing. The 3A+ drawing gives no hole size.'),
    ),
    notes=(
        "Connector outlines are the component body as drawn by Raspberry Pi Ltd, overhang past the board edge included.",
        'Mounting hole diameter: Carried over from the Pi 3 Model B drawing. The 3A+ drawing gives no hole size.',
        'Hole IDs are assigned by this drawing, bottom row first then left to right, and mean the same thing on every Raspberry Pi sheet here.',
        "Design mounting hole keep-outs to 6.2 mm diameter on every model. That is what the Raspberry Pi HAT mechanical specification (github.com/raspberrypi/hats) requires around each hole, and it is the largest of the figures the individual models publish. The KEEPOUT column gives what this model's own drawing shows, which is not always anything.",
        'The source drawing is a reduced plot, not 1:1. Its scale was recovered from the mounting hole rectangle as 1.0685 and applied. Residual error over the 85 mm width is a few tenths of a millimetre, so treat every dimension on this sheet as +/-0.5 rather than the +/-0.20 the other models carry.',
        "Hole positions are the 3.5 mm inset and 58 x 49 mm rectangle dimensioned on this model's drawing.",
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
                x0=7.1, y0=50.0, x1=57.9, y1=55.0),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=66.65, y0=37.995, x1=88.0, y1=53.505),
        Feature(key='usb_a_1', label='USB 3.0 type A (upper pair)', kind='usb_a',
                x0=70.5, y0=20.43, x1=88.0, y1=34.25),
        Feature(key='usb_a_2', label='USB 2.0 type A (lower pair)', kind='usb_a',
                x0=70.3, y0=1.65, x1=88.0, y1=15.57),
        Feature(key='usb_power', label='USB-C power input', kind='usb_power',
                x0=6.875, y0=-1.25, x1=15.525, y1=6.15),
        Feature(key='hdmi0', label='micro-HDMI 0', kind='connector',
                x0=22.4, y0=-1.43, x1=29.6, y1=6.52),
        Feature(key='hdmi1', label='micro-HDMI 1', kind='connector',
                x0=35.9, y0=-1.43, x1=43.1, y1=6.52),
        Feature(key='av', label='3.5 mm A/V jack', kind='connector',
                x0=50.5, y0=0.0, x1=57.5, y1=12.5),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.dxf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.dxf',
               note='Read from the DXF: hole and keep-out circles on layer 0.'),
    ),
    notes=(
        "Connector outlines are the component body as drawn by Raspberry Pi Ltd, overhang past the board edge included.",
        'Mounting hole diameter: Read from the DXF: hole and keep-out circles on layer 0.',
        'Hole IDs are assigned by this drawing, bottom row first then left to right, and mean the same thing on every Raspberry Pi sheet here.',
        "Design mounting hole keep-outs to 6.2 mm diameter on every model. That is what the Raspberry Pi HAT mechanical specification (github.com/raspberrypi/hats) requires around each hole, and it is the largest of the figures the individual models publish. The KEEPOUT column gives what this model's own drawing shows, which is not always anything.",
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
                x0=7.08, y0=50.04, x1=57.84, y1=54.96),
        Feature(key='ethernet', label='Ethernet RJ45', kind='ethernet',
                x0=66.72, y0=2.212, x1=87.96, y1=18.193),
        Feature(key='usb_a_1', label='USB 3.0 type A (upper pair)', kind='usb_a',
                x0=70.92, y0=40.842, x1=87.24, y1=53.154),
        Feature(key='usb_a_2', label='USB 3.0 type A (lower pair)', kind='usb_a',
                x0=70.92, y0=22.92, x1=87.24, y1=35.16),
        Feature(key='usb_power', label='USB-C power input', kind='usb_power',
                x0=7.8, y0=-1.316, x1=14.52, y1=5.987),
        Feature(key='hdmi0', label='micro-HDMI 0', kind='connector',
                x0=23.04, y0=-0.84, x1=28.56, y1=6.84),
        Feature(key='hdmi1', label='micro-HDMI 1', kind='connector',
                x0=36.48, y0=-0.84, x1=42.0, y1=6.84),
    ),
    tolerance='',
    sources=(
        Source(label="Mechanical drawing", ref='https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf',
               note="Raspberry Pi Ltd"),
        Source(label="Mounting holes", ref='https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf',
               note='Hole diameter dimensioned on the drawing as ø2.7 mm; the keep-out circle is drawn and measures 5.80 mm.'),
    ),
    notes=(
        "Connector outlines are the component body as drawn by Raspberry Pi Ltd, overhang past the board edge included.",
        'Mounting hole diameter: Hole diameter dimensioned on the drawing as ø2.7 mm; the keep-out circle is drawn and measures 5.80 mm.',
        'Hole IDs are assigned by this drawing, bottom row first then left to right, and mean the same thing on every Raspberry Pi sheet here.',
        "Design mounting hole keep-outs to 6.2 mm diameter on every model. That is what the Raspberry Pi HAT mechanical specification (github.com/raspberrypi/hats) requires around each hole, and it is the largest of the figures the individual models publish. The KEEPOUT column gives what this model's own drawing shows, which is not always anything.",
        "AUX1 and AUX2 are 3.0 mm holes additional to the four M2.5 mounting holes. Each sits 6.0 mm inboard of the mounting hole it shares an X coordinate with, and the pair are diagonally opposite each other.",
        "Hole positions are the 3.5 mm inset and 58 x 49 mm rectangle dimensioned on this model's drawing.",
    ),
)
