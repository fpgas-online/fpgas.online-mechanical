# Tools

The machinery that belongs to no subject. Everything here works on *all*
families, or on none in particular; anything that belongs to one board family
lives with that family instead.

Everything runs under `uv run --no-project` with its dependencies named on the
command line. There is no `pyproject.toml` and nothing to install first.
`make` runs the ones that matter, in order.

## Libraries

Imported, not run.

| | |
|---|---|
| [`drafting/`](drafting/README.md) | The 2D drawing library: turns a `BoardSpec` into an ISO-style sheet |
| `schema.py` | `BoardSpec`, `Outline`, `Hole`, `Slot`, `Pmod`, `Feature`, `Source` |
| `layout.py` | Where the sheets are. One answer, so the generator and the checks cannot disagree about the set |
| `kicad_pcb.py` | Minimal reader for KiCad `.kicad_pcb` s-expression files |
| `kicad_extract.py` | What every KiCad-sourced extractor does the same way: outline resolution and its checks, holes, Pmod hosts, bodies |
| `step_model.py` | Minimal STEP assembly reader on OpenCascade: the board slab, its through-holes, and each named part's placed box |
| `render_svg.py` | SVG to PDF and PNG via Inkscape, text exported as paths |
| `reproducible.py` | Pins the clocks, tool version strings and GUIDs that cairo, Inkscape, pypdf and ezdxf stamp into their output |

## Build

| | |
|---|---|
| `fetch_raspberry_pi.sh` | Downloads Raspberry Pi Ltd's mechanical drawings into `tmp/` |
| `fetch_fpga.sh` | Clones the ULX3S and ButterStick repositories and downloads the Arty A7 drawing and the PYNQ-Z2 model into `tmp/` |
| `generate_diagrams.py` | Renders every sheet as SVG, then PDF, PNG and preview |
| `update_readme.py` | Rewrites the preview grid in the front-page README |

The extractors are not here. Each lives with its subject:
[`tinytapeout/extract.py`](../tinytapeout/README.md),
[`raspberry_pi/extract.py`](../raspberry_pi/README.md),
[`fpga/extract.py`](../fpga/README.md), and
[`tinytapeout/mounting_plate/design.py`](../tinytapeout/mounting_plate/README.md).

## Checks

Each has caught a real defect. `make check` runs all but `crosscheck_gerber.py`,
which needs network. A sixth, `verify.py`, is specific to the mounting plate
and lives with it.

- **`check_sheets.py`** re-reads the generated SVGs, recomputes every text
  bounding box from the same font metrics the layout used, and reports text
  that collides, has a line running through it, falls outside the frame, or
  drops below the 2.5 mm ISO 3098 floor. It also checks that every sheet
  appears in the preview grid and that every reference in it resolves, so
  adding a sheet cannot silently leave the grid showing the wrong set. It
  found the notes block printing over the sources heading on four Raspberry Pi
  sheets, a datum leader running back through its own text, and overall
  dimension extension lines crossing the ordinate labels.

- **`check_balloons.py`** looks one level below the finished SVG, at the
  obstacle model the balloon placer works from, and reports every leader whose
  final route crosses something a reader cannot afford to have a line ruled
  over: a phantom Pmod host, another balloon, another leader, an ordinate
  witness line. It found that a Pmod host's two-letter label was reserving the
  whole height of its pin field, which walled off the diagonal every leader
  from the lower-left corner of a Raspberry Pi wanted to take.

- **`check_drill_template.py`** measures the drill template PDFs instead of
  trusting them. It reads each page back, finds every hole as a circle, and
  compares where it landed against the plate data that drew it; it also checks
  both scale bars really are 100 mm and that nothing strays into the border
  the printer cannot reach. Rendering an SVG guarantees none of this: a
  different exporter or a page sized in points would pass every other check
  here and put the holes 4 % out. Fed a page scaled by a print queue's own
  auto-fit factor it reports five problems and finds no holes at all.

- **`check_pdfs.py`** checks what is about to go into the repository, because
  the PDFs are the artefact: someone who clones this gets them without
  installing Inkscape, a font or `uv`. For every sheet it confirms a PDF is
  staged beside it, that the PDF is a render of the staged SVG rather than of
  some earlier one, that the page is the size the drawing claims so it prints
  1:1, and that no font is embedded. It reads the git *index*: the working
  tree is whatever `make diagrams` wrote moments ago and agrees with itself
  regardless, and HEAD would mean a rename could not go green until after it
  had been committed. The comparison is byte for byte, which it can be because
  `reproducible.py` makes rendering reproducible; it used to compare only page
  content streams, because cairo stamped a clock into every file it wrote.

- **`crosscheck_gerber.py`** compares an extracted board outline against the
  upstream Edge_Cuts gerber, which KiCad's own plotter produced from the same
  board file. Both give 104.500 x 81.000 mm for the DB mpw board, so the
  parsing and coordinate path is confirmed against something that did not come
  from this repository. Needs network, so it is not part of `make`.

## Probes

One-off investigation tools, kept because they are how some of the numbers
were arrived at and how a disputed one would be checked again. Not run by
`make`.

| | |
|---|---|
| `dump_rpi_dxf.py` | Dumps the mechanical features of a Raspberry Pi DXF, layer by layer |
| `dump_rpi_pdf.py` | Dumps features from the Pi 5's vector PDF, recovering the plot scale; its rectangle recovery also serves the Arty A7 plot |
| `plot_pcb_check.py` | Sanity plot of an extracted `.kicad_pcb` |
