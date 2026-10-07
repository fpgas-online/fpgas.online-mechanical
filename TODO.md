# TODO

Status key: `[ ]` not started, `[~]` in progress, `[x]` done. Sections are not
numbered, so that two branches can each add one: cite a section by its title
or its issue number.

Everything the request asked for is done, and all four rounds of both reviews
have been acted on. The work is pushed to github.com/fpgas-online/fpgas.online-mechanical. Two balloon leaders on the Pi 4B and Pi 5 still cross the
phantom Pmod host JC; that is a physical overlap, not a placement fault, and
`tools/check_balloons.py` reports it every run.

Since then: two A4 drill templates, printed at 1:1 and drilled through, with a
checker that measures the finished PDFs rather than trusting them.

## Data collection  -- DONE
- [x] Tiny Tapeout: identify every mechanically distinct demo board revision
- [x] Tiny Tapeout: extract outline / holes / Pmods / USB-C / 7-seg / LEDs from KiCad
- [x] Raspberry Pi: download official mechanical drawings (3B, 3B+, 4B, 5)
- [x] Raspberry Pi: extract outline / holes / USB / Ethernet from DXF
- [x] Raspberry Pi: extract Pi 5 geometry from vector PDF
- [x] Digilent Pmod interface specification header geometry
- [x] Digilent Pmod HAT Adapter geometry (photogrammetry, +/-0.75 mm)
- [x] Waveshare 25 W PoE -> USB-C splitter dimensions
- [x] Generic AliExpress PoE -> micro-USB splitter dimensions
- [x] Consolidate everything into each family's own data module with per-value source attribution

## Drawing engine  -- DONE
- [x] Minimal 2D drafting library: sheet, border, title block, views
- [x] Dimension primitives: linear, ordinate, leader, balloon, datum
- [x] Hole tables, feature schedules, notes and source blocks
- [x] SVG output plus PDF/PNG conversion

## Diagrams  -- DONE
- [x] Tiny Tapeout demo boards, 8 sheets, one per production revision
- [x] Raspberry Pi 3B/3B+ (combined) / 4B / 5  (the 3A+ was dropped on
      request; HDMI and audio connectors dropped on request)
- [x] Raspberry Pi + Digilent Pmod HAT Adapter overlay, on every Pi sheet
- [x] Digilent Pmod HAT Adapter on its own
- [x] Generic PoE -> micro-USB splitter
- [x] Waveshare 25 W PoE -> USB-C splitter

## Tiny Tapeout generic mounting plate  -- DONE
- [x] Overlay every TT board revision in a common Pmod-referenced frame
- [x] Choose plate outline and hole pattern
- [x] Mounting plate fabrication drawing
- [x] Board fitting guide, one view per revision
- [x] Cut file: `tinytapeout/mounting_plate/output/tt-generic-mounting-plate.dxf`

## Review
- [x] Sub-agent code review, round 1 -- acted on
- [x] Sub-agent mechanical drawing review, round 1 -- acted on
- [x] Sub-agent code review, round 2 -- acted on
- [x] Sub-agent mechanical drawing review, round 2 -- acted on
      (S-2/M-8 fitting guide, M-13 PoE sheets, m-2 slot lengths, m-3 USED BY
      key, m-4 ISO 128 line types, m-7 balloon leaders)
- [x] Sub-agent code review, round 3 -- acted on
- [x] Sub-agent mechanical drawing review, round 3 -- all 20 findings acted on
      (dimension placement, note and title block contradictions, label
      ownership, legends, ISO 5457 frame, URL breaking, lettering sizes)
- [x] Sub-agent code review, round 4 -- acted on
- [x] Sub-agent mechanical drawing review, round 4 -- all findings acted on
      (projection symbol, assembled envelope, setback dimension, plate
      ordinate, general tolerance provenance, balloon on a feature, notes
      reading order, connector body on the plate)
- [x] Automated sheet checker (`tools/check_sheets.py`): text collisions,
      out-of-frame content, text under the 2.5 mm ISO 3098 floor
- [x] Automated arc check in the extractor: a resolved arc must pass through
      the point KiCad puts on it
