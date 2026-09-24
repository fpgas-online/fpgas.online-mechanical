# Raspberry Pi

The Raspberry Pi boards a Tiny Tapeout demo board is usually paired with, and
boards that are not Raspberry Pis but take their HATs, each drawn with a
[Digilent Pmod HAT Adapter](../accessories/README.md) overlaid so the Pmod host
positions can be read off directly.

| | |
|---|---|
| `boards.py` | **Generated.** Every Raspberry Pi drawn here |
| `extract.py` | Reads Raspberry Pi Ltd's own drawings and writes `boards.py` |
| `orangepi_pc.py` | Hand-curated: the Orange Pi PC, every reading it was measured from, and the figures and tolerance worked out from them |
| `measure_orangepi_pc.py` | Photogrammetry for the Orange Pi PC |
| `crosscheck_orangepi_pc.py` | Reads the Orange Pi PC out of other people's models of it |
| `verify_orangepi_pc.py` | Holds the Orange Pi PC's figures to checks they were not fitted to; run by `make check` |
| `output/` | The `RPI-…` sheets, as SVG and PDF, and `raspberry-pi-sheets.pdf`, all of them bound into one document |

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
</table>

<!-- sheets:end -->

## Where the numbers come from

For the Raspberry Pis, from Raspberry Pi Ltd's published mechanical drawings. The Pi 3B, 3B+ and 4B
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
2 whether it is micro-USB, USB-C or a barrel jack, Ethernet is 3.

HDMI, micro-HDMI and the 3.5 mm audio jack are deliberately not drawn on the
Pi sheets. The Orange Pi PC's sheet draws them, from 6 up, because nobody else
has drawn that board at all and a case round it has to clear them.

## Orange Pi PC (`RPI-OPIPC`)

Xunlong publish one mechanical figure for this board, its size, and no
drawing. It is drawn here from photographs: the four board edges are found in
each, a homography takes the corners onto the 85 x 56 mm rectangle, and the
holes, the header and every connector are measured in that frame. Two
independent pairs of photographs are used, top and bottom -- linux-sunxi's of
a v1.3 board and Xunlong's product page views of a v1.2 -- and the figure
drawn is the mean of every photograph that shows a thing.

The header is found from its solder joints, in the bottom views, where they
lie in the board plane. A connector's top face stands off the board and is
drawn larger than it is, about the point under the lens; the header gives
that point and the lens's distance too, its pin tips in the top view against
its joints in the bottom view of the same board, and each top face is put
back where it stands.

The sheet quotes **+/-0.4 mm** for holes and header and **+/-1.1 mm** for the
parts, each the worst disagreement between two photographs of one thing or
with a check the fit did not use. `verify_orangepi_pc.py` recomputes both and
holds the figures to:

- the header, which must come out 48.26 mm from pin 1 to pin 39 on a 2.54 mm
  pitch with its rows 2.54 mm apart;
- the board's own proportions in the photographs, which say 56 mm, not the
  55 mm of Xunlong's manual;
- the network jack, USB pair and micro-USB, whose widths must match the same
  parts on Raspberry Pi Ltd's drawings, and the HDMI, barrel and audio jacks,
  Xunlong's PC Plus drawing;
- the standoffs of every 3D-printable case fetched, Roman Gachin's model of
  the board, landroo's case cut-outs, and Xunlong's assembly drawing of the
  Orange Pi PC Plus, a sibling board said to be the same size. That last is
  the closest thing to a drawing Xunlong have published, and it centres every
  part the PC shares within half a millimetre of where the photographs do.

```sh
tools/fetch_orangepi_pc.sh                            # once, needs network
uv run --no-project --with numpy --with opencv-python-headless python \
    raspberry_pi/measure_orangepi_pc.py --grids tmp/orangepi_pc
uv run --no-project --with numpy --with trimesh --with scipy --with networkx \
    --with shapely --with ezdxf --with ezdwg --with libarchive-c python \
    raspberry_pi/crosscheck_orangepi_pc.py
uv run --no-project python raspberry_pi/verify_orangepi_pc.py
```

The connector edges are read by eye off a 1 mm grid ruled on the rectified
photographs; `--grids` writes them, so any reading can be checked.

## A fitting warning

Pmod host JC on the Pmod HAT Adapter overhangs the lower board edge, where
these boards carry their HDMI and power connectors. Digilent's manual says to
fit the two standoffs opposite the 40-pin connector so JC's pins cannot touch
the HDMI shell. Each Pi sheet repeats that.

On the Orange Pi PC that advice cannot be taken. Its header sits 1.34 mm
right of and 0.15 mm below a Pi's and the adapter goes with it, so the
adapter's holes miss the board's by 2 mm or more and no standoff joins the
two: the header carries it alone. What clears the adapter's underside is not
established, because no heights were measured, and the sheet says so.
