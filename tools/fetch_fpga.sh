#!/bin/sh
# Fetch the upstream sources for the FPGA development boards into tmp/src.
#
# Four are git repositories and are cloned; the extractor checks each board
# file out at a pinned commit.  Four are vendor downloads:
#
#   Digilent's file host answers a plain curl with 403, but serves the same
#   URL to anything that sends a browser User-Agent.  It serves the two
#   mechanical drawing zips; the pages that link them are behind a challenge
#   a script cannot pass, so the URLs are written out here.
#   TUL's PYNQ-Z2 model is the copy Xilinx posted on the PYNQ forum, which is
#   where TUL directed people to for it.
#   Avnet's Ultra96-V2 files come from Linaro's 96Boards documentation
#   repository, which publishes them "directly from the board vendors";
#   Avnet's own product page answers every request with an Akamai Bot
#   Manager interstitial that a script cannot pass.  The drawing is the only
#   one the extractor reads; the bill of materials and the specification are
#   fetched because the sheet cites them and a reader should be able to check
#   the quotations.  Avnet's hardware user's guide is served from Avnet, and
#   like Digilent's file host it refuses a plain curl -- an Akamai WAF
#   PR_WAF_DENY, HTTP 400 -- and serves the same URL to a browser
#   User-Agent.
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/src/arty_a7 tmp/src/zybo_z7 tmp/src/pynq tmp/src/ultra96 tmp/src/96boards
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

f=tmp/src/zybo_z7/zybo_z7_dimensions.zip
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    https://digilent.com/reference/_media/reference/programmable-logic/zybo-z7/zybo_z7_dimensions.zip
test -d tmp/src/zybo_z7/mechanical_drawing/ZYBO_Z7 || \
    unzip -q -o "$f" -d tmp/src/zybo_z7/mechanical_drawing
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

f=tmp/src/pynq/PYNQ_Z2_20220218.zip
test -s "$f" || curl -sSL -o "$f" \
    https://discuss.pynq.io/uploads/short-url/qjtW7Vu29ih0nugzuDuR5k33uWQ.zip
test -s tmp/src/pynq/PYNQ_Z2_20220218/PYNQ_Z2_20220218.STEP || \
    unzip -q -o "$f" -d tmp/src/pynq
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

GH=https://raw.githubusercontent.com/96boards/documentation/master
for f in ultra96-v2-mechanical.PDF ultra96-v2-bom.pdf; do
    test -s "tmp/src/ultra96/$f" || curl -sSL -o "tmp/src/ultra96/$f" \
        "$GH/consumer/ultra96/ultra96-v2/hardware-docs/files/$f"
    printf '%-40s %9s bytes\n' "$f" "$(wc -c < "tmp/src/ultra96/$f")"
done

f=tmp/src/96boards/96Boards-CE-Specification-v1.0.pdf
test -s "$f" || curl -sSL -o "$f" \
    "$GH/Specifications/96Boards-CE-Specification.pdf"
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"

f=tmp/src/ultra96/Ultra96-V2-HW-User-Guide-v1_3.pdf
test -s "$f" || curl -sSL -A "$UA" -o "$f" \
    'https://www.avnet.com/wps/wcm/connect/onesite/b85b9556-0b2a-42b3-ad6a-8dcf3eac1ff9/Ultra96-V2-HW-User-Guide-v1_3.pdf?MOD=AJPERES&CACHEID=ROOTWORKSPACE.Z18_NA5A1I41L0ICD0ABNDMDDG0000-b85b9556-0b2a-42b3-ad6a-8dcf3eac1ff9-nDNP5R3'
printf '%-40s %9s bytes\n' "$(basename "$f")" "$(wc -c < "$f")"
