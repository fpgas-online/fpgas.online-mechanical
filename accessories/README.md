# Accessories

Parts that are neither a Tiny Tapeout board nor a Raspberry Pi, but that turn
up in the same assemblies.

| | |
|---|---|
| `parts.py` | Hand-curated, with per-value provenance: the Pmod HAT Adapter, its pin map, the PoE splitters and the PoE M.2 HAT+ (B) |
| `measure_pmod_hat.py` | Photogrammetry for the Pmod HAT Adapter |
| `measure_poe_m2_hat.py` | Photogrammetry for the PoE M.2 HAT+ (B)'s M.2 system |
| `raspmod.py` | **Generated.** The Raspmod's geometry and pin map |
| `extract.py` | Reads the Raspmod's KiCad board file and writes `raspmod.py` |
| `compare.py` | Rewrites the tables in `raspmod-vs-pmod-hat.md` from the two data modules |
| [`raspmod-vs-pmod-hat.md`](raspmod-vs-pmod-hat.md) | The two ways of putting Pmods on a Raspberry Pi, compared: pin maps and mechanics |
| `output/` | Five `ACC-…` sheets, as SVG and PDF |

`parts.py` is hand-curated because its sources are not machine-readable: a
product photo, a dimensioned marketing image, and a pinout table on a web
page. Every value cites where it came from and, where the figure is a
measurement rather than a published dimension, its error bar. The Raspmod is
the exception: its KiCad board file is published, so `extract.py` reads it
the way the FPGA and Tiny Tapeout extractors read theirs.

```sh
uv run --no-project python accessories/extract.py      # needs tmp/src, see make fetch
uv run --no-project python accessories/compare.py
```

A sheet's file is named for what the part is, and the title block says who
makes it and what its part number is. `ACC_STEMS` in
[`tools/layout.py`](../tools/layout.py) maps each part key to its stem, and
what that drops differs by part: the two PoE splitters' keys name their
vendor, because that is what you buy -- `waveshare-poe-usbc` becomes
`output/poe-usbc.pdf`. The adapter's key never did: it is `pmod-hat-adapter`,
and `digilent-` was put in front of it by hand when the file name was written,
which is where the old `ACC-DIGILENT-PMOD-HAT-ADAPTER` came from. The
Raspmod's key is already what the thing is called. The M.2 HAT assembly's key
names its vendor and Waveshare's variant letter, both of which the title
block's part number says, so `waveshare-poe-m2-hat-b-acorn` becomes
`output/poe-m2-hat-acorn.pdf`.

