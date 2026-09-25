# The camera holder

A printed stand that bolts onto the [generic mounting
plate](../mounting_plate/README.md) and holds a Raspberry Pi Camera Module
v1.3, lens down, over whichever Tiny Tapeout demo board is on the plate --
where [`RPICAM-OVER-PLATE`](../../raspberry_pi_camera/README.md) says the
camera has to be for the stock 65 degree lens to take in the whole board, of
every revision.

| | |
|---|---|
| `holder.py` | **Hand-written, derived.** The holder as boxes and holes, worked out at import from the optics, the plate and the camera |
| `verify.py` | Proves the camera is where it has to be, every board is in the picture and none of it is hidden, nothing touches a board, a standoff or a cable, and every fastener fits |
| `export_step.py` | Writes the assembly as a STEP, and each part as a STEP lying the way it prints |
| `export_dxf.py` | Writes the beam, the one flat part, as a DXF cut file |
| `output/` | `TT-MP-CAMERA`, as SVG and PDF, the STEP files and the DXF |

```sh
uv run --no-project python tinytapeout/camera_holder/verify.py
uv run --no-project --with cadquery python tinytapeout/camera_holder/export_step.py
uv run --no-project --with ezdxf python tinytapeout/camera_holder/export_dxf.py
```

## The sheet

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/tt-camera-holder.pdf"><img src="output/previews/tt-camera-holder.png" width="270" alt="TT-MP-CAMERA Camera Holder, TT Mounting Plate"></a><br>
<b>TT-MP-CAMERA</b> Camera Holder, TT Mounting Plate<br>Holds a Camera Module over every demo board revision
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

Nothing in `holder.py` is typed in that another module already knows:

- **Where the lens goes** is `raspberry_pi_camera/optics.py`'s plate
  subject, frame A: the union of every revision's assembled envelope --
  outline, connectors, and the Pmod bodies over the front edge -- plus 5 mm
  all round, made 4:3. Its centre is (63.38, 44.82) on the plate, and the
  stock lens's declared 53.50 x 41.41 degrees reach it from 139.17 mm above
  the board face. That is `RPICAM-OVER-PLATE`'s derivation; the holder only
  adds the plate underneath it.
- **What it stands on** is `tinytapeout/mounting_plate/plate.py`: the
  outline, the four M4 fixings along the plate's left and right edges, and
  the 8 mm standoff every board now stands on, so the highest board face is
  8 + 1.60 = 9.60 mm above the plate. The lens face therefore has to be at
  least 148.77 mm above the plate face. It is set at **150.00**: a
  millimetre over that for the print, rounded up to a figure a rule can
  check.
- **What it carries** is `raspberry_pi_camera/v1.py`, the Camera Module
  v1.3 written by hand from Gert van Loo's 2013 hand-measured sheet and
  checked against Raspberry Pi Spy's caliper measurement: its ø2.0 holes
  on the 21 x 12.5 pattern, its optical axis (±0.4, since the lens module
  is glued on), its 0.95 board, the lens 5.20 proud of it, and the FFC
  connector 2.8 deep on the far face.

## Why it is shaped like this

**A portal, open front and back.** Every revision's Pmod hosts face the
front edge and every revision's USB-C connector is on the front or the back,
so those two sides cannot carry anything. The holder is two side frames on
the plate's left and right edges and a beam across their tops; the camera
hangs from the beam's middle.

**Each side frame is a window.** Two revisions, DB 4+ and DB 06+, carry
three side Pmod positions along their left edge, J12 to J14, not fitted. Their
connector bodies stand 2.50 mm in from the plate's edge, so the side frame's
wall is outside that, its inner face 1.00 mm clear of them and mostly off the
plate, and it is a window: a post at each end, 9 mm long, a rail over the
top, the foot under the bottom, and nothing between. A peripheral in one of
those positions comes out through the window.

**The feet share the plate's own fixings.** Each foot sits over the two M4
fixings the plate already has along that edge and is clamped by the same
screws, so the plate needs no new hole and the holder cannot be put on
anywhere but where it was designed to go. On a plate standing alone that is
an M4 x 12 button head, washer and nut; on a plate bolted to a chassis, the
plate's own screws 5 mm longer. The button head is low enough -- 7.20 mm
above the plate with the 5 mm foot -- to sit under a side Pmod body on a
board that overhangs it.

**The camera hangs from a carrier that turns.** The camera has to be turned
so that its long image axis lies along the plate's X: frame A is 140.27 wide
and 105.20 deep, and a quarter turn out the picture falls 17.1 mm short at
each end. Nobody publishes which way the OV5647's pixel rows run on the
module, so the holder assumes the long axis is along the board's 25 mm width
and makes the assumption cheap to be wrong about: the camera screws to a
carrier, and the carrier bolts to the beam's pad on a square of four M3
fixings centred on the lens axis. Turn it a quarter turn and the lens does
not move. Check the first picture.

**The FFC leaves under the carrier.** The carrier's bosses stand it 3.80 mm
off the camera's far face, a millimetre over the connector, and the cable
leaves the connector 1.27 mm down, towards the back, and out from under the
carrier with 7 mm to the nearest boss or nut. Take it up behind the beam.

**Nothing of it is between the lens and a board.** `verify.py` walks the
sight lines from the lens face to every revision's envelope and finds them
clear. The side frames' lower ends are in the picture's margin, outside every
board, which is why the notes ask for matte black.

## Printing it

Four parts, three different, all PETG or anything else opaque, at least four
perimeters so the screws have wall to bite. Each lies with no overhang:

| Part | Printed | As it lies |
|---|---|---|
| Side frame, left and right | on its outer face, the foot standing up from the bed | 163.9 x 92.0 x 18.7 mm |
| Beam | flat, on its top face | 152.0 x 46.0 x 6.0 mm |
| Camera carrier | on its top face, bosses up | 46.0 x 46.0 x 7.8 mm |

The right side frame is the left one mirrored, not turned: the foot's
fixings are not symmetric along the frame, so each has its own file,
`tt-camera-holder-side-left.step` and `tt-camera-holder-side-right.step`.
`tt-camera-holder.step` is the assembly, every part where it goes over the
plate. The beam is flat, so it can be cut from 6 mm sheet from
`tt-camera-holder-beam.dxf` instead of printed.

## What is assumed, and what is not known

- **Which way the pixel rows run.** ASSUMED, as above, and made cheap to
  correct.
- **Focus.** The stock lens is "Approx 1 m to ∞" and the lens face is
  140.4 mm above the board: the boards are out of focus, a point spreading to
  about 21 pixels, 1.1 mm on the board, on the thin-lens estimate
  `RPICAM-OVER-PLATE` explains. The holder puts the stock camera where its
  field of view is right; it cannot make it focus there.
- **The boards' buttons** are not in `tinytapeout/boards.py`, so nothing
  checks them. They are pressed from above, and above the boards there is
  nothing but the beam 164 mm up.
- **Heights on the boards.** No board file gives a component a height, so
  `verify.py` keeps the holder out of every revision's envelope at every
  height from the board's underside to the lens.
- **The camera's small parts** beside the lens module -- LED D1 and R9 by
  MT1 in Raspberry Pi Spy's photograph -- are not dimensioned by any source,
  so the M2 screw heads on the lens side are checked against the lens module
  and its flex tail, not against them.

## Coordinates

The plate's: origin at its lower-left corner, X right, Y towards the back,
seen from above, and Z up from its **top** face. `holder.py` gives every part
as boxes and holes in those coordinates, and the drawing, the STEP and
`verify.py` all read them from there.
