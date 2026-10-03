# Scratch / working state

Living record of what is being built, what has been found, what worked and what
did not. Read this first when resuming work with no other context.

## Goal

Produce 2D orthographic / blueprint style **mechanical diagrams** (the kind you
would use to design a laser-cut or milled mounting plate, as in the Onshape
document the request linked) for:

1. Every Tiny Tapeout demo board -- outline, mounting holes, the Pmod headers
   along the "front" edge (3 on later boards, 2 on early ones), USB-C
   power/control connector, 7-segment display, other LEDs.
2. Raspberry Pi 3, 4 and 5 -- outline, mounting holes, power-input USB
   connector, USB-A ports, Ethernet jack, and where the Pmod headers land when
   a Digilent Pmod HAT Adapter is fitted.
3. Generic AliExpress PoE -> micro-USB splitter, and the Waveshare 25 W PoE ->
   USB-C splitter.
4. A "Tiny Tapeout generic mounting plate": one plate, pre-drilled so that any
   Tiny Tapeout demo board version can be mounted on standoffs with the Pmod
   headers always ending up in the same place.

## Ground rules (from the request)

- Data first: put everything into a computer-readable file (Python dicts).
- Use **official** sources: Tiny Tapeout KiCad files, Raspberry Pi Ltd
  mechanical drawings, Digilent Pmod spec, vendor product pages.
- Quick/hacky extraction scripts are fine. Do **not** build big test suites.
- Commit after every change, small logical commits. The git history is the log.
- Periodically have sub-agents review (a) the code and (b) the diagrams.

## Status

Phase: **complete; second drawing review outstanding**.

Everything asked for exists and is committed:

| Deliverable | Where |
|-------------|-------|
| 8 Tiny Tapeout demo board sheets | `diagrams/tinytapeout/` |
| 5 Raspberry Pi sheets, Pmod HAT overlaid | `diagrams/raspberry-pi/` |
| Digilent Pmod HAT Adapter, 2 PoE splitters | `diagrams/accessories/` |
| Generic mounting plate, fabrication + fitting guide + DXF | `diagrams/mounting-plate/` |

Each sheet as SVG, PDF and PNG.  A3, 1:1 except the fitting guide at 1:2.

Layout, after the reviews: view top-left with its dimensions below and left,
schedules in the right-hand column, notes and sources in a band across the
bottom that flows into columns and can spill into whatever the schedules leave
at the foot of the column.

Automated checks, all passing:

- `scripts/check_sheets.py` -- text collisions, lines running through text,
  out-of-frame content, anything under the 2.5 mm ISO 3098 cap-height floor.
  Every one of these classes caught a real defect at least once.
- `scripts/verify_mounting_plate.py` -- every revision's fasteners fit, every
  Pmod host lands on its plate position, no board overhangs, connector faces
  clear the plate front edge.
- Arc and outline checks inside `scripts/extract_tinytapeout.py`.
- `scripts/crosscheck_gerber.py` -- compares the extracted TT01/02/03 outline
  against the upstream Edge_Cuts gerber, an artefact KiCad's own plotter
  produced from the same board file.  Both give 104.500 x 81.000 mm, which
  confirms the whole s-expression parsing and coordinate path against something
  that did not come from this repository.

18 sheets exist under `diagrams/`, as SVG, PDF and PNG:
8 Tiny Tapeout revisions, 5 Raspberry Pi models (each with the Pmod HAT
Adapter overlaid), 3 accessories, and 2 mounting plate sheets.

The first code review has been acted on.  Its most important finding was that
the Raspberry Pi keep-out figures were being presented as if all equally
authoritative when only the Pi 4B's is machine-read and three models publish no
keep-out at all.

All source data is now in `data/`:

| File | Contents | Generated? |
|------|----------|------------|
| `data/schema.py` | frozen dataclasses, coordinate convention | no |
| `data/tinytapeout_boards.py` | 8 Tiny Tapeout demo board revisions | yes, from KiCad |
| `data/raspberry_pi_boards.py` | Pi 3B/3B+ (one sheet), 4B, 5 | yes, from DXF/PDF |
| sheets vs data | the data keeps every revision; the drawing set has one sheet per distinct geometry | |
| `data/accessories.py` | Pmod spec, Pmod HAT Adapter, 2 PoE splitters | no, hand-curated |

## Sources found so far

### Tiny Tapeout

Upstream repos (cloned into `tmp/src/`, git-ignored):

- `github.com/TinyTapeout/tt123-demo-pcb` -- `mpw-mb1.kicad_pcb`, the TT01/02/03
  board. Two Pmods only.
- `github.com/TinyTapeout/tt-demo-pcb` -- `tinytapeout-demo.kicad_pcb`, the
  TT04-and-later board. Three Pmods.
- `github.com/TinyTapeout/pcb-files` -- gerber/BOM archive for all boards.

Demo board revision history, recovered by walking the KiCad title block over
every commit that touched the PCB (`tmp/revscan.py`):

| Date       | Rev   | Title                                    | Commit    |
|------------|-------|------------------------------------------|-----------|
| 2024-03-01 | 1.1.0 | TinyTapeout 4+ Demoboard                 | 2555cc99f |
| 2024-03-12 | 1.1.1 | TinyTapeout 4+ Demoboard                 | 5a520bd64 |
| 2024-04-10 | 1.1.2 | TinyTapeout 4+ Demoboard                 | c43d09998 |
| 2024-04-11 | 1.2.0 | TinyTapeout 4+ Demoboard                 | 45f993362 |
| 2024-04-12 | 1.2.1 | TinyTapeout 4+ Demoboard                 | 8aad3f8bb |
| 2024-04-26 | 1.2.2 | TinyTapeout 4+ Demoboard                 | cfdd80d7b |
| 2024-06-11 | 1.2.3 | TinyTapeout 4+ Demoboard                 | a88cbc08b |
| 2024-08-07 | 1.2.4 | TinyTapeout 4+ Demoboard                 | 859f44210 |
| 2024-08-27 | 2.0.0 | TinyTapeout 06+ Demoboard                | 34afa4ae7 |
| 2024-10-10 | 2.0.1 | TinyTapeout 06+ Demoboard                | 68affaf68 |
| 2024-12-10 | 2.1.0 | TinyTapeout 06+ Demoboard                | 074afefe7 |
| 2025-01-08 | 2.1.1 | TinyTapeout 06+ Demoboard                | 22031a595 |
| 2025-02-11 | 2.1.2 | TinyTapeout 06+ Demoboard                | b1abc80dc |
| 2025-09-11 | 3.0   | Tiny Tapeout Demoboard v3 (PRELIMINARY)  | 3b4873f6f |
| 2025-12-01 | 3.2   | Tiny Tapeout Demoboard v3                | d830790ca |
| 2026-06-23 | 3.3   | Tiny Tapeout Demoboard v3                | ecb636ace |

Shuttle -> production revision, from `doc/historic/README.md` upstream:

| Shuttle    | Board             | Rev     | Commit named upstream |
|------------|-------------------|---------|-----------------------|
| TT01/02/03 | mpw-mb1           | 2.2.x   | tt123-demo-pcb        |
| TT04       | tinytapeout-demo  | 1.2.2   | cfdd80d7b             |
| TT05       | tinytapeout-demo  | 1.2.3   | a88cbc08b             |
| TT06       | tinytapeout-demo  | 2.0.1   | 292760e1f             |
| TT07       | tinytapeout-demo  | 2.1.0   | a799acb38             |
| TT08       | tinytapeout-demo  | 2.1.2   | 028a51b1e             |
| TT09+      | ???               | ???     | to be confirmed       |

### Raspberry Pi

Raspberry Pi Ltd publish per-model mechanical drawings. `datasheets.raspberrypi.com`
now 301-redirects to `pip.raspberrypi.com`, so `curl -L` is required.

- Pi 3B, Pi 3B+, Pi 4B: **DXF available** -- layered
  (`BOARD_OUTLINE`, `PARTS_TOP`, `PINS_TOP`, `SILK_TOP`, ...). This is by far
  the best source: exact geometry plus silkscreen reference designators.
- Pi 5: PDF only. That drawing is 1:1 vector on A4, so the geometry
  can be lifted out of the PDF content stream.

### Digilent Pmod

- Pmod Interface Specification 1.2.0 gives the numbers that matter: 2.54 mm
  (.10 in) pin grid in both axes, and **22.86 mm (.90 in) centre-to-centre
  spacing between adjacent host ports on a board edge**.  Host keep-out box is
  10.16 mm (.40 in) across with a 3.81 mm (.15 in) margin from the pin
  envelope.  The spec gives no numeric host-side board-edge setback.
- **Digilent publish nothing mechanical for the Pmod HAT Adapter (410-366).**
  No drawing, no DXF, no STEP, no board files anywhere under
  github.com/Digilent.  Reference manual and schematic are electrical only.
  So `scripts/measure_pmod_hat.py` measures the three host positions off
  Digilent's official top-view photo, using the four HAT mounting screws to set
  scale and origin.  Cross-check against the pin pitch says the result is good
  to about +/-0.75 mm.  JA and JB measured 23.18 mm apart and are snapped to
  the specified 22.86 mm.
- Digilent's site is behind Cloudflare.  `curl` gets a 403 unless it sends a
  browser User-Agent plus a matching `Referer` and `Sec-Fetch-*` headers.

### PoE splitters

- Waveshare PoE Splitter (25 W) Type-C: **102.5 x 29.6 x 24.8 mm**, from both
  the product page specification table and Waveshare's own dimensioned image.
  Finned aluminium extrusion, RJ45 in one end plate, captive lead at the other
  ending in an RJ45 male plug and a USB-C male plug.  5 V 5 A out, 37-57 V in.
  No panel mounting holes.
- Generic AliExpress PoE -> micro-USB: no single authority.  Most AliExpress
  listings quote the packaging, not the body.  Two independent sources agree on
  an 80 mm body: DSLRKIT's own 80 x 27 x 22 mm and Adafruit's measured
  80 x 30 x 24 mm.  Gigabit variants run longer, around 95 mm.  Glued plastic
  clamshell, no mounting holes.

### Tiny Tapeout shuttles after TT08

Per tinytapeout.com/chips, **no shuttle after TT08 has shipped**.  TT09 shows
TBD/TBD, TT10 was cancelled, and every IHP/SKY/GF run since carries only an
estimated delivery date.  So there is no authoritative TT09+ board revision to
find, and the v3.x boards are recorded without a shuttle.

## Decisions

- Extract geometry from machine-readable sources (KiCad `.kicad_pcb` s-expr,
  DXF, 1:1 vector PDF) rather than transcribing dimension text by eye.
- Hand-curated numbers are always tagged with their source in the data file.
- Machine-read the *numbers*, hand-curate the *identification*.  Each extractor
  carries a small table saying which designator, or which approximate position
  and size, corresponds to which mechanical role.  A source that changes makes
  the selector miss and the script fail loudly.
- Coordinate frame for everything: origin at the lower-left corner of the
  board's bounding box, X right, Y up, top view, millimetres.

## The mounting plate design

Plate is **135 x 101 mm**, corner radius 4.  Origin at its lower-left corner.

- Pmod host pin-field centres land at plate **x = 38.75, 61.61, 84.47** and
  **y = 9.00**, for every board revision.
- The plate's front edge sits 9.00 mm below the Pmod row, so the connector
  bodies overhang it by 2.78 mm and a peripheral plugs into clear air.  This
  works because the pin-field-centre to connector-face distance is **11.78 mm
  on every revision**, the footprint being unchanged throughout.
- 11 holes + 1 slot serve all five distinct board geometries, plus 6 M4 plate
  fixings in the clear border.  Rules: under 1 mm apart share one hole; too
  close to drill separately become a slot; otherwise separate holes.
- The TT01/02/03 board's two Pmods go on plate positions **2 and 3**, not 1 and
  2: that makes the plate 5.15 mm narrower, because that board is both the
  widest and the one whose Pmods sit furthest right.

## Key facts for the mounting plate

- **Pmod host pitch is 22.86 mm on every Tiny Tapeout revision**, TT01 through
  v3.3, because the Digilent spec mandates it.  That is what makes a single
  generic plate possible.
- The distance from the front board edge to the Pmod pin-field centre does
  change between generations:

  | Board | Pin-field centre Y | Pmod centre X positions |
  |-------|-------------------|--------------------------|
  | mpw-mb1 2.2.6 (TT01-03) | 4.465 | 41.85, 64.71 (two only) |
  | v1.2.2 / v1.2.3 (TT04/05) | 4.275 | 27.695, 50.555, 73.415 |
  | v2.0.1 / v2.1.0 / v2.1.2 (TT06-08) | 3.775 | 28.005, 50.865, 73.725 |
  | v3.2 / v3.3 | 3.23 | 19.35, 42.21, 65.07 |

- Mounting hole patterns differ per generation, and v3 has only two holes,
  on a diagonal:

  | Board | Size | Holes (dia 3.2 mm) |
  |-------|------|--------------------|
  | mpw-mb1 2.2.6, v1.2.x | 104.5 x 81.0 | 3.75/3.75, 100.75/3.75, 3.75/77.25, 100.75/77.25 |
  | v2.x | 99.5 x 78.0 | 3.5/3.5, 96.0/8.0, 3.5/74.5, 96.0/74.5 |
  | v3.2 | 85.0 x 80.0 | 4.0/76.0, 77.0/8.5 |
  | v3.3 | 85.0 x 85.0 | 4.0/81.0, 77.0/8.5 |

  Note the v2.x lower-right hole is at Y = 8.0, not 3.5: that pattern is not
  symmetric.

## What the reviews caught

Code review, round 1:

- Raspberry Pi keep-out figures were tabulated as if all equally authoritative
  when only the Pi 4B's is machine-read and three models publish none at all.
- A silent 3.2 mm fallback for a missing mounting hole drill size.
- The SVG large-arc flag hardcoded to 0.
- Hole clustering on the plate could average three coincident positions.

Code review, round 2:

- **Ordinate witness lines started on the far side of the feature** and ran
  back through it: the extension gap was subtracted where it should have been
  added.
- The identical-geometry signature compared bounding boxes but not the outline
  profile.
- An unused non-centred mode in `View.fit` mis-placed any view whose bounding
  box did not start at zero.

Self-check, `scripts/verify_mounting_plate.py`:

- **The plate had a real defect.**  Two revisions want a fastener 0.613 mm
  apart and the merge rule put one 3.40 mm hole at their midpoint, leaving an
  M3 shank 0.307 mm off centre in a hole with 0.200 mm of play.  The screw does
  not go in for either board.  Two positions may share a hole only when the
  hole's own clearance swallows the offset, which for 3.40 mm on M3 is 0.40 mm.
  That pair is now a slot; the tightest clearance anywhere is +0.144 mm.

Drawing review, round 1:

- **Text was sized by em, not cap height.**  ISO 3098 specifies lettering by
  character height, so `font-size="2.5"` gives a 1.82 mm capital.  Everything
  is now declared as a cap height; the DejaVu cap ratio is 0.7290.
- **Ordinate witness lines started at a board edge, not at the feature.**  So
  nothing said which number belonged to which hole.
- The Pi 5 was missing both micro-HDMI connectors, because the rectangle
  recovery only closed shapes drawn as a pair of full-width horizontals.
- Notes ran through the sources block on four Raspberry Pi sheets.
- `0.00 TYP` on the Pmod HAT sheet: the host-pitch dimension took the first two
  hosts on the board rather than the first two on a shared edge.
- Pi 4B hole IDs were in a different order from every other Pi.
- Balloon leaders routed through neighbouring features.

Drawing review, round 2:

- **S-2 / M-8: the fitting guide did not say what a group was.**  The captions
  gave only "TT01-03"; they now name the board revisions and shuttles in the
  group, label the holes and slots that group uses, and cross-reference the
  hole table on TT-MP-01.
- **M-13: the PoE splitter sheets.**  The RJ45 aperture had no X position in
  the end view; the aperture dimensions were quoted as if measured; the plan's
  dimensions were split above and below the view and stacked longest first.
  All four are photo-scaled, so they are now marked REF with the figure they
  are good to in a note, and each view has one dimension stack per axis:
  size nearest the view, then location, then overall.
- **m-2 / m-3: the plate hole table.**  Slots had no length, and the USED BY
  column mixed shuttle ranges with board revisions without saying so.  A LENGTH
  column and a key note, the key generated from the data.
- **m-4: line types had drifted.**  Six hand-written dash arrays, and the
  fitting guide's board outlines were chain-dot, which is a centre line.  Named
  D_CENTRE / D_PHANTOM / D_HIDDEN now carry one meaning each.
- **m-7: balloon leaders ruled across the phantom Pmod hosts.**  See below;
  this one went deep.

## Balloon placement, what was actually wrong

Chasing m-7 turned up five separate mis-prices in the placer, not one:

- The leader could only start at the feature's centre.  On the Pi 3 sheets the
  micro-USB sits under host JC, so every leader from its centre crossed JC.  A
  leader may now anchor anywhere on its feature.
- Every obstacle cost the same.  A leader across a connector outline is untidy;
  a leader across another balloon, another leader or a phantom host is
  unreadable.  Obstacles carry a weight now.
- A leader was charged for crossing its own feature, which every leader has to
  start on, so the balloon got wedged into whatever gap was nearest.
- The board outline was charged to leaders as well as to balloons.  A leader
  crossing the outline is how a balloon in the margin points at a part on the
  board; only the balloon itself must keep off the line.
- The ordinate witness lines are drawn after the balloons and so were invisible
  to the placer.  A balloon sat on one, which is what `check_sheets` was
  reporting.

One more, found by the new checker rather than by eye: a Pmod host's label
reserved the pin field's **full height** for a two-letter label, walling off
the diagonal every leader from the lower-left corner wanted to take.  Sizing
that box to the text took the crossings from 8 to 2.

The two that remain are the same physical case on the Pi 4B and Pi 5: the
micro-HDMI connectors sit directly beneath host JC, so a leader from them
crosses the host whichever way it leaves.  Both sheets carry a note saying so,
the one beginning "Pmod host JC on the Pmod HAT Adapter overhangs the lower
board edge".  Its number is not the same on the two sheets, because the number
of board-specific notes before it differs; cite it by its opening words, not by
number.  `scripts/check_balloons.py` now lists those two crossings as accepted
by balloon, and fails on any other.

Code review, round 3:

- **The REF tolerance note on the Waveshare sheet was wrong.**  It quoted
  "+/-1.5 mm to +/-2.0 mm"; the 2.0 belonged to the captive output cable, a
  feature that carries a tolerance but is not dimensioned anywhere on the
  sheet.  One definition now decides both which values are marked REF and what
  the note says about them.
- **Neither SVG-level check could fail a build.**  Both printed their findings
  and exited 0.  `check_sheets.py` exits 1 on any problem now, and
  `check_balloons.py` gates against a baseline listed per sheet and per
  balloon so a new crossing is caught even on a sheet that already has one.
- A balloon's own feature was exempted from its leader's obstacle set by
  comparing rectangles by value, not by index.
- `flip_text` had never been passed by any caller.

Drawing review, round 3, all twenty findings acted on:

- **Three dimensions pointed at nothing or at the wrong thing.**  The Pmod
  setback ran on a fixed lane that went through MT2 on the v3 boards and MT3
  on the adapter, with its value printed across the pin field.  The ordinate
  witness line locating the Pmod hosts on the Pi sheets stopped six
  millimetres short of the host, because it started inside the host's own body
  and the break logic removed the first stretch.
- **Notes and title blocks contradicted their own sheets.**  Note 9 on the
  plate named H2/H3, 78 mm apart, for a 1.59 mm web that is between H1 and H2.
  The v3 sheets were titled "(ETR)", an acronym defined nowhere and absent
  from the KiCad title block.  ACC-01 claimed +/-0.20 on a board whose host
  positions its own note says are +/-0.75.  ACC-03 called its envelope a
  maximum while a note said gigabit variants are 15 mm longer.  TT-MP-01 and
  TT-MP-02 carried different tolerances for one part.  The Model B's hole
  tolerance had been carried onto two drawings that state none.
- **Labels read as belonging to the wrong feature.**  "H3" and "PMOD 1"
  printed as one word; H3 and slot S1 had swapped over each other's features;
  two labels from neighbouring fitting-guide views landed on each other.
- **baseline="middle" was off by a whole cap height**, so every balloon digit
  sat high in its circle and every rotated ordinate label sat off its witness
  line.  Found only after moving the frame to ISO 5457 margins pushed the zone
  digits outside the trim line.
- Meaning was carried by colour alone with no key on any sheet; there is a
  legend on all eighteen now.
- Making room for what the sheets had to say needed the notes band to spill
  into the annotation column's dead space, and that exposed `notes_columns`'
  dry pass drawing its "(continued)" headings.

## What the third review asked for and did not get

- **Bigger views.**  The board sheets stay at 1:1 so an A3 print can be laid
  on the board; a 104 mm board on a 420 mm sheet leaves white space whatever
  is done with it.  What that space is for is now the notes, the sources and
  the legend.  Where a scale really was inconsistent -- the two PoE splitter
  sheets, the smaller drawn at half the size of the larger -- it is fixed.
- **A revision history block.**  Every sheet is Rev A, first issue, and the
  date is in the title block; a one-row history would say nothing the title
  block does not.  Worth adding at the first revision, not before.

Code review, round 4:

- **The output cable exit's dimensions on both PoE sheets were anchored at the
  far end of the plan**, so they sat against the RJ45 aperture eighty
  millimetres from the feature they describe.  Same class as round 3's "labels
  that read as belonging to the wrong feature", reintroduced by the commit
  meant to answer it.  The numbers are on the feature's own leader now.
- Unreachable code after a `return`, a callout without the reservation its
  twin had, duplicated thickness logic with an unhandled branch, and a
  docstring describing an arc format that changed when arcs began being
  resolved at extraction.

Drawing review, round 4, all findings acted on:

- **The projection symbol was the third-angle symbol** on the two sheets that
  say, and are laid out in, first angle.  The trapezium's short side faced the
  circles; in first angle it faces away.  Checked against the standard before
  changing it.
- **The assembled envelope counted positions marked "not fitted"**,
  overstating five demo board sheets by 8 mm.
- **The Pmod setback dimension's extension line ended in open board** on nine
  sheets.  Round 3 moved its lane clear of the holes it used to cross, which
  put it where there was nothing to point at.  The pin row has a centre line
  now, which is what a row of centres should have had all along.
- **The plate's 9.00 ordinate ran through hole H3 and slot S1.**
- **The general tolerance block asserted figures no source states.**  Fifteen
  sheets.  A note says where they come from, and a sheet whose schedule quotes
  the source's own tolerance no longer gives a second, different one.
- **A balloon sat on a connector on the Pi 3A+.**  Two mis-prices: a balloon's
  own feature was priced like a neighbour's, and witness lines were charged to
  leaders as well as balloons, so crossing one cost more than covering a
  feature.
- **"SOURCES (continued)" printed ninety millimetres above "SOURCES."**  The
  notes' tail spilled into the top of the annotation column; it goes to the
  foot of it now, level with the band, so the sheet reads left to right along
  its bottom.
- **The same line type meant two different things**: on a board sheet the
  chain-double-dot rectangle at a Pmod host is the connector body, on the
  plate it was the pin-field envelope.  The plate now draws both, exactly as
  the board sheets do, which also puts the 2.78 mm front-edge overhang its own
  note calls the point of the design on the view for the first time.
- Smaller: fillet radii printed to mixed precision, the same sentence in both
  a note and a source on every Pi sheet, and no statement anywhere that these
  sheets are generated and uncountersigned.

## Things that did not work

- `curl` without `-L` against `datasheets.raspberrypi.com` returns a 301 with a
  zero-length body. Always follow redirects.
- Cloning `tt-demo-pcb` with `--filter=blob:none` makes walking history
  painfully slow (each `git show` is a network round trip). Re-fetched all
  blobs with `git fetch --refetch`.
- **The KiCad footprint rotation transform was wrong at first** and silently
  mirrored every rotated footprint about its own origin.  KiCad measures
  rotation counter-clockwise on a Y-down screen, so the transform is the
  transpose of the usual maths-frame one.  Parts at 0 and 180 degrees come out
  identical either way, which is why it survived a first look.  Caught by
  plotting the extraction over the official board render: the 2x16 ANALOG
  header came out hanging off the left edge of the board.
- Connector footprints can carry their own `Edge.Cuts` geometry.  Reading only
  board-level edge cuts lost the USB-C recess in the TT04/TT05 board's upper
  edge.
- `pdfplumber` reports path points as `(x, top)`, Y down from the top of the
  sheet.  Using them directly mirrors the whole board vertically, and the
  mounting hole pattern is symmetric enough to hide it.  Caught because the
  40-pin GPIO header came out along the bottom edge instead of the top.
- Fetching Digilent images with plain `curl` returns a Cloudflare challenge
  page with a `.png` name.  A browser User-Agent plus `Referer` and
  `Sec-Fetch-*` headers gets the real file.
- Trying to pull the Digilent image out of a Playwright page with `fetch()` or
  a canvas both failed, on CSP and then on a hang.  Plain `curl` with the right
  headers was the answer.

- **Making the board outline a hard obstacle for leaders as well as balloons**
  pushed three balloons back onto the connectors they pointed at.  A leader
  crossing the outline is normal; only the balloon must keep off it.  The two
  costs had to be separated.
- **Letting a leader off scot-free for crossing its own feature** then let the
  balloon sit on top of that feature, because sitting on it had become the
  cheapest option.  The exemption belongs to the leader only.
- Widening the notes on the mounting plate and PoE sheets overflowed the notes
  band, which fails loudly rather than trimming.  Both times the fix was to
  cut prose, not to shrink the type.
- Writing a tolerance inline on a short dimension (`17.00 +/-1.5`) makes the
  value wider than the feature it dimensions, so the extension lines run
  through it.  REF plus a note is both shorter and the correct notation.

- **Adding notes is not free.**  Four rounds of "the notes will not fit this
  sheet at any band height".  The band is bounded by what the view leaves, and
  the view's margins were set generously and never measured.  Measuring them --
  the deepest dimension cleared the notes band by ten millimetres -- and
  letting the band spill into the annotation column's dead space fixed it
  properly; trimming prose four times had only moved the wall.
- **Reserving space for something drawn later has to use the same geometry.**
  Three separate faults, all the same shape: the radius callout reserved one
  span and drew another, the Pmod envelopes were drawn after the labels that
  had to avoid them, and the ordinate witness lines were drawn after the
  balloons.  Each is now computed once and used for both.

- **Fixing a placement by moving it is not the same as fixing it.**  Twice now
  a dimension was moved off the thing it was colliding with and left pointing
  at nothing: the Pmod setback lane, and the cable exit's dimensions.  The
  test is not "does it still collide" but "does its extension line end on the
  feature".
- **A weight that is right for one purpose is wrong for another.**  Witness
  lines had to be hard so balloons would not sit on them, which then made
  crossing one with a leader cost more than covering a feature.  Three
  obstacle classes now split position from route: the board outline, the
  witness lines, and a balloon's own feature.

## Dropped