- [x] `tinytapeout/mounting_plate/verify.py`: proves the finished plate accepts
      every revision, with a real M3 fastener clearance check
- [x] `tools/check_balloons.py`: reports every balloon leader that crosses a
      hard obstacle, and by how much

## Repository
- [x] README explaining what is here and how the numbers were obtained
- [x] Apache 2.0 licence

## Repository layout  -- DONE
- [x] Group by subject, not by kind: each family owns its data, its extractor
      and its sheets
- [x] Mounting plate under `tinytapeout/`, drafting library under `tools/`
- [x] `tools/layout.py`: one answer to "where are the sheets"
- [x] A README per directory, each about that directory
- [x] `check_sheets.py` also checks every relative link in every README
- [x] `output/` reproduces byte for byte: clocks, tool version strings and
      GUIDs pinned in `tools/reproducible.py`, so a rebuild leaves
      `git status` silent, on a second machine as well as the first

## Drill templates  -- DONE
- [x] A4 portrait 1:1 template for the mounting plate itself
      (`TT-MP-DRILL`)
- [x] A4 portrait 1:1 template for the chassis the plate bolts to
      (`TT-MP-CHASSIS`)
- [x] Printed scale bar per axis, so a scaled print is caught before drilling
- [x] `tools/check_drill_template.py`: measures the PDFs back and proves
      every hole lands where the plate data puts it

## Sheets named, not numbered  -- DONE
- [x] `tools/layout.py` derives every drawing name from the sheet's own file
      stem, so a sheet added on a branch cannot collide with one added on
      another
- [x] The generator, the README builder, the notes, the schedule cross
      references and `accessories/compare.py` all ask for it; no drawing name
      is written out by hand anywhere
- [x] DRAWING NO widened to half the title block, measured against the longest
      name at the ISO 3098 floor; `check_sheets.py` reads the cell back and
      fails on an overflow or on a sheet not carrying its own name
- [x] `check_pdfs.py` reads the bound copies: every page is a committed sheet
      and every bookmark opens with that sheet's name
- [x] Stems short enough to read as labels: a demo board sheet is its first
      revision and its last, an accessory drops the vendor its title block
      names, and the mounting plate's three satellites drop the PLATE the
      family prefix already says
- [x] Names short enough to quote: at most four or five characters behind the
      prefix, which the stems cannot give and do not have to. A family may
      have a rule in `FAMILY_NAME_RULES` that cuts its stem down to a name --
      a demo board is named for the first revision it covers (`TT-DB-V121`,
      `TT-DB-TT123`) and an accessory by a table, the kind of part and which
      one (`ACC-HAT-PMOD`, `ACC-POE-MUSB`). No file moves, so every link,
      preview and branch that cites a stem keeps working
- [ ] The open pull requests each rename their own sheets on top of this

## FPGA development boards  -- sheets done, four items open
- [x] Arty A7 from Digilent's DXF and PDF plot; no mounting holes, rubber feet
- [x] ULX3S from KiCad at the four tags sold, required to agree
- [x] PYNQ-Z2 from TUL's STEP assembly; LEDs not in the model, said in words
- [x] ButterStick from KiCad r1.0a, SYZYGY standoff holes in the schedule
- [x] Cynthion from KiCad at r1.4.0, the initial production release; four USB
      ports took two new numbers at the end of the family schedule and the
      status LED row a third, and its mezzanine receptacle J5 took the
      family's first expansion slot
- [x] Ultra96-V2 from Avnet's Altium "Mechanical and Drill" plot, scale
      recovered from the outline and checked against the 96Boards CE
      specification; no Pmod, no Ethernet
- [x] Zybo Z7 from the same drawing pair as the Arty A7, with Digilent's STEP
      assembly naming which of the plot's outlines is which
- [x] `fpga-sheets.pdf`, every FPGA sheet bound into one document
- [ ] PYNQ-Z2 LED positions, by photogrammetry from TUL's product photo if
      no vector source turns up
- [x] `dims.ordinate_reach` and `_view_margins`: a view whose ordinate chain
      staggers a label into a second lane is given the room out of the height
      the sheet has spare, instead of a flat 30 mm on the chain's edge. Only
      a sheet the centring leaves short moves: the Zybo Z7, short by 9.17 mm,
      and the Cynthion, short by 3.33; no other sheet changes
