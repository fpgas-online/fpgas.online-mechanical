# The camera holder

A printed stand that bolts onto the [generic mounting
plate](../mounting_plate/README.md) and holds a Raspberry Pi Camera Module
v1.3, lens down, over whichever Tiny Tapeout demo board is on the plate --
where [`RPICAM-OVER-PLATE`](../../raspberry_pi_camera/README.md) says the
camera has to be for its lens to take in the whole board, of every revision.
One per lens: `TT-MP-CAM65` for the stock 65 degree lens, and
`TT-MP-CAM120`, about half as tall, for the 120 degree fisheye.

| | |
|---|---|
| `holder.py` | **Hand-written, derived.** The holder as boxes and holes, worked out at import from the optics, the plate and the camera, once per lens |
| `verify.py` | Proves, for each holder, the camera is where it has to be, every board is in the picture and none of it is hidden, nothing touches a board, a standoff or a cable, and every fastener fits; and that the two share their beam and carrier |
| `export_step.py` | Writes each holder's assembly as a STEP, and each part as a STEP lying the way it prints |
| `export_dxf.py` | Writes the beam, the one flat part, as a DXF cut file |
| `output/` | `TT-MP-CAM65` and `TT-MP-CAM120`, as SVG and PDF, the STEP files and the DXF |

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
  all round, made 4:3. Its centre is (63.38, 44.82) on the plate. The stock
  lens's declared 53.50 x 41.41 degrees reach it from 139.17 mm above the
  board face, and the wide lens's 96 x 72 from 72.40. That is
  `RPICAM-OVER-PLATE`'s derivation; the holder only adds the plate
  underneath it.
- **What it stands on** is `tinytapeout/mounting_plate/plate.py`: the
  outline, the four M4 fixings along the plate's left and right edges, and
  the 8 mm standoff every board now stands on, so the highest board face is
  8 + 1.60 = 9.60 mm above the plate. The lens face therefore has to be at
  least 148.77 mm above the plate face for the stock lens and 82.00 for the
  wide one. They are set at **150.00** and **83.00**: a millimetre over for
  the print, rounded up to a figure a rule can check.
- **What it carries** is `raspberry_pi_camera/v1.py`, the Camera Module
  v1.3 written by hand from Gert van Loo's 2013 hand-measured sheet and
  checked against Raspberry Pi Spy's caliper measurement: its ø2.0 holes
  (±0.2) on the 21 x 12.5 pattern, its optical axis (±0.65, since the lens
  module is glued on and the two measurements disagree by up to that), its
  0.95 board, the lens 5.20 proud of it, and the FFC connector 2.8 deep on
  the far face. The picture has 5.47 mm to spare round the tightest board,
  so the lens's ±0.65 is well inside it. A board whose holes come out at the
  bottom of their tolerance will not take an M2 until they are opened with a
  2.0 drill.

## A holder per lens

The 120 degree lens takes the same frame in from 72.40 mm where the stock
lens needs 139.17, so its lens face goes 67 mm lower. That is a second
holder rather than an adjustable one. A carrier that slid 67 mm up and down
the posts would be set by eye, locked by friction, and knocked; a fixed
height is one a rule can check and nobody can set wrong, and the notes on
each sheet give it. And the second holder costs little: everything above the
lens face is the same stack, so the **beam and the carrier are the same two
parts in both**, only lower, and `verify.py` checks it box by box. Only the
side frames differ, in how long their posts are.

The wide lens sees the rig. Its picture is 20.5 mm wider than frame A across
the plate, so the side frames show in it, outside every board, and anything
standing on a board may rise only 6.9 mm before it leaves the picture,
against 13.2 at 65 degrees. `verify.py` still finds every sight line from
the lens to every board clear.

**Which 120 degree camera.** The lens sold as 120 degrees on an OV5647 is
Arducam's B006604, a spy camera for the Pi Zero, 60 x 11.5 mm on its flex,
which this carrier does not take. `TT-MP-CAM120` carries a Camera Module
v1.3's board -- its holes, its lens axis, its lens face 5.20 mm off the
board -- with a 120 degree lens ASSUMED on it. That is the weak point of this
holder, and it is not a small one. A module whose lens stands further off
its board puts the face lower by the difference, and the 1.00 mm over the
least is all there is to take it: an M12 fisheye on a v1.3-sized board
stands far more than 5.20 mm proud, and with the face 10 mm low the picture
covers about 92 mm down the plate against the boards' 95.2, so their edges
are cut off. YXF's M6 lens, 4.48 mm long, is the kind of lens it does fit.
Before building it, measure the lens that will go in it; a carrier for the
B006604 itself, or bosses cut to a measured lens, is in `TODO.md`.

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
plate, and it is a window: a post at each end, 8 mm long, a rail over the
top, the foot under the bottom, and nothing between. A peripheral in one of
those positions comes out through the window.

