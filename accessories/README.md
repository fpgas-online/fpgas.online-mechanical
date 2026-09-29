# Accessories

Parts that are neither a Tiny Tapeout board nor a Raspberry Pi, but that turn
up in the same assemblies.

| | |
|---|---|
| `parts.py` | Hand-curated, with per-value provenance: every part here that has no machine-readable source, and the Pmod HAT Adapter's pin map |
| `measure_pmod_hat.py` | Photogrammetry for the Pmod HAT Adapter |
| `raspmod.py` | **Generated.** The Raspmod's geometry and pin map |
| `raspmod_direct.py` | **Generated.** The direct Raspmod's geometry, its plugs and where the Pi's pin 1 is under it |
| `extract.py` | Reads both Raspmods' KiCad board files and writes `raspmod.py` and `raspmod_direct.py` |
| `compare.py` | Rewrites the tables in `raspmod-vs-pmod-hat.md` from the two data modules |
| [`raspmod-vs-pmod-hat.md`](raspmod-vs-pmod-hat.md) | The two ways of putting Pmods on a Raspberry Pi, compared: pin maps and mechanics |
| `output/` | The `ACC-…` sheets, as SVG and PDF |

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
Raspmod's key is already what the thing is called.

The drawing name is not that stem in capitals. A drawing number is quoted in
notes, on orders and out loud, so `ACC_NAMES`, beside `ACC_STEMS`, gives each
stem a name of two short words: the kind of part, then which one of that kind.
`pmod-hat` is `ACC-HAT-PMOD`, `raspmod` is `ACC-HAT-RMOD` and `raspmod-direct`
is `ACC-HAT-DRMOD`, the three ways of
putting Pmod ports on a Raspberry Pi; `poe-usbc` is `ACC-POE-USBC` and
`poe-microusb` is `ACC-POE-MUSB`, the two splitters. A table rather than a
rule, because these stems are words and not codes and nothing mechanical
shortens `raspmod` to four characters that still say which board it is. HAT is
Digilent's own word for its adapter; the Raspmod is filed under it as the
other way of doing the same job, though it is
[not a HAT](raspmod-vs-pmod-hat.md) in the specification's sense and reaches
the Pi over a ribbon cable.

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
<a href="output/raspmod-direct.pdf"><img src="output/previews/raspmod-direct.png" width="270" alt="ACC-HAT-DRMOD Raspmod, direct"></a><br>
<b>ACC-HAT-DRMOD</b> Raspmod, direct<br>TT Demoboard To Raspi Direct rev 2.0: on the Pi's GPIO header, flat beside the demoboard or an Arty
</td>
<td width="33%" valign="top" align="center">
<a href="output/raspmod-direct-on-pi.pdf"><img src="output/previews/raspmod-direct-on-pi.png" width="270" alt="ACC-FIT-DRMOD Raspmod, direct, on a Raspberry Pi"></a><br>
<b>ACC-FIT-DRMOD</b> Raspmod, direct, on a Raspberry Pi<br>Every Model B sized Pi under the adapter, pin 1 on pin 1, and where a fourth plug would go
</td>
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

## Raspmod, direct (`ACC-HAT-DRMOD`)

The Raspmod with its ribbon cable taken out: the same board, its 2x20 box
header swapped for an SMT socket on the underside (Adafruit 2187, 3.8 mm
tall) so that it sits straight on a Raspberry Pi's GPIO header, and its
three plugs turned to right-angle headers that go sideways into a board's
Pmod hosts, the Pi lying flat beside that board. The 10 mm at the pin-40
end -- the clock and reset header and the push button -- is cut off so the
board clears the Pi's Ethernet and USB stack. It is a fork of Pat Deegan's
board at a pinned commit, `direct-gpio` on
[mithro/tinytapeout-demoboard-to-raspi](https://github.com/mithro/tinytapeout-demoboard-to-raspi),
and the extractor reads it as it reads the original, plus one more thing:
where the socket's pin 1 is, which is what places the Pi under it.

Two base plates carry a Pi, this adapter and an FPGA board at the heights
that make the plugs meet the hosts: see [`base_plates/`](../base_plates/README.md).

`ACC-FIT-DRMOD` draws it where it lives: on the Pi, every Model B sized
model at once, pin 1 on pin 1, with the parts some model puts under it --
the 3B+ and 4B's PoE header, which stops it seating, and the Pi 5's UART
connector, which clears -- each named with its height, and a fourth plug in
phantom one host pitch beyond P3 with the edge a board four plugs wide would
have. `pi_under.py` is the list of those parts, read off the Pi drawings,
and the composite; `base_plates/design.py` uses the same list to say which
Pis fit. It is the sheet a board reshaped to fit every model, with a plug for
each of the Arty's four hosts, is drawn against.

**The pin mapping is not yet right.** Swapping the footprints mirrors each
plug's mating with a host -- pin 1 lands on pin 6, and the ports come out
reversed -- so the copper between the plugs and the sockets has to be
re-routed before the board is made. Nothing mechanical moves when it is; the
sheet says so.

## PoE splitters (`ACC-POE-USBC`, `ACC-POE-MUSB`)

Drawn as three-view envelope drawings, which is what they are useful as: they
go inside a box and what matters is the space they need and where the cable
leaves.

Waveshare publish a dimensioned image for the 25 W PoE to USB-C splitter. The
generic AliExpress PoE to micro-USB part has no single authority, so the
envelope drawn is the larger of two independent body figures, and the sheet
says so rather than presenting a figure it cannot support.
