# Tiny Tapeout demo boards

Everything Tiny Tapeout: the mechanical data, the extractor that produces it,
the drawings, and the [generic mounting plate](mounting_plate/README.md) that
accepts any revision.

| | |
|---|---|
| `boards.py` | **Generated.** Every mechanically distinct demo board revision |
| `extract.py` | Reads the upstream KiCad board files and writes `boards.py` |
| `output/` | `TT-DB-01` to `TT-DB-06`, as SVG, PDF and PNG |
| `mounting_plate/` | The plate every revision bolts onto, and its drill templates |

```sh
uv run --no-project python tinytapeout/extract.py     # needs tmp/src, see make fetch
```

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

Shuttle-to-revision mapping comes from the upstream historic README, which
stops at TT08; later revisions are named from Tiny Tapeout's own board
revision spreadsheet, which is also where the name "ETR" for v3.2 comes from.

## One sheet per geometry, not per revision

Several revisions differ only electrically. v1.2.2 and v1.2.3 are the same
board mechanically, as are v2.0.1 and v2.1.0, so eight revisions make six
sheets, and each sheet names every revision and shuttle it covers.

`boards.py` still carries all eight: it is a database of what was built, and
the mounting plate is designed against individual revisions. Only the drawing
set is merged, and the generator compares outline, holes, Pmod hosts and every
feature before merging two revisions rather than taking a note's word for it.

Feature numbers are fixed across the family, so a number means the same part
on every sheet. That leaves gaps -- the revisions with a fourth LED have no
DIP switch and the ones with a DIP switch have no fourth LED -- so a part a
board does not carry still gets a row, marked as such.