- [ ] Check the Pmod HAT Adapter's pin 1 corner against the adapter's
      silkscreen; `accessories/parts.py` has it opposite the Pmod convention
- [ ] Cynthion's three side buttons and its two SWD connectors are not drawn.
      The buttons reach 2.50 mm past the left and right edges and a case
      needs holes for them, which is in the notes and the envelope figure but
      is not a feature with a balloon
- [ ] Ultra96-V2 connector shells: the plot has pads and no body outlines,
      so every feature on FPGA-ULTRA96-V2 is a pad extent. Avnet's product
      page is indexed as offering STEP models of the board and of its heat
      sink, and the page itself answers with an Akamai Bot Manager
      interstitial; with one of those models the shells and the heat sink
      envelope could be drawn instead

## Raspmod, the other Pi-to-Pmod adapter  -- DONE
- [x] Pat Deegan's TT Demoboard To Raspi, from its KiCad board file at a
      pinned commit; plugs checked to sit on the demoboard's 22.86 mm pitch
- [x] Pmod headers can be plugs as well as hosts; a part can be on the
      underside; the depth-dimension lane keeps clear of the dimension's
      own extent rather than the whole board
- [x] `accessories/raspmod-vs-pmod-hat.md`: both adapters' Pi pin maps and
      mechanics side by side, tables regenerated from the data modules
- [ ] Measure how far in front of the demoboard's front edge the Raspmod's
      faces sit when mated: the plug pin length and the host socket depth
      are footprint figures, not measured ones

## The three Raspberry Pis on one outline  -- DONE
- [x] `RPI-ALL`: the Pi 3B/3B+, 4B and 5 superimposed on the
      85 x 56 outline they share, everything common drawn once in continuous
      line and everything that moves once per model in that model's own line
      type
- [x] A balloon ring carries its model's line type, because three outlines on
      top of one another leave nowhere for a leader's dot that belongs to one
      of them alone
- [x] One leader to each place, with a balloon per model on it in model
      order (ISO 6433 grouped references), the rows in a column outside the
      board; the overall height moved to the left to leave the right to
      them
- [x] Per-model feature and hole schedules, the connector swap stated in
      words, and the union envelope, 88.00 x 57.32 mm
- [x] `tools/check_balloons.py` watches the new sheet, and every other: it
      walks `generate_diagrams.draw_sheets()`, and reports a leader crossing
      another leader or a ring, a feature it does not point at, or a
      dimension line
- [ ] Ask whether the Pmod HAT Adapter belongs on it after all. It is left
      off because its host positions say nothing about how the models differ
      and its pin fields fall exactly where they do differ; if a plate
      designer wants the two questions answered on one page, a second view
      on the same sheet would be the way rather than an overlay

## Orange Pi PC  -- DONE
- [x] Find what Shenzhen Xunlong publish: manual, schematic, datasheet, wiki,
      product page, the old download host and the forum, all read. There is
      no drawing, and SCRATCH.md says where it was looked for
- [x] `RPI-OPIPC`, measured from two pairs of photographs, linux-sunxi's
      v1.3 and Xunlong's v1.2, top and bottom: holes and header to
      +/-0.4 mm, parts to +/-1.1: no reading, and no check on holes and
      header, further than that from what is drawn
- [x] `verify_orangepi_pc.py` in `make check`: the header's pitch and length,
      the board's proportions, standard part widths against the Pi drawings,
      and the case standoffs, Gachin's model, landroo's cut-outs and
      Xunlong's PC Plus drawing
- [x] The Pmod HAT Adapter overlay, moved onto this board's header, and a
      note, worked out from the geometry, that its holes miss the board's
- [x] The scale across the board from the header: fitted to the edges alone,
      both bottom views put pin 1 to pin 39 0.5 to 0.7 % long, and the holes
      79.40 apart where most cases and the PC Plus say 78.96 to 79.15. On the
      header's scale they are 78.96
