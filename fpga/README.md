# FPGA development boards

Seven FPGA boards that turn up in the same racks as the Tiny Tapeout demo
boards, each drawn on its own sheet with its Pmod hosts, USB ports, Ethernet
jack and user LEDs marked.

| | |
|---|---|
| `boards.py` | **Generated.** Arty A7, ULX3S, PYNQ-Z2, ButterStick, Icepi Zero, Cynthion and Zybo Z7 |
| `extract.py` | Reads each board's own published source and writes `boards.py` |
| `output/` | `FPGA-ARTY-A7`, `FPGA-ULX3S`, `FPGA-PYNQ-Z2`, `FPGA-BUTTERSTICK`, `FPGA-ICEPI-ZERO`, `FPGA-CYNTHION` and `FPGA-ZYBO-Z7`, as SVG and PDF, and `fpga-sheets.pdf`, the seven bound into one document |

```sh
tools/fetch_fpga.sh                                   # once, needs network
uv run --no-project --with ezdxf --with pdfplumber --with cadquery \
    python fpga/extract.py
```

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/arty-a7.pdf"><img src="output/previews/arty-a7.png" width="270" alt="FPGA-ARTY-A7 Digilent Arty A7"></a><br>
<b>FPGA-ARTY-A7</b> Digilent Arty A7<br>A7-35T and A7-100T
</td>
<td width="33%" valign="top" align="center">
<a href="output/ulx3s.pdf"><img src="output/previews/ulx3s.png" width="270" alt="FPGA-ULX3S ULX3S"></a><br>
<b>FPGA-ULX3S</b> ULX3S<br>v3.0.3, v3.0.7, v3.0.8 and v3.1.7
</td>
<td width="33%" valign="top" align="center">
<a href="output/pynq-z2.pdf"><img src="output/previews/pynq-z2.png" width="270" alt="FPGA-PYNQ-Z2 TUL PYNQ-Z2"></a><br>
<b>FPGA-PYNQ-Z2</b> TUL PYNQ-Z2<br>137 x 87 mm
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/butterstick.pdf"><img src="output/previews/butterstick.png" width="270" alt="FPGA-BUTTERSTICK ButterStick"></a><br>
<b>FPGA-BUTTERSTICK</b> ButterStick<br>r1.0
</td>
<td width="33%" valign="top" align="center">
<a href="output/icepi-zero.pdf"><img src="output/previews/icepi-zero.png" width="270" alt="FPGA-ICEPI-ZERO Icepi Zero"></a><br>
<b>FPGA-ICEPI-ZERO</b> Icepi Zero<br>v1.3, Raspberry Pi Zero form factor
</td>
<td width="33%" valign="top" align="center">
<a href="output/cynthion.pdf"><img src="output/previews/cynthion.png" width="270" alt="FPGA-CYNTHION Cynthion"></a><br>
<b>FPGA-CYNTHION</b> Cynthion<br>r1.4.0
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/zybo-z7.pdf"><img src="output/previews/zybo-z7.png" width="270" alt="FPGA-ZYBO-Z7 Digilent Zybo Z7"></a><br>
<b>FPGA-ZYBO-Z7</b> Digilent Zybo Z7<br>Z7-10 and Z7-20
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

Each maker publishes something different, so each board has its own reader,
and the sheet says which it was.

- **Arty A7**: Digilent's mechanical drawing, a DXF with the outline, every
  through-hole pad and the connector slots, plus the PDF plot beside it,
  which is where the component bodies are. The PDF's plot scale is recovered
  from the outline, per axis, and the two sources are checked against each
  other wherever they overlap: the RJ45 body has to sit on the DXF's locating
  pegs, the USB shell on its slots, each Pmod body on its pin field. The
  Arty **has no mounting holes**; it stands on rubber feet, which Digilent
  staff confirmed on their forum. The drawing puts the Pmod hosts on a
  22.80 mm pitch with their pin rows 2.50 mm apart, a metric-grid drawing of
  a 0.9 in, 0.1 in part; both are within the sheet's general tolerance and
  the sheet says so.
- **ULX3S**: the KiCad board file, read at all four tags the maker's manual
  lists as sold (v3.0.3, v3.0.7, v3.0.8, v3.1.7). All four are required to
  agree on everything drawn before one sheet may cover them. No Pmod host
  and no Ethernet: its two right-angle 2x20 GPIO sockets are drawn instead.
- **PYNQ-Z2**: TUL's STEP assembly, the only machine-readable thing they
  publish. The board slab, its four holes, the Pmod pin holes and the named
  connector solids are read out of the solids. The user LEDs are not in the
  model, so they are not drawn, and the sheet says where they are in words.
- **ButterStick**: the KiCad board file at the r1.0a release that was sold.
  No Pmod: three SYZYGY ports, each bringing two plated standoff holes that
  the maker's own acrylic plate bolts through, so those six join the two M3
  holes in the schedule.
