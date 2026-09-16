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
| `layout.py` | Where the sheets and the bound copies are, what file each sheet is written to and what each is called: one answer, so nothing can disagree about the set, a file stem or a drawing name. A name is the stem in capitals behind the family prefix, unless the family has a rule in `FAMILY_NAME_RULES` that cuts it shorter. Not what goes *into* a bound copy: that page list is `generate_diagrams.bundles()`, one answer for the same reason |
| `kicad_pcb.py` | Minimal reader for KiCad `.kicad_pcb` s-expression files |
| `kicad_extract.py` | What every KiCad-sourced extractor does the same way: outline resolution and its checks, holes, Pmod hosts, bodies |
| `step_model.py` | Minimal STEP assembly reader on OpenCascade: the board slab, its through-holes, and each named part's placed box |
| `photo_frame.py` | Measuring a board off a square-on photograph: its edges, a homography onto its known size, and circles, blobs and ruled grids in that frame |
| `render_svg.py` | SVG to PDF and PNG via Inkscape, text exported as paths |
| `reproducible.py` | Pins the clocks, tool version strings and GUIDs that cairo, Inkscape, pypdf and ezdxf stamp into their output, and the export clock, the absolute path and the per-process product counter OpenCascade stamps into a STEP |

## Build

| | |
|---|---|
| `fetch_raspberry_pi.sh` | Downloads Raspberry Pi Ltd's board mechanical drawings into `tmp/` |
| `fetch_raspberry_pi_camera.sh` | Downloads Raspberry Pi Ltd's camera mechanical drawings into `tmp/`, what stands in for a drawing of the Camera Module 1, and every vendor page and datasheet the lens and camera position sheets quote their optics from, pinned Internet Archive captures where there are any |
| `fetch_fpga.sh` | Clones the repositories and downloads the drawings and models the FPGA boards are read from into `tmp/`; [`fpga/README.md`](../fpga/README.md) says which board is read from what |
| `fetch_orangepi_pc.sh` | Downloads the photographs the Orange Pi PC is measured from, and the models it is checked against, into `tmp/` |
| `generate_diagrams.py` | Renders every sheet as SVG, then PDF and a preview PNG, and binds the A3 sets into their bound copies -- the plate's two A3 sheets go into the Tiny Tapeout one, and the accessories and the A4 drill templates are bound into nothing. Also the data: `tt_sheets()`, the per-family sheet lists and `bundles()` say what the set is, and `update_readme.py` and `check_pdfs.py` import them rather than restating them |
| `update_readme.py` | Rewrites the preview grid in the front-page README |

The extractors are not here. Each lives with its subject:

- [`accessories/extract.py`](../accessories/README.md)
- [`fpga/extract.py`](../fpga/README.md)
- [`raspberry_pi/extract.py`](../raspberry_pi/README.md)
- [`raspberry_pi_camera/extract.py`](../raspberry_pi_camera/README.md)
- [`tinytapeout/extract.py`](../tinytapeout/README.md)
- [`tinytapeout/mounting_plate/design.py`](../tinytapeout/mounting_plate/README.md)

The camera holder has no extractor:
[`tinytapeout/camera_holder/holder.py`](../tinytapeout/camera_holder/README.md)
is derived at import from the modules it is built on.

## Checks

`make check` runs all but `crosscheck_gerber.py`, which needs network. Each
of the checks listed at the end of this section has caught a real defect. A
check specific to one family or one made part is not among them: it lives
with its family, and not every one of those has caught something yet.

- [`tinytapeout/mounting_plate/verify.py`](../tinytapeout/mounting_plate/README.md)
  proves the finished plate accepts every demo board revision, with a real M3
  fastener clearance check. It has caught a real defect: a merge rule that
  produced a plate whose holes the fasteners did not fit.
- [`tinytapeout/camera_holder/verify.py`](../tinytapeout/camera_holder/README.md)
  proves, for the holder built for each lens, that it puts the lens where
  the camera position sheet says it has to be, that every revision's whole
  board is then in the picture with none of it hidden, that the holder
  touches no board, standoff or cable, and that every fastener fits; and
  that the holders share their beam and carrier.  Newer than anything it
  could have caught.
