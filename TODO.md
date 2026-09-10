# TODO

Status key: `[ ]` not started, `[~]` in progress, `[x]` done.

## 1. Data collection  -- DONE
- [x] Tiny Tapeout: identify every mechanically distinct demo board revision
- [x] Tiny Tapeout: extract outline / holes / Pmods / USB-C / 7-seg / LEDs from KiCad
- [x] Raspberry Pi: download official mechanical drawings (3B, 3B+, 3A+, 4B, 5)
- [x] Raspberry Pi: extract outline / holes / USB / Ethernet from DXF
- [x] Raspberry Pi: extract Pi 5 and Pi 3A+ geometry from vector PDF
- [x] Digilent Pmod interface specification header geometry
- [x] Digilent Pmod HAT Adapter geometry (photogrammetry, +/-0.75 mm)
- [x] Waveshare 25 W PoE -> USB-C splitter dimensions
- [x] Generic AliExpress PoE -> micro-USB splitter dimensions
- [x] Consolidate everything into `data/*.py` with per-value source attribution

## 2. Drawing engine  -- DONE
- [x] Minimal 2D drafting library: sheet, border, title block, views
- [x] Dimension primitives: linear, ordinate, leader, balloon, datum
- [x] Hole tables, feature schedules, notes and source blocks
- [x] SVG output plus PDF/PNG conversion

## 3. Diagrams  -- DONE
- [x] Tiny Tapeout demo boards, 8 sheets, one per production revision
- [x] Raspberry Pi 3A+ / 3B / 3B+ / 4B / 5
- [x] Raspberry Pi + Digilent Pmod HAT Adapter overlay, on every Pi sheet
- [x] Digilent Pmod HAT Adapter on its own
- [x] Generic PoE -> micro-USB splitter
- [x] Waveshare 25 W PoE -> USB-C splitter

## 4. Tiny Tapeout generic mounting plate  -- DONE
- [x] Overlay every TT board revision in a common Pmod-referenced frame
- [x] Choose plate outline and hole pattern
- [x] Mounting plate fabrication drawing
- [x] Board fitting guide, one view per revision
- [x] Cut file: `diagrams/mounting-plate/tt-generic-mounting-plate.dxf`

## 5. Review
- [x] Sub-agent code review, round 1 -- acted on
- [x] Sub-agent mechanical drawing review, round 1 -- acted on
- [x] Sub-agent code review, round 2 -- acted on
- [~] Sub-agent mechanical drawing review, round 2
- [x] Automated sheet checker (`scripts/check_sheets.py`): text collisions,
      out-of-frame content, text under the 2.5 mm ISO 3098 floor
- [x] Automated arc check in the extractor: a resolved arc must pass through
      the point KiCad puts on it
- [x] `scripts/verify_mounting_plate.py`: proves the finished plate accepts
      every revision, with a real M3 fastener clearance check

## 6. Repository
- [x] README explaining what is here and how the numbers were obtained
- [x] Apache 2.0 licence
