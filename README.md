# Mechanical diagrams

2D orthographic (blueprint style) mechanical drawings of the hardware
[fpgas.online](https://fpgas.online) is built from: the boards, the adapters
and the accessories that end up in the same rack, plus the plates and
templates made to mount them.

The drawings are for designing the things the boards mount into -- plates,
brackets, enclosures, rack shelves. Every dimension is traceable to an
official source or, where a maker publishes none, was measured and checked,
and the sheet says so and to what tolerance. Each sheet lists its sources.

Adding hardware is the normal case. Each family lives in its own directory
with its data, the extractor that produces it and the sheets rendered from
it, so a new board is a new directory and does not disturb the others.

## What is here

| Directory | Sheets, and what they are of |
|-----------|------------------------------|
| [`tinytapeout/`](tinytapeout/README.md) | `TT-DB-*` -- Tiny Tapeout demo boards, one sheet per distinct geometry |
| [`tinytapeout/mounting_plate/`](tinytapeout/mounting_plate/README.md) | `TT-MP-*` -- The plate every demo board revision bolts onto, and its drill templates |
| [`tinytapeout/camera_holder/`](tinytapeout/camera_holder/README.md) | `TT-MP-CAM65`, `TT-MP-CAM120` -- A printed stand on the plate that holds a Camera Module v1.3 over whichever board is on it, one per lens, with STEP solids and a DXF |
| [`raspberry_pi/`](raspberry_pi/README.md) | `RPI-*` -- Raspberry Pi boards, and boards that take their HATs, each with a Digilent Pmod HAT Adapter overlaid, and the Raspberry Pis all on the one outline they share |
| [`raspberry_pi_camera/`](raspberry_pi_camera/README.md) | `RPICAM-*` -- Raspberry Pi camera modules, with the lens module, its optical axis and the FFC connector marked; the OV5647's stock, autofocus and 120 degree lenses, every figure declared and derived, and their focus; then where to put an OV5647 camera over a board to frame it: how high and where, in two elevations, and whether it is in focus there; over the plate and the Acorn, where the Camera Module v1.3's lens face goes with its lens refocused |
| [`fpga/`](fpga/README.md) | `FPGA-*` -- FPGA development boards, one sheet each, with Pmod, USB, Ethernet and LEDs marked |
| [`accessories/`](accessories/README.md) | `ACC-*` -- Parts that are none of the boards above but turn up in the same assemblies, such as Pi-to-Pmod adapters and PoE splitters, with [a comparison of the two Pi-to-Pmod adapters](accessories/raspmod-vs-pmod-hat.md) |
| [`tools/`](tools/README.md) | The [drafting library](tools/drafting/README.md), the generator and the checks |

Which boards and parts a family holds is in its own README, and every sheet
is shown [below](#the-sheets).

## What a sheet is called

A sheet's drawing name is its own file stem, in capitals, behind its family's
prefix: `fpga/output/arty-a7.pdf` is **`FPGA-ARTY-A7`** and
`raspberry_pi/output/rpi5.pdf` is **`RPI-5`**. The part of the stem the prefix
already says is dropped: the mounting plate's four stems all begin
`tt-generic-mounting-plate`, which is what `TT-MP` says.

Some families are named by a rule instead, because their file stems say more
than a drawing number can carry. A file name is read once from a directory
listing by somebody choosing between files, and can afford to say what a sheet
covers; a drawing number is read off a title block, quoted in a note on another
sheet, written on an order and said out loud across a workshop, so it has to be
short enough to take in at a glance and to copy without a slip -- at most four
or five characters behind the prefix. So the stems are left exactly as they
are, and only the name is cut:

- a demo board sheet is named for the first revision it covers, with the `p`
  separators taken out, so `tt-demo-board-v1p2p1-v1p2p3.pdf` is `TT-DB-V121`;
  or for the board name where the revisions carry one, so
  `tt-demo-board-tt123-v2p2p5-v2p2p6.pdf` is `TT-DB-TT123`. A sheet covers one
  geometry and the first revision to carry it is where that geometry came
  from -- v1.2.2 and v1.2.3 are on the `TT-DB-V121` sheet because mechanically
  they are the v1.2.1 board -- while the sheet's title, subtitle and notes list
  every revision and shuttle in full.
- an accessory is named for what kind of part it is and which one of that kind:
  `ACC-HAT-PMOD` and `ACC-HAT-RMOD` are the two ways of putting Pmod ports on a
  Raspberry Pi, `ACC-HAT-M2POE` the HAT that gives one an M.2 slot and Power
  over Ethernet, `ACC-POE-USBC` and `ACC-POE-MUSB` the two PoE splitters. That
  one is a table, `ACC_NAMES`, keyed by file stem, because these stems are
  words rather than codes and nothing mechanical shortens them.
- a mounting plate sheet is named for which of the family's four it is, in one
  word: `TT-MP-PLATE` is the fabrication drawing, `TT-MP-FIT` the fitting
  guide, `TT-MP-DRILL` and `TT-MP-CHASSIS` the two A4 drill templates. What is
  left of these stems once `TT-MP` has said `tt-generic-mounting-plate` is the
  sheet's title (`chassis-drill-template`), which the sheet already carries in
  full, so that one is a table as well, `PLATE_NAMES`.
- a camera sheet is named for its module, `RPICAM-3`, the lens sheet
  `RPICAM-LENS`, and those that put a camera over a subject are OVER and
  one word for the subject, `RPICAM-OVER-ARTY`: a table, `RPICAM_NAMES`,
  since the stem says the subject in full.
- the camera holders, a made part filed in a directory of their own, take
  the plate's prefix, since they bolt through the plate's own fixings, and
  CAM and the lens's angle from `HOLDER_NAMES`: `TT-MP-CAM65` and
  `TT-MP-CAM120`.
- a Raspberry Pi sheet is named for its model, `RPI-5`, and a sheet that is
  no model's own takes its name from a table, `RPI_NAMES`, since its stem is
  words: the three models superimposed, `models-compared`, are `RPI-ALL`,
  and a board that is not a Raspberry Pi but takes its HATs has a stem
  saying whose it is, so `orangepi-pc.pdf` is `RPI-OPIPC`.

Nothing is numbered. A number is a position in a list, so it depends on what
else is in the list: two branches each adding a board sheet gave it the same
next number, and whichever merged second had to renumber, re-render, rebind
and revisit every reference written against the old number. A name derived
from the sheet alone is fixed when the sheet is created, and nothing else in
the set can take it away. [`tools/layout.py`](tools/layout.py) derives every
name; nothing anywhere writes one out by hand, and `tools/check_sheets.py`
reads each sheet's DRAWING NO cell back to prove it.

Each sheet is written as SVG and PDF, plus a small preview beside it.
**The PDFs are committed**, so cloning this is enough to print from: no
Inkscape, no font, no `uv`. A3 and mostly 1:1, so a print can be laid on the
board; the drill templates are A4 portrait and always 1:1.

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

### Tiny Tapeout demo boards

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-tt123-v2p2p5-v2p2p6.pdf"><img src="tinytapeout/output/previews/tt-demo-board-tt123-v2p2p5-v2p2p6.png" width="270" alt="TT-DB-TT123 DB mpw v2.2.5 / DB mpw v2.2.6"></a><br>
<b>TT-DB-TT123</b> DB mpw v2.2.5 / DB mpw v2.2.6<br>mpw-mb1 rev 2.2.5 and 2.2.6
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v1p2p1-v1p2p3.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v1p2p1-v1p2p3.png" width="270" alt="TT-DB-V121 DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c"></a><br>
<b>TT-DB-V121</b> DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c<br>tinytapeout-demo rev 1.2.1, 1.2.2 and 1.2.3
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v2p0p1-v2p1p0.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v2p0p1-v2p1p0.png" width="270" alt="TT-DB-V201 DB 06+ v2.0.1 / DB 06+ v2.1.0"></a><br>
<b>TT-DB-V201</b> DB 06+ v2.0.1 / DB 06+ v2.1.0<br>tinytapeout-demo rev 2.0.1 and 2.1.0
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v2p1p2.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v2p1p2.png" width="270" alt="TT-DB-V212 DB 06+ v2.1.2"></a><br>
<b>TT-DB-V212</b> DB 06+ v2.1.2<br>tinytapeout-demo rev 2.1.2
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v3p2.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v3p2.png" width="270" alt="TT-DB-V32 DB ETR v3.2"></a><br>
<b>TT-DB-V32</b> DB ETR v3.2<br>tinytapeout-demo rev 3.2
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v3p3.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v3p3.png" width="270" alt="TT-DB-V33 DB ETR v3.3"></a><br>
<b>TT-DB-V33</b> DB ETR v3.3<br>tinytapeout-demo rev 3.3
</td>
</tr>
</table>

### Raspberry Pi, and boards that take its HATs

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi/output/rpi3b.pdf"><img src="raspberry_pi/output/previews/rpi3b.png" width="270" alt="RPI-3B Raspberry Pi 3 Model B and B+"></a><br>
<b>RPI-3B</b> Raspberry Pi 3 Model B and B+<br>85 x 56 mm, both models
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi/output/rpi4b.pdf"><img src="raspberry_pi/output/previews/rpi4b.png" width="270" alt="RPI-4B Raspberry Pi 4 Model B"></a><br>
<b>RPI-4B</b> Raspberry Pi 4 Model B<br>85 x 56 mm
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi/output/rpi5.pdf"><img src="raspberry_pi/output/previews/rpi5.png" width="270" alt="RPI-5 Raspberry Pi 5"></a><br>
<b>RPI-5</b> Raspberry Pi 5<br>85 x 56 mm
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi/output/rpi-models-compared.pdf"><img src="raspberry_pi/output/previews/rpi-models-compared.png" width="270" alt="RPI-ALL Raspberry Pi 3B/3B+, 4B and 5 compared"></a><br>
<b>RPI-ALL</b> Raspberry Pi 3B/3B+, 4B and 5 compared<br>One 85 x 56 outline: what is shared and what moves
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi/output/orangepi-pc.pdf"><img src="raspberry_pi/output/previews/orangepi-pc.png" width="270" alt="RPI-OPIPC Xunlong Orange Pi PC"></a><br>
<b>RPI-OPIPC</b> Xunlong Orange Pi PC<br>Allwinner H3, v1.2 and v1.3, 85 x 56 mm
</td>
<td width="33%"></td>
</tr>
</table>

### Raspberry Pi camera modules

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/cm1.pdf"><img src="raspberry_pi_camera/output/previews/cm1.png" width="270" alt="RPICAM-1 Raspberry Pi Camera Module 1 (v1.3)"></a><br>
<b>RPICAM-1</b> Raspberry Pi Camera Module 1 (v1.3)<br>25 x 23.9 mm, OmniVision OV5647, hand measured
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/cm2.pdf"><img src="raspberry_pi_camera/output/previews/cm2.png" width="270" alt="RPICAM-2 Raspberry Pi Camera Module 2"></a><br>
<b>RPICAM-2</b> Raspberry Pi Camera Module 2<br>25 x 23.862 mm, Sony IMX219
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/cm3.pdf"><img src="raspberry_pi_camera/output/previews/cm3.png" width="270" alt="RPICAM-3 Raspberry Pi Camera Module 3"></a><br>
<b>RPICAM-3</b> Raspberry Pi Camera Module 3<br>25 x 23.862 mm, standard and wide, Sony IMX708
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/ov5647-lenses.pdf"><img src="raspberry_pi_camera/output/previews/ov5647-lenses.png" width="270" alt="RPICAM-LENS OV5647 Lenses and Focus"></a><br>
<b>RPICAM-LENS</b> OV5647 Lenses and Focus<br>Camera Module v1: stock, autofocus and 120 degree lenses
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/over-tt-mounting-plate.pdf"><img src="raspberry_pi_camera/output/previews/over-tt-mounting-plate.png" width="270" alt="RPICAM-OVER-PLATE Camera over the TT Mounting Plate"></a><br>
<b>RPICAM-OVER-PLATE</b> Camera over the TT Mounting Plate<br>Camera Module v1.3, stock 65 degree lens: lens face heights
</td>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/over-arty-a7.pdf"><img src="raspberry_pi_camera/output/previews/over-arty-a7.png" width="270" alt="RPICAM-OVER-ARTY Camera over the Arty A7"></a><br>
<b>RPICAM-OVER-ARTY</b> Camera over the Arty A7<br>Camera Module OV5647, 65 and 120 degree lenses
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="raspberry_pi_camera/output/over-acorn-cle-215-plus.pdf"><img src="raspberry_pi_camera/output/previews/over-acorn-cle-215-plus.png" width="270" alt="RPICAM-OVER-ACORN Camera over the Acorn CLE-215+"></a><br>
<b>RPICAM-OVER-ACORN</b> Camera over the Acorn CLE-215+<br>Camera Module v1.3, stock 65 degree lens: lens face heights
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

### FPGA development boards

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="fpga/output/arty-a7.pdf"><img src="fpga/output/previews/arty-a7.png" width="270" alt="FPGA-ARTY-A7 Digilent Arty A7"></a><br>
<b>FPGA-ARTY-A7</b> Digilent Arty A7<br>A7-35T and A7-100T
</td>
<td width="33%" valign="top" align="center">
<a href="fpga/output/ulx3s.pdf"><img src="fpga/output/previews/ulx3s.png" width="270" alt="FPGA-ULX3S ULX3S"></a><br>
<b>FPGA-ULX3S</b> ULX3S<br>v3.0.3, v3.0.7, v3.0.8 and v3.1.7
</td>
<td width="33%" valign="top" align="center">
<a href="fpga/output/pynq-z2.pdf"><img src="fpga/output/previews/pynq-z2.png" width="270" alt="FPGA-PYNQ-Z2 TUL PYNQ-Z2"></a><br>
<b>FPGA-PYNQ-Z2</b> TUL PYNQ-Z2<br>137 x 87 mm
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="fpga/output/butterstick.pdf"><img src="fpga/output/previews/butterstick.png" width="270" alt="FPGA-BUTTERSTICK ButterStick"></a><br>
<b>FPGA-BUTTERSTICK</b> ButterStick<br>r1.0
</td>
<td width="33%" valign="top" align="center">
<a href="fpga/output/icepi-zero.pdf"><img src="fpga/output/previews/icepi-zero.png" width="270" alt="FPGA-ICEPI-ZERO Icepi Zero"></a><br>
<b>FPGA-ICEPI-ZERO</b> Icepi Zero<br>v1.3, Raspberry Pi Zero form factor
</td>
<td width="33%" valign="top" align="center">
<a href="fpga/output/cynthion.pdf"><img src="fpga/output/previews/cynthion.png" width="270" alt="FPGA-CYNTHION Cynthion"></a><br>
<b>FPGA-CYNTHION</b> Cynthion<br>r1.4.0
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="fpga/output/ultra96-v2.pdf"><img src="fpga/output/previews/ultra96-v2.png" width="270" alt="FPGA-ULTRA96-V2 Avnet Ultra96-V2"></a><br>
<b>FPGA-ULTRA96-V2</b> Avnet Ultra96-V2<br>96Boards CE, 85 x 54 mm
</td>
<td width="33%" valign="top" align="center">
<a href="fpga/output/zybo-z7.pdf"><img src="fpga/output/previews/zybo-z7.png" width="270" alt="FPGA-ZYBO-Z7 Digilent Zybo Z7"></a><br>
<b>FPGA-ZYBO-Z7</b> Digilent Zybo Z7<br>Z7-10 and Z7-20
</td>
<td width="33%"></td>
</tr>
</table>

### Accessories

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="accessories/output/pmod-hat.pdf"><img src="accessories/output/previews/pmod-hat.png" width="270" alt="ACC-HAT-PMOD Digilent Pmod HAT Adapter"></a><br>
<b>ACC-HAT-PMOD</b> Digilent Pmod HAT Adapter<br>410-366, fitted to a Raspberry Pi 40-pin GPIO header
</td>
<td width="33%" valign="top" align="center">
<a href="accessories/output/poe-usbc.pdf"><img src="accessories/output/previews/poe-usbc.png" width="270" alt="ACC-POE-USBC Waveshare PoE Splitter 25 W, Type-C"></a><br>
<b>ACC-POE-USBC</b> Waveshare PoE Splitter 25 W, Type-C<br>POE-SPLITTER-25W-TYPE-C, extruded aluminium body
</td>
<td width="33%" valign="top" align="center">
<a href="accessories/output/poe-microusb.pdf"><img src="accessories/output/previews/poe-microusb.png" width="270" alt="ACC-POE-MUSB Generic PoE splitter to micro-USB"></a><br>
<b>ACC-POE-MUSB</b> Generic PoE splitter to micro-USB<br>IEEE 802.3af, 5 V output, sealed plastic body
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="accessories/output/raspmod.pdf"><img src="accessories/output/previews/raspmod.png" width="270" alt="ACC-HAT-RMOD Raspmod"></a><br>
<b>ACC-HAT-RMOD</b> Raspmod<br>TT Demoboard To Raspi rev 1.0, silkscreen v1.1: a frontplate for the demoboard's three Pmod hosts
</td>
<td width="33%" valign="top" align="center">
<a href="accessories/output/poe-m2-hat-acorn.pdf"><img src="accessories/output/previews/poe-m2-hat-acorn.png" width="270" alt="ACC-HAT-M2POE Acorn CLE-215+ in a PoE M.2 HAT+ on a Pi 5"></a><br>
<b>ACC-HAT-M2POE</b> Acorn CLE-215+ in a PoE M.2 HAT+ on a Pi 5<br>Plan envelope of the assembly; the Raspberry Pi 5 is the board drawn
</td>
<td width="33%"></td>
</tr>
</table>

### Mounting plate

<table>
<tr>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate.png" width="270" alt="TT-MP-PLATE TT Generic Mounting Plate"></a><br>
<b>TT-MP-PLATE</b> TT Generic Mounting Plate<br>Accepts every demo board revision, Pmod hosts fixed in place
</td>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-fitting-guide.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-fitting-guide.png" width="270" alt="TT-MP-FIT TT Mounting Plate Fitting Guide"></a><br>
<b>TT-MP-FIT</b> TT Mounting Plate Fitting Guide<br>Which holes each demo board revision uses
</td>
</tr>
<tr>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-drill-template.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-drill-template.png" width="270" alt="TT-MP-DRILL Drill Template: Mounting Plate"></a><br>
<b>TT-MP-DRILL</b> Drill Template: Mounting Plate<br>A4 at 1:1 - print, tape down and drill through
</td>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-chassis-drill-template.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-chassis-drill-template.png" width="270" alt="TT-MP-CHASSIS Drill Template: Chassis"></a><br>
<b>TT-MP-CHASSIS</b> Drill Template: Chassis<br>A4 at 1:1 - the six M4 fixings in the box the plate bolts to
</td>
</tr>
</table>

### Camera holder

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/camera_holder/output/tt-camera-holder-65.pdf"><img src="tinytapeout/camera_holder/output/previews/tt-camera-holder-65.png" width="270" alt="TT-MP-CAM65 Camera Holder, 65 deg Lens"></a><br>
<b>TT-MP-CAM65</b> Camera Holder, 65 deg Lens<br>Holds a Camera Module over every demo board revision
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/camera_holder/output/tt-camera-holder-120.pdf"><img src="tinytapeout/camera_holder/output/previews/tt-camera-holder-120.png" width="270" alt="TT-MP-CAM120 Camera Holder, 120 deg Lens"></a><br>
<b>TT-MP-CAM120</b> Camera Holder, 120 deg Lens<br>Holds a Camera Module over every demo board revision
</td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Printing at true size

Most sheets are 1:1, and any drill template has to be. Print with page scaling
**off** -- choose *Actual size* or *100 %*, never *Fit to page*, or from a
shell:

```sh
lp -d <queue> -o media=A4 -o print-scaling=none \
   tinytapeout/mounting_plate/output/tt-generic-mounting-plate-drill-template.pdf
```

`auto-fit` is the usual default and it shrinks A4 by around 4 %, which moves
the far corner of a hole pattern by millimetres. Every drill template carries a
printed 100 mm scale bar on each axis for exactly this reason: measure them
before drilling. See
[the mounting plate README](tinytapeout/mounting_plate/README.md).

## Pictures for the docs site

Some sheets are also drawn as pictures for
[the fpgas.online docs](https://github.com/fpgas-online/fpgas.online-docs),
in an `output/docs/` directory beside the sheet: the views on their own,
for the page about the board, and the whole sheet, for a "full drawing"
link, each as SVG and PNG and each twice -- as drafted, for the light theme,
and recoloured to read on the dark theme's ground. Both have a transparent
ground, so neither is a white page on a dark site. The views are the
sheet's own layout cut into panels and stacked: on
[`RPICAM-OVER-ACORN`](raspberry_pi_camera/output/docs/over-acorn-cle-215-plus-views-light.png)
the two elevations, the plan, the notes beside the plan, the heights table
and the legend, each a panel of its own so that the picture is narrow enough
to print its smallest text at 2.5 mm or more across an A4 page. On
[`TT-MP-PLATE`](tinytapeout/mounting_plate/output/docs/tt-generic-mounting-plate-views-light.png),
for a builder fitting a demo board and not whoever cuts the plate, they are
the plan, the legend, the table of which board revisions use each hole, and
the notes (the standoffs and fasteners, and the sources), a column to a
panel. Its whole-sheet pictures are PNG only: the whole-sheet SVG is over the
commit-size hook's 400-line limit, so the docs link
[the sheet's own PDF](tinytapeout/mounting_plate/output/tt-generic-mounting-plate.pdf)
for the zoomable full drawing. On
[`TT-MP-FIT`](tinytapeout/mounting_plate/output/docs/tt-generic-mounting-plate-fitting-guide-views-a-light.png),
the guide to fitting a board, the views are two pictures, `-views-a` (each
board revision on the plate, two to a panel, and the legend) and `-views-b`
(the placement and USB-C tables, and the notes), because the SVG of them all
is over the same limit; a third picture, `-v3`, is the two version 3 boards
(DB ETR v3.2 and v3.3) and the legend alone, for the step that puts one on
the plate. Its whole-sheet pictures are PNG only, linking
[the sheet's PDF](tinytapeout/mounting_plate/output/tt-generic-mounting-plate-fitting-guide.pdf).
On [`RPICAM-OVER-PLATE`](raspberry_pi_camera/output/docs/over-tt-mounting-plate-views-a-light.png),
where the camera goes over the plate and how high, `-views-a` is the
elevations with the lens-face dimension chain, the plan with frames A and B,
the first notes, the heights and frames tables and the legend, and `-views-b`
the notes that run on and the sources, so that neither is over two and a half
A4 pages; its whole-sheet pictures are PNG only, linking
[the sheet's PDF](raspberry_pi_camera/output/over-tt-mounting-plate.pdf).

The dark pictures' label masks are painted in Furo's page background,
`#131416`, so they belong on the page background, not inside an admonition,
a sidebar or a code block with another ground. The whole-sheet PNG is for
linking; link the SVG for zoom, or the PDF where there is no SVG.

[`tools/docs_images.py`](tools/docs_images.py) writes them as part of
`make diagrams` and says how to add a sheet;
[`tools/docs_palette.py`](tools/docs_palette.py) is what each colour becomes
in the dark, and why. `make check` holds the committed pictures against the
committed sheet, byte for byte. Text in the dark pictures keeps 7:1 against
the ground and 4.5:1 against the table fills.

## Regenerating

```sh
make fetch     # download the upstream sources into tmp/, once
make data      # re-extract the mechanical database from them
make check     # render every sheet, refresh the grids, then run the checks
```

Rebuilding is deterministic, and that is checked rather than hoped for: three
full `make clean && make diagrams` cycles produce every output file
byte-identical, so `git status` is silent after a rebuild unless a drawing
actually changed. Cairo, pypdf and ezdxf all stamp a clock, cairo, Inkscape
and pypdf their names and versions, and ezdxf two random GUIDs into what
they write;
`tools/reproducible.py` pins all of it. That is what lets a second machine
reproduce the set: Inkscape 1.4 and 1.4.3 on the same cairo draw identical
content and differed only in the version string.

That holds across days as well as within one. Each title block carries a
`VERSION` -- `git describe` of the last commit that changed anything outside an
`output/` directory -- where a render date used to be. A date meant every sheet
in the repository changed whenever anyone rebuilt on a new morning, and it
never answered the question a reader actually has, which is which version of
the data the drawing was made from. A `+` on the end means it was rendered
with uncommitted changes.

Every check that runs over the output has caught a real defect, from text
colliding on a sheet to a mounting hole no M3 screw actually fits. The
camera family's and the camera holder's own checks, which read their data
rather than the output, have caught nothing yet.
[`tools/README.md`](tools/README.md) says what each one does and what it
found.

GitHub Actions runs `make check` on every push to `main` and on every pull
request, from [`.github/workflows/check.yml`](.github/workflows/check.yml). It
runs in a Debian 13 container, not on the runner's own Ubuntu, because
`check_pdfs.py` holds each committed PDF against a fresh render of the SVG
committed beside it, byte for byte, and the committed PDFs were drawn by
Debian 13's Inkscape 1.4 on cairo 1.18.4 with DejaVu 2.37. It needs none of
the upstream sources, so it runs no `make fetch`.

## Licence

Apache 2.0; see [`LICENSE`](LICENSE). The upstream sources these drawings are
derived from keep their own licences:

<!-- One row per source, in alphabetical order, so that two pull requests
     adding different sources put their rows in different places rather than
     both rewriting one sentence. -->

| Upstream source | Its licence, or whose it is |
|---|---|
| Arty A7 drawing | Digilent's |
| ButterStick board files | Its maker's open hardware licence |
| Camera Module v1.3 hand-measured drawing | Gert van Loo's |
| Cynthion board file | Great Scott Gadgets' under the CERN-OHL-P v2 |
| Icepi Zero board files | Solderpad Hardware Licence 2.1 |
| Orange Pi PC photographs | Xunlong's, and linux-sunxi's contributors' |
| PYNQ-Z2 model | TUL's |
| Raspberry Pi camera mechanical drawings | Raspberry Pi Ltd's |
| Raspberry Pi mechanical drawings | Raspberry Pi Ltd's |
| Raspberry Pi Spy camera module diagram | Raspberry Pi Spy's |
| Tiny Tapeout board files | Apache 2.0 |
| Ultra96-V2 drawing | Avnet's, republished by Linaro with the 96Boards Consumer Edition specification |
| ULX3S board files | Its maker's open hardware licence |