- **Icepi Zero**: the KiCad board file at the `v1.3` tag, whose commit is
  "Final mass production files" -- the revision made in quantity and sold,
  and the only one the repository tags. It is read a second time at a later
  commit of that same revision, where it has been re-saved in KiCad 10 and
  **re-annotated**: two of the three USB-C receptacles swapped designators
  and three of the five user LEDs were renumbered, and nothing moved. Every
  position is required to agree between the two, and the sheet carries the
  designators the sold boards were fabbed with and says the later file
  disagrees.
  Nothing is looked up by designator for that reason: the programming port
  is the receptacle sharing the FT231X's data pair, a user LED is one a
  resistor drives from `/LED0` to `/LED4`, and the rest are found by
  footprint. No Pmod host and no Ethernet. The board is the Raspberry Pi
  Zero outline and hole pattern, which the sheet states and the extractor
  checks against the figures on Raspberry Pi's own Zero drawing: same
  65 x 30 and same 58 x 23 hole pattern 3.5 mm in from all four edges,
  drilled 2.70, the bottom of the Pi Zero's 2.75 +/-0.05 band, and cornered
  R3.50 rather than R3.00. The 2x20 GPIO
  header is **not fitted** -- it is absent from the production BOM -- and
  the position's pins are checked to sit on the Raspberry Pi arrangement
  before the note says so.
- **Cynthion**: the KiCad board file at `r1.4.0`, whose release notes call it
  the initial production release; it is the newest release, the tip of the
  repository, and no commit since has touched the board file. Great Scott
  Gadgets publish it under the CERN-OHL-P v2 and publish no mechanical
  drawing, so every figure on the sheet is read from that file. A 56 x 56 mm
  square on R3 with a recess in its top edge, four M2 holes, two Pmod hosts
  on the front edge, a 30-way mezzanine receptacle in the middle of the
  component side, and **four USB ports**. The board file numbers its own Pmod
  pads, so pin 1 is checked against the Pmod convention rather than asserted
  from it; the two agree. Its hosts are right-angle sockets, so the housings
  hang off the front edge and a peripheral plugs in level with the board --
  which is also why this is the first sheet to state its own assembled
  envelope rather than take the computed one.
- **Zybo Z7**: the same mechanical drawing the Arty A7 has, a DXF and a PDF
  plot, published the day after it and read by the same code. It has no
  keep-out layer, so the board edge is the one closed rectangle of whole
  segments on `Mechanical1` that every plated hole sits inside; and its Pmod
  sockets are plotted with a keying notch in both long edges, so they close
  no rectangle and are read as runs of segments instead. Nothing in the
  drawing is named, so which outline is which comes from Digilent's STEP
  assembly, whose every solid carries its reference designator and which is
  placed in the drawing's own frame. **Six Pmod hosts**: JA, the XADC port,
  on the right edge, JF, the MIO port, on the left, and JB to JE along the
  lower edge on a 23.00 mm pitch -- not the specification's 22.86. The
  drawing is of the fully fitted board, which is the Zybo Z7-20; the Z7-10
  leaves JB and one of the two tri-colour LEDs off the same PCB.

The PYNQ-Z1 was looked at and left out: Digilent's 3D model of it has no
mounting holes and its outline disagrees with their own stated size.

Feature numbers are fixed across the family, so a reader flipping between
sheets finds the Ethernet jack at 3 whether the board has one or not. Rows
of LEDs are one feature each, with the count and pitch in the label; eight
balloons on a 20 mm row would say nothing a plate designer needs. The Icepi
Zero's two FPGA USB-C ports are one row for the same reason: identical
receptacles with 1.86 mm of board between them, the count and the 12.50 mm
pitch in the label. Numbers 6 to 8 are the expansion connectors, whichever
connectors a board puts on its edges: the ULX3S's two GPIO sockets,
ButterStick's three SYZYGY ports, and on the Icepi Zero its GPIO header,
its video connector and its card socket, so that nothing a cable or a card
goes into is left off the drawing.

A number, once issued, keeps its meaning, so a board that wants a slot the
family has not got gets a new number at the end rather than a renumbering.
Cynthion is the first board here with more than two USB ports and the first
with a second LED row that is not the user row, so 9, 10 and 11 were added
for the third and fourth USB ports and the status LEDs. That is why its four
USB ports read 1, 2, 9, 10 and not 1 to 4, and why the other five sheets'
schedules each gained three "not on this board" rows. Its mezzanine
receptacle takes slot 6, the family's first expansion connector, which is the
one slot it did fit; a note says it is a board-to-board socket rather than
the edge port that slot holds on the other sheets.

Pin 1 of every Pmod host follows the Pmod convention, top right looking into
the socket, fed by the row of holes farther from the board edge. The Tiny
Tapeout board files number theirs the same way and the PYNQ-Z2 manual draws
it. Neither Digilent's DXF nor TUL's model names a pin. On the Zybo Z7 the
rule can be checked against the board itself: Digilent's top view has 3V3
and GND silkscreened at the end of every host farthest from the pin the rule
picks, which is where pins 5 and 6 belong, on all six hosts and on all three
edges they sit on.