- **Raspberry Pi 3 Model A+**, at the user's request.  It was the only source
  in the package that was a reduced plot rather than a 1:1 one, so removing it
  left the reduced-plot handling unreachable.  Rather than delete that
  handling, the test for it now comes from the recovered scale instead of a
  per-model flag: a flag has to be remembered, and a reduced source added later
  would otherwise be described as 1:1 by a sheet that never noticed.  The
  Raspberry Pi sheets renumbered from RPI-01..05 to RPI-01..04.

## Changes after the reviews

- **v3.2 has shipped.**  It said otherwise because the historic README, which
  is where every other revision's shuttle mapping comes from, does not carry
  it.  Tiny Tapeout's own board revision spreadsheet does: TT09, TTSKY25a,
  TTSKY25b, TTGF0p2, and the name "ETR".  A revision can now cite its own
  shuttle source instead of every sheet pointing at one document.
- **Mounting holes are numbered in board-version order**, so each revision's
  set is contiguous.  Numbered spatially, one board's pattern was H1, H3, H9,
  H10.
- **The USB-C is marked on the plate**, one outline per revision.  It moves
  further between revisions than anything else on these boards.
- **TT01-03's two Pmod hosts already aligned** with the later boards' second
  and third.  The fitting guide said "3 Pmods starting at position 1" and left
  the reader to work it out; it lists the plate positions now.
- **HDMI and audio dropped from the Raspberry Pi sheets**, on request.  That
  removed the two accepted balloon crossings with them: the micro-HDMI
  connectors were what forced a leader across Pmod host JC.
- **Pi 3B and 3B+ are one sheet.**  Not asserted: both drawings are read and
  every connector position required to match, so the sheet covers both only
  while they agree.
- **One feature numbering across the Raspberry Pi family**, and the 40-pin
  GPIO header in one position on every sheet.  The two DXFs agreed exactly and
  the Pi 5's PDF read 0.060 mm out, which is plot noise; the readings are
  checked against a tolerance and snapped, and the sheets say so rather than
  presenting a shared number as though each drawing had stated it.

- **One sheet per distinct geometry, not per revision.**  v1.2.2 and v1.2.3
  are the same board mechanically, as are v2.0.1 and v2.1.0, so eight demo
  board sheets became six.  The data still carries all eight: it is a database
  of what was built, and the plate is designed against individual revisions.
  Only the drawing set is merged, and the generator compares outline, holes,
  Pmod hosts and every feature before merging two revisions rather than taking
  a note's word for it.
- **Feature numbers are fixed per family**, so a number means the same part on
  every sheet of that family.  On the demo boards that leaves gaps, because
  the revisions with a fourth LED have no DIP switch and the ones with a DIP
  switch have no fourth LED; every number keeps a row, and a part the board does not carry is marked as such rather than leaving a gap.  The
  Raspberry Pi family has no gaps, so the same mechanism is invisible there.

- **Drill templates are gauges, not drawings.**  TT-MP-03 and TT-MP-04 are A4
  portrait at 1:1: printed, taped to the work, punched and drilled through.
  The thing that can ruin them is invisible on screen, so the sheets carry two
  printed 100 mm scale bars and `check_drill_template.py` measures the PDFs
  back and compares every hole against the plate data that drew it.
- **The default print setting is the failure mode.**  The queue these were
  written for reports `print-scaling/Print Scaling: auto *auto-fit fill fit
  none` and a 4.32 mm hard border, so its default scales A4 by
  min(201.36/210, 288.36/297) = 0.9588 and moves the far corner of the hole
  pattern 5.6 mm.  Both sheets say so on their face, the README gives the
  `lp -o print-scaling=none` invocation, and feeding the checker a page scaled
  by that exact factor makes it report five problems and find no holes at all.
- **Two scale bars, not one**, because a laser fuser shrinks paper along the
  feed direction: the axes scale by different amounts, which a single bar
  cannot see.
- **Everything drilled is black and nothing else is.**  A colour laser
  registers its planes to a few tenths of a millimetre, which is more than the
  clearance being worked to, so a hole circle and its punch cross stay in the
  one plane that cannot misregister against itself.  The board outlines are
  pale washes, one hue per revision, and are not obstacles for label
  placement: five of them cover most of the plate, so avoiding them would
  leave nowhere to put an ID.
- **The layout is measured, not guessed.**  The bottom band is sized from
  `notes_height` and `table_height` and the drawing gets what is left; if that
  is less than the plate needs the sheet refuses to render rather than quietly
  shrinking the one thing on it that has to be true size.  It fired twice
  while this was written, which is how the notes came to be one line each.

## Repository layout: grouped by subject

Everything above was written when the repository grouped by *kind* --
`data/`, `drafting/`, `diagrams/`, `scripts/` -- so paths in earlier entries
are the old ones. The layout now groups by *subject*, because grouping by kind
smeared everything about one board across four directories:

| Was | Is |
|-----|----|
| `data/tinytapeout_boards.py` | `tinytapeout/boards.py` |
| `scripts/extract_tinytapeout.py` | `tinytapeout/extract.py` |
| `diagrams/tinytapeout/` | `tinytapeout/diagrams/` |
| `data/mounting_plate.py` | `tinytapeout/mounting_plate/plate.py` |
| `scripts/design_mounting_plate.py` | `tinytapeout/mounting_plate/design.py` |
| `scripts/verify_mounting_plate.py` | `tinytapeout/mounting_plate/verify.py` |
| `diagrams/mounting-plate/` | `tinytapeout/mounting_plate/diagrams/` |
| `data/raspberry_pi_boards.py` | `raspberry_pi/boards.py` |
| `data/accessories.py` | `accessories/parts.py` |
| `data/schema.py` | `tools/schema.py` |
| `drafting/` | `tools/drafting/` |

- **The mounting plate is a Tiny Tapeout thing**, so it sits under
  `tinytapeout/` rather than beside it.
- **`raspberry-pi` had to become `raspberry_pi`.** A Python package cannot
  have a hyphen in it, and merging code and output into one directory makes
  that directory a package.
- **Not everything has a subject.** The drafting library, the schema, the
  generator and four of the six checks work on every family or on none, so
  they live in `tools/`. Grouping by subject alone does not cover them.
- **`tools/layout.py` is the one answer to "where are the sheets".** The
  generator, the README builder and the three checks that walk every sheet all
  need it, and a family added in one and forgotten in another is exactly the
  drift those checks exist to catch.
- **Previews sit beside the sheets they preview** rather than in one pool, so
  a family stays self-contained.
- **One README per directory**, each about that directory: where its numbers
  came from, what is checked rather than assumed, what to run. The front page
  is a table of contents and the things that are true of all of them.
- **`check_sheets.py` now also checks every relative link in every README**,
  because a documentation split means links written relative to the file they
  sit in, and moving a directory then breaks links in files nobody touched.
  Proved by breaking one.
- **`check_pdfs.py` reads the git index, not HEAD.** It started on HEAD, which
  meant this very rename could not go green until after it had been committed.
  The index is what is about to become the repository, so staging an SVG
  without its PDF fails before the commit rather than after it.

## Reproducible output

`output/` is entirely build product, and committing build product only pays
off if rebuilding is a no-op. It was not: every `make diagrams` dirtied the
sixteen PDFs and the DXF whether or not a drawing had changed, so `git status`
after a rebuild had to be inspected by hand and discarded. Twice I did exactly
that. `tools/reproducible.py` pins what varies.

- **The PDF carries one field that varies between runs, and it is not where
  you would look.** (One more varied between machines, and a second is
  pinned alongside it; see the note on reproducing across machines, below.)
  Two renders of one SVG differ by *four bytes*, and grepping the file for
  `/CreationDate`, `/Producer` or `/ID` finds nothing: cairo puts the Info
  dictionary inside a compressed object stream, so those four bytes are
  deflate output. There is no `/ID` in the trailer at all. Rewriting through
  pypdf with a pinned `/CreationDate` fixes it, and the page content stream,
  the page size and the resources come through untouched -- checked, not
  assumed.
- **ezdxf already had the switch.** `ezdxf.options.write_fixed_meta_data_for_testing`
  pins the four timestamps, both GUIDs and the "written by ezdxf" marker. Its
  name says testing; reproducible output is the same requirement. It even pins
  to 2000-01-01, which is where the epoch in `reproducible.py` came from. It
  has to be set *before* `ezdxf.new()`, because one of the marks is written
  when the document is created rather than when it is saved -- set it later
  and exactly one line of the file still moves.
- **PYTHONHASHSEED was the real lesson.** After the timestamps and GUIDs were
  pinned, two consecutive exports came out identical and I nearly called it
  done. A `make clean` cycle then disagreed. Running the export twelve times
  gave *two* distinct files, about half each: ezdxf keeps the classes a DXF
  version requires in a `set` of strings and registers them by iterating it,
  and set iteration order depends on the per-process hash seed. Registering
  them explicitly and sorting afterwards settles it; the export registers them
  again but `add_class` ignores a name it already holds.

  The general lesson: **two runs is not a determinism test.** Anything
  hash-seed dependent passes it half the time. The check is now three full
  `make clean && make diagrams` cycles compared across every output file,
  67 of them at the time of writing.
- **`check_pdfs.py` compares bytes now**, not page content streams. The
  content-stream comparison only existed because the bytes could never match.

## Grouping the drill template by board revision

The drill template's schedule was indexed by hole: a row per feature, with a
`USED BY` column naming the revisions it serves, under the heading "SCHEDULE -
USED BY names the board revisions a feature serves".  That is the fabricator's
index, and TT-MP-01 already carries it.  Someone standing at a drill press has
the opposite question -- *I have a v3.3 board, which holes do I drill* -- and
had to read ten rows to answer it.

- **Grouping cannot partition the features.** H1, H9, S1 and S2 each serve two
  revisions, so a revision-major table repeats four of the twelve.  They repeat
  marked with `*` rather than being cross-referenced, so each block is a
  complete drill list: a reader fits one board from one block and never has to
  assemble their hole set from two places.
- **The block header row doubles as the block heading.** Heading each table
  with the revision name in the ID column's slot, rather than drawing a
  separate heading above it, buys back the six heading rows that grouping would
  otherwise have cost -- the difference between fitting and not.
- **Five columns, not four.** Six blocks at four columns needs 51.0 mm of band;
  the sheet has 50.6 mm, measured by binary search against the layout guard
  rather than estimated.  At five columns the tallest column is 40.9 mm.
- **The IDs became revision letters.** `H1..H10` in data order told a reader
  nothing: the numbering was already grouped by revision, but nothing on the
  sheet said so.  They are now `A1..A4` for TT01-03 through `E1` for v3.3, so a
  label on the 1:1 view names the board it is there for.  A shared feature
  takes the letter of the *first* revision that uses it and keeps that one name
  everywhere; two names for one hole is how a hole gets drilled twice.
- **The fitting guide had a second, private numbering.** `_guide_view` counted
  its own `H1..` as it walked the holes.  That agreed with `hole_ids` only
  while both used the same rule, and the moment the IDs became letters the
  guide's views said `H4` beside a table that said `A4`.  It labels from
  `hole_ids` now, which is what that function's docstring claimed all along.
- **Two checkers, two different frames.** The over-long legend title was inside
  the drawing frame as far as `check_sheets` was concerned and 0.4 mm into the
  printer's unreachable margin as far as `check_drill_template` was concerned.
  Only the second one caught it.

## The sheets carry a version, not a date

Every title block had a DATE, filled with `date.today()`.  It was worse than
useless: rebuilding on a new morning rewrote all sixteen sheets and their PDFs
and PNGs, so `git status` after a rebuild said "everything changed" whether or
not any drawing had, and the reader who wanted to know which data a drawing
came from was told the weather instead.

The cell is now `VERSION`, holding `git describe --tags --always`.

- **It describes the last commit to touch a source path, not HEAD.** That is
  what makes it converge, and it is not obvious.  The output is committed, so
  stamping HEAD would mean: render at X, commit sheets as Y, rebuild and every
  sheet now says Y, commit as Z, rebuild again...  There is no fixed point.
  Excluding `*/output/*` gives one: committing output does not change the last
  source commit, so the rebuild after it is a no-op.
- **The workflow it implies is the one already in use**: commit source, then
  regenerate, then commit output.  A single commit holding both would embed the
  describe of its own parent and never reproduce.
- **Dirty is marked `+`, not `-dirty`.** The cell has 38.05 mm of room;
  `v0.0-78-gb9dedc6` needs 31.38 and `v0.0-78-gb9dedc6-dirty` needs 40.94.
  `_title_cell` raises rather than overprint a neighbouring field, so the long
  form would have made the ordinary edit-and-rebuild loop fail to render --
  a guard firing on the normal case rather than on a mistake.
- **No git, no problem**: a tarball or a history-less clone stamps `no-git`
  rather than failing.

## Names and shuttles from Tiny Tapeout's board spreadsheet

Tiny Tapeout keep a board revision spreadsheet, and it is now the authority for
two things the drawings had been getting from elsewhere: what a board is called
and which shuttles used it.

- **The ID column is the canonical name.** Sheets are titled `DB mpw v2.2.6`,
  `DB 4+ v1.2.2`, `DB 06+ v2.1.2`, `DB ETR v3.2` -- the board's identifier,
  not a description of it. The old titles ("Tiny Tapeout 06+ Demo Board") were
  the only place in the world spelling it that way: the KiCad title blocks and
  the spreadsheet both say "Demoboard".
- **TT01 and TT02 both leave the mpw sheet.** Its "Used by" column gives
  `DB mpw v2.2.6` to TT03 alone. TT01 was a bare-die trial run with no PCB at
  all, and TT02 shipped on `DB mpw v2.2.5`, a revision the upstream KiCad
  repository does not carry -- so TT02 now appears on no sheet, which is the
  honest answer rather than a convenient one.
- **The plate groups were renamed with it.** They were `TT01-03`, `TT04-05`,
  `TT06-08`, `v3.2`, `v3.3` -- shuttle ranges, and the first one was a false
  claim as soon as TT01 and TT02 left. They are the board IDs now, which name
  the board rather than asserting who used it.
- **The shuttle list was typed out twice**, in `extract.py` per revision and in
  `design.py` per plate group, agreeing only because someone kept them in step.
  Dropping TT01 is exactly the edit that desynchronises them: the fitting guide
  would have gone on claiming TT01 while the board sheet denied it.
  `design.py` reads `used_by` out of the board data now and its fourth field
  is gone.

Two things broke in ways worth recording, both because a name changed shape:

- **`DB 4+` ends in the character that separated the names.** A hole's
  provenance label was `TT04-05:MT1+TT06-08:MT1`, joined with `+`. With the IDs
  as names that became `DB 4+:MT1+DB 06+:MT1`, which splits into pieces naming
  no revision at all, and the plate refused to build: "DB 4+ uses 0 plate
  positions but its board has 4 mounting holes". The separator is `LABEL_SEP`
  in `tools/schema.py` now, and it is `|`.
- **The label's order was load-bearing and nobody knew.** The first revision in
  a label is the one the feature is lettered for, and the labels were built
  with `sorted()`. `TT01-03` < `TT04-05` < `v3.2` happened to be board order,
  so the sort was right by luck for as long as the names lasted. `DB ETR v3.2`
  sorts before `DB mpw`, so hole A1 silently became D1. It sorts by placement
  order now.

The fitting guide's placement table also turned out to have been overflowing
its column all along -- 205 mm of content in 162 mm -- and `table()` had been
quietly scaling it. The longer names pushed it far enough that text began to
collide and `check_sheets` finally caught it. It is six columns now: the board
revisions each group covers are on that group's own view a few centimetres
away, and carrying them in the table too cost 36 mm.

## DB mpw v2.2.5 was there all along

Having just written that TT02's board "is not in the upstream board repository
and so not drawn here", the obvious question came back: where is it?  It is in
`tt123-demo-pcb` at commit `303509a`, "v2.2.5: 7-seg fp, new osc, nRST pull-up",
dated 2023-11-13.  The repository has no tag for it, only the two tags v2.1 and
v2.2.3, which is why looking for one found nothing.

Extracted and compared against v2.2.6: outline, mounting holes, Pmod hosts and
every one of the six features are identical.  So it is the same sheet, merged
the way v1.2.2/v1.2.3 and v2.0.1/v2.1.0 already were, and TT02 is back on it.

Three things this turned up:

- **A board can be in the data and on no sheet, silently.** `TT_ORDER` in
  `generate_diagrams.py` is a hand-written list, and adding v2.2.5 to the
  extractor put it in `boards.py` and nowhere else: the build wrote its
  sixteen sheets and said nothing.  It now refuses to run if a board in the
  data is missing from `TT_ORDER`.
- **A merged sheet kept only its first revision's notes.**  The note about
  TT01 never having a PCB belongs to v2.2.6; v2.2.5 joined the sheet in front
  of it and the note left the drawing.  Notes are unioned across the covered
  revisions now.
- **The merge hardcoded the board file's name.**  `subtitle=f"tinytapeout-demo
  rev {covered}"` was true of every merged sheet until this one, whose file is
  `mpw-mb1`.  It comes from the first revision's own subtitle now.

Unioning the notes then pushed the 4+ sheet past its notes budget by exactly
one line, which turned out to be a duplicate that had been on every Tiny
Tapeout sheet: the family note and the per-board note both stated the 22.86 mm
Pmod pitch.  They are one note now, carrying the Digilent citation.

## Registering the demo board sheets on the Pmod hosts

Flipping through the bound PDF, the boards jumped around the page: each sheet
was fitted to its own board, so the Pmod hosts -- the one thing that does not
move between revisions, and the reason a single mounting plate works -- landed
somewhere different on every page.

The sheets now share a horizontal frame, 121.75 mm wide, built from the same
Pmod-referenced offsets the plate uses: first host at the origin, or at the
second grid position for the two-host mpw board.  The hosts land on the same
three columns of every sheet, and what moves between pages is what actually
changed: the outline, the mounting holes, the USB-C.

**Vertically it did not, at first, and the reason was worth keeping.**  Sharing
the vertical extent means every sheet reserves the tallest board's height (v3.3
at 85 mm) on top of the 11.78 mm Pmod body overhang: 95.2 mm of drawing.  An A3
sheet holds that at 1:1 only with a notes band of 120 mm or less, and the 4+
sheet -- two merged revisions, so two board-file sources and two extra notes --
wanted 128 mm.  Measured, at band 120 it fitted two of its four notes.  Every
way round it was worse:

- band 128 for the family: every sheet drops to 1:2, losing true size, which is
  the property that lets a print be laid on the board;
- three note columns instead of two: 1 of 6 sheets rendered, not 5;
- condensing the merged sheet's two KiCad sources into one entry: still fails;
- a uniform band with the view anchored to the bottom rather than centred:
  algebraically identical to sharing the frame, because the area's top edge does
  not move with the band.  The feasible anchor's upper bound came out 181.58 at
  every band height tried, which is what makes it identical rather than merely
  similar.

So the first version registered horizontally only, and I wrote here that a few
millimetres of vertical alignment was not worth a note.

**Then the notes turned out not to be worth much either.**  Told they "looked
pretty useless", I read the fifteen printed on a sheet and four of them were
about how to read a drawing rather than about the board: the chain-double-dot
rectangle being a connector body, which the legend says with a sample of the
line; the sheet's own rounding to three decimals, justifying itself to a reader
who had not noticed; the feature numbers being fixed across the family, which
the schedule's own "- not on this board" rows demonstrate; and four USB-C fillet
radii to three decimals, contributed by a connector footprint, that nobody cuts
to.  The recess those radii described is real and stayed; the radii went.

With those gone the 4+ sheet fits the shared frame with its remaining notes
intact, so the registration is now on both axes: every Pmod host on every sheet
lands at exactly (103.87, 179.68), (126.73, 179.68) or (149.59, 179.68), all at
1:1.  The mpw board's two hosts take the second and third, the same way they sit
on the plate.

The general lesson is that the trade-off was never alignment against notes.  It
was alignment against *four particular notes*, and nobody had looked at them.

## The mpw board's DIP switch was missing

Asked why `DB mpw v2.2.5` and `v2.2.6` showed no 8-way DIP switch, the answer
was that the board has one and the extractor was never told.  `ROLES` carries a
`switch` designator per revision and the mpw entry simply had no `switch` key,
so the feature schedule printed "not on this board" for a part that is on it:
SW2, footprint `TinyTapeout:219-9GULLWING`, 11.04 x 21.45 mm.

It is a **9**-position switch, not 8.  Its footprint has 18 pads against the
16 of the `GENERIC_PIANO_8DIP` every later revision uses, and it is 2.1 mm
longer.  The label was the string "8-way input DIP switch" written into the
call, so it would have printed "8-way" for a 9-way part.  The count is divided
out of the pad count now, and the family-wide name in `FEATURE_NAMES` -- the
one used for the "not on this board" rows -- dropped the number it could not
know.

v1.2.2 and v1.2.3 really do have no DIP switch: their four SW designators are
all pushbuttons.  That one was right.

## Which kit a board ships in, and the TT03p5 board

The demo board sheets said which *shuttles* a board served and never which
*product* it arrives in, which is the question a reader actually has: nobody
identifies the board on their desk by reading a revision off the silkscreen.

Tiny Tapeout's spreadsheet has a Kit table, and it is not a restatement of the
shuttle column:

- `DB 06+ v2.1.2` ships in **two** kits for one shuttle -- the TT08 Dev Kit and
  its CoB edition, same demoboard, different breakout;
- `DB ETR v3.2` ships in **five**, and one of them is the FPGA Dev Kit, whose
  FabricFox iCE40UP5K sits where the ASIC carrier would go.  That is not a
  shuttle at all, so the shuttle column could never have named it.

So `kits` is its own field on `BoardSpec`, unioned across merged sheets the way
the shuttles already were -- taking them from the first revision put "TT02 Dev
Kit" on a sheet that is also the TT03 board.

**TT03p5 was missing too.**  Asked where it was, the answer was the same shape
as the v2.2.5 answer: its board, `DB 4+ v1.2.1`, is in `tt-demo-pcb` at commit
`8aad3f8`, and extracting it shows outline, holes, Pmods, every feature and
every edge identical to v1.2.2.  So it merges onto TT-DB-02, which now covers
three revisions and three kits.

The spreadsheet flags that revision "version to confirm" -- the TT03p5 render is
labelled v1.1.2 while the ID says v1.2.1 -- and the sheet says so rather than
quietly picking one.  Worth noting the commit dates are no help here: every 4+
revision from 1.1.2 to 1.2.3 is dated within sixteen days of April 2024, so the
history was squashed and the dates do not order the boards.

Fitting the kit note meant cutting two more notes, both of which had been
flagged as borderline and neither of which was about the board: one said port
names differ between families (a cross-reference to a drawing the sheet already
cites) and one said the board is 1.6 mm nominal rather than the KiCad stackup
sum (which MATERIAL in the title block says in three words).  The thickness note
survives in the one case that still needs it, where the stackup sum matches no
standard thickness and the title block would otherwise print an unexplained
number.

## Cutting the notes back to what the drawing cannot show

Every sheet was rendered and read as a picture, note by note, with one test:
does the drawing, its tables, its legend or its title block already say this?
Most of what was there failed it.  The demo board sheets went from twelve
notes to between five and nine, the Pi sheets from eleven to fourteen down
to eight or nine, the plate from eleven to nine, the fitting guide from five
to three, the enclosures from seven and nine to five and six.  The drill
templates kept their count and lost a third of their words.

What went, and why:

- **"All dimensions in millimetres. The datum symbol marks the origin, X right,
  Y up"** -- UNITS is in the title block, the datum symbol is a standard
  symbol, and the ordinate chains start at 0 on it.  What survives is the one
  thing a plan view cannot say: which side it is seen from.  A hole pattern
  viewed from the far side is its own mirror image.
- **"GENERAL TOLERANCE is a board-house figure"** and **"no CHECKED field
  because nobody signed it"** -- about the drawing, not the part.  DRAWN says
  "generated".
- **"Geometry is design nominal, read from the KiCad board file"** -- SOURCES
  cites the board file at its commit.
- **"Connector outlines are the component body as drawn by Raspberry Pi Ltd"**
  -- the legend says component body and SOURCES says Raspberry Pi Ltd.
- **"First-angle projection. The plan is the view from above..."** -- the title
  block carries the projection symbol and every view is captioned.
- **"The corner radius is nominal, end view only"** -- the callout says
  "R1.50 nominal (4 places), body section".
- Process narration: "read from both drawings separately and required to
  match", "agreed to 0.060 mm and were snapped", "scale recovered as 1.00002",
  "compared feature by feature before merging".  The result is what a reader
  needs; how it was checked is in the extractor.
- Electrical detail on a mechanical sheet: "no X1 and a 0R at R51", "5 V at
  up to 5 A (25 W)".
- Things visible on the view: DB mpw's two hosts sitting on positions 2 and 3
  (the fitting guide draws it and the table says "2, 3"); every revision's
  hosts landing on the same three positions (the whole sheet shows it); the
  AUX hole geometry on the Pi 5 (the schedule gives it).
- Duplicates: the Pi 3B hole tolerance was in the schedule, in the title block
  ("hole dia per schedule"), in SOURCES and in a note.  The drill template's
  scale bar length was in the caption and the note; "* shared: drill once" was
  in the schedule heading and the note; the revision letters were in the legend
  strip and the note.

What stayed was tightened rather than cut: the kits, now just the list (what a
kit *is* belongs to the shop); the Pmod pitch's citation, now also naming the
plate it serves; the keep-out design figure; the JC-over-HDMI warning; the
derived-hosts tolerance, now stated from `PMOD_HAT_TOL` on the Pi sheets rather
than a copied 0.75; the two enclosures' clamp-or-strap and cable-lead facts;
the plate's slot-row and USED BY conventions and its ID letter key.

Two corrections fell out of reading the sheets as a reader would.  The Pmod
HAT sheet said "only the Pmod host positions are derived", but the barrel jack
is scaled from the same photo at +/-1.5 mm; the note now names both.  And the
notes on three sheets showed a blank line between two notes: `notes_height`
reserved every line at a fixed "99." indent while `notes` drew at the real
widest number, 2 mm narrower, so a line that wrapped differently at the two
widths left its reserved extra line empty.  Both now measure at the same
indent.

The identical-geometry note is now emitted only for a revision that has a
twin; "no other revision shares this geometry" on a single-revision sheet was a
sheet saying it was for one board.

## Why balloon 5 on TT-DB-01 was 34 mm from its LED

Asked why one balloon on the mpw sheet sat a long way from the LED it
labelled, with every other balloon on the sheet close to its feature.  Every
ballooned sheet was rendered and read: the same thing happened to one LED
balloon on TT-DB-02, 03 and 04, always the last of a cluster.  The placer was
instrumented to print, for the flung balloon, what every near candidate
touched.  Three things, each of them a clearance that was right for one kind
of obstacle and wrong for another:

- **Balloon to balloon.**  A candidate is tested as a disc 2 mm larger than
  the balloon, and placed balloons were held at that same radius, so two
  balloons could not come within 10.4 mm centre to centre: a 4 mm gap between
  3.2 mm circles.  Four LEDs at 4.5 mm pitch in a corner cannot get four
  balloons round them at that spacing.  Now `BALLOON_GAP` = 1.2 mm of paper
  between rims, and the mpw sheet's four sit in a fan under their LEDs.
