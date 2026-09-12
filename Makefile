# Regenerate everything from the sources.
#
# The upstream inputs live under tmp/ and are not committed: run `make fetch`
# once to get them, then `make` to rebuild the data and every drawing.

UV := uv run --no-project
DRAW := $(UV) --with pillow
EXTRACT := $(UV) --with ezdxf --with pdfplumber

.PHONY: all data diagrams check fetch clean

all: check

## fetch: download the upstream sources into tmp/ (needs network)
fetch:
	scripts/fetch_raspberry_pi.sh
	@test -d tmp/src/tt-demo-pcb || git clone --quiet \
		https://github.com/TinyTapeout/tt-demo-pcb tmp/src/tt-demo-pcb
	@test -d tmp/src/tt123-demo-pcb || git clone --quiet \
		https://github.com/TinyTapeout/tt123-demo-pcb tmp/src/tt123-demo-pcb

## data: re-extract the mechanical database from those sources
data:
	$(UV) python scripts/extract_tinytapeout.py
	$(EXTRACT) python scripts/extract_raspberry_pi.py
	$(UV) python scripts/design_mounting_plate.py

## diagrams: render every sheet as SVG, PDF and PNG, plus the plate cut file
diagrams:
	$(DRAW) python scripts/generate_diagrams.py
	$(UV) --with ezdxf python scripts/export_plate_dxf.py
	$(DRAW) python scripts/update_readme.py

## check: the three things that have caught real defects
check: diagrams
	$(DRAW) python scripts/check_sheets.py
	$(UV) python scripts/verify_mounting_plate.py
	$(DRAW) python scripts/check_balloons.py
	$(UV) --with pdfplumber --with pillow python scripts/check_drill_template.py
	$(UV) --with pypdf --with pillow python scripts/check_pdfs.py

clean:
	rm -f diagrams/*/*.svg diagrams/*/*.pdf diagrams/*/*.png diagrams/*/*.dxf
