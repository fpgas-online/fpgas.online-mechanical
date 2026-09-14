# FPGA development boards

Four FPGA boards that turn up in the same racks as the Tiny Tapeout demo
boards, each drawn on its own sheet with its Pmod hosts, USB ports, Ethernet
jack and user LEDs marked.

| | |
|---|---|
| `boards.py` | **Generated.** Arty A7, ULX3S, PYNQ-Z2 and ButterStick |
| `extract.py` | Reads each board's own published source and writes `boards.py` |
| `output/` | `FPGA-01` to `FPGA-04`, as SVG and PDF, and `fpga-sheets.pdf`, the four bound into one document |

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
<a href="output/arty-a7.pdf"><img src="output/previews/arty-a7.png" width="270" alt="FPGA-01 Digilent Arty A7"></a><br>
<b>FPGA-01</b> Digilent Arty A7<br>A7-35T and A7-100T
</td>
<td width="33%" valign="top" align="center">
<a href="output/ulx3s.pdf"><img src="output/previews/ulx3s.png" width="270" alt="FPGA-02 ULX3S"></a><br>
<b>FPGA-02</b> ULX3S<br>v3.0.3, v3.0.7, v3.0.8 and v3.1.7
</td>
<td width="33%" valign="top" align="center">
<a href="output/pynq-z2.pdf"><img src="output/previews/pynq-z2.png" width="270" alt="FPGA-03 TUL PYNQ-Z2"></a><br>
<b>FPGA-03</b> TUL PYNQ-Z2<br>137 x 87 mm
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/butterstick.pdf"><img src="output/previews/butterstick.png" width="270" alt="FPGA-04 ButterStick"></a><br>
<b>FPGA-04</b> ButterStick<br>r1.0
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

The PYNQ-Z1 was looked at and left out: Digilent's 3D model of it has no
mounting holes and its outline disagrees with their own stated size.

Feature numbers are fixed across the family, so a reader flipping between
sheets finds the Ethernet jack at 3 whether the board has one or not. Rows
of LEDs are one feature each, with the count and pitch in the label; eight
balloons on a 20 mm row would say nothing a plate designer needs.

Pin 1 of every Pmod host follows the Pmod convention, top right looking into
the socket, fed by the row of holes farther from the board edge. The Tiny
Tapeout board files number theirs the same way and the PYNQ-Z2 manual draws
it. Neither Digilent's DXF nor TUL's model names a pin.