- **Balloon to line.**  The board outline, the ordinate witness lines and the
  overall dimensions were in the same set as component bodies, at the same
  2 mm clearance, so a balloon kept 5.2 mm off the board edge on every side.
  A line needs a millimetre.  Now `LINE_GAP` = 1.0, scored separately.
- **The lane above the board.**  On the 4+ sheet the fourth LED sits under the
  row, the edge is 3.7 mm to the right, and the neighbours' balloons took the
  rest, so the only spot a drafter would use is the lane between the outline
  and the width dimension.  That lane was 9 mm wide, which no balloon fits,
  and the candidate rings stepped 12.5 to 16.5 mm, straight over it anyway.
  `OVERALL_GAP` is now 12 mm and the rings go 9, 11, 13, 15, 17.5.

Nothing about the scoring weights changed.  The scoring was right: a leader
should not run through a neighbouring LED, and a 34 mm clean leader was the
cheapest thing the clearances left.  The clearances were wrong.

Every sheet was re-read afterwards.  Side effects, all of them improvements:
the Pi 4B's power-connector balloon dropped from a 20 mm diagonal to a short
horizontal leader; several USB and GPIO balloons on the Pi sheets moved into
the new lane above the board; the v3.2 sheet's USB-C balloon moved from a
diagonal to directly under its connector.  The Pi 3B and Pi 5 power
connectors still carry a 20 mm leader up into the board: the connector is in
the datum corner, the strip below it belongs to the ordinate chain, and the
witness line for the 3.50 hole runs left of it.  The leader is straight and
crosses nothing, so it stays.

**Short link for the Pmod specification** as well: `mith.ro/pmod-spec/`
resolves to Digilent's `pmod-interface-specification-1_2_0.pdf`, and both
sheets that cite it now print the short form.  Digilent's server answers
curl with 403 even given a browser user agent, so the target could not be
fetched from here; the URL is the one the sheets have always carried.

## Four FPGA boards, three kinds of source

Asked for sheets of the Arty A7, ULX3S, PYNQ-Z2 and ButterStick with Pmod,
USB, Ethernet and LEDs marked.  They are a new family, `fpga/`, drawn by the
same renderer as the demo boards, and the work was mostly in finding and
reading what each maker actually publishes:

- **Arty A7**: Digilent publish a DXF and a PDF plot.  The DXF carries the
  outline, every through-hole pad and the connector slots, nothing else; the
  PDF has the component bodies but no pad data.  So the outline, the four
  Pmod pin fields, the RJ45 pegs and the USB shell slots come from the DXF,
  and the RJ45, USB, Pmod bodies and eight LEDs from the PDF, whose scale is
  recovered from the outline per axis (they disagree by 0.2 %) and checked
  against the DXF wherever both have the same feature.  The DXF is a metric
  drawing of an imperial board: hosts on 22.80 not 22.86, pin rows 2.50 not
  2.54, outline 109.0 x 87.0 where the PDF's dimensions say 4.3 x 3.4 in.
  The sheet reports the drawing and says so.  **The Arty has no mounting
  holes**; the Ø10 rings at the corners are rubber feet, confirmed by
  Digilent on their forum.  Which LED row is which comes from the package
  sizes in Digilent's older Rev C 3D model: the 1.6 x 1.6 row is the
  tri-colour LD0-LD3, the 0603 row is LD4-LD7.
- **ULX3S**: KiCad, read at every tag the maker's manual marks "for sale"
  (v3.0.3, v3.0.7, v3.0.8, v3.1.7), and the four are required to agree on
  everything drawn before one sheet covers them.  They do.  The release tags
  are KiCad 5 files, so `tools/kicad_pcb.py` now reads `(module ...)` as
  well as `(footprint ...)`.  No Pmod and no Ethernet; the two right-angle
  2x20 GPIO sockets are drawn in their place.
- **PYNQ-Z2**: TUL publish a STEP assembly and nothing else machine-readable,
  so `tools/step_model.py` reads the board slab, its through-holes and each
  named part's placed box out of OpenCascade.  The Pmod pin holes are found
  as two 2x6 grids of 1.524 mm holes; the four 3.4 mm holes are the mounting
  holes.  The LEDs are not in the model and are not drawn; the sheet says
  where they are in words.  The PYNQ-Z1 was looked at and dropped: its 3D
  model has no holes and its outline disagrees with Digilent's own stated
  size.
- **ButterStick**: KiCad at the r1.0a release.  No Pmod: three SYZYGY ports,
  whose six plated standoff holes join the two M3 holes in the schedule,
  because the maker's own acrylic plate bolts through all eight.

Rows of LEDs are one feature each with the count and pitch in the label,
measured from the boxes rather than written in.  Feature numbers are fixed
across the family so the Ethernet jack is 3 on every sheet, present or not.

Pin 1 of a host follows the Pmod convention, top right looking into the
socket, which the PYNQ-Z2 manual draws and the Tiny Tapeout board files
number the same way.  **Found on the way: the Pmod HAT Adapter data in
`accessories/parts.py` puts pin 1 at the diagonally opposite corner of every
host, bottom-left looking in.**  That is hand-curated photogrammetry and was
not touched; it needs checking against the adapter's silkscreen.

Three drafting changes fell out, each from a sheet that needed it:

- A horizontal ordinate chain staggered its labels by their height rather
  than their width, so ButterStick's 18.09 and 18.50 overprinted.  Both
  kinds of chain now step a lane by the widest label.  This moves the
  second-lane labels on the demo board sheets a few millimetres further
  from the board, which is the clearance they should have had.
- The PYNQ-Z2 is 138.8 mm across with its hosts and fell to 1:2 for want of
  fourteen millimetres.  A view that misses 1:1 now retries with the right
  margin narrowed to 24 mm, which holds only the overall height dimension,
  before it accepts a smaller scale.  No sheet that already fitted moves.
- The Pmod spacing dimension is drawn after the balloons and was never
  reserved against them.  For hosts on a vertical edge it runs up the left
  of the view, and the PYNQ-Z2's micro-USB balloon sat on its value.

The KiCad geometry helpers moved out of `tinytapeout/extract.py` into
`tools/kicad_extract.py` so the new family reads a board file the same way;
the demo board data regenerates byte for byte.  `tools/dump_rpi_pdf.py` had
its second rectangle pass emitting every box transposed; fixed, and the Pi 5
USB-C box moved by 0.04 mm as a result.

## Reproducing the set on a second machine

The first rebuild on another computer dirtied every PDF in the repository
while changing no drawing. The committed set was drawn with Inkscape 1.4.3 on
cairo 1.18.4; this machine has Debian's Inkscape 1.4 (e7c3feb100, 2024-10-09)
on the same cairo. Rendering TT-DB-06's committed SVG on both gives content
streams that are byte-identical, 1,143,124 bytes with the same SHA-256, and
Info dictionaries that differ in one field: `/Creator` reads `Inkscape 1.4`
on one and `Inkscape 1.4.3` on the other. `/Producer` was `cairo 1.18.4` on
both. So "reproducible" had quietly meant "on one machine", by the width of a
point release's name.

`normalise_pdf` now pins `/Creator` and `/Producer` beside the date, for the
same reason the date is pinned: the version of the tool that drew a sheet is
not a property of the drawing, and the byte comparison in `check_pdfs.py` is
what says the drawing came out the same. Pinning both, not just the one that
moved, so that the next cairo release cannot repeat this. The price is that
the artefact no longer records which toolchain built it, which is why the
versions compared are written down here.

Two things the first attempt at this got wrong, both caught in review. The
three bound copies are pypdf's work, not cairo's, and pypdf already writes
its name without a version; stamping them as Inkscape on cairo overwrote a
true string with a false one, so a bound copy is pinned as `pypdf` with no
`/Creator`. And `check_pdfs.py` does not walk the bound copies at all, so the
only evidence they reproduce is a manual rebuild: `combine_pdfs` over the
committed sheet PDFs gives `raspberry-pi-sheets.pdf` back byte for byte.

The Inkscape 1.4.3 AppImage was tried first and is worse: it bundles cairo
1.16.0, so its `/Producer` differs instead. Debian's package is the one that
draws the same bytes.

## Sheets are named, not numbered

Every sheet carried a family prefix and a sequence position -- `TT-DB-01` to
`TT-DB-06`, `RPI-01` to `RPI-03`, `FPGA-01` to `FPGA-04`, `ACC-01` to
`ACC-04`, `TT-MP-01` to `TT-MP-04` -- produced by `enumerate()` over a reading
order list in the generator, repeated by the same `enumerate()` in the README
builder, and quoted by hand in four notes, two comments, `compare.py` and
every README. A sheet's identity therefore depended on what else was in the
set. With several pull requests open at once that each add a sheet, it
collides: four of them each called their FPGA sheet `FPGA-05`, and whichever
merged second had to renumber, re-render, rebind, and go back over every cross
reference written against the old number.

**The rule.** A sheet's drawing name is its own file stem in capitals, behind
its family's prefix, with the head of the stem that the prefix already says
taken off. One function, `tools.layout.drawing_name(family, stem)`, and one
table beside it giving each family its prefix and that lead:

| family | prefix | lead dropped |
|---|---|---|
| `tinytapeout` | `TT-DB` | `tt-demo-board` |
| `raspberry-pi` | `RPI` | `rpi` |
| `fpga` | `FPGA` | -- |
| `accessories` | `ACC` | -- |
| `mounting-plate` | `TT-MP` | `tt-generic-mounting-plate` |

Dots become `p` and underscores hyphens on the way into a file stem, which is
`slug()` and is how the stems were already written, so `v2.2.5` is `V2P2P5`.

**Then the names were too long.** The owner's verdict on the first set of
them: "The names in #30 are way to long for the tiny tapeout and accessories.
Try to keep them short." A name is its file stem in capitals, so the stems are
what gives. Three changes, none of them to the rule above:

| | was | is |
|---|---|---|
| a demo board sheet covering several revisions | every revision, and every board name with it: `tt-demo-board-tt123-v2p2p5-tt123-v2p2p6` | the first revision and the last, a shared board name once: `tt-demo-board-tt123-v2p2p5-v2p2p6` |
| an accessory sheet | a vendor the sheet already names: `digilent-pmod-hat-adapter`, `waveshare-poe-usbc` | what the part is: `pmod-hat`, `poe-usbc` |
| the mounting plate's lead | `tt-generic-mounting`, so every name said PLATE | `tt-generic-mounting-plate`, which `TT-MP` is |

The demo board stems are a range because the revisions are already in order,
so the end points say which. It gives up saying that v1.2.2 is on the sheet
between v1.2.1 and v1.2.3 -- the sheet's title, subtitle and notes still list
every revision and shuttle it covers, in full, and those are what a reader of
the drawing has in front of them, where the file name is what somebody types.
`TT-DB-TT123-V2P2P5-V2P2P6` is 50.25 mm against 61.75, and said `TT123` once.

The accessory stems say what the part is, and leave the vendor and the part
number to the title block, which carries both: "Waveshare PoE Splitter 25 W,
Type-C" over "POE-SPLITTER-25W-TYPE-C". `ACC_STEMS` in `tools/layout.py` maps
each part key to its stem and refuses a part that has no row. What the stem
drops is not the same thing in each row, and it is worth being exact, because
two of the four keys carry no vendor at all:

| part key | stem | what went |
|---|---|---|
| `pmod-hat-adapter` | `pmod-hat` | `-adapter`, from the key. The old file was `digilent-pmod-hat-adapter`: the vendor was never in the key, it was written in front of it by hand when the file was named, and that is where `ACC-DIGILENT-PMOD-HAT-ADAPTER` came from |
| `waveshare-poe-usbc` | `poe-usbc` | the vendor, which this key does carry, because the data is a catalogue of things somebody has to buy and that is what they buy |
| `generic-poe-microusb` | `poe-microusb` | `generic-`, which says only that no vendor is authoritative -- a fact the sheet's notes state properly |
| `raspmod` | `raspmod` | nothing; the key is already what the thing is called |

`ACC-DIGILENT-PMOD-HAT-ADAPTER` at 60.84 mm becomes `ACC-PMOD-HAT` at 26.95.

The plate's lead is the other direction: it moved out one word rather than in.
See below -- the file stems did not change, only what the prefix accounts for.

**Where the mounting plate's lead stops.** It takes the whole of
`tt-generic-mounting-plate`, which leaves the plate's own fabrication drawing
with nothing at all -- and that is a case the rule now has an answer for,
arrived at the long way round.

The first attempt took the whole lead too, and handed the plate's own sheet
back the bare prefix, `TT-MP`. Three things were wrong with that, all of them
found in review:

- `TT-MP` is a substring of `TT-MP-FITTING-GUIDE`, so a check asking "does
  this sheet carry its own name" could be satisfied by the sheet's *note*
  citing the fitting guide. Deleting the title block's text element from the
  plate SVG and re-running the check proved it: the check still passed.
- "Work from the coordinates on TT-MP" reads as a pointer at the family, which
  is four drawings, not at the one that governs every dimension.
- The issue's own worked example was `TT-MP-PLATE`.

So the lead was shortened to `tt-generic-mounting`, one word, and every name
in the family said PLATE: `TT-MP-PLATE`, `TT-MP-PLATE-FITTING-GUIDE`,
`TT-MP-PLATE-DRILL-TEMPLATE`, `TT-MP-PLATE-CHASSIS-DRILL-TEMPLATE`. That
answered the review and made the names longer, and PLATE on the last three
said nothing `TT-MP` had not: this family *is* the plate and three satellites.

The lead goes back to the whole stem, and the rule gains its one general case
instead. **When stripping the lead leaves nothing, the name takes the lead's
last word**, so the sheet whose stem is exactly its family's lead is named for
what it is: `TT-MP-PLATE`, with `TT-MP-FITTING-GUIDE`, `TT-MP-DRILL-TEMPLATE`
and `TT-MP-CHASSIS-DRILL-TEMPLATE` beside it. It is not special pleading for
this family. A family named after its principal sheet is an ordinary shape,
and the reason not to hand back the bare prefix is general too: a name that is
a prefix of its siblings' names cannot be told from them by any test that
reads a sheet, which is exactly how `TT-MP` made the carry check vacuous. The
rule produces no such name, and `drawing_name`'s docstring says that is why.

The file stems do not change, so nothing on disk moves: the four files are
still `tt-generic-mounting-plate*`, and so is the DXF cut file, which the
fabrication drawing cites by name and something outside this repository may
link to.

`TT-MP-CHASSIS-DRILL-TEMPLATE` is then the longest name in the set at
**56.43 mm**, ahead of `TT-DB-TT123-V2P2P5-V2P2P6` at 50.25 mm -- the longest
name the demo boards ever carried, and superseded below -- and it fits
the 79.30 mm cell with 23 mm to spare. It fits the drill templates' split
header line too, which now leaves both titles at 3.5 mm.

The whole set, 21 sheets, against the numbers they carried before this branch
and each set of names they have carried on it. The `now` column is the rule
in the section below this one, which is where the demo boards and the
accessories stopped being named for their stems at all; the file column has
not moved since the stems were shortened, and does not move again.

| numbered | named for the stem | stem shortened | now | file |
|---|---|---|---|---|
| `TT-DB-01` | `TT-DB-TT123-V2P2P5-TT123-V2P2P6` | `TT-DB-TT123-V2P2P5-V2P2P6` | `TT-DB-TT123` | `tinytapeout/output/tt-demo-board-tt123-v2p2p5-v2p2p6` |
| `TT-DB-02` | `TT-DB-V1P2P1-V1P2P2-V1P2P3` | `TT-DB-V1P2P1-V1P2P3` | `TT-DB-V121` | `tinytapeout/output/tt-demo-board-v1p2p1-v1p2p3` |
| `TT-DB-03` | `TT-DB-V2P0P1-V2P1P0` | `TT-DB-V2P0P1-V2P1P0` | `TT-DB-V201` | `tinytapeout/output/tt-demo-board-v2p0p1-v2p1p0` |
| `TT-DB-04` | `TT-DB-V2P1P2` | `TT-DB-V2P1P2` | `TT-DB-V212` | `tinytapeout/output/tt-demo-board-v2p1p2` |
| `TT-DB-05` | `TT-DB-V3P2` | `TT-DB-V3P2` | `TT-DB-V32` | `tinytapeout/output/tt-demo-board-v3p2` |
| `TT-DB-06` | `TT-DB-V3P3` | `TT-DB-V3P3` | `TT-DB-V33` | `tinytapeout/output/tt-demo-board-v3p3` |
| `RPI-01` | `RPI-3B` | `RPI-3B` | `RPI-3B` | `raspberry_pi/output/rpi3b` |
| `RPI-02` | `RPI-4B` | `RPI-4B` | `RPI-4B` | `raspberry_pi/output/rpi4b` |
| `RPI-03` | `RPI-5` | `RPI-5` | `RPI-5` | `raspberry_pi/output/rpi5` |
| `FPGA-01` | `FPGA-ARTY-A7` | `FPGA-ARTY-A7` | `FPGA-ARTY-A7` | `fpga/output/arty-a7` |
| `FPGA-02` | `FPGA-ULX3S` | `FPGA-ULX3S` | `FPGA-ULX3S` | `fpga/output/ulx3s` |
| `FPGA-03` | `FPGA-PYNQ-Z2` | `FPGA-PYNQ-Z2` | `FPGA-PYNQ-Z2` | `fpga/output/pynq-z2` |
| `FPGA-04` | `FPGA-BUTTERSTICK` | `FPGA-BUTTERSTICK` | `FPGA-BUTTERSTICK` | `fpga/output/butterstick` |
| `ACC-01` | `ACC-DIGILENT-PMOD-HAT-ADAPTER` | `ACC-PMOD-HAT` | `ACC-HAT-PMOD` | `accessories/output/pmod-hat` |
| `ACC-02` | `ACC-WAVESHARE-POE-USBC` | `ACC-POE-USBC` | `ACC-POE-USBC` | `accessories/output/poe-usbc` |
| `ACC-03` | `ACC-GENERIC-POE-MICROUSB` | `ACC-POE-MICROUSB` | `ACC-POE-MUSB` | `accessories/output/poe-microusb` |
| `ACC-04` | `ACC-RASPMOD` | `ACC-RASPMOD` | `ACC-HAT-RMOD` | `accessories/output/raspmod` |
| `TT-MP-01` | `TT-MP-PLATE` | `TT-MP-PLATE` | `TT-MP-PLATE` | `tinytapeout/mounting_plate/output/tt-generic-mounting-plate` |
| `TT-MP-02` | `TT-MP-PLATE-FITTING-GUIDE` | `TT-MP-FITTING-GUIDE` | `TT-MP-FITTING-GUIDE` | `…/tt-generic-mounting-plate-fitting-guide` |
| `TT-MP-03` | `TT-MP-PLATE-DRILL-TEMPLATE` | `TT-MP-DRILL-TEMPLATE` | `TT-MP-DRILL-TEMPLATE` | `…/tt-generic-mounting-plate-drill-template` |
| `TT-MP-04` | `TT-MP-PLATE-CHASSIS-DRILL-TEMPLATE` | `TT-MP-CHASSIS-DRILL-TEMPLATE` | `TT-MP-CHASSIS-DRILL-TEMPLATE` | `…/tt-generic-mounting-plate-chassis-drill-template` |

**Why the file stem and not something shorter.** The argument for it is not
brevity, it is that a collision needs nobody's attention. Two sheets in a
family can only collide if their stems differ by something `slug()` and
`upper()` throw away -- `rpi5`, `rpi-5` and `rpi_5` all give `RPI-5` -- so it
is very nearly the file system's guarantee but not quite, which is why
`check_sheets.py` checks for duplicates rather than assuming there can be
none. The name and the path also convert into each other by hand, so a
reference to `FPGA-PYNQ-Z2` tells a reader where to find it. The alternatives
all gave that up:

- **A per-sheet name declared in the data**, beside the title. Collision-free
  in the same way, but it is a second string to keep in step with the file
  name, and nothing would notice the two disagreeing.
- **The board's title, slugged** -- `TT-DB-DB-ETR-V3P3` from "DB ETR v3.3".
  The titles carry spaces, slashes and, on the merged sheets, the whole list
  of revisions joined by " / ". Slugging them is a second naming rule.
- **The first revision only on a merged sheet** -- `TT-DB-V1P2P1` for the
  sheet covering v1.2.1, v1.2.2 and v1.2.3. Shorter still than the range that
  was chosen, and rejected for the same reason the full list was: it says
  where the sheet starts and nothing about where it stops, so two sheets that
  differ only in how far they run would be told apart by neither. The range
  keeps both end points, and the stem still matches the file, which is the
  property being bought. A revision joining a group renames one sheet; that is
  a real drawing change, it changes the sheet's title too, and one rename on a
  branch that is already re-rendering that sheet is not the problem this is
  fixing.
- **Restoring the dots** -- `TT-DB-V2.2.5`. Not reversible: `p` for a dot can
  be undone only where no literal `p` occurs, and `pynq-z2` has two.

**The title block had to grow.** The DRAWING NO cell was a quarter of the
165 mm title block, 41.25 mm wide with 38.05 mm of room inside it. Measured
with the drafting library's own font metrics at the ISO 3098 minimum, 2.5 mm
capitals in DejaVu Sans Condensed Bold, nine of the first 21 names overran it,
and seven of those were on the nineteen sheets that have a title block for a
name to overrun: the longest of the seven, `TT-DB-TT123-V2P2P5-TT123-V2P2P6`,
needed 61.75 mm and `ACC-DIGILENT-PMOD-HAT-ADAPTER` 60.84 mm. (The two over
it with no title block were the drill templates, whose
`TT-MP-PLATE-CHASSIS-DRILL-TEMPLATE` was the widest name of all at 68.27 mm
and had nothing to overrun. "Eight" was recorded here and in the comment on
`ROW_FRACS`, and is neither figure.) So the second row of the title block
no longer splits into four quarters: SIZE, SHEET and REV hold a sheet size, a
page count and a revision letter and never needed a quarter each, and the row
is now 0.14 / 0.20 / 0.50 / 0.16, which gives DRAWING NO an 82.5 mm cell with
79.3 mm of room. Sideways rather than by adding a row: the title block's
height comes out of the notes band and the view, and an A3 holds the tallest
demo board at 1:1 with nothing to spare. VERSION keeps its quarter and its
38.05 mm, which is the figure `reproducible.py`'s one-character dirty mark is
sized against.

The row stayed that way when the stems were shortened, because three of the 19
sheets with a title block still overran the old quarter, and it stays that way
now that nothing does. The widest name on a sheet that has a title block is
`TT-MP-FITTING-GUIDE` at 37.56 mm, which clears 38.05 mm by half a
millimetre, and half a millimetre is not a margin: the mounting plate and the
FPGA sheets are named for their file stems, which nobody is keeping short for
this, and `FPGA-ARTY-ETHERNET-LIGHT-PIPE`, waiting on another branch, is
58.03 mm. The widest name in this set is `TT-MP-CHASSIS-DRILL-TEMPLATE` at
56.43 mm, on a drill template, which has no title block to overrun. Restoring
the quarter would also re-render all 19 sheets to buy a field nothing wants.

The drill templates have no title block. Their header line carried the drawing
number, the version, the page size and the scale, right-aligned, beside a
title that shrank to fit whatever was left. While the number was eight
characters that line was not tight at all: `TT-MP-03` with the version left
**91.93 mm** for the plate template's title, which needs 70.25 mm at the ISO
floor, and the same for the chassis title's 52.57 mm. The names are what broke
it. `TT-MP-PLATE-DRILL-TEMPLATE` on that line left **59.97 mm** for that
70.25 mm title, and the chassis 45.49 mm for 52.57 mm: both short, the plate
by more.

So the line is split -- what the sheet is, with the page size and scale, on
the title line; what it was drawn from under it -- which costs no height and
leaves both titles at a proper size rather than the floor.

The shorter names would very nearly fit on one line again -- and "very nearly"
is as precise as that can be put, because the figure is not a constant. The
version on that line is `git describe`, whose abbreviated hash is as long as
it has to be to stay unique and whose characters are not all the same width,
so the room left for the plate template's **70.25 mm** title moves from commit
to commit. Across the 29 version strings this branch's sheets have carried it
runs from **70.41 mm** to **72.24 mm**: a margin of **0.16 mm** at worst,
2.00 mm at best, and 0.98 mm on the version these sheets went out with.

Nothing that thin survives. The commit count reaching four digits costs
**1.96 mm** by itself, more than the margin for every one of those strings but
the most fortunate hash, where it leaves 0.03 mm; the dirty mark on an
uncommitted render costs 2.59 mm and takes all of them. The header would be
right in the repository and wrong on the next commit, which is the shape of
the "69.2 against 70.2" quoted here before and withdrawn. So the line stays
split. The split title line carries no version, so its room does not move:
**104.80 mm** beside `TT-MP-DRILL-TEMPLATE` and **90.32 mm** beside
`TT-MP-CHASSIS-DRILL-TEMPLATE`, and both titles are set at 3.5 mm where one
line would put both at the 2.5 mm floor. The plate template's title is a
millimetre taller than it was, which is the visible part of the change.

Two things were said about this before and were wrong. The figure quoted was
"69.2 mm for a title needing 70.2 mm", which is only reachable from a render
with uncommitted source, where the version carries its `+`; no committed sheet
ever had it. And the sheet named as the tight one was the chassis, when it is
the plate: the plate template has the long title.

The defect worth recording is the one that would have shipped in silence.
`fit_size` returns the ISO floor when nothing on its ladder fits, so the old
line would have drawn the title straight through the stamp rather than
refusing. `_fit_beside` refuses. It is *not* a face mismatch -- `fit_size`
defaults to sans bold and the title is drawn sans bold -- but the two faces
are far enough apart that measuring in the wrong one would be invisible until
it printed: "DRILL TEMPLATE - MOUNTING PLATE" at the 2.5 mm floor is 70.25 mm
in sans bold and 56.21 mm in condensed regular, so `_fit_beside` passes the
face and weight through to both calls instead of leaving them to two different
sets of defaults.

**What now catches this.** `check_sheets.py` derives every sheet's name and
then reads the sheet back: it finds the DRAWING NO cell by its own label,
measures the cell between the rules that were actually drawn -- 79.30 mm on
all nineteen sheets that have one, so a family overriding the column width
could not slip past -- and reports separately if the name does not fit and if
the cell does not say it. Reading the cell rather than searching the file is
what stops a note citing another drawing from standing in for the title block,
which is exactly what `TT-MP` did; a sheet doctored to read `FPGA-01` in the
cell while a note says `FPGA-ARTY-A7` now fails, where a substring test
passed. With the cell put back to a quarter of the block it reported seven
sheets over, 38.74 to 61.75 mm of name in 38.05 mm of cell, and three with the
names shortened. Seven and not the nine names that were over the quarter,
because a sheet with no title block has no cell to measure and this check
passes over it; the range quoted was always the seven's.

It also reports a name that is a *prefix* of another sheet's, which is the
property `drawing_name`'s docstring argues for and nothing enforced. Two such
names are distinct strings, so the duplicate test passes them, and nothing
that quotes the shorter one can be read unambiguously. The hole the bare
`TT-MP` opened is closed by reading the cell, but the rule is general and
`tt_name` keeps it reachable: it takes the `p` separators out, so a `v3p2`
sheet is `V32` and a `v3p2p1` sheet would be `V321`, which begins with it.
Checked on a synthetic pair rather than argued: two sheets named `TT-MP` and
`TT-MP-FITTING-GUIDE`, each carrying its own name and neither a duplicate,
produce exactly one problem, and `TT-DB-V32` beside `TT-DB-V33` produces none.

