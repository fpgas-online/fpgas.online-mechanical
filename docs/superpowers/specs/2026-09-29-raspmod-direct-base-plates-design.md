# Raspmod Direct and its two base plates -- design

Date: 2026-09-29. Branches: `direct-gpio` in
`mithro/tinytapeout-demoboard-to-raspi` (the PCB) and `raspmod-direct` in
`fpgas-online/fpgas.online-mechanical` (the drawings), the latter based on
`origin/main` at 1ad4b7c with nothing borrowed from the open branches: none
of #22, #24, #25, #26, #29 touches anything the base plates use.

## What is being made

1. **The PCB.** Pat Deegan's TT Demoboard To Raspi (Raspmod), altered so that
   it sits *on* a Raspberry Pi's 40-pin header instead of hanging off a
   ribbon, and lies flat beside the FPGA board with right-angle plugs into
   its Pmod hosts. Not rerouted: every pad of every kept part stays where it
   is, with its number and its net.
2. **`BP-TT`**, a base plate carrying the TT generic mounting plate
   (`TT-MP-PLATE`, by its six M4 fixings) and a Raspberry Pi, at the heights
   that put the adapter's plugs into the demoboard's hosts.
3. **`BP-ARTY`**, a base plate carrying a Digilent Arty A7 in four corner
   cups and a Raspberry Pi, likewise, with two Pi positions: plugs into
   JA-JC or into JB-JD.
4. **`ACC-HAT-DRMOD`**, the altered board's own sheet, beside `ACC-HAT-RMOD`.

Both plates: plan plus a side elevation through the Pmod axis showing the
whole stack with every standoff and cup height dimensioned, reviewed by a
sub-agent reading the rendered PNGs, and proved by a `verify.py`.

## The numbers, and where each comes from

| Figure | Value | Source |
|---|---|---|
| Adafruit 2187 = Kaweei CS25582-40G-M36-0A, socket height | 3.8 +/-0.3 | Adafruit's spec-sheet image (Kaweei drawing CXRD110523-289) |
| its recommended layout | pads 1.02 x 2.10 on 2.54, rows 8.3 apart; holes dia 1.20 at the pins | same |
| Pi GPIO header height above the Pi's top face | 8.5 (2.54 body + pins) | Pi 4 and 3B+ mechanical drawings, `Z=8.5` |
| Pi 4 PoE header centre | (58.25, 49.86), 2x2, same height | Pi 4 mechanical drawing (25.75+32.5, 56-6.14) |
| Pi 4 Ethernet jack | x 66.65..88, y 38.0..53.5, Z 13.5 | `raspberry_pi/boards.py` |
| Pi 5 upper USB stack | x 70.92..87.24, y 40.84..53.15, Z 16 | `raspberry_pi/boards.py`, Pi 5 drawing |
| Pi PCB thickness | to be measured off the Pi 5 drawing's 1:1 side view; 1.6 assumed until then | not stated by Raspberry Pi Ltd |
| Host socket, Wurth 613012243121 | legs 3.3 +/-0.2, body 5.0 +/-0.2, 8.5 deep: rows at 4.53 and 7.07 above the host's top face | Wurth datasheet; the demoboard's KiCad file names the part |
| Right-angle male 2x6, Wurth 61301221021 | body 5.08 on the PCB, rows at 1.27 and 3.81 above the PCB; near-body leg is the lower pin; body back face 1.5 from the near leg | Wurth datasheet |
| Arty A7 PCB thickness | 1.50 | Digilent Arty rev C STEP (slab faces) |
| Arty rubber feet | 3.70 tall, dia 8.7, at the four corners | same STEP, `Ruber_Feet` |
| Arty Pmod sockets | pin field 11.75 from the top edge, faces flush with it, pitch 22.80 | `fpga/boards.py`; STEP models them as 5.08 boxes on the PCB, a placeholder |
| Arty socket standoff | ASSUMED 3.3, as Wurth's; stated on the sheet | no source settles it |
| Demoboard on the TT plate | 8.0 mm standoffs, board 1.56 thick | `tinytapeout/mounting_plate/plate.py` |

### The stack (Z up from each board's top face)

* Adapter underside = Pi top + 2.54 + 3.8 = **6.34**; adapter top = **7.94**
  (adapter 1.6 thick, from its board file).
* Adapter plug rows = adapter top + 1.27 / 3.81 = Pi top + 9.21 / 11.75.
* Host rows = host top + 4.53 / 7.07, so **host top = Pi top + 4.68**.
* `BP-TT`: host top = base + 0 (plate flat) + 3.0 + 8.0 + 1.56 = base + 12.56;
  Pi top = base + s_pi + t_pi, so s_pi = 12.56 - 4.68 - 1.6 = **6.28**: Pi on
  M2.5 x 6 F/F standoffs, residual 0.28 mm, inside the connectors' own
  +/-0.2 + 0.2.
* `BP-ARTY`: Pi on M2.5 x 4: Pi top = base + 5.6; Arty top = base + 10.28;
  Arty underside = base + 8.78; feet 3.70, so the **cup ledge is 5.08**
  above the base plate (5.1 as made, residual 0.02).