The drawing name is not that stem in capitals. A drawing number is quoted in
notes, on orders and out loud, so `ACC_NAMES`, beside `ACC_STEMS`, gives each
stem a name of two short words: the kind of part, then which one of that kind.
`pmod-hat` is `ACC-HAT-PMOD` and `raspmod` is `ACC-HAT-RMOD`, the two ways of
putting Pmod ports on a Raspberry Pi; `poe-m2-hat-acorn` is `ACC-HAT-M2POE`,
the HAT that gives a Pi an M.2 slot and Power over Ethernet; `poe-usbc` is
`ACC-POE-USBC` and `poe-microusb` is `ACC-POE-MUSB`, the two splitters. A
table rather than a rule, because these stems are words and not codes and
nothing mechanical shortens `raspmod` to four characters that still say which
board it is. HAT is Digilent's own word for its adapter; the Raspmod is filed
under it as the other way of doing the same job, though it is
[not a HAT](raspmod-vs-pmod-hat.md) in the specification's sense and reaches
the Pi over a ribbon cable. The PoE M.2 HAT+ (B) earns the same word on the
test the Raspmod fails -- it sits on the Pi's 40-pin header and bolts through
the Pi's four mounting holes -- rather than on the specification's shape,
which is a 65 x 56.0/56.5 mm board where this one is 85 x 56. `M2POE` is
what it
adds to the Pi underneath it.

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/pmod-hat.pdf"><img src="output/previews/pmod-hat.png" width="270" alt="ACC-HAT-PMOD Digilent Pmod HAT Adapter"></a><br>
<b>ACC-HAT-PMOD</b> Digilent Pmod HAT Adapter<br>410-366, fitted to a Raspberry Pi 40-pin GPIO header
</td>
<td width="33%" valign="top" align="center">
<a href="output/poe-usbc.pdf"><img src="output/previews/poe-usbc.png" width="270" alt="ACC-POE-USBC Waveshare PoE Splitter 25 W, Type-C"></a><br>
<b>ACC-POE-USBC</b> Waveshare PoE Splitter 25 W, Type-C<br>POE-SPLITTER-25W-TYPE-C, extruded aluminium body
</td>
<td width="33%" valign="top" align="center">
<a href="output/poe-microusb.pdf"><img src="output/previews/poe-microusb.png" width="270" alt="ACC-POE-MUSB Generic PoE splitter to micro-USB"></a><br>
<b>ACC-POE-MUSB</b> Generic PoE splitter to micro-USB<br>IEEE 802.3af, 5 V output, sealed plastic body
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/raspmod.pdf"><img src="output/previews/raspmod.png" width="270" alt="ACC-HAT-RMOD Raspmod"></a><br>
<b>ACC-HAT-RMOD</b> Raspmod<br>TT Demoboard To Raspi rev 1.0, silkscreen v1.1: a frontplate for the demoboard's three Pmod hosts
</td>
<td width="33%" valign="top" align="center">
<a href="output/poe-m2-hat-acorn.pdf"><img src="output/previews/poe-m2-hat-acorn.png" width="270" alt="ACC-HAT-M2POE Acorn CLE-215+ in a PoE M.2 HAT+ on a Pi 5"></a><br>
<b>ACC-HAT-M2POE</b> Acorn CLE-215+ in a PoE M.2 HAT+ on a Pi 5<br>Plan envelope of the assembly; the Raspberry Pi 5 is the board drawn
</td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Digilent Pmod HAT Adapter (`ACC-HAT-PMOD`)

Digilent publish no mechanical drawing, DXF, STEP or board file for this part.
The three Pmod host positions were measured photogrammetrically from
Digilent's own top view, with scale and origin set by the four HAT mounting
screws, and are quoted at **+/-0.75 mm**.

That error bar is not a guess. The fit is checked against something not used
to derive it: the 40-way GPIO header must come out 50.8 mm long at a 2.54 mm
pitch, and the residual on that check is the honest error bar for everything
else measured here.

```sh
uv run --no-project --with pillow --with numpy python \
    accessories/measure_pmod_hat.py tmp/digilent/hat.png
```

## Raspmod (`ACC-HAT-RMOD`)

Pat Deegan's "TT Demoboard To Raspi": not a HAT but a frontplate, whatever its
drawing number says -- the `HAT` there files it with the Digilent adapter it
is an alternative to, not with the specification. Three
2x6 pin headers on its underside go into a Tiny Tapeout demoboard's three
Pmod hosts, three sockets on its front take external Pmods in their place,
and a 2x20 box header carries every signal to a Raspberry Pi over a ribbon
cable. It has no mounting holes; the plugs carry it.

Everything on the sheet is read from the board file at a pinned commit,
including the fact that the plugs sit on the demoboard's 22.86 mm host pitch,
which the extractor checks. The pin map comes from the same file, because
KiCad writes each pad's net into it. Which demoboard it fits, and how it
differs from the Digilent adapter, is in
[`raspmod-vs-pmod-hat.md`](raspmod-vs-pmod-hat.md).

## Acorn CLE-215+ in a PoE M.2 HAT+ (B) (`ACC-HAT-M2POE`)