- [ ] Why the edges read narrow: on the header's scale the board is 84.44
      and 84.61 wide, not 85. Probably the edge finder lands inside the
      routed edge; an edge finder that did not would let the header go back
      to being a check
- [ ] Heights: none are measured, so whether the Pmod HAT Adapter clears
      the IR receiver, the audio jack and the debug UART pins under it is not
      established. The oblique linux-sunxi views might give them
- [ ] The debug UART header J3 and the camera connector CON1 are measured and
      checked but not drawn: on the sheet their balloons, or the ones they
      crowded out, could only cross the adapter's hosts JB and JC
- [ ] How far a microSD card stands out of its socket, and the audio jack's
      width, which is the narrowest part checked against the PC Plus drawing
      at 5.15 mm against 6.20

## Icepi Zero  -- DONE
- [x] `FPGA-ICEPI-ZERO` from cheyao's KiCad board file at the `v1.3` tag,
      the mass production files, and again at the re-annotated tip of the
      same revision, the two required to agree on every position
- [x] Nothing found by reference designator, because the re-annotation moved
      them: the programming port is the receptacle on the FT231X's data
      pair, a user LED is one driven from `/LED0` to `/LED4`
- [x] Raspberry Pi Zero outline and hole pattern, checked against the figures
      on Raspberry Pi's own Zero drawing before the note claims it
- [x] The 2x20 GPIO position is not fitted, and its pins are checked to sit
      on the Raspberry Pi arrangement before the note says so
- [ ] Measure how far a card in the microSD socket stands proud of the left
      edge; the board file gives the socket, not the card
- [ ] The two underside buttons are in a note rather than drawn, and the
      third USB-C port shares feature 2 with the second: both want a feature
      number, which means renumbering the family and restamping its sheets

## The assembled envelope leaves out the Pmod host bodies
- [ ] `_sheet_text` builds the "assembled envelope" note from the features
      only, and Pmod hosts are not features, so wherever a board's host
      bodies stand outside its outline the figure is short by that overhang.
      Seven issued sheets: the six demo boards, whose right-angle housings
      hang off the front edge (TT-DB-V33 goes 86.65 -> 95.20 mm), and the
      PYNQ-Z2, whose hosts reach 1.24 mm past the right edge (137.60 ->
      138.84). Widening the computation needs the demo board output and
      `tinytapeout-sheets.pdf` rebuilt with it, so it is a change of its own.
      Cynthion states its own figure through `BoardSpec.envelope_note`
      meanwhile; that field should go when this is fixed.

## Raspberry Pi camera modules  -- DONE
- [x] `RPICAM-2`, Camera Module 2, from `RPI-CAM-V2_1`, a 1.5055:1 plot with
      every figure outlined; scale recovered from the 21 x 12.5 hole rectangle
- [x] `RPICAM-3`, Camera Module 3 standard and wide, from `RP-008153-DS-1` and
      `RP-008155-DS-1`, true 1:1, one sheet after the two were read separately
      and required to agree
- [x] A `lens` feature kind, drawn with a centre mark at the optical axis
- [x] `raspberry-pi-camera-sheets.pdf`, the sheets bound into one document
- [x] `RPICAM-1`, the Camera Module 1, the OV5647 board lettered v1.3.
      Raspberry Pi never drew it, so it is hand-curated in `v1.py` from Gert
      van Loo's hand-measured sheet of 21 May 2013, with Raspberry Pi Spy's
      caliper measurement as a second opinion; kept in this family, not
      moved to `accessories/`, because the family is the subject
- [x] `measure_cm1.py` scales what that sheet draws and does not dimension,
      the scale checked against every figure it prints: worst 0.09 mm
- [x] `verify.py` holds `v1.py` to its cached sources, and its hole pattern
      to Raspberry Pi's Camera Module 2 and 3 drawings, 0.023 and 0.008 apart
