# Raspberry Pi

The Raspberry Pi boards a Tiny Tapeout demo board is usually paired with. Each
of `RPI-3B`, `RPI-4B` and `RPI-5` draws one model with a
[Digilent Pmod HAT Adapter](../accessories/README.md) overlaid, so the Pmod
host positions can be read off directly; `RPI-ALL` draws all three
models on the one 85 x 56 outline they share.

The Pi 5 is drawn a second time, with a different part on it, on
[`ACC-HAT-M2POE`](../accessories/README.md): an Acorn CLE-215+ in a Waveshare
PoE M.2 HAT+ (B). That sheet is filed with the accessories because what is new
on it is the accessory, and because the data behind it is hand-curated where
everything in this directory is generated.

| | |
|---|---|
| `boards.py` | **Generated.** Pi 3B/3B+, 4B and 5 |
| `extract.py` | Reads Raspberry Pi Ltd's own drawings and writes `boards.py` |
| `output/` | `RPI-3B`, `RPI-4B`, `RPI-5` and `RPI-ALL`, as SVG and PDF, and `raspberry-pi-sheets.pdf`, the four bound into one document |

```sh
tools/fetch_raspberry_pi.sh                           # once, needs network
uv run --no-project --with ezdxf --with pdfplumber python raspberry_pi/extract.py
```

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/rpi3b.pdf"><img src="output/previews/rpi3b.png" width="270" alt="RPI-3B Raspberry Pi 3 Model B and B+"></a><br>
<b>RPI-3B</b> Raspberry Pi 3 Model B and B+<br>85 x 56 mm, both models
</td>
<td width="33%" valign="top" align="center">
<a href="output/rpi4b.pdf"><img src="output/previews/rpi4b.png" width="270" alt="RPI-4B Raspberry Pi 4 Model B"></a><br>
<b>RPI-4B</b> Raspberry Pi 4 Model B<br>85 x 56 mm
</td>
<td width="33%" valign="top" align="center">
<a href="output/rpi5.pdf"><img src="output/previews/rpi5.png" width="270" alt="RPI-5 Raspberry Pi 5"></a><br>
<b>RPI-5</b> Raspberry Pi 5<br>85 x 56 mm
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/rpi-models-compared.pdf"><img src="output/previews/rpi-models-compared.png" width="270" alt="RPI-ALL Raspberry Pi 3B/3B+, 4B and 5 compared"></a><br>
<b>RPI-ALL</b> Raspberry Pi 3B/3B+, 4B and 5 compared<br>One 85 x 56 outline: what is shared and what moves
</td>
<td width="33%"></td>
<td width="33%"></td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

From Raspberry Pi Ltd's published mechanical drawings. The Pi 3B, 3B+ and 4B
have layered DXF; the Pi 5 is a vector PDF whose plot scale is recovered from
the mounting hole rectangle and *checked* to be 1:1 rather than assumed.

Identification is human: the `PARTS` table gives, for each connector, roughly
where it sits and roughly how big it is. The script finds the one outline that
matches and emits *its* exact numbers. If a source changes, the selector stops
matching and the script fails.

## Verified, not asserted

- **The Pi 3B and 3B+ share one sheet** only because both DXFs are read and
  every hole and connector position is required to match. The sheet covers
  both for exactly as long as they agree.
- **The 40-pin GPIO header is in the same place on every sheet**, because the
  Raspberry Pi HAT specification fixes it. The three readings are compared
  against a tolerance and snapped to the modal value: two agreed exactly and
  the Pi 5's PDF read 0.060 mm out, which is plot noise. The sheets say the
  number is shared rather than presenting it as though each drawing had stated
  it independently.

Feature numbers are fixed across the family: GPIO header is 1, power input is
2 whether it is micro-USB or USB-C, Ethernet is 3.

HDMI, micro-HDMI and the 3.5 mm audio jack are deliberately not drawn.

## The combined sheet

`RPI-ALL` is the three models superimposed. Everything they share
is drawn once in continuous line -- the outline, the four mounting hole
centres and the 40-pin header -- and everything that moves is drawn once per
model in that model's own broken line type, with a legend. Of those three
shared things only the header is checked by `extract.py`: the outline is
declared per model in the extractor's own table, and only the Pi 4B's holes
are read from its DXF, the other two coming from a hard-coded
`STANDARD_HOLES`. So the sheet's renderer checks all three itself and refuses
to draw rather than assert something it has not compared. What it is for is
the union envelope, 88.00 x 57.32 mm; the fact that the Ethernet jack and the
USB type A ports swap places between the Pi 3 and the Pi 4, so a chassis cut
for one will not take the other; and the two extra 3.00 mm holes the Pi 5
adds. Feature numbers are the family's, so a number appears twice where the
part is in two places, and the balloon's ring is drawn in the line type of
the model it belongs to.

The Pmod HAT Adapter is not on it. It is the same on all three models, so it
says nothing about how they differ, and its phantom pin fields fall exactly
across the lower edge and the right-hand connectors -- the two places this
sheet exists to show. `RPI-3B`, `RPI-4B`, `RPI-5` and `ACC-HAT-PMOD` carry
it.

## A fitting warning

Pmod host JC on the Pmod HAT Adapter overhangs the lower board edge, where
these boards carry their HDMI and power connectors. Digilent's manual says to
fit the two standoffs opposite the 40-pin connector so JC's pins cannot touch
the HDMI shell. Each sheet repeats that.
