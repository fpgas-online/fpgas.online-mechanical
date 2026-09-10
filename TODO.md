# TODO

Status key: `[ ]` not started, `[~]` in progress, `[x]` done.

## 1. Data collection
- [~] Tiny Tapeout: identify every mechanically distinct demo board revision
- [ ] Tiny Tapeout: extract outline / holes / Pmods / USB-C / 7-seg / LEDs from KiCad
- [~] Raspberry Pi: download official mechanical drawings (3B, 3B+, 3A+, 4B, 5)
- [ ] Raspberry Pi: extract outline / holes / USB / Ethernet from DXF
- [ ] Raspberry Pi: extract Pi 5 and Pi 3A+ geometry from 1:1 vector PDF
- [ ] Digilent Pmod interface specification header geometry
- [ ] Digilent Pmod HAT Adapter geometry
- [ ] Waveshare 25 W PoE -> USB-C splitter dimensions
- [ ] Generic AliExpress PoE -> micro-USB splitter dimensions
- [ ] Consolidate everything into `data/*.py` with per-value source attribution

## 2. Drawing engine
- [ ] Minimal 2D drafting library: sheet, border, title block, views
- [ ] Dimension primitives: linear, ordinate, diameter, leader/balloon
- [ ] Hole tables
- [ ] SVG output plus PDF/PNG conversion

## 3. Diagrams
- [ ] Tiny Tapeout demo boards, one sheet per mechanically distinct revision
- [ ] Raspberry Pi 3B / 3B+ / 3A+ / 4B / 5
- [ ] Raspberry Pi + Digilent Pmod HAT Adapter overlay
- [ ] Generic PoE -> micro-USB splitter
- [ ] Waveshare 25 W PoE -> USB-C splitter

## 4. Tiny Tapeout generic mounting plate
- [ ] Overlay every TT board revision in a common Pmod-referenced frame
- [ ] Choose plate outline and hole pattern
- [ ] Mounting plate drawing plus a cut file

## 5. Review
- [ ] Sub-agent code review
- [ ] Sub-agent mechanical drawing review
