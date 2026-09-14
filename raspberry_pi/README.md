# Raspberry Pi

The Raspberry Pi boards a Tiny Tapeout demo board is usually paired with, each
drawn with a [Digilent Pmod HAT Adapter](../accessories/README.md) overlaid so
the Pmod host positions can be read off directly.

| | |
|---|---|
| `boards.py` | **Generated.** Pi 3B/3B+, 4B and 5 |
| `extract.py` | Reads Raspberry Pi Ltd's own drawings and writes `boards.py` |
| `output/` | `RPI-01` to `RPI-03`, as SVG and PDF |

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
<a href="output/rpi3b.pdf"><img src="output/previews/rpi3b.png" width="270" alt="RPI-01 Raspberry Pi 3 Model B and B+"></a><br>
<b>RPI-01</b> Raspberry Pi 3 Model B and B+<br>85 x 56 mm, both models
</td>
<td width="33%" valign="top" align="center">
<a href="output/rpi4b.pdf"><img src="output/previews/rpi4b.png" width="270" alt="RPI-02 Raspberry Pi 4 Model B"></a><br>
<b>RPI-02</b> Raspberry Pi 4 Model B<br>85 x 56 mm
</td>
<td width="33%" valign="top" align="center">
<a href="output/rpi5.pdf"><img src="output/previews/rpi5.png" width="270" alt="RPI-03 Raspberry Pi 5"></a><br>
<b>RPI-03</b> Raspberry Pi 5<br>85 x 56 mm
</td>
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

## A fitting warning

Pmod host JC on the Pmod HAT Adapter overhangs the lower board edge, where
these boards carry their HDMI and power connectors. Digilent's manual says to
fit the two standoffs opposite the 40-pin connector so JC's pins cannot touch
the HDMI shell. Each sheet repeats that.
