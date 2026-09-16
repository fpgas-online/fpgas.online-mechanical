"""Raspmod mechanical data and pin map, from its KiCad board file.

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
PI_HEADER: dict[int, tuple[str, str]] = {
    1: ('3V3', 'VDD'),
    2: ('5V', ''),
    3: ('SDA_I2C1/GPIO02', '/P3_1'),
    4: ('5V', ''),
    5: ('SCL_I2C1/GPIO03', '/P3_5'),
    6: ('GND', 'GND'),
    7: ('GPCLK0/GPIO04', '/P3_2'),
    8: ('GPIO14/UART_TXD', '/P3_6'),
    9: ('GND', 'GND'),
    10: ('GPIO15/UART_RXD', '/P3_3'),
    11: ('GPIO17/SPI1_~{CE1}', '/P3_7'),
    12: ('GPIO18/SPI1_~{CE0}/PCM_CLK/PWM0', '/P3_4'),
    13: ('GPIO27/SDIO_DAT3', '/P3_8'),
    14: ('GND', 'GND'),
    15: ('GPIO22/SDIO_CLK', '/P2_1'),
    16: ('GPIO23/SDIO_CMD', '/P2_5'),
    17: ('3V3', 'VDD'),
    18: ('GPIO24/SDIO_DAT0', '/P2_6'),
    19: ('MOSI_SPI0/GPIO10', '/P2_2'),
    20: ('GND', 'GND'),
    21: ('MISO_SPI0/GPIO09', '/P2_7'),
    22: ('GPIO25/SDIO_DAT1', '/P2_3'),
    23: ('SCLK_SPI0/GPIO11', '/P2_8'),
    24: ('~{CE0}_SPI0/GPIO08', '/P2_4'),
    25: ('GND', 'GND'),
    26: ('~{CE1}_SPI0/GPIO07', '/~{RST}'),
    27: ('ID_SD_I2C0/GPIO00', '/USR_SW'),
    28: ('ID_SC_I2C0/GPIO01', '/CLK'),
    29: ('GPCLK1/GPIO05', '/P1_5'),
    30: ('GND', 'GND'),
    31: ('GPCLK2/GPIO06', '/P1_6'),
    32: ('GPIO12/PWM0', '/P1_1'),
    33: ('GPIO13/PWM1', '/P1_2'),
    34: ('GND', 'GND'),
    35: ('GPIO19/SPI1_MISO/PCM_FS', '/P1_3'),
    36: ('GPIO16/SPI1_~{CE2}', '/P1_7'),
    37: ('GPIO26/SDIO_DAT2', '/P1_4'),
    38: ('GPIO20/SPI1_MOSI/PCM_DIN/PWM1', '/P1_8'),
    39: ('GND', 'GND'),
    40: ('GPIO21/SPI1_SCLK/PCM_DOUT', '/USR_IO'),
}

#: Each port's twelve Pmod pins -> the Raspmod net on that pin.  The host
#: socket and the underside plug of a port share every net, which is checked
#: at extraction.
PORT_PINS: dict[str, dict[int, str]] = {
    'P1': {
        1: '/P1_1',
        2: '/P1_2',
        3: '/P1_3',
        4: '/P1_4',
        5: 'GND',
        6: '+3V3',
        7: '/P1_5',
        8: '/P1_6',
        9: '/P1_7',
        10: '/P1_8',
        11: 'GND',
        12: '+3V3',
    },
    'P2': {
        1: '/P2_1',
        2: '/P2_2',
        3: '/P2_3',
        4: '/P2_4',
        5: 'GND',
        6: '+3V3',
        7: '/P2_5',
        8: '/P2_6',
        9: '/P2_7',
        10: '/P2_8',
        11: 'GND',
        12: '+3V3',
    },
    'P3': {
        1: '/P3_1',
        2: '/P3_2',
        3: '/P3_3',
        4: '/P3_4',
        5: 'GND',
        6: '+3V3',
        7: '/P3_5',
        8: '/P3_6',
        9: '/P3_7',
        10: '/P3_8',
        11: 'GND',
        12: '+3V3',
    },
}

RASPMOD = BoardSpec(
    key='raspmod',
    title='Raspmod',
    subtitle="TT Demoboard To Raspi rev 1.0, silkscreen v1.1: a frontplate for the demoboard's three Pmod hosts",
    family="accessory",
    front_edge="bottom",
    outline=Outline(width=72.3, height=31.3,
                    corner_radius=2.0, thickness=1.6,
                    edges=(
                        ('line', 0.0, 2.0, 0.0, 29.3),
                        ('line', 2.0, 31.3, 70.3, 31.3),
                        ('line', 70.3, 0.0, 2.0, 0.0),
                        ('line', 72.3, 29.3, 72.3, 2.0),
                        ('arc', 0.0, 29.3, 2.0, 31.3, 2.0, 0, 0),
                        ('arc', 2.0, 0.0, 0.0, 2.0, 2.0, 0, 0),
                        ('arc', 70.3, 31.3, 72.3, 29.3, 2.0, 0, 0),
                        ('arc', 72.3, 2.0, 70.3, 0.0, 2.0, 0, 0),
                    )),
    pmods=(
        PmodHeader(key='p1_host', label='P1', designator='J5', edge='bottom', role='host',
                   cx=17.74, cy=14.29, pin1_x=24.09, pin1_y=15.56,
                   body_x0=9.59, body_y0=10.56, body_x1=26.39, body_y1=17.56),
        PmodHeader(key='p1_plug', label='P1', designator='J2', edge='bottom', role='plug',
                   cx=17.79, cy=4.13, pin1_x=24.14, pin1_y=5.4,
                   body_x0=9.64, body_y0=0.4, body_x1=25.94, body_y1=7.2),
        PmodHeader(key='p2_host', label='P2', designator='J6', edge='bottom', role='host',
                   cx=40.6, cy=14.29, pin1_x=46.95, pin1_y=15.56,
                   body_x0=32.45, body_y0=10.56, body_x1=49.25, body_y1=17.56),
        PmodHeader(key='p2_plug', label='P2', designator='J3', edge='bottom', role='plug',
                   cx=40.65, cy=4.13, pin1_x=47.0, pin1_y=5.4,
                   body_x0=32.5, body_y0=0.4, body_x1=48.8, body_y1=7.2),
        PmodHeader(key='p3_host', label='P3', designator='J7', edge='bottom', role='host',
                   cx=63.46, cy=14.29, pin1_x=69.81, pin1_y=15.56,
                   body_x0=55.31, body_y0=10.56, body_x1=72.11, body_y1=17.56),
        PmodHeader(key='p3_plug', label='P3', designator='J4', edge='bottom', role='plug',
                   cx=63.51, cy=4.13, pin1_x=69.86, pin1_y=5.4,
                   body_x0=55.36, body_y0=0.4, body_x1=71.66, body_y1=7.2),
    ),
    features=(
        Feature(key='ribbon', label='40-way ribbon header J1 to the Raspberry Pi GPIO, 2x20 box', kind='header',
                designator='J1', x0=17.23, y0=22.69, x1=69.08, y1=28.84,
                note='Pin 1 at (67.28, 27.04), the right-hand end of the upper row. Courtyard of the 2x20 box header; the ribbon plugs in from the front.', side='top', number=1),
        Feature(key='clkrst_socket', label='Clock and reset socket J8, 1x2', kind='header',
                designator='J8', x0=24.87, y0=11.27, x1=30.97, y1=14.82,
                note='', side='top', number=2),
        Feature(key='clkrst_pins', label='Clock and reset pins J9, 1x2, on the underside', kind='header',
                designator='J9', x0=24.87, y0=1.06, x1=31.02, y1=4.66,
                note="Underside. Falls on pins 2 and 3 of the demoboard's clock/reset SIL header; the maker's README says a 2-pin header has to be added to the demoboard there.", side='bottom', number=3),
        Feature(key='aux', label='Auxiliary socket J10, 1x4: GND, 3V3, USR_IO, USR_SW', kind='header',
                designator='J10', x0=0.525, y0=11.66, x1=4.075, y1=22.86,
                note='', side='top', number=4),
        Feature(key='power_jumper', label='Power jumper J11: Pi 3V3 to the Pmod VCC rail', kind='header',
                designator='J11', x0=11.05, y0=18.16, x1=14.6, y1=24.26,
                note='', side='top', number=5),
        Feature(key='user_switch', label='User push button SW1, USR_SW', kind='switch',
                designator='SW1', x0=4.05, y0=0.35, x1=8.55, y1=8.75,
                note='', side='top', number=6),
    ),
    sources=(
        Source(label='KiCad board file',
               ref='https://github.com/psychogenic/tinytapeout-demoboard-to-raspi  TTDB_2_Raspi.kicad_pcb @ 2c2e3db',
               note='title block: TT Demoboard To Raspi rev 1.0, dated 2024-12-14, Psychogenic Technologies; the silkscreen reads v1.1'),
        Source(label='Purpose',
               ref='https://github.com/psychogenic/tinytapeout-demoboard-to-raspi/blob/main/README.md',
               note='quoted: "Connects all I/O from TT demoboard to RPi ribbon cable while still allowing the PMODs to be used with external modules."'),
        Source(label='Clock and reset',
               ref='https://github.com/psychogenic/tinytapeout-demoboard-to-raspi/blob/main/README.md',
               note='quoted: "the clock and reset are only available through the SIL (not one of the PMODs) so these must be connected by adding a 2-pin header to the demoboard in the right spot."'),
    ),
    notes=(
        "Not a HAT. The board stands on edge in front of a Tiny Tapeout demoboard, its three underside plugs in the demoboard's Pmod hosts and its component side facing forward; the Raspberry Pi connects by ribbon cable only.",
        "PLUG rows are the underside 2x6 pin headers. Their fields sit 10.16 mm below the HOST fields and 0.05 mm to the right, on the demoboard's 22.86 mm host pitch, so P1 goes into the INPUT host, P2 into BIDIR and P3 into OUTPUT.",
        'HOST rows J5 to J7 are vertical sockets facing out of the component side; EDGE gives the axis the columns run along, and pin 1 is the right-hand end of the upper row on both rows.',
        'No mounting holes: the plugs carry the board.',
        'The pin map, read from the same board file, is in accessories/raspmod-vs-pmod-hat.md.',
    ),
)