`check_pdfs.py` had never read a bound copy at all, which the note above on
reproducing the set on a second machine says outright; it now matches every
page of every bundle against the committed sheet PDFs by content stream and
requires the bookmark to open with that page's drawing name.

## A drawing number is not a file name

The owner read the shortened names and said they were still far too long:
"They should be at most TT-DB-<4-5 characters> and ACC-{HAT,POE}-<4-5
characters>." Everything above this heading answered "the names are too long"
by shortening the stems, because the name *was* the stem in capitals. There
was nothing left to take out of the stems, and that was the wrong place to
look anyway.

**The two are read by different people for different reasons.** A file name is
read once, from a directory listing, by somebody choosing between files: both
end points of a revision range are worth the characters there, and so is
`poe-microusb` rather than a code. A drawing number is read off a title block,
quoted in a note on another sheet, written on an order, typed into a
spreadsheet and said out loud across a workshop; it has to be taken in at a
glance and copied without a slip, and four or five characters behind the
prefix is what that costs. So this time the stems do not move at all. Every
README link, every preview `<img>`, every bound copy's page order and every
other branch that cites a file keeps working, and the only thing that changes
is the string in the DRAWING NO cell.

**The rule.** `drawing_name` strips the family's lead as before, and then, if
the family has a row in a new `FAMILY_NAME_RULES` table, replaces what is left
with what that rule makes of it. A separate table and not a third column of
`FAMILY_PREFIXES`: several branches are open at once, each adding a row to
that table, and changing its shape would conflict with every one of them,
where a new table beside it conflicts with nothing. A rule takes the stem and
nothing else, because `drawing_name_for` has to answer from a rendered
sheet's path alone -- the checks and the bundle bookmarks all go through it.

Three families have no rule and are untouched: `RPI-3B`, `FPGA-ARTY-A7`,
`TT-MP-PLATE` and the rest are already as short as those sheets can honestly
be said to be, and a table of names for them would be a second string to keep
in step with the files.

**`tt_name`.** The rest of a demo board stem is words: a board name first if
the revisions carry one, then the revisions. If the first word is not a
revision it is the name -- `tt123-v2p2p5-v2p2p6` gives `TT123` -- and
otherwise the name is the first revision with its `p` separators taken out.
The six sheets:

| file | name |
|---|---|
| `tt-demo-board-tt123-v2p2p5-v2p2p6` | `TT-DB-TT123` |
| `tt-demo-board-v1p2p1-v1p2p3` | `TT-DB-V121` |
| `tt-demo-board-v2p0p1-v2p1p0` | `TT-DB-V201` |
| `tt-demo-board-v2p1p2` | `TT-DB-V212` |
| `tt-demo-board-v3p2` | `TT-DB-V32` |
| `tt-demo-board-v3p3` | `TT-DB-V33` |

Naming a sheet after one of the revisions on it is exact rather than
approximate. A sheet covers one geometry -- the generator compares outline,
holes, hosts and every feature before it merges two revisions -- and the first
revision to carry that geometry is where it came from: v1.2.2 and v1.2.3 are
on `TT-DB-V121` because mechanically they *are* the v1.2.1 board. The title,
the subtitle and the notes still list every revision and every shuttle, which
is what a reader with the drawing in front of them has.

**A revision may be lettered, and the pattern has to say so.** The 4+ sheet's
own title is "DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c", so a lettered
revision is not a hypothetical in this data, it is already on a drawing; it
simply has not been the *first* revision of a sheet yet. A pattern of
`v\d+(?:p\d+)*` does not match `v1p2p2c`, and the failure would be silent
rather than loud: an unmatched first word is taken for a board name and passed
through whole, so the sheet would quietly be called `TT-DB-V1P2P2C` -- a
stem-shaped name, which is the one thing this rule exists to prevent. The
pattern takes an optional trailing letter, and keeps it: `V122C`. The number
and the letter are separate groups so the `p` separators come out of the
number alone, which costs nothing and means a revision whose letter is `p`
does not lose it.

**This reverses a decision recorded above, and it is worth saying which.**
"The first revision only on a merged sheet" is listed there among the
alternatives rejected, because it says where a sheet starts and nothing about
where it stops. That is a file name's job and the reason still holds for the
file name, which keeps the range. It was never an argument about the drawing
number, and as a drawing number the objection does not apply: two sheets
cannot start at one revision, because a revision is on exactly one sheet, and
the number is not what anybody browses a directory with.

**`ACC_NAMES`.** A table, because the accessory stems are words and not codes
and no mechanical shortening of `raspmod` leaves four characters that still
say which board it is. Keyed by the stem rather than the part key, so it
answers from a rendered file the way `tt_name` does, and a stem with no row is
a `SystemExit` naming the table, as `acc_stem` already was for a part with no
stem.

| file | name | |
|---|---|---|
| `pmod-hat` | `ACC-HAT-PMOD` | Digilent's Pmod HAT Adapter |
| `raspmod` | `ACC-HAT-RMOD` | the Raspmod |
| `poe-usbc` | `ACC-POE-USBC` | Waveshare's splitter, Type-C out |
| `poe-microusb` | `ACC-POE-MUSB` | the generic splitter, micro-USB out |

The first word is the kind and the second which one of it, so two names quoted
in one note show which two parts are alternatives to each other. `HAT` is
Digilent's own word for the adapter that sits on the Pi's 40-pin header. The
Raspmod is filed under it as the other way of getting Pmod ports onto a Pi and
is *not* a HAT: it does not sit on the header, it uses the ID EEPROM pins for
a switch and a clock, and `raspmod-vs-pmod-hat.md` is largely about the
difference. The name says what shelf the drawing is on, not what the part
conforms to, and all three documents that carry the name say so outright
rather than leaving a reader to find the contradiction.

**Nothing else had to move.** The names are between 9 and 12 characters and
between 17.69 mm (`TT-DB-V32`, `TT-DB-V33`) and 26.70 mm (`ACC-POE-MUSB`) at
the ISO 3098 floor, against the 79.30 mm the DRAWING NO cell has, so no cell,
no header line and no title block proportion changes. No new name is a prefix
of a sibling's, which is the property `drawing_name`'s docstring explains and
`TT-MP` once broke; `TT-DB-V32` and `TT-DB-V33` are the closest pair in the
set and neither contains the other. The widest name with a title block is now
`TT-MP-FITTING-GUIDE` at 37.56 mm, from a family with no rule.

**The entries above this one keep the numbers the sheets carried when they
were written.** They are a log of what happened on a date, not references to
resolve, and rewriting them would make the record say something that was not
true at the time.

## The mounting plate's four, one word each

The owner read the set once more and asked for the mounting plate's three
satellites to be "something like `TT-MP-FIT`, `TT-MP-DRILL`, `TT-MP-CHASSIS`"
(18 September 2026). The entry above had left that family with no rule on the
grounds that `TT-MP-PLATE` and the rest "are already as short as those sheets
can honestly be said to be" -- which was true of the plate and not of
`TT-MP-CHASSIS-DRILL-TEMPLATE`, whose 56.43 mm made it the widest name in the
set by 22 mm. What is left of those stems once `TT-MP` has said
`tt-generic-mounting-plate` is a title (`fitting-guide`,
`chassis-drill-template`), and the sheet carries its title in full already.

**A table, like the accessories.** `PLATE_NAMES` in `tools/layout.py` is
keyed by the four stems, built from `PLATE_STEM`, `FITTING_GUIDE_STEM` and
`DRILL_TEMPLATE_STEMS` rather than retyped, and gives one word each: `plate`,
`fit`, `drill`, `chassis`. `plate_name` is the family's row in
`FAMILY_NAME_RULES`. Because a rule is handed what is left after the lead is
stripped, and the plate's own stem is the lead entire, the stripping moved out
of `drawing_name` into `strip_lead`, which both sides of the lookup go
through: the keys of the table and the stem being asked about are cut the
same way, and the sheet whose stem is the lead is the one they would have
disagreed about. `TT-MP-PLATE` is unchanged.

| stem | was | is | width |
|---|---|---|---|
| `tt-generic-mounting-plate` | `TT-MP-PLATE` | `TT-MP-PLATE` | 22.18 mm |
| `…-fitting-guide` | `TT-MP-FITTING-GUIDE` | `TT-MP-FIT` | 16.98 mm |
| `…-drill-template` | `TT-MP-DRILL-TEMPLATE` | `TT-MP-DRILL` | 21.63 mm |
| `…-chassis-drill-template` | `TT-MP-CHASSIS-DRILL-TEMPLATE` | `TT-MP-CHASSIS` | 26.51 mm |

**Measured again.** Every name in the set at the ISO 3098 floor, bold: the
widest is now `FPGA-BUTTERSTICK` at 34.33 mm, and every one of the nineteen
names on a sheet with a title block clears the 38.05 mm a quarter-width
DRAWING NO cell had, the closest by 3.72 mm where `TT-MP-FITTING-GUIDE` had
cleared it by 0.49. The half cell (79.30 mm) stays all the same:
`FPGA-ARTY-ETHERNET-LIGHT-PIPE` on the light pipe branch is 58.03 mm, and a
quarter's clearance has been of the half-millimetre class within this branch
already. The `ROW_FRACS` comment and the `check_drawing_names` docstring say
so with these figures.

**The drill template header.** The split of the templates' header into a
title line and a version line was justified above by fit: one line beside
`TT-MP-DRILL-TEMPLATE` and a `git describe` string left the plate's 70.25 mm
title a margin of 0.16 mm at worst. Beside `TT-MP-DRILL` one line would leave
86.99 mm, a margin of 16.74 mm, still 8.51 mm with the dirty mark -- so the
fit no longer decides it. The split stays for the type size: one line sets
the plate's title at the 2.5 mm floor, the split line at 3.5 mm. The split
title line now has 121.37 mm beside `TT-MP-DRILL` and 116.86 mm beside
`TT-MP-CHASSIS`. Fitted one sheet at a time, as before, the plate's title
stayed at 3.5 mm and the chassis's, 52.57 mm at the floor, took the 5.0 mm
rung its shorter name left room for, and the two templates that are printed
and used together came out with headers a size apart. So the header sizes
are now one pair for the family, `_header_sizes`: each line at the largest
rung every template's string fits at beside its own right-hand end, which is
3.5 mm for the titles and the 2.5 mm floor for the subtitles. The refusal to
draw a title through its neighbour is still made per sheet.

**Everything that quoted the names.** `README.md` ("What a sheet is called"
gains the third rule), `tinytapeout/mounting_plate/README.md`, `TODO.md`
under "Drill templates", the docstrings in `layout.py`, `check_sheets.py`,
`sheet.py` and `template_sheet.py`. The README grids are regenerated. The
entries above keep the names the sheets carried when they were written.

## The bound copies were outside the net

`check_pdfs.py` walked every committed sheet and said nothing at all about
the three bound copies. That is not an oversight anyone would spot from the
outside, because the walk is over the SVGs: it finds a sheet, renders it, and
compares. A bundle has no SVG. It is the one output in an `output/` directory
with no drawing of its own, so there was nothing for the walk to find it by,
and the check's own summary line -- "N problems across N PDFs" -- counted
the sheets and read as though it had covered everything.

What that cost was a bound copy shipped with three pages re-rendered at a
VERSION stamp no committed sheet carried. The set was green. The bundle was a
PDF of the right size with the right bookmarks, and page 1 is an A3 drawing
whether it is this week's or last week's; the stamp is 3.4 mm of text in the
title block. It was caught by a reviewer extracting content streams and
hashing them by hand, which is not a thing to rely on twice.

So a bundle is now checked against what it claims to be. Page for page, the
bound page's content stream against the staged sheet PDF's -- the content
stream rather than the file, because the same drawing bound into a document
is renumbered and recompressed and only the operators survive intact -- and
the page's MediaBox against the sheet's, because a drawing can come through
whole on a page of the wrong size, which is the same lie as a sheet that does
not print 1:1. Then the page count, the bookmark labels in order and the page
each bookmark actually opens, and an Info dictionary whose key set is exactly
`/Producer`, `/Title` and `/CreationDate`, so that a `/ModDate` or somebody's
`/Creator` is noticed rather than ignored.

One line per defect, not per page it shows up on. A swapped pair of bookmarks
is one mistake, and reporting it as five problems would make the count at the
foot of the run mean nothing, which is what the count meant before any of
this.

The page list had to come from somewhere, and the only place it existed was
inside `generate_diagrams.main()`, as lists accumulated while the sheets were
being rendered -- which meant the one way to learn what belonged in a bundle
was to render the whole set again. Retyping it into the check would have given
the two copies room to drift apart, which is the same shape of bug one level
up. So the bundle definitions moved out into `bundles()`, with
`tt_board_sheets()`, `rpi_sheets()`, `fpga_sheets()` and `plate_sheets()`
under it naming each family's sheets, their drawing names and their paths.
Data only; nothing in there renders or binds, and the check imports it.

`main()` now draws from those same functions rather than building its lists
as it goes, so a sheet's name and the file it is written to are stated once.
Two things confirm the refactor changed nothing: `--no-raster` writes all 21
SVGs with exactly one line different in each, and that line is the title
block's VERSION stamp, which any source commit moves -- the `+` for an
uncommitted working tree, a new describe hash once the commit lands -- and
rebinding all three bundles from `bundles()` over the committed sheet PDFs
gives the committed bundles back byte for byte.

Proved the other way as well, before trusting it. A bad bundle was built
under `tmp/`: `rpi3b.svg` taken from the index, its stamp changed to
`v0.0-9-gdeadbee`, rendered, and bound in front of the committed Pi 4B and
Pi 5 sheets with the real labels and title, so that the only thing wrong with
it was the thing that actually went wrong. One problem, naming the page, the
sheet it should have been and both hashes. Binding that same stale page and
then dropping the Pi 5 sheet gives three: the page count, the stale page, and
a bookmark list two entries long for three pages.

**Where this met the naming change.** #30 landed under this branch and had
written a bound-copy check of its own: the same gap, found from the other
side. The two are one check now, taking the stronger half of each. The page
list is this branch's, `generate_diagrams.bundles()`, so a page is compared
against the sheet that *belongs* in that position rather than against any
sheet in the index, and with it come the MediaBox, the bookmark labels in
order, the page each bookmark opens and the Info key set. From #30 comes
`content_stream()`, which hands back `b""` for a page with nothing on it and
never matches on it: pypdf's `ContentStream` is a dict subclass and an empty
one is falsy, so a comparison written the obvious way would find two empty
streams equal and pass having compared nothing. #30's other rule, that a
bookmark opens with its page's drawing name, is inside the labels already,
because the generator builds every label from that name.

#30's `tools.layout.bundles()` is kept, doing the one thing the generator's
list cannot: it finds the bound copies the way a bundle is defined, a PDF in
an output directory with no SVG beside it, so a bundle that is committed and
that the generator does not bind is reported rather than never looked at.

The proof was run again on the check as it now stands, against the committed
set:

- bound correctly from the committed sheet PDFs: 0 problems. All three
  bundles rebuilt that way are byte for byte the committed ones, at 3035895,
  1302973 and 1544306 bytes, which is the refactor's own receipt as well.
- page 1's content stream lengthened by nine bytes: 1 problem, naming the
  page, the sheet it should have been, both lengths and both hashes.
- bookmark 1 left reading `FPGA-01  Digilent Arty A7  -  A7-35T and
  A7-100T`: 1 problem, quoting what it reads and what it should.
- the ButterStick page dropped: 2 problems, the page count and a bookmark
  list three entries long for four pages.
- page 1 replaced by a blank page: 1 problem, page 1 has no content stream
  to compare against `fpga/output/arty-a7.pdf`. That is #30's guard, on this
  branch's comparison, catching the case neither branch's check would have
  reported as anything worse than agreement.

**Three things the review found.** A missing Info key was counted twice: once
by the key-set line and again by the value comparison beneath it, reading
`/Title is None, not ...`. That is the one-line-per-defect rule broken by the
check that wrote it, and `meta.get` is how -- an absent key and a wrong value
look the same through it. The value comparisons ask only whether what is
*there* is right; an absent one is the key-set line's to report, and a bundle
with no `/Title` is 1 problem where it was 2.

`unbound_copies` called a stray it had found on disk "committed", but
`tools.layout.bundles()` globs the working tree, where a PDF may be nothing
but litter the next `make clean` takes away. It reports only what is in the
index as well now, like every other line in the file, so an untracked stray
is silent and a staged one is named. The gap that leaves -- a bundle deleted
from the working tree but still staged -- is in neither list and is what `git
status` is for; that is said in the docstring rather than left to be found.

And a truncated or empty bundle raised out of `PdfReader` before any of this
ran, so `make check` stack-traced: no problem count, and nothing said about
the two bundles after it. Reading a file that is not a PDF is exactly what
this check is for, so it is one problem now, quoting the size and what pypdf
said -- 4096 bytes of a real bundle gives `PdfStreamError: Stream has ended
unexpectedly`, and an empty file `EmptyFileError`.

## Why the Sheets column read TT-DB- on one line and 01 on the next

A screenshot of the front page's "What is here" table, taken while the sheets
were still numbered: the middle column broke every sheet number in half,
`TT-DB-` above and `01`..`06` below.  Nothing in the Markdown asked for it.
GitHub lays a table out as `width: max-content; max-width: 100%`, and this
table's natural width is wider than the README column it sits in -- 838 px in
a 1440 px window, 582 px in a 1024 px one -- so the browser gives each column
something between its smallest and its natural width.  A hyphen is a break
opportunity, so the smallest `TT-DB-01` could be was the width of `TT-DB-`,
and the third column, carrying up to 161 characters of Markdown, 123 of them
rendered text, was worth more to the auto layout than the middle column's last
twenty pixels.

Measured rather than guessed: on the published page the `TT-DB-01` code span
came back 45 px tall, two lines, with the `06` beside it sitting 24 px lower.

Three fixes were rendered through GitHub's own `/markdown` API and each
swapped into the live README's DOM, so the stylesheet and the column width
doing the measuring were GitHub's:

- **Shorter descriptions** in the third column.  Cut to about 50 characters
  each, the identifiers still broke.  It moves the window width at which the
  squeeze starts; it does not remove the squeeze.
- **Non-breaking hyphens**, U+2011, inside the code spans.  The character
  itself survives the pipeline -- it is `&nbsp;` and friends that do not,
  because entities are not decoded inside backticks -- and the break goes
  away at both widths.  Rejected anyway: it puts a character in the sheet
  identifiers that no file name, no title block and no `grep` for one
  contains, in aid of a rendering problem.
- **Two columns**, the identifier leading the description.  Every one of them
  stays on one line at both widths, because it is now at the start of a wide
  cell and the wrapping lands on the prose after it.

The last is what the README has.

**Measured again once the numbers were names.**  Everything above was measured
while the column held `TT-DB-01`..`06` and its four neighbours.  It now holds
a family glob -- `TT-DB-*`, `TT-MP-*`, `RPI-*`, `FPGA-*`, `ACC-*` -- so the
same three tables were rendered and swapped in a second time rather than
assuming the squeeze had survived the rename.  It has: the three-column table
still breaks `TT-DB-*` across two lines at a 567 px README column, and the
two-column table keeps all five globs whole, one 20 px line each, at 567 px
and at 838.  A glob leaves as many hyphens to break at as the number it
replaced, so the fix is needed rather than made redundant, and it is the same
fix, unchanged apart from what the cells say.

(The README column measures 567 px in a 1024 px window today against the
582 px recorded above.  Same window, same page; GitHub's own furniture around
the column has moved in between.)

The family READMEs name their sheets, where they name them at all, inside
the description rather than in a column of their own, except the mounting
plate's, which keeps a Sheet column of four.  Measured the same way while the
sheets were still numbered, none of them broke a sheet number; with the names,
`FPGA-BUTTERSTICK` comes back in two pieces at a 605 px body width and whole
at 838, and the plate's Sheet column has not been re-measured since its names
were shortened.  That is this same squeeze turning up somewhere else, on
tables this branch does not touch; it is noted here rather than fixed here.

## The Arty's ordinate chain, and which edge a chain belongs on

The X ordinate chain went below the view on every sheet, and the overall
width went above it, because that is where a drafter puts them and because
the first boards drawn here had their Pmod hosts and most of their holes
along the bottom edge. The Arty A7 has neither. Its four Pmod hosts sit
11.75 mm from the TOP edge, and it has no mounting holes at all, so every
value in the chain belonged to a feature at the top of the board and every
witness line was drawn 90.88 mm long, the height of the board and then some
to reach a chain underneath; one of the four was broken into four pieces on
the way by the Ethernet jack and both LED rows. Four lines the height of the
drawing, to carry four numbers that describe a strip along the top edge.
Issue #4.

So the chain now goes on the horizontal edge its own features are nearest.
Every feature that puts a value into the chain votes -- each mounting hole,
and each host on a horizontal edge, the phantom HAT's included -- and the
majority wins; a tie keeps the chain below. The overall width goes on the
other edge, and with it go the Pmod spacing dimension's lane, the balloon
bounds, the witness lines' reserved extent, the reserved band for the
overall dimension, and the deeper of the two view margins, so the view
itself shifts ten millimetres down the page to pay for the room.

The votes are counted per feature and not per distinct X, which is the
whole reason only one sheet moves. A board with holes at both edges has an
equal claim from each, and there are three of them: the ULX3S and the
PYNQ-Z2 tie 2-2 on four holes each and the ButterStick 4-4 on eight, and all
three stay where they were. The Raspberry Pi 3B and 4B are 3-2 below -- the
two lower mounting holes and the phantom Pmod HAT Adapter's host JC against
the two upper holes -- and the Pi 5, which carries six holes rather than
four, is 4-3. Both stay below. The demo boards are 4-1, 4-2 or 5-2 below,
the Pmod HAT Adapter 3-2, the Raspmod 3-0. The Arty is 4-0 above. Counting
instead by distinct X, or by summed distance, moves the ULX3S and all three
Pi sheets as well, which is a bigger change than anyone asked for and, on
the ULX3S, the wrong fix: its witness lines are long because
`_ordinate_values` anchors them at the top pair of a symmetric set of four
holes, not because the chain is in the wrong place. That tie-break is a
separate question and was left alone.

Proved rather than assumed: every `<text>` element of all 21 sheets,
attributes and content, compared against the branch this one sits on with the
VERSION stamp masked. Twenty are byte for byte identical and only
`fpga/output/arty-a7.svg` differs, in 14 of its 177 text elements. The same
comparison over the whole file, geometry included, says the same thing. The
sheet is FPGA-ARTY-A7 and no line of this branch says so: the name comes from
the file stem the generator was already writing to.

What the Arty sheet gains, measured rather than eyeballed: each of the four
host witness lines is 27.38 mm where it was 90.88 mm, and all four are now a
single clean run instead of one of them being chopped into four by the parts
it crossed. The zero ordinate's own line is 18.30 mm either way. The 22.80
TYP spacing sits between the hosts and the chain, the 109.00 overall width
sits just under the bottom edge with short extension lines, and the 11.75
pin-field depth still writes its value inboard of its host, which is now the
side away from the chain rather than towards it.

The balloons are a mixed result, and the eye gets it backwards: it reads
balloons 4 and 5 as having moved above their LED rows on shorter leaders, and
neither half of that survives a measurement. Leader lengths, tip to balloon
rim: balloon 1, the micro-USB, 7.80 mm down to 5.80, having dropped
10.6 mm relative to the board to sit level with its connector rather than
above it; balloon 3, the Ethernet jack, 14.30 mm unchanged, barely moved;
balloon 4, LD4-LD7, 5.80 mm unchanged, mirrored 9 mm across its own tip at
exactly the same height, so it did not move vertically at all; and balloon
5, LD0-LD3, 14.30 mm up to 17.80 -- it moved 14.2 mm up and 35.4 mm right,
from below-left of its tip to above-right of it, and paid 3.5 mm of leader
for the room. The whole view sits ten millimetres lower on the page, which
is the swapped margin; the figures above are relative to the board, not to
the sheet.

One interaction this leaves open: the corner-radius callout is drawn five
millimetres above the board, where a top chain's spacing dimension now sits
six millimetres above it. Nothing in the set has both -- the Arty's outline
has no corner radius -- but this is nearer than it sounds, not a
hypothetical for some future board. Twelve of the fifteen board sheets here
carry a corner radius, and the Raspberry Pi 5 is 4-3 below, one mounting
hole away from a top chain. So `render_board` now refuses the combination
outright with a `SystemExit` naming the board and saying what to do: flip
the callout below the board the way the overall width flips, and reserve it
there for the balloon placer too. A collision a reader would notice before a
check does should not be able to go out silently.

## The Icepi Zero, and a board file that was re-annotated after it was sold

Asked for a sheet of cheyao's Icepi Zero, an ECP5 board in the Raspberry Pi
Zero form factor, as a fifth member of the `fpga/` family.  The KiCad sources
are in the repository rather than in a release, under `hardware/v1.0` to
`v1.4-wip`, and the licence is the Solderpad Hardware Licence 2.1.

**Which revision was sold.**  Only `v1.3` is tagged, and its commit is "Final
mass production files"; the maker's JOURNAL.md has v1.0 to v1.2 as the
prototypes he had made in ones and twos and ends with a batch of v1.3 ordered
and Crowd Supply accepting the campaign, and `v1.4-wip` is marked work in
progress.  So the sheet is drawn from `hardware/v1.3/icepi-zero.kicad_pcb` at
the tag, 6e4aaba2.

**What was awkward.**  The same file at the tip of the repository is still
called v1.3 and still has the same board in it -- every outline edge, hole and
component box is identical -- but it has been re-saved in KiCad 10 and
**re-annotated**.  The programming port is J3 in the file the boards were
fabbed from and J5 in the current one; the five user LEDs are D1, D4, D2, D3,
D5 left to right in the first and D1 to D5 in order in the second; the red
FTDI activity LED went from D8 to D14; and the GPIO header's DNP flag was
cleared although the production BOM still leaves it off.  A drawing that named
parts out of either file alone would be wrong about a board someone is holding.

So the extractor reads both commits through one function and requires them to
agree on every position, and nothing in that function is looked up by
designator: the programming port is the receptacle that shares the FT231X's
data pair, a user LED is one a resistor drives from `/LED0` to `/LED4`, the
mounting holes are every drill of 2 mm or more, and the rest are found by
footprint library.  The sheet then carries the mass-production designators and
one note says the current file disagrees and how.  Two smaller things fell out
of reading two KiCad generations: KiCad 10 writes a pad's net as `(net "GND")`
where KiCad 9 wrote `(net 4 "GND")`, so the name is the last atom rather than a
fixed index, and it wrote the same eight outline edges out in a different
order, so the outlines are compared as sets.

**Decisions.**