### The plan (X, Y in the host board's own frame)

Mated on the Pi (pin 1 on pin 1 is a 180 degree turn), adapter (x, y) maps
to Pi (X, Y) = (75.65 - x, 78.31 - y): pin 1 (67.28, 27.04) lands on the Pi's
(8.37, 51.27). Shortened to 62.3 wide the adapter covers Pi X 13.35..75.65,
Y 47.01..78.31, so 22.3 mm of it overhangs the Pi's GPIO edge and its plug
edge is 22.31 beyond that edge. The Pi 4's Ethernet jack starts at X 66.65:
the board is cut at x = 10 (Pi X 65.65), which loses J10 and SW1, both
optional per the maker's README, and keeps J11.

Plug pin-field centres (x = 17.79, 40.65, 63.51; y = 4.13) go over the host
pin-field centres. Male body face is 1.5 + 2.5 beyond the near leg row
(y = 2.86), so the adapter's edge sits 1.14 in front of the male body's face,
which is at the socket face when fully home: adapter edge = socket face +
1.14. The demoboard's socket face is 2.78 in front of the TT plate's front
edge; the Arty's is flush with its own edge.

Pi holes in the host frame follow from the map above; `design.py` computes
them, never types them.

## The PCB, in detail

* Files edited in place on `direct-gpio` by a Python script over the
  s-expressions (`tools/kicad_pcb.py` reads; edits are string surgery on the
  footprint blocks), checked pad-for-pad before and after, then
  `kicad-cli pcb drc` and `kicad-cli sch erc`.
* J1: `PinHeader_2x20_P2.54mm_Vertical` -> `RaspmodDirect:PinSocket_2x20_P2.54mm_SMD_CS25582_Under`:
  the 40 plated holes exactly as they are (drill as now), plus 40 SMT pads
  on B.Cu at +/-4.15 from the header centre line, 1.02 x 2.10, each joined
  to its hole by a short B.Cu stub inside the footprint. Same reference,
  same nets.
* J2, J3, J4: `PMODPeriph2B_UNDERVERT` -> `RaspmodDirect:PinHeader_2x06_P2.54mm_PMODPeriph2B_TopRA_Mirror`:
  the TT library's right-angle footprint with its pin numbers mirrored so
  that pad 1 stays at the +x end of the row further from the edge, on F.Cu,
  body toward the edge, pins past it.
* J9 removed (its socket would hit the host board). J10, SW1 removed with
  the cut end; their tracks and any stub left behind removed; no-connect
  flags on the schematic pins they leave.
* Edge.Cuts: the left edge moves from x = 0 to x = 10, corners re-rounded at
  R2. Silkscreen in the cut region removed; the "Raspberry Pi Ribbon"
  legend reworded; title block "TT Demoboard To Raspi, direct" rev 2.0 with
  a README section saying what changed and why, and the compatibility
  statement: Pi 5 and 3B; not 3B+ or 4B (PoE header under J1).
* Review material: `kicad-cli pcb render` top and bottom, and an SVG plot of
  the copper, committed under `images/`.

## The drawings, in detail

* `accessories/extract.py` gains a second target: the fork at a pinned
  commit, written to `accessories/raspmod_direct.py`; `ACC_STEMS` and
  `ACC_NAMES` gain `raspmod-direct` -> `hat-drmod`. Drawn by `render_board`
  like the Raspmod.
* New family `base_plates/` (`FAMILY_DIRS["base-plates"]`, prefix `BP`, no
  lead), `design.py` -> generated `plates.py` holding two `BoardSpec`s with
  the holes tabulated, plus the placements of every phantom part in the
  plate's frame; `verify.py`; `README.md`; `tools/drafting/baseplate_sheet.py`
  after `holder_sheet.py`: front elevation looking along +Y through the
  Pmod axis, plan under it, hole table, standoff table, legend, notes.
* `BP_NAMES = {"tt-pi": "tt", "arty-pi": "arty"}` so the names are `BP-TT`
  and `BP-ARTY`; neither is a prefix of the other.
* `verify.py` proves: plug rows meet host rows within 0.4; nothing the Pi
  drawings give a Z for under the adapter's strip reaches 6.34; no two
  outlines overlap on the plate; the cups clear the Arty's parts; the two
  Pi hole sets do not coincide with anything else.
* Sheet notes state the Pi thickness measurement, the Arty socket
  assumption, and the model exclusion.
* Registered in `generate_diagrams.py` (`baseplate_sheets()`, bound into no
  bundle), `update_readme.py` (`groups()`, `FAMILY_READMES`), the Makefile
  (`clean`, `check` runs `base_plates/verify.py`), and the root README's
  family table.

## Order of work

1. PCB: clone, script, footprints, cut, DRC/ERC, renders, README, commit,
   push `direct-gpio`, PR on the fork with the renders inline.
2. Drawings: extractor + `ACC-HAT-DRMOD`; then `base_plates/` data, sheet,
   verify; render; sub-agent review loop; `make check` under the lock;
   source commits, then output commits; README/TODO/SCRATCH; PR with the
   previews inline.