**The feet share the plate's own fixings.** Each foot sits over the two M4
fixings the plate already has along that edge and is clamped by the same
screws, so the plate needs no new hole and the holder cannot be put on
anywhere but where it was designed to go. On a plate standing alone that is
an M4 x 16 button head, washer and nut; on a plate bolted to a chassis, the
plate's own screws 5 mm longer. The button head is low enough -- 7.20 mm
above the plate with the 5 mm foot -- to sit under a side Pmod body on a
board that overhangs it.

**The camera hangs from a carrier that turns.** The camera has to be turned
so that its long image axis lies along the plate's X: frame A is 140.27 wide
and 105.20 deep, and a quarter turn out the picture falls 17.1 mm short at
each end, or 16.8 on the 120 degree holder. Nobody publishes which way the OV5647's pixel rows run on the
module, so the holder assumes the long axis is along the board's 25 mm width
and makes the assumption cheap to be wrong about: the camera screws to a
carrier, and the carrier bolts to the beam's pad on a square of four M3
fixings centred on the lens axis. Turn it a quarter turn and the lens does
not move. Check the first picture.

**The camera screws up into the carrier.** Four M2 x 10, heads on the lens
side, through the camera's holes and the carrier's bosses into nuts sitting
in hex pockets in the carrier's top face, 0.75 mm clear of the beam's pad
the carrier bolts up against. The camera's holes are ø2.0 as measured and
carried ±0.2; an M2 goes through them as measured, and a tight one wants
opening with a 2.0 drill.

**The FFC leaves under the carrier.** The carrier's bosses stand it 3.80 mm
off the camera's far face, a millimetre over the connector, and the cable
leaves the connector 1.27 mm down, towards the back, and out from under the
carrier with 7 mm to the nearest boss or nut. Plug it in before the camera
goes on -- the connector's latch is out of reach in that gap -- and take it
up and back over the beam: a cable drooping behind the camera would hang
into the picture.

**How stiff it is.** Not checked, estimated: a 10 mm square PETG post is
about 1.5 N/mm as a 150 mm cantilever, so four about 6 N/mm before the feet
give. These posts are 8 mm front to back, which about halves that fore and
aft, before the rail and the beam brace them into a frame. A few-gram camera does not load it; a knock moves it and the
5 mm margin takes a millimetre or two. The weak point is where each foot
leaves the plate's edge, loaded across its print layers. The 120 degree
holder's posts are 84 mm rather than 151, and a cantilever's stiffness goes
as the cube of its length, so it is about six times as stiff.

**Nothing of it is between the lens and a board.** `verify.py` walks the
sight lines from the lens face to every revision's envelope and finds them
clear. The side frames' lower ends are in the picture's margin, outside every
board, which is why the notes ask for matte black.

## Printing it

All PETG or anything else opaque, at least four
perimeters so the screws have wall to bite. Each lies with no overhang:

| Part | Printed | As it lies |
|---|---|---|
| Side frame, left and right, 65 degree holder | on its outer face, the foot standing up from the bed | 166.0 x 92.0 x 18.7 mm |
| Side frame, left and right, 120 degree holder | the same | 99.0 x 92.0 x 18.7 mm |
| Beam, both holders | flat, on its top face | 152.0 x 46.0 x 6.0 mm |
| Camera carrier, both holders | on its top face, bosses up, nut pockets on the bed | 46.0 x 46.0 x 9.8 mm |

The right side frame is the left one mirrored, not turned: the foot's
fixings are not symmetric along the frame, so each has its own file,
`tt-camera-holder-65-side-left.step` and `-side-right.step`, and the same
for `-120-`. The beam and the carrier are one file each,
`tt-camera-holder-beam.step` and `tt-camera-holder-carrier.step`, for both
holders. `tt-camera-holder-65.step` and `tt-camera-holder-120.step` are the
assemblies, every part where it goes over the plate. The beam is flat, so it
can be cut from 6 mm sheet from `tt-camera-holder-beam.dxf` instead of
printed.

## What is assumed, and what is not known

- **Which way the pixel rows run.** ASSUMED, as above, and made cheap to
  correct.
- **Focus.** Both fixed lenses are "1 m to infinity". The stock lens's face
  is 140.4 mm above the board and the wide lens's 73.4: the boards are out
  of focus, a point spreading to about 21 pixels, 1.1 mm on the board, and
  18 pixels, 0.8 mm, on the thin-lens estimate `RPICAM-LENS` explains. The
  holders put each camera where its field of view is right; they cannot make
  it focus there. Arducam's motorised OV5647, the B0176, focuses from 80 mm
  and would. Its board is the stock module's 24 x 25 mm, but nobody
  dimensions its hole pattern or its taller voice-coil lens, so it has no
  holder here.
- **The 120 degree camera** is a v1.3's board with a wide lens ASSUMED on
  it, as above.
- **The boards' buttons** are not in `tinytapeout/boards.py`, so nothing
  checks them. They are pressed from above, and above the boards there is
  nothing but the beam, 166 mm up on the 65 degree holder and 99 on the
  120.
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
