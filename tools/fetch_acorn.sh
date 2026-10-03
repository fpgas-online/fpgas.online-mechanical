#!/bin/sh
# Fetch what the SQRL Acorn CLE-215+'s LEDs are measured from, and checked
# against, into tmp/src/acorn-cle-215 and tmp/src/nitefury.
#
# SQRL publish no drawing and no board file for the Acorn, and their site is
# gone, so accessories/measure_acorn_leds.py measures the LEDs off SQRL's own
# product photograph, from the Wayback Machine at the capture pinned below;
# "id_" asks for the file as captured rather than wrapped in the archive's
# page.  The rest are not measured:
#
#   enjoy-digital-*  Enjoy-Digital's shop photograph of a shipping CLE-215+
#                    with its heatsink and blower on, which shows the same
#                    LEDs at the same end, clear of the blower.
#   litex-wiki-*     A tweet of Enjoy-Digital's on the LiteX wiki's Acorn
#                    page, showing them lit, green, beside the blower.
#   nitefury/        RHS Research's schematic and bill of materials for the
#                    NiteFury, the open card the Acorn is pin-compatible
#                    with, at the repository's head on 30 September 2026.
#                    Its four user LEDs are D5 to D8, the designators the
#                    photographs show beside the Acorn's A4 to A1; its LED
#                    package is not the Acorn's, which is larger, so nothing
#                    is sized from it.
set -eu
cd "$(dirname "$0")/.."
d=tmp/src/acorn-cle-215
n=tmp/src/nitefury
mkdir -p "$d" "$n"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

get() {  # get <file> <url>
  test -s "$1" || curl -sSL -A "$UA" -o "$1" "$2"
  printf '%-52s %9s bytes\n' "${1#tmp/src/}" "$(wc -c < "$1")"
}

wb=https://web.archive.org/web
get "$d/sqrl-acornBanner@2x.png" \
    "$wb/20190928032642id_/http://squirrelsresearch.com/images/acornBanner@2x.png"
get "$d/enjoy-digital-DSC_0616.jpg" \
    "https://cdn.shopify.com/s/files/1/0868/1973/3829/files/DSC_0616.jpg?v=1725366968"
get "$d/litex-wiki-101612799.png" \
    "https://user-images.githubusercontent.com/1450143/101612799-592b6700-3a0b-11eb-9d3f-94f255cae8f7.png"
nf=https://raw.githubusercontent.com/RHSResearchLLC/NiteFury-and-LiteFury/6d1b8512f74c2faecec00a25a1cbf362eee2bf72
get "$n/uEVB.pdf" "$nf/Hardware/uEVB.pdf"
get "$n/uEVB-BOM-Z3.xlsx" "$nf/Hardware/uEVB-BOM-Z3.xlsx"
