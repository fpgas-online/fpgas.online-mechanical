# The generic mounting plate

One plate that accepts **any** Tiny Tapeout demo board revision on standoffs
while holding the Pmod host headers in a single fixed place.

| | |
|---|---|
| `plate.py` | **Generated.** The plate, and where each revision sits on it |
| `design.py` | Derives the hole pattern from every revision and writes `plate.py` |
| `verify.py` | Proves the finished plate really does accept every revision |
| `export_dxf.py` | Writes the four-layer DXF cut file |
| `output/` | Four `TT-MP-PLATE-…` sheets, plus the DXF |

| Sheet | |
|-------|--|
| `TT-MP-PLATE` | Fabrication drawing: every hole and slot, tabulated |
| `TT-MP-PLATE-FITTING-GUIDE` | Fitting guide: which holes each revision uses |
| `TT-MP-PLATE-DRILL-TEMPLATE` | Drill template for the plate, A4 at 1:1 |
| `TT-MP-PLATE-CHASSIS-DRILL-TEMPLATE` | Drill template for the chassis it bolts to, A4 at 1:1 |

Every name here says PLATE because every file stem does: the drawing name is
the file stem in capitals behind the family prefix, and `TT-MP` accounts for
the `tt-generic-mounting` all four begin with, no more. Stopping the prefix
one word later would have left the plate's own drawing called `TT-MP`, which
reads as the family rather than as one sheet of it.

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="50%" valign="top" align="center">
<a href="output/tt-generic-mounting-plate.pdf"><img src="output/previews/tt-generic-mounting-plate.png" width="270" alt="TT-MP TT Generic Mounting Plate"></a><br>
<b>TT-MP</b> TT Generic Mounting Plate<br>Accepts every demo board revision, Pmod hosts fixed in place
</td>
<td width="50%" valign="top" align="center">
<a href="output/tt-generic-mounting-plate-fitting-guide.pdf"><img src="output/previews/tt-generic-mounting-plate-fitting-guide.png" width="270" alt="TT-MP-FITTING-GUIDE TT Mounting Plate Fitting Guide"></a><br>
<b>TT-MP-FITTING-GUIDE</b> TT Mounting Plate Fitting Guide<br>Which holes each demo board revision uses
</td>
</tr>
<tr>
<td width="50%" valign="top" align="center">
<a href="output/tt-generic-mounting-plate-drill-template.pdf"><img src="output/previews/tt-generic-mounting-plate-drill-template.png" width="270" alt="TT-MP-DRILL-TEMPLATE Drill Template: Mounting Plate"></a><br>
<b>TT-MP-DRILL-TEMPLATE</b> Drill Template: Mounting Plate<br>A4 at 1:1 - print, tape down and drill through
</td>
<td width="50%" valign="top" align="center">
<a href="output/tt-generic-mounting-plate-chassis-drill-template.pdf"><img src="output/previews/tt-generic-mounting-plate-chassis-drill-template.png" width="270" alt="TT-MP-CHASSIS-DRILL-TEMPLATE Drill Template: Chassis"></a><br>
<b>TT-MP-CHASSIS-DRILL-TEMPLATE</b> Drill Template: Chassis<br>A4 at 1:1 - the six M4 fixings in the box the plate bolts to
</td>
</tr>
</table>

<!-- sheets:end -->

## Why one plate works

Every revision, `DB mpw v2.2.6` through `DB ETR v3.3`, spaces its Pmod host
headers 22.86 mm apart, because the Digilent Pmod Interface Specification
mandates that pitch for host ports on a board edge.

Nothing else about the boards stayed still. The outline went 104.5 x 81 to
99.5 x 78 to 85 x 85, the mounting hole pattern changed three times and
dropped from four holes to two, and the distance from the front edge to the
Pmod pin field moved from 4.465 mm to 3.23 mm.

That one invariant is enough. Place each revision so its Pmod hosts land on a
common 22.86 mm grid and its mounting holes fall where they fall. Ten holes,
two slots and six plate fixings cover all five distinct geometries on a
135 x 101 mm plate. Where two revisions want a fastener too close together to
drill separately -- 0.613 mm apart in one case -- they share a slot rather
than a hole that neither screw fits.

`verify.py` proves this from the data rather than from the drawing: every
revision's fasteners pass an M3, every Pmod host lands exactly on its plate
position, no board overhangs, and the connector faces clear the front edge.

## Printing the drill templates

`TT-MP-PLATE-DRILL-TEMPLATE` and `TT-MP-PLATE-CHASSIS-DRILL-TEMPLATE` are
not drawings to read, they are gauges to use:
print, tape to the work, punch every cross, drill through. That only works if
the page leaves the printer at exactly 1:1, and no print dialog does that by
default. A CUPS queue will tell you what it intends:

```console
$ lpoptions -p WellandColor -l | grep print-scaling
print-scaling/Print Scaling: auto *auto-fit fill fit none
```

`auto-fit` is the default, and it shrinks A4 to whatever the hardware can
actually reach. The same queue reports a 4.32 mm border on all four edges, so
auto-fit scales the page by `min(201.36/210, 288.36/297)` = 0.9588 and moves
the far corner of the hole pattern by 5.6 mm. Print with scaling off:

```sh
lp -d <queue> -o media=A4 -o print-scaling=none \
   tinytapeout/mounting_plate/output/tt-generic-mounting-plate-drill-template.pdf
```

From a viewer, choose **Actual size** or **100 %**, never Fit to page or
Shrink to fit.

Then measure the two printed scale bars before drilling anything. Each is
100.0 mm overall. There are two because a laser fuser shrinks paper along the
feed direction, which scales the axes by different amounts that a single bar
cannot see. If either is short the print scaled: reprint, rather than
compensating at the drill.

Everything drilled is printed in black and nothing else is. A colour laser
registers its planes to a few tenths of a millimetre, more than the clearance
being worked to, so a hole circle and its punch cross stay in the one plane
that cannot misregister against itself. The pale washes are board outlines and
the grey dashed boxes are Pmod connector bodies: clearance, not features.

`tools/check_drill_template.py` measures the finished PDFs back and proves
every hole lands where `plate.py` puts it.

## Coordinates

Origin at the plate's lower-left corner, X right, Y up, seen from the side the
board mounts on. `PLACEMENTS` in `plate.py` gives the offset from each board's
own frame to the plate frame. Board holes and slots are 3.4 mm, a close
clearance fit on M3; plate fixings are 4.3 mm, a clearance fit on M4.
