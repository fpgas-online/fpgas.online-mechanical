# Raspberry Pi camera modules

The camera boards, drawn for the thing that actually gets designed round them:
a mount with a light path through it. Each sheet marks the board outline, the
four mounting holes, the lens and sensor module with its optical axis, and the
camera FFC connector on the underside.

| | |
|---|---|
| `boards.py` | **Generated.** Camera Module 2, and Camera Module 3 standard and wide |
| `extract.py` | Reads Raspberry Pi Ltd's own drawings and writes `boards.py` |
| `output/` | `RPICAM-2` and `RPICAM-3`, as SVG and PDF, and `raspberry-pi-camera-sheets.pdf`, the two bound into one document |

```sh
tools/fetch_raspberry_pi_camera.sh                    # once, needs network
uv run --no-project --with pdfplumber python raspberry_pi_camera/extract.py
```

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/cm2.pdf"><img src="output/previews/cm2.png" width="270" alt="RPICAM-2 Raspberry Pi Camera Module 2"></a><br>
<b>RPICAM-2</b> Raspberry Pi Camera Module 2<br>25 x 23.862 mm, Sony IMX219
</td>
<td width="33%" valign="top" align="center">
<a href="output/cm3.pdf"><img src="output/previews/cm3.png" width="270" alt="RPICAM-3 Raspberry Pi Camera Module 3"></a><br>
<b>RPICAM-3</b> Raspberry Pi Camera Module 3<br>25 x 23.862 mm, standard and wide, Sony IMX708
</td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

Three PDFs, all Raspberry Pi Ltd's, all vector, none of them a DXF:

