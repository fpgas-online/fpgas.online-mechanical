#!/bin/sh
# Fetch the upstream sources for the FPGA development boards into tmp/src.
#
# Some are git repositories and are cloned; the extractor checks each board
# file out at a pinned commit.  The rest are vendor downloads:
#
#   Digilent's file host answers a plain curl with 403, but serves the same
#   URL to anything that sends a browser User-Agent.
#   TUL's PYNQ-Z2 model is the copy Xilinx posted on the PYNQ forum, which is
#   where TUL directed people to for it.
#
# Three more come from the makers of the parts on those boards, for the
# Ethernet light pipe adapter: Digilent's Arty A7 schematic, which names the
# RJ45; Bel's drawing of that RJ45; and Bivar's drawing of the light pipe the
# adapter carries.
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/src/arty_a7 tmp/src/pynq tmp/src/bel_magjack tmp/src/bivar
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

test -d tmp/src/ulx3s || git clone --quiet https://github.com/emard/ulx3s tmp/src/ulx3s
test -d tmp/src/butterstick || git clone --quiet \
    https://github.com/butterstick-fpga/butterstick-hardware tmp/src/butterstick
test -d tmp/src/icepi-zero || git clone --quiet \
    https://github.com/cheyao/icepi-zero tmp/src/icepi-zero
test -d tmp/src/cynthion || git clone --quiet \
    https://github.com/greatscottgadgets/cynthion-hardware tmp/src/cynthion

f=tmp/src/arty_a7/arty_a7_mechanical_drawing.zip
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    https://digilent.com/reference/_media/reference/programmable-logic/arty-a7/arty_a7.zip
test -d "tmp/src/arty_a7/mechanical_drawing/Arty A7" || \
    unzip -q -o "$f" -d tmp/src/arty_a7/mechanical_drawing
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

f=tmp/src/arty_a7/arty_a7_sch.pdf
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    https://digilent.com/reference/_media/reference/programmable-logic/arty-a7/arty_a7_sch.pdf
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

# Bel's drawing of the Arty's RJ45, J9.  The part number is on the schematic
# sheet above; the drawing is what says where its LED windows are.
f=tmp/src/bel_magjack/dr-mag-08b0-1x1t-36-f.pdf
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    "https://www.belfuse.com/media/drawings/products/magjack%20ICMs/dr-mag-08b0-1x1t-36-f.pdf"
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

# Bivar's drawing of the PLP2 press-fit light pipe, which fixes the adapter's
# bore diameter, its press-fit depth and the pipe lengths on offer.
f=tmp/src/bivar/PLP2-XXX.pdf
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    https://www.bivar.com/parts_content/Datasheets/PLP2-XXX.pdf
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

f=tmp/src/pynq/PYNQ_Z2_20220218.zip
test -s "$f" || curl -sSL -o "$f" \
    https://discuss.pynq.io/uploads/short-url/qjtW7Vu29ih0nugzuDuR5k33uWQ.zip
test -s tmp/src/pynq/PYNQ_Z2_20220218/PYNQ_Z2_20220218.STEP || \
    unzip -q -o "$f" -d tmp/src/pynq
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"
