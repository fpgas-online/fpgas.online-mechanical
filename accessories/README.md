# Accessories

Parts that are neither a Tiny Tapeout board nor a Raspberry Pi, but that turn
up in the same assemblies.

| | |
|---|---|
| `parts.py` | Hand-curated, with per-value provenance |
| `measure_pmod_hat.py` | Photogrammetry for the Pmod HAT Adapter |
| `output/` | `ACC-01` to `ACC-03`, as SVG and PDF |

`parts.py` is the one hand-curated data module, because its sources are not
machine-readable: a product photo and a dimensioned marketing image. Every
value cites where it came from and, where the figure is a measurement rather
than a published dimension, its error bar.

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/digilent-pmod-hat-adapter.pdf"><img src="output/previews/digilent-pmod-hat-adapter.png" width="270" alt="ACC-01 Digilent Pmod HAT Adapter"></a><br>
<b>ACC-01</b> Digilent Pmod HAT Adapter<br>410-366, fitted to a Raspberry Pi 40-pin GPIO header
</td>
<td width="33%" valign="top" align="center">
<a href="output/waveshare-poe-usbc.pdf"><img src="output/previews/waveshare-poe-usbc.png" width="270" alt="ACC-02 Waveshare PoE Splitter 25 W, Type-C"></a><br>
<b>ACC-02</b> Waveshare PoE Splitter 25 W, Type-C<br>POE-SPLITTER-25W-TYPE-C, extruded aluminium body
</td>
<td width="33%" valign="top" align="center">
<a href="output/generic-poe-microusb.pdf"><img src="output/previews/generic-poe-microusb.png" width="270" alt="ACC-03 Generic PoE splitter to micro-USB"></a><br>
<b>ACC-03</b> Generic PoE splitter to micro-USB<br>IEEE 802.3af, 5 V output, sealed plastic body
</td>
</tr>
</table>

<!-- sheets:end -->

## Digilent Pmod HAT Adapter (ACC-01)

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

## PoE splitters (ACC-02, ACC-03)

Drawn as three-view envelope drawings, which is what they are useful as: they
go inside a box and what matters is the space they need and where the cable
leaves.

Waveshare publish a dimensioned image for the 25 W PoE to USB-C splitter. The
generic AliExpress PoE to micro-USB part has no single authority, so the
envelope drawn is the larger of two independent body figures, and the sheet
says so rather than presenting a figure it cannot support.
