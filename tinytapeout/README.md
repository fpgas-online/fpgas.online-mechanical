# Tiny Tapeout demo boards

Everything Tiny Tapeout: the mechanical data, the extractor that produces it,
the drawings, and the [generic mounting plate](mounting_plate/README.md) that
accepts any revision.

| | |
|---|---|
| `boards.py` | **Generated.** Every mechanically distinct demo board revision |
| `extract.py` | Reads the upstream KiCad board files and writes `boards.py` |
| `output/` | One `TT-DB-…` sheet per geometry, as SVG and PDF, and `tinytapeout-sheets.pdf`, the plate sheets and demo boards bound into one document |
| `mounting_plate/` | The plate every revision bolts onto, and its drill templates |

```sh
uv run --no-project python tinytapeout/extract.py     # needs tmp/src, see make fetch
```

## The sheets

<!-- sheets:begin -->

Each thumbnail links to the PDF. The same sheet is also there as SVG.

<table>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-tt123-v2p2p5-tt123-v2p2p6.pdf"><img src="output/previews/tt-demo-board-tt123-v2p2p5-tt123-v2p2p6.png" width="270" alt="TT-DB-TT123-V2P2P5-TT123-V2P2P6 DB mpw v2.2.5 / DB mpw v2.2.6"></a><br>
<b>TT-DB-TT123-V2P2P5-TT123-V2P2P6</b> DB mpw v2.2.5 / DB mpw v2.2.6<br>mpw-mb1 rev 2.2.5 and 2.2.6
</td>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-v1p2p1-v1p2p2-v1p2p3.pdf"><img src="output/previews/tt-demo-board-v1p2p1-v1p2p2-v1p2p3.png" width="270" alt="TT-DB-V1P2P1-V1P2P2-V1P2P3 DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c"></a><br>
<b>TT-DB-V1P2P1-V1P2P2-V1P2P3</b> DB 4+ v1.2.1 / DB 4+ v1.2.2 / DB 4+ v1.2.2c<br>tinytapeout-demo rev 1.2.1, 1.2.2 and 1.2.3
</td>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-v2p0p1-v2p1p0.pdf"><img src="output/previews/tt-demo-board-v2p0p1-v2p1p0.png" width="270" alt="TT-DB-V2P0P1-V2P1P0 DB 06+ v2.0.1 / DB 06+ v2.1.0"></a><br>
<b>TT-DB-V2P0P1-V2P1P0</b> DB 06+ v2.0.1 / DB 06+ v2.1.0<br>tinytapeout-demo rev 2.0.1 and 2.1.0
</td>
</tr>
<tr>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-v2p1p2.pdf"><img src="output/previews/tt-demo-board-v2p1p2.png" width="270" alt="TT-DB-V2P1P2 DB 06+ v2.1.2"></a><br>
<b>TT-DB-V2P1P2</b> DB 06+ v2.1.2<br>tinytapeout-demo rev 2.1.2
</td>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-v3p2.pdf"><img src="output/previews/tt-demo-board-v3p2.png" width="270" alt="TT-DB-V3P2 DB ETR v3.2"></a><br>
<b>TT-DB-V3P2</b> DB ETR v3.2<br>tinytapeout-demo rev 3.2
</td>
<td width="33%" valign="top" align="center">
<a href="output/tt-demo-board-v3p3.pdf"><img src="output/previews/tt-demo-board-v3p3.png" width="270" alt="TT-DB-V3P3 DB ETR v3.3"></a><br>
<b>TT-DB-V3P3</b> DB ETR v3.3<br>tinytapeout-demo rev 3.3
</td>
</tr>
</table>

<!-- sheets:end -->

## Where the numbers come from

Read straight out of the upstream KiCad board files, at the commit each
shuttle was produced from: board outline, mounting holes, Pmod host pin
fields, USB connector, seven-segment display and LEDs.

The rule is **machine-read the numbers, hand-curate the identification**.
`extract.py` carries a table saying which reference designator corresponds to
which mechanical role. If a board file changes, the selector stops matching
and the script fails, rather than quietly emitting a wrong dimension.

Two things are checked rather than trusted:

- a resolved arc must pass through the point KiCad puts on it;
- `tools/crosscheck_gerber.py` compares an extracted outline against the
  upstream Edge_Cuts gerber, which KiCad's own plotter produced from the same
  board file. Both give 104.500 x 81.000 mm for the DB mpw board, so the
  parsing is confirmed against something that did not come from here.

Which shuttles used a board comes from the "Used by" column of Tiny Tapeout's
own board revision spreadsheet, which is authoritative for it and the only
source covering every revision. Board names are that spreadsheet's ID column,
which is where `DB mpw`, `DB 4+`, `DB 06+` and `DB ETR` come from. The upstream
historic README is still cited for the revision-to-commit mapping it gives,
but it stops at v2.1.2 and is not a shuttle record.

## One sheet per geometry, not per revision

Several revisions differ only electrically. v2.2.5 and v2.2.6 are the same
board mechanically, as are v1.2.2 and v1.2.3, and v2.0.1 and v2.1.0, so nine
revisions make six sheets, and each sheet names every revision and shuttle it
covers.

`boards.py` still carries all nine: it is a database of what was built, and
the mounting plate is designed against individual revisions. Only the drawing
set is merged, and the generator compares outline, holes, Pmod hosts and every
feature before merging two revisions rather than taking a note's word for it.

Feature numbers are fixed across the family, so a number means the same part
on every sheet. That leaves gaps -- only the earliest boards carry a fourth
LED, and only they carry a second DIP switch -- so a part a board does not
carry still gets a row, marked as such.

Every revision carries an 8-way input DIP switch. The two `DB mpw` boards
carry a second, 9-way one beside it; the way count on each sheet is halved out
of the footprint's pad count rather than written into a label.
