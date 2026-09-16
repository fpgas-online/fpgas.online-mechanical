# The drafting library

A small 2D drafting library. It renders a `BoardSpec` -- from
[`tinytapeout/`](../../tinytapeout/README.md),
[`raspberry_pi/`](../../raspberry_pi/README.md) or
[`accessories/`](../../accessories/README.md) -- as an ISO-style sheet in
SVG, in sheet millimetres. There is no CAD dependency: the output is an SVG whose viewBox is
in millimetres and whose `width`/`height` are physical, so one user unit is
one millimetre on paper and every line weight below is a real pen width.

| Module | Role |
|--------|------|
| `canvas.py` | SVG primitives in sheet millimetres, Y up. The flip to SVG's Y-down happens once, here |
| `style.py` | Line weights, ISO 128 line types, lettering sizes, colours, sheet sizes, and real font metrics |
| `sheet.py` | The sheet itself: ISO 5457 frame, zone markings, title block, columns, tables, wrapped note blocks |
| `view.py` | A scaled orthographic view: maps model millimetres into a rectangle on the sheet |
| `dims.py` | Dimension primitives: linear, ordinate, leader, balloon, datum, centre mark |
| `board_sheet.py` | The board drawing: outline, holes, features, schedules, and the balloon placer |
| `plate_sheet.py` | The mounting plate fabrication drawing and the fitting guide |
| `rpi_compare_sheet.py` | `RPI-ALL`: the three Raspberry Pi models on the one outline they share |
| `camera_sheet.py` | Camera position sheets: a subject with the footprints a picture covers drawn over it |
| `enclosure_sheet.py` | Three-view envelope drawings, for the PoE splitters |
| `template_sheet.py` | A4 portrait drill templates, always 1:1 |

## Conventions

All sheets use the same frame: origin at the lower-left corner of the part, X
right, Y up, viewed from the component side, millimetres. Holes and Pmod
positions are ordinate dimensions from that single datum, so they neither
accumulate tolerance nor overlap on the sheet, and each witness line starts at
the feature it dimensions.

Sheet layout: the view sits top-left with its Y dimensions to the left and its
X dimensions on whichever horizontal edge its features are nearest, decided
per board by `_x_chain_edge` in `board_sheet.py` (the bottom unless a majority
of the dimensioned features sit on the top edge, as the Arty A7's Pmod hosts
do); schedules go in the right-hand column; notes and sources flow into a band
across the bottom, plus whatever is left at the foot of the column. Balloons
are placed inside the view against an obstacle list, so a leader is never
routed through a neighbouring feature.

Text is sized by ISO 3098 character height, not by font em. Nothing is smaller
than 2.5 mm capitals, which is 3.43 mm of font size for these faces. Long hole
schedules are tabulated rather than dimensioned individually, which is standard
once a part has more than a handful of holes.

The general tolerance lives in the title block, where a real drawing puts it
and where it cannot be the note that gets dropped for space.

DRAWING NO carries a name, not a number, and it is given half the title block
rather than the quarter the other fields in its row share. Half is more than
anything in this set needs now that the three families with the longest
stems are named by a rule: the widest name left, `FPGA-BUTTERSTICK`, clears a
quarter by 3.72 mm, where the mounting plate's fitting guide cleared it by
half a millimetre before that family had a rule of its own. But a sheet on
another branch needs half as much again as a quarter has, so the field is
sized for the names it will be given, not the ones it has. The two drill
templates carry their name in a header line instead, having no title block
for it to overrun.
The name itself is [`tools/layout.py`](../layout.py)'s. Any title block value that
will not fit its cell at the ISO 3098 minimum stops the render rather than
overprinting its neighbour, and `check_sheets.py` measures every name in the
set against the cell the sheet was actually drawn with, found on the page by
its own label and measured between its own rules.

Only three broken line types appear, each carrying exactly one meaning:
long-dash dotted for centre lines and axes, long-dash double-dotted for the
outlines of adjacent parts and keep-out envelopes, dashed for hidden detail
and for a part deliberately not fitted. They are named in `style.py` rather
than written out at each call site, because a chain-dot and a chain-double-dot
look nearly alike at A3 and had drifted into six hand-written variants.

One sheet adds three more, and only because none of the three above says what
it needs to say. `rpi_compare_sheet.py` draws three Raspberry Pi models on one
outline, where continuous means "shared by all of them" and a long dash, a
short dash and a dot mean one model each. They are a key, not a feature type;
they live in that module rather than in `style.py`, they appear on no other
sheet, and the legend on that sheet names all three.

## Reserve, then draw

The recurring bug in this library is reservation and drawing computing the
same geometry separately, so a label is placed clear of where a line was going
to be and the line then goes somewhere else. Radius callouts, Pmod envelopes,
witness lines, overall dimensions and the drill template's front-edge callout
each caused it once. The fix each time was a single shared function, or
reserving from the drawn geometry rather than from a second calculation of it.

`check_sheets.py` and `check_balloons.py` exist to catch what survives that.
See [the tools README](../README.md).
