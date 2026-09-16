# TODO

Status key: `[ ]` not started, `[~]` in progress, `[x]` done.

Everything the request asked for is done, and all four rounds of both reviews
have been acted on. The work is pushed to github.com/fpgas-online/fpgas.online-mechanical. Two balloon leaders on the Pi 4B and Pi 5 still cross the
phantom Pmod host JC; that is a physical overlap, not a placement fault, and
`tools/check_balloons.py` reports it every run.

Since then: two A4 drill templates, printed at 1:1 and drilled through, with a
checker that measures the finished PDFs rather than trusting them.

## 1. Data collection  -- DONE
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

## 2. Drawing engine  -- DONE
- [x] Minimal 2D drafting library: sheet, border, title block, views
- [x] Dimension primitives: linear, ordinate, leader, balloon, datum
- [x] Hole tables, feature schedules, notes and source blocks
- [x] SVG output plus PDF/PNG conversion

## 3. Diagrams  -- DONE
- [x] Tiny Tapeout demo boards, 8 sheets, one per production revision
- [x] Raspberry Pi 3B/3B+ (combined) / 4B / 5  (the 3A+ was dropped on
      request; HDMI and audio connectors dropped on request)
- [x] Raspberry Pi + Digilent Pmod HAT Adapter overlay, on every Pi sheet
- [x] Digilent Pmod HAT Adapter on its own
- [x] Generic PoE -> micro-USB splitter
- [x] Waveshare 25 W PoE -> USB-C splitter

## 4. Tiny Tapeout generic mounting plate  -- DONE
- [x] Overlay every TT board revision in a common Pmod-referenced frame
- [x] Choose plate outline and hole pattern
- [x] Mounting plate fabrication drawing
- [x] Board fitting guide, one view per revision
- [x] Cut file: `tinytapeout/mounting_plate/output/tt-generic-mounting-plate.dxf`

## 5. Review
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

## 6. Repository
- [x] README explaining what is here and how the numbers were obtained
- [x] Apache 2.0 licence

## 8. Repository layout  -- DONE
- [x] Group by subject, not by kind: each family owns its data, its extractor
      and its sheets
- [x] Mounting plate under `tinytapeout/`, drafting library under `tools/`
- [x] `tools/layout.py`: one answer to "where are the sheets"
- [x] A README per directory, each about that directory
- [x] `check_sheets.py` also checks every relative link in every README
- [x] `output/` reproduces byte for byte: clocks, tool version strings and
      GUIDs pinned in `tools/reproducible.py`, so a rebuild leaves
      `git status` silent, on a second machine as well as the first

## 7. Drill templates  -- DONE
- [x] A4 portrait 1:1 template for the mounting plate itself
      (`TT-MP-DRILL`)
- [x] A4 portrait 1:1 template for the chassis the plate bolts to
      (`TT-MP-CHASSIS`)
- [x] Printed scale bar per axis, so a scaled print is caught before drilling
- [x] `tools/check_drill_template.py`: measures the PDFs back and proves
      every hole lands where the plate data puts it

## 11. Sheets named, not numbered  -- DONE
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

## 9. FPGA development boards  -- sheets done, four items open
- [x] Arty A7 from Digilent's DXF and PDF plot; no mounting holes, rubber feet
- [x] ULX3S from KiCad at the four tags sold, required to agree
- [x] PYNQ-Z2 from TUL's STEP assembly; LEDs not in the model, said in words
- [x] ButterStick from KiCad r1.0a, SYZYGY standoff holes in the schedule
- [x] Cynthion from KiCad at r1.4.0, the initial production release; four USB
      ports took two new numbers at the end of the family schedule and the
      status LED row a third, and its mezzanine receptacle J5 took the
      family's first expansion slot
- [x] Zybo Z7 from the same drawing pair as the Arty A7, with Digilent's STEP
      assembly naming which of the plot's outlines is which