- [`raspberry_pi/verify_orangepi_pc.py`](../raspberry_pi/README.md)
  holds the Orange Pi PC's figures, measured off photographs, to checks the
  measurement was not fitted to: the sizes of standard parts on other
  vendors' drawings, and Xunlong's drawing and other people's models and
  cases of the board.
- [`raspberry_pi_camera/verify_optics.py`](../raspberry_pi_camera/README.md)
  has not caught one yet -- it is newer than the sheets it checks. It proves
  that every figure quoted in `raspberry_pi_camera/optics.py` is in the
  vendor page it is credited to; that the pinhole model reproduces Raspberry
  Pi's own declared field of view from their own focal length and pixel
  count, and does *not* reproduce it from the sensor image area printed
  beside it; that each lens's figures agree or disagree with the sensor's 4:3
  under its projection as the sheets say they do, and that the 120 degree
  lens's pair is the split of its declared diagonal between the rectilinear
  and equisolid bounds; that the frame margin absorbs every other pair the
  evidence allows, and the wide lens's barrel distortion puts the frame's
  corners inside the picture; that every frame is the smallest 4:3 rectangle
  holding its target plus the stated margin, and that both angles reach it
  at the height printed; that a target whose plane is not the subject's own
  top face says so; that every hyperfocal distance, depth of field and focus
  verdict is the one the arithmetic gives; and that what the elevations draw
  is right -- the angle each labels lies along its axis, the camera is turned
  the way that needs it lower, and the figures the notes derive come out the
  same by another route.

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
  that collides, has a line running through it, is covered by a balloon,
  falls outside the frame, or drops below the 2.5 mm ISO 3098 floor. It also
  derives every sheet's drawing name and reads the sheet back for it: the
  DRAWING NO cell is found by its own label and measured between its own
  rules, so a name that does not fit and a cell that says something else are
  two separate reports and neither can be satisfied by a note elsewhere on the
  sheet citing another drawing. And it checks that every sheet appears in the
  preview grid and that every reference in it resolves, so adding a sheet
  cannot silently leave the grid showing the wrong set. It found the notes
  block printing over the sources heading on four Raspberry Pi sheets, a datum
  leader running back through its own text, and overall dimension extension
  lines crossing the ordinate labels. The balloon test came last and found the
  defect it was written for: a balloon on the Cynthion sheet whose rim came
  0.81 mm down into the 3.23 that dimensions the Pmod pin rows. A balloon is a
  white disc, so it takes a bite out of whatever it lands on, and neither the
  text-to-text test nor the line test could see it.

- **`check_balloons.py`** walks every sheet the generator writes, drawn by
  the generator's own `draw_sheets()` so that it judges the leaders on the
  page, and holds every leader -- a balloon's or a callout's -- against four
  things: another leader or another balloon's ring, a hard obstacle in the
  placer's model (a phantom Pmod host, an ordinate witness line), the body of
  a feature it does not point at, and a dimension or extension line. It also
  reports a balloon sitting on a feature outline. Leader against leader is an
  exact segment intersection, because two leaders meeting at a steep angle
  share less than a millimetre of paper and a sampled test steps over them.
  Anything not listed in its `ACCEPTED`, per sheet and per leader, fails. It
  found that a Pmod host's two-letter label was reserving the whole height of
  its pin field, which walled off the diagonal every leader from the
  lower-left corner of a Raspberry Pi wanted to take; and, once it looked at
  feature bodies and dimensions, that on `RPI-ALL` three leaders were ruled
  across the overall height and one across two connectors it did not point
  at.

- **`check_leader_arrows.py`** reads the finished SVGs back and reports every
  balloon leader ruled through a dimension arrowhead, testing segment against
  triangle rather than sampling. A leader across a dimension *line* is
  ordinary and the placer allows it; a leader through the solid triangle at
  its end is not. It found one, on the sheet being added at the time, which
  reserving the overall dimensions' arrowheads fixed. What a leader is comes
  off the sheet -- a line in a balloon ring's colour with an end on that ring
  -- because colour alone sees the Pmod pin-row centre line, which wears the
  balloon colour and lies along the dimension that measures to it, as a
  leader through that dimension's arrowhead on three sheets, and position
  alone sees the dashed phantom circle seven sheets draw at exactly the
  balloon radius as a balloon. It says how many leaders it
  examined as well as how many were through an arrowhead, because a rule that
  finds no leaders on a sheet otherwise reports it clean.

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
