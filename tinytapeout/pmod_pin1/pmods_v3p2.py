"""The Tiny Tapeout demo board v3.2's Pmod sockets, for the pin 1 picture.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project python tinytapeout/pmod_pin1/extract.py

Read out of https://github.com/TinyTapeout/tt-demo-pcb
tinytapeout-demo.kicad_pcb at commit 0277545, whose board file is the one d830790 has
(blob 719cfe8c599d).  KiCad coordinates: millimetres, Y down, top
view, so the board's front edge, the one the sockets face, is at the
largest Y.  Each socket's ``pads`` are (number, shape, x, y, size, net);
``mark`` the lines of its footprint's silkscreen corner mark and ``corner``
where they meet; ``body`` its fabrication outline past the board edge;
``lines``, ``arcs``, ``blocks`` and ``texts`` (text, x, y, height, justify,
bold) the board's own front silkscreen round it.
"""

SOURCE = {
    "url": 'https://github.com/TinyTapeout/tt-demo-pcb',
    "path": 'tinytapeout-demo.kicad_pcb',
    "commit": '0277545',
    "same_as": 'd830790',
    "blob": '719cfe8c599d',
}

#: The board's front edge, the Edge.Cuts line the sockets face, and how far
#: it runs.
FRONT_EDGE_Y = 97.5
FRONT_EDGE_X = (70.2, 148.8)