- *The third USB-C port.*  The board has three identical USB-C receptacles in
  one row on the bottom edge on a 12.50 mm pitch: one to the FT231X for JTAG
  and console, two to the FPGA.  The family's feature numbers are fixed and
  adding one would have put a "not on this board" row on all four existing
  sheets, so the two FPGA ports are one row feature, exactly as a row of LEDs
  is, with the count and the pitch in the label.  There is 1.86 mm of board
  between their courtyards, so the one rectangle overstates the part by a
  sliver rather than by a gap.
- *GPDI and microSD at 7 and 8.*  Numbers 6 to 8 are the family's expansion
  connectors and already mean a different connector on each board.  Leaving
  the video connector and the card socket off the sheet to protect the
  wording of two schedule rows would have been a mechanical drawing missing
  two of the four things a cable or a card goes into.
- *The buttons.*  SW1 and SW2 are on the underside and there was no number
  left for them, so they are in a note with their centres, the way the
  PYNQ-Z2's LEDs are.
- *The Pi Zero comparison.*  Raspberry Pi's own Zero drawing, RPI-ZERO-V1_2,
  has no extractable text, so it was rendered and read: 65 x 30, corner radius
  3.0, 4x M2.5 drilled 2.75 +/-0.05, 58 x 23 apart, 3.5 in from each edge.
  The Icepi matches the outline and the hole pattern exactly, drills 2.70
  (the bottom of the Pi's tolerance band) and rounds its corners R3.50.  Those
  figures are a constant in the extractor, which checks the board against them
  before the note claims the pattern, and the drawing is cited for the
  comparison only.
- *The GPIO header.*  It is not fitted: the production BOM at the tag lists no
  2x20 header, and the tagged board file marks it DNP.  The note says where
  pin 1 of the position is and that the pins sit on the Raspberry Pi 40-pin
  arrangement, which the extractor checks -- 3V3, both 5 V pins, GPIO2, GPIO3
  and all eight grounds in the Pi's places -- before the note is allowed to
  say it.

The board file's stackup sums to 1.6458 mm, which the title block prints as
"PCB, 1.6 nominal"; the README's "1.2mm/1.6mm PCB with JLC04121H-7628 Stackup"
is an ordering option for someone fabbing their own and is not on the sheet.

**What review found.**  The hole schedule printed KEEPOUT 2.70 against a 2.70
drill on all four holes.  `tools/kicad_extract.hole` took the largest pad as
the keep-out whatever it was, which is right for a plated hole -- the pad is
the annular ring a screw head must not touch, and it is where the demo boards'
6.4 against a 3.2 drill comes from -- and wrong for an unplated one, where the
pad is the aperture.  A plate designer reads a keep-out equal to the drill as
no clearance at all, and the sheet was also drawing a phantom circle exactly on
top of each hole and carrying a LEGEND row for linework that never showed.  A
pad no bigger than its drill now reports nothing, and the schedule says "not
given"; regenerating every family's data module changed those four rows and
nothing else.

The rest of that round was the sheet asserting what it had not checked: the
tag was never resolved against the pinned commit, the Pi Zero guard compared
two insets and never the 58 x 23 span, "LED0 at the left-hand end" was taken
on trust, one hole's drill spoke for four, and pin 1 of the GPIO position --
the one thing about that header the boxes cannot catch, since a header turned
end for end keeps its courtyard -- was not compared between the two commits.
Each guard was made to fire on a doctored input before it was kept.  The
README quote was also the wording at the tip rather than at v1.3, where the
sentence begins "Icepi Zero is an FPGA development board" with no "The".

## Cynthion, and four USB ports in a schedule with room for two

Asked for a sheet of the production Cynthion, Great Scott Gadgets' USB test
instrument.  Which revision ships is answered by the repository itself: the
`r1.4.0` release notes read "Initial production release", that tag is the
newest one, it is the tip of `cynthion-hardware`, and nothing committed since
has touched the board file.  CERN-OHL-P v2.  There is no mechanical drawing,
no STEP file, and no board size stated on the product page or in the
documentation's device overview, so `cynthion.kicad_pcb` is the whole source
and every figure on the sheet comes out of it.  The title block is templated -- the board file
says `${TITLE}` and `${VERSION}` -- so the citation reads the project file's
text variables at the same commit rather than taking the revision from the
tag name.

56.00 x 56.00 mm on R3.00, four M2 holes 50 mm apart and 3 mm in from each
edge, a recess in the top edge 1.00 mm deep, flat from x = 41.00 to 47.00 and
ramping 2.00 back to the edge at 39.00 and 49.00, two Pmod hosts on the front
edge on the usual 22.86 mm, a 30-way mezzanine receptacle in the middle of
the component side, six user LEDs the FPGA drives and five status LEDs the
debug microcontroller drives, both rows on 3.00 mm, and no Ethernet.  Nothing
in the repository says what the recess is for, so its `profile_note` gives
the geometry and says as much; the figures are measured off the resolved
outline, which checks the shape as it measures.  The hosts are right-angle
sockets: the pin field is on the board and the housing hangs 8.07 mm off the
front edge, so the fab outline is taken rather than the courtyard -- what a
case has to clear, not what an assembly machine wants free.

**The board file numbers its own Pmod pads**, which neither of the other two
Pmod boards in this family does, so pin 1 could be checked rather than
asserted: `pmod_from_pins` works out where the Pmod convention puts pin 1 and
the extractor then requires the pad the board file calls "1" to be within
0.01 mm of it.  Both hosts agree, on a board whose maker had no reason to
follow this repository's reading of the convention.

Four USB ports -- CONTROL and AUX on the left edge, TARGET C and TARGET A on
the right -- where `FEATURE_ORDER` had `usb_prog` and one `usb_second`.
Renumbering was not available, because a feature number is printed on
balloons and schedules on sheets that are already out, so 9 and 10 were added
at the end for the third and fourth ports and 11 for the status LED row,
which is a second row of LEDs and not the tri-colour row slot 5 means.  The
ports take the slots in the order Great Scott Gadgets' own device overview
introduces them, which is also the order the top-level schematic lists the
port sheets in, so Cynthion's four read 1, 2, 9, 10 and its sheet says why.
The other five FPGA sheets each gained three "not on this board" rows; that
is the whole of their diff, at x >= 243 mm, and no view geometry moved.

One drafting fault, found by `check_sheets.py` and of a kind already on
record: the balloon for the user LEDs landed 0.45 mm from the 3.23 that
dimensions the Pmod pin rows, and the two read as one word.  The pin-field
depth dimension is drawn last of everything and writes its value along its
own lane, and unlike the host spacing dimension beside it -- reserved when
the PYNQ-Z2 arrived -- that lane was never reserved against the balloons.
The lane follows from the drawn parts alone, so it now moves into
`_depth_lanes`, is worked out before the balloons, reserved for position
only, and then drawn from the same answer.  No other sheet moved.

**Found on the way and deliberately not fixed here**: the "assembled
envelope" note counts features but not Pmod host bodies, so wherever a
board's host bodies stand outside its outline the figure is short by that
overhang.  That is seven already-issued sheets, not just the right-angle
ones: the six demo board sheets, whose housings hang off the front edge, and
the PYNQ-Z2, whose hosts reach 1.24 mm past the right edge.  Widening the
computation moves the figure on all seven (TT-DB-V33 goes 86.65 -> 95.20 mm,
the PYNQ-Z2 137.60 -> 138.84 in X), which is a change of its own and not one
to slip in beside a new board.  It is in TODO.md.

Cynthion could not simply wait for it, though, because 58.00 x 56.00 is
8.07 mm short in Y and someone cutting a front panel would believe it.  So
`BoardSpec` grew `envelope_note`, which replaces the computed note when a
board sets it, and the Cynthion extractor works its own figure out over the
features and the host bodies together: 58.00 x 64.07, and 61.00 x 64.07 with
the three side buttons, which are given separately because a reader needs to
be able to take the number apart.  Empty on every other board, so nothing
else moved.

Three things came out of review, all of them the drawing saying something
untrue or nothing at all:

- **J5, the mezzanine.**  Row 6 read "Expansion connector, first - not on
  this board" while the board carries a 30-way surface-mount mezzanine
  receptacle, not marked do-not-populate, in the BOM, drawn on the schematic
  sheet called Expansion Interfaces.  A row that denies a part is worse than
  no row, so it is scheduled; it is a board-to-board socket in the middle of
  the component side rather than an edge port, which the drawing cannot say
  and a note does.  The contact count is counted off the footprint, so the
  label cannot claim a width the part has not got.
- **The recess** was drawn and never explained; `Outline.profile_note` is
  what the demo boards use for their USB-C shell recess and it now carries
  this one.
- **The title-block reader** used `dict.get`, so an upstream rename would
  have printed "None rev None" in the SOURCES line a reader checks to find
  the revision.  TITLE, VERSION and COPYRIGHT are required now, and the
  project file's path comes off `CYNTHION_PATH` instead of being spelled out
  again.

Schedule 11 was renamed "Status LEDs, debug controller" as well.  The name is
printed on the five sheets that do not carry the row, and "driven by the
debug controller" pushed every FPGA feature schedule from 140 to 154 mm wide,
for a row that on five of the six says only that the board has none.

## The camera boards, and two drawings that disagree with themselves

Asked for mechanical diagrams of the Raspberry Pi camera boards. They are a
new family, `raspberry_pi_camera/`, on the repository's own rule that a new
board is a new directory: a 25 x 23.862 mm camera shares nothing with an
85 x 56 mm Pi but the company that made it. Putting them in `raspberry_pi/`
would have meant one `FEATURE_ORDER` covering both, so every Pi sheet would
carry two permanently unused numbers and every camera sheet five; the Pi
sheets are all drawn with the Pmod HAT Adapter overlaid in one shared view
frame, which a 25 mm board would be lost in. The cameras are `RPICAM-2` and
`RPICAM-3`.

**What the family is called.** A sheet's name comes from its own file stem, so
a new family is one row in `FAMILY_PREFIXES` beside the row in `FAMILY_DIRS`
it already needs: `("RPICAM", "cm")`. The stems are the module numbers, `cm2`
and `cm3`, and the prefix already says what kind of module, so the lead comes
off exactly as the Pi family strips `rpi` from `rpi5` to get `RPI-5`;
`RPICAM-CM2` would have said camera twice. `drawing_name` refuses by name when
the row is missing -- it says which family and which file to add it to --
rather than inventing a prefix, so a family registered in one place and
forgotten in the other cannot render. What that leaves for a later sheet in
this family is worth writing down: a stem that does not begin `cm` keeps all
of itself, so an HQ Camera sheet written to `hq.svg` is `RPICAM-HQ` with no
further decision to make.

**What Raspberry Pi actually publish.** Three PDFs and nothing else. The
Camera Module 2 drawing is `RPI-CAM-V2_1`, dated 12/11/2015, drawn by Mike
Stimson and approved by James Adams; the Camera Module 3 standard and wide
drawings are `RP-008153-DS-1` and `RP-008155-DS-1`, on the Product Information
Portal under Camera Module 3 design files. No DXF for any of them. A STEP
model exists for the Camera Module 3 and was not used: the drawing is a true
1:1 plot with a live text layer and already gives everything, and a 10 MB
assembly would only be a second opinion about the same numbers.

**Neither plot is assumed 1:1, and one of them is nowhere near.** The scale is
recovered from the mounting hole rectangle -- 21 mm across, 12.5 mm up, the
lower pair 2 mm in from two edges -- the same way `tools/dump_rpi_pdf.py`
recovers a Pi's from its 58 x 49 pattern, then checked against the dimensions
the drawing prints. Camera Module 3 comes back at **1.0000:1** with the
outline within 0.004 mm. Camera Module 2 comes back at **1.5055:1**: it is
plotted half again bigger than the part, and a sheet that trusted the page
would have drawn a 37.6 x 35.9 mm camera. The Camera Module 2 drawing is also
a quarter turn round, with the 25 mm width running up the page; recovering the
frame from the hole rectangle fixes the rotation as well as the scale, and the
transform is a rotation rather than an axis swap, which would have mirrored a
board whose hole pattern is symmetric enough to hide it.

**Half the Camera Module 2 drawing cannot be read at all.** `page.chars` is
empty: every digit on it is a filled path, so not one printed figure can be
quoted back from the file. Its geometry is machine-read exactly as the other's
is, and the sheet says in a note that its printed dimensions were transcribed
by eye. The Camera Module 3 drawings do carry text, so every figure quoted
from them -- `25`, `23.862`, `12.5`, `14.5`, `14.4`, `10.8`, `8.9`, `ø2.2`,
`ø4.75`, `ø5.75`, `1.12`, `2.75`, `5.71`, `19.61`, `11.3`, `6.98`, `66`, `41`
-- is checked against the file, and a transcription error fails the
extraction.

**Finding a circle drawn as four arcs.** The Camera Module 3 plot emits a
closed path per circle; the Camera Module 2 plot emits four quarter arcs.
Merging arc bounding boxes by proximity does not work, because a hole 2 mm in
from two edges of a board with a 2 mm corner radius is *concentric with the
corner arc*: merged, the two give one blob half again the size of either. A
quarter arc's bounding box is a square with the circle's centre at one of its
corners, so the four quarters of a circle all name that centre and nothing
else names it more than twice. Told apart by radius, the hole and the corner
are two circles, which is what they are.

**The connector is on the underside**, so the Camera Module 3 plan view does
not draw it. It is built instead from the two elevations: the front elevation
gives 19.61 across, the side elevation 5.71 down the board, and both give its
2.75 height, which is required to agree before either is used. The Camera
Module 2 plan does draw it, as two boxes -- the body and the wider latch ears
that reach the board edge -- and the sheet takes the envelope of both, 20.88 x
5.52, against the 20.8 and 5.5 printed beside them. Both boards' bodies
measure 19.61 across, so it is the same part.

**Raspberry Pi's claim, checked.** Their documentation says board dimensions
and mounting-hole positions for Camera Module 3 are identical to Camera Module
2. Each drawing is read on its own and the two patterns compared: they agree
to **0.025 mm**, which is the plot noise of the 1.5:1 source, so the sheets
may repeat the claim. The same documentation says the sensor module changed in
size *and position*; it changed in size, from 8.5 to 10.8 mm square, but the
optical axis is at (12.50, 14.40) on one drawing and (12.49, 14.40) on the
other, which is the same place.

**Where the drawings disagree with themselves.** The Camera Module 3
elevations are 1:1 for the board section (1.120 drawn against 1.12 printed)
and for the connector (2.750 against 2.75), but the lens stack is drawn short:
11.3 printed scales 10.08, 6.98 scales 5.81, and the wide drawing's 12 scales
10.93. The High Quality Camera drawing does it too, `ø30.75` scaling 30.42 and
`ø22.4` scaling 22.25 while its ø2.5 mounting holes scale 2.500 exactly. The
printed figures are the specification and the sheets quote them as printed;
the sheets carry no height dimension, because there is no view on them to hang
one from and the source's own geometry would contradict it.

**Two drafting changes.** A `lens` feature kind, because none of the existing
ones fits a lens and sensor module and the sheets needed one; it draws like any
other component body but also gets a centre mark, since the optical axis is
the point of a camera board and halving two schedule extents is not a way to
find it. And `_pcb_material` no longer calls a thickness a "KiCad stackup sum":
the Camera Module 3's 1.12 is a finished thickness dimensioned on a drawing,
and it is the first board here to reach that branch at all -- every other
thickness in the repository is within 0.05 mm of nominal 1.6.

**Notes cut to buy a scale.** Both sheets started at 2:1, which puts a 25 mm
board in the corner of an A3 sheet. 5:1 wants 119.4 mm of view height and the
notes band was leaving 119.0. The cuts were all of prose that explained the
extraction rather than the board -- field-of-view angles, a note repeating what
the legend already says about hidden detail, the descriptive tail on each
source line -- and the two sheets are now drawn at 5:1 on the same frame, so
flipping between them shows the lens module growing and the board standing
still.

**Left out, and said so on the sheet's behalf in the family README.** There is
no official mechanical drawing for the OV5647 Camera Module 1 and there never
was: no Product Information Portal category, nothing ever served under
`datasheets.raspberrypi.com/camera/`, and the archived
`raspberrypi.org/documentation/hardware/camera/mechanical/` directory held the
v2 camera and the HQ camera only. "Around 25 × 24 × 9 mm" in a product table
is not a drawing. The High Quality Camera's drawing does exist,
`RP-008200-DS-1`, and was read -- 38 x 38 outline, four ø2.5 holes 4.04 in from
each corner, the 8.5 sensor square on the board centre, a knurled ø36 C/CS
mount over an ø22.4 aperture, a tripod boss 13.86 across reaching 11.35 below
the lower edge -- but it has no sheet: `render_board` draws every feature as a
rectangle and a ø36 knurled ring drawn square is a worse drawing than none,
and the drawing never locates the FFC connector in plan at all.

## The Camera Module v1.3, drawn without a drawing

Asked for the original camera, the OV5647 board lettered v1.3, which the
camera family had left out because Raspberry Pi never drew it (#39). Nothing
about that has changed: there is still no drawing of theirs. What changed is
finding a source honest about what it is.

**Gert van Loo's sheet.** On 21 May 2013 he posted one page to the forum's
camera board thread "Mechanical data": "As with the raspberry-Pi mechanical
data it is hand measured, accuracy about 0.05 mm no guarantees." It is on
Scribd, which serves it as a page image with the printed figures in a
separate text layer, so both are cached -- the image to measure and the text
to quote from. It is a real drawing, plan and elevation, "scale 5:1", and it
prints nearly everything a mount needs: 25 x 23.9, 0.95 thick, four ø2 holes
at 9.35 and 21.85 from the connector edge and 2 and 23 up, an 8 mm lens
module 5.1 from the connector edge and 5.2 tall, the connector 5.6 deep and
2.8 below.

**The check that makes it usable.** If the Camera Module 2 kept the old hole
pattern, Raspberry Pi drew it after all, on the later board. Measured from
the connector edge, Gert's hand-measured centres agree with Raspberry Pi's
Camera Module 2 drawing to 0.023 mm and the Camera Module 3's to 0.008.
That is the equivalent of the Pmod HAT Adapter's 50.8 mm header: a figure
the measurement was not used to make, landing where it should. Measured from
the far edge they are 0.05 apart instead, because his board is 23.9 and
theirs 23.862, which is why the comparison is taken from the edge both
boards are measured from. His three heights add up to 8.95 against
Raspberry Pi's own "Around 25 × 24 × 9 mm".

**Scaling what it draws and does not dimension.** The connector's length
along the edge, the sensor's flex tail and its height, the steps of the lens
stack. `measure_cm1.py` takes the scale from the two overall dimensions,
which agree on it to 0.02 %, and measures every other printed figure off the
drawing: the worst is 0.09 mm, the lens tip, drawn 5.11 against 5.2 printed.
The first version found the lens module's edges on the one row the dashed
centre line crosses and reported the module 8.81 wide; the check against the
printed 8 caught it. The search windows are in one image's pixels, so the
script refuses any other image by its hash.

**Where the two measurements disagree.** Raspberry Pi Spy measured a Rev 1.3
board with calipers four days earlier, to the half millimetre. It agrees
about the holes and puts the lens module 5.5 from the connector edge where
Gert has 5.1. Neither is wrong in a way that can be found from here: the
same thread says the module is stuck on with adhesive, and nothing locates
it. So 0.4 is the optical axis's error bar, not a disagreement to resolve by
picking a side, and the sheet uses Gert's figure because everything else of
his that can be checked checks out.

**Things that could have been assumed and were not.** The holes are ø2.0:
both measurements say 2 and the Camera Module 2 drawing says 2.2, so this
sheet does not borrow the later board's figure. The corners are square, in
all three drawings and in the photograph. The thickness is 0.95, and the
drafting note that explains a non-standard thickness said it was "within
0.05 mm of no standard finished thickness", which for 0.95 is true only
because 1.0 - 0.95 is a hair over 0.05 in floating point; the note now says
the figure is the source's own. Arducam's B0033 drawing is a clone's and
supplies nothing: it agrees about the holes and prints the lens 10.25 from
the edge.

**Where it lives.** In `raspberry_pi_camera/`, as `v1.py`, beside the
generated `boards.py` rather than in `accessories/parts.py` with the other
hand-measured part: the family is the subject, not the method. The extractor
now ends `boards.py` by importing `CM1` into `BOARDS`, so everything that
walks the family draws it with no second list to keep in step. It shares the
Camera Module 2 and 3 sheets' frame and band, and stays at 5:1.

**What review changed.** A reviewer reading the same sources found the data
claiming more than they support in four places. The connector had been
scheduled as its dashed body, 19.45 long, where the drawing also draws the
connector's face on the board edge running 20.73 -- the latch ears, which the
Camera Module 2 sheet includes in the 20.88 it schedules -- so a holder
built to the body would have fouled the ears; the envelope is scheduled now.
The holes had been given +/-0.1 on a diameter both sources give only as "2";
they carry +/-0.2, which admits the Camera Module 2's 2.2, and Raspberry Pi
Spy's "will accept a 2mm machine screw" turned out to end "according to
various posts and photos I have seen". The lens's +/-0.4 was the spread
between the measurements with nothing for Raspberry Pi Spy reading to the
half millimetre, and is +/-0.65. And a forum post quoted as a second sighting
of the lens's offset from the holes begins "from the drawing it would
appear", so it was Gert's sheet read twice. The height check against "around
9 mm" was held to 0.1 when Raspberry Pi's own table is 0.2 to 0.4 off their
own Camera Module 3 drawings; it is a sanity check at 0.5 now, and says so.

## Where the camera goes: the RPICAM-OVER-* sheets

Issue #7. Sheets saying where an OV5647 camera has to sit above a Tiny
Tapeout mounting plate and a Digilent Arty A7, for a 65 and a 120 degree
lens, framing the whole board and framing just the indicators.

### The decision that shaped everything: the frame does not depend on the lens

The obvious layout is one sheet per lens, which is how the issue is worded.
It is the wrong shape, and working out why decided the rest of the sheet.

A frame footprint -- the rectangle of the subject that ends up in the picture
-- is the **sensor's** aspect ratio, not the lens's. The OV5647 is 2592 x
1944, which is 4:3 exactly, and that is the shape of the file that comes out
whatever is screwed onto the front. So the smallest frame holding a given
target is the same rectangle for both lenses, and the only thing the lens
changes is how far above it the camera goes.

That means a subject has exactly as many rectangles as it has things worth
framing -- two, here -- and both lenses share them. One sheet per subject
with both lenses on it therefore draws each rectangle once; one sheet per lens
would have drawn all of them twice, on two different subjects at two
different scales on one A3 page, and still
sent anyone setting up a rig to the other page to find out what the other
lens does. **One sheet per subject, both lenses in the tables.**

Both come out at 1:1, which is what the rest of the set is.

### No side elevation -- superseded

The issue offers "a side elevation or a table giving the heights". The heights
run from 12.3 to 146.8 mm. An elevation at the plan's own 1:1 would want
another 150 mm of sheet height, which an A3 carrying a 1:1 plan and a notes
band does not have; at any other scale it would be a view beside a 1:1 view,
inviting exactly the measurement it cannot support. A table, and the notes say
what Z is measured from.

That was the wrong way round, and the owner said so: the question is a
height, so the view that shows the height is the primary one and the plan is
the one that can shrink. See "The camera position sheets lead with the
elevations" below.

### Every height fails the focus check, and that is the finding

Raspberry Pi give the Camera Module 1's focus as `Fixed` and its depth of
field as `Approx 1 m to ∞`. The *largest* height on any of these sheets is
146.8 mm, a seventh of that metre; the smallest is 12.3 mm. So a stock Camera
Module OV5647 cannot focus on any of these boards, at either lens, at any of
the framings asked for.

`verify_optics.py` passes while reporting `TOO CLOSE` on every row that has
a published limit. It has to: what is being checked is that the sheet prints the
verdict the arithmetic gives, not that the problem has gone away. The 120
degree lens prints `UNKNOWN` instead, because Arducam publish no near limit
for it at all.

The useful conclusion is a mount decision rather than a drawing one: a rig
built to these sheets needs an adjustable-focus or motorised OV5647.

### The pinhole model is established, not assumed

The one piece of luck in the sources. Raspberry Pi publish a focal length, a
sensor size, a pixel count *and* a field of view, and any two predict the
third -- so the model can be checked instead of asserted.

    2 x atan(2592 x 0.0014 / 2 / 3.60) = 53.496    declared 53.50 +/- 0.13
    2 x atan(1944 x 0.0014 / 2 / 3.60) = 41.413    declared 41.41 +/- 0.11

Four thousandths of a degree on both axes. And it only works against the
**active pixel array**: their own "Sensor image area", 3.76 x 2.74 mm, printed
one row above in the same table, gives 55.149 across and misses by 1.65
degrees. So the declared field of view is the rectilinear angle to the edge of
the array, which is the arithmetic the sheets do. `FOV_CHECK` carries both
rows and `verify_optics.py` requires the array to match and the image area
not to.

### "65 degrees" is the diagonal, and it is the image area's diagonal

Neither Raspberry Pi nor Arducam ever print 65. What they print for the stock
lens is 53.50 x 41.41 and 54 x 41 respectively. The 65 is the diagonal:

    image area:    2 x atan(sqrt(3.76^2 + 2.74^2) / 2 / 3.60) = 65.74
    active array:  2 x atan(sqrt(3.6288^2 + 2.7216^2) / 2 / 3.60) = 64.42

So the marketing figure comes from the rectangle that does *not* reproduce the
declared H and V. Both are on the sheet, and the computation uses the pair the
vendors do print.

### Arducam's 120 x 90 cannot both be right

Superseded: the 120 is the diagonal, and the pair is 96 x 72. See "Both
lenses, and what they really are" below.

On a 4:3 sensor a rectilinear lens has tan(V/2) = tan(H/2) x 3/4. The stock
lens passes: 53.50 implies 41.416 against a declared 41.41. The wide lens does
not: 120 implies 104.82, not 90. Nearly fifteen degrees.

Rather than pick one, the height is taken as the greater of what each declared
angle asks for. On every frame here that is the vertical, so at the height
printed the picture is wider across than the rectangle drawn -- which is the
safe direction, and the sheet says it.

### The margin is five millimetres flat

Not a percentage. What a hand-aimed camera on a stand has to absorb is where
the stand ends up, which is a few millimetres whatever is being framed. Ten
per cent round the Arty's LED row would have been 0.36 mm on the short axis,
which is under the board data's own tolerance and would have been a number
pretending to be a margin.

### The camera may be turned through ninety degrees

The frame is the smaller of the two 4:3 orientations. Every target on the
plate and the Arty is wider than it is tall, so every frame here is
landscape; a target taller than it is wide would put the camera higher
framed landscape than turned through ninety degrees. The `LONG` column says
which way round, and `verify_optics.py` checks that the declared angles
reach the frame the way round it was drawn -- which is the one place the
orientation could have been got backwards without anything looking wrong.

### The indicators on the plate are not clustered

Worth knowing before building a rig: across the five revision families the
LEDs and 7-segment displays span 90.91 x 62.79 mm of a 135 x 101 mm plate, so
framing "just the LEDs" buys 47 mm of height over framing the whole plate and
not much else. That is not a fault in the plate; it is that the LEDs move
between revisions and a fixed rig has to cover all of them. The sheet draws
every position, over all five, and says so.

### The position sheets are named from a table

The position sheets are named from a table, `RPICAM_NAMES` in
`tools/layout.py`, keyed by their file stems: OVER and one word for the
subject, `RPICAM-OVER-PLATE` and `RPICAM-OVER-ARTY`, the wider of them 36.03
mm at the ISO 3098 floor where the stems in capitals ran to 61.02. The
owner's bound is four or five characters behind the prefix, and a stem that
says its subject in full -- `over-tt-mounting-plate` -- is right for a file
and far past it for a drawing number; the sheet's title says the subject in
full anyway.
### The annotation column stayed at 165 mm, and the notes were cut

These sheets carry three small tables and no schedule, so the column could
have been narrower, and every millimetre off it is a millimetre on every line
of the notes band beside it -- which these sheets want, because their notes are
mostly optics, a subject the drawing cannot show at all. At 138 mm everything
fitted except the title block: the `VERSION` cell is a quarter of the column
and below about 157 mm it can no longer hold a `git describe` string. Widening
the grid's cells unequally would have been the right fix and would have
changed every title block in the repository, so the notes were cut instead.

Two small library changes did go in: a title block may rename its `MATERIAL`
field, because these sheets draw no part and a field headed MATERIAL with a
board name in it is worse than either (they say `SUBJECT`); and the legend
gained the two frame line styles. Those are colours as well as a line type,
because on a sheet where one frame contains the other, type K alone cannot
say *which* frame a rectangle is, and that is the only question a reader has.

### Z is measured from the target's plane, not the subject's face

The review caught the one thing here that was wrong rather than untidy, and it
is worth writing down because it is the mistake this whole model invites.

The camera height is a distance from the pinhole to the plane it is focused
and framed on. The subject's own top face is the obvious plane to quote it
from, and on one of these frames it is the wrong one: `RPICAM-OVER-PLATE`
frame B frames the demo boards' indicators, and a demo board stands on
standoffs above the plate. At the 100.1 mm the sheet first gave, a board
12 mm up put the picture at 88.83 x 66.62 against an indicator union of
90.91 x 62.79. The outer LEDs were outside the frame.

The picture at `h` above the plane the height was set from is `(Z - h) / Z`
of what is drawn, so the error is always in the direction that loses the
edges -- never the safe one. A `Target` now carries the plane it lies in and
Z is quoted above that, with a PLANE note on every sheet saying which.

Where the offset to the subject's own face is known, the sheet gives it. Where
it is not, the sheet says so rather than inventing one, and the
plate-to-board offset is not: it is the standoff height plus the board
thickness. The thickness is in `tinytapeout/boards.py`, 1.56 to 1.60 mm
across the revisions; the standoff height is the builder's and is specified
nowhere in this repository, standoffs having never been drawn. Measure the
stack.

Frame A on the plate keeps the plate's own face, because the plate is what it
frames. The board still stands above it and is still inside it, so the sheet
prints the headroom instead: the board outlines stay in the picture up to
25.2 mm above the plate at 65 deg and 9.5 mm at 120 deg. At 120 degrees that
is less than a 10 mm standoff and a 1.6 mm board, which is worth knowing
before building the rig.

### What is left uncertain

- Z is to the lens's entrance pupil, and no vendor says where that sits behind
  the front element. On a 3.60 mm lens it is a few millimetres. Set Z from the
  lens face; the sheets say ASSUMED.
- The 120 degree figure is Arducam's, for the M6 lens on their B006604, which
  is a Pi Zero sized OV5647 board rather than a Camera Module shaped one. The
  sensor is the same and the framing arithmetic carries over, but the source
  is a catalogue row and not a lens datasheet. Nobody appears to publish a
  full H/V/D set, measured and defined, for any 120 degree OV5647 module.
- Neither vendor says how the field of view is measured. The check above says
  it behaves like a rectilinear angle to the array edge on the stock lens; at
  120 degrees real lenses are not rectilinear and the frame will be barrel
  distorted. Nothing here models distortion.
- The plate-to-board offset is not published: it needs a standoff height
  nobody here has written down. The sheet says to measure, and says which way
  the error goes if you do not; it cannot do better until somebody specifies
  a standoff.
- The 65 degree column's excess over the rectangle drawn is 0.01 to 0.02 mm,
  which is the rounding in the declared 53.50 and 41.41 rather than anything
  physical. It is reported by `verify_optics.py` and not by the sheets.

## The camera position sheets lead with the elevations

Issue #7 again, part (b). The owner asked for the side view to be the
primary one: the board, the camera over it, the 65 degree lens's field of
view, and dimensions saying how high and where for the whole board to be in
the picture.

### Two elevations, because the picture has two axes

"65 degrees" is the stock lens's diagonal. What reaches the edge of the
picture is the declared angle along each axis -- 53.50 across the sensor's
long side, 41.41 along its short side -- and which lies along the subject's
X depends on which way the camera is turned. So one elevation per axis: the
front elevation along +Y with X across it, and the end elevation, first
angle, seen from the right and drawn on the left with Y across it, so that Y
reads left to right. Each draws its own angle from the lens face to frame A's
edges. Z is dimensioned once, on the front elevation.

Reading 65 as the angle across the long side is the mistake the name
invites, and it is not small: over the plate it gives Z 110.1 where 139.2 is
needed, and the picture misses 14.6 mm off each end. Every sheet prints its
own figure. Turned the other way the camera would need 174.3.

### The plan stayed, smaller

It is the only view showing which way the picture lies over the subject and
where frame B is, so it earns its place, but not at the elevations' scale:
at 1:2 under the front elevation it took the paper the notes needed and
pushed the plate sheet to 1:5. It sits under the end elevation at the next
standard scale down, dimensions nothing (the elevations dimension frame A,
the table every frame), and the notes flow into the paper the views leave --
beside the plan, then across the full width, then the column's foot --
rather than a band. The scale is the largest at which the views and the
notes both fit: 1:2 for the plate and for the Arty. Getting the plate to 1:2
took cutting every note that said a thing twice.

### Frame A on the plate is every board, not the plate

A camera fixed over the plate has to take in whichever board is on it, not
the plate. Frame A is now the union of every revision's assembled envelope,
Pmod bodies included, set from the demo board's top face. That needed the
standoff, which the plate never specified. It does now: 8 mm, a choice made
no shorter than what Tiny Tapeout's own printed base gives the board
(`case/tt06_demo_base.scad` in tt-demo-pcb: `Height = 8` with a 1.6 PCB in
its top, so 6.4 mm studs over a pocket "for PTH pins and rubber feet"). The
board face is then 9.56 to 9.60 above the plate; Z is set from the higher.

### Focus, said plainly and quantified

Every height is nearer than the stock lens's "Approx 1 m to infinity", so the
board is out of focus. How far: on a thin lens set at the 2 m hyperfocal
distance that range implies, a point spreads to 21 pixels, 1.1 mm on the
board, at the plate's 139.2. Set at infinity instead it is 1.2 mm, so the
figure does not hang on the assumption. The only published close limits are
other sensors': the plate's heights are beyond "Approx 10 cm", and the
Arty's LEDs are nearer than even "Approx 5 cm".

### The entrance pupil, bounded by the data

Nobody locates it, but the v1.3's data gives the lens 5.20 mm proud of the
board, and the pupil is between the sensor and the lens face. So set the
face at Z and the picture is up to 3.7% larger over the plate, never
smaller -- which is what the first note says instead of "a few millimetres".

## A camera holder on the TT plate: TT-MP-CAMERA

Part (b)'s second half: something that puts the camera where
`RPICAM-OVER-PLATE` says, built on the plate.

### The camera

The stock 65 degree lens is the Camera Module v1.3's, and Raspberry Pi never
drew that board. Another branch, `issue-39-rpi-camera-v1`, wrote its data by
hand from Gert van Loo's 2013 hand-measured sheet, and this one is built on
it: `raspberry_pi_camera/v1.py` is that branch's. Its reviewed version gives
the lens an error bar of ±0.65, the holes ±0.2 and the connector its latch
ears, and puts the optical axis at (12.5, 14.8). Holes ø2.0 on the family's
21 x 12.5 pattern, the lens module 8 mm square and 5.20 proud, the board
0.95, the FFC connector 2.8 deep on the far face. Until it landed the holder
was developed against Camera Module 3's pattern, flagged, and verify.py
failed on it.

### Why a portal

Every revision's Pmod hosts are on the front edge and every USB-C is on the
front or the back, so the holder stands on the left and right edges and
spans over. The only connectors on a side are J12 to J14 on DB 4+ and DB 06+,
not fitted, whose bodies stand 2.50 mm in from the plate's left edge; the
side frame's wall is 1.00 mm outside that and mostly off the plate, and it
is a window -- posts at the ends, a rail, a foot -- so a peripheral in one
comes out through it.

The feet sit over the plate's four side M4 fixings and share their screws.
That is the plate's own pattern, so no hole is added and the holder can only
go on one way. The plate's left and right fixings are mirror images about
its centre line to 0.003 mm, which is what lets the two side frames be
mirror images.

### Why the carrier turns

Which way the OV5647's pixel rows run on the v1.3 is published nowhere. The
frame's long side has to lie along the plate's X; a quarter turn out, the
picture falls 17.1 mm short at each end. So the camera is on a carrier that
bolts to the beam on a square of four M3 centred on the lens axis, and turns
a quarter at a time without moving the axis. Printed bosses for both hole
orientations on one part were the first idea and do not work: whichever
way the second set is turned, one of its bosses lands 1.1 mm into the
camera's FFC connector and two are centred off the board's edge.

### The height

Lens face 150.00 above the plate face: 139.17 over the highest board face,
9.60 up, is 148.77, plus a millimetre for the print, rounded up. The stack
above it is the camera's own 5.20 and 0.95, bosses a millimetre over the
connector's 2.8, a 6 mm carrier with the camera's M2 nuts in pockets in
its top, and the beam on the rails.

### What came up while it was being written

- The first cut of the side frame's fixings took every plate fixing with X
  under the centre line, which included one of the two at the back.
- An M2 does not pass a ø2.0 hole at the nominal sizes. It does at the
  thread's own tolerance -- 6g puts an M2's major diameter at most 1.981 --
  so that is the check. v1.py carries the holes ±0.2, since no source reads
  them finer, and at 1.80 an M2 does not go: verify.py reports it, and the
  fix is a 2.0 drill.
- The M3 carrier screw the first table named was 12 mm: 6 mm of beam, 4 of
  carrier and a 2.4 mm nut want 12.4. Lengths are worked from the grips now.

### What is left uncertain

- It has not been printed.
- The sensor orientation, as above.
- The v1.3's small parts beside the lens, LED D1 and R9 by MT1, which no
  source dimensions, against the M2 heads on the lens side.
- Focus, which no holder can fix for the stock lens.

## Both lenses, and what they really are

The owner's request, in full: get the real horizontal and vertical angles of
the v1 camera's two lenses, the ~65 and the "wide" ~120 degree, document
them, draw both, and document the focus of the fixed and the autofocus
versions.

### The 120 is a diagonal

The previous finding was that Arducam's "120(H) x 90(V)" for the B006604
could not both be right on a 4:3 sensor. The B006604's own product page
settles why: "angle of view: 120° diagonal", "Diagnoal Field of View (DFOV)
120°". The catalogue row put the diagonal in the H column, and made V three
quarters of it. H = 120 with D = 120 is not a lens at all: the middle of the
sensor's side is nearer the axis than its corner, and every projection maps
nearer to narrower, so H < D always. That rejection holds whatever the lens.

The same catalogue table has the same camera without its IR filter, the
B006604N, as "96(H) x 72(V)". Split a 120 degree diagonal equidistantly --
r = f theta, angle proportional to image height -- and the long side is 120
x 3.6288 / 4.536 = 96.00 and the short 72.00, exactly. Commonlands' OV5647
page, which works each lens's field of view out on this sensor's active area
from its real distortion data, has a 2.2 mm fisheye at 96 x 72 x 122. So 96
x 72 it is, with the rectilinear split (108.36 x 92.20) as the widest a lens
could be and the equisolid (94.31 x 69.83) and YXF's M6 lens made for these
modules (92.4 x 73.9, printed with its labels shuffled) as narrower ones.

### Distortion, and why tan() is still right for coverage

The request warned that rectilinear tan() maths is wrong for a wide lens. It
is, for getting from a focal length or a diagonal to an angle, and that is
where the 108 came from. It is not wrong for coverage: a ray theta off the
axis meets a plane Z below Z tan(theta) out, whatever glass bent it there.
So once the angle to the middle of each side of the picture is right, the
coverage of the board along that line is 2 Z tan(A/2). What changes is the
corners: under barrel distortion the sensor's straight edges land on the
board as curves bowing outwards (tan(theta)/r grows with r), so the
rectangle drawn from H and V is inside the picture. `verify_optics.py` walks
the edge down for the equidistant and the equisolid projections and checks
it, and checks the margin absorbs every narrower pair at every height -- the
tightest leaves 2.93 of the 5.00 mm.

### The autofocus module, and focus

Arducam's B0176 is the motorised OV5647. UCTRONICS, Arducam's own store,
gives it "Focus Distance 80mm to infinity", 54 x 44 and a 35 mm equivalent
of 35; its predecessor the B0121 says 54 x 41 and "4 cm to infinity". The 35
mm equivalent gives f = 35 x 4.536 / 43.27 = 3.67 mm. No F number anywhere;
F2.9 is assumed from the stock lens and only enters the depth of field.

Depth of field is worked at a two-pixel circle of confusion. That is not
arbitrary: the stock lens's "Approx 1 m to infinity" is exactly what a lens
focused at its hyperfocal distance gives with a 2.24 um circle, 1.6 pixels.
The fixed lenses' hyperfocal distances come out at 1.60 m (stock) and 0.70 m
(wide, with f and N as above). Every position-sheet height is out of focus
on both fixed lenses; the motorised one is in range at every height of 80
mm or more -- all but the Arty's LED row.

### Why a separate lens sheet

Putting every declared and derived figure on the position sheets did not
fit: the plate sheet dropped to 1:2.5 and still overflowed. So the position
sheets carry the figures they compute with, and `RPICAM-LENS` carries the
rest: every figure, what became of it, focus, depth of field, and a plan of
each picture on a board 100 mm down, the fisheye's bowed. It had no room for
a second section along the short side either; the plan dimensions that way
and the table has the angle. Its sources are named in one entry, pointing
at `optics.py` for the addresses: the pinned captures are long enough that
listing them took half the sheet.

### Two holders, not one adjustable one

The 120 degree lens needs the lens face at 82.00 over the plate against the
stock lens's 148.77. A carrier sliding 67 mm on the posts would be set by
eye and knocked out of place; two fixed heights are checkable with a rule.
Everything above the lens face is the same stack, so the beam and carrier
are identical parts, only lower -- `verify.py` checks it -- and only the side
frames differ. Named `TT-MP-CAM65` and `TT-MP-CAM120`: `TT-MP-CAMERA` beside a
`TT-MP-CAMERA-120` would have made one a prefix of the other, which the
naming rules forbid.

The honest gap: the lens sold as 120 degrees is on the B006604, a 60 x 11.5
mm Pi Zero board. The 120 holder carries a v1.3's board with a wide lens
ASSUMED on it. A carrier for the B006604 wants a drawing of that board.

### What did not work

- arducam.com and uctronics.com answer curl, WebFetch and a Playwright
  browser alike with a Cloudflare challenge. Every page quoted from them is
  a pinned Internet Archive capture; the B006604N's own page has none and is
  not quoted -- the catalogue row stands for it.
- Waveshare's RPi Camera (G), sold as 160 diagonal and 120 across, declares
  3.15 mm, which gives 82.5 degrees diagonal even equidistantly. Recorded,
  not drawn.

### What the review of the lens work changed

- 96 x 72 is Arducam's arithmetic, not evidence. Every row in that block
  of their catalogue is its diagonal times 0.8 and 0.6 -- B006603 72.4 x
  54.3 from 90.5, B006605 128 x 96 from 160 -- so the equidistant split is
  how the table was written. It stays the pair used, as the vendor's own and
  the usual first model of a fisheye, but it is no longer called
  corroborated; Commonlands' lens, the one independent figure, scaled to 120
  is 94.4 x 70.8, near the equisolid, and is now an alternative the margin is
  checked to absorb. YXF's figures are flagged relabelled.
- The lean the margin allows was atan(margin / Z), which is right on the
  lens axis only. At the picture's edge a lean moves it sec^2 of the
  half-angle further, so it is now solved there: 1.82 deg at 65 over the
  plate, not 2.06, and 2.68 at 120, not 3.95. And the stand's error and the
  lens's uncertainty come out of one margin, which the sheets now say.
- The tables' one-letter flags read DECLARED and DERIVED both as D; they
  are DECL, DERI and ASSU now, and the diagonal's comes from the data.
- The wide lens's "1 m to infinity" is not what its own optics give (its
  hyperfocal distance is 0.70 m) and reads copied from the stock lens's;
  said so, and it changes no verdict.
- The autofocus note printed a depth of field at frame A's height whether
  or not the lens can focus there; where it cannot, it now says so.
- The 120 holder's 1.00 mm is too little for any real M12 fisheye on a
  v1.3-sized board: with the face 10 mm low the boards' edges are cut off.
  The README says so plainly and TODO carries the fix.

## The three Pis on one outline

Asked for a combined Raspberry Pi drawing, like the Tiny Tapeout fitting
guide is for the demo boards.  The bound `raspberry-pi-sheets.pdf` already
existed, so what was wanted was the other kind of combined: one view with
every model on it.

The three Model B sized Pis make that easy in one way and hard in another.
Easy, because the outline, the four mounting hole centres and the 40-pin
header really are the same on all three, which is what lets them be drawn
once, in continuous line, with everything broken meaning "this model only".

**That is less well checked upstream than it looks.** `extract.py` reads the
40-pin header out of each model's own drawing and requires the three readings
to agree, because the HAT specification fixes it.
It does not do the same for the other two. The outline size is declared per
model in the extractor's `MODELS` table, and `cross_check` says in as many
words that comparing it would be comparing the file with itself. The holes
are worse: only the Pi 4B has `holes_from_source`, so its four centres come
out of its DXF, while the Pi 3B/3B+ and the Pi 5 take theirs from the
hard-coded `STANDARD_HOLES`, and the read pattern and the constant are never
compared with each other. A sheet that draws all three once, in the line type
that means "identical", and then prints a note saying they are identical, was
asserting two thirds of that. `require_shared()` now checks the outline, the
four mounting hole centres and the header before anything is drawn and stops
with what differs; perturbing any of the three by a hundredth of a millimetre
is caught.

Hard, because what does differ is stacked on top of itself. The Pi 4B's upper
USB pair overlaps the Pi 3's lower pair on all four sides: inside it on the
left by 1.20 mm and at the top by 1.32, and past it on the right by 1.00 and
below it by 1.22. Taken against the Pi 5's lower pair as well, the overhang on
the right is 0.76 mm. Worse is the Pi 4B's *lower* USB pair, where the widest
strip not also inside the Pi 3's or the Pi 5's Ethernet jack is 0.562 mm tall,
along the bottom edge. The Pi 5's RJ45 is within about a millimetre of the
Pi 3's on all four sides.

That broke the balloon convention rather than the drawing.  A balloon says
which schedule row a shape belongs to by where its dot sits, and here a dot
sits on three shapes at once.  Three things were tried:

- **Exclusive dots.**  Search the points that are inside this group's
  outlines and outside every other group's.  It works for the RJ45 -- the
  Pi 4B's reaches 2.65 mm further left than the Pi 3's upper USB pair, which is room for a
  dot -- and is far too tight for the USB pairs: the widest exclusive strip
  is 1.22 mm for the upper pair and 0.562 for the lower, against the 1.4 mm
  a dot with `DOT_CLEAR` on each side of it needs.  Kept anyway, as a score
  rather than a filter: fewest foreign outlines first, then nearest the
  centre.
- **Colour.**  Resolves it on screen and loses it in a photocopier, which is
  what these sheets are for.
- **The ring's line type.**  `dims.balloon` now takes a dash and
  `_Ballooned` carries one, so a balloon is drawn in the line type of the
  outline it points at.  A dashed "3" is the Pi 4B's Ethernet jack, a plain
  black "3" is the position the Pi 3B/3B+ and the Pi 5 share.  That survives
  a monochrome print, which the dot position and the colour do not.

Both defaults are the old values, so every other sheet renders byte for byte
as before; that was checked before anything else was believed.

**The Pmod HAT Adapter is not on it.**  Every individual Pi sheet carries it
in phantom and should: its host positions are the reason those sheets exist.
On this one it would say nothing -- it is identical on all three models, so
it is not part of what the sheet compares -- and it would cost a great deal,
because host JC overhangs the lower edge, where all three power connectors
are, and the pin fields of JA and JB sit over the right-hand connectors.
Those are the two places this drawing exists to show.  A note says so and
sends the reader to RPI-3B, RPI-4B, RPI-5 and ACC-HAT-PMOD.

Three smaller decisions.  The keep-out circles drawn are the HAT
specification's 6.2 mm rather than any one model's, because a plate is
designed to the figure that satisfies all three; the three the drawings
actually show are in the hole schedule, as a triple whose order is in the
column heading rather than in a note.  The sheet asserts no manufacturing
tolerance: two of the three drawings disagree about the mounting hole
diameter, so the title block says "reference only" and names the sheets that
govern.  And the notes band came out at 156 mm against the 104 mm the other
three Pi sheets share, so RPI-ALL's view sits 26.00 mm higher
than theirs, measured off the mounting holes in the four finished SVGs -- it
is a different kind of sheet, as TT-MP-FIT is, and the alternative
was cutting the sources to fit.  The sources were cut anyway, to one line per
drawing: most models cite their own file twice and the second entry carries a
paragraph about which circle on which layer was read, which across the three
models is five URLs in seven entries with three such derivations.  A
derivation belongs to the model it was made for, and a note sends the reader
to its sheet.  Even so the last source line spills into the annotation column
under "SOURCES
(continued)". This is the first sheet in the repository to need that spill;
the seven others that carry a "(continued)" heading continue into the second
column of the notes band, which is the step before it.

One note is there for a place the sheet's own scheme cannot be read.  The
three power connectors come within 0.025 mm of each other on their nearest
faces, so at 1:1 the corner where they sit is not three line types but one
printed three times, and the sheet would otherwise be claiming a distinction
it cannot draw there.  A 2:1 detail view would have shown it properly and
cost the notes band its last twenty millimetres, for figures the feature
schedule already gives exactly; the note was the cheaper honesty.

## Naming a sheet that is not a board

The sheet is named from its own file stem like every other, through the
family's rule: `drawing_name` of `raspberry_pi/output/rpi-models-compared.svg`
is RPI-ALL.  The Pi family had no rule -- a model sheet's stem leaves only
the model behind `rpi`, and RPI-5 wants no shortening -- and this sheet is
why it has one: what its stem leaves is `models-compared`, a title, and the
owner's bound is four or five characters behind the prefix.  `RPI_NAMES` has
one row, ALL, for the models superimposed; `rpi_name` passes a model through
and refuses anything else, so a sheet added to this family without a row
stops the render instead of carrying a stem-shaped name.  That it is not a
board key turned out not to matter,
which is the point of naming a sheet after itself: the other three Pi sheets
are named from a key in `RPI_ORDER` by way of `slug`, and this one has no key
at all, only a file it is written to.  Nothing in the generator had to learn
that a family can hold a sheet that is not a board; it does need its own
entry beside `rpi_sheets()`, because it has no single board spec for the
bound copy's outline to take a title and a subtitle from, which is exactly
the shape `plate_sheets()` already had.

Five references to a drawing name are written on this branch, and two of them
are on the drawing rather than beside it: the note explaining why the Pmod
HAT Adapter is left off, and the GENERAL TOLERANCE field, which says which
sheets govern the dimensions this one only reports.  Both are built from
`MODEL_SHEETS`, derived from the same stems the generator writes those sheets
to, so neither can drift from the title block it points at.  The other three
are prose: the family README, the drafting library's index and TODO.md.

Deriving them cost the tolerance field its first wording.  "reference only -
RPI-3B, RPI-4B and RPI-5 govern every dimension" is 115.0 mm of lettering in
a 105.7 mm cell; `_title_cell` refuses to draw a value that will not fit
rather than overprinting the next field, which is how it was found.  The
field reads "reference only - governed by" and the three names, 94.7 mm.  It
is the GENERAL TOLERANCE cell, so "every dimension" was the part that could
go, and the sheets it names are still the ones that govern.

## RPI-ALL's balloons, the second time

"The balloons are all over the place."  They were: eight balloons, each
placed on its own by the placer wherever it scored cheapest, so the three
bays on the right sent leaders to the far right, below the board and back
inside it.  check_balloons passed the sheet throughout, and working out why
was the first job.  It sampled each leader against hard obstacles only, so
a leader ruled through a connector it did not point at, or across the
56.00, was nothing to it; it threw away a crossing shorter than 2 mm, which
is every crossing at a steep angle; and the placed balloons live in a scene
the placer builds per balloon and discards, so a leader through another
ring was invisible.  Rewritten to test exactly, against everything, on
every sheet as the generator draws it, it found on this sheet one leader
through two connector bodies, three across the height and the corner
callout across an extension line -- and, it should be said, no two leaders
actually crossing: the ones that looked crossed ran close and nearly
parallel.  Everywhere else it found only leaders across an overall
dimension, which the placer allows on purpose; those went into ACCEPTED.

The layout was the wrong question.  Each bay holds one connector from each
model, not always the same connector, and three leaders into one bay are
three dots in the same few millimetres whatever the placer does.  Pointing
at the place instead, with every model's number on the one leader, is what
ISO 6433 does for items that share a location.  The other way round -- one
balloon per place, the models only in the schedule -- would have given the
place a number, and a number on these sheets is a part.

Two details took a render each.  The leader first came out in the first
model's colour, which says the leader is the Pi 3's; it is black now, like
the rest of what the models share.  And the Pi 3's long-dash ring met its
leader in a gap, because SVG starts a circle's dashes at three o'clock, so
a broken ring is now drawn from half a dash before the point its leader
touches.

## The Orange Pi PC, measured because nobody has drawn it

Asked for an Orange Pi PC sheet in the `raspberry_pi/` family, as RPI-04 when
sheets still had numbers. It is `RPI-OPIPC`, from the stem `orangepi-pc`, cut
short by a row of `RPI_NAMES` in `tools/layout.py`, because
`RPI-ORANGEPI-PC` is twice as long as a drawing number should be.

The first attempt stopped at "blocked, no source": Xunlong publish no drawing
of this board, and the entry said a sheet would wait for one. That was the
wrong conclusion. Nothing published is a reason to measure, not a reason not
to draw -- the Pmod HAT Adapter was measured off a photograph for the same
reason -- so the board is measured, from photographs, and the sheet says so
and how well.

### What Xunlong publish, which is one figure

Kept from the first attempt, so that nobody repeats the search:

- **The official resource page**,
  `orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-PC.html`,
  offers five documents, each a Google Drive link, and none of them is a
  drawing: User Manual, Schematic, Certified, Datasheet, Official Tools.
- **The user manual** (136 pages, WPS 文字, dated 2021-12-13) gives, in the
  hardware table in section 1.4, `Product Size 85mm×55mm` and `Weight 43g`.
  Its "Top and bottom views" and "Interface Details" are annotated
  photographs; the callouts name the ports and carry no dimension.
- **The schematic**, 15 A3 sheets whose revision block runs to 2015-05-29, is
  electrical throughout. **The datasheet** is Allwinner's H3 datasheet.
  **Certified** is two regulatory certificates.
- **The wiki** re-types the manual's first chapter, down to the same
  `Product Size 85mm×55mm`.
- **The product page** says `85 mm × 55mm` in its specification table -- and
  56 in the one dimensioned picture on the page, a photograph of the
  underside with "85mm" and "56mm" ruled across it. It is the second of the
  Xunlong photographs measured here.
- **The old download host**, `orangepi.org/download/`, in the Wayback CDX
  index: four mechanical files, for the Lite, the PC Plus, the Zero and the
  Plus 2E. None is the PC.
- **The forum** has asked for this drawing since 2015. The answers are a
  Thingiverse model, a member's own measurements, and "PC and PC-Plus has
  the same size", pointing at the PC Plus drawing.
- **linux-sunxi** gives `Dimensions 85 mm x 55 mm` and no more.

### The photographs

`tools/fetch_orangepi_pc.sh` fetches everything. Two pairs are measured:

- linux-sunxi's `Orange_Pi_PC_v1.3_front.jpg` and `_back.jpg`, a v1.3 board
  on a Fujifilm X-E2 at 35 mm, 2560 pixels across. linux-sunxi.org answers a
  script with a Cloudflare block, so they come from the Wayback Machine's
  January 2026 capture.
- Xunlong's product page views of a v1.2, `PC40.png` and
  `PC/Rectangle 641.png`, 700 pixels across the board and sharp.

A third pair, linux-sunxi's `Xunlong_Orange_Pi_PC_top.PNG` and `_bottom.PNG`
of another v1.2, was measured and dropped: it is shot obliquely, the far half
of the board is out of focus, and the fitted left edge ran along the side of
the board rather than its top face, putting MT3 a millimetre off.

### The method

`tools/photo_frame.py` finds the four board edges where no connector hides
them, fits a line to each and a homography from their corners onto
85 x 56 mm. `raspberry_pi/measure_orangepi_pc.py` then measures in that frame:
holes as circles fitted to their copper rings, in all four views; the header
from its forty solder joints in the bottom views, where they lie in the board
plane; and each connector's top face, read by eye off a 1 mm grid ruled on the
rectified top view (`--grids` writes the images) and corrected for parallax.

The parallax is the part that took working out. A USB pair's top face is
16 mm nearer the lens than the board and is drawn larger, about the point
under the lens, by D / (D - z) -- 2.5 % in the v1.3 photograph, a millimetre at
the far end of a USB port. The header gives both unknowns: its pin tips in
the top view against its solder joints in the bottom view of the same board
say where that point is and, taking the tips as 8.5 mm up, how far off the
lens was. Each part's height only sets the size of the correction; a 2 mm
error in one moves a corrected edge by 0.5 mm at most.

### The board is 56 mm, not 55

Every figure Xunlong print in text says 55; their own dimensioned photograph
says 56, and so does their PC Plus drawing, whose board outline is
85.00 x 56.00 with 2 mm corner radii. The homography cannot decide it -- it
maps the corners onto whatever rectangle it is given -- so each photograph's
own proportions are read at the board's centre: 55.99, 55.88, 57.09 and
55.72. The 57.09 is Xunlong's top view, which is out on this and on nothing
else, and is taken to be shot tilted. The median is 55.94, a millimetre from
the manual. The sheet is 85 x 56 and says why.

### What the checks found

`raspberry_pi/verify_orangepi_pc.py` holds the result to what it was not fitted
to. Two things came out of it worth writing down.

**Fitted to the edges, everything was 0.5 to 0.7 % wide.** The header's pin 1
to pin 39 came out 48.58 and 48.48 mm where it is 48.26, and the holes 79.40
apart where every case but two, and the PC Plus, put them 78.96 to 79.15
apart. The first version left that in, inside a +/-0.4 tolerance, on the
argument that fitting the scale to the header would leave the header check
proving nothing. The review before pushing said otherwise, and it was
right: the hole pitch is the one number a plate is drilled from, it was
0.3 to 0.4 mm long, and the header, the PC Plus drawing, six cases and the
reviewer's own measurement off the raw photographs all said so. So the scale
across the board is now the header's own pitch; the board's edges on that
scale, 84.44 and 84.61 wide against the 85 drawn, are what the header check
now tests. The likeliest cause is the edge finder landing inside the routed
edge, on the solder mask rather than the laminate -- a bright band a few
pixels wide runs along the v1.3 board's edge -- though the Xunlong view says
84.6 as well, so part of it may be the board. Up the board the header's two
rows are too short a ruler and the edges' scale is kept; the holes come out
50.16 apart there, where the PC Plus says 50.11.

**Xunlong's PC Plus drawing is the best check there is.** It is two AutoCAD
2000 DWGs in a RAR that 7-Zip cannot unpack (libarchive can), read with
`ezdwg` into `ezdxf`. It is a different board -- the PC with eMMC and Wi-Fi
-- but its holes are within 0.10 mm of where the photographs put this
board's, every part the two share is centred within 0.40 mm, and its
header's pin 1 is within 0.31.

Roman Gachin's 3MF model agrees on the holes but has the header's rows
3.19 mm apart and the barrel jack and UART header 1.2 and 1.5 mm right of
where the photographs put them and 1.6 and 1.2 mm right of Xunlong; landroo's
case cuts its microSD and USB pair openings 1.8 and 1.25 mm off centre, and
puts its standoffs 80 mm apart, 3 mm in from an 86 x 57 box. The check
accepts a third-party figure outside the tolerance only when it is outside it
against Xunlong's drawing too, which all of those are.

### The tolerance, and what it means

The first wording said each tolerance was "the worst disagreement between
two photographs". It is not: it is the furthest any one reading lies from the
figure drawn, which is the mean of them. Two readings of one edge can
disagree by up to 1.55 mm -- the USB pair's upper side, 19.25 in Xunlong's
top view against 20.80 from below in the v1.3 view -- and the further of the
four readings of that side is 0.94 from their mean. The sheet says what the
number is.

### Decided on the way

- **The Pmod HAT Adapter is overlaid**, moved onto this board's header, which
  is 1.52 mm right of and 0.15 mm below a Pi's. The first attempt said not to
  overlay it unless a source put the header in the Pi's place. The header is
  measured now, so the adapter can be put where it goes; what cannot be
  claimed is that it bolts down, and the sheet's note about its holes is now
  worked out from the geometry for every sheet rather than asserted: here it
  says they miss by 2.0 mm or more, rounded down, and no standoff can join
  the two.
- **It does not join `rpi_view_frame`.** Every Model B Pi is one outline with
  one hole pattern, which is what that frame holds still. This board has
  neither, so it is fitted to its own view, after the Pis in the bound copy.
- **Parts 6 to 11 are this board's own numbers.** A Pi sheet draws neither
  HDMI nor audio; a case round this board has to clear them, and nobody else
  has drawn them.
- **The debug UART header and the camera connector are not drawn.** The
  UART's balloon could only reach it across the adapter's host JC; with the
  camera connector drawn, the microSD socket's and power button's balloons
  could only get out across JB. Both are well inside the outline, and both
  are measured and checked with the rest.
- **Pin 1 is a dot.** The first version drew the header's body and gave pin 1
  nowhere, though pin 1 is what was measured; a feature can now carry a pin 1,
  and the sheet marks it.
- **The corners are rounded, radius measured**: 1.7 to 2.4 mm over the
  fifteen corners the edge finder could see, drawn at the median, 2.3. The
  PC Plus drawing says 2.
- **Two leaders cross JB, and are accepted.** With the pin 1 dot and the
  radius on, `check_sheets.py` found a balloon parked on the overall width's
  extension line, which nothing reserved; reserving it left the microSD
  socket's and power button's leaders no way out but across the adapter's
  hosts. They are in `check_balloons.py`'s ACCEPTED with the reason: three
  parts on the left edge, hosts inboard, a chain on each other side, and one
  strip out, which the micro-USB takes.

## The Orange Pi PC's balloons, beside their parts

"The bubbles on the orange pi diagram are all in weird places -- they should
be as close as possible to the item."  Five of them sat up and to the right
of the board, their leaders across the board, other parts and each other,
and two were in ACCEPTED for crossing the adapter's host JB.  Nothing was
wrong with the placer's scoring of those places; it had no nearer ones.  The
ordinate chains bounded it, the Y chain a wall on the left and the X chain a
floor below, and this board has its micro-USB, microSD socket and power
button on the left edge and its barrel, HDMI and audio jacks on the bottom
one, all overhanging, with the chains nine millimetres off them.  A balloon
wants more than that once it is kept clear of the part and of the chain's
labels.

Three ways were weighed.  Fixing the balloons by hand, which #19 made
possible, would have fixed this sheet and nothing else, and been undone by
the next change to the board.  Moving a chain away from the connectors, as
the Arty's X chain moved to the edge its features are nearest, does not help
here: the Y chain has four of its six features on the left, and every edge
of this board has parts on it.  What a drafter does is put the balloon out
past the chain, the leader running between the witness lines, so that is
what the placer may now do.  The chains are planned before the balloons from
the call that draws them, and past the chain line their labels and witness
lines are hard.

That brought the bottom edge in at once and left the left edge's balloons
out past the labels, 34 and 42 mm from their parts: the strip beside them
was clean only in slivers a few tenths of a millimetre wide, and a clean
leader, however long, stopped the placer trying a dot anywhere but the
part's centre.  Three small changes brought them in; each alone does not.

Charging a leader for crossing a witness line and an overall dimension came
out of the same work.  Without it the first version sent a right-hand
balloon on each Pi sheet across the overall height to reach the space past
the chain; with it the Pi 4B's balloon 5, which had crossed the height since
the check was written, stopped.

The balloon for the camera connector and the debug UART header, which are
still not drawn, has not been tried again.

## The Ultra96-V2, out of an Altium plot

Asked for a sheet of Avnet's Ultra96-V2, the Zynq UltraScale+ board built to
the Linaro 96Boards Consumer Edition form factor. Avnet's own product page is
indexed as listing a mechanical drawing and three STEP models -- the board
alone, the heat sink alone, and the two together -- and none of them could be
reached. Avnet sit behind Akamai, and it refuses in two different ways: the
product page answers a scripted fetch and a browser under Playwright alike
with a Bot Manager interstitial -- a kilobyte of JavaScript, HTTP 200, `_abck`
and `ak_bmsc` cookies -- while a file URL under `wps/wcm/connect` refuses a
plain `curl` with an Akamai WAF `PR_WAF_DENY` and HTTP 400 but serves the same
URL to a request carrying a browser User-Agent, exactly as Digilent's file
host does. That is how the hardware user's guide is fetched. It is not how the
product page can be read, so the mechanical drawing and the STEP models it is
indexed as offering stayed out of reach, and a CDX query of the Internet
Archive's index of avnet.com turns up the Ultra96-V1 mechanical drawing and
the V2 assembly drawings but no V2 mechanical drawing and no STEP file at all.
So the page's contents are hearsay from a search index, not something read
here. What is reachable is Linaro's
`96boards/documentation` repository, which republishes the vendors' hardware
documents, and it carries `ultra96-v2-mechanical.PDF` under the heading
"Mechanical and Drill". That file is Avnet's, an Altium NEXUS plot of the
U96-US1SBC V2 board dated 2019-03-01, and it is a vector drawing, not a scan.

It is also a plot of the whole board rather than a mechanical drawing in the
usual sense: 45,883 line segments of copper, silkscreen and drills, with the
overall sizes dimensioned in inches across the top and bottom. Its media box
is cropped to the drawing, so the Altium sheet frame, the title block and
anything like a drill table are outside it -- the content stream still
reaches from -87 to 631 mm across, and only the crop hides it. Nothing on the
visible page fixes the scale except the board outline, so the scale is
recovered from that, per axis, against the 96Boards 85 x 54 mm. The axes
disagree by 0.02 %.

That reference figure is the one number on the sheet that is not measured,
which makes the checks on it worth stating. The drawing dimensions itself, in
inches and as stroked glyphs rather than text, and those figures are not used
for anything -- but read off the page they say 3.346 and 2.126 in, which are
84.99 and 54.00 mm, and 0.157, 0.728, 1.240 and 1.969 in for the mounting
holes, which are 3.99, 18.49, 31.50 and 50.01 mm. Measured, the four holes
come out at (4.000, 18.500), (4.000, 50.000), (81.013, 18.500) and
(81.013, 50.000) against the specification's 4.00 and 81.00 by 18.50 and
50.00, so the worst error is 13 um. The low-speed connector's twenty columns
span exactly 2.000 mm each and its pad rows exactly 5.000 apart; the
high-speed connector's thirty span exactly 0.800 and its rows exactly 4.400 --
one check per axis, neither of them the axis's own reference. And the two
connectors' centre lines land on the specification's: the low-speed one on
y = 50.00, which the 2D Reference Drawing calls "center line as per mounting
holes", and the high-speed one on 15.45, an unlabelled ordinate on it.

What makes the plot readable at all is that Altium wrote the designators into
it as text. Every pad carries a string -- `PAJ501` for pin 1 of J5, `PAJ5010`
for pin 10, `PAJ70S1` for the micro-USB's first shield land -- so a filled
shape can be named without guessing which component it belongs to. The
strings are drawn glyph by glyph and each ends with a space, and the space
has to end a word as well as the usual baseline and advance test: without it
the micro-USB's two middle shield lands came back as one word naming two
pads. Avnet's bill of materials says what each designator is, and how many
pads the plot names for each component is asserted, so a footprint that
changed shape is an error rather than a quietly smaller box. That count is
not the BOM part's pin count and the first version of this said it was: J5 is
a 40POS part with forty named pads and J4 a 60POS part with sixty, but J7 is
a "10 POS" part with fourteen, ten contacts and four shield lands, and J8 and
J9 are "9PS" parts with eleven, nine contacts and two shell posts. Nor are
names and pads one for one: the micro-USB's four shield lands are drawn as a
single path, so its fourteen names resolve to eleven shapes, and the number of
distinct shapes is asserted too, because two names collapsing onto one pad is
otherwise indistinguishable from a match that went wrong. Three pads are
filled black instead of the copper grey -- pin 1 of each USB type A port and
one pad of the barrel jack -- and black rectangles are taken as copper for
that reason, while black curves are not, because all 1,545 of those are drill
holes.

The plot gives three footprints a pad with no name of its own, written
`PAJ10None`, `PAJ30None` and `PAJ40None`: the hold-down tabs of the two 2 mm
right-angle headers and one on J4, each 1.20 mm square. J4's sits 1.65 mm
clear of the left end of its pin field with nothing answering it at the right
end, so folding it in would put the box of a symmetrical part 2.85 mm out on
one side. All three are left out and the extractor says why.

There is no component body outline anywhere on the plot, which is why every
feature on the sheet is a pad extent and the sheet says so. The silkscreen
brackets a connector rather than enclosing it, and the only closed outlines
it draws are around the 0603 parts. The mounting holes are drawn as solid
5.0 mm discs with no drill inside them, which is the specification's keepout
and not a hole, so the diameter in the schedule is the specification's M2.5
and the note says where it came from.

Two more things the board itself decides. It has no Ethernet -- Avnet's
hardware user's guide says so in as many words -- and no tri-colour LED, so
schedule rows 3 and 5 are empty, and it has no Pmod, so the two 96Boards
connectors take the expansion rows 6 and 7 and row 8 stays unused. Row 1 is
the family's "USB programming / console port", and on this board it is the
USB 3.0 device port: programming is JTAG on a 1x8 2 mm header and the console
is a 1x4 2 mm header, neither of which is drawn, and a note says so rather
than letting the row imply otherwise. `row_feature` grew an option for a row
that is not on a pitch, because the four user LEDs sit 1.40, 1.52 and
1.40 mm apart and a label claiming 1.44 would be inventing one.

Two things the drafting library gained. The feature schedule can now say what
its extents are extents of, because "X EXTENT mm" over a pad extent reads
exactly like "X EXTENT mm" over the component bodies the other sheets
carry, and an aperture cut to a connector's pads is too small. It goes in the
table's heading -- "FEATURE SCHEDULE - PAD EXTENTS" -- and not in the column
heads, which turned out to be too narrow to take another word: "X PAD EXTENT
mm" and "Y PAD EXTENT mm" came out 0.08 mm apart and `check_sheets.py` read
them as one word. The first note under the drawing says the same thing in
capitals. And the balloon placer now reserves the two
arrowheads of each overall dimension against leaders as well as balloons: the
band between them is deliberately left crossable, because pricing the whole
of it boxes balloons into the board's interior, but an arrowhead is a solid
filled triangle three millimetres long and a leader ruled through one stops it
reading as an arrowhead. The LED balloon on this sheet went out to the right
at exactly the height of the 54.00 dimension's lower arrowhead and straight
through it. `tools/check_leader_arrows.py` reads the finished SVGs back and
tests segment against triangle, and it found that one and nothing else.

Its first version asked only whether a line was `style.C_HIGHLIGHT`, which is
the balloon colour on every sheet in the set, and that reads three things
that are not leaders: the Pmod pin-row centre line on FPGA-ARTY-A7,
ACC-HAT-PMOD and ACC-HAT-RMOD, drawn in the balloon colour, dashed
`D_CENTRE`, running along the lane the pin-field depth dimension occupies,
and meeting that dimension's arrowhead because the dimension measures to it.
Those three were written up as a deferred defect and were never one.

So a leader is now read off the sheet: a balloon is a ring of the balloon
radius, and its leader is a line in that ring's colour with an end on that
ring. Both halves are load-bearing here and both were measured. Without the
end-on-a-ring half the three centre lines come back. Without the colour half,
seven sheets -- the six demo boards and FPGA-BUTTERSTICK -- draw a dashed grey
circle of exactly the balloon radius, and forty-four black lines stop on one
of those without being its leader. Taking the colour off the ring rather than
fixing it at `style.C_HIGHLIGHT` is what stops a sheet that coloured its
balloons some other way passing for having nothing on it to check. With
both, the checker reports nothing across the set -- which is why it goes into
`make check` beside `check_balloons.py` rather than waiting outside it for a
defect to justify it. Its summary line counts the leaders it examined as well
as the problems it found, because a rule that matches none of a sheet's
leaders reports that sheet clean and nothing else printed would say it had
looked at nothing.

RPI-ALL, merged while this branch was open, is such a sheet, and shows how
far that goes. Its balloons are in each model's colour, but the leader several
of them share is drawn in the line colour, which is not the colour of the
ring it ends on, so the colour half does not read it: the check examines one
of RPI-ALL's balloon leaders and not the four shared ones. Main's
`check_balloons.py`, which works from the drawing rather than the SVG, holds
every leader on RPI-ALL against every dimension line and finds none crossing
one. A rule that did read them -- a balloon is a filled ring, and the phantom
circle is not filled -- was tried on the set: it reads exactly those four more
and nothing else, and none of them is through an arrowhead. It replaces the
argument above, so it is left for a change of its own.

The reservation began as an obstacle and not only a test, so it could move
a balloon on a sheet already issued, and it moved one: balloon 9 on
FPGA-CYNTHION. That leader was not ruled through an arrowhead -- the check
passes that sheet with the reservation and without it -- but the balloon
had to keep its disc two millimetres clear of the arrowhead's box as well.
Once #22 made a leader pay for crossing an overall dimension line, that
cost more: the balloon went about 40 mm down past the ordinate chain. So on
a board sheet the box is now four hard segments a leader is charged for
crossing, which price a leader through it and leave a balloon beside it
alone. On #22's placer the reservation moves nothing: rendered with it and
without it, every sheet in the set comes out byte for byte the same, this
sheet's own balloon 4 included, which the crossing charge already keeps off
the 54.00 line and its arrowheads. It stays, because the check it answers
still runs and a leader through an arrowhead is a defect at any price.

One consequence of adding a sheet without restamping the rest: the committed
`fpga-sheets.pdf` carries more than one VERSION stamp, this branch's on the
page it draws and older ones on the others. The front page's claim that
`git status` is silent after a rebuild is false here until the whole set is
restamped after merge. That is deliberate. Restamping the whole set to add
one sheet makes a pull request that cannot be read and conflicts with every
other branch in flight; the stale stamps are a day's inconvenience and the
conflicts are not.

## The Zybo Z7, and a drawing that names nothing

Digilent publish the Zybo Z7's mechanical drawing as the same pair as the
Arty A7's -- `ZYBO_Z7_DXF.DXF` and `Mechanical_ZYBO_Z7.pdf`, in a zip the
Resource Center links as "Zybo Z7 Mechanical Drawings" -- and the two files
are dated a day apart in September 2020, out of the same Altium job.  So the
Arty's reader became a shared one and the Zybo's numbers came out of it,
with two differences the drawing itself forced:

- **No keep-out layer.**  The Arty's outline is the whole of its
  `KeepOutLayer`; the Zybo drawing has no such layer and keeps its edge on
  `Mechanical1`, among the dimension lines.  Those run past whatever they
  measure and their ends do not meet, so the edge is picked out as the one
  closed rectangle of whole segments that every plated hole sits inside:
  121.92 x 83.82, exactly 4.8 x 3.3 in.
- **Notched Pmod sockets.**  The plot draws each 2x6 host as a rectangle
  with a keying notch cut into both long edges, so it closes no rectangle at
  all and `rectangles()` cannot see it -- all six hosts were invisible.
  `outlines()` walks the segment graph and returns the extent of each
  connected run, which finds any closed body whatever shape it is drawn as.
  It over-reaches in exactly one place on this sheet: a dimension's extension
  line leaves the USB-A's own front corner and carries the run 1.5 mm past
  the back of the shell, so that one body is read from the rectangles.

Nothing in either file is named.  What identifies the parts is Digilent's own
STEP assembly, `Zybo_Z7.step`: every solid in it carries its reference
designator and it is placed in the drawing's frame, origin on the board's
lower-left corner, so its boxes can be used as they are.  That is the role
the Arty Rev C model plays there, but far stronger -- the Arty model only
told two LED rows apart by package size, and this one names JA to JF, J3,
J11, J12 and LD0 to LD13 outright.  Every body the plot supplies is then
required to land on the model's box and, where the DXF has the same feature,
on the DXF's own figure: each host on its pin field, the RJ45 on its two
3.25 mm locating pegs, the micro-USB on its four shell pads, the USB-A on its
two 2.4 mm shield legs.  All agree to about 0.01 mm, the micro-USB
furthest out at 0.0105.

Three things the sheet says that the drawing cannot:

- **The host pitch is 23.00 mm, not 22.86.**  The four hosts along the lower
  edge are on a round metric pitch, so a plate cut to the 0.9 in grid the
  Tiny Tapeout plate uses does not fit them.  The pin rows are 2.50 apart
  rather than 2.54, the same metric-grid drawing as the Arty's.
- **Which variant.**  The Z7-10 and the Z7-20 are one PCB; the -10 leaves
  Pmod JB and one of the two tri-colour LEDs unfitted, which the reference
  manual says and the Resource Center's own table counts ("Pmod Connectors
  6 (5*)", "2 RGB LEDs (1*)").  The drawing is of the fully fitted board.
- **What hangs below.**  J10, a micro-AB USB socket sharing the OTG signals
  with the USB-A, is fitted on the UNDERSIDE directly below it and projects
  2.72 mm below the laminate and 0.82 past the left edge.  It is not the
  figure a plate has to clear, though: C250, a bottom-side capacitor inside
  the Ethernet jack's footprint, reaches 3.10 mm in Digilent's model, and a
  note quoting an underside projection has to quote the governing one.  The
  sheet gives 3.10 and names both.

Pin 1 came out checkable for once.  The family's rule -- top right looking
into the socket, fed by the row of holes farther from the board edge -- puts
pins 5 and 6, GND and VCC, at the far end of every host.  Digilent's top view
of the board has 3V3 and GND silkscreened at exactly that end of all six,
across all three edges they sit on.  The XADC host JA is the clearest: its
six labels read AD14, AD7, AD15, AD6, GND, 3V3 down the column the rule
picks, which is pins 1 to 6 in order.

Getting at any of this took a detour.  Digilent's wiki pages answer a script
with a Cloudflare challenge, and the browser could not pass it either; the
`_media` and `files.digilent.com` URLs are served normally to a browser
User-Agent, but nothing says what they are called.  The filename came out of
a Wayback Machine snapshot of the Resource Center, which is also where the
"Width 3.3 in (88 mm)" quote on the sheet comes from -- a figure that
contradicts its own 3.3 in, and which the drawing settles at 83.82.

Four sources, four vintages, and a drawing that does not say which board it
is of.  The reference manual is revised 2018-02-21 and says it applies to
rev. B; the schematic is revision D.1; the drawing files are dated
2020-09-03; the STEP is an OpenCascade export of 2023-03-07.  Nothing in the
DXF or the plot carries a revision, and the zip's stale Altium previews are
dated 2017, so the drawing is most likely of the same rev B the manual is.
What ties them together is not their dates but that they are checked against
each other on the board itself: the model's outline is the DXF's to a
millionth of a millimetre, its connector boxes land on the DXF's pads and
pegs to a hundredth, and the designators it supplies are the ones
silkscreened in Digilent's own photograph of the board.  A revision that had
moved any of that would have failed one of those checks rather than passed
all of them.

## The Zybo Z7's ordinate lane, and the room a chain actually needs

The first cut of the sheet put a digit through a rule.  The datum's 0 and the
mounting holes' 3.81 are closer together along the lower ordinate chain than
a label is tall, so 3.81 staggers out to a second lane -- and that lane ended
inside the stroke of the rule under NOTES, with the whole "3" glyph below it.

`VIEW_MARGIN_BOTTOM` was the culprit: a flat 30 mm, which is about what a
chain needs when its labels all fit in one lane and nothing like enough for
two.  Measuring every sheet in the repository with `dims.ordinate_reach`, the
new function that runs the chain's own lane assignment without drawing it,
fourteen of the seventeen board sheets `render_board` draws want more than
30 -- the ULX3S, the Icepi Zero and the Pmod HAT Adapter, all at 19.83, do
not -- and twelve of them stagger a label into a second lane.  The Tiny
Tapeout sheets want 42.76, as does this one.  They do not collide because a
view is centred in what its margins leave, so half of whatever height the
sheet has spare already falls below the board.  One sheet is left short by
that centring and no other: this one, by 9.17 mm, because it is the sheet
whose notes band is capped by its own view.

Reserving the full figure in `_view_height_needed`, which is what decides how
tall the notes band may be, was tried first and rejected: it pays for the
chain out of the notes band, which is not this decision's to spend.
So the reservation happens after the band is fixed instead, in
`_view_margins`: a sheet the centring leaves short has its bottom margin
raised by twice the shortfall, which puts all of the spare height below the
board rather than half, and its top margin cut to `_view_room_free_edge`, the
room the one dimension up there actually occupies.  Only a short sheet moves,
which is this one and nothing else: its margins go from (20.00, 30.00) to
(17.21, 39.97).

That is worth 6.38 mm here -- the board rises by exactly the difference --
and it is the whole of the fix.  The label now clears the rule by 6.3 mm,
measured on the render at 2400 px rather than computed, where before it ran
into the stroke.

There was nothing left to win in the text, because the text had already been
cut once.  The board size and the board photograph are two facts on one
Resource Center page and were folded into a single citation when the sheet
was written, not here: spelled out separately they cost a hundred and ninety
characters and a whole URL, and the notes band wants 52 mm of the annotation
column against the 45 there are, which is not a blemish but a sheet that
cannot be drawn at all.

One thing the measuring turned up on the way.  `ordinate_reach` decides that
two values crowd each other by comparing their gap with the height of a
label, and a label's height is a sheet figure that does not grow with the
view, so the gap has to be a sheet figure too.  Feeding it model millimetres
reads a 2:1 sheet as crowded when it is not: the Pmod HAT Adapter and the
Icepi Zero, two of the three sheets drawn at 2:1, were each asking for
30.30 mm of margin for a chain that wants 19.83.  `_chain_room` takes the
view's scale and multiplies the positions by it.  Neither sheet was short at
either figure, so nothing moved; it was wrong by 10.47 mm in the direction
that happens not to show.

Two things worth writing down, both of which the first draft of this section
got wrong.

Why 39.97 mm of margin beats a 42.76 mm reach is not that the text metrics
are loose.  `text_width("3.81", T_DIM)` is 6.867 mm -- the 9.42 in the first
draft was that call made with `em(T_DIM)`, the SVG font size, where a cap
height belongs -- and 6.867 is an advance width containing 6.34 mm of ink,
which is what an advance width is for.  Taking the library at its own word
the label's run ends 5.91 mm above the rule; measured on the render it is
6.30.  The margin is the smaller number because `_chain_room` measures
to the floor of the drawing area, and the first thing drawn in the notes
band is 8.70 mm below that floor: 4 mm of gap between the area and the band,
and 4.70 mm of heading above the band's first rule.  A chain may reach a
little past the margin and still land on blank paper.

And the annotation column is not narrow.  At this band's three columns it is
165 mm against their 65, two and a half times as wide; at two columns it is
still a little over one and a half.  What makes a millimetre of band height
cost more than a millimetre of column is that the band is two or three
columns, so a millimetre of it is two or three millimetres of text, and the
tail that moves carries a repeated SOURCES heading with it.  The column is
what makes this sheet tight all the same -- six hosts, five features, an
eight-row feature schedule and a legend leave 32 mm of it -- which is why
folding two citations into one was worth more than any amount of rewording.

Three edges of the mechanism worth having closed even though none of them
bites today.  A sheet drawn on a family's shared view frame is not biased at
all: the bias is a per-sheet decision, and one member of a family moving
alone would break the frame as surely as a taller notes band would, so a
family that comes to need it should take the largest of its members' margins
the way it already takes the tallest of their bands.  The pair of margins is
applied when either has moved, not only when the bottom has, or a sheet
wanting the top margin's give without wanting the bottom raised past its
floor -- a shortfall between 30.00 and 32.79 -- would have had it computed
and thrown away.  And `_chain_room` counts only the spacing dimensions
`render_board` actually draws: a pair of hosts sharing a coordinate, as the
Pmod HAT Adapter's JA and JB do, gets no dimension and must not be reserved
paper for one.

## The Zybo Z7's ordinate lane, rebased onto the Cynthion

The Cynthion merged while this branch was open, and it is the second sheet
the centring leaves short.  Its lower ordinate chain staggers into a second
lane and wants 40.80 mm; a centred view gives it 37.47, so it is 3.33 short,
and `_view_margins` moves it the way it moves the Zybo Z7: from (20.00,
30.00) to (17.21, 33.87).  Nothing on the sheet collided before -- the checks
passed on main -- so this is the rule applied as written, not a fault
repaired, and no board is made an exception to it.  The sheet is re-rendered
here and rebound into `fpga-sheets.pdf` with the Zybo Z7.

The counts in the section above were taken before the Cynthion was in the
set and stand as the record of that measurement.  The comments in
`board_sheet.py` and the item in TODO.md say what is true now, naming the
sheets rather than counting them: every board sheet `render_board` draws
wants more than 30 mm except the ULX3S, the Icepi Zero and the Pmod HAT
Adapter, and the Zybo Z7 and the Cynthion are the two the centring leaves
short.

## An Acorn in a PoE M.2 HAT on a Pi 5

Asked for a sheet of the SQRL Acorn CLE-215+ fitted in a Waveshare M.2 / PoE
HAT on a Raspberry Pi 5, so that a plate or enclosure designer can see what
the stack's plan envelope really is. Three questions had to be settled before
anything could be drawn, and each of them had a published answer.

**Which Acorn.** `fpgas.online-docs` says it outright: "The SQRL Acorn CLE-215+
is an M.2 form factor PCIe FPGA accelerator card ... In the fpgas.online fleet
it sits either in an M.2 HAT on a Raspberry Pi 5 or in a Compute Blade's own
M.2 slot", form factor M.2 2280, connector M.2 M-key. Nothing in this
repository mentioned it before. That page is cached beside the other sources
this drawing was made from, at
`tmp/src/acorn-cle-215/fpgas-online-docs-boards-acorn-index.md`, with the
commit it was read at in the `.provenance` file next to it; it is `gh api
repos/fpgas-online/fpgas.online-docs/contents/docs/boards/acorn/index.md`, so
a reader can fetch it again rather than take the quotation on trust.

**Which Waveshare HAT.** They sell three: PoE M.2 HAT+, PoE M.2 HAT+ (B) and
PoE M.2 HAT+ (C). Only the (B) is "Compatible with M.2 hard drives of 2230 /
2242 / 2260 / 2280 sizes"; the other two stop at 2242, so neither can take an
Acorn. The (B) is also the only one the size of a Pi: its dimension drawing
says 85.00 x 56.00, against the plain one's 70.00 x 56.50 and the (C)'s
65.00 x 56.50, both of which those boards' own drawings state. **Waveshare's
wiki gives the (B) "Product size: 56.5mm x 70.0mm"**, which is the plain HAT's
size and contradicts the (B)'s own drawing; the sheet says so rather than
choosing quietly. Their wiki is behind Cloudflare and answers curl and a
headless browser with 403, so every page and image here came from the Internet
Archive at `web.archive.org/web/2025id_/`.

**Where the M.2 slot is.** This is the part that had to be earned. Waveshare's
dimension drawing is a photograph of the real board with six figures printed on
it and "Unit: mm" in the corner: 85.00 and 56.00 for the outline, 58.00 and
49.00 for the mounting hole rectangle, 3.50 from a hole centre to the board
edge at the socket end -- which together are the Raspberry Pi's own hole
pattern, so the HAT bolts through the Pi's four holes -- and 3.00, which is not
a board dimension at all but the amount by which the 2280 standoff's boss hangs
off the opposite edge. Nothing else of the M.2 system is dimensioned, and there
is no DXF, STEP or board file from Waveshare that carries it.

So `accessories/measure_poe_m2_hat.py` recovers it from that image, the way
`measure_pmod_hat.py` recovers the Digilent adapter's hosts: scale and origin
from the four mounting holes, whose pitch the drawing states. What makes this
one far tighter than the Pmod HAT's +/-0.75 mm is that there are three separate
checks the fit never used, and they close on each other:

- the board's own edges come out 84.88 x 55.88 against the declared
  85.00 x 56.00, with the lower-left corner at (0.17, 0.23);
- the three standoffs that sit clear of the board edge each give the M.2
  connector datum on their own, through the M.2 specification's 30, 42 and
  60 mm module lengths. They read 5.08, 5.07 and 5.05 mm: a spread of 0.04 mm
  across fifty millimetres of board;
- the fourth standoff is then *predicted* at 80 mm from that datum and never
  measured -- it is the one the drawing rules a dimension line down and the
  one with white paper behind it, so no threshold separates it from either --
  and the boss whose diameter the other three fix reaches 88.00 mm, which is
  exactly the 85.00 + 3.00 Waveshare printed.

The worst residual on any of those three is 0.12 mm, the board's own width
and height. The corner in the first of them is a fourth check, and the widest
residual of the four at 0.23 mm, which is what the derived positions' +/-0.2
is rounded from. The socket's own moulding is read off the same image but off
a rectangle rather than a circle, and is quoted at +/-1 mm.

**That corner is also the only thing proving which way up the drawing is
read**, and the first version of the script did not check it. It named the
four hole rings by which half of the image each fell in and said in a comment
that this asserted the 180 degree turn. It asserts nothing: a picture the
other way up has one ring per quadrant too, and the hole rectangle is
symmetric, so the fit comes out with the same 8.1767 px/mm either way. Turn
the image and the script ran happily on to `X -20.04 .. 64.83` and only died
later, in the standoff search, for reasons that had nothing to do with the
orientation. What is *not* symmetric is where those holes sit in the board:
3.50 mm in from one end of an 85 mm board and 23.50 in from the other. So the
check is that the board's lower-left corner comes back at the origin, and a
view read the wrong way round misses it by twenty millimetres -- against the
0.17 and 0.23 it is out the right way round, which is why the tolerance on it
can be a generous millimetre and still never be in doubt.

Adding it moved the script's headline figure, which is the worst residual on
any check the fit did not use: 0.12 mm, the board's own width and height,
before, and 0.23 mm, this corner's Y, after. The quoted +/-0.2 is the same
either way, because the script rounds -- `max(0.2, round(worst, 1))` -- but
`parts.py`, this file and `TODO.md` all said 0.12 was the worst of
everything, and they say what it is the worst of now.

Two things fall out that matter to whoever is cutting the plate. The card's far
end lands at X 85.07 -- the M.2 specification puts the retention screw's
half-moon cutout on the module's far end edge, so the card ends where the screw
is -- which is a hair past the Pi's 85 mm edge, and the standoff boss reaches
88.00. That is the Ethernet and USB edge, which the Pi's own connectors already
overhang by 2.96 and 2.24 mm, so 3.00 is the figure to allow rather than 2.96.
The assembled envelope note on the sheet now says 88.00 x 57.32 mm, and it says
that because `_sheet_text` counts a phantom part drawn in detail into the
envelope; without that it would have printed 87.96 and contradicted the note
above it.

The card itself is the specification's 2280 outline with SQRL's own extra
millimetre: "Acorn should fit comfortably in most M.2 slots, but it is one
millimeter wider than the official specifications. Ensure you have clearance."
Their site is gone and the Internet Archive's 2020 capture is the source. The
CLE-215+ carries a heatsink whose extent nobody publishes, so none is drawn and
the sheet says no height is claimed.

**What it is called.** `ACC-HAT-M2POE`, by the two rows it needs in
`tools/layout.py`. The part key is `waveshare-poe-m2-hat-b-acorn`, which
names the vendor and Waveshare's variant letter because that is what somebody
buying one types; the title block already prints both, so `ACC_STEMS` drops
them and the file is `accessories/output/poe-m2-hat-acorn.svg`. `ACC_NAMES`
cuts that stem to the name a drawing carries: HAT, because the thing sits on
the Pi's 40-pin header and bolts through the Pi's four mounting holes, which
is the test `raspmod-vs-pmod-hat.md` applies and the one the Raspmod, filed
under the same word, fails. Not the specification's shape: that is a
65 x 56.0/56.5 mm board and this is 85 x 56, and nothing published says
whether it carries the ID EEPROM, so neither is claimed. Then M2POE, five
characters for what it adds to the Pi underneath it, an M.2 slot and Power
over Ethernet. The stem itself is what the file is called and is allowed to
say more, which is the whole point of the split.

**Where it lives.** `accessories/`, even though the outline on the sheet is a
Raspberry Pi's. The numbers that are new are hand-curated from a
dimensioned vendor image and two specifications, which is exactly what
`accessories/parts.py` is for and exactly the class of source the PoE splitters
there came from; `raspberry_pi/boards.py` is generated from Raspberry Pi Ltd's
drawings and nothing hand-curated belongs in it. The Raspberry Pi family also
shares one view frame and one bound copy across three sheets that are defined
as "each with a Digilent Pmod HAT Adapter overlaid", and a fourth sheet with a
different overlay would have had to be held out of both anyway.

**One overlay, not two.** The obvious shape is the HAT overlaid on the Pi and
the card overlaid on the HAT, and the drafting library has no nesting. It does
not need any: the card's position *is* the HAT's geometry -- the socket and the
standoff are what put it there -- so the card is one of the HAT overlay's own
features, and `POE_M2_HAT_WITH_ACORN` is the HAT with that feature added.

The drafting change is `overlay_detail`, off by default so that not a line
moves on any sheet that already existed. With it on, an overlay's holes and
component bodies are drawn in phantom too, they go into the view's bounding
box, the ordinate chain and the assembled envelope, and they get their own two
schedules headed with the part's own name -- `WAVESHARE POE M.2 HAT+ (B):
HOLES` and `: BODIES`, not the word "phantom", because a table of holes called
2230 to 2280 says nothing about whose standoffs they are and a reader who has
not reached the notes yet will take an unattributed schedule for the board's.
Four details were each wrong first:

- A phantom hole that lands on one of the host board's own holes is drawn
  once, by the host. The HAT bolts through the Pi's four mounting holes, and
  drawing both put a dashed circle a fortieth of a millimetre outside a solid
  one, which reads as a defect rather than as the coincidence it is. The four
  holes stay in the HAT's own data, where they are its geometry and where its
  schedule is not complete without them; it is the *drawing* that shows each
  of them once.
- The detail goes on after the board's own features, not with the overlay
  outline. The board's component bodies are filled, the card runs the length
  of the Pi and ends over the Ethernet jack, and drawn in one pass with the
  outline the 2280 standoff and the card's far end -- the one thing the sheet
  exists to show -- vanished under that fill. The outline still goes on first:
  it is the edge of the part, not a thing sitting on the board.
- A phantom body is an obstacle for balloons the way the **board outline** is,
  not the way a component body is: its edges are hard for a balloon to sit on
  and free for a leader to cross. Treated as a filled rectangle, the card --
  eighty millimetres of it -- forbade two thirds of the board, and
  `check_balloons.py` reported the Pi's USB-C balloon parked across its lower
  edge in the one corner the placer had left.
- A phantom body is named inside its own outline, and the name has to be short
  enough and the paper under it clear. The full name ran over the Pi's USB
  ports; centred, the shorter one ran through the mounting hole column's
  ordinate witness line. It now uses the feature's designator where there is
  one, keeps the full name for the schedule, and is drawn only where it clears
  the host's own parts -- which is what a designator is for.

Two smaller things the sheet does not show, and therefore does not carry.
`ACCESSORIES` in `accessories/parts.py` means "drawn as the subject of a sheet
of its own"; the M.2 HAT is never that, so it is not in there.
`check_balloons.py` walks every sheet the generator draws, so it sees the HAT
where it is drawn, on the assembly sheet, with the Pi under it. And the HAT
carries no `tolerance` override, because that field can only ever reach a
title block belonging to the *subject* of a drawing: on this sheet the general
tolerance is the Pi's, which is right, and what the reader needs about the
phantom part is in the notes and in the heading of its own two schedules.

Fitting all that in cost a round of trimming. Putting the HAT's four mounting
holes back into its schedule is four more table rows, the standoff thread and
the missing-Z note are two more lines of notes, and the annotation column ran
out by thirty millimetres. The sources kept their figures and lost their
padding -- the M.2 citation is now the two sections the drawing rests on, the
SQRL quotation elides the sentence between the two halves that matter -- and
the notes lost the sentence that said what the phantom schedules contain, now
that those schedules are headed with the name of the part they belong to.

## RPICAM-OVER-ACORN, back from a branch of its own

Issue #7's branch was split on 25 September 2026 so that it would wait on
the Camera Module v1.3's branch alone. This sheet came off it then, because
the card, where it is seated and the HAT's standoff are all imported from
`accessories/parts.py`, and those are the M.2 HAT branch's, so it was kept as
one commit on `issue-7-camera-over-acorn` until that branch was under it. It
comes back as it was. What was written about it at the time is below.

It is also the second place Z is not measured from the subject's own face:
the Acorn is a card seated in a HAT above the Pi, roughly 16 mm up. Set from
the Pi, at 89.3 mm the picture at the card was 73.89 x 55.41 against a
90 x 67.50 frame, so the 80 mm card did not fit at all. Nobody publishes the
Pi-to-card offset -- Waveshare dimension no height on their drawing,
`accessories/parts.py` carries none either, and the CLE-215+'s heatsink is
unpublished -- so both Acorn frames are set from the card's own top face,
the HIGHEST plane either target reaches, and everything below it is covered
by more than the frame, which is the safe direction. And its two frames are
not nested: neither contains the other.

The widest drawing name in the set is now `RPICAM-OVER-ACORN`, 37.70 mm at
the ISO 3098 floor, 0.35 mm inside the quarter-width cell the DRAWING NO no
longer has to fit.

### The Acorn, and where the card sits

The card itself needs no branch: the PCI Express M.2 specification gives Type
2280 as 22 x 80 mm, and SQRL's own archived product page adds the millimetre
-- "it is one millimeter wider than the official specifications" -- so 23 x
80, with both citations on the sheet.

Where it *sits* is `accessories/parts.py`'s, which `ACC-HAT-M2POE` is drawn
from: the connector datum at X 5.07, the module axis at Y 18.26, the HAT's
own 85.00 mm width and the 3.00 mm the 2280 standoff projects past it.
Nothing is copied -- the card feature itself is imported, so the rectangle on
this sheet is the rectangle on that one. The assembly's 88.00 x 57.32 mm
envelope then falls out of this repository's own Pi 5 data: the Pi's own
assembled *envelope*, connectors included, is 87.960 x 57.320 over an
85 x 56 board, and the standoff takes the 87.960 to 88.00.

The boss itself is not drawn. When this was written, drawing it would have
meant restating a fourth figure, its ø5.87, for a circle 2 mm outside the
Pi's own Ethernet jack; the note carries the 88.00 instead.

Its LEDs are simply not published. SQRL issued no mechanical drawing and the
company's site is gone, so there is no indicator frame for the Acorn: frame B
is the card. The sheet says that rather than inventing one.

### Rebased onto #25, 30 September 2026

`accessories/parts.py` as it merged carries more than this sheet was written
against: the boss is `POE_M2_BOSS_DIA`, the card's size is `ACORN_WIDTH` and
`ACORN_LENGTH`, and the M.2 specification, SQRL's page and Waveshare's
drawing are `Source`s of the part's own, which `ACC-HAT-M2POE` prints. The
sheet had its own shorter copies of those three. Printing the part's instead
made the sources column long enough to push the plan from 1:2.5 to 1:5, so
the sheet now cites the module and that sheet in one line, the way the Arty's
cites `fpga/boards.py` and not Digilent, and "both citations on the sheet"
above is no longer so: they are one cross reference away. The figures in its
frame notes and tolerance are interpolated from the module rather than typed.
With no quotation left on the sheet from a page this family does not fetch,
`verify_optics.py` no longer lists any as cited from elsewhere.

Nothing moved: the card is still 23 x 80 at X 5.07 and Y 18.26, and the far
edge is still 88.00. That edge is the declared 85.00 + 3.00; the module's
own geometry, the 2280 standoff at 5.07 + 80 with half its ø5.87 boss, puts
it at 88.005, which is the same number at two decimals, and which
`ACC-HAT-M2POE`'s note prints as 88.00. The frames and every height came out
as the README had them.

Rendered for the first time, the card's name written on it ran through frame
B's axis mark and into the Pi's RJ45 body: at 1:2.5 the card is a 32 x 9 mm
strip with both camera axes in its middle, and no part of it clear of them
is as wide as "Acorn" at the ISO 3098 floor. So the legend names it -- the
phantom line is "Adjacent part or connector body, and the Acorn CLE-215+" --
and frame B, whose target it is, marks it on the view.

### Only the LEDs, 30 September 2026

Asked for on the PR: "The only part of the acorn that needs to be seen is
the leds at the end of the acorn." So the sheet frames them alone, and the
whole assembly and the card go, with everything above that says the LEDs are
not published and that frame B is the card. They are not published, but
they can be measured.

**Where they are.** Five, at the card's far end on its component side, the
heatsink side, which is up in the HAT: four silkscreened A1 to A4 in a
column on the +Y side of the retention screw's half-moon, and one
silkscreened PWR on the -Y side. The Internet Archive kept the banner off
SQRL's Acorn page, `images/acornBanner@2x.png` captured 28 September 2019: a
CLE-215 and a CLE-215+ side by side, cut out of their background at about
15 px/mm, with the far end of each clear of the heatsink. That is what
`accessories/measure_acorn_leds.py` measures. Its own product renders are
no use: `acorn-final@2x.png` is an earlier layout, with a connector strip
and two plated holes by the LEDs, and `product-diagram-215@2x.png` shows the
underside, and the top only under its heatsink.

What else was looked for, and what it gave:

- RHS Research's NiteFury and LiteFury repository has a schematic PDF and a
  bill of materials, no board file. The four user LEDs are D5 to D8 there,
  green 0402s, with a red NOT READY and a green POWER besides; the Acorn's
  photographs show D8 to D5 beside A1 to A4. The connector end of the
  LiteFury and NiteFury looks the same as the Acorn's in the photographs;
  their LED end is under their heatsink in both product photographs, so the
  layout is not shown to be shared there, and nothing positional is taken
  from them. Their 0402 is not the Acorn's LED either, which is visibly
  larger.
- Enjoy-Digital's shop photograph of the LiteX Acorn baseboard with a
  shipping CLE-215+ in it show the same column and PWR at the same end,
  clear of the heatsink and just past its blower; a tweet of theirs on the
  LiteX wiki shows them lit, green.
- A Hackaday project's photograph shows a green board with the same A1 to
  A4 and PWR arrangement lit, but it is a different board -- wider than an
  M.2 card, with the earlier render's connector strip -- and is not used.
- eBay listings could not be read without a browser, and were not needed.

**How well.** The two cards are fitted separately, 80 x 23, the heatsink's
overhang, the cable loop and the narrower finger strip excluded from the
edges; rms 0.2 to 0.3 px an edge. The photograph leans 11 and 15 degrees,
which the homography takes out. Scale checks the fit does not use: the
finger pitch, 0.494 and 0.4865 against 0.50, and the half-moon cutout, 3.32
and 3.24 against 3.50 -- the retoucher painted the cutout black, so its
edge is the plating's, and it is the worse of the two. The two cards agree
to 0.22 mm, the readings by eye against an automatic reading to 0.15. The
worst scale error, 7.3 %, at A1's far edge 10.62 mm from the half-moon, is
0.78 mm; with the 0.22 that is +/-1.0 mm. The two cards are one shoot, so
their agreement is one term of the error bar, not the whole of it.

The photographs also put the half-moon 0.31 and 0.49 mm to +Y of the card's
own centreline. That is inside the scale error across 11.5 mm, and the card
stays drawn centred on the HAT's axis; the LEDs are located from the
half-moon, which is where the screw is, so it does not move them.

**The frame.** The LEDs' union is 2.26 x 14.47 mm, so the frame is 18.35 x
24.47 with its long side along Y, over X 83.59, Y 21.65. The heights are
24.3 at 65 degrees, 24.5 on the autofocus module, 12.6 at 120, all from the
card's top face, and none in focus: the autofocus module's 80 mm is more
than three times as far. At 80 it is sharp and the column is 460 of the
sensor's 2592 columns long; TODO has it.

**Occlusion.** The camera is over the LEDs, which is what the frame model
does anyway, and it is the right place: the blower stands just short of the
column on the connector side, and from above the column no ray to an LED
passes over it. The camera board, 25 mm across, does overhang the blower in
plan; the sheet gives the board's underside, Z + 5.20, and says to raise
the camera if the blower is taller. Nothing is above the card in the HAT:
the Pi's USB and Ethernet jacks are under the HAT, not over the card.

**The sheet.** One frame, as `issue-7-camera-over-arty-ethernet` has for the
Arty's Ethernet LEDs, and the first single-frame sheet to be rendered. Three
things in `camera_sheet.py` had never met a frame this small or this far
from the datum:

- the lateral dimension ran from X0 Y0, 74 mm outside the front elevation,
  across the end elevation. Where the datum is not in the view it is now an
  ordinate: the axis's extension line carried down, "X 83.59" at its end;
- the 120 lens's camera, 12 mm under the stock lens's, covered the stock
  lens's arc and angle, so where a lower camera is in the way the arc comes
  up into the gap above it;
- at the plan's 1:2 the LEDs are a millimetre wide and the axis mark, filled
  white, sat on A4. The mark is left unfilled where an indicator is under
  it, and `Subject.plan_callout` names the target with a leader, arrowed
  rather than dotted so as not to hide PWR.

Each only acts where the datum is out of the view, a camera is in the way,
an indicator is under the mark or a subject asks for a callout. Only the
third reaches another sheet: frame B's axis mark on `RPICAM-OVER-ARTY`
reaches over the Arty's LED rows, and is unfilled now too.

`ACC-HAT-M2POE` does not draw the LEDs. It is the plan envelope of the
assembly, for an enclosure; an indicator inside the card changes nothing
about that.

### The autofocus module is not the B0176, 3 October 2026

The sheets took "the autofocus camera" to be Arducam's B0176 and so said
nothing focuses on the Acorn's LEDs below its 80 mm. The module on the
Acorn's host is not a B0176: it is the "AF-65 Degrees" variant of an
AliExpress listing, a clone of the v1.3's board -- "Raspberry pi Camera Rev
1.3" on the silkscreen, the same four holes -- with an OV5647 in a square
voice-coil can, its flex marked P5V04A2, and no Arducam marking. The listing
publishes no focus distance, focal length, F number or driver chip; the 65
in the variant's name is the only optical figure. Similar listings say the
same or less: one by another seller gives "Diagonal angle: 65 degree", which
is the stock lens's diagonal. So the module is its own lens record, with the
stock lens's angles, focal length and F number ASSUMED, and its close limit
None: the sheets say it is not published rather than borrow the B0176's.

The rpi-hwid audit confirms it is motorised -- a lens driver at 0x0c beside
the OV5647 at 0x36, behaving like a DW9714 but not identified -- and its
focus sweep shows the coil moving focus nearer, but no object distances were
recorded, so it gives no close limit either.

What focuses closer is the module's, so the sheets now give each variant:

- the v1.3 as sold, Raspberry Pi's "Approx 1 m";
- the v1.3 with its lens unscrewed. Raspberry Pi's own post on it gives no
  distance. Two forum users measured it in 2013: jbeale "about 6 cm" as the
  closest, after "170 degrees: focus at 7 cm", and towolf 3 cm where the
  lens starts to fall out. The 6 cm is used, and called a forum user's;
- a lens focused by hand: Arducam's B0031, "From less than an inch to
  infinity", so 25.4 mm at most;
- the motorised module used here: not published;
- the B0176, "80mm to infinity", kept as a comparison and marked as not the
  module used.

The height in focus is the higher of the close limit and the field-of-view
height plus f: a lens focused at Z stands f Z / (Z - f) from the sensor and
covers what a pinhole at Z - f does. On the Acorn's LEDs that is 60.0 mm for
the v1.3 unscrewed and 27.9 for the B0031; for the module used, it waits on
a measured close limit.
