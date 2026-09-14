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

- **The PDF carries one varying field and it is not where you would look.**
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
  `make clean && make diagrams` cycles compared across all 65 files.
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
