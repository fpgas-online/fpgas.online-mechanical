"""The two base plates: a Raspberry Pi and an FPGA board, joined by the direct Raspmod.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with pdfplumber --with cadquery python base_plates/design.py

Plate coordinates: origin at the plate's lower-left corner, X right, Y away
from the viewer, seen from above; Z up from the plate's top face.  See
design.py for how every figure is arrived at.
"""

from __future__ import annotations

from base_plates.model import Box, Plate, Standoff
from tools.schema import BoardSpec, Hole, Outline, Source

#: The stack, above the Pi's top face: see design.py.
ADAPTER_UNDER = 6.34
ADAPTER_TOP = 7.94
HOST_ABOVE_PI = 4.68
HOST_ROWS = (4.53, 7.07)
PLUG_ROWS = (1.27, 3.81)
#: A corner cup's screw hole: the M3 screw cuts its own thread in it.
CUP_SCREW_HOLE = 2.5
EDGE_TO_PLUG_FACE = 1.18
#: The Pi's PCB, measured: two horizontal lines 1.41 mm apart in the side elevation of the Pi 5 drawing, at plot scale 1.0000.
PI_PCB_T = 1.41
#: The Arty's PCB and its rubber feet, from Digilent's rev C STEP model.
ARTY_PCB_T = 1.5
ARTY_FEET_H = 3.7
ARTY_FEET_DIA = 8.7
ARTY_FEET = ((5.0, 5.0), (5.0, 82.0), (104.0, 5.0), (104.0, 82.0))
#: The adapter's footprint over the Pi, in the Pi's frame: what has to be
#: no taller than ADAPTER_UNDER there.
ADAPTER_OVER_PI = (3.35, 46.97, 65.65, 78.27)

