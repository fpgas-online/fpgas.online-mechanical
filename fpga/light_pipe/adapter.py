"""Arty A7 Ethernet LED light pipe adapter.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber \\
        python fpga/light_pipe/design.py

Jack frame, used by every dimension here: origin on the jack's centre plane,
in its front face, at the board's top surface.  X runs back into the board,
Y across it and Z up.  ``JACK_FACE_X`` and ``JACK_CENTRE_Y`` put that frame on
the Arty A7 of ``fpga/boards.py``.

The part is symmetric about Y = 0.  One cheek, bore, pocket, roof slot and
skirt are given; the other of each is its mirror image.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Outline, Source


#: The jack the adapter clips onto, and where it is.
JACK_PART = '08B0-1X1T-36-F'
JACK_DESIGNATOR = 'J9'
JACK_ON_SHEET = 'sheet 8 of 12, ETHERNET: J9 is 08B0-1X1T-36-F'
SHIELD_W = 16.31
SHIELD_H = 13.49
BODY_D = 25.53
SPRING_PROUD = 1.4
SPRING_PROUD_TOL = 0.51
SPRING_FRONT = 0.64
SPRING_TOP_LEN = 6.35
FACE_TO_PEG = 7.75
#: Bel's title block, on a three-decimal inch dimension.
BEL_TOL = 0.254

#: Measured off Bel's front view, whose plot scale is recovered per
#: axis from the two overall dimensions it states.  The axes agree
#: to 0.58 %; figures from this
#: view are good to about +/-0.20 mm.
READ_TOL = 0.20
PLOT_ANISO = 0.99420

#: One LED window, as distances from the jack's centre plane and the
#: board's top surface.  The other is its mirror.
WINDOW_Y0, WINDOW_Y1 = 5.04, 7.92
WINDOW_Z0, WINDOW_Z1 = 10.632, 13.204

#: The opening a plug goes through, and the keyway its latch enters.
APERTURE_Y, APERTURE_Z0, APERTURE_Z1 = 6.56, 3.02, 10.64
KEYWAY_Y, KEYWAY_Z0, KEYWAY_Z1 = 3.32, 10.64, 13.49

#: The EMI springs: the side pair is what grips the skirts, the top
#: pair is what the roof's slots clear.
SIDE_SPRING_Y, SIDE_SPRING_Z0, SIDE_SPRING_Z1 = 9.18, 7.945, 8.803
TOP_SPRING_Y0, TOP_SPRING_Y1, TOP_SPRING_Z = 2.92, 4.12, 14.519

#: The jack on the Arty A7, from Digilent's DXF: the centre line and
#: front face of the frame above, in board coordinates.
BOARD_KEY = 'arty-a7'
JACK_CENTRE_Y = 44.0
JACK_FACE_X = -0.101
PEG_X = 7.649
PEG_SPACING_DXF = 16.104
PEG_SPACING_BEL = 16.13

#: The light pipe, from Bivar's drawing.
PIPE_PART = 'PLP2-4MM'
PIPE_SERIES = 'PLP2'
PIPE_LEN = 4.0
PIPE_DIA = 2.8
PIPE_RIB_DIA = 3.1
FLANGE_DIA = 3.3
FLANGE_T = 0.8
PIPE_HOLE = 2.92
PIPE_HOLE_PLUS, PIPE_HOLE_MINUS = 0.08, 0.05
PANEL_MIN, PANEL_MAX = 1.19, 2.36
PIPE_MATERIAL = 'polycarbonate, 94V-0, clear'
PIPE_ON_SHEET = 'PLP2-4MM is on the offering list; material polycarbonate, 94V-0, clear'

#: The bore: a cylinder at 45 degrees in the X-Z plane, rising
#: forwards.  Along its axis z - x does not change, so the plane the
#: pipe's tip lies on and the plane its flange seats on are two
#: values of z - x.  (BORE_X, BORE_Z) is the tip's centre.
BORE_ANGLE = 45.0
BORE_Y = 6.48
BORE_X, BORE_Z = -1.29, 12.08
BORE_DIA = 3.2
PRESS_DIA, PRESS_LEN = 2.92, 2.0
ENTRY_K = 13.37
FACET_K = 19.027
FACET_X, FACET_Z = -4.118, 14.908

#: The cheek: the block the bore runs through, cut off at the facet.
CHEEK_X0, CHEEK_X1 = -5.533, 0.0
CHEEK_Y0, CHEEK_Y1 = 4.08, 10.21
CHEEK_Z0, CHEEK_Z1 = 11.09, 16.377

#: The light pocket in the cheek's back face, open at the bottom: it
#: keeps the adapter off the LED window and lets the window see the
#: end of the pipe.
POCKET_X0, POCKET_X1 = -2.471, 0.0
POCKET_Y0, POCKET_Y1 = 4.83, 8.13
POCKET_Z0, POCKET_Z1 = 11.09, 13.354

#: The roof over the jack, which joins the two cheeks and the two
#: skirts, and the slot in it that clears a top EMI spring.
ROOF_X0, ROOF_X1 = 0.0, 10.0
ROOF_Y1 = 10.21
ROOF_Z0, ROOF_Z1 = 14.477, 16.377
SLOT_X0, SLOT_X1 = 0.0, 7.3
SLOT_Y0, SLOT_Y1 = 2.64, 4.4

#: The skirt down the side of the jack: the jack's own side EMI
#: spring bears on it, and that is what holds the adapter on.
SKIRT_X0, SKIRT_X1 = 0.0, 10.0
SKIRT_Y0, SKIRT_Y1 = 8.81, 10.21
SKIRT_Z0, SKIRT_Z1 = 6.95, 16.377

#: The envelope, for the sheet's views and for anything designing a
#: box around the board.
WIDTH, DEPTH, HEIGHT = 20.42, 15.533, 9.427

#: The clearances the design was built to, which verify.py checks the
#: finished geometry against.
CLEARANCES = {
    'plug aperture': 0.45,
    'pipe tip to jack face': 0.3,
    'bore to cheek inner face': 0.8,
    'skirt to shield': 0.52,
    'roof to shield': 0.86,
    'roof slot to top EMI spring': 0.28,
    'flange rim to the edge of its seat': 0.35,
}


ADAPTER = BoardSpec(
    key="arty-ethernet-light-pipe",
    title="Arty A7 Ethernet Light Pipe",
    subtitle="Clips over J9 and carries its two LEDs to a face you can see from above",
    family="lightpipe",
    body="enclosure",
    front_edge="left",
    outline=Outline(width=15.533, height=20.42, z_height=9.427),
    tolerance="printed +/-0.20   bore dia +0.05/-0   see notes",
    sources=(
        Source(label="Board schematic",
               ref="https://digilent.com/reference/_media/reference/programmable-logic/arty-a7/arty_a7_sch.pdf",
               note="Digilent, Arty A7 rev E.0, 2018-01-09: sheet 8 of 12, ETHERNET: J9 is 08B0-1X1T-36-F."),
        Source(label="Jack drawing",
               ref="https://www.belfuse.com/media/drawings/products/magjack%20ICMs/dr-mag-08b0-1x1t-36-f.pdf",
               note="Bel MagJack 08B0-1X1T-36-F, drawing 08B01X1T36-F rev E, 2018-03-18. Stated dimensions are its own; the LED windows, the plug aperture, the latch keyway and the EMI springs are measured off its front view, whose plot scale is recovered per axis from the 0.642 [16.31] and 0.531 [13.49] it dimensions (the axes agree to 0.58 %)."),
        Source(label="Board drawing",
               ref="https://digilent.com/reference/_media/reference/programmable-logic/arty-a7/arty_a7.zip",
               note="Digilent, Arty_A7_DXF.DXF: the two Ø1.575 mm board-lock pads at x = 7.649 put the jack's centre line at y = 44.0. They are 16.104 mm apart, against Bel's 0.635 [16.13], so the two drawings are of the same jack; Bel's 0.305 [7.75] from the pegs to the front face puts that face at x = -0.101."),
        Source(label="Light pipe drawing",
               ref="https://www.bivar.com/parts_content/Datasheets/PLP2-XXX.pdf",
               note="Bivar PLP2-XXX rev Y, 2018-07-06, press-fit panel mount front mount light pipe: PLP2-4MM is on the offering list; material polycarbonate, 94V-0, clear. The bore is built from its Ø0.115 +0.003/-0.002 recommended mounting hole and its 0.047-0.093 in panel thickness."),
    ),
    notes=(
        "The adapter slides onto the front of J9 and stops against its front face. Nothing fixes it but the jack's own side EMI springs, which stand 1.40 +/-0.51 mm proud of the shield and bear on the skirts: over that whole band the springs are deflected and the shield itself never touches.",
        "Print it upside down, on the top face. Every other face then rises from the plate, the two 45 degree facets and the two bores are the only overhangs, and neither needs support.",
        "Bore diameters are for a printed hole. A printer that comes out undersize will not take the pipe: ream the press-fit length to Bivar's Ø2.92 +0.08/-0.05 and test the fit on a scrap before printing the part.",
        "The pipe's tip is 0.30 mm in front of the jack's front face and its light crosses that gap in air. Nothing of the adapter touches the LED windows: the pocket clears both of them.",
        "A plug and a plain boot pass under the cheeks. A snagless boot whose hood stands above the plug's own top face within 6 mm of the jack will foul them; the note on the cheek gives the height that is clear.",
        "MEASURED figures come off Bel's front view and are good to about +/-0.20 mm. Figures Bel dimensions carry its own +/-0.254 mm (.XXX +/-0.010 in). Both are wider than the printed part's tolerance, and the clearances are sized for them.",
    ),
)
