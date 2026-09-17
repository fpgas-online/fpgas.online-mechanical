# The Arty A7 Ethernet light pipe

The Arty A7's Ethernet LEDs are inside its RJ45 and face **forwards**, out of
two windows in the jack's front face. Looking down at the board -- which is
how anyone reads a board on a bench, and the only way a camera over a rack
can read one -- there is nothing to see. This is a small printed part that
clips over the front of that jack and carries two catalogue light pipes from
those windows up to a face that does point at you, while leaving the cable
opening and the latch alone.

| | |
|---|---|
| `adapter.py` | **Generated.** The jack, the pipe, and every dimension of the part |
| `design.py` | Reads the three published drawings and writes `adapter.py` |
| `verify.py` | Proves the cable still fits, the pipes see the windows, and the part fits the jack |
| `export_step.py` | Writes the STEP solid to print from |
| `output/` | `FPGA-LP-ARTY`, as SVG and PDF, and the STEP |

```sh
tools/fetch_fpga.sh                                    # once, needs network
uv run --no-project --with ezdxf --with pdfplumber \
    python fpga/light_pipe/design.py
uv run --no-project python fpga/light_pipe/verify.py
uv run --no-project --with cadquery python fpga/light_pipe/export_step.py
```

## The sheet

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/arty-ethernet-light-pipe.pdf"><img src="output/previews/arty-ethernet-light-pipe.png" width="270" alt="FPGA-LP-ARTY Arty A7 Ethernet Light Pipe"></a><br>
<b>FPGA-LP-ARTY</b> Arty A7 Ethernet Light Pipe<br>Clips over J9 and carries its two LEDs to a face you can see from above
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

Three drawings and one chain between them, all machine-read by `design.py`:

- **Digilent's Arty A7 schematic** names the jack. Sheet 8, ETHERNET, carries
  `J9` and the part number `08B0-1X1T-36-F` beside it. Everything below hangs
  off that one string, so it is read out of the PDF rather than remembered.
- **Bel's drawing of that MagJack** is where the LED windows are. Its front
  view is vector art, so once the plot scale is recovered -- per axis, from
  the `0.642 [16.31]` and `0.531 [13.49]` the drawing itself dimensions, the
  two axes agreeing to 0.58 % -- the windows, the plug aperture, the latch
  keyway and the EMI springs can be measured off it. That is the same bargain
  [`fpga/extract.py`](../extract.py) strikes with Digilent's Arty plot:
  identification by hand, measurement by machine. Figures read that way are
  good to about ±0.20 mm and are marked MEASURED on the sheet; figures Bel
  dimensions carry Bel's own ±0.254 mm (`.XXX ±0.010 in`) and are marked
  STATED.
- **Digilent's Arty A7 DXF** puts that jack on the board. Its two Ø1.575 mm
  pads are the jack's board locks; they are 16.104 mm apart against Bel's
  `0.635 [16.13]`, which is what says the two drawings are of the same part,
  and their midpoint is the jack's centre plane, `y = 44.000`. Bel's
  `0.305 [7.75]` runs from those locks forward to the front face -- both ends
  of it are in the side view's vector geometry, the face line the
  `1.005 [25.53]` also starts from and the peg's own extension line 7.786 mm
  behind it -- so the face is at `x = -0.101`, a tenth of a millimetre proud
  of the board's own edge.

  **Digilent's plot of the same jack disagrees**, and that is worth knowing
  rather than averaging away. Read as the body plus what stands in front of
  it, the plot puts that face 0.63 mm further back. The plot's own bodies are
  good to about ±0.3, so 0.63 means its rectangle is not the jack's envelope:
  a courtyard, or a footprint drawn with clearance. The sheet uses the DXF
  reading and carries ±0.63 on it, and that uncertainty is on **where the
  part sits on the board**, not on the part: the adapter butts against the
  front face, wherever the front face is.
- **Bivar's PLP2 drawing** is the bore. The pipe is a Ø2.8 mm rod on Ø3.1 mm
  press-fit ribs with a Ø3.3 x 0.8 mm domed flange, for a Ø2.92 mm hole in a
  1.19 to 2.36 mm panel, and the bore is built from exactly those figures.