- [ ] Measure a v1.3 board in hand to close what the sources leave open:
  - [ ] The lens module's near side from the connector edge, which the two
        measurements give as 5.1 and 5.5, the second to the half millimetre;
        that spread is the optical axis's +/-0.65, and several boards
        measured would say whether it is glue or error
  - [ ] The hole diameter with pin gauges: both measurements say 2 and
        neither finer, the Camera Module 2 drawing 2.2; the sheet carries
        +/-0.2 until then
  - [ ] The FFC connector's length along the edge, scaled at 19.45 for the
        body and 20.73 over the latch ears
  - [ ] The height of the sensor flex over J2, scaled at 1.18, and of D1, R9
        and every other part on the lens side, which no source gives
  - [ ] Whether anything but the connector is on the underside, and how
        tall it stands
  - [ ] The lens's clear aperture
- [ ] The High Quality Camera, `RP-008200-DS-1`: needs a round feature and a
      profiled outline before `render_board` can draw its ø36 C/CS mount and
      its tripod boss honestly, and its FFC connector is in no plan view
- [ ] The Global Shutter Camera, `RP-008195-DS-1`, if anyone wants it

## Where the camera goes  -- DONE
- [x] OV5647 optics from the vendors' own words: sensor, focal length, the
      65 and 120 degree lenses' declared field of view, and the focus range;
      every quote checked against the cached page by `verify_optics.py`
- [x] The pinhole model established rather than assumed: the declared 53.50
      and 41.41 come back out of the declared 3.60 mm and 2592 x 1944 to four
      thousandths of a degree, and only against the active pixel array
- [x] A sheet per subject, each named for what it is over:
      `RPICAM-OVER-PLATE`, `RPICAM-OVER-ARTY`, and `RPICAM-OVER-ACORN` for
      an Acorn CLE-215+ in a Waveshare PoE M.2 HAT+ (B) on a Pi 5
- [x] Two frames per subject, whole subject and indicators, and one on the
      Acorn's, its LEDs: each the smallest 4:3 rectangle holding its target
      plus 5.00 mm all round, with the camera height for both lenses and the
      focus verdict against the published near limit
- [x] `RPICAM-OVER-ACORN` reworked for one module, the v1.3 with its stock
      lens, and lens-face heights: F 60.0 above the card, H1 = S + 60.0
      above the mounting plate, H2 = 60.0 - T clear of the highest point;
      the 120 degree lens and the other modules are off that sheet
- [x] Tim Ansell's report of 3 October 2026 recorded on the sheet and in the
      README: the autofocus camera about 10 cm above the Acorn's LEDs, in
      focus, wanting a crop -- of 3.97, DERIVED, the LED column 386 pixels
- [ ] The same rework for `RPICAM-OVER-ARTY`, `RPICAM-OVER-PLATE` and
      `RPICAM-LENS`, in a pull request of their own
- [x] Z measured from the plane the frame's target lies in, not the subject's
      own top face: the demo boards' indicators are on a board standing on
      standoffs above the plate, and the Acorn is a card seated above a Pi
- [x] `raspberry_pi_camera/verify_optics.py`: the quotes, the model, and
      every frame against its target and its height
- [x] The 120 degree lens's field of view: the B006604's own page gives the
      120 as a DIAGONAL, so the catalogue's 120 x 90 is rejected, and the
      catalogue's 96 x 72 for the same camera without its IR filter -- the
      diagonal split equidistantly, which Commonlands reproduce from a real
      fisheye -- is used
- [x] The autofocus module used here is its own lens record: the "AF-65
      Degrees" variant of an AliExpress listing, a v1.3 clone board, not the
      Arducam B0176 the sheets used to take it for. The B0176's "80mm to
      infinity" stays only as a comparison, marked as a different module