- [x] Ultra96-V2 from Avnet's Altium "Mechanical and Drill" plot, scale
      recovered from the outline and checked against the 96Boards CE
      specification; no Pmod, no Ethernet
- [x] `fpga-sheets.pdf`, the eight boards, bound with the light pipe
- [ ] PYNQ-Z2 LED positions, by photogrammetry from TUL's product photo if
      no vector source turns up
- [x] `dims.ordinate_reach` and `_view_margins`: a view whose ordinate chain
      staggers a label into a second lane is given the room out of the height
      the sheet has spare, instead of a flat 30 mm on the chain's edge. Only
      a sheet the centring leaves short moves, which is the Zybo Z7, short by
      9.17 mm, and the Cynthion, short by 3.33; no other sheet changes
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

## 10. Raspmod, the other Pi-to-Pmod adapter  -- DONE
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

## 13. The three Raspberry Pis on one outline  -- DONE
- [x] `RPI-ALL`: the Pi 3B/3B+, 4B and 5 superimposed on the
      85 x 56 outline they share, everything common drawn once in continuous
      line and everything that moves once per model in that model's own line
      type
- [x] A balloon ring carries its model's line type, because three outlines on
      top of one another leave nowhere for a leader's dot that belongs to one
      of them alone
- [x] Per-model feature and hole schedules, the connector swap stated in
      words, and the union envelope, 88.00 x 57.32 mm
- [x] `tools/check_balloons.py` watches the new sheet: it takes a renderer
      rather than a board spec, so a sheet drawn by its own module is no
      longer invisible to it
- [ ] Ask whether the Pmod HAT Adapter belongs on it after all. It is left
      off because its host positions say nothing about how the models differ
      and its pin fields fall exactly where they do differ; if a plate
      designer wants the two questions answered on one page, a second view
      on the same sheet would be the way rather than an overlay

## 14. Icepi Zero  -- DONE
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

## 15. The assembled envelope leaves out the Pmod host bodies
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

## 16. An Acorn in a PoE M.2 HAT on a Pi 5  -- DONE
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
      part would settle both
- [ ] Check the derived socket footprint against a real board: it is the one
      figure here quoted at +/-1 mm rather than +/-0.2

## 17. Arty A7 Ethernet light pipe (issue #8)  -- DONE
- [x] Name the jack from Digilent's schematic: `J9`, Bel `08B0-1X1T-36-F`
- [x] Measure its LED windows, plug aperture, latch keyway and EMI springs
      off Bel's own drawing, scale recovered per axis from the figures it
      dimensions
- [x] Cross-check the two drawings against each other: Digilent's board-lock
      pads are 16.104 mm apart, Bel's are 16.13
- [x] Bore the part for a catalogue light pipe, Bivar `PLP2-4MM`, to Bivar's
      own mounting hole and panel thickness
- [x] `fpga/light_pipe/verify.py`: 37 checks over the cable, the light path
      and the fit, and one figure it reports rather than claims
- [x] `FPGA-LP-ARTY`, three views at 5:1, bound into
      `fpga-sheets.pdf`
- [x] STEP solid, `fpga/light_pipe/output/arty-ethernet-light-pipe.step`
- [x] Act on the review: the 7.75 reading, the proud LED window, the skirt
      clearance against the grip, the section's hatch angle, the tautologies
      in verify.py, `make clean`, and the file counts
- [ ] Print one and try it. Two things are calculated and neither has been
      put on a real jack: the retention, which is 0.33 mm of deflection in
      the jack's own EMI spring at minimum material and nothing else, and the
      bore, which is a printed hole holding a press fit
- [ ] Decide whether 0.33 mm of spring deflection is enough grip in practice.
      It is what the two tolerances leave after the shield is cleared by
      0.31; if it turns out not to be, the answer is a barb on the skirt or
      a screw into the roof, not a smaller clearance
- [ ] Measure a snagless patch cord's boot against the cheeks. The sheet says
      a boot standing proud of the plug's own top face within 7 mm of the
      jack will foul them; that 7 mm is the part's own geometry, and no
      published boot drawing was found to check it against