## Why it is shaped like this

The light leaves the window horizontally and has to arrive vertically, and
there is almost nowhere to do the turn. In front of the jack is the cable; in
the middle of the front face is the latch; the window itself is 2.88 x 2.57 mm
and sits 0.235 mm inside the shield's edge with its lower edge **on** the top
edge of the opening the plug goes through. And the front of this jack is not
one plane: Bel's side view draws the face over z 0.51..10.46 and
13.20..13.49 and, between those, the window band standing 0.64 mm in front of
it. So the pipe tips are set from the window rather than from the face, and
at maximum material, because the `0.025` that dimensions it carries Bel's
±0.254: the tip stands 0.30 mm clear of a window as proud as it is allowed
to be, and 0.55 mm clear of one as drawn. So:

- **A bore at 45 degrees, not a bend.** A flexible light pipe looks like the
  obvious answer until you draw it: turning light through a right angle with
  a bend means a quarter circle, and a quarter circle stands as far in front
  of the jack as its own bend radius, which for any pipe thick enough to
  carry this light is several times the 3.5 mm a rigid pipe in a 45 degree
  bore needs. The tip of that rigid pipe is a circle lying at 45 degrees to
  the window, so what the window sees of it is an ellipse 2.80 mm across and
  1.98 mm high -- inside the window on both axes, which is what `verify.py`
  checks.
- **The lens looks up and forward, not straight up.** The alternative is a
  vertical bore with a 45 degree mitre cut on the pipe's tip, which is what a
  right-angle light pipe is. It would aim the lens straight up, but the mitre
  is a hand operation on a Ø2.8 mm rod whose polish decides whether it works
  at all. A catalogue pipe pressed into a printed hole has no such step.
- **Two cheeks with an open channel between them.** The latch keyway is
  ±3.32 mm wide and the bores are at ±6.48, so the part is two blocks either
  side of an 8.16 mm channel that is open to the sky. Nothing bridges that
  channel forward of the jack's face, so a finger still reaches the latch.
- **Everything in front of the jack is above the plug.** The cheeks' undersides
  and both pipe tips stand 0.45 mm above the top edge of the plug aperture.
  A plug and a plain boot pass under them; a snagless boot standing proud of
  the plug's own top face within 7 mm of the jack will not.
- **The jack's own EMI springs hold it on.** They stand 1.40 ±0.51 mm proud of
  a 16.31 ±0.254 mm shield, and those two tolerances leave 0.64 mm to split
  between clearing the shield and deflecting the spring. The skirts sit at
  ±8.59: 0.31 mm clear of the shield at maximum material, and the spring
  deflected by 0.33 mm at minimum material, 1.60 at maximum and 0.59 at the
  figures Bel actually draws. The first version of this split it 0.53/0.11
  and 0.11 mm of leaf-spring deflection is no grip at all, which matters
  because nothing else fixes the part: no screw, no glue, and nothing that
  has to be got at once the board is in a box. It has still never been tried
  on a real jack.

## Printing it

Print it **upside down, on its top face**. Everything else then grows from
the build plate, the two 45 degree facets and the two bores are the only
overhangs and both are at 45 degrees, and nothing needs support. Any opaque
filament does; it is 0.80 cm³, about a gram.

The one dimension a printer will get wrong is the bore. It is Ø2.92 mm for
the first 2.00 mm from the facet, which is Bivar's own recommended mounting
hole over their own panel thickness, and a printer that comes out undersize
will not take the pipe: ream it, or print a scrap of the cheek first and try
a pipe in it.

## Coordinates

Origin on the jack's centre plane, in its front face, at the board's top
surface. X runs back into the board, Y across it and Z up; the part is
symmetric about Y = 0, so `adapter.py` gives one cheek, one bore, one pocket,
one roof slot and one skirt, and the other of each is its mirror image.
`JACK_FACE_X` and `JACK_CENTRE_Y` put that frame on the Arty A7 of
[`fpga/boards.py`](../boards.py): the part occupies x -6.53 to 9.90 and
y 34.01 to 53.99 in board coordinates, overhanging the board's front edge by
6.53 mm -- with the ±0.63 above on all of that, because it is the jack's own
position on the board that is known that well.