An assembly rather than a part, and the only sheet here whose outline belongs
to a Raspberry Pi. The board drawn is the Pi 5, because that is the thing the
enclosure is built around and its geometry is Raspberry Pi Ltd's; what is new
is the phantom part on top of it, and that is an accessory measured off a
vendor image, which is what this directory is for. `raspberry_pi/boards.py` is
generated from Raspberry Pi Ltd's own drawings and nothing hand-curated
belongs in it.

Waveshare sell three PoE-plus-M.2 HATs for the Pi 5 and only the **(B)** takes
a 2280 card; the plain one and the (C) stop at 2242. The Acorn CLE-215+ is an
M.2 2280 M-key card, so the (B) is the one drawn.

Waveshare's dimension drawing states the outline and the mounting holes --
85.00 x 56.00, holes on a 58.00 x 49.00 rectangle 3.50 in from one end, which
is the Pi's own pattern -- and one more figure, the 3.00 mm by which the 2280
standoff projects past the opposite board edge. It dimensions nothing else of
the M.2 system, and there is no drawing, DXF, STEP or board file that does.

So the socket and the four standoffs are recovered from the same image the way
the Pmod HAT Adapter's hosts are, with scale and origin from the mounting
holes. Three checks the fit did not use come out at 0.12 mm or better: the
board's own edges against the declared 85.00 x 56.00; the three standoffs that
sit clear of the edge, each of which gives the connector datum independently
through the M.2 specification's 30, 42 and 60 mm module lengths, agreeing to
0.04 mm; and the fourth standoff, predicted at 80 mm from that datum and never
measured, whose boss then reaches exactly the 88.00 mm Waveshare's 3.00 puts
it at. Only three bosses are measured, so the fourth's diameter is the other
three's; Waveshare's 3.00 is what checks the pair of them.

The first of those checks is also what proves the image is being read the
right way up. Waveshare draw the HAT turned through 180 degrees from the way
Raspberry Pi Ltd draw a Pi, and nothing about the hole rectangle can show
that: it is symmetric, so a fit made on it comes out the same either way
round. What is not symmetric is that those holes sit 3.50 mm in from one end
of an 85 mm board and 23.50 in from the other, so the board's own lower-left
corner has to come back at the origin, and a view read the wrong way round
misses it by twenty millimetres. Read the right way round it lands at
(0.17, 0.23), which is a fourth residual and the widest of any check the fit
did not use; it is what the +/-0.2 mm on the sheet is rounded from, and why
a whole millimetre of tolerance on the orientation check itself is generous
and still cannot be in doubt.

```sh
uv run --no-project --with pillow --with numpy python \
    accessories/measure_poe_m2_hat.py \
    tmp/src/waveshare-poe-m2-hat/poe-m2-hat-b-size.jpg
```

The card itself is the M.2 specification's 2280 outline with SQRL's own extra
millimetre of width: they publish no drawing, their site is gone, and what the
Internet Archive has is the sentence that the Acorn "is one millimeter wider
than the official specifications". The CLE-215+ carries a heatsink whose
extent nobody publishes, so none is drawn and the sheet says so.

The sheet is plan only and gives no height for anything: Waveshare publish no
stack-up for the HAT or its standoffs, and SQRL none for the card. What the
sheet's `DIA` column gives for a standoff is the M2 x 0.4 tapped thread the
retention screw goes into, not a clearance hole; `BOSS` is what the standoff
actually occupies, and it is the boss, not the screw, that decides how far
past the Pi's edge the assembly reaches.

## PoE splitters (`ACC-POE-USBC`, `ACC-POE-MUSB`)

Drawn as three-view envelope drawings, which is what they are useful as: they
go inside a box and what matters is the space they need and where the cable
leaves.

Waveshare publish a dimensioned image for the 25 W PoE to USB-C splitter. The
generic AliExpress PoE to micro-USB part has no single authority, so the
envelope drawn is the larger of two independent body figures, and the sheet
says so rather than presenting a figure it cannot support.
