"""The direct Raspmod's mechanical data and pin map, from its KiCad board file.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python accessories/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, viewed from the component side, millimetres.  The
component side carries the three Pmod host sockets, facing up, and the three
right-angle plugs along the lower edge, pins out past it; the socket that
goes onto the Raspberry Pi's header is on the underside.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Outline, PmodHeader, Source

#: Raspberry Pi 40-pin header pin -> (the Pi's name for it, the board's net
#: it lands on).  The Pi's names are the ``pinfunction`` KiCad's Raspberry Pi
#: symbol gives each pin; the nets are the board's own.  A pin with no net is
#: not connected: pin 17, the Pi's second 3V3, deliberately, see the board's
#: README.
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
    17: ('3V3', ''),
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

#: Each port's twelve Pmod pins -> the board's net on that pin.  The host
#: socket and the plug of a port share every net, which is checked at
#: extraction.  Laid flat on the Pi the plug rows meet a host's in mirror
#: image, pin 1 on pin 6; the copper is to be redone, and this table is the
#: board as it is.
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

#: Where the Pi's pins 1 and 2 come through J1, in board coordinates: the
#: point the board is placed on a Pi by.  Pin 1 is the right-hand end of the
#: upper row, pin 2 below it, and the rows run along X on the 2.54 pitch.
PI_PIN1 = (57.28, 27.04)
PI_PIN2 = (57.28, 24.5)

RASPMOD_DIRECT = BoardSpec(
    key='raspmod-direct',
    title='Raspmod, direct',
    subtitle="TT Demoboard To Raspi Direct rev 2.0: on the Pi's GPIO header, flat beside the demoboard or an Arty",
    family="accessory",
    front_edge="bottom",
    outline=Outline(width=62.3, height=31.3,
                    corner_radius=2.0, thickness=1.6,
                    edges=(
                        ('line', 0.0, 2.0, 0.0, 29.3),
                        ('line', 2.0, 31.3, 60.3, 31.3),
                        ('line', 60.3, 0.0, 2.0, 0.0),
                        ('line', 62.3, 29.3, 62.3, 2.0),
                        ('arc', 0.0, 29.3, 2.0, 31.3, 2.0, 0, 0),
                        ('arc', 2.0, 0.0, 0.0, 2.0, 2.0, 0, 0),
                        ('arc', 60.3, 31.3, 62.3, 29.3, 2.0, 0, 0),
                        ('arc', 62.3, 2.0, 60.3, 0.0, 2.0, 0, 0),
                    )),
    pmods=(
        PmodHeader(key='p1_host', label='P1', designator='J5', edge='bottom', role='host',
                   cx=7.74, cy=14.29, pin1_x=14.09, pin1_y=15.56,
                   body_x0=-0.41, body_y0=10.56, body_x1=16.39, body_y1=17.56),
        PmodHeader(key='p1_plug', label='P1', designator='J2', edge='bottom', role='plug',
                   cx=7.79, cy=4.13, pin1_x=14.14, pin1_y=5.4,
                   body_x0=-0.36, body_y0=-7.7, body_x1=15.94, body_y1=6.85),
        PmodHeader(key='p2_host', label='P2', designator='J6', edge='bottom', role='host',
                   cx=30.6, cy=14.29, pin1_x=36.95, pin1_y=15.56,
                   body_x0=22.45, body_y0=10.56, body_x1=39.25, body_y1=17.56),
        PmodHeader(key='p2_plug', label='P2', designator='J3', edge='bottom', role='plug',
                   cx=30.65, cy=4.13, pin1_x=37.0, pin1_y=5.4,
                   body_x0=22.5, body_y0=-7.7, body_x1=38.8, body_y1=6.85),
        PmodHeader(key='p3_host', label='P3', designator='J7', edge='bottom', role='host',
                   cx=53.46, cy=14.29, pin1_x=59.81, pin1_y=15.56,
                   body_x0=45.31, body_y0=10.56, body_x1=62.11, body_y1=17.56),
        PmodHeader(key='p3_plug', label='P3', designator='J4', edge='bottom', role='plug',
                   cx=53.51, cy=4.13, pin1_x=59.86, pin1_y=5.4,
                   body_x0=45.36, body_y0=-7.7, body_x1=61.66, body_y1=6.85),
    ),
    features=(
        Feature(key='socket', label='40-way socket J1 onto the Raspberry Pi GPIO, 2x20 SMT, underside', kind='header',
                designator='J1', x0=6.6, y0=20.59, x1=59.7, y1=30.95,
                note="Pin 1 at (57.28, 27.04), the right-hand end of the upper row. Courtyard of the SMT socket on the underside, 3.8 mm tall; the Pi's pins come up through the plated holes.", side='top', number=1, pins=(20, 2), pin1=(57.28, 27.04)),
        Feature(key='clkrst_socket', label='Clock and reset socket J8, 1x2', kind='header',
                designator='J8', x0=14.87, y0=11.27, x1=20.97, y1=14.82,
                note='', side='top', number=2),
        Feature(key='power_jumper', label='Power jumper J11: Pi 3V3 to the Pmod VCC rail', kind='header',
                designator='J11', x0=1.05, y0=18.16, x1=4.6, y1=24.26,
                note='', side='top', number=3),
    ),
    sources=(
        Source(label='KiCad board file',
               ref='https://github.com/mithro/tinytapeout-demoboard-to-raspi  TTDB_2_Raspi.kicad_pcb @ 33386eb',
               note='title block: TT Demoboard To Raspi Direct rev 2.0, dated 2026-09-29, Psychogenic Technologies; branch direct-gpio, made by scripts/make_direct.py over https://github.com/psychogenic/tinytapeout-demoboard-to-raspi  @ 2c2e3db'),
        Source(label='What changed',
               ref='https://github.com/mithro/tinytapeout-demoboard-to-raspi/blob/direct-gpio/README.md',
               note='J1 an SMT socket underneath, J2 to J4 right-angle on top, 10 mm cut off the pin-40 end with J9, J10 and SW1, pin 17 unconnected'),
        Source(label='Socket',
               ref='https://www.adafruit.com/product/2187',
               note='Adafruit 2187, Kaweei CS25582-40G-M36-0A: 3.8 mm tall, pins through the PCB'),
    ),
    notes=(
        "Sits on a Raspberry Pi's 40-pin header by the SMT socket J1 on its underside, component side up, and lies flat beside the FPGA board: the three right-angle plugs go sideways into its Pmod hosts, and the three sockets J5 to J7 face up.",
        'PLUG rows are right-angle 2x6 headers on the component side, pins out past the lower edge. Their fields sit 10.16 mm below the HOST fields and 0.05 mm to the right, on the 22.86 mm host pitch.',
        "PIN MAPPING NOT YET RIGHT: laid flat this way the plug rows meet a host's in mirror image, pin 1 on pin 6, and the ports reverse. The copper is to be redone before the board is made; nothing on this sheet moves when it is.",
        'Fits a Raspberry Pi 5 or 3B. Not a 3B+ or 4B: their PoE header stands 8.5 mm tall under J1, where the board sits 6.34 mm up.',
        "No mounting holes: the Pi's header carries the board. BP-TT and BP-ARTY hold the pair with a demoboard or an Arty.",
        'The pin map, read from the same board file, is PI_HEADER and PORT_PINS in accessories/raspmod_direct.py.',
    ),
)
