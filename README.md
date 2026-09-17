# Mechanical diagrams

2D orthographic (blueprint style) mechanical drawings of the hardware
[fpgas.online](https://fpgas.online) is built from: the boards, the adapters
and the accessories that end up in the same rack, plus the plates and
templates made to mount them.

The drawings are for designing the things the boards mount into -- plates,
brackets, enclosures, rack shelves. Every dimension is traceable to an
official source, and each sheet lists its sources.

Adding hardware is the normal case. Each family lives in its own directory
with its data, the extractor that produces it and the sheets rendered from
it, so a new board is a new directory and does not disturb the others.

## What is here

| Directory | Sheets | |
|-----------|--------|--|
| [`tinytapeout/`](tinytapeout/README.md) | `TT-DB-*` | Tiny Tapeout demo boards, one sheet per distinct geometry |
| [`tinytapeout/mounting_plate/`](tinytapeout/mounting_plate/README.md) | `TT-MP`, `TT-MP-*` | The plate every demo board revision bolts onto, and its drill templates |
| [`raspberry_pi/`](raspberry_pi/README.md) | `RPI-*` | Pi 3B/3B+, 4B and 5, each with a Digilent Pmod HAT Adapter overlaid |
| [`fpga/`](fpga/README.md) | `FPGA-*` | Digilent Arty A7, ULX3S, TUL PYNQ-Z2 and ButterStick, with Pmod, USB, Ethernet and LEDs marked |
| [`accessories/`](accessories/README.md) | `ACC-*` | Pmod HAT Adapter, two PoE splitters as envelope drawings, and the Raspmod, with [a comparison of the two Pi-to-Pmod adapters](accessories/raspmod-vs-pmod-hat.md) |
| [`tools/`](tools/README.md) | -- | The [drafting library](tools/drafting/README.md), the generator and the checks |

## What a sheet is called

A sheet's drawing name is its own file, in capitals, behind its family's
prefix: `fpga/output/arty-a7.pdf` is **`FPGA-ARTY-A7`** and
`tinytapeout/output/tt-demo-board-v3p3.pdf` is **`TT-DB-V3P3`**. The part of
the stem the prefix already says is dropped, so `rpi5.pdf` is `RPI-5` and the
mounting plate's own fabrication drawing, having nothing left after the strip,
is `TT-MP` -- the family's principal sheet, with `TT-MP-FITTING-GUIDE` and the
two drill templates hanging off it.

Nothing is numbered. A number is a position in a list, so it depends on what
else is in the list: two branches each adding a board sheet gave it the same
next number, and whichever merged second had to renumber, re-render, rebind
and revisit every reference written against the old number. A name derived
from the sheet alone is fixed when the sheet is created, and no two sheets can
take the same one because no two sheets can share a file.
[`tools/layout.py`](tools/README.md) derives every name; nothing anywhere
writes one out by hand.

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
<a href="tinytapeout/output/tt-demo-board-tt123-v2p2p5-tt123-v2p2p6.pdf"><img src="tinytapeout/output/previews/tt-demo-board-tt123-v2p2p5-tt123-v2p2p6.png" width="270" alt="TT-DB-TT123-V2P2P5-TT123-V2P2P6 DB mpw v2.2.5 / DB mpw v2.2.6"></a><br>
<b>TT-DB-TT123-V2P2P5-TT123-V2P2P6</b> DB mpw v2.2.5 / DB mpw v2.2.6<br>mpw-mb1 rev 2.2.5 and 2.2.6
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v1p2p1-v1p2p2-v1p2p3.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v1p2p1-v1p2p2-v1p2p3.png" width="270" alt="TT-DB-V1P2P1-V1P2P2-V1P2P3 DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c"></a><br>
<b>TT-DB-V1P2P1-V1P2P2-V1P2P3</b> DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c<br>tinytapeout-demo rev 1.2.1, 1.2.2 and 1.2.3
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v2p0p1-v2p1p0.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v2p0p1-v2p1p0.png" width="270" alt="TT-DB-V2P0P1-V2P1P0 DB 06+ v2.0.1 / DB 06+ v2.1.0"></a><br>
<b>TT-DB-V2P0P1-V2P1P0</b> DB 06+ v2.0.1 / DB 06+ v2.1.0<br>tinytapeout-demo rev 2.0.1 and 2.1.0
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v2p1p2.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v2p1p2.png" width="270" alt="TT-DB-V2P1P2 DB 06+ v2.1.2"></a><br>
<b>TT-DB-V2P1P2</b> DB 06+ v2.1.2<br>tinytapeout-demo rev 2.1.2
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v3p2.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v3p2.png" width="270" alt="TT-DB-V3P2 DB ETR v3.2"></a><br>
<b>TT-DB-V3P2</b> DB ETR v3.2<br>tinytapeout-demo rev 3.2
</td>
<td width="33%" valign="top" align="center">
<a href="tinytapeout/output/tt-demo-board-v3p3.pdf"><img src="tinytapeout/output/previews/tt-demo-board-v3p3.png" width="270" alt="TT-DB-V3P3 DB ETR v3.3"></a><br>
<b>TT-DB-V3P3</b> DB ETR v3.3<br>tinytapeout-demo rev 3.3
</td>
</tr>
</table>

### Raspberry Pi, with a Digilent Pmod HAT Adapter overlaid

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
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

### Accessories

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="accessories/output/digilent-pmod-hat-adapter.pdf"><img src="accessories/output/previews/digilent-pmod-hat-adapter.png" width="270" alt="ACC-DIGILENT-PMOD-HAT-ADAPTER Digilent Pmod HAT Adapter"></a><br>
<b>ACC-DIGILENT-PMOD-HAT-ADAPTER</b> Digilent Pmod HAT Adapter<br>410-366, fitted to a Raspberry Pi 40-pin GPIO header
</td>
<td width="33%" valign="top" align="center">
<a href="accessories/output/waveshare-poe-usbc.pdf"><img src="accessories/output/previews/waveshare-poe-usbc.png" width="270" alt="ACC-WAVESHARE-POE-USBC Waveshare PoE Splitter 25 W, Type-C"></a><br>
<b>ACC-WAVESHARE-POE-USBC</b> Waveshare PoE Splitter 25 W, Type-C<br>POE-SPLITTER-25W-TYPE-C, extruded aluminium body
</td>
<td width="33%" valign="top" align="center">
<a href="accessories/output/generic-poe-microusb.pdf"><img src="accessories/output/previews/generic-poe-microusb.png" width="270" alt="ACC-GENERIC-POE-MICROUSB Generic PoE splitter to micro-USB"></a><br>
<b>ACC-GENERIC-POE-MICROUSB</b> Generic PoE splitter to micro-USB<br>IEEE 802.3af, 5 V output, sealed plastic body
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="accessories/output/raspmod.pdf"><img src="accessories/output/previews/raspmod.png" width="270" alt="ACC-RASPMOD Raspmod"></a><br>
<b>ACC-RASPMOD</b> Raspmod<br>TT Demoboard To Raspi rev 1.0, silkscreen v1.1: a frontplate for the demoboard's three Pmod hosts
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

### Mounting plate

<table>
<tr>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate.png" width="270" alt="TT-MP TT Generic Mounting Plate"></a><br>
<b>TT-MP</b> TT Generic Mounting Plate<br>Accepts every demo board revision, Pmod hosts fixed in place
</td>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-fitting-guide.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-fitting-guide.png" width="270" alt="TT-MP-FITTING-GUIDE TT Mounting Plate Fitting Guide"></a><br>
<b>TT-MP-FITTING-GUIDE</b> TT Mounting Plate Fitting Guide<br>Which holes each demo board revision uses
</td>
</tr>
<tr>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-drill-template.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-drill-template.png" width="270" alt="TT-MP-DRILL-TEMPLATE Drill Template: Mounting Plate"></a><br>
<b>TT-MP-DRILL-TEMPLATE</b> Drill Template: Mounting Plate<br>A4 at 1:1 - print, tape down and drill through
</td>
<td width="50%" valign="top" align="center">
<a href="tinytapeout/mounting_plate/output/tt-generic-mounting-plate-chassis-drill-template.pdf"><img src="tinytapeout/mounting_plate/output/previews/tt-generic-mounting-plate-chassis-drill-template.png" width="270" alt="TT-MP-CHASSIS-DRILL-TEMPLATE Drill Template: Chassis"></a><br>
<b>TT-MP-CHASSIS-DRILL-TEMPLATE</b> Drill Template: Chassis<br>A4 at 1:1 - the six M4 fixings in the box the plate bolts to
</td>
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

## Regenerating

```sh
make fetch     # download the upstream sources into tmp/, once
make data      # re-extract the mechanical database from them
make check     # render every sheet, refresh the grids, then run the checks
```

Rebuilding is deterministic, and that is checked rather than hoped for: three
full `make clean && make diagrams` cycles produce all 67 output files
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

Six checks run over the output and each has caught a real defect, from text
colliding on a sheet to a mounting hole no M3 screw actually fits.
[`tools/README.md`](tools/README.md) says what each one does and what it
found.

## Licence

Apache 2.0; see [`LICENSE`](LICENSE). The upstream sources these drawings are
derived from keep their own licences: the Tiny Tapeout board files are Apache
2.0, the Raspberry Pi mechanical drawings are Raspberry Pi Ltd's, the Arty A7
drawing is Digilent's, the PYNQ-Z2 model is TUL's, and the ULX3S and
ButterStick board files carry their makers' open hardware licences.
