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

## FPGA development boards  -- sheets done, three items open
- [x] Arty A7 from Digilent's DXF and PDF plot; no mounting holes, rubber feet
- [x] ULX3S from KiCad at the four tags sold, required to agree
- [x] PYNQ-Z2 from TUL's STEP assembly; LEDs not in the model, said in words
- [x] ButterStick from KiCad r1.0a, SYZYGY standoff holes in the schedule
- [x] Cynthion from KiCad at r1.4.0, the initial production release; four USB
      ports took two new numbers at the end of the family schedule and the
      status LED row a third, and its mezzanine receptacle J5 took the
      family's first expansion slot
- [x] `fpga-sheets.pdf`, every FPGA sheet bound into one document
- [ ] PYNQ-Z2 LED positions, by photogrammetry from TUL's product photo if
      no vector source turns up
- [ ] Check the Pmod HAT Adapter's pin 1 corner against the adapter's
      silkscreen; `accessories/parts.py` has it opposite the Pmod convention
- [ ] Cynthion's three side buttons and its two SWD connectors are not drawn.
      The buttons reach 2.50 mm past the left and right edges and a case
      needs holes for them, which is in the notes and the envelope figure but
      is not a feature with a balloon

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
