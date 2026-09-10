# Board mechanical diagrams

2D orthographic (blueprint style) mechanical drawings of the Tiny Tapeout demo
boards, the Raspberry Pi boards they are usually paired with, a couple of PoE
splitters, and a generic mounting plate that any Tiny Tapeout demo board
revision bolts onto.

The drawings are meant for designing things the boards mount into: plates,
brackets, enclosures. Every dimension is traceable to an official source, and
each sheet lists its sources.

## What is here

| Directory | Contents |
|-----------|----------|
| `diagrams/tinytapeout/` | 8 sheets, one per Tiny Tapeout demo board revision |
| `diagrams/raspberry-pi/` | 5 sheets: Pi 3A+, 3B, 3B+, 4B, 5, each with a Digilent Pmod HAT Adapter overlaid |
| `diagrams/accessories/` | Pmod HAT Adapter, and two PoE splitters as three-view envelope drawings |
| `diagrams/mounting-plate/` | The generic mounting plate, plus a fitting guide |
| `data/` | The mechanical database. Two modules are generated; the rest is hand-curated with per-value provenance |
| `scripts/` | Extractors, the plate designer, and the generator |
| `drafting/` | A small 2D drafting library that renders a `BoardSpec` as an ISO-style sheet |

Each sheet is written as SVG, PDF and PNG. A3, mostly 1:1.

## Regenerating

```sh
scripts/fetch_raspberry_pi.sh                       # official Pi drawings
git clone https://github.com/TinyTapeout/tt-demo-pcb    tmp/src/tt-demo-pcb
git clone https://github.com/TinyTapeout/tt123-demo-pcb tmp/src/tt123-demo-pcb

uv run --no-project python scripts/extract_tinytapeout.py
uv run --no-project --with ezdxf --with pdfplumber python scripts/extract_raspberry_pi.py
uv run --no-project python scripts/design_mounting_plate.py
uv run --no-project --with pillow python scripts/generate_diagrams.py
uv run --no-project --with ezdxf python scripts/export_plate_dxf.py
uv run --no-project --with pillow python scripts/check_sheets.py
```

`check_sheets.py` re-reads the generated SVGs, recomputes every text bounding
box from the same font metrics the layout used, and reports text that collides,
falls outside the frame, or drops below the 2.5 mm ISO 3098 floor. It found the
notes block running through the sources heading on four of the Raspberry Pi
sheets, which is not obvious at screen size.

## How the numbers were obtained

The rule throughout: **machine-read the numbers, hand-curate the
identification**. Each extractor carries a small table saying which reference
designator, or which approximate position and size, corresponds to which
mechanical role. If a source changes, the selector stops matching and the
script fails, rather than quietly emitting a wrong dimension.

- **Tiny Tapeout**: read straight out of the upstream KiCad board files, at the
  commit each shuttle was produced from. Board outline, mounting holes, Pmod
  host pin fields, USB connector, seven-segment display and LEDs.
- **Raspberry Pi**: from Raspberry Pi Ltd's own drawings. The Pi 3B, 3B+ and 4B
  have layered DXF; the Pi 5 is a 1:1 vector PDF; the Pi 3A+ is a reduced PDF
  whose plot scale is recovered from the mounting hole rectangle.
- **Digilent Pmod HAT Adapter**: Digilent publish no mechanical drawing, DXF,
  STEP or board file for it. The three Pmod host positions were measured
  photogrammetrically from Digilent's own top view, with scale and origin set
  by the four HAT mounting screws, and are quoted at +/-0.75 mm. The fit is
  checked against the 2.54 mm pin pitch, which is what sets that error bar.
- **PoE splitters**: Waveshare publish a dimensioned image. The generic
  AliExpress part has no single authority, so the envelope drawn is the larger
  of two independent body figures and the sheet says so.

## The mounting plate

Every Tiny Tapeout demo board revision, TT01 through v3.3, spaces its Pmod host
headers 22.86 mm apart, because the Digilent Pmod Interface Specification
mandates that pitch for host ports on a board edge. Nothing else about the
boards stayed still: the outline went 104.5 x 81 to 99.5 x 78 to 85 x 85, the
mounting hole pattern changed three times and dropped from four holes to two,
and the distance from the front edge to the Pmod pin field moved from 4.465 mm
to 3.23 mm.

That one invariant is enough. Place each revision so its Pmod hosts land on a
common 22.86 mm grid, and its mounting holes fall where they fall. Eleven holes
and one slot cover all five distinct geometries on a 135 x 101 mm plate.

## Conventions

All sheets use the same frame: origin at the lower-left corner of the part, X
right, Y up, viewed from the component side, millimetres. Holes and Pmod
positions are ordinate dimensions from that single datum, so they neither
overlap on the sheet nor accumulate tolerance.

Dimensions and balloons are kept on opposite sides of each view. Long hole
schedules are tabulated rather than dimensioned individually.

## Licence

Apache 2.0. The upstream sources it draws from keep their own licences: the
Tiny Tapeout board files are Apache 2.0, and the Raspberry Pi drawings are
Raspberry Pi Ltd's.
