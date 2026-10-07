# Where pin 1 is

Two pictures for the docs site's Tiny Tapeout fitting page, to go beside
the photographs of the cable step: where pin 1 is on the demo board v3.2's
three Pmod sockets, and on the Digilent Pmod HAT Adapter's three ports.
They are pictures, not sheets: no title block, no A3, drawn only with what
tells one pin from another, each light and dark on a transparent ground, as
SVG and PNG.

| | |
|---|---|
| `extract.py` | Reads the v3.2 board file and writes `pmods_v3p2.py`, checking every claim the picture makes about the board |
| `pmods_v3p2.py` | **Generated.** Each socket's pads, nets, corner mark, body and the silkscreen round it |
| `hat.py` | **Hand-written, derived.** The HAT's ports, from `accessories/parts.py`, and which end of each is pin 1 |
| `draw.py` | Draws both pictures; `tools/docs_images.py` writes them |
| `output/docs/` | `tt-demoboard-v3.2-pmods-{light,dark}` and `digilent-pmod-hat-ports-{light,dark}`, SVG and PNG |

```sh
tools/fetch_pmod_pin1.sh                                    # once
uv run --no-project python tinytapeout/pmod_pin1/extract.py
uv run --no-project --with pillow --with pypdf python tools/docs_images.py
```

## The demo board

[Light](output/docs/tt-demoboard-v3.2-pmods-light.png),
[dark](output/docs/tt-demoboard-v3.2-pmods-dark.png). The sockets seen from
above with the board's front edge, the one they hang over, at the bottom:
INPUT (`J11`, `ui_in`), BIDIR (`J12`, `uio`) and OUTPUT (`J13`, `uo_out`).
Pin 1 is the square pad under `i0`, `b0` and `o0`, at the right-hand end of
the row further from the edge.

The board prints a corner mark, an L, at the other end of that row, beside
pin 6, which is 3.3 V. That is where a pin 1 mark usually is, and it has
been taken for one; the picture marks it "NOT PIN 1". The mark is the
footprint's own silkscreen and sits under the left edge of the box the
board prints round each socket's label, so on the board the two read as one
line.

Everything drawn is read out of Tiny Tapeout's
[`tt-demo-pcb`](https://github.com/TinyTapeout/tt-demo-pcb)
`tinytapeout-demo.kicad_pcb` at commit `0277545` (12 January 2026), the
last commit at rev 3.2: pad numbers, shapes and positions, the nets, the
corner mark, the socket bodies past the edge (the footprint's fabrication
outline), and the board's own silkscreen round each socket -- the label box,
the block it prints over pins 5 and 11, and the words. The board file there
is the one `d830790` ("v3.2 as prototyped") has, which `TT-DB-V32` is drawn
from; `extract.py` checks that, and that pad 1 is the only square pad, that
pins 5 and 11 are on GND and 6 and 12 on +3V3, that the label over pad 1
ends in 0, and that the corner mark is nearer pad 6 than pad 1, and stops if
any is not so. Only the lettering is not to the board's size: it is set for
reading, at seven tenths of the board's height at this scale or 2.6 mm,
whichever is larger. GND and 3V3 under the columns are what the picture
adds; the board prints them on its back only.

## The Pmod HAT Adapter

[Light](output/docs/digilent-pmod-hat-ports-light.png),
[dark](output/docs/digilent-pmod-hat-ports-dark.png). The HAT as Digilent
photograph it, 40-pin header at the top: JA and JB face the left edge, JC
the bottom one. Pin 1 is the square pad with the 1 Digilent print beside it,
in the row further from the edge, at the end of JA and JB nearer the bottom
of the board and the end of JC nearer the barrel jack; 3V3 and GND are
printed by pins 6 and 5, at the other end.

Digilent publish no board file, so this one is not machine-read. Where each
port is comes from `accessories/parts.py`, which measured it off Digilent's
top view to about +/-0.75 mm, and the outline and holes from the Raspberry
Pi HAT specification, as on `ACC-HAT-PMOD`. Which end and row is pin 1, and
where the lettering is, is read off the same top view, on the
[reference manual page](https://digilent.com/reference/add-ons/pmod-hat/reference-manual),
and off the photograph in the reference manual for Rev. B; the pads are not
drawn to size, since nobody publishes it.

The reading is `PMOD_HAT_PIN1_END` in `parts.py`, which holds each port's
`pin1_x`, `pin1_y` to it; `hat.py` uses the same reading and stops if its
pin 1 is not where `parts.py` puts it, so the picture and the sheets'
tables cannot disagree.

## Checks

`tools/docs_images.py` writes both through the same strict reader and
palette as the sheets' pictures, so a colour the dark palette does not know
stops the build, and refuses a picture whose smallest text prints under
2.5 mm at 180 mm wide or with two pieces of text overprinting.
`tools/check_docs_images.py` holds the committed files to what `draw.py`
draws, byte for byte.