- [x] Focus per variant: the v1.3 as sold, unscrewed by hand (6 cm, a forum
      user's measurement), focused by hand (Arducam's B0031, "less than an
      inch") and motorised, each with the lowest height that both frames and
      focuses, the higher of its close limit and Z + f
- [x] Lens distortion, bounded rather than guessed: coverage of a plane is
      2 Z tan(A/2) whatever the projection, the frame's corners are inside a
      barrel-distorted picture, and the margin is checked to absorb the
      equisolid split and YXF's lens at every height
- [x] Both lenses drawn on the plate's and the Arty's position sheet, each with its camera at its
      own height, and `RPICAM-LENS` for every lens figure, declared and
      derived, and the depth of field
- [ ] The B006604's real projection. Nobody publishes its lens's focal
      length, F number or distortion; 2.17 mm is derived from its diagonal
      and F2.4 is YXF's for a lens of the same angle. A photograph of a
      ruler at a known height would settle H and V to a tenth of a degree
- [ ] The autofocus module's close limit. Its listing publishes none, and
      the rpi-hwid focus sweep recorded no object distances: a ruler or a
      target at measured heights under it, swept through its focus codes,
      would give one, and with it the module's height in focus
- [ ] The autofocus module's focal length and F number, which the sheets
      ASSUME are the stock lens's 3.60 mm and F2.9
- [x] A standoff height for the Tiny Tapeout plate: 8 mm, in
      `tinytapeout/mounting_plate/plate.py`, no shorter than Tiny Tapeout's
      own printed base stands the board, and `RPICAM-OVER-PLATE` adds it
- [x] The elevations lead: two per sheet, one per axis of the picture, the
      stock lens's declared angle in each plane drawn from the lens to frame
      A's edges, Z and the lens's X and Y dimensioned; the plan kept, smaller
- [x] The plate's frame A is every revision's board rather than the plate,
      set from the board face
- [x] Say what the diagonal does if it is read as the angle across, how far
      the stand may lean, how soft the stock lens is at these heights, and
      which published close limits each height is inside
- [x] Draw the Camera Module v1.3 over the lens from its own data, which
      bounds the entrance pupil by the lens's 5.20 mm
- [ ] `RPICAM-OVER-ETH`, the Arty with its Ethernet LEDs, is parked on the
      branch `issue-7-camera-over-arty-ethernet`, one source commit on top
      of this one. Its note cites the light pipe that brings those LEDs up
      from `fpga/light_pipe/adapter.py`, so it waits for the light pipe
      branch (issue #8, PR #29) to be on its base, then re-renders
- [x] The Acorn taken from `accessories/parts.py` rather than restated: the
      card feature, its seated position and its LEDs are that module's, which
      `ACC-HAT-M2POE` is drawn from too, so the card is one rectangle in one
      place
- [x] `RPICAM-OVER-ACORN` frames the Acorn's LEDs alone, A1 to A4 and PWR
      at the card's far end, with the camera over them: measured off SQRL's
      own product photograph by `accessories/measure_acorn_leds.py`, to
      +/-1.0 mm
- [ ] MEASURE S on the rig: the mounting plate's face, the base of the
      standoffs under the Pi 5, to the Acorn card's top face. Not published
      and, the hardware's owners say, not measured. Put it in
      `ACORN_STACK_S` in `accessories/parts.py` with its tolerance and
      source, and `RPICAM-OVER-ACORN` prints H1 as a figure
- [ ] MEASURE T on the rig: the card's top face to the highest point of the
      assembly, and note which part that is, the heatsink's blower or a part
      of the HAT. Into `ACORN_STACK_T`, and the sheet prints the clearance H2
- [ ] Measure the lens-to-LED distance on the reference Acorn, which is
      "about 10 cm" by eye, and how the camera is held
- [ ] The Acorn's LEDs measured on a card in hand, which would take the
      +/-1.0 mm off them: the photograph's own scale checks come out up to
      7 % short of the specification
- [ ] The v1.3's close limit with its lens unscrewed is one forum user's
      "about 6 cm"; raspi.tv's page gives none. Unscrew one over a ruler and
      measure it: F on `RPICAM-OVER-ACORN` is that figure

## A camera holder on the TT plate  -- DONE, unprinted
- [x] `tinytapeout/camera_holder/holder.py`: a portal of two window-shaped
      side frames and a beam, derived at import from the optics, the plate
      and the Camera Module v1.3 data, with the lens face at 150.00 above
      the plate face against the 148.77 the stock lens needs
- [x] The feet share the plate's own four M4 side fixings: no new hole
- [x] A carrier that turns a quarter at a time about the lens axis, because
      which way the OV5647's rows run on the module is not published
- [x] `verify.py`: the camera's height and position, every revision whole
      in the picture and unhidden, clear of every board, standoff and cable,
      every fastener
- [x] STEP solids, assembled and per part as printed; the beam as a DXF
- [x] The holder's sheets, bound into the Tiny Tapeout copy after the plate's own sheets
- [ ] Print one and put it on a plate. Nothing here has been built
- [ ] Check which way the picture's long side runs on a real v1.3 and set
      `QUARTER_TURNS` to it, so the sheet stops saying ASSUMED
- [ ] Measure the v1.3's small parts beside the lens -- LED D1 and R9 by MT1
      -- against the M2 screw heads on the lens side
- [ ] A focusable OV5647 would make the picture sharp as well as whole. If
      one is chosen, its lens height and hole pattern go in as a second
      `CameraBoard` and the holder is re-derived for it
- [x] A holder per lens: `TT-MP-CAM65` and `TT-MP-CAM120`, the lens face at
      150.00 and 83.00, sharing the beam and the carrier; `verify.py` makes
      every check of each and checks the two share those parts
- [ ] A 120 degree OV5647 on a board this carrier takes. `TT-MP-CAM120`
      carries a v1.3's board with the wide lens ASSUMED 5.20 mm proud of it,
      and has 1.00 mm to spare; a taller lens, any M12 fisheye, drops the
      face further than that and cuts the boards' edges off. Either a
      carrier for the B006604, a Pi Zero spy camera, from a measured drawing
      of it, or bosses cut to a measured lens

## An Acorn in a PoE M.2 HAT on a Pi 5  -- DONE
- [x] Identify the card: SQRL Acorn CLE-215+, M.2 2280 M-key, which is what
      "Acorn" means at fpgas.online
- [x] Identify the HAT: Waveshare PoE M.2 HAT+ **(B)**, the only one of their
      three that takes a 2280 card
- [x] Waveshare's dimension drawing transcribed as declared figures, and the
      M.2 socket and standoffs recovered from it by photogrammetry, checked
      three ways to 0.12 mm and a fourth, the board's corner, to 0.23
- [x] Card outline from the PCI Express M.2 Specification's Type 2280, with
      SQRL's own extra millimetre of width
- [x] `overlay_detail`: an overlay's holes and bodies drawn in phantom, in
      the view frame, the ordinate chain, the envelope note and their own
      tables; off by default, so no existing sheet moves
- [x] `ACC-HAT-M2POE`, the assembly sheet: the Pi 5 drawn, the HAT and
      the card phantom
- [ ] Heights. Nothing published gives the HAT's stack-up or the CLE-215+'s
      heatsink, so the sheet is plan only and claims no Z at all. A measured
      part would settle both; `ACORN_STACK_S` and `ACORN_STACK_T` in
      `parts.py` are where the two a camera needs go
- [ ] Check the derived socket footprint against a real board: it is the one
      figure here quoted at +/-1 mm rather than +/-0.2

## Pictures for the docs site  -- DONE for RPICAM-OVER-ACORN and TT-MP-PLATE
- [x] `tools/docs_images.py`: each listed sheet's views and whole sheet,
      light and dark, transparent, SVG and PNG, under `output/docs/`
- [x] `tools/docs_palette.py`: every colour's dark-ground value and its
      reason, held to WCAG 7:1 for text on the dark ground (4.5:1 on its fills) and 3:1
      for lines; an unmapped
      colour, an opacity or an unknown attribute stops the build
- [x] `tools/check_docs_images.py`: the committed pictures are what the
      committed sheet makes
- [x] `RPICAM-OVER-ACORN` pictured: its elevations and plan, heights table
      and legend
- [x] `TT-MP-PLATE` pictured (7 October 2026): the plan, legend, hole
      table and notes, for a builder fitting a board. Whole-sheet pictures
      PNG only, `SHEET_PNG_ONLY`
- [ ] The plate's whole-sheet SVG is over the commit-size hook's 400 lines:
      question mech-01 to Tim is open. When answered, drop it from
      `SHEET_PNG_ONLY` and commit the two SVGs
- [ ] The next sheets: give the renderer `docs_panels` and add the SVG to
      `DOCS_SHEETS`
- [x] The views print at A4 width (180 mm) with the smallest text at
      2.71 mm: the notes beside the plan are a panel of their own, so the
      widest panel is the 164 mm heights table and legend