| Sheet | Drawing | Published |
|---|---|---|
| `RPICAM-2` | [`camera-module-2-mechanical-drawing.pdf`](https://datasheets.raspberrypi.com/camera/camera-module-2-mechanical-drawing.pdf), title block **RASPBERRY PI CAMERA MODULE V2.1**, ref `RPI-CAM-V2_1` | dated 12/11/2015, drawn Mike Stimson, approved James Adams |
| `RPICAM-3` | [`camera-module-3-standard-mechanical-drawing.pdf`](https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf), `RP-008153-DS-1` | on the Product Information Portal, [Camera Module 3 design files](https://pip.raspberrypi.com/categories/1207-design-files) |
| `RPICAM-3` | [`camera-module-3-wide-mechanical-drawing.pdf`](https://datasheets.raspberrypi.com/camera/camera-module-3-wide-mechanical-drawing.pdf), `RP-008155-DS-1` | the same place |

## Neither plot is assumed to be 1:1

A PDF is CAD data only once you know what scale it was plotted at, so the
scale is *recovered* rather than assumed, the way `raspberry_pi/extract.py`
recovers the Pi 5's. Camera Module 3 turns out to be a true 1:1 plot; Camera
Module 2 turns out to be plotted at 1.5055.

The invariant is the mounting hole rectangle: 21 mm apart across the board,
12.5 mm apart up it, the lower pair 2 mm in from two edges. Finding it fixes
the origin, the orientation and the scale at once, and the two overall
dimensions the drawing prints are then required to come back out of it.

| | Recovered plot scale | Outline came back within |
|---|---|---|
| Camera Module 2 | **1.5055 : 1** | 0.031 mm of 25 x 23.862 |
| Camera Module 3 | **1.0000 : 1** | 0.004 mm of 25 x 23.862 |

The Camera Module 2 drawing is half again bigger than the part. A reader who
took the page at face value would get a 37.6 x 35.9 mm camera.

## What is machine-read and what is only printed

The two drawings are not equally readable, and the sheets say so.

- **Camera Module 3** carries its dimension text *as text*, and both
  drawings are checked, each against its own figures. Thirteen are on both --
  `25`, `23.862`, `12.5`, `14.5`, `14.4`, `10.8`, `8.9`, `ø2.2`, `ø4.75`,
  `1.12`, `2.75`, `5.71`, `19.61` -- the standard adds `ø5.75`, `11.3`,
  `6.98`, `66` and `41`, and the wide adds `ø6.95`, `12`, `8.3`, `102` and
  `67`. The comparison is against whole words, not a substring of the page:
  `12` is a figure the wide drawing prints on its own *and* the first half of
  the `12.5` both of them print. A transcription error fails the extraction
  rather than reaching a sheet.
- **Camera Module 2** carries none. `page.chars` is empty: every digit on it
  is a filled path. Its geometry is machine-read exactly as the other's is,
  but its printed dimensions are transcribed by eye, and the sheet carries a
  note saying that.

What was machine-read on each, in board coordinates (origin at the lower-left
corner, X across the 25 mm width, Y up the 23.862 mm height, viewed from the
lens side):

| | Camera Module 2 | Camera Module 3 |
|---|---|---|
| Outline | 25 x 23.862, R2.0 corners | the same |
| Mounting holes | ø2.2 at (2.00, 2.00), (22.98, 2.00), (2.00, 14.52), (22.98, 14.52) | ø2.2 with a ø4.75 land, at (2.00, 2.00), (23.00, 2.00), (2.00, 14.50), (23.00, 14.50) |
| Lens and sensor module | 8.45 x 8.49, centre (12.49, 14.40) | 10.80 x 10.80, centre (12.50, 14.40) |
| Clear aperture | not dimensioned | printed ø5.75 standard, ø6.95 wide; **drawn 5.750 and 7.000** |
| FFC connector, underside | 20.88 x 5.52, from the plan view | 19.61 x 5.71, from the two elevations |
| Board thickness | not stated | 1.12 |
| Height | **not stated anywhere on the drawing** | 11.3 standard, 12 wide, printed |

Raspberry Pi state that "board dimensions and mounting-hole positions for
Camera Module 3 are identical to Camera Module 2"
([camera.html, Advanced information](https://www.raspberrypi.com/documentation/accessories/camera.html)).
That is not taken on trust: each drawing is read on its own and the two hole
patterns compared. **They agree to 0.025 mm**, which is the plot noise of the
1.5:1 source, so the sheets may repeat the claim. The lens module is where the
two boards differ, and by the figures above it grew from 8.5 to 10.8 mm square
without its optical axis moving: 0.01 mm apart on two independent drawings.

## Where these drawings disagree with themselves

Worth knowing before designing to them. The Camera Module 3 drawing's side and
front elevations are 1:1 for the board section (1.120 drawn against 1.12
printed) and for the connector (2.750 against 2.75), but the lens stack is
drawn short: the printed 11.3 mm overall scales 10.08, and 6.98 above the
board scales 5.81. The wide drawing does the same, 12 printed against 10.93
drawn.

It is not only the heights. The **wide drawing's clear aperture is printed
`ø6.95` and drawn 7.000**, while the standard's `ø5.75` is drawn 5.750
exactly; the extractor measures the aperture on each drawing rather than
transcribing it, requires the two to stay within 0.2 mm, and prints both, and
`RPICAM-3` says both numbers. The High Quality Camera drawing does the same
thing again, `ø30.75` scaling 30.42 and `ø22.4` scaling 22.25 while its ø2.5
mounting holes scale 2.500 exactly.

The printed figures are the specification and the sheets quote them as
printed; the sheets do not dimension the height, because there is no view on
them to dimension it on and the source's own geometry would disagree with the
number.

## What is not here, and why

**Camera Module 1, the OV5647 board.** There is no official Raspberry Pi
mechanical drawing for it, and there never was. It has no category on the
Product Information Portal -- the peripherals index lists Camera Module 2,
Camera Module 3, the High Quality Camera and the Global Shutter Camera and
nothing earlier -- `datasheets.raspberrypi.com/camera/` has never served one,
and the archived `raspberrypi.org/documentation/hardware/camera/mechanical/`
directory held drawings for the v2 camera and the HQ camera only. The
documentation gives "around 25 × 24 × 9 mm" in a product table, which is a
product table and not a drawing. Rather than draw a sheet from a specification
table, the board is left out. Third-party OV5647 modules in 65 and 120 degree
lenses are a different matter: they are somebody else's part with somebody
else's drawing, and belong to whoever draws them.

**The High Quality Camera.** Its drawing *does* exist and was read --
[`RP-008200-DS-1`, hq-camera-cs-mechanical-drawing](https://pip.raspberrypi.com/documents/RP-008200-DS),
a 2.34618:1 plot on A4 landscape, with a live text layer. Machine-read from
it: a 38 x 38 mm outline; four ø2.5 holes 4.04 mm in from each corner, 29.94
apart; the 8.5 mm sensor square on the board centre; the C/CS lens mount as
`ø30.75` over an `ø22.4` aperture inside a knurled `ø36` ring drawn scalloped
between 35.38 and 38.00; and a tripod boss centred on the lower edge and
reaching 11.35 mm below it, printed `13.97` across where the drawing draws
13.86. The thread is *not* on that drawing: `1/4–20 UNC` appears in the
separate CS/M12 mount document,
[`RP-008201-DS-1`](https://pip.raspberrypi.com/documents/RP-008201-DS),
published February 2025, whose physical-specification page redraws both
mounts at a reduced scale. The camera has no sheet here for two
reasons, both about the source and the renderer rather than about the camera:
`board_sheet.render_board` draws every scheduled feature as a rectangle, and a
ø36 knurled ring drawn as a square is a worse drawing than none; and the
drawing never locates the FFC connector in plan at all -- it appears only in
the side elevation, as a 5.71 x 2.75 section -- so one of the five things
these sheets exist to mark cannot be marked. `TODO.md` carries it.

**The sensor module's lower body, as a scheduled feature.** It was
considered and left out. On both boards the module has a body below the lens
housing that reaches toward the lower edge -- stepped on the Camera Module 2,
notched on the Camera Module 3 -- and it is raised material a mount has to
clear, so it is not nothing. But a `Feature` is a bounding box, and a
schedule entry reading "6.72 to 16.14" for a shape with a step in it would be
a precise-looking figure that is wrong at the corner it omits. Both sheets
carry its extents in a note instead, where prose can say "stepped", and both
say where they came from. Drawing it properly needs a feature that is a
profile rather than a box, which is the same change the High Quality Camera
wants; `TODO.md` carries that one.

**The Global Shutter Camera and the AI Camera.** Drawings exist
([`RP-008195-DS`](https://pip.raspberrypi.com/documents/RP-008195-DS) for the
GS Camera); neither was asked for and neither is drawn.

**The Camera Module 3 STEP model.**
[`camera-module-3-step.zip`](https://datasheets.raspberrypi.com/camera/camera-module-3-step.zip)
is published and was not used. The drawing is a true 1:1 plot with a live text
layer and gives everything these sheets need; a 10 MB assembly would be a
second source for the same numbers.

## Feature numbers

Fixed across the family, as they are on the Raspberry Pi sheets: **1** is the
lens and sensor module and **2** is the camera FFC connector, on every sheet.