PLATES = {
    'tt-pi': Plate(
        key='tt-pi',
        title='Base Plate, TT Plate and Raspberry Pi',
        subtitle='A demoboard on the TT plate, a Pi, and the direct Raspmod between them',
        spec=BoardSpec(
            key='tt-pi',
            title='Base Plate, TT Plate and Raspberry Pi',
            subtitle='A demoboard on the TT plate, a Pi, and the direct Raspmod between them',
            family="baseplate",
            outline=Outline(width=135.0, height=192.0, corner_radius=4.0, thickness=3.0),
            holes=(
                Hole(x=5.37, y=113.0, dia=3.3, label='MP1', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=5.37, y=165.0, dia=3.3, label='MP2', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=129.63, y=113.0, dia=3.3, label='MP3', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=129.63, y=165.0, dia=3.3, label='MP4', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=42.0, y=186.88, dia=3.3, label='MP5', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=93.0, y=186.88, dia=3.3, label='MP6', kind='mp'),  # tapped M4, the TT plate's fixing
                Hole(x=30.11, y=12.27, dia=2.75, label='PI1', kind='pi'),  # M2.5 clearance, the Pi's MT1
                Hole(x=88.11, y=12.27, dia=2.75, label='PI2', kind='pi'),  # M2.5 clearance, the Pi's MT2
                Hole(x=30.11, y=61.27, dia=2.75, label='PI3', kind='pi'),  # M2.5 clearance, the Pi's MT3
                Hole(x=88.11, y=61.27, dia=2.75, label='PI4', kind='pi'),  # M2.5 clearance, the Pi's MT4
            ),
            sources=(
                Source(label='Adapter',
                       ref='accessories/raspmod_direct.py, ACC-HAT-DRMOD',
                       note='outline, plugs and socket pin 1'),
                Source(label='Raspberry Pi',
                       ref='raspberry_pi/boards.py',
                       note='outline, holes and header; the PCB 1.41 thick is not published and is two horizontal lines 1.41 mm apart in the side elevation of the Pi 5 drawing, at plot scale 1.0000'),
                Source(label='Wurth 613012243121',
                       ref='https://www.we-online.com/components/products/datasheet/613012243121.pdf',
                       note="angled 2x6 socket, the demoboard's: legs 3.3, body 5.0, 8.5 deep"),
                Source(label='Wurth 61301221021',
                       ref='https://www.we-online.com/components/products/datasheet/61301221021.pdf',
                       note='angled 2x6 pin header: near leg 1.5 from the body, pins 6 long'),
                Source(label='Kaweei CS25582-40G-M36-0A, Adafruit 2187',
                       ref='https://www.adafruit.com/product/2187',
                       note='2x20 SMT socket, 3.8 tall'),
                Source(label='Raspberry Pi 4 and 3B+ mechanical drawings',
                       ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf',
                       note='the 40-pin header: 2.54 body, 8.5 to the pin tips'),
                Source(label='TT mounting plate',
                       ref='tinytapeout/mounting_plate/plate.py',
                       note='outline, the six M4 fixings, the hosts, the 8 mm standoff'),
            ),
            notes=(
                'TT-MP-PLATE lies flat on this plate, screwed down through its six M4 fixings into the tapped holes; the demoboard stands on it on its 8 mm standoffs as that sheet says.',
                'The Pi stands on M2.5 x 6 standoffs over 0.5 washers, screwed from below, countersunk; the plug rows then meet the host rows to +0.01.',
                "The adapter's pin 1 sits on the Pi's pin 1, which turns it a half turn to the Pi: its pin-1 end is over the Pi's SD-card end. Push the plugs home until their faces meet the hosts', 1.18 behind the adapter's edge.",
                'FITS a Raspberry Pi 3 Model B or a Raspberry Pi 5. NOT a Raspberry Pi 4 Model B or a Raspberry Pi 3 Model B+: their PoE header is under the adapter.',
                'DO NOT BUILD ACC-HAT-DRMOD AS DRAWN: its pin mapping is mirrored, plug pin 1 on host pin 6. Its copper is to be re-routed first; this plate does not change.',
            ),
        ),
        boxes=(
            Box('adjacent', 'TT-MP-PLATE', 0.0, 135.0, 91.0, 192.0, 0.0, 3.0, (), ''),
            Box('adjacent', 'Demoboard, every revision', 10.74, 124.26, 95.53, 181.77, 11.0, 12.58, (), ''),
            Box('header', 'Pmod host socket', 30.6, 46.85, 88.22, 103.07, 15.88, 20.88, (17.11, 19.65), ''),
            Box('header', 'Pmod host socket', 53.46, 69.71, 88.22, 103.07, 15.88, 20.88, (17.11, 19.65), ''),
            Box('header', 'Pmod host socket', 76.32, 92.57, 88.22, 103.07, 15.88, 20.88, (17.11, 19.65), ''),
            Box('standoff', 'M3 x 8', 20.9, 25.9, 175.27, 180.27, 3.0, 11.0, (), ''),
            Box('standoff', 'M3 x 8', 93.9, 98.9, 102.77, 107.77, 3.0, 11.0, (), ''),
            Box('adjacent', 'Raspberry Pi', 26.61, 111.61, 8.77, 64.77, 6.5, 7.91, (), ''),
            Box('standoff', 'M2.5 x 6.5', 27.61, 32.61, 9.77, 14.77, 0.0, 6.5, (), ''),
            Box('standoff', 'M2.5 x 6.5', 85.61, 90.61, 9.77, 14.77, 0.0, 6.5, (), ''),
            Box('standoff', 'M2.5 x 6.5', 27.61, 32.61, 58.77, 63.77, 0.0, 6.5, (), ''),
            Box('standoff', 'M2.5 x 6.5', 85.61, 90.61, 58.77, 63.77, 0.0, 6.5, (), ''),
            Box('header', 'Pi 40-pin header', 33.71, 84.51, 58.77, 63.77, 7.91, 16.41, (), ''),
            Box('adjacent', 'ACC-HAT-DRMOD', 29.96, 92.26, 55.74, 87.04, 14.25, 15.85, (), ''),
            Box('header', "Adapter socket, on the Pi's header", 32.56, 85.66, 56.09, 66.45, 10.45, 14.25, (), ''),
            Box('header', 'Plug P1', 76.35, 92.59, 85.68, 88.22, 15.85, 20.93, (17.12, 19.66), ''),
            Box('header', 'Plug P1 pins', 78.12, 90.82, 88.22, 94.22, 16.8, 19.98, (17.12, 19.66), ''),
            Box('header', 'Plug P2', 53.49, 69.73, 85.68, 88.22, 15.85, 20.93, (17.12, 19.66), ''),
            Box('header', 'Plug P2 pins', 55.26, 67.96, 88.22, 94.22, 16.8, 19.98, (17.12, 19.66), ''),
            Box('header', 'Plug P3', 30.63, 46.87, 85.68, 88.22, 15.85, 20.93, (17.12, 19.66), ''),
            Box('header', 'Plug P3 pins', 32.4, 45.1, 88.22, 94.22, 16.8, 19.98, (17.12, 19.66), ''),
        ),
        standoffs=(
            Standoff(6, 'M4 screw into the plate', 'TT-MP-PLATE'),
            Standoff(4, "M3 x 8 F/F, the TT plate's own", 'demoboard'),
            Standoff(4, 'M2.5 x 6 F/F over a 0.5 washer', 'Raspberry Pi'),
        ),
        levels=(
            ('TT plate top face', 3.0),
            ('Demoboard underside', 11.0),
            ('Demoboard top face', 12.58),
            ('Host socket rows', (17.11, 19.65)),
            ('Pi underside', 6.5),
            ('Pi top face', 7.91),
            ('Adapter underside', 14.25),
            ('Adapter top face', 15.85),
            ('Plug rows', (17.12, 19.66)),
        ),
        residual=0.01,
        fits=('Raspberry Pi 3 Model B', 'Raspberry Pi 5'),
        excluded=(('Raspberry Pi 4 Model B', 'PoE header, 3B+ and 4B (8.5 mm)'), ('Raspberry Pi 3 Model B+', "PoE header (8.5 mm), where the 4B's is")),
        pi_positions=(('', 26.61, 8.77),),
        made=(),
    ),
    'arty-pi': Plate(
        key='arty-pi',
        title='Base Plate, Arty A7 and Raspberry Pi',
        subtitle='An Arty A7 in corner cups, a Pi, and the direct Raspmod between them',
        spec=BoardSpec(
            key='arty-pi',
            title='Base Plate, Arty A7 and Raspberry Pi',
            subtitle='An Arty A7 in corner cups, a Pi, and the direct Raspmod between them',
            family="baseplate",
            outline=Outline(width=132.0, height=183.0, corner_radius=4.0, thickness=3.0),
            holes=(
                Hole(x=112.0, y=170.0, dia=3.4, label='CUP1', kind='cup'),  # M3 clearance, countersunk below, into the cup
                Hole(x=112.0, y=93.0, dia=3.4, label='CUP2', kind='cup'),  # M3 clearance, countersunk below, into the cup
                Hole(x=13.0, y=170.0, dia=3.4, label='CUP3', kind='cup'),  # M3 clearance, countersunk below, into the cup
                Hole(x=13.0, y=93.0, dia=3.4, label='CUP4', kind='cup'),  # M3 clearance, countersunk below, into the cup
                Hole(x=42.44, y=12.17, dia=2.75, label='PIA1', kind='pi'),  # M2.5 clearance, the Pi's MT1
                Hole(x=100.44, y=12.17, dia=2.75, label='PIA2', kind='pi'),  # M2.5 clearance, the Pi's MT2
                Hole(x=42.44, y=61.17, dia=2.75, label='PIA3', kind='pi'),  # M2.5 clearance, the Pi's MT3
                Hole(x=100.44, y=61.17, dia=2.75, label='PIA4', kind='pi'),  # M2.5 clearance, the Pi's MT4
                Hole(x=19.64, y=12.17, dia=2.75, label='PIB1', kind='pi'),  # M2.5 clearance, the Pi's MT1
                Hole(x=77.64, y=12.17, dia=2.75, label='PIB2', kind='pi'),  # M2.5 clearance, the Pi's MT2
                Hole(x=19.64, y=61.17, dia=2.75, label='PIB3', kind='pi'),  # M2.5 clearance, the Pi's MT3
                Hole(x=77.64, y=61.17, dia=2.75, label='PIB4', kind='pi'),  # M2.5 clearance, the Pi's MT4
            ),
            sources=(
                Source(label='Adapter',
                       ref='accessories/raspmod_direct.py, ACC-HAT-DRMOD',
                       note='outline, plugs and socket pin 1'),
                Source(label='Raspberry Pi',
                       ref='raspberry_pi/boards.py',
                       note='outline, holes and header; the PCB 1.41 thick is not published and is two horizontal lines 1.41 mm apart in the side elevation of the Pi 5 drawing, at plot scale 1.0000'),
                Source(label='Wurth 613012243121',
                       ref='https://www.we-online.com/components/products/datasheet/613012243121.pdf',
                       note="angled 2x6 socket, the demoboard's: legs 3.3, body 5.0, 8.5 deep"),
                Source(label='Wurth 61301221021',
                       ref='https://www.we-online.com/components/products/datasheet/61301221021.pdf',
                       note='angled 2x6 pin header: near leg 1.5 from the body, pins 6 long'),
                Source(label='Kaweei CS25582-40G-M36-0A, Adafruit 2187',
                       ref='https://www.adafruit.com/product/2187',
                       note='2x20 SMT socket, 3.8 tall'),
                Source(label='Raspberry Pi 4 and 3B+ mechanical drawings',
                       ref='https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf',
                       note='the 40-pin header: 2.54 body, 8.5 to the pin tips'),
                Source(label='Arty A7',
                       ref='fpga/boards.py',
                       note='outline and the four hosts; no mounting holes'),
                Source(label='Arty rev C STEP',
                       ref='https://digilent.com/reference/_media/reference/programmable-logic/arty/arty_revc_cad.zip',
                       note='board 1.5 thick; feet 3.7 tall, 8.7 across, 5.0 from each corner'),
            ),
            notes=(
                'The Arty has no mounting holes: it stands on its rubber feet in four printed corner cups, see DETAIL B, screwed from below, countersunk, the M3 screw cutting its own thread in the cup.',
                "The Pi stands on M2.5 x 4 standoffs, the shortest usual, screwed from below, countersunk; the cups' height follows, and the plug rows meet the host rows to +0.00.",
                'TWO POSITIONS: holes PIA1-4 put the Pi where the plugs go into JA, JB and JC; PIB1-4 where they go into JB, JC and JD. Use one set.',
                "The adapter's pin 1 sits on the Pi's pin 1, which turns it a half turn to the Pi: its pin-1 end is over the Pi's SD-card end. Push the plugs home until their faces meet the hosts', 1.18 behind the adapter's edge.",
                'FITS a Raspberry Pi 3 Model B or a Raspberry Pi 5. NOT a Raspberry Pi 4 Model B or a Raspberry Pi 3 Model B+: their PoE header is under the adapter.',
                "ASSUMED: the Arty's Pmod sockets stand on 3.3 mm legs like the demoboard's. Digilent name no part, and their STEP models a socket as a plain box. If the body sits on the board instead, the rows are 3.26 lower: make the cups 3.26 taller, 8.15 under the foot.",
                'DO NOT BUILD ACC-HAT-DRMOD AS DRAWN: its pin mapping is mirrored, plug pin 1 on host pin 6. Its copper is to be re-routed first; this plate does not change.',
            ),
        ),
        boxes=(
            Box('adjacent', 'Digilent Arty A7', 8.0, 117.0, 88.0, 175.0, 8.59, 10.09, (), ''),
            Box('header', 'Pmod host JA', 89.16, 104.4, 88.12, 101.68, 13.39, 18.39, (14.62, 17.16), ''),
            Box('header', 'Pmod host JB', 66.36, 81.6, 88.12, 101.68, 13.39, 18.39, (14.62, 17.16), ''),
            Box('header', 'Pmod host JC', 43.56, 58.8, 88.12, 101.68, 13.39, 18.39, (14.62, 17.16), ''),
            Box('header', 'Pmod host JD', 20.76, 36.0, 88.12, 101.68, 13.39, 18.39, (14.62, 17.16), ''),
            Box('adjacent', 'Rubber foot', 107.65, 116.35, 165.65, 174.35, 4.89, 8.59, (), ''),
            Box('made', 'Cup', 106.0, 119.0, 164.0, 177.0, 0.0, 4.89, (), ''),
            Box('made', 'Cup wall', 117.0, 119.0, 164.0, 177.0, 4.89, 12.09, (), ''),
            Box('made', 'Cup wall', 106.0, 119.0, 175.0, 177.0, 4.89, 12.09, (), ''),
            Box('adjacent', 'Rubber foot', 107.65, 116.35, 88.65, 97.35, 4.89, 8.59, (), ''),
            Box('made', 'Cup', 106.0, 119.0, 84.0, 97.0, 0.0, 4.89, (), ''),
            Box('made', 'Cup wall', 117.0, 119.0, 84.0, 97.0, 4.89, 12.09, (), ''),
            Box('made', 'Cup wall', 106.0, 119.0, 84.0, 86.0, 4.89, 12.09, (), ''),
            Box('adjacent', 'Rubber foot', 8.65, 17.35, 165.65, 174.35, 4.89, 8.59, (), ''),
            Box('made', 'Cup', 4.0, 17.0, 164.0, 177.0, 0.0, 4.89, (), ''),
            Box('made', 'Cup wall', 4.0, 6.0, 164.0, 177.0, 4.89, 12.09, (), ''),
            Box('made', 'Cup wall', 4.0, 17.0, 175.0, 177.0, 4.89, 12.09, (), ''),
            Box('adjacent', 'Rubber foot', 8.65, 17.35, 88.65, 97.35, 4.89, 8.59, (), ''),
            Box('made', 'Cup', 4.0, 17.0, 84.0, 97.0, 0.0, 4.89, (), ''),
            Box('made', 'Cup wall', 4.0, 6.0, 84.0, 97.0, 4.89, 12.09, (), ''),
            Box('made', 'Cup wall', 4.0, 17.0, 84.0, 86.0, 4.89, 12.09, (), ''),
            Box('adjacent', 'Raspberry Pi', 38.94, 123.94, 8.67, 64.67, 4.0, 5.41, (), 'A'),
            Box('standoff', 'M2.5 x 4', 39.94, 44.94, 9.67, 14.67, 0.0, 4.0, (), 'A'),
            Box('standoff', 'M2.5 x 4', 97.94, 102.94, 9.67, 14.67, 0.0, 4.0, (), 'A'),
            Box('standoff', 'M2.5 x 4', 39.94, 44.94, 58.67, 63.67, 0.0, 4.0, (), 'A'),
            Box('standoff', 'M2.5 x 4', 97.94, 102.94, 58.67, 63.67, 0.0, 4.0, (), 'A'),
            Box('header', 'Pi 40-pin header', 46.04, 96.84, 58.67, 63.67, 5.41, 13.91, (), 'A'),
            Box('adjacent', 'ACC-HAT-DRMOD', 42.29, 104.59, 55.64, 86.94, 11.75, 13.35, (), 'A'),
            Box('header', "Adapter socket, on the Pi's header", 44.89, 97.99, 55.99, 66.35, 7.95, 11.75, (), 'A'),
            Box('header', 'Plug P1', 88.68, 104.92, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'A'),
            Box('header', 'Plug P1 pins', 90.45, 103.15, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'A'),
            Box('header', 'Plug P2', 65.82, 82.06, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'A'),
            Box('header', 'Plug P2 pins', 67.59, 80.29, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'A'),
            Box('header', 'Plug P3', 42.96, 59.2, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'A'),
            Box('header', 'Plug P3 pins', 44.73, 57.43, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'A'),
            Box('alt', 'Raspberry Pi', 16.14, 101.14, 8.67, 64.67, 4.0, 5.41, (), 'B'),
            Box('alt', 'M2.5 x 4', 17.14, 22.14, 9.67, 14.67, 0.0, 4.0, (), 'B'),
            Box('alt', 'M2.5 x 4', 75.14, 80.14, 9.67, 14.67, 0.0, 4.0, (), 'B'),
            Box('alt', 'M2.5 x 4', 17.14, 22.14, 58.67, 63.67, 0.0, 4.0, (), 'B'),
            Box('alt', 'M2.5 x 4', 75.14, 80.14, 58.67, 63.67, 0.0, 4.0, (), 'B'),
            Box('alt', 'Pi 40-pin header', 23.24, 74.04, 58.67, 63.67, 5.41, 13.91, (), 'B'),
            Box('alt', 'ACC-HAT-DRMOD', 19.49, 81.79, 55.64, 86.94, 11.75, 13.35, (), 'B'),
            Box('alt', "Adapter socket, on the Pi's header", 22.09, 75.19, 55.99, 66.35, 7.95, 11.75, (), 'B'),
            Box('alt', 'Plug P1', 65.88, 82.12, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'B'),
            Box('alt', 'Plug P1 pins', 67.65, 80.35, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'B'),
            Box('alt', 'Plug P2', 43.02, 59.26, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'B'),
            Box('alt', 'Plug P2 pins', 44.79, 57.49, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'B'),
            Box('alt', 'Plug P3', 20.16, 36.4, 85.58, 88.12, 13.35, 18.43, (14.62, 17.16), 'B'),
            Box('alt', 'Plug P3 pins', 21.93, 34.63, 88.12, 94.12, 14.3, 17.48, (14.62, 17.16), 'B'),
        ),
        standoffs=(
            Standoff(4, 'corner cup, printed, and an M3 countersunk screw from below', 'Arty A7'),
            Standoff(4, 'M2.5 x 4 F/F, in either set of four holes', 'Raspberry Pi'),
        ),
        levels=(
            ('Cup ledge', 4.89),
            ('Arty underside', 8.59),
            ('Arty top face', 10.09),
            ('Host socket rows', (14.62, 17.16)),
            ('Pi underside', 4.0),
            ('Pi top face', 5.41),
            ('Adapter underside', 11.75),
            ('Adapter top face', 13.35),
            ('Plug rows', (14.62, 17.16)),
        ),
        residual=0.0,
        fits=('Raspberry Pi 3 Model B', 'Raspberry Pi 5'),
        excluded=(('Raspberry Pi 4 Model B', 'PoE header, 3B+ and 4B (8.5 mm)'), ('Raspberry Pi 3 Model B+', "PoE header (8.5 mm), where the 4B's is")),
        pi_positions=(('A: plugs into JA, JB, JC', 38.94, 8.67), ('B: plugs into JB, JC, JD', 16.14, 8.67)),
        made=(('Corner cup', 4, '13 x 13 x 12.09', 'ledge 4.89 tall under the foot, 2 mm walls on the two outer sides to 12.09, a 2.5 hole for the M3 screw; print flat'),),
    ),

}
