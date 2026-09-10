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

Phase: **data collection**.

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
- Pi 3A+, Pi 5: PDF only. The Pi 5 drawing is 1:1 vector on A4, so the geometry
  can be lifted out of the PDF content stream.

### Still to find

- Digilent Pmod interface specification (header geometry, keep-outs).
- Digilent Pmod HAT Adapter (410-366) board geometry -- where its three Pmod
  headers sit relative to the Pi's 40-pin GPIO header.
- Waveshare 25 W PoE -> USB-C splitter dimensions.
- Generic AliExpress PoE -> micro-USB splitter dimensions.

## Decisions

- Extract geometry from machine-readable sources (KiCad `.kicad_pcb` s-expr,
  DXF, 1:1 vector PDF) rather than transcribing dimension text by eye.
- Hand-curated numbers are always tagged with their source in the data file.

## Things that did not work

- `curl` without `-L` against `datasheets.raspberrypi.com` returns a 301 with a
  zero-length body. Always follow redirects.
- Cloning `tt-demo-pcb` with `--filter=blob:none` makes walking history
  painfully slow (each `git show` is a network round trip). Re-fetched all
  blobs with `git fetch --refetch`.