- [ ] Say which LED is link and which is speed. Bel's schematic gives LED1 as
      yellow on pins 7/8 and LED2 as a bi-colour green/orange on 9/10;
      Digilent's sheet 8 drives two of those four pins through 274 ohm
      resistors, and which is which was not read off the schematic

## 18. Raspberry Pi camera modules  -- DONE
- [x] `RPICAM-2`, Camera Module 2, from `RPI-CAM-V2_1`, a 1.5055:1 plot with
      every figure outlined; scale recovered from the 21 x 12.5 hole rectangle
- [x] `RPICAM-3`, Camera Module 3 standard and wide, from `RP-008153-DS-1` and
      `RP-008155-DS-1`, true 1:1, one sheet after the two were read separately
      and required to agree
- [x] A `lens` feature kind, drawn with a centre mark at the optical axis
- [x] `raspberry-pi-camera-sheets.pdf`, the two bound into one document
- [ ] The High Quality Camera, `RP-008200-DS-1`: needs a round feature and a
      profiled outline before `render_board` can draw its ø36 C/CS mount and
      its tripod boss honestly, and its FFC connector is in no plan view
- [ ] The Global Shutter Camera, `RP-008195-DS-1`, if anyone wants it

## 19. Where the camera goes  -- DONE
- [x] OV5647 optics from the vendors' own words: sensor, focal length, the
      65 and 120 degree lenses' declared field of view, and the focus range;
      every quote checked against the cached page by `verify.py`
- [x] The pinhole model established rather than assumed: the declared 53.50
      and 41.41 come back out of the declared 3.60 mm and 2592 x 1944 to four
      thousandths of a degree, and only against the active pixel array
- [x] Four sheets, each named for what it is over:
      `RPICAM-OVER-PLATE`, `RPICAM-OVER-ARTY`,
      `RPICAM-OVER-ETH` for the Arty with its Ethernet LEDs, and
      `RPICAM-OVER-ACORN` for an Acorn CLE-215+ in a Waveshare
      PoE M.2 HAT+ (B) on a Pi 5
- [x] Two frames per subject, whole subject and indicators, each the smallest
      4:3 rectangle holding its target plus 5.00 mm all round, with the camera
      height for both lenses and the focus verdict against the published near
      limit
- [x] `raspberry_pi_camera/verify.py`: the quotes, the model, and every frame
      against its target and its height
- [x] The Acorn taken from `accessories/parts.py` rather than restated: the
      card feature, its seated position and the HAT's standoff overhang are
      that module's, which `ACC-HAT-M2POE` is drawn from too, so the card is
      one rectangle in one place
- [ ] `RPICAM-OVER-ETH`'s frame should cover the light pipe's
      exits rather than the RJ45 jack's body. `FPGA-LP-ARTY`
      now draws the adapter, and its pipe tips are 5.01 mm in FRONT of the
      jack's face, not over the body; measured from the board edge they are
      5.11 mm past it against a frame that reaches 7.28 mm past it, so the
      frame is loose rather than wrong, and tightening it onto the exits
      would shrink it, and with it the height.
- [ ] A 120 degree OV5647 lens with a properly specified field of view. The
      figure used is Arducam's catalogue row for their B006604, a Pi Zero
      sized board with an M6 lens, and their declared 120 x 90 is not
      self-consistent on a 4:3 sensor -- 120 across implies 104.82 down. No
      vendor found publishes a measured H/V/D set for any wide OV5647.
- [ ] A near limit for the adjustable-focus and autofocus OV5647 variants.
      Arducam publish neither a lens height nor a focus distance for the
      B0176, so the sheets can only say that every height is inside the STOCK
      lens's 1 m and that a focusable module is what a rig needs.
- [ ] Lens distortion. The model is rectilinear, which the stock lens's own
      declared figures confirm to a hundredth of a degree; at 120 degrees a
      real lens is not, and the frame will be barrel distorted. Nothing here
      models it.