SOCKETS = (
    {
        'ref': 'J11',
        'name': 'INPUT',
        'pads': (
            ('1', 'rect', 92.7, 93.0, 1.7, 'ui_in0'),
            ('2', 'oval', 90.16, 93.0, 1.7, 'ui_in1'),
            ('3', 'oval', 87.62, 93.0, 1.7, 'ui_in2'),
            ('4', 'oval', 85.08, 93.0, 1.7, 'ui_in3'),
            ('5', 'oval', 82.54, 93.0, 1.7, 'GND'),
            ('6', 'circle', 80.0, 93.0, 1.7, '+3V3'),
            ('7', 'oval', 92.7, 95.54, 1.7, '/ui_in4'),
            ('8', 'oval', 90.16, 95.54, 1.7, '/ui_in5'),
            ('9', 'oval', 87.62, 95.54, 1.7, '/ui_in6'),
            ('10', 'oval', 85.08, 95.54, 1.7, '/ui_in7'),
            ('11', 'oval', 82.54, 95.54, 1.7, 'GND'),
            ('12', 'oval', 80.0, 95.54, 1.7, '+3V3'),
        ),
        'mark': (
            (78.67, 91.89, 80.0, 91.89),
            (78.67, 93.0, 78.67, 91.89),
        ),
        'corner': (78.67, 91.89),
        'body': (
            (78.73, 98.03, 79.7, 97.06),
            (78.73, 105.57, 78.73, 98.03),
            (79.7, 97.06, 93.97, 97.06),
            (93.97, 97.06, 93.97, 105.57),
            (93.97, 105.57, 78.73, 105.57),
        ),
        'lines': (
            (79.7, 86.2, 92.9, 86.2),
            (78.7, 91.8, 78.7, 87.2),
            (93.9, 87.2, 93.9, 91.9),
        ),
        'arcs': (
            (92.9, 86.2, 93.6071, 86.4929, 93.9, 87.2),
            (78.7, 87.2, 78.9929, 86.4929, 79.7, 86.2),
        ),
        'blocks': (
            (81.2, 91.4, 83.8, 96.9),
        ),
        'texts': (
            ('INPUT', 88.4, 88.9, 2.0, 'bottom', True),
            ('ui_in', 93.8, 90.5, 1.4, 'right bottom', True),
            ('i3', 85.1, 91.9, 1.0, 'bottom', False),
            ('i2', 87.64, 91.9, 1.0, 'bottom', False),
            ('i1', 90.18, 91.9, 1.0, 'bottom', False),
            ('i0', 92.72, 91.9, 1.0, 'bottom', False),
        ),
    },
    {
        'ref': 'J12',
        'name': 'BIDIR',
        'pads': (
            ('1', 'rect', 115.56, 93.0, 1.7, 'uio0'),
            ('2', 'oval', 113.02, 93.0, 1.7, 'uio1'),
            ('3', 'oval', 110.48, 93.0, 1.7, 'uio2'),
            ('4', 'oval', 107.94, 93.0, 1.7, 'uio3'),
            ('5', 'oval', 105.4, 93.0, 1.7, 'GND'),
            ('6', 'circle', 102.86, 93.0, 1.7, '+3V3'),
            ('7', 'oval', 115.56, 95.54, 1.7, '/uio4'),
            ('8', 'oval', 113.02, 95.54, 1.7, '/uio5'),
            ('9', 'oval', 110.48, 95.54, 1.7, '/uio6'),
            ('10', 'oval', 107.94, 95.54, 1.7, '/uio7'),
            ('11', 'oval', 105.4, 95.54, 1.7, 'GND'),
            ('12', 'oval', 102.86, 95.54, 1.7, '+3V3'),
        ),
        'mark': (
            (101.53, 91.89, 102.86, 91.89),
            (101.53, 93.0, 101.53, 91.89),
        ),
        'corner': (101.53, 91.89),
        'body': (
            (101.59, 98.03, 102.56, 97.06),
            (101.59, 105.57, 101.59, 98.03),
            (102.56, 97.06, 116.83, 97.06),
            (116.83, 97.06, 116.83, 105.57),
            (116.83, 105.57, 101.59, 105.57),
        ),
        'lines': (
            (116.7, 87.2, 116.7, 91.9),
            (102.5, 86.2, 115.7, 86.2),
            (101.5, 91.8, 101.5, 87.2),
        ),
        'arcs': (
            (115.7, 86.2, 116.4071, 86.4929, 116.7, 87.2),
            (101.5, 87.2, 101.7929, 86.4929, 102.5, 86.2),
        ),
        'blocks': (
            (104.1, 91.4, 106.7, 96.9),
        ),
        'texts': (
            ('BIDIR', 111.8, 88.9, 2.0, 'bottom', True),
            ('uio', 116.5, 90.5, 1.4, 'right bottom', True),
            ('b3', 108.08, 91.9, 1.0, 'bottom', False),
            ('b2', 110.62, 91.9, 1.0, 'bottom', False),
            ('b1', 113.16, 91.9, 1.0, 'bottom', False),
            ('b0', 115.7, 91.9, 1.0, 'bottom', False),
        ),
    },
    {
        'ref': 'J13',
        'name': 'OUTPUT',
        'pads': (
            ('1', 'rect', 138.42, 93.0, 1.7, 'uo_out0'),
            ('2', 'oval', 135.88, 93.0, 1.7, 'uo_out1'),
            ('3', 'oval', 133.34, 93.0, 1.7, 'uo_out2'),
            ('4', 'oval', 130.8, 93.0, 1.7, 'uo_out3'),
            ('5', 'oval', 128.26, 93.0, 1.7, 'GND'),
            ('6', 'circle', 125.72, 93.0, 1.7, '+3V3'),
            ('7', 'oval', 138.42, 95.54, 1.7, '/uo_out4'),
            ('8', 'oval', 135.88, 95.54, 1.7, '/uo_out5'),
            ('9', 'oval', 133.34, 95.54, 1.7, '/uo_out6'),
            ('10', 'oval', 130.8, 95.54, 1.7, '/uo_out7'),
            ('11', 'oval', 128.26, 95.54, 1.7, 'GND'),
            ('12', 'oval', 125.72, 95.54, 1.7, '+3V3'),
        ),
        'mark': (
            (124.39, 91.89, 125.72, 91.89),
            (124.39, 93.0, 124.39, 91.89),
        ),
        'corner': (124.39, 91.89),
        'body': (
            (124.45, 98.03, 125.42, 97.06),
            (124.45, 105.57, 124.45, 98.03),
            (125.42, 97.06, 139.69, 97.06),
            (139.69, 97.06, 139.69, 105.57),
            (139.69, 105.57, 124.45, 105.57),
        ),
        'lines': (
            (124.4, 91.8, 124.4, 87.2),
            (139.6, 87.2, 139.6, 91.9),
            (125.4, 86.2, 138.6, 86.2),
        ),
        'arcs': (
            (138.6, 86.2, 139.3071, 86.4929, 139.6, 87.2),
            (124.4, 87.2, 124.6929, 86.4929, 125.4, 86.2),
        ),
        'blocks': (
            (127.0, 91.4, 129.6, 96.9),
        ),
        'texts': (
            ('OUTPUT', 133.6, 88.9, 1.7, 'bottom', True),
            ('uo_out', 139.3, 90.5, 1.4, 'right bottom', True),
            ('o3', 130.78, 91.9, 1.0, 'bottom', False),
            ('o2', 133.32, 91.9, 1.0, 'bottom', False),
            ('o1', 135.86, 91.9, 1.0, 'bottom', False),
            ('o0', 138.4, 91.9, 1.0, 'bottom', False),
        ),
    },
)
