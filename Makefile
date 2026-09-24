# Regenerate everything from the sources.
#
# The repository groups by subject: each family's directory owns its data,
# its extractor and its sheets, the mounting plate sits under tinytapeout/,
# and tools/ holds the machinery that belongs to no subject.  README.md says
# which families there are.
#
# The upstream inputs live under tmp/ and are not committed: run `make fetch`
# once to get them, then `make` to rebuild the data and every drawing.

UV := uv run --no-project
# Writing a PDF now normalises it, which needs pypdf.
DRAW := $(UV) --with pillow --with pypdf
EXTRACT := $(UV) --with ezdxf --with pdfplumber

.PHONY: all data diagrams check fetch clean

all: check

## fetch: download the upstream sources into tmp/ (needs network)
fetch:
	tools/fetch_raspberry_pi.sh
	@test -d tmp/src/tt-demo-pcb || git clone --quiet \
		https://github.com/TinyTapeout/tt-demo-pcb tmp/src/tt-demo-pcb
	@test -d tmp/src/tt123-demo-pcb || git clone --quiet \
		https://github.com/TinyTapeout/tt123-demo-pcb tmp/src/tt123-demo-pcb
	tools/fetch_fpga.sh
	tools/fetch_orangepi_pc.sh
	@test -d tmp/src/tinytapeout-demoboard-to-raspi || git clone --quiet \
		https://github.com/psychogenic/tinytapeout-demoboard-to-raspi \
		tmp/src/tinytapeout-demoboard-to-raspi

## data: re-extract the mechanical database from those sources
data:
	$(UV) python tinytapeout/extract.py
	$(EXTRACT) python raspberry_pi/extract.py
	$(EXTRACT) --with cadquery python fpga/extract.py
	$(UV) python accessories/extract.py
	$(UV) python tinytapeout/mounting_plate/design.py

## diagrams: render every sheet as SVG, PDF and PNG, plus the plate cut file
diagrams:
	$(DRAW) python tools/generate_diagrams.py
	$(UV) --with ezdxf python tinytapeout/mounting_plate/export_dxf.py
	$(DRAW) python tools/update_readme.py
	$(UV) python accessories/compare.py

## check: the things that have caught real defects
check: diagrams
	$(DRAW) python tools/check_sheets.py
	$(UV) python tinytapeout/mounting_plate/verify.py
	$(DRAW) python tools/check_balloons.py
	$(UV) --with pdfplumber --with pillow python tools/check_drill_template.py
	$(UV) --with pypdf --with pillow python tools/check_pdfs.py

# Every output/ directory is build product: `make clean && make diagrams`
# restores every file in them byte for byte, since
# tools/reproducible.py pins the clocks and tool version strings the formats
# would otherwise stamp in.  So remove them outright rather than picking off
# extensions one at a time.
clean:
	rm -rf accessories/output raspberry_pi/output fpga/output \
	       tinytapeout/output tinytapeout/mounting_plate/output
