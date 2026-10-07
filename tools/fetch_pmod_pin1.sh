#!/bin/sh
# Fetch what the pin 1 pictures in tinytapeout/pmod_pin1/ are drawn from, into
# tmp/src/tt-demo-pcb and tmp/src/pmod-hat.
#
#   tt-demo-pcb/  Tiny Tapeout's demo board repository, the clone `make fetch`
#                 already makes for the demo board sheets.  The pictures read
#                 the v3.2 board file at commit 0277545 (12 January 2026), the
#                 last commit at rev 3.2; tinytapeout/pmod_pin1/extract.py
#                 checks the file there is the one d830790 ("v3.2 as
#                 prototyped"), which the TT-DB-V32 sheet is drawn from, has.
#   pmod-hat/     Digilent's Pmod HAT Adapter Reference Manual, the PDF and
#                 the web page, which say they apply to Revision B, and the
#                 top view of the board on that page, which is where pin 1 of
#                 each port is seen: the square pad with a 1 printed beside
#                 it.  Digilent publish no board file and their site answers
#                 scripts with a bot check, so all three come from the Wayback
#                 Machine at the captures pinned below; "id_" asks for the
#                 file as captured rather than wrapped in the archive's page.
set -eu
cd "$(dirname "$0")/.."
t=tmp/src/tt-demo-pcb
d=tmp/src/pmod-hat
mkdir -p "$d"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

test -d "$t" || git clone --quiet https://github.com/TinyTapeout/tt-demo-pcb "$t"
git -C "$t" cat-file -e 0277545^{commit} || git -C "$t" fetch --quiet origin
git -C "$t" log -1 --format='tt-demo-pcb at %h, %ad: %s' --date=short 0277545

get() {  # get <file> <url>
  test -s "$1" || curl -sSfL -A "$UA" -o "$1" "$2"
  printf '%-52s %9s bytes\n' "${1#tmp/src/}" "$(wc -c < "$1")"
}

wb=https://web.archive.org/web
dg=https://digilent.com/reference
get "$d/pmod-hat-adapter-rm.pdf" \
    "$wb/20240705113115id_/$dg/_media/reference/add-ons/pmod-hat/171205ag_dual_brand_pmod-hat-adapter_rm.pdf"
get "$d/reference-manual.html" \
    "$wb/20231001045824id_/$dg/add-ons/pmod-hat/reference-manual"
get "$d/pmod-hat-adapter-top-1000.png" \
    "$wb/20250127035250id_/$dg/_media/reference/add-ons/pmod-hat/pmod-hat-adapter-top-1000.png"
