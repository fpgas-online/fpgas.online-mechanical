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
| `layout.py` | Where the sheets and the bound copies are, what file each sheet is written to and what each is called: one answer, so nothing can disagree about the set, a file stem or a drawing name. A name is the stem in capitals behind the family prefix, unless the family has a rule in `FAMILY_NAME_RULES` that cuts it shorter, which the demo boards and the accessories do. Not what goes *into* a bound copy: that page list is `generate_diagrams.bundles()`, one answer for the same reason |
| `kicad_pcb.py` | Minimal reader for KiCad `.kicad_pcb` s-expression files |
| `kicad_extract.py` | What every KiCad-sourced extractor does the same way: outline resolution and its checks, holes, Pmod hosts, bodies |
| `step_model.py` | Minimal STEP assembly reader on OpenCascade: the board slab, its through-holes, and each named part's placed box |
| `render_svg.py` | SVG to PDF and PNG via Inkscape, text exported as paths |
| `reproducible.py` | Pins the clocks, tool version strings and GUIDs that cairo, Inkscape, pypdf and ezdxf stamp into their output |

## Build

| | |
|---|---|
| `fetch_raspberry_pi.sh` | Downloads Raspberry Pi Ltd's mechanical drawings into `tmp/` |
| `fetch_fpga.sh` | Clones the ULX3S, ButterStick and Icepi Zero repositories and downloads the Arty A7 drawing and the PYNQ-Z2 model into `tmp/` |
| `generate_diagrams.py` | Renders every sheet as SVG, then PDF and a preview PNG, and binds the A3 sets into their bound copies -- the plate's two A3 sheets go into the Tiny Tapeout one, and the accessories and the A4 drill templates are bound into nothing. Also the data: `tt_sheets()`, the per-family sheet lists and `bundles()` say what the set is, and `update_readme.py` and `check_pdfs.py` import them rather than restating them |
| `update_readme.py` | Rewrites the preview grid in the front-page README |

The extractors are not here. Each lives with its subject:
[`tinytapeout/extract.py`](../tinytapeout/README.md),
[`raspberry_pi/extract.py`](../raspberry_pi/README.md),
[`fpga/extract.py`](../fpga/README.md), and
[`tinytapeout/mounting_plate/design.py`](../tinytapeout/mounting_plate/README.md).

## Checks

Each has caught a real defect. `make check` runs all but `crosscheck_gerber.py`,
which needs network. A check specific to one made part is not here: it lives
with the part, as the mounting plate's `verify.py` does.

GitHub Actions runs `make check` on every push to `main` and on every pull
request: [`.github/workflows/check.yml`](../.github/workflows/check.yml). The
job runs in a `debian:trixie` container with Inkscape and both DejaVu font
packages installed from Debian 13, which is what the committed PDFs were drawn
with; `check_pdfs.py` compares bytes, and only that Inkscape, cairo and font
are known to write the same ones. The workflow prints the versions it drew
with, and a run that fails uploads every `output/` directory as the run left
it.

What that run does not catch is a source changed and no sheet re-rendered.
`check_pdfs.py` holds the committed PDF against the committed SVG, and the two
still agree with each other; the other checks read the fresh render, which is
fine. Only comparing the rebuilt tree with the committed one would say so, and
the workflow has no such step yet, because a full rebuild restamps every sheet
that carries an older `VERSION` than the last source commit and so dirties
the tree with nothing wrong.

- **`check_sheets.py`** re-reads the generated SVGs, recomputes every text
  bounding box from the same font metrics the layout used, and reports text
  that collides, has a line running through it, falls outside the frame, or
  drops below the 2.5 mm ISO 3098 floor. It also derives every sheet's drawing
  name and reads the sheet back for it: the DRAWING NO cell is found by its
  own label and measured between its own rules, so a name that does not fit
  and a cell that says something else are two separate reports and neither can
  be satisfied by a note elsewhere on the sheet citing another drawing. And it
  checks that every sheet appears in the
  preview grid and that every reference in it resolves, so adding a sheet
  cannot silently leave the grid showing the wrong set. It found the notes
  block printing over the sources heading on four Raspberry Pi sheets, a datum
  leader running back through its own text, and overall dimension extension
  lines crossing the ordinate labels.

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

  It then walks the bound copies, which have no SVG and so cannot be
  checked by re-rendering anything. Each is held against the page list
  `generate_diagrams.bundles()` defines -- imported, not retyped, so the two
  cannot drift -- page by page on the content stream and on the page size,
  then on its bookmark labels, which open with the drawing names, on the page
  each bookmark opens, and on its pinned Info dictionary. A bound copy left
  in an output directory that the generator does not bind is reported as
  well. Until this nothing read a bundle at all and the only evidence one was
  what it claimed was a manual rebuild: one went out holding three pages
  re-rendered at a VERSION stamp no committed sheet carried, the set was
  green, the bundle was a PDF like any other, and only a reviewer hashing
  content streams by hand could see it. Fed such a bundle this names the
  page, the sheet it should have been, and both hashes.

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
