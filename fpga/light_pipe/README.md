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
- **Digilent's Arty A7 DXF and plot** put that jack on the board. The DXF's
  two Ø1.575 mm pads are the jack's board locks; they are 16.104 mm apart
  against Bel's `0.635 [16.13]`, which is what says the two drawings are of
  the same part, and their midpoint is the jack's centre plane, `y = 44.000`.
  The front face takes three readings that agree to 0.14 mm: the plot draws
  the jack over its EMI springs, so the face is Bel's 0.64 mm spring wrap
  behind the plot's front edge (0.400) and Bel's 25.53 mm body in front of
  its back edge (0.527), and Bel's `0.305 [7.75]` from the board locks,
  which runs to those same spring tips rather than to the face, gives 0.539.
  The mean, `x = 0.463`, is what the sheet uses. Reading that 7.75 as if it
  ran to the front face instead puts the jack 0.6 mm forward and fails both
  of the plot's readings, which is how the misreading was caught.
- **Bivar's PLP2 drawing** is the bore. The pipe is a Ø2.8 mm rod on Ø3.1 mm
  press-fit ribs with a Ø3.3 x 0.8 mm domed flange, for a Ø2.92 mm hole in a
  1.19 to 2.36 mm panel, and the bore is built from exactly those figures.

## Why it is shaped like this

The light leaves the window horizontally and has to arrive vertically, and
there is almost nowhere to do the turn. In front of the jack is the cable; in
the middle of the front face is the latch; the window itself is 2.88 x 2.57 mm
and sits 0.28 mm inside the shield's edge with its lower edge **on** the top
edge of the opening the plug goes through. So:

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
  the plug's own top face within 6 mm of the jack will not.
- **The jack's own EMI springs hold it on.** They stand 1.40 ±0.51 mm proud of
  a 16.31 ±0.254 mm shield, and the skirts sit at ±8.81, so the spring is
  deflected by between 0.12 and 1.39 mm per side across the whole of both
  tolerance bands while the shield itself never touches. Nothing else fixes
  the part: no screw, no glue, and nothing that has to be got at once the
  board is in a box.

## Printing it

Print it **upside down, on its top face**. Everything else then grows from
the build plate, the two 45 degree facets and the two bores are the only
overhangs and both are at 45 degrees, and nothing needs support. Any opaque
filament does; it is 0.78 cm³, about a gram.

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
[`fpga/boards.py`](../boards.py): the part occupies x -5.07 to 10.46 and
y 33.79 to 54.21 in board coordinates, overhanging the board's front edge by
5.07 mm.